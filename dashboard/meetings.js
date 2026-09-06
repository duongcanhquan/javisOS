// Trang Cuộc họp — ghi chú → Bắt đầu → nhận diện người nói → Tổng kết (Antigravity).
// Nạp TRƯỚC console.js; console gọi window.JavisMeetings.render(el).
(function () {
  "use strict";

  var CDN = "/static/vendor/moonshine-wasm/dist/index.js";
  var CDN_FALLBACK =
    "https://cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm@0.1.5/dist/index.js";
  // Model Moonshine host sẵn trên VPS (cùng origin) — tránh tải HuggingFace/CDN ngoài.
  // (chi tiết từng ngôn ngữ: MOONSHINE_LOCAL)
  var MOONSHINE_VI_LOCAL = null; // legacy alias — dùng moonshineLocalUrls("vi")
  // Lần đầu: ~135MB VI + biên dịch WASM/ORT — cần thời gian; lần sau dùng cache trình duyệt.
  var MOONSHINE_LOAD_TIMEOUT_MS = 120000;
  var MOONSHINE_LOAD_TIMEOUT_OTHER_MS = 90000;
  var state = {
    meetingId: null,
    path: "",
    mic: null,
    speechRec: null,
    sttEngine: "", // "moonshine" | "webspeech" | "whisper"
    whisper: null,
    _whisperReady: null,
    moonshineMod: null,
    moonshineTranscriber: null,
    moonshineReady: false,
    moonshinePreloading: false,
    moonshinePreloadError: null,
    moonshineLang: null,
    moonshineLoadingLang: null,
    lang: "vi",
    _moonshineLoadPromise: null,
    abortRequested: false,
    running: false,
    stopped: false,
    loading: false,
    ws: null,
    lines: 0,
    speakers: {}, // index -> name
    lineBuffer: [], // dòng chờ meetingId (STT bật trước fetch)
    summaryPath: "",
    knowledgeDone: false,
    _sttWatchdog: null,
    _sttFailoverDone: false,
  };

  var archiveState = {
    tab: "new",
    q: "",
    period: "all",
    debounce: null,
    openPath: "",
    total: 0,
  };

  // Model Moonshine host sẵn trên VPS (cùng origin). Không có → CDN ngoài (chậm / hay treo).
  var MOONSHINE_LOCAL = {
    vi: {
      arch: "Base",
      files: ["encoder_model.ort", "decoder_model_merged.ort", "tokenizer.bin"],
    },
    zh: {
      arch: "Base",
      files: ["encoder_model.ort", "decoder_model_merged.ort", "tokenizer.bin"],
    },
    ja: {
      arch: "Base",
      files: ["encoder_model.ort", "decoder_model_merged.ort", "tokenizer.bin"],
    },
    ar: {
      arch: "Base",
      files: ["encoder_model.ort", "decoder_model_merged.ort", "tokenizer.bin"],
    },
    uk: {
      arch: "Base",
      files: ["encoder_model.ort", "decoder_model_merged.ort", "tokenizer.bin"],
    },
    es: {
      arch: "Base",
      files: ["encoder_model.ort", "decoder_model_merged.ort", "tokenizer.bin"],
    },
    ko: {
      arch: "Tiny",
      files: ["encoder_model.ort", "decoder_model_merged.ort", "tokenizer.bin"],
    },
    en: {
      arch: "TinyStreaming",
      files: [
        "frontend.ort",
        "encoder.ort",
        "adapter.ort",
        "cross_kv.ort",
        "decoder_kv.ort",
        "streaming_config.json",
        "tokenizer.bin",
      ],
    },
  };

  function moonshineLocalUrls(lang) {
    lang = normalizeLang(lang);
    var cfg = MOONSHINE_LOCAL[lang];
    if (!cfg) return null;
    var out = {};
    (cfg.files || []).forEach(function (f) {
      out[f] = "/static/vendor/moonshine-models/" + lang + "/" + f;
    });
    return out;
  }

  // Moonshine WASM: ngôn ngữ có model local trên VPS → ưu tiên Moonshine (nhanh).
  // EN / ngôn ngữ khác chưa local: Web Speech trước.
  var MOONSHINE_LANG = {
    // identify_speakers=false: không kéo model diarization từ CDN (hay treo / 404 local).
    vi: { arch: "Base", opts: { max_tokens_per_second: "13.0", identify_speakers: "false" }, label: "Tiếng Việt" },
    en: { arch: "TinyStreaming", opts: {}, label: "English" },
    es: { arch: "Base", opts: {}, label: "Español" },
    zh: { arch: "Base", opts: { max_tokens_per_second: "13.0" }, label: "中文" },
    ja: { arch: "Base", opts: { max_tokens_per_second: "13.0" }, label: "日本語" },
    ko: { arch: "Tiny", opts: { max_tokens_per_second: "13.0" }, label: "한국어" },
    ar: { arch: "Base", opts: { max_tokens_per_second: "13.0" }, label: "العربية" },
    uk: { arch: "Base", opts: { max_tokens_per_second: "13.0" }, label: "Українська" },
  };
  var MOONSHINE_VI_OPTS_LITE = {
    max_tokens_per_second: "13.0",
    identify_speakers: "false",
  };
  var WEB_SPEECH_BCP47 = {
    vi: "vi-VN",
    en: "en-US",
    es: "es-ES",
    zh: "zh-CN",
    ja: "ja-JP",
    ko: "ko-KR",
    ar: "ar-SA",
    uk: "uk-UA",
    fr: "fr-FR",
    de: "de-DE",
    th: "th-TH",
    id: "id-ID",
    pt: "pt-BR",
    ru: "ru-RU",
    hi: "hi-IN",
    it: "it-IT",
    nl: "nl-NL",
    pl: "pl-PL",
    tr: "tr-TR",
    ms: "ms-MY",
  };
  var ALL_LANG_CODES = Object.keys(WEB_SPEECH_BCP47).concat(["auto"]);

  var LANG_KEY = "javis.meeting.lang";

  function normalizeLang(v) {
    v = String(v || "vi").trim().toLowerCase();
    if (v === "cn" || v === "zh-cn" || v === "zh-tw") v = "zh";
    if (v.indexOf("-") > 0) v = v.split("-")[0];
    if (ALL_LANG_CODES.indexOf(v) < 0 && v !== "auto") v = "vi";
    return v;
  }

  function meetingLang() {
    var el = document.querySelector("#mtLang");
    return normalizeLang((el && el.value) || state.lang || "vi");
  }

  function langLabel(code) {
    if (code === "auto") return "Tự nhận diện";
    if (MOONSHINE_LANG[code]) return MOONSHINE_LANG[code].label;
    var map = {
      fr: "Français",
      de: "Deutsch",
      th: "ไทย",
      id: "Indonesia",
      pt: "Português",
      ru: "Русский",
      hi: "हिन्दी",
      it: "Italiano",
      nl: "Nederlands",
      pl: "Polski",
      tr: "Türkçe",
      ms: "Bahasa Melayu",
    };
    return map[code] || code;
  }

  function saveMeetingLang(v) {
    state.lang = normalizeLang(v);
    try {
      localStorage.setItem(LANG_KEY, state.lang);
    } catch (e) {}
  }

  function loadMeetingLang() {
    try {
      var v = normalizeLang(localStorage.getItem(LANG_KEY) || "vi");
      state.lang = v;
      return v;
    } catch (e) {
      state.lang = "vi";
      return "vi";
    }
  }

  function whisperLangCode(lang) {
    lang = normalizeLang(lang);
    if (lang === "auto") return "auto";
    return lang || "vi";
  }

  function webSpeechLang(lang) {
    lang = normalizeLang(lang);
    if (lang === "auto") return navigator.language || "en-US";
    return WEB_SPEECH_BCP47[lang] || "en-US";
  }

  function moonshineSupports(lang) {
    return !!MOONSHINE_LANG[normalizeLang(lang)];
  }

  function isIOSLike() {
    var ua = navigator.userAgent || "";
    if (/iPad|iPhone|iPod/.test(ua)) return true;
    // iPadOS 13+ báo MacIntel + touch
    if (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1) return true;
    return false;
  }

  function isMobileLike() {
    var ua = navigator.userAgent || "";
    if (/Android|webOS|iPhone|iPad|iPod|Mobile/i.test(ua)) return true;
    return isIOSLike();
  }

  /**
   * Moonshine WASM build có pthread → cần SharedArrayBuffer (= crossOriginIsolated).
   * Thiếu COOP/COEP trên document thì load() có thể “thành công” giả hoặc im, không ra chữ.
   */
  function moonshineRuntimeOk() {
    try {
      if (typeof SharedArrayBuffer === "undefined") return false;
      if (typeof crossOriginIsolated !== "undefined" && !crossOriginIsolated) return false;
      return true;
    } catch (e) {
      return false;
    }
  }

  /**
   * Không ưu tiên cloud STT trên mobile nữa (trước từng ép Groq Whisper).
   * Chuỗi phổ thông: Moonshine (desktop) → Cloud STT Gemini (VI khi thiếu WASM) → Web Speech.
   */
  function preferWhisperLive() {
    return false;
  }

  /**
   * Desktop + COOP/COEP OK + model local (hoặc VI): Moonshine trước.
   * Tắt tay: localStorage.setItem("javis.meeting.preferMoonshine","0")
   */
  function preferMoonshineFirst(lang) {
    try {
      if (localStorage.getItem("javis.meeting.preferMoonshine") === "0") return false;
    } catch (e) {}
    if (isMobileLike()) return false;
    if (!moonshineRuntimeOk()) return false;
    lang = normalizeLang(lang);
    if (MOONSHINE_LOCAL[lang]) return true;
    return lang === "vi";
  }

  /** Failover Moonshine khi Web Speech/Gemini lỗi — cùng điều kiện runtime. */
  function preferMoonshineFailover(lang) {
    try {
      if (localStorage.getItem("javis.meeting.preferMoonshine") === "0") return false;
    } catch (e) {}
    return moonshineRuntimeOk() && moonshineSupports(lang);
  }

  /**
   * VI/CJK: ưu tiên Cloud STT (Gemini) trước Web Speech — Web Speech VI hay lỗi network.
   */
  function preferCloudBeforeWebSpeech(lang) {
    if (preferMoonshineFirst(lang)) return false;
    lang = normalizeLang(lang);
    return (
      lang === "vi" ||
      lang === "zh" ||
      lang === "ja" ||
      lang === "ko" ||
      lang === "ar" ||
      lang === "uk" ||
      lang === "en"
    );
  }

  function micConstraints() {
    return {
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
      },
    };
  }

  async function tryStartCloudStt(root, micPromise) {
    state._whisperReady = null;
    var ok = await fetchWhisperReady();
    if (!ok) return null;
    var mp = micPromise;
    if (!mp && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      mp = navigator.mediaDevices.getUserMedia(micConstraints());
    }
    if (!mp) return null;
    try {
      await startWhisperMeeting(root, mp);
      setStatus(root, "Đang ghi (" + cloudSttLabel() + ") — nói rõ từng câu.", "ok");
      return "whisper";
    } catch (e) {
      stopWhisper();
      try {
        await discardMicStream(mp);
      } catch (e2) {}
      return null;
    }
  }

  function armAudioSessionForMic() {
    try {
      if (navigator.audioSession && "type" in navigator.audioSession) {
        navigator.audioSession.type = "play-and-record";
      }
    } catch (e) {}
  }

  async function discardMicStream(micPromise) {
    if (!micPromise) return;
    try {
      var stream = await micPromise.catch(function () {
        return null;
      });
      if (stream && stream.getTracks) {
        stream.getTracks().forEach(function (t) {
          try {
            t.stop();
          } catch (e) {}
        });
      }
    } catch (e) {}
  }

  function clearSttWatchdog() {
    if (state._sttWatchdog) {
      clearTimeout(state._sttWatchdog);
      state._sttWatchdog = null;
    }
  }

  function resetMoonshineCache() {
    state.moonshineTranscriber = null;
    state.moonshineReady = false;
    state.moonshinePreloadError = null;
    state._moonshineLoadPromise = null;
    state.moonshineLang = null;
    state.moonshineLoadingLang = null;
  }


  function hasWebSpeech() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  function fbrain() {
    try {
      return window.currentBrainPath ? currentBrainPath() : "brain";
    } catch (e) {
      return "brain";
    }
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function ic(name, opt) {
    try {
      return window.ic ? window.ic(name, opt || {}) : "";
    } catch (e) {
      return "";
    }
  }

  function setStatus(root, msg, kind) {
    var el = root.querySelector("#mtStatus");
    if (!el) return;
    el.textContent = msg || "";
    el.style.color =
      kind === "err"
        ? "var(--warn-ink)"
        : kind === "ok"
          ? "var(--ok-ink, var(--text))"
          : "var(--text3)";
  }

  function setPhase(root, phase) {
    // phase: setup | live | stopped | done
    root.querySelectorAll("[data-mt-phase]").forEach(function (n) {
      n.hidden = n.getAttribute("data-mt-phase") !== phase;
    });
    // Trái: form thông tin luôn hiện. Phải: transcript (placeholder lúc setup).
    // Dưới form (trái): tổng kết + đưa vào kiến thức khi dừng.
    var setup = root.querySelector("#mtSetup");
    var live = root.querySelector("#mtLivePanel");
    var after = root.querySelector("#mtAfter");
    var stage = root.querySelector("#mtPanelNew");
    if (setup) setup.hidden = false;
    if (live) live.hidden = false;
    if (after) after.hidden = !(phase === "stopped" || phase === "done");
    if (stage) {
      stage.classList.toggle("mt-phase-setup", phase === "setup");
      stage.classList.toggle("mt-phase-live", phase === "live");
      stage.classList.toggle(
        "mt-phase-after",
        phase === "stopped" || phase === "done"
      );
    }
    var analyzeBtn = root.querySelector("#mtAnalyze");
    if (analyzeBtn) analyzeBtn.disabled = !(phase === "stopped" || phase === "done");
    // Khoá form khi đang ghi
    ["#mtTitle", "#mtPeople", "#mtNotes"].forEach(function (sel) {
      var n = root.querySelector(sel);
      if (n) n.disabled = phase === "live";
    });
    if ((phase === "stopped" || phase === "done") && state.path) {
      var kh = root.querySelector("#mtKnowHost");
      if (kh && kh.hidden) showKnowledgePanel(root, state.path);
    }
  }

  function speakerName(idx) {
    if (idx == null || idx < 0) return "";
    if (state.speakers[idx]) return state.speakers[idx];
    return "Người " + (idx + 1);
  }

  function dominantSpeakerIndex(line) {
    if (!line) return -1;
    if (typeof line.speakerIndex === "number" && line.speakerIndex >= 0) {
      return line.speakerIndex;
    }
    var spans = (line && line.speakerSpans) || [];
    if (!spans.length) return -1;
    var best = spans[0];
    for (var i = 1; i < spans.length; i++) {
      if ((spans[i].duration || 0) > (best.duration || 0)) best = spans[i];
    }
    var idx = best.speakerIndex;
    return typeof idx === "number" ? idx : parseInt(idx, 10);
  }

  function refreshSpeakerBar(root) {
    var bar = root.querySelector("#mtSpeakers");
    if (!bar) return;
    var keys = Object.keys(state.speakers)
      .map(Number)
      .sort(function (a, b) {
        return a - b;
      });
    if (!keys.length) {
      bar.innerHTML =
        '<span class="dim">Khi có nhiều người nói, hệ thống gắn nhãn Người 1, Người 2… — bấm để đổi tên.</span>';
      return;
    }
    bar.innerHTML = keys
      .map(function (k) {
        return (
          '<button type="button" class="mt-spk" data-idx="' +
          k +
          '">' +
          esc(speakerName(k)) +
          "</button>"
        );
      })
      .join("");
    bar.querySelectorAll(".mt-spk").forEach(function (btn) {
      btn.onclick = function () {
        var idx = parseInt(btn.getAttribute("data-idx"), 10);
        var cur = speakerName(idx);
        var neu = window.prompt("Đặt tên người nói này:", cur);
        if (neu && neu.trim()) {
          state.speakers[idx] = neu.trim().slice(0, 40);
          refreshSpeakerBar(root);
        }
      };
    });
  }

  function appendFinal(root, text, wall, speaker) {
    var box = root.querySelector("#mtLines");
    if (!box) return;
    var empty = box.querySelector(".mt-empty");
    if (empty) empty.remove();
    var row = document.createElement("div");
    row.className = "mt-line";
    var who = speaker
      ? '<span class="mt-who">' + esc(speaker) + "</span> "
      : "";
    row.innerHTML =
      '<span class="mt-ts">' +
      esc(wall || "") +
      "</span> " +
      who +
      '<span class="mt-tx">' +
      esc(text) +
      "</span>";
    box.appendChild(row);
    box.scrollTop = box.scrollHeight;
    state.lines++;
    var c = root.querySelector("#mtCount");
    if (c) c.textContent = String(state.lines);
  }

  function setPartial(root, text, speaker) {
    var el = root.querySelector("#mtPartial");
    if (!el) return;
    var prefix = speaker ? speaker + ": " : "";
    el.textContent = text ? prefix + text : "";
  }

  function wsUrl() {
    var proto = location.protocol === "https:" ? "wss" : "ws";
    return proto + "://" + location.host + "/ws";
  }

  function ensureWs() {
    return new Promise(function (resolve) {
      if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        resolve(state.ws);
        return;
      }
      try {
        if (state.ws) {
          try {
            state.ws.close();
          } catch (e) {}
        }
        var sock = new WebSocket(wsUrl());
        state.ws = sock;
        sock.onopen = function () {
          resolve(sock);
        };
        sock.onerror = function () {
          resolve(null);
        };
        sock.onclose = function () {
          if (state.ws === sock) state.ws = null;
        };
        setTimeout(function () {
          if (sock.readyState !== WebSocket.OPEN) resolve(null);
        }, 2500);
      } catch (e) {
        resolve(null);
      }
    });
  }

  /** Trả mic cho SpeechRecognition — chat voice (app.js) giữ getUserMedia thì SR im lặng. */
  function releaseMicConflicts() {
    try {
      if (window.javisReleaseMicForMeeting) {
        window.javisReleaseMicForMeeting();
        return;
      }
    } catch (e) {}
    try {
      if (typeof tatRanhTay === "function") tatRanhTay();
    } catch (e) {}
    try {
      if (typeof voice !== "undefined" && voice) {
        if (voice.stopListening) voice.stopListening();
        if (voice._stopMicMeter) voice._stopMicMeter();
      }
    } catch (e) {}
  }


  function queueLine(text, t0, t1, speaker, speakerIndex) {
    if (!(text || "").trim()) return;
    if (!state.meetingId) {
      state.lineBuffer.push({
        text: text,
        t0: t0 || 0,
        t1: t1 || 0,
        speaker: speaker || "",
        speakerIndex: speakerIndex == null ? -1 : speakerIndex,
      });
      return;
    }
    sendLine(text, t0, t1, speaker, speakerIndex);
  }

  async function flushLineBuffer() {
    var buf = state.lineBuffer || [];
    state.lineBuffer = [];
    for (var i = 0; i < buf.length; i++) {
      var ln = buf[i];
      await sendLine(ln.text, ln.t0, ln.t1, ln.speaker, ln.speakerIndex);
    }
  }

  async function sendLine(text, t0, t1, speaker, speakerIndex) {
    var mid = state.meetingId;
    if (!mid || !(text || "").trim()) return;
    var payload = {
      type: "meeting_line",
      action: "meeting_line",
      meeting_id: mid,
      text: text,
      t0: t0 || 0,
      t1: t1 || 0,
      speaker: speaker || "",
      speaker_index: speakerIndex == null ? -1 : speakerIndex,
      brain: fbrain(),
    };
    var sock = await ensureWs();
    if (sock && sock.readyState === WebSocket.OPEN) {
      try {
        sock.send(JSON.stringify(payload));
        return;
      } catch (e) {}
    }
    try {
      var f = new FormData();
      f.append("text", text);
      f.append("t0", String(t0 || 0));
      f.append("t1", String(t1 || 0));
      f.append("speaker", speaker || "");
      f.append("speaker_index", String(speakerIndex == null ? -1 : speakerIndex));
      f.append("brain", fbrain());
      var resp = await fetch("/meetings/" + encodeURIComponent(mid) + "/line", {
        method: "POST",
        body: f,
      });
      var d = {};
      try {
        d = await resp.json();
      } catch (e) {}
      if (!resp.ok || (d && d.ok === false)) {
        var root = document.querySelector(".mt-wrap") && document.querySelector(".mt-wrap").closest(".cview-section");
        if (root) {
          setStatus(
            root,
            "Không ghi được dòng vào file: " + ((d && d.error) || resp.status),
            "err"
          );
        }
      }
    } catch (e) {}
  }

  function promiseTimeout(promise, ms, message) {
    var timer = null;
    return Promise.race([
      Promise.resolve(promise).finally(function () {
        if (timer) clearTimeout(timer);
      }),
      new Promise(function (_, reject) {
        timer = setTimeout(function () {
          reject(new Error(message || "Hết thời gian chờ"));
        }, ms);
      }),
    ]);
  }

  async function fetchWhisperReady() {
    if (state._whisperReady !== null) return state._whisperReady;
    try {
      var r = await fetch("/stt/status", { credentials: "same-origin" });
      if (!r.ok) {
        state._whisperReady = false;
        return false;
      }
      var d = await r.json();
      state._whisperReady = !!(d && d.available);
      state._sttProviderLabel = (d && (d.label || d.provider)) || "Cloud STT";
      return state._whisperReady;
    } catch (e) {
      state._whisperReady = false;
      return false;
    }
  }

  function cloudSttLabel() {
    return state._sttProviderLabel || "Cloud STT";
  }

  function pickRecorderMime() {
    if (typeof MediaRecorder === "undefined") return "";
    var cands = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
    for (var i = 0; i < cands.length; i++) {
      try {
        if (MediaRecorder.isTypeSupported(cands[i])) return cands[i];
      } catch (e) {}
    }
    return "";
  }

  function stopWhisper() {
    var w = state.whisper;
    state.whisper = null;
    if (!w) return;
    if (w.vadTimer) {
      clearInterval(w.vadTimer);
      w.vadTimer = null;
    }
    if (w.recorder) {
      try {
        w.recorder.ondataavailable = null;
        w.recorder.onstop = null;
        w.recorder.onerror = null;
        if (w.recorder.state === "recording" || w.recorder.state === "paused") w.recorder.stop();
      } catch (e) {}
      w.recorder = null;
    }
    if (w.stream) {
      try {
        w.stream.getTracks().forEach(function (t) {
          t.stop();
        });
      } catch (e) {}
      w.stream = null;
    }
  }

  function appendWhisperLine(root, tx) {
    var wall = new Date().toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    appendFinal(root, tx, wall, "");
    queueLine(tx, 0, 0, "", -1);
  }

  function restartWhisperRecorder(w) {
    if (!state.running || state.sttEngine !== "whisper" || !w || !w.stream) return;
    var mime = pickRecorderMime();
    var rec;
    try {
      rec = mime
        ? new MediaRecorder(w.stream, { mimeType: mime, audioBitsPerSecond: 128000 })
        : new MediaRecorder(w.stream);
    } catch (e) {
      rec = new MediaRecorder(w.stream);
    }
    w.recorder = rec;
    w.mime = rec.mimeType || mime || "audio/webm";
    w.chunks = [];
    rec.ondataavailable = function (ev) {
      if (ev.data && ev.data.size > 0) w.chunks.push(ev.data);
    };
    rec.onerror = function () {
      setStatus(w.root, "Micro ghi âm lỗi. Thử tải lại trang.", "err");
    };
    try {
      rec.start(250);
    } catch (e) {
      try {
        rec.start();
      } catch (e2) {}
    }
  }

  function startWhisperVad(root, w) {
    if (w.vadTimer) clearInterval(w.vadTimer);
    var silentTicks = 0;
    var baseline = 0;
    var ticks = 0;
    var needSilent = 19;
    w.vadTimer = setInterval(function () {
      if (!state.running || state.sttEngine !== "whisper" || !w.analyser || !w.timeData) return;
      w.analyser.getByteTimeDomainData(w.timeData);
      var s = 0;
      var N = w.timeData.length;
      for (var k = 0; k < N; k++) {
        var dv = w.timeData[k] - 128;
        s += dv * dv;
      }
      var rms = Math.sqrt(s / N) / 128;
      ticks++;
      if (ticks <= 5) {
        baseline = Math.max(baseline, rms);
        return;
      }
      var thresh = Math.max(0.028, baseline * 1.8 + 0.012);
      if (rms > thresh) {
        w.speechSeen = true;
        silentTicks = 0;
        setPartial(root, "Đang nghe…", "");
      } else if (w.speechSeen) {
        silentTicks++;
        if (silentTicks >= needSilent) {
          silentTicks = 0;
          finalizeWhisperChunk(root, w);
        }
      }
    }, 100);
  }

  function finalizeWhisperChunk(root, w) {
    if (!w || w._flushing) return;
    w._flushing = true;
    var rec = w.recorder;
    var done = function () {
      w._flushing = false;
      var type = (w.chunks[0] && w.chunks[0].type) || w.mime || "audio/webm";
      var blob = new Blob(w.chunks, { type: type });
      w.chunks = [];
      var hadSpeech = w.speechSeen;
      w.speechSeen = false;
      if (!hadSpeech || blob.size < 1200) {
        if (state.running && state.sttEngine === "whisper") restartWhisperRecorder(w);
        return;
      }
      setPartial(root, "Đang nhận dạng…", "");
      var fd = new FormData();
      var ext = type.indexOf("mp4") >= 0 ? "m4a" : type.indexOf("ogg") >= 0 ? "ogg" : "webm";
      fd.append("file", blob, "meeting." + ext);
      fd.append("lang", whisperLangCode(meetingLang()));
      fetch("/stt", { method: "POST", body: fd, credentials: "same-origin" })
        .then(function (r) {
          if (r.status === 503) {
            return r.json().then(function (j) {
              throw new Error(
                (j && j.detail) || "Cloud STT chưa sẵn sàng. Models → Gemini, hoặc dùng Web Speech / Moonshine."
              );
            });
          }
          if (!r.ok) {
            return r.json().then(function (j) {
              throw new Error((j && j.detail) || "STT lỗi " + r.status);
            });
          }
          return r.json();
        })
        .then(function (d) {
          var tx = String((d && d.text) || "").replace(/\s+/g, " ").trim();
          setPartial(root, "");
          if (tx) appendWhisperLine(root, tx);
          if (state.running && state.sttEngine === "whisper") {
            setStatus(root, "Micro đang nghe (" + cloudSttLabel() + ") — nói rõ từng câu.", "ok");
            restartWhisperRecorder(w);
          }
        })
        .catch(function (e) {
          setPartial(root, "");
          setStatus(root, (e && e.message) || String(e), "err");
          if (state.running && state.sttEngine === "whisper") restartWhisperRecorder(w);
        });
    };
    if (!rec || rec.state === "inactive") {
      done();
      return;
    }
    rec.onstop = function () {
      rec.onstop = null;
      done();
    };
    try {
      rec.stop();
    } catch (e) {
      done();
    }
  }

  async function startWhisperMeeting(root, micPromise) {
    stopWhisper();
    var stream = await micPromise;
    var w = {
      root: root,
      stream: stream,
      recorder: null,
      mime: "audio/webm",
      chunks: [],
      speechSeen: false,
      vadTimer: null,
      analyser: null,
      timeData: null,
      _flushing: false,
    };
    state.whisper = w;
    state.sttEngine = "whisper";

    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var src = ctx.createMediaStreamSource(stream);
    var an = ctx.createAnalyser();
    an.fftSize = 2048;
    src.connect(an);
    w.analyser = an;
    w.timeData = new Uint8Array(an.fftSize);

    restartWhisperRecorder(w);
    startWhisperVad(root, w);
    setStatus(root, "Micro đang nghe (" + cloudSttLabel() + ") — nói rõ từng câu.", "ok");
  }

  async function importMoonshineModule() {
    if (state.moonshineMod) return state.moonshineMod;
    try {
      state.moonshineMod = await import(/* webpackIgnore: true */ CDN);
      return state.moonshineMod;
    } catch (e) {
      state.moonshineMod = await import(/* webpackIgnore: true */ CDN_FALLBACK);
      return state.moonshineMod;
    }
  }

  function loadMoonshineTranscriberOnce(root, onProgress, lang, optsOverride) {
    lang = normalizeLang(lang || "vi");
    var cfg = MOONSHINE_LANG[lang] || MOONSHINE_LANG.vi;
    var opts = optsOverride || cfg.opts || {};
    var localUrls = moonshineLocalUrls(lang);
    var modPromise = importMoonshineModule();
    return modPromise.then(function (mod) {
      var archName =
        (MOONSHINE_LOCAL[lang] && MOONSHINE_LOCAL[lang].arch) || cfg.arch || "Base";
      var arch =
        (mod.ModelArch && mod.ModelArch[archName]) ||
        (mod.ModelArch && mod.ModelArch.Base) ||
        archName;
      var progress = function (loaded, total, file) {
        var frac = total ? Math.min(1, loaded / total) : 0;
        if (onProgress) onProgress(frac, file || "");
      };
      // Ưu tiên file local trên VPS — tránh catalog CDN / diarization.
      if (localUrls && typeof mod.Transcriber.loadFromUrls === "function") {
        return mod.Transcriber.loadFromUrls(localUrls, {
          language: lang,
          modelArch: arch,
          options: opts,
          onProgress: progress,
        });
      }
      return mod.Transcriber.load({
        language: lang,
        modelArch: arch,
        options: opts,
        onProgress: progress,
      });
    });
  }

  function ensureMoonshineTranscriber(root, onProgress, lang) {
    lang = normalizeLang(lang || meetingLang());
    if (!moonshineSupports(lang)) {
      return Promise.reject(new Error("Moonshine chưa hỗ trợ ngôn ngữ: " + lang));
    }
    if (state.moonshineTranscriber && state.moonshineLang === lang && state.moonshineReady) {
      return Promise.resolve(state.moonshineTranscriber);
    }
    // Đổi ngôn ngữ giữa chừng: bỏ promise cũ (tránh trả model tiếng Việt khi đang cần English).
    if (
      state._moonshineLoadPromise &&
      state.moonshineLoadingLang &&
      state.moonshineLoadingLang !== lang
    ) {
      resetMoonshineCache();
    } else if (state.moonshineLang && state.moonshineLang !== lang) {
      resetMoonshineCache();
    }
    if (state._moonshineLoadPromise && state.moonshineLoadingLang === lang) {
      return state._moonshineLoadPromise;
    }

    var started = Date.now();
    var tick = null;
    if (onProgress) {
      tick = setInterval(function () {
        var sec = Math.round((Date.now() - started) / 1000);
        onProgress(0, "đang tải… " + sec + "s");
      }, 1000);
    }

    state.moonshineLoadingLang = lang;
    state._moonshineLoadPromise = (async function () {
      var prog =
        onProgress ||
        function (frac) {
          updateMoonshinePreloadHint(root, frac, lang);
        };
      var transcriber;
      var cfg = MOONSHINE_LANG[lang] || MOONSHINE_LANG.vi;
      try {
        transcriber = await loadMoonshineTranscriberOnce(root, prog, lang, cfg.opts);
      } catch (e1) {
        // Không null _moonshineLoadPromise ở đây — tránh caller thứ hai nạp song song khi retry.
        var lite =
          lang === "vi"
            ? MOONSHINE_VI_OPTS_LITE
            : Object.assign({}, cfg.opts || {}, { identify_speakers: "false" });
        transcriber = await loadMoonshineTranscriberOnce(root, prog, lang, lite);
      }
      if (state.moonshineLoadingLang !== lang) {
        throw new Error("Đã đổi ngôn ngữ — huỷ nạp Moonshine.");
      }
      state.moonshineTranscriber = transcriber;
      state.moonshineReady = true;
      state.moonshineLang = lang;
      state.moonshineLoadingLang = null;
      state.moonshinePreloadError = null;
      updateMoonshinePreloadHint(root, 1, lang);
      return transcriber;
    })()
      .catch(function (e) {
        if (state.moonshineLoadingLang === lang) {
          state._moonshineLoadPromise = null;
          state.moonshineLoadingLang = null;
          state.moonshinePreloadError = e;
        }
        throw e;
      })
      .finally(function () {
        if (tick) clearInterval(tick);
      });

    return state._moonshineLoadPromise;
  }

  function updateMoonshinePreloadHint(root, frac, lang) {
    var el = root && root.querySelector("#mtMoonshinePreload");
    if (!el) return;
    lang = normalizeLang(lang || meetingLang());
    var label = langLabel(lang);
    if (!moonshineSupports(lang)) {
      el.textContent =
        "Ngôn ngữ " +
        label +
        ": dùng Web Speech hoặc Cloud STT (Gemini ở Models).";
      el.style.color = "var(--text3)";
      return;
    }
    if (preferMoonshineFirst(lang)) {
      if (state.moonshineReady && state.moonshineLang === lang) {
        el.textContent =
          "Moonshine sẵn sàng (" + label + ") — lần sau dùng cache trình duyệt.";
        el.style.color = "var(--ok-ink, var(--text3))";
        return;
      }
      if (typeof frac === "number" && frac > 0 && frac < 1) {
        el.textContent =
          "Đang chuẩn bị Moonshine (" + label + ")… " + Math.round(frac * 100) + "%";
      } else if (state.moonshinePreloading) {
        el.textContent = "Đang chuẩn bị Moonshine (" + label + ")…";
      } else if (state.moonshinePreloadError) {
        el.textContent =
          "Moonshine lỗi — Bắt đầu sẽ dùng Gemini/Web Speech.";
      } else {
        el.textContent =
          "Moonshine ưu tiên (máy chủ) — lần đầu có thể 1–2 phút nạp model; lần sau nhanh.";
      }
      el.style.color = "var(--ok-ink, var(--text3))";
      return;
    }
    if (!moonshineRuntimeOk()) {
      el.textContent =
        "Trình duyệt thiếu WASM threads — dùng Gemini/Web Speech. Mở lại bằng Chrome/Edge HTTPS.";
    } else {
      el.textContent =
        "Moonshine tắt (localStorage preferMoonshine=0) — dùng Gemini/Web Speech.";
    }
    el.style.color = "var(--ok-ink, var(--text3))";
  }

  function preloadMoonshine(root) {
    var lang = meetingLang();
    updateMoonshinePreloadHint(root, 0, lang);
    if (!preferMoonshineFirst(lang)) return;
    if (!moonshineSupports(lang)) return;
    if (state.moonshineReady && state.moonshineLang === lang) return;
    importMoonshineModule().catch(function () {});
    try {
      var urls = moonshineLocalUrls(lang);
      if (urls) {
        Object.keys(urls).forEach(function (k) {
          fetch(urls[k], { method: "HEAD", credentials: "same-origin" }).catch(function () {});
        });
      }
    } catch (e) {}
  }

  async function stopMoonshineMic() {
    if (!state.mic) return;
    try {
      await state.mic.stop();
    } catch (e) {}
    try {
      state.mic.close();
    } catch (e) {}
    state.mic = null;
    if (state.sttEngine === "moonshine") state.sttEngine = "";
  }

  function stopWebSpeech() {
    if (!state.speechRec) return;
    try {
      state.speechRec.onend = null;
      state.speechRec.onerror = null;
      state.speechRec.onresult = null;
      state.speechRec.stop();
    } catch (e) {}
    state.speechRec = null;
  }

  /** Dự phòng: Web Speech (Chrome/Edge/Safari) — nhanh nhưng không phân biệt người nói. */
  function startWebSpeech(root) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) throw new Error("Trình duyệt không hỗ trợ nhận giọng. Dùng Chrome hoặc Edge qua HTTPS.");
    stopWebSpeech();
    armAudioSessionForMic();
    var ios = isIOSLike();
    var rec = new SR();
    rec.lang = webSpeechLang(meetingLang());
    // iOS continuous=true hay tự dừng / đệm kẹt — false + restart ổn hơn.
    rec.continuous = !ios;
    rec.interimResults = true;
    rec.maxAlternatives = 3;

    function wireHandlers(r) {
      r.onstart = function () {
        setStatus(root, "Micro đang nghe — nói rõ từng câu.", "ok");
      };

      r.onspeechstart = function () {
        var partial = root.querySelector("#mtPartial");
        if (partial && !partial.textContent) partial.textContent = "…";
      };

      r.onresult = function (ev) {
        if (!state.running && !state.loading) return;
        var interim = "";
        var finals = [];
        for (var i = ev.resultIndex; i < ev.results.length; i++) {
          var piece = ((ev.results[i][0] && ev.results[i][0].transcript) || "").trim();
          if (!piece) continue;
          if (ev.results[i].isFinal) finals.push(piece);
          else interim += piece;
        }
        if (interim) setPartial(root, interim.replace(/\s+/g, " ").trim(), "");
        finals.forEach(function (tx) {
          tx = tx.replace(/\s+/g, " ").trim();
          if (!tx) return;
          setPartial(root, "");
          var wall = new Date().toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });
          appendFinal(root, tx, wall, "");
          queueLine(tx, 0, 0, "", -1);
        });
      };

      r.onerror = function (ev) {
        var err = (ev && ev.error) || "";
        if (err === "no-speech" || err === "aborted") return;
        if (err === "not-allowed") {
          setStatus(root, "Micro bị chặn. Cho phép microphone cho trang này (biểu tượng ổ khóa trên thanh địa chỉ).", "err");
        } else if (err === "audio-capture") {
          setStatus(root, "Không thấy micro. Kiểm tra tai nghe/micro đã cắm và không bị app khác giữ.", "err");
        } else if (err === "network" || err === "language-not-supported" || err === "service-not-allowed") {
          // vi-VN trên Web Speech hay lỗi network (Google STT). Moonshine → Cloud STT.
          var langNow = meetingLang();
          if (state.running && !state._sttFailoverDone) {
            state._sttFailoverDone = true;
            setStatus(root, "Web Speech lỗi (" + err + ") — đang chuyển…", "err");
            (async function () {
              try {
                clearSttWatchdog();
                stopWebSpeech();
                if (preferMoonshineFailover(langNow) && moonshineSupports(langNow)) {
                  await startMoonshine(root);
                  armSttWatchdog(root);
                  setStatus(root, "Đã chuyển Moonshine (local).", "ok");
                  return;
                }
                var cloud = await tryStartCloudStt(root, null);
                if (cloud) {
                  armSttWatchdog(root);
                  return;
                }
                setStatus(
                  root,
                  "Nhận giọng cần mạng hoặc Models → Gemini. Thử File ghi âm → chữ.",
                  "err"
                );
              } catch (e) {
                setStatus(
                  root,
                  "Chuyển STT lỗi: " +
                    ((e && e.message) || e) +
                    " — thử File ghi âm → chữ.",
                  "err"
                );
              }
            })();
            return;
          }
          setStatus(
            root,
            "Nhận giọng cần mạng (Chrome gửi âm thanh lên Google). Kiểm tra kết nối, Models → Gemini, hoặc File ghi âm → chữ.",
            "err"
          );
        } else {
          setStatus(root, "Nhận giọng: " + err, "err");
        }
      };

      r.onend = function () {
        if (!(state.running && state.speechRec === r)) return;
        var delay = ios ? 250 : 40;
        setTimeout(function () {
          if (!(state.running && state.speechRec === r)) return;
          try {
            r.start();
          } catch (e) {}
        }, delay);
      };
    }

    wireHandlers(rec);

    try {
      rec.start();
    } catch (e1) {
      stopWebSpeech();
      rec = new SR();
      rec.lang = webSpeechLang(meetingLang());
      rec.continuous = !ios;
      rec.interimResults = true;
      rec.maxAlternatives = 3;
      wireHandlers(rec);
      rec.start();
    }
    state.speechRec = rec;
    state.sttEngine = "webspeech";
  }

  function startWebSpeechSafe(root) {
    try {
      startWebSpeech(root);
    } catch (e) {
      var name = (e && e.name) || "";
      if (name === "NotAllowedError" || name === "PermissionDeniedError") {
        throw new Error(
          "Micro bị chặn. Cho phép microphone cho trang này (biểu tượng ổ khóa trên thanh địa chỉ)."
        );
      }
      throw e;
    }
  }

  async function startMoonshine(root) {
    if (state.abortRequested) throw new Error("Đã hủy");
    if (!moonshineRuntimeOk()) {
      throw new Error(
        "Trình duyệt chưa bật WASM threads (crossOriginIsolated=false). Tải lại trang hoặc dùng Web Speech (Chrome/Edge)."
      );
    }
    var lang = meetingLang();
    var label = langLabel(lang);
    var mod = await importMoonshineModule();
    var timeoutMs =
      lang === "vi" ? MOONSHINE_LOAD_TIMEOUT_MS : MOONSHINE_LOAD_TIMEOUT_OTHER_MS;

    // MicTranscriber + model local trên VPS khi có (không kéo CDN ngoài).
    var localUrls = moonshineLocalUrls(lang);
    var localCfg = MOONSHINE_LOCAL[lang];
    if (!state.moonshineReady || state.moonshineLang !== lang) {
      if (state._moonshineLoadPromise) resetMoonshineCache();
      setStatus(
        root,
        localUrls
          ? "Nạp Moonshine (" + label + ", máy chủ)… 0s"
          : "Nạp Moonshine (" + label + ")… 0s"
      );
    }

    var cfg = MOONSHINE_LANG[lang] || { arch: "Base" };
    var archName =
      (localCfg && localCfg.arch) || cfg.arch || (lang === "vi" ? "Base" : "TinyStreaming");
    var arch =
      (mod.ModelArch && mod.ModelArch[archName]) ||
      (mod.ModelArch && mod.ModelArch.Base) ||
      (mod.ModelArch && mod.ModelArch.TinyStreaming);

    var startedAt = Date.now();
    var beat = setInterval(function () {
      if (state.abortRequested) return;
      var sec = Math.round((Date.now() - startedAt) / 1000);
      setStatus(
        root,
        localUrls
          ? "Nạp Moonshine (" + label + ", máy chủ)… " + sec + "s"
          : "Nạp Moonshine (" + label + ")… " + sec + "s — tải model từ mạng."
      );
    }, 1000);

    var mic = new mod.MicTranscriber().language(lang).modelArch(arch);
    // BẮT BUỘC map object file→URL (loadFromUrls). String baseUrl dùng catalog CDN → hay treo/404.
    if (localUrls && typeof mic.modelsFrom === "function") {
      mic.modelsFrom(localUrls);
    }
    mic
      .onProgress(function (frac, file) {
        if (state.abortRequested) return;
        if (typeof frac === "number" && frac > 0) {
          setStatus(
            root,
            "Tải model " + label + "… " + Math.round(frac * 100) + "%" +
              (file ? " · " + file : "")
          );
        } else if (file) {
          setStatus(root, "Tải Moonshine (" + label + ")… " + file);
        }
      })
      .onText(function (text) {
        setPartial(root, text || "", "");
      })
      .onLine(function (line) {
        if (!state.running && !state.loading) return;
        var tx = (line && line.text) || "";
        if (!tx.trim()) return;
        var idx = -1;
        var who = "";
        setPartial(root, "");
        var t0 = line.startTime || 0;
        var t1 = t0 + (line.duration || 0);
        var wall = new Date().toLocaleTimeString("vi-VN", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });
        appendFinal(root, tx, wall, who);
        queueLine(tx, t0, t1, who, idx);
      })
      .onError(function (err) {
        setStatus(root, "Moonshine: " + ((err && err.message) || err), "err");
      });

    try {
      await promiseTimeout(
        mic.load(),
        timeoutMs,
        "Moonshine " +
          label +
          " treo khi nạp (" +
          Math.round(timeoutMs / 1000) +
          "s) — chuyển Gemini/Web Speech."
      );
      if (state.abortRequested) throw new Error("Đã hủy");
      setStatus(root, "Xin quyền micro…");
      await mic.start();
    } catch (e) {
      try {
        mic.close();
      } catch (e2) {}
      resetMoonshineCache();
      throw e;
    } finally {
      clearInterval(beat);
    }

    state.mic = mic;
    state.sttEngine = "moonshine";
    state.moonshineReady = true;
    state.moonshineLang = lang;
    state._moonshineLoadPromise = null;
    state.moonshineLoadingLang = null;
    setStatus(
      root,
      "Đang ghi (Moonshine · " + label + "). Nói rõ từng câu.",
      "ok"
    );
  }

  function seedSpeakersFromInput(root) {
    state.speakers = {};
    var raw = ((root.querySelector("#mtPeople") || {}).value || "").trim();
    if (!raw) return;
    raw.split(/[,;\n]+/).forEach(function (p, i) {
      var n = p.trim();
      if (n) state.speakers[i] = n.slice(0, 40);
    });
  }

  async function cleanupAudio() {
    clearSttWatchdog();
    stopWebSpeech();
    stopWhisper();
    await stopMoonshineMic();
    state.sttEngine = "";
  }

  function armSttWatchdog(root) {
    clearSttWatchdog();
    var linesAtStart = state.lines;
    state._sttWatchdog = setTimeout(function () {
      state._sttWatchdog = null;
      if (!state.running || state.abortRequested) return;
      if (state.lines > linesAtStart) return;
      if (state._sttFailoverDone) {
        setStatus(
          root,
          "Vẫn chưa ghi được lời. Cho phép micro, dùng Chrome/Edge (Web Speech), hoặc File ghi âm → chữ.",
          "err"
        );
        return;
      }
      state._sttFailoverDone = true;
      var prev = state.sttEngine;
      setStatus(root, "Chưa nhận được giọng — đang chuyển chế độ nhận dạng…", "err");
      (async function () {
        try {
          await cleanupAudio();
          state.running = true;
          var langNow = meetingLang();
          // Thứ tự failover: Moonshine → Cloud STT → Web Speech (không kẹt Google STT).
          if (
            prev !== "moonshine" &&
            preferMoonshineFailover(langNow) &&
            moonshineSupports(langNow)
          ) {
            try {
              await startMoonshine(root);
              setStatus(root, "Đã chuyển Moonshine (local).", "ok");
              armSttWatchdog(root);
              return;
            } catch (eM) {}
          }
          if (prev !== "whisper") {
            var cloud = await tryStartCloudStt(root, null);
            if (cloud) {
              armSttWatchdog(root);
              return;
            }
          }
          if (hasWebSpeech()) {
            startWebSpeechSafe(root);
            setStatus(root, "Đã chuyển Web Speech — nói rõ từng câu.", "ok");
            armSttWatchdog(root);
            return;
          }
          setStatus(
            root,
            "Vẫn chưa ghi được lời. Cho phép micro, Models → Gemini, hoặc File ghi âm → chữ.",
            "err"
          );
        } catch (e) {
          var msg = String((e && e.message) || e || "");
          if (/Moonshine|tải quá lâu|timeout/i.test(msg)) {
            setStatus(
              root,
              "Không tải được Moonshine. Dùng Models → Gemini (Cloud STT) hoặc File ghi âm → chữ.",
              "err"
            );
            return;
          }
          setStatus(root, "Chuyển STT lỗi: " + msg, "err");
        }
      })();
    }, 12000);
  }

  async function stopOrCancelMeeting(root) {
    if (!state.loading && !state.running && !state.meetingId) return;
    state.abortRequested = true;
    state.running = false;
    var stopBtn = root.querySelector("#mtStop");
    var startBtn = root.querySelector("#mtStart");
    if (stopBtn) stopBtn.disabled = true;
    await cleanupAudio();
    state.lineBuffer = [];
    setPartial(root, "");
    if (state.meetingId) {
      try {
        var f = new FormData();
        f.append("brain", fbrain());
        await fetch("/meetings/" + encodeURIComponent(state.meetingId) + "/stop", {
          method: "POST",
          body: f,
        });
      } catch (e) {}
      state.stopped = true;
      setPhase(root, "stopped");
      setStatus(
        root,
        "Đã dừng ghi" +
          (state.lines ? " · " + state.lines + " đoạn" : "") +
          " — bấm Tổng kết hoặc Cuộc họp mới.",
        "ok"
      );
    } else {
      state.meetingId = null;
      setPhase(root, "setup");
      setStatus(root, "Đã hủy.", "ok");
    }
    if (startBtn) startBtn.disabled = false;
    var lsUnlock = root.querySelector("#mtLang");
    if (lsUnlock) lsUnlock.disabled = false;
    state.loading = false;
    if (state.ws) {
      try {
        state.ws.close();
      } catch (e) {}
      state.ws = null;
    }
  }

  async function beginSttFast(root, langFixed, opts) {
    opts = opts || {};
    if (state.abortRequested) return null;
    var lang = normalizeLang(langFixed || meetingLang());
    var micPromise = opts.micPromise || null;

    armAudioSessionForMic();
    state._whisperReady = null; // luôn hỏi lại /stt/status (user có thể vừa dán Gemini)

    // 1) Desktop + isolation OK: Moonshine. Lỗi → Web Speech / Cloud STT.
    if (preferMoonshineFirst(lang) && moonshineSupports(lang)) {
      try {
        await startMoonshine(root);
        return "moonshine";
      } catch (e) {
        await cleanupAudio();
        resetMoonshineCache();
        releaseMicConflicts();
        await new Promise(function (r) {
          setTimeout(r, 350);
        });
        var afterMoon = await tryStartCloudStt(root, null);
        if (afterMoon) {
          setStatus(
            root,
            "Moonshine lỗi — đang ghi " + cloudSttLabel() + ". " + ((e && e.message) || ""),
            "err"
          );
          return afterMoon;
        }
        if (hasWebSpeech()) {
          try {
            startWebSpeechSafe(root);
            setStatus(
              root,
              "Moonshine lỗi — đang ghi Web Speech. " + ((e && e.message) || ""),
              "err"
            );
            return "webspeech";
          } catch (wsErr) {
            throw new Error(
              "Moonshine và Web Speech đều lỗi: " +
                ((e && e.message) || e) +
                " / " +
                ((wsErr && wsErr.message) || wsErr)
            );
          }
        }
        throw e;
      }
    }

    // 2) VI/CJK khi không Moonshine: Cloud STT (Gemini) trước — Web Speech VI hay network-fail.
    if (preferCloudBeforeWebSpeech(lang)) {
      if (micPromise) {
        // Cloud STT cần MediaRecorder; giữ micPromise.
        var cloud1 = await tryStartCloudStt(root, micPromise);
        if (cloud1) return cloud1;
        micPromise = null;
      } else {
        var cloud2 = await tryStartCloudStt(root, null);
        if (cloud2) return cloud2;
      }
    } else if (micPromise) {
      // Sắp dùng Web Speech → nhả mic sớm kẻo Chrome im.
      await discardMicStream(micPromise);
      micPromise = null;
    }

    // 3) Web Speech (phổ thông, không cần API key).
    if (hasWebSpeech()) {
      if (micPromise) {
        await discardMicStream(micPromise);
        micPromise = null;
      }
      startWebSpeechSafe(root);
      setStatus(
        root,
        "Đang ghi (Web Speech · " + langLabel(lang) + "). Nói rõ từng câu.",
        "ok"
      );
      return "webspeech";
    }

    // 4) Không Web Speech: cloud STT.
    var cloud3 = await tryStartCloudStt(root, micPromise);
    if (cloud3) return cloud3;

    // 5) Moonshine VI nếu còn (thiếu Web Speech nhưng có isolation).
    if (preferMoonshineFailover(lang) && moonshineSupports(lang)) {
      await startMoonshine(root);
      return "moonshine";
    }

    throw new Error(
      "Không nhận dạng được giọng. Dùng Chrome/Edge qua HTTPS; Models → Gemini cho Cloud STT; hoặc tải lại trang để bật Moonshine."
    );
  }

  async function startMeeting(root) {
    if (state.running || state.loading) return;
    if (
      !window.isSecureContext &&
      location.hostname !== "localhost" &&
      location.hostname !== "127.0.0.1"
    ) {
      setStatus(
        root,
        "Micro cần HTTPS. Mở https://javis.vietmycollege.com để ghi.",
        "err"
      );
      return;
    }
    var title = ((root.querySelector("#mtTitle") || {}).value || "").trim();
    var notes = ((root.querySelector("#mtNotes") || {}).value || "").trim();
    var people = ((root.querySelector("#mtPeople") || {}).value || "").trim();
    if (!title) {
      setStatus(root, "Nhập tiêu đề cuộc họp trước khi bắt đầu.", "err");
      (root.querySelector("#mtTitle") || {}).focus && root.querySelector("#mtTitle").focus();
      return;
    }

    state.loading = true;
    state.stopped = false;
    state.abortRequested = false;
    state._sttFailoverDone = false;
    state.lineBuffer = [];
    seedSpeakersFromInput(root);
    var langAtStart = meetingLang();
    var langSelLock = root.querySelector("#mtLang");
    if (langSelLock) langSelLock.disabled = true;
    var startBtn = root.querySelector("#mtStart");
    var stopBtnEarly = root.querySelector("#mtStop");
    if (startBtn) startBtn.disabled = true;
    if (stopBtnEarly) stopBtnEarly.disabled = false;

    releaseMicConflicts();
    armAudioSessionForMic();
    state.lines = 0;

    setPhase(root, "live");
    root.querySelector("#mtLines").innerHTML =
      '<div class="mt-empty dim">Đang nghe… mỗi câu sẽ ghi vào file transcript.</div>';
    root.querySelector("#mtSummary").innerHTML = "";
    refreshSpeakerBar(root);

    var sttStarted = false;
    var moonshineFail = null;
    var sttEngine = null;
    var micPromise = null;
    // Xin mic sớm khi sắp dùng Cloud STT (MediaRecorder). Web Speech: không xin trước (Chrome im).
    if (
      (preferCloudBeforeWebSpeech(langAtStart) || !hasWebSpeech()) &&
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia
    ) {
      micPromise = navigator.mediaDevices.getUserMedia(micConstraints());
    }
    try {
      // STT trong cử chỉ bấm — TRƯỚC await fetch (voice.js: await fetch làm Chrome im lặng).
      state.running = true;
      setStatus(
        root,
        preferMoonshineFirst(langAtStart)
          ? "Bật micro (Moonshine)…"
          : hasWebSpeech()
            ? "Bật micro (Web Speech)…"
            : "Bật micro…"
      );
      try {
        sttEngine = await beginSttFast(root, langAtStart, { micPromise: micPromise });
        if (sttEngine) sttStarted = true;
      } catch (fastErr) {
        moonshineFail = fastErr;
        state.running = false;
      }

      setStatus(
        root,
        sttStarted ? "Đang nghe — tạo file ghi chú…" : "Tạo file ghi chú trên server…"
      );
      var f = new FormData();
      f.append("title", title);
      f.append("notes", notes);
      f.append("attendees", people);
      f.append("language", langAtStart);
      f.append("brain", fbrain());
      var r = await (await fetch("/meetings/start", { method: "POST", body: f })).json();
      if (!r.ok) throw new Error(r.error || "Không tạo được phiên");
      if (state.abortRequested) throw new Error("Đã hủy");
      state.meetingId = r.id;
      state.path = r.path || "";
      var pathEl = root.querySelector("#mtPath");
      if (pathEl) pathEl.textContent = r.path || "";
      var countEl = root.querySelector("#mtCount");
      if (countEl) countEl.textContent = String(state.lines || 0);

      await flushLineBuffer();

      if (!sttStarted) {
        state.running = true;
        try {
          sttEngine = await beginSttFast(root, langAtStart, { micPromise: micPromise });
          if (sttEngine) sttStarted = true;
        } catch (e2) {
          moonshineFail = e2;
        }
      }

      if (!sttStarted) {
        var cloudLast = await tryStartCloudStt(root, micPromise);
        if (cloudLast) {
          sttStarted = true;
          sttEngine = cloudLast;
        } else if (hasWebSpeech()) {
          try {
            startWebSpeechSafe(root);
            sttStarted = true;
            sttEngine = "webspeech";
          } catch (wsErr) {
            throw new Error(
              (moonshineFail && moonshineFail.message) ||
                ((wsErr && wsErr.message) ||
                  "Không nghe được micro. Cho phép micro, Models → Gemini, hoặc Chrome/Edge HTTPS.")
            );
          }
        } else {
          throw new Error(
            (moonshineFail && moonshineFail.message) ||
              "Không nghe được micro. Cho phép micro, Models → Gemini, hoặc File ghi âm → chữ."
          );
        }
      }

      if (!state.running) state.running = true;
      if (sttEngine === "webspeech") {
        setStatus(
          root,
          "Đang nghe (Web Speech). Nói rõ từng câu — mỗi câu ghi vào file.",
          "ok"
        );
      } else if (sttEngine === "moonshine") {
        setStatus(
          root,
          "Đang ghi (Moonshine). Nói rõ; hệ thống gắn nhãn người nói khi phân biệt được.",
          "ok"
        );
      } else if (sttEngine === "whisper") {
        setStatus(root, "Micro đang nghe (" + cloudSttLabel() + ") — nói rõ từng câu.", "ok");
      }
      armSttWatchdog(root);
      await ensureWs();
      loadArchive(root);
    } catch (e) {
      state.running = false;
      await cleanupAudio();
      state.sttEngine = "";
      state.lineBuffer = [];
      if (state.meetingId && !state.abortRequested) {
        try {
          var fStop = new FormData();
          fStop.append("brain", fbrain());
          await fetch("/meetings/" + encodeURIComponent(state.meetingId) + "/stop", {
            method: "POST",
            body: fStop,
          });
        } catch (err) {}
      }
      setStatus(
        root,
        state.abortRequested ? "Đã hủy." : "Không bắt đầu được: " + (e.message || e),
        state.abortRequested ? "ok" : "err"
      );
      if (startBtn) startBtn.disabled = false;
      if (!state.abortRequested) state.meetingId = null;
      setPhase(root, state.abortRequested && state.meetingId ? "stopped" : "setup");
    } finally {
      state.loading = false;
      var stopBtnFin = root.querySelector("#mtStop");
      if (stopBtnFin && !state.running && !state.stopped) stopBtnFin.disabled = true;
      if (!state.running) {
        var ls = root.querySelector("#mtLang");
        if (ls) ls.disabled = false;
      }
    }
  }

  async function stopRecording(root) {
    await stopOrCancelMeeting(root);
  }

  async function loadProjectOptions(selectEl, selectedId) {
    if (!selectEl) return;
    selectEl.innerHTML = '<option value="">— Không gắn dự án (chỉ Wiki) —</option>';
    try {
      var r = await (
        await fetch("/projects?brain=" + encodeURIComponent(fbrain()))
      ).json();
      var list = r.projects || r.items || [];
      list.forEach(function (p) {
        var opt = document.createElement("option");
        opt.value = p.id || "";
        opt.textContent = p.name || p.id || "Dự án";
        if (selectedId && selectedId === p.id) opt.selected = true;
        selectEl.appendChild(opt);
      });
    } catch (e) {}
  }

  function knowledgePanelHtml(prefix, pathHint) {
    return (
      '<div class="mt-know" id="' +
      prefix +
      'Know">' +
      '<div class="mt-know-title">' +
      ic("brain") +
      " Đưa vào kiến thức</div>" +
      '<p class="mt-know-hint">Chưng thành Wiki; tuỳ chọn gắn / ghim dự án.</p>' +
      '<div class="mt-field"><label>Chủ đề / tên trang Wiki</label>' +
      '<input type="text" id="' +
      prefix +
      'KnowTopic" placeholder="VD: Quyết định pricing Q3 · Brief landing"></div>' +
      '<div class="mt-field"><label>Gắn dự án (tuỳ chọn)</label>' +
      '<select id="' +
      prefix +
      'KnowProject"></select></div>' +
      '<label class="mt-know-pin"><input type="checkbox" id="' +
      prefix +
      'KnowPin" checked> Ghim tài liệu vào dự án (nạp khi chat trong dự án)</label>' +
      '<div class="mt-toolbar" style="margin-top:10px">' +
      '<button class="s-btn" type="button" id="' +
      prefix +
      'KnowGo" data-path="' +
      esc(pathHint || "") +
      '">' +
      ic("notebook") +
      " Đưa vào kiến thức</button>" +
      "</div>" +
      '<div class="mt-know-result dim" id="' +
      prefix +
      'KnowResult"></div>' +
      "</div>"
    );
  }

  function showKnowledgePanel(root, path) {
    var host = root.querySelector("#mtKnowHost");
    if (!host) return;
    host.hidden = false;
    host.innerHTML = knowledgePanelHtml("mt", path || state.path || "");
    var sel = host.querySelector("#mtKnowProject");
    loadProjectOptions(sel, "");
    var topic = host.querySelector("#mtKnowTopic");
    var titleEl = root.querySelector("#mtTitle");
    if (topic && titleEl && titleEl.value) topic.value = titleEl.value.trim();
    var go = host.querySelector("#mtKnowGo");
    if (go) {
      go.onclick = function () {
        runToKnowledge(root, {
          path: go.getAttribute("data-path") || state.path,
          topic: (host.querySelector("#mtKnowTopic") || {}).value || "",
          projectId: (host.querySelector("#mtKnowProject") || {}).value || "",
          pin: !!(host.querySelector("#mtKnowPin") || {}).checked,
          resultEl: host.querySelector("#mtKnowResult"),
          btn: go,
        });
      };
    }
  }

  async function runToKnowledge(root, opts) {
    opts = opts || {};
    var path = (opts.path || "").trim();
    if (!path) {
      setStatus(root, "Chưa có file cuộc họp để đưa vào kiến thức.", "err");
      return;
    }
    var btn = opts.btn;
    var resultEl = opts.resultEl;
    if (btn) btn.disabled = true;
    if (resultEl) resultEl.textContent = "Đang chưng vào Wiki…";
    setStatus(root, "Đưa cuộc họp vào kiến thức…");
    try {
      var f = new FormData();
      f.append("path", path);
      f.append("brain", fbrain());
      f.append("topic", opts.topic || "");
      f.append("project_id", opts.projectId || "");
      f.append("pin", opts.pin ? "1" : "0");
      var r = await (await fetch("/meetings/to-knowledge", { method: "POST", body: f })).json();
      if (!r.ok) throw new Error(r.error || "Lỗi");
      state.knowledgeDone = true;
      var msg =
        "Đã tạo Wiki: " +
        (r.wiki_path || "") +
        (r.project_id ? " · gắn dự án" + (r.pinned ? " (ghim)" : "") : "");
      if (r.project_warn) msg += " · cảnh báo dự án: " + r.project_warn;
      if (resultEl) {
        resultEl.innerHTML =
          '<span class="mt-know-ok">✓ ' +
          esc(msg) +
          "</span>" +
          (r.wiki_path
            ? ' <button type="button" class="s-btn-ghost mt-know-open" style="margin-left:6px">Mở trang Wiki</button>'
            : "");
        var openBtn = resultEl.querySelector(".mt-know-open");
        if (openBtn && r.wiki_path) {
          openBtn.onclick = function () {
            openMeetingEditor(r.wiki_path);
          };
        }
      }
      setStatus(root, msg, "ok");
      refreshList(root);
      loadArchive(root);
    } catch (e) {
      if (resultEl) resultEl.textContent = "Lỗi: " + (e.message || e);
      setStatus(root, "Đưa vào kiến thức lỗi: " + (e.message || e), "err");
      if (btn) btn.disabled = false;
    }
  }

  async function runAnalyze(root) {
    var mid = state.meetingId;
    if (!mid) {
      setStatus(root, "Chưa có phiên để tổng kết.", "err");
      return;
    }
    if (state.running) {
      await stopRecording(root);
    }
    setStatus(root, "Đang tổng kết bằng Antigravity… thường 30–90 giây.");
    var box = root.querySelector("#mtSummary");
    if (box) box.innerHTML = '<div class="dim">Trợ lý đang đọc transcript và viết tổng kết…</div>';
    var btn = root.querySelector("#mtAnalyze");
    if (btn) btn.disabled = true;
    try {
      var f = new FormData();
      f.append("brain", fbrain());
      var r = await (
        await fetch("/meetings/" + encodeURIComponent(mid) + "/analyze", {
          method: "POST",
          body: f,
        })
      ).json();
      if (!r.ok) throw new Error(r.error || "Tổng kết lỗi");
      state.summaryPath = r.summary_path || "";
      state.knowledgeDone = false;
      if (box) {
        box.innerHTML =
          '<div class="mt-sum-path dim">Đã lưu: ' +
          esc(r.summary_path || "") +
          '</div><pre class="mt-sum-body">' +
          esc(r.summary || "") +
          "</pre>";
      }
      setPhase(root, "done");
      setStatus(root, "Xong tổng kết · " + (r.summary_path || ""), "ok");
      showKnowledgePanel(root, state.path);
      refreshList(root);
    } catch (e) {
      if (box) box.innerHTML = "";
      setStatus(root, "Tổng kết lỗi: " + (e.message || e), "err");
      if (btn) btn.disabled = false;
    }
  }

  async function uploadFallback(root, file) {
    if (!file) return;
    state.loading = true;
    setStatus(root, "Upload + Cloud STT…");
    try {
      if (!state.meetingId) {
        var title =
          ((root.querySelector("#mtTitle") || {}).value || "").trim() || file.name;
        var notes = ((root.querySelector("#mtNotes") || {}).value || "").trim();
        var people = ((root.querySelector("#mtPeople") || {}).value || "").trim();
        var fs = new FormData();
        fs.append("title", title);
        fs.append("notes", notes);
        fs.append("attendees", people);
        fs.append("language", meetingLang());
        fs.append("brain", fbrain());
        var sr = await (await fetch("/meetings/start", { method: "POST", body: fs })).json();
        if (!sr.ok) throw new Error(sr.error || "Không tạo phiên");
        state.meetingId = sr.id;
        state.path = sr.path || "";
        var pathEl = root.querySelector("#mtPath");
        if (pathEl) pathEl.textContent = sr.path || "";
      }
      var f = new FormData();
      f.append("file", file);
      f.append("brain", fbrain());
      f.append("lang", whisperLangCode(meetingLang()));
      var r = await (
        await fetch("/meetings/" + encodeURIComponent(state.meetingId) + "/upload-stt", {
          method: "POST",
          body: f,
        })
      ).json();
      if (!r.ok) throw new Error(r.error || r.noi_voi_javis || "STT lỗi");
      var box = root.querySelector("#mtLines");
      if (box) {
        box.innerHTML = "";
        appendFinal(root, r.text || "(trống)", r.provider || cloudSttLabel() || "STT", "");
      }
      state.stopped = true;
      setPhase(root, "stopped");
      setStatus(root, "Đã nhận transcript (" + (r.provider || cloudSttLabel() || "STT") + "). Bấm Tổng kết cuộc họp.", "ok");
    } catch (e) {
      setStatus(root, "Fallback lỗi: " + (e.message || e), "err");
    } finally {
      state.loading = false;
    }
  }

  async function deleteMeetingFile(root, relPath) {
    if (!relPath) return;
    var label = relPath.split("/").pop() || relPath;
    if (!window.confirm("Xóa cuộc họp \"" + label + "\"? Xóa transcript, tổng kết và file jsonl. Không hoàn tác.")) return;
    try {
      var f = new FormData();
      f.append("path", relPath);
      f.append("brain", fbrain());
      var r = await (
        await fetch("/meetings/delete", { method: "POST", body: f })
      ).json();
      if (!r.ok) throw new Error(r.error || "Xóa lỗi");
      setStatus(root, "Đã xóa " + (r.deleted || []).length + " file.", "ok");
      if (archiveState.openPath === relPath) {
        archiveState.openPath = "";
        var det = root.querySelector("#mtArchiveDetail");
        if (det) det.hidden = true;
      }
      loadArchive(root);
    } catch (e) {
      setStatus(root, "Xóa lỗi: " + (e.message || e), "err");
    }
  }

  function todayIso() {
    var d = new Date();
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + day;
  }

  function daysAgoIso(n) {
    var d = new Date();
    d.setDate(d.getDate() - n);
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + day;
  }

  function formatDateGroupLabel(dateKey) {
    if (!dateKey) return "Không rõ ngày";
    var today = todayIso();
    var yest = daysAgoIso(1);
    var parts = dateKey.split("-");
    var nice =
      parts.length === 3
        ? parts[2] + "/" + parts[1] + "/" + parts[0]
        : dateKey;
    if (dateKey === today) return "Hôm nay · " + nice;
    if (dateKey === yest) return "Hôm qua · " + nice;
    try {
      var dt = new Date(dateKey + "T12:00:00");
      var wd = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"][dt.getDay()];
      return wd + " · " + nice;
    } catch (e) {
      return nice;
    }
  }

  function archiveQueryParams() {
    var p = new URLSearchParams();
    p.set("brain", fbrain());
    p.set("limit", "80");
    if (archiveState.q) p.set("q", archiveState.q);
    if (archiveState.period === "today") {
      p.set("date", todayIso());
    } else if (archiveState.period === "week") {
      p.set("date_from", daysAgoIso(6));
      p.set("date_to", todayIso());
    } else if (archiveState.period === "month") {
      p.set("date_from", daysAgoIso(29));
      p.set("date_to", todayIso());
    }
    return p.toString();
  }

  function setMtTab(root, tab) {
    archiveState.tab = tab === "archive" ? "archive" : "new";
    tab = archiveState.tab;
    root.querySelectorAll(".mt-tab").forEach(function (btn) {
      var on = btn.getAttribute("data-mt-tab") === tab;
      btn.classList.toggle("mt-tab-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
      btn.setAttribute("tabindex", on ? "0" : "-1");
    });
    var panelNew = root.querySelector("#mtPanelNew");
    var panelArch = root.querySelector("#mtPanelArchive");
    // Ẩn hẳn panel không chọn — không chồng nội dung dưới tab kia.
    if (panelNew) {
      panelNew.hidden = tab !== "new";
      panelNew.setAttribute("aria-hidden", tab !== "new" ? "true" : "false");
    }
    if (panelArch) {
      panelArch.hidden = tab !== "archive";
      panelArch.setAttribute("aria-hidden", tab !== "archive" ? "true" : "false");
    }
    var wrap = root.querySelector(".mt-wrap") || root;
    wrap.classList.toggle("mt-on-archive", tab === "archive");
    if (tab === "archive") loadArchive(root);
  }

  function openMeetingEditor(relPath) {
    if (!relPath) return;
    try {
      if (window.JavisEditFile) {
        window.JavisEditFile(relPath);
        return;
      }
    } catch (e) {}
    var url =
      "/files/raw?brain=" +
      encodeURIComponent(fbrain()) +
      "&path=" +
      encodeURIComponent(relPath.replace(/^\.?\//, ""));
    window.open(url, "_blank");
  }

  async function openMeetingDetail(root, relPath) {
    if (!relPath) return;
    archiveState.openPath = relPath;
    var box = root.querySelector("#mtArchiveDetail");
    if (!box) return;
    box.hidden = false;
    box.innerHTML = '<div class="dim">Đang mở cuộc họp…</div>';
    try {
      var r = await (
        await fetch(
          "/meetings/detail?brain=" +
            encodeURIComponent(fbrain()) +
            "&path=" +
            encodeURIComponent(relPath)
        )
      ).json();
      if (!r.ok) throw new Error(r.error || "Không đọc được");
      var people = (r.attendees || []).join(", ") || "—";
      var tabs =
        '<div class="mt-detail-tabs">' +
        '<button type="button" class="mt-dtab mt-dtab-active" data-dtab="transcript">Transcript</button>' +
        (r.has_summary
          ? '<button type="button" class="mt-dtab" data-dtab="summary">Tổng kết</button>'
          : "") +
        (r.notes_full
          ? '<button type="button" class="mt-dtab" data-dtab="notes">Ghi chú</button>'
          : "") +
        "</div>";
      box.innerHTML =
        '<div class="mt-detail-head">' +
        '<div class="mt-detail-title">' +
        esc(r.title || "") +
        "</div>" +
        '<div class="mt-detail-meta">' +
        esc(r.date || "") +
        (r.time ? " · " + esc(r.time) : "") +
        " · " +
        esc(people) +
        (r.line_count ? " · " + r.line_count + " đoạn" : "") +
        "</div>" +
        '<div class="mt-detail-actions">' +
        '<button type="button" class="s-btn mt-detail-know">' +
        ic("brain") +
        " Đưa vào kiến thức</button>" +
        '<button type="button" class="s-btn-ghost mt-detail-edit">Sửa file</button>' +
        '<button type="button" class="s-btn-ghost mt-detail-del">Xóa</button>' +
        '<button type="button" class="s-btn-ghost mt-detail-close">Đóng</button>' +
        "</div></div>" +
        tabs +
        '<div id="mtArchKnowHost" hidden style="margin:0 0 12px"></div>' +
        '<div class="mt-detail-body" id="mtDetailBody"><pre class="mt-detail-pre">' +
        esc(r.transcript || "(Chưa có transcript)") +
        "</pre></div>";
      box.querySelector(".mt-detail-close").onclick = function () {
        archiveState.openPath = "";
        box.hidden = true;
      };
      box.querySelector(".mt-detail-edit").onclick = function () {
        openMeetingEditor(r.path);
      };
      box.querySelector(".mt-detail-del").onclick = function () {
        deleteMeetingFile(root, r.path);
      };
      var knowBtn = box.querySelector(".mt-detail-know");
      if (knowBtn) {
        knowBtn.onclick = function () {
          var host = box.querySelector("#mtArchKnowHost");
          if (!host) return;
          host.hidden = false;
          host.innerHTML = knowledgePanelHtml("mtArch", r.path || "");
          loadProjectOptions(host.querySelector("#mtArchKnowProject"), r.project_id || "");
          var topicIn = host.querySelector("#mtArchKnowTopic");
          if (topicIn) {
            topicIn.value = (r.knowledge_topic || r.title || "").trim();
          }
          var go = host.querySelector("#mtArchKnowGo");
          if (go) {
            go.onclick = function () {
              runToKnowledge(root, {
                path: r.path,
                topic: (host.querySelector("#mtArchKnowTopic") || {}).value || "",
                projectId: (host.querySelector("#mtArchKnowProject") || {}).value || "",
                pin: !!(host.querySelector("#mtArchKnowPin") || {}).checked,
                resultEl: host.querySelector("#mtArchKnowResult"),
                btn: go,
              });
            };
          }
          host.scrollIntoView({ behavior: "smooth", block: "nearest" });
        };
      }
      var bodies = {
        transcript: r.transcript || "(Chưa có transcript)",
        summary: r.summary || "(Chưa có tổng kết)",
        notes: r.notes_full || "(Không có ghi chú)",
      };
      box.querySelectorAll(".mt-dtab").forEach(function (btn) {
        btn.onclick = function () {
          box.querySelectorAll(".mt-dtab").forEach(function (b) {
            b.classList.remove("mt-dtab-active");
          });
          btn.classList.add("mt-dtab-active");
          var key = btn.getAttribute("data-dtab");
          var body = box.querySelector("#mtDetailBody");
          if (body) {
            body.innerHTML =
              '<pre class="mt-detail-pre">' + esc(bodies[key] || "") + "</pre>";
          }
        };
      });
      box.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (e) {
      box.innerHTML =
        '<div class="dim">Không mở được: ' + esc(e.message || e) + "</div>";
    }
  }

  function renderArchiveGroups(root, data) {
    var el = root.querySelector("#mtArchiveList");
    if (!el) return;
    var groups = (data && data.groups) || [];
    archiveState.total = (data && data.total) || 0;
    var badge = root.querySelector("#mtArchiveBadge");
    if (badge) badge.textContent = archiveState.total ? String(archiveState.total) : "";
    if (!groups.length) {
      el.innerHTML =
        '<div class="mt-archive-empty">' +
        ic("search", { size: 28 }) +
        "<p>Không tìm thấy cuộc họp.</p>" +
        '<p class="dim">Thử đổi từ khóa hoặc bộ lọc ngày.</p></div>';
      return;
    }
    el.innerHTML = groups
      .map(function (g) {
        var cards = (g.items || [])
          .map(function (it) {
            var tags = "";
            if (it.has_summary) tags += '<span class="mt-tag mt-tag-ok">Tổng kết</span>';
            else tags += '<span class="mt-tag">Chưa tổng kết</span>';
            if (it.line_count) tags += '<span class="mt-tag">' + it.line_count + " đoạn</span>";
            var people = (it.attendees || []).slice(0, 4).map(function (n) {
              return '<span class="mt-chip">' + esc(n) + "</span>";
            }).join("");
            if ((it.attendees || []).length > 4) {
              people += '<span class="mt-chip dim">+' + (it.attendees.length - 4) + "</span>";
            }
            return (
              '<article class="mt-card-item" data-path="' +
              esc(it.path) +
              '">' +
              '<div class="mt-card-top">' +
              '<span class="mt-card-time">' +
              esc(it.time || "—") +
              "</span>" +
              '<h4 class="mt-card-title">' +
              esc(it.title || it.path) +
              "</h4>" +
              "</div>" +
              '<div class="mt-card-tags">' +
              tags +
              "</div>" +
              (people ? '<div class="mt-card-people">' + people + "</div>" : "") +
              '<p class="mt-card-excerpt">' +
              esc(it.excerpt || "Chưa có nội dung ghi.") +
              "</p>" +
              '<div class="mt-card-actions">' +
              '<button type="button" class="s-btn mt-card-open">Xem</button>' +
              '<button type="button" class="s-btn-ghost mt-card-edit">Sửa</button>' +
              '<button type="button" class="s-btn-ghost mt-card-del">Xóa</button>' +
              "</div></article>"
            );
          })
          .join("");
        return (
          '<section class="mt-day-group">' +
          '<h3 class="mt-day-label">' +
          esc(formatDateGroupLabel(g.date)) +
          "</h3>" +
          '<div class="mt-day-cards">' +
          cards +
          "</div></section>"
        );
      })
      .join("");
    el.querySelectorAll(".mt-card-open").forEach(function (btn) {
      btn.onclick = function () {
        var card = btn.closest(".mt-card-item");
        openMeetingDetail(root, card && card.getAttribute("data-path"));
      };
    });
    el.querySelectorAll(".mt-card-edit").forEach(function (btn) {
      btn.onclick = function () {
        var card = btn.closest(".mt-card-item");
        openMeetingEditor(card && card.getAttribute("data-path"));
      };
    });
    el.querySelectorAll(".mt-card-del").forEach(function (btn) {
      btn.onclick = function () {
        var card = btn.closest(".mt-card-item");
        deleteMeetingFile(root, card && card.getAttribute("data-path"));
      };
    });
    el.querySelectorAll(".mt-card-item").forEach(function (card) {
      card.onclick = function (ev) {
        if (ev.target.closest("button")) return;
        openMeetingDetail(root, card.getAttribute("data-path"));
      };
    });
  }

  async function loadArchive(root) {
    var el = root.querySelector("#mtArchiveList");
    if (el) el.innerHTML = '<div class="dim">Đang tải lưu trữ…</div>';
    try {
      var r = await (
        await fetch("/meetings/archive?" + archiveQueryParams())
      ).json();
      if (!r.ok) throw new Error(r.error || "Lỗi tải");
      renderArchiveGroups(root, r);
    } catch (e) {
      if (el) el.innerHTML = '<div class="dim">Không tải được: ' + esc(e.message || e) + "</div>";
    }
  }

  function refreshList(root) {
    loadArchive(root);
  }

  function injectCss() {
    var s = document.getElementById("mt-css");
    if (!s) {
      s = document.createElement("style");
      s.id = "mt-css";
      document.head.appendChild(s);
    }
    s.textContent =
      ".mt-wrap{max-width:none;width:100%;box-sizing:border-box;display:flex;flex-direction:column;min-height:0;" +
      "height:calc(100dvh - 108px);max-height:calc(100dvh - 108px)}" +
      ".mt-wrap.mt-on-archive{height:auto;max-height:none;overflow:visible}" +
      /* display:grid trên panel đè [hidden] mặc định → hai tab chồng nhau */
      "#mtPanelNew[hidden],#mtPanelArchive[hidden]{display:none!important}" +
      "#mtPanelArchive:not([hidden]){flex:1;min-height:0;display:flex;flex-direction:column;overflow:auto}" +
      /* Ghi mới: 2 cột — trái form (1) | phải transcript (3). Không dùng flex kẻo đè grid. */
      "#mtPanelNew:not([hidden]){flex:1;min-height:0;display:grid;" +
      "grid-template-columns:minmax(0,1fr) minmax(0,3fr);gap:12px;align-items:stretch;overflow:hidden}" +
      ".mt-hint{font-size:13px;color:var(--text3);line-height:1.45;margin:0 0 8px}" +
      ".mt-tabs{display:flex;gap:6px;margin:0 0 14px;padding:4px;flex:none;align-self:flex-start;" +
      "border:1px solid var(--border);border-radius:10px;background:var(--surface-1,var(--bg))}" +
      ".mt-tab{appearance:none;border:1px solid transparent;background:transparent;color:var(--text3);" +
      "font:inherit;font-size:13.5px;font-weight:500;padding:8px 16px;margin:0;cursor:pointer;" +
      "border-radius:8px;display:inline-flex;align-items:center;gap:6px;line-height:1.2}" +
      ".mt-tab:hover{color:var(--text);background:var(--surface-2,rgba(127,127,127,.08))}" +
      ".mt-tab-active{color:var(--text);background:var(--bg,var(--surface-0,#111));" +
      "border-color:var(--border);font-weight:650;box-shadow:0 1px 2px rgba(0,0,0,.06)}" +
      ".mt-tab-badge{display:inline-block;margin-left:2px;padding:1px 7px;border-radius:999px;font-size:11px;" +
      "background:var(--surface-2,var(--border));color:var(--text3);font-weight:600}" +
      ".mt-tab-active .mt-tab-badge{background:var(--surface-2,var(--border));color:var(--text2)}" +
      /* —— Split: trái thông tin (~1/4) | phải transcript (~3/4) —— */
      ".mt-stage{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,3fr);gap:12px;flex:1;min-height:0;overflow:hidden;align-items:stretch}" +
      ".mt-col-info{display:flex;flex-direction:column;gap:8px;min-width:0;min-height:0;overflow:auto;padding-right:2px}" +
      ".mt-col-live{display:flex;flex-direction:column;min-width:0;min-height:0;overflow:hidden}" +
      ".mt-live-shell{flex:1;display:flex;flex-direction:column;min-height:0;border:1px solid var(--border);border-radius:12px;background:var(--surface-1);padding:10px 12px;overflow:hidden}" +
      ".mt-live-head{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px;flex:none;margin:0 0 6px}" +
      ".mt-live-title{font-size:13px;font-weight:600;color:var(--text2)}" +
      ".mt-col-live .mt-meta{margin:0;font-size:12px;gap:8px}" +
      ".mt-col-live #mtSpeakers{margin:0 0 6px;flex:none;max-height:52px;overflow:auto}" +
      ".mt-live{flex:1;min-height:0;max-height:none;overflow:auto;border:none;border-radius:0;background:transparent;padding:4px 2px;font-size:13.5px;line-height:1.5}" +
      ".mt-partial{flex:none;min-height:1.2em;margin-top:4px;padding-top:6px;font-size:13px}" +
      ".mt-live-actions{flex:none;margin-top:8px;padding-top:8px;border-top:1px solid var(--border)}" +
      ".mt-live-placeholder{display:none;flex:1;align-items:center;justify-content:center;text-align:center;padding:24px;color:var(--text3);font-size:13.5px;line-height:1.5}" +
      ".mt-phase-setup .mt-live-placeholder{display:flex}" +
      ".mt-phase-setup .mt-live-body{display:none}" +
      ".mt-phase-live .mt-live-placeholder,.mt-phase-after .mt-live-placeholder{display:none}" +
      ".mt-phase-live .mt-live-body,.mt-phase-after .mt-live-body{display:flex;flex-direction:column;flex:1;min-height:0}" +
      /* Form trái gọn */
      ".mt-card{border:1px solid var(--border);border-radius:12px;background:var(--surface-1);padding:12px;margin:0;flex:none}" +
      ".mt-field{margin:0 0 8px}.mt-field:last-child{margin-bottom:0}" +
      ".mt-field label{display:block;font-size:11.5px;letter-spacing:.01em;color:var(--text3);margin:0 0 3px}" +
      ".mt-field input,.mt-field textarea,.mt-field select{width:100%;box-sizing:border-box;padding:7px 9px;border:1px solid var(--border);border-radius:8px;background:var(--bg,var(--surface-0,#111));color:var(--text);font:inherit;font-size:13px}" +
      ".mt-field textarea{min-height:52px;max-height:96px;resize:vertical}" +
      ".mt-field input:disabled,.mt-field textarea:disabled{opacity:.72}" +
      ".mt-toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:6px 0 0}" +
      ".mt-toolbar .s-btn,.mt-toolbar .s-btn-ghost{font-size:12.5px;padding:6px 10px}" +
      "#mtAfter:not([hidden]){flex:none;display:flex;flex-direction:column;gap:8px;min-height:0}" +
      "#mtAfter .mt-sum{max-height:140px;overflow:auto}" +
      ".mt-sum-body{white-space:pre-wrap;font-family:inherit;font-size:12.5px;line-height:1.45;background:var(--bg,var(--surface-0,#111));border:1px solid var(--border);border-radius:8px;padding:10px;margin:4px 0 0}" +
      ".mt-know{border:1px solid var(--border);border-radius:10px;background:var(--surface-1);padding:10px;margin:0}" +
      ".mt-know-title{font-size:13px;font-weight:600;color:var(--text);margin:0 0 4px;display:flex;align-items:center;gap:6px}" +
      ".mt-know-hint{font-size:12px;color:var(--text3);line-height:1.4;margin:0 0 8px}" +
      ".mt-know-pin{display:flex;align-items:flex-start;gap:6px;font-size:12px;color:var(--text2);margin:2px 0 0;cursor:pointer;line-height:1.35}" +
      ".mt-know-result{margin-top:6px;font-size:12px;min-height:1.1em}" +
      ".mt-know-ok{color:var(--ok-ink,var(--text2))}" +
      "#mtStatus{font-size:12.5px;margin:0;min-height:1.2em;flex:none}" +
      ".mt-line{margin:0 0 8px}.mt-ts{color:var(--text3);font-size:11.5px;margin-right:6px}" +
      ".mt-who{display:inline-block;font-weight:600;color:var(--accent-ink,var(--text));margin-right:4px}" +
      ".mt-spk{margin:0 4px 4px 0;padding:3px 8px;border-radius:999px;border:1px solid var(--border);background:transparent;color:var(--text);cursor:pointer;font-size:12px}" +
      ".mt-spk:hover{border-color:var(--accent-ink,var(--text2))}" +
      /* Archive (full width dưới tabs) */
      ".mt-archive-toolbar{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 16px;align-items:center}" +
      ".mt-search-wrap{flex:1;min-width:200px;display:flex;align-items:center;gap:8px;border:1px solid var(--border);border-radius:10px;padding:8px 12px;background:var(--bg,var(--surface-0,#111))}" +
      ".mt-search-wrap input{flex:1;border:none;background:transparent;color:var(--text);font:inherit;outline:none;min-width:0}" +
      ".mt-filter-row{display:flex;flex-wrap:wrap;gap:6px}" +
      ".mt-filter{padding:6px 12px;border-radius:999px;border:1px solid var(--border);background:transparent;color:var(--text3);font-size:12.5px;cursor:pointer}" +
      ".mt-filter-active{border-color:var(--accent-ink,var(--text2));color:var(--text);background:var(--surface-2,var(--surface-1))}" +
      ".mt-day-group{margin:0 0 22px}" +
      ".mt-day-label{font-size:13px;font-weight:600;color:var(--text2);margin:0 0 10px;padding:0 2px}" +
      ".mt-day-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}" +
      ".mt-card-item{border:1px solid var(--border);border-radius:12px;background:var(--surface-1);padding:14px 14px 12px;cursor:pointer;transition:border-color .15s,box-shadow .15s}" +
      ".mt-card-item:hover{border-color:var(--accent-ink,var(--text3));box-shadow:0 2px 12px rgba(0,0,0,.06)}" +
      ".mt-card-top{display:flex;gap:10px;align-items:flex-start;margin:0 0 8px}" +
      ".mt-card-time{font-size:12px;color:var(--text3);min-width:42px;padding-top:2px;font-variant-numeric:tabular-nums}" +
      ".mt-card-title{margin:0;font-size:15px;font-weight:600;color:var(--text);line-height:1.35;flex:1}" +
      ".mt-card-tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px}" +
      ".mt-tag{font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid var(--border);color:var(--text3)}" +
      ".mt-tag-ok{border-color:var(--ok-ink,var(--border));color:var(--ok-ink,var(--text2))}" +
      ".mt-chip{font-size:11.5px;padding:2px 8px;border-radius:999px;background:var(--surface-2,var(--border));color:var(--text2)}" +
      ".mt-card-people{display:flex;flex-wrap:wrap;gap:5px;margin:0 0 8px}" +
      ".mt-card-excerpt{font-size:13px;color:var(--text3);line-height:1.5;margin:0 0 10px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}" +
      ".mt-card-actions{display:flex;gap:8px;flex-wrap:wrap}" +
      ".mt-card-actions .s-btn,.mt-card-actions .s-btn-ghost{font-size:12.5px;padding:5px 10px}" +
      ".mt-archive-empty{text-align:center;padding:36px 16px;color:var(--text3)}" +
      ".mt-archive-empty p{margin:8px 0 0}" +
      "#mtArchiveDetail{margin:16px 0 0;border:1px solid var(--border);border-radius:12px;background:var(--surface-1);padding:16px}" +
      ".mt-detail-head{margin:0 0 12px}" +
      ".mt-detail-title{font-size:17px;font-weight:600;color:var(--text);margin:0 0 4px}" +
      ".mt-detail-meta{font-size:13px;color:var(--text3);margin:0 0 10px}" +
      ".mt-detail-actions{display:flex;flex-wrap:wrap;gap:8px}" +
      ".mt-detail-tabs{display:flex;gap:6px;margin:12px 0 10px;border-bottom:1px solid var(--border)}" +
      ".mt-dtab{border:none;background:transparent;color:var(--text3);font:inherit;font-size:13px;padding:8px 10px;margin:0 0 -1px;border-bottom:2px solid transparent;cursor:pointer}" +
      ".mt-dtab-active{color:var(--text);border-bottom-color:var(--accent-ink,var(--text));font-weight:600}" +
      ".mt-detail-body{max-height:360px;overflow:auto;border:1px solid var(--border);border-radius:8px;background:var(--bg,var(--surface-0,#111))}" +
      ".mt-detail-pre{margin:0;padding:14px;font-size:13px;line-height:1.55;white-space:pre-wrap;font-family:inherit;color:var(--text)}" +
      ".mt-steps{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 14px;font-size:12.5px;color:var(--text3)}" +
      ".mt-steps span{padding:3px 9px;border:1px solid var(--border);border-radius:999px}" +
      /* Mobile: xếp dọc, cho cuộn trang */
      "@media (max-width:900px){" +
      ".mt-wrap{height:auto;max-height:none;overflow:visible}" +
      "#mtPanelNew:not([hidden]),.mt-stage{grid-template-columns:1fr;overflow:visible;height:auto}" +
      ".mt-col-info{overflow:visible;max-height:none}" +
      ".mt-col-live{min-height:280px}" +
      ".mt-live-shell{min-height:280px}" +
      ".mt-live{max-height:50vh}" +
      "}";
  }

  function render(el) {
    injectCss();
    // Vào tab Họp: tắt rảnh tay / nhả mic chat ngay, tránh Web Speech họp bị im.
    releaseMicConflicts();
    state.meetingId = null;
    state.running = false;
    state.stopped = false;
    state.lines = 0;
    state.speakers = {};

    el.innerHTML =
      '<div class="cview-section mt-wrap">' +
      '<nav class="mt-tabs" role="tablist" aria-label="Chế độ cuộc họp">' +
      '<button type="button" class="mt-tab mt-tab-active" id="mtTabNew" data-mt-tab="new" role="tab" aria-selected="true" aria-controls="mtPanelNew">' +
      ic("mic") +
      " Ghi mới</button>" +
      '<button type="button" class="mt-tab" id="mtTabArchive" data-mt-tab="archive" role="tab" aria-selected="false" aria-controls="mtPanelArchive">' +
      ic("folder-open") +
      ' Lưu trữ <span class="mt-tab-badge" id="mtArchiveBadge"></span></button>' +
      "</nav>" +
      '<div id="mtPanelNew" class="mt-stage mt-phase-setup" role="tabpanel" aria-labelledby="mtTabNew">' +
      '<aside class="mt-col mt-col-info">' +
      '<div class="mt-card" id="mtSetup">' +
      '<div class="mt-field"><label>Tiêu đề *</label>' +
      '<input type="text" id="mtTitle" placeholder="Họp kế hoạch Q3…" autocomplete="off"></div>' +
      '<div class="mt-field"><label>Thành phần</label>' +
      '<input type="text" id="mtPeople" placeholder="An, Bình, Chi" autocomplete="off"></div>' +
      '<div class="mt-field"><label>Ghi chú / mục tiêu</label>' +
      '<textarea id="mtNotes" placeholder="Agenda ngắn…" rows="2"></textarea></div>' +
      '<div class="mt-field"><label>Ngôn ngữ</label>' +
      '<select id="mtLang">' +
      '<optgroup label="Moonshine local (máy chủ)">' +
      '<option value="vi">Tiếng Việt</option>' +
      '<option value="zh">中文</option>' +
      '<option value="ja">日本語</option>' +
      '<option value="ko">한국어</option>' +
      '<option value="es">Español</option>' +
      '<option value="ar">العربية</option>' +
      '<option value="uk">Українська</option>' +
      '<option value="en">English (Moonshine Tiny)</option>' +
      "</optgroup>" +
      '<optgroup label="Web Speech / Cloud STT">' +
      '<option value="fr">Français</option>' +
      '<option value="de">Deutsch</option>' +
      '<option value="th">ไทย</option>' +
      '<option value="id">Indonesia</option>' +
      '<option value="pt">Português</option>' +
      '<option value="ru">Русский</option>' +
      '<option value="hi">हिन्दी</option>' +
      '<option value="it">Italiano</option>' +
      '<option value="nl">Nederlands</option>' +
      '<option value="pl">Polski</option>' +
      '<option value="tr">Türkçe</option>' +
      '<option value="ms">Bahasa Melayu</option>' +
      '<option value="auto">Tự nhận diện</option>' +
      "</optgroup>" +
      "</select>" +
      "</div>" +
      '<div id="mtMoonshinePreload" class="dim" style="font-size:12.5px;margin:0 0 10px;line-height:1.4"></div>' +
      '<div class="mt-toolbar">' +
      '<button class="s-btn" id="mtStart" type="button">' +
      ic("play") +
      " Bắt đầu</button>" +
      '<label class="s-btn-ghost" style="cursor:pointer;display:inline-flex;align-items:center;gap:5px" title="Âm thanh chỉ dùng tạm để STT">' +
      ic("upload-cloud") +
      ' File → chữ<input type="file" id="mtFile" accept="audio/*,.mp3,.wav,.m4a,.ogg,.webm" hidden></label>' +
      "</div></div>" +
      '<div id="mtAfter" hidden>' +
      '<div class="mt-toolbar">' +
      '<button class="s-btn" id="mtAnalyze" type="button">' +
      ic("sparkles") +
      " Tổng kết</button>" +
      '<button class="s-btn-ghost" id="mtNew" type="button">Họp mới</button>' +
      "</div>" +
      '<div class="mt-sum" id="mtSummary"></div>' +
      '<div id="mtKnowHost" hidden></div>' +
      "</div>" +
      '<div id="mtStatus"></div>' +
      "</aside>" +
      '<section class="mt-col mt-col-live" aria-label="Nội dung ghi nhận">' +
      '<div id="mtLivePanel" class="mt-live-shell">' +
      '<div class="mt-live-placeholder dim">Điền thông tin bên trái, bấm <b>Bắt đầu</b> — transcript hiện ở đây.</div>' +
      '<div class="mt-live-body">' +
      '<div class="mt-live-head">' +
      '<span class="mt-live-title">Transcript</span>' +
      '<div class="mt-meta"><span><code id="mtPath">—</code></span><span>Đoạn <b id="mtCount">0</b></span></div>' +
      "</div>" +
      '<div id="mtSpeakers"></div>' +
      '<div class="mt-live" id="mtLines"><div class="mt-empty dim">Đang nghe… mỗi câu sẽ hiện tại đây.</div></div>' +
      '<div class="mt-partial" id="mtPartial"></div>' +
      '<div class="mt-toolbar mt-live-actions">' +
      '<button class="s-btn-ghost" id="mtStop" type="button" disabled>' +
      ic("circle-stop") +
      " Dừng / Hủy</button>" +
      "</div></div></div>" +
      "</section>" +
      "</div>" +
      '<div id="mtPanelArchive" hidden role="tabpanel" aria-labelledby="mtTabArchive">' +
      '<div class="mt-archive-toolbar">' +
      '<label class="mt-search-wrap">' +
      ic("search") +
      '<input type="search" id="mtArchiveSearch" placeholder="Tìm tiêu đề, người tham dự, nội dung transcript…" autocomplete="off">' +
      "</label>" +
      '<div class="mt-filter-row">' +
      '<button type="button" class="mt-filter mt-filter-active" data-period="all">Tất cả</button>' +
      '<button type="button" class="mt-filter" data-period="today">Hôm nay</button>' +
      '<button type="button" class="mt-filter" data-period="week">7 ngày</button>' +
      '<button type="button" class="mt-filter" data-period="month">30 ngày</button>' +
      "</div></div>" +
      '<div id="mtArchiveList"><div class="dim">Đang tải…</div></div>' +
      '<div id="mtArchiveDetail" hidden></div>' +
      "</div>" +
      "</div>";

    el.querySelector("#mtStart").onclick = function () {
      startMeeting(el);
    };
    el.querySelector("#mtStop").onclick = function () {
      stopRecording(el);
    };
    el.querySelector("#mtAnalyze").onclick = function () {
      runAnalyze(el);
    };
    el.querySelector("#mtNew").onclick = function () {
      roi();
      render(el);
    };
    el.querySelector("#mtFile").onchange = function (ev) {
      var file = ev.target.files && ev.target.files[0];
      uploadFallback(el, file);
      ev.target.value = "";
    };

    el.querySelectorAll(".mt-tab").forEach(function (btn) {
      btn.onclick = function () {
        setMtTab(el, btn.getAttribute("data-mt-tab"));
      };
    });
    var searchIn = el.querySelector("#mtArchiveSearch");
    if (searchIn) {
      searchIn.oninput = function () {
        archiveState.q = searchIn.value.trim();
        if (archiveState.debounce) clearTimeout(archiveState.debounce);
        archiveState.debounce = setTimeout(function () {
          loadArchive(el);
        }, 320);
      };
    }
    el.querySelectorAll(".mt-filter").forEach(function (btn) {
      btn.onclick = function () {
        archiveState.period = btn.getAttribute("data-period") || "all";
        el.querySelectorAll(".mt-filter").forEach(function (b) {
          b.classList.toggle(
            "mt-filter-active",
            b.getAttribute("data-period") === archiveState.period
          );
        });
        loadArchive(el);
      };
    });

    setPhase(el, "setup");
    setMtTab(el, archiveState.tab || "new");
    setStatus(el, "Điền thông tin rồi bấm Bắt đầu cuộc họp.");
    var langSel = el.querySelector("#mtLang");
    var savedLang = loadMeetingLang();
    if (langSel) {
      langSel.value = savedLang;
      langSel.onchange = function () {
        var neu = langSel.value;
        saveMeetingLang(neu);
        if (
          state.moonshineLang &&
          state.moonshineLang !== normalizeLang(neu)
        ) {
          resetMoonshineCache();
        } else if (
          state.moonshineLoadingLang &&
          state.moonshineLoadingLang !== normalizeLang(neu)
        ) {
          resetMoonshineCache();
        }
        if (preferMoonshineFirst(neu)) preloadMoonshine(el);
        else updateMoonshinePreloadHint(el, 0, neu);
      };
    }
    // Làm mới trạng thái Cloud STT + gợi ý engine mỗi lần mở tab.
    state._whisperReady = null;
    fetchWhisperReady().then(function () {
      updateMoonshinePreloadHint(el, 0, savedLang);
    });
    preloadMoonshine(el);
  }

  function roi() {
    state.running = false;
    state.lineBuffer = [];
    releaseMicConflicts();
    stopWebSpeech();
    stopWhisper();
    if (state.mic) {
      try {
        state.mic.stop();
      } catch (e) {}
      try {
        state.mic.close();
      } catch (e) {}
      state.mic = null;
      state.sttEngine = "";
    }
    if (state.ws) {
      try {
        state.ws.close();
      } catch (e) {}
      state.ws = null;
    }
  }

  function isRecording() {
    return !!(state.running || state.loading);
  }

  window.JavisMeetings = { render: render, roi: roi, isRecording: isRecording };
})();
