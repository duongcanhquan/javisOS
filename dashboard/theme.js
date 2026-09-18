// ============================================
// JAVIS OS - Bộ đổi tông: TỐI · NEON · SÁNG
// ============================================
// Tông lưu ở localStorage "javis.theme": "dark" | "neon" | "light".
// Tông sáng đặt data-theme="light" trên <html>; neon đặt data-theme="neon";
// tông tối gỡ hẳn thuộc tính (mặc định :root luôn là tối).
//
// Giá trị cũ "dim" (tông tối-nhạt, đã gỡ ở 0.9.250) quy về "dark".
// "cyber" / "cyberpunk" (bí danh lúc soạn) quy về "neon".
//
// apply() nhận tên tông HOẶC boolean cũ (true = sáng, false = tối) để
// chỗ gọi cũ không gãy. Canvas nghe "javis-theme-change" với
// detail = { theme, light, neon }.
(function () {
  var KEY = "javis.theme";
  var NAMES = ["dark", "neon", "light"];
  var root = document.documentElement;

  function read() {
    try { return localStorage.getItem(KEY) || ""; } catch (e) { return ""; }
  }
  function write(v) {
    try { localStorage.setItem(KEY, v); } catch (e) {}
  }

  function normalize(v) {
    if (v === true || v === "light") return "light";
    if (v === "neon" || v === "cyber" || v === "cyberpunk") return "neon";
    return "dark";
  }

  function current() {
    var a = root.getAttribute("data-theme");
    if (a === "light" || a === "neon") return a;
    return "dark";
  }

  function isLight() { return current() === "light"; }
  function isNeon() { return current() === "neon"; }

  function labelOf(name) {
    var keys = {
      dark: "top.theme_now_dark",
      neon: "top.theme_now_neon",
      light: "top.theme_now_light",
    };
    var fallback = {
      dark: "Đang dùng tông tối - bấm để chọn tông",
      neon: "Đang dùng tông Neon - bấm để chọn tông",
      light: "Đang dùng tông sáng - bấm để chọn tông",
    };
    var key = keys[name] || keys.dark;
    var txt = window.t ? window.t(key) : key;
    if (txt === key) txt = fallback[name] || fallback.dark;
    return txt;
  }

  function optLabel(name) {
    var keys = {
      dark: "top.theme_opt_dark",
      neon: "top.theme_opt_neon",
      light: "top.theme_opt_light",
    };
    var fallback = { dark: "Tối", neon: "Neon", light: "Sáng" };
    var key = keys[name];
    var txt = window.t ? window.t(key) : key;
    if (txt === key) txt = fallback[name];
    return txt;
  }

  function syncMeta(name) {
    var m = document.querySelector('meta[name="theme-color"]');
    if (!m) {
      m = document.createElement("meta");
      m.setAttribute("name", "theme-color");
      document.head.appendChild(m);
    }
    var color = name === "light" ? "#ffffff" : name === "neon" ? "#071226" : "#0c101c";
    m.setAttribute("content", color);
  }

  function markSelected(name) {
    document.querySelectorAll("[data-theme-set]").forEach(function (el) {
      var on = el.getAttribute("data-theme-set") === name;
      el.classList.toggle("on", on);
      if (el.hasAttribute("aria-checked")) {
        el.setAttribute("aria-checked", on ? "true" : "false");
      }
    });
  }

  function syncButton(name) {
    var b = document.getElementById("themeToggle");
    if (!b) return;
    b.setAttribute("aria-pressed", name === "light" ? "true" : "false");
    var txt = labelOf(name);
    b.title = txt;
    b.setAttribute("aria-label", txt);
    markSelected(name);
    var pop = document.getElementById("themePop");
    if (pop) {
      pop.querySelectorAll("[data-theme-set]").forEach(function (btn) {
        var n = btn.getAttribute("data-theme-set");
        var span = btn.querySelector("[data-i18n], span:last-child");
        if (n && span) span.textContent = optLabel(n);
      });
    }
  }

  function setPopOpen(open) {
    var b = document.getElementById("themeToggle");
    var pop = document.getElementById("themePop");
    if (!pop) return;
    if (open) pop.removeAttribute("hidden");
    else pop.setAttribute("hidden", "");
    if (b) b.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function popIsOpen() {
    var pop = document.getElementById("themePop");
    return !!(pop && !pop.hasAttribute("hidden"));
  }

  function emit(name) {
    var detail = { theme: name, light: name === "light", neon: name === "neon" };
    try {
      window.dispatchEvent(new CustomEvent("javis-theme-change", { detail: detail }));
    } catch (e) {
      try {
        var ev = document.createEvent("Event");
        ev.initEvent("javis-theme-change", false, false);
        window.dispatchEvent(ev);
      } catch (e2) {}
    }
  }

  function apply(nameOrLight, persist) {
    var name = normalize(nameOrLight);
    if (name === "dark") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", name);
    if (persist) write(name);
    syncMeta(name);
    syncButton(name);
    emit(name);
  }

  function set(name, persist) {
    apply(name, persist !== false);
    setPopOpen(false);
  }

  function toggle() {
    var order = { dark: "neon", neon: "light", light: "dark" };
    apply(order[current()] || "neon", true);
  }

  window.addEventListener("javis:i18n", function () {
    syncButton(current());
  });

  window.javisTheme = {
    names: NAMES,
    current: current,
    isLight: isLight,
    isNeon: isNeon,
    apply: apply,
    set: set,
    toggle: toggle,
    on: function (fn) {
      if (typeof fn !== "function") return;
      window.addEventListener("javis-theme-change", function (e) {
        var light = !!(e && e.detail ? e.detail.light : isLight());
        fn(light, e && e.detail ? e.detail.theme : current());
      });
      try { fn(isLight(), current()); } catch (err) {}
    },
  };

  function init() {
    var saved = read();
    if (saved === "dim") { write("dark"); saved = "dark"; }
    apply(normalize(saved), false);

    var wrap = document.getElementById("themeWrap");
    var b = document.getElementById("themeToggle");
    var pop = document.getElementById("themePop");
    if (b) {
      b.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        if (pop) setPopOpen(!popIsOpen());
        else toggle();
      });
    }
    if (pop) {
      pop.addEventListener("click", function (ev) {
        var btn = ev.target.closest("[data-theme-set]");
        if (!btn) return;
        ev.preventDefault();
        ev.stopPropagation();
        set(normalize(btn.getAttribute("data-theme-set")), true);
      });
    }
    document.addEventListener("click", function (ev) {
      if (!popIsOpen()) return;
      if (wrap && wrap.contains(ev.target)) return;
      setPopOpen(false);
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") setPopOpen(false);
    });

    window.addEventListener("storage", function (e) {
      if (e.key === KEY) apply(normalize(e.newValue), false);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
