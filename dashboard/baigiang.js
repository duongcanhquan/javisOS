/**
 * Công việc → Bài giảng: workbench full màn.
 * Trái = chọn tab đầu ra + brief/input; phải = kết quả chạy.
 */
(function () {
  "use strict";

  var FORMATS = [
    {
      id: "slide",
      slug: "bo-bai-giang-slide",
      label: "Slide",
      full: "Slide trình chiếu",
      tagline: "Dạy trên lớp / seminar",
      when: "Cần chiếu máy chiếu hoặc gửi trước cho học viên. Ít chữ, có gợi ý hình.",
      gets: ["Deck 10–16 slide", "Speaker notes", "Gợi ý ảnh / biểu đồ"],
      example: "«Quang hợp lớp 8» → hook → 3 bước → ví dụ → quiz → tóm tắt.",
      time: "~10–20 phút",
      topicPh: "VD: Quang hợp cho học sinh lớp 8",
    },
    {
      id: "video",
      slug: "bo-bai-giang-video",
      label: "Video",
      full: "Video giải thích",
      tagline: "Clip xem lại / Zalo / LMS",
      when: "Giải thích một ý khó bằng hình động để học viên tự xem trước hoặc ôn.",
      gets: ["Beat giảng (hook → giải thích → ví dụ)", "Gói render / pack thủ công", "Độ dài gợi ý 60–90s"],
      example: "«Vì sao trời xanh?» → clip ~75 giây, kết luận 1 câu dễ nhớ.",
      time: "Kịch bản nhanh; render lâu hơn",
      topicPh: "VD: Vì sao trời xanh?",
    },
    {
      id: "lop-hoc",
      slug: "bo-bai-giang-lop-hoc",
      label: "Lớp học",
      full: "Lớp học tương tác",
      tagline: "Cảnh · quiz · thực hành",
      when: "Dạy live và cần kịch bản cả buổi: hoạt động, câu hỏi, bài tập ngắn.",
      gets: ["Outline 8–15 cảnh", "Quiz + PBL ngắn", "Script giảng từng cảnh"],
      example: "«Biến trong Python» → mở → demo → mini-lab → quiz → tổng kết.",
      time: "~20–40 phút",
      topicPh: "VD: Nhập môn biến trong Python",
    },
    {
      id: "van-ban",
      slug: "bo-bai-giang-van-ban",
      label: "Bài đọc",
      full: "Bài đọc + ảnh & biểu đồ",
      tagline: "Handout / đọc trước",
      when: "Cần tài liệu chữ rõ, có chỗ ảnh/biểu đồ, học viên đọc một mình được.",
      gets: ["Longread 1200–2000 chữ", "Chỗ [ẢNH]/[BIỂU ĐỒ]", "Ví dụ + bài luyện"],
      example: "«An toàn mạng» → 5 mục + bảng so sánh + checklist mang về.",
      time: "~15–25 phút",
      topicPh: "VD: An toàn mạng cho học sinh",
    },
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

  var OM_LS_URL = "javis.baigiang.openmaicUrl";
  var OM_LS_CODE = "javis.baigiang.openmaicCode";
  var OM_DEFAULT_URL = "https://openmaic.vietmycollege.com";
  var OM_DEFAULT_CODE = "vietmy-openmaic";

  function loadOm() {
    var url = OM_DEFAULT_URL;
    var code = OM_DEFAULT_CODE;
    try {
      url = localStorage.getItem(OM_LS_URL) || OM_DEFAULT_URL;
      code = localStorage.getItem(OM_LS_CODE);
      if (code == null || code === "") code = OM_DEFAULT_CODE;
    } catch (e) {}
    return { url: String(url).trim().replace(/\/$/, ""), code: String(code).trim() };
  }

  function saveOm(url, code) {
    try {
      localStorage.setItem(OM_LS_URL, String(url || "").trim().replace(/\/$/, ""));
      localStorage.setItem(OM_LS_CODE, String(code == null ? "" : code).trim());
    } catch (e) {}
  }

  function omLangRules(lang) {
    var L = String(lang || "vi").trim().toLowerCase() || "vi";
    if (L === "vietnamese") L = "vi";
    return {
      code: L,
      isVi: L === "vi" || L.indexOf("vi") === 0,
    };
  }

  /** Lệnh handoff (advanced). API OpenMAIC chỉ nhận en-US|zh-CN — dùng en-US + nội dung VI. */
  function buildOpenmaicHandoff(opts) {
    opts = opts || {};
    var om = loadOm();
    var topic = opts.topic || "(chưa ghi chủ đề)";
    var goals = opts.goals || "";
    var paste = opts.paste || "";
    var slugHint = opts.slugHint || "exports/bai-giang/<slug>/lop-hoc.md";
    var lines = [
      "Trong Javis: Việc → Bài giảng → Lớp học → bấm «Tạo lớp OpenMAIC» (không mở domain riêng / Live Demo).",
      "Server tự gọi " + om.url + " với language=en-US + script tiếng Việt + TTS Edge.",
      "",
      "Nếu generate thủ công (debug):",
      "URL API: " + om.url,
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
        "Sau khi ghi exports/bai-giang/<slug>/lop-hoc.md: hướng dẫn user bấm «Tạo lớp OpenMAIC» NGAY TRONG Javis (không mở domain OpenMAIC, không Live Demo)."
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
    var lastLopHocPath = "";
    var lastTopic = "";
    var omPollTimer = null;
    var omGenerating = false;

    root.innerHTML =
      '<div class="jw" id="bgJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Tạo bài giảng</h2>" +
      '<p class="jw-lead">Chọn loại đầu ra, điền brief hoặc dán giáo án. Tab Lớp học: tạo classroom OpenMAIC <b>ngay trong Javis</b> (không mở domain riêng).</p></div>' +
      '<div class="jw-top-actions">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="bgSeed">Chuẩn bị lần đầu</button>' +
      "</div></div>" +
      '<div class="jw-tabs" role="tablist" id="bgTabs"></div>' +
      "</div>" +
      '<div class="jw-body">' +
      '<aside class="jw-left"><div class="jw-left-scroll" id="bgLeft"></div></aside>' +
      '<section class="jw-right">' +
      '<div class="jw-right-head"><h3>Kết quả</h3><div class="jw-status" id="bgStatus">Chưa chạy</div></div>' +
      '<div class="jw-out" id="bgOut">' +
      '<div class="jw-empty" id="bgEmpty"><strong>Sẵn sàng tạo</strong>Chọn tab đầu ra, nhập chủ đề, rồi bấm Chạy. Tiến trình và nội dung hiện tại đây.</div>' +
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
    tabsEl.innerHTML = FORMATS.map(function (f, i) {
      return (
        '<button type="button" class="jw-tab' +
        (i === 0 ? " on" : "") +
        '" role="tab" aria-selected="' +
        (i === 0 ? "true" : "false") +
        '" data-i="' +
        i +
        '">' +
        esc(f.label) +
        "</button>"
      );
    }).join("");

    function fmt() {
      return FORMATS[tabIdx] || FORMATS[0];
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
      var gets = (f.gets || []).map(function (g) {
        return "<li>" + esc(g) + "</li>";
      }).join("");
      var left = root.querySelector("#bgLeft");
      left.innerHTML =
        '<div class="jw-brief">' +
        '<p class="jw-brief-kicker">Đầu ra đang chọn</p>' +
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
        '<div class="jw-field"><label for="bgTopic">Chủ đề *</label>' +
        '<input id="bgTopic" type="text" autocomplete="off" placeholder="' +
        esc(f.topicPh) +
        '"></div>' +
        '<div class="jw-field"><label for="bgAudience">Đối tượng học</label>' +
        '<input id="bgAudience" type="text" placeholder="Ví dụ: học sinh THCS, sinh viên năm 1"></div>' +
        '<div class="jw-field"><label for="bgGoals">Mục tiêu học</label>' +
        '<textarea id="bgGoals" rows="3" placeholder="Sau buổi học, học viên…"></textarea></div>' +
        '<div class="jw-field"><label for="bgPaste">Dán giáo án / đề cương / kịch bản</label>' +
        '<textarea id="bgPaste" rows="5" placeholder="Ctrl+V nội dung sẵn có (Word, PDF copy, outline…). Dùng cho lớp học, video, slide — không cần gõ lại."></textarea>' +
        '<p class="jw-hint">Paste một lần → agent dùng làm nguyên liệu. Tab Video: dán beat/script nếu đã có.</p></div>' +
        '<div class="jw-field"><label for="bgLang">Ngôn ngữ</label>' +
        '<select id="bgLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
        '<div class="jw-field"><label for="bgFiles">File đính kèm</label>' +
        '<input id="bgFiles" type="file" multiple>' +
        '<p class="jw-hint" id="bgFileList">Giáo án, PDF, ảnh… (tuỳ chọn)</p></div>' +
        openmaicBlock(f) +
        '<div class="jw-actions">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="bgRun">Chạy: ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgStop" disabled>Dừng xem</button>' +
        "</div>";

      wireLeft();
    }

    function openmaicBlock(f) {
      if (!f || f.id !== "lop-hoc") return "";
      return (
        '<div class="jw-om" id="bgOmPanel">' +
        '<p class="jw-brief-kicker">OpenMAIC trong Javis</p>' +
        '<p class="jw-hint">Sau khi Chạy xong: bấm <b>Tạo lớp OpenMAIC</b> ở cột Kết quả. Javis gọi server (language=en-US + nội dung VI + TTS Edge tiếng Việt).</p>' +
        '<div class="jw-om-llm" id="bgOmLlm">' +
        '<p class="jw-brief-kicker">LLM cho OpenMAIC (tự cài)</p>' +
        '<p class="jw-hint">Chọn nhà model; key lấy từ trang <b>Models</b> (không dán lại ở đây). Generate lớp tính phí theo API key đó.</p>' +
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
        '<button type="button" class="jw-btn jw-btn-primary" id="bgOmLlmApply">Áp dụng lên OpenMAIC</button>' +
        "</div></div>" +
        '<div class="jw-field"><label for="bgOmPath">Đường dẫn lop-hoc.md (tuỳ chọn)</label>' +
        '<input id="bgOmPath" type="text" autocomplete="off" placeholder="Ví dụ: exports/bai-giang/…/lop-hoc.md">' +
        '<p class="jw-hint">Để trống = tự lấy từ kết quả chạy. Có quiz.md cùng thư mục sẽ kèm theo.</p></div>' +
        '<details class="jw-om-adv"><summary>Tuỳ chọn nâng cao</summary>' +
        '<p class="jw-hint">Chỉ khi cần debug ngoài Javis.</p>' +
        '<div class="jw-actions jw-om-actions">' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmCopyCmd">Copy lệnh debug</button>' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmOpen">Mở URL public</button>' +
        "</div></details></div>"
      );
    }

    function wireLeft() {
      root.querySelector("#bgFiles").onchange = async function () {
        var files = Array.from((root.querySelector("#bgFiles").files) || []);
        uploaded = [];
        var list = root.querySelector("#bgFileList");
        if (!files.length) {
          if (list) list.textContent = "Giáo án, PDF, ảnh… (tuỳ chọn)";
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
        try { if (es) es.close(); } catch (e) {}
        es = null;
        setBusy(false, "Đã dừng theo dõi (server có thể vẫn chạy).", true);
      };

      root.querySelector("#bgRun").onclick = run;

      var copyCmdBtn = root.querySelector("#bgOmCopyCmd");
      var openBtn = root.querySelector("#bgOmOpen");
      var pathEl = root.querySelector("#bgOmPath");
      if (pathEl && lastLopHocPath) pathEl.value = lastLopHocPath;

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
        bits.push(keyOk ? "Models: đã có key" : "Models: chưa có key — vào trang Models dán key");
        bits.push(dockerOk ? "Docker: áp dụng trực tiếp được" : "Docker: chưa gắn socket — Áp dụng chỉ lưu, cần sync deploy");
        if (omLlmCache.default_model) bits.push("Đã chọn: " + omLlmCache.default_model);
        if (omLlmCache.container_model) {
          bits.push("Container: " + omLlmCache.container_model);
          if (omLlmCache.in_sync === false) {
            bits.push("CHƯA ĐỒNG BỘ — bấm Áp dụng hoặc chạy sync deploy");
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
          setStatus("Clipboard bị chặn — xem cột Kết quả để copy tay.", false);
        }
      }

      if (copyCmdBtn) {
        copyCmdBtn.onclick = async function () {
          var text = buildOpenmaicHandoff({
            topic: ((root.querySelector("#bgTopic") || {}).value || "").trim() || lastTopic || "(chưa ghi chủ đề)",
            goals: ((root.querySelector("#bgGoals") || {}).value || "").trim(),
            paste: ((root.querySelector("#bgPaste") || {}).value || "").trim(),
            lang: ((root.querySelector("#bgLang") || {}).value || "vi").trim(),
            slugHint:
              ((root.querySelector("#bgOmPath") || {}).value || "").trim() ||
              lastLopHocPath ||
              "exports/bai-giang/<slug>/lop-hoc.md",
          });
          await copyText(text, "Đã copy lệnh debug (ưu tiên dùng nút Tạo lớp trong Javis).");
        };
      }
      if (openBtn) {
        openBtn.onclick = function () {
          var om = loadOm();
          window.open(om.url || OM_DEFAULT_URL, "_blank", "noopener,noreferrer");
          setStatus("Đã mở URL public (debug). Classroom nên xem trong iframe Javis.", true);
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
      if (btn) btn.hidden = true;
      if (hint) hint.textContent = "Classroom sẵn sàng trong khung dưới.";
      setStatus("Lớp OpenMAIC đã sẵn trong Javis.", true);
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
        setStatus("Thiếu đường dẫn lop-hoc.md — điền ô path hoặc chạy workflow Lớp học trước.", false);
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
              appendLog("Đã điền path gợi ý: " + firstHint + " — bấm lại «Tạo lớp OpenMAIC».");
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
            !!r.enableTTS
        );
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
      var maxTries = 120;
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
            if (tries === 1 || tries % 3 === 0) {
              appendLog("[openmaic] " + st + (step ? " / " + step : ""));
            }
            setStatus("OpenMAIC: " + st + (step ? " — " + step : "") + " (" + tries + ")");
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
              appendLog("Classroom URL:\n" + url);
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
              setStatus("Hết thời gian chờ OpenMAIC — job " + jobId + " có thể vẫn chạy.", false);
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
      stopOmPoll();
      omGenerating = false;
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
        await fetch("/studio/seed-bai-giang", { method: "POST", body: fd0 });
      } catch (e0) {}

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
                "OpenMAIC trong Javis: bấm «Tạo lớp OpenMAIC» ở cột Kết quả" +
                  (lastLopHocPath ? "\npath: " + lastLopHocPath : "") +
                  "\n(language=en-US + nội dung VI + TTS Edge — không mở domain)."
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
        finishBusy("Mất kết nối stream (có thể đã xong hoặc lỗi).", false);
      };
    }

    paintLeft();
  };
})();
