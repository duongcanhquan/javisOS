/* Việc nền báo xong KHÔNG được khoá cứng khung chat.

       node tests/js/test_viec_nen_khong_khoa_chat.js

   Ba triệu chứng, MỘT gốc, nằm ở dòng định tuyến khung WebSocket: khung `push` hồi sinh
   một lượt đã chết với cờ running=true. Test này CHẠY THẬT chính biểu thức định tuyến lấy
   từ app.js, không chỉ soi mẫu chữ.
*/
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "..", "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");
const app = read("dashboard/app.js");

let fails = [];
function check(name, cond, extra) {
  console.log((cond ? "ok   " : "FAIL ") + name + (cond || extra === undefined ? "" : "  [" + extra + "]"));
  if (!cond) fails.push(name);
}

// ---- 1. Nhấc nguyên biểu thức định tuyến ra chạy ----
const m = app.match(/const KHUNG_LUOT = \[[\s\S]*?\n {2}const t = !sid[\s\S]*?: null\)\);/);
check("tìm được biểu thức định tuyến khung trong app.js", !!m);
const dinhTuyen = new Function("turns", "sid", "data", (m ? m[0] : "const t=null;") + "\nreturn t;");

const SID = "abc123";
let turns = {};

let t = dinhTuyen(turns, SID, { type: "push", content: "Kết quả việc nền" });
check("khung push KHÔNG dựng lại lượt đã chết", turns[SID] === undefined);
check("khung push trả t = null (nơi nhận đã tự lo phần hiển thị)", t === null);

turns = {};
t = dinhTuyen(turns, SID, { type: "inbox" });
check("khung inbox cũng không dựng lượt", turns[SID] === undefined);

turns = {};
t = dinhTuyen(turns, SID, { type: "stream", content: "xin" });
check("khung stream vẫn dựng bộ đệm mới", !!turns[SID] && turns[SID].running === true);
check("khung stream trả đúng bộ đệm vừa dựng", t === turns[SID]);

turns = {};
dinhTuyen(turns, SID, { type: "status", content: "đang nghĩ" });
check("khung status vẫn dựng bộ đệm mới", !!turns[SID] && turns[SID].running === true);

turns = {};
const dang = (turns[SID] = { text: "nửa câu", bubble: {}, spoke: false, running: true });
t = dinhTuyen(turns, SID, { type: "push", content: "việc nền xong" });
check("đang có lượt chạy: push trả đúng bộ đệm đang có, không thay mới", t === dang);
check("đang có lượt chạy: push không đổi cờ running", turns[SID].running === true);

turns = {};
dinhTuyen(turns, SID, { type: "stream", content: "Ừ, để xem ngay." });
dinhTuyen(turns, SID, { type: "response", content: "Ừ, để xem ngay." });
delete turns[SID];
dinhTuyen(turns, SID, { type: "push", content: "Xong việc nền rồi" });
check("CA THẬT: sau việc nền, phiên KHÔNG còn bị coi là đang chạy",
  !(turns[SID] && turns[SID].running));

// ---- 2. sendMessage không nuốt lặng tin lúc rảnh tay ----
check("CANARY: bỏ hẳn kiểu nuốt lặng `if (turns[sid].running) return;`",
  !/if \(turns\[sid\] && turns\[sid\]\.running\) return;/.test(app));
check("gõ lúc rảnh tay thì DỪNG lượt cũ rồi gửi",
  /if \(!handsFree\) return;[\s\S]{0,80}stopCurrent\(\);/.test(app));

console.log(fails.length ? "\n" + fails.length + " FAIL" : "\nTat ca OK");
process.exit(fails.length ? 1 : 0);
