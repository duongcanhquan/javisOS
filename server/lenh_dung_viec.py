"""Lệnh "dừng việc nền" là LỆNH, không phải một việc mới.

Chủ dự án gốc gặp vòng lặp: bảo "tạm dừng cái việc tìm kiếm ngầm đi nhé" thì model dạ rồi
GIAO THÊM một việc nền mang nội dung "dừng việc nền đang chạy". Nói lần nữa lại đẻ thêm một
cái nữa.

Chữa bằng luật CỨNG chứ không chỉ dặn model: nhận ra câu này thì huỷ ngay tại chỗ, không hỏi
model, không giao việc.

Ranh giới: phải có ĐỦ CẶP một từ DỪNG và một từ chỉ VIỆC ĐANG CHẠY NGẦM. Chỉ "dừng việc" thì
không tính, vì "dừng việc nhập liệu lại" là chuyện khác hẳn.
"""
from __future__ import annotations

import re

_DUNG_TU = (
    "dừng", "tạm dừng", "ngừng", "huỷ", "hủy", "bỏ", "tắt", "thôi", "dẹp", "khoan làm",
    "stop", "cancel", "abort", "kill", "halt",
)
_VIEC_TU = (
    "việc nền", "viec nen", "việc ngầm", "viec ngam", "chạy nền", "chay nen", "chạy ngầm",
    "ngầm", "ngam", "nền", "nen", "tác vụ", "tac vu", "đang chạy", "dang chay",
    "background", "task", "job",
)


def la_lenh_dung_viec(text: str) -> bool:
    """Câu này có phải là LỆNH dừng việc nền đang chạy không (thuần, test được)."""
    s = " " + re.sub(r"\s+", " ", str(text or "").lower().strip()) + " "
    if not s.strip():
        return False
    co_dung = any((" " + t + " ") in s or s.startswith(" " + t + " ") for t in _DUNG_TU)
    if not co_dung:
        return False
    return any(v in s for v in _VIEC_TU)


def cau_tra_loi(so_huy: int) -> str:
    if so_huy <= 0:
        return "Không có việc nền nào đang chạy."
    if so_huy == 1:
        return "Đã dừng việc đang chạy."
    return f"Đã dừng {so_huy} việc đang chạy."


def thu_huy(brain: str) -> str:
    """Huỷ việc Kanban đang chạy của brain; trả câu nói với người dùng."""
    import tasks as tasks_mod
    f = tasks_mod.current()
    if f is None:
        return cau_tra_loi(0)
    ids = f.huy_viec_dang_chay(brain)
    return cau_tra_loi(len(ids))
