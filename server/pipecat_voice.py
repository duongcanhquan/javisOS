"""Fast-path giọng nói kiểu Pipecat, không cài gói pipecat-ai.

pipecat-ai[websocket] đòi fastapi>=0.115.6; Javis ghim 0.115.0 / starlette<0.39
vì claude-agent-sdk. Module này chỉ giữ bảng chốt câu + lấy khung TTS đầu.

Tắt voice.fast_turn = về 1.9s như cũ. Engine / MCP / Telegram / Zalo / họp không đi đây.
"""
from __future__ import annotations

SILENCE_CU = 1900       # chưa nói / còn interim / fast_turn tắt
SILENCE_DO = 1400       # kết bằng liên từ: câu chưa xong
SILENCE_THUONG = 900    # đã có chữ, chưa hết câu (Web Speech tiếng Việt ít dấu câu)
SILENCE_XONG = 400      # hết câu (.?!…)

# Liên từ / giới từ đứng cuối = người dùng còn nói tiếp. Khớp test_pipecat_voice.py.
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
