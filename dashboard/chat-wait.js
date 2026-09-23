/* chat-wait.js - cau cho khi VMOS dang soan, dac biet luot lau.

   Bon cau xoay theo thoi gian cho (giay). Phan THUAN de test bang node:
     node tests/js/test_chat_wait.js
   Chip + TTS nam trong app.js.

   Hop dong UI (0.55.223+): chip chi hien 4 cau nay. tool_call / tool_result /
   status khac KHONG duoc de chip (van track MCP o noi khac).

   Ghi chu: KHONG dung ky tu em dash o bat ky dau. */
(function () {
  "use strict";

  var WAIT_LINES = [
    "Em làm ngay đây ạ!",
    "Em đang tìm thông tin trong não và sớm trả lời...",
    "Chờ em một chút, sắp xong rồi ạ...",
    "Cảm ơn vì đã chờ em...",
  ];
  // Mốc giây (kể từ lúc gửi) khi đổi sang câu tương ứng. Câu cuối giữ nguyên.
  var WAIT_AT_SEC = [0, 8, 20, 35];
  // Câu đời trước (vẫn nhận để TTS/chip không đọc lại khi WS gửi cũ).
  var WAIT_LINES_LEGACY = [
    "Em đang soạn câu trả lời...",
    "Thời gian đọc dữ liệu có thể hơi lâu, anh chờ em nhé...",
    "Sắp xong rồi, em cần chuẩn hóa dữ liệu...",
    "Dữ liệu khá nhiều, em sẽ không bốc phét đâu...",
  ];

  function waitIndexAt(elapsedSec) {
    var s = Number(elapsedSec);
    if (!isFinite(s) || s < 0) s = 0;
    var idx = 0;
    for (var i = 0; i < WAIT_AT_SEC.length; i++) {
      if (s >= WAIT_AT_SEC[i]) idx = i;
    }
    return idx;
  }

  function waitLineAt(elapsedSec) {
    return WAIT_LINES[waitIndexAt(elapsedSec)];
  }

  function isWaitFiller(s) {
    var t = String(s || "").trim();
    if (!t) return false;
    if (WAIT_LINES.indexOf(t) !== -1) return true;
    if (WAIT_LINES_LEGACY.indexOf(t) !== -1) return true;
    if (t === "wait") return true;
    // Câu chờ đời trước: WS vẫn có thể gửi, rotator trên dashboard giữ quyền.
    if (t.indexOf("Anh cho em thời gian") === 0) return true;
    if (t === "Cho em chút thời gian để trả lời.") return true;
    if (t === "Cho mình chút thời gian để trả lời.") return true;
    return false;
  }

  var API = {
    LINES: WAIT_LINES,
    AT_SEC: WAIT_AT_SEC,
    first: WAIT_LINES[0],
    waitLineAt: waitLineAt,
    waitIndexAt: waitIndexAt,
    isWaitFiller: isWaitFiller,
  };

  if (typeof window !== "undefined") window.JavisWait = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})();
