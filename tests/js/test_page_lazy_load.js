/* Canary: trang ít dùng lazy-load, không nạp eager trong index. */
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "../..");
let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails++;
}

const html = fs.readFileSync(path.join(root, "dashboard/index.html"), "utf8");
const consoleJs = fs.readFileSync(path.join(root, "dashboard/console.js"), "utf8");
const mainPy = fs.readFileSync(path.join(root, "server/main.py"), "utf8");

const lazyFiles = [
  "meetings.js",
  "baigiang.js",
  "video.js",
  "marketing.js",
  "org.js",
  "drive-projects.js",
  "guides.js",
  "tool-apis.js",
  "usage.js",
  "workspace.js",
  "chatbots.js",
];

check("PAGE_LAZY + ensurePageScript + withLazyPage",
  /PAGE_LAZY/.test(consoleJs) && /ensurePageScript/.test(consoleJs) && /withLazyPage/.test(consoleJs));
check("javis-page-lazy JSON trong index",
  /id="javis-page-lazy"/.test(html) && lazyFiles.every((f) => html.includes('"' + f + '"')));
lazyFiles.forEach((f) => {
  check("index không eager /static/" + f, !html.includes("/static/" + f));
  check("console khai báo file " + f, consoleJs.includes('file: "' + f + '"'));
});
check("_renderGen guard trong withLazyPage",
  /async function withLazyPage/.test(consoleJs) && /_renderGen/.test(consoleJs));
check("server fingerprint lazy assets",
  /_PAGE_LAZY_ASSETS/.test(mainPy) && /javis-page-lazy/.test(mainPy));
check("dash sig gồm mtime lazy files",
  /for name in _PAGE_LAZY_ASSETS/.test(mainPy));
check("lazy URL dùng /asset/{ver}/",
  /function _pageScriptUrl/.test(consoleJs) &&
  consoleJs.includes('"/asset/"') &&
  !/return "\/static\/" \+ file \+ "\?v="/.test(consoleJs));
check("đổi brain gọi _pageLeave trước renderPage",
  /gs\.addEventListener\("change"/.test(consoleJs) &&
  /const leave = _pageLeave/.test(consoleJs));
check("console trước Alpine defer",
  html.indexOf("/static/console.js") > 0 &&
  html.indexOf("/static/console.js") < html.indexOf("alpinejs"));

process.exit(fails ? 1 : 0);
