/* Canary: trang Tạo video gắn rail + script. */
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "../..");
let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails++;
}

const videoJs = fs.readFileSync(path.join(root, "dashboard/video.js"), "utf8");

const { execFileSync } = require("child_process");
try {
  execFileSync(process.execPath, ["--check", path.join(root, "dashboard/video.js")], { stdio: "pipe" });
  check("video.js cú pháp hợp lệ (node --check)", true);
} catch (e) {
  check("video.js cú pháp hợp lệ (node --check)", false);
  console.log("      ", (e.stderr || e.message || "").toString().slice(0, 200));
}

const consoleJs = fs.readFileSync(path.join(root, "dashboard/console.js"), "utf8");
const indexHtml = fs.readFileSync(path.join(root, "dashboard/index.html"), "utf8");
const vi = fs.readFileSync(path.join(root, "dashboard/i18n/vi.json"), "utf8");
const en = fs.readFileSync(path.join(root, "dashboard/i18n/en.json"), "utf8");

check("video.js export renderTaoVideo", /window\.renderTaoVideo\s*=/.test(videoJs));
check("video.js có tab Promo / pipeline postcard", /postcard-video/.test(videoJs) && /Promo ngắn/.test(videoJs));
check("video.js form chia mục 1/2", /jw-sec/.test(videoJs) && /Bạn muốn nói gì/.test(videoJs));
check("video.js tab có blurb", /jw-tab-blurb/.test(videoJs));
check("video.js không em dash", !videoJs.includes("\u2014"));
check("console rail có id video", /"video"/.test(consoleJs) && /ids: \[.*"video"/.test(consoleJs));
check("console gọi renderTaoVideo", /renderTaoVideo/.test(consoleJs));
check("index nạp video.js", /\/static\/video\.js/.test(indexHtml));
check("i18n vi page.video.label", /"page\.video\.label"\s*:\s*"Tạo video"/.test(vi));
check("i18n en page.video.label", /"page\.video\.label"\s*:\s*"Make video"/.test(en));

process.exit(fails ? 1 : 0);
