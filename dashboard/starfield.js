// Nền ngân hà cho khoang não (#starfield): sao twinkle + drift xoắn chậm.
// Tôn trọng lite / pause / document.hidden / prefers-reduced-motion.
(function () {
  "use strict";

  var canvas = null;
  var ctx = null;
  var stars = [];
  var raf = 0;
  var running = false;
  var paused = false;
  var lite = false;
  var reduced = false;
  var lightTheme = false;
  var w = 0;
  var h = 0;
  var t0 = 0;
  var STAR_N = 100;

  function prefersReduced() {
    try {
      return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    } catch (e) {
      return false;
    }
  }

  function themeIsLight() {
    try {
      return document.documentElement.getAttribute("data-theme") === "light";
    } catch (e) {
      return false;
    }
  }

  function resize() {
    if (!canvas) return;
    var parent = canvas.parentElement;
    var cw = (parent && parent.clientWidth) || window.innerWidth || 800;
    var ch = (parent && parent.clientHeight) || window.innerHeight || 600;
    if (cw < 2 || ch < 2) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    if (w === cw && h === ch && canvas.width === Math.floor(cw * dpr)) return;
    w = cw;
    h = ch;
    canvas.width = Math.floor(cw * dpr);
    canvas.height = Math.floor(ch * dpr);
    canvas.style.width = cw + "px";
    canvas.style.height = ch + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    seedStars();
  }

  function seedStars() {
    stars = [];
    var n = lite || reduced ? 40 : STAR_N;
    var cx = w * 0.5;
    var cy = h * 0.48;
    for (var i = 0; i < n; i++) {
      var ang = Math.random() * Math.PI * 2;
      var rad = Math.pow(Math.random(), 0.55) * Math.min(w, h) * 0.55;
      stars.push({
        x: cx + Math.cos(ang) * rad,
        y: cy + Math.sin(ang) * rad * 0.72,
        r: 0.6 + Math.random() * 1.6,
        a: 0.25 + Math.random() * 0.7,
        ph: Math.random() * Math.PI * 2,
        spd: 0.00008 + Math.random() * 0.00018,
        orbit: rad,
        ang: ang,
        cool: Math.random() > 0.55,
      });
    }
  }

  function drawStatic() {
    if (!ctx || !w) return;
    ctx.clearRect(0, 0, w, h);
    var fill = lightTheme ? "rgba(30, 60, 90," : "rgba(210, 235, 255,";
    for (var i = 0; i < stars.length; i++) {
      var s = stars[i];
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = fill + s.a + ")";
      ctx.fill();
    }
  }

  function frame(now) {
    raf = 0;
    if (!running || paused || lite || document.hidden) return;
    if (!ctx || !w) {
      schedule();
      return;
    }
    if (!t0) t0 = now;
    var t = now - t0;
    var cx = w * 0.5;
    var cy = h * 0.48;
    ctx.clearRect(0, 0, w, h);

    for (var i = 0; i < stars.length; i++) {
      var s = stars[i];
      if (!reduced) {
        s.ang += s.spd;
        s.x = cx + Math.cos(s.ang) * s.orbit;
        s.y = cy + Math.sin(s.ang) * s.orbit * 0.72;
      }
      var tw = 0.55 + 0.45 * Math.sin(t / 900 + s.ph);
      var alpha = s.a * tw;
      var col = s.cool
        ? lightTheme
          ? "rgba(20, 90, 120,"
          : "rgba(170, 230, 255,"
        : lightTheme
          ? "rgba(40, 70, 110,"
          : "rgba(230, 245, 255,";
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r * (0.85 + 0.2 * tw), 0, Math.PI * 2);
      ctx.fillStyle = col + alpha + ")";
      ctx.fill();
    }
    schedule();
  }

  function schedule() {
    if (raf || !running || paused || lite || document.hidden || reduced) return;
    raf = requestAnimationFrame(frame);
  }

  function stopRaf() {
    if (raf) {
      cancelAnimationFrame(raf);
      raf = 0;
    }
  }

  function applyGates() {
    reduced = prefersReduced();
    lightTheme = themeIsLight();
    var host = document.querySelector(".hud-center");
    if (host) {
      host.classList.toggle("brain-galaxy-static", reduced || lite || paused);
      host.classList.toggle("brain-galaxy-lite", lite);
    }
    if (reduced || lite || paused || document.hidden) {
      stopRaf();
      drawStatic();
      return;
    }
    schedule();
  }

  function start() {
    canvas = document.getElementById("starfield");
    if (!canvas) return;
    ctx = canvas.getContext("2d");
    if (!ctx) return;
    running = true;
    resize();
    applyGates();
  }

  var api = {
    pause: function () {
      paused = true;
      applyGates();
    },
    wake: function () {
      paused = false;
      applyGates();
    },
    setLite: function (on) {
      lite = !!on;
      if (lite) seedStars();
      else if (canvas) seedStars();
      applyGates();
    },
    resize: function () {
      resize();
      applyGates();
    },
    refreshTheme: function () {
      lightTheme = themeIsLight();
      applyGates();
    },
  };
  window.JavisStarfield = api;

  function boot() {
    start();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  window.addEventListener("resize", function () {
    if (window.JavisStarfield) window.JavisStarfield.resize();
  });
  document.addEventListener("visibilitychange", function () {
    applyGates();
  });
  window.addEventListener("javis-theme-change", function () {
    if (window.JavisStarfield) window.JavisStarfield.refreshTheme();
  });
  try {
    if (window.matchMedia) {
      window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", applyGates);
    }
  } catch (e) {}
})();
