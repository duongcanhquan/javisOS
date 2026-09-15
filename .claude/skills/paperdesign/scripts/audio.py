#!/usr/bin/env python3
"""
Audio stage: per-beat narration (one consistent voice) + one instrumental BGM.

Default narration: Atlas `xai/tts-v1` (named `voice_id` + language).
Optional local narration: set `voice.backend` to `zerotts` (or `javis` / `local`)
to speak via Javis ZeroTTS - free, Vietnamese-focused; BGM still uses Atlas.
Falls back to Atlas TTS if ZeroTTS is missing or fails.

VOICE CLONING: set `voice.clone_ref` to a local audio sample and narration
switches to bytedance/seed-audio-1.0 with the sample as @audio1. Clone always
uses Atlas (ZeroTTS open-source cannot clone).

Usage: python3 audio.py <project_dir>   (default: out/tang-30s)
"""
import base64
import json
import os
import subprocess
import sys

from provider import get_provider, run_jobs

# xai/tts-v1 is a clean, predictable multilingual TTS (named voices + language
# select) — the default. Seed-Audio handles voice cloning (see CLONE_TEMPLATE)
# and SFX; never hand it bare narration without a pinned speaker.
VOICE_MODEL = "xai/tts-v1"
CLONE_MODEL = "bytedance/seed-audio-1.0"
MUSIC_MODEL = "minimax/music-2.6"

# Every clause is load-bearing: the speaker pin + "clean dry studio vocal only"
# block is what makes seed-audio's timing beat-alignable (without it the model
# invents pauses and SFX). `persona` tunes delivery (documentary narrator,
# luxury voice-over, ...); default suits explainers.
CLONE_TEMPLATE = (
    "**Speaker A** @audio1 keeps their own vocal timbre and speaks fluent natural "
    "{language} with a neutral accent, upbeat pace, crisp articulation, friendly and "
    "energetic like a {persona}. Clean dry studio vocal only — no background music, "
    "no sound effects, no room noise or reverb. They say: \"{script}\""
)
LANG_NAMES = {"en": "English", "zh": "Mandarin Chinese", "ja": "Japanese",
              "ko": "Korean", "es": "Spanish", "fr": "French", "de": "German",
              "vi": "Vietnamese"}

# Atlas / UI voice picker → ZeroTTS preset id.
_ATLAS_TO_ZEROTTS = {
    "vi-mai": "maichi", "mai": "maichi", "maichi": "maichi",
    "vi-duc": "giahuy", "duc": "giahuy", "giahuy": "giahuy",
    "vi-minh": "quangminh", "minh": "quangminh", "quangminh": "quangminh",
    "leo": "giahuy", "ara": "maichi", "eve": "baotrang",
    "baotrang": "baotrang", "kimoanh": "kimoanh", "hamy": "hamy",
    "huuduc": "huuduc", "tiendat": "tiendat",
}


