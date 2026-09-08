#!/usr/bin/env node
/** Đăng nhập mới → khung chat trống; F5 vẫn restore. Lịch sử vẫn mở chat cũ. */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "../..");
const src = fs.readFileSync(path.join(ROOT, "dashboard/app.js"), "utf8");
const fails = [];
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails.push(name);
}

check("có markFreshLogin", src.includes("function markFreshLogin"));
check("có consumeFreshLogin", src.includes("function consumeFreshLogin"));
check("có bootChatView", src.includes("function bootChatView"));
check("cờ sessionStorage javis.freshLogin", src.includes('javis.freshLogin'));
check("login thành công gọi markFreshLogin",
  /\/auth\/login[\s\S]{0,400}markFreshLogin\(\);\s*location\.reload/.test(src));
check("boot dùng bootChatView chứ không restoreSession trần",
  src.includes("bootChatView();") && !/\/\/[^\n]*\nrestoreSession\(\);/.test(
    src.slice(src.indexOf("// Boot khung chat:"))));
check("fresh login xoá snapshot local",
  /consumeFreshLogin[\s\S]{0,500}saveSessionMap\(\{\}\)/.test(src)
  && /consumeFreshLogin[\s\S]{0,500}saveViewByBrain\(\{\}\)/.test(src));
check("fresh login gọi resetChatView",
  /consumeFreshLogin[\s\S]{0,600}resetChatView\(\{\s*skipPersist:\s*true\s*\}\)/.test(src));
check("F5 vẫn đi restoreSession khi không fresh",
  /bootChatView[\s\S]{0,800}restoreSession\(\)/.test(src));

if (fails.length) {
  console.log("THẤT BẠI:", fails.join("; "));
  process.exit(1);
}
console.log("OK - test_login_new_chat");
