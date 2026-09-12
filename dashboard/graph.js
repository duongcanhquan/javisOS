// ============================================
// JAVIS OS - Knowledge graph "Tinh vân bộ não" (force-graph / d3-force, kiểu Obsidian)
// Engine d3-force. Thiết kế: node = sao phát sáng, TÔ MÀU THEO DANH MỤC
// (thư mục cha, khớp nhãn PERSONAL/BUSINESS...), hover = rọi đèn vùng liên quan (synapse), thở nhẹ
// lúc nghỉ, nhãn chỉ hiện khi hover / zoom sát / vài hub lớn.
// ============================================

// --- Bảng màu danh mục: gán theo tên danh mục ổn định ---
// Hai bảng CÙNG THỨ TỰ HUE nên một thư mục giữ nguyên "màu nhận dạng" khi đổi tông:
// chàm vẫn là chàm, lục vẫn là lục - chỉ đổi độ đậm cho hợp nền.
// Tối: màu rực để nổi trên nền đen. Sáng: mực sẫm cùng hue, đều đạt >=4.5:1 trên
// giấy ngà - bê nguyên bảng rực sang nền trắng thì chấm nào cũng nhợt như nhau.
const CAT_COLORS_DARK = ["#7ee0d8", "#3fdc9a", "#6b8cff", "#ff7a9c", "#4aa8ff", "#93b4ff",
  "#f0c853", "#5ad1c4", "#e07ad1", "#7ed957", "#67e8f9", "#9fb0cf"];
const CAT_COLORS_LIGHT = ["#0f766e", "#0f8f63", "#1d4ed8", "#c93b62", "#1668c4", "#3b6bff",
  "#96760a", "#0e8b81", "#a83c95", "#3e8f22", "#0e7490", "#5a688a"];

// Bảng đang dùng + các màu phụ thuộc tông của lớp vẽ. Đổi tông thì hoán bảng rồi
// vẽ lại; không rebuild đồ thị nên vị trí node và trạng thái hover giữ nguyên.
let CAT_COLORS = CAT_COLORS_DARK;
let INK = {
  hoverCore: "#ffffff",                      // lõi node đang trỏ - "nóng nhất"
  fallback: "#3ee0d6",
  glowCore: "rgba(255,255,255,0.95)",        // lõi trắng nóng của quầng sáng
  glowStops: [[0.28, 0.9], [0.6, 0.32]],
  linkIdle: "rgba(110,180,220,0.08)",
  linkOn: "rgba(62,224,214,0.42)",
  linkOff: "rgba(80,140,200,0.02)",
  labelHalo: "rgba(4,6,12,0.85)",
  labelText: "rgba(233,235,246,0.96)",
};
const INK_LIGHT = {
  hoverCore: "#121826",
  fallback: "#0f766e",
  // Trên giấy KHÔNG có "lõi trắng nóng": quầng sáng đổi thành vệt mực loang,
  // đậm ở tâm rồi thấm nhạt ra - cùng hue với node.
  glowCore: null,
  glowStops: [[0.0, 0.55], [0.30, 0.30], [0.62, 0.11]],
  linkIdle: "rgba(80,140,180,0.16)",
  linkOn: "rgba(13,148,136,0.50)",
  linkOff: "rgba(80,140,180,0.05)",
  labelHalo: "rgba(244,246,251,0.92)",
  labelText: "rgba(18,24,38,0.97)",
};
const INK_DARK = INK;

function _catOf(node) {
  const segs = (node.path || "").split("/");
  let cat = segs.length >= 2 ? segs[segs.length - 2] : "root";
  cat = cat.replace(/^\d+\s*[-_.]\s*/, "").trim().toLowerCase();   // bỏ tiền tố "07 - "
  return cat || "root";
}
function _hash(s) { let h = 0; s = String(s || ""); for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return h; }

// Gán màu danh mục (tuần tự theo danh mục) vào n.color của từng node.
// Nhớ CHỈ SỐ danh mục (không phải màu) để đổi tông chỉ là tra lại bảng khác.
window.JavisCatColorize = function (nodes) {
  const idx = {}; let next = 0;
  (nodes || []).forEach(n => {
    const segs = (n.path || "").split("/");
    let cat = (segs.length >= 2 ? segs[segs.length - 2] : "root").replace(/^\d+\s*[-_.]\s*/, "").trim().toLowerCase() || "root";
    if (!(cat in idx)) { idx[cat] = next; next++; }
    n.__catIdx = idx[cat];
    n.color = CAT_COLORS[idx[cat] % CAT_COLORS.length];   // ghi đè màu tím backend bằng màu danh mục
  });
  window.__javisCatIdx = idx;
  window.__javisCatMap = _mapFromIdx(idx);   // để nhãn danh mục tô chữ khớp màu
  return window.__javisCatMap;
};

function _mapFromIdx(idx) {
  const map = {};
  Object.keys(idx || {}).forEach(k => { map[k] = CAT_COLORS[idx[k] % CAT_COLORS.length]; });
  return map;
}

// Mở một lối tra màu cho nhãn danh mục trong app.js.
// để nó lấy đúng bảng màu của tông đang bật.
window.JavisCatColorAt = function (idx) {
  return CAT_COLORS[(idx || 0) % CAT_COLORS.length];
};

