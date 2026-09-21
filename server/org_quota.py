"""Trần ổ Javis con. quota_gb=0 nghĩa là không trần (bản quan)."""
from __future__ import annotations

import os
from pathlib import Path

import config as cfgmod


def quota_bytes() -> int:
    gb = None
    marker = Path(cfgmod.STATE_DIR) / "org-quota"
    if marker.is_file():
        try:
            gb = int(marker.read_text(encoding="utf-8").strip() or "0")
        except (TypeError, ValueError):
            gb = 0
    elif os.getenv("JAVIS_QUOTA_GB"):
        try:
            gb = int(os.getenv("JAVIS_QUOTA_GB") or 0)
        except (TypeError, ValueError):
            gb = 0
    else:
        gb = 0
    if gb <= 0:
        return 0
    return gb * 1024 * 1024 * 1024


def _dir_bytes(root: Path) -> int:
    n = 0
    if not root.exists():
        return 0
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for fn in filenames:
                p = Path(dirpath) / fn
                try:
                    n += p.stat().st_size
                except OSError:
                    pass
    except OSError:
        return n
    return n


def used_bytes() -> int:
    brains = Path(os.getenv("BRAINS_DIR") or "/brains")
    return _dir_bytes(Path(cfgmod.STATE_DIR)) + _dir_bytes(brains)


def guard(extra: int = 0) -> str | None:
    cap = quota_bytes()
    if cap <= 0:
        return None
    used = used_bytes() + max(0, int(extra or 0))
    if used <= cap:
        return None
    gb = cap // (1024 * 1024 * 1024)
    return (f"Hết hạn mức ổ ({gb} GB). Xóa bớt file hoặc nhờ quản trị tăng trần.")
