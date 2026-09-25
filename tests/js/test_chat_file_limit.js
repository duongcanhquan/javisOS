/* Trần file đính kèm chat + dòng ghi dưới ô nhập. */
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");
const APP = read("dashboard/app.js");
const HTML = read("dashboard/index.html");
const CON = read("dashboard/console.js");
const VI = read("dashboard/i18n/vi.json");
let fails = [];
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails.push(name);
}
check("dòng giới hạn dưới ô chat", HTML.includes('id="chatLimitNote"') && HTML.includes("3 file tài liệu"));
check("dòng đi theo sang trang Trò chuyện", CON.includes('"chatLimitNote"'));
check("chặn trước khi tải", APP.includes("function nhanFileChat") && APP.includes("function chanFileChat"));
check("kéo thả đi qua nhanFileChat", APP.includes("nhanFileChat(e.dataTransfer.files)"));
check("câu tiếng Việt", VI.includes("Đã đủ 3 file tài liệu mỗi lượt."));
check("nút chọn folder", HTML.includes('id="folderBtn"') && HTML.includes('id="folderInput"'));
check("logic chonFolderChat", APP.includes("function chonFolderChat") && APP.includes("/upload/folder"));
check("i18n folder", VI.includes("bar.folder") || VI.includes("Chọn thư mục trên máy"));
if (fails.length) {
  console.log("FAIL " + fails.join(", "));
  process.exit(1);
}
console.log("TẤT CẢ PASS");
