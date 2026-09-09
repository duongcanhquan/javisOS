/* Cuộc họp: hàng rào WASM (pthread, timeout, không CDN) — đi cùng test_meetings_ghi_ngay.js

       node tests/js/test_meetings_wasm_treo.js
*/
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const src = fs.readFileSync(path.join(ROOT, "dashboard", "meetings.js"), "utf8");
const html = fs.readFileSync(path.join(ROOT, "dashboard", "index.html"), "utf8");
const fails = [];

function check(name, cond, extra) {
  console.log((cond ? "ok   " : "FAIL ") + name + (cond || extra === undefined ? "" : "  [" + extra + "]"));
  if (!cond) fails.push(name);
}

check("timeout khởi tạo WASM ~28s (không 180s)",
  /MOONSHINE_INIT_TIMEOUT_MS\s*=\s*28000/.test(src) &&
  /promiseTimeout\(\s*mod\.Transcriber\.load\(\{[\s\S]{0,220}MOONSHINE_INIT_TIMEOUT_MS/.test(src));
check("ngủ AudioContext trước khi Transcriber.load",
  /function pauseAudioForWasmLoad\(/.test(src) &&
  /await pauseAudioForWasmLoad\(\);\s*transcriber = await promiseTimeout\(\s*mod\.Transcriber\.load/.test(src));
check("mở mic lúc nạp model với keepSuspended: true",
  /openMoonshineMicEarly\(\{\s*keepSuspended:\s*true\s*\}\)/.test(src));
check("gắn micro sau load thì resume (keepSuspended: false)",
  /openMoonshineMicEarly\(\{\s*keepSuspended:\s*false\s*\}\)/.test(src));
check("không import jsDelivr Moonshine (pthread pool = số CPU → treo)",
  src.indexOf("cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm") === -1 &&
  !/CDN_FALLBACK/.test(src));
const v = Number((html.match(/meetings\.js\?v=(\d+)/) || [])[1] || 0);
check("meetings.js đã bump ?v= (>= 35)", v >= 35, v);

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_meetings_wasm_treo");
