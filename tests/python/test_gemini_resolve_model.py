"""gemini_resolve_model: Google ngừng 2.5-flash với user mới → đổi sang 3.6-flash.

Chạy: .venv/bin/python tests/python/test_gemini_resolve_model.py
"""
import tempfile
import os

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-gemini-map-"))

from _paths import SERVER  # noqa: E402,F401
import engine  # noqa: E402

fails = []


def check(name, cond):
    print(("PASS: " if cond else "FAIL: ") + name)
    if not cond:
        fails.append(name)


check("mặc định trống", engine.gemini_resolve_model(None) == "gemini-3.6-flash")
check("mặc định ''", engine.gemini_resolve_model("") == "gemini-3.6-flash")
check("2.5-flash → 3.6", engine.gemini_resolve_model("gemini-2.5-flash") == "gemini-3.6-flash")
check("models/ prefix",
      engine.gemini_resolve_model("models/gemini-2.5-flash") == "gemini-3.6-flash")
check("2.5-pro → 3.1-pro-preview",
      engine.gemini_resolve_model("gemini-2.5-pro") == "gemini-3.1-pro-preview")
check("giữ 3.6-flash", engine.gemini_resolve_model("gemini-3.6-flash") == "gemini-3.6-flash")

if fails:
    raise SystemExit(f"{len(fails)} FAIL: {fails}")
print("ALL PASS")