// --- Sprite quầng sáng (cache theo màu) → vẽ bằng drawImage (rẻ), tạo hiệu ứng tinh vân ---
const _glowCache = {};
function _hexA(hex, a) {
  const m = String(hex || "#9d7aff").replace("#", "");
  const r = parseInt(m.substring(0, 2), 16), g = parseInt(m.substring(2, 4), 16), b = parseInt(m.substring(4, 6), 16);
  return `rgba(${r || 157},${g || 122},${b || 255},${a})`;
}
function _glowSprite(color) {
  const key = color + (INK === INK_LIGHT ? "|L" : "|D");
  if (_glowCache[key]) return _glowCache[key];
  const s = 64, cv = document.createElement("canvas"); cv.width = cv.height = s;
  const ctx = cv.getContext("2d");
  const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  if (INK.glowCore) g.addColorStop(0, INK.glowCore);   // lõi trắng nóng (chỉ tông tối)
  INK.glowStops.forEach(([at, a]) => g.addColorStop(at, _hexA(color, a)));
  g.addColorStop(1, _hexA(color, 0));                  // viền tan vào nền
  ctx.fillStyle = g; ctx.fillRect(0, 0, s, s);
  _glowCache[key] = cv; return cv;
}

// Đổi tông: hoán bảng màu + bảng mực, gán lại màu cho node đang có, rồi vẽ lại.
// Không nạp lại dữ liệu nên toạ độ node, cụm đang rọi sáng và node đang trỏ giữ nguyên.
function _applyGraphTheme(light) {
  CAT_COLORS = light ? CAT_COLORS_LIGHT : CAT_COLORS_DARK;
  INK = light ? INK_LIGHT : INK_DARK;
  if (window.__javisCatIdx) window.__javisCatMap = _mapFromIdx(window.__javisCatIdx);
  const g = window.__javisGraph;
  if (g && g._recolor) g._recolor();
  try { window.dispatchEvent(new Event("javis-catcolors-change")); } catch (e) {}
}
// Đọc tông hiện tại từ thuộc tính trên <html>. Bọc typeof vì file này còn được nạp
// trong Node (test JS ở tests/js/) với DOM giả lập tối thiểu, không có documentElement.
function _themeIsLight() {
  return typeof document !== "undefined" && document.documentElement
    ? document.documentElement.getAttribute("data-theme") === "light"
    : false;
}
// KHÔNG dùng window.javisTheme.on() ở đây: file này có lúc nạp trước theme.js, khi đó
// window.javisTheme chưa tồn tại nên đăng ký hụt IM LẶNG và đồ thị kẹt ở bảng màu tối.
// Nghe thẳng sự kiện + tự đọc thuộc tính thì đúng ở mọi thứ tự nạp.
if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
  window.addEventListener("javis-theme-change", function (e) {
    _applyGraphTheme(!!(e && e.detail && e.detail.light));
  });
}
_applyGraphTheme(_themeIsLight());

// Lực kéo mọi node về tâm (0,0) tỉ lệ khoảng cách → cả mạng co lại thành hình tròn ở giữa,
// node bị kéo ra sẽ tự trôi về. (d3 custom force: hàm(alpha) + initialize(nodes)).
function _centerGravity(strength) {
  let _nodes = [];
  const force = (alpha) => {
    const k = strength * alpha;
    for (let i = 0; i < _nodes.length; i++) { const n = _nodes[i]; n.vx -= n.x * k; n.vy -= n.y * k; }
  };
  force.initialize = (ns) => { _nodes = ns; };
  return force;
}

// Xoáy rất nhẹ quanh tâm (thiên hà) — tangential, không đẩy bán kính. strength ~0.008–0.02.
function _swirlForce(strength) {
  let _nodes = [];
  const force = () => {
    // Không nhân alpha: giữ drift chậm sau khi simulation nguội (alpha≈0).
    const k = strength;
    for (let i = 0; i < _nodes.length; i++) {
      const n = _nodes[i];
      if (n.fx != null || n.fy != null) continue;
      n.vx += -n.y * k;
      n.vy += n.x * k;
    }
  };
  force.initialize = (ns) => { _nodes = ns; };
  force.strength = (_) => { if (_ != null) strength = _; return force; };
  return force;
}

function _prefersReducedMotion() {
  try {
    return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  } catch (e) { return false; }
}

class JavisGraph {
  constructor(container) {
    this.container = container;
    this.graph = null;
    this.level = 0;
    this._thinking = false;
    this._fitted = false;
    this._t0 = 0;
    this._hoverId = null;
    this._nbrs = new Set();
    this._catFilter = null;
    this._swirl = null;
    this._swirlOn = false;
    this._lite = false;
    this._reducedMotion = _prefersReducedMotion();
    // Flow layer: calm | flow | deep — lưu thông cạnh, pulse node, cite từ chat
    this._flowMode = "flow";
    try {
      const saved = localStorage.getItem("javis.brainFlowMode");
      if (saved === "calm" || saved === "flow" || saved === "deep") this._flowMode = saved;
    } catch (e) {}
    this._hotLinks = new Map();   // key "a||b" -> untilMs
    this._pulseUntil = new Map(); // nodeId -> untilMs
    this._citeId = null;
    this._citeUntil = 0;
    this._intelEvents = [];       // {t, kind, text, path}
    this._flowTick = 0;
    window.__javisGraph = this;
    try { window.dispatchEvent(new Event("javis-graph-created")); } catch (e) {}
  }

