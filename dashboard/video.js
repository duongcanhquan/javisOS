/**
 * Công việc → Tạo video: workbench wizard full màn (không timeline).
 * Mỗi tab = một kiểu video; form gọn, lời gần gũi; phải = bước + kết quả.
 */
(function () {
  "use strict";

  var FEATURES = [
    {
      id: "postcard",
      pipeline: "postcard-video",
      label: "Promo ngắn",
      blurb: "Đẹp, ít chữ, nhạc + hiệu ứng",
      full: "Video promo ngắn",
      when: "Giới thiệu sản phẩm / app / dịch vụ trên Reels, TikTok, ads.",
      example: "Ra mắt app ghi chú → clip 30 giây dọc màn hình.",
      time: "Thường 15–45 giây",
      topicPh: "VD: Ra mắt app ghi chú cho học sinh",
      needsUrl: true,
      assetsLabel: "Link sản phẩm hoặc ảnh chụp màn hình *",
      assetsHint: "Cần link hoặc ảnh thật để làm đúng giao diện sản phẩm.",
      assetsPh: "https://… hoặc mô tả ảnh đã có",
    },
    {
      id: "short-vo",
      pipeline: "pixcelvideo",
      label: "Có lời đọc",
      blurb: "Ảnh từng cảnh + giọng nói",
      full: "Video có lời đọc",
      when: "Muốn clip giải thích hoặc bán hàng có giọng đọc sẵn (tiếng Việt).",
      example: "Máy lọc nước gia đình → 30 giây có lời thoại.",
      time: "Nhanh nếu máy đã có ChatGPT + ffmpeg",
      topicPh: "VD: Vì sao nên dùng máy lọc nước",
      needsUrl: false,
      assetsLabel: "Link / ảnh tham khảo (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Có thì dán, không có cũng được",
    },
    {
      id: "collage",
      pipeline: "paperdesign",
      label: "Collage",
      blurb: "Kiểu poster giấy, có lời",
      full: "Video collage giấy",
      when: "Thích kiểu cắt dán báo / Vox: từng cảnh một poster rồi chuyển động.",
      example: "Lạm phát là gì? → collage ~45 giây có lời kể.",
      time: "Cần key Atlas; nên duyệt kịch bản trước khi render",
      topicPh: "VD: Lạm phát giải thích ngắn",
      needsUrl: false,
      assetsLabel: "Ảnh / tài liệu (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Ảnh sản phẩm, logo…",
    },
    {
      id: "remotion",
      pipeline: "remotion",
      label: "Đồ họa",
      blurb: "Số liệu, UI, chữ chạy",
      full: "Video đồ họa chuyển động",
      when: "Cần biểu đồ, dashboard, chữ/UI chuyển động mượt.",
      example: "Tăng trưởng quý 3 → biểu đồ chuyển động 20 giây.",
      time: "Cần Node trên máy chạy Javis",
      topicPh: "VD: Số liệu tăng trưởng quý 3",
      needsUrl: false,
      assetsLabel: "Số liệu / ảnh (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Link sheet, ảnh dashboard…",
    },
    {
      id: "auto",
      pipeline: "để đạo diễn chọn",
      label: "Javis chọn",
      blurb: "Điền brief, để Javis quyết",
      full: "Để Javis chọn kiểu phù hợp",
      when: "Chưa chắc kiểu nào - điền đủ ý, Javis chọn đường làm.",
      example: "Giới thiệu quán cà phê → Javis chọn kiểu phù hợp.",
      time: "Tùy kiểu được chọn",
      topicPh: "VD: Video giới thiệu cửa hàng cà phê",
      needsUrl: false,
      assetsLabel: "Link / ảnh (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Có gì dán vào đây",
    },
  ];

  var STEPS = [
    { id: "research", label: "Tìm hiểu", agents: ["nghien-cuu-chu-de-video"] },
    { id: "script", label: "Viết kịch bản", agents: ["bien-kich-video"] },
    { id: "direct", label: "Làm video", agents: ["dao-dien-video"] },
    { id: "qa", label: "Kiểm tra", agents: ["kiem-chung-video"] },
  ];

  var FIELD_IDS = [
    "vidTopic",
    "vidGoals",
    "vidAudience",
    "vidDuration",
    "vidAspect",
    "vidLang",
    "vidChannel",
    "vidTone",
    "vidAssets",
    "vidScript",
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
    var draft = {};

    root.innerHTML =
      '<div class="jw jw-video" id="vidJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Tạo video</h2>" +
      '<p class="jw-lead">Chọn một kiểu ở hàng tab → điền vài dòng bên trái → bấm <b>Tạo video</b>. Theo dõi bước bên phải.</p></div>' +
      "</div>" +
      '<div class="jw-tabs jw-tabs-video" role="tablist" id="vidTabs"></div>' +
      '<p class="jw-tab-hint" id="vidTabHint"></p>' +
      "</div>" +
      '<div class="jw-body">' +
      '<aside class="jw-left"><div class="jw-left-scroll" id="vidLeft"></div></aside>' +
      '<section class="jw-right">' +
      '<div class="jw-right-head"><h3>Đang làm gì</h3><div class="jw-status" id="vidStatus">Chưa chạy</div></div>' +
      '<ol class="jw-steps" id="vidSteps" aria-label="Các bước làm video"></ol>' +
      '<div class="jw-out" id="vidOut">' +
      '<div class="jw-empty" id="vidEmpty">' +
      "<strong>Bắt đầu từ bên trái</strong>" +
      "Chọn tab kiểu video, ghi chủ đề và mục tiêu, rồi bấm Tạo video. " +
      "Tiến trình hiện ở đây. File xong thường nằm trong Files → attachments/videos/." +
      "</div>" +
      '<pre class="jw-log" id="vidLog" hidden></pre>' +
      "</div></section></div></div>";

    var tabsEl = root.querySelector("#vidTabs");
    FEATURES.forEach(function (f, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "jw-tab jw-tab-stack" + (i === 0 ? " on" : "");
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", i === 0 ? "true" : "false");
      b.setAttribute("data-i", String(i));
      b.innerHTML =
        '<span class="jw-tab-label">' +
        esc(f.label) +
        '</span><span class="jw-tab-blurb">' +
        esc(f.blurb) +
        "</span>";
      tabsEl.appendChild(b);
    });

    function feat() {
      return FEATURES[tabIdx] || FEATURES[0];
    }

    function paintTabHint() {
      var f = feat();
      var el = root.querySelector("#vidTabHint");
      if (!el) return;
      el.innerHTML =
        "<b>" +
        esc(f.full) +
        "</b> · " +
        esc(f.when) +
        ' <span class="dim">· ' +
        esc(f.time) +
        "</span>";
    }

    function paintSteps() {
      var ol = root.querySelector("#vidSteps");
      if (!ol) return;
      ol.innerHTML = STEPS.map(function (s, i) {
        var cls = "jw-step-item";
        if (i < stepIdx) cls += " done";
        else if (i === stepIdx) cls += " on";
        return (
          '<li class="' +
          cls +
          '"><span class="n">' +
          (i + 1) +
          "</span><span class="jw-step-lab">' +
          esc(s.label) +
          "</span></li>"
        );
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

    function saveDraft() {
      FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (el) draft[id] = el.value;
      });
    }

    function restoreDraft() {
      FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (el && draft[id] != null) el.value = draft[id];
      });
    }

    function paintLeft() {
      var f = feat();
      var left = root.querySelector("#vidLeft");
      left.innerHTML =
        '<div class="jw-brief jw-brief-lite">' +
        '<p class="jw-brief-kicker">Kiểu đang chọn</p>' +
        "<h3>" +
        esc(f.full) +
        "</h3>" +
        "<p>" +
        esc(f.when) +
        "</p>" +
        '<p class="jw-ex">Ví dụ: ' +
        esc(f.example) +
        "</p>" +
        "</div>" +
        '<p class="jw-sec">1. Bạn muốn nói gì</p>' +
        '<div class="jw-field"><label for="vidTopic">Chủ đề *</label>' +
        '<input id="vidTopic" type="text" autocomplete="off" placeholder="' +
        esc(f.topicPh) +
        '"></div>' +
        '<div class="jw-field"><label for="vidGoals">Mục tiêu *</label>' +
        '<textarea id="vidGoals" rows="2" placeholder="VD: để mọi người nhớ sản phẩm / muốn thử / hiểu một ý"></textarea></div>' +
        '<div class="jw-field"><label for="vidAudience">Người xem</label>' +
        '<input id="vidAudience" type="text" placeholder="VD: phụ huynh, chủ quán, học sinh"></div>' +
        '<p class="jw-sec">2. Hình thức</p>' +
        '<div class="jw-row2">' +
        '<div class="jw-field"><label for="vidDuration">Dài bao lâu *</label>' +
        '<select id="vidDuration">' +
        '<option value="15s">15 giây</option>' +
        '<option value="30s" selected>30 giây (gợi ý)</option>' +
        '<option value="45s">45 giây</option>' +
        '<option value="60s">60 giây</option>' +
        '<option value="90s">90 giây</option>' +
        "</select></div>" +
        '<div class="jw-field"><label for="vidAspect">Khung hình *</label>' +
        '<select id="vidAspect">' +
        '<option value="9:16" selected>Dọc điện thoại (Reels/TikTok)</option>' +
        '<option value="1:1">Vuông</option>' +
        '<option value="16:9">Ngang (YouTube)</option>' +
        "</select></div></div>" +
        '<div class="jw-row2">' +
        '<div class="jw-field"><label for="vidLang">Ngôn ngữ *</label>' +
        '<select id="vidLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
        '<div class="jw-field"><label for="vidChannel">Đăng ở đâu</label>' +
        '<input id="vidChannel" type="text" placeholder="Reels, TikTok, YouTube, Ads…"></div></div>' +
        '<div class="jw-field"><label for="vidAssets">' +
        esc(f.assetsLabel) +
        "</label>" +
        '<textarea id="vidAssets" rows="2" placeholder="' +
        esc(f.assetsPh) +
        '"></textarea>' +
        (f.assetsHint ? '<p class="jw-hint">' + esc(f.assetsHint) + "</p>" : "") +
        "</div>" +
        '<details class="jw-more">' +
        "<summary>Thêm kịch bản, tone, file (tuỳ chọn)</summary>" +
        '<div class="jw-field"><label for="vidTone">Giọng / cảm xúc</label>' +
        '<input id="vidTone" type="text" placeholder="VD: ấm áp, sạch sẽ, vui, chuyên nghiệp"></div>' +
        '<div class="jw-field"><label for="vidScript">Kịch bản sẵn có</label>' +
        '<textarea id="vidScript" rows="5" placeholder="Có outline hoặc lời thoại thì dán vào. Để trống = Javis viết giúp."></textarea></div>' +
        '<div class="jw-field"><label for="vidFiles">Đính kèm ảnh / logo / file nghe</label>' +
        '<input id="vidFiles" type="file" multiple>' +
        '<p class="jw-hint" id="vidFileList">Chưa chọn file</p></div>' +
        '<div class="jw-actions jw-actions-ghost">' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="vidSeed">Cài bộ làm video (một lần)</button>' +
        "</div></details>" +
        '<div class="jw-actions jw-actions-main">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="vidRun">Tạo video · ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="vidStop" disabled>Dừng xem</button>' +
        "</div>" +
        '<p class="jw-hint jw-hint-foot">Lần đầu có thể bấm «Cài bộ làm video» trong mục tuỳ chọn. Các lần sau cứ Tạo video.</p>';

      restoreDraft();
      wireLeft();
      paintTabHint();
    }

    function wireLeft() {
      FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (!el) return;
        el.addEventListener("change", saveDraft);
        el.addEventListener("input", saveDraft);
      });

      var filesEl = root.querySelector("#vidFiles");
      if (filesEl) {
        filesEl.onchange = async function () {
          var files = Array.from(filesEl.files || []);
          uploaded = [];
          var list = root.querySelector("#vidFileList");
          if (!files.length) {
            if (list) list.textContent = "Chưa chọn file";
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

      var stopBtn = root.querySelector("#vidStop");
      if (stopBtn) {
        stopBtn.onclick = function () {
          try {
            if (es) es.close();
          } catch (e) {}
          es = null;
          setBusy(false, "Đã dừng theo dõi (việc trên máy có thể vẫn chạy).", true);
        };
      }

      var runBtn = root.querySelector("#vidRun");
      if (runBtn) runBtn.onclick = run;

      var seedBtn = root.querySelector("#vidSeed");
      if (seedBtn) {
        seedBtn.onclick = async function () {
          if (running) return;
          seedBtn.disabled = true;
          seedBtn.textContent = "Đang cài…";
          setStatus("Đang cài bộ làm video…");
          try {
            var fd = new FormData();
            fd.append("brain", brain());
            var r = await (await fetch("/studio/seed-video", { method: "POST", body: fd })).json();
            if (!r || !r.ok) {
              setStatus((r && r.error) || "Cài chưa xong", false);
              return;
            }
            setStatus("Đã sẵn sàng. Bạn có thể bấm Tạo video.", true);
          } catch (e) {
            setStatus(String((e && e.message) || e), false);
          } finally {
            seedBtn.disabled = false;
            seedBtn.textContent = "Cài bộ làm video (một lần)";
          }
        };
      }
    }

    function selectTab(i) {
      saveDraft();
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
        runBtn.textContent = busy ? "Đang tạo…" : "Tạo video · " + f.label;
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
      saveDraft();
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
        missing.push("Link / ảnh sản phẩm");
      }
      if (missing.length) {
        setStatus("Thiếu: " + missing.join(", ") + ". Điền bên trái rồi bấm Tạo video.", false);
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

    async function run() {
      if (running) return;
      var v = validateInputs();
      if (!v) return;

      var f = v.feat;
      var brief = composeBrief(v);

      stepIdx = 0;
      paintSteps();
      setBusy(true, "Đang tạo «" + f.full + "»…");
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
            finishBusy("Xong. Xem Files → attachments/videos/ (hoặc đường dẫn trong log).", true);
          } else {
            appendLog(ev.data);
          }
        } catch (eParse) {
          appendLog(ev.data);
        }
      };
      es.onerror = function () {
        finishBusy("Mất kết nối (có thể đã xong hoặc lỗi). Xem log bên dưới.", false);
      };
    }

    paintSteps();
    paintLeft();
  };
})();
