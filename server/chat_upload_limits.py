"""Trần file đính kèm trong chat. Kho file trong não không đi qua đây."""
from __future__ import annotations

import os

DOC_MAX = 3
IMG_MAX = 4
DOC_BYTES = 15 * 1024 * 1024
IMG_BYTES = 8 * 1024 * 1024
IMG_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"})

NOTE = "Mỗi lượt: tối đa 3 file tài liệu (15 MB mỗi file) và 4 ảnh (8 MB mỗi ảnh)."


class QuaTran(Exception):
    """File vượt trần byte. message là câu hiện cho người dùng."""


def la_anh(name: str) -> bool:
    ext = os.path.splitext(name or "")[1].lower()
    return ext in IMG_EXTS


def tran_byte(name: str) -> int:
    return IMG_BYTES if la_anh(name) else DOC_BYTES


def loi_qua_tran(name: str) -> str:
    if la_anh(name):
        return "Ảnh này nặng hơn 8 MB."
    return "File này nặng hơn 15 MB."


def loi_kich_thuoc(name: str, size: int | None) -> str | None:
    if size is None:
        return None
    try:
        n = int(size)
    except (TypeError, ValueError):
        return None
    if n > tran_byte(name):
        return loi_qua_tran(name)
    return None
