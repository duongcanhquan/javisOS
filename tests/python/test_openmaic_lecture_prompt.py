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
check("narration dài 45-90s / ~60s", "45-90" in low and "60" in low)
check("Remotion-style emphasis", "remotion" in low or "visual emphasis" in low or "primary visual focus" in low)
check("ảnh và biểu đồ", "image" in low and ("chart" in low or "diagram" in low))
check("cấm chỉ đọc bullet", "reading bullets" in low or "not reading bullets" in low or "lecture is not reading" in low)

if _loi:
    raise SystemExit("FAIL: " + ", ".join(_loi))
print("ALL OK")
