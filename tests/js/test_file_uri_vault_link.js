/* Link markdown Antigravity/Gemini chen file:// phai mo dung file vault, khong 404.

       node tests/js/test_file_uri_vault_link.js

   Loi that (RCA dashboard): bam [wiki/...](file:///brains/Brain%20Default/wiki/....md)
   -> popup "Khong tim thay file", data-vault-path van la chuoi file://...
   Goc: appFileRef khong nhan file://; isVaultRel coi file: la path tuong doi. */
const path = require("path");
const fs = require("fs");

const ROOT = path.join(__dirname, "..", "..");
const {
  mdToHtml, appFileRef, appFilePath, isVaultRel,
  fileUriToPathish, normalizeVaultOpenPath,
} = require(path.join(ROOT, "dashboard", "chat-render.js"));
const CR = fs.readFileSync(path.join(ROOT, "dashboard", "chat-render.js"), "utf8");
const CONSOLE = fs.readFileSync(path.join(ROOT, "dashboard", "console.js"), "utf8");
const INDEX = fs.readFileSync(path.join(ROOT, "dashboard", "index.html"), "utf8");
const CLAUDE = fs.readFileSync(path.join(ROOT, "CLAUDE.md"), "utf8");

const fails = [];
const check = (name, cond) => {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails.push(name);
};

global.currentBrainPath = () => "brains/Brain Default";

const vaultPath = (md) => {
  const m = /data-vault-path="([^"]*)"/.exec(mdToHtml(md));
  return m ? m[1] : null;
};

const TITLE = "30 Ngày Làm Chủ Antigravity (CES Global).md";
const ENC = "30%20Ng%C3%A0y%20L%C3%A0m%20Ch%E1%BB%A7%20Antigravity%20(CES%20Global).md";
const FILE_BRAINS =
  "file:///brains/Brain%20Default/wiki/" + ENC;
const FILE_OTHER_NAME =
  "file:///brains/School%20of%20Art/wiki/Phap-Ly.md";
const FILE_BARE = "file:///wiki/" + ENC;
const FILE_LOCALHOST =
  "file://localhost/brains/Brain%20Default/wiki/foo.md";

// ============================================================
// 1. isVaultRel khong con nuot file://
// ============================================================
check("CANARY: file:// KHONG phai vault-rel", isVaultRel(FILE_BRAINS) === false);
check("wiki/foo.md van la vault-rel", isVaultRel("wiki/foo.md") === true);
check("https khong phai vault-rel", isVaultRel("https://x.com/a") === false);

// ============================================================
// 2. fileUriToPathish
// ============================================================
check("file:///brains/... -> /brains/...",
  fileUriToPathish(FILE_BRAINS) ===
  "/brains/Brain Default/wiki/" + TITLE);
check("file:///wiki/... -> /wiki/...",
  fileUriToPathish(FILE_BARE) === "/wiki/" + TITLE);
check("file://localhost/brains/... bo host",
  fileUriToPathish(FILE_LOCALHOST) === "/brains/Brain Default/wiki/foo.md");
check("file:///C:/Windows... bi loai (khong vault)",
  fileUriToPathish("file:///C:/Users/x/a.md") === "");

// ============================================================
// 3. appFileRef / appFilePath - dung RCA
// ============================================================
check("CANARY: file:///brains/Brain Default/wiki/... -> path wiki",
  appFilePath(FILE_BRAINS) === "wiki/" + TITLE);
check("appFileRef tra brain dang chat",
  (appFileRef(FILE_BRAINS) || {}).brain === "brains/Brain Default");
check("file:///wiki/... (khong /brains) van ra wiki/...",
  appFilePath(FILE_BARE) === "wiki/" + TITLE);
check("file:// + ten nao KHAC (doi ten / Antigravity) van lay path tuong doi",
  appFilePath(FILE_OTHER_NAME) === "wiki/Phap-Ly.md");
