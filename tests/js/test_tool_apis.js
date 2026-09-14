/* Canary trang Khóa API. Chay: node tests/js/test_tool_apis.js */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const root = path.join(__dirname, "../..");
const TA = require("../../dashboard/tool-apis.js");

let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails++;
}

try {
  execFileSync(process.execPath, ["--check", path.join(root, "dashboard/tool-apis.js")], { stdio: "pipe" });
  check("tool-apis.js cú pháp hợp lệ", true);
} catch (e) {
  check("tool-apis.js cú pháp hợp lệ", false);
}

check("export render + htmlFrom", typeof TA.render === "function" && typeof TA.htmlFrom === "function");

const html = TA.htmlFrom({
  groups: [
    { id: "video", label: "Video", label_en: "Video" },
    { id: "image", label: "Ảnh", label_en: "Images" },
    { id: "search", label: "Tìm trên web", label_en: "Web search" },
    { id: "voice", label: "Giọng đọc", label_en: "Voice" },
    { id: "maps", label: "Bản đồ", label_en: "Maps" },
    { id: "custom", label: "Khóa tự thêm", label_en: "Custom keys" },
  ],
  items: [{
    id: "atlascloud", env: "ATLASCLOUD_API_KEY", group: "video", kind: "secret",
    label: "Atlas Cloud", label_en: "Atlas Cloud",
    dung_de: "Collage giấy", dung_de_en: "Paper collage",
    where: "https://www.atlascloud.ai/console/api-keys",
    set: false, from_env: false, suffix: "",
  }, {
    id: "image_seedream", env: "IMAGE_SEEDREAM_API_KEY", group: "image", kind: "secret",
    label: "Seedream", label_en: "Seedream",
    dung_de: "Ảnh slide", dung_de_en: "Slide images",
    where: "", set: false, from_env: false, suffix: "",
  }, {
    id: "tts_azure", env: "TTS_AZURE_API_KEY", group: "voice", kind: "secret",
    label: "Azure TTS", label_en: "Azure TTS",
    dung_de: "Đọc lời", dung_de_en: "Narration",
    where: "", set: true, from_env: false, suffix: "aaaa",
  }],
  custom: [{ env: "MY_VIDEO_API_KEY", set: true, from_env: false, suffix: "zz99" }],
});
check("vẽ thẻ Atlas", html.indexOf("Atlas Cloud") !== -1 && html.indexOf("ATLASCLOUD_API_KEY") !== -1);
check("vẽ nhóm ảnh Seedream", html.indexOf("Seedream") !== -1 && html.indexOf("IMAGE_SEEDREAM_API_KEY") !== -1);
check("vẽ nhóm giọng Azure TTS", html.indexOf("Azure TTS") !== -1);
check("vẽ khóa tự thêm", html.indexOf("MY_VIDEO_API_KEY") !== -1);
check("có form thêm khóa", html.indexOf("id=\"taAdd\"") !== -1 && html.indexOf("id=\"taNewEnv\"") !== -1);
check("htmlFrom không lộ khóa đầy đủ", html.indexOf("sk-") === -1);
check("không em dash", html.indexOf("\u2014") === -1);

const indexHtml = fs.readFileSync(path.join(root, "dashboard/index.html"), "utf8");
const consoleJs = fs.readFileSync(path.join(root, "dashboard/console.js"), "utf8");
const videoJs = fs.readFileSync(path.join(root, "dashboard/video.js"), "utf8");
check("index nạp tool-apis.js trước console.js",
  indexHtml.indexOf('src="/static/tool-apis.js') !== -1
  && indexHtml.indexOf('src="/static/tool-apis.js') < indexHtml.indexOf('src="/static/console.js'));
check("console rail có tool_apis", /"tool_apis"/.test(consoleJs) && /tool_apis:\s*"key"/.test(consoleJs));
check("trang Tạo video trỏ Khóa API", /vidGotoKeys/.test(videoJs) && /tool_apis/.test(videoJs));

if (fails) {
  console.log("\nFAIL - test_tool_apis: " + fails + " lỗi");
  process.exit(1);
}
console.log("\nOK - test_tool_apis: tất cả pass");
