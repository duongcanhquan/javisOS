"""Trần file đính kèm trong chat. Kho file trong não không đi qua đây."""
from __future__ import annotations

import os
import re

DOC_MAX = 3
IMG_MAX = 4
DOC_BYTES = 15 * 1024 * 1024
IMG_BYTES = 8 * 1024 * 1024
IMG_EXTS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"})

# Thư mục máy (nút folder cạnh đính kèm): trần riêng, không dùng DOC_MAX=3.
FOLDER_MAX_FILES = 50
FOLDER_MAX_TOTAL_BYTES = 100 * 1024 * 1024
FOLDER_NOTE = (
    "Mỗi thư mục: tối đa 50 file, tổng 100 MB "
    "(mỗi tài liệu ≤15 MB, mỗi ảnh ≤8 MB)."
)

NOTE = "Mỗi lượt: tối đa 3 file tài liệu (15 MB mỗi file) và 4 ảnh (8 MB mỗi ảnh)."

_SAFE_SEG = re.compile(r"^[^\x00/\\]+$")


def sanitize_relpath(rel: str) -> str | None:
    """Chuẩn hoá đường dẫn tương đối trong folder upload. None nếu không an toàn."""
    raw = (rel or "").replace("\\", "/").strip().lstrip("/")
    if not raw or raw.startswith("../") or "/../" in f"/{raw}/" or raw == "..":
        return None
    parts = [p for p in raw.split("/") if p and p != "."]
    if not parts or any(p == ".." for p in parts):
        return None
    out = []
    for p in parts:
        if not _SAFE_SEG.match(p):
            return None
        # Giữ Unicode; bỏ ký tự điều khiển đã chặn ở trên.
        out.append(p)
    return "/".join(out)


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
