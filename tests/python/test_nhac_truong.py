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
    v3 = c.post("/nhac-truong/viec", json={"tieu_de": "Mất tiến", "brief": "ngắn", "phong": ["noi-dung"]})
    vid3 = v3.json()["viec"]["id"]
    p3 = Path(goc) / "nhac-truong" / "viec" / f"{vid3}.json"
    mat = json.loads(p3.read_text(encoding="utf-8"))
    mat["trang_thai"] = "dang_chay"
    mat["loi"] = [{"ten": "An", "lop": "kiem", "loi": "QUYET: CHUA", "quyet": "CHUA", "phong": "noi-dung", "vai": "truong", "vong": 1}]
    p3.write_text(json.dumps(mat), encoding="utf-8")
    doc3 = c.get(f"/nhac-truong/viec/{vid3}")
    viec3 = doc3.json()["viec"]
    check("mất tiến thì thôi ghi đang chạy", doc3.status_code == 200 and viec3["trang_thai"] == "dung" and viec3["song"] is False)
    check("mất tiến vẫn giữ lời đã nói", any(r.get("quyet") == "CHUA" for r in viec3["loi"]) and "Chạy tiếp" in (viec3.get("loi_chay") or ""))


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


def test_hang_thiet_ke_va_lam_lai_mot_phong():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ")
    nt.them_nguoi(kho, "noi-dung", "An", "", "", "truong")
    nt.tao_phong(kho, "Thiết kế", "Đúng bộ")
    nt.them_nguoi(kho, "thiet-ke", "Bình", "", "thiết kế", "truong")
    check("phòng chữ không bị coi là thiết kế", nt.loai_hang(kho.doc_phong("noi-dung")) == "")
    check("phòng thiết kế nộp ảnh", nt.loai_hang(kho.doc_phong("thiet-ke")) == "thiet_ke")
    nt.tao_phong(kho, "Video", "Đúng nhịp")
    nt.them_nguoi(kho, "video", "Chi", "", "làm video", "truong")
    check("phòng video nộp video", nt.loai_hang(kho.doc_phong("video")) == "video")
    viec = nt.tao_viec(kho, "Bộ nhận diện", "Thiết kế theo bộ cho chiến dịch.", ["noi-dung", "thiet-ke"], 1)

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        if kind in ("KIEM", "HOP"):
            return "QUYET: DAT"
        if "nộp thiết kế" in prompt:
            return "MON: Bìa | landscape | nền xanh chữ trắng\nMON: Poster | portrait | cùng xanh\nMON: Icon | square | cùng xanh"
        if kind == "KET":
            return "Kết quả gồm nội dung và bộ thiết kế."
        return "Bản nội dung đã chốt, không đụng tới."

    async def ra(viec_id, phong, loai_f, ten, mo_ta, ti_le, script):
        p = Path(kho.goc) / "nhac-truong" / "viec" / viec_id / "hang" / phong
        p.mkdir(parents=True, exist_ok=True)
        f = p / ((nt.slugify(ten) or "mon") + ".txt")
        f.write_text(mo_ta or "", encoding="utf-8")
        return {"ok": True, "file": f.relative_to(Path(kho.goc)).as_posix(), "ten": ten}

    xong = asyncio.run(nt.chay(kho, viec["id"], noi, ra))
    bo = (xong.get("hang") or {}).get("thiet-ke") or []
    check("bộ có đủ món", len(bo) >= 3 and all(it.get("file") for it in bo))
    check("kết quả dẫn file", "Hàng đã nộp" in (xong.get("ket_qua") or "") and "thiet-ke/" in (xong.get("ket_qua") or ""))
    check("phòng chữ không sinh file", "noi-dung" not in (xong.get("hang") or {}))
    ban_nd = xong["ban"]["noi-dung"]
    thay = []

    async def noi2(nguoi, prompt):
        kind = loai(prompt)
        if kind in ("KIEM", "HOP"):
            return "QUYET: DAT"
        if "nộp thiết kế" in prompt:
            thay.append("HÀNG PHÒNG TRƯỚC" in prompt and "Bản nội dung đã chốt" in prompt)
            return "MON: Bìa | landscape | nền đỏ\nMON: Poster | portrait | cùng đỏ\nMON: Icon | square | cùng đỏ"
        if kind == "KET":
            return "Kết quả sau khi thiết kế làm lại."
        return "không được đụng phòng trước"

    lai = asyncio.run(nt.chay_them(kho, xong["id"], noi2, "Đổi bộ sang màu đỏ.", phong_lai="thiet-ke", ra_file=ra))
    check("làm lại một phòng vẫn xong", lai["trang_thai"] == "xong")
    check("phòng trước giữ nguyên bản", lai["ban"]["noi-dung"] == ban_nd)
    check("thiết kế thấy hàng phòng trước", any(thay))
    check("bộ mới theo comment", "đỏ" in " ".join(it.get("mo_ta") or "" for it in (lai.get("hang") or {}).get("thiet-ke") or []))


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
    dai = "Trọng tâm bài này. " + ("lặp lại cho dài " * 80) + "\n1. Bỏ câu hứa\n2. Thêm nguồn\nMOC-BAN"
    nguoi = {"ten": "An", "vai": "truong", "tinh_cach": "", "skills": [], "vi_tri": ""}
    phong = {"ten": "Nội dung", "tieu_chi": "Rõ", "slug": "noi-dung"}
    viec = {"tieu_de": "Bài", "brief": "ngắn"}
    p = nt.lap_prompt("DOI", nguoi, phong, viec, ban=dai, lenh="thiếu nguồn", giao_cho={"ten": "Chi", "vai": "thanh_vien"})
    check("bước sau đọc đủ bản", "MOC-BAN" in p and "lặp lại cho dài" in p)
    check("sửa thì trả lại cả file", "Viết lại cả file cho đủ" in p and "FILE:" in p)
    lam = nt.lap_prompt("LAM", nguoi, phong, viec, ban=dai)
    check("bước sau không chép file vào câu nói", "không chép nguyên file trước" in lam)
    check("bước sau nhận đủ bản trước", "MOC-BAN" in lam and "…" not in lam)
    dau = nt.lap_prompt("LAM", nguoi, phong, viec)
    check("bản đầu là file đủ", "FILE:" in dau and "HET FILE" in dau and "Không viết hết" not in dau)
    check("bản dài vẫn giữ", nt._cat("A" * 9000) == "A" * 9000)
    ket = nt.lap_prompt("KET", nguoi, phong, viec, cac_ban={"noi-dung": dai + "\nMOC-CUOI"})
    check("kết quả nhận đủ bản", "MOC-CUOI" in ket and "MOC-BAN" in ket)


