"""Hợp đồng deploy OpenMAIC: đọc Gemini key từ container Javis đúng cách.

Chạy: python tests/run.py openmaic_deploy_key

Bối cảnh (2026-09-08): 0.55.140 bắt buộc GOOGLE_API_KEY nhưng extract key fail vì
thiếu docker exec -i / JAVIS_STATE_DIR=/data/state / PYTHONPATH=/app/server.
"""
from _paths import ROOT  # noqa: E402,F401
import re
import sys

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


script = (ROOT / "scripts" / "vps-deploy-openmaic.sh").read_text(encoding="utf-8")
wf = (ROOT / ".github" / "workflows" / "deploy-openmaic-vps.yml").read_text(encoding="utf-8")

check(
    "script: docker exec -i khi đọc gemini key (heredoc)",
    re.search(r"docker exec -i .*python3", script) is not None,
)
check(
    "script: JAVIS_STATE_DIR=/data/state khi đọc key",
    "JAVIS_STATE_DIR=/data/state" in script,
)
check(
    "script: PYTHONPATH=/app/server hoặc sys.path.insert /app/server",
    "PYTHONPATH=/app/server" in script or 'sys.path.insert(0, "/app/server")' in script,
)
check(
    "script: không dùng from server.config khi đọc key",
    "from server.config import read_settings" not in script,
)
check(
    "script: fallback GOOGLE_API_KEY từ .env.local",
    re.search(r"Dùng lại GOOGLE_API_KEY", script) is not None,
)
check(
    "script: có nhánh SYNC_KEY_ONLY",
    "OPENMAIC_SYNC_KEY_ONLY" in script,
)
check(
    "workflow: truyền OPENMAIC_SYNC_KEY_ONLY",
    "OPENMAIC_SYNC_KEY_ONLY" in wf,
)
check(
    "workflow: mặc định ALLOW_NO_KEY=0 (generate cần key)",
    re.search(r"OPENMAIC_ALLOW_NO_KEY=0", wf) is not None,
)

if FAIL:
    print("FAILED:", ", ".join(FAIL))
    sys.exit(1)
print("all ok")
