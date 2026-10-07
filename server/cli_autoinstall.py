"""Trạng thái CLI mà container Docker tự cài lúc khởi động.

`docker/entrypoint.sh` cài Antigravity CLI (`agy`) và Grok Build (`grok`) ở nền khi máy chưa có,
và ghi một dòng vào `<JAVIS_HOME_PERSIST>/.cli-auto-install/<bin>`: `installing`, `ok` hoặc
`failed`. Module này chỉ ĐỌC file đó để trang Models nói "đang tự cài" thay vì đưa một lệnh
mà người cài qua Hostinger không có chỗ gõ.

Ngoài Docker thì thư mục không có, mọi câu trả lời là "" và đường cài tay giữ nguyên.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

# Cài dở (container bị tắt giữa chừng) không được hiện "đang cài" mãi.
STUCK_AFTER_S = 15 * 60


def state_dir() -> Path:
    return Path(os.getenv("JAVIS_HOME_PERSIST") or "/data/home") / ".cli-auto-install"


def state(binary: str) -> str:
    """"installing", "failed", "ok", hoặc "" khi container chưa từng thử."""
    try:
        raw = (state_dir() / binary).read_text(encoding="utf-8").split()
    except (OSError, ValueError):
        return ""
    if not raw:
        return ""
    word = raw[0]
    try:
        at = float(raw[1]) if len(raw) > 1 else 0.0
    except ValueError:
        at = 0.0
    if word == "installing":
        return "failed" if at and time.time() - at > STUCK_AFTER_S else "installing"
    return word if word in ("ok", "failed") else ""


def log_path() -> str:
    return str(state_dir() / "install.log")