def test_file_dinh_kem_khong_vao_hoi_thoai():
    dai = "NOI: Tôi bàn giao. Ông đọc file. Lưu ý: giữ số liệu.\nFILE: bao-cao.md\n" + ("Đoạn đủ. " * 40) + "MOC-FILE\nHET FILE"
    t = nt.tach_tra_loi(dai)
    check("câu nói không chứa bài dài", "MOC-FILE" not in t["noi"] and "bàn giao" in t["noi"])
    check("file giữ nguyên bài", "MOC-FILE" in t["tep"] and t["ban"].count("Đoạn đủ") == 40)

    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Đủ ý", "lan_luot")
    nt.them_nguoi(kho, "noi-dung", "An", "", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Bình", "", "", "thanh_vien")
    nt.them_nguoi(kho, "noi-dung", "Chi", "", "", "thanh_vien")
    thay = []
    lan = {"n": 0}

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        if kind == "KIEM":
            return "QUYET: DAT"
        if kind == "GIAO":
            return "THU_TU: binh > chi"
        if kind == "LAM" and nguoi["slug"] == "binh":
            return "NOI: Tôi bàn giao. Ông đọc file. Lưu ý: thêm nguồn.\nFILE: ban-binh.md\n" + ("Nội dung Bình. " * 30) + "MOC-BINH\nHET FILE"
        if kind == "NHAN" and nguoi["slug"] == "chi":
            lan["n"] += 1
            if lan["n"] == 1:
                thay.append("MOC-BINH" in prompt)
                return "NOI:\n- Thiếu nguồn\n- Câu mở chưa rõ\nFILE: ban-binh-note.md\n" + ("Nội dung Bình. " * 30) + "NOTE: thêm nguồn\nHET FILE\nNHAN: CHUA\nSUA: Thêm nguồn."
            return "NHAN: OK"
        if kind == "DOI" and nguoi["slug"] == "binh":
            thay.append("Thiếu nguồn" in prompt and "NOTE: thêm nguồn" in prompt)
            return "NOI: Đã sửa theo ý và bàn giao lại.\nFILE: ban-binh-sua.md\nNội dung Bình đã có nguồn. MOC-SUA\nHET FILE"
        if kind == "LAM" and nguoi["slug"] == "chi":
            thay.append("MOC-SUA" in prompt)
            return "NOI: Tôi bàn giao phần viết.\nFILE: ban-chi.md\nBài của Chi.\nHET FILE"
        if kind == "NHAN":
            return "NHAN: OK"
        return "tiếp"

    viec = nt.tao_viec(kho, "Bàn giao", "một bài", ["noi-dung"], 2)
    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    lam = [r for r in xong["loi"] if r["lop"] == "lam" and r["slug"] == "binh"]
    check("hội thoại không dán bài dài", lam and "MOC-BINH" not in lam[0]["loi"] and "bàn giao" in lam[0]["loi"])
    check("file nằm ở đính kèm", lam and "MOC-BINH" in (lam[0].get("tep") or {}).get("noi_dung", ""))
    check("người sau đọc file, không đọc câu cụt", thay[:3] == [True, True, True])
    check("bản phòng giữ bài đã sửa", "MOC-SUA" in (xong.get("ban") or {}).get("noi-dung", ""))


def test_du_an_dai_khong_dut():
    cu = "Mở đầu dự án.\n" + ("Đoạn đã chốt. " * 200) + "\nCUỐI-CŨ"
    moi = "Chỉ sửa câu đầu."
    giu = nt._giu_ban(cu, moi)
    check("bản dài không bị thay bằng một câu", giu == cu)
    y = nt.y_phan_hoi("QUYET: CHUA\n- Thiếu mục 2\n- Sai số bảng 4\nSUA: xem các dòng trên")
    check("phản hồi giữ hết ý", "Thiếu mục 2" in y and "Sai số bảng 4" in y and "QUYET" not in y)
    dai = "Câu mở ngắn.\n" + ("Nội dung rất dài của dự án. " * 80) + "MỐC-CUỐI"
    t = nt.tach_tra_loi(dai, giau=True)
    check("hội thoại chỉ lấy ý đầu", "MỐC-CUỐI" not in t["noi"] and "Câu mở ngắn" in t["noi"])
    check("file ngầm giữ đến cuối", t["ban"].endswith("MỐC-CUỐI") and "MỐC-CUỐI" in t["tep"])

    async def noi(_nguoi, prompt):
        if "Viết TIẾP" in prompt:
            return "phần tiếp theo hết bài.\nHET FILE"
        return "NOI: Bàn giao bản dài.\nFILE: du-an.md\nPhần đầu của dự án.\n⚠️ Phản hồi bị cắt do hết max_tokens. Nhắn 'tiếp tục' để model viết tiếp."

    ghep = asyncio.run(nt._goi_du(noi, {"ten": "An"}, "viết bản"))
    check("bị cắt thì viết tiếp và ghép", "Phần đầu của dự án" in ghep and "phần tiếp theo hết bài" in ghep)
    check("không lưu câu báo bị cắt", "bị cắt" not in ghep and "HET FILE" in ghep)


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


def test_chat_hoi_phong_roi_moi_giao():
    ds = [
        {"slug": "marketing", "ten": "Marketing", "nguoi": [{"ten": "An", "vai": "truong"}]},
        {"slug": "phap-che", "ten": "Pháp chế", "nguoi": [{"ten": "Bình", "vai": "truong"}]},
    ]
    mot, hoi = nt.chon_phong(ds, "")
    check("chưa chỉ phòng thì hỏi", not mot and "Marketing" in hoi and "Pháp chế" in hoi)
    mot, hoi = nt.chon_phong(ds, "phòng")
    check("tên không khớp đúng thì không đoán", not mot and "đừng đoán" in hoi)
    mot, hoi = nt.chon_phong(ds, "Marketing")
    check("đúng tên thì chọn một phòng", [p["slug"] for p in mot] == ["marketing"] and not hoi)
    mot, hoi = nt.chon_phong([ds[0]], "")
    check("chỉ một phòng thì dùng phòng đó", mot and mot[0]["slug"] == "marketing")

    import importlib.util
    p = ROOT / "system" / "plugins" / "javis-nhac-truong" / "plugin.py"
    spec = importlib.util.spec_from_file_location("javis_nhac_truong_plugin", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    goc = Path(tempfile.mkdtemp(prefix="javis-nt-chat-"))
    kho = nt.Kho(goc)
    nt.tao_phong(kho, "Marketing", "Đúng khách")
    nt.tao_phong(kho, "Pháp chế", "Không hứa quá")
    nt.them_nguoi(kho, "marketing", "An", "thẳng", "", "truong")
    nt.them_nguoi(kho, "phap-che", "Bình", "chặt", "", "truong")

    class Ctx:
        vault_root = str(goc)

    hoi = asyncio.run(mod._chay({"op": "giao", "title": "Bài", "brief": "viết bài"}, Ctx()))
    check("tool chưa rõ phòng thì hỏi", "Hỏi" in hoi and not list((goc / "nhac-truong" / "viec").glob("*.json")))
    da_chay = {}
    cu = rte.bat_chay

    def gia(brain, vid):
        da_chay["vid"] = vid
        da_chay["brain"] = brain
        return "bat"

    rte.bat_chay = gia
    try:
        tra = asyncio.run(mod._chay({
            "op": "giao", "title": "Bài tuần", "brief": "viết bài ngắn", "phong": "Marketing",
        }, Ctx()))
    finally:
        rte.bat_chay = cu
    check("giao đúng phòng thì chạy", da_chay.get("vid") == "bai-tuan" and "Marketing" in tra and "Theo dõi" in tra)
    check("cùng brain đang chat", da_chay.get("brain") == str(goc))


def test_chay_lai_noi_cho_dung():
    kho = nt.Kho(tempfile.mkdtemp())
    p = nt.tao_phong(kho, "Nội dung", "Rõ ý", "lan_luot")
    nt.them_nguoi(kho, p["slug"], "An", "thẳng", "", "truong")
    nt.them_nguoi(kho, p["slug"], "Lan", "viết ngắn", "", "thanh_vien")
    nt.them_nguoi(kho, p["slug"], "Bình", "chỉnh", "", "thanh_vien")
    viec = nt.tao_viec(kho, "Bài dở", "viết bài", [p["slug"]], 2)
    viec["trang_thai"] = "dung"
    viec["loi"] = [
        {"phong": p["slug"], "slug": "an", "ten": "An", "vai": "truong", "lop": "giao",
         "vong": 1, "loi": "THU_TU: lan > binh", "quyet": "", "giao_cho": "Lan"},
        {"phong": p["slug"], "slug": "lan", "ten": "Lan", "vai": "thanh_vien", "lop": "lam",
         "vong": 1, "loi": "Mở bài của Lan.", "quyet": "",
         "tep": {"ten": "a.md", "noi_dung": "Mở bài đầy đủ của Lan, đủ dài."}},
    ]
    viec["ban"] = {p["slug"]: "[Lan]\nMở bài đầy đủ của Lan, đủ dài."}
    viec["khoa"] = {p["slug"]: False}
    viec["dat"] = {p["slug"]: False}
    kho.luu_viec(viec)
    seen = []

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        seen.append((nguoi["slug"], kind, prompt))
        if kind == "NHAN":
            return "NHAN: OK"
        if kind == "KIEM":
            return "QUYET: DAT"
        if kind == "KET":
            return "Kết quả nối từ bản Lan."
        if kind == "LAM":
            return "Phần của " + nguoi["ten"]
        return "tiếp"

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("chạy lại thì xong", xong["trang_thai"] == "xong")
    check("không giao lại từ đầu", seen and seen[0][1] != "GIAO")
    check("người sau làm tiếp", ("binh", "LAM") in [(s, k) for s, k, _ in seen])
    check("người đã làm không làm lại", ("lan", "LAM") not in [(s, k) for s, k, _ in seen])
    check("giữ lời đã nói", any(r.get("loi") == "Mở bài của Lan." for r in xong["loi"]))
    check("người sau thấy bản trước", any("Mở bài đầy đủ của Lan" in pmt for _, k, pmt in seen if k in ("NHAN", "LAM")))

    chua = nt.tao_viec(kho, "Bài chưa đạt", "viết lại", [p["slug"]], 3)
    chua["trang_thai"] = "dung"
    chua["loi"] = [
        {"phong": p["slug"], "slug": "an", "ten": "An", "vai": "truong", "lop": "kiem",
         "vong": 1, "loi": "QUYET: CHUA\nSUA: Bỏ câu hứa.", "quyet": "CHUA"},
    ]
    chua["ban"] = {p["slug"]: "Bản vòng một còn câu hứa."}
    chua["khoa"] = {p["slug"]: False}
    chua["dat"] = {p["slug"]: False}
    kho.luu_viec(chua)
    sua = []

    async def noi_sua(nguoi, prompt):
        kind = loai(prompt)
        if kind == "LAM":
            sua.append("Bỏ câu hứa" in prompt)
            return "Bản sửa, đã bỏ câu hứa."
        if kind == "GIAO":
            return "THU_TU: lan > binh"
        if kind == "NHAN":
            return "NHAN: OK"
        if kind == "KIEM":
            return "QUYET: DAT"
        if kind == "KET":
            return "Đã bỏ câu hứa."
        return "Bản sửa."

    lai = asyncio.run(nt.chay(kho, chua["id"], noi_sua))
    check("chưa đạt thì sửa tiếp", lai["trang_thai"] == "xong" and any(sua))
    check("giữ lời chưa đạt", any(r.get("quyet") == "CHUA" for r in lai["loi"]))
    check("vòng sửa là vòng sau", any(r.get("lop") == "giao" and int(r.get("vong") or 0) == 2 for r in lai["loi"]))


def test_hop_dung_khong_noi_lai():
    kho = nt.Kho(tempfile.mkdtemp())
    a = nt.tao_phong(kho, "Nội dung", "Rõ")
    b = nt.tao_phong(kho, "Pháp chế", "Chặt")
    nt.them_nguoi(kho, a["slug"], "An", "", "", "truong")
    nt.them_nguoi(kho, b["slug"], "Hà", "", "", "truong")
    viec = nt.tao_viec(kho, "Bài họp", "brief", [a["slug"], b["slug"]], 2)
    viec["trang_thai"] = "dang_chay"
    viec["khoa"] = {a["slug"]: True, b["slug"]: True}
    viec["dat"] = {a["slug"]: False, b["slug"]: False}
    viec["ban"] = {a["slug"]: "Bản nội dung", b["slug"]: "Bản pháp chế"}
    viec["loi"] = [
        {"phong": a["slug"], "slug": "an", "lop": "kiem", "vong": 1, "loi": "QUYET: DAT", "quyet": "DAT"},
        {"phong": b["slug"], "slug": "ha", "lop": "kiem", "vong": 1, "loi": "QUYET: DAT", "quyet": "DAT"},
        {"phong": a["slug"], "slug": "an", "lop": "chia", "vong": 1, "loi": "Bỏ câu hứa bên pháp chế.", "quyet": ""},
    ]
    kho.luu_viec(viec)
    seen = []

    async def noi(nguoi, prompt):
        kind = loai(prompt)
        seen.append((nguoi["slug"], kind))
        if kind == "HOP":
            return "QUYET: DAT"
        if kind == "KET":
            return "Kết quả sau họp."
        if kind == "DAP":
            return "Đã nghe góp ý."
        if kind == "CHIA":
            return "Góp lại."
        return "không được gọi " + kind

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("file đang chạy dở vẫn nối", xong["trang_thai"] == "xong")
    check("không góp lại câu đã nói", ("an", "CHIA") not in seen)
    check("không xếp lại phòng đã xong", ("an", "GIAO") not in seen and ("ha", "GIAO") not in seen)
    check("người chưa đáp thì đáp", ("ha", "DAP") in seen)
    check("giữ góp ý cũ", sum(1 for r in xong["loi"] if r.get("loi") == "Bỏ câu hứa bên pháp chế.") == 1)


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
    test_hang_thiet_ke_va_lam_lai_mot_phong()
    test_het_lan_cai_thi_truong_phan()
    test_gon_khong_dan_ca_bai()
    test_file_dinh_kem_khong_vao_hoi_thoai()
    test_du_an_dai_khong_dut()
    test_phong_trao_doi()
    test_file_dung_va_chay_them()
    test_chat_hoi_phong_roi_moi_giao()
    test_chay_lai_noi_cho_dung()
    test_hop_dung_khong_noi_lai()
    if _fails:
        print(f"\n{len(_fails)} FAIL")
        sys.exit(1)
    print("\nOK - nhạc trưởng")
