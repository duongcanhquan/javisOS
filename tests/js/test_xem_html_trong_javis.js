/* Mở landing/HTML trên Javis phải còn nút Về Javis — không kẹt trang thuần.

       node tests/js/test_xem_html_trong_javis.js

   Chủ repo 2026-09-13: tạo landing từ skill, bấm mở trên Javis — không có nút thoát
   về Javis / đóng. Gốc: .html mở mã nguồn; "Mở tab mới" đi /files/raw; PWA standalone
   thường thay chính cửa sổ app, landing không có chrome Javis.

   Hợp đồng: xem trang trong iframe, thanh Javis còn, tab mới qua /files/html-view. */
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const D = (f) => fs.readFileSync(path.join(ROOT, "dashboard", f), "utf8");
const CONSOLE = D("console.js");
const FE = D("file-editor.js");
const CR = D("chat-render.js");
const CSS = D("style.css");
const INDEX = D("index.html");

const fails = [];
const check = (name, cond) => { console.log((cond ? "ok   " : "FAIL ") + name); if (!cond) fails.push(name); };

check("console.js có _neRenderHtmlPage", /function _neRenderHtmlPage\s*\(/.test(CONSOLE));
check("mặc định xem trang (iframe /files/raw)",
  /ne-body ne-html mode-preview/.test(CONSOLE) && /iframe class="ne-frame"/.test(CONSOLE));
check("có nút gat Xem trang / Sửa mã",
  /Xem trang/.test(CONSOLE) && /Sửa mã/.test(CONSOLE));
check("nút đóng HTML ghi Về Javis",
  /← Về Javis/.test(CONSOLE) && /ne-back/.test(CONSOLE));
check("Mở tab mới HTML đi html-view, không raw",
  /_moFileNgoai/.test(CONSOLE)
  && /_vtHtmlView/.test(CONSOLE)
  && /\/files\/html-view\?/.test(CONSOLE)
  && /window\.open\(_vtHtmlView\(rel\)/.test(CONSOLE));
check("CANARY: PWA không window.open raw HTML",
  /_laPwa/.test(CONSOLE) && /display-mode:\s*standalone/.test(CONSOLE)
  && CONSOLE.indexOf("_laPwa()") < CONSOLE.indexOf("window.open(_vtHtmlView"));
check("openNote .html đi _neRenderHtmlPage, vẫn ghim",
  /ext === "\.html"/.test(CONSOLE) && /_neRenderHtmlPage\(/.test(CONSOLE)
  && /JavisPin\.set\(\{ name: d\.name \|\| it\.name \|\| rel, rel, abs: d\.abs \}\)/.test(CONSOLE));
check("_neCommonBtns gọi _moFileNgoai (HTML không nhảy raw trực tiếp)",
  /_moFileNgoai\(rel\)/.test(CONSOLE));

check("file-editor có renderHtml", /function renderHtml\s*\(/.test(FE));
check("file-editor HTML mặc định iframe + Về Javis",
  /jvfe-html/.test(FE) && /← Về Javis/.test(FE) && /function htmlViewUrl/.test(FE));
check("file-editor PWA chặn nhảy raw",
  /laPwa\(\)/.test(FE) && /e\.preventDefault\(\)/.test(FE));
check("CANARY: không lưu HTML khi mã nguồn chưa tải (tránh ghi đè file rỗng)",
  /ready\(\)|typeof ready === "function"/.test(FE) && /return loaded/.test(FE));
check("file-editor vẫn có openLink (test_code_hl)",
  /function openLink\(/.test(FE) && /JavisCodeHL\.attach/.test(FE));

check("chat-render: link .html title Xem trang",
  /Xem trang/.test(CR) && /\.html\?\$/.test(CR));
check("chat-render: .md vẫn Mở ra sửa", /Mở ra sửa/.test(CR));

check("CSS: ne-html preview ẩn mã nguồn, source ẩn iframe",
  /\.ne-body\.ne-html\.mode-preview \.ne-src/.test(CSS)
  && /\.ne-body\.ne-html\.mode-source \.ne-frame/.test(CSS)
  && /\.ne-actions button\.ne-back/.test(CSS));

const cacheV = (f) => Number((INDEX.match(new RegExp(f.replace(/\./g, "\\.") + "\\?v=(\\d+)")) || [])[1] || 0);
check("index.html cache-bust console / file-editor / chat-render / style",
  cacheV("console.js") >= 149
  && cacheV("file-editor.js") >= 9
  && cacheV("chat-render.js") >= 15
  && cacheV("style.css") >= 93);

console.log();
if (fails.length) { console.log(fails.length + " test HỎNG: " + fails.join(", ")); process.exit(1); }
console.log("OK - test_xem_html_trong_javis: tất cả pass");
