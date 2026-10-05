/* Hub marketingskills + openmontage + gap skills. */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "../..");

function check(name, cond) {
  if (!cond) {
    console.error("FAIL", name);
    process.exit(1);
  }
  console.log("ok  ", name);
}

function read(rel) {
  return fs.readFileSync(path.join(ROOT, rel), "utf8");
}

const hub = read(".claude/skills/marketingskills/SKILL.md");
const om = read(".claude/skills/openmontage/SKILL.md");
const mkt = read(".claude/skills/marketing-hub/SKILL.md");
const lam = read(".claude/skills/lam-video/SKILL.md");
const cat = read(".claude/skills/lam-video/references/catalog.md");

check("marketingskills hub", hub.includes("coreyhaines31/marketingskills") && hub.includes("cold-email-b2b"));
check("openmontage AGPL no vendor", om.includes("AGPL") && om.includes("Cấm") && om.includes("OPENMONTAGE_HOME"));
check("gap skills exist", ["cold-email-b2b", "churn-prevention", "ab-testing-marketing", "lead-magnets"].every((s) =>
  fs.existsSync(path.join(ROOT, `.claude/skills/${s}/SKILL.md`))
));
check("marketing-hub map", mkt.includes("marketingskills") && mkt.includes("cold-email-b2b"));
check("lam-video openmontage", lam.includes("openmontage") && cat.includes("`openmontage`"));
check("desc marketingskills <=150", /description:\s*"([^"]+)"/.exec(hub)[1].length <= 150);
check("desc openmontage <=150", /description:\s*"([^"]+)"/.exec(om)[1].length <= 150);

console.log("TẤT CẢ PASS");
