// Trang Cuộc họp — ghi chú → Bắt đầu → nhận diện người nói → Tổng kết (Ollama).
// Nạp TRƯỚC console.js; console gọi window.JavisMeetings.render(el).
(function () {
  "use strict";

  var CDN = "/static/vendor/moonshine-wasm/dist/index.js";
  var CDN_FALLBACK =
    "https://cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm@0.1.5/dist/index.js";
  var MOONSHINE_LOAD_TIMEOUT_MS = 90000;
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
    _moonshineLoadPromise: null,
    abortRequested: false,
    running: false,
    stopped: false,
    loading: false,
    ws: null,
    lines: 0,
    speakers: {}, // index -> name
    lineBuffer: [], // dòng chờ meetingId (STT bật trước fetch)
  };

  var archiveState = {
    tab: "new",
    q: "",
    period: "all",
    debounce: null,
    openPath: "",
    total: 0,
  };

  // Tiếng Việt chỉ có model Base (~70MB). MicTranscriber mặc định MediumStreaming (~270MB, chỉ có en).
  var MOONSHINE_VI_OPTS = {
    max_tokens_per_second: "13.0",
    identify_speakers: "true",
  };

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
    // setup form stays visible until live; during live show live panel
    var setup = root.querySelector("#mtSetup");
    var live = root.querySelector("#mtLivePanel");
    var after = root.querySelector("#mtAfter");
    if (setup) setup.hidden = phase === "live";
    if (live) live.hidden = phase === "setup";
    if (after) after.hidden = !(phase === "stopped" || phase === "done");
    var analyzeBtn = root.querySelector("#mtAnalyze");
    if (analyzeBtn) analyzeBtn.disabled = !(phase === "stopped" || phase === "done");
  }

  function speakerName(idx) {
    if (idx == null || idx < 0) return "";
    if (state.speakers[idx]) return state.speakers[idx];
    return "Người " + (idx + 1);
  }

  function dominantSpeakerIndex(line) {
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
      await fetch("/meetings/" + encodeURIComponent(mid) + "/line", {
        method: "POST",
        body: f,
      });
    } catch (e) {}
  }

  function promiseTimeout(promise, ms, message) {
    return Promise.race([
      promise,
      new Promise(function (_, reject) {
        setTimeout(function () {
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
      return state._whisperReady;
    } catch (e) {
      state._whisperReady = false;
      return false;
    }
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
      fd.append("lang", "vi");
      fetch("/stt", { method: "POST", body: fd, credentials: "same-origin" })
        .then(function (r) {
          if (r.status === 503) {
            return r.json().then(function (j) {
              throw new Error(
                (j && j.detail) || "Chưa cấu hình Groq API key. Vào trang Models → Groq."
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
            setStatus(root, "Micro đang nghe (Whisper) — nói rõ từng câu.", "ok");
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
    setStatus(root, "Micro đang nghe (Whisper) — nói rõ từng câu.", "ok");
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

  function ensureMoonshineTranscriber(root, onProgress) {
    if (state.moonshineTranscriber) {
      return Promise.resolve(state.moonshineTranscriber);
    }
    if (state._moonshineLoadPromise) return state._moonshineLoadPromise;

    var started = Date.now();
    var tick = null;
    if (onProgress) {
      tick = setInterval(function () {
        var sec = Math.round((Date.now() - started) / 1000);
        onProgress(0, "đang tải… " + sec + "s");
      }, 1000);
    }

    state._moonshineLoadPromise = (async function () {
      var mod = await importMoonshineModule();
      var prog =
        onProgress ||
        function (frac) {
          updateMoonshinePreloadHint(root, frac);
        };
      var transcriber = await mod.Transcriber.load({
        language: "vi",
        modelArch: mod.ModelArch.Base,
        options: MOONSHINE_VI_OPTS,
        onProgress: function (loaded, total, file) {
          var frac = total ? Math.min(1, loaded / total) : 0;
          if (typeof frac === "number" && frac > 0) prog(frac, file || "");
          else prog(0, file || "");
        },
      });
      state.moonshineTranscriber = transcriber;
      state.moonshineReady = true;
      state.moonshinePreloadError = null;
      updateMoonshinePreloadHint(root, 1);
      return transcriber;
    })()
      .catch(function (e) {
        state._moonshineLoadPromise = null;
        state.moonshinePreloadError = e;
        throw e;
      })
      .finally(function () {
        if (tick) clearInterval(tick);
      });

    return state._moonshineLoadPromise;
  }

  function updateMoonshinePreloadHint(root, frac) {
    var el = root && root.querySelector("#mtMoonshinePreload");
    if (!el) return;
    if (state.moonshineReady) {
      el.textContent = "Moonshine sẵn sàng (model tiếng Việt ~70MB, lần sau dùng cache).";
      el.style.color = "var(--ok-ink, var(--text3))";
      return;
    }
    if (typeof frac === "number" && frac > 0 && frac < 1) {
      el.textContent =
        "Đang chuẩn bị Moonshine (model tiếng Việt)… " + Math.round(frac * 100) + "%";
    } else if (state.moonshinePreloading) {
      el.textContent = "Đang chuẩn bị Moonshine…";
    } else if (state.moonshinePreloadError) {
      el.textContent = "Moonshine chưa tải được — vẫn thử lại khi bấm Bắt đầu.";
    } else {
      el.textContent = "";
    }
  }

  function preloadMoonshine(root) {
    if (state.moonshineReady || state.moonshinePreloading || state._moonshineLoadPromise) return;
    state.moonshinePreloading = true;
    ensureMoonshineTranscriber(root)
      .catch(function (e) {
        state.moonshinePreloadError = e;
        updateMoonshinePreloadHint(root);
      })
      .finally(function () {
        state.moonshinePreloading = false;
      });
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

  /** Dự phòng: Web Speech (Chrome/Edge) — nhanh nhưng không phân biệt người nói. */
  function startWebSpeech(root) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) throw new Error("Trình duyệt không hỗ trợ nhận giọng. Dùng Chrome hoặc Edge qua HTTPS.");
    stopWebSpeech();
    var rec = new SR();
    rec.lang = "vi-VN";
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 3;

    rec.onstart = function () {
      setStatus(root, "Micro đang nghe — nói rõ từng câu.", "ok");
    };

    rec.onspeechstart = function () {
      var partial = root.querySelector("#mtPartial");
      if (partial && !partial.textContent) partial.textContent = "…";
    };

    rec.onresult = function (ev) {
      if (!state.running) return;
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

    rec.onerror = function (ev) {
      var err = (ev && ev.error) || "";
      if (err === "no-speech" || err === "aborted") return;
      if (err === "not-allowed") {
        setStatus(root, "Micro bị chặn. Cho phép microphone cho trang này (biểu tượng ổ khóa trên thanh địa chỉ).", "err");
      } else if (err === "audio-capture") {
        setStatus(root, "Không thấy micro. Kiểm tra tai nghe/micro đã cắm và không bị app khác giữ.", "err");
      } else if (err === "network") {
        setStatus(
          root,
          "Nhận giọng cần mạng (Chrome gửi âm thanh lên Google). Kiểm tra kết nối hoặc dùng File ghi âm → chữ.",
          "err"
        );
      } else {
        setStatus(root, "Nhận giọng: " + err, "err");
      }
    };

    rec.onend = function () {
      if (state.running && state.speechRec === rec) {
        try {
          rec.start();
        } catch (e) {}
      }
    };

    try {
      rec.start();
    } catch (e1) {
      stopWebSpeech();
      rec = new SR();
      rec.lang = "vi-VN";
      rec.continuous = true;
      rec.interimResults = true;
      rec.maxAlternatives = 3;
      rec.onstart = function () {
        setStatus(root, "Micro đang nghe — nói rõ từng câu.", "ok");
      };
      rec.onspeechstart = function () {
        var partial = root.querySelector("#mtPartial");
        if (partial && !partial.textContent) partial.textContent = "…";
      };
      rec.onresult = function (ev) {
        if (!state.running) return;
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
      rec.onerror = function (ev) {
        var err = (ev && ev.error) || "";
        if (err === "no-speech" || err === "aborted") return;
        if (err === "not-allowed") {
          setStatus(root, "Micro bị chặn. Cho phép microphone cho trang này (biểu tượng ổ khóa trên thanh địa chỉ).", "err");
        } else if (err === "audio-capture") {
          setStatus(root, "Không thấy micro. Kiểm tra tai nghe/micro đã cắm và không bị app khác giữ.", "err");
        } else if (err === "network") {
          setStatus(
            root,
            "Nhận giọng cần mạng (Chrome gửi âm thanh lên Google). Kiểm tra kết nối hoặc dùng File ghi âm → chữ.",
            "err"
          );
        } else {
          setStatus(root, "Nhận giọng: " + err, "err");
        }
      };
      rec.onend = function () {
        if (state.running && state.speechRec === rec) {
          try {
            rec.start();
          } catch (e) {}
        }
      };
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
    var mod = await importMoonshineModule();
    if (!state.moonshineReady) {
      setStatus(root, "Nạp model Moonshine (tiếng Việt, ~70MB)…");
    }
    var transcriber = await promiseTimeout(
      ensureMoonshineTranscriber(root, function (frac, hint) {
        if (state.abortRequested) return;
        if (frac > 0) {
          setStatus(root, "Tải model tiếng Việt… " + Math.round(frac * 100) + "%");
        } else {
          setStatus(
            root,
            "Tải model Moonshine (tiếng Việt, ~70MB)… " + (hint || "")
          );
        }
      }),
      MOONSHINE_LOAD_TIMEOUT_MS,
      "Moonshine không tải được trong 90 giây. Kiểm tra mạng hoặc dùng Web Speech."
    );
    if (state.abortRequested) throw new Error("Đã hủy");

    var mic = new mod.MicTranscriber()
      .useTranscriber(transcriber)
      .onText(function (text) {
        setPartial(root, text || "", "");
      })
      .onLine(function (line) {
        var tx = (line && line.text) || "";
        if (!tx.trim()) return;
        var idx = dominantSpeakerIndex(line);
        if (idx >= 0 && state.speakers[idx] == null) {
          state.speakers[idx] = "Người " + (idx + 1);
          refreshSpeakerBar(root);
        }
        var who = idx >= 0 ? speakerName(idx) : "";
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

    setStatus(root, "Xin quyền micro…");
    await mic.start();
    state.mic = mic;
    state.sttEngine = "moonshine";
    setStatus(
      root,
      "Đang ghi (Moonshine). Nói rõ; hệ thống gắn nhãn người nói khi phân biệt được.",
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
    stopWebSpeech();
    stopWhisper();
    await stopMoonshineMic();
    state.sttEngine = "";
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
    state.loading = false;
    if (state.ws) {
      try {
        state.ws.close();
      } catch (e) {}
      state.ws = null;
    }
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
    state.lineBuffer = [];
    seedSpeakersFromInput(root);
    var startBtn = root.querySelector("#mtStart");
    var stopBtnEarly = root.querySelector("#mtStop");
    if (startBtn) startBtn.disabled = true;
    if (stopBtnEarly) stopBtnEarly.disabled = false;

    releaseMicConflicts();

    setPhase(root, "live");
    root.querySelector("#mtLines").innerHTML =
      '<div class="mt-empty dim">Đang nghe… mỗi câu sẽ ghi vào file transcript.</div>';
    root.querySelector("#mtSummary").innerHTML = "";
    refreshSpeakerBar(root);

    var sttStarted = false;
    var moonshineFail = null;
    var micPromise = null;
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      micPromise = navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });
    }
    try {
      setStatus(root, "Tạo file ghi chú trên server…");
      var f = new FormData();
      f.append("title", title);
      f.append("notes", notes);
      f.append("attendees", people);
      f.append("language", "vi");
      f.append("brain", fbrain());
      var r = await (await fetch("/meetings/start", { method: "POST", body: f })).json();
      if (!r.ok) throw new Error(r.error || "Không tạo được phiên");
      if (state.abortRequested) throw new Error("Đã hủy");
      state.meetingId = r.id;
      state.path = r.path || "";
      state.lines = 0;
      var pathEl = root.querySelector("#mtPath");
      if (pathEl) pathEl.textContent = r.path || "";
      var countEl = root.querySelector("#mtCount");
      if (countEl) countEl.textContent = "0";

      try {
        setStatus(root, "Bật Moonshine…");
        await startMoonshine(root);
        if (state.abortRequested) throw new Error("Đã hủy");
        state.running = true;
        sttStarted = true;
      } catch (moonErr) {
        moonshineFail = moonErr;
        await stopMoonshineMic();
        if (state.abortRequested) throw moonErr;
        if (hasWebSpeech()) {
          setStatus(root, "Moonshine không khả dụng — chuyển Web Speech…");
          startWebSpeechSafe(root);
          state.running = true;
          sttStarted = true;
        }
      }

      await flushLineBuffer();

      if (!sttStarted) {
        var whisperOk = await fetchWhisperReady();
        if (whisperOk && micPromise) {
          try {
            await startWhisperMeeting(root, micPromise);
            state.running = true;
            sttStarted = true;
          } catch (whErr) {
            if (micPromise && micPromise.catch) {
              try {
                await micPromise.catch(function () {});
              } catch (e) {}
            }
            throw new Error(
              (whErr && whErr.message) ||
                "Không bật được micro Whisper. Cho phép micro hoặc dán key Groq ở trang Models."
            );
          }
        } else if (whisperOk && !micPromise) {
          throw new Error(
            "Trình duyệt không hỗ trợ micro. Dùng Chrome/Edge hoặc File ghi âm → chữ."
          );
        } else {
          throw new Error(
            (moonshineFail && moonshineFail.message) ||
              "Không nghe được micro. Cho phép micro, kiểm tra mạng (Moonshine), hoặc dán key Groq ở Models."
          );
        }
      } else if (state.sttEngine === "webspeech") {
        setStatus(
          root,
          "Đang nghe (Web Speech). Không phân biệt người nói — Moonshine sẽ dùng lại khi tải xong.",
          "ok"
        );
      }
      await ensureWs();
      refreshList(root);
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
    }
  }

  async function stopRecording(root) {
    await stopOrCancelMeeting(root);
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
    setStatus(root, "Đang tổng kết bằng Ollama (javis-qwen3-8b)… có thể mất 1–2 phút.");
    var box = root.querySelector("#mtSummary");
    if (box) box.innerHTML = '<div class="dim">Trợ lý đang đọc transcript và viết tổng kết…</div>';
    var btn = root.querySelector("#mtAnalyze");
    if (btn) btn.disabled = true;
    try {
      var f = new FormData();
      f.append("brain", fbrain());
      f.append("model", "javis-qwen3-8b");
      var r = await (
        await fetch("/meetings/" + encodeURIComponent(mid) + "/analyze", {
          method: "POST",
          body: f,
        })
      ).json();
      if (!r.ok) throw new Error(r.error || "Tổng kết lỗi");
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
    setStatus(root, "Upload + Groq Whisper…");
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
        fs.append("language", "vi");
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
        appendFinal(root, r.text || "(trống)", "Groq", "");
      }
      state.stopped = true;
      setPhase(root, "stopped");
      setStatus(root, "Đã nhận transcript Groq. Bấm Tổng kết cuộc họp.", "ok");
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
    archiveState.tab = tab;
    root.querySelectorAll(".mt-tab").forEach(function (btn) {
      var on = btn.getAttribute("data-mt-tab") === tab;
      btn.classList.toggle("mt-tab-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    var panelNew = root.querySelector("#mtPanelNew");
    var panelArch = root.querySelector("#mtPanelArchive");
    if (panelNew) panelNew.hidden = tab !== "new";
    if (panelArch) panelArch.hidden = tab !== "archive";
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
        '<button type="button" class="s-btn-ghost mt-detail-edit">Sửa file</button>' +
        '<button type="button" class="s-btn-ghost mt-detail-del">Xóa</button>' +
        '<button type="button" class="s-btn-ghost mt-detail-close">Đóng</button>' +
        "</div></div>" +
        tabs +
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
    if (document.getElementById("mt-css")) return;
    var s = document.createElement("style");
    s.id = "mt-css";
    s.textContent =
      ".mt-wrap{max-width:920px}" +
      ".mt-hero{margin:0 0 16px}" +
      ".mt-hero h2{margin:0 0 6px;font-size:22px;color:var(--text)}" +
      ".mt-hint{font-size:14px;color:var(--text3);line-height:1.6;margin:0 0 14px;max-width:720px}" +
      ".mt-tabs{display:flex;gap:8px;margin:0 0 16px;border-bottom:1px solid var(--border);padding-bottom:0}" +
      ".mt-tab{appearance:none;border:none;background:transparent;color:var(--text3);font:inherit;font-size:14px;padding:10px 14px;margin:0 0 -1px;border-bottom:2px solid transparent;cursor:pointer;border-radius:8px 8px 0 0}" +
      ".mt-tab:hover{color:var(--text)}" +
      ".mt-tab-active{color:var(--text);border-bottom-color:var(--accent-ink,var(--text));font-weight:600}" +
      ".mt-tab-badge{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:999px;font-size:11px;background:var(--surface-2,var(--border));color:var(--text3)}" +
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
      ".mt-card{border:1px solid var(--border);border-radius:12px;background:var(--surface-1);padding:16px 16px 14px;margin:0 0 14px}" +
      ".mt-field{margin:0 0 12px}.mt-field label{display:block;font-size:13px;color:var(--text2);margin:0 0 5px}" +
      ".mt-field input,.mt-field textarea{width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid var(--border);border-radius:8px;background:var(--bg,var(--surface-0,#111));color:var(--text);font:inherit}" +
      ".mt-field textarea{min-height:72px;resize:vertical}" +
      ".mt-toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:4px 0 0}" +
      ".mt-live{border:1px solid var(--border);border-radius:10px;background:var(--surface-1);padding:12px;min-height:240px;max-height:440px;overflow:auto;font-size:14px;line-height:1.55}" +
      ".mt-line{margin:0 0 10px}.mt-ts{color:var(--text3);font-size:12px;margin-right:6px}" +
      ".mt-who{display:inline-block;font-weight:600;color:var(--accent-ink,var(--text));margin-right:4px}" +
      ".mt-partial{min-height:1.4em;color:var(--text3);font-style:italic;margin-top:8px;padding-top:8px;border-top:1px dashed var(--border)}" +
      ".mt-meta{font-size:13px;color:var(--text3);margin:8px 0;display:flex;flex-wrap:wrap;gap:12px}" +
      ".mt-spk{margin:0 6px 6px 0;padding:4px 10px;border-radius:999px;border:1px solid var(--border);background:transparent;color:var(--text);cursor:pointer;font-size:13px}" +
      ".mt-spk:hover{border-color:var(--accent-ink,var(--text2))}" +
      ".mt-sum-body{white-space:pre-wrap;font-family:inherit;font-size:14px;line-height:1.55;background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:14px;margin:8px 0 0}" +
      "#mtStatus{font-size:13.5px;margin:8px 0 0;min-height:1.3em}" +
      ".mt-steps{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 14px;font-size:12.5px;color:var(--text3)}" +
      ".mt-steps span{padding:3px 9px;border:1px solid var(--border);border-radius:999px}";
    document.head.appendChild(s);
  }

  function render(el) {
    injectCss();
    state.meetingId = null;
    state.running = false;
    state.stopped = false;
    state.lines = 0;
    state.speakers = {};

    el.innerHTML =
      '<div class="cview-section mt-wrap">' +
      '<div class="mt-hero">' +
      "<h2>" +
      ic("mic") +
      " Cuộc họp</h2>" +
      '<p class="mt-hint"><b>Chỉ lưu chữ</b> (markdown trong <code>sources/meetings/</code>) — <b>không lưu file ghi âm</b> trên server. <b>Mặc định: Moonshine</b> (~70MB, tải một lần, có nhãn Người 1/2…) chạy ngay trên máy bạn. Nếu Moonshine lỗi: Chrome dùng Web Speech; hoặc key <b>Groq</b> ở Models (Whisper). Hoặc “File ghi âm → chữ”. <b>Tổng kết</b> bằng Ollama (<code>javis-qwen3-8b</code>).</p>' +
      '<p class="mt-hint" style="margin-top:-6px"><b>Cần HTTPS</b> (vd <code>https://javis.vietmycollege.com</code>) và cho phép micro khi trình duyệt hỏi. Họp online (Zoom/Meet): micro thường chỉ nghe rõ bạn — ghi file rồi “File → chữ” nếu cần bắt cả phòng.</p>' +
      '<p class="mt-hint dim" id="mtMoonshinePreload" style="margin-top:-6px;font-size:13px"></p>' +
      '<div class="mt-steps"><span>1. Ghi chú</span><span>2. Ghi chữ</span><span>3. Dừng</span><span>4. Tổng kết</span></div>' +
      "</div>" +
      '<nav class="mt-tabs" role="tablist">' +
      '<button type="button" class="mt-tab mt-tab-active" data-mt-tab="new" role="tab" aria-selected="true">' +
      ic("mic") +
      " Ghi mới</button>" +
      '<button type="button" class="mt-tab" data-mt-tab="archive" role="tab" aria-selected="false">' +
      ic("folder-open") +
      ' Lưu trữ <span class="mt-tab-badge" id="mtArchiveBadge"></span></button>' +
      "</nav>" +
      '<div id="mtPanelNew">' +
      '<div class="mt-card" id="mtSetup">' +
      '<div class="mt-field"><label>Tiêu đề cuộc họp *</label>' +
      '<input type="text" id="mtTitle" placeholder="Vd: Họp kế hoạch Q3 — Marketing"></div>' +
      '<div class="mt-field"><label>Thành phần (cách nhau bằng dấu phẩy)</label>' +
      '<input type="text" id="mtPeople" placeholder="Vd: An, Bình, Chi"></div>' +
      '<div class="mt-field"><label>Ghi chú / mục tiêu trước khi họp</label>' +
      '<textarea id="mtNotes" placeholder="Mục đích họp, agenda ngắn, điểm cần quyết…"></textarea></div>' +
      '<div class="mt-toolbar">' +
      '<button class="s-btn" id="mtStart" type="button">' +
      ic("play") +
      " Bắt đầu cuộc họp</button>" +
      '<label class="s-btn-ghost" style="cursor:pointer;display:inline-flex;align-items:center;gap:6px" title="Âm thanh chỉ dùng tạm để STT, không lưu trên server">' +
      ic("upload-cloud") +
      ' File ghi âm → chữ<input type="file" id="mtFile" accept="audio/*,.mp3,.wav,.m4a,.ogg,.webm" hidden></label>' +
      "</div></div>" +
      '<div id="mtLivePanel" hidden>' +
      '<div class="mt-meta"><span>File: <code id="mtPath">—</code></span><span>Đoạn: <b id="mtCount">0</b></span></div>' +
      '<div id="mtSpeakers" style="margin:8px 0 10px"></div>' +
      '<div class="mt-live" id="mtLines"><div class="mt-empty dim">Chưa có dòng nào.</div></div>' +
      '<div class="mt-partial" id="mtPartial"></div>' +
      '<div class="mt-toolbar" style="margin-top:12px">' +
      '<button class="s-btn-ghost" id="mtStop" type="button" disabled>' +
      ic("circle-stop") +
      " Dừng / Hủy</button>" +
      "</div></div>" +
      '<div id="mtAfter" hidden>' +
      '<div class="mt-toolbar" style="margin-top:8px">' +
      '<button class="s-btn" id="mtAnalyze" type="button">' +
      ic("sparkles") +
      " Tổng kết cuộc họp</button>" +
      '<button class="s-btn-ghost" id="mtNew" type="button">Cuộc họp mới</button>' +
      "</div>" +
      '<div class="mt-sum" id="mtSummary" style="margin-top:12px"></div>' +
      "</div>" +
      '<div id="mtStatus"></div>' +
      "</div>" +
      '<div id="mtPanelArchive" hidden>' +
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

  window.JavisMeetings = { render: render, roi: roi };
})();
