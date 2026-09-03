"""Trả lời xã giao tức thì - không gọi model / CLI.

Ca đau: "xin chào" qua Antigravity/Claude CLI mất vài chục giây vì spawn process + nạp
tool, trong khi người dùng chỉ muốn một câu chào lại. Classifier đường tắt đã nhận diện
nhóm conversation, nhưng đường tắt với CLI vẫn gọi engine - chưa đủ nhẹ cho giao tiếp.

Chỉ bắt câu XÃ GIAO THUẦN (toàn bộ tin nhắn là chào/cảm ơn). "Xin chào, hôm nay doanh thu?"
không khớp → vẫn đi engine đầy đủ.
"""
from __future__ import annotations

import re
import unicodedata


def _norm(value: str) -> str:
    raw = str(value or "").replace("đ", "d").replace("Đ", "D")
    raw = unicodedata.normalize("NFKD", raw.casefold())
    return " ".join("".join(c for c in raw if not unicodedata.combining(c)).split())


# Toàn câu là chào / cảm ơn (+ dấu câu / emoji đơn giản). Không cho mệnh đề phụ.
_CHAO = re.compile(
    r"^(xin\s+chao|chao(\s+ban)?|hello|hi|hey)"
    r"([\s!?.…💕🙏😊]*|(\s+ban)?[\s!?.…]*)$"
)
_CAM_ON = re.compile(
    r"^(cam\s+on(\s+ban)?|thanks?(?:\s+you)?)"
    r"([\s!?.…💕🙏😊]*)$"
)


def try_reply(text, ten_tro_ly="Javis"):
    """Trả câu đáp sẵn nếu là xã giao thuần; None = để engine xử lý."""
    raw = (text or "").strip()
    if not raw or len(raw) > 64:
        return None
    # Có xuống dòng / danh sách → không phải chào xã giao.
    if "\n" in raw or raw.count("?") > 1:
        return None
    n = _norm(raw)
    # Còn chữ nội dung sau phần chào (vd "xin chao, bao cao giup") → None.
    ten = (ten_tro_ly or "Javis").strip() or "Javis"
    if _CAM_ON.match(n):
        return f"Không có gì ạ. Cần {ten} giúp gì tiếp cứ nói nhé."
    if _CHAO.match(n):
        return f"Chào bạn. Mình là {ten}, sẵn sàng hỗ trợ."
    return None
