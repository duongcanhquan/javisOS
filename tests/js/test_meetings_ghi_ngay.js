/* Cuộc họp: Moonshine trước, thanh trạng thái đúng engine, không đẩy Gemini khi Moonshine chạy.

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

check("beginSttFast gọi Moonshine trước (không cần engineReady mới chịu chạy)",
  beginFn.indexOf("await startMoonshine") !== -1 &&
  beginFn.indexOf("preferMoonshineFirst") < beginFn.indexOf("await startMoonshine") &&
  beginFn.indexOf("await startMoonshine") < beginFn.indexOf("hasWebSpeech"));
check("Moonshine lỗi thì Web Speech, không đẩy Gemini",
  /không đẩy Gemini/.test(beginFn) &&
  beginFn.indexOf("startWebSpeechSafe") < beginFn.indexOf("tryStartCloudStt"));
check("thanh trạng thái theo state.sttEngine (setMeetingSttStatus)",
  /function setMeetingSttStatus\(/.test(src) &&
  /Đang ghi \(Moonshine · /.test(src) &&
  src.indexOf("setMeetingSttStatus(root)") !== -1);
check("không hiện 'ghi ngay' Cloud/Gemini khi Bắt đầu Moonshine",
  !/Bật micro — ghi ngay/.test(src) && /Bật micro \(Moonshine\)/.test(src));
check("timeout WASM 28s + ngủ audio lúc load",
  /MOONSHINE_INIT_TIMEOUT_MS\s*=\s*28000/.test(src) && /function pauseAudioForWasmLoad\(/.test(src));
check("không import jsDelivr Moonshine",
  src.indexOf("cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm") === -1);
const v = Number((html.match(/meetings\.js\?v=(\d+)/) || [])[1] || 0);
check("meetings.js đã bump ?v= (>= 35)", v >= 35, v);

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_meetings_ghi_ngay");
