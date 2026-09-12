// Sóng não / sóng thông tin dưới nền khoang não (#brainWaves).
// Nằm giữa tinh vân và starfield: EEG ribbon mềm + gói tin chạy dọc sóng.
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
  var packets = [];

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
  }

  function waveSpecs() {
    // EEG-ish: delta / theta / alpha / beta (+ gamma khi deep)
    var base = [
      { amp: 0.055, freq: 1.1, speed: 0.00035, y: 0.38, w: 1.1, cool: true },
      { amp: 0.04, freq: 1.7, speed: 0.00055, y: 0.52, w: 0.95, cool: true },
      { amp: 0.032, freq: 2.4, speed: 0.0008, y: 0.66, w: 0.8, cool: false },
    ];
    if (mode === "deep") {
      base.push({ amp: 0.028, freq: 3.6, speed: 0.0012, y: 0.78, w: 0.7, cool: false });
      base[0].amp *= 1.35;
      base[1].amp *= 1.25;
    } else if (mode === "calm") {
      base = [base[0], base[1]];
      base[0].amp *= 0.55;
      base[0].speed *= 0.45;
      base[1].amp *= 0.45;
      base[1].speed *= 0.4;
    } else {
      base[0].amp *= 1.05;
    }
    return base;
  }

  function strokeWave(spec, t, alphaMul) {
    var midY = h * spec.y;
    var amp = h * spec.amp;
    var col = spec.cool
      ? lightTheme
        ? "rgba(14, 116, 144,"
        : "rgba(100, 230, 255,"
      : lightTheme
        ? "rgba(126, 58, 140,"
        : "rgba(255, 140, 210,";

    ctx.beginPath();
    for (var x = 0; x <= w; x += 3) {
      var nx = x / w;
      var y =
        midY +
        Math.sin(nx * Math.PI * 2 * spec.freq + t * spec.speed) * amp +
        Math.sin(nx * Math.PI * 2 * (spec.freq * 0.37) - t * spec.speed * 0.6) * amp * 0.35;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = col + (0.22 * alphaMul) + ")";
    ctx.lineWidth = spec.w;
    ctx.lineJoin = "round";
    ctx.stroke();

    // Soft glow pass
    ctx.strokeStyle = col + (0.1 * alphaMul) + ")";
    ctx.lineWidth = spec.w * 3.2;
    ctx.stroke();
  }

  function ensurePackets(n) {
    while (packets.length < n) {
      packets.push({
        wi: (Math.random() * 3) | 0,
        u: Math.random(),
        spd: 0.00012 + Math.random() * 0.00025,
        r: 1.4 + Math.random() * 1.8,
        cool: Math.random() > 0.45,
      });
    }
    if (packets.length > n) packets.length = n;
  }

  function drawPackets(specs, t, alphaMul) {
    if (!specs.length) return;
    for (var i = 0; i < packets.length; i++) {
      var p = packets[i];
      var spec = specs[p.wi % specs.length];
      p.u += p.spd * (mode === "deep" ? 1.6 : mode === "calm" ? 0.35 : 1);
      if (p.u > 1.05) {
        p.u = -0.05;
        p.wi = (Math.random() * specs.length) | 0;
        spec = specs[p.wi];
      }
      var x = p.u * w;
      var nx = Math.max(0, Math.min(1, p.u));
      var midY = h * spec.y;
      var amp = h * spec.amp;
      var y =
        midY +
        Math.sin(nx * Math.PI * 2 * spec.freq + t * spec.speed) * amp +
        Math.sin(nx * Math.PI * 2 * (spec.freq * 0.37) - t * spec.speed * 0.6) * amp * 0.35;
      var col = p.cool
        ? lightTheme
          ? "rgba(8, 145, 178,"
          : "rgba(160, 245, 255,"
        : lightTheme
          ? "rgba(168, 85, 247,"
          : "rgba(255, 170, 230,";
      var g = ctx.createRadialGradient(x, y, 0, x, y, p.r * 4);
      g.addColorStop(0, col + (0.85 * alphaMul) + ")");
      g.addColorStop(0.45, col + (0.28 * alphaMul) + ")");
      g.addColorStop(1, col + "0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(x, y, p.r * 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function paint(animated) {
    if (!ctx || !w) return;
    ctx.clearRect(0, 0, w, h);
    var t = animated ? (typeof performance !== "undefined" ? performance.now() : Date.now()) - t0 : 0;
    var specs = waveSpecs();
    var alphaMul = mode === "calm" ? 0.55 : mode === "deep" ? 1.15 : 0.9;
    if (lightTheme) alphaMul *= 0.75;

    for (var i = 0; i < specs.length; i++) strokeWave(specs[i], t, alphaMul);

    if (animated && mode !== "calm") {
      ensurePackets(mode === "deep" ? 7 : 4);
      drawPackets(specs, t, alphaMul);
    }
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
