"""ZeroTTS provider: optional, lazy, fallback-safe. Không tải weights, không mạng.

    python tests/run.py zerotts_tts
"""
from __future__ import annotations

import asyncio
import importlib
import sys
import types
from pathlib import Path
from _paths import ROOT, SERVER  # noqa: E402,F401

sys.path.insert(0, str(SERVER))

_fails: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ---- module tồn tại, không kéo zerotts lúc import ----
import zerotts_tts as zt  # noqa: E402

zt.reset_engine_for_tests()
check("import zerotts_tts không kéo package zerotts", "zerotts" not in sys.modules)
check("available() False khi chưa cài", zt.available() is False)
st = zt.status()
check("status() có available/voices/default_voice",
      st.get("available") is False and len(st.get("voices") or []) >= 8
      and st.get("default_voice") == "maichi")
check("preset maichi nằm trong list",
      any(v.get("id") == "maichi" for v in zt.preset_voices()))

# ---- synthesize thiếu gói → raise rõ ràng (caller /tts sẽ fallback Edge) ----
try:
    asyncio.run(zt.synthesize("Xin chào", voice="maichi"))
    raised = False
    err = ""
except Exception as e:
    raised = True
    err = str(e)
check("synthesize thiếu gói thì raise", raised)
check("lỗi gợi ý pip install zerotts", "pip install zerotts" in err)

# ---- mock package: WAV hợp lệ, không đụng HF ----
fake = types.ModuleType("zerotts")


class _FakeEngine:
    sample_rate = 16000

    @classmethod
    def from_pretrained(cls, _repo):
        return cls()

    def synthesize(self, text, voice=None, **_kw):
        n = max(160, int(self.sample_rate * 0.05))
        if n == 1:
            return [0.0]
        step = 0.4 / (n - 1)
        return [-0.2 + i * step for i in range(n)]


fake.ZeroTTS = _FakeEngine
fake.normalize_vi_text = lambda s: s
sys.modules["zerotts"] = fake
sys.modules["zerotts.chunking"] = types.ModuleType("zerotts.chunking")
sys.modules["zerotts.chunking"].chunk_text = lambda t, max_chunk_sec=15: [t]
sys.modules["zerotts.chunking"].clean_segment_punctuation = lambda s: s
sys.modules["zerotts.chunking"].normalize_punctuation = lambda s: s

zt.reset_engine_for_tests()
check("available() True khi mock package", zt.available() is True)
audio, media = asyncio.run(zt.synthesize("Xin chào ZeroTTS.", voice="maichi"))
check("synthesize mock trả WAV", media == "audio/wav" and audio[:4] == b"RIFF")
check("WAV đủ dài", len(audio) > 44)

