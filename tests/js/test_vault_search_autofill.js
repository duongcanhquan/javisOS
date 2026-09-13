/* Ô tìm note panel VAULT không được tự điền username (Chrome/Edge).
   Chạy: node tests/js/test_vault_search_autofill.js
*/
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const HTML = fs.readFileSync(path.join(ROOT, "dashboard", "index.html"), "utf8");
const CSS = fs.readFileSync(path.join(ROOT, "dashboard", "style.css"), "utf8");
const CON = fs.readFileSync(path.join(ROOT, "dashboard", "console.js"), "utf8");

let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails++;
}

const inp = (HTML.match(/<input[^>]*id="vaultSearch"[^>]*>/) || [""])[0];
check("có ô #vaultSearch", /id="vaultSearch"/.test(inp));
check("type=search (không phải text — Chrome hay nhét username vào text)", /type="search"/.test(inp));
check("name riêng, không phải username", /name="javis-vault-note-q"/.test(inp));
check("autocomplete=off + chống LastPass/1Password",
  /autocomplete="off"/.test(inp) && /data-lpignore="true"/.test(inp) && /data-1p-ignore="true"/.test(inp));
check("placeholder Tìm note (không value sẵn)",
  /placeholder="Tìm note\.\.\."/.test(inp) && !/\svalue=/.test(inp));

check("console có _vtChanAutofill", /function _vtChanAutofill\(/.test(CON));
check("_vtWire gọi chặn autofill", /_vtChanAutofill\(input,\s*apply\)/.test(CON));
check("chỉ tin keydown/paste, không tin input giả",
  /dataset\.vtUserTyped/.test(CON) && /animationName === "javis-vt-af"/.test(CON));
check("xoá value autofill rồi apply lại cây",
  /input\.value = ""/.test(CON) && /pageshow/.test(CON));

check("CSS bắt :-webkit-autofill",
  /#vaultSearch:-webkit-autofill/.test(CSS) && /javis-vt-af/.test(CSS));

const v = (f) => Number((HTML.match(new RegExp(f.replace(/\./g, "\\.") + "\\?v=(\\d+)")) || [])[1] || 0);
check("console.js cache-bust >= 149", v("console.js") >= 149);
check("style.css cache-bust >= 93", v("style.css") >= 93);

if (fails) { console.log("\n" + fails + " FAIL"); process.exit(1); }
console.log("\nTẤT CẢ PASS");
