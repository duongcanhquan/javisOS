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
check("Moonshine lỗi (không ghi loa) thì Web Speech, không đẩy Gemini",
  /không đẩy Gemini/.test(beginFn) &&
  beginFn.indexOf("startWebSpeechSafe") < beginFn.indexOf("tryStartCloudStt"));
check("đang mix loa máy thì không nhảy Web Speech",
  /function allowWebSpeechFallback\(/.test(src) &&
  /allowWebSpeechFallback\(\) && hasWebSpeech\(\)/.test(src) &&
  /allowWebSpeechFallback\(\) && hasWebSpeech\(\) && prev !== "webspeech"/.test(src));
check("watchdog không recover Moonshine khi capture còn sống (giọng nhỏ / ngắt câu)",
  /function moonshineCaptureAlive\(/.test(src) &&
  /_lastChunkAt/.test(src) &&
  /if \(moonshineCaptureAlive\(\)\)/.test(src) &&
  !/function moonshineCaptureAlive\([\s\S]{0,280}peakRms/.test(src));
check("im lặng đầu họp không restart mic (chunk vẫn chảy thì không phải mic chết)",
  /deadMic = \(cap\.chunks \|\| 0\) < 8/.test(src) &&
  !/\(cap\.peakRms \|\| 0\) < 0\.0008/.test(src));
check("chốt transcribe khi hết giọng và khi teardown (tránh mất câu / chậm)",
  /function moonshineForceTranscribe\(/.test(src) &&
  /cap\._hadSpeech/.test(src) &&
  /moonshineForceTranscribe\(cap\)/.test(src) &&
  /async function teardownMoonshineCapture[\s\S]{0,400}moonshineForceTranscribe\(cap\)/.test(src));
check("mix loa máy lỗi không xóa cờ khi display vẫn sống",
  /if \(!displayAudioLive\(\)\) \{\s*state\._hasSystemAudio = false/.test(src));
check("recover STT giữ display stream (không mất loa máy)",
  /function cleanupSttEngines\(/.test(src) &&
  /cleanupSttEngines\(\{\s*keepDisplay:\s*true/.test(src));
check("transcribe Moonshine không gọi mỗi chunk (tránh trễ / teardown nhầm)",
  /MOONSHINE_TRANSCRIBE_MIN_MS\s*=\s*320/.test(src) &&
  /function moonshineMaybeTranscribe\(/.test(src) &&
  src.indexOf("moonshineMaybeTranscribe(cap") !== -1 &&
  !/addAudio\(resampled, 16000\);\s*cap\.moonStream\.transcribe\(\)/.test(src));
check("EN Moonshine có max_tokens_per_second (chặn decoder chậm / bịa)",
  /en:\s*\{[\s\S]{0,180}max_tokens_per_second:\s*"13\.0"/.test(src));
check("thanh trạng thái theo state.sttEngine (setMeetingSttStatus)",
  /function setMeetingSttStatus\(/.test(src) &&
  /Đang ghi \(Moonshine · /.test(src) &&
  src.indexOf("setMeetingSttStatus(root)") !== -1);
check("không hiện 'ghi ngay' Cloud/Gemini khi Bắt đầu Moonshine",
  !/Bật micro — ghi ngay/.test(src) && /Bật micro \(Moonshine\)/.test(src));
check("timeout WASM ~40s (không 180s) + ngủ audio lúc load",
  /MOONSHINE_INIT_TIMEOUT_MS\s*=\s*40000/.test(src) && /function pauseAudioForWasmLoad\(/.test(src));
check("không import jsDelivr Moonshine",
  src.indexOf("cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm") === -1);
const v = Number((html.match(/meetings\.js\?v=(\d+)/) || [])[1] || 0);
check("meetings.js đã bump ?v= (>= 43)", v >= 43, v);

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_meetings_ghi_ngay");
