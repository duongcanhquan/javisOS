#!/usr/bin/env python3
"""Sinh dashboard/vendor/lucide-icons.js từ dashboard/icons.manifest.json.

Chạy lại mỗi khi thêm/bớt icon trong manifest:

    python tools/gen_icons.py

Nguồn hình là Phosphor Icons bản Regular (nét mảnh). Khóa trong file vendor VẪN là tên
cũ trong manifest, vì khắp dashboard gọi ic("tên-cũ"). Bảng MAP bên dưới dịch
tên cũ sang slug Phosphor khi hai bên không trùng.

Script tải SVG rồi rút phần ruột (bỏ thẻ <svg> ngoài, vì icons.js tự dựng thẻ
bọc). Kết quả ghi vào vendor/ và được commit - app không gọi mạng lúc chạy.

Cần internet KHI CHẠY SCRIPT. Nếu một tên không có thật, script dừng và báo
tên sai thay vì ghi ra file thiếu icon.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "dashboard" / "icons.manifest.json"
OUT = ROOT / "dashboard" / "vendor" / "lucide-icons.js"
OUT_CSS = ROOT / "dashboard" / "vendor" / "lucide-icons.css"

PH_VERSION = "2.1.1"
CDN = "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@{ver}/assets/regular/{name}.svg"
TIMEOUT = 20

# Tên trong manifest (khóa ic()) -> slug file Phosphor Regular.
# Tên không có trong bảng này được hiểu là trùng slug Phosphor.
MAP = {
    "alarm-clock": "alarm",
    "arrow-up-down": "arrows-down-up",
    "ban": "prohibit",
    "bot": "robot",
    "brush-cleaning": "broom",
    "building-2": "buildings",
    "chart-column": "chart-bar",
    "chevron-down": "caret-down",
    "chevron-left": "caret-left",
    "chevron-right": "caret-right",
    "chevron-up": "caret-up",
    "chevrons-down": "caret-double-down",
    "chevrons-up": "caret-double-up",
    "circle-check": "check-circle",
    "circle-dot": "radio-button",
    "circle-help": "question",
    "circle-stop": "stop-circle",
    "circle-user": "user-circle",
    "circle-x": "x-circle",
    "clipboard-check": "clipboard-text",
    "ellipsis-vertical": "dots-three-vertical",
    "external-link": "arrow-square-out",
    "eye-off": "eye-slash",
    "file-type": "file",
    "folder-tree": "folders",
    "history": "clock-counter-clockwise",
    "layers": "stack",
    "list-todo": "list-checks",
    "loader": "circle-notch",
    "log-out": "sign-out",
    "mail": "envelope",
    "maximize": "arrows-out",
    "menu": "list",
    "message-circle": "chat-circle",
    "messages-square": "chats",
    "mic": "microphone",
    "minimize": "arrows-in",
    "panel-left": "sidebar",
    "pen-line": "pen",
    "pin": "push-pin",
    "plane-takeoff": "airplane-takeoff",
    "puzzle": "puzzle-piece",
    "quote": "quotes",
    "rotate-cw": "arrow-clockwise",
    "save": "floppy-disk",
    "scroll-text": "scroll",
    "search": "magnifying-glass",
    "send": "paper-plane-tilt",
    "settings": "gear",
    "sparkles": "sparkle",
    "square-kanban": "kanban",
    "square-pen": "note-pencil",
    "table-2": "table",
    "trash-2": "trash",
    "trending-down": "trend-down",
    "trending-up": "trend-up",
    "triangle-alert": "warning",
    "type": "text-t",
    "undo-2": "arrow-u-up-left",
    "upload-cloud": "cloud-arrow-up",
    "volume-2": "speaker-high",
    "webhook": "webhooks-logo",
    "workflow": "flow-arrow",
    "zap": "lightning",
}

# Thuộc tính thẻ <svg> ngoài do icons.js dựng, nên rút bỏ khỏi phần ruột.
OUTER_SVG = re.compile(r"^.*?<svg\b[^>]*>(.*)</svg>\s*$", re.DOTALL)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
WS = re.compile(r"\s+")


def load_manifest() -> tuple[list[str], list[str]]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    names: list[str] = []
    for group, items in data.get("groups", {}).items():
        if not isinstance(items, list):
            sys.exit(f"Nhóm '{group}' trong manifest phải là một danh sách.")
        names.extend(items)
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        sys.exit("Tên icon bị lặp trong manifest: " + ", ".join(dupes))

    css_vars = data.get("css_vars", []) or []
    missing = sorted(set(css_vars) - set(names))
    if missing:
        sys.exit(
            "css_vars có tên chưa nằm trong groups: " + ", ".join(missing) +
            "\nThêm chúng vào một nhóm trước đã."
        )
    return sorted(set(names)), sorted(set(css_vars))


def data_uri(body: str) -> str:
    """Bọc ruột icon thành data URI dùng được trong mask/background của CSS.

    Chỉ escape đúng những ký tự phá cú pháp url(...) trong CSS. Giữ nguyên phần
    còn lại cho file dễ đọc và nhẹ hơn so với base64.
    """
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256' fill='black'>"
        + body.replace('"', "'") + "</svg>"
    )
    for ch, rep in (("%", "%25"), ("#", "%23"), ("<", "%3C"), (">", "%3E")):
        svg = svg.replace(ch, rep)
    return 'url("data:image/svg+xml,' + svg + '")'


def fetch(name: str) -> str:
    slug = MAP.get(name, name)
    url = CDN.format(ver=PH_VERSION, name=slug)
    # curl chứ không phải urllib: máy macOS hay thiếu CA trong Python,
    # còn curl dùng kho chứng chỉ của hệ điều hành.
    try:
        raw = subprocess.run(
            ["curl", "-fsSL", url],
            check=True,
            capture_output=True,
            timeout=TIMEOUT,
        ).stdout.decode("utf-8")
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 22:
            sys.exit(
                f"Không có icon '{name}' (Phosphor '{slug}') trong "
                f"@phosphor-icons/core@{PH_VERSION}.\n"
                f"Tra slug tại https://phosphoricons.com rồi sửa MAP trong tools/gen_icons.py."
            )
        sys.exit(f"Tải '{name}' lỗi (curl {exc.returncode}): {url}")
    except (OSError, subprocess.TimeoutExpired) as exc:
        sys.exit(f"Không nối được CDN ({exc}). Script này cần internet.")

    raw = COMMENT.sub("", raw)
    match = OUTER_SVG.match(raw)
    if not match:
        sys.exit(f"SVG của '{name}' không đúng khuôn mong đợi, không rút được ruột.")
    body = WS.sub(" ", match.group(1)).strip()
    if not body:
        sys.exit(f"Icon '{name}' rút ra rỗng.")
    return body


def main() -> None:
    names, css_vars = load_manifest()
    print(f"Manifest có {len(names)} icon. Đang tải Phosphor Regular @{PH_VERSION}...")

    icons: dict[str, str] = {}
    for i, name in enumerate(names, 1):
        icons[name] = fetch(name)
        print(f"  [{i:3d}/{len(names)}] {name}")

    lines = [
        "// FILE TỰ SINH - ĐỪNG SỬA TAY.",
        f"// Nguồn: @phosphor-icons/core@{PH_VERSION} bản Regular, nét mảnh (giấy phép MIT) - https://phosphoricons.com",
        "// Sinh lại: sửa dashboard/icons.manifest.json rồi chạy python tools/gen_icons.py",
        "window.LucideIcons = {",
    ]
    for name in names:
        lines.append(f'  {json.dumps(name)}: {json.dumps(icons[name])},')
    lines.append("};")
    lines.append(f'window.LucideIconsVersion = "phosphor-regular@{PH_VERSION}";')
    lines.append("")

    # newline="\n": cả repo dùng LF. Trên Windows, Python ở text mode tự đổi \n
    # thành \r\n, làm diff thành "cả file thay đổi" và che mất sửa đổi thật.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    size = OUT.stat().st_size
    print(f"\nĐã ghi {OUT.relative_to(ROOT)} - {len(names)} icon, {size / 1024:.1f}KB.")

    css = [
        "/* FILE TỰ SINH - ĐỪNG SỬA TAY. */",
        f"/* Nguồn: @phosphor-icons/core@{PH_VERSION} bản Regular, nét mảnh (giấy phép MIT) - https://phosphoricons.com */",
        "/* Sinh lại: sửa css_vars trong dashboard/icons.manifest.json rồi chạy",
        "   python tools/gen_icons.py */",
        "",
        "/* Icon dạng data URI cho những chỗ CHỈ CSS với tới được: content của",
        "   ::before/::after, background... Thẻ SVG không nhét vào content: được.",
        "   Dùng kèm lớp .ic-mask trong style.css để icon vẫn ăn currentColor. */",
        ":root {",
    ]
    for name in css_vars:
        css.append(f"  --ic-{name}: {data_uri(icons[name])};")
    css.append("}")
    css.append("")
    OUT_CSS.write_text("\n".join(css), encoding="utf-8")
    print(f"Đã ghi {OUT_CSS.relative_to(ROOT)} - {len(css_vars)} biến CSS, "
          f"{OUT_CSS.stat().st_size / 1024:.1f}KB.")


if __name__ == "__main__":
    main()
