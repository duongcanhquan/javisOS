/* Fast-turn giọng nói khớp server/pipecat_voice.py

       node tests/js/test_voice_fast_turn.js
*/
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const fails = [];
function check(name, cond, extra) {
  console.log((cond ? "ok   " : "FAIL ") + name + (cond || extra === undefined ? "" : "  [" + extra + "]"));
  if (!cond) fails.push(name);
}

function napVoice() {
  const win = {
    SpeechRecognition: class { start() {} stop() {} abort() {} },
    speechSynthesis: { getVoices: () => [], cancel() {}, speak() {} },
    localStorage: { getItem: () => null, setItem() {} },
    AudioContext: null,
    isSecureContext: true,
  };
  const doc = { addEventListener() {}, createElement: () => ({ play: () => Promise.resolve() }) };
  const src = fs.readFileSync(path.join(ROOT, "dashboard", "voice.js"), "utf8").replace(/\r\n/g, "\n");
  return new Function("window", "localStorage", "navigator", "document",
    src + "; return JavisVoice;")(win, win.localStorage,
      { userAgent: "node", platform: "x", mediaDevices: null }, doc);
}

const JavisVoice = napVoice();
const ms = (text, interim, fast) => JavisVoice.silenceMsForTurn(text, interim, fast);

check("tắt fast_turn luôn 1900", ms("Xong chưa?", false, false) === 1900);
check("chưa có chữ → 1900", ms("", false, true) === 1900);
check("còn interim → 1900", ms("hôm nay mình", true, true) === 1900);
check("hết câu hỏi → 400", ms("Mấy giờ rồi?", false, true) === 400);
check("hết câu than → 400", ms("Làm ngay!", false, true) === 400);
check("hết câu chấm → 400", ms("Xong rồi.", false, true) === 400);
check("câu thường → 900", ms("mở trang models", false, true) === 900);
check("cụm 'và' → 1400", ms("viết giúp anh và", false, true) === 1400);
check("cụm 'nhưng' → 1400", ms("hay đấy nhưng", false, true) === 1400);
check("cụm 'and' → 1400", ms("open the file and", false, true) === 1400);

const voice = fs.readFileSync(path.join(ROOT, "dashboard", "voice.js"), "utf8").replace(/\r\n/g, "\n");
const html = fs.readFileSync(path.join(ROOT, "dashboard", "index.html"), "utf8").replace(/\r\n/g, "\n");
check("onresult dùng endpointDelay (móc fast-turn), không cứng 1900",
  /if \(this\.endpointDelay\) ms = this\.endpointDelay\(display\)/.test(voice));
check("có static silenceMsForTurn khớp pipecat_voice.py",
  /static silenceMsForTurn\(text, hasInterim, fastTurn\)/.test(voice));
check("có setFastTurn cho quick-settings / console",
  /setFastTurn\(on\) \{ this\.fastTurn = !!on; \}/.test(voice));
check("index.html có công tắc qsFastTurn", html.includes('id="qsFastTurn"'));
const v = Number((html.match(/voice\.js\?v=(\d+)/) || [])[1] || 0);
check("voice.js đã bump ?v= (>= 26)", v >= 26, v);
check("constructor gán fastTurn trước _initRecognition",
  /this\.fastTurn =[\s\S]*?this\._initRecognition\(\)/.test(voice));

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_voice_fast_turn");
