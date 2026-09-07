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

  function composeBrief(topic, audience, goals, lang, fmt, files) {
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
    if (files && files.length) parts.push("File đính kèm:\n- " + files.join("\n- "));
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

    root.innerHTML =
      '<div class="jw" id="bgJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Tạo bài giảng</h2>" +
      '<p class="jw-lead">Chọn loại đầu ra ở tab, điền brief bên trái, theo dõi kết quả bên phải. File lưu trong <code>exports/bai-giang/</code>.</p></div>' +
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
        '<div class="jw-field"><label for="bgLang">Ngôn ngữ</label>' +
        '<select id="bgLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
        '<div class="jw-field"><label for="bgFiles">File đính kèm</label>' +
        '<input id="bgFiles" type="file" multiple>' +
        '<p class="jw-hint" id="bgFileList">Giáo án, PDF, ảnh… (tuỳ chọn)</p></div>' +
        '<div class="jw-actions">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="bgRun">Chạy: ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="bgStop" disabled>Dừng xem</button>' +
        "</div>";

      wireLeft();
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
        if (es) {
          try { es.close(); } catch (e) {}
          es = null;
        }
        root.querySelector("#bgStop").disabled = true;
        setStatus("Đã dừng theo dõi (server có thể vẫn chạy).", true);
      };

      root.querySelector("#bgRun").onclick = run;
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

    tabsEl.querySelectorAll(".jw-tab").forEach(function (btn) {
      btn.onclick = function () {
        selectTab(parseInt(btn.getAttribute("data-i"), 10) || 0);
      };
    });

    root.querySelector("#bgSeed").onclick = async function () {
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
      }
    };

    async function run() {
      var topic = ((root.querySelector("#bgTopic") || {}).value || "").trim();
      if (!topic) {
        setStatus("Nhập chủ đề bên trái trước.", false);
        return;
      }
      var f = fmt();
      var audience = ((root.querySelector("#bgAudience") || {}).value || "").trim();
      var goals = ((root.querySelector("#bgGoals") || {}).value || "").trim();
      var lang = ((root.querySelector("#bgLang") || {}).value || "vi").trim();
      var brief = composeBrief(topic, audience, goals, lang, f, uploaded);

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        await fetch("/studio/seed-bai-giang", { method: "POST", body: fd0 });
      } catch (e0) {}

      if (es) {
        try { es.close(); } catch (e1) {}
      }
      var log = root.querySelector("#bgLog");
      if (log) log.innerHTML = "";
      appendLog("--- Brief ---\n" + brief + "\n---");
      setStatus("Đang tạo «" + f.full + "»…");
      root.querySelector("#bgStop").disabled = false;
      root.querySelector("#bgRun").disabled = true;

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
            setStatus("Lỗi khi tạo", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 8000 ? res.slice(0, 8000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            setStatus("Xong. Xem exports/bai-giang/ trong Files.", true);
            es.close();
            es = null;
            root.querySelector("#bgStop").disabled = true;
            root.querySelector("#bgRun").disabled = false;
          } else {
            appendLog(ev.data);
          }
        } catch (eParse) {
          appendLog(ev.data);
        }
      };
      es.onerror = function () {
        setStatus("Mất kết nối stream (có thể đã xong).", false);
        root.querySelector("#bgRun").disabled = false;
        root.querySelector("#bgStop").disabled = true;
        try { if (es) es.close(); } catch (e2) {}
        es = null;
      };
    }

    paintLeft();
  };
})();
