/* Độ nhạy mic cuộc họp: AGC + VAD phòng, không EQ worklet, không bịa beamforming.

       node tests/js/test_meetings_nhay_mic.js
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

check("VAD phòng họp ~0.38 (không còn 0.6)",
  /vad_threshold:\s*"0\.38"/.test(src) && !/vad_threshold:\s*"0\.6"/.test(src));
check("cửa RMS sau AGC (~0.01)",
  /SPEECH_PEAK_MIN\s*=\s*0\.01/.test(src));
check("đo đỉnh giọng trên PCM đã AGC (không chặn giọng xa trước boost)",
  /moonshineAgcChunk\(chunk, cap\)/.test(src) &&
  /if \(rms > \(cap\.lineSpeechPeak/.test(src) &&
  src.indexOf("var boosted = moonshineAgcChunk") < src.indexOf("cap.lineSpeechPeak = rms"));
check("có AGC phần mềm trước khi đưa vào Moonshine",
  /function moonshineAgcChunk\(/.test(src) && /AGC_TARGET_RMS/.test(src));
check("AGC không khuếch đại im lặng số",
  /AGC_SILENCE_RMS/.test(src));
check("giữ lọc câu bịa (subscribe / La La School)",
  /function isMoonshineHallucinationText\(/.test(src) && src.indexOf("subscribe") >= 0 && src.indexOf("thanks for watching") >= 0);
check("mic họp: khử vọng + AGC, không khử ồn mạnh",
  /echoCancellation:\s*true/.test(src)
  && /autoGainControl:\s*true/.test(src)
  && /noiseSuppression:\s*false/.test(src));
check("getUserMedia không ép channelCount: 1 (dàn mic OS)",
  /function moonshineMicConstraints\(/.test(src) &&
  !/function moonshineMicConstraints\(\) \{[\s\S]{0,400}channelCount:\s*1/.test(src));
check("không EQ Web Audio giữa mic và worklet",
  !/function wireSpeechEmphasis\(/.test(src) && !/createBiquadFilter/.test(src));
check("addModule worklet một lần + fallback ScriptProcessor",
  /_javisMoonshineWorklet/.test(src) && /createScriptProcessor/.test(src));
check("hiện mức mic khi chưa ra chữ (không kẹt im lặng)",
  /startMoonshineMicLevelPulse/.test(src) && /mic /.test(src));
check("không hiện 'không tải lại model' lúc WASM init",
  !/Khởi tạo nhận dạng .*không tải lại model/.test(src));
check("Cloud STT họp VAD thấp hơn 0.028",
  /Math\.max\(0\.012, baseline/.test(src));
const v = Number((html.match(/meetings\.js\?v=(\d+)/) || [])[1] || 0);
check("meetings.js đã bump ?v= (>= 32)", v >= 32, v);

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_meetings_nhay_mic");
