/* Tín hiệu thiên hà nền — kiểm tra surface API + HTML/CSS/gates.
   Chạy: node tests/js/test_brain_waves.js
*/
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const WAVES = fs.readFileSync(path.join(ROOT, "dashboard", "brain-waves.js"), "utf8");
const HTML = fs.readFileSync(path.join(ROOT, "dashboard", "index.html"), "utf8");
const CSS = fs.readFileSync(path.join(ROOT, "dashboard", "style.css"), "utf8");
const CONSOLE = fs.readFileSync(path.join(ROOT, "dashboard", "console.js"), "utf8");

let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails++;
}

check("brain-waves.js export JavisBrainWaves", /window\.JavisBrainWaves\s*=/.test(WAVES));
check("có pause/wake/setLite/setMode", /pause:\s*function/.test(WAVES) && /wake:\s*function/.test(WAVES) && /setLite:\s*function/.test(WAVES) && /setMode:\s*function/.test(WAVES));
check("tôn trọng prefers-reduced-motion", /prefers-reduced-motion/.test(WAVES));
check("đổi nhịp theo javis-flow-mode", /javis-flow-mode/.test(WAVES));
check("HTML có canvas #brainWaves", /id="brainWaves"/.test(HTML));
check("HTML nạp brain-waves.js", /brain-waves\.js/.test(HTML));
check("CSS #brainWaves pointer-events none", /#brainWaves[\s\S]{0,160}pointer-events:\s*none/.test(CSS));
check("CSS #brainWaves trên starfield (z-index 1)", /#brainWaves[\s\S]{0,200}z-index:\s*1/.test(CSS));
check("CSS #brainWaves mờ (opacity < 1)", /#brainWaves[\s\S]{0,220}opacity:\s*0\.\d+/.test(CSS));
check("console.js gate pause/lite BrainWaves", /JavisBrainWaves/.test(CONSOLE) && /JavisBrainWaves[\s\S]{0,40}pause/.test(CONSOLE));
check("có vòng radar + tia ping", /drawRings/.test(WAVES) && /drawBeams/.test(WAVES) && /drawPings/.test(WAVES));
check("không vẽ ribbon sóng não", !/strokeRibbon|function ribbons\s*\(/.test(WAVES));
check("ping vẫn chuyển động (spd)", /spd:\s*0\.00/.test(WAVES) && /requestAnimationFrame/.test(WAVES));

if (fails) { console.log("\n" + fails + " FAIL"); process.exit(1); }
console.log("\nTẤT CẢ PASS");
