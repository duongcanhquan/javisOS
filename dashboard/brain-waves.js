// Tín hiệu thiên hà dưới nền khoang não (#brainWaves).
// Vòng radar + tia ping bắn từ nguồn thiên hà + ribbon sóng chạy rõ.
// Tôn trọng lite / pause / document.hidden / prefers-reduced-motion.
(function () {
  "use strict";

  var canvas = null;
  var ctx = null;
  var raf = 0;
  var running = false;
  var paused = false;
  var lite = false;
  var reduced = false;
  var lightTheme = false;
  var w = 0;
  var h = 0;
  var t0 = 0;
  var mode = "flow"; // calm | flow | deep
  var beams = [];
  var pings = [];
  var rings = [];

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

  function readMode() {
    try {
      var g = window.__javisGraph;
      if (g && g.getFlowMode) return g.getFlowMode() || "flow";
      var saved = localStorage.getItem("javis.brainFlowMode");
      if (saved === "calm" || saved === "flow" || saved === "deep") return saved;
    } catch (e) {}
    return "flow";
  }

  function resize() {
    if (!canvas) return;
    var parent = canvas.parentElement;
    var cw = (parent && parent.clientWidth) || window.innerWidth || 800;
    var ch = (parent && parent.clientHeight) || window.innerHeight || 600;
    if (cw === w && ch === h) return;
    w = cw;
    h = ch;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    seedScene(true);
  }

  function origin() {
    // Nguồn tín hiệu: góc trên, hơi lệch - kiểu thiên hà / vệ tinh
    return { x: w * 0.72, y: h * 0.14 };
  }

  function modeScale() {
    if (mode === "deep") return { amp: 1.35, speed: 1.55, beams: 9, pings: 14, rings: 5 };
    if (mode === "calm") return { amp: 0.7, speed: 0.55, beams: 4, pings: 4, rings: 3 };
    return { amp: 1, speed: 1, beams: 7, pings: 9, rings: 4 };
  }

  function seedScene(force) {
    if (!w || !h) return;
    var ms = modeScale();
    if (force || beams.length !== ms.beams) {
      beams = [];
      for (var i = 0; i < ms.beams; i++) {
        // Quạt tia từ nguồn xuống/vào giữa khoang não
        var a = Math.PI * 0.55 + (i / Math.max(1, ms.beams - 1)) * Math.PI * 0.85;
        beams.push({
          ang: a,
          len: 0.55 + (i % 3) * 0.12,
          cool: i % 2 === 0,
          dash: 8 + (i % 4) * 3,
          phase: Math.random() * Math.PI * 2,
        });
      }
    }
    if (force || pings.length !== ms.pings) {
      pings = [];
      for (var j = 0; j < ms.pings; j++) {
        pings.push({
          bi: j % Math.max(1, ms.beams),
          u: Math.random(),
          spd: 0.0018 + Math.random() * 0.0032,
          r: 2.2 + Math.random() * 2.4,
          cool: Math.random() > 0.4,
          trail: 0.08 + Math.random() * 0.1,
        });
      }
    }
    if (force || rings.length !== ms.rings) {
      rings = [];
      for (var k = 0; k < ms.rings; k++) {
        rings.push({
          u: k / ms.rings,
          spd: 0.00022 + k * 0.00004,
          cool: k % 2 === 0,
        });
      }
    }
  }

  function col(cool, a) {
    if (cool) {
      return lightTheme
        ? "rgba(8, 145, 178," + a + ")"
        : "rgba(120, 240, 255," + a + ")";
    }
    return lightTheme
      ? "rgba(147, 51, 234," + a + ")"
      : "rgba(255, 150, 220," + a + ")";
  }

  function drawOriginGlow(ox, oy, alphaMul, t) {
    var pulse = 0.65 + 0.35 * Math.sin(t * 0.004);
    var r = Math.min(w, h) * 0.09 * pulse;
    var g = ctx.createRadialGradient(ox, oy, 0, ox, oy, r);
    g.addColorStop(0, col(true, 0.55 * alphaMul));
    g.addColorStop(0.35, col(false, 0.22 * alphaMul));
    g.addColorStop(1, col(true, 0));
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(ox, oy, r, 0, Math.PI * 2);
    ctx.fill();

    // Nhân sáng trung tâm
    ctx.fillStyle = col(true, 0.9 * alphaMul);
    ctx.beginPath();
    ctx.arc(ox, oy, 2.5 + pulse, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawRings(ox, oy, alphaMul, t, animated) {
    var maxR = Math.sqrt(w * w + h * h) * 0.95;
    for (var i = 0; i < rings.length; i++) {
      var rg = rings[i];
      var u = animated ? (rg.u + t * rg.spd * modeScale().speed) % 1 : rg.u;
      var rad = 40 + u * maxR;
      var fade = 1 - u;
      ctx.beginPath();
      ctx.arc(ox, oy, rad, 0, Math.PI * 2);
      ctx.strokeStyle = col(rg.cool, (0.18 + 0.28 * fade) * alphaMul);
      ctx.lineWidth = 1.2 + fade * 1.6;
      ctx.setLineDash(rg.cool ? [6, 10] : [2, 8]);
      ctx.lineDashOffset = animated ? -t * 0.06 : 0;
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  function drawBeams(ox, oy, alphaMul, t, animated) {
    var reach = Math.sqrt(w * w + h * h);
    for (var i = 0; i < beams.length; i++) {
      var b = beams[i];
      var len = reach * b.len;
      var x2 = ox + Math.cos(b.ang) * len;
      var y2 = oy + Math.sin(b.ang) * len;
      var shimmer = animated ? 0.55 + 0.45 * Math.sin(t * 0.003 + b.phase) : 0.7;

      ctx.beginPath();
      ctx.moveTo(ox, oy);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = col(b.cool, 0.16 * shimmer * alphaMul);
      ctx.lineWidth = 1.1;
      ctx.setLineDash([b.dash, b.dash * 1.4]);
      ctx.lineDashOffset = animated ? -t * (0.08 + i * 0.01) * modeScale().speed : 0;
      ctx.stroke();

      // Glow rộng
      ctx.strokeStyle = col(b.cool, 0.07 * shimmer * alphaMul);
      ctx.lineWidth = 4.5;
      ctx.setLineDash([]);
      ctx.stroke();
    }
  }

  function drawPings(ox, oy, alphaMul, t, animated) {
    if (!beams.length) return;
    var reach = Math.sqrt(w * w + h * h);
    var spdMul = modeScale().speed;
    for (var i = 0; i < pings.length; i++) {
      var p = pings[i];
      var b = beams[p.bi % beams.length];
      if (animated) {
        p.u += p.spd * spdMul;
        if (p.u > 1.08) {
          p.u = -0.05;
          p.bi = (Math.random() * beams.length) | 0;
          b = beams[p.bi];
          p.spd = 0.0018 + Math.random() * 0.0035;
        }
      }
      var len = reach * b.len;
      var x = ox + Math.cos(b.ang) * len * Math.max(0, Math.min(1, p.u));
      var y = oy + Math.sin(b.ang) * len * Math.max(0, Math.min(1, p.u));

      // Vệt đuôi (chirp)
      var tx = ox + Math.cos(b.ang) * len * Math.max(0, p.u - p.trail);
      var ty = oy + Math.sin(b.ang) * len * Math.max(0, p.u - p.trail);
      var grad = ctx.createLinearGradient(tx, ty, x, y);
      grad.addColorStop(0, col(p.cool, 0));
      grad.addColorStop(1, col(p.cool, 0.75 * alphaMul));
      ctx.strokeStyle = grad;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(tx, ty);
      ctx.lineTo(x, y);
      ctx.stroke();

      var g = ctx.createRadialGradient(x, y, 0, x, y, p.r * 5);
      g.addColorStop(0, col(p.cool, 0.95 * alphaMul));
      g.addColorStop(0.4, col(p.cool, 0.35 * alphaMul));
      g.addColorStop(1, col(p.cool, 0));
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(x, y, p.r * 5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function strokeRibbon(spec, t, alphaMul, animated) {
    var midY = h * spec.y;
    var amp = h * spec.amp * modeScale().amp;
    var phase = animated ? t * spec.speed : 0;
    ctx.beginPath();
    for (var x = 0; x <= w; x += 4) {
      var nx = x / w;
      var y =
        midY +
        Math.sin(nx * Math.PI * 2 * spec.freq + phase) * amp +
        Math.sin(nx * Math.PI * 2 * (spec.freq * 0.41) - phase * 0.7) * amp * 0.4;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = col(spec.cool, 0.32 * alphaMul);
    ctx.lineWidth = spec.w;
    ctx.lineJoin = "round";
    ctx.stroke();
    ctx.strokeStyle = col(spec.cool, 0.12 * alphaMul);
    ctx.lineWidth = spec.w * 3.5;
    ctx.stroke();
  }

  function ribbons() {
    var list = [
      { amp: 0.07, freq: 1.35, speed: 0.0022, y: 0.42, w: 1.4, cool: true },
      { amp: 0.055, freq: 2.1, speed: 0.003, y: 0.58, w: 1.15, cool: true },
      { amp: 0.045, freq: 2.9, speed: 0.0038, y: 0.72, w: 1, cool: false },
    ];
    if (mode === "deep") {
      list.push({ amp: 0.04, freq: 4.1, speed: 0.005, y: 0.84, w: 0.9, cool: false });
    } else if (mode === "calm") {
      list = [list[0], list[1]];
      list[0].speed *= 0.55;
      list[1].speed *= 0.5;
    }
    return list;
  }

  function paint(animated) {
    if (!ctx || !w) return;
    ctx.clearRect(0, 0, w, h);
    var t = animated ? (typeof performance !== "undefined" ? performance.now() : Date.now()) - t0 : 0;
    var alphaMul = mode === "calm" ? 0.7 : mode === "deep" ? 1.25 : 1;
    if (lightTheme) alphaMul *= 0.85;
    seedScene(false);

    var o = origin();
    drawOriginGlow(o.x, o.y, alphaMul, t);
    drawRings(o.x, o.y, alphaMul, t, animated);
    drawBeams(o.x, o.y, alphaMul, t, animated);
    drawPings(o.x, o.y, alphaMul, t, animated);

    var specs = ribbons();
    for (var i = 0; i < specs.length; i++) strokeRibbon(specs[i], t, alphaMul * 0.85, animated);
  }

  function frame() {
    raf = 0;
    if (!running || paused || lite || document.hidden || reduced) return;
    paint(true);
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
    mode = readMode();
    seedScene(true);
    if (reduced || lite || paused || document.hidden) {
      stopRaf();
      paint(false);
      return;
    }
    schedule();
  }

  function start() {
    canvas = document.getElementById("brainWaves");
    if (!canvas) return;
    ctx = canvas.getContext("2d");
    if (!ctx) return;
    running = true;
    t0 = typeof performance !== "undefined" ? performance.now() : Date.now();
    mode = readMode();
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
      applyGates();
    },
    setMode: function (m) {
      if (m === "calm" || m === "flow" || m === "deep") mode = m;
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
  window.JavisBrainWaves = api;

  function boot() {
    start();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  window.addEventListener("resize", function () {
    if (window.JavisBrainWaves) window.JavisBrainWaves.resize();
  });
  document.addEventListener("visibilitychange", applyGates);
  window.addEventListener("javis-theme-change", function () {
    if (window.JavisBrainWaves) window.JavisBrainWaves.refreshTheme();
  });
  window.addEventListener("javis-flow-mode", function (e) {
    if (e && e.detail && e.detail.mode) api.setMode(e.detail.mode);
  });
  try {
    if (window.matchMedia) {
      window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", applyGates);
    }
  } catch (e) {}
})();
