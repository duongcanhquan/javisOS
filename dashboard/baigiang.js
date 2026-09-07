/**
 * Trang Bài giảng (Việc): giúp giảng viên chọn đầu ra rõ ràng rồi tạo bằng Gemini.
 * Trọng tâm UX = menu lựa chọn có mô tả + ví dụ, không phải form kỹ thuật.
 */
(function () {
  "use strict";

  /** Mỗi đầu ra: khi nào chọn, nhận gì, ví dụ cụ thể cho giảng viên. */
  var FORMATS = [
    {
      id: "slide",
      slug: "bo-bai-giang-slide",
      label: "Slide trình chiếu",
      tagline: "Dạy trên lớp / họp phụ huynh / seminar ngắn",
      when:
        "Bạn cần chiếu máy chiếu hoặc gửi trước cho học viên đọc. Muốn cấu trúc rõ, ít chữ, có gợi ý hình.",
      gets: [
        "Deck 10–16 slide (1 ý / slide)",
        "Ghi chú giảng viên (speaker notes)",
        "Gợi ý ảnh / biểu đồ từng slide",
      ],
      example:
        "Chủ đề «Quang hợp lớp 8» → slide mở đầu hook → 3 bước quang hợp → ví dụ thực tế → quiz 1 câu → tóm tắt.",
      time: "~10–20 phút tạo khung",
    },
    {
      id: "video",
      slug: "bo-bai-giang-video",
      label: "Video giải thích",
      tagline: "Clip ngắn học viên xem lại / gửi Zalo / LMS",
      when:
        "Bạn muốn giải thích một ý khó bằng hình động, học viên tự xem trước hoặc ôn sau giờ.",
      gets: [
        "Kịch bản / beat giảng (hook → giải thích → ví dụ → chốt)",
        "Gói sẵn để render (paperdesign / Remotion / pack thủ công)",
        "Độ dài gợi ý (thường 60–90 giây nếu chưa nói)",
      ],
      example:
        "«Vì sao trời xanh?» → video 75 giây: câu hỏi mở → thí nghiệm tư duy → kết luận 1 câu dễ nhớ.",
      time: "Kịch bản nhanh; render có thể lâu hơn",
    },
    {
      id: "lop-hoc",
      slug: "bo-bai-giang-lop-hoc",
      label: "Lớp học tương tác",
      tagline: "Buổi học có cảnh, hỏi đáp, quiz, thực hành",
      when:
        "Bạn dạy live (online/offline) và cần kịch bản cả buổi: hoạt động, câu hỏi, bài tập ngắn.",
      gets: [
        "Outline 8–15 cảnh (mục tiêu + hoạt động từng đoạn)",
        "Quiz 4–8 câu + 1 bài thực hành ngắn (PBL)",
        "Script giảng từng cảnh (nói được luôn)",
      ],
      example:
        "«Nhập môn biến trong Python» → cảnh mở (5’) → demo (10’) → học viên làm mini-lab → quiz → tổng kết.",
      time: "~20–40 phút cho gói đầy đủ",
    },
    {
      id: "van-ban",
      slug: "bo-bai-giang-van-ban",
      label: "Bài đọc + ảnh & biểu đồ",
      tagline: "Handout / tài liệu đọc trước / gửi email phụ huynh",
      when:
        "Bạn cần tài liệu chữ rõ ràng, có chỗ chèn ảnh và biểu đồ, học viên đọc một mình được.",
      gets: [
        "Bài đọc dài (thường 1200–2000 chữ)",
        "Chỗ [ẢNH] / [BIỂU ĐỒ] có chú thích",
        "Ví dụ cụ thể + bài luyện ngắn cuối bài",
      ],
      example:
        "«An toàn mạng cho học sinh» → longread 5 mục + 1 bảng so sánh + 1 checklist mang về nhà.",
      time: "~15–25 phút",
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

  function composeBrief(topic, audience, goals, lang, fmt, files) {
    var parts = [];
    parts.push("Chủ đề: " + topic);
    parts.push("Đối tượng: " + (audience || "học viên phổ thông / mới bắt đầu"));
    parts.push("Mục tiêu học: " + (goals || "(chưa ghi - agent sẽ hỏi nếu thiếu)"));
    parts.push("Ngôn ngữ: " + (lang || "vi"));
    parts.push("Định dạng đầu ra: " + (fmt ? fmt.label : ""));
    if (fmt) {
      parts.push("Mô tả định dạng: " + fmt.tagline);
      parts.push("Ví dụ tham chiếu: " + fmt.example);
    }
    if (files && files.length) {
      parts.push("File đính kèm (đường dẫn stage/upload):\n- " + files.join("\n- "));
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
      '<label class="bg-card" data-slug="' +
      esc(f.slug) +
      '" style="display:block;padding:14px 16px;border:1.5px solid var(--line);border-radius:12px;margin:0 0 10px;cursor:pointer;background:var(--panel);transition:border-color .15s,box-shadow .15s">' +
      '<div style="display:flex;gap:10px;align-items:flex-start">' +
      '<input type="radio" name="bgFmt" value="' +
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

  function paintSelected(root) {
    var cards = root.querySelectorAll(".bg-card");
    cards.forEach(function (card) {
      var inp = card.querySelector('input[type="radio"]');
      var on = inp && inp.checked;
      card.style.borderColor = on ? "var(--accent, #3b82f6)" : "var(--line)";
      card.style.boxShadow = on ? "0 0 0 1px var(--accent, #3b82f6)" : "none";
    });
    var picked = root.querySelector('input[name="bgFmt"]:checked');
    var slug = picked ? picked.value : FORMATS[0].slug;
    var fmt = FORMATS.filter(function (f) {
      return f.slug === slug;
    })[0];
    var hint = root.querySelector("#bgPickHint");
    if (hint && fmt) {
      hint.innerHTML =
        "Đã chọn: <b>" +
        esc(fmt.label) +
        "</b> — " +
        esc(fmt.tagline) +
        ". Điền chủ đề bên dưới rồi bấm <b>Tạo</b>.";
    }
    var runBtn = root.querySelector("#bgRun");
    if (runBtn && fmt) {
      runBtn.textContent = "Tạo: " + fmt.label;
    }
  }

  window.renderBaiGiang = function (root) {
    if (!root) return;

    root.innerHTML =
      '<div class="si-wrap" style="max-width:860px">' +
      '<h2 style="margin:0 0 6px">Tạo bài giảng</h2>' +
      '<p class="dim" style="margin:0 0 18px;line-height:1.5">Dành cho giảng viên: chọn <b>một đầu ra</b> phù hợp buổi dạy, ' +
      "điền chủ đề (kèm file giáo án/PDF nếu có). Javis dùng Gemini: nghiên cứu → viết ví dụ → thiết kế → lưu file.</p>" +
      '<div class="si-field" style="margin-bottom:18px">' +
      '<label style="font-size:15px;margin-bottom:8px">1. Bạn muốn tạo gì?</label>' +
      '<p class="dim" style="margin:0 0 10px;font-size:13px;line-height:1.4">Đọc mô tả và ví dụ rồi chọn. Mỗi loại có lộ trình riêng (agent + skill riêng).</p>' +
      FORMATS.map(cardHtml).join("") +
      '<p id="bgPickHint" class="dim" style="margin:8px 0 0;font-size:13px;line-height:1.4"></p>' +
      "</div>" +
      '<div style="border-top:1px solid var(--line);padding-top:16px;margin-bottom:8px">' +
      '<label style="display:block;font-size:15px;margin-bottom:10px;color:var(--text3)">2. Thông tin buổi học</label>' +
      '<div class="si-field"><label>Chủ đề *</label>' +
      '<input type="text" id="bgTopic" placeholder="VD: Quang hợp cho học sinh lớp 8" autocomplete="off"></div>' +
      '<div class="si-field"><label>Đối tượng học</label>' +
      '<input type="text" id="bgAudience" placeholder="VD: học sinh THCS, sinh viên năm 1, giáo viên mới"></div>' +
      '<div class="si-field"><label>Mục tiêu học (mỗi dòng một ý)</label>' +
      '<textarea id="bgGoals" rows="3" placeholder="Sau buổi học, học viên…&#10;Giải thích được…&#10;Làm được…"></textarea></div>' +
      '<div class="si-field"><label>Ngôn ngữ đầu ra</label>' +
      '<select id="bgLang" class="loop-sel"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div>' +
      '<div class="si-field"><label>File đính kèm (giáo án, PDF, ảnh… — tùy chọn)</label>' +
      '<input type="file" id="bgFiles" multiple>' +
      '<div class="dim" id="bgFileList" style="font-size:12.5px;margin-top:6px"></div></div>' +
      "</div>" +
      '<div class="si-actions" style="display:flex;gap:8px;flex-wrap:wrap;margin:14px 0;align-items:center">' +
      '<button class="s-btn" type="button" id="bgRun">Tạo</button>' +
      '<button class="s-btn-ghost" type="button" id="bgStop" disabled>Dừng xem</button>' +
      '<button class="s-btn-ghost" type="button" id="bgSeed" title="Cài agent/workflow Gemini vào brain đang mở">Chuẩn bị lần đầu</button>' +
      "</div>" +
      '<div id="bgStatus" class="dim" style="margin:0 0 10px"></div>' +
      '<details style="margin:0 0 8px"><summary class="dim" style="cursor:pointer;font-size:13px">Nhật ký chạy (chi tiết kỹ thuật)</summary>' +
      '<pre id="bgLog" style="max-height:360px;overflow:auto;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);font-size:12.5px;white-space:pre-wrap;margin-top:8px"></pre>' +
      "</details>" +
      '<p class="dim" style="font-size:12.5px;line-height:1.4">File xong nằm trong <code>exports/bai-giang/</code> của brain đang mở.</p>' +
      "</div>";

    var uploaded = [];
    var es = null;

    paintSelected(root);
    root.querySelectorAll('input[name="bgFmt"]').forEach(function (inp) {
      inp.addEventListener("change", function () {
        paintSelected(root);
      });
    });
    root.querySelectorAll(".bg-card").forEach(function (card) {
      card.addEventListener("click", function () {
        var inp = card.querySelector('input[type="radio"]');
        if (inp) {
          inp.checked = true;
          paintSelected(root);
        }
      });
    });

    function setStatus(msg, ok) {
      var el = root.querySelector("#bgStatus");
      if (!el) return;
      el.textContent = msg || "";
      el.style.color = ok === false ? "var(--danger-ink, #c44)" : "var(--text3)";
    }

    function appendLog(line) {
      var log = root.querySelector("#bgLog");
      if (!log) return;
      log.textContent += line + "\n";
      log.scrollTop = log.scrollHeight;
      var det = log.closest("details");
      if (det) det.open = true;
    }

    root.querySelector("#bgFiles").onchange = async function () {
      var input = root.querySelector("#bgFiles");
      var files = input && input.files ? Array.from(input.files) : [];
      uploaded = [];
      var list = root.querySelector("#bgFileList");
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
          if (r && (r.path || r.name)) {
            uploaded.push(r.path || r.name);
          } else if (r && r.error) {
            appendLog("Upload lỗi: " + r.error);
          }
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

    root.querySelector("#bgSeed").onclick = async function () {
      setStatus("Đang chuẩn bị agent + workflow Gemini…");
      try {
        var fd = new FormData();
        fd.append("brain", brain());
        var r = await (await fetch("/studio/seed-bai-giang", { method: "POST", body: fd })).json();
        if (!r || !r.ok) {
          setStatus((r && r.error) || "Chuẩn bị thất bại", false);
          return;
        }
        setStatus(
          "Sẵn sàng " +
            (r.workflows || []).length +
            " loại đầu ra. Chọn một thẻ ở trên rồi tạo.",
          true
        );
      } catch (e) {
        setStatus(String((e && e.message) || e), false);
      }
    };

    root.querySelector("#bgStop").onclick = function () {
      if (es) {
        try {
          es.close();
        } catch (e) {}
        es = null;
      }
      root.querySelector("#bgStop").disabled = true;
      setStatus("Đã dừng theo dõi (việc trên server có thể vẫn chạy).", true);
    };

    root.querySelector("#bgRun").onclick = async function () {
      var topic = ((root.querySelector("#bgTopic") || {}).value || "").trim();
      if (!topic) {
        setStatus("Nhập chủ đề trước (mục 2).", false);
        return;
      }
      var fmtEl = root.querySelector('input[name="bgFmt"]:checked');
      var slug = fmtEl ? fmtEl.value : FORMATS[0].slug;
      var fmt = FORMATS.filter(function (f) {
        return f.slug === slug;
      })[0];
      var audience = ((root.querySelector("#bgAudience") || {}).value || "").trim();
      var goals = ((root.querySelector("#bgGoals") || {}).value || "").trim();
      var lang = ((root.querySelector("#bgLang") || {}).value || "vi").trim();
      var brief = composeBrief(topic, audience, goals, lang, fmt, uploaded);

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        await fetch("/studio/seed-bai-giang", { method: "POST", body: fd0 });
      } catch (e0) {}

      if (es) {
        try {
          es.close();
        } catch (e1) {}
      }
      root.querySelector("#bgLog").textContent = "";
      appendLog("--- Brief ---\n" + brief + "\n---");
      setStatus("Đang tạo «" + (fmt ? fmt.label : slug) + "»…");
      root.querySelector("#bgStop").disabled = false;
      root.querySelector("#bgRun").disabled = true;

      var url =
        "/workflows/run?slug=" +
        encodeURIComponent(slug) +
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
            appendLog(
              "[xong bước] " +
                (data.agent || "") +
                (data.verified === false ? " (cần chỉnh lại)" : "")
            );
            if (data.output) {
              var out = String(data.output);
              appendLog(out.length > 4000 ? out.slice(0, 4000) + "\n…(cắt)" : out);
            }
          } else if (typ === "error") {
            appendLog("ERROR: " + (data.message || data.error || ev.data));
            setStatus("Lỗi khi tạo", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 6000 ? res.slice(0, 6000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            setStatus(
              "Xong «" +
                (fmt ? fmt.label : "") +
                "». Mở exports/bai-giang/ trong Files để xem.",
              true
            );
            es.close();
            es = null;
            root.querySelector("#bgStop").disabled = true;
            root.querySelector("#bgRun").disabled = false;
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
        root.querySelector("#bgRun").disabled = false;
        root.querySelector("#bgStop").disabled = true;
        paintSelected(root);
        try {
          if (es) es.close();
        } catch (e2) {}
        es = null;
      };
    };
  };
})();
