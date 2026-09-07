#!/usr/bin/env node
/**
 * Smoke test Moonshine STT path Javis uses after 0.55.116:
 * Transcriber.load(Base files) + createStream + addAudio (early AudioContext).
 *
 * Does NOT need a real mic: feeds WAV via MediaStreamDestination.
 *
 * Usage (from repo root, with models + wasm available):
 *   node scripts/moonshine-stt-smoke.mjs
 *
 * Env:
 *   MOONSHINE_WASM_DIR  — default: dashboard/vendor/moonshine-wasm/dist
 *   MOONSHINE_MODELS_DIR — default: tries vendor then /tmp/moonshine-probe/models
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const PORT = 8791;

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch (_) {}
  const candidates = [
    path.join(ROOT, "node_modules/playwright"),
    "/tmp/moonshine-probe/node_modules/playwright",
  ];
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, "index.mjs")) || fs.existsSync(path.join(c, "index.js"))) {
      return await import(pathToFileURL(path.join(c, "index.mjs")).href).catch(async () => {
        const req = createRequire(path.join(c, "package.json"));
        return { chromium: req(".").chromium };
      });
    }
  }
  throw new Error("playwright not installed — npm i -D playwright (or use /tmp/moonshine-probe)");
}

function findWasmDir() {
  const env = process.env.MOONSHINE_WASM_DIR;
  if (env && fs.existsSync(path.join(env, "index.js"))) return env;
  const candidates = [
    path.join(ROOT, "dashboard/vendor/moonshine-wasm/dist"),
    "/tmp/moonshine-probe/www-live-wasm",
    "/tmp/moonshine-probe/www/moonshine-wasm",
  ];
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, "index.js"))) return c;
  }
  return null;
}

function findModelsDir() {
  const env = process.env.MOONSHINE_MODELS_DIR;
  if (env && fs.existsSync(path.join(env, "en"))) return env;
  const candidates = [
    path.join(ROOT, "dashboard/vendor/moonshine-models"),
    "/tmp/moonshine-probe/models",
  ];
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, "en", "encoder_model.ort"))) return c;
  }
  return null;
}

function ensureSampleWav(wwwDir) {
  const out = path.join(wwwDir, "sample-en.wav");
  if (fs.existsSync(out) && fs.statSync(out).size > 1000) return out;
  const aiff = path.join(wwwDir, "sample-en.aiff");
  spawnSync(
    "say",
    [
      "-v",
      "Samantha",
      "-o",
      aiff,
      "Hello this is a longer speech recognition sample for testing the moonshine base model transcription quality.",
    ],
    { stdio: "ignore" }
  );
  spawnSync("afconvert", ["-f", "WAVE", "-d", "LEI16", aiff, out], { stdio: "ignore" });
  if (!fs.existsSync(out)) throw new Error("Could not create sample-en.wav (need macOS say/afconvert)");
  return out;
}

const wasmDir = findWasmDir();
const modelsDir = findModelsDir();
if (!wasmDir) {
  console.error("FAIL: moonshine wasm not found");
  process.exit(2);
}
if (!modelsDir) {
  console.error("FAIL: moonshine models not found");
  process.exit(2);
}

const www = fs.mkdtempSync(path.join(os.tmpdir(), "javis-moonshine-smoke-"));
fs.symlinkSync(wasmDir, path.join(www, "moonshine-wasm"));
fs.symlinkSync(modelsDir, path.join(www, "models"));
ensureSampleWav(www);

const html = `<!doctype html><html><body>
<button id="start" type="button">Start</button>
<pre id="out"></pre>
<script type="module">
window.__RESULT = { ok: false, ready: true };
const log = (...a) => { document.getElementById('out').textContent += a.join(' ') + '\\n'; console.log(...a); };

function resampleTo16k(input, inputRate) {
  const TARGET = 16000;
  if (inputRate === TARGET) return input;
  const ratio = inputRate / TARGET;
  const outLength = Math.floor(input.length / ratio);
  const output = new Float32Array(outLength);
  for (let i = 0; i < outLength; i++) {
    const pos = i * ratio;
    const idx = Math.floor(pos);
    const frac = pos - idx;
    const a = input[idx] || 0;
    const b = input[idx + 1] != null ? input[idx + 1] : a;
    output[i] = a + (b - a) * frac;
  }
  return output;
}

async function fetchFile(u) {
  const r = await fetch(u);
  if (!r.ok) throw new Error('fetch ' + u + ' ' + r.status);
  return new Uint8Array(await r.arrayBuffer());
}

async function runFromGesture() {
  if (!crossOriginIsolated) throw new Error('not crossOriginIsolated');
  const mod = await import('/moonshine-wasm/index.js');

  // EARLY capture AudioContext inside the click gesture (Javis 0.55.116).
  const capCtx = new AudioContext();
  if (capCtx.state === 'suspended') await capCtx.resume();
  const earlyState = capCtx.state;

  // Simulate long model download AFTER gesture
  await new Promise((r) => setTimeout(r, 2000));

  const files = {
    'encoder_model.ort': await fetchFile('/models/en/encoder_model.ort'),
    'decoder_model_merged.ort': await fetchFile('/models/en/decoder_model_merged.ort'),
    'tokenizer.bin': await fetchFile('/models/en/tokenizer.bin'),
  };
  const transcriber = await mod.Transcriber.load({
    files,
    modelArch: mod.ModelArch.Base,
    options: { identify_speakers: 'false' },
  });

  // Keep using the early context (not a new one after await).
  if (capCtx.state === 'suspended') await capCtx.resume();

  const ab = await (await fetch('/sample-en.wav')).arrayBuffer();
  const audio = await capCtx.decodeAudioData(ab.slice(0));
  const dest = capCtx.createMediaStreamDestination();
  const src = capCtx.createBufferSource();
  src.buffer = audio;
  src.connect(dest);
  src.start();

  const sourceNode = capCtx.createMediaStreamSource(dest.stream);
  const moonStream = transcriber.createStream({});
  const lines = [];
  const partials = [];
  moonStream.addListener({
    onLineTextChanged: (ev) => { if (ev?.line?.text) partials.push(ev.line.text); },
    onLineCompleted: (ev) => { if (ev?.line?.text) lines.push(ev.line.text); },
    onError: (ev) => { console.error(ev); },
  });
  moonStream.start();

  let peakRms = 0;
  const onChunk = (chunk) => {
    let sum = 0;
    for (let i = 0; i < chunk.length; i++) sum += chunk[i] * chunk[i];
    const rms = Math.sqrt(sum / Math.max(1, chunk.length));
    if (rms > peakRms) peakRms = rms;
    const resampled = resampleTo16k(chunk, capCtx.sampleRate);
    moonStream.addAudio(resampled, 16000);
    moonStream.transcribe();
  };

  const script = capCtx.createScriptProcessor(4096, 1, 1);
  script.onaudioprocess = (ev) => onChunk(new Float32Array(ev.inputBuffer.getChannelData(0)));
  sourceNode.connect(script);
  script.connect(capCtx.destination);

  await new Promise((r) => setTimeout(r, 7500));
  try { moonStream.stop(); } catch (e) {}
  const text = lines.join(' ').trim();
  window.__RESULT = {
    ok: text.length > 10 && peakRms > 0.0001,
    text,
    lineCount: lines.length,
    partialCount: partials.length,
    peakRms,
    isolated: crossOriginIsolated,
    earlyState,
    capState: capCtx.state,
  };
  log(JSON.stringify(window.__RESULT));
}

document.getElementById('start').onclick = () => {
  runFromGesture().catch((e) => {
    window.__RESULT = { ok: false, error: String(e && e.stack || e) };
    log('FATAL', window.__RESULT.error);
  });
};
</script></body></html>`;

fs.writeFileSync(path.join(www, "index.html"), html);

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".wasm": "application/wasm",
  ".ort": "application/octet-stream",
  ".bin": "application/octet-stream",
  ".wav": "audio/wav",
};

const server = http.createServer((req, res) => {
  let rel = decodeURIComponent(new URL(req.url || "/", "http://x").pathname);
  if (rel === "/") rel = "/index.html";
  const file = path.normalize(path.join(www, rel));
  if (!file.startsWith(www) || !fs.existsSync(file)) {
    res.writeHead(404);
    return res.end("missing");
  }
  res.writeHead(200, {
    "Content-Type": MIME[path.extname(file)] || "application/octet-stream",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "credentialless",
    "Cross-Origin-Resource-Policy": "same-origin",
  });
  res.end(fs.readFileSync(file));
});

await new Promise((r) => server.listen(PORT, "127.0.0.1", r));
console.log("smoke on", PORT, "wasm=", wasmDir, "models=", modelsDir);

const { chromium } = await loadPlaywright();
const browser = await chromium.launch({ headless: true });
const page = await (await browser.newContext()).newPage();
page.on("console", (m) => console.log("BROWSER:", m.text()));
await page.goto(`http://127.0.0.1:${PORT}/`);
await page.waitForFunction(() => window.__RESULT && window.__RESULT.ready === true, { timeout: 30000 });
await page.click('#start');
await page.waitForFunction(() => window.__RESULT && (window.__RESULT.ok === true || window.__RESULT.error), {
  timeout: 180000,
});
const result = await page.evaluate(() => window.__RESULT);
await browser.close();
server.close();

console.log("==== RESULT ====");
console.log(JSON.stringify(result, null, 2));
if (!result.ok) process.exit(1);
console.log("PASS");
