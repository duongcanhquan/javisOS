"""Fast-path giọng nói theo kiến trúc Pipecat, KHÔNG nhúng gói pipecat-ai.

Pipecat (https://github.com/pipecat-ai/pipecat) xếp VAD -> STT stream -> LLM -> TTS stream
để tới loa ~500-800ms. Nhúng `pipecat-ai` vào cùng process Javis thì GÃY pin:

  pipecat-ai[websocket] đòi fastapi>=0.115.6
  Javis ghim fastapi==0.115.0 và starlette<0.39 vì claude-agent-sdk

Module này lấy đúng hai đòn của Pipecat mà không kéo dependency:

  1. Smart turn: im lặng sau câu đã rõ ngắn hơn 1.9s; cụm dở / interim giữ 1.9s.
  2. TTS stream: Edge TTS vốn đã yield từng khung - /tts?stream=1 phát ngay, không
     đợi cả file MP3. Server chỉ stream sau khi có khung đầu (tránh HTTP 200 rỗng).

Engine (Claude/Codex/MCP/skill) không đụng. Chat chữ, Telegram, Zalo, cuộc họp không
đi qua đây. Tắt `voice.fast_turn` là về đúng hành vi cũ.
"""
from __future__ import annotations

SILENCE_CU = 1900       # chưa nói / còn interim / fast_turn tắt - giữ như voice.js cũ
SILENCE_DO = 1400       # kết bằng liên từ: câu chưa xong
SILENCE_THUONG = 900    # đã có chữ, chưa hết câu (Web Speech tiếng Việt ít dấu câu)
SILENCE_XONG = 400      # hết câu (.?!…)

# Liên từ / giới từ đứng cuối = người dùng còn nói tiếp. Khớp bảng test_pipecat_voice.py.
_CUM_DO = frozenset({
    "và", "thì", "là", "mà", "nhưng", "hoặc", "với", "của", "để", "nếu", "vì", "nên",
    "khi", "trong", "từ", "tới", "đến", "về", "tại", "như", "cũng",
    "and", "or", "but", "the", "a", "an", "to", "of", "in", "with", "for", "if", "when",
})


def _chu_cuoi(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    cuoi = t.split()[-1]
    return cuoi.strip(".,!?;:\"'()[]{}").lower()


def _het_cau(text: str) -> bool:
    t = (text or "").rstrip()
    if not t:
        return False
    return t[-1] in ".!?…。？！" or (len(t) >= 2 and t[-1] in "\"')" and t[-2] in ".!?…。？！")


def silence_ms_for_turn(text: str, has_interim: bool = False, fast_turn: bool = True) -> int:
    """Ms chờ im lặng trước khi chốt câu. Giữ 1900 khi chưa chắc đã nói xong."""
    if not fast_turn:
        return SILENCE_CU
    if has_interim:
        return SILENCE_CU
    t = (text or "").strip()
    if not t:
        return SILENCE_CU
    if _chu_cuoi(t) in _CUM_DO:
        return SILENCE_DO
    if _het_cau(t):
        return SILENCE_XONG
    return SILENCE_THUONG


async def lay_khung_dau(agen):
    """Lấy khung audio đầu từ iterator. None = không stream được, đi đường file đủ."""
    async for part in agen:
        if part:
            return part
    return None


def want_stream(params) -> bool:
    """Cờ /tts?stream=1. Mặc định tắt - OpenMAIC và client cũ không đổi."""
    if not params:
        return False
    raw = params.get("stream")
    if raw is True:
        return True
    if raw is False or raw is None:
        return False
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def status() -> dict:
    return {
        "ok": True,
        "engine": "javis-fastpath",
        "pipecat_package": False,
        "ly_do": (
            "Không cài pipecat-ai trong venv Javis: extra websocket đòi fastapi>=0.115.6, "
            "Javis ghim fastapi==0.115.0 / starlette<0.39 vì Agent SDK."
        ),
        "fast_turn": True,
        "tts_stream": True,
    }
