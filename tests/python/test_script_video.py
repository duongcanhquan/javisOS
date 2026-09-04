"""Render video từ kịch bản (native, không Pixelle).

    python tests/python/test_script_video.py
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import shutil
from pathlib import Path
import tempfile

import script_video as sv

loi = []


def check(ten, dieu, them=""):
    print(("ok   " if dieu else "FAIL ") + ten + (f"  [{them}]" if them and not dieu else ""))
    if not dieu:
        loi.append(ten)


check("tách đoạn trống", sv.tach_canh("A.\n\nB.\n\nC.") == ["A.", "B.", "C."])
check("tách theo dòng", sv.tach_canh("A.\nB.") == ["A.", "B."])
check("rỗng → []", sv.tach_canh("  \n") == [])
check("trần cảnh", len(sv.tach_canh("\n\n".join(f"c{i}" for i in range(30)))) == sv._MAX_SCENES)

# Chỉ chạy render thật khi có ffmpeg (CI/local).
if shutil.which("ffmpeg"):
    brain = Path(tempfile.mkdtemp(prefix="javis-sv-"))
    script = (
        "Mất 4 năm đại học truyền thống hay tự tin làm chủ sự nghiệp?\n\n"
        "Cao đẳng Việt Mỹ Hà Nội - lộ trình 9 cộng tinh gọn."
    )

    async def _go():
        return await sv.render_script_video(
            script=script,
            title="Viet My",
            vault_root=str(brain),
            aspect="portrait",
            voice="vi-VN-HoaiMyNeural",
            with_images=False,  # CI không có ChatGPT OAuth
        )

    res = asyncio.run(_go())
    check("render ok", res.get("ok") is True, res.get("error"))
    if res.get("ok"):
        p = Path(res["path"])
        check("file mp4 tồn tại", p.is_file() and p.stat().st_size > 1000, str(p))
        check("rel_path attachments", res["rel_path"].startswith("attachments/") and res["rel_path"].endswith(".mp4"))
        check("2 cảnh", res.get("scenes") == 2)

    # Overlay trên ảnh nền giả
    from PIL import Image
    brain2 = Path(tempfile.mkdtemp(prefix="javis-sv-img-"))
    bg = brain2 / "bg.jpg"
    Image.new("RGB", (800, 1200), (40, 80, 120)).save(bg, "JPEG")
    framed = sv.ve_khung("Câu thử overlay", (540, 960), title="Test", bg_image=str(bg))
    check("overlay có size đúng", framed.size == (540, 960))
    check("prompt_anh có style", "photorealistic" in sv.prompt_anh("học thực hành").lower() or "campus" in sv.prompt_anh("x").lower())
else:
    print("skip  render (không có ffmpeg)")

print()
if loi:
    print(f"{len(loi)} ĐỎ: " + ", ".join(loi))
    raise SystemExit(1)
print("ALL PASS")
