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
      full: "Kiểm SEO + SEO GPT",
      tagline: "Google on-page · tối ưu cho chat AI",
      when: "Có URL/bản nháp: cần lỗi SEO thường VÀ SEO GPT (để LLM dễ đọc và đưa vào khi chat).",
      gets: [
        "Điểm SEO cổ điển (title, meta, H1…)",
        "Điểm SEO GPT (lead trả lời thẳng, FAQ, entity)",
        "Checklist P0–P2 + lead/FAQ đề xuất",
      ],
      example: "Landing thiếu câu trả lời đầu trang → AI khó trích; thêm lead + FAQ.",
      time: "~5–15 phút",
      topicPh: "URL hoặc tên trang cần kiểm",
      topicLabel: "URL / trang *",
    },
    {
      id: "viet-seo",
      slug: "bo-marketing-viet-seo",
      label: "Viết SEO",
      full: "Viết bài SEO + SEO GPT",
      tagline: "Xếp tìm kiếm · dễ AI trích dẫn",
      when: "Cần bài web vừa SEO Google vừa dễ ChatGPT/Claude/Gemini đưa vào câu trả lời khi chat.",
      gets: [
        "Lead trả lời thẳng + bài đầy đủ",
        "Title, meta, slug + FAQ 3–6",
        "Khối «đoạn chat có thể trích» + entity",
      ],
      example: "«học vẽ online Hà Nội?» → lead 60 chữ + FAQ + meta.",
      time: "~15–30 phút",
      topicPh: "Chủ đề / từ khóa / câu hỏi chat chính",
      topicLabel: "Chủ đề / câu hỏi *",
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
      id: "facebook-page",
      slug: "bo-marketing-facebook",
      label: "Page FB",
      full: "Facebook Page (organic)",
      tagline: "Bài đăng · tương tác · ý tưởng tuần",
      when: "Xem Page đã đấu, bài đăng kỳ gần đây, gợi ý nội dung tuần tới.",
      gets: [
        "Trạng thái Page đã kết nối",
        "Bảng bài đăng trong kỳ",
        "3 gợi ý nội dung tuần tới",
      ],
      example: "«7 ngày» → 4 bài Page, chủ đề nổi, 3 caption gợi ý.",
      time: "~5–15 phút",
      topicPh: "VD: 7 ngày gần nhất (thêm tên Page nếu có nhiều)",
      topicLabel: "Kỳ / Page *",
    },
    {
      id: "facebook-ads",
      slug: "bo-marketing-ads",
      label: "Ads FB",
      full: "Báo cáo Facebook Ads",
      tagline: "Spend · CTR · CPC · CPM · campaign",
      when: "Cần báo cáo ads đủ số đo, bảng chiến dịch, giải thích dễ hiểu.",
      gets: [
        "Tóm tắt tình hình 30 giây",
        "Bảng số: spend, reach, CTR, CPC, CPM, chuyển đổi",
        "Bảng từng chiến dịch + việc nên làm",
      ],
      example: "Kỳ last_7d → chi tiêu, CTR, campaign tốt/yếu rõ ràng.",
      time: "~5–20 phút (cần Meta Ads)",
      topicPh: "Để trống = mọi account mặc định; hoặc tên/id account",
      topicLabel: "Ad account (tuỳ chọn)",
      topicOptional: true,
      needsPeriod: true,
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

  function composeBrief(topic, audience, goals, lang, feat, files, period) {
    var parts = [
      "Việc Marketing: " + (feat ? feat.full : ""),
      "Chủ đề / đầu vào: " + (topic || "(không ghi)"),
      "Đối tượng: " + (audience || "(chưa ghi)"),
      "Mục tiêu: " + (goals || "(chưa ghi - agent hỏi nếu thiếu)"),
      "Ngôn ngữ: " + (lang || "vi"),
    ];
    if (period) parts.push("Kỳ báo cáo (date_preset): " + period);
    if (feat) {
      parts.push("Mô tả: " + feat.tagline);
      parts.push("Ví dụ tham chiếu: " + feat.example);
      if (feat.id === "facebook-ads") {
        parts.push(
          "Yêu cầu báo cáo: bảng số tổng (spend, impressions, reach, frequency, clicks, CTR, CPC, CPM, actions) + bảng campaign + tóm tắt dễ hiểu + việc nên làm."
        );
      }
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
    var running = false;

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
      '<div class="jw-empty" id="mktEmpty"><strong>Chọn việc rồi chạy</strong>Kết quả SEO, bài viết, nghiên cứu, Page FB hoặc báo cáo Ads (đủ số đo) hiện tại đây.</div>' +
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
        (f.needsPeriod
          ? '<div class="jw-field"><label for="mktPeriod">Kỳ báo cáo Ads *</label>' +
            '<select id="mktPeriod">' +
            '<option value="last_7d">7 ngày gần nhất</option>' +
            '<option value="last_14d">14 ngày gần nhất</option>' +
            '<option value="last_30d">30 ngày gần nhất</option>' +
            '<option value="this_month">Tháng này</option>' +
            '<option value="last_month">Tháng trước</option>' +
            '<option value="yesterday">Hôm qua</option>' +
            "</select>" +
            '<p class="jw-hint">Báo cáo gồm: tóm tắt tình hình, bảng số tổng, bảng từng chiến dịch, việc nên làm.</p></div>'
          : "") +
        '<div class="jw-field"><label for="mktAudience">Đối tượng / thương hiệu</label>' +
        '<input id="mktAudience" type="text" placeholder="VD: phụ huynh THCS, SME F&B"></div>' +
        '<div class="jw-field"><label for="mktGoals">Mục tiêu</label>' +
        '<textarea id="mktGoals" rows="3" placeholder="VD: tăng organic&#10;soạn content tuần"></textarea></div>' +
        '<div class="jw-field"><label for="mktLang">Ngôn ngữ</label>' +
        '<select id="mktLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
        '<div class="jw-field"><label for="mktFiles">File đính kèm</label>' +
        '<input id="mktFiles" type="file" multiple>' +
        '<p class="jw-hint" id="mktFileList">Bản nháp, brief, ảnh… (tuỳ chọn)</p></div>' +
        (f.id === "facebook-page"
          ? '<p class="jw-hint">Cần connector Store: <b>facebook-pages</b>. Thiếu thì kết quả hướng dẫn đấu nối.</p>'
          : "") +
        (f.id === "facebook-ads"
          ? '<p class="jw-hint">Cần connector Store: <b>meta-ads-graph</b> (Meta Ads). Chỉ đọc số - không tự sửa campaign.</p>'
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
        try { if (es) es.close(); } catch (e) {}
        es = null;
        setBusy(false, "Đã dừng theo dõi (việc trên server có thể vẫn chạy).", true);
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
      var f = feat();
      var runBtn = root.querySelector("#mktRun");
      var stopBtn = root.querySelector("#mktStop");
      var seedBtn = root.querySelector("#mktSeed");
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
      var topic = ((root.querySelector("#mktTopic") || {}).value || "").trim();
      var goals = ((root.querySelector("#mktGoals") || {}).value || "").trim();
      var period = "";
      if (f.needsPeriod) {
        period = ((root.querySelector("#mktPeriod") || {}).value || "").trim();
      }
      var missing = [];
      if (!f.topicOptional && !topic) {
        markField("mktTopic", true);
        missing.push((f.topicLabel || "Đầu vào").replace(/\s*\*$/, ""));
      }
      if (f.needsPeriod && !period) {
        markField("mktPeriod", true);
        missing.push("Kỳ báo cáo");
      }
      if ((f.id === "viet-seo" || f.id === "nghien-cuu" || f.id === "kiem-seo") && !goals) {
        markField("mktGoals", true);
        missing.push("Mục tiêu");
      }
      if (missing.length) {
        setStatus("Thiếu thông tin: " + missing.join(", ") + ". Điền bên trái rồi bấm Chạy.", false);
        return null;
      }
      if (!topic && f.needsPeriod) topic = "Báo cáo Ads đủ số đo";
      return {
        topic: topic,
        period: period || (f.needsPeriod ? "last_7d" : ""),
        audience: ((root.querySelector("#mktAudience") || {}).value || "").trim(),
        goals: goals,
        lang: ((root.querySelector("#mktLang") || {}).value || "vi").trim(),
        feat: f,
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

    root.querySelector("#mktSeed").onclick = async function () {
      if (running) return;
      var seedBtn = root.querySelector("#mktSeed");
      if (seedBtn) {
        seedBtn.disabled = true;
        seedBtn.textContent = "Đang chuẩn bị…";
      }
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
      var brief = composeBrief(v.topic, v.audience, v.goals, v.lang, f, uploaded, v.period);

      setBusy(true, "Đang chạy «" + f.full + "»…");
      if (es) {
        try { es.close(); } catch (e1) {}
        es = null;
      }
      var log = root.querySelector("#mktLog");
      if (log) log.innerHTML = "";
      appendLog("--- Brief ---\n" + brief + "\n---");

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        await fetch("/studio/seed-marketing", { method: "POST", body: fd0 });
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
            appendLog("[xong bước] " + (data.agent || ""));
            if (data.output) {
              var out = String(data.output);
              appendLog(out.length > 5000 ? out.slice(0, 5000) + "\n…(cắt)" : out);
            }
          } else if (typ === "error") {
            appendLog("ERROR: " + (data.message || data.error || ev.data));
            finishBusy("Lỗi khi chạy", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 8000 ? res.slice(0, 8000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            finishBusy("Xong. Xem exports/marketing/ trong Files.", true);
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
