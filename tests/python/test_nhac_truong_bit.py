"""Bịt lỗ: duyệt từ chat, khuôn không nhận một chữ, phòng sau không nhận cả bản dài.

    python tests/python/test_nhac_truong_bit.py
"""
import asyncio
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-ntb-"))

import nhac_truong as nt  # noqa: E402
import routes.nhac_truong as rte  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


def test_khuon_mot_chu_va_rut_so():
    phong = {"khuon": {"truong": ["nguon", "so_lieu"]}}
    check("một chữ không qua khuôn", "nguon" in nt.thieu_khuon(phong, "## nguon\nx\n## so_lieu\n12 tỷ doanh thu"))
    check("chữ giữ chỗ không qua", "nguon" in nt.thieu_khuon(phong, "## nguon\nok\n## so_lieu\n12 tỷ doanh thu"))
    ban = "## nguon\nvăn bản nguồn\n\nđoạn dài không cần chép lại " + ("lặp " * 40) + "\n## so_lieu\n12 tỷ doanh thu\n"
    check("đủ chữ thì qua khuôn", nt.thieu_khuon(phong, ban) == [])
    viec = {}
    nt.gop_fact(viec, "noi-dung", ban, phong)
    by = {f["khoa"]: f["gia_tri"] for f in viec["so"]}
    check("sổ lấy số từ trường, không cần dòng FACT", by.get("so-lieu") == "12 tỷ doanh thu")
    nt.gop_fact(viec, "noi-dung", ban + "\nFACT: so_lieu = 9 tỷ", phong)
    by = {f["khoa"]: f["gia_tri"] for f in viec["so"]}
    check("dòng FACT ghi đè trường", by.get("so-lieu") == "9 tỷ")
    sach = "## so_lieu\n12 tỷ\nFACT: doanh_thu = 9 tỷ"
    check("FACT không dính vào nội dung trường", nt._gia_tri_khuon(sach).get("so-lieu") == "12 tỷ")
    trong = nt.Kho(tempfile.mkdtemp())
    check("không có việc chờ thì chat đi tiếp", nt.thu_duyet(trong, "duyệt bài này") == (None, None))


def test_phong_viet_khong_nhan_ca_ban():
    dai = "đoạn dài không cần chép " + ("lặp " * 50)
    ban = "## nguon\nvăn bản nguồn đã chốt\n\n" + dai
    viec = {
        "id": "bai",
        "tieu_de": "Bài",
        "brief": "soát",
        "phong": ["noi-dung", "phap-che", "hau-ky"],
        "ban": {"noi-dung": ban},
        "khuon_da": {"noi-dung": ["nguon"]},
        "so": [{"khoa": "nguon", "gia_tri": "văn bản nguồn đã chốt", "nguon": "noi-dung"}],
    }
    nguoi = {"ten": "Minh", "vai": "thanh_vien", "skills": [], "tinh_cach": ""}
    viet = {"slug": "phap-che", "ten": "Pháp chế", "tieu_chi": "Không bịa", "loai": "viet"}
    ve = {"slug": "hau-ky", "ten": "Hậu kỳ", "tieu_chi": "Vẽ", "loai": "thiet_ke"}
    p_viet = nt.lap_prompt("LAM", nguoi, viet, viec)
    p_ve = nt.lap_prompt("LAM", nguoi, ve, viec)
    check("phòng viết không nhận đoạn dài", "không cần chép" not in p_viet and "văn bản nguồn đã chốt" in p_viet)
    check("phòng vẽ vẫn nhận cả bản", "không cần chép" in p_ve)


