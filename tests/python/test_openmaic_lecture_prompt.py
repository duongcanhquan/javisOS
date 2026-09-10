"""Prompt OpenMAIC: liên mạch + dẫn giải slide.

    python tests/run.py openmaic_lecture_prompt
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import main as app_main

_loi = []


def check(ten, dieu_kien):
    print(f"       {'ok  ' if dieu_kien else 'FAIL'} {ten}")
    if not dieu_kien:
        _loi.append(ten)


req = app_main._openmaic_build_requirement(
    "Quang hợp",
    "## Cảnh 1\nScript mẫu\n## Cảnh 2\nChlorophyll",
    "## Quiz\nQ1?",
)

low = req.lower()
check("có CONTINUITY / cấm chào lại", "continuity" in low and "xin chào" in low)
check("cấm chào từ scene 2", "from scene 2" in low and "never say" in low)
check("dẫn giải nội dung slide", "slide-grounded" in low or "visible on that scene" in low)
check("đi theo bullet/diagram", "bullet" in low and "diagram" in low)
check("welcome chỉ scene 1", "only on scene 1" in low or "only scene 1" in low)
check("nhúng lop-hoc + quiz", "chlorophyll" in low and "q1?" in low)
check("final check nhắc greeting", "greeting" in low)

if _loi:
    raise SystemExit("FAIL: " + ", ".join(_loi))
print("ALL OK")
