"""Paperdesign audio: backend ZeroTTS opt-in, mặc định Atlas; không mạng.

    python tests/run.py paperdesign_zerotts_narr
"""
from __future__ import annotations

import ast
import json
import sys
import tempfile
import types
from pathlib import Path

from _paths import ROOT, SERVER  # noqa: E402,F401

_fails: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


audio_py = ROOT / ".claude" / "skills" / "paperdesign" / "scripts" / "audio.py"
check("có audio.py", audio_py.is_file())
src = audio_py.read_text(encoding="utf-8")
check("audio.py parse được", True)
try:
    ast.parse(src)
except SyntaxError as e:
    check(f"audio.py AST ({e})", False)

check("hỗ trợ voice.backend=zerotts", 'backend == "zerotts"' in src or "backend == 'zerotts'" in src)
check("có _narrate_zerotts", "_narrate_zerotts" in src)
check("fallback Atlas khi ZeroTTS lỗi", "fallback" in src.lower())
check("clone_ref buộc Atlas", "clone_ref" in src and "không clone" in src.lower())

# UI
vid = (ROOT / "dashboard" / "video.js").read_text(encoding="utf-8")
check("UI có vidNarrBackend", "vidNarrBackend" in vid)
check("UI có option zerotts", 'value: "zerotts"' in vid)
check("composeBrief ép beats voice.backend", "backend\":\"zerotts\"" in vid or 'backend":"zerotts"' in vid)

# Runtime mock (không ffmpeg/Atlas)
sys.path.insert(0, str(audio_py.parent))
sys.path.insert(0, str(SERVER))

import provider as provmod  # noqa: E402

class _FakeProv:
    def submit_audio(self, *a, **k):
        raise AssertionError("Atlas submit_audio không được gọi khi ZeroTTS ok + đã có bgm")
    def download(self, *a, **k):
        pass

provmod.get_provider = lambda name=None: _FakeProv()
provmod.run_jobs = lambda *a, **k: {}

fake = types.ModuleType("zerotts")
class _Eng:
    sample_rate = 16000
    @classmethod
    def from_pretrained(cls, *a, **k):
        return cls()
    def synthesize(self, text, voice=None, **k):
        n = max(160, int(self.sample_rate * 0.05))
        return [0.05] * n
fake.ZeroTTS = _Eng
fake.normalize_vi_text = lambda s: s
sys.modules["zerotts"] = fake
sys.modules["zerotts.chunking"] = types.ModuleType("zerotts.chunking")
sys.modules["zerotts.chunking"].chunk_text = lambda t, max_chunk_sec=15: [t]
sys.modules["zerotts.chunking"].clean_segment_punctuation = lambda s: s
sys.modules["zerotts.chunking"].normalize_punctuation = lambda s: s

import zerotts_tts as ztts  # noqa: E402
if hasattr(ztts, "reset_engine_for_tests"):
    ztts.reset_engine_for_tests()

import audio as au  # noqa: E402
au._wav_to_mp3 = lambda wav, mp3, speed=1.0: Path(mp3).write_bytes(b"ID3" + b"\0" * 200)

td = Path(tempfile.mkdtemp(prefix="pd-zt-"))
(td / "audio").mkdir()
(td / "audio" / "bgm.mp3").write_bytes(b"ID3bgm")
doc = {
    "voice": {"backend": "zerotts", "voice_id": "maichi", "language": "vi", "speed": 1.0},
    "beats": [
        {"id": "b1", "narration": "Xin chào từ ZeroTTS."},
        {"id": "b2", "narration": "Collage giấy dùng giọng local."},
    ],
}
(td / "beats.json").write_text(json.dumps(doc), encoding="utf-8")
au.run(str(td))
out = json.loads((td / "beats.json").read_text(encoding="utf-8"))
check("beat dùng narration_backend=zerotts", out["beats"][0].get("narration_backend") == "zerotts")
check("file narr mp3 tồn tại", Path(out["beats"][0]["narration_audio"]).is_file())

if _fails:
    print("FAILED:", ", ".join(_fails))
    raise SystemExit(1)
print("ALL PASS")
