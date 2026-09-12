// Brain Flow HUD — intel strip, chế độ Calm/Flow/Deep, trail chat↔graph, pulse vault.
// Tôn trọng prefers-reduced-motion. Không phụ thuộc Alpine.
(function () {
  var MODE_KEY = "javis.brainFlowMode";
  var MODE_LABEL = { calm: "CALM", flow: "FLOW", deep: "DEEP" };
  var MODE_HINT = {
    calm: "Yên — chỉ chấm & cạnh",
    flow: "Chảy — particle + tín hiệu sống",
    deep: "Sâu — axon + intel đầy đủ",
  };

  function reduced() {
    try {
      return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    } catch (e) {
      return false;
    }
  }

  function graph() {
    return window.__javisGraph || window.__javisGraph || null;
  }

  function $(id) {
    return document.getElementById(id);
  }

  function ensureHud() {
    var root = document.querySelector(".hud-center");
    if (!root) return null;
    var strip = $("brainIntel");
    if (!strip) {
      strip = document.createElement("div");
      strip.id = "brainIntel";
      strip.className = "brain-intel";
      strip.setAttribute("aria-live", "polite");
      strip.innerHTML =
        '<div class="bi-mode" id="brainIntelMode">FLOW</div>' +
        '<div class="bi-line" id="brainIntelLine">não đang lắng…</div>' +
        '<div class="bi-meta" id="brainIntelMeta"></div>';
      root.appendChild(strip);
    }
    var trail = $("brainTrail");
    if (!trail) {
      trail = document.createElement("svg");
      trail.id = "brainTrail";
      trail.className = "brain-trail";
      trail.setAttribute("aria-hidden", "true");
      root.appendChild(trail);
    }
    var btn = $("brainFlowBtn");
    if (!btn) {
      btn = document.createElement("button");
      btn.id = "brainFlowBtn";
      btn.type = "button";
      btn.className = "brain-overlay-toggle brain-flow-btn";
      btn.setAttribute("aria-label", "Đổi chế độ não Calm / Flow / Deep");
      btn.title = MODE_HINT.flow;
      btn.innerHTML =
        '<svg class="bf-ico" viewBox="0 0 24 24" aria-hidden="true">' +
        '<path d="M4 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0"></path>' +
        '<path d="M4 17c2-4 4-4 6 0s4 4 6 0 4-4 6 0"></path>' +
        '<path d="M4 7c2-4 4-4 6 0s4 4 6 0 4-4 6 0"></path>' +
        "</svg>" +
        '<span class="bf-badge" id="brainFlowBadge">FLOW</span>';
      root.appendChild(btn);
      btn.addEventListener("click", function () {
        var g = graph();
        var mode = g && g.cycleFlowMode ? g.cycleFlowMode() : cycleLocal();
        applyModeUi(mode);
      });
    }
    return { root: root, strip: strip, trail: trail, btn: btn };
  }

  function cycleLocal() {
    var order = ["calm", "flow", "deep"];
    var cur = "flow";
    try {
      cur = localStorage.getItem(MODE_KEY) || "flow";
    } catch (e) {}
    var next = order[(order.indexOf(cur) + 1) % order.length];
    try {
      localStorage.setItem(MODE_KEY, next);
    } catch (e) {}
    return next;
  }

  function applyModeUi(mode) {
    mode = mode || "flow";
    var root = document.querySelector(".hud-center");
    if (root) {
      root.classList.remove("brain-flow-calm", "brain-flow-flow", "brain-flow-deep");
      root.classList.add("brain-flow-" + mode);
    }
    var badge = $("brainFlowBadge");
    if (badge) badge.textContent = MODE_LABEL[mode] || "FLOW";
    var btn = $("brainFlowBtn");
    if (btn) btn.title = MODE_HINT[mode] || MODE_HINT.flow;
    var modeEl = $("brainIntelMode");
    if (modeEl) modeEl.textContent = MODE_LABEL[mode] || "FLOW";
    if (mode === "calm") {
      var strip = $("brainIntel");
      if (strip) strip.classList.add("bi-dim");
    } else {
      var s2 = $("brainIntel");
      if (s2) s2.classList.remove("bi-dim");
    }
  }

  function flashIntel() {
    var strip = $("brainIntel");
    if (!strip) return;
    strip.classList.remove("bi-flash");
    void strip.offsetWidth;
    strip.classList.add("bi-flash");
    clearTimeout(flashIntel._t);
    flashIntel._t = setTimeout(function () { strip.classList.remove("bi-flash"); }, 900);
  }

  function renderIntel(snap, ev) {
    var line = $("brainIntelLine");
    var meta = $("brainIntelMeta");
    if (!line || !meta) return;
    if (ev && ev.text) {
      flashIntel();
      var tag =
        ev.kind === "cite"
          ? "cite"
          : ev.kind === "born"
            ? "sinh"
            : ev.kind === "link"
              ? "nối"
              : ev.kind === "think"
                ? "suy"
                : "tín";
      line.innerHTML = '<span class="bi-tag">' + tag + "</span> " + escapeHtml(ev.text);
    } else if (snap) {
      line.textContent =
        snap.nodes + " note · " + snap.links + " liên kết" + (snap.thinking ? " · đang suy…" : "");
    }
    if (snap) {
      var bits = [];
      if (snap.hot) bits.push(snap.hot + " mạch nóng");
      if (snap.orphans) bits.push(snap.orphans + " cô đơn");
      meta.textContent = bits.join(" · ");
    }
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function refreshFromGraph() {
    var g = graph();
    if (!g || !g.intelSnapshot) return;
    var snap = g.intelSnapshot();
    applyModeUi(snap.mode);
    renderIntel(snap, snap.recent && snap.recent[0]);
  }

  // Pulse dòng file trên cây vault
  window.javisPulseVault = function (rel) {
    if (!rel) return;
    var tree = $("vaultTree");
    if (!tree) return;
    var want = String(rel).replace(/^\/+/, "");
    var node =
      tree.querySelector('.vt-node[data-rel="' + cssEscape(want) + '"]') ||
      tree.querySelector('.vt-node[data-rel$="' + cssEscape(want.split("/").pop()) + '"]');
    if (!node) return;
    node.classList.remove("vt-pulse");
    void node.offsetWidth;
    node.classList.add("vt-pulse");
    setTimeout(function () {
      node.classList.remove("vt-pulse");
    }, 1800);
  };

  function cssEscape(s) {
    if (window.CSS && CSS.escape) return CSS.escape(s);
    return String(s).replace(/"/g, '\\"');
  }

  // Trail SVG từ bubble chat (hoặc điểm mép phải) tới node trên graph
  window.javisBrainCite = function (path, fromEl) {
    var g = graph();
    var n = g && g.citeNode ? g.citeNode(path, 3000) : null;
    window.javisPulseVault(path);
    if (n) {
      try {
        g.noteIntel("cite", n.label || path, n.path || n.id);
      } catch (e) {}
    }
    drawTrail(fromEl, n);
    refreshFromGraph();
    return n;
  };

  function drawTrail(fromEl, node) {
    if (reduced()) return;
    var hud = ensureHud();
    if (!hud || !hud.trail) return;
    var svg = hud.trail;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var root = hud.root.getBoundingClientRect();
    var x1, y1;
    if (fromEl && fromEl.getBoundingClientRect) {
      var r = fromEl.getBoundingClientRect();
      x1 = r.left - root.left + r.width * 0.1;
      y1 = r.top - root.top + r.height / 2;
    } else {
      x1 = root.width - 8;
      y1 = root.height * 0.45;
    }
    var x2 = root.width * 0.5;
    var y2 = root.height * 0.5;
    if (node && node.x != null && gCoords(node)) {
      var c = gCoords(node);
      x2 = c.x;
      y2 = c.y;
    }
    var mx = (x1 + x2) / 2;
    var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute(
      "d",
      "M " + x1 + " " + y1 + " Q " + mx + " " + (y1 - 40) + " " + x2 + " " + y2
    );
    path.setAttribute("class", "brain-trail-path");
    svg.appendChild(path);
    var dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    dot.setAttribute("cx", x2);
    dot.setAttribute("cy", y2);
    dot.setAttribute("r", "4");
    dot.setAttribute("class", "brain-trail-dot");
    svg.appendChild(dot);
    svg.classList.add("show");
    clearTimeout(drawTrail._t);
    drawTrail._t = setTimeout(function () {
      svg.classList.remove("show");
      while (svg.firstChild) svg.removeChild(svg.firstChild);
    }, 1600);
  }

  function gCoords(node) {
    var g = graph();
    if (!g || !g.graph || typeof g.graph.graph2ScreenCoords !== "function") return null;
    try {
      return g.graph.graph2ScreenCoords(node.x, node.y);
    } catch (e) {
      return null;
    }
  }

  function onGraphAdd(detail) {
    if (!detail) return;
    if (detail.path || detail.id) window.javisPulseVault(detail.path || detail.id);
    refreshFromGraph();
  }

  function init() {
    var hud = ensureHud();
    if (!hud) return;
    var g = graph();
    var mode = (g && g.getFlowMode && g.getFlowMode()) || null;
    if (!mode) {
      try {
        mode = localStorage.getItem(MODE_KEY) || "flow";
      } catch (e) {
        mode = "flow";
      }
    }
    if (g && g.setFlowMode) g.setFlowMode(mode);
    applyModeUi(mode);
    refreshFromGraph();

    window.addEventListener("javis-intel", function (e) {
      var g2 = graph();
      renderIntel(g2 && g2.intelSnapshot ? g2.intelSnapshot() : null, e.detail);
    });
    window.addEventListener("javis-flow-mode", function (e) {
      applyModeUi(e.detail && e.detail.mode);
      refreshFromGraph();
    });
    window.addEventListener("javis-graph-created", function () {
      var g3 = graph();
      if (g3 && g3.setFlowMode) g3.setFlowMode(mode);
      refreshFromGraph();
    });
    window.addEventListener("javis-brain-cite", function (e) {
      var d = e.detail || {};
      window.javisBrainCite(d.path || d.target, d.el);
    });
    window.addEventListener("javis-graph-add", function (e) {
      onGraphAdd(e.detail);
    });

    // Quét intel định kỳ nhẹ — não “còn sống”
    setInterval(function () {
      if (document.hidden) return;
      if (!document.body || document.body.classList.contains("in-console")) return;
      refreshFromGraph();
    }, 4000);

    // Boot: ép FLOW (nếu chưa chọn), flash intel, để người dùng THẤY ngay là não đang chạy
    setTimeout(function () {
      var g4 = graph();
      if (g4 && g4.setFlowMode && g4.getFlowMode && g4.getFlowMode() === "calm") {
        /* giữ calm nếu user đã chọn */
      } else if (g4 && g4.setFlowMode) {
        g4.setFlowMode(g4.getFlowMode() || "flow");
      }
      applyModeUi((g4 && g4.getFlowMode && g4.getFlowMode()) || "flow");
      refreshFromGraph();
      flashIntel();
      var line = $("brainIntelLine");
      if (line && (!line.textContent || line.textContent.indexOf("lắng") >= 0)) {
        line.innerHTML = '<span class="bi-tag">flow</span> mạch tri thức đang chảy — bấm nút FLOW để đổi nhịp';
      }
    }, 700);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
