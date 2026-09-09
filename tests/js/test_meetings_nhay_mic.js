/* Độ nhạy mic cuộc họp: AGC + VAD phòng, không bịa beamforming.

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
check("cửa RMS giọng xa ~0.0035 (không còn 0.012)",
  /SPEECH_PEAK_MIN\s*=\s*0\.0035/.test(src) && !/speechPeak < 0\.012/.test(src));
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
check("không ép channelCount: 1 (để máy dùng dàn mic nếu có)",
  !/channelCount:\s*1/.test(src));
check("nhấn dải giọng (highpass + peaking), không giả beamforming",
  /wireSpeechEmphasis\(/.test(src) && /createBiquadFilter/.test(src));
check("Cloud STT họp VAD thấp hơn 0.028",
  /Math\.max\(0\.012, baseline/.test(src));
const v = Number((html.match(/meetings\.js\?v=(\d+)/) || [])[1] || 0);
check("meetings.js đã bump ?v= (>= 31)", v >= 31, v);

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_meetings_nhay_mic");
