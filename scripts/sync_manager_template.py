#!/usr/bin/env python3
"""CLI host: promote / sync manager template → tenants.

Chạy trên VPS (có docker):

  # 1) Đưa chuẩn từ quan vào manager (một lần)
  python scripts/sync_manager_template.py --promote-from javis-quan

  # 2) Đồng bộ manager → mọi tenant
  python scripts/sync_manager_template.py --sync

  # Dry-run
  python scripts/sync_manager_template.py --sync --dry-run
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))

import manager_template_sync as m  # noqa: E402


if __name__ == "__main__":
    # Default to --sync when no action flags (ops convenience)
    argv = sys.argv[1:]
    if not argv:
        argv = ["--sync"]
    elif not any(a in ("--sync", "--promote-from", "--src") or a.startswith("--promote-from=") for a in argv):
        if "--help" not in argv and "-h" not in argv:
            argv = ["--sync", *argv]
    raise SystemExit(m.main(argv))
