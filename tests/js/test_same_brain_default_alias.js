#!/usr/bin/env node
/**
 * sameBrain phải khớp alias "brain" với não mặc định ĐÃ ĐỔI TÊN (không chỉ Brain Default).
 * Regression: bấm hội thoại cũ → im lặng không mở → chỉ chat được cuộc mới nhất.
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "../..");
const appSrc = fs.readFileSync(path.join(ROOT, "dashboard/app.js"), "utf8");

// Rút hàm sameBrain + phụ thuộc tối thiểu vào sandbox.
const start = appSrc.indexOf("function normBrainKey");
const end = appSrc.indexOf("function loadSessionMap");
if (start < 0 || end < 0) {
  console.error("FAIL không tìm thấy sameBrain block trong app.js");
  process.exit(1);
}
const snippet = appSrc.slice(start, end);

const document = {
  querySelector(sel) {
    if (sel === "#graphSource option[value='brain']") {
      return {
        dataset: { brainName: "APC.HN", brainPath: "/data/brains/APC.HN" },
        textContent: "APC.HN · 12",
      };
    }
    return null;
  },
};

const ctx = { document, console };
vm.createContext(ctx);
vm.runInContext(snippet, ctx);

const { sameBrain } = ctx;
let fail = 0;
function check(name, cond) {
  console.log((cond ? "  OK  " : "FAIL  ") + name);
  if (!cond) fail++;
}

check("brain ↔ Brain Default path", sameBrain("brain", "/brains/Brain Default"));
check("brain ↔ APC.HN path (default đổi tên)", sameBrain("brain", "/data/brains/APC.HN"));
check("brain ↔ APC.HN name", sameBrain("brain", "APC.HN"));
check("APC.HN path ↔ brain", sameBrain("/data/brains/APC.HN", "brain"));
check("khác brain thật sự", !sameBrain("/data/brains/School of Art", "brain"));
check("cùng path", sameBrain("/data/brains/X", "/data/brains/X"));

process.exit(fail ? 1 : 0);
