/* Nhãn orb khi não đang xử lý: KÍCH HOẠT SUY NGHĨ NÃO, không còn ĐANG SUY NGHĨ.

       node tests/js/test_orb_suy_nghi_nao.js
*/
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");
const APP = read("dashboard/app.js");
const HTML = read("dashboard/index.html");
const DOC_VI = read("docs/02-tro-chuyen-va-giong-noi.md");
const DOC_EN = read("docs/en/02-chat-and-voice.md");
const GRAPH_VI = read("docs/03-do-thi-tri-thuc.md");
const GRAPH_EN = read("docs/en/03-knowledge-graph.md");

const NHAN = "KÍCH HOẠT SUY NGHĨ NÃO";
const CU = "ĐANG SUY NGHĨ";

const fails = [];
function check(name, cond, extra) {
  console.log((cond ? "ok   " : "FAIL ") + name + (cond || extra === undefined ? "" : "  [" + extra + "]"));
  if (!cond) fails.push(name);
}

const thinking = APP.match(/setOrbState\(\s*"thinking"\s*,\s*"([^"]*)"\s*\)/g) || [];
check("có đúng 3 chỗ setOrbState thinking", thinking.length === 3, thinking.length);
check("mọi chỗ thinking dùng nhãn mới",
  thinking.length > 0 && thinking.every((s) => s.includes(NHAN)), thinking.join(" | "));
check("app.js không còn nhãn ĐANG SUY NGHĨ", !APP.includes(CU));

check("docs 02 ghi nhãn mới", DOC_VI.includes("| " + NHAN + " |"));
check("docs 02 không còn ĐANG SUY NGHĨ", !DOC_VI.includes(CU));
check("docs 03 ghi nhãn mới", GRAPH_VI.includes(NHAN));
check("docs 03 không còn ĐANG SUY NGHĨ", !GRAPH_VI.includes(CU));
check("docs EN 02 ghi ACTIVATE BRAIN THINKING", DOC_EN.includes("| ACTIVATE BRAIN THINKING |"));
check("docs EN 03 ghi ACTIVATE BRAIN THINKING", GRAPH_EN.includes("ACTIVATE BRAIN THINKING"));

const v = Number((HTML.match(/app\.js\?v=(\d+)/) || [])[1] || 0);
check("app.js đã bump ?v= (>= 107)", v >= 107, v);

console.log();
if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_orb_suy_nghi_nao: tat ca pass");
