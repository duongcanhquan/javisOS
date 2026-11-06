"""Session đăng nhập phải sống qua recreate / đọc lại từ ổ.

    python tests/run.py auth_session_persist
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from _paths import ROOT, SERVER  # noqa: E402,F401

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-sess-auth-")

import config as cfg  # noqa: E402

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


tok = cfg.new_session()
check("ghi .sessions.json ra ổ", cfg._SESS_PATH.is_file())
raw = json.loads(cfg._SESS_PATH.read_text(encoding="utf-8"))
check("token nằm trong file", tok in raw)

# Giả lập process mới: RAM trống, file còn.
cfg.SESSIONS = {}
check("valid_session đọc lại từ ổ sau khi RAM trống", cfg.valid_session(tok))
check("RAM được nạp lại từ ổ", tok in cfg.SESSIONS)

cfg.clear_sessions()
check("clear_sessions xoá file + RAM", not cfg.valid_session(tok))

main_src = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
cook = main_src.split("def _session_cookie", 1)[-1].split("def _env_bat", 1)[0]
check("Secure cookie nhận DOMAIN_NAME tenant", "DOMAIN_NAME" in cook)
login = main_src.split("async def auth_login", 1)[-1].split("@app.post", 1)[0]
check("login không phân biệt hoa thường tên", ".lower()" in login)

od = (ROOT / "server" / "org_docker.py").read_text(encoding="utf-8")
check("có helper giữ ổ cũ khi recreate", "def _tenant_core_binds" in od)
binds_fn = od.split("def _tenant_core_binds", 1)[-1].split("def apply_public_hosts", 1)[0]
check("ưu tiên Mounts đang gắn", "Mounts" in binds_fn and "volumes" in binds_fn)

if FAIL:
    print(f"\nFAIL - test_auth_session_persist: {len(FAIL)} lỗi: {FAIL}")
    sys.exit(1)
print("\nOK - test_auth_session_persist: tất cả pass")
