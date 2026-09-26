/* Nút ? prompt help cạnh thanh chat + module popup. */
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

const HTML = fs.readFileSync(path.join(ROOT, "dashboard/index.html"), "utf8");
const JS = fs.readFileSync(path.join(ROOT, "dashboard/prompt-help.js"), "utf8");
const DRIVE = fs.readFileSync(path.join(ROOT, "dashboard/drive-projects.js"), "utf8");
const GUIDES = fs.readFileSync(path.join(ROOT, "dashboard/guides.js"), "utf8");
const SYNC = fs.readFileSync(path.join(ROOT, "scripts/sync-tenant-images-vps.sh"), "utf8");
const VI = JSON.parse(fs.readFileSync(path.join(ROOT, "dashboard/i18n/vi.json"), "utf8"));
const EN = JSON.parse(fs.readFileSync(path.join(ROOT, "dashboard/i18n/en.json"), "utf8"));

check("nút promptHelpBtn trong hudVoice", HTML.includes('id="promptHelpBtn"') && HTML.includes("ph-help-btn"));
check("nạp prompt-help.js", HTML.includes("/static/prompt-help.js"));
check("module mở popup", JS.includes("window.JavisPromptHelp") && JS.includes("function open"));
check("có Chép + Dán vào chat", JS.includes('data-ph="copy"') && JS.includes('data-ph="paste"'));
check("4 kênh nhập + tra cứu", JS.includes("s1_h") && JS.includes("s2_h") && JS.includes("s3_h") && JS.includes("s4_h") && JS.includes("s5_h"));
check("Kho Drive gắn nút ?", DRIVE.includes("JavisPromptHelp.mountInline"));
check("Hướng dẫn nhắc nút ?", GUIDES.includes("prompt chuẩn") && GUIDES.includes("Dán vào chat"));
check("script sync tenant images", SYNC.includes("apply_public_hosts") && SYNC.includes("prompt-help.js"));
check("i18n vi title", typeof VI["prompt_help.title"] === "string" && VI["prompt_help.title"].length > 5);
check("i18n en title", typeof EN["prompt_help.title"] === "string" && EN["prompt_help.title"].length > 5);
check("i18n vi có prompt lưu file", VI["prompt_help.s1_save"].includes("ingest-source"));
check("không em dash trong chuỗi help", !Object.keys(VI).filter((k) => k.startsWith("prompt_help.")).some((k) => /\u2014/.test(VI[k])));

console.log("TẤT CẢ PASS");