def probe_dur(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    try:
        return float(out.strip())
    except ValueError:
        return 0.0


def _resolve_zerotts_voice(voice_id: str) -> str:
    key = (voice_id or "").strip().lower()
    if key.startswith("zerotts:"):
        key = key.split(":", 1)[1].strip()
    return _ATLAS_TO_ZEROTTS.get(key, key or "maichi")


def _import_zerotts_tts():
    """Nạp server/zerotts_tts từ repo (script chạy trong skill paperdesign)."""
    from pathlib import Path
    here = Path(__file__).resolve()
    # .../repo/.claude/skills/paperdesign/scripts/audio.py → parents[4] = repo
    root = here.parents[4]
    server = root / "server"
    if server.is_dir() and str(server) not in sys.path:
        sys.path.insert(0, str(server))
    import zerotts_tts as ztts  # type: ignore
    return ztts


def _wav_to_mp3(wav_path: str, mp3_path: str, speed: float = 1.0) -> None:
    cmd = ["ffmpeg", "-y", "-i", wav_path]
    # ZeroTTS không có speed API - chỉnh bằng atempo nếu cần (0.5..2.0)
    sp = float(speed or 1.0)
    if abs(sp - 1.0) >= 0.05:
        sp = max(0.5, min(2.0, sp))
        cmd += ["-filter:a", f"atempo={sp}"]
    cmd += ["-codec:a", "libmp3lame", "-q:a", "4", mp3_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(mp3_path) or os.path.getsize(mp3_path) < 64:
        raise RuntimeError((r.stderr or r.stdout or "ffmpeg wav→mp3 lỗi")[-400:])


def _narrate_zerotts(doc: dict, adir: str, voice: dict) -> None:
    """Lời thoại local ZeroTTS → narr_*.mp3. BGM vẫn do Atlas lo ở run()."""
    ztts = _import_zerotts_tts()
    if not ztts.available():
        raise RuntimeError(
            "ZeroTTS chưa cài trên máy chạy Javis. "
            "Chạy: pip install zerotts (lần đầu ~900MB), hoặc đổi backend về atlas."
        )
    voice_id = _resolve_zerotts_voice(
        voice.get("voice_id") or voice.get("zerotts_voice") or ""
    )
    speed = float(voice.get("speed", 1.0) or 1.0)
    print(f"[narr] backend=zerotts voice={voice_id} speed={speed}")
    for beat in doc["beats"]:
        text = (beat.get("narration") or "").strip()
        dest = os.path.join(adir, f"narr_{beat['id']}.mp3")
        if not text:
            print(f"[narr {beat['id']}] trống - bỏ qua")
            continue
        wav_bytes, _ = ztts.synthesize_sync(text, voice=voice_id)
        wav_path = dest[:-4] + ".wav"
        with open(wav_path, "wb") as f:
            f.write(wav_bytes)
        try:
            _wav_to_mp3(wav_path, dest, speed=speed)
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass
        beat["narration_audio"] = dest
        beat["narration_dur"] = round(probe_dur(dest), 2)
        beat["narration_backend"] = "zerotts"
        print(f"[narr {beat['id']}] {beat['narration_dur']}s -> {dest}")


def run(project_dir: str):
    bpath = os.path.join(project_dir, "beats.json")
    with open(bpath) as f:
        doc = json.load(f)
    adir = os.path.join(project_dir, "audio")
    os.makedirs(adir, exist_ok=True)

    prov = get_provider(doc.get("provider"))
    voice = doc.get("voice", {}) or {}
    voice_id = voice.get("voice_id", "leo")     # named male documentary-ish voice
    language = voice.get("language", doc.get("language", "en"))
    speed = float(voice.get("speed", 1.0))

    clone_ref = voice.get("clone_ref")          # local audio sample -> clone this voice
    persona = voice.get("persona", "YouTube tutorial creator")
    backend = (voice.get("backend") or "atlas").strip().lower()
    if backend in ("javis", "local", "zero"):
        backend = "zerotts"

    # Clone giọng thật chỉ có trên Atlas seed-audio - ZeroTTS open-source không clone được.
    if clone_ref and backend == "zerotts":
        print("[narr] có clone_ref → bắt buộc Atlas seed-audio (ZeroTTS không clone)")
        backend = "atlas"

    if backend == "zerotts":
        try:
            _narrate_zerotts(doc, adir, voice)
        except Exception as e:
            print(f"[narr ZeroTTS] {type(e).__name__}: {e} → fallback Atlas xai/tts-v1")
            backend = "atlas"

    specs = {}
    if backend != "zerotts":
        if clone_ref:
            with open(clone_ref, "rb") as f:
                ref_b64 = base64.b64encode(f.read()).decode()
            lang_name = LANG_NAMES.get(language, language)
            for beat in doc["beats"]:
                specs[f"narr_{beat['id']}"] = (lambda t=beat["narration"]: prov.submit_audio(
                    CLONE_MODEL,
                    text=CLONE_TEMPLATE.format(language=lang_name, persona=persona, script=t),
                    format="mp3", sample_rate=44100,
                    references=[{"audio_data": ref_b64}]))
        else:
            for beat in doc["beats"]:
                specs[f"narr_{beat['id']}"] = (lambda t=beat["narration"]:
                    prov.submit_audio(
                        VOICE_MODEL, text=t, language=language, voice_id=voice_id,
                        codec="mp3", sample_rate=44100, speed=speed))

    # BGM: only generate if we don't already have one (it's slow + costs more).
    bgm_path = os.path.join(adir, "bgm.mp3")
    if not os.path.exists(bgm_path):
        music_prompt = doc.get("music", "cinematic majestic traditional Chinese guzheng erhu, warm")
        specs["bgm"] = (lambda mp=music_prompt: prov.submit_audio(
            MUSIC_MODEL, prompt=mp, is_instrumental=True, format="mp3"))
    else:
        print(f"[bgm] reuse existing {bgm_path}")

    done = {}
    if specs:
        done = run_jobs(prov, specs, poll_s=4, stall_s=150, max_retries=2, deadline_s=600)

    # download + record (Atlas narration and/or BGM)
    if backend != "zerotts":
        for beat in doc["beats"]:
            url = done.get(f"narr_{beat['id']}")
            if url:
                dest = os.path.join(adir, f"narr_{beat['id']}.mp3")
                prov.download(url, dest)
                beat["narration_audio"] = dest
                beat["narration_dur"] = round(probe_dur(dest), 2)
                beat["narration_backend"] = "atlas"
                print(f"[narr {beat['id']}] {beat['narration_dur']}s -> {dest}")
    bgm_url = done.get("bgm")
    if bgm_url:
        bgm = os.path.join(adir, "bgm.mp3")
        prov.download(bgm_url, bgm)
        doc["bgm_path"] = bgm
        doc["bgm_dur"] = round(probe_dur(bgm), 2)
        print(f"[bgm] {doc['bgm_dur']}s -> {bgm}")

    with open(bpath, "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("updated", bpath)


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "..", "out", "tang-30s")
    run(os.path.abspath(proj))
