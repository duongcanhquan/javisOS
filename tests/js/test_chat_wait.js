/* Canary: cau cho xoay khi luot tra loi lau. Chay: node tests/js/test_chat_wait.js */
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "../..");
const W = require("../../dashboard/chat-wait.js");

let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails++;
}

const LINES = W.LINES;
check("đủ 4 câu chờ", Array.isArray(LINES) && LINES.length === 4);
check("câu 1: Em làm ngay đây ạ!", LINES[0] === "Em làm ngay đây ạ!");
check("câu 2: tìm trong não...", LINES[1] === "Em đang tìm thông tin trong não và sớm trả lời...");
check("câu 3: sắp xong rồi ạ", LINES[2] === "Chờ em một chút, sắp xong rồi ạ...");
check("câu 4: cảm ơn vì đã chờ", LINES[3] === "Cảm ơn vì đã chờ em...");
check("first trùng câu 1", W.first === LINES[0]);
check("không còn xưng anh trong câu chờ", !LINES.join("").includes("anh chờ"));

check("0s -> câu 1", W.waitLineAt(0) === LINES[0]);
check("7s vẫn câu 1", W.waitLineAt(7) === LINES[0]);
check("8s -> câu 2", W.waitLineAt(8) === LINES[1]);
check("19s vẫn câu 2", W.waitLineAt(19) === LINES[1]);
check("20s -> câu 3", W.waitLineAt(20) === LINES[2]);
check("34s vẫn câu 3", W.waitLineAt(34) === LINES[2]);
check("35s -> câu 4", W.waitLineAt(35) === LINES[3]);
check("999s vẫn câu 4", W.waitLineAt(999) === LINES[3]);
check("số âm coi như 0", W.waitLineAt(-3) === LINES[0]);
check("NaN coi như 0", W.waitLineAt("x") === LINES[0]);

check("isWaitFiller nhận 4 câu mới", LINES.every(W.isWaitFiller));
check("isWaitFiller nhận bộ 0.55.x (legacy)",
  W.isWaitFiller("Em đang soạn câu trả lời...")
  && W.isWaitFiller("Thời gian đọc dữ liệu có thể hơi lâu, anh chờ em nhé..."));
check("isWaitFiller nhận câu 0.55.218", W.isWaitFiller("Anh cho em thời gian để thực hiện, thời gian có thể lâu một chút vì cần kết nối và so sánh dữ liệu thật..."));
check("isWaitFiller nhận câu cũ", W.isWaitFiller("Cho em chút thời gian để trả lời."));
check("isWaitFiller bỏ tool status", !W.isWaitFiller("Nhận data - đang phân tích..."));
check("isWaitFiller rỗng", !W.isWaitFiller("") && !W.isWaitFiller(null));

const waitJs = fs.readFileSync(path.join(root, "dashboard/chat-wait.js"), "utf8");
const appJs = fs.readFileSync(path.join(root, "dashboard/app.js"), "utf8");
const indexHtml = fs.readFileSync(path.join(root, "dashboard/index.html"), "utf8");
const mainPy = fs.readFileSync(path.join(root, "server/main.py"), "utf8");

check("chat-wait.js không em dash", !waitJs.includes("\u2014"));
check("không viết nhầm chuẩn háo", !waitJs.includes("chuẩn háo") && !LINES.join("").includes("chuẩn háo"));

check("index nạp chat-wait.js trước app.js",
  indexHtml.indexOf("chat-wait.js") !== -1
  && indexHtml.indexOf("chat-wait.js") < indexHtml.indexOf("app.js?v="));
check("app.js gọi startWaitRotate", /startWaitRotate\s*\(/.test(appJs));
check("app.js gọi stopWaitRotate", /stopWaitRotate\s*\(/.test(appJs));
check("app.js không còn Cho em chút thời gian để trả lời",
  !appJs.includes("Cho em chút thời gian để trả lời."));
// 0.55.223: tool không được đè chip chờ (trước đây stopWaitRotate + showActivity trên tool_call).
check("tool_call không stopWaitRotate / showActivity trên chip", (() => {
  const m = appJs.match(/data\.type === ["']tool_call["'][\s\S]{0,280}?else if/);
  if (!m) return false;
  const block = m[0];
  return block.includes("trackMCP")
    && !/stopWaitRotate\s*\(/.test(block)
    && !/showActivity\s*\(/.test(block);
})());
check("tool_result không đè chip chờ", (() => {
  const m = appJs.match(/data\.type === ["']tool_result["'][\s\S]{0,220}?else if/);
  if (!m) return false;
  return !/stopWaitRotate\s*\(/.test(m[0]) && !/showActivity\s*\(/.test(m[0]);
})());
check("response TTS cắt waitFiller rồi speak khi chưa spoke",
  /waitFiller[\s\S]{0,200}?resumeMic:\s*false/.test(appJs)
  && /!t\.spoke && finalText\.trim\(\)/.test(appJs));
check("isWaitFiller nhận marker wait từ server", W.isWaitFiller("wait"));
check("server status là marker wait (chip dashboard xoay 4 câu)",
  /"content":\s*"wait"/.test(mainPy));
check("server không còn câu chờ 0.55.218",
  !mainPy.includes("Anh cho em thời gian để thực hiện"));

if (fails) {
  console.log("\nFAIL - test_chat_wait: " + fails + " lỗi");
  process.exit(1);
}
console.log("\nOK - test_chat_wait: tất cả pass");
