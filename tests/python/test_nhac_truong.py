"""Nhạc trưởng: trưởng phòng chặn bản, họp liên phòng, trần vòng.

    python tests/run.py nhac_truong
"""
import asyncio
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-nt-"))

import nhac_truong as nt  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import routes.nhac_truong as rte  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


def loai(prompt):
    m = re.search(r"^LOAI: (\w+)", prompt, re.M)
    return m.group(1) if m else ""


async def dung_phong(kho):
    nt.tao_phong(kho, "Nội dung", "Rõ ý, đúng brief")
    nt.tao_phong(kho, "Pháp chế", "Không hứa quá, không bịa số")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng, không viết hộ", "dieu-phoi", "truong")
    nt.them_nguoi(kho, "noi-dung", "Lan", "viết ngắn", "viet-bai", "thanh_vien")
    nt.them_nguoi(kho, "phap-che", "Hà", "soi từng câu", "phap-che", "truong")
    nt.them_nguoi(kho, "phap-che", "Minh", "đối chiếu nguồn", "wiki", "thanh_vien")


def test_tao_va_chan_hai_truong():
    kho = nt.Kho(tempfile.mkdtemp())
    p = nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, p["slug"], "An", "thẳng", "dieu-phoi", "truong")
    n = nt.them_nguoi(kho, p["slug"], "Chi", "ấm", "viết bài, nghiên cứu", "thanh_vien")
    check("skill giữ nguyên chữ người gõ", n["skills"] == ["viết bài", "nghiên cứu"])
    nt.them_nguoi(kho, p["slug"], "Bình", "cũng muốn làm trưởng", "", "truong", vi_tri="Chuyên viên nội dung")
    phong = kho.doc_phong(p["slug"])
    truong = [n["ten"] for n in phong["nguoi"] if n.get("vai") == "truong"]
    binh = next(n for n in phong["nguoi"] if n["ten"] == "Bình")
    check("đổi trưởng thì chỉ còn một", truong == ["Bình"] and binh["vi_tri"] == "Chuyên viên nội dung")
    try:
        nt.tao_viec(kho, "Bài", "800 chữ", ["phap-che"])
        check("việc cần phòng có thật", False)
    except nt.LoiNhacTruong:
        check("việc cần phòng có thật", True)


def test_thieu_quyet_la_chua():
    check("thiếu QUYET là chưa", nt.doc_quyet("tạm được")["quyet"] == "")
    check("đọc Đạt có dấu", nt.doc_quyet("QUYET: ĐẠT")["quyet"] == "DAT")
    check("đọc chưa và trả", nt.doc_quyet("QUYET: CHƯA\nTRA: Nội dung\nSUA: Bỏ câu")["tra"] == "noi-dung")


def test_noi_thu_xong():
    kho = nt.Kho(tempfile.mkdtemp())
    asyncio.run(dung_phong(kho))
    viec = nt.tao_viec(kho, "Bài UAV", "800 chữ, không hứa kết quả", ["noi-dung", "phap-che"], 2)
    prompts = []

    async def noi(nguoi, prompt):
        prompts.append(prompt)
        return await nt.noi_thu(nguoi, prompt)

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("chạy thử xong", xong["trang_thai"] == "xong")
    check("cả hai phòng đạt", xong["dat"]["noi-dung"] and xong["dat"]["phap-che"])
    ban = "\n".join(xong["ban"].values())
    check("bản chốt không còn cam kết", "cam kết" not in ban)
    kiem = [r for r in xong["loi"] if r["lop"] == "kiem"]
    check("nội bộ từng chưa rồi đạt", any(r["quyet"] == "CHUA" for r in kiem) and any(r["quyet"] == "DAT" for r in kiem))
    check("prompt có tính cách", any("thẳng, không viết hộ" in p for p in prompts))
    md = Path(kho.goc) / "viec" / f"{viec['id']}.md"
    check("có file biên bản", md.is_file() and "An" in md.read_text(encoding="utf-8"))
    check("có kết quả cuối", "Kết quả cuối" in (xong.get("ket_qua") or "") and "## Kết quả" in md.read_text(encoding="utf-8"))


