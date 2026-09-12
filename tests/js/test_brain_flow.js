/* Brain Flow — particle/intel/cite API trên graph.js + brain-flow.js
   Chạy: node tests/js/test_brain_flow.js
*/
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const GRAPH = fs.readFileSync(path.join(ROOT, "dashboard", "graph.js"), "utf8");
const FLOW = fs.readFileSync(path.join(ROOT, "dashboard", "brain-flow.js"), "utf8");
const CSS = fs.readFileSync(path.join(ROOT, "dashboard", "style.css"), "utf8");
const HTML = fs.readFileSync(path.join(ROOT, "dashboard", "index.html"), "utf8");
const CHAT = fs.readFileSync(path.join(ROOT, "dashboard", "chat-render.js"), "utf8");
const APP = fs.readFileSync(path.join(ROOT, "dashboard", "app.js"), "utf8");

let fails = 0;
function check(name, cond) {
  console.log((cond ? "ok   " : "FAIL ") + name);
  if (!cond) fails++;
}

check("có setFlowMode / getFlowMode / cycleFlowMode",
  /setFlowMode\s*\(/.test(GRAPH) && /getFlowMode\s*\(/.test(GRAPH) && /cycleFlowMode\s*\(/.test(GRAPH));
check("có linkDirectionalParticles", /linkDirectionalParticles\s*\(/.test(GRAPH));
check("có citeNode + pulseNode + flashNewLinks",
  /citeNode\s*\(/.test(GRAPH) && /pulseNode\s*\(/.test(GRAPH) && /flashNewLinks\s*\(/.test(GRAPH));
check("có noteIntel + intelSnapshot",
  /noteIntel\s*\(/.test(GRAPH) && /intelSnapshot\s*\(/.test(GRAPH));
check("có _drawFlowLink vệt axon", /_drawFlowLink\s*\(/.test(GRAPH));
check("emitParticle khi cite/flash", /emitParticle\s*\(/.test(GRAPH));
check("calm/_reducedMotion tắt particle",
  /_flowMode === "calm"/.test(GRAPH) && /_reducedMotion/.test(GRAPH));
check("addOrUpdate gọi flashNewLinks",
  /addOrUpdate[\s\S]{0,1200}?flashNewLinks/.test(GRAPH));

global.window = global;
global.document = {
  createElement: () => ({ getContext: () => null, width: 0, height: 0 }),
  documentElement: { getAttribute: () => null },
};
global.localStorage = {
  _m: {},
  getItem(k) { return this._m[k] || null; },
  setItem(k, v) { this._m[k] = String(v); },
};
global.performance = { now: () => Date.now() };
global.window.dispatchEvent = () => true;
global.window.CustomEvent = function (type, init) {
  this.type = type;
  this.detail = init && init.detail;
};
global.Event = function (type) { this.type = type; };

function makeFG() {
  return {
    _data: { nodes: [], links: [] },
    _emitted: 0,
    graphData(d) { if (d !== undefined) { this._data = d; return this; } return this._data; },
    width() { return this; }, height() { return this; },
    backgroundColor() { return this; }, nodeId() { return this; },
    nodeRelSize() { return this; }, nodeVal() { return this; },
    linkColor() { return this; }, linkWidth() { return this; },
    linkDirectionalParticles() { return this; },
    linkDirectionalParticleWidth() { return this; },
    linkDirectionalParticleSpeed() { return this; },
    linkDirectionalParticleColor() { return this; },
    linkCanvasObjectMode() { return this; }, linkCanvasObject() { return this; },
    nodeCanvasObjectMode() { return this; }, nodeCanvasObject() { return this; },
    onNodeHover() { return this; }, onNodeClick() { return this; },
    onNodeDragEnd() { return this; }, onBackgroundClick() { return this; },
    d3Force() { return this; }, d3AlphaTarget() { return this; },
    d3ReheatSimulation() { return this; },
    warmupTicks() { return this; }, cooldownTime() { return this; },
    enableNodeDrag() { return this; }, enableZoomInteraction() { return this; },
    enablePanInteraction() { return this; },
    zoomToFit() { return this; }, pauseAnimation() { return this; },
    resumeAnimation() { return this; },
    emitParticle() { this._emitted += 1; return this; },
    graph2ScreenCoords(x, y) { return { x: x + 10, y: y + 10 }; },
  };
}
global.ForceGraph = function () {
  return function () { return makeFG(); };
};

require(path.join(ROOT, "dashboard", "graph.js"));
check("JavisGraph export", typeof window.JavisGraph === "function");

const g = new window.JavisGraph({ clientWidth: 800, clientHeight: 600, style: {} });
g.graph = makeFG();
const link = { source: "a", target: "b" };
g.graph.graphData({
  nodes: [
    { id: "a", label: "Alpha", path: "Alpha.md", x: 10, y: 20, links: 1 },
    { id: "b", label: "Beta", path: "Beta.md", x: 40, y: 50, links: 1 },
  ],
  links: [link],
});

check("default flow mode = flow", g.getFlowMode() === "flow");
check("cycleFlowMode flow→deep", g.cycleFlowMode() === "deep");
check("cycleFlowMode deep→calm", g.cycleFlowMode() === "calm");
check("calm → 0 particle", g._particleCount(link) === 0);
g.setFlowMode("flow");
check("citeNode tìm theo path", !!g.citeNode("Alpha.md", 1000));
check("citeNode bật hot link", g._isHotLink(link) === true);
check("intelSnapshot có nodes/links/mode", (() => {
  const s = g.intelSnapshot();
  return s.nodes === 2 && s.links === 1 && s.mode === "flow";
})());
check("noteIntel đẩy recent", (() => {
  g.noteIntel("born", "Gamma", "Gamma.md");
  const r = g.intelSnapshot().recent[0];
  return r && (r.text === "Gamma" || r.kind === "born");
})());
check("addOrUpdate note mới flash", (() => {
  const r = g.addOrUpdate({ id: "c", label: "Gamma", path: "Gamma.md", links: 1 }, ["a"], true);
  return r.created === true && g._hotLinks.size >= 1;
})());

check("brain-flow.js có HUD + pulse + cite",
  /brain-intel/.test(FLOW) && /javisPulseVault/.test(FLOW) && /javisBrainCite/.test(FLOW));
check("brain-flow lắng nghe javis-intel / javis-flow-mode",
  /javis-intel/.test(FLOW) && /javis-flow-mode/.test(FLOW));
check("index nạp brain-flow.js", /brain-flow\.js/.test(HTML));
check("CSS có brain-intel + vt-pulse + brain-trail",
  /brain-intel/.test(CSS) && /vt-pulse/.test(CSS) && /brain-trail/.test(CSS));
check("chat-render gọi javisBrainCite", /javisBrainCite/.test(CHAT));
check("app.js bắn javis-graph-add", /javis-graph-add/.test(APP));

if (fails) {
  console.log("\n" + fails + " FAIL");
  process.exit(1);
}
console.log("\nTẤT CẢ PASS");
