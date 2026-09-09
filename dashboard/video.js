/**
 * Công việc → Tạo video: workbench wizard (không timeline).
 * Tab = pipeline; trái = brief + kịch bản; phải = bước + log SSE.
 */
(function () {
  "use strict";

  var FEATURES = [
    {
      id: "postcard",
      pipeline: "postcard-video",
      label: "Postcard",
      full: "Postcard video (cinematic)",
      tagline: "Promo ngắn · shot Remotion · SFX/BGM",
      when: "Teaser / launch / demo UI 15-45s, muốn motion đẹp kiểu shotcraft.",
      gets: ["Brief → nghiên cứu → beat", "Pipeline postcard-video", "mp4 hoặc pack thiếu môi trường"],
      example: "«App ghi chú mới» → postcard 30s 9:16, SFX + BGM.",
      time: "Kịch bản nhanh; render Remotion lâu hơn",
      topicPh: "VD: Ra mắt app ghi chú cho học sinh",
      needsUrl: true,
    },
    {
      id: "short-vo",
      pipeline: "pixcelvideo",
      label: "Short + VO",
      full: "Short có ảnh và giọng đọc",
      tagline: "Topic → ảnh AI + TTS → mp4",
      when: "Cần clip giải thích / bán hàng có lời đọc tiếng Việt sẵn.",
      gets: ["Kịch bản từng cảnh", "Ảnh + Edge-TTS", "mp4 ghép ffmpeg"],
      example: "«Máy lọc nước gia đình» → 30s 9:16 có VO.",
      time: "~vài phút nếu đủ ChatGPT + ffmpeg",
      topicPh: "VD: Vì sao nên dùng máy lọc nước",
    },
    {
      id: "collage",
      pipeline: "paperdesign",
      label: "Collage",
      full: "Collage giấy (Vox / paperdesign)",
      tagline: "Poster xé giấy · motion · VO",
      when: "Explainer / ads kiểu collage editorial, có Atlas key.",
      gets: ["Beat + style", "Poster + motion", "VO + nhạc → mp4"],
      example: "«Lạm phát là gì?» → collage 45s có narration.",
      time: "Tốn Atlas; cần duyệt beat trước gen",
      topicPh: "VD: Lạm phát giải thích 60 giây",
    },
    {
      id: "remotion",
      pipeline: "remotion",
      label: "Remotion",
      full: "Remotion (React motion)",
      tagline: "Data viz · UI motion · caption",
      when: "Cần composition React/Remotion tùy biến, không bắt buộc shotcraft.",
      gets: ["Storyboard", "Composition Remotion", "Render mp4 (cần Node)"],
      example: "«Dashboard tăng trưởng Q3» → chart motion 20s.",
      time: "Cần Node + project Remotion",
      topicPh: "VD: Số liệu tăng trưởng quý 3",
    },
    {
      id: "auto",
      pipeline: "để đạo diễn chọn",
      label: "Tự chọn",
      full: "Để đạo diễn chọn pipeline",
      tagline: "Javis chọn theo brief",
      when: "Chưa chắc loại nào - để agent chọn trong catalog lam-video.",
      gets: ["Nghiên cứu + kịch bản", "1 pipeline phù hợp", "Output hoặc thiếu sót rõ"],
      example: "Brief đủ 5 mục → đạo diễn chọn pixcel/postcard/…",
      time: "Tùy pipeline được chọn",
      topicPh: "VD: Video giới thiệu cửa hàng cà phê",
    },
  ];

  var STEPS = [
    { id: "research", label: "Nghiên cứu", agents: ["nghien-cuu-chu-de-video"] },
    { id: "script", label: "Kịch bản", agents: ["bien-kich-video"] },
    { id: "direct", label: "Làm video", agents: ["dao-dien-video"] },
    { id: "qa", label: "Kiểm chứng", agents: ["kiem-chung-video"] },
  ];

  function brain() {
    try {
      if (typeof window.currentBrainPath === "function") return window.currentBrainPath() || "brain";
      return "brain";
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

  function composeBrief(v) {
    var f = v.feat;
    var parts = [
      "Chủ đề: " + v.topic,
      "Mục tiêu: " + (v.goals || "(chưa ghi)"),
      "Audience: " + (v.audience || "(chưa ghi)"),
      "Độ dài: " + (v.duration || "30s"),
      "Tỉ lệ: " + (v.aspect || "9:16"),
      "Ngôn ngữ VO + chữ trên hình: " + (v.lang || "vi"),
      "Kênh: " + (v.channel || "(chưa ghi)"),
      "Pipeline: " + (f.pipeline || "để đạo diễn chọn"),
      "Tone / vibe: " + (v.tone || "(chưa ghi)"),
    ];
    if (v.assets) parts.push("Tài sản / URL: " + v.assets);
    if (v.script) parts.push("Kịch bản / beat dán sẵn:\n" + v.script);
    if (v.files && v.files.length) parts.push("File đính kèm:\n- " + v.files.join("\n- "));
    parts.push(
      "Yêu cầu UI Tạo video: làm đúng pipeline đã chọn; thiếu môi trường thì nói rõ và đưa Manual pack, không hứa suông."
    );
    return parts.join("\n");
  }

  function formatLogLine(raw) {
    var s = String(raw == null ? "" : raw);
    if (/^#{1,3}\s/.test(s.trim())) {
      return '<span class="jw-h">' + esc(s.trim().replace(/^#+\s*/, "")) + "</span>";
    }
    if (/^\[(step|status|step_start|xong bước|step_done)/i.test(s.trim())) {
      return '<span class="jw-step">' + esc(s) + "</span>";
    }
    return esc(s);
  }

  function agentToStep(agent) {
    var a = String(agent || "").toLowerCase();
    for (var i = 0; i < STEPS.length; i++) {
      for (var j = 0; j < STEPS[i].agents.length; j++) {
        if (a.indexOf(STEPS[i].agents[j]) >= 0) return i;
      }
    }
    return -1;
  }

  window.renderTaoVideo = function (root) {
    if (!root) return;
    var uploaded = [];
    var es = null;
    var tabIdx = 0;
    var running = false;
    var stepIdx = -1;

    root.innerHTML =
      '<div class="jw" id="vidJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Tạo video</h2>" +
      '<p class="jw-lead">Chọn loại, điền brief và kịch bản. Trái: form. Phải: bước chạy + kết quả. Không cần timeline kéo-thả.</p></div>' +
      '<div class="jw-top-actions">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="vidSeed">Chuẩn bị lần đầu</button>' +
      "</div></div>" +
      '<div class="jw-tabs" role="tablist" id="vidTabs"></div>' +
      "</div>" +
      '<div class="jw-body">' +
      '<aside class="jw-left"><div class="jw-left-scroll" id="vidLeft"></div></aside>' +
      '<section class="jw-right">' +
      '<div class="jw-right-head"><h3>Tiến độ & kết quả</h3><div class="jw-status" id="vidStatus">Chưa chạy</div></div>' +
      '<ol class="jw-steps" id="vidSteps" aria-label="Các bước pipeline"></ol>' +
      '<div class="jw-out" id="vidOut">' +
      '<div class="jw-empty" id="vidEmpty"><strong>Sẵn sàng tạo</strong>Chọn tab, điền chủ đề + mục tiêu, bấm Chạy. Log và bước hiện tại đây. mp4 thường ở attachments/videos/ hoặc out/ (Files).</div>' +
      '<pre class="jw-log" id="vidLog" hidden></pre>' +
      "</div></section></div></div>";

    var tabsEl = root.querySelector("#vidTabs");
    FEATURES.forEach(function (f, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "jw-tab" + (i === 0 ? " on" : "");
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", i === 0 ? "true" : "false");
      b.setAttribute("data-i", String(i));
      b.textContent = f.label;
      tabsEl.appendChild(b);
    });

    function feat() {
      return FEATURES[tabIdx] || FEATURES[0];
    }

    function paintSteps() {
      var ol = root.querySelector("#vidSteps");
      if (!ol) return;
      ol.innerHTML = STEPS.map(function (s, i) {
        var cls = "jw-step-item";
        if (i < stepIdx) cls += " done";
        else if (i === stepIdx) cls += " on";
        return '<li class="' + cls + '"><span class="n">' + (i + 1) + "</span> " + esc(s.label) + "</li>";
      }).join("");
    }

    function setStatus(msg, kind) {
      var el = root.querySelector("#vidStatus");
      if (!el) return;
      el.textContent = msg || "";
      el.className = "jw-status" + (kind === false ? " err" : kind === true ? " ok" : "");
    }

    function showLog() {
      var empty = root.querySelector("#vidEmpty");
      var log = root.querySelector("#vidLog");
      if (empty) empty.hidden = true;
      if (log) log.hidden = false;
    }

    function appendLog(line) {
      showLog();
      var log = root.querySelector("#vidLog");
      if (!log) return;
      log.innerHTML += formatLogLine(line) + "\n";
      var out = root.querySelector("#vidOut");
      if (out) out.scrollTop = out.scrollHeight;
    }

    function advanceStep(agent) {
      var i = agentToStep(agent);
      if (i >= 0 && i !== stepIdx) {
        stepIdx = i;
        paintSteps();
      }
    }

    function paintLeft() {
      var f = feat();
      var gets = (f.gets || [])
        .map(function (g) {
          return "<li>" + esc(g) + "</li>";
        })
        .join("");
      var left = root.querySelector("#vidLeft");
      left.innerHTML =
        '<div class="jw-brief">' +
        '<p class="jw-brief-kicker">Loại video đang chọn</p>' +
        "<h3>" +
        esc(f.full) +
        "</h3>" +
        "<p><b>Chọn khi:</b> " +
        esc(f.when) +
        "</p>" +
        "<ul>" +
        gets +
        "</ul>" +
        '<p class="jw-ex"><b>Ví dụ:</b> ' +
        esc(f.example) +
        "</p>" +
        '<div class="jw-meta"><span class="jw-chip">' +
        esc(f.time) +
        '</span><span class="jw-chip">' +
        esc(f.tagline) +
        "</span></div></div>" +
        '<div class="jw-field"><label for="vidTopic">Chủ đề *</label>' +
        '<input id="vidTopic" type="text" autocomplete="off" placeholder="' +
        esc(f.topicPh) +
        '"></div>' +
        '<div class="jw-field"><label for="vidGoals">Mục tiêu *</label>' +
        '<textarea id="vidGoals" rows="2" placeholder="VD: nhận diện thương hiệu / bán / giải thích"></textarea></div>' +
        '<div class="jw-field"><label for="vidAudience">Đối tượng</label>' +
        '<input id="vidAudience" type="text" placeholder="VD: phụ huynh, SME, Gen Z"></div>' +
        '<div class="jw-row2">' +
        '<div class="jw-field"><label for="vidDuration">Độ dài *</label>' +
        '<select id="vidDuration">' +
        '<option value="15s">15 giây</option>' +
        '<option value="30s" selected>30 giây</option>' +
        '<option value="45s">45 giây</option>' +
        '<option value="60s">60 giây</option>' +
        '<option value="90s">90 giây</option>' +
        "</select></div>" +
        '<div class="jw-field"><label for="vidAspect">Tỉ lệ *</label>' +
        '<select id="vidAspect">' +
        '<option value="9:16" selected>9:16 Reels/TikTok</option>' +
        '<option value="1:1">1:1 vuông</option>' +
        '<option value="16:9">16:9 YouTube</option>' +
        "</select></div></div>" +
        '<div class="jw-row2">' +
        '<div class="jw-field"><label for="vidLang">Ngôn ngữ *</label>' +
        '<select id="vidLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
        '<div class="jw-field"><label for="vidChannel">Kênh</label>' +
        '<input id="vidChannel" type="text" placeholder="Reels / Ads / YouTube"></div></div>' +
        '<div class="jw-field"><label for="vidTone">Tone / vibe</label>' +
        '<input id="vidTone" type="text" placeholder="cinematic, sạch, vui,…"></div>' +
        '<div class="jw-field"><label for="vidAssets">URL / tài sản' +
        (f.needsUrl ? " *" : "") +
        "</label>" +
        '<textarea id="vidAssets" rows="2" placeholder="URL sản phẩm, staging, hoặc mô tả ảnh/screenshot sẵn"></textarea>' +
        (f.needsUrl
          ? '<p class="jw-hint">Postcard cần URL hoặc screenshot thật - không bịa UI.</p>'
          : "") +
        "</div>" +
        '<div class="jw-field"><label for="vidScript">Kịch bản / beat (tuỳ chọn)</label>' +
        '<textarea id="vidScript" rows="6" placeholder="Dán beat/shot hoặc outline. Để trống = agent viết sau bước nghiên cứu."></textarea>' +
        '<p class="jw-hint">Có sẵn kịch bản thì dán đây để bỏ qua viết lại từ đầu.</p></div>' +
        '<div class="jw-field"><label for="vidFiles">File đính kèm</label>' +
        '<input id="vidFiles" type="file" multiple>' +
        '<p class="jw-hint" id="vidFileList">Ảnh SP, logo, VO… (tuỳ chọn)</p></div>' +
        '<div class="jw-actions">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="vidRun">Chạy: ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="vidStop" disabled>Dừng xem</button>' +
        "</div>";

      wireLeft();
    }

    function wireLeft() {
      var filesEl = root.querySelector("#vidFiles");
      if (filesEl) {
        filesEl.onchange = async function () {
          var files = Array.from(filesEl.files || []);
          uploaded = [];
          var list = root.querySelector("#vidFileList");
          if (!files.length) {
            if (list) list.textContent = "Ảnh SP, logo, VO… (tuỳ chọn)";
            return;
          }
          if (list) list.textContent = "Đang tải…";
          for (var i = 0; i < files.length; i++) {
            var fd = new FormData();
            fd.append("file", files[i]);
            fd.append("brain", brain());
            try {
              var r = await (await fetch("/upload", { method: "POST", body: fd })).json();
              if (r && (r.path || r.name)) uploaded.push(r.path || r.name);
              else if (r && r.error) appendLog("Upload lỗi: " + r.error);
            } catch (e) {
              appendLog("Upload lỗi: " + ((e && e.message) || e));
            }
          }
          if (list) {
            list.textContent = uploaded.length
              ? "Đã tải: " + uploaded.join(", ")
              : "Không tải được file.";
          }
        };
      }

      root.querySelector("#vidStop").onclick = function () {
        try {
          if (es) es.close();
        } catch (e) {}
        es = null;
        setBusy(false, "Đã dừng theo dõi (việc trên server có thể vẫn chạy).", true);
      };

      root.querySelector("#vidRun").onclick = run;
    }

    function selectTab(i) {
      tabIdx = i;
      tabsEl.querySelectorAll(".jw-tab").forEach(function (btn, j) {
        var on = j === i;
        btn.classList.toggle("on", on);
        btn.setAttribute("aria-selected", on ? "true" : "false");
      });
      paintLeft();
    }

    function clearFieldErrors() {
      root.querySelectorAll(".jw-field.err").forEach(function (w) {
        w.classList.remove("err");
      });
    }

    function markField(id, bad) {
      var el = root.querySelector("#" + id);
      if (!el) return;
      var wrap = el.closest(".jw-field");
      if (wrap) wrap.classList.toggle("err", !!bad);
      if (bad) {
        try {
          el.focus();
        } catch (e) {}
      }
    }

    function setBusy(busy, statusMsg, statusOk) {
      running = !!busy;
      var f = feat();
      var runBtn = root.querySelector("#vidRun");
      var stopBtn = root.querySelector("#vidStop");
      var seedBtn = root.querySelector("#vidSeed");
      if (runBtn) {
        runBtn.disabled = busy;
        runBtn.classList.toggle("jw-busy", busy);
        runBtn.textContent = busy ? "Đang chạy…" : "Chạy: " + f.label;
      }
      if (stopBtn) stopBtn.disabled = !busy;
      if (seedBtn) seedBtn.disabled = busy;
      tabsEl.querySelectorAll(".jw-tab").forEach(function (t) {
        t.disabled = busy;
      });
      if (statusMsg != null) setStatus(statusMsg, statusOk);
    }

    function validateInputs() {
      clearFieldErrors();
      var f = feat();
      var topic = ((root.querySelector("#vidTopic") || {}).value || "").trim();
      var goals = ((root.querySelector("#vidGoals") || {}).value || "").trim();
      var assets = ((root.querySelector("#vidAssets") || {}).value || "").trim();
      var missing = [];
      if (!topic) {
        markField("vidTopic", true);
        missing.push("Chủ đề");
      }
      if (!goals) {
        markField("vidGoals", true);
        missing.push("Mục tiêu");
      }
      if (f.needsUrl && !assets) {
        markField("vidAssets", true);
        missing.push("URL / tài sản");
      }
      if (missing.length) {
        setStatus("Thiếu: " + missing.join(", ") + ". Điền bên trái rồi bấm Chạy.", false);
        return null;
      }
      return {
        topic: topic,
        goals: goals,
        audience: ((root.querySelector("#vidAudience") || {}).value || "").trim(),
        duration: ((root.querySelector("#vidDuration") || {}).value || "30s").trim(),
        aspect: ((root.querySelector("#vidAspect") || {}).value || "9:16").trim(),
        lang: ((root.querySelector("#vidLang") || {}).value || "vi").trim(),
        channel: ((root.querySelector("#vidChannel") || {}).value || "").trim(),
        tone: ((root.querySelector("#vidTone") || {}).value || "").trim(),
        assets: assets,
        script: ((root.querySelector("#vidScript") || {}).value || "").trim(),
        files: uploaded.slice(),
        feat: f,
      };
    }

    function finishBusy(statusMsg, statusOk) {
      try {
        if (es) es.close();
      } catch (e) {}
      es = null;
      if (statusOk) {
        stepIdx = STEPS.length - 1;
        paintSteps();
      }
      setBusy(false, statusMsg, statusOk);
    }

    tabsEl.querySelectorAll(".jw-tab").forEach(function (btn) {
      btn.onclick = function () {
        if (running) {
          setStatus("Đang chạy - chờ xong hoặc bấm Dừng xem trước khi đổi tab.", false);
          return;
        }
        selectTab(parseInt(btn.getAttribute("data-i"), 10) || 0);
      };
    });

    root.querySelector("#vidSeed").onclick = async function () {
      if (running) return;
      var seedBtn = root.querySelector("#vidSeed");
      if (seedBtn) {
        seedBtn.disabled = true;
        seedBtn.textContent = "Đang chuẩn bị…";
      }
      setStatus("Đang chuẩn bị agent + workflow Bộ Video…");
      try {
        var fd = new FormData();
        fd.append("brain", brain());
        var r = await (await fetch("/studio/seed-video", { method: "POST", body: fd })).json();
        if (!r || !r.ok) {
          setStatus((r && r.error) || "Chuẩn bị thất bại", false);
          return;
        }
        setStatus("Sẵn sàng workflow " + (r.workflow || "bo-video-da-pipeline") + ".", true);
      } catch (e) {
        setStatus(String((e && e.message) || e), false);
      } finally {
        if (seedBtn) {
          seedBtn.disabled = false;
          seedBtn.textContent = "Chuẩn bị lần đầu";
        }
      }
    };

    async function run() {
      if (running) return;
      var v = validateInputs();
      if (!v) return;

      var f = v.feat;
      var brief = composeBrief(v);

      stepIdx = 0;
      paintSteps();
      setBusy(true, "Đang chạy «" + f.full + "»…");
      if (es) {
        try {
          es.close();
        } catch (e1) {}
        es = null;
      }
      var log = root.querySelector("#vidLog");
      if (log) log.innerHTML = "";
      appendLog("--- Brief ---\n" + brief + "\n---");

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        await fetch("/studio/seed-video", { method: "POST", body: fd0 });
      } catch (e0) {}

      var url =
        "/workflows/run?slug=" +
        encodeURIComponent("bo-video-da-pipeline") +
        "&brain=" +
        encodeURIComponent(brain()) +
        "&input=" +
        encodeURIComponent(brief);
      es = new EventSource(url);
      es.onmessage = function (ev) {
        try {
          var data = JSON.parse(ev.data);
          var typ = data.type || "";
          if (typ === "token" || typ === "text" || typ === "chunk") {
            appendLog(data.text || data.token || data.content || "");
          } else if (typ === "step" || typ === "status" || typ === "step_start") {
            advanceStep(data.agent || data.message || "");
            appendLog(
              "[" + typ + "] " + (data.message || data.agent || data.step || JSON.stringify(data))
            );
          } else if (typ === "step_done") {
            advanceStep(data.agent || "");
            appendLog("[xong bước] " + (data.agent || ""));
            if (data.output) {
              var out = String(data.output);
              appendLog(out.length > 5000 ? out.slice(0, 5000) + "\n…(cắt)" : out);
            }
          } else if (typ === "error") {
            appendLog("ERROR: " + (data.message || data.error || ev.data));
            finishBusy("Lỗi khi tạo video", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 8000 ? res.slice(0, 8000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            finishBusy("Xong. Xem log + Files (attachments/videos hoặc out/).", true);
          } else {
            appendLog(ev.data);
          }
        } catch (eParse) {
          appendLog(ev.data);
        }
      };
      es.onerror = function () {
        finishBusy("Mất kết nối stream (có thể đã xong hoặc lỗi).", false);
      };
    }

    paintSteps();
    paintLeft();
  };
})();
