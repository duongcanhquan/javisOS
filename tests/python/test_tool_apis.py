"""Kho khóa API dịch vụ (Atlas, xAI, Tavily, khóa tự thêm).

    python tests/python/test_tool_apis.py
"""
from _paths import ROOT, SERVER, DASHBOARD  # noqa: E402,F401
import os

import config as cfgmod
import tool_apis as ta

fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


# ---- catalog ----
ids = [x["id"] for x in ta.CATALOG]
check("có ô Atlas Cloud", "atlascloud" in ids and ta.catalog_item("atlascloud")["env"] == "ATLASCLOUD_API_KEY")
check("có ô xAI", "xai" in ids)
check("có ô Tavily", "tavily" in ids)
check("có ô Kling", "video_kling" in ids and ta.catalog_item("video_kling")["env"] == "VIDEO_KLING_API_KEY")
check("có ô Seedream", "image_seedream" in ids)
check("có ô Firecrawl", "firecrawl" in ids and ta.catalog_item("firecrawl")["env"] == "FIRECRAWL_KEY")
check("không ô ElevenLabs (đã có Cài đặt)", "elevenlabs" not in ids)
check("có ô Google Maps", "google_maps" in ids)
check("nhóm có image/voice/maps", {g["id"] for g in ta.GROUPS} >= {"video", "image", "search", "voice", "maps", "custom"})
check("catalog không em dash", all("\u2014" not in str(x) for x in ta.CATALOG))

# ---- mutate ----
cfg = {"tool_apis": {"keys": {}}}
ta.mutate(cfg, "set", id="atlascloud", key="sk-atlas-123456")
check("lưu Atlas vào settings", cfg["tool_apis"]["keys"]["atlascloud"] == "sk-atlas-123456")
try:
    ta.mutate(cfg, "set", id="atlascloud", key="••••1234")
    check("từ chối bản che ••••", False)
except ta.ToolApiError:
    check("từ chối bản che ••••", True)

try:
    ta.mutate(cfg, "set", id="khong-co", key="abc")
    check("từ chối id lạ", False)
except ta.ToolApiError:
    check("từ chối id lạ", True)

try:
    ta.mutate(cfg, "set_custom", env="PATH", key="x")
    check("cấm PATH", False)
except ta.ToolApiError:
    check("cấm PATH", True)

try:
    ta.mutate(cfg, "set_custom", env="JAVIS_ADMIN_PASSWORD", key="x")
    check("cấm JAVIS_", False)
except ta.ToolApiError:
    check("cấm JAVIS_", True)

try:
    ta.mutate(cfg, "set_custom", env="ATLASCLOUD_API_KEY", key="x")
    check("cấm trùng env catalog", False)
except ta.ToolApiError:
    check("cấm trùng env catalog", True)

try:
    ta.mutate(cfg, "set_custom", env="FIRECRAWL_API_KEY", key="x")
    check("cấm trùng also_env catalog", False)
except ta.ToolApiError:
    check("cấm trùng also_env catalog", True)

try:
    ta.mutate(cfg, "set_custom", env="ELEVENLABS_API_KEY", key="x")
    check("cấm trùng Cài đặt ElevenLabs", False)
except ta.ToolApiError:
    check("cấm trùng Cài đặt ElevenLabs", True)

try:
    ta.mutate(cfg, "set_custom", env="OPENAI_API_KEY", key="x")
    check("cấm trùng Models OpenAI", False)
except ta.ToolApiError:
    check("cấm trùng Models OpenAI", True)

ta.mutate(cfg, "set_custom", env="MY_VIDEO_API_KEY", key="secret-zz")
check("thêm khóa tự đặt", cfg["tool_apis"]["keys"]["MY_VIDEO_API_KEY"] == "secret-zz")

# ---- view không lộ khóa ----
v = ta.view(cfg)
blob = str(v)
check("view không chứa khóa Atlas đầy đủ", "sk-atlas-123456" not in blob)
check("view không chứa khóa custom đầy đủ", "secret-zz" not in blob)
atlas = next(x for x in v["items"] if x["id"] == "atlascloud")
check("view Atlas set=True + suffix", atlas["set"] is True and atlas["suffix"] == "3456")
check("view có custom MY_VIDEO_API_KEY", any(c["env"] == "MY_VIDEO_API_KEY" for c in v["custom"]))

ta.mutate(cfg, "clear", id="atlascloud")
check("xoá Atlas", "atlascloud" not in cfg["tool_apis"]["keys"])
ta.mutate(cfg, "clear_custom", env="MY_VIDEO_API_KEY")
check("xoá custom", "MY_VIDEO_API_KEY" not in cfg["tool_apis"]["keys"])

