"""Giai đoạn 3 và phối hợp: hai cổng duyệt, chạy tiếp từ chỗ dừng.

    python tests/python/test_nhac_truong_gd3.py
"""
import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-nt3-"))

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


def _phong(kho):
    nt.tao_phong(kho, "Nội dung", "Đủ ý")
    nt.tao_phong(kho, "Thiết kế", "Nộp món")
    nt.them_nguoi(kho, "noi-dung", "An", "thẳng", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Lan", "viết", "", "thanh_vien")
    nt.them_nguoi(kho, "thiet-ke", "Bình", "vẽ", "", "truong")
    nt.them_nguoi(kho, "thiet-ke", "Chi", "poster", "", "thanh_vien")
    nt.dat_khuon(kho, "noi-dung", ["nguon"])


def _noi(calls, thay):
    async def noi(nguoi, prompt):
        kind = loai(prompt)
        calls.append(nguoi.get("ten") + ":" + kind)
        if "Ý CHỈ ĐẠO" in prompt:
            thay.append(prompt)
        if "SỔ VIỆC" in prompt and nguoi.get("ten") == "Chi":
            thay.append("so:" + kind)
        if kind == "GIAO":
            return "Làm bản."
        if kind == "LAM" and nguoi.get("ten") == "Lan":
            return "NOI: đủ\nFILE: ban.md\n## nguon\nvăn bản\nFACT: doanh_thu = 12 tỷ\nHET FILE"
        if kind == "LAM":
            return "NOI: món\nFILE: ban.md\nMON: Poster | landscape | nền xanh\nHET FILE"
        if kind in ("KIEM", "HOP"):
            return "QUYET: DAT\nTRA: noi-dung"
        if kind == "KET":
            return "Xong."
        return "QUYET: DAT"
    return noi


def test_hai_cong_va_chay_tiep():
    kho = nt.Kho(tempfile.mkdtemp())
    _phong(kho)
    check("phòng thiết kế bị nhận ra", nt.loai_hang(kho.doc_phong("thiet-ke")) == "thiet_ke")
    viec = nt.tao_viec(kho, "Bài và poster", "Viết rồi vẽ", ["noi-dung", "thiet-ke"], vong=3, bat_cong=True)
    try:
        nt.duyet(kho, viec["id"], "sớm")
        check("duyệt khi không chờ thì bị chặn", False)
    except nt.LoiNhacTruong:
        check("duyệt khi không chờ thì bị chặn", True)
    calls, thay, tin = [], [], []

    async def bao(v):
        tin.append(v.get("cong") or "")

    noi = _noi(calls, thay)
    mot = asyncio.run(nt.chay(kho, viec["id"], noi, bao=bao))
    check("cổng 1 là kế hoạch", mot["trang_thai"] == "cho_duyet" and mot["cong"] == "ke_hoach")
    check("chưa ai làm khi chưa duyệt kế hoạch", not any(x.endswith(":LAM") for x in calls))
    check("telegram nhận đúng cổng kế hoạch", tin == ["ke_hoach"] and "kế hoạch" in nt.tin_cong(mot))
    goc_giao = next(r["loi"] for r in mot["loi"] if r["lop"] == "giao")
    lai = asyncio.run(nt.chay(kho, viec["id"], noi, bao=bao))
    check("chạy lại khi chưa duyệt thì vẫn đứng cổng", lai["cong"] == "ke_hoach" and lai["trang_thai"] == "cho_duyet")
    check("chưa duyệt thì không nói thêm", len(lai["loi"]) == len(mot["loi"]))
    nt.duyet(kho, viec["id"], "thêm số nguồn")
    hai = asyncio.run(nt.chay(kho, viec["id"], noi, bao=bao))
    check("cổng 2 trước thiết kế", hai["trang_thai"] == "cho_duyet" and hai["cong"] == "ban_thao")
    check("thiết kế chưa nói trước cổng 2", not any(x.startswith("Chi:") or x.startswith("Bình:") for x in calls))
    check("bản nội dung còn nguyên", "văn bản" in (hai["ban"].get("noi-dung") or ""))
    check("sổ đã có số trước khi vẽ", any(f.get("khoa") == "doanh-thu" for f in hai.get("so") or []))
    check("ý chỉ đạo đi vào lượt làm tiếp", any("thêm số nguồn" in p for p in thay))
    nt.duyet(kho, viec["id"], "nền xanh")
    ba = asyncio.run(nt.chay(kho, viec["id"], noi, bao=bao))
    check("duyệt xong thì việc xong", ba["trang_thai"] == "xong")
    check("lệnh giao đầu không bị xoá", any(r.get("lop") == "giao" and r.get("loi") == goc_giao for r in ba["loi"]))
    check("phòng vẽ thấy sổ việc", "so:LAM" in thay or "so:GIAO" in thay)
    check("telegram nhận cổng bản thảo", "ban_thao" in tin)


def test_api_cong():
    goc = tempfile.mkdtemp()
    app = FastAPI()
    rte.register(app, rte.Deps(brain_root=lambda _n: goc, noi=nt.noi_thu))
    c = TestClient(app)
    c.post("/nhac-truong/phong", json={"ten": "Nội dung", "tieu_chi": "Rõ"})
    c.post("/nhac-truong/phong/noi-dung/nguoi", json={"ten": "An", "vai": "truong"})
    c.post("/nhac-truong/phong/noi-dung/nguoi", json={"ten": "Lan"})
    k = c.post("/nhac-truong/phong/noi-dung/khuon", json={"truong": ["nguon", "so_lieu"], "ten": "Brief"})
    check("api lưu khuôn", k.status_code == 200 and k.json()["phong"]["khuon"]["truong"] == ["nguon", "so-lieu"])
    v = c.post("/nhac-truong/viec", json={
        "tieu_de": "Bài cổng", "brief": "ngắn", "phong": ["noi-dung"], "vong": 2, "bat_cong": True,
    })
    vid = v.json()["viec"]["id"]
    check("api bật cổng", v.json()["viec"]["bat_cong"] is True)
    chay = c.post(f"/nhac-truong/viec/{vid}/chay", json={"thu": True})
    body = chay.json()["viec"]
    check("chạy thử cũng dừng ở kế hoạch", body["trang_thai"] == "cho_duyet" and body["cong"] == "ke_hoach")
    du = c.post(f"/nhac-truong/viec/{vid}/duyet", json={"y": "giữ nguồn"})
    check("api đồng ý rồi chạy tiếp", du.status_code == 200 and du.json()["trang_thai"] == "dang_chay")
    trang = ""
    for _ in range(40):
        trang = c.get(f"/nhac-truong/viec/{vid}").json()["viec"]["trang_thai"]
        if trang != "dang_chay":
            break
    check("sau đồng ý thì không còn cổng kế hoạch", trang != "cho_duyet" and trang != "dang_chay")
    doc = c.get(f"/nhac-truong/viec/{vid}").json()["viec"]
    check("ý góp vẫn nằm trong việc", doc.get("y_kien") == "giữ nguồn")
    check("lời đã giao không bị xoá", any(r.get("lop") == "giao" for r in doc.get("loi") or []))


if __name__ == "__main__":
    test_hai_cong_va_chay_tiep()
    test_api_cong()
    if _fails:
        print("FAIL", _fails)
        raise SystemExit(1)
    print("OK - giai đoạn 3")
