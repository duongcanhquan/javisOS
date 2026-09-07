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

  /** Lệnh handoff OpenMAIC: khóa locale + TTS để tránh giọng Trung / Live Demo. */
  function buildOpenmaicHandoff(opts) {
    opts = opts || {};
    var om = loadOm();
    var lang = omLangRules(opts.lang || "vi");
    var topic = opts.topic || "(chưa ghi chủ đề)";
    var goals = opts.goals || "";
    var paste = opts.paste || "";
    var slugHint = opts.slugHint || "exports/bai-giang/<slug>/lop-hoc.md";
    var lines = [
      "Self-hosted OpenMAIC (KHÔNG Live Demo / KHÔNG open.maic.chat).",
      "URL: " + om.url,
      "Mã site (ACCESS_CODE, nhập 1 lần): " + (om.code || OM_DEFAULT_CODE),
      "",
      "Tạo LẠI classroom mới (không dùng bản cũ) từ:",
      slugHint,
      "(+ quiz.md cùng thư mục nếu hữu ích).",
      "",
      "Chủ đề: " + topic,
    ];
    if (goals) lines.push("Mục tiêu: " + goals);
    if (lang.isVi) {
      lines.push(
        "language=vi — toàn bộ script, quiz, UI, requirement bằng tiếng Việt dấu đầy đủ."
      );
      lines.push("CẤM language=zh / zh-CN / zh-TW. CẤM fallback language=en-US khi nội dung là Việt.");
    } else {
      lines.push("language=" + lang.code + " — giữ đúng ngôn ngữ brief; không chuyển sang zh.");
    }
    lines.push("");
    lines.push("TTS (tránh giọng Trung / ngọng):");
    lines.push("- enableTTS=true nếu /api/health.capabilities.tts=true");
    lines.push(
      "- Provider: OpenAI TTS → Javis Edge-TTS. Voice: nova hoặc alloy (Hoài My); onyx hoặc echo (Nam Minh)."
    );
    lines.push("- CẤM Browser Native / speechSynthesis / Doubao / Qwen / mọi voice zh-*");
    lines.push("- Script không Pinyin, không chữ Hán.");
    if (paste) {
      lines.push("");
      lines.push("--- Nội dung / giáo án dán ---");
      lines.push(paste);
    }
    lines.push("");
    lines.push(
      "Khi xong, trả đúng một dòng URL classroom tuyệt đối trên " +
        om.url.replace(/^https?:\/\//, "").split("/")[0] +
        " (không markdown)."
    );
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
      var om = loadOm();
      var lr = omLangRules(lang);
      parts.push(
        "OpenMAIC self-host: " +
          om.url +
          " (KHÔNG Live Demo / open.maic.chat)."
      );
      if (om.code) parts.push("Mã site OpenMAIC (nhập 1 lần): " + om.code);
      parts.push(
        "OpenMAIC language=" +
          (lr.isVi ? "vi" : lr.code) +
          "; TTS OpenAI/Edge (nova/alloy); CẤM Browser Native / Doubao / Qwen / zh-*."
      );
      parts.push(
        "Cuối gói: ghi khối handoff OpenMAIC (self-host + language + TTS) để user copy sang Generate classroom."
      );
    }
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

  window.renderBaiGiang = function (root) {
    if (!root) return;
    var uploaded = [];
    var es = null;
    var tabIdx = 0;
    var running = false;

    root.innerHTML =
      '<div class="jw" id="bgJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Tạo bài giảng</h2>" +
      '<p class="jw-lead">Chọn loại đầu ra ở tab, điền brief hoặc <b>dán giáo án</b> bên trái. Tab Lớp học: lưu mã OpenMAIC 1 lần. File trong <code>exports/bai-giang/</code>.</p></div>' +
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
        '<input id="bgAudience" type="text" placeholder="VD: học sinh THCS, sinh viên năm 1"></div>' +
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
      var om = loadOm();
      return (
        '<div class="jw-om" id="bgOmPanel">' +
        '<p class="jw-brief-kicker">OpenMAIC (lớp học live)</p>' +
        "<p class=\"jw-hint\">Self-host + <b>language=vi</b> + TTS Edge. Không Live Demo / Browser Native (tránh giọng Trung).</p>" +
        '<div class="jw-field"><label for="bgOmUrl">URL OpenMAIC</label>' +
        '<input id="bgOmUrl" type="url" value="' +
        esc(om.url) +
        '" placeholder="' +
        esc(OM_DEFAULT_URL) +
        '"></div>' +
        '<div class="jw-field"><label for="bgOmCode">Mã site (ACCESS_CODE)</label>' +
        '<input id="bgOmCode" type="text" autocomplete="off" value="' +
        esc(om.code) +
        '" placeholder="' +
        esc(OM_DEFAULT_CODE) +
        '">' +
        '<p class="jw-hint">Nhập trên OpenMAIC 1 lần / trình duyệt (~7 ngày). Để trống nếu site không hỏi mã.</p></div>' +
        '<div class="jw-actions jw-om-actions">' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmSave">Lưu mã & URL</button>' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmCopyCmd">Copy lệnh OpenMAIC</button>' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmCopy">Copy brief</button>' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgOmOpen">Mở OpenMAIC</button>' +
        "</div></div>"
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

      var saveBtn = root.querySelector("#bgOmSave");
      var copyBtn = root.querySelector("#bgOmCopy");
      var copyCmdBtn = root.querySelector("#bgOmCopyCmd");
      var openBtn = root.querySelector("#bgOmOpen");

      function persistOmFields() {
        var urlEl = root.querySelector("#bgOmUrl");
        var codeEl = root.querySelector("#bgOmCode");
        if (urlEl || codeEl) {
          saveOm(
            (urlEl && urlEl.value) || loadOm().url,
            (codeEl && codeEl.value) || ""
          );
        }
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
          setStatus("Clipboard bị chặn — xem cột Kết quả để copy tay.", false);
        }
      }

      if (saveBtn) {
        saveBtn.onclick = function () {
          var url = ((root.querySelector("#bgOmUrl") || {}).value || "").trim();
          var code = ((root.querySelector("#bgOmCode") || {}).value || "").trim();
          if (!url) {
            setStatus("Thiếu URL OpenMAIC.", false);
            return;
          }
          saveOm(url, code);
          setStatus("Đã lưu OpenMAIC URL + mã site (trình duyệt này).", true);
        };
      }
      if (copyCmdBtn) {
        copyCmdBtn.onclick = async function () {
          persistOmFields();
          var text = buildOpenmaicHandoff({
            topic: ((root.querySelector("#bgTopic") || {}).value || "").trim() || "(chưa ghi chủ đề)",
            goals: ((root.querySelector("#bgGoals") || {}).value || "").trim(),
            paste: ((root.querySelector("#bgPaste") || {}).value || "").trim(),
            lang: ((root.querySelector("#bgLang") || {}).value || "vi").trim(),
            slugHint: "exports/bai-giang/<slug>/lop-hoc.md",
          });
          await copyText(text, "Đã copy lệnh OpenMAIC (vi + TTS Edge) — dán vào chat/Generate.");
        };
      }
      if (copyBtn) {
        copyBtn.onclick = async function () {
          persistOmFields();
          var topic = ((root.querySelector("#bgTopic") || {}).value || "").trim() || "(chưa ghi chủ đề)";
          var goals = ((root.querySelector("#bgGoals") || {}).value || "").trim();
          var paste = ((root.querySelector("#bgPaste") || {}).value || "").trim();
          var lang = ((root.querySelector("#bgLang") || {}).value || "vi").trim();
          var om = loadOm();
          var text =
            composeBrief(topic, "", goals, lang, fmt(), uploaded, paste) +
            "\n\n--- Lệnh OpenMAIC ---\n" +
            buildOpenmaicHandoff({
              topic: topic,
              goals: goals,
              paste: paste,
              lang: lang,
            }) +
            "\n\n→ Dán lệnh vào Generate trên " +
            om.url +
            " (không lấy mã cloud).";
          await copyText(text, "Đã copy brief + lệnh OpenMAIC (chuẩn tiếng Việt).");
        };
      }
      if (openBtn) {
        openBtn.onclick = function () {
          persistOmFields();
          var om = loadOm();
          var url = om.url || OM_DEFAULT_URL;
          window.open(url, "_blank", "noopener,noreferrer");
          setStatus(
            "Đã mở OpenMAIC. Settings TTS → OpenAI (Edge). language=vi. Mã: «" +
              (om.code || OM_DEFAULT_CODE) +
              "».",
            true
          );
        };
      }
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
      if (f.id === "lop-hoc") {
        var urlEl = root.querySelector("#bgOmUrl");
        var codeEl = root.querySelector("#bgOmCode");
        if (urlEl || codeEl) {
          saveOm((urlEl && urlEl.value) || loadOm().url, (codeEl && codeEl.value) || "");
        }
      }
      var brief = composeBrief(v.topic, v.audience, v.goals, v.lang, f, uploaded, v.paste);

      setBusy(true, "Đang chạy «" + f.full + "»…");
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
              var omDone = loadOm();
              var handoff = buildOpenmaicHandoff({
                topic: v.topic,
                goals: v.goals,
                paste: v.paste,
                lang: v.lang,
                slugHint: "exports/bai-giang/<slug>/lop-hoc.md",
              });
              appendLog(
                "OpenMAIC: " +
                  omDone.url +
                  " | mã: " +
                  (omDone.code || "(không)") +
                  " | language=vi + TTS Edge\n→ Bấm «Copy lệnh OpenMAIC» bên trái.\n\n" +
                  handoff
              );
            }
            finishBusy(
              f.id === "lop-hoc"
                ? "Xong. Copy lệnh OpenMAIC (vi + Edge TTS) — không Live Demo."
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
