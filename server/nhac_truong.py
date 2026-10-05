"""Nhạc trưởng: phòng ban, trưởng phòng, họp liên phòng, biên bản.

Cơ chế mượn từ CrewAI hierarchical và AutoGen group chat, không nhúng runtime của họ.
Trưởng phòng giao việc và chặn bản phòng. Liên phòng chỉ các trưởng phòng nói.
Mỗi trưởng chỉ được ghi Đạt cho tiêu chí phòng mình. Trần vòng để khỏi chạy mãi.

Phần này không gọi model. `noi(nguoi, prompt)` do chỗ gọi đưa vào, nên test chạy không cần API.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

VONG_MAC_DINH = 2
VONG_TRAN = 4
LOI_TRAN = 8000


class LoiNhacTruong(ValueError):
    pass


class LoiNoi(RuntimeError):
    """Model không trả lời được. Việc dừng, không bịa bản đạt."""


def slugify(s: str) -> str:
    t = unicodedata.normalize("NFD", str(s or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("đ", "d").replace("Đ", "D")
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:48]


def _slug_ok(s: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", s or ""))


def doc_quyet(text: str) -> dict:
    """Đọc quyết định. Thiếu dòng QUYET thì coi là chưa đạt, không được lọt."""
    quyet, sua, tra = "", [], ""
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        head, _, rest = line.partition(":")
        rest = rest.strip()
        key = _khong_dau(head).strip().upper()
        if key == "QUYET":
            v = _khong_dau(rest).upper()
            if v.startswith("DAT"):
                quyet = "DAT"
            elif v.startswith("CHUA"):
                quyet = "CHUA"
        elif key == "SUA":
            if rest.strip():
                sua.append(rest.strip())
        elif key == "TRA":
            tra = slugify(rest)
    return {"quyet": quyet, "sua": " ".join(sua).strip(), "tra": tra}


def _khong_dau(s: str) -> str:
    t = unicodedata.normalize("NFD", str(s or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.replace("đ", "d").replace("Đ", "D")


class Kho:
    def __init__(self, brain: str | Path):
        self.brain = Path(brain)
        self.goc = self.brain / "nhac-truong"

    def _phong_path(self, slug: str) -> Path:
        if not _slug_ok(slug):
            raise LoiNhacTruong("Slug phòng không hợp lệ.")
        return self.goc / "phong" / f"{slug}.json"

    def _viec_path(self, vid: str) -> Path:
        if not _slug_ok(vid):
            raise LoiNhacTruong("Mã việc không hợp lệ.")
        return self.goc / "viec" / f"{vid}.json"

    def ds_phong(self) -> list:
        d = self.goc / "phong"
        if not d.is_dir():
            return []
        out = []
        for f in sorted(d.glob("*.json")):
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return out

    def doc_phong(self, slug: str) -> dict:
        p = self._phong_path(slug)
        if not p.is_file():
            raise LoiNhacTruong("Không có phòng này.")
        return json.loads(p.read_text(encoding="utf-8"))

    def luu_phong(self, phong: dict) -> None:
        p = self._phong_path(phong["slug"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(phong, ensure_ascii=False, indent=2), encoding="utf-8")

    def xoa_phong(self, slug: str) -> None:
        p = self._phong_path(slug)
        if p.is_file():
            p.unlink()

    def ds_viec(self) -> list:
        d = self.goc / "viec"
        if not d.is_dir():
            return []
        out = []
        for f in sorted(d.glob("*.json")):
            try:
                v = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            out.append({
                "id": v.get("id"),
                "tieu_de": v.get("tieu_de"),
                "trang_thai": v.get("trang_thai"),
                "phong": v.get("phong") or [],
            })
        return out

    def doc_viec(self, vid: str) -> dict:
        p = self._viec_path(vid)
        if not p.is_file():
            raise LoiNhacTruong("Không có việc này.")
        return json.loads(p.read_text(encoding="utf-8"))

    def luu_viec(self, viec: dict) -> None:
        p = self._viec_path(viec["id"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(viec, ensure_ascii=False, indent=2), encoding="utf-8")
        md = self.goc / "viec" / f"{viec['id']}.md"
        md.write_text(bien_ban(viec), encoding="utf-8")


def tao_phong(kho: Kho, ten: str, tieu_chi: str = "") -> dict:
    ten = (ten or "").strip()
    if not ten:
        raise LoiNhacTruong("Phòng cần một tên.")
    slug = slugify(ten)
    if not slug:
        raise LoiNhacTruong("Tên phòng không tạo được mã.")
    if (kho.goc / "phong" / f"{slug}.json").is_file():
        raise LoiNhacTruong("Đã có phòng trùng tên.")
    phong = {
        "slug": slug,
        "ten": ten,
        "tieu_chi": (tieu_chi or "").strip() or "Đúng brief, không bịa.",
        "nguoi": [],
    }
    kho.luu_phong(phong)
    return phong


def them_nguoi(kho: Kho, phong_slug: str, ten: str, tinh_cach: str = "",
               skills: str = "", vai: str = "thanh_vien", agent: str = "") -> dict:
    phong = kho.doc_phong(phong_slug)
    ten = (ten or "").strip()
    if not ten:
        raise LoiNhacTruong("Người cần một tên.")
    ns = slugify(ten)
    if not ns:
        raise LoiNhacTruong("Tên không tạo được mã.")
    if any(n.get("slug") == ns for n in phong["nguoi"]):
        raise LoiNhacTruong("Phòng đã có người trùng tên.")
    vai = (vai or "thanh_vien").strip()
    if vai not in ("truong", "thanh_vien"):
        raise LoiNhacTruong("Vai chỉ là trưởng phòng hoặc thành viên.")
    if vai == "truong" and any(n.get("vai") == "truong" for n in phong["nguoi"]):
        raise LoiNhacTruong("Mỗi phòng một trưởng phòng.")
    nguoi = {
        "slug": ns,
        "ten": ten,
        "vai": vai,
        "tinh_cach": (tinh_cach or "").strip()[:400],
        "skills": _tach_skill(skills),
        "agent": slugify(agent) if (agent or "").strip() else "",
    }
    phong["nguoi"].append(nguoi)
    kho.luu_phong(phong)
    return nguoi


def xoa_nguoi(kho: Kho, phong_slug: str, nguoi_slug: str) -> None:
    phong = kho.doc_phong(phong_slug)
    phong["nguoi"] = [n for n in phong["nguoi"] if n.get("slug") != nguoi_slug]
    kho.luu_phong(phong)


def _tach_skill(skills) -> list:
    if isinstance(skills, (list, tuple)):
        skills = ", ".join(str(x) for x in skills)
    sk = []
    seen = set()
    for raw in re.split(r"[,;\n]", str(skills or "")):
        s = raw.strip()[:40]
        key = s.lower()
        if s and key not in seen:
            seen.add(key)
            sk.append(s)
        if len(sk) >= 8:
            break
    return sk


def sua_phong(kho: Kho, slug: str, tieu_chi: str) -> dict:
    phong = kho.doc_phong(slug)
    tieu = (tieu_chi or "").strip()
    if not tieu:
        raise LoiNhacTruong("Tiêu chí không được trống.")
    phong["tieu_chi"] = tieu[:500]
    kho.luu_phong(phong)
    return phong


def sua_nguoi(kho: Kho, phong_slug: str, nguoi_slug: str, tinh_cach=None,
              skills=None, vai=None) -> dict:
    phong = kho.doc_phong(phong_slug)
    nguoi = next((n for n in phong["nguoi"] if n.get("slug") == nguoi_slug), None)
    if not nguoi:
        raise LoiNhacTruong("Không có người này.")
    if vai is not None:
        vai = (vai or "thanh_vien").strip()
        if vai not in ("truong", "thanh_vien"):
            raise LoiNhacTruong("Vai chỉ là trưởng phòng hoặc thành viên.")
        if vai == "truong" and any(
            n.get("vai") == "truong" and n.get("slug") != nguoi_slug for n in phong["nguoi"]
        ):
            raise LoiNhacTruong("Mỗi phòng một trưởng phòng.")
        nguoi["vai"] = vai
    if tinh_cach is not None:
        nguoi["tinh_cach"] = str(tinh_cach or "").strip()[:400]
    if skills is not None:
        nguoi["skills"] = _tach_skill(skills)
    kho.luu_phong(phong)
    return nguoi


def xoa_viec(kho: Kho, vid: str, force: bool = False) -> None:
    viec = kho.doc_viec(vid)
    if viec.get("trang_thai") == "dang_chay" and not force:
        raise LoiNhacTruong("Việc đang chạy, chưa xoá được.")
    p = kho._viec_path(vid)
    if p.is_file():
        p.unlink()
    md = kho.goc / "viec" / f"{vid}.md"
    if md.is_file():
        md.unlink()


def _truong(phong: dict) -> dict:
    for n in phong.get("nguoi") or []:
        if n.get("vai") == "truong":
            return n
    raise LoiNhacTruong(f"Phòng {phong.get('ten') or phong.get('slug')} chưa có trưởng phòng.")


def _thanh_vien(phong: dict) -> list:
    return [n for n in phong.get("nguoi") or [] if n.get("vai") != "truong"]


def tao_viec(kho: Kho, tieu_de: str, brief: str, phong_slugs: list, vong: int = VONG_MAC_DINH) -> dict:
    tieu_de = (tieu_de or "").strip()
    brief = (brief or "").strip()
    if not tieu_de or not brief:
        raise LoiNhacTruong("Việc cần tiêu đề và brief.")
    slugs = []
    for s in phong_slugs or []:
        s = slugify(s) if not _slug_ok(str(s)) else str(s)
        if s and s not in slugs:
            slugs.append(s)
    if not slugs:
        raise LoiNhacTruong("Chọn ít nhất một phòng.")
    for s in slugs:
        _truong(kho.doc_phong(s))
    try:
        vong = int(vong)
    except (TypeError, ValueError):
        vong = VONG_MAC_DINH
    vong = min(VONG_TRAN, max(1, vong))
    vid = slugify(tieu_de) or "viec"
    base = vid
    n = 2
    while (kho.goc / "viec" / f"{vid}.json").is_file():
        vid = f"{base}-{n}"
        n += 1
    viec = {
        "id": vid,
        "tieu_de": tieu_de,
        "brief": brief,
        "phong": slugs,
        "vong_toi_da": vong,
        "trang_thai": "nhap",
        "loi": [],
        "ban": {},
        "dat": {s: False for s in slugs},
        "khoa": {s: False for s in slugs},
        "mo": [],
        "loi_chay": "",
    }
    kho.luu_viec(viec)
    return viec


def _cat(text: str) -> str:
    t = (text or "").strip()
    if len(t) > LOI_TRAN:
        return t[:LOI_TRAN]
    return t


def _them(viec: dict, phong: dict, nguoi: dict, lop: str, vong: int, loi: str, quyet: str = "") -> None:
    viec["loi"].append({
        "phong": phong["slug"],
        "phong_ten": phong["ten"],
        "slug": nguoi["slug"],
        "ten": nguoi["ten"],
        "vai": nguoi["vai"],
        "lop": lop,
        "vong": vong,
        "loi": _cat(loi),
        "quyet": quyet,
    })


def lap_prompt(loai: str, nguoi: dict, phong: dict, viec: dict, ban: str = "",
               lenh: str = "", cac_ban: dict | None = None) -> str:
    sk = ", ".join(nguoi.get("skills") or []) or "(chưa gán)"
    vai = "trưởng phòng" if nguoi.get("vai") == "truong" else "thành viên"
    dong = [
        f"LOAI: {loai}",
        f"Bạn là {nguoi.get('ten')}, {vai} phòng {phong.get('ten')}.",
        f"Tính cách: {nguoi.get('tinh_cach') or '(chưa mô tả)'}",
        f"Skill: {sk}",
        f"Tiêu chí phòng này, chỉ bạn giữ khi bạn là trưởng: {phong.get('tieu_chi')}",
        f"Việc: {viec.get('tieu_de')}",
        f"Brief: {viec.get('brief')}",
        "Chỉ trả lời trong lượt này. Không gửi tin, không đăng bài, không chi tiền.",
    ]
    if loai == "GIAO":
        dong.append("Giao mỗi người một đầu việc đúng skill. Không viết hộ cả bài.")
    elif loai == "LAM":
        dong.append("Làm đúng đầu việc của bạn. Viết bản bạn phụ trách.")
        if lenh:
            dong.append("LỆNH SỬA: " + lenh)
            dong.append("Sửa đúng chỗ bị bắt. Giữ phần đã đạt.")
    elif loai == "KIEM":
        dong += [
            "Bạn đang kiểm bản phòng mình. Giả định bản đang sai cho đến khi đọc hết.",
            "BAN HIỆN TẠI:",
            ban or "(trống)",
            "HẾT BẢN",
            "Chỉ xét BAN HIỆN TẠI. Kết thúc bằng đúng một trong hai:",
            "QUYET: DAT",
            "hoặc",
            "QUYET: CHUA",
            "SUA: một câu chỉ chỗ phải sửa",
        ]
    elif loai == "HOP":
        dong.append("HỌP TRƯỞNG. Chỉ các trưởng phòng. Bạn không sửa hộ phòng khác.")
        dong.append("Bạn chỉ ghi DAT khi tiêu chí phòng mình đạt trên các bản dưới đây.")
        for slug, text in (cac_ban or {}).items():
            dong += [f"[{slug}]", text or "(trống)"]
        dong += [
            "Kết thúc bằng:",
            "QUYET: DAT",
            "hoặc",
            "QUYET: CHUA",
            "SUA: một câu",
            "TRA: slug phòng phải sửa",
        ]
    elif loai == "SUA":
        dong.append("Mang lệnh này về team. Nhắc đúng chỗ phải sửa, không viết hộ.")
        if lenh:
            dong.append("LỆNH SỬA: " + lenh)
    return "\n".join(dong)


async def _goi(noi, nguoi: dict, prompt: str) -> str:
    try:
        kq = noi(nguoi, prompt)
        if hasattr(kq, "__await__"):
            kq = await kq
    except LoiNoi:
        raise
    except Exception as e:
        raise LoiNoi(f"{nguoi.get('ten') or 'Người'} không nói được: {type(e).__name__}: {e}") from e
    text = _cat(str(kq or ""))
    if not text:
        raise LoiNoi(f"{nguoi.get('ten') or 'Người'} trả lời rỗng.")
    return text


async def chay(kho: Kho, vid: str, noi) -> dict:
    viec = kho.doc_viec(vid)
    try:
        phongs = [kho.doc_phong(s) for s in viec["phong"]]
        for p in phongs:
            _truong(p)
    except LoiNhacTruong as e:
        viec["trang_thai"] = "loi"
        viec["loi_chay"] = str(e)
        kho.luu_viec(viec)
        return viec
    viec["trang_thai"] = "dang_chay"
    viec["loi"] = []
    viec["ban"] = {p["slug"]: "" for p in phongs}
    viec["dat"] = {p["slug"]: False for p in phongs}
    viec["khoa"] = {p["slug"]: False for p in phongs}
    viec["mo"] = []
    viec["loi_chay"] = ""
    kho.luu_viec(viec)
    vmax = int(viec.get("vong_toi_da") or VONG_MAC_DINH)
    try:
        for phong in phongs:
            await _noi_bo(kho, viec, phong, noi, vmax)
        if len(phongs) == 1:
            viec["dat"][phongs[0]["slug"]] = bool(viec["khoa"][phongs[0]["slug"]])
        else:
            await _hop(kho, viec, phongs, noi, vmax)
    except LoiNoi as e:
        viec["trang_thai"] = "loi"
        viec["loi_chay"] = str(e)
        kho.luu_viec(viec)
        return viec
    except Exception as e:
        viec["trang_thai"] = "loi"
        viec["loi_chay"] = str(e) or "Việc dừng giữa chừng."
        kho.luu_viec(viec)
        return viec
    if all(viec["dat"].get(p["slug"]) for p in phongs):
        viec["trang_thai"] = "xong"
        viec["mo"] = []
    else:
        viec["trang_thai"] = "lech"
    kho.luu_viec(viec)
    return viec


async def _noi_bo(kho: Kho, viec: dict, phong: dict, noi, vmax: int) -> None:
    truong = _truong(phong)
    mems = _thanh_vien(phong)
    lenh = ""
    for vong in range(1, vmax + 1):
        giao = await _goi(noi, truong, lap_prompt("GIAO", truong, phong, viec, lenh=lenh))
        _them(viec, phong, truong, "giao", vong, giao)
        if not mems:
            viec["ban"][phong["slug"]] = giao
        else:
            manh = []
            for mem in mems:
                loi = await _goi(noi, mem, lap_prompt("LAM", mem, phong, viec, lenh=lenh))
                _them(viec, phong, mem, "lam", vong, loi)
                manh.append(loi)
            viec["ban"][phong["slug"]] = "\n\n".join(manh)
        kiem = await _goi(noi, truong, lap_prompt(
            "KIEM", truong, phong, viec, ban=viec["ban"][phong["slug"]]))
        q = doc_quyet(kiem)
        quyet = q["quyet"] or "CHUA"
        _them(viec, phong, truong, "kiem", vong, kiem, quyet)
        kho.luu_viec(viec)
        if quyet == "DAT":
            viec["khoa"][phong["slug"]] = True
            return
        lenh = q["sua"] or "Sửa cho đúng tiêu chí phòng."
        viec["mo"].append(f"{phong['ten']}: {lenh}")
    viec["khoa"][phong["slug"]] = False


async def _sua_phong(kho: Kho, viec: dict, phong: dict, noi, lenh: str, vong: int) -> None:
    truong = _truong(phong)
    ra_lenh = await _goi(noi, truong, lap_prompt("SUA", truong, phong, viec, lenh=lenh))
    _them(viec, phong, truong, "sua", vong, ra_lenh)
    mems = _thanh_vien(phong)
    if not mems:
        viec["ban"][phong["slug"]] = ra_lenh
        return
    manh = []
    for mem in mems:
        loi = await _goi(noi, mem, lap_prompt("LAM", mem, phong, viec, lenh=lenh))
        _them(viec, phong, mem, "lam", vong, loi)
        manh.append(loi)
    viec["ban"][phong["slug"]] = "\n\n".join(manh)
    kho.luu_viec(viec)


async def _hop(kho: Kho, viec: dict, phongs: list, noi, vmax: int) -> None:
    by = {p["slug"]: p for p in phongs}
    slugs = [p["slug"] for p in phongs]
    for vong in range(1, vmax + 1):
        orders = []
        for phong in phongs:
            truong = _truong(phong)
            text = await _goi(noi, truong, lap_prompt(
                "HOP", truong, phong, viec, cac_ban=viec["ban"]))
            q = doc_quyet(text)
            quyet = q["quyet"] or "CHUA"
            # Chỉ tiêu chí phòng mình. Không được gật hộ phòng khác.
            viec["dat"][phong["slug"]] = quyet == "DAT"
            _them(viec, phong, truong, "hop", vong, text, quyet)
            if quyet != "DAT":
                # Không ghi TRA thì lệnh về đúng phòng của người đang nói.
                tra = q["tra"] if q["tra"] in by else phong["slug"]
                orders.append((tra, q["sua"] or "Sửa cho đạt tiêu chí."))
        kho.luu_viec(viec)
        if all(viec["dat"].get(s) for s in slugs):
            viec["mo"] = []
            return
        viec["mo"] = [f"{by[tra]['ten']}: {sua}" for tra, sua in orders]
        if vong == vmax:
            return
        seen = {}
        for tra, sua in orders:
            seen[tra] = sua
        for tra, sua in seen.items():
            await _sua_phong(kho, viec, by[tra], noi, sua, vong)


def bien_ban(viec: dict) -> str:
    d = [
        f"# {viec.get('tieu_de') or 'Việc'}",
        "",
        viec.get("brief") or "",
        "",
        f"Trạng thái: {viec.get('trang_thai') or 'nhap'}",
        "",
    ]
    if viec.get("loi_chay"):
        d += [f"Lỗi: {viec['loi_chay']}", ""]
    lop_ten = {
        "giao": "giao việc",
        "lam": "làm",
        "kiem": "kiểm",
        "hop": "họp trưởng",
        "sua": "mang lệnh về",
    }
    for row in viec.get("loi") or []:
        vai = "trưởng phòng" if row.get("vai") == "truong" else "thành viên"
        quyet = f" · {row['quyet']}" if row.get("quyet") else ""
        d.append(
            f"**{row.get('ten')}** ({vai}, {row.get('phong_ten')}, "
            f"{lop_ten.get(row.get('lop'), row.get('lop'))}, vòng {row.get('vong')}{quyet})"
        )
        d.append("")
        d.append(row.get("loi") or "")
        d.append("")
    if viec.get("trang_thai") in ("xong", "lech"):
        d.append("## Bản chốt")
        d.append("")
        for slug, text in (viec.get("ban") or {}).items():
            d.append(f"### {slug}")
            d.append("")
            d.append(text or "(trống)")
            d.append("")
        if viec.get("mo"):
            d.append("Còn mở:")
            for m in viec["mo"]:
                d.append(f"- {m}")
            d.append("")
    return "\n".join(d).rstrip() + "\n"


async def noi_thu(nguoi: dict, prompt: str) -> str:
    """Người giả để chạy thử không cần model. Chỉ xét BAN HIỆN TẠI, không xét lịch sử."""
    loai = ""
    m = re.search(r"^LOAI: (\w+)", prompt, re.M)
    if m:
        loai = m.group(1)
    if loai == "GIAO":
        return "Lấy đúng brief. Cấm câu hứa kết quả. Mỗi người một việc đúng skill."
    if loai == "SUA":
        return "Sửa đúng câu bị bắt. Giữ phần còn lại."
    if loai in ("LAM",):
        if "LỆNH SỬA" in prompt:
            return "Buổi học gồm các phần trong đề cương. Không hứa kết quả."
        return "Bản nháp có câu cam kết tiến bộ."
    ban = _ban_trong_prompt(prompt)
    if "cam kết" in ban or "cam ket" in _khong_dau(ban).lower():
        tra = _phong_co_loi(prompt)
        dong = "QUYET: CHUA\nSUA: Bỏ câu cam kết."
        if loai == "HOP" and tra:
            dong += f"\nTRA: {tra}"
        return dong
    return "QUYET: DAT"


def _ban_trong_prompt(prompt: str) -> str:
    m = re.search(r"BAN HIỆN TẠI:\n(.*)\nHẾT BẢN", prompt, re.S)
    if m:
        return m.group(1)
    blocks = re.findall(r"^\[([a-z0-9-]+)\]\n(.*?)(?=\n\[|\nKết thúc|\Z)", prompt, re.S | re.M)
    return "\n".join(body for _s, body in blocks)


def _phong_co_loi(prompt: str) -> str:
    blocks = re.findall(r"^\[([a-z0-9-]+)\]\n(.*?)(?=\n\[|\nKết thúc|\Z)", prompt, re.S | re.M)
    for slug, body in blocks:
        if "cam kết" in body or "cam ket" in _khong_dau(body).lower():
            return slug
    return ""