  _prep(nodes) {
    nodes = nodes || [];
    if (!this._catMap) { this._catMap = {}; this._catNext = 0; }
    const markHubs = nodes.length > 6;                          // chỉ đánh dấu hub khi nạp cả mạng
    const hubIds = markHubs
      ? new Set([...nodes].sort((a, b) => (b.links || 0) - (a.links || 0)).slice(0, 4).map(n => n.id))
      : null;
    nodes.forEach(n => {
      const cat = _catOf(n);
      // Gán màu TUẦN TỰ theo danh mục (mỗi danh mục một màu khác nhau) - không hash để tránh trùng.
      // Lưu CHỈ SỐ để đổi tông chỉ cần tra lại bảng màu khác, khỏi gán lại từ đầu.
      if (!(cat in this._catMap)) { this._catMap[cat] = this._catNext; this._catNext++; }
      n.__cat = cat;
      n.__catIdx = this._catMap[cat];
      n.__c = CAT_COLORS[n.__catIdx % CAT_COLORS.length];
      n.__r = 3 + Math.sqrt(Math.min(55, n.links || 0)) * 1.9;   // chấm sáng vừa (glow tinh linh)
      n.__ph = (_hash(n.id) % 628) / 100;                       // pha thở lệch nhau
      if (markHubs) n.__hub = hubIds.has(n.id);
    });
  }

  async load(query = "source=all") {
    // Mặc định ẨN note cô đơn (0 wikilink): tránh màn hình đầy chấm rời (README.ja-JP, DESIGN-pl...).
    // Server còn lọc noise; ?orphans=1 chỉ hiện cô đơn nếu muốn kiểu Obsidian.
    const res = await fetch(`/graph?${query}&orphans=0`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `Không tải được đồ thị (${res.status})`);
    const nodes = Array.isArray(data.nodes) ? data.nodes : [];
    this._catMap = null;                     // gán lại màu danh mục tươi cho mỗi lần nạp
    this._prep(nodes);
    window.__javisCatIdx = this._catMap;                    // danh mục → chỉ số
    window.__javisCatMap = _mapFromIdx(this._catMap);       // để nhãn danh mục (app.js) tô chữ khớp màu node
    const links = (data.edges || []).map(e => ({ source: e.source, target: e.target }));

    if (!this.graph) {
      if (!window.ForceGraph) throw new Error("Thư viện đồ thị 2D chưa tải (kiểm tra mạng)");
      const self = this;
      this.graph = ForceGraph()(this.container)
        .backgroundColor("rgba(0,0,0,0)")
        .autoPauseRedraw(false)                             // vẽ liên tục → hover nhạy tức thì + thở mượt
        .nodeId("id")
        .nodeRelSize(1)
        .nodeVal(n => { const r = (n.__r || 4) + 5; return r * r; })   // vùng bắt hover rộng hơn hình (dễ trỏ)
        .warmupTicks(24)
        .cooldownTime(5000)
        .linkColor(l => {
          if (self._hoverId != null) {
            const s = (l.source && l.source.id) || l.source, tg = (l.target && l.target.id) || l.target;
            return (s === self._hoverId || tg === self._hoverId) ? INK.linkOn : INK.linkOff;
          }
          if (self._swirlOn && !self._reducedMotion) {
            const t = (typeof performance !== "undefined" ? performance.now() : Date.now());
            const shimmer = 0.72 + 0.28 * Math.sin(t / 1800 + (l.__ph || 0));
            const m = String(INK.linkIdle).match(/rgba?\(([^)]+)\)/);
            if (m) {
              const parts = m[1].split(",").map((x) => x.trim());
              if (parts.length >= 4) {
                const a = Math.min(0.2, parseFloat(parts[3]) * shimmer * 1.35);
                return "rgba(" + parts[0] + "," + parts[1] + "," + parts[2] + "," + a.toFixed(3) + ")";
              }
            }
          }
          return INK.linkIdle;
        })
        .linkWidth(l => {
          if (self._isHotLink(l)) return self._flowMode === "deep" ? 2.8 : 2.1;
          if (self._hoverId != null) {
            const s = (l.source && l.source.id) || l.source, t = (l.target && l.target.id) || l.target;
            if (s === self._hoverId || t === self._hoverId) return 1.6;
          }
          if (self._flowMode === "deep") return 0.85;
          if (self._flowMode === "flow") return 0.7;
          return 0.35;
        })
        .linkDirectionalParticles(l => self._particleCount(l))
        .linkDirectionalParticleWidth(l => self._isHotLink(l) ? 3.4 : (self._flowMode === "deep" ? 2.6 : 2.1))
        .linkDirectionalParticleSpeed(l => self._particleSpeed(l))
        .linkDirectionalParticleColor(l => self._particleColor(l))
        .linkCanvasObjectMode(() => self._flowMode === "calm" || self._reducedMotion ? undefined : "after")
        .linkCanvasObject((l, ctx, scale) => self._drawFlowLink(l, ctx, scale))
        .nodeCanvasObjectMode(() => "replace")
        .nodeCanvasObject((n, ctx, scale) => self._drawNode(n, ctx, scale))
        .onNodeHover(n => {
          self._hoverId = n ? n.id : null;
          self._nbrs = new Set();
          if (n) {
            self.graph.graphData().links.forEach(l => {
              const s = (l.source && l.source.id) || l.source, t = (l.target && l.target.id) || l.target;
              if (s === n.id) self._nbrs.add(t); else if (t === n.id) self._nbrs.add(s);
            });
          }
          self.container.style.cursor = n ? "pointer" : "grab";
        })
        .onNodeClick(n => { if (window.onGraphNodeClick) window.onGraphNodeClick(n); })   // chỉ mở note, KHÔNG lia camera
        .onNodeDragEnd(n => { n.fx = null; n.fy = null; })                                // thả kéo → node tự trôi về
        .onBackgroundClick(() => { self._catFilter = null; })                            // KHÔNG recenter → bấm được node viền
        .minZoom(0.05).maxZoom(3)                                                         // min nâng lên = mức fit sau khi lắng
        .onEngineStop(() => {
          if (self._fitted) return;
          self._fitted = true;
          self._fit(500);
          self._keepSwirlAlive();
        });

      // Lực đẩy vừa (node gần nhau, không văng) + hút MẠNH về tâm (co thành khối TRÒN, kéo node lẻ vào)
      // + link ngắn (cụm liên kết bám sát). Cân bằng để tròn co vào giữa như Obsidian mà chấm vẫn tách.
      try { this.graph.d3Force("charge").strength(-70); } catch (e) {}
      try { const lf = this.graph.d3Force("link"); if (lf) lf.distance(26); } catch (e) {}
      try { this.graph.d3Force("gravity", _centerGravity(0.1)); } catch (e) {}           // hút mạnh hơn → kéo cụm rời/xa vào gần
      this._swirl = _swirlForce(0.012);
      this._applySwirlGate();
      this.resize();
    }

