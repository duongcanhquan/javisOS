"""Giai đoạn 2: khuôn bàn giao và sổ việc dùng chung.

    python tests/python/test_nhac_truong_gd2.py
"""
import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-nt2-"))

import nhac_truong as nt  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


def loai(prompt):
    m = re.search(r"^LOAI: (\w+)", prompt, re.M)
    return m.group(1) if m else ""


def test_khuon_va_fact_thuan():
    check("đủ đề mục thì không thiếu", nt.thieu_khuon(
        {"khuon": {"truong": ["nguon", "so_lieu"]}},
        "## nguon\nvăn bản\n## so_lieu\n12",
    ) == [])
    check("thiếu trường thì nêu đúng tên", nt.thieu_khuon(
        {"khuon": {"truong": ["nguon", "so_lieu"]}},
        "## nguon\nvăn bản",
    ) == ["so-lieu"])
    check("JSON artifact cũng được tính", nt.thieu_khuon(
        {"khuon": {"truong": ["nguon"]}},
        '{"artifact":{"nguon":"văn bản"}}',
    ) == [])
    check("phòng không khuôn thì không bắt", nt.thieu_khuon({}, "## gì cũng được") == [])
    check("đọc FACT", nt.doc_fact("FACT: doanh_thu = 12 tỷ")[0]["khoa"] == "doanh-thu")
    viec = {}
    nt.gop_fact(viec, "noi-dung", "FACT: doanh_thu = 12 tỷ")
    nt.gop_fact(viec, "phap-che", "FACT: doanh_thu = 11 tỷ\nFACT: nguon = văn bản")
    by = {f["khoa"]: f for f in viec["so"]}
    check("cùng khóa thì bản sau ghi đè", by["doanh-thu"]["gia_tri"] == "11 tỷ" and by["doanh-thu"]["nguon"] == "phap-che")
    check("khóa mới được thêm", by["nguon"]["gia_tri"] == "văn bản")


def test_thieu_khuon_khong_goi_truong_va_dung_vong_2():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Đủ trường")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Lan", "viết", "", "thanh_vien")
    nt.dat_khuon(kho, "noi-dung", ["nguon", "so_lieu"])
    viec = nt.tao_viec(kho, "Bài thiếu", "Viết đủ trường", ["noi-dung"], vong=6)
    calls = []

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        calls.append(kind)
        if kind == "GIAO":
            return "Lan viết bản."
        if kind == "LAM":
            return "NOI: thiếu\nFILE: ban.md\n## nguon\nvăn bản\nHET FILE"
        return "QUYET: DAT"

    out = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("thiếu trường thì lệch", out["trang_thai"] == "lech")
    check("xin một câu chỉ đạo", "chỉ đạo" in (out.get("xin_y") or ""))
    check("trưởng không được gọi chấm khi thiếu khuôn", "KIEM" not in calls)
    check("dừng ở vòng 2, không hỏi mãi", calls.count("LAM") == 2)


def test_so_viec_chuyen_sang_phong_sau():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Đủ trường")
    nt.tao_phong(kho, "Pháp chế", "Không bịa")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Lan", "viết", "", "thanh_vien")
    nt.them_nguoi(kho, "phap-che", "Hà", "soi", "", "truong")
    nt.them_nguoi(kho, "phap-che", "Minh", "đối chiếu", "", "thanh_vien")
    nt.dat_khuon(kho, "noi-dung", ["nguon", "so_lieu"], ten="Brief")
    viec = nt.tao_viec(kho, "Bài đủ", "Viết rồi soát", ["noi-dung", "phap-che"], vong=4)
    thay = []

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        thay.append((nguoi.get("ten"), kind, "SỔ VIỆC" in prompt and "doanh-thu" in prompt))
        if kind == "GIAO":
            return "Làm bản."
        if kind == "LAM" and nguoi.get("ten") == "Lan":
            if "LỆNH SỬA" in prompt:
                return "NOI: đủ\nFILE: ban.md\n## nguon\nvăn bản\n## so_lieu\n12 tỷ\nFACT: doanh_thu = 12 tỷ\nHET FILE"
            return "NOI: thiếu\nFILE: ban.md\n## nguon\nvăn bản\nHET FILE"
        if kind in ("LAM", "KIEM", "HOP"):
            return "QUYET: DAT\nTRA: noi-dung" if kind != "LAM" else "NOI: đã soát\nFILE: ban.md\nkhông hứa quá\nHET FILE"
        if kind == "KET":
            return "Bản xong."
        return "QUYET: DAT"

    out = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("đủ khuôn thì xong", out["trang_thai"] == "xong")
    by = {f["khoa"]: f for f in out.get("so") or []}
    check("sổ giữ số đã chốt", by.get("doanh-thu", {}).get("gia_tri") == "12 tỷ")
    check("phòng sau thấy sổ, không phải tự bịa lại", any(ten == "Minh" and kind == "LAM" and co for ten, kind, co in thay))
    check("bỏ khuôn thì phòng sạch", "khuon" not in nt.dat_khuon(kho, "noi-dung", []))


if __name__ == "__main__":
    test_khuon_va_fact_thuan()
    test_thieu_khuon_khong_goi_truong_va_dung_vong_2()
    test_so_viec_chuyen_sang_phong_sau()
    if _fails:
        print("FAIL", _fails)
        raise SystemExit(1)
    print("OK - giai đoạn 2")
