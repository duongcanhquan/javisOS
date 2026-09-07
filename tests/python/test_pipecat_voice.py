"""Fast-path giọng nói kiểu Pipecat: chốt lượt nhanh + TTS stream, không nhúng gói pipecat-ai.

    python tests/run.py pipecat_voice

Không chạm mạng. Không import main.py (nặng). Pipecat-ai KHÔNG được là dependency:
extra websocket của họ đòi fastapi>=0.115.6, Javis đang ghim 0.115.0.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import ast
import os
import sys
import tempfile

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-pipecat-")

import pipecat_voice as pv  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# ---- 1. Tắt fast_turn = hành vi cũ (1.9s), không cắt sớm ----
check("tắt fast_turn luôn 1900 dù đã hết câu",
      pv.silence_ms_for_turn("Xong chưa?", has_interim=False, fast_turn=False) == 1900)
check("chưa có chữ thì 1900 (tránh gửi vì tiếng động)",
      pv.silence_ms_for_turn("", has_interim=False, fast_turn=True) == 1900)
check("còn interim thì 1900 (tiếng Việt hay ngắt giữa cụm)",
      pv.silence_ms_for_turn("hôm nay mình", has_interim=True, fast_turn=True) == 1900)

# ---- 2. Câu đã rõ → chốt sớm ----
check("hết câu chấm hỏi → 400ms",
      pv.silence_ms_for_turn("Mấy giờ rồi?", has_interim=False, fast_turn=True) == 400)
check("hết câu chấm than → 400ms",
      pv.silence_ms_for_turn("Làm ngay!", has_interim=False, fast_turn=True) == 400)
check("hết câu chấm → 400ms",
      pv.silence_ms_for_turn("Xong rồi.", has_interim=False, fast_turn=True) == 400)
check("câu thường không dấu → 900ms",
      pv.silence_ms_for_turn("mở trang models", has_interim=False, fast_turn=True) == 900)
check("hằng SILENCE_THUONG = 900", pv.SILENCE_THUONG == 900)

# ---- 3. Cụm dở (liên từ) KHÔNG cắt sớm hơn đường cũ quá nhiều ----
check("kết bằng 'và' → 1400ms",
      pv.silence_ms_for_turn("viết giúp anh và", has_interim=False, fast_turn=True) == 1400)
check("kết bằng 'nhưng' → 1400ms",
      pv.silence_ms_for_turn("hay đấy nhưng", has_interim=False, fast_turn=True) == 1400)
check("kết bằng 'and' → 1400ms",
      pv.silence_ms_for_turn("open the file and", has_interim=False, fast_turn=True) == 1400)

# ---- 4. Gói pipecat-ai không phải dependency; module không import nó ----
src = (SERVER / "pipecat_voice.py").read_text(encoding="utf-8")
tree = ast.parse(src)
imports = []
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.extend(a.name.split(".")[0] for a in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
        imports.append(node.module.split(".")[0])
check("pipecat_voice.py không import pipecat", "pipecat" not in imports)
check("pipecat_voice.py không import fastapi", "fastapi" not in imports)
_req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
check("requirements.txt không cài pipecat-ai",
      not any(ln.strip().startswith("pipecat") for ln in _req.splitlines()
              if ln.strip() and not ln.strip().startswith("#")))
check("module không còn status()/want_stream (chết, không ai gọi)",
      "def status(" not in src and "def want_stream(" not in src)

# ---- 5. /tts?stream=1 là cờ FastAPI, mặc định tắt ----
import config as cfg  # noqa: E402
check("config._DEFAULT voice.fast_turn = True",
      (cfg._DEFAULT.get("voice") or {}).get("fast_turn") is True)
merged = cfg._deep_merge(cfg._DEFAULT, {"voice": {"tts_provider": "edge"}})
check("máy cũ thiếu fast_turn vẫn nhận True sau merge",
      (merged.get("voice") or {}).get("fast_turn") is True)

# ---- 7. /tts nhận stream= mà KHÔNG thêm path mới (bảng route không đổi) ----
_main = (SERVER / "main.py").read_text(encoding="utf-8")
check("/tts có stream: bool = Query(False)",
      "stream: bool = Query(False)" in _main)
check("Edge TTS có iterator khung (không đợi cả file khi stream)",
      "async def _tts_edge_iter" in _main)
check("voice.js trong index đã bump ?v=23",
      "voice.js?v=23" in (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8"))
check("/tts stream đợi khung đầu trước khi 200",
      "await pv.lay_khung_dau(agen)" in _main)
check("/tts không stream khi chưa có khung đầu",
      "Không có khung đầu" in _main)
check("đường file đủ không bọc StreamingResponse thừa",
      "_phat_mot" not in _main)

# ---- 8. lay_khung_dau: rỗng / lỗi = None, có data = khung đầu ----
import asyncio  # noqa: E402


async def _agen_rong():
    if False:
        yield b"x"


async def _agen_trong_roi_data():
    yield b""
    yield b"ID3"


async def _agen_data():
    yield b"frame-1"
    yield b"frame-2"


check("lay_khung_dau hết iterator → None",
      asyncio.run(pv.lay_khung_dau(_agen_rong())) is None)
check("lay_khung_dau bỏ khung rỗng, lấy khung có data",
      asyncio.run(pv.lay_khung_dau(_agen_trong_roi_data())) == b"ID3")
async def _kiem_con():
    agen = _agen_data()
    first = await pv.lay_khung_dau(agen)
    rest = [p async for p in agen]
    return first, rest


check("lay_khung_dau trả khung đầu, phần còn lại vẫn yield",
      asyncio.run(_kiem_con()) == (b"frame-1", [b"frame-2"]))

if _fails:
    print("FAIL", len(_fails), "checks:", "; ".join(_fails))
    sys.exit(1)
print("ok   all", "pipecat_voice")