def test_phap_che_chan_du_noi_bo_bo_qua():
    kho = nt.Kho(tempfile.mkdtemp())
    asyncio.run(dung_phong(kho))
    viec = nt.tao_viec(kho, "Ra mắt", "không hứa kết quả học", ["noi-dung", "phap-che"], 2)

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        if nguoi["slug"] == "lan" and kind == "LAM":
            if "LỆNH SỬA" in prompt:
                return "Buổi học gồm 6 phần. Không hứa kết quả."
            return "Phụ huynh yên tâm vì cam kết tiến bộ."
        if kind == "KIEM":
            return "QUYET: DAT"
        if kind == "HOP" and nguoi["slug"] == "ha":
            if "cam kết" in prompt.split("Kết thúc bằng:")[0]:
                return "QUYET: CHUA\nTRA: noi-dung\nSUA: Bỏ câu cam kết ở đoạn 3."
            return "QUYET: DAT"
        if kind == "HOP":
            return "QUYET: DAT"
        return "Làm phần của mình."

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("liên phòng cứu bản lọt", xong["trang_thai"] == "xong")
    check("Hà từng chặn", any(r["slug"] == "ha" and r["quyet"] == "CHUA" for r in xong["loi"]))
    check("bản nội dung đã bỏ câu hứa", "cam kết" not in xong["ban"]["noi-dung"])


def test_truong_khong_gat_ho_phong_khac():
    kho = nt.Kho(tempfile.mkdtemp())
    asyncio.run(dung_phong(kho))
    viec = nt.tao_viec(kho, "Lệch", "một brief", ["noi-dung", "phap-che"], 2)

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        if kind == "HOP" and nguoi["slug"] == "an":
            return "QUYET: CHUA\nSUA: còn yếu\nTRA: noi-dung"
        if kind == "HOP":
            return "QUYET: DAT"
        if kind == "KIEM":
            return "QUYET: DAT"
        return "bản ổn"

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("hết vòng thì lệch", xong["trang_thai"] == "lech")
    check("lệch vẫn có kết quả", bool((xong.get("ket_qua") or "").strip()))
    check("pháp chế vẫn đạt phần mình", xong["dat"]["phap-che"] is True)
    check("nội dung không được gật hộ", xong["dat"]["noi-dung"] is False)
    hop_ha = [r for r in xong["loi"] if r["lop"] == "hop" and r["slug"] == "ha"]
    check("trần 2 vòng họp", len(hop_ha) == 2)


def test_mot_phong():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Lan", "ngắn", "viet", "thanh_vien")
    viec = nt.tao_viec(kho, "Một phòng", "viết ngắn", ["noi-dung"], 2)
    xong = asyncio.run(nt.chay(kho, viec["id"], nt.noi_thu))
    check("một phòng không họp liên phòng", xong["trang_thai"] == "xong" and not any(r["lop"] == "hop" for r in xong["loi"]))


