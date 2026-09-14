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
check("câu 1: Em đang soạn câu trả lời...", LINES[0] === "Em đang soạn câu trả lời...");
check("câu 2: Thời gian đọc dữ liệu...", LINES[1] === "Thời gian đọc dữ liệu có thể hơi lâu, anh chờ em nhé...");
check("câu 3: chuẩn hóa (không phải chuẩn háo)", LINES[2] === "Sắp xong rồi, em cần chuẩn hóa dữ liệu...");
check("câu 4: không bốc phét", LINES[3] === "Dữ liệu khá nhiều, em sẽ không bốc phét đâu...");
check("first trùng câu 1", W.first === LINES[0]);

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
