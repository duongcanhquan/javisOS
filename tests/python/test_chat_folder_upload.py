"""Upload thư mục máy vào staging chat."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

import chat_upload_limits as cul


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        raise SystemExit(1)


check("sanitize ok", cul.sanitize_relpath("docs/a.md") == "docs/a.md")
check("sanitize slash", cul.sanitize_relpath("/docs/a.md") == "docs/a.md")
check("sanitize win", cul.sanitize_relpath(r"docs\\a.md") == "docs/a.md")
check("reject ..", cul.sanitize_relpath("../x") is None)
check("reject nested ..", cul.sanitize_relpath("a/../b") is None)
check("folder caps", cul.FOLDER_MAX_FILES == 50 and cul.FOLDER_MAX_TOTAL_BYTES == 100 * 1024 * 1024)

# API
import atexit
import shutil
_TMP = ROOT / ".tmp-folder-upload-test"
os.environ.setdefault("JAVIS_STATE_DIR", str(_TMP))
atexit.register(lambda: shutil.rmtree(_TMP, ignore_errors=True))
from fastapi.testclient import TestClient
import main as m

client = TestClient(m.app, base_url="http://127.0.0.1")
r = client.post(
    "/upload/folder",
    files=[
        ("files", ("note.md", io.BytesIO(b"# hello\n"), "text/markdown")),
        ("files", ("x.txt", io.BytesIO(b"body"), "text/plain")),
        ("relpaths", (None, "docs/note.md")),
        ("relpaths", (None, "docs/sub/x.txt")),
        ("folder_name", (None, "TaiLieu")),
        ("brain", (None, "Brain Default")),
    ],
)
print("status", r.status_code, r.text[:500])
assert r.status_code == 200, r.text
body = r.json()
check("ok", body.get("ok") is True)
check("2 files", len(body.get("files") or []) == 2)
check("root exists", Path(body["root"]).is_dir())
check("nested written", (Path(body["root"]) / "docs" / "sub" / "x.txt").is_file())
check("name", body.get("name") == "TaiLieu")

# reject path escape
bad = client.post(
    "/upload/folder",
    files=[
        ("files", ("x.md", io.BytesIO(b"x"), "text/markdown")),
        ("relpaths", (None, "../escape.md")),
        ("folder_name", (None, "bad")),
    ],
)
bj = bad.json()
check("escape skipped or fail", bj.get("ok") is False or (bj.get("skipped") and not bj.get("files")))

print("TẤT CẢ PASS")