def test_api():
    goc = tempfile.mkdtemp()
    app = FastAPI()
    rte.register(app, rte.Deps(brain_root=lambda _n: goc))
    c = TestClient(app)
    r = c.post("/nhac-truong/phong", json={"ten": "Nội dung", "tieu_chi": "Rõ"})
    check("api tạo phòng", r.status_code == 200 and r.json()["phong"]["slug"] == "noi-dung")
    c.post("/nhac-truong/phong/noi-dung/nguoi", json={"ten": "An", "vai": "truong", "tinh_cach": "thẳng"})
    c.post("/nhac-truong/phong/noi-dung/nguoi", json={"ten": "Lan", "skills": "viết bài"})
    hai = c.post("/nhac-truong/phong/noi-dung/nguoi", json={"ten": "Bình", "vai": "truong", "vi_tri": "Biên tập"})
    truong = [n["ten"] for n in hai.json()["phong"]["nguoi"] if n.get("vai") == "truong"]
    check("api đổi trưởng giữ một người", hai.status_code == 200 and truong == ["Bình"])
    v = c.post("/nhac-truong/viec", json={"tieu_de": "Bài", "brief": "ngắn", "phong": ["noi-dung"], "vong": 2})
    vid = v.json()["viec"]["id"]
    chay = c.post(f"/nhac-truong/viec/{vid}/chay", json={"thu": True})
    body = chay.json()
    check("api chạy thử", chay.status_code == 200 and body["viec"]["trang_thai"] == "xong")
    doc = c.get(f"/nhac-truong/viec/{vid}")
    check("api đọc lại biên bản", doc.json()["viec"]["loi"])
    md = Path(goc) / "nhac-truong" / "viec" / f"{vid}.md"
    check("api ghi file md", md.is_file() and "Kết quả" in md.read_text(encoding="utf-8"))
    trang = c.get(f"/nhac-truong/viec/{vid}/ket-qua")
    check("api mở được trang kết quả", trang.status_code == 200 and "Lưu PDF" in trang.text and "Kết quả cuối" in trang.text and "Trạng thái" in trang.text and "ngắn" in trang.text)
    check("link trong kết quả bấm được", 'href="https://vi-du.test/a"' in nt.html_lien("Xem https://vi-du.test/a."))
    sua = c.post("/nhac-truong/phong/noi-dung", json={"tieu_chi": "Đúng brief"})
    check("api sửa tiêu chí", sua.status_code == 200 and sua.json()["phong"]["tieu_chi"] == "Đúng brief")
    trong = c.post("/nhac-truong/phong/noi-dung", json={"tieu_chi": " "})
    check("api chặn tiêu chí trống", trong.status_code == 400)
    doi = c.post("/nhac-truong/phong/noi-dung/nguoi/lan", json={"tinh_cach": "ấm", "skills": "sửa bài"})
    check("api sửa người", doi.status_code == 200 and doi.json()["nguoi"]["tinh_cach"] == "ấm")
    hai_vai = c.post("/nhac-truong/phong/noi-dung/nguoi/lan", json={"vai": "truong", "vi_tri": "Chuyên viên"})
    nguoi = hai_vai.json()["phong"]["nguoi"]
    truong = [n["slug"] for n in nguoi if n.get("vai") == "truong"]
    lan = next(n for n in nguoi if n["slug"] == "lan")
    check("api sửa được vị trí trưởng", hai_vai.status_code == 200 and truong == ["lan"] and lan["vi_tri"] == "Chuyên viên")
    xoa = c.delete(f"/nhac-truong/viec/{vid}")
    check("api xoá việc", xoa.status_code == 200 and not md.is_file())
    v2 = c.post("/nhac-truong/viec", json={"tieu_de": "Kẹt", "brief": "ngắn", "phong": ["noi-dung"]})
    vid2 = v2.json()["viec"]["id"]
    p2 = Path(goc) / "nhac-truong" / "viec" / f"{vid2}.json"
    data = json.loads(p2.read_text(encoding="utf-8"))
    data["trang_thai"] = "dang_chay"
    p2.write_text(json.dumps(data), encoding="utf-8")
    xoa2 = c.delete(f"/nhac-truong/viec/{vid2}")
    check("api xoá việc kẹt không còn chạy", xoa2.status_code == 200 and not p2.is_file())


def test_sua_va_xoa():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng", "viết", "truong")
    nt.them_nguoi(kho, "noi-dung", "Lan", "ngắn", "một", "thanh_vien")
    p = nt.sua_phong(kho, "noi-dung", "Rõ hơn, không bịa")
    check("sửa tiêu chí", p["tieu_chi"] == "Rõ hơn, không bịa")
    try:
        nt.sua_phong(kho, "noi-dung", "  ")
        check("tiêu chí trống", False)
    except nt.LoiNhacTruong:
        check("tiêu chí trống", True)
    n = nt.sua_nguoi(kho, "noi-dung", "lan", tinh_cach="ấm", skills="sửa bài, đọc")
    check("sửa người giữ chữ", n["tinh_cach"] == "ấm" and n["skills"] == ["sửa bài", "đọc"])
    nt.sua_nguoi(kho, "noi-dung", "lan", vai="truong", vi_tri="Chuyên viên nội dung")
    phong = kho.doc_phong("noi-dung")
    truong = [n["slug"] for n in phong["nguoi"] if n.get("vai") == "truong"]
    lan = next(n for n in phong["nguoi"] if n["slug"] == "lan")
    check("sửa được vị trí, vẫn một trưởng", truong == ["lan"] and lan["vi_tri"] == "Chuyên viên nội dung")
    doi = nt.sua_nguoi(kho, "noi-dung", "lan", ten="Lan Phương")
    check("đổi tên hiển thị, giữ slug", doi["ten"] == "Lan Phương" and doi["slug"] == "lan")
    viec = nt.tao_viec(kho, "Xoá", "brief đủ", ["noi-dung"])
    md = Path(kho.goc) / "viec" / f"{viec['id']}.md"
    md.write_text("biên bản", encoding="utf-8")
    viec["trang_thai"] = "dang_chay"
    kho.luu_viec(viec)
    try:
        nt.xoa_viec(kho, viec["id"])
        check("không xoá khi đang chạy", False)
    except nt.LoiNhacTruong:
        check("không xoá khi đang chạy", True)
    nt.xoa_viec(kho, viec["id"], force=True)
    con = Path(kho.goc) / "viec" / f"{viec['id']}.json"
    check("xoá được việc kẹt", not con.is_file() and not md.is_file())


