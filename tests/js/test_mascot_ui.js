/* Linh vật góc màn (page-mascot port)

       node tests/js/test_mascot_ui.js
*/
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..", "..");
const fails = [];
function check(name, cond, extra) {
  console.log((cond ? "ok   " : "FAIL ") + name + (cond || extra === undefined ? "" : "  [" + extra + "]"));
  if (!cond) fails.push(name);
}

const html = fs.readFileSync(path.join(ROOT, "dashboard", "index.html"), "utf8");
const css = fs.readFileSync(path.join(ROOT, "dashboard", "style.css"), "utf8");
const js = fs.readFileSync(path.join(ROOT, "dashboard", "mascot.js"), "utf8");
const vi = fs.readFileSync(path.join(ROOT, "dashboard", "i18n", "vi.json"), "utf8");
const en = fs.readFileSync(path.join(ROOT, "dashboard", "i18n", "en.json"), "utf8");
const notice = fs.readFileSync(path.join(ROOT, "dashboard", "mascots", "NOTICE.md"), "utf8");

check("index có #mascotPickerHost", html.includes('id="mascotPickerHost"'));
check("index nạp mascot.js", /\/static\/mascot\.js\?v=\d+/.test(html));
check("CSS có .javis-mascot", css.includes(".javis-mascot {") || css.includes(".javis-mascot{"));
check("CSS ẩn trên cảm ứng", css.includes("(hover: none) and (pointer: coarse)"));
check("i18n vi qs.mascot", vi.includes('"qs.mascot"'));
check("i18n en qs.mascot", en.includes('"qs.mascot"'));
check("NOTICE ghi nguồn page-mascot", notice.includes("nilbuild/page-mascot"));

const catalog = [
  "fox", "cat", "otter", "panda", "bunny", "owl", "frog", "droid",
];
for (const id of catalog) {
  const d = path.join(ROOT, "dashboard", "mascots", id, "directions.webp");
  const r = path.join(ROOT, "dashboard", "mascots", id, "reactions.webp");
  check("sheet " + id + "/directions.webp", fs.existsSync(d) && fs.statSync(d).size > 1000);
  check("sheet " + id + "/reactions.webp", fs.existsSync(r) && fs.statSync(r).size > 1000);
}

check("mascot.js khoá localStorage", js.includes('javis.mascot.enabled') && js.includes('javis.mascot"'));
check("mascot.js có 8 hướng CLOCKWISE", js.includes("CLOCKWISE") && js.includes("down-right"));
check("mascot.js boop + dizzy", js.includes("DIZZY_AFTER") && js.includes("function boop"));
check("mascot.js expose JavisMascot", js.includes("window.JavisMascot"));

// Runtime: bật linh vật → hiện #javisMascot; tắt → ẩn.
const store = Object.create(null);
const localStorage = {
  getItem(k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
  setItem(k, v) { store[k] = String(v); },
  removeItem(k) { delete store[k]; },
};

const created = [];
const document = {
  body: {
    appendChild(el) { created.push(el); return el; },
  },
  readyState: "complete",
  addEventListener() {},
  createElement(tag) {
    const el = {
      tagName: String(tag).toUpperCase(),
      style: {},
      dataset: {},
      hidden: false,
      children: [],
      classList: { toggle() {}, add() {}, remove() {} },
      setAttribute(k, v) { this[k] = v; },
      getAttribute(k) { return this[k] == null ? null : String(this[k]); },
      querySelector(sel) {
        if (sel === ".javis-mascot-btn") return this._btn;
        if (sel === ".javis-mascot-squash") return this._squash;
        if (sel === ".javis-mascot-dir") return this._dir;
        if (sel === ".javis-mascot-react") return this._react;
        if (sel === "#qsMascot") return this._toggle;
        if (sel === ".javis-mascot-grid") return this._grid;
        return null;
      },
      querySelectorAll(sel) {
        if (sel === ".javis-mascot-pick") return this._picks || [];
        return [];
      },
      addEventListener() {},
      set innerHTML(v) {
        this._html = v;
        this._btn = {
          style: {},
          setAttribute() {},
          addEventListener() {},
        };
        this._squash = { animate() {} };
        this._dir = { style: {} };
        this._react = { style: {} };
      },
      get innerHTML() { return this._html || ""; },
    };
    return el;
  },
  getElementById(id) {
    if (id === "mascotPickerHost") {
      if (!document._host) {
        document._host = document.createElement("div");
        document._host.id = "mascotPickerHost";
        document._host.querySelector = function (sel) {
          if (sel === "#qsMascot") {
            return { checked: localStorage.getItem("javis.mascot.enabled") === "1", addEventListener() {} };
          }
          if (sel === ".javis-mascot-grid") return { hidden: false };
          return null;
        };
        document._host.querySelectorAll = function () { return []; };
      }
      return document._host;
    }
    return null;
  },
};

const windowObj = {
  localStorage,
  document,
  Image: function () { this.src = ""; },
  matchMedia() { return { matches: true }; },
  addEventListener() {},
  removeEventListener() {},
  setTimeout() { return 1; },
  clearTimeout() {},
  t(k) { return k; },
};
windowObj.window = windowObj;

vm.runInNewContext(js, {
  window: windowObj,
  document,
  localStorage,
  Image: windowObj.Image,
});

check("JavisMascot API có mặt", !!(windowObj.JavisMascot && windowObj.JavisMascot.setEnabled));
check("mặc định tắt", windowObj.JavisMascot.isOn() === false);

windowObj.JavisMascot.setEnabled(true);
const root = created.find((el) => el.id === "javisMascot");
check("bật → tạo #javisMascot", !!root);
check("bật → không hidden", root && root.hidden === false);
check("bật → localStorage=1", localStorage.getItem("javis.mascot.enabled") === "1");

windowObj.JavisMascot.setId("otter");
check("đổi linh vật otter", windowObj.JavisMascot.id() === "otter");
check("chọn character tự bật nếu đang tắt rồi vẫn on", windowObj.JavisMascot.isOn() === true);

windowObj.JavisMascot.setEnabled(false);
check("tắt → hidden", root.hidden === true);
check("tắt → localStorage=0", localStorage.getItem("javis.mascot.enabled") === "0");

if (fails.length) {
  console.log("\n" + fails.length + " failed");
  process.exit(1);
}
console.log("\nall ok");