def test_loai_phong_va_cau_duyet():
    check("đồng ý kèm câu", nt.la_dong_y("Đồng ý, thêm số nguồn") == (True, "thêm số nguồn"))
    check("duyệt không câu", nt.la_dong_y("duyệt") == (True, ""))
    check("câu thường không phải duyệt", nt.la_dong_y("xem giúp bài này")[0] is False)
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.tao_phong(kho, "Hậu kỳ", "Làm hình")
    nt.them_nguoi(kho, "noi-dung", "An", "", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Lan", "", "", "thanh_vien")
    nt.them_nguoi(kho, "hau-ky", "Bình", "", "", "truong")
    nt.sua_phong(kho, "hau-ky", loai="thiet_ke")
    check("tên không có chữ thiết kế vẫn là phòng vẽ", nt.loai_hang(kho.doc_phong("hau-ky")) == "thiet_ke")
    viec = nt.tao_viec(kho, "Bài hình", "viết rồi vẽ", ["noi-dung", "hau-ky"], vong=2, bat_cong=True)

    async def noi(nguoi, prompt):
        kind = ""
        for line in prompt.splitlines():
            if line.startswith("LOAI: "):
                kind = line.split(":", 1)[1].strip()
        if kind == "GIAO":
            return "Làm bản."
        if kind == "LAM":
            return "NOI: xong\nFILE: ban.md\nbản đủ để dùng\nHET FILE"
        if kind in ("KIEM", "HOP"):
            return "QUYET: DAT\nTRA: noi-dung"
        return "Xong."

    mot = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("dừng ở kế hoạch", mot["cong"] == "ke_hoach")
    nt.duyet_loi(kho, "đồng ý")
    hai = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("phòng gắn loại thiết kế cũng bị chặn", hai["cong"] == "ban_thao" and "Bình" not in " ".join(
        r.get("ten") or "" for r in hai["loi"] if r.get("phong") == "hau-ky"))
    try:
        nt.duyet_loi(kho, "xem giúp")
        check("câu thường không duyệt được", False)
    except nt.LoiNhacTruong:
        check("câu thường không duyệt được", True)


def test_chat_duyet():
    p = ROOT / "system" / "plugins" / "javis-nhac-truong" / "plugin.py"
    spec = importlib.util.spec_from_file_location("javis_nhac_truong_bit", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    goc = Path(tempfile.mkdtemp(prefix="javis-nt-chat2-"))
    kho = nt.Kho(goc)
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "", "", "truong")

    class Ctx:
        vault_root = str(goc)

    da = {}
    cu = rte.bat_chay

    def gia(brain, vid, tu_dau=False):
        da["vid"] = vid
        da["brain"] = brain
        return "bat"

    rte.bat_chay = gia
    try:
        tra = asyncio.run(mod._chay({
            "op": "giao", "title": "Bài chat", "brief": "viết ngắn", "phong": "Nội dung",
        }, Ctx()))
        viec = kho.doc_viec("bai-chat")
        check("chat bật cổng duyệt", viec.get("bat_cong") is True and "op=duyet" in tra)
        viec["trang_thai"] = "cho_duyet"
        viec["cong"] = "ke_hoach"
        kho.luu_viec(viec)
        xem = asyncio.run(mod._chay({"op": "xem", "id": "bai-chat"}, Ctx()))
        check("xem báo đang chờ", "chờ duyệt" in xem)
        xong = asyncio.run(mod._chay({"op": "duyet", "id": "bai-chat", "y": "thêm nguồn"}, Ctx()))
    finally:
        rte.bat_chay = cu
    sau = kho.doc_viec("bai-chat")
    check("chat duyệt rồi chạy tiếp", "ke_hoach" in (sau.get("da_duyet") or []) and sau.get("y_kien") == "thêm nguồn")
    check("chat nói chạy từ chỗ dừng", "chỗ dừng" in xong and da.get("vid") == "bai-chat")
    check("nút telegram gắn đúng việc", (nt.nut_duyet(sau) or {}).get("inline_keyboard", [[{}]])[0][0].get("callback_data") == "ntd:bai-chat")


if __name__ == "__main__":
    test_khuon_mot_chu_va_rut_so()
    test_phong_viet_khong_nhan_ca_ban()
    test_loai_phong_va_cau_duyet()
    test_chat_duyet()
    if _fails:
        print("FAIL", _fails)
        raise SystemExit(1)
    print("OK - bịt lỗ")
