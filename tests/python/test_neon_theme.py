"""Tông Neon/Cyberpunk là lựa chọn thứ ba, không thay tông tối mặc định.

Chạy:
    .venv/bin/python tests/python/test_neon_theme.py
"""
import json
import re

from _paths import ROOT, SERVER  # noqa: E402,F401

STYLE = (ROOT / "dashboard" / "style.css").read_text(encoding="utf-8")
CONSOLE_CSS = (ROOT / "dashboard" / "console.css").read_text(encoding="utf-8")
THEME_JS = (ROOT / "dashboard" / "theme.js").read_text(encoding="utf-8")
GRAPH = (ROOT / "dashboard" / "graph.js").read_text(encoding="utf-8")
INDEX = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
CONSOLE_JS = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")
VI = json.loads((ROOT / "dashboard" / "i18n" / "vi.json").read_text(encoding="utf-8"))
EN = json.loads((ROOT / "dashboard" / "i18n" / "en.json").read_text(encoding="utf-8"))

fails = []


def check(name: str, condition: bool) -> None:
    print(("PASS: " if condition else "FAIL: ") + name)
    if not condition:
        fails.append(name)


check("style.css có khối :root[data-theme=\"neon\"]",
      ':root[data-theme="neon"]' in STYLE)
check("nền neon là navy đậm",
      re.search(r':root\[data-theme="neon"\][^}]*--bg:\s*#04091a', STYLE) is not None)
check("nhấn neon là cyan",
      re.search(r':root\[data-theme="neon"\][^}]*--accent:\s*#5ce1ff', STYLE) is not None)
check("magenta / coral nằm trong token neon",
      "#ff2bd6" in STYLE and "#ff7a59" in STYLE)
check("KPI neon chữ trắng",
      "--text-hi: #ffffff" in STYLE.split(':root[data-theme="neon"]', 1)[-1][:2500])

check("console.css kính neon có viền phát sáng",
      "rgba(92, 225, 255" in CONSOLE_CSS and ':root[data-theme="neon"]' in CONSOLE_CSS)
check("tiêu đề bảng neon dùng cyan",
      ":root[data-theme=\"neon\"] .cview-title" in CONSOLE_CSS)

check("theme.js hiểu 3 tông",
      '"neon"' in THEME_JS and "NAMES = [\"dark\", \"neon\", \"light\"]" in THEME_JS)
check("theme.js vẫn nhận apply(true) kiểu cũ",
      "v === true || v === \"light\"" in THEME_JS)
check("sự kiện mang theme + light + neon",
      "theme: name" in THEME_JS and "neon: name === \"neon\"" in THEME_JS)

check("FOUC áp neon trước khi vẽ",
      "data-theme','neon'" in INDEX or 'data-theme","neon"' in INDEX or "data-theme','neon'" in INDEX)
check("nút header có menu 3 tông",
      'id="themePop"' in INDEX and 'data-theme-set="neon"' in INDEX and 'id="themeWrap"' in INDEX)
check("icon tia sét cho neon",
      "ic-zap" in INDEX)

check("đồ thị có bảng màu neon",
      "CAT_COLORS_NEON" in GRAPH and "INK_NEON" in GRAPH)
check("Cài đặt có ô chọn tông",
      'id="setThemePicks"' in CONSOLE_JS and 'settings.theme' in CONSOLE_JS)

for key in ("top.theme_now_neon", "top.theme_opt_neon", "top.theme_menu",
            "settings.theme", "settings.theme_neon"):
    check(f"vi.json có {key}", key in VI and isinstance(VI[key], str) and VI[key])
    check(f"en.json có {key}", key in EN and isinstance(EN[key], str) and EN[key])

check("tông tối mặc định không bị neon đè --bg",
      re.search(r"^:root \{[^}]*--bg:\s*#06080f", STYLE, re.M) is not None
      or ("--bg: #06080f;" in STYLE.split(":root[data-theme", 1)[0]))
check("tông sáng vẫn còn --bg giấy",
      ':root[data-theme="light"]' in STYLE and "--bg: #f4f6fb;" in STYLE)
check("apply(false) vẫn về tối (không nhảy nhầm neon)",
      'if (v === true || v === "light") return "light"' in THEME_JS
      and 'if (v === "neon"' in THEME_JS)
check("ô theme trên header không phình hàng flex",
      "display: inline-flex" in STYLE)
check("menu tông trong ngăn kéo mobile không dùng absolute (tránh bị overflow cắt)",
      ".rail-sys .theme-pop" in STYLE and "position: static" in STYLE)
check("terminal có bảng màu neon riêng",
      "isNeon" in (ROOT / "dashboard" / "code-term.js").read_text(encoding="utf-8")
      and "#5ce1ff" in (ROOT / "dashboard" / "code-term.js").read_text(encoding="utf-8"))

check("gcard.current tông tối/sáng giữ bóng cũ",
      "0 8px 30px rgba(62, 224, 214, 0.18)" in CONSOLE_CSS)
check("neon mới ghi đè bóng gcard.current, không đè tông khác",
      ':root[data-theme="neon"] .gcard.current' in CONSOLE_CSS)
check("token --accent tối mặc định không đổi",
      "--accent: #3ee0d6;" in STYLE.split(":root[data-theme", 1)[0])
check("token --accent sáng không đổi",
      "--accent: #0d9488;" in STYLE)
check("menu header dùng menuitemradio + aria-checked",
      'role="menuitemradio"' in INDEX and 'aria-checked="true"' in INDEX)
check("chọn tông lạ bị chuẩn hoá về tối",
      'return "dark"' in THEME_JS)

if fails:
    raise SystemExit(f"\nFAIL - test_neon_theme: {len(fails)} lỗi: {fails}")
print("\nOK - test_neon_theme: tất cả pass")
