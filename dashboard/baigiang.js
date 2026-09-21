/**
 * Công việc → Bài giảng: workbench full màn.
 * Trái = chọn tab đầu ra + brief/input; phải = kết quả chạy.
 */
(function () {
  "use strict";

  var FORMATS = [
    {
      id: "lop-hoc",
      slug: "bo-bai-giang-lop-hoc",
      label: "Lớp học",
      blurb: "OpenMAIC · quiz · thực hành",
      full: "Lớp học tương tác",
      tagline: "Cảnh · quiz · thực hành",
      when: "Dạy live: kịch bản cả buổi rồi tạo classroom OpenMAIC ngay trong VMOS.",
      gets: ["Outline 8-15 cảnh", "Quiz + PBL ngắn", "Tạo lớp OpenMAIC trong khung Kết quả"],
      example: "«Biến trong Python» → mở → demo → mini-lab → quiz → tổng kết.",
      time: "~20-40 phút",
      topicPh: "VD: Nhập môn biến trong Python",
    },
    {
      id: "slide",
      slug: "bo-bai-giang-slide",
      label: "Slide",
      blurb: "Deck dạy / seminar",
      full: "Slide trình chiếu",
      tagline: "Dạy trên lớp / seminar",
      when: "Cần chiếu máy chiếu hoặc gửi trước cho học viên. Ít chữ, có gợi ý hình.",
      gets: ["Deck HTML đẹp (theme + preview)", "Outline + speaker notes", "Gợi ý ảnh / biểu đồ"],
      example: "«Quang hợp lớp 8» → hook → 3 bước → ví dụ → quiz → tóm tắt.",
      time: "~10-20 phút",
      topicPh: "VD: Quang hợp cho học sinh lớp 8",
    },
    {
      id: "van-ban",
      slug: "bo-bai-giang-van-ban",
      label: "Bài đọc",
      blurb: "Handout + ảnh / biểu đồ",
      full: "Bài đọc minh họa",
      tagline: "Handout / đọc trước",
      when: "Cần tài liệu chữ rõ, có chỗ ảnh/biểu đồ, học viên đọc một mình được.",
      gets: ["Longread 1200-2000 chữ", "Chỗ [ẢNH]/[BIỂU ĐỒ]", "Ví dụ + bài luyện"],
      example: "«An toàn mạng» → 5 mục + bảng so sánh + checklist mang về.",
      time: "~15-25 phút",
      topicPh: "VD: An toàn mạng cho học sinh",
    },
    {
      id: "video",
      slug: "bo-bai-giang-video",
      label: "Video bài giảng",
      blurb: "Clip giáo dục 60-90s",
      full: "Video bài giảng (giải thích)",
      tagline: "Clip xem lại / Zalo / LMS",
      when: "Giải thích một ý khó để học viên xem trước hoặc ôn  -  không phải video marketing.",
      gets: ["Beat giảng (hook → giải thích → ví dụ)", "Gói render / pack thủ công", "Độ dài gợi ý 60-90s"],
      example: "«Vì sao trời xanh?» → clip ~75 giây, kết luận 1 câu dễ nhớ.",
      time: "Kịch bản nhanh; render lâu hơn",
      topicPh: "VD: Vì sao trời xanh?",
      crossLink: "video",
      crossText: "Cần promo / Reels / có lời đọc marketing → Công việc · Tạo video",
    },
  ];

  var BG_FIELD_IDS = ["bgTopic", "bgAudience", "bgGoals", "bgPaste", "bgLang"];

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

  var OM_FALLBACK_URL = "https://openmaic.vietmycollege.com";

  /** Lệnh handoff (advanced). API OpenMAIC chỉ nhận en-US|zh-CN  -  dùng en-US + nội dung VI. */
  function buildOpenmaicHandoff(opts) {
    opts = opts || {};
    var pub = opts.publicUrl || OM_FALLBACK_URL;
    var topic = opts.topic || "(chưa ghi chủ đề)";
    var goals = opts.goals || "";
    var paste = opts.paste || "";
    var slugHint = opts.slugHint || "exports/bai-giang/<slug>/lop-hoc.md";
    var lines = [
      "Trong VMOS: Việc → Bài giảng → Lớp học → bấm «Tạo lớp OpenMAIC» (không mở domain riêng / Live Demo).",
      "Server tự gọi OpenMAIC với language=en-US + script tiếng Việt + TTS Edge.",
      "",
      "Nếu generate thủ công (debug):",
      "URL public: " + pub,
      "path: " + slugHint,
      "Chủ đề: " + topic,
    ];
    if (goals) lines.push("Mục tiêu: " + goals);
    lines.push(
      "language=en-US (bắt buộc API; nội dung requirement/script vẫn tiếng Việt). CẤM zh-CN. CẤM language=vi (fallback zh)."
    );
    lines.push("TTS: OpenAI/Edge (nova/alloy); CẤM Browser Native / Doubao / Qwen / zh-*.");
    if (paste) {
      lines.push("");
      lines.push("--- Nội dung / giáo án dán ---");
      lines.push(paste);
    }
    return lines.join("\n");
  }

  function composeBrief(topic, audience, goals, lang, fmt, files, paste) {
    var parts = [
      "Chủ đề: " + topic,
      "Đối tượng: " + (audience || "học viên phổ thông / mới bắt đầu"),
      "Mục tiêu học: " + (goals || "(chưa ghi - agent sẽ hỏi nếu thiếu)"),
      "Ngôn ngữ: " + (lang || "vi"),
      "Định dạng đầu ra: " + (fmt ? fmt.full : ""),
    ];
    if (fmt) {
      parts.push("Mô tả định dạng: " + fmt.tagline);
      parts.push("Ví dụ tham chiếu: " + fmt.example);
    }
    if (paste && String(paste).trim()) {
      parts.push("Nội dung / giáo án dán sẵn:\n" + String(paste).trim());
    }
    if (files && files.length) parts.push("File đính kèm:\n- " + files.join("\n- "));
    if (fmt && fmt.id === "lop-hoc") {
      parts.push(
        "Sau khi ghi exports/bai-giang/<slug>/lop-hoc.md: hướng dẫn user bấm «Tạo lớp OpenMAIC» NGAY TRONG VMOS (không mở domain OpenMAIC, không Live Demo)."
      );
      parts.push(
        "Script/quiz tiếng Việt dấu đủ. OpenMAIC API dùng language=en-US + TTS Edge (tránh fallback zh-CN)."
      );
    }
    return parts.join("\n");
  }

  function slugifyTopic(topic) {
    var s = String(topic || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return s || "bai-giang";
  }

  function extractLopHocPath(text, topic) {
    var blob = String(text || "");
    var m = blob.match(/exports\/bai-giang\/[^\s"'<>\\]+\/lop-hoc\.md/i);
    if (m) return m[0].replace(/\\/g, "/");
    if (topic) return "exports/bai-giang/" + slugifyTopic(topic) + "/lop-hoc.md";
    return "";
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

  window.renderBaiGiang = function (root) {
    if (!root) return;
    var uploaded = [];
    var es = null;
    var tabIdx = 0;
    var running = false;
    var runFinished = false;
    var lastLopHocPath = "";
    var lastTopic = "";
    var omPollTimer = null;
    var omGenerating = false;
    var draft = {};
    var lastOmThin = false;
    var cachedPublicUrl = "";

    root.innerHTML =
      '<div class="jw" id="bgJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Bài giảng</h2>" +
      '<p class="jw-lead">Chọn loại đầu ra · điền brief · Chạy. <b>Lớp học</b> tạo classroom OpenMAIC trong khung Kết quả (không mở domain riêng). Video marketing → <button type="button" class="jw-link" id="bgGotoVideo">Tạo video</button>.</p></div>' +
      '<div class="jw-top-actions">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="bgSeed">Chuẩn bị lần đầu</button>' +
      "</div></div>" +
      '<div class="jw-tabs jw-tabs-stack" role="tablist" id="bgTabs"></div>' +
      '<p class="jw-tab-hint" id="bgTabHint"></p>' +
      "</div>" +
      '<div class="jw-body">' +
      '<aside class="jw-left"><div class="jw-left-scroll" id="bgLeft"></div></aside>' +
      '<section class="jw-right">' +
      '<div class="jw-right-head"><h3>Kết quả</h3><div class="jw-status" id="bgStatus">Chưa chạy</div></div>' +
      '<div class="jw-out" id="bgOut">' +
      '<div class="jw-empty" id="bgEmpty"><strong>Sẵn sàng tạo</strong>Chọn tab đầu ra, nhập chủ đề + mục tiêu, rồi bấm Chạy. File xong thường ở Files → exports/bai-giang/.</div>' +
      '<pre class="jw-log" id="bgLog" hidden></pre>' +
      '<div class="jw-om-stage" id="bgOmStage" hidden>' +
      '<div class="jw-om-stage-bar">' +
      '<button type="button" class="jw-btn jw-btn-primary" id="bgOmCreate" hidden>Tạo lớp OpenMAIC</button>' +
      '<span class="jw-hint" id="bgOmStageHint"></span>' +
      "</div>" +
      '<iframe class="jw-om-frame" id="bgOmFrame" title="OpenMAIC classroom" hidden></iframe>' +
      "</div>" +
      "</div></section>" +
      "</div></div>";

    var tabsEl = root.querySelector("#bgTabs");
    FORMATS.forEach(function (f, i) {
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
        esc(f.blurb || f.tagline) +
        "</span>";
      tabsEl.appendChild(b);
    });

    var gotoVid = root.querySelector("#bgGotoVideo");
    if (gotoVid) {
      gotoVid.onclick = function () {
        try {
          if (window.Alpine && Alpine.store("nav")) Alpine.store("nav").go("video");
        } catch (e) {}
      };
    }

    function fmt() {
      return FORMATS[tabIdx] || FORMATS[0];
    }

    function paintTabHint() {
      var f = fmt();
      var el = root.querySelector("#bgTabHint");
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

    function saveDraft() {
      BG_FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (el) draft[id] = el.value;
      });
      var pathEl = root.querySelector("#bgOmPath");
      if (pathEl) draft.bgOmPath = pathEl.value;
    }

    function restoreDraft() {
      BG_FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (el && draft[id] != null) el.value = draft[id];
      });
      var pathEl = root.querySelector("#bgOmPath");
      if (pathEl) {
        pathEl.value = draft.bgOmPath || lastLopHocPath || "";
      }
      var list = root.querySelector("#bgFileList");
      if (list && uploaded.length) {
        list.textContent = "Đã tải: " + uploaded.join(", ");
      }
    }

    function setStatus(msg, kind) {
      var el = root.querySelector("#bgStatus");
      if (!el) return;
      el.textContent = msg || "";
      el.className = "jw-status" + (kind === false ? " err" : kind === true ? " ok" : "");
    }

    function showLog() {
      var empty = root.querySelector("#bgEmpty");
      var log = root.querySelector("#bgLog");
      if (empty) empty.hidden = true;
      if (log) log.hidden = false;
    }

    function appendLog(line) {
      showLog();
      var log = root.querySelector("#bgLog");
      if (!log) return;
      log.innerHTML += formatLogLine(line) + "\n";
      var out = root.querySelector("#bgOut");
      if (out) out.scrollTop = out.scrollHeight;
    }

    function paintLeft() {
      var f = fmt();
      var gets = (f.gets || [])
        .map(function (g) {
          return "<li>" + esc(g) + "</li>";
        })
        .join("");
      var left = root.querySelector("#bgLeft");
      left.innerHTML =
        '<div class="jw-brief jw-brief-lite">' +
        '<p class="jw-brief-kicker">Đầu ra đang chọn</p>' +
        "<h3>" +
        esc(f.full) +
        "</h3>" +
        "<p>" +
        esc(f.when) +
        "</p>" +
        "<ul>" +
        gets +
        "</ul>" +
        '<p class="jw-ex">Ví dụ: ' +
        esc(f.example) +
        "</p>" +
        (f.crossText
          ? '<p class="jw-cross"><button type="button" class="jw-link" id="bgCrossLink">' +
            esc(f.crossText) +
            "</button></p>"
          : "") +
        "</div>" +
        '<p class="jw-sec">1. Brief</p>' +
        '<div class="jw-field"><label for="bgTopic">Chủ đề *</label>' +
        '<input id="bgTopic" type="text" autocomplete="off" placeholder="' +
        esc(f.topicPh) +
        '"></div>' +
        '<div class="jw-field"><label for="bgAudience">Đối tượng học</label>' +
        '<input id="bgAudience" type="text" placeholder="Ví dụ: học sinh THCS, sinh viên năm 1"></div>' +
        '<div class="jw-field"><label for="bgGoals">Mục tiêu học *</label>' +
        '<textarea id="bgGoals" rows="3" placeholder="Sau buổi học, học viên…"></textarea></div>' +
        '<div class="jw-field"><label for="bgPaste">Dán giáo án / đề cương (tuỳ chọn)</label>' +
        '<textarea id="bgPaste" rows="4" placeholder="Ctrl+V nội dung sẵn có…"></textarea></div>' +
        '<div class="jw-row2">' +
        '<div class="jw-field"><label for="bgLang">Ngôn ngữ</label>' +
        '<select id="bgLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
        '<div class="jw-field"><label for="bgFiles">File đính kèm</label>' +
        '<input id="bgFiles" type="file" multiple>' +
        '<p class="jw-hint" id="bgFileList">Giáo án, PDF, ảnh…</p></div></div>' +
        openmaicBlock(f) +
        '<div class="jw-actions jw-actions-main">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="bgRun">Chạy: ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgStop" disabled>Dừng xem</button>' +
        "</div>";

      restoreDraft();
      wireLeft();
      paintTabHint();
    }

    function openmaicBlock(f) {
      if (!f || f.id !== "lop-hoc") return "";
      return (
        '<div class="jw-om" id="bgOmPanel">' +
        '<p class="jw-sec">2. OpenMAIC (sau khi Chạy)</p>' +
        '<p class="jw-hint">Bước 1: Chạy workflow → có file lop-hoc.md. Bước 2: bấm <b>Tạo lớp OpenMAIC</b> ở cột Kết quả.</p>' +
        '<div class="jw-field"><label for="bgOmPath">Đường dẫn lop-hoc.md</label>' +
        '<input id="bgOmPath" type="text" autocomplete="off" placeholder="Ví dụ: exports/bai-giang/…/lop-hoc.md">' +
        '<p class="jw-hint">Để trống = tự lấy từ log sau khi Chạy.</p></div>' +
        '<details class="jw-more">' +
        "<summary>LLM &amp; debug OpenMAIC</summary>" +
        '<p class="jw-hint">Chọn model khi tạo lớp. Key lấy từ trang Models. Nút «Lưu LLM» chỉ lưu cấu hình  -  không tạo lớp.</p>' +
        '<div class="jw-field"><label for="bgOmProv">Nhà cung cấp</label>' +
        '<select id="bgOmProv">' +
        '<option value="google">Google Gemini</option>' +
        '<option value="openai">OpenAI (API)</option>' +
        '<option value="deepseek">DeepSeek</option>' +
        "</select></div>" +
        '<div class="jw-field"><label for="bgOmModel">Model</label>' +
        '<select id="bgOmModel"></select>' +
        '<p class="jw-hint" id="bgOmLlmHint">Đang tải…</p></div>' +
        '<div class="jw-actions">' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmLlmApply">Lưu LLM cho OpenMAIC</button>' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmCopyCmd">Copy lệnh debug</button>' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmOpen">Mở URL public</button>' +
        "</div></details></div>"
      );
    }

    function wireLeft() {
      BG_FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (!el) return;
        el.addEventListener("change", saveDraft);
        el.addEventListener("input", saveDraft);
      });
      var pathWatch = root.querySelector("#bgOmPath");
      if (pathWatch) {
        pathWatch.addEventListener("change", saveDraft);
        pathWatch.addEventListener("input", saveDraft);
      }

      var cross = root.querySelector("#bgCrossLink");
      if (cross) {
        cross.onclick = function () {
          try {
            if (window.Alpine && Alpine.store("nav")) Alpine.store("nav").go("video");
          } catch (e) {}
        };
      }

      root.querySelector("#bgFiles").onchange = async function () {
        var files = Array.from((root.querySelector("#bgFiles").files) || []);
        uploaded = [];
        var list = root.querySelector("#bgFileList");
        if (!files.length) {
          if (list) list.textContent = "Giáo án, PDF, ảnh…";
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
        if (list) list.textContent = uploaded.length ? "Đã tải: " + uploaded.join(", ") : "Không tải được file.";
      };

      root.querySelector("#bgStop").onclick = function () {
        runFinished = true;
        try { if (es) es.close(); } catch (e) {}
        es = null;
        setBusy(false, "Đã dừng theo dõi (server có thể vẫn chạy).", true);
      };

      root.querySelector("#bgRun").onclick = run;

      var copyCmdBtn = root.querySelector("#bgOmCopyCmd");
      var openBtn = root.querySelector("#bgOmOpen");
      var pathEl = root.querySelector("#bgOmPath");
      if (pathEl && lastLopHocPath && !pathEl.value) pathEl.value = lastLopHocPath;

      // --- OpenMAIC LLM module ---
      var omLlmCache = null;
      function fillOmModels(prov) {
        var sel = root.querySelector("#bgOmModel");
        var hint = root.querySelector("#bgOmLlmHint");
        if (!sel || !omLlmCache) return;
        var meta = (omLlmCache.providers || {})[prov] || {};
        var models = meta.models || [];
        var cur = (omLlmCache.config && omLlmCache.config.provider === prov && omLlmCache.config.model) || meta.default_model || "";
        sel.innerHTML = models
          .map(function (m) {
            return '<option value="' + esc(m) + '"' + (m === cur ? " selected" : "") + ">" + esc(m) + "</option>";
          })
          .join("");
        if (cur && models.indexOf(cur) < 0) {
          sel.innerHTML = '<option value="' + esc(cur) + '" selected>' + esc(cur) + "</option>" + sel.innerHTML;
        }
        var keyOk = !!meta.has_key;
        var dockerOk = !!omLlmCache.docker;
        var bits = [];
        bits.push(keyOk ? "Models: đã có key" : "Models: chưa có key  -  vào trang Models dán key");
        bits.push(dockerOk ? "Docker: áp dụng trực tiếp được" : "Docker: chưa gắn socket  -  Áp dụng chỉ lưu, cần sync deploy");
        if (omLlmCache.default_model) bits.push("Đã chọn: " + omLlmCache.default_model);
        if (omLlmCache.container_model) {
          bits.push("Container: " + omLlmCache.container_model);
          if (omLlmCache.in_sync === false) {
            bits.push("CHƯA ĐỒNG BỘ  -  bấm Lưu LLM hoặc sync deploy");
          }
        }
        if (hint) hint.textContent = bits.join(" · ");
      }
      async function loadOmLlm() {
        var provEl = root.querySelector("#bgOmProv");
        var hint = root.querySelector("#bgOmLlmHint");
        if (!provEl) return;
        try {
          var r = await (await fetch("/openmaic/llm")).json();
          omLlmCache = r || {};
          var p = (r.config && r.config.provider) || "google";
          provEl.value = p;
          fillOmModels(p);
        } catch (e) {
          if (hint) hint.textContent = "Không tải được cấu hình LLM: " + ((e && e.message) || e);
        }
      }
      var provEl = root.querySelector("#bgOmProv");
      if (provEl) {
        provEl.onchange = function () {
          fillOmModels(provEl.value);
        };
      }
      var applyLlmBtn = root.querySelector("#bgOmLlmApply");
      if (applyLlmBtn) {
        applyLlmBtn.onclick = async function () {
          var provider = ((root.querySelector("#bgOmProv") || {}).value || "google").trim();
          var model = ((root.querySelector("#bgOmModel") || {}).value || "").trim();
          applyLlmBtn.disabled = true;
          setStatus("Đang áp dụng LLM OpenMAIC…");
          try {
            var res = await fetch("/openmaic/llm", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ provider: provider, model: model }),
            });
            var j = await res.json().catch(function () {
              return null;
            });
            if (!res.ok) {
              var err = (j && (j.detail || j.error || j.message)) || "HTTP " + res.status;
              if (typeof err === "object") err = JSON.stringify(err);
              setStatus(String(err), false);
              appendLog("OpenMAIC LLM ERROR: " + err);
            } else if (j && j.applied === false) {
              var warn =
                (j && j.hint) ||
                "Đã lưu lựa chọn nhưng OpenMAIC chưa đổi model (Docker chưa sẵn). Cần sync deploy.";
              setStatus(String(warn), false);
              appendLog("--- OpenMAIC LLM (CHƯA áp vào container) ---\n" + warn);
              await loadOmLlm();
            } else {
              var msg =
                (j && j.message) ||
                "Đã recreate OpenMAIC → " + ((j && j.default_model) || "");
              setStatus(String(msg), true);
              appendLog("--- OpenMAIC LLM ---\n" + msg);
              await loadOmLlm();
            }
          } catch (e) {
            setStatus(String((e && e.message) || e), false);
          }
          applyLlmBtn.disabled = false;
        };
      }
      loadOmLlm();

      async function resolvePublicUrl() {
        if (cachedPublicUrl) return cachedPublicUrl;
        try {
          var h = await (await fetch("/openmaic/health")).json();
          if (h && h.public_url) {
            cachedPublicUrl = String(h.public_url).replace(/\/$/, "");
            return cachedPublicUrl;
          }
        } catch (e) {}
        return OM_FALLBACK_URL;
      }

      async function copyText(text, okMsg) {
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
          } else {
            throw new Error("no clipboard");
          }
          setStatus(okMsg || "Đã copy.", true);
        } catch (e) {
          appendLog("--- Copy thủ công ---\n" + text + "\n---");
          setStatus("Clipboard bị chặn  -  xem cột Kết quả để copy tay.", false);
        }
      }

      if (copyCmdBtn) {
        copyCmdBtn.onclick = async function () {
          var pub = await resolvePublicUrl();
          var text = buildOpenmaicHandoff({
            publicUrl: pub,
            topic: ((root.querySelector("#bgTopic") || {}).value || "").trim() || lastTopic || "(chưa ghi chủ đề)",
            goals: ((root.querySelector("#bgGoals") || {}).value || "").trim(),
            paste: ((root.querySelector("#bgPaste") || {}).value || "").trim(),
            slugHint:
              ((root.querySelector("#bgOmPath") || {}).value || "").trim() ||
              lastLopHocPath ||
              "exports/bai-giang/<slug>/lop-hoc.md",
          });
          await copyText(text, "Đã copy lệnh debug (ưu tiên dùng nút Tạo lớp trong VMOS).");
        };
      }
      if (openBtn) {
        openBtn.onclick = async function () {
          var pub = await resolvePublicUrl();
          window.open(pub, "_blank", "noopener,noreferrer");
          setStatus("Đã mở URL public (debug). Classroom nên xem trong iframe VMOS.", true);
        };
      }
    }

    function stopOmPoll() {
      if (omPollTimer) {
        clearTimeout(omPollTimer);
        omPollTimer = null;
      }
    }

    function showOmStage(showCreate) {
      var stage = root.querySelector("#bgOmStage");
      var btn = root.querySelector("#bgOmCreate");
      var hint = root.querySelector("#bgOmStageHint");
      if (stage) stage.hidden = false;
      if (btn) {
        btn.hidden = !showCreate;
        btn.disabled = omGenerating;
        btn.textContent = omGenerating ? "Đang tạo lớp…" : "Tạo lớp OpenMAIC";
        btn.onclick = function () {
          startOpenmaicGenerate();
        };
      }
      if (hint && showCreate && !omGenerating) {
        hint.textContent = lastLopHocPath
          ? "Nguồn: " + lastLopHocPath
          : "Sẽ dùng path exports/bai-giang/…/lop-hoc.md";
      }
    }

    function showOmIframe(url) {
      var frame = root.querySelector("#bgOmFrame");
      var hint = root.querySelector("#bgOmStageHint");
      var btn = root.querySelector("#bgOmCreate");
      if (frame && url) {
        frame.hidden = false;
        frame.src = url;
      }
      if (btn) {
        btn.hidden = !lastOmThin;
        btn.disabled = false;
        btn.textContent = lastOmThin ? "Tạo lại lớp OpenMAIC" : "Tạo lớp OpenMAIC";
      }
      if (hint) {
        hint.textContent = lastOmThin
          ? "Classroom mỏng  -  xem cảnh báo trong log; có thể tạo lại."
          : "Classroom sẵn sàng trong khung dưới.";
      }
      if (!lastOmThin) {
        setStatus("Lớp OpenMAIC đã sẵn trong VMOS.", true);
      }
    }

    async function startOpenmaicGenerate() {
      if (omGenerating || running) return;
      var pathInput = ((root.querySelector("#bgOmPath") || {}).value || "").trim();
      var path = pathInput || lastLopHocPath;
      if (!path) {
        path = extractLopHocPath(
          (root.querySelector("#bgLog") || {}).textContent || "",
          lastTopic || ((root.querySelector("#bgTopic") || {}).value || "")
        );
      }
      if (!path) {
        setStatus("Thiếu đường dẫn lop-hoc.md  -  điền ô path hoặc chạy workflow Lớp học trước.", false);
        return;
      }
      lastLopHocPath = path;
      omGenerating = true;
      stopOmPoll();
      showOmStage(true);
      setStatus("Đang gửi generate → OpenMAIC…");
      appendLog("--- OpenMAIC generate ---\npath: " + path);

      try {
        var fd = new FormData();
        fd.append("brain", brain());
        fd.append("path", path);
        fd.append("topic", lastTopic || ((root.querySelector("#bgTopic") || {}).value || "").trim());
        fd.append("enable_tts", "1");
        var res = await fetch("/openmaic/generate", { method: "POST", body: fd });
        var r = await res.json().catch(function () {
          return null;
        });
        if (!res.ok || !r || !r.jobId) {
          var err =
            (r && (r.error || r.detail || r.message)) ||
            "generate thất bại (HTTP " + res.status + ")";
          if (typeof err === "object") err = JSON.stringify(err);
          appendLog("ERROR: " + err);
          // Gợi ý path: điền ô path để user sửa / bấm lại
          var hintM = String(err).match(/Gợi ý gần đúng:\s*([^\n]+)/i);
          if (hintM) {
            var firstHint = hintM[1].split(",")[0].trim();
            var pathField = root.querySelector("#bgOmPath");
            if (pathField && firstHint) {
              pathField.value = firstHint;
              lastLopHocPath = firstHint;
              appendLog("Đã điền path gợi ý: " + firstHint + "  -  bấm lại «Tạo lớp OpenMAIC».");
            }
          }
          setStatus(String(err), false);
          omGenerating = false;
          showOmStage(true);
          return;
        }
        if (r.path && r.path !== path) {
          lastLopHocPath = r.path;
          var pf = root.querySelector("#bgOmPath");
          if (pf) pf.value = r.path;
          appendLog("Đã sửa path → " + r.path);
        }
        appendLog(
          "jobId: " +
            r.jobId +
            " | language=" +
            (r.language || "en-US") +
            " | TTS=" +
            !!r.enableTTS +
            " | img=" +
            !!r.enableImageGeneration +
            " | web=" +
            !!r.enableWebSearch
        );
        if (r.capabilities && r.capabilities.imageGeneration === false) {
          appendLog(
            "CẢNH BÁO: OpenMAIC chưa bật imageGeneration (thiếu provider ảnh) → slide dễ thiếu hình/biểu đồ."
          );
        }
        setStatus("OpenMAIC đang tạo lớp… (" + (r.status || "queued") + ")");
        pollOpenmaicJob(r.jobId, Math.max(4000, Number(r.pollIntervalMs) || 5000));
      } catch (e) {
        appendLog("ERROR: " + ((e && e.message) || e));
        setStatus(String((e && e.message) || e), false);
        omGenerating = false;
        showOmStage(true);
      }
    }

    function pollOpenmaicJob(jobId, intervalMs) {
      stopOmPoll();
      var tries = 0;
      // 15 cảnh + TTS có thể > 10 phút
      var maxTries = 240;
      function tick() {
        tries += 1;
        fetch("/openmaic/jobs/" + encodeURIComponent(jobId))
          .then(function (res) {
            return res.json();
          })
          .then(function (data) {
            if (!data) throw new Error("poll trống");
            var st = data.status || "";
            var step = data.step || "";
            var prog = "";
            if (data.scenesGenerated != null && data.totalScenes != null) {
              prog = " scenes " + data.scenesGenerated + "/" + data.totalScenes;
            } else if (data.scenesCount != null) {
              prog = " scenes=" + data.scenesCount;
            }
            if (tries === 1 || tries % 3 === 0) {
              appendLog("[openmaic] " + st + (step ? " / " + step : "") + prog);
            }
            setStatus("OpenMAIC: " + st + (step ? "  -  " + step : "") + prog + " (" + tries + ")");
            if (data.failed || String(st).toLowerCase() === "failed") {
              omGenerating = false;
              appendLog("ERROR: " + (data.error || data.message || "generate failed"));
              setStatus("OpenMAIC tạo lớp thất bại.", false);
              showOmStage(true);
              return;
            }
            var url =
              data.embedUrl ||
              data.classroomUrl ||
              (data.result && (data.result.url || data.result.classroomUrl)) ||
              "";
            if (data.done && url) {
              omGenerating = false;
              var sc = data.scenesCount;
              appendLog(
                "Classroom URL:\n" +
                  url +
                  (sc != null ? "\nscenesCount: " + sc : "")
              );
              if (data.thinClassroom || (typeof sc === "number" && sc < 3)) {
                lastOmThin = true;
                appendLog(
                  "CẢNH BÁO: chỉ " +
                    (sc != null ? sc : "?") +
                    " scene  -  thường là slide chào. " +
                    (data.warning ||
                      "Kiểm tra lop-hoc.md (cần outline 8-15 cảnh + script) và thử model mạnh hơn OpenAI (vd. gpt-4o).")
                );
                setStatus(
                  "Lớp chỉ có " + (sc != null ? sc : "ít") + " scene  -  xem cảnh báo trong log.",
                  false
                );
              } else {
                lastOmThin = false;
              }
              showOmIframe(url);
              return;
            }
            if (data.done && !url) {
              omGenerating = false;
              appendLog("Xong nhưng thiếu URL classroom: " + JSON.stringify(data).slice(0, 800));
              setStatus("OpenMAIC xong nhưng thiếu URL.", false);
              showOmStage(true);
              return;
            }
            if (tries >= maxTries) {
              omGenerating = false;
              setStatus("Hết thời gian chờ OpenMAIC  -  job " + jobId + " có thể vẫn chạy.", false);
              showOmStage(true);
              return;
            }
            omPollTimer = setTimeout(tick, intervalMs);
          })
          .catch(function (e) {
            if (tries >= maxTries) {
              omGenerating = false;
              setStatus("Poll OpenMAIC lỗi: " + ((e && e.message) || e), false);
              showOmStage(true);
              return;
            }
            omPollTimer = setTimeout(tick, intervalMs);
          });
      }
      tick();
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
        try { el.focus(); } catch (e) {}
      }
    }

    function setBusy(busy, statusMsg, statusOk) {
      running = !!busy;
      var f = fmt();
      var runBtn = root.querySelector("#bgRun");
      var stopBtn = root.querySelector("#bgStop");
      var seedBtn = root.querySelector("#bgSeed");
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
      var topic = ((root.querySelector("#bgTopic") || {}).value || "").trim();
      var goals = ((root.querySelector("#bgGoals") || {}).value || "").trim();
      var missing = [];
      if (!topic) {
        markField("bgTopic", true);
        missing.push("Chủ đề");
      }
      if (!goals) {
        markField("bgGoals", true);
        missing.push("Mục tiêu học");
      }
      if (missing.length) {
        setStatus("Thiếu thông tin: " + missing.join(", ") + ". Điền bên trái rồi bấm Chạy.", false);
        return null;
      }
      return {
        topic: topic,
        audience: ((root.querySelector("#bgAudience") || {}).value || "").trim(),
        goals: goals,
        lang: ((root.querySelector("#bgLang") || {}).value || "vi").trim(),
        paste: ((root.querySelector("#bgPaste") || {}).value || "").trim(),
        feat: fmt(),
      };
    }

    function finishBusy(statusMsg, statusOk) {
      runFinished = true;
      try { if (es) es.close(); } catch (e) {}
      es = null;
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

    root.querySelector("#bgSeed").onclick = async function () {
      if (running) return;
      var seedBtn = root.querySelector("#bgSeed");
      if (seedBtn) {
        seedBtn.disabled = true;
        seedBtn.textContent = "Đang chuẩn bị…";
      }
      setStatus("Đang chuẩn bị agent + workflow…");
      try {
        var fd = new FormData();
        fd.append("brain", brain());
        var r = await (await fetch("/studio/seed-bai-giang", { method: "POST", body: fd })).json();
        if (!r || !r.ok) {
          setStatus((r && r.error) || "Chuẩn bị thất bại", false);
          return;
        }
        setStatus("Sẵn sàng " + (r.workflows || []).length + " loại đầu ra.", true);
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
      lastTopic = v.topic;
      var brief = composeBrief(v.topic, v.audience, v.goals, v.lang, f, uploaded, v.paste);

      setBusy(true, "Đang chạy «" + f.full + "»…");
      runFinished = false;
      stopOmPoll();
      omGenerating = false;
      lastOmThin = false;
      var stage = root.querySelector("#bgOmStage");
      var frame = root.querySelector("#bgOmFrame");
      var createBtn = root.querySelector("#bgOmCreate");
      if (stage) stage.hidden = true;
      if (frame) {
        frame.hidden = true;
        frame.removeAttribute("src");
      }
      if (createBtn) createBtn.hidden = true;
      if (es) {
        try { es.close(); } catch (e1) {}
        es = null;
      }
      var log = root.querySelector("#bgLog");
      if (log) log.innerHTML = "";
      appendLog("--- Brief ---\n" + brief + "\n---");

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        var seedRes = await fetch("/studio/seed-bai-giang", { method: "POST", body: fd0 });
        var seedJson = await seedRes.json().catch(function () { return null; });
        if (!seedRes.ok || (seedJson && seedJson.ok === false)) {
          appendLog(
            "CẢNH BÁO seed: " +
              ((seedJson && (seedJson.error || seedJson.detail)) || "HTTP " + seedRes.status)
          );
        }
      } catch (e0) {
        appendLog("CẢNH BÁO seed: " + ((e0 && e0.message) || e0));
      }

      var url =
        "/workflows/run?slug=" +
        encodeURIComponent(f.slug) +
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
            appendLog("[" + typ + "] " + (data.message || data.agent || data.step || JSON.stringify(data)));
          } else if (typ === "step_done") {
            appendLog("[xong bước] " + (data.agent || "") + (data.verified === false ? " (cần chỉnh)" : ""));
            if (data.output) {
              var out = String(data.output);
              appendLog(out.length > 5000 ? out.slice(0, 5000) + "\n…(cắt)" : out);
            }
          } else if (typ === "error") {
            appendLog("ERROR: " + (data.message || data.error || ev.data));
            finishBusy("Lỗi khi tạo", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 8000 ? res.slice(0, 8000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            if (f.id === "lop-hoc") {
              var logEl = root.querySelector("#bgLog");
              var blob =
                (logEl ? logEl.textContent : "") +
                "\n" +
                (data.result ? String(data.result) : "");
              lastLopHocPath = extractLopHocPath(blob, v.topic);
              var pathField = root.querySelector("#bgOmPath");
              if (pathField && lastLopHocPath) pathField.value = lastLopHocPath;
              appendLog(
                "OpenMAIC trong VMOS: bấm «Tạo lớp OpenMAIC» ở cột Kết quả" +
                  (lastLopHocPath ? "\npath: " + lastLopHocPath : "") +
                  "\n(language=en-US + nội dung VI + TTS Edge  -  không mở domain)."
              );
              showOmStage(true);
            }
            finishBusy(
              f.id === "lop-hoc"
                ? "Xong. Bấm «Tạo lớp OpenMAIC» trong panel Kết quả."
                : "Xong. Xem exports/bai-giang/ trong Files.",
              true
            );
          } else {
            appendLog(ev.data);
          }
        } catch (eParse) {
          appendLog(ev.data);
        }
      };
      es.onerror = function () {
        if (runFinished || !running) return;
        finishBusy("Mất kết nối stream (có thể đã xong hoặc lỗi).", false);
      };
    }

    window._bgLeave = function () {
      runFinished = true;
      stopOmPoll();
      try { if (es) es.close(); } catch (e) {}
      es = null;
    };

    paintLeft();
  };
})();
