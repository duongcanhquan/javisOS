/**
 * Trang Marketing (Công việc): chọn việc rõ ràng cho marketer/giảng viên,
 * rồi chạy workflow Gemini (SEO / nghiên cứu / Facebook).
 */
(function () {
  "use strict";

  var FEATURES = [
    {
      id: "kiem-seo",
      slug: "bo-marketing-kiem-seo",
      label: "Kiểm SEO",
      tagline: "Soi trang hoặc bản nháp trước khi đăng",
      when:
        "Bạn có URL landing/blog hoặc bản viết dở và muốn biết lỗi SEO + cách sửa theo ưu tiên.",
      gets: [
        "Bảng điểm on-page (title, meta, H1, cấu trúc)",
        "Checklist sửa P0 / P1 / P2",
        "2–3 biến thể title + meta đề xuất",
      ],
      example:
        "Dán https://truong.edu.vn/khoa-hoc-ve → báo thiếu meta, H1 trùng, đề xuất title mới.",
      time: "~5–15 phút",
      placeholderTopic: "URL hoặc tên trang cần kiểm SEO",
    },
    {
      id: "viet-seo",
      slug: "bo-marketing-viet-seo",
      label: "Viết bài SEO",
      tagline: "Bài web có từ khóa, vẫn đọc tự nhiên",
      when:
        "Cần bài blog/landing để kéo tìm kiếm hữu cơ, kèm meta sẵn đăng.",
      gets: [
        "Outline H1–H2 + bài đầy đủ",
        "Title tag, meta description, slug",
        "CTA và ví dụ cụ thể trong bài",
      ],
      example:
        "Từ khóa «học vẽ online Hà Nội» → bài ~1200 chữ + FAQ + meta.",
      time: "~15–30 phút",
      placeholderTopic: "Chủ đề / từ khóa chính của bài",
    },
    {
      id: "nghien-cuu",
      slug: "bo-marketing-nghien-cuu",
      label: "Nghiên cứu thị trường",
      tagline: "Phân khúc, đối thủ, insight trước khi chạy ads",
      when:
        "Trước khi viết content hoặc đổ ngân sách ads - cần bức tranh thị trường có nguồn.",
      gets: [
        "Phân khúc + nhu cầu (JTBD)",
        "Đối thủ / khoảng trống",
        "Insight hành động + Sources",
      ],
      example:
        "«Trường nghệ thuật tại Hà Nội» → SOM ước + 5 đối thủ + 3 góc content.",
      time: "~20–40 phút",
      placeholderTopic: "Sản phẩm / thị trường cần nghiên cứu",
    },
    {
      id: "facebook",
      slug: "bo-marketing-facebook",
      label: "Facebook & Ads",
      tagline: "Xem kết nối Page/Ads và tổng kết kỳ",
      when:
        "Muốn biết Page nào đã đấu, tuần này đăng gì, ads nào đang chạy (số thật từ MCP).",
      gets: [
        "Trạng thái kết nối (hoặc hướng dẫn cài Store)",
        "Tóm tắt bài đăng / insights kỳ",
        "3 gợi ý nội dung tuần tới",
      ],
      example:
        "«7 ngày gần nhất» → 4 bài Page, 1 campaign đang spend, gợi ý 3 caption.",
      time: "~5–20 phút (cần đã kết nối Meta)",
      placeholderTopic: "Kỳ cần xem (VD: 7 ngày gần nhất) + Page nếu có nhiều",
    },
  ];

  function brain() {
    try {
      if (typeof window.currentBrainPath === "function") {
        return window.currentBrainPath() || "brain";
      }
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
    var parts = [];
    parts.push("Việc Marketing: " + (feat ? feat.label : ""));
    parts.push("Chủ đề / đầu vào: " + topic);
    parts.push("Đối tượng: " + (audience || "(chưa ghi)"));
    parts.push("Mục tiêu: " + (goals || "(chưa ghi - agent hỏi nếu thiếu)"));
    parts.push("Ngôn ngữ: " + (lang || "vi"));
    if (feat) {
      parts.push("Mô tả: " + feat.tagline);
      parts.push("Ví dụ tham chiếu: " + feat.example);
    }
    if (files && files.length) {
      parts.push("File đính kèm:\n- " + files.join("\n- "));
    }
    return parts.join("\n");
  }

  function cardHtml(f, i) {
    var gets = (f.gets || [])
      .map(function (g) {
        return "<li>" + esc(g) + "</li>";
      })
      .join("");
    return (
      '<label class="mkt-card" data-slug="' +
      esc(f.slug) +
      '" style="display:block;padding:14px 16px;border:1.5px solid var(--line);border-radius:12px;margin:0 0 10px;cursor:pointer;background:var(--panel)">' +
      '<div style="display:flex;gap:10px;align-items:flex-start">' +
      '<input type="radio" name="mktFmt" value="' +
      esc(f.slug) +
      '"' +
      (i === 0 ? " checked" : "") +
      ' style="margin-top:4px;flex-shrink:0">' +
      '<div style="flex:1;min-width:0">' +
      '<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:baseline">' +
      "<strong style=\"font-size:15.5px\">" +
      esc(f.label) +
      "</strong>" +
      '<span class="dim" style="font-size:12.5px">' +
      esc(f.tagline) +
      "</span></div>" +
      '<p style="margin:8px 0 0;font-size:13.5px;line-height:1.45;color:var(--text2)">' +
      "<b>Chọn khi:</b> " +
      esc(f.when) +
      "</p>" +
      '<div style="margin:8px 0 0;font-size:13px;line-height:1.4"><b>Bạn nhận được:</b><ul style="margin:4px 0 0 18px;padding:0">' +
      gets +
      "</ul></div>" +
      '<p class="dim" style="margin:8px 0 0;font-size:12.5px;line-height:1.45"><b>Ví dụ:</b> ' +
      esc(f.example) +
      "</p>" +
      '<p class="dim" style="margin:6px 0 0;font-size:12px">' +
      esc(f.time) +
      "</p>" +
      "</div></div></label>"
    );
  }

  function currentFeat(root) {
    var el = root.querySelector('input[name="mktFmt"]:checked');
    var slug = el ? el.value : FEATURES[0].slug;
    return (
      FEATURES.filter(function (f) {
        return f.slug === slug;
      })[0] || FEATURES[0]
    );
  }

  function paintSelected(root) {
    root.querySelectorAll(".mkt-card").forEach(function (card) {
      var inp = card.querySelector('input[type="radio"]');
      var on = inp && inp.checked;
      card.style.borderColor = on ? "var(--accent, #3b82f6)" : "var(--line)";
      card.style.boxShadow = on ? "0 0 0 1px var(--accent, #3b82f6)" : "none";
    });
    var feat = currentFeat(root);
    var hint = root.querySelector("#mktPickHint");
    if (hint) {
      hint.innerHTML =
        "Đã chọn: <b>" +
        esc(feat.label) +
        "</b> — " +
        esc(feat.tagline) +
        ". Điền đầu vào bên dưới rồi bấm <b>Chạy</b>.";
    }
    var topic = root.querySelector("#mktTopic");
    if (topic && feat.placeholderTopic) {
      topic.placeholder = feat.placeholderTopic;
    }
    var runBtn = root.querySelector("#mktRun");
    if (runBtn) runBtn.textContent = "Chạy: " + feat.label;
  }

  window.renderMarketing = function (root) {
    if (!root) return;

    root.innerHTML =
      '<div class="si-wrap" style="max-width:860px">' +
      '<h2 style="margin:0 0 6px">Marketing</h2>' +
      '<p class="dim" style="margin:0 0 18px;line-height:1.5">Chọn <b>một việc</b> bên dưới. ' +
      "Javis dùng Gemini + skill/agent đã seed; chạy được cả trên chat, Telegram, Zalo như việc thường. " +
      "File kết quả: <code>exports/marketing/</code>.</p>" +
      '<div class="si-field" style="margin-bottom:18px">' +
      '<label style="font-size:15px;margin-bottom:8px">1. Bạn muốn làm gì?</label>' +
      '<p class="dim" style="margin:0 0 10px;font-size:13px;line-height:1.4">Mỗi thẻ có mô tả và ví dụ để chọn đúng.</p>' +
      FEATURES.map(cardHtml).join("") +
      '<p id="mktPickHint" class="dim" style="margin:8px 0 0;font-size:13px;line-height:1.4"></p>' +
      "</div>" +
      '<div style="border-top:1px solid var(--line);padding-top:16px;margin-bottom:8px">' +
      '<label style="display:block;font-size:15px;margin-bottom:10px;color:var(--text3)">2. Đầu vào</label>' +
      '<div class="si-field"><label>Chủ đề / URL / kỳ *</label>' +
      '<input type="text" id="mktTopic" autocomplete="off"></div>' +
      '<div class="si-field"><label>Đối tượng / thương hiệu</label>' +
      '<input type="text" id="mktAudience" placeholder="VD: phụ huynh học sinh cấp 2, SME F&B"></div>' +
      '<div class="si-field"><label>Mục tiêu (mỗi dòng một ý)</label>' +
      '<textarea id="mktGoals" rows="3" placeholder="VD: tăng organic&#10;soạn content tuần&#10;hiểu đối thủ"></textarea></div>' +
      '<div class="si-field"><label>Ngôn ngữ</label>' +
      '<select id="mktLang" class="loop-sel"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
      '<div class="si-field"><label>File đính kèm (tùy chọn)</label>' +
      '<input type="file" id="mktFiles" multiple>' +
      '<div class="dim" id="mktFileList" style="font-size:12.5px;margin-top:6px"></div></div>' +
      "</div>" +
      '<div class="si-actions" style="display:flex;gap:8px;flex-wrap:wrap;margin:14px 0">' +
      '<button class="s-btn" type="button" id="mktRun">Chạy</button>' +
      '<button class="s-btn-ghost" type="button" id="mktStop" disabled>Dừng xem</button>' +
      '<button class="s-btn-ghost" type="button" id="mktSeed">Chuẩn bị lần đầu</button>' +
      "</div>" +
      '<div id="mktStatus" class="dim" style="margin:0 0 10px"></div>' +
      '<details style="margin:0 0 8px"><summary class="dim" style="cursor:pointer;font-size:13px">Nhật ký chạy</summary>' +
      '<pre id="mktLog" style="max-height:360px;overflow:auto;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);font-size:12.5px;white-space:pre-wrap;margin-top:8px"></pre>' +
      "</details>" +
      '<p class="dim" style="font-size:12.5px;line-height:1.45">Facebook/Ads cần connector trên trang <b>MCP / Store</b> ' +
      "(facebook-pages, meta-ads-graph). Chat: nói «kiểm SEO …» hoặc «tổng kết Facebook tuần này».</p>" +
      "</div>";

    var uploaded = [];
    var es = null;

    paintSelected(root);
    root.querySelectorAll('input[name="mktFmt"]').forEach(function (inp) {
      inp.addEventListener("change", function () {
        paintSelected(root);
      });
    });
    root.querySelectorAll(".mkt-card").forEach(function (card) {
      card.addEventListener("click", function () {
        var inp = card.querySelector('input[type="radio"]');
        if (inp) {
          inp.checked = true;
          paintSelected(root);
        }
      });
    });

    function setStatus(msg, ok) {
      var el = root.querySelector("#mktStatus");
      if (!el) return;
      el.textContent = msg || "";
      el.style.color = ok === false ? "var(--danger-ink, #c44)" : "var(--text3)";
    }

    function appendLog(line) {
      var log = root.querySelector("#mktLog");
      if (!log) return;
      log.textContent += line + "\n";
      log.scrollTop = log.scrollHeight;
      var det = log.closest("details");
      if (det) det.open = true;
    }

    root.querySelector("#mktFiles").onchange = async function () {
      var input = root.querySelector("#mktFiles");
      var files = input && input.files ? Array.from(input.files) : [];
      uploaded = [];
      var list = root.querySelector("#mktFileList");
      if (!files.length) {
        if (list) list.textContent = "";
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

    root.querySelector("#mktSeed").onclick = async function () {
      setStatus("Đang chuẩn bị agent + workflow Marketing (Gemini)…");
      try {
        var fd = new FormData();
        fd.append("brain", brain());
        var r = await (await fetch("/studio/seed-marketing", { method: "POST", body: fd })).json();
        if (!r || !r.ok) {
          setStatus((r && r.error) || "Chuẩn bị thất bại", false);
          return;
        }
        setStatus(
          "Sẵn sàng " + (r.workflows || []).length + " việc Marketing. Chọn thẻ rồi chạy.",
          true
        );
      } catch (e) {
        setStatus(String((e && e.message) || e), false);
      }
    };

    root.querySelector("#mktStop").onclick = function () {
      if (es) {
        try {
          es.close();
        } catch (e) {}
        es = null;
      }
      root.querySelector("#mktStop").disabled = true;
      setStatus("Đã dừng theo dõi.", true);
    };

    root.querySelector("#mktRun").onclick = async function () {
      var topic = ((root.querySelector("#mktTopic") || {}).value || "").trim();
      if (!topic) {
        setStatus("Nhập chủ đề / URL / kỳ ở mục 2.", false);
        return;
      }
      var feat = currentFeat(root);
      var audience = ((root.querySelector("#mktAudience") || {}).value || "").trim();
      var goals = ((root.querySelector("#mktGoals") || {}).value || "").trim();
      var lang = ((root.querySelector("#mktLang") || {}).value || "vi").trim();
      var brief = composeBrief(topic, audience, goals, lang, feat, uploaded);

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        await fetch("/studio/seed-marketing", { method: "POST", body: fd0 });
      } catch (e0) {}

      if (es) {
        try {
          es.close();
        } catch (e1) {}
      }
      root.querySelector("#mktLog").textContent = "";
      appendLog("--- Brief ---\n" + brief + "\n---");
      setStatus("Đang chạy «" + feat.label + "»…");
      root.querySelector("#mktStop").disabled = false;
      root.querySelector("#mktRun").disabled = true;

      var url =
        "/workflows/run?slug=" +
        encodeURIComponent(feat.slug) +
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
            appendLog(
              "[" + typ + "] " + (data.message || data.agent || data.step || JSON.stringify(data))
            );
          } else if (typ === "step_done") {
            appendLog("[xong bước] " + (data.agent || ""));
            if (data.output) {
              var out = String(data.output);
              appendLog(out.length > 4000 ? out.slice(0, 4000) + "\n…(cắt)" : out);
            }
          } else if (typ === "error") {
            appendLog("ERROR: " + (data.message || data.error || ev.data));
            setStatus("Lỗi khi chạy", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 6000 ? res.slice(0, 6000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            setStatus("Xong «" + feat.label + "». Xem exports/marketing/.", true);
            es.close();
            es = null;
            root.querySelector("#mktStop").disabled = true;
            root.querySelector("#mktRun").disabled = false;
            paintSelected(root);
          } else {
            appendLog(ev.data);
          }
        } catch (eParse) {
          appendLog(ev.data);
        }
      };
      es.onerror = function () {
        setStatus("Mất kết nối stream (có thể đã xong hoặc lỗi).", false);
        root.querySelector("#mktRun").disabled = false;
        root.querySelector("#mktStop").disabled = true;
        paintSelected(root);
        try {
          if (es) es.close();
        } catch (e2) {}
        es = null;
      };
    };
  };
})();