# ---- inject env ----
old = os.environ.get("ATLASCLOUD_API_KEY")
old_fc = os.environ.get("FIRECRAWL_KEY")
old_fc2 = os.environ.get("FIRECRAWL_API_KEY")
try:
    os.environ.pop("ATLASCLOUD_API_KEY", None)
    os.environ.pop("FIRECRAWL_KEY", None)
    os.environ.pop("FIRECRAWL_API_KEY", None)
    cfg2 = {"tool_apis": {"keys": {"atlascloud": "sk-live-9999", "firecrawl": "fc-live-8888"}}}
    owned = ta.inject(cfg2)
    check("inject đặt ATLASCLOUD_API_KEY", os.environ.get("ATLASCLOUD_API_KEY") == "sk-live-9999")
    check("inject trả tên biến đã đặt", "ATLASCLOUD_API_KEY" in owned)
    check("inject Firecrawl chính", os.environ.get("FIRECRAWL_KEY") == "fc-live-8888")
    check("inject Firecrawl alias", os.environ.get("FIRECRAWL_API_KEY") == "fc-live-8888" and "FIRECRAWL_API_KEY" in owned)
finally:
    for ten, cu in (("ATLASCLOUD_API_KEY", old), ("FIRECRAWL_KEY", old_fc), ("FIRECRAWL_API_KEY", old_fc2)):
        if cu is None:
            os.environ.pop(ten, None)
        else:
            os.environ[ten] = cu

old3 = os.environ.get("ATLASCLOUD_API_KEY")
try:
    os.environ["ATLASCLOUD_API_KEY"] = "from-docker-keep"
    owned_skip = ta.inject({"tool_apis": {"keys": {"atlascloud": "from-page-new"}}})
    check("không ghi đè env đã có", os.environ.get("ATLASCLOUD_API_KEY") == "from-docker-keep")
    check("bỏ qua thì không owned", "ATLASCLOUD_API_KEY" not in owned_skip)
    os.environ.pop("ATLASCLOUD_API_KEY", None)
    cfg_up = {"tool_apis": {"keys": {"atlascloud": "from-page-1"}}}
    owned_1 = ta.inject(cfg_up)
    check("env trống thì bơm từ trang", os.environ.get("ATLASCLOUD_API_KEY") == "from-page-1")
    owned_2 = ta.inject({"tool_apis": {"keys": {"atlascloud": "from-page-2"}}}, duoc_ghi_de=owned_1)
    check("đã owned thì cập nhật được", os.environ.get("ATLASCLOUD_API_KEY") == "from-page-2" and "ATLASCLOUD_API_KEY" in owned_2)
finally:
    if old3 is None:
        os.environ.pop("ATLASCLOUD_API_KEY", None)
    else:
        os.environ["ATLASCLOUD_API_KEY"] = old3

# ---- apply_tool_env gọi inject + gỡ khi xoá ----
old2 = os.environ.get("TAVILY_API_KEY")
try:
    os.environ.pop("TAVILY_API_KEY", None)
    cfgmod._TOOL_ENV_OWNED = set()
    cfgmod.apply_tool_env({"voice": {}, "tool_apis": {"keys": {"tavily": "tvly-test-aaaa"}}})
    check("apply_tool_env bơm Tavily", os.environ.get("TAVILY_API_KEY") == "tvly-test-aaaa")
    cfgmod.apply_tool_env({"voice": {}, "tool_apis": {"keys": {}}})
    check("xoá key thì gỡ env đã owned", os.environ.get("TAVILY_API_KEY") in (None, ""))
finally:
    if old2 is None:
        os.environ.pop("TAVILY_API_KEY", None)
    else:
        os.environ["TAVILY_API_KEY"] = old2
    cfgmod._TOOL_ENV_OWNED = set()

# ---- canary dây nguồn ----
check("mã hoá tool_apis.keys.*", "tool_apis.keys.*" in cfgmod._SECRET_PATHS)
src_main = (SERVER / "main.py").read_text(encoding="utf-8")
check("có GET /tool-apis", '@app.get("/tool-apis")' in src_main)
check("có POST /tool-apis", '@app.post("/tool-apis")' in src_main)
check("GET /settings che tool_apis", "keys_set" in src_main and "tool_apis" in src_main)

console = (DASHBOARD / "console.js").read_text(encoding="utf-8")
html = (DASHBOARD / "index.html").read_text(encoding="utf-8")
check("rail có tool_apis", '"tool_apis"' in console and "ids: [\"mcp\"" in console)
check("VIEW_ICON key cho tool_apis", "tool_apis: \"key\"" in console)
check("render uỷ quyền JavisToolApis", "JavisToolApis" in console)
check("index nạp tool-apis.js trước console.js",
      html.index('src="/static/tool-apis.js') < html.index('src="/static/console.js'))
js = (DASHBOARD / "tool-apis.js").read_text(encoding="utf-8")
check("tool-apis.js không em dash", "\u2014" not in js)
py = (SERVER / "tool_apis.py").read_text(encoding="utf-8")
check("tool_apis.py không em dash", "\u2014" not in py)

if fails:
    raise SystemExit(f"\nFAIL - test_tool_apis: {len(fails)} lỗi")
print("\nOK - test_tool_apis: tất cả pass")