def test_tra_thieu_ve_phong_nguoi_noi():
    kho = nt.Kho(tempfile.mkdtemp())
    asyncio.run(dung_phong(kho))
    viec = nt.tao_viec(kho, "Trả về đúng phòng", "một brief", ["phap-che", "noi-dung"], 2)

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        if kind == "HOP" and nguoi["slug"] == "an":
            return "QUYET: CHUA\nSUA: còn yếu"
        if kind in ("HOP", "KIEM"):
            return "QUYET: DAT"
        return "bản ổn"

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    lan = sum(1 for r in xong["loi"] if r["slug"] == "lan" and r["lop"] == "lam")
    minh = sum(1 for r in xong["loi"] if r["slug"] == "minh" and r["lop"] == "lam")
    check("thiếu TRA thì sửa đúng phòng người nói", lan == 2 and minh == 1)


def test_mat_phong_va_loi_khac_khong_ket():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng", "", "truong")
    viec = nt.tao_viec(kho, "Mất phòng", "brief đủ", ["noi-dung"])
    kho.xoa_phong("noi-dung")
    xong = asyncio.run(nt.chay(kho, viec["id"], nt.noi_thu))
    check("mất phòng thì lỗi, không kẹt đang chạy", xong["trang_thai"] == "loi" and "Không có phòng" in xong["loi_chay"])

    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng", "", "truong")
    viec = nt.tao_viec(kho, "Đứt", "brief đủ", ["noi-dung"])

    async def dut(_n, _p):
        raise RuntimeError("đứt")

    xong = asyncio.run(nt.chay(kho, viec["id"], dut))
    check("lỗi lạ không kẹt đang chạy", xong["trang_thai"] == "loi" and "đứt" in xong["loi_chay"])


def test_loi_noi_khong_bia_dat():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng", "", "truong")

    async def noi(_n, _p):
        raise nt.LoiNoi("Chưa có model.")

    viec = nt.tao_viec(kho, "Gãy", "brief đủ dài", ["noi-dung"])
    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("model gãy thì lỗi, không đạt", xong["trang_thai"] == "loi" and xong["dat"]["noi-dung"] is False)


def test_doc_thu_tu():
    mems = [
        {"slug": "binh", "ten": "Bình", "vai": "thanh_vien", "vi_tri": "Nghiên cứu"},
        {"slug": "chi", "ten": "Chi", "vai": "thanh_vien", "vi_tri": "Content"},
    ]
    check("trưởng đảo bước", [m["slug"] for m in nt.doc_thu_tu("THU_TU: chi > binh", mems)] == ["chi", "binh"])
    check("trưởng bỏ người không cần", [m["slug"] for m in nt.doc_thu_tu("xong\nTHU_TU: chi", mems)] == ["chi"])
    check("không xếp thì giữ quy trình", [m["slug"] for m in nt.doc_thu_tu("làm theo phòng", mems)] == ["binh", "chi"])
    check("nhận ok", nt.doc_nhan("ổn\nNHAN: OK") == "OK")
    check("thiếu nhận là chưa", nt.doc_nhan("tạm được") == "")


