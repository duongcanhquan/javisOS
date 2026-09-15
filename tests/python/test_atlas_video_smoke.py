"""Smoke offline: Atlas Cloud wiring (paperdesign) + catalog + script không gãy.

Không gọi mạng billable. Không cần ATLASCLOUD_API_KEY.

    python tests/run.py atlas_video_smoke
"""
from __future__ import annotations

import ast
import importlib.util
import sys

from _paths import ROOT, SERVER  # noqa: E402,F401

_fails: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


atlas_py = ROOT / ".claude" / "skills" / "paperdesign" / "scripts" / "atlas_cloud.py"
check("có atlas_cloud.py", atlas_py.is_file())

src = atlas_py.read_text(encoding="utf-8")
try:
    tree = ast.parse(src)
    check("atlas_cloud AST ok", True)
except SyntaxError as e:
    check(f"atlas_cloud AST ok ({e})", False)
    tree = None

names = {
    n.name for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
} if tree else set()
for fn in ("_key", "submit_image", "submit_video", "submit_media", "poll", "download", "chat"):
    check(f"atlas_cloud có {fn}", fn in names)

check("atlas_cloud đọc ATLASCLOUD_API_KEY", "ATLASCLOUD_API_KEY" in src)
check("atlas_cloud gửi User-Agent (WAF)", "User-Agent" in src or "vox-director" in src)

spec = importlib.util.spec_from_file_location("atlas_cloud_smoke", atlas_py)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["atlas_cloud_smoke"] = mod
try:
    spec.loader.exec_module(mod)
    check("import atlas_cloud offline", True)
except Exception as e:
    check(f"import atlas_cloud offline ({e})", False)
    mod = None

if mod is not None:
    try:
        mod._key()
        check("không có key → _key phải raise", False)
    except Exception as e:
        check("không có key → _key raise rõ ràng", "ATLASCLOUD_API_KEY" in str(e))

import tool_apis as ta  # noqa: E402
check("catalog có atlascloud", any(x.get("id") == "atlascloud" for x in ta.CATALOG))
item = ta.catalog_item("atlascloud")
check("atlascloud env đúng", (item or {}).get("env") == "ATLASCLOUD_API_KEY")

audio_py = ROOT / ".claude" / "skills" / "paperdesign" / "scripts" / "audio.py"
if audio_py.is_file():
    a = audio_py.read_text(encoding="utf-8")
    check("paperdesign audio dùng Atlas TTS xai/tts-v1", "xai/tts-v1" in a)
    check("paperdesign không đụng voice.tts_provider Javis", "tts_provider" not in a)
else:
    check("paperdesign audio.py tồn tại", False)

vid = (ROOT / "dashboard" / "video.js").read_text(encoding="utf-8")
check("video.js có pipeline paperdesign", "paperdesign" in vid)

sv = (SERVER / "script_video.py").read_text(encoding="utf-8")
check("script_video có nhánh ZeroTTS", "_tts_zerotts_to_file" in sv and "zerotts" in sv)
check("script_video vẫn fallback Edge", "_tts_edge_to_file" in sv)

if _fails:
    print("FAILED:", ", ".join(_fails))
    raise SystemExit(1)
print("ALL PASS")
