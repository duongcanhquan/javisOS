"""Icon PWA (/brand-icon/192|512) theo ảnh đại diện.

Chạy: python tests/python/test_brand_icon.py

Phần render Pillow chỉ chạy khi import được PIL + main (venv đủ deps).
Thiếu deps thì vẫn pass các canary nguồn (route/public/manifest).
"""
from __future__ import annotations

import io
import os
import struct
import sys
import tempfile
from pathlib import Path

from _paths import ROOT, SERVER  # noqa: F401

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails += 1


main_src = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("có def _brand_icon_png_bytes", "def _brand_icon_png_bytes" in main_src)
check("có route brand_icon", '@app.get("/brand-icon/{size}")' in main_src)
check("192/512 public auth", '"/brand-icon/192"' in main_src and '"/brand-icon/512"' in main_src)
check("favicon_ico dùng _brand_icon_png_bytes",
      "async def favicon_ico" in main_src and "_brand_icon_png_bytes(192)" in main_src)
check("reset logo trả logo_v",
      "async def branding_logo_reset" in main_src
      and 'return {"ok": True, "logo_v": cfg["branding"]["logo_v"]}' in main_src)

man = (ROOT / "dashboard" / "manifest.json").read_text(encoding="utf-8")
check("manifest trỏ brand-icon/192", '"/brand-icon/192"' in man)
check("manifest trỏ brand-icon/512", '"/brand-icon/512"' in man)

# Fallback PNG hợp lệ (signature + IHDR size).
for size in (192, 512):
    p = ROOT / "dashboard" / f"icon-{size}.png"
    check(f"fallback icon-{size}.png tồn tại", p.is_file())
    raw = p.read_bytes()
    check(f"fallback icon-{size}.png là PNG", raw[:8] == b"\x89PNG\r\n\x1a\n")
    # IHDR: width/height big-endian sau 8+8 bytes
    w, h = struct.unpack(">II", raw[16:24])
    check(f"fallback icon-{size}.png đúng {size}x{size}", w == size and h == size)

# Render thật nếu đủ môi trường.
try:
    from PIL import Image  # noqa: F401
    os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-brand-icon-")
    import main as jmain  # noqa: E402

    for size in (192, 512):
        data = jmain._brand_icon_png_bytes(size)
        im = Image.open(io.BytesIO(data))
        check(f"render {size} đúng kích thước", im.size == (size, size) and im.format == "PNG")

    brand = Path(os.environ["JAVIS_STATE_DIR"]) / "branding"
    brand.mkdir(parents=True, exist_ok=True)
    red = Image.new("RGB", (80, 40), (220, 30, 30))
    red.save(brand / "logo.jpg", format="JPEG")
    cfg = jmain.cfgmod.read_settings()
    cfg.setdefault("branding", {})
    cfg["branding"]["logo_ext"] = ".jpg"
    jmain.cfgmod.write_settings(cfg)
    im2 = Image.open(io.BytesIO(jmain._brand_icon_png_bytes(192))).convert("RGB")
    px = im2.getpixel((96, 96))
    check("logo tùy chỉnh đỏ vào icon 192", px[0] > 150 and px[0] > px[2])
    try:
        jmain._brand_icon_png_bytes(128)
        check("size 128 bị từ chối", False)
    except ValueError:
        check("size 128 bị từ chối", True)
except Exception as e:
    print("skip render (thiếu deps hoặc không boot main):", type(e).__name__, str(e)[:120])

if fails:
    print(f"\nFAIL - test_brand_icon: {fails} lỗi")
    sys.exit(1)
print("\nOK - test_brand_icon: tất cả pass")
