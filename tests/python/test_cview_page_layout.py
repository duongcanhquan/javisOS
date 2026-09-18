"""Trang quản lý (Tài khoản, Cài đặt...) căn giữa, 2 cột desktop, 1 cột mobile.

Chạy:
    .venv/bin/python tests/python/test_cview_page_layout.py
"""
from _paths import ROOT, SERVER  # noqa: E402,F401

CONSOLE = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")
CSS = (ROOT / "dashboard" / "console.css").read_text(encoding="utf-8")
INDEX = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")

fails = []


def check(name: str, condition: bool) -> None:
    if condition:
        print(f"PASS: {name}")
    else:
        print(f"FAIL: {name}")
        fails.append(name)


check("có khung .cview-page căn giữa 1180px",
      "width: min(1180px, 100%)" in CSS and ".cview-page" in CSS)
check("Tài khoản xếp lưới 2 cột",
      'class="cview-page ac-page"' in CONSOLE and 'class="cview-stack"' in CONSOLE)
check("Tài khoản không còn thẻ max-width:560px",
      'style="max-width:560px"' not in CONSOLE.split("async function renderAccount", 1)[1].split(
          "async function renderTfa", 1)[0])
check("desktop hẹp / tablet về 1 cột trước mobile",
      "@media (max-width: 1100px)" in CSS and ".cview-stack { grid-template-columns: 1fr; }" in CSS)
check("mobile: chữ ô nhập 16px (không zoom iOS)",
      ".js-input { font-size: 16px;" in CSS)
check("mobile: nút form cao tối thiểu 44px",
      "min-height: 44px" in CSS)
check("2FA setup QR + bước cạnh nhau",
      'class="tfa-setup"' in CONSOLE and ".tfa-setup-copy" in CSS)
check("cache bust console.css không tụt",
      "console.css?v=64" in INDEX)
check("Cài đặt cùng bề ngang 1180",
      ".settings-page { width: min(100%, 1180px)" in CSS)

if fails:
    raise SystemExit(f"\nFAIL - test_cview_page_layout: {len(fails)} lỗi")
print("\nOK - test_cview_page_layout: tất cả pass")
