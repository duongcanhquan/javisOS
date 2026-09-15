"""JAVIS_UPDATES_UI mặc định bật - người cài fork này thấy chuông + trang Cập nhật.

    python tests/python/test_updates_ui_mac_dinh.py
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import os
import sys

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


# Xóa biến môi trường tạm để đo đúng mặc định trong code.
_cu = os.environ.pop("JAVIS_UPDATES_UI", None)
try:
    import config as cfgmod
    check("mặc định updates_ui_bat() = True", cfgmod.updates_ui_bat() is True)
    os.environ["JAVIS_UPDATES_UI"] = "0"
    check("JAVIS_UPDATES_UI=0 tắt", cfgmod.updates_ui_bat() is False)
    os.environ["JAVIS_UPDATES_UI"] = "1"
    check("JAVIS_UPDATES_UI=1 bật", cfgmod.updates_ui_bat() is True)
finally:
    if _cu is None:
        os.environ.pop("JAVIS_UPDATES_UI", None)
    else:
        os.environ["JAVIS_UPDATES_UI"] = _cu

compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
check("compose đặt JAVIS_UPDATES_UI mặc định 1",
      "JAVIS_UPDATES_UI: ${JAVIS_UPDATES_UI:-1}" in compose)
hostinger = (ROOT / "docker-compose.hostinger.yml").read_text(encoding="utf-8")
check("hostinger compose cũng mặc định 1",
      "JAVIS_UPDATES_UI: ${JAVIS_UPDATES_UI:-1}" in hostinger)
dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
check("Dockerfile ENV JAVIS_UPDATES_UI=1", "JAVIS_UPDATES_UI=1" in dockerfile)
main = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("GITHUB_REPO trỏ fork duongcanhquan/javisOS",
      'GITHUB_REPO = "duongcanhquan/javisOS"' in main)

print()
if _fails:
    print(f"{len(_fails)} ĐỎ: " + ", ".join(_fails))
    sys.exit(1)
print("OK - test_updates_ui_mac_dinh")