    this._fitted = false;
    this._t0 = (typeof performance !== "undefined" ? performance.now() : Date.now());
    try { this.graph.minZoom(0.05); } catch (e) {}   // mở lại giới hạn để lần fit mới không bị kẹp
    links.forEach((l, i) => { l.__ph = ((i * 17) % 628) / 100; });
    this.graph.graphData({ nodes, links });
    this._applySwirlGate();
    this.startAmbientSynapses();
    this.noteIntel("born", "não thức — " + nodes.length + " note · " + links.length + " mạch", "");
    this.resize();
    return data;
  }

  _drawNode(n, ctx, scale) {
    if (n.x == null || n.y == null) return;
    const t = (typeof performance !== "undefined" ? performance.now() : Date.now());
    const ent = this._t0 ? Math.min(1, (t - this._t0) / 700) : 1;      // fade-in khi mở
    const hovering = this._hoverId != null;
    const isHover = n.id === this._hoverId;
    const isNbr = hovering && this._nbrs.has(n.id);
    const catDim = this._catFilter && n.__cat !== this._catFilter && !isHover && !isNbr;
    const dim = (hovering && !isHover && !isNbr) || catDim;
    const breathe = 1 + (this._swirlOn && !this._reducedMotion ? 0.08 : 0.05)
      * Math.sin(t / 650 + (n.__ph || 0));       // thở nhẹ, lệch pha (mạnh hơn khi ngân hà bật)
    const pulse = this._thinking ? (1 + (0.16 + 0.3 * this.level) * Math.sin(t / 220)) : (1 + 0.25 * this.level);
    let born = 1;
    if (n.__born) { const age = (t - n.__born) / 500; born = age < 1 ? age : 1; if (age >= 1) n.__born = 0; }  // nảy sinh
    const nowMs = t;
    const pulseLeft = this._pulseUntil.get(n.id) || 0;
    const isPulsing = pulseLeft > nowMs;
    const citeOn = this._citeId === n.id && this._citeUntil > nowMs;
    const flowBoost = (isPulsing || citeOn) ? (1.15 + 0.2 * Math.sin(nowMs / 90)) : 1;
    const r = (n.__r || 5) * (isHover ? 1.35 : 1) * breathe * pulse * (0.4 + 0.6 * born) * flowBoost;
    const alpha = (dim ? 0.14 : 1) * ent * (0.4 + 0.6 * born);

    // Quầng cite / pulse — ma mị, phosphor lạnh
    if ((citeOn || isPulsing) && !this._reducedMotion) {
      const ring = r * (citeOn ? 3.6 : 2.8);
      const g = ctx.createRadialGradient(n.x, n.y, r * 0.2, n.x, n.y, ring);
      g.addColorStop(0, citeOn ? "rgba(255,120,200,0.55)" : "rgba(62,224,214,0.45)");
      g.addColorStop(0.45, citeOn ? "rgba(180,80,220,0.18)" : "rgba(80,160,255,0.16)");
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.globalAlpha = 0.9 * ent;
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(n.x, n.y, ring, 0, Math.PI * 2); ctx.fill();
    }

    // Quầng sáng (tông sáng: vệt mực loang quanh chấm)
    ctx.globalAlpha = alpha;
    const spr = _glowSprite(n.__c || INK.fallback);
    const gsz = r * (citeOn ? 3.1 : 2.4);
    ctx.drawImage(spr, n.x - gsz / 2, n.y - gsz / 2, gsz, gsz);
    // Lõi đặc
    ctx.globalAlpha = Math.min(1, alpha + 0.15);
    ctx.beginPath(); ctx.arc(n.x, n.y, r * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = isHover ? INK.hoverCore : (n.__c || INK.fallback);
    ctx.fill();
    ctx.globalAlpha = 1;

    // Nhãn: CHỈ note đang trỏ (như Obsidian). KHÔNG hiện-hết-khi-zoom (vừa loạn, vừa làm zoom khựng
    // do phải vẽ hàng trăm chữ mỗi frame).
    const showLabel = isHover;
    if (showLabel && n.label) {
      const la = (dim ? 0.16 : (isHover ? 1 : 0.85)) * ent;
      const fs = Math.max(9, 11 / scale);
      ctx.font = `${fs}px -apple-system, Segoe UI, sans-serif`;
      ctx.textAlign = "center"; ctx.textBaseline = "top";
      const ly = n.y + r + 2;
      ctx.globalAlpha = la;
      ctx.lineWidth = 3 / scale; ctx.strokeStyle = INK.labelHalo;
      ctx.strokeText(n.label, n.x, ly);
      ctx.fillStyle = INK.labelText;
      ctx.fillText(n.label, n.x, ly);
      ctx.globalAlpha = 1;
    }
  }

  // Đổi tông: gán lại màu node theo bảng mới rồi ép vẽ lại một frame.
  // Không đụng graphData().nodes/links nên d3-force không bị khởi động lại - đồ thị
  // đứng yên tại chỗ, chỉ đổi màu. (Đổ lại graphData sẽ làm mạng giật và fit lại camera.)
  _recolor() {
    if (!this.graph) return;
    const d = this.graph.graphData();
    (d.nodes || []).forEach(n => {
      if (n.__catIdx != null) n.__c = CAT_COLORS[n.__catIdx % CAT_COLORS.length];
      if (n.color) n.color = n.__c || n.color;
    });
    // Ép force-graph vẽ lại dây nối (linkColor là hàm nên chỉ cần đánh thức vòng vẽ).
    try { this.graph.linkColor(this.graph.linkColor()); } catch (e) {}
  }

  // Lề chừa quanh đồ thị khi canh khung, TÍNH THEO khung thật chứ không phải số cố định.
  //
  // Trước bản này là `zoomToFit(500, 70)` - 70px mỗi bên, hằng số hợp lý cho khoang não
  // desktop (~900x700) nhưng thảm hoạ trên điện thoại. Khoang não mobile chỉ cao khoảng
  // 228px, nên 70px trên cộng 70px dưới ăn mất 140px, còn đúng 88px cho TOÀN BỘ đồ thị -
  // đó chính là "cục nhỏ xíu giữa màn hình" chủ repo chụp lại. Theo tỉ lệ thì desktop giữ
  // nguyên cảm giác cũ (700 * 0.10 = 70) còn mobile tự co xuống (228 * 0.10 = 23).
  _fitPad() {
    const w = this.container ? this.container.clientWidth : 0;
    const h = this.container ? this.container.clientHeight : 0;
    const nho = Math.min(w || 800, h || 600);
    return Math.max(10, Math.min(70, Math.round(nho * 0.10)));
  }

  _fit(ms = 400) {
    if (!this.graph) return;
    try {
      this.graph.zoomToFit(ms, this._fitPad());                 // canh cho MỌI node vừa khung
      // Sau khi fit: chặn zoom-out nhỏ hơn mức "mọi node vừa khung". Đặt sau khi hoạt ảnh
      // fit chạy xong, nếu không nó đọc phải mức zoom giữa chừng.
      setTimeout(() => {
        try { this.graph.minZoom(Math.min(this.graph.zoom() * 0.95, 1.2)); } catch (e) {}
      }, ms + 100);
    } catch (e) {}
  }

  // Canh lại khung theo yêu cầu (bung/thu khoang não trên điện thoại). Mở lại minZoom
  // trước: lần fit trước đã kẹp nó ở mức của khung CŨ, giữ nguyên là khung to hơn không
  // bao giờ zoom-out đủ để thấy hết.
  refit(ms = 400) {
    if (!this.graph) return;
    this.resize();
    try { this.graph.minZoom(0.05); } catch (e) {}
    this._fit(ms);
  }

  resize() {
    if (!this.graph || !this.container) return;
    const p = this.container.parentElement;
    const w = this.container.clientWidth || (p ? p.clientWidth : 800);
    const h = this.container.clientHeight || (p ? p.clientHeight : 600);
    if (w && h) this.graph.width(w).height(h);
  }

  // --- Điều khiển vòng đời đồ thị ---
  pause() {
    if (this.graph) { try { this.graph.pauseAnimation(); } catch (e) {} }
    this._setSwirlActive(false);
  }
  wake() {
    if (this.graph) { try { this.graph.resumeAnimation(); } catch (e) {} }
    this._applySwirlGate();
  }
  resume() { this.wake(); }
  setThinking(active) {
    const on = !!active;
    if (on && !this._thinking) this.noteIntel("think", "đang suy luận…", "");
    this._thinking = on;
    this._refreshFlowPaint();
  }
  setLevel(l) { this.level = l || 0; }

  /** Lite/mobile: tắt xoáy ngân hà (starfield cũng nhận qua console). */
  setLite(on) {
    this._lite = !!on;
    this._applySwirlGate();
  }

  _applySwirlGate() {
    this._reducedMotion = _prefersReducedMotion();
    const want = !this._lite && !this._reducedMotion;
    this._setSwirlActive(want);
  }

  _setSwirlActive(on) {
    this._swirlOn = !!on && !!this.graph;
    if (!this.graph) return;
    try {
      if (this._swirlOn) {
        this.graph.d3Force("swirl", this._swirl || _swirlForce(0.012));
        this._keepSwirlAlive();
      } else {
        this.graph.d3Force("swirl", null);
        try { this.graph.d3AlphaTarget(0); } catch (e) {}
      }
    } catch (e) {}
  }

  _keepSwirlAlive() {
    if (!this.graph || !this._swirlOn || this._reducedMotion) return;
    try {
      // alphaTarget nhỏ: simulation không tắt hẳn → swirl + shimmer tiếp tục
      this.graph.d3AlphaTarget(0.018);
      this.graph.d3ReheatSimulation();
    } catch (e) {}
  }

  // Rọi sáng một danh mục (bấm nhãn PERSONAL/SALES... quanh não). null = bỏ lọc.
  spotlightCategory(cat) {
    this._catFilter = cat ? String(cat).replace(/^\d+\s*[-_.]\s*/, "").trim().toLowerCase() : null;
    return this._catFilter;
  }

  nodeStats() {
    const d = this.graph ? this.graph.graphData() : { nodes: [], links: [] };
    return { nodes: d.nodes.length, links: d.links.length };
  }

  // --- Timelapse "cuộc đời brain": dựng lại mạng từ trống, note hiện dần theo thời gian tạo ---
  // Node sinh ra được XÓA toạ độ để d3 đặt lại từ đầu → mạng tự nở và co kéo hữu cơ như não
  // đang lớn lên. Link chỉ hiện khi CẢ HAI đầu đã ra đời. Chỉ chạy khi user bấm - không nền.
  // Nhịp CỐ ĐỊNH cho mỗi note (không ép tổng thời gian): não càng dày phim càng dài,
  // xem thư thái như lật album - yêu cầu của chủ, đừng đổi lại thành duration.
  // 160ms/note = chủ chốt sau khi thử 320ms thấy hơi rề.
  startTimelapse(perNoteMs = 160) {
    if (!this.graph || this._tlTimer) return false;
    const d = this.graph.graphData();
    if (!d.nodes.length) return false;
    this._tlFull = { nodes: d.nodes, links: d.links };            // snapshot khôi phục khi dừng/xong
    const order = [...d.nodes].sort((a, b) => (a.t || 0) - (b.t || 0));
    order.forEach(n => { delete n.x; delete n.y; delete n.vx; delete n.vy; n.fx = null; n.fy = null; });
    const total = order.length;
    const present = new Set();
    let i = 0;
    const self = this;
    // Warmup 24 tick sync mỗi lần đổ data sẽ khựng khi lặp hàng trăm lần → tắt trong lúc chiếu
    try { this.graph.warmupTicks(0); } catch (e) {}
    this.graph.graphData({ nodes: [], links: [] });               // não trống - thức giấc
    this._tlTimer = setInterval(() => {
      const now = (typeof performance !== "undefined" ? performance.now() : Date.now());
      const n = order[i];
      present.add(n.id); n.__born = now;
      i += 1;
      const links = self._tlFull.links.filter(l => {
        const s = (l.source && l.source.id) || l.source, t = (l.target && l.target.id) || l.target;
        return present.has(s) && present.has(t);
      });
      self.graph.graphData({ nodes: order.slice(0, i), links });
      if (i >= total) self.stopTimelapse();                       // hết phim → trả lại trạng thái thường
    }, perNoteMs);
    return true;
  }

  stopTimelapse() {
    if (this._tlTimer) { clearInterval(this._tlTimer); this._tlTimer = null; }
    try { this.graph.warmupTicks(24); } catch (e) {}
    if (this._tlFull) { this.graph.graphData(this._tlFull); this._tlFull = null; }
    try { window.dispatchEvent(new Event("javis-timelapse-end")); } catch (e) {}
  }

  get timelapseRunning() { return !!this._tlTimer; }


  // --- Brain Flow: lưu thông cạnh + intel ---
  _linkKey(l) {
    const s = (l.source && l.source.id) || l.source;
    const t = (l.target && l.target.id) || l.target;
    return s < t ? s + "||" + t : t + "||" + s;
  }
  _isHotLink(l) {
    const until = this._hotLinks.get(this._linkKey(l));
    return until && until > (typeof performance !== "undefined" ? performance.now() : Date.now());
  }
  _particleCount(l) {
    // Đậm hơn bản đầu: Flow/Deep phải NHÌN THẤY dòng chảy ngay, không chỉ 1 chấm mờ.
    if (this._reducedMotion || this._flowMode === "calm" || this._lite) return 0;
    if (this._isHotLink(l)) return this._flowMode === "deep" ? 8 : 5;
    if (this._hoverId != null) {
      const s = (l.source && l.source.id) || l.source, t = (l.target && l.target.id) || l.target;
      if (s === this._hoverId || t === this._hoverId) return this._flowMode === "deep" ? 7 : 4;
    }
    if (this._thinking) return this._flowMode === "deep" ? 4 : 3;
    return this._flowMode === "deep" ? 3 : 2;   // flow: 2 hạt/cạnh — nhìn thấy rõ mạng đang chảy
  }
  _particleSpeed(l) {
    if (this._isHotLink(l)) return 0.014;
    if (this._thinking) return 0.01;
    return this._flowMode === "deep" ? 0.0075 : 0.0055;
  }
  _particleColor(l) {
    if (this._isHotLink(l)) return "rgba(255,170,230,1)";
    if (this._thinking) return "rgba(140,220,255,0.95)";
    return INK === INK_LIGHT ? "rgba(13,148,136,0.9)" : "rgba(140,245,255,0.92)";
  }
  _drawFlowLink(l, ctx, scale) {
    if (this._reducedMotion || this._flowMode === "calm") return;
    const sa = l.source, ta = l.target;
    if (!sa || !ta || sa.x == null || ta.x == null) return;
    const hot = this._isHotLink(l);
    const hover = this._hoverId != null && (
      ((sa.id || sa) === this._hoverId) || ((ta.id || ta) === this._hoverId)
    );
    const now = (typeof performance !== "undefined" ? performance.now() : Date.now());
    const ph = (l.__ph || 0) + now / (hot ? 280 : (this._flowMode === "deep" ? 520 : 720));
    // Vệt axon trên MỌI cạnh ở Flow/Deep — mạng phải nhìn như đang dẫn điện
    ctx.save();
    let a = 0.22;
    if (hot) a = 0.7;
    else if (hover) a = 0.48;
    else if (this._thinking) a = 0.34;
    else if (this._flowMode === "deep") a = 0.28;
    ctx.globalAlpha = a;
    ctx.strokeStyle = hot ? "rgba(255,150,220,0.95)"
      : (INK === INK_LIGHT ? "rgba(13,148,136,0.7)" : "rgba(120,235,255,0.85)");
    ctx.lineWidth = (hot ? 2.2 : (hover ? 1.4 : 1.05)) / Math.max(scale, 0.4);
    ctx.setLineDash([5 / scale, 7 / scale]);
    ctx.lineDashOffset = -ph * 10;
    ctx.beginPath(); ctx.moveTo(sa.x, sa.y); ctx.lineTo(ta.x, ta.y); ctx.stroke();
    // Hạt sáng chạy dọc axon (thêm lớp nhìn thấy ngoài particle engine)
    if (!this._lite) {
      const t = ((now / (hot ? 900 : 1600)) + (l.__ph || 0)) % 1;
      const px = sa.x + (ta.x - sa.x) * t;
      const py = sa.y + (ta.y - sa.y) * t;
      const grd = ctx.createRadialGradient(px, py, 0, px, py, (hot ? 5 : 3.2) / Math.max(scale, 0.5));
      grd.addColorStop(0, hot ? "rgba(255,200,240,1)" : "rgba(180,255,255,0.95)");
      grd.addColorStop(1, "rgba(0,0,0,0)");
      ctx.globalAlpha = hot ? 0.95 : 0.65;
      ctx.fillStyle = grd;
      ctx.beginPath();
      ctx.arc(px, py, (hot ? 5 : 3.2) / Math.max(scale, 0.5), 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  setFlowMode(mode) {
    const m = (mode === "calm" || mode === "deep") ? mode : "flow";
    this._flowMode = m;
    try { localStorage.setItem("javis.brainFlowMode", m); } catch (e) {}
    this._refreshFlowPaint();
    try { window.dispatchEvent(new CustomEvent("javis-flow-mode", { detail: { mode: m } })); } catch (e) {}
    return m;
  }
  getFlowMode() { return this._flowMode || "flow"; }

  /** Nhịp synapse nền: thỉnh thoảng bắn particle trên vài cạnh hub — não "thở". */
  startAmbientSynapses() {
    if (this._ambientTimer || this._reducedMotion || this._lite) return;
    const self = this;
    this._ambientTimer = setInterval(() => {
      if (!self.graph || self._flowMode === "calm" || self._reducedMotion) return;
      try {
        const links = self.graph.graphData().links || [];
        if (!links.length) return;
        const n = self._flowMode === "deep" ? 4 : 2;
        for (let i = 0; i < n; i++) {
          const l = links[(Math.random() * links.length) | 0];
          self._hotLinks.set(self._linkKey(l), (typeof performance !== "undefined" ? performance.now() : Date.now()) + 900);
          try { self.graph.emitParticle(l); } catch (e) {}
        }
        self._refreshFlowPaint();
      } catch (e) {}
    }, self._flowMode === "deep" ? 1600 : 2400);
  }
  stopAmbientSynapses() {
    if (this._ambientTimer) { clearInterval(this._ambientTimer); this._ambientTimer = null; }
  }

  cycleFlowMode() {
    const order = ["calm", "flow", "deep"];
    const i = order.indexOf(this.getFlowMode());
    return this.setFlowMode(order[(i + 1) % order.length]);
  }
  _refreshFlowPaint() {
    if (!this.graph) return;
    try {
      this.graph
        .linkDirectionalParticles(this.graph.linkDirectionalParticles())
        .linkWidth(this.graph.linkWidth())
        .linkCanvasObjectMode(this.graph.linkCanvasObjectMode());
    } catch (e) {}
  }

  pulseNode(id, ms) {
    if (!id) return;
    const now = (typeof performance !== "undefined" ? performance.now() : Date.now());
    this._pulseUntil.set(id, now + (ms || 1600));
    this._pruneFlowMaps(now);
  }
  citeNode(idOrPath, ms) {
    if (!idOrPath || !this.graph) return null;
    const d = this.graph.graphData();
    const want = String(idOrPath).replace(/\\/g, "/");
    const base = want.split("/").pop().replace(/\.md$/i, "");
    let n = d.nodes.find(x => x.id === want || x.path === want);
    if (!n) n = d.nodes.find(x => (x.path || "").endsWith("/" + want) || (x.path || "") === want);
    if (!n) n = d.nodes.find(x => (x.label || "").replace(/\.md$/i, "") === base || (x.id || "").endsWith("/" + base + ".md") || (x.id || "").endsWith("/" + base));
    if (!n) return null;
    const now = (typeof performance !== "undefined" ? performance.now() : Date.now());
    this._citeId = n.id;
    this._citeUntil = now + (ms || 2800);
    this.pulseNode(n.id, ms || 2800);
    // Đánh nóng các cạnh kề + bắn particle
    (d.links || []).forEach(l => {
      const s = (l.source && l.source.id) || l.source, t = (l.target && l.target.id) || l.target;
      if (s === n.id || t === n.id) {
        this._hotLinks.set(this._linkKey(l), now + (ms || 2800));
        try { this.graph.emitParticle(l); } catch (e) {}
      }
    });
    this._refreshFlowPaint();
    this.noteIntel("cite", n.label || base, n.path || n.id);
    return n;
  }
  flashNewLinks(nodeId, linkTargets, ms) {
    if (!this.graph || !nodeId) return;
    const now = (typeof performance !== "undefined" ? performance.now() : Date.now());
    const d = this.graph.graphData();
    const targets = new Set(linkTargets || []);
    (d.links || []).forEach(l => {
      const s = (l.source && l.source.id) || l.source, t = (l.target && l.target.id) || l.target;
      if ((s === nodeId && targets.has(t)) || (t === nodeId && targets.has(s)) || ((s === nodeId || t === nodeId) && !targets.size)) {
        this._hotLinks.set(this._linkKey(l), now + (ms || 3200));
        try { this.graph.emitParticle(l); } catch (e) {}
      }
    });
    this.pulseNode(nodeId, ms || 2200);
    this._refreshFlowPaint();
  }
  noteIntel(kind, text, path) {
    const ev = { t: Date.now(), kind: kind || "info", text: String(text || "").slice(0, 80), path: path || "" };
    this._intelEvents.unshift(ev);
    if (this._intelEvents.length > 12) this._intelEvents.length = 12;
    try { window.dispatchEvent(new CustomEvent("javis-intel", { detail: ev })); } catch (e) {}
  }
  intelSnapshot() {
    const d = this.graph ? this.graph.graphData() : { nodes: [], links: [] };
    const nodes = d.nodes || [], links = d.links || [];
    const deg = new Map();
    links.forEach(l => {
      const s = (l.source && l.source.id) || l.source, t = (l.target && l.target.id) || l.target;
      deg.set(s, (deg.get(s) || 0) + 1); deg.set(t, (deg.get(t) || 0) + 1);
    });
    let orphans = 0;
    nodes.forEach(n => { if (!(deg.get(n.id) > 0)) orphans += 1; });
    const now = (typeof performance !== "undefined" ? performance.now() : Date.now());
    let hot = 0;
    this._hotLinks.forEach(u => { if (u > now) hot += 1; });
    return {
      mode: this.getFlowMode(),
      nodes: nodes.length,
      links: links.length,
      orphans,
      hot,
      thinking: !!this._thinking,
      recent: this._intelEvents.slice(0, 4),
    };
  }
  _pruneFlowMaps(now) {
    this._hotLinks.forEach((u, k) => { if (u <= now) this._hotLinks.delete(k); });
    this._pulseUntil.forEach((u, k) => { if (u <= now) this._pulseUntil.delete(k); });
    if (this._citeUntil && this._citeUntil <= now) { this._citeId = null; this._citeUntil = 0; }
  }

  addOrUpdate(node, linkTargets, isNew) {
    if (!this.graph || !node || !node.id) return { created: false };
    const d = this.graph.graphData();
    let n = d.nodes.find(x => x.id === node.id);
    if (!n) {
      n = { ...node };
      this._prep([n]);
      n.__born = (typeof performance !== "undefined" ? performance.now() : Date.now());   // hiệu ứng nảy sinh
      d.nodes.push(n);
    } else {
      Object.assign(n, { label: node.label, path: node.path, links: node.links, color: node.color });
      this._prep([n]);
    }
    (linkTargets || []).forEach(tid => {
      const dup = d.links.some(l => {
        const s = (l.source && l.source.id) || l.source, t = (l.target && l.target.id) || l.target;
        return (s === node.id && t === tid) || (s === tid && t === node.id);
      });
      if (!dup) d.links.push({ source: node.id, target: tid });
    });
    this.graph.graphData({ nodes: d.nodes, links: d.links });
    if (isNew || (linkTargets && linkTargets.length)) {
      this.flashNewLinks(node.id, linkTargets, isNew ? 3600 : 2400);
      this.noteIntel(isNew ? "born" : "link", node.label || node.id, node.path || node.id);
    }
    return { created: !!isNew };
  }
}

window.JavisGraph = JavisGraph;