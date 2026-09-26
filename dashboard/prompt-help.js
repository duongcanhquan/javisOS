/* prompt-help.js - nút ? cạnh thanh chat (+ Kho Drive): popup prompt chuẩn
   nhập / lưu / tra cứu (file chat, Drive, folder máy, search mạng).
   Cùng bundle dashboard → quan + mọi tenant dùng chung sau deploy image. */
(function () {
  "use strict";

  var MODAL_ID = "promptHelpModal";

  function t(key, fb) {
    try {
      if (typeof window.t === "function") {
        var v = window.t(key);
        if (v && v !== key) return v;
      }
    } catch (e) {}
    return fb != null ? fb : key;
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function ensureCss() {
    if (document.getElementById("promptHelpCss")) return;
    var st = document.createElement("style");
    st.id = "promptHelpCss";
    st.textContent =
      "#promptHelpModal .ph-box{max-width:640px;width:min(640px,96vw);max-height:88vh;overflow:hidden;display:flex;flex-direction:column;}" +
      "#promptHelpModal .ph-body{padding:0 18px 16px;overflow-y:auto;flex:1;font-size:14px;line-height:1.45;color:var(--text2);}" +
      "#promptHelpModal .ph-rule{margin:0 0 12px;padding:10px 12px;border-radius:10px;background:var(--sunken);border:1px solid var(--glass-brd);color:var(--text);font-size:13.5px;}" +
      "#promptHelpModal .ph-sec{margin:0 0 14px;padding-bottom:12px;border-bottom:1px solid var(--glass-brd);}" +
      "#promptHelpModal .ph-sec:last-child{border-bottom:0;margin-bottom:0;}" +
      "#promptHelpModal .ph-h{font-weight:700;font-size:14.5px;color:var(--text);margin:0 0 6px;}" +
      "#promptHelpModal .ph-note{margin:0 0 8px;font-size:13px;color:var(--text3);}" +
      "#promptHelpModal .ph-block{margin:0 0 8px;}" +
      "#promptHelpModal .ph-lab{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 4px;}" +
      "#promptHelpModal .ph-lab span{font-size:12px;font-weight:600;color:var(--text3);letter-spacing:.02em;}" +
      "#promptHelpModal .ph-acts{display:flex;gap:6px;flex-shrink:0;}" +
      "#promptHelpModal .ph-acts button{background:var(--bg3);border:1px solid var(--border);color:var(--text);font-size:12px;padding:4px 8px;border-radius:7px;cursor:pointer;}" +
      "#promptHelpModal .ph-acts button:hover{border-color:var(--accent);}" +
      "#promptHelpModal .ph-pre{margin:0;padding:10px 12px;border-radius:9px;background:var(--sunken);border:1px solid var(--glass-brd);color:var(--text);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px;line-height:1.4;white-space:pre-wrap;word-break:break-word;}" +
      "#promptHelpModal .ph-foot{padding:10px 18px 14px;border-top:1px solid var(--glass-brd);font-size:12.5px;color:var(--text3);}" +
      ".attach-btn.ph-help-btn{color:var(--text2);}" +
      ".attach-btn.ph-help-btn:hover{color:var(--accent);}" +
      ".ph-inline-help{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;margin-left:8px;border-radius:8px;border:1px solid var(--border);background:var(--bg3);color:var(--text2);cursor:pointer;vertical-align:middle;}" +
      ".ph-inline-help:hover{border-color:var(--accent);color:var(--accent);}" +
      ".ph-inline-help svg{display:block;}";
    document.head.appendChild(st);
  }

  function sections() {
    return [
      {
        h: t("prompt_help.s1_h", "1) File / ảnh trong chat"),
        note: t("prompt_help.s1_note", "Mặc định chỉ đọc. Muốn dùng lâu phải nói lưu + chưng cất."),
        blocks: [
          {
            lab: t("prompt_help.lab_read", "Chỉ đọc"),
            text: t(
              "prompt_help.s1_read",
              "Đọc (các) file đính kèm rồi tóm tắt ý chính. Không lưu vào sources."
            ),
          },
          {
            lab: t("prompt_help.lab_save", "Lưu + tra cứu sau"),
            text: t(
              "prompt_help.s1_save",
              "Lưu (các) file này vào sources/, status unprocessed, rồi chạy ingest-source.\nChưng cất lên wiki (1 ý = 1 trang, có [[citation]] và aliases).\nBáo đường sources + trang wiki đã tạo/cập nhật."
            ),
          },
        ],
      },
      {
        h: t("prompt_help.s2_h", "2) Link folder Google Drive"),
        note: t(
          "prompt_help.s2_note",
          "Hoặc dùng trang Kho Drive: Đồng bộ lại → Chưng cất kho."
        ),
        blocks: [
          {
            lab: t("prompt_help.lab_drive_new", "Tạo kho + chưng cất"),
            text: t(
              "prompt_help.s2_new",
              "Tạo kho Drive tên «<Tên kho>» từ link này: <URL folder>\nĐồng bộ rclone → mirror sources/drive/<slug>/\nRồi chưng cất toàn bộ file unprocessed (trừ README); kho lớn xếp Kanban theo batch.\nPDF chưa có chữ thì liệt kê rõ."
            ),
          },
          {
            lab: t("prompt_help.lab_drive_again", "Đồng bộ + chưng cất lại"),
            text: t(
              "prompt_help.s2_again",
              "Đồng bộ lại kho Drive «<Tên>», rồi Chưng cất kho:\ningest-source mọi file unprocessed trong sources/drive/<slug>/."
            ),
          },
        ],
      },
      {
        h: t("prompt_help.s3_h", "3) Folder trên máy (nút thư mục)"),
        note: t("prompt_help.s3_note", "Chọn folder bằng nút cạnh kẹp giấy (tối đa 50 file / 100 MB), rồi gửi kèm lệnh."),
        blocks: [
          {
            lab: t("prompt_help.lab_read", "Chỉ đọc"),
            text: t(
              "prompt_help.s3_read",
              "Đọc toàn bộ folder vừa chọn. Tóm tắt cấu trúc + ý chính từng nhóm file.\nKhông lưu vào brain."
            ),
          },
          {
            lab: t("prompt_help.lab_save", "Lưu + tra cứu sau"),
            text: t(
              "prompt_help.s3_save",
              "Lưu toàn bộ folder này vào sources/local/<slug-ngắn>/ (giữ cấu trúc tương đối),\gắn status: unprocessed, rồi ingest-source từng file.\nChưng cất lên wiki; kho lớn thì xếp batch Kanban + báo tiến độ.\nBỏ qua file rác (__MACOSX, .DS_Store). Báo file nào không đọc được."
            ),
          },
        ],
      },
      {
        h: t("prompt_help.s4_h", "4) Search trên mạng"),
        note: t("prompt_help.s4_note", "Cần Tavily hoặc engine có WebSearch. Báo cáo → sources/research → wiki."),
        blocks: [
          {
            lab: t("prompt_help.lab_research", "Nghiên cứu + lưu"),
            text: t(
              "prompt_help.s4_save",
              "Nghiên cứu sâu về: <chủ đề / câu hỏi>.\nDùng web (Tavily/WebSearch). Lưu báo cáo vào sources/research/<slug>.md\n(status: unprocessed, kèm URL nguồn), rồi ingest-source lên wiki.\nPhân biệt fact vs suy luận; liệt kê nguồn. Không bịa link."
            ),
          },
          {
            lab: t("prompt_help.lab_quick", "Chỉ tìm nhanh"),
            text: t(
              "prompt_help.s4_quick",
              "Search nhanh: <câu hỏi>. Tóm tắt + link. Không ghi vào sources/wiki."
            ),
          },
        ],
      },
      {
        h: t("prompt_help.s5_h", "5) Tra cứu sau (mọi kênh)"),
        note: t(
          "prompt_help.s5_note",
          "Tri thức tái dùng nằm ở wiki - không nhét cả kho vào memory."
        ),
        blocks: [
          {
            lab: t("prompt_help.lab_query", "Hỏi lại chuẩn"),
            text: t(
              "prompt_help.s5_query",
              "Mở wiki/index.md, tìm trang liên quan <chủ đề>.\nTrả lời dựa trên wiki + sources gốc nếu cần.\nMọi khẳng định cụ thể có [[citation]].\nWiki chưa có thì nói rõ gap (có thể ghi wiki/_open-questions.md), không bịa."
            ),
          },
        ],
      },
    ];
  }

  function copyText(text, btn) {
    var done = function () {
      if (!btn) return;
      var old = btn.textContent;
      btn.textContent = t("prompt_help.copied", "Đã chép");
      setTimeout(function () {
        btn.textContent = old;
      }, 1200);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(function () {
        legacyCopy(text);
        done();
      });
    } else {
      legacyCopy(text);
      done();
    }
  }

  function legacyCopy(text) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    } catch (e) {}
  }

  function pasteToChat(text) {
    var inp = document.getElementById("chatInput");
    if (!inp) {
      alert(t("prompt_help.no_chat", "Mở trang Trò chuyện rồi thử lại."));
      return;
    }
    inp.value = text;
    try {
      inp.dispatchEvent(new Event("input", { bubbles: true }));
    } catch (e) {}
    inp.focus();
    close();
    try {
      if (window.Alpine && Alpine.store && Alpine.store("nav")) {
        Alpine.store("nav").page = "chat";
      }
    } catch (e2) {}
  }

  function close() {
    var m = document.getElementById(MODAL_ID);
    if (m) m.classList.remove("open");
    document.removeEventListener("keydown", onEsc);
  }

  function onEsc(e) {
    if (e.key === "Escape") close();
  }

  function open() {
    ensureCss();
    var m = document.getElementById(MODAL_ID);
    if (!m) {
      m = document.createElement("div");
      m.id = MODAL_ID;
      m.className = "mp-overlay";
      m.setAttribute("role", "presentation");
      document.body.appendChild(m);
    }

    var xIcon =
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>';

    var body = "";
    body +=
      '<p class="ph-rule">' +
      esc(
        t(
          "prompt_help.rule",
          "Quy tắc: chỉ đọc nếu không nói lưu. Muốn dùng lâu phải nói rõ lưu sources + chưng cất wiki. Về sau hỏi theo chủ đề + «dựa trên wiki, có citation»."
        )
      ) +
      "</p>";

    var secs = sections();
    for (var i = 0; i < secs.length; i++) {
      var s = secs[i];
      body += '<section class="ph-sec">';
      body += '<h3 class="ph-h">' + esc(s.h) + "</h3>";
      if (s.note) body += '<p class="ph-note">' + esc(s.note) + "</p>";
      for (var j = 0; j < s.blocks.length; j++) {
        var b = s.blocks[j];
        var id = "phb-" + i + "-" + j;
        body += '<div class="ph-block" data-ph-id="' + id + '">';
        body +=
          '<div class="ph-lab"><span>' +
          esc(b.lab) +
          '</span><div class="ph-acts">' +
          '<button type="button" data-ph="copy">' +
          esc(t("prompt_help.copy", "Chép")) +
          "</button>" +
          '<button type="button" data-ph="paste">' +
          esc(t("prompt_help.paste", "Dán vào chat")) +
          "</button>" +
          "</div></div>";
        body += '<pre class="ph-pre" data-ph-text>' + esc(b.text) + "</pre>";
        body += "</div>";
      }
      body += "</section>";
    }

    m.innerHTML =
      '<div class="mp-box ph-box" role="dialog" aria-modal="true" aria-labelledby="phTitle">' +
      '<div class="mp-head"><div><div class="mp-title" id="phTitle">' +
      esc(t("prompt_help.title", "Prompt nhập & lưu dữ liệu")) +
      '</div><div class="mp-sub">' +
      esc(
        t(
          "prompt_help.sub",
          "File chat · Drive · folder máy · search mạng - chép hoặc dán thẳng vào ô chat."
        )
      ) +
      "</div></div>" +
      '<button type="button" class="mp-x" data-act="close" aria-label="' +
      esc(t("prompt_help.close", "Đóng")) +
      '">' +
      xIcon +
      "</button></div>" +
      '<div class="ph-body">' +
      body +
      "</div>" +
      '<div class="ph-foot">' +
      esc(
        t(
          "prompt_help.foot",
          "Không dùng «ghi nhớ hết vào memory» cho cả kho. Memory chỉ vài fact bền; tri thức tái dùng = wiki."
        )
      ) +
      "</div></div>";

    m.classList.add("open");
    document.addEventListener("keydown", onEsc);

    m.querySelectorAll('[data-act="close"]').forEach(function (btn) {
      btn.onclick = close;
    });
    m.onclick = function (e) {
      if (e.target === m) close();
    };

    m.querySelectorAll(".ph-block").forEach(function (block) {
      var pre = block.querySelector("[data-ph-text]");
      var text = pre ? pre.textContent : "";
      var copyBtn = block.querySelector('[data-ph="copy"]');
      var pasteBtn = block.querySelector('[data-ph="paste"]');
      if (copyBtn)
        copyBtn.onclick = function () {
          copyText(text, copyBtn);
        };
      if (pasteBtn)
        pasteBtn.onclick = function () {
          pasteToChat(text);
        };
    });

    var closeBtn = m.querySelector(".mp-x");
    if (closeBtn) closeBtn.focus();
  }

  function helpSvg() {
    return (
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">' +
      '<circle cx="12" cy="12" r="10"/>' +
      '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>' +
      '<line x1="12" y1="17" x2="12.01" y2="17"/>' +
      "</svg>"
    );
  }

  function wireChatButton() {
    var btn = document.getElementById("promptHelpBtn");
    if (!btn || btn._phWired) return;
    btn._phWired = true;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      open();
    });
  }

  /** Nút ? nhỏ gắn vào header trang (vd Kho Drive). */
  function mountInline(host) {
    if (!host || host.querySelector(".ph-inline-help")) return null;
    ensureCss();
    var b = document.createElement("button");
    b.type = "button";
    b.className = "ph-inline-help";
    b.title = t("prompt_help.btn", "Gợi ý prompt nhập / lưu dữ liệu");
    b.setAttribute("aria-label", t("prompt_help.btn", "Gợi ý prompt nhập / lưu dữ liệu"));
    b.innerHTML = helpSvg();
    b.onclick = function (e) {
      e.preventDefault();
      open();
    };
    host.appendChild(b);
    return b;
  }

  window.JavisPromptHelp = { open: open, close: close, mountInline: mountInline };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wireChatButton);
  } else {
    wireChatButton();
  }
  // i18n đổi ngôn ngữ: cập nhật title nút
  window.addEventListener("javis:i18n", function () {
    var btn = document.getElementById("promptHelpBtn");
    if (btn) {
      var lab = t("prompt_help.btn", "Gợi ý prompt nhập / lưu dữ liệu");
      btn.title = lab;
      btn.setAttribute("aria-label", lab);
    }
  });
})();
