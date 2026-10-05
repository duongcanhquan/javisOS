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
GON = 480


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
            elif v.startswith("LAM"):
                quyet = "LAM"
            elif v.startswith("SUA"):
                quyet = "SUA"
        elif key == "SUA":
            if rest.strip():
                sua.append(rest.strip())
        elif key == "TRA":
            tra = slugify(rest)
    return {"quyet": quyet, "sua": " ".join(sua).strip(), "tra": tra}


def doc_nhan(text: str) -> str:
    """Người nhận bàn giao. Thiếu dòng NHAN thì coi là chưa nhận."""
    for raw in str(text or "").splitlines():
        head, _, rest = raw.strip().partition(":")
        rest = rest.strip()
        if _khong_dau(head).strip().upper() != "NHAN":
            continue
        v = _khong_dau(rest).upper()
        if v.startswith("OK"):
            return "OK"
        if v.startswith("CHUA"):
            return "CHUA"
    return ""


def doc_thu_tu(text: str, mems: list) -> list:
    """Trưởng xếp thứ tự. Thiếu hoặc sai thì giữ quy trình có sẵn của phòng."""
    by = {m.get("slug"): m for m in mems}
    for raw in str(text or "").splitlines():
        head, _, rest = raw.strip().partition(":")
        if _khong_dau(head).replace(" ", "").replace("_", "").upper() != "THUTU":
            continue
        out = []
        for phan in re.split(r"[>,]+", rest):
            s = slugify(phan)
            if s in by and by[s] not in out:
                out.append(by[s])
        if out:
            return out
    return list(mems)


def _theo_xep(viec: dict, phong: dict, mems: list) -> list:
    by = {m.get("slug"): m for m in mems}
    da = ((viec.get("xep") or {}).get(phong.get("slug")) or [])
    out = []
    for item in da:
        s = item.get("slug") if isinstance(item, dict) else item
        if s in by and by[s] not in out:
            out.append(by[s])
    return out or list(mems)


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


def _cach(raw: str) -> str:
    return raw if raw in ("lan_luot", "cung") else ""


def tao_phong(kho: Kho, ten: str, tieu_chi: str = "", cach_lam: str = "") -> dict:
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
        "cach_lam": _cach(cach_lam) or "cung",
        "nguoi": [],
    }
    kho.luu_phong(phong)
    return phong


def _ha_truong(phong: dict, giu: str) -> None:
    for n in phong["nguoi"]:
        if n.get("vai") == "truong" and n.get("slug") != giu:
            n["vai"] = "thanh_vien"


def _vi_tri(raw) -> str:
    return str(raw or "").strip()[:80]


