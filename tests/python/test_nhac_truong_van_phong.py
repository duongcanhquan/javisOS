"""Kernel văn phòng dùng chung — ngoài từng việc."""
from __future__ import annotations

import asyncio
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


def test_van_phong_va_patch_prompt():
    kho = nt.Kho(tempfile.mkdtemp())
    nt.tao_phong(kho, "Nội dung", "Rõ", "lan_luot")
    nt.them_nguoi(kho, "noi-dung", "An", "", "", "truong")
    nt.them_nguoi(kho, "noi-dung", "Bình", "", "", "thanh_vien")
    vp0 = nt.dong_bo_van_phong(kho)
    check("seed phòng vào văn phòng", "noi-dung" in (vp0.get("phong") or {}))
    nguoi = (vp0["phong"]["noi-dung"].get("nguoi") or [])
    check("người idle lúc chưa chạy", nguoi and all(n.get("tt") == "idle" for n in nguoi))

    viec = nt.tao_viec(kho, "Bài ngắn", "viết một bài", ["noi-dung"], 2)
    async def noi(nguoi, prompt):
        kind = ""
        for ln in prompt.splitlines():
            if ln.startswith("LOAI:"):
                kind = ln.split(":", 1)[1].strip()
                break
        if kind == "GIAO":
            return "THU_TU: binh"
        if kind == "LAM":
            return "NOI: Bàn giao.\nFILE: a.md\n## Nguồn\ncũ\n## Than\nnội dung\nHET FILE"
        if kind == "NHAN":
            return "NHAN: OK"
        if kind == "KIEM":
            return "QUYET: DAT"
        return "ok"

    xong = asyncio.run(nt.chay(kho, viec["id"], noi))
    check("việc xong", xong.get("trang_thai") in ("xong", "lech"))
    vp = nt.doc_van_phong(kho)
    ban = ((vp.get("phong") or {}).get("noi-dung") or {}).get("ban") or ""
    check("bàn phòng giữ bản sau chạy", "Nguồn" in ban or "Than" in ban)

    # Việc mới kế thừa sổ nếu có
    vp["phong"]["noi-dung"]["so"] = [{"khoa": "ngan-sach", "gia_tri": "10tr", "nguon": "test"}]
    nt.luu_van_phong(kho, vp)
    viec2 = nt.tao_viec(kho, "Bài hai", "viết tiếp", ["noi-dung"], 1)
    check("việc mới nhận sổ phòng", any(f.get("khoa") == "ngan-sach" for f in (viec2.get("so") or [])))

    dai = "## Nguồn\n" + ("cũ " * 200) + "\n## Than\n" + ("giữ " * 200)
    p = nt.lap_prompt(
        "DOI",
        {"ten": "Bình", "vai": "thanh_vien", "skills": [], "tinh_cach": ""},
        {"ten": "Nội dung", "tieu_chi": "Rõ", "slug": "noi-dung"},
        {"tieu_de": "Bài", "brief": "x" * 2000},
        ban=dai,
        lenh="Sửa mục Nguồn cho đúng",
    )
    check("brief rút khi DOI", "Brief: " in p and len(p) < len(dai) + len("x" * 2000))
    check("DOI không nhét hết than", p.count("giữ ") < 50)


if __name__ == "__main__":
    test_van_phong_va_patch_prompt()
    print("PASS van_phong")