def test_lan_luot_ban_giao():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Marketing", "Đúng brief", "lan_luot")
    nt.them_nguoi(kho, "marketing", "An", "ngắn", "", "truong", vi_tri="Trưởng marketing")
    nt.them_nguoi(kho, "marketing", "Bình", "soi số", "", "thanh_vien", vi_tri="Nghiên cứu")
    nt.them_nguoi(kho, "marketing", "Chi", "viết", "", "thanh_vien", vi_tri="Content")
    nt.doi_cho(kho, "marketing", "chi", "len")
    thu_tu = [n["ten"] for n in kho.doc_phong("marketing")["nguoi"] if n["vai"] != "truong"]
    check("đưa bước lên", thu_tu == ["Chi", "Bình"])
    nt.doi_cho(kho, "marketing", "chi", "xuong")
    thay = []
    lan = {"n": 0}

    async def noi(nguoi, prompt):
        dang = kho.doc_viec(viec["id"]).get("dang_lam") or {}
        thay.append(dang.get("ten"))
        kind = loai(prompt)
        if kind == "KIEM":
            return "QUYET: DAT"
        if kind == "GIAO":
            check("trưởng thấy quy trình và việc", "slug binh" in prompt and "một bài" in prompt)
            return "Nghiên cứu rồi mới viết.\nTHU_TU: binh > chi"
        if kind == "NHAN" and nguoi["slug"] == "chi":
            lan["n"] += 1
            if lan["n"] == 1:
                return "Thiếu nguồn.\nNHAN: CHUA\nSUA: Thêm nguồn."
            check("content thấy nguồn rồi mới nhận", "khảo sát" in prompt)
            return "Nguồn ổn.\nNHAN: OK"
        if kind == "DOI" and nguoi["slug"] == "binh":
            return "Insight: khách đọc buổi tối. Nguồn: khảo sát 12 người."
        if kind == "LAM" and nguoi["slug"] == "binh":
            return "Insight: khách đọc buổi tối."
        if kind == "LAM" and nguoi["slug"] == "chi":
            check("content chỉ làm sau khi nhận", "BƯỚC TRƯỚC ĐÃ CHỐT" in prompt and "khảo sát" in prompt)
            return "Bài ngắn theo insight."
        return "tiếp"

    viec = nt.tao_viec(kho, "Bài ra mắt", "một bài, không hứa", ["marketing"], 2)
    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    loi = [(r["slug"], r["lop"], r.get("quyet") or "") for r in xong["loi"]]
    check("cãi xong mới làm bước sau", loi == [
        ("an", "giao", ""),
        ("binh", "lam", ""),
        ("chi", "nhan", "CHUA"),
        ("binh", "doi", ""),
        ("chi", "nhan", "OK"),
        ("chi", "lam", ""),
        ("an", "kiem", "DAT"),
    ])
    check("trưởng xếp đúng người", [n["slug"] for n in xong["xep"]["marketing"]] == ["binh", "chi"])
    check("trang thấy người đang nói", thay[:3] == ["An", "Bình", "Chi"])
    check("hết việc thì không còn người đang làm", xong.get("dang_lam") is None and xong["trang_thai"] == "xong")


def test_tran_muoi_va_dung_som():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Lan", "", "", "thanh_vien")
    cao = nt.tao_viec(kho, "Trần", "brief đủ", ["noi-dung"], 99)
    check("trần vòng là 10", cao["vong_toi_da"] == 10)
    mac = nt.tao_viec(kho, "Mặc định", "brief đủ", ["noi-dung"])
    check("mặc định 6 vòng", mac["vong_toi_da"] == 6)

    async def dat_ngay(nguoi, prompt):
        if loai(prompt) == "KIEM":
            return "QUYET: DAT"
        return "bản ổn"

    som = asyncio.run(nt.chay(kho, cao["id"], dat_ngay))
    check("hết lỗi thì dừng ở vòng 1", som["trang_thai"] == "xong" and sum(1 for r in som["loi"] if r["lop"] == "kiem") == 1)

    lap = {"n": 0}

    async def lap_loi(nguoi, prompt):
        if loai(prompt) == "KIEM":
            lap["n"] += 1
            return "QUYET: CHUA\nSUA: Thiếu nguồn."
        return "bản vẫn thiếu nguồn"

    ket = asyncio.run(nt.chay(kho, mac["id"], lap_loi))
    check("cùng một lỗi thì không đốt hết 6 vòng", lap["n"] == 2 and ket["trang_thai"] == "lech")