def them_nguoi(kho: Kho, phong_slug: str, ten: str, tinh_cach: str = "",
               skills: str = "", vai: str = "thanh_vien", agent: str = "",
               vi_tri: str = "") -> dict:
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
    if vai == "truong":
        _ha_truong(phong, "")
    nguoi = {
        "slug": ns,
        "ten": ten,
        "vai": vai,
        "vi_tri": _vi_tri(vi_tri),
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


def sua_phong(kho: Kho, slug: str, tieu_chi: str | None = None, cach_lam: str | None = None) -> dict:
    phong = kho.doc_phong(slug)
    if tieu_chi is not None:
        tieu = (tieu_chi or "").strip()
        if not tieu:
            raise LoiNhacTruong("Tiêu chí không được trống.")
        phong["tieu_chi"] = tieu[:500]
    if cach_lam is not None:
        cach = _cach(str(cach_lam))
        if not cach:
            raise LoiNhacTruong("Cách làm chỉ là lần lượt hoặc cùng làm.")
        phong["cach_lam"] = cach
    kho.luu_phong(phong)
    return phong


def doi_cho(kho: Kho, phong_slug: str, nguoi_slug: str, huong: str) -> dict:
    """Đổi thứ tự thành viên. Lần lượt đi theo thứ tự này, trưởng không nằm trong bước."""
    phong = kho.doc_phong(phong_slug)
    buoc = huong == "len"
    if huong not in ("len", "xuong"):
        raise LoiNhacTruong("Chỉ đưa lên hoặc xuống.")
    idx = [i for i, n in enumerate(phong["nguoi"]) if n.get("vai") != "truong"]
    pos = next((k for k, i in enumerate(idx) if phong["nguoi"][i].get("slug") == nguoi_slug), -1)
    if pos < 0:
        raise LoiNhacTruong("Chỉ đổi thứ tự thành viên.")
    den = pos - 1 if buoc else pos + 1
    if den < 0 or den >= len(idx):
        return phong
    a, b = idx[pos], idx[den]
    phong["nguoi"][a], phong["nguoi"][b] = phong["nguoi"][b], phong["nguoi"][a]
    kho.luu_phong(phong)
    return phong


def sua_nguoi(kho: Kho, phong_slug: str, nguoi_slug: str, tinh_cach=None,
              skills=None, vai=None, vi_tri=None) -> dict:
    phong = kho.doc_phong(phong_slug)
    nguoi = next((n for n in phong["nguoi"] if n.get("slug") == nguoi_slug), None)
    if not nguoi:
        raise LoiNhacTruong("Không có người này.")
    if vai is not None:
        vai = (vai or "thanh_vien").strip()
        if vai not in ("truong", "thanh_vien"):
            raise LoiNhacTruong("Vai chỉ là trưởng phòng hoặc thành viên.")
        if vai == "truong":
            _ha_truong(phong, nguoi_slug)
        nguoi["vai"] = vai
    if vi_tri is not None:
        nguoi["vi_tri"] = _vi_tri(vi_tri)
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


def _gon(text: str, tran: int = GON) -> str:
    """Chỉ giữ trọng tâm và các điểm đánh số, để lượt sau không nuốt cả bài."""
    t = (text or "").strip()
    if len(t) <= tran:
        return t
    diem = []
    for ln in t.splitlines():
        s = ln.strip()
        if re.match(r"^(?:\d+[\).\]]|điểm\s+\d+|diem\s+\d+)\s+", s, re.I):
            diem.append(s)
    dau = t[:tran].rstrip()
    if " " in dau:
        dau = dau.rsplit(" ", 1)[0]
    them = [d for d in diem if d not in dau][:6]
    if not them:
        return dau + "…"
    return dau + "…\nĐiểm giữ lại:\n" + "\n".join(them)


def _nhan(nguoi: dict) -> str:
    ten = nguoi.get("ten") or ""
    vt = (nguoi.get("vi_tri") or "").strip()
    if nguoi.get("vai") == "truong":
        return f"{ten} (trưởng)" + (f", {vt}" if vt else "")
    return f"{ten} ({vt})" if vt else ten


def _them(viec: dict, phong: dict, nguoi: dict, lop: str, vong: int, loi: str,
          quyet: str = "", giao_cho: str = "") -> None:
    viec["loi"].append({
        "phong": phong["slug"],
        "phong_ten": phong["ten"],
        "slug": nguoi["slug"],
        "ten": nguoi["ten"],
        "vai": nguoi["vai"],
        "vi_tri": (nguoi.get("vi_tri") or "").strip(),
        "lop": lop,
        "vong": vong,
        "loi": _cat(loi),
        "quyet": quyet,
        "giao_cho": giao_cho,
    })


def _bao(kho: Kho, viec: dict, phong: dict, nguoi: dict, buoc: str, giao: dict | None = None) -> None:
    """Ghi người đang nói trước khi model trả lời, để trang theo dõi không đứng trống."""
    viec["dang_lam"] = {
        "phong": phong.get("slug") or "",
        "phong_ten": phong.get("ten") or "",
        "ten": nguoi.get("ten") or "",
        "vi_tri": (nguoi.get("vi_tri") or "").strip(),
        "buoc": buoc,
        "giao_cho": _nhan(giao) if giao else "",
    }
    kho.luu_viec(viec)


def _ghi(kho: Kho, viec: dict, phong: dict, nguoi: dict, lop: str, vong: int, loi: str,
         quyet: str = "", giao_cho: str = "") -> None:
    _them(viec, phong, nguoi, lop, vong, loi, quyet, giao_cho)
    kho.luu_viec(viec)


def lap_prompt(loai: str, nguoi: dict, phong: dict, viec: dict, ban: str = "",
               lenh: str = "", cac_ban: dict | None = None, giao_cho: dict | None = None,
               thanh_vien: list | None = None, luot: int = 0) -> str:
    ban_day = ban or ""
    if loai != "KET":
        ban = _gon(ban)
        lenh = _gon(lenh, 240)
        if cac_ban:
            cac_ban = {k: _gon(v) for k, v in cac_ban.items()}
    sk = ", ".join(nguoi.get("skills") or []) or "(chưa gán)"
    vai = "trưởng phòng" if nguoi.get("vai") == "truong" else "thành viên"
    vi_tri = (nguoi.get("vi_tri") or "").strip()
    chuc = f"{vi_tri}, {vai}" if vi_tri else vai
    dong = [
        f"LOAI: {loai}",
        f"Bạn là {nguoi.get('ten')}, {chuc} phòng {phong.get('ten')}.",
        f"Tính cách: {nguoi.get('tinh_cach') or '(chưa mô tả)'}",
        f"Skill: {sk}",
        f"Tiêu chí phòng này, chỉ bạn giữ khi bạn là trưởng: {phong.get('tieu_chi')}",
        f"Việc: {viec.get('tieu_de')}",
        f"Brief: {viec.get('brief')}",
        "Chỉ trả lời trong lượt này. Không gửi tin, không đăng bài, không chi tiền.",
    ]
    if loai == "KET":
        dong.append("Viết bản kết quả cuối, đầy đủ, dùng được ngay. Không kể lại cuộc nói.")
    elif loai == "LAM" and not ban_day:
        dong.append("Đây là bản đầu. Viết đủ phần của bạn để người sau chỉ sửa từng điểm.")
    else:
        dong.append("Viết ngắn, chỉ trọng tâm. Không chép lại bài đã có. Chỗ cần sửa ghi điểm 1, điểm 2. Không viết hết.")
    if loai == "GIAO":
        dong.append("Vài dòng: ai làm gì. Không viết bài.")
        if thanh_vien:
            dong.append("Quy trình có sẵn của phòng:")
            for i, m in enumerate(thanh_vien, 1):
                dong.append(f"{i}. {_nhan(m)} | slug {m.get('slug')}")
            dong.append("Việc đi đúng quy trình thì giữ thứ tự đó. Việc thực tế không cần ai, hoặc cần đảo bước, thì xếp lại.")
            dong.append("Kết thúc bằng đúng một dòng: THU_TU: slug > slug")
        elif giao_cho:
            dong.append("Bước 1 là " + _nhan(giao_cho) + ".")
    elif loai == "NHAN":
        dong += [
            "Bạn nhận bàn giao từ " + (_nhan(giao_cho) if giao_cho else "bước trước") + ".",
            "BẢN ĐANG NHẬN:",
            ban or "(trống)",
            "HẾT BẢN",
            "Một hoặc hai câu rồi dòng NHAN. Không tóm tắt lại bài.",
            "Chưa hiểu hoặc thấy sai thì nói thẳng. Chưa nhận thì chưa làm phần của bạn.",
        ]
        if luot == 1:
            dong += [
                "Lượt nhận: 1",
                "Đây là lượt nhận đầu. Phải nêu một chỗ chưa chắc. Chưa được NHAN: OK ở lượt này.",
            ]
        dong += [
            "Kết thúc bằng đúng một trong hai:",
            "NHAN: OK",
            "hoặc",
            "NHAN: CHUA",
            "SUA: một câu chỗ chưa ổn",
        ]
    elif loai == "DOI":
        dong += [
            (_nhan(giao_cho) if giao_cho else "Bước sau") + " chưa nhận bài của bạn.",
            "Họ nói: " + (lenh or "chưa rõ."),
            "BẢN BẠN VỪA GIAO:",
            ban or "(trống)",
            "HẾT BẢN",
            "Không viết lại cả bài. Chỉ ghi các điểm đã chỉnh, đánh số.",
        ]
    elif loai == "XU":
        dong += [
            "Hai người chưa thống nhất hết số lần được trao đổi.",
            "BẢN ĐANG TRANH:",
            ban or "(trống)",
            "HẾT BẢN",
            "Một câu rồi dòng QUYET. Không viết lại bài. Kết thúc bằng:",
            "QUYET: LAM",
            "hoặc",
            "QUYET: SUA",
            "SUA: một câu bước trước phải sửa",
        ]
    elif loai == "LAM":
        if ban:
            dong += [
                "BƯỚC TRƯỚC ĐÃ CHỐT:",
                ban,
                "HẾT BẢN",
                "Phần này đã được nhận. Không chép bản trước.",
                "Chỉ viết phần mới của bước bạn, hoặc điểm 1, điểm 2 chỗ bạn sửa.",
            ]
        else:
            dong.append("Viết đủ phần của bạn. Người sau sẽ chỉ nêu điểm cần sửa.")
        if giao_cho:
            dong.append("Cuối lời, một câu bàn giao cho " + _nhan(giao_cho) + ": việc bước sau cần nhận.")
        if lenh:
            dong.append("LỆNH SỬA: " + lenh)
            dong.append("Chỉ sửa đúng các điểm bị bắt. Không viết lại phần đã ổn.")
    elif loai == "KIEM":
        dong += [
            "Bạn đang kiểm bản phòng mình. Giả định bản đang sai cho đến khi đọc hết.",
            "BAN HIỆN TẠI:",
            ban or "(trống)",
            "HẾT BẢN",
            "Không viết lại bản. Chỉ dòng QUYET và, nếu chưa đạt, một câu SUA.",
            "Chỉ xét BAN HIỆN TẠI. Kết thúc bằng đúng một trong hai:",
            "QUYET: DAT",
            "hoặc",
            "QUYET: CHUA",
            "SUA: một câu chỉ chỗ phải sửa",
        ]
    elif loai == "HOP":
        dong.append("HỌP TRƯỞNG. Chỉ các trưởng phòng. Bạn không sửa hộ phòng khác.")
        dong.append("Bạn chỉ ghi DAT khi tiêu chí phòng mình đạt trên các bản dưới đây.")
        dong.append("Không viết lại bản. Chỉ dòng QUYET, một câu SUA nếu chưa đạt, và TRA.")
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
    elif loai == "KET":
        dong.append("Ghép các bản dưới đây thành một kết quả cho người giao việc.")
        dong.append("Giữ nội dung đã làm. Bỏ câu trao đổi. Không ghi QUYET.")
        if viec.get("mo"):
            dong.append("Còn lệch: " + "; ".join(viec.get("mo") or []))
        for slug, text in (cac_ban or {}).items():
            dong += [f"[{slug}]", text or "(trống)"]
    elif loai == "CHIA":
        dong += [
            "Bạn đang nói với trưởng phòng " + (_nhan(giao_cho) if giao_cho else "bên cạnh") + ".",
            "Đọc bản phòng họ. Góp một chỗ chưa chắc, hoặc một ý phòng bạn có mà họ cần.",
            "BẢN PHÒNG HỌ:",
            ban or "(trống)",
            "HẾT BẢN",
            "Một hoặc hai câu. Chỉ điểm cần sửa. Không viết QUYET. Không viết hộ bài của họ.",
        ]
    elif loai == "DAP":
        dong += [
            (_nhan(giao_cho) if giao_cho else "Phòng kia") + " vừa góp ý phòng bạn.",
            "Họ nói: " + (lenh or "chưa rõ."),
            "BẢN PHÒNG BẠN:",
            ban or "(trống)",
            "HẾT BẢN",
            "Một hoặc hai câu. Điểm nào giữ, điểm nào sửa. Không viết lại bài. Không viết QUYET.",
        ]
    elif loai == "GOP":
        dong += [
            "Đọc bản mọi người trong phòng vừa viết. Nêu một chỗ chưa chắc hoặc một ý cần người kia chỉnh.",
            "BẢN CẢ PHÒNG:",
            ban or "(trống)",
            "HẾT BẢN",
            "Một hoặc hai câu. Chỉ điểm cần người kia chỉnh. Không viết lại bài.",
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
        await _ket(kho, viec, phongs, noi)
    except LoiNoi as e:
        viec["trang_thai"] = "loi"
        viec["loi_chay"] = str(e)
        viec["dang_lam"] = None
        kho.luu_viec(viec)
        return viec
    except Exception as e:
        viec["trang_thai"] = "loi"
        viec["loi_chay"] = str(e) or "Việc dừng giữa chừng."
        viec["dang_lam"] = None
        kho.luu_viec(viec)
        return viec
    if all(viec["dat"].get(p["slug"]) for p in phongs):
        viec["trang_thai"] = "xong"
        viec["mo"] = []
    else:
        viec["trang_thai"] = "lech"
    viec["dang_lam"] = None
    kho.luu_viec(viec)
    return viec


async def _chan(kho: Kho, viec: dict, phong: dict, noi, truoc: dict, sau: dict, ban: str, vong: int) -> str:
    """Bước sau cãi với bước trước. Nhận rồi mới được làm. Hết lần thì trưởng phán."""
    truong = _truong(phong)
    vmax = min(VONG_TRAN, max(1, int(viec.get("vong_toi_da") or VONG_MAC_DINH)))
    for i in range(vmax):
        _bao(kho, viec, phong, sau, "nhan", truoc)
        text = await _goi(noi, sau, lap_prompt(
            "NHAN", sau, phong, viec, ban=ban, giao_cho=truoc, luot=i + 1))
        nhan = doc_nhan(text) or "CHUA"
        if i == 0 and nhan == "OK":
            nhan = "CHUA"
            if "SUA:" not in text.upper() and "SỬA:" not in text.upper():
                text = text.rstrip() + "\nSUA: Làm rõ một chỗ chưa chắc trước khi nhận."
        _ghi(kho, viec, phong, sau, "nhan", vong, text, nhan, _nhan(truoc))
        if nhan == "OK":
            return ban
        sua = doc_quyet(text)["sua"] or "Làm rõ chỗ chưa ổn."
        _bao(kho, viec, phong, truoc, "doi", sau)
        ban = await _goi(noi, truoc, lap_prompt("DOI", truoc, phong, viec, ban=ban, lenh=sua, giao_cho=sau))
        _ghi(kho, viec, phong, truoc, "doi", vong, ban, giao_cho=_nhan(sau))
    _bao(kho, viec, phong, truong, "xu", sau)
    xu = await _goi(noi, truong, lap_prompt("XU", truong, phong, viec, ban=ban, giao_cho=sau))
    q = doc_quyet(xu)
    _ghi(kho, viec, phong, truong, "xu", vong, xu, q["quyet"] or "LAM")
    if q["quyet"] == "SUA":
        _bao(kho, viec, phong, truoc, "doi", sau)
        ban = await _goi(noi, truoc, lap_prompt(
            "DOI", truoc, phong, viec, ban=ban, lenh=q["sua"] or "Sửa đúng chỗ trưởng chỉ.", giao_cho=sau))
        _ghi(kho, viec, phong, truoc, "doi", vong, ban, giao_cho=_nhan(sau))
    return ban


async def _chuoi(kho: Kho, viec: dict, phong: dict, noi, mems: list, lenh: str, vong: int) -> str:
    """Đi đúng thứ tự trưởng đã xếp. Bước sau chưa nhận thì chưa làm."""
    truong = _truong(phong)
    manh = []
    ban_truoc = ""
    nguoi_truoc = None
    for i, mem in enumerate(mems):
        sau = mems[i + 1] if i + 1 < len(mems) else truong
        if nguoi_truoc:
            ban_truoc = await _chan(kho, viec, phong, noi, nguoi_truoc, mem, ban_truoc, vong)
        _bao(kho, viec, phong, mem, "lam", sau)
        loi = await _goi(noi, mem, lap_prompt(
            "LAM", mem, phong, viec, ban=ban_truoc, lenh=lenh, giao_cho=sau))
        _ghi(kho, viec, phong, mem, "lam", vong, loi, giao_cho=_nhan(sau))
        manh.append(f"[{_nhan(mem)}]\n{loi}")
        ban_truoc = loi
        nguoi_truoc = mem
    return "\n\n".join(manh)


async def _noi_bo(kho: Kho, viec: dict, phong: dict, noi, vmax: int) -> None:
    if phong.get("cach_lam") == "lan_luot" and _thanh_vien(phong):
        await _noi_bo_lan(kho, viec, phong, noi, vmax)
        return
    truong = _truong(phong)
    mems = _thanh_vien(phong)
    lenh = ""
    for vong in range(1, vmax + 1):
        _bao(kho, viec, phong, truong, "giao", mems[0] if mems else None)
        giao = await _goi(noi, truong, lap_prompt("GIAO", truong, phong, viec, lenh=lenh))
        _ghi(kho, viec, phong, truong, "giao", vong, giao)
        if not mems:
            viec["ban"][phong["slug"]] = giao
        else:
            manh = []
            for mem in mems:
                _bao(kho, viec, phong, mem, "lam")
                loi = await _goi(noi, mem, lap_prompt("LAM", mem, phong, viec, lenh=lenh))
                _ghi(kho, viec, phong, mem, "lam", vong, loi)
                manh.append(loi)
            viec["ban"][phong["slug"]] = "\n\n".join(manh)
            if len(mems) > 1:
                for mem in mems:
                    khac = next((m for m in mems if m["slug"] != mem["slug"]), None)
                    _bao(kho, viec, phong, mem, "gop", khac)
                    gop = await _goi(noi, mem, lap_prompt(
                        "GOP", mem, phong, viec, ban=viec["ban"][phong["slug"]], giao_cho=khac))
                    _ghi(kho, viec, phong, mem, "gop", vong, gop, giao_cho=_nhan(khac) if khac else "")
        _bao(kho, viec, phong, truong, "kiem")
        kiem = await _goi(noi, truong, lap_prompt(
            "KIEM", truong, phong, viec, ban=viec["ban"][phong["slug"]]))
        q = doc_quyet(kiem)
        quyet = q["quyet"] or "CHUA"
        _ghi(kho, viec, phong, truong, "kiem", vong, kiem, quyet)
        if quyet == "DAT":
            viec["khoa"][phong["slug"]] = True
            return
        lenh = q["sua"] or "Sửa cho đúng tiêu chí phòng."
        viec["mo"].append(f"{phong['ten']}: {lenh}")
    viec["khoa"][phong["slug"]] = False


async def _noi_bo_lan(kho: Kho, viec: dict, phong: dict, noi, vmax: int) -> None:
    truong = _truong(phong)
    mems = _thanh_vien(phong)
    lenh = ""
    for vong in range(1, vmax + 1):
        _bao(kho, viec, phong, truong, "giao")
        giao = await _goi(noi, truong, lap_prompt(
            "GIAO", truong, phong, viec, lenh=lenh, thanh_vien=mems))
        day = doc_thu_tu(giao, mems)
        viec.setdefault("xep", {})[phong["slug"]] = [
            {"slug": m["slug"], "ten": m["ten"], "vi_tri": (m.get("vi_tri") or "").strip()} for m in day
        ]
        _ghi(kho, viec, phong, truong, "giao", vong, giao, giao_cho=_nhan(day[0]))
        viec["ban"][phong["slug"]] = await _chuoi(kho, viec, phong, noi, day, lenh, vong)
        _bao(kho, viec, phong, truong, "kiem")
        kiem = await _goi(noi, truong, lap_prompt(
            "KIEM", truong, phong, viec, ban=viec["ban"][phong["slug"]]))
        q = doc_quyet(kiem)
        quyet = q["quyet"] or "CHUA"
        _ghi(kho, viec, phong, truong, "kiem", vong, kiem, quyet)
        if quyet == "DAT":
            viec["khoa"][phong["slug"]] = True
            return
        lenh = q["sua"] or "Sửa cho đúng tiêu chí phòng."
        viec["mo"].append(f"{phong['ten']}: {lenh}")
    viec["khoa"][phong["slug"]] = False


async def _sua_phong(kho: Kho, viec: dict, phong: dict, noi, lenh: str, vong: int) -> None:
    truong = _truong(phong)
    mems = _thanh_vien(phong)
    _bao(kho, viec, phong, truong, "sua", mems[0] if mems else None)
    ra_lenh = await _goi(noi, truong, lap_prompt("SUA", truong, phong, viec, lenh=lenh))
    _ghi(kho, viec, phong, truong, "sua", vong, ra_lenh)
    if not mems:
        viec["ban"][phong["slug"]] = ra_lenh
        kho.luu_viec(viec)
        return
    if phong.get("cach_lam") == "lan_luot":
        viec["ban"][phong["slug"]] = await _chuoi(kho, viec, phong, noi, _theo_xep(viec, phong, mems), lenh, vong)
        kho.luu_viec(viec)
        return
    manh = []
    for mem in mems:
        _bao(kho, viec, phong, mem, "lam")
        loi = await _goi(noi, mem, lap_prompt("LAM", mem, phong, viec, lenh=lenh))
        _ghi(kho, viec, phong, mem, "lam", vong, loi)
        manh.append(loi)
    viec["ban"][phong["slug"]] = "\n\n".join(manh)
    kho.luu_viec(viec)


async def _trao(kho: Kho, viec: dict, phongs: list, noi, vong: int) -> None:
    """Trưởng phòng góp ý bản phòng kia, trưởng kia đáp. Rồi mới họp chốt."""
    if len(phongs) < 2:
        return
    for i, phong in enumerate(phongs):
        khac = phongs[(i + 1) % len(phongs)]
        truong = _truong(phong)
        kia = _truong(khac)
        ban_khac = (viec.get("ban") or {}).get(khac["slug"]) or ""
        _bao(kho, viec, phong, truong, "chia", kia)
        y = await _goi(noi, truong, lap_prompt(
            "CHIA", truong, phong, viec, ban=ban_khac, giao_cho=kia))
        _ghi(kho, viec, phong, truong, "chia", vong, y, giao_cho=_nhan(kia))
        _bao(kho, viec, khac, kia, "dap", truong)
        d = await _goi(noi, kia, lap_prompt(
            "DAP", kia, khac, viec, ban=(viec.get("ban") or {}).get(khac["slug"]) or "",
            lenh=y, giao_cho=truong))
        _ghi(kho, viec, khac, kia, "dap", vong, d, giao_cho=_nhan(truong))


async def _hop(kho: Kho, viec: dict, phongs: list, noi, vmax: int) -> None:
    by = {p["slug"]: p for p in phongs}
    slugs = [p["slug"] for p in phongs]
    for vong in range(1, vmax + 1):
        await _trao(kho, viec, phongs, noi, vong)
        orders = []
        for phong in phongs:
            truong = _truong(phong)
            _bao(kho, viec, phong, truong, "hop")
            text = await _goi(noi, truong, lap_prompt(
                "HOP", truong, phong, viec, cac_ban=viec["ban"]))
            q = doc_quyet(text)
            quyet = q["quyet"] or "CHUA"
            # Chỉ tiêu chí phòng mình. Không được gật hộ phòng khác.
            viec["dat"][phong["slug"]] = quyet == "DAT"
            _ghi(kho, viec, phong, truong, "hop", vong, text, quyet)
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


async def _ket(kho: Kho, viec: dict, phongs: list, noi) -> None:
    """Một bản kết quả đầy đủ sau khi các lượt trao đổi đã ngắn."""
    phong = phongs[0]
    truong = _truong(phong)
    nguon = {}
    for p in phongs:
        manh = []
        for row in viec.get("loi") or []:
            if row.get("phong") == p["slug"] and row.get("lop") == "lam":
                manh.append(row.get("loi") or "")
        ban = (viec.get("ban") or {}).get(p["slug"]) or ""
        if ban and ban not in "\n".join(manh):
            manh.append(ban)
        nguon[p["slug"]] = "\n\n".join(x for x in manh if x)
    _bao(kho, viec, phong, truong, "ket")
    text = await _goi(noi, truong, lap_prompt("KET", truong, phong, viec, cac_ban=nguon))
    viec["ket_qua"] = text
    kho.luu_viec(viec)


def bien_ban(viec: dict) -> str:
    d = [
        f"# {viec.get('tieu_de') or 'Việc'}",
        "",
        viec.get("brief") or "",
        "",
        f"Trạng thái: {viec.get('trang_thai') or 'nhap'}",
        "",
    ]
    if viec.get("ket_qua"):
        d += ["## Kết quả", "", viec["ket_qua"], ""]
    if viec.get("loi_chay"):
        d += [f"Lỗi: {viec['loi_chay']}", ""]
    lop_ten = {
        "giao": "giao việc",
        "lam": "làm",
        "kiem": "kiểm",
        "hop": "họp trưởng",
        "sua": "mang lệnh về",
        "nhan": "nhận bàn giao",
        "doi": "trả lời",
        "xu": "trưởng xử",
        "chia": "góp ý phòng khác",
        "dap": "đáp lại",
        "gop": "trao đổi trong phòng",
    }
    for row in viec.get("loi") or []:
        vai = "trưởng phòng" if row.get("vai") == "truong" else "thành viên"
        quyet = f" · {row['quyet']}" if row.get("quyet") else ""
        d.append(
            f"**{row.get('ten')}** ({vai}, {row.get('phong_ten')}, "
            f"{lop_ten.get(row.get('lop'), row.get('lop'))}, vòng {row.get('vong')}{quyet})"
        )
        if row.get("giao_cho"):
            d.append(f"Bàn giao cho {row['giao_cho']}.")
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
    if loai == "NHAN":
        if "Lượt nhận: 1" in prompt or "cam kết" in prompt or "cam ket" in _khong_dau(prompt).lower():
            return "Còn một chỗ chưa chắc.\nNHAN: CHUA\nSUA: Làm rõ chỗ này trước khi nhận."
        return "Phần này dùng được.\nNHAN: OK"
    if loai == "CHIA":
        return "Phòng bên: còn một chỗ chưa chắc. Cần nói rõ căn cứ, không giữ câu hứa."
    if loai == "DAP":
        return "Đã nghe phòng bên. Giữ phần đúng brief. Chỗ chưa chắc thì sửa."
    if loai == "GOP":
        return "Phần người cùng phòng còn chỗ chưa chắc. Nên sửa trước khi trưởng chốt."
    if loai == "DOI":
        return "Đã bỏ câu hứa. Giữ phần còn lại."
    if loai == "XU":
        return "QUYET: LAM"
    if loai == "SUA":
        return "Sửa đúng câu bị bắt. Giữ phần còn lại."
    if loai == "KET":
        return "Kết quả cuối. Buổi học theo đề cương, không hứa kết quả. Các phần đã chốt được giữ trong bản này."
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