# ---- config + main wiring (không import main nặng nếu có thể: đọc source) ----
cfg_src = (SERVER / "config.py").read_text(encoding="utf-8")
check("config mặc định tts_provider=edge", '"tts_provider": "edge"' in cfg_src)
check("config có zerotts_voice", '"zerotts_voice"' in cfg_src)
check("requirements.txt KHÔNG ghim zerotts",
      not any(ln.strip().startswith("zerotts") for ln in
              (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
              if ln.strip() and not ln.strip().startswith("#")))

main_src = (SERVER / "main.py").read_text(encoding="utf-8")
check("main cho phép tts_provider=zerotts", '"zerotts"' in main_src and "tts_provider" in main_src)
check("main có nhánh _tts_zerotts", "async def _tts_zerotts" in main_src)
check("main trả media_type động (WAV)", "media_type=media" in main_src)
check("main không import zerotts ở top-level",
      "import zerotts" not in "\n".join(main_src.splitlines()[:120]))
check("main lazy import zerotts_tts trong helper",
      "import zerotts_tts" in main_src)

# UI + i18n
console = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")
check("console có option zerotts", 'opt("zerotts"' in console or "\"zerotts\"" in console)
check("console lưu zerotts_voice", "zerotts_voice" in console)
vi = (ROOT / "dashboard" / "i18n" / "vi.json").read_text(encoding="utf-8")
en = (ROOT / "dashboard" / "i18n" / "en.json").read_text(encoding="utf-8")
check("i18n vi có tts_zerotts", "settings.tts_zerotts" in vi)
check("i18n en có tts_zerotts", "settings.tts_zerotts" in en)

# dọn mock để không làm bẩn tiến trình test runner
for k in list(sys.modules):
    if k == "zerotts" or k.startswith("zerotts."):
        del sys.modules[k]
zt.reset_engine_for_tests()


# ---- script_video tôn trọng tts_provider=zerotts (mock, không ffmpeg nếu dest .wav) ----
import script_video as sv  # noqa: E402
import types as _types

# gắn lại mock package (đã xoá ở trên) — tạo lại tối thiểu
_fake2 = _types.ModuleType("zerotts")

class _FakeEngine2:
    sample_rate = 16000
    @classmethod
    def from_pretrained(cls, _repo):
        return cls()
    def synthesize(self, text, voice=None, **_kw):
        n = max(160, int(self.sample_rate * 0.05))
        step = 0.4 / max(1, n - 1)
        return [-0.2 + i * step for i in range(n)]

_fake2.ZeroTTS = _FakeEngine2
_fake2.normalize_vi_text = lambda s: s
sys.modules["zerotts"] = _fake2
sys.modules["zerotts.chunking"] = _types.ModuleType("zerotts.chunking")
sys.modules["zerotts.chunking"].chunk_text = lambda t, max_chunk_sec=15: [t]
sys.modules["zerotts.chunking"].clean_segment_punctuation = lambda s: s
sys.modules["zerotts.chunking"].normalize_punctuation = lambda s: s
zt.reset_engine_for_tests()

_orig_voice = sv._voice_settings
sv._voice_settings = lambda: {"tts_provider": "zerotts", "zerotts_voice": "maichi"}
_called = {"edge": 0, "zt": 0}
_orig_edge = sv._tts_edge_to_file
_orig_zt = sv._tts_zerotts_to_file

async def _edge_spy(text, dest, voice):
    _called["edge"] += 1
    dest.write_bytes(b"ID3edge")

async def _zt_spy(text, dest, voice_cfg):
    _called["zt"] += 1
    # dùng đường thật tới WAV để kiểm synthesize
    await _orig_zt(text, dest.with_suffix(".wav"), voice_cfg)
    dest.write_bytes(dest.with_suffix(".wav").read_bytes()[:4] and b"ID3zt" or b"x")

sv._tts_edge_to_file = _edge_spy
# Gọi _tts_zerotts_to_file thật với dest .wav để khỏi cần ffmpeg
async def _run():
    out = Path(tempfile.mkdtemp()) / "a.wav"
    await sv._tts_file("Xin chào video.", out, "vi-VN-HoaiMyNeural")
    return out
import tempfile
out = asyncio.run(_run())
check("script_video provider=zerotts không gọi Edge", _called["edge"] == 0 and out.is_file() and out.stat().st_size > 44)
sv._voice_settings = lambda: {"tts_provider": "edge"}
async def _run_edge():
    out2 = Path(tempfile.mkdtemp()) / "b.mp3"
    await sv._tts_file("Hello", out2, "vi-VN-HoaiMyNeural")
    return out2
out2 = asyncio.run(_run_edge())
check("script_video provider=edge đi Edge spy", _called["edge"] == 1 and out2.read_bytes() == b"ID3edge")
sv._voice_settings = _orig_voice
sv._tts_edge_to_file = _orig_edge
sv._tts_zerotts_to_file = _orig_zt
for k in list(sys.modules):
    if k == "zerotts" or k.startswith("zerotts."):
        del sys.modules[k]
zt.reset_engine_for_tests()

if _fails:
    print("FAILED:", ", ".join(_fails))
    sys.exit(1)
print("ALL OK")
