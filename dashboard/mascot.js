/* VMOS dashboard page mascot - cursor-follow sprite (vanilla port of
   nilbuild/page-mascot MIT © Kamran Ahmed). Preference: localStorage only. */
(function () {
  "use strict";

  var KEY_ID = "javis.mascot";
  var KEY_ON = "javis.mascot.enabled";
  var SIZE = 112;
  var BASE = "/static/mascots/";

  var CATALOG = [
    { id: "fox", label: "Cáo", label_en: "Fox" },
    { id: "cat", label: "Mèo", label_en: "Cat" },
    { id: "otter", label: "Rái cá", label_en: "Otter" },
    { id: "panda", label: "Gấu trúc", label_en: "Panda" },
    { id: "bunny", label: "Thỏ", label_en: "Bunny" },
    { id: "owl", label: "Cú", label_en: "Owl" },
    { id: "frog", label: "Ếch", label_en: "Frog" },
    { id: "droid", label: "Robot", label_en: "Droid" },
  ];

  var DIRECTIONS = [
    "up-left", "up", "up-right",
    "left", "center", "right",
    "down-left", "down", "down-right",
  ];
  var REACTIONS = [
    "blink", "heart", "sparkle",
    "surprised", "wink", "bashful",
    "sleepy", "dizzy", "delighted",
  ];
  var CLOCKWISE = [
    "right", "down-right", "down", "down-left",
    "left", "up-left", "up", "up-right",
  ];
  var SECTOR = (Math.PI * 2) / CLOCKWISE.length;
  var HYSTERESIS = 0.12;
  var DEAD_ZONE = 70;
  var PAYOFFS = ["heart", "sparkle", "delighted"];
  var BOOP_PAYOFF = 120;
  var BOOP_END = 560;
  var SQUASH_MS = 420;
  var DIZZY_AFTER = 4;
  var DIZZY_WINDOW = 1600;
  var DIZZY_END = 1100;
  var SQUASH = [
    { transform: "scale(1, 1)", easing: "ease-in" },
    { transform: "scale(1.10, 0.86)", offset: 0.18, easing: "ease-out" },
    { transform: "scale(0.95, 1.08)", offset: 0.45, easing: "ease-in-out" },
    { transform: "scale(1.03, 0.97)", offset: 0.72, easing: "ease-in-out" },
    { transform: "scale(1, 1)" },
  ];

  function lsGet(k) {
    try { return localStorage.getItem(k); } catch (e) { return null; }
  }
  function lsSet(k, v) {
    try { localStorage.setItem(k, v); } catch (e) {}
  }
  function t(key, fallback) {
    try {
      if (window.t) {
        var v = window.t(key);
        if (v && v !== key) return v;
      }
    } catch (e) {}
    return fallback;
  }
  function isEn() {
    try {
      return !!(window.JavisI18n && JavisI18n.lang && JavisI18n.lang() === "en");
    } catch (e) { return false; }
  }
  function charLabel(c) {
    return isEn() ? (c.label_en || c.label) : c.label;
  }
  function wrap(angle) {
    return Math.atan2(Math.sin(angle), Math.cos(angle));
  }
  function cellPos(index) {
    return ((index % 3) * 50) + "% " + (Math.floor(index / 3) * 50) + "%";
  }
  function validId(id) {
    return CATALOG.some(function (c) { return c.id === id; });
  }
  function readId() {
    var id = lsGet(KEY_ID) || "fox";
    return validId(id) ? id : "fox";
  }
  function readOn() {
    return lsGet(KEY_ON) === "1";
  }
  function finePointer() {
    try {
      return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    } catch (e) { return true; }
  }
  function reduceMotion() {
    try {
      return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    } catch (e) { return false; }
  }

  var rootEl = null;
  var btnEl = null;
  var squashEl = null;
  var dirLayer = null;
  var reactLayer = null;
  var direction = "center";
  var reaction = null;
  var sector = -1;
  var pointer = null;
  var timers = [];
  var boops = { count: 0, at: 0 };
  var trackingBound = false;

  function clearTimers() {
    timers.forEach(function (id) { window.clearTimeout(id); });
    timers = [];
  }
  function later(ms, next) {
    timers.push(window.setTimeout(function () {
      reaction = next;
      paintLayers();
    }, ms));
  }
  function paintLayers() {
    if (!dirLayer || !reactLayer) return;
    dirLayer.style.backgroundPosition = cellPos(DIRECTIONS.indexOf(direction));
    dirLayer.style.opacity = reaction ? "0" : "1";
    reactLayer.style.backgroundPosition = cellPos(
      REACTIONS.indexOf(reaction || "blink")
    );
    reactLayer.style.opacity = reaction ? "1" : "0";
  }
  function setSheets(id) {
    if (!dirLayer || !reactLayer) return;
    var dirUrl = BASE + id + "/directions.webp";
    var reactUrl = BASE + id + "/reactions.webp";
    dirLayer.style.backgroundImage = "url(" + dirUrl + ")";
    reactLayer.style.backgroundImage = "url(" + reactUrl + ")";
    // Warm reaction sheet so first boop is instant.
    try {
      var img = new Image();
      img.src = reactUrl;
    } catch (e) {}
  }
  function aim() {
    if (!btnEl || !pointer) return;
    var box = btnEl.getBoundingClientRect();
    var dx = pointer.x - (box.left + box.width / 2);
    var dy = pointer.y - (box.top + box.height / 2);
    if (Math.hypot(dx, dy) < DEAD_ZONE) {
      sector = -1;
      direction = "center";
      paintLayers();
      return;
    }
    var angle = Math.atan2(dy, dx);
    if (
      sector !== -1 &&
      Math.abs(wrap(angle - sector * SECTOR)) < SECTOR / 2 + HYSTERESIS
    ) {
      return;
    }
    sector = (Math.round(angle / SECTOR) + CLOCKWISE.length) % CLOCKWISE.length;
    direction = CLOCKWISE[sector];
    paintLayers();
  }
  function onPointerMove(e) {
    pointer = { x: e.clientX, y: e.clientY };
    if (!reaction) aim();
  }
  function bindTracking(on) {
    if (on && !trackingBound && finePointer()) {
      window.addEventListener("pointermove", onPointerMove, { passive: true });
      window.addEventListener("scroll", aim, { passive: true });
      trackingBound = true;
    } else if (!on && trackingBound) {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("scroll", aim);
      trackingBound = false;
      pointer = null;
      sector = -1;
      direction = "center";
      paintLayers();
    }
  }
  function boop() {
    clearTimers();
    var now = Date.now();
    boops.count = now - boops.at < DIZZY_WINDOW ? boops.count + 1 : 1;
    boops.at = now;
    if (boops.count >= DIZZY_AFTER) {
      boops.count = 0;
      reaction = "dizzy";
      paintLayers();
      later(DIZZY_END, null);
    } else {
      reaction = "blink";
      paintLayers();
      later(BOOP_PAYOFF, PAYOFFS[(boops.count - 1) % PAYOFFS.length]);
      later(BOOP_END, null);
    }
    if (!reduceMotion() && squashEl && squashEl.animate) {
      try {
        squashEl.animate(SQUASH, { duration: SQUASH_MS, easing: "linear" });
      } catch (e) {}
    }
  }
  function ensureRoot() {
    if (rootEl) return rootEl;
    rootEl = document.createElement("div");
    rootEl.id = "javisMascot";
    rootEl.className = "javis-mascot";
    rootEl.hidden = true;
    rootEl.innerHTML =
      '<button type="button" class="javis-mascot-btn" aria-label="">' +
      '<span class="javis-mascot-squash">' +
      '<span class="javis-mascot-layer javis-mascot-dir" aria-hidden="true"></span>' +
      '<span class="javis-mascot-layer javis-mascot-react" aria-hidden="true"></span>' +
      "</span></button>";
    document.body.appendChild(rootEl);
    btnEl = rootEl.querySelector(".javis-mascot-btn");
    squashEl = rootEl.querySelector(".javis-mascot-squash");
    dirLayer = rootEl.querySelector(".javis-mascot-dir");
    reactLayer = rootEl.querySelector(".javis-mascot-react");
    btnEl.style.width = SIZE + "px";
    btnEl.style.height = SIZE + "px";
    btnEl.addEventListener("click", boop);
    return rootEl;
  }
  function syncAria(id) {
    if (!btnEl) return;
    var c = CATALOG.find(function (x) { return x.id === id; }) || CATALOG[0];
    var name = charLabel(c);
    var label = t("qs.mascot_boop", "Boop ") + name;
    btnEl.setAttribute("aria-label", label);
    btnEl.title = label;
  }
  function apply() {
    ensureRoot();
    var on = readOn();
    var id = readId();
    if (!on) {
      rootEl.hidden = true;
      bindTracking(false);
      clearTimers();
      reaction = null;
      paintLayers();
      syncPicker();
      return;
    }
    setSheets(id);
    syncAria(id);
    direction = "center";
    reaction = null;
    paintLayers();
    rootEl.hidden = false;
    bindTracking(true);
    syncPicker();
  }
  function setEnabled(on) {
    lsSet(KEY_ON, on ? "1" : "0");
    apply();
  }
  function setId(id) {
    if (!validId(id)) return;
    lsSet(KEY_ID, id);
    if (!readOn()) lsSet(KEY_ON, "1");
    apply();
  }

  function syncPicker() {
    var host = document.getElementById("mascotPickerHost");
    if (!host) return;
    var on = readOn();
    var cur = readId();
    var toggle = host.querySelector("#qsMascot");
    if (toggle) toggle.checked = on;
    host.querySelectorAll(".javis-mascot-pick").forEach(function (btn) {
      var id = btn.getAttribute("data-id");
      var active = on && id === cur;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    var grid = host.querySelector(".javis-mascot-grid");
    if (grid) grid.hidden = !on;
  }

  function renderPicker() {
    var host = document.getElementById("mascotPickerHost");
    if (!host || host.dataset.ready === "1") {
      syncPicker();
      return;
    }
    host.dataset.ready = "1";
    var cards = CATALOG.map(function (c) {
      var url = BASE + c.id + "/directions.webp";
      return (
        '<button type="button" class="javis-mascot-pick" data-id="' + c.id + '"' +
        ' title="' + charLabel(c) + '" aria-label="' + charLabel(c) + '" aria-pressed="false">' +
        '<span class="javis-mascot-thumb" style="background-image:url(' + url + ')"></span>' +
        '<span class="javis-mascot-name">' + charLabel(c) + "</span>" +
        "</button>"
      );
    }).join("");
    host.innerHTML =
      '<label class="qs-row">' +
      "<span><i data-ic=\"sparkles\"></i> <span data-i18n=\"qs.mascot\">" +
      t("qs.mascot", "Linh vật góc màn") +
      "</span></span>" +
      '<span class="toggle"><input type="checkbox" id="qsMascot"><span></span></span>' +
      "</label>" +
      '<div class="qs-hint" data-i18n="qs.mascot_hint">' +
      t(
        "qs.mascot_hint",
        "Nhìn theo chuột. Bấm vào linh vật để boop. Ẩn trên điện thoại cảm ứng."
      ) +
      "</div>" +
      '<div class="javis-mascot-grid" hidden>' + cards + "</div>";

    var toggle = host.querySelector("#qsMascot");
    if (toggle) {
      toggle.addEventListener("change", function () {
        setEnabled(toggle.checked);
      });
    }
    host.querySelectorAll(".javis-mascot-pick").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setId(btn.getAttribute("data-id"));
      });
    });
    try {
      if (window.JavisIcons && JavisIcons.refresh) JavisIcons.refresh(host);
    } catch (e) {}
    try {
      if (window.JavisI18n && JavisI18n.applyDom) JavisI18n.applyDom(host);
    } catch (e) {}
    syncPicker();
  }

  function init() {
    ensureRoot();
    renderPicker();
    apply();
    window.addEventListener("javis:i18n", function () {
      var host = document.getElementById("mascotPickerHost");
      if (host) {
        host.dataset.ready = "";
        host.innerHTML = "";
      }
      renderPicker();
      syncAria(readId());
    });
  }

  window.JavisMascot = {
    catalog: CATALOG,
    isOn: readOn,
    id: readId,
    setEnabled: setEnabled,
    setId: setId,
    refresh: apply,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
