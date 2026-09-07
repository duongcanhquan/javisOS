/**
 * Công việc → Marketing: workbench full màn.
 * Tab từng việc; trái = lệnh/input; phải = kết quả.
 */
(function () {
  "use strict";

  var FEATURES = [
    {
      id: "kiem-seo",
      slug: "bo-marketing-kiem-seo",
      label: "Kiểm SEO",
      full: "Kiểm SEO",
      tagline: "Soi trang / bản nháp trước khi đăng",
      when: "Có URL hoặc bản viết và muốn lỗi SEO + cách sửa theo ưu tiên.",
      gets: ["Bảng điểm on-page", "Checklist P0 / P1 / P2", "2–3 title + meta đề xuất"],
      example: "https://truong.edu.vn/khoa-hoc → thiếu meta, H1 trùng, đề xuất title mới.",
      time: "~5–15 phút",
      topicPh: "URL hoặc tên trang cần kiểm",
      topicLabel: "URL / trang *",
    },
    {
      id: "viet-seo",
      slug: "bo-marketing-viet-seo",
      label: "Viết SEO",
      full: "Viết bài SEO",
      tagline: "Bài web có từ khóa, đọc tự nhiên",
      when: "Cần blog/landing kéo tìm kiếm hữu cơ, kèm meta sẵn đăng.",
      gets: ["Outline + bài đầy đủ", "Title, meta, slug", "CTA + ví dụ trong bài"],
      example: "«học vẽ online Hà Nội» → ~1200 chữ + FAQ + meta.",
      time: "~15–30 phút",
      topicPh: "Chủ đề / từ khóa chính",
      topicLabel: "Chủ đề / từ khóa *",
    },
    {
      id: "nghien-cuu",
      slug: "bo-marketing-nghien-cuu",
      label: "Nghiên cứu",
      full: "Nghiên cứu thị trường",
      tagline: "Phân khúc · đối thủ · insight",
      when: "Trước content/ads - cần bức tranh thị trường có nguồn.",
      gets: ["Phân khúc + JTBD", "Đối thủ / khoảng trống", "Insight + Sources"],
      example: "«Trường nghệ thuật Hà Nội» → SOM ước + đối thủ + góc content.",
      time: "~20–40 phút",
      topicPh: "Sản phẩm / thị trường cần nghiên cứu",
      topicLabel: "Thị trường / sản phẩm *",
    },
    {
      id: "facebook",
      slug: "bo-marketing-facebook",
      label: "Facebook",
      full: "Facebook & Ads",
      tagline: "Kết nối Page/Ads + tổng kết kỳ",
      when: "Xem Page đã đấu, bài đăng / ads kỳ gần đây (số thật từ MCP).",
      gets: ["Trạng thái kết nối", "Tóm tắt posts / insights", "3 gợi ý nội dung"],
      example: "«7 ngày gần nhất» → 4 bài, 1 campaign, 3 caption gợi ý.",
      time: "~5–20 phút",
      topicPh: "VD: 7 ngày gần nhất + tên Page (nếu nhiều)",
      topicLabel: "Kỳ / Page *",
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

  function composeBrief(topic, audience, goals, lang, feat, files) {
    var parts = [
      "Việc Marketing: " + (feat ? feat.full : ""),
      "Chủ đề / đầu vào: " + topic,
      "Đối tượng: " + (audience || "(chưa ghi)"),
      "Mục tiêu: " + (goals || "(chưa ghi - agent hỏi nếu thiếu)"),
      "Ngôn ngữ: " + (lang || "vi"),
    ];
    if (feat) {
      parts.push("Mô tả: " + feat.tagline);
      parts.push("Ví dụ tham chiếu: " + feat.example);
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

  window.renderMarketing = function (root) {
    if (!root) return;
    var uploaded = [];
    var es = null;
    var tabIdx = 0;

    root.innerHTML =
      '<div class="jw" id="mktJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Marketing</h2>" +
      '<p class="jw-lead">Mỗi tab là một việc riêng. Trái: lệnh và input. Phải: kết quả chạy. Cũng gọi được từ chat / Telegram / Zalo.</p></div>' +
      '<div class="jw-top-actions">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="mktSeed">Chuẩn bị lần đầu</button>' +
      "</div></div>" +
      '<div class="jw-tabs" role="tablist" id="mktTabs"></div>' +
      "</div>" +
      '<div class="jw-body">' +
      '<aside class="jw-left"><div class="jw-left-scroll" id="mktLeft"></div></aside>' +
      '<section class="jw-right">' +
      '<div class="jw-right-head"><h3>Kết quả</h3><div class="jw-status" id="mktStatus">Chưa chạy</div></div>' +
      '<div class="jw-out" id="mktOut">' +
      '<div class="jw-empty" id="mktEmpty"><strong>Chọn việc rồi chạy</strong>Kết quả SEO, bài viết, nghiên cứu hoặc tổng kết Facebook hiện tại đây.</div>' +
      '<pre class="jw-log" id="mktLog" hidden></pre>' +
      "</div></section>" +
      "</div></div>";

    var tabsEl = root.querySelector("#mktTabs");
    tabsEl.innerHTML = FEATURES.map(function (f, i) {
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

    function feat() {
      return FEATURES[tabIdx] || FEATURES[0];
    }

    function setStatus(msg, kind) {
      var el = root.querySelector("#mktStatus");
      if (!el) return;
      el.textContent = msg || "";
      el.className = "jw-status" + (kind === false ? " err" : kind === true ? " ok" : "");
    }

    function showLog() {
      var empty = root.querySelector("#mktEmpty");
      var log = root.querySelector("#mktLog");
      if (empty) empty.hidden = true;
      if (log) log.hidden = false;
    }

    function appendLog(line) {
      showLog();
      var log = root.querySelector("#mktLog");
      if (!log) return;
      log.innerHTML += formatLogLine(line) + "\n";
      var out = root.querySelector("#mktOut");
      if (out) out.scrollTop = out.scrollHeight;
    }

    function paintLeft() {
      var f = feat();
      var gets = (f.gets || []).map(function (g) {
        return "<li>" + esc(g) + "</li>";
      }).join("");
      var left = root.querySelector("#mktLeft");
      left.innerHTML =
        '<div class="jw-brief">' +
        '<p class="jw-brief-kicker">Việc đang chọn</p>' +
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
        '<div class="jw-field"><label for="mktTopic">' +
        esc(f.topicLabel || "Đầu vào *") +
        "</label>" +
        '<input id="mktTopic" type="text" autocomplete="off" placeholder="' +
        esc(f.topicPh) +
        '"></div>' +
        '<div class="jw-field"><label for="mktAudience">Đối tượng / thương hiệu</label>' +
        '<input id="mktAudience" type="text" placeholder="VD: phụ huynh THCS, SME F&B"></div>' +
        '<div class="jw-field"><label for="mktGoals">Mục tiêu</label>' +
        '<textarea id="mktGoals" rows="3" placeholder="VD: tăng organic&#10;soạn content tuần"></textarea></div>' +
        '<div class="jw-field"><label for="mktLang">Ngôn ngữ</label>' +
        '<select id="mktLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
        '<div class="jw-field"><label for="mktFiles">File đính kèm</label>' +
        '<input id="mktFiles" type="file" multiple>' +
        '<p class="jw-hint" id="mktFileList">Bản nháp, brief, ảnh… (tuỳ chọn)</p></div>' +
        (f.id === "facebook"
          ? '<p class="jw-hint">Cần connector Store: facebook-pages / meta-ads-graph. Thiếu thì kết quả sẽ hướng dẫn đấu nối.</p>'
          : "") +
        '<div class="jw-actions">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="mktRun">Chạy: ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="mktStop" disabled>Dừng xem</button>' +
        "</div>";

      wireLeft();
    }

    function wireLeft() {
      root.querySelector("#mktFiles").onchange = async function () {
        var files = Array.from((root.querySelector("#mktFiles").files) || []);
        uploaded = [];
        var list = root.querySelector("#mktFileList");
        if (!files.length) {
          if (list) list.textContent = "Bản nháp, brief, ảnh… (tuỳ chọn)";
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

      root.querySelector("#mktStop").onclick = function () {
        if (es) {
          try { es.close(); } catch (e) {}
          es = null;
        }
        root.querySelector("#mktStop").disabled = true;
        setStatus("Đã dừng theo dõi.", true);
      };

      root.querySelector("#mktRun").onclick = run;
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

    root.querySelector("#mktSeed").onclick = async function () {
      setStatus("Đang chuẩn bị agent + workflow…");
      try {
        var fd = new FormData();
        fd.append("brain", brain());
        var r = await (await fetch("/studio/seed-marketing", { method: "POST", body: fd })).json();
        if (!r || !r.ok) {
          setStatus((r && r.error) || "Chuẩn bị thất bại", false);
          return;
        }
        setStatus("Sẵn sàng " + (r.workflows || []).length + " việc Marketing.", true);
      } catch (e) {
        setStatus(String((e && e.message) || e), false);
      }
    };

    async function run() {
      var topic = ((root.querySelector("#mktTopic") || {}).value || "").trim();
      if (!topic) {
        setStatus("Nhập đầu vào bên trái trước.", false);
        return;
      }
      var f = feat();
      var audience = ((root.querySelector("#mktAudience") || {}).value || "").trim();
      var goals = ((root.querySelector("#mktGoals") || {}).value || "").trim();
      var lang = ((root.querySelector("#mktLang") || {}).value || "vi").trim();
      var brief = composeBrief(topic, audience, goals, lang, f, uploaded);

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        await fetch("/studio/seed-marketing", { method: "POST", body: fd0 });
      } catch (e0) {}

      if (es) {
        try { es.close(); } catch (e1) {}
      }
      var log = root.querySelector("#mktLog");
      if (log) log.innerHTML = "";
      appendLog("--- Brief ---\n" + brief + "\n---");
      setStatus("Đang chạy «" + f.full + "»…");
      root.querySelector("#mktStop").disabled = false;
      root.querySelector("#mktRun").disabled = true;

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
            appendLog("[xong bước] " + (data.agent || ""));
            if (data.output) {
              var out = String(data.output);
              appendLog(out.length > 5000 ? out.slice(0, 5000) + "\n…(cắt)" : out);
            }
          } else if (typ === "error") {
            appendLog("ERROR: " + (data.message || data.error || ev.data));
            setStatus("Lỗi khi chạy", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 8000 ? res.slice(0, 8000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            setStatus("Xong. Xem exports/marketing/ trong Files.", true);
            es.close();
            es = null;
            root.querySelector("#mktStop").disabled = true;
            root.querySelector("#mktRun").disabled = false;
          } else {
            appendLog(ev.data);
          }
        } catch (eParse) {
          appendLog(ev.data);
        }
      };
      es.onerror = function () {
        setStatus("Mất kết nối stream (có thể đã xong).", false);
        root.querySelector("#mktRun").disabled = false;
        root.querySelector("#mktStop").disabled = true;
        try { if (es) es.close(); } catch (e2) {}
        es = null;
      };
    }

    paintLeft();
  };
})();
