/**
 * Công việc → Marketing: workbench full màn.
 * Nhóm tab: SEO | Nghiên cứu | Facebook. Trái = brief; phải = kết quả.
 */
(function () {
  "use strict";

  var FEATURES = [
    {
      id: "kiem-seo",
      group: "SEO",
      slug: "bo-marketing-kiem-seo",
      label: "Kiểm SEO",
      blurb: "On-page + SEO GPT",
      full: "Kiểm SEO + SEO GPT",
      tagline: "Google on-page · tối ưu cho chat AI",
      when: "Có URL/bản nháp: tìm lỗi SEO cổ điển và SEO GPT (để LLM dễ trích).",
      gets: [
        "Điểm SEO cổ điển (title, meta, H1…)",
        "Điểm SEO GPT (lead, FAQ, entity)",
        "Checklist P0-P2",
      ],
      example: "Landing thiếu lead đầu trang → thêm lead + FAQ.",
      time: "~5-15 phút · kèm bước nghiên cứu ngắn",
      topicPh: "https://… hoặc tên trang",
      topicLabel: "URL / trang *",
      goalsOptionalIfUrl: true,
    },
    {
      id: "viet-seo",
      group: "SEO",
      slug: "bo-marketing-viet-seo",
      label: "Viết bài SEO",
      blurb: "Bài web + FAQ AI",
      full: "Viết bài SEO + SEO GPT",
      tagline: "Xếp tìm kiếm · dễ AI trích dẫn",
      when: "Cần bài web SEO Google và dễ ChatGPT/Claude/Gemini trích dẫn.",
      gets: ["Lead trả lời thẳng + bài đầy đủ", "Title, meta, slug + FAQ", "Khối «đoạn chat có thể trích»"],
      example: "«học vẽ online Hà Nội?» → lead 60 chữ + FAQ + meta.",
      time: "~15-30 phút · kèm bước nghiên cứu ngắn",
      topicPh: "Chủ đề / từ khóa / câu hỏi chat",
      topicLabel: "Chủ đề / câu hỏi *",
    },
    {
      id: "nghien-cuu",
      group: "Nghiên cứu",
      slug: "bo-marketing-nghien-cuu",
      label: "Thị trường",
      blurb: "Phân khúc · đối thủ",
      full: "Nghiên cứu thị trường",
      tagline: "Phân khúc · đối thủ · insight",
      when: "Trước content/ads  -  cần bức tranh thị trường có nguồn.",
      gets: ["Phân khúc + JTBD", "Đối thủ / khoảng trống", "Insight + Sources"],
      example: "«Trường nghệ thuật Hà Nội» → SOM + đối thủ + góc content.",
      time: "~20-40 phút",
      topicPh: "Sản phẩm / thị trường cần nghiên cứu",
      topicLabel: "Thị trường / sản phẩm *",
    },
    {
      id: "facebook-page",
      group: "Facebook",
      slug: "bo-marketing-facebook",
      label: "Page",
      blurb: "Organic · ý tưởng tuần",
      full: "Facebook Page (organic)",
      tagline: "Bài đăng · tương tác · ý tưởng tuần",
      when: "Xem Page đã đấu, bài đăng kỳ gần đây, gợi ý nội dung tuần tới.",
      gets: ["Trạng thái Page đã kết nối", "Bảng bài đăng trong kỳ", "3 gợi ý nội dung tuần tới"],
      example: "7 ngày → 4 bài Page, chủ đề nổi, 3 caption gợi ý.",
      time: "~5-15 phút",
      topicPh: "Tên Page (nếu có nhiều); để trống = Page mặc định",
      topicLabel: "Page (tuỳ chọn)",
      topicOptional: true,
      needsPeriod: true,
      connectorId: "facebook-pages",
      periodLabel: "Kỳ xem Page *",
    },
    {
      id: "facebook-ads",
      group: "Facebook",
      slug: "bo-marketing-ads",
      label: "Ads",
      blurb: "Spend · CTR · campaign",
      full: "Báo cáo Facebook Ads",
      tagline: "Spend · CTR · CPC · CPM · campaign",
      when: "Báo cáo ads đủ số đo, bảng chiến dịch, việc nên làm.",
      gets: [
        "Tóm tắt tình hình 30 giây",
        "Bảng số: spend, reach, CTR, CPC, CPM",
        "Bảng từng chiến dịch + việc nên làm",
      ],
      example: "Kỳ last_7d → chi tiêu, CTR, campaign tốt/yếu.",
      time: "~5-20 phút",
      topicPh: "Để trống = account mặc định; hoặc tên/id account",
      topicLabel: "Ad account (tuỳ chọn)",
      topicOptional: true,
      needsPeriod: true,
      connectorId: "meta-ads-graph",
      periodLabel: "Kỳ báo cáo Ads *",
    },
  ];

  var MKT_FIELD_IDS = ["mktTopic", "mktAudience", "mktGoals", "mktLang", "mktPeriod"];

  var PERIOD_OPTS =
    '<option value="last_7d">7 ngày gần nhất</option>' +
    '<option value="last_14d">14 ngày gần nhất</option>' +
    '<option value="last_30d">30 ngày gần nhất</option>' +
    '<option value="this_month">Tháng này</option>' +
    '<option value="last_month">Tháng trước</option>' +
    '<option value="yesterday">Hôm qua</option>';

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

  function looksLikeUrl(s) {
    return /^https?:\/\//i.test(String(s || "").trim());
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
      if (feat.id === "facebook-page") {
        parts.push(
          "Yêu cầu Page: trạng thái kết nối, bảng bài đăng trong kỳ, insight tương tác, 3 gợi ý nội dung tuần tới."
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
    var runFinished = false;
    var draft = {};
    var connCache = null;
    var connOk = true;

    root.innerHTML =
      '<div class="jw" id="mktJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Marketing</h2>" +
      '<p class="jw-lead">SEO · Nghiên cứu · Facebook. Trái: brief. Phải: kết quả. File xong ở Files → exports/marketing/. Tab Facebook cần connector đã đấu.</p></div>' +
      '<div class="jw-top-actions">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="mktSeed">Chuẩn bị lần đầu</button>' +
      "</div></div>" +
      '<div class="jw-tab-groups" id="mktTabGroups"></div>' +
      '<p class="jw-tab-hint" id="mktTabHint"></p>' +
      "</div>" +
      '<div class="jw-body">' +
      '<aside class="jw-left"><div class="jw-left-scroll" id="mktLeft"></div></aside>' +
      '<section class="jw-right">' +
      '<div class="jw-right-head"><h3>Kết quả</h3><div class="jw-status" id="mktStatus">Chưa chạy</div></div>' +
      '<div class="jw-out" id="mktOut">' +
      '<div class="jw-empty" id="mktEmpty"><strong>Chọn việc rồi chạy</strong>SEO, nghiên cứu, Page hoặc Ads hiện tại đây.</div>' +
      '<pre class="jw-log" id="mktLog" hidden></pre>' +
      "</div></section>" +
      "</div></div>";

    var groupsEl = root.querySelector("#mktTabGroups");
    var groups = [];
    FEATURES.forEach(function (f, i) {
      var g = f.group || "Khác";
      var found = null;
      for (var gi = 0; gi < groups.length; gi++) {
        if (groups[gi].name === g) {
          found = groups[gi];
          break;
        }
      }
      if (!found) {
        found = { name: g, items: [] };
        groups.push(found);
      }
      found.items.push({ f: f, i: i });
    });

    groupsEl.innerHTML = groups
      .map(function (g) {
        var tabs = g.items
          .map(function (it) {
            return (
              '<button type="button" class="jw-tab jw-tab-stack' +
              (it.i === 0 ? " on" : "") +
              '" role="tab" aria-selected="' +
              (it.i === 0 ? "true" : "false") +
              '" data-i="' +
              it.i +
              '"><span class="jw-tab-label">' +
              esc(it.f.label) +
              '</span><span class="jw-tab-blurb">' +
              esc(it.f.blurb || "") +
              "</span></button>"
            );
          })
          .join("");
        return (
          '<div class="jw-tab-group"><span class="jw-tab-group-lab">' +
          esc(g.name) +
          '</span><div class="jw-tabs jw-tabs-video" role="tablist">' +
          tabs +
          "</div></div>"
        );
      })
      .join("");

    function feat() {
      return FEATURES[tabIdx] || FEATURES[0];
    }

    function paintTabHint() {
      var f = feat();
      var el = root.querySelector("#mktTabHint");
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

    function saveDraft() {
      MKT_FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (el) draft[id] = el.value;
      });
    }

    function restoreDraft() {
      MKT_FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (el && draft[id] != null && draft[id] !== "") el.value = draft[id];
      });
      var list = root.querySelector("#mktFileList");
      if (list && uploaded.length) list.textContent = "Đã tải: " + uploaded.join(", ");
    }

    function gotoConnect() {
      try {
        if (window.Alpine && Alpine.store("nav")) Alpine.store("nav").go("mcp");
      } catch (e) {}
    }

    async function refreshConnectorStatus(f) {
      var box = root.querySelector("#mktConnBox");
      if (!box || !f.connectorId) {
        connOk = true;
        return;
      }
      box.innerHTML = '<p class="jw-hint">Đang kiểm tra connector…</p>';
      connOk = false;
      try {
        if (!connCache) {
          connCache = await (await fetch("/connect/catalog")).json();
        }
        var cid = f.connectorId;
        var cat = (connCache && connCache.catalog) || [];
        var conns = (connCache && connCache.connections) || [];
        var removed = (connCache && connCache.removed) || [];
        var inCat = false;
        for (var i = 0; i < cat.length; i++) {
          if (cat[i].id === cid) {
            inCat = true;
            break;
          }
        }
        var linked = [];
        for (var j = 0; j < conns.length; j++) {
          if (conns[j].connector_id === cid) linked.push(conns[j]);
        }
        var wasRemoved = false;
        for (var k = 0; k < removed.length; k++) {
          if (removed[k].id === cid) {
            wasRemoved = true;
            break;
          }
        }
        if (linked.length) {
          connOk = true;
          box.innerHTML =
            '<div class="jw-conn ok"><span class="jw-conn-dot"></span><div><b>Đã kết nối</b> · ' +
            esc(cid) +
            " (" +
            linked.length +
            ' tài khoản)<br><span class="jw-hint">Chỉ đọc báo cáo  -  không tự sửa campaign.</span></div></div>';
        } else if (wasRemoved || !inCat) {
          connOk = false;
          box.innerHTML =
            '<div class="jw-conn bad"><span class="jw-conn-dot"></span><div><b>Chưa có connector</b> · ' +
            esc(cid) +
            '<br><button type="button" class="jw-link" id="mktGotoConn">Mở Kết nối / Store để cài</button></div></div>';
        } else {
          connOk = false;
          box.innerHTML =
            '<div class="jw-conn warn"><span class="jw-conn-dot"></span><div><b>Có trong kho nhưng chưa đấu</b> · ' +
            esc(cid) +
            '<br><button type="button" class="jw-link" id="mktGotoConn">Đấu tài khoản tại Kết nối</button></div></div>';
        }
        var btn = root.querySelector("#mktGotoConn");
        if (btn) btn.onclick = gotoConnect;
      } catch (e) {
        connOk = true;
        box.innerHTML =
          '<p class="jw-hint">Không kiểm tra được connector  -  vẫn có thể chạy; nếu lỗi, mở <button type="button" class="jw-link" id="mktGotoConn">Kết nối</button>.</p>';
        var b2 = root.querySelector("#mktGotoConn");
        if (b2) b2.onclick = gotoConnect;
      }
    }

    function paintLeft() {
      var f = feat();
      var gets = (f.gets || [])
        .map(function (g) {
          return "<li>" + esc(g) + "</li>";
        })
        .join("");
      var left = root.querySelector("#mktLeft");
      left.innerHTML =
        '<div class="jw-brief jw-brief-lite">' +
        '<p class="jw-brief-kicker">' +
        esc(f.group || "Việc") +
        "</p>" +
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
        "</p></div>" +
        (f.connectorId ? '<div id="mktConnBox" class="jw-conn-box"></div>' : "") +
        '<p class="jw-sec">Brief</p>' +
        '<div class="jw-field"><label for="mktTopic">' +
        esc(f.topicLabel || "Đầu vào *") +
        "</label>" +
        '<input id="mktTopic" type="text" autocomplete="off" placeholder="' +
        esc(f.topicPh) +
        '"></div>' +
        (f.needsPeriod
          ? '<div class="jw-field"><label for="mktPeriod">' +
            esc(f.periodLabel || "Kỳ báo cáo *") +
            "</label>" +
            '<select id="mktPeriod">' +
            PERIOD_OPTS +
            "</select></div>"
          : "") +
        '<div class="jw-field"><label for="mktAudience">Đối tượng / thương hiệu</label>' +
        '<input id="mktAudience" type="text" placeholder="Ví dụ: phụ huynh THCS, SME F&B"></div>' +
        '<div class="jw-field"><label for="mktGoals">Mục tiêu' +
        (f.goalsOptionalIfUrl ? " (tuỳ chọn nếu đã có URL)" : f.id === "viet-seo" || f.id === "nghien-cuu" ? " *" : "") +
        "</label>" +
        '<textarea id="mktGoals" rows="3" placeholder="Ví dụ: tăng organic, soạn content tuần"></textarea></div>' +
        '<div class="jw-row2">' +
        '<div class="jw-field"><label for="mktLang">Ngôn ngữ</label>' +
        '<select id="mktLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
        '<div class="jw-field"><label for="mktFiles">File đính kèm</label>' +
        '<input id="mktFiles" type="file" multiple>' +
        '<p class="jw-hint" id="mktFileList">Bản nháp, brief…</p></div></div>' +
        '<div class="jw-actions jw-actions-main">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="mktRun">Chạy: ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="mktStop" disabled>Dừng xem</button>' +
        "</div>";

      restoreDraft();
      wireLeft();
      paintTabHint();
      if (f.connectorId) refreshConnectorStatus(f);
      else connOk = true;
    }

    function wireLeft() {
      MKT_FIELD_IDS.forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (!el) return;
        el.addEventListener("change", saveDraft);
        el.addEventListener("input", saveDraft);
      });

      root.querySelector("#mktFiles").onchange = async function () {
        var files = Array.from((root.querySelector("#mktFiles").files) || []);
        uploaded = [];
        var list = root.querySelector("#mktFileList");
        if (!files.length) {
          if (list) list.textContent = "Bản nháp, brief…";
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
        runFinished = true;
        try {
          if (es) es.close();
        } catch (e) {}
        es = null;
        setBusy(false, "Đã dừng theo dõi (việc trên server có thể vẫn chạy).", true);
      };

      root.querySelector("#mktRun").onclick = run;
    }

    function selectTab(i) {
      saveDraft();
      tabIdx = i;
      groupsEl.querySelectorAll(".jw-tab").forEach(function (btn) {
        var on = parseInt(btn.getAttribute("data-i"), 10) === i;
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
      groupsEl.querySelectorAll(".jw-tab").forEach(function (t) {
        t.disabled = busy;
      });
      if (statusMsg != null) setStatus(statusMsg, statusOk);
    }

    function validateInputs() {
      clearFieldErrors();
      var f = feat();
      if (f.connectorId && !connOk) {
        setStatus("Chưa đấu connector «" + f.connectorId + "». Mở Kết nối trước khi chạy.", false);
        return null;
      }
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
      var needGoals = f.id === "viet-seo" || f.id === "nghien-cuu";
      if (f.id === "kiem-seo" && !(f.goalsOptionalIfUrl && looksLikeUrl(topic))) {
        needGoals = true;
      }
      if (needGoals && !goals) {
        markField("mktGoals", true);
        missing.push("Mục tiêu");
      }
      if (missing.length) {
        setStatus("Thiếu thông tin: " + missing.join(", ") + ". Điền bên trái rồi bấm Chạy.", false);
        return null;
      }
      if (!topic && f.needsPeriod) {
        topic = f.id === "facebook-page" ? "Tóm tắt Page organic trong kỳ" : "Báo cáo Ads đủ số đo";
      }
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
      runFinished = true;
      try {
        if (es) es.close();
      } catch (e) {}
      es = null;
      setBusy(false, statusMsg, statusOk);
    }

    groupsEl.querySelectorAll(".jw-tab").forEach(function (btn) {
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

      runFinished = false;
      setBusy(true, "Đang chạy «" + f.full + "»…");
      if (es) {
        try {
          es.close();
        } catch (e1) {}
        es = null;
      }
      var log = root.querySelector("#mktLog");
      if (log) log.innerHTML = "";
      appendLog("--- Brief ---\n" + brief + "\n---");

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        var seedRes = await fetch("/studio/seed-marketing", { method: "POST", body: fd0 });
        var seedJson = await seedRes.json().catch(function () {
          return null;
        });
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
        if (runFinished || !running) return;
        finishBusy("Mất kết nối stream (có thể đã xong hoặc lỗi).", false);
      };
    }

    window._mktLeave = function () {
      runFinished = true;
      try {
        if (es) es.close();
      } catch (e) {}
      es = null;
    };

    paintLeft();
  };
})();
