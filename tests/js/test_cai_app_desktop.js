/* "Mở như app" phải có ở BẢN MÁY TÍNH, không chỉ mobile (chủ yêu cầu 27/08/2026).

   Vì sao trước đây desktop không cài được: manifest chỉ khai một icon PNG với
   sizes "any" - giá trị đó chỉ hợp lệ cho SVG, nên Chrome/Edge desktop coi trang là
   KHÔNG đủ điều kiện cài và không bao giờ hiện nút cài. iOS thì đi đường
   apple-touch-icon riêng nên mobile vẫn chạy dạng app được, tạo cảm giác "mobile có,
   desktop không".

   0.55.237: icon PWA lấy từ /brand-icon/192|512 (= ảnh đại diện), không còn cứng
   /static/icon-*.png. File icon-*.png vẫn giữ làm fallback khi render lỗi.

   Kiểm trên SOURCE thật: manifest phải có icon PNG vuông khai sizes rõ, route
   brand-icon phải có trong main.py, và app.js phải bắt beforeinstallprompt.

       node tests/js/test_cai_app_desktop.js
*/
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..", "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");
const manifest = JSON.parse(read("dashboard/manifest.json"));
const html = read("dashboard/index.html");
const app = read("dashboard/app.js");
const css = read("dashboard/style.css");
const mainPy = read("server/main.py");

let fails = [];
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails.push(name);
}

// ---- 1. Manifest đủ điều kiện cài trên desktop ----
const icons = manifest.icons || [];
const i192 = icons.find((i) => i.sizes === "192x192");
const i512 = icons.find((i) => i.sizes === "512x512");
check("manifest có icon 192x192", !!i192);
check("manifest có icon 512x512", !!i512);
check("icon khai type image/png", icons.every((i) => i.type === "image/png"));
check("không còn icon PNG khai sizes 'any' (Chrome coi là không hợp lệ)",
  !icons.some((i) => i.sizes === "any"));
check("display standalone giữ nguyên", manifest.display === "standalone");
check("icon 192 trỏ /brand-icon/192 (ảnh đại diện)",
  !!(i192 && String(i192.src).indexOf("/brand-icon/192") === 0));
check("icon 512 trỏ /brand-icon/512 (ảnh đại diện)",
  !!(i512 && String(i512.src).indexOf("/brand-icon/512") === 0));

// ---- 2. Fallback file + route server ----
check("dashboard/icon-192.png tồn tại (fallback)", fs.existsSync(path.join(root, "dashboard", "icon-192.png")));
check("dashboard/icon-512.png tồn tại (fallback)", fs.existsSync(path.join(root, "dashboard", "icon-512.png")));
check("main.py có route /brand-icon/{size}", /@app\.get\(["']\/brand-icon\/\{size\}["']\)/.test(mainPy));
check("brand-icon 192/512 nằm trong AUTH public",
  mainPy.indexOf('"/brand-icon/192"') !== -1 && mainPy.indexOf('"/brand-icon/512"') !== -1);

// ---- 3. Nút "Mở như app" trên thanh trạng thái ----
check("index.html có nút installAppBtn", html.indexOf('id="installAppBtn"') !== -1);
check("nút ẩn mặc định (chỉ hiện khi trình duyệt báo cài được)",
  /id="installAppBtn"[^>]*hidden|hidden[^>]*id="installAppBtn"/.test(html));
check("CSS có .install-app-btn", css.indexOf(".install-app-btn") !== -1);

// ---- 4. app.js bắt đúng luồng cài của Chromium ----
check("nghe beforeinstallprompt", app.indexOf('addEventListener("beforeinstallprompt"') !== -1);
check("chặn mini-infobar tự bung (preventDefault)",
  /beforeinstallprompt[\s\S]{0,200}preventDefault\(\)/.test(app));
check("bấm nút mới bung hộp cài (prompt())", app.indexOf(".prompt()") !== -1);
check("đã chạy dạng app thì không bày nút (display-mode: standalone)",
  app.indexOf("display-mode: standalone") !== -1);
check("cài xong thì giấu nút (appinstalled)", app.indexOf('addEventListener("appinstalled"') !== -1);

// ---- cache-bust: đổi manifest phải đổi ?v= để trình duyệt đọc bản mới ----
check("manifest.json đã bump ?v= (>= 3)",
  Number((html.match(/manifest\.json\?v=(\d+)/) || [])[1] || 0) >= 3);

console.log();
if (fails.length) {
  console.log("THAT BAI " + fails.length + ": " + fails.join(", "));
  process.exit(1);
}
console.log("OK - test_cai_app_desktop: tat ca pass");
