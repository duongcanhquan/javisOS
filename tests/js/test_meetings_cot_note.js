/* Cuộc họp: 3 cột trên 1 màn (form | transcript | note) + tổng kết lại từ lưu trữ.

       node tests/js/test_meetings_cot_note.js
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

check("cột ghi chú sống #mtLiveNotes",
  /id="mtLiveNotes"/.test(src) && /mt-col-notes/.test(src));
check("3 cột trên 1 hàng (info | transcript | note)",
  /grid-template-columns:minmax\(0,[^)]+\) minmax\(0,[^)]+\) minmax\(0,[^)]+\)/.test(src) ||
  /grid-template-columns:[^;]*mt-col/.test(src) ||
  (/mt-col-info/.test(src) && /mt-col-live/.test(src) && /mt-col-notes/.test(src) &&
   /grid-template-columns:/.test(src) && (src.match(/minmax\(0,/g) || []).length >= 3));
check("không để form ghi chú cũ chiếm cột trái (chuyển sang cột note)",
  !/<textarea id="mtNotes"/.test(src));
check("lưu note lúc họp (debounce /meetings/.../notes)",
  /\/meetings\/" \+ encodeURIComponent\(.*\) \+ "\/notes"/.test(src) ||
  /\/notes"/.test(src) && /function flushLiveNotes\(/.test(src));
check("lưu trữ luôn có tab Tổng kết (kể cả chưa có file summary)",
  /data-dtab="summary"/.test(src) &&
  !/\(r\.has_summary\s*\n?\s*\? '<button[^']*data-dtab="summary"/.test(src));
check("nút Tổng kết lại trên chi tiết lưu trữ",
  /mt-detail-analyze/.test(src) && /Tổng kết/.test(src));
check("màn ghi mới khóa chiều cao viewport (không kéo dài trang)",
  /height:calc\(100dvh - 108px\)/.test(src) && /#mtPanelNew:not\(\[hidden\]\)\{flex:1/.test(src));
check("nút mở rộng tổng kết (overlay đọc được)",
  /function openSummaryOverlay\(/.test(src) &&
  /Mở rộng/.test(src) &&
  /mt-sum-overlay/.test(src) &&
  /mtSumOverlay/.test(src));
check("ô gắn dự án có tìm + danh sách hiện (không chỉ select 1 hàng)",
  /KnowProjectQ/.test(src) &&
  /size="6"/.test(src) &&
  /Chưa thấy dự án trên bộ não/.test(src) &&
  /function paintProjectSelect\(/.test(src));
check("GET dự án cuộc họp dùng credentials và não đang mở",
  /\/projects\?brain=/.test(src) &&
  /credentials:\s*"same-origin"/.test(src));
check("tab Fathom trên trang cuộc họp (không ghi mic trong Javis)",
  /data-mt-tab="fathom"/.test(src) &&
  /mtPanelFathom/.test(src) &&
  /Fathom không ghi mic trong Javis/.test(src) &&
  /\/meetings\/fathom\/sync/.test(src) &&
  /\/meetings\/fathom\/import/.test(src) &&
  /Alpine\.store\("nav"\)\.go\("mcp"\)/.test(src) &&
  /function safeHttpUrl\(/.test(src));
const v = Number((html.match(/meetings\.js\?v=(\d+)/) || [])[1] || 0);
check("meetings.js đã bump ?v= (>= 45)", v >= 45, v);

if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_meetings_cot_note");
