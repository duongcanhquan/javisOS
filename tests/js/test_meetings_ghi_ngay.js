/* Cuộc họp: Bắt đầu ghi ngay (Cloud/Web Speech), không chờ Moonshine WASM.

       node tests/js/test_meetings_ghi_ngay.js
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

const begin = src.split("async function beginSttFast")[1] || "";
const beginFn = begin.split("async function startMeeting")[0] || "";

check("có moonshineEngineReady (chỉ dùng Moonshine khi đã nạp xong)",
  /function moonshineEngineReady\(/.test(src));
check("beginSttFast gọi Moonshine khi engineReady, không chặn WASM lúc Bắt đầu",
  /moonshineEngineReady\(lang\)/.test(beginFn) &&
  beginFn.indexOf("moonshineEngineReady") < beginFn.indexOf("await startMoonshine"));
check("beginSttFast ghi Cloud STT trước khi last-resort Moonshine",
  beginFn.indexOf("tryStartCloudStt") < beginFn.lastIndexOf("await startMoonshine") &&
  /Đang ghi \(/.test(beginFn));
check("Cloud STT không bị preferMoonshineFirst chặn",
  /function preferCloudBeforeWebSpeech\(lang\) \{[\s\S]{0,80}lang = normalizeLang/.test(src) &&
  !/function preferCloudBeforeWebSpeech\(lang\) \{[\s\S]{0,120}preferMoonshineFirst/.test(src));
check("Bắt đầu hiện 'ghi ngay' khi Moonshine chưa sẵn",
  /Bật micro — ghi ngay/.test(src) && /useMoonNow/.test(src));
check("hint: Bắt đầu vẫn ghi ngay khi đang chuẩn bị Moonshine",
  /Bắt đầu vẫn ghi ngay/.test(src) && /Bấm Bắt đầu sẽ ghi ngay/.test(src));
check("timeout WASM 28s + ngủ audio lúc load (last-resort)",
  /MOONSHINE_INIT_TIMEOUT_MS\s*=\s*28000/.test(src) && /function pauseAudioForWasmLoad\(/.test(src));
check("không import jsDelivr Moonshine",
  src.indexOf("cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm") === -1);
const v = Number((html.match(/meetings\.js\?v=(\d+)/) || [])[1] || 0);
check("meetings.js đã bump ?v= (>= 34)", v >= 34, v);

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_meetings_ghi_ngay");
