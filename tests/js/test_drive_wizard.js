/* Kho Drive UI wizard: tab Mac/Windows + 3 bước tự chuyển.

       node tests/js/test_drive_wizard.js
*/
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const JS = fs.readFileSync(path.join(ROOT, "dashboard", "drive-projects.js"), "utf8");
const CSS = fs.readFileSync(path.join(ROOT, "dashboard", "workbench.css"), "utf8");
const CODE = JS.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

const fails = [];
const check = (name, cond) => {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails.push(name);
};

check("có thanh 3 bước", /Bước 1/.test(JS) && /Bước 2/.test(JS) && /Bước 3/.test(JS));
check("currentStep quyết định bước đang làm", /function currentStep\(/.test(CODE));
check("VPS có tablist Mac / Windows tách biệt", /dp-os-tabs/.test(CODE) && /role="tablist"/.test(JS));
check("nút Bắt đầu riêng cho Mac và Windows", /dpStartMac/.test(CODE) && /dpStartWin/.test(CODE));
check("pane Mac/Windows ẩn hiện theo data-show",
  /dp-os-body\[data-show="mac"\]/.test(CSS) && /dp-os-pane\[data-os="win"\]/.test(CSS));
check("bước 2 chỉ khi đã kết nối Google", /Đang làm bước 2/.test(JS) && /dpCreate/.test(CODE));
check("bước 3 hướng dẫn đồng bộ hàng ngày", /Đồng bộ lại/.test(JS) && /Dùng hàng ngày/.test(JS));
check("phân biệt với Kết nối Google Workspace", /Kết nối → Google/.test(JS) || /Kết nối → Google/.test(CODE) || /menu <b>Kết nối/.test(JS));
check("pair API vẫn dùng cho VPS", /\/drive-projects\/rclone\/pair\/start/.test(CODE));
check("localhost vẫn có đường authorize", /\/drive-projects\/rclone\/authorize\/start/.test(CODE));

console.log();
if (fails.length) {
  console.log(fails.length + " test HỎNG: " + fails.join(", "));
  process.exit(1);
}
console.log("Tất cả test drive_wizard đã qua.");
