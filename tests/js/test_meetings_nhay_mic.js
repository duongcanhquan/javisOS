/* Độ nhạy mic cuộc họp: AGC xa + mix loa máy, không EQ worklet, không bịa beamforming.

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

check("VAD phòng họp ~0.28 (giọng xa, không còn 0.38/0.6)",
  /vad_threshold:\s*"0\.28"/.test(src) && !/vad_threshold:\s*"0\.38"/.test(src) &&
    !/vad_threshold:\s*"0\.6"/.test(src));
check("cửa RMS sau AGC (~0.006, bắt xa)",
  /SPEECH_PEAK_MIN\s*=\s*0\.006/.test(src));
check("AGC chỉ khuếch đại, không hạ giọng đã rõ (want < 1 thì giữ 1)",
  /AGC_MAX_GAIN\s*=\s*16/.test(src) &&
    /if \(want < 1\) want = 1/.test(src) &&
    !/AGC_MIN_GAIN\s*=\s*0\.4/.test(src));
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
check("mic cuộc họp: tắt hết APM Chrome (AEC+NS+AGC phần cứng; AGC true vẫn xoá loa họp)",
  /function moonshineMicConstraints\(/.test(src) &&
  /echoCancellation:\s*false/.test(src) &&
  /googEchoCancellation:\s*false/.test(src) &&
  /autoGainControl:\s*false/.test(src) &&
  /googAutoGainControl:\s*false/.test(src) &&
  !/echoCancellation:\s*aec/.test(src) &&
  /voiceIsolation:\s*false/.test(src) &&
  /noiseSuppression:\s*false/.test(src));
check("getUserMedia không fallback { audio: true } (mặc định Chrome bật AEC)",
  !/getUserMedia\(\{\s*audio:\s*true\s*\}\)/.test(src));
check("getUserMedia không bật AEC theo hasSys",
  !/moonshineMicConstraints\(\{\s*aec:\s*hasSys\s*\}\)/.test(src) &&
  !/moonshineMicConstraints\(\{\s*aec:\s*!!state\._hasSystemAudio\s*\}\)/.test(src));
check("ghi tiếng máy: getDisplayMedia + systemAudio include",
  /function ensureDisplayAudio\(/.test(src) &&
  /getDisplayMedia\(attempts/.test(src) &&
  /systemAudio:\s*"include"/.test(src));
check("mix mic phòng + loa máy vào worklet (sysGain ≥ 1, không hạ tiếng máy)",
  /cap\.sysGain\.gain\.value = 1(?:\.2)?/.test(src) &&
  /cap\.mixGain\.connect\(cap\.workletNode\)/.test(src) &&
  !/sysGain\.gain\.value = 0\.72/.test(src));
check("checkbox Ghi tiếng máy",
  /id="mtSysAudio"/.test(src) && /Ghi tiếng máy/.test(src));
check("getUserMedia không ép channelCount: 1 (dàn mic OS)",
  /function moonshineMicConstraints\(/.test(src) &&
  !/function moonshineMicConstraints\([\s\S]{0,500}channelCount:\s*1/.test(src));
check("không EQ Web Audio giữa mic và worklet",
  !/function wireSpeechEmphasis\(/.test(src) && !/createBiquadFilter/.test(src));
check("addModule worklet một lần + fallback ScriptProcessor",
  /_javisMoonshineWorklet/.test(src) && /createScriptProcessor/.test(src));
check("worklet gộp ~4096 mẫu rồi mới postMessage (khớp smoke test, không transcribe mỗi 128)",
  /this\._buf=new Float32Array\(4096\)/.test(src) &&
  /createScriptProcessor\(4096/.test(src));
check("hiện mức tín hiệu khi chưa ra chữ (không kẹt im lặng)",
  /startMoonshineMicLevelPulse/.test(src) && /mức /.test(src));
check("không hiện 'không tải lại model' lúc WASM init",
  !/Khởi tạo nhận dạng .*không tải lại model/.test(src));
check("Cloud STT họp VAD thấp hơn 0.01",
  /Math\.max\(0\.008, baseline/.test(src));
check("hủy chia sẻ màn hình không hỏi lần hai",
  /function displayShareCancelled\(/.test(src) &&
  /NotAllowedError/.test(src) && /AbortError/.test(src) &&
  /\{ video: true, audio: true \}/.test(src));
check("mix loa máy lỗi thì tắt AEC trên mic",
  /applyMicAec\(false\)/.test(src) &&
  src.indexOf("state._hasSystemAudio = false") >= 0);
const v = Number((html.match(/meetings\.js\?v=(\d+)/) || [])[1] || 0);
check("meetings.js đã bump ?v= (>= 40)", v >= 40, v);

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_meetings_nhay_mic");