check("/brains/... khong file:// van khop khi dung nao",
  appFilePath("/brains/Brain Default/wiki/x.md") === "wiki/x.md");
check("/brains/Other/... khong file://: khong mo nham (giu luat cu)",
  appFileRef("/brains/Other Brain/wiki/x.md") === null);

// ============================================================
// 4. mdToHtml: data-vault-path PHAI sach (khong con file://)
// ============================================================
const rcaMd = "[Antigravity](" + FILE_BRAINS + ")";
check("CANARY: render RCA -> data-vault-path = wiki/... (khong file://)",
  vaultPath(rcaMd) === "wiki/" + TITLE);
check("render khong de sot chuoi file: trong data-vault-path",
  (vaultPath(rcaMd) || "").indexOf("file:") < 0);
check("href deep-link #open= cung la path sach",
  /href="#open=wiki%2F/.test(mdToHtml(rcaMd)) ||
  /href="#open=.*30/.test(mdToHtml(rcaMd)));

const schoolMd =
  "[phap ly](file:///brains/School%20of%20Art/wiki/Phap-Ly-Lien-Ket.md)";
check("School of Art file:// -> wiki/Phap-Ly-Lien-Ket.md",
  vaultPath(schoolMd) === "wiki/Phap-Ly-Lien-Ket.md");

// Anh file:// cung ve /files/raw dung path
const anh = mdToHtml("![a](file:///brains/Brain%20Default/attachments/a%20b.png)");
check("anh file:// khong con file: trong src", anh.indexOf("file:") < 0);
check("anh file:// ra /files/raw", /\/files\/raw\?/.test(anh));
check("anh file:// path dung (mot lop ma hoa)",
  /path=attachments%2Fa%20b\.png/.test(anh) || /path=attachments%2Fa\+b\.png/.test(anh) === false);
check("anh file:// path attachments/a b.png",
  /path=attachments%2Fa%20b\.png/.test(anh));

// ============================================================
// 5. normalizeVaultOpenPath (phong thu click / lich su cu)
// ============================================================
check("normalize file:// brains -> wiki path",
  normalizeVaultOpenPath(FILE_BRAINS) === "wiki/" + TITLE);
check("normalize path thuong giu nguyen",
  normalizeVaultOpenPath("wiki/foo.md") === "wiki/foo.md");

// ============================================================
// 6. Canary ma nguon: loai file: trong isVaultRel; openVaultPath phong thu
// ============================================================
check("isVaultRel loai file: trong regex",
  /!\^\(https\?:\|mailto:\|data:\|blob:\|file:\|\\\/\)/i.test(CR) ||
  /file:\|\\\//.test(CR));
check("co ham fileUriToPathish", /function fileUriToPathish\(/.test(CR));
check("openVaultPath phong thu file:",
  /function openVaultPath[\s\S]*?\^file:/i.test(CONSOLE));
check("cache-bust chat-render >= 13",
  /chat-render\.js\?v=(\d+)/.test(INDEX) &&
  parseInt(RegExp.$1, 10) >= 13);
check("CLAUDE.md cam file:// trong link vault",
  /NEVER use the `file:\/\//.test(CLAUDE) || /NEVER use the \*\*`file:\/\//.test(CLAUDE) ||
  /NEVER use the \*\*`file:\/\//.test(CLAUDE) ||
  CLAUDE.indexOf("NEVER use the `file://` scheme") >= 0);

// ============================================================
// 7. Khong pha URL ngoai / path tuong doi thuong
// ============================================================
check("URL https van mo tab ngoai, khong vault",
  mdToHtml("[x](https://example.com/a%20b)").indexOf("data-vault-path") < 0);
check("path tuong doi thuong van chay",
  vaultPath("[x](wiki/hello.md)") === "wiki/hello.md");
check("%20 path tuong doi van decode",
  vaultPath("[x](wiki/Hello%20World.md)") === "wiki/Hello World.md");

console.log("");
if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_file_uri_vault_link: tat ca pass");
