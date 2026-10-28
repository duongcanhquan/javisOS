"""Văn phòng 2.5D: look + avatar."""
from __future__ import annotations

import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
import nhac_truong as nt  # noqa: E402


def check(ten: str, ok: bool):
    if not ok:
        raise AssertionError(ten)
    print("ok", ten)


def test_look_va_avatar():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ", "lan_luot")
    nt.them_nguoi(kho, "noi-dung", "An", "", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Bình", "", "", "thanh_vien")

    vp = nt.luu_look(kho, canh="hop", mau="bien")
    check("lưu cảnh họp", (vp.get("look") or {}).get("canh") == "hop")
    check("lưu màu biển", (vp.get("look") or {}).get("mau") == "bien")

    try:
        nt.luu_look(kho, canh="xyz")
        check("cảnh lạ bị chặn", False)
    except nt.LoiNhacTruong:
        check("cảnh lạ bị chặn", True)

    kq = nt.luu_avatar(kho, "noi-dung", "an", "preset:pixel-2")
    phong = kq["phong"]
    an = next(n for n in phong["nguoi"] if n["slug"] == "an")
    check("avatar trên người phòng", an.get("avatar") == "preset:pixel-2")
    vp2 = kq["van_phong"]
    nguoi = ((vp2.get("phong") or {}).get("noi-dung") or {}).get("nguoi") or []
    hit = next(n for n in nguoi if n["slug"] == "an")
    check("avatar trên van-phong", hit.get("avatar") == "preset:pixel-2")

    try:
        nt.luu_avatar(kho, "noi-dung", "an", "preset:khong-co")
        check("preset lạ bị chặn", False)
    except nt.LoiNhacTruong:
        check("preset lạ bị chặn", True)

    # Preset SVG cũ vẫn nhận (data cũ) dù picker chỉ liệt kê pixel.
    nt.luu_avatar(kho, "noi-dung", "an", "preset:ceo-01")
    an2 = next(n for n in kho.doc_phong("noi-dung")["nguoi"] if n["slug"] == "an")
    check("giữ được avatar SVG cũ", an2.get("avatar") == "preset:ceo-01")
    nt.luu_avatar(kho, "noi-dung", "an", "preset:pixel-2")

    vp3 = nt.dong_bo_van_phong(kho)
    hit3 = next(
        n for n in ((vp3.get("phong") or {}).get("noi-dung") or {}).get("nguoi") or []
        if n["slug"] == "an"
    )
    check("đồng bộ giữ avatar", hit3.get("avatar") == "preset:pixel-2")
    check("look còn sau đồng bộ", (vp3.get("look") or {}).get("canh") == "hop")

    pixel = Path(__file__).resolve().parents[2] / "dashboard" / "nt-pixel" / "assets" / "characters"
    check("có sprite pixel", (pixel / "char_0.png").is_file() and (pixel / "char_5.png").is_file())
    check("picker = 6 pixel", list(nt.AVATAR_PRESET) == [f"pixel-{i}" for i in range(6)])
    for ma in nt.AVATAR_PRESET:
        check("file " + ma, (pixel / ("char_" + ma.split("-", 1)[1] + ".png")).is_file())
    check("hợp lệ cả SVG cũ", "ceo-01" in nt.AVATAR_HOP and "design-01" in nt.AVATAR_HOP)

    nt.them_nguoi(kho, "noi-dung", "Chi", "", "", "thanh_vien", avatar="preset:pixel-4")
    phong = kho.doc_phong("noi-dung")
    chi = next(n for n in phong["nguoi"] if n["slug"] == "chi")
    check("thêm người kèm avatar", chi.get("avatar") == "preset:pixel-4")

    vp4 = nt.luu_look(kho, phong_cach="sang_tao")
    check("phong cách sáng tạo", (vp4.get("look") or {}).get("phong_cach") == "sang_tao")
    check("phong cách gắn cảnh/màu", (vp4.get("look") or {}).get("canh") == "sang" and (vp4.get("look") or {}).get("mau") == "cat")


if __name__ == "__main__":
    test_look_va_avatar()
    print("PASS stage")
