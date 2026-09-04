// Trang Cuộc họp — ghi chú → Bắt đầu → nhận diện người nói → Tổng kết (Ollama).
// Nạp TRƯỚC console.js; console gọi window.JavisMeetings.render(el).
(function () {
  "use strict";

  var CDN = "https://cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm@0.1.5/dist/index.js";
  var state = {
    meetingId: null,
    path: "",
    mic: null,
    running: false,
    stopped: false,
    loading: false,
    ws: null,
    lines: 0,
    speakers: {}, // index -> name
  };

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

  async function loadMoonshine(root) {
    setStatus(root, "Đang tải Moonshine WASM (lần đầu có thể tải model tiếng Việt)…");
    var mod = await import(/* webpackIgnore: true */ CDN);
    return mod.MicTranscriber;
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
    seedSpeakersFromInput(root);
    var startBtn = root.querySelector("#mtStart");
    if (startBtn) startBtn.disabled = true;
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
      state.meetingId = r.id;
      state.path = r.path || "";
      state.lines = 0;
      var pathEl = root.querySelector("#mtPath");
      if (pathEl) pathEl.textContent = r.path || "";
      var countEl = root.querySelector("#mtCount");
      if (countEl) countEl.textContent = "0";
      root.querySelector("#mtLines").innerHTML =
        '<div class="mt-empty dim">Đang nghe… mỗi câu sẽ ghi vào file transcript.</div>';
      root.querySelector("#mtSummary").innerHTML = "";
      refreshSpeakerBar(root);
      setPhase(root, "live");

      var MicTranscriber = await loadMoonshine(root);
      var mic = new MicTranscriber()
        .language("vi")
        .onProgress(function (frac) {
          setStatus(root, "Tải model tiếng Việt… " + Math.round((frac || 0) * 100) + "%");
        })
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
          sendLine(tx, t0, t1, who, idx);
        })
        .onError(function (err) {
          setStatus(root, "Moonshine: " + ((err && err.message) || err), "err");
        });

      setStatus(root, "Nạp model…");
      await mic.load();
      setStatus(root, "Xin quyền micro…");
      await mic.start();
      state.mic = mic;
      state.running = true;
      var stopBtn = root.querySelector("#mtStop");
      if (stopBtn) stopBtn.disabled = false;
      setStatus(root, "Đang ghi vào file. Nói rõ; hệ thống gắn nhãn người nói khi phân biệt được.", "ok");
      await ensureWs();
    } catch (e) {
      setStatus(root, "Không bắt đầu được: " + (e.message || e), "err");
      if (startBtn) startBtn.disabled = false;
      state.meetingId = null;
      setPhase(root, "setup");
    } finally {
      state.loading = false;
    }
  }

  async function stopRecording(root) {
    if (!state.meetingId) return;
    var stopBtn = root.querySelector("#mtStop");
    if (stopBtn) stopBtn.disabled = true;
    try {
      if (state.mic) {
        try {
          await state.mic.stop();
        } catch (e) {}
        try {
          state.mic.close();
        } catch (e) {}
        state.mic = null;
      }
      state.running = false;
      setPartial(root, "");
      var f = new FormData();
      f.append("brain", fbrain());
      var r = await (
        await fetch("/meetings/" + encodeURIComponent(state.meetingId) + "/stop", {
          method: "POST",
          body: f,
        })
      ).json();
      if (!r.ok) throw new Error(r.error || "Dừng lỗi");
      state.stopped = true;
      setPhase(root, "stopped");
      setStatus(
        root,
        "Đã dừng ghi · " +
          (r.line_count || 0) +
          " đoạn · " +
          (r.path || "") +
          " — bấm Tổng kết cuộc họp.",
        "ok"
      );
    } catch (e) {
      setStatus(root, "Dừng lỗi: " + (e.message || e), "err");
      if (stopBtn) stopBtn.disabled = false;
    } finally {
      if (state.ws) {
        try {
          state.ws.close();
        } catch (e) {}
        state.ws = null;
      }
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
    setStatus(root, "Đang tổng kết bằng Ollama (qwen3:4b)… có thể mất 1–2 phút.");
    var box = root.querySelector("#mtSummary");
    if (box) box.innerHTML = '<div class="dim">Trợ lý đang đọc transcript và viết tổng kết…</div>';
    var btn = root.querySelector("#mtAnalyze");
    if (btn) btn.disabled = true;
    try {
      var f = new FormData();
      f.append("brain", fbrain());
      f.append("model", "qwen3:4b");
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

  async function refreshList(root) {
    var el = root.querySelector("#mtRecent");
    if (!el) return;
    try {
      var r = await (
        await fetch("/meetings/list?brain=" + encodeURIComponent(fbrain()) + "&limit=15")
      ).json();
      var items = r.items || [];
      if (!items.length) {
        el.innerHTML = '<div class="dim">Chưa có file cuộc họp.</div>';
        return;
      }
      el.innerHTML = items
        .map(function (it) {
          return (
            '<div class="mt-recent-row"><span class="mt-kind">' +
            esc(it.kind) +
            "</span> <code>" +
            esc(it.path) +
            "</code></div>"
          );
        })
        .join("");
    } catch (e) {
      el.innerHTML = '<div class="dim">Không tải danh sách.</div>';
    }
  }

  function injectCss() {
    if (document.getElementById("mt-css")) return;
    var s = document.createElement("style");
    s.id = "mt-css";
    s.textContent =
      ".mt-wrap{max-width:780px}" +
      ".mt-hero{margin:0 0 16px}" +
      ".mt-hero h2{margin:0 0 6px;font-size:22px;color:var(--text)}" +
      ".mt-hint{font-size:14px;color:var(--text3);line-height:1.6;margin:0 0 14px;max-width:640px}" +
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
      ".mt-recent-row{font-size:13px;margin:4px 0;color:var(--text2)}.mt-kind{display:inline-block;min-width:72px;color:var(--text3)}" +
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
      '<p class="mt-hint">Ghi chú thông tin → Bắt đầu (micro trên máy bạn) → hệ thống ghi chữ vào file và gắn nhãn người nói → Dừng ghi → <b>Tổng kết cuộc họp</b> bằng Ollama <code>qwen3:4b</code> (ý kiến, đề xuất, quyết định). VPS cũng có <code>llama3.2:3b</code>.</p>' +
      '<div class="mt-steps"><span>1. Ghi chú</span><span>2. Bắt đầu ghi</span><span>3. Dừng</span><span>4. Tổng kết</span></div>' +
      "</div>" +
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
      '<label class="s-btn-ghost" style="cursor:pointer;display:inline-flex;align-items:center;gap:6px">' +
      ic("upload-cloud") +
      ' Tải file ghi âm<input type="file" id="mtFile" accept="audio/*,.mp3,.wav,.m4a,.ogg,.webm" hidden></label>' +
      "</div></div>" +
      '<div id="mtLivePanel" hidden>' +
      '<div class="mt-meta"><span>File: <code id="mtPath">—</code></span><span>Đoạn: <b id="mtCount">0</b></span></div>' +
      '<div id="mtSpeakers" style="margin:8px 0 10px"></div>' +
      '<div class="mt-live" id="mtLines"><div class="mt-empty dim">Chưa có dòng nào.</div></div>' +
      '<div class="mt-partial" id="mtPartial"></div>' +
      '<div class="mt-toolbar" style="margin-top:12px">' +
      '<button class="s-btn-ghost" id="mtStop" type="button">' +
      ic("circle-stop") +
      " Dừng ghi</button>" +
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
      '<div class="si-log" style="margin-top:22px"><h3 style="font-size:15px;color:var(--text)">File cuộc họp gần đây</h3><div id="mtRecent">Đang tải…</div></div>' +
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

    setPhase(el, "setup");
    refreshList(el);
    setStatus(el, "Điền thông tin rồi bấm Bắt đầu cuộc họp.");
  }

  function roi() {
    if (state.mic) {
      try {
        state.mic.stop();
      } catch (e) {}
      try {
        state.mic.close();
      } catch (e) {}
      state.mic = null;
      state.running = false;
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