def test_sua_viec_dang_soan():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "", "", "truong")
    viec = nt.tao_viec(kho, "Bài", "brief cũ", ["noi-dung"], 2)
    sua = nt.sua_viec(kho, viec["id"], "Bài sửa", "brief mới", ["noi-dung"], 8)
    check("sửa việc đang soạn giữ id", sua["id"] == viec["id"] and sua["brief"] == "brief mới" and sua["vong_toi_da"] == 8)
    viec["trang_thai"] = "xong"
    kho.luu_viec(viec)
    try:
        nt.sua_viec(kho, viec["id"], "Lại", "brief", ["noi-dung"])
        check("việc đã chạy không soạn lại", False)
    except nt.LoiNhacTruong:
        check("việc đã chạy không soạn lại", True)


def test_het_lan_cai_thi_truong_phan():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Marketing", "Đúng brief", "lan_luot")
    nt.them_nguoi(kho, "marketing", "An", "", "", "truong")
    nt.them_nguoi(kho, "marketing", "Bình", "", "", "thanh_vien")
    nt.them_nguoi(kho, "marketing", "Chi", "", "", "thanh_vien")

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        if kind == "KIEM":
            return "QUYET: DAT"
        if kind == "GIAO":
            return "THU_TU: binh > chi"
        if kind == "NHAN":
            return "NHAN: CHUA\nSUA: sai số"
        if kind == "XU":
            return "QUYET: LAM"
        return "bản đã chỉnh"

    viec = nt.tao_viec(kho, "Bài", "một bài ngắn", ["marketing"], 1)
    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("hết lần cãi thì trưởng cho đi tiếp", [r["lop"] for r in xong["loi"]] == [
        "giao", "lam", "nhan", "doi", "xu", "lam", "kiem",
    ])


def test_gon_khong_dan_ca_bai():
    dai = "Trọng tâm bài này. " + ("lặp lại cho dài " * 80) + "\n1. Bỏ câu hứa\n2. Thêm nguồn"
    nguoi = {"ten": "An", "vai": "truong", "tinh_cach": "", "skills": [], "vi_tri": ""}
    phong = {"ten": "Nội dung", "tieu_chi": "Rõ", "slug": "noi-dung"}
    viec = {"tieu_de": "Bài", "brief": "ngắn"}
    p = nt.lap_prompt("DOI", nguoi, phong, viec, ban=dai, lenh="thiếu nguồn", giao_cho={"ten": "Chi", "vai": "thanh_vien"})
    check("không dán cả bài dài", len(p) < len(dai))
    check("còn điểm sửa", "1. Bỏ câu hứa" in p and "2. Thêm nguồn" in p)
    check("bảo không viết lại cả bài", "Không viết lại cả bài" in p)
    lam = nt.lap_prompt("LAM", nguoi, phong, viec, ban=dai)
    check("bước sau không được chép cả bài", "Không chép bản trước" in lam and len(lam) < 1800)
    dau = nt.lap_prompt("LAM", nguoi, phong, viec)
    check("bản đầu viết đủ", "bản đầu" in dau and "Không viết hết" not in dau)
    ket = nt.lap_prompt("KET", nguoi, phong, viec, cac_ban={"noi-dung": dai + "\nMOC-CUOI"})
    check("kết quả nhận đủ bản", "MOC-CUOI" in ket)


def test_phong_trao_doi():
    kho = nt.Kho(tempfile.mkdtemp())
    asyncio.run(dung_phong(kho))
    nt.them_nguoi(kho, "noi-dung", "Bình", "ngắn", "soat", "thanh_vien")
    viec = nt.tao_viec(kho, "Đối thoại", "một brief", ["noi-dung", "phap-che"], 1)

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        if kind == "KIEM":
            return "QUYET: DAT"
        if kind == "HOP":
            return "QUYET: DAT"
        if kind == "CHIA":
            return "Bản phòng kia còn một câu chưa có căn cứ."
        if kind == "DAP":
            return "Giữ phần đúng brief. Câu đó sẽ bỏ."
        return "bản ổn"

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    lops = [r["lop"] for r in xong["loi"]]
    check("trưởng góp ý phòng kia", "chia" in lops and "dap" in lops)
    check("người cùng phòng trao đổi trước khi chốt", "gop" in lops)
    check("họp vẫn chốt sau khi đã nói", xong["trang_thai"] == "xong" and lops.index("chia") < lops.index("hop"))


def test_file_dung_va_chay_them():
    kho = nt.Kho(tempfile.mkdtemp())
    asyncio.run(dung_phong(kho))
    nt.sua_phong(kho, "noi-dung", ten="Nội dung mới", cach_lam="lan_luot")
    check("đổi tên phòng", kho.doc_phong("noi-dung")["ten"] == "Nội dung mới")
    viec = nt.tao_viec(kho, "Co file", "brief ngắn", ["noi-dung"], 1, tai_lieu=[
        {"ten": "a.md", "noi_dung": "nội dung A"},
        {"ten": "b.md", "noi_dung": "nội dung B"},
        {"ten": "c.md", "noi_dung": "nội dung C"},
        {"ten": "d.md", "noi_dung": "bỏ file thứ tư"},
    ], xep={"noi-dung": ["lan"]})
    check("tối đa 3 file", len(viec["tai_lieu"]) == 3 and viec["xep_khoa"] is True)

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        if kind == "KIEM":
            return "QUYET: DAT"
        if kind == "KET":
            return "Kết quả cuối đủ để dùng."
        if kind == "GIAO":
            return "THU_TU: minh > lan"
        return "Bản đầu đủ ý cho bước này."

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("có kết quả cuối", "Kết quả cuối" in (xong.get("ket_qua") or ""))
    giao = [r for r in xong["loi"] if r["lop"] == "giao"]
    check("giữ thứ tự đã khóa", giao and "Lan" in (giao[0].get("giao_cho") or ""))

    thay = []

    async def them(nguoi, prompt):
        kind = loai(prompt)
        if kind == "THEM":
            thay.append("COMMENT MUỐN SỬA" in prompt and "Kết quả cuối" in prompt)
            return "Điểm 1. Câu mở ngắn hơn."
        if kind == "KET":
            return "Kết quả đã sửa theo comment."
        return "ngắn"

    lai = asyncio.run(nt.chay_them(kho, viec["id"], them, "Sửa câu mở cho ngắn."))
    check("chạy thêm xong", lai["trang_thai"] == "xong" and lai["ket_qua"] == "Kết quả đã sửa theo comment.")
    check("prompt giữ kết quả cũ", any(thay))

    viec2 = nt.tao_viec(kho, "Dung giua", "brief", ["noi-dung"], 1)

    async def noi_dung(nguoi, prompt):
        ban = kho.doc_viec(viec2["id"])
        ban["huy"] = True
        kho.luu_viec(ban)
        return "bản dở"

    dung = asyncio.run(nt.chay(kho, viec2["id"], noi_dung))
    check("dừng giữa chừng", dung["trang_thai"] == "dung")
    check("dừng vẫn để bản nhìn được", "bản dở" in (dung.get("ket_qua") or "") or "Bản dở" in (dung.get("ket_qua") or ""))


if __name__ == "__main__":
    test_tao_va_chan_hai_truong()
    test_thieu_quyet_la_chua()
    test_noi_thu_xong()
    test_phap_che_chan_du_noi_bo_bo_qua()
    test_truong_khong_gat_ho_phong_khac()
    test_mot_phong()
    test_tra_thieu_ve_phong_nguoi_noi()
    test_mat_phong_va_loi_khac_khong_ket()
    test_api()
    test_sua_va_xoa()
    test_loi_noi_khong_bia_dat()
    test_doc_thu_tu()
    test_lan_luot_ban_giao()
    test_tran_muoi_va_dung_som()
    test_sua_viec_dang_soan()
    test_het_lan_cai_thi_truong_phan()
    test_gon_khong_dan_ca_bai()
    test_phong_trao_doi()
    test_file_dung_va_chay_them()
    if _fails:
        print(f"\n{len(_fails)} FAIL")
        sys.exit(1)
    print("\nOK - nhạc trưởng")
