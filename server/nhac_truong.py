"""Nhạc trưởng: phòng ban, trưởng phòng, họp liên phòng, biên bản.

Cơ chế mượn từ CrewAI hierarchical và AutoGen group chat, không nhúng runtime của họ.
Trưởng phòng giao việc và chặn bản phòng. Liên phòng chỉ các trưởng phòng nói.
Mỗi trưởng chỉ được ghi Đạt cho tiêu chí phòng mình. Trần vòng để khỏi chạy mãi.

Phần này không gọi model. `noi(nguoi, prompt)` do chỗ gọi đưa vào, nên test chạy không cần API.
"""
from __future__ import annotations

import asyncio
import json
import re
import unicodedata
from pathlib import Path

VONG_MAC_DINH = 6
VONG_TRAN = 10
LOI_TRAN = 200000


class LoiNhacTruong(ValueError):
    pass


class LoiNoi(RuntimeError):
    """Model không trả lời được. Việc dừng, không bịa bản đạt."""


class LoiDung(Exception):
    """Người bấm Dừng. Không phải lỗi model."""


class LoiCong(Exception):
    """Dừng đúng một cổng duyệt. Việc giữ chỗ, không xoá bản."""

    def __init__(self, cong: str):
        self.cong = cong
        super().__init__(cong)


def slugify(s: str) -> str:
    t = unicodedata.normalize("NFD", str(s or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("đ", "d").replace("Đ", "D")
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:48]


def _slug_ok(s: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", s or ""))


_QUYET_HOP = ("DAT", "CHUA", "LAM", "SUA")
_NHAN_HOP = ("OK", "CHUA")
_GOI_HOP = ("phap_che", "web", "drive", "van_hanh")


def _cac_obj(text: str) -> list:
    """Các object JSON phẳng: khối ```json hoặc một dòng { ... }."""
    raws = []
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text or "", re.S | re.I):
        raws.append(m.group(1))
    for ln in str(text or "").splitlines():
        s = ln.strip().rstrip(",")
        if len(s) >= 2 and s[0] == "{" and s[-1] == "}":
            raws.append(s)
    out = []
    for s in raws:
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _obj_co_khoa(text: str, khoa: str) -> dict | None:
    found = [o for o in _cac_obj(text) if khoa in o]
    return found[-1] if found else None


def _ma_quyet(raw) -> str:
    v = _khong_dau(str(raw or "")).strip().upper()
    for ma in _QUYET_HOP:
        if v.startswith(ma):
            return ma
    return ""


def _quyet_tu_dong(text: str) -> dict:
    """Đọc dòng QUYET / SUA / TRA. Thiếu dòng QUYET thì coi là chưa đạt."""
    quyet, sua, tra = "", [], ""
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        head, _, rest = line.partition(":")
        rest = rest.strip()
        key = _khong_dau(head).strip().upper()
        if key == "QUYET":
            quyet = _ma_quyet(rest) or quyet
        elif key == "SUA":
            if rest.strip():
                sua.append(rest.strip())
        elif key == "TRA":
            tra = slugify(rest)
    return {"quyet": quyet, "sua": " ".join(sua).strip(), "tra": tra}


def doc_quyet(text: str) -> dict:
    """Đọc quyết định. Có khối JSON thì chỉ tin khối đó. Không có thì đọc dòng chữ."""
    obj = _obj_co_khoa(text, "quyet")
    if obj is not None:
        return {
            "quyet": _ma_quyet(obj.get("quyet")),
            "sua": str(obj.get("sua") or "").strip(),
            "tra": slugify(str(obj.get("tra") or "")),
        }
    return _quyet_tu_dong(text)


def _trung_lenh(a: str, b: str) -> bool:
    """Cùng một lỗi thì dừng, không đốt hết số vòng."""
    def g(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").strip().lower())
    x, y = g(a), g(b)
    return bool(x) and x == y


def _nhan_tu_dong(text: str) -> str:
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


def doc_nhan(text: str) -> str:
    """Người nhận bàn giao. Có khối JSON thì chỉ tin khối đó. Không có thì đọc dòng NHAN."""
    obj = _obj_co_khoa(text, "nhan")
    if obj is not None:
        v = _khong_dau(str(obj.get("nhan") or "")).strip().upper()
        if v.startswith("OK"):
            return "OK"
        if v.startswith("CHUA"):
            return "CHUA"
        return ""
    return _nhan_tu_dong(text)


def doc_goi(text: str) -> dict:
    """Một lời gọi tool đọc. Rỗng nếu không có, hoặc nếu cùng khối đã là quyết định."""
    obj = _obj_co_khoa(text, "goi")
    if not obj or "quyet" in obj or "nhan" in obj:
        return {}
    ten = str(obj.get("goi") or "").strip()
    if ten not in _GOI_HOP:
        return {}
    return {"ten": ten, "q": str(obj.get("q") or "").strip()[:300]}


def vai_doc(nguoi: dict, prompt: str = "") -> set:
    """Tool đọc mà người này được gọi. Xét chức danh, skill và dòng vai trong prompt."""
    dong = ""
    m = re.search(r"^Bạn là .+$", prompt or "", re.M)
    if m:
        dong = m.group(0)
    blob = _khong_dau(" ".join([
        str((nguoi or {}).get("vi_tri") or ""),
        " ".join((nguoi or {}).get("skills") or []),
        dong,
    ])).lower()
    vai = set()
    if any(k in blob for k in ("nghien cuu", "thi truong", "research", "marketing")):
        vai.update(("web", "drive"))
    if any(k in blob for k in ("phap che", "luat", "legal")):
        vai.add("phap_che")
    if any(k in blob for k in ("van hanh", "cis", "cms")):
        vai.add("van_hanh")
    return vai


def loi_nguon(vai: set) -> str:
    """Câu nhắc trong lượt: gọi đúng một tool đọc, thiếu nguồn thì không bịa số."""
    if not vai:
        return ""
    dong = ["Được gọi đúng một tool đọc, bằng một dòng JSON, và chưa viết FILE."]
    if "phap_che" in vai:
        dong.append('{"goi":"phap_che","q":"câu cần tra trong kho pháp chế"}')
    if "web" in vai:
        dong.append('{"goi":"web","q":"câu cần tra trên web"}')
    if "drive" in vai:
        dong.append('{"goi":"drive","q":"tên file hoặc câu tìm trên Drive"}')
    if "van_hanh" in vai:
        dong.append('{"goi":"van_hanh","q":"số liệu lớp hoặc sinh viên cần lấy"}')
    dong.append("Nếu kết quả nói chưa nối hoặc không có số, viết rõ chưa có số liệu. Không bịa.")
    return "\n".join(dong)


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


def _mems(viec: dict, phong: dict) -> list:
    """Thứ tự người đã khóa khi giao việc. Không khóa thì theo quy trình phòng."""
    mems = _thanh_vien(phong)
    if viec.get("xep_khoa") and (viec.get("xep") or {}).get(phong.get("slug")):
        return _theo_xep(viec, phong, mems)
    return mems


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

    def luu_viec(self, viec: dict, *, tha_huy: bool = False) -> None:
        p = self._viec_path(viec["id"])
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.is_file() and not tha_huy and not viec.get("huy"):
            try:
                cu = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                cu = {}
            if cu.get("huy"):
                viec["huy"] = True
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


def sua_phong(kho: Kho, slug: str, tieu_chi: str | None = None, cach_lam: str | None = None,
              ten: str | None = None, loai: str | None = None) -> dict:
    phong = kho.doc_phong(slug)
    if ten is not None:
        ten = (ten or "").strip()
        if not ten:
            raise LoiNhacTruong("Tên phòng không được trống.")
        phong["ten"] = ten[:80]
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
    if loai is not None:
        gan = str(loai or "").strip()
        if gan not in ("", "viet", "thiet_ke", "video"):
            raise LoiNhacTruong("Loại phòng chỉ là viết, thiết kế hoặc video.")
        if gan:
            phong["loai"] = gan
        else:
            phong.pop("loai", None)
    kho.luu_phong(phong)
    return phong


def dat_khuon(kho: Kho, slug: str, truong, ten: str = "") -> dict:
    """Khuôn bàn giao của một phòng. Danh sách trường để trống thì bỏ khuôn."""
    phong = kho.doc_phong(slug)
    ds = []
    for t in truong or []:
        s = slugify(str(t))
        if s and s not in ds:
            ds.append(s)
    if not ds:
        phong.pop("khuon", None)
    else:
        phong["khuon"] = {"ten": (ten or "Bàn giao").strip()[:80] or "Bàn giao", "truong": ds[:12]}
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
              skills=None, vai=None, vi_tri=None, ten=None) -> dict:
    phong = kho.doc_phong(phong_slug)
    nguoi = next((n for n in phong["nguoi"] if n.get("slug") == nguoi_slug), None)
    if not nguoi:
        raise LoiNhacTruong("Không có người này.")
    if ten is not None:
        ten = str(ten or "").strip()
        if not ten:
            raise LoiNhacTruong("Người cần có tên.")
        nguoi["ten"] = ten[:80]
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


def chuan_tai_lieu(raw) -> list:
    """Tối đa 3 file chữ. Giữ gần nguyên văn để bước sau còn dữ liệu mà làm."""
    out = []
    for item in raw or []:
        if len(out) >= 3:
            break
        if not isinstance(item, dict):
            continue
        nd = str(item.get("noi_dung") or "").strip()
        if not nd:
            continue
        ten = str(item.get("ten") or "tai-lieu").strip()[:80] or "tai-lieu"
        out.append({"ten": ten, "noi_dung": nd[:LOI_TRAN]})
    return out


def luu_icon(kho: Kho, slug: str, data: str) -> dict:
    phong = kho.doc_phong(slug)
    raw = (data or "").strip()
    if not raw:
        phong.pop("icon", None)
        kho.luu_phong(phong)
        return phong
    if not raw.startswith("data:image/") or ";base64," not in raw:
        raise LoiNhacTruong("Icon cần là ảnh PNG, JPG hoặc WebP.")
    if len(raw) > 180000:
        raise LoiNhacTruong("Ảnh icon quá lớn. Chọn ảnh nhỏ hơn.")
    phong["icon"] = raw
    kho.luu_phong(phong)
    return phong


def dat_thu_tu_phong(kho: Kho, vid: str, slugs: list) -> dict:
    viec = kho.doc_viec(vid)
    if viec.get("trang_thai") == "dang_chay":
        raise LoiNhacTruong("Dừng việc trước khi đổi thứ tự phòng.")
    hop = []
    co = list(viec.get("phong") or [])
    for s in slugs or []:
        s = str(s or "").strip()
        if s in co and s not in hop:
            hop.append(s)
    for s in co:
        if s not in hop:
            hop.append(s)
    if not hop:
        raise LoiNhacTruong("Việc cần ít nhất một phòng.")
    viec["phong"] = hop
    viec["thu_tu_phong"] = hop
    kho.luu_viec(viec)
    return viec


def chan_chay_thu(viec: dict) -> str:
    """Chạy thử chỉ cho việc trống. Không trộn lời giả vào việc đã nói."""
    if viec.get("loi"):
        return "Việc đã có lời. Chạy thử chỉ dùng khi việc còn trống. Dùng Chạy tiếp hoặc Chạy lại."
    return ""


def ket_phan(viec: dict) -> str:
    """Bản nhìn thấy được khi dừng giữa chừng hoặc chưa viết kết quả."""
    co = (viec.get("ket_qua") or "").strip()
    if co:
        return co
    parts = []
    for slug, text in (viec.get("ban") or {}).items():
        t = (text or "").strip()
        if t:
            parts.append(f"## {slug}\n{t}")
    if not parts:
        loi = [str(r.get("loi") or "").strip() for r in (viec.get("loi") or [])]
        loi = [x for x in loi if x]
        if loi:
            return "Bản dở, lời cuối đã có.\n\n" + loi[-1]
        return "Chưa có bản kết. Việc dừng trước khi viết xong."
    return "Bản dở, ghép từ phần đã làm.\n\n" + "\n\n".join(parts)


def _bi_huy(kho: Kho, vid: str) -> bool:
    try:
        return bool(kho.doc_viec(vid).get("huy"))
    except LoiNhacTruong:
        return False


def _mo_ta_phong(ds: list) -> str:
    dong = ["Các phòng đang có:"]
    for p in ds or []:
        truong = next((n.get("ten") for n in (p.get("nguoi") or []) if n.get("vai") == "truong"), "chưa có trưởng")
        dong.append(f"- {p.get('ten')} (mã {p.get('slug')}, trưởng {truong})")
    return "\n".join(dong)


def chon_phong(ds: list, chu: str) -> tuple[list, str]:
    """Chọn phòng theo đúng tên hoặc mã. Mơ hồ thì trả lời để hỏi lại, không đoán."""
    rooms = list(ds or [])
    if not rooms:
        return [], "Chưa có phòng nào. Bảo người dùng tạo phòng ở trang Nhạc trưởng trước."
    raw = (chu or "").strip()
    if not raw:
        if len(rooms) == 1:
            return rooms, ""
        return [], "Chưa chỉ phòng. Hỏi người dùng muốn giao phòng nào. Đừng đoán.\n" + _mo_ta_phong(rooms)
    chon = []
    for tok in [t.strip() for t in re.split(r"[,;\n]+", raw) if t.strip()]:
        q = slugify(tok)
        dung, gan = [], []
        for p in rooms:
            slug = str(p.get("slug") or "")
            ten = slugify(p.get("ten") or "")
            if q and (q == slug or q == ten):
                dung.append(p)
            elif q and len(q) >= 3 and ((ten and (q in ten or ten in q)) or (slug and q in slug)):
                gan.append(p)
        if len(dung) == 1:
            if dung[0] not in chon:
                chon.append(dung[0])
            continue
        if not dung and len(gan) == 1:
            if gan[0] not in chon:
                chon.append(gan[0])
            continue
        return [], f"Không chốt được phòng cho \"{tok}\". Hỏi lại, đừng đoán.\n" + _mo_ta_phong(rooms)
    if not chon:
        return [], "Chưa chọn được phòng.\n" + _mo_ta_phong(rooms)
    return chon, ""


def tao_viec(kho: Kho, tieu_de: str, brief: str, phong_slugs: list, vong: int = VONG_MAC_DINH,
             tai_lieu=None, xep: dict | None = None, bat_cong: bool = False) -> dict:
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
        "tai_lieu": chuan_tai_lieu(tai_lieu),
        "huy": False,
        "bat_cong": bool(bat_cong),
    }
    if isinstance(xep, dict) and xep:
        sach = {}
        for slug, day in xep.items():
            if slug not in slugs or not isinstance(day, list):
                continue
            sach[slug] = [str(s) for s in day if str(s).strip()][:12]
        if sach:
            named = {}
            for k, day in sach.items():
                by = {n.get("slug"): n for n in (kho.doc_phong(k).get("nguoi") or [])}
                hang = []
                for s in day:
                    n = by.get(s) or {}
                    hang.append({
                        "slug": s,
                        "ten": n.get("ten") or s,
                        "vi_tri": (n.get("vi_tri") or "").strip(),
                    })
                named[k] = hang
            viec["xep"] = named
            viec["xep_khoa"] = True
    kho.luu_viec(viec)
    return viec


def _gan_xep(kho: Kho, slugs: list, xep: dict | None) -> dict | None:
    if not isinstance(xep, dict) or not xep:
        return None
    sach = {}
    for slug, day in xep.items():
        if slug not in slugs or not isinstance(day, list):
            continue
        sach[slug] = [str(s) for s in day if str(s).strip()][:12]
    if not sach:
        return None
    named = {}
    for k, day in sach.items():
        by = {n.get("slug"): n for n in (kho.doc_phong(k).get("nguoi") or [])}
        named[k] = [{
            "slug": s,
            "ten": (by.get(s) or {}).get("ten") or s,
            "vi_tri": ((by.get(s) or {}).get("vi_tri") or "").strip(),
        } for s in day]
    return named


def sua_viec(kho: Kho, vid: str, tieu_de: str, brief: str, phong_slugs: list,
             vong: int = VONG_MAC_DINH, tai_lieu=None, xep: dict | None = None,
             bo_xep: bool = False, bat_cong=None) -> dict:
    """Sửa việc mới soạn, chưa chạy. Việc đã chạy thì sửa bằng comment."""
    viec = kho.doc_viec(vid)
    if viec.get("trang_thai") != "nhap":
        raise LoiNhacTruong("Việc đã chạy. Muốn sửa kết quả thì ghi comment và chạy lại.")
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
    viec["tieu_de"] = tieu_de
    viec["brief"] = brief
    viec["phong"] = slugs
    viec["vong_toi_da"] = vong
    if bat_cong is not None:
        viec["bat_cong"] = bool(bat_cong)
    viec["dat"] = {s: False for s in slugs}
    viec["khoa"] = {s: False for s in slugs}
    viec["ban"] = {s: "" for s in slugs}
    if tai_lieu is not None:
        viec["tai_lieu"] = chuan_tai_lieu(tai_lieu)
    if bo_xep:
        viec.pop("xep", None)
        viec["xep_khoa"] = False
    else:
        named = _gan_xep(kho, slugs, xep)
        if named:
            viec["xep"] = named
            viec["xep_khoa"] = True
    kho.luu_viec(viec)
    return viec


def _cat(text: str) -> str:
    t = (text or "").strip()
    if len(t) > LOI_TRAN:
        return t[:LOI_TRAN]
    return t


_MO_FILE = re.compile(r"(?m)^FILE:\s*(.*?)\s*$", re.I)
_HET_FILE = re.compile(r"(?m)^HET FILE\s*$", re.I)
_DONG_LENH = re.compile(r"^(?:NOI|NHAN|QUYET|QUYẾT|SUA|SỬA|TRA|THU[_ ]?TU|THỨ TỰ)\s*:", re.I)


def y_phan_hoi(text: str) -> str:
    """Giữ hết ý phản hồi. Bỏ dòng điều khiển, không rút còn một câu."""
    giu = []
    for ln in str(text or "").splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("{") and s.endswith("}"):
            continue
        if s.startswith("```"):
            continue
        if re.match(r"^(?:QUYET|QUYẾT|NHAN|NHẬN|TRA|THU[_ ]?TU|THỨ TỰ|FILE|HET FILE|NOI)\s*:", s, re.I):
            continue
        if re.match(r"^(?:SUA|SỬA)\s*:", s, re.I):
            rest = s.split(":", 1)[1].strip()
            if rest:
                giu.append("- " + rest)
            continue
        giu.append(s)
    return "\n".join(giu).strip()


def _y_chinh(text: str, tran: int = 700) -> str:
    """Phần hiện trong hội thoại: ý chính, không phải cả bản."""
    dong = []
    n = 0
    for ln in str(text or "").splitlines():
        s = ln.strip()
        if not s or _DONG_LENH.match(s) or re.match(r"^(?:FILE|HET FILE)\s*:", s, re.I):
            continue
        if dong and n + len(s) > tran:
            break
        dong.append(s)
        n += len(s) + 1
        if n >= tran:
            break
    return "\n".join(dong).strip() or "Bản đầy đủ nằm trong file đính kèm."


def _giu_ban(cu: str, moi: str) -> str:
    """Sửa bài không được thay bản dài bằng một mẩu ngắn."""
    cu, moi = (cu or "").strip(), (moi or "").strip()
    if not moi:
        return cu
    if not cu or len(cu) < 800 or len(moi) >= int(len(cu) * 0.35) or cu in moi:
        return moi
    return cu


def tach_tra_loi(text: str, giau: bool = False) -> dict:
    """Tách câu nói ngắn và file đính kèm. Bản dài luôn nằm trong file khi giau=True."""
    raw = str(text or "").strip()
    m = _MO_FILE.search(raw)
    if not m:
        if giau and len(raw) > 700:
            return {
                "noi": _y_chinh(raw),
                "ban": raw,
                "ten": "ban-day-du.md",
                "tep": raw,
                "ngoai": raw,
            }
        return {"noi": raw, "ban": raw, "ten": "", "tep": "", "ngoai": raw}
    ten = (m.group(1) or "").strip() or "tai-lieu.md"
    sau = raw[m.end():]
    if sau.startswith("\n"):
        sau = sau[1:]
    het = _HET_FILE.search(sau)
    if het:
        than = sau[:het.start()].strip()
        duoi = sau[het.end():].strip()
    else:
        than = sau.strip()
        duoi = ""
    dau = raw[:m.start()].strip()
    ngoai = "\n".join(x for x in (dau, duoi) if x).strip()
    noi = []
    for line in ngoai.splitlines():
        s = line.strip()
        mn = re.match(r"^NOI:\s?(.*)$", s, re.I)
        if mn and mn.group(1).strip():
            noi.append(mn.group(1).strip())
    if not noi:
        noi = [s for s in dau.splitlines() if s.strip() and not _DONG_LENH.match(s.strip())]
    cau = "\n".join(noi).strip() or ("Đã gửi file " + ten + ".")
    return {"noi": cau, "ban": than or raw, "ten": ten[:80], "tep": than, "ngoai": ngoai or raw}


def _tep_row(t: dict):
    if not (t.get("tep") or "").strip():
        return None
    return {"ten": t.get("ten") or "tai-lieu.md", "noi_dung": t["tep"]}


def _nhan(nguoi: dict) -> str:
    ten = nguoi.get("ten") or ""
    vt = (nguoi.get("vi_tri") or "").strip()
    if nguoi.get("vai") == "truong":
        return f"{ten} (trưởng)" + (f", {vt}" if vt else "")
    return f"{ten} ({vt})" if vt else ten


def _them(viec: dict, phong: dict, nguoi: dict, lop: str, vong: int, loi: str,
          quyet: str = "", giao_cho: str = "", tep: dict | None = None) -> None:
    row = {
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
    }
    if tep and str(tep.get("noi_dung") or "").strip():
        row["tep"] = {
            "ten": (str(tep.get("ten") or "tai-lieu.md").strip() or "tai-lieu.md")[:80],
            "noi_dung": _cat(str(tep.get("noi_dung") or "")),
        }
    viec["loi"].append(row)


def _bao(kho: Kho, viec: dict, phong: dict, nguoi: dict, buoc: str, giao: dict | None = None) -> None:
    """Ghi người đang nói trước khi model trả lời, để trang theo dõi không đứng trống."""
    if _bi_huy(kho, viec["id"]):
        raise LoiDung("Đã dừng.")
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
         quyet: str = "", giao_cho: str = "", tep: dict | None = None) -> None:
    _them(viec, phong, nguoi, lop, vong, loi, quyet, giao_cho, tep)
    kho.luu_viec(viec)


def loai_hang(phong: dict, viec: dict | None = None) -> str:
    """Phòng nộp file gì. Loại gắn trên phòng được tin trước tên."""
    gan = str((phong or {}).get("loai") or "").strip()
    if gan == "viet":
        return ""
    if gan in ("thiet_ke", "video"):
        return gan
    nguoi = (phong or {}).get("nguoi") or []
    blob = _khong_dau(" ".join([
        (phong or {}).get("ten") or "",
        " ".join((n.get("vi_tri") or "") for n in nguoi),
        " ".join(" ".join(n.get("skills") or []) for n in nguoi),
    ])).lower()
    def diem(tu):
        return sum(1 for t in tu if t in blob)
    video = diem(("video", "lam video", "clip", "phim", "motion"))
    ve = diem(("thiet ke", "design", "poster", "logo", "banner", "thumbnail", "nhan dien", "do hoa", "graphic"))
    if video > ve and video:
        return "video"
    if ve:
        return "thiet_ke"
    if video:
        return "video"
    return ""


def theo_bo(viec: dict) -> bool:
    b = _khong_dau((viec or {}).get("brief") or "")
    return any(k in b for k in ("theo bo", "bo nhan dien", "thiet ke bo", "mot bo", "design system"))


def _tom_khuon(truong: list, ban: str) -> str:
    """Chỉ các trường đã đủ. Thiếu trường thì trả rỗng để người gọi giữ nguyên bản."""
    gia = _gia_tri_khuon(ban)
    if not truong or any(t not in gia for t in truong):
        return ""
    return "\n".join(f"## {t}\n{gia[t]}" for t in truong)


def _truoc(viec: dict, slug: str, phong: dict | None = None) -> list:
    """Hàng các phòng đứng trước. Phòng viết chỉ nhận trường đã chốt. Phòng vẽ vẫn nhận cả bản."""
    slugs = list((viec or {}).get("phong") or [])
    if slug not in slugs:
        return []
    giu_day = loai_hang(phong or {}, viec) in ("thiet_ke", "video")
    dong = []
    hang = (viec or {}).get("hang") or {}
    da = (viec or {}).get("khuon_da") or {}
    for s in slugs[:slugs.index(slug)]:
        ban = str(((viec or {}).get("ban") or {}).get(s) or "").strip()
        files = hang.get(s) or []
        if not ban and not files:
            continue
        if not dong:
            dong.append("HÀNG PHÒNG TRƯỚC ĐÃ CHỐT. Dùng làm đầu vào. Không viết lại, không xoá.")
        dong.append(f"[{s}]")
        tom = "" if giu_day else _tom_khuon(da.get(s) or [], ban)
        if ban:
            dong.append(tom or ban)
        for it in files[:6]:
            dong.append("- " + str(it.get("ten") or "món") + ": " + str(it.get("file") or it.get("loi") or ""))
    return dong


def _yeu_cau_hang(phong: dict, viec: dict) -> list:
    k = loai_hang(phong, viec)
    if k == "thiet_ke":
        dong = [
            "Phòng này nộp thiết kế, không nộp lời hứa.",
            "Cuối bản, mỗi món một dòng: MON: Tên | landscape | mô tả hình đủ để vẽ",
            "Tỉ lệ chỉ landscape, portrait hoặc square.",
        ]
        if theo_bo(viec):
            dong.append("Brief xin một bộ. Nộp ít nhất 3 món, cùng màu và cùng kiểu, tối đa 6.")
        else:
            dong.append("Nộp đúng các món brief xin, tối đa 6.")
        return dong
    if k == "video":
        return [
            "Phòng này nộp video, không nộp lời hứa.",
            "Cuối bản, mỗi cảnh một dòng: CANH: hình thấy gì và câu thoại",
            "Tối đa 4 cảnh, ngắn.",
        ]
    return []


def doc_hang(text: str, kind: str) -> list:
    """Đọc các dòng MON hoặc CANH ở cuối bản làm."""
    out = []
    for line in (text or "").splitlines():
        s = line.strip()
        if kind == "thiet_ke" and re.match(r"^MON:\s*", s, re.I):
            parts = [p.strip() for p in s.split(":", 1)[1].split("|")]
            ten = (parts[0] if parts else "")[:80] or f"Món {len(out) + 1}"
            ti = (parts[1] if len(parts) > 1 else "landscape").lower()
            if ti not in ("landscape", "portrait", "square"):
                ti = "landscape"
            mo = (parts[2] if len(parts) > 2 else ten)[:500]
            out.append({"ten": ten, "ti_le": ti, "mo_ta": mo, "loai": "anh"})
        elif kind == "video" and re.match(r"^CANH:\s*", s, re.I):
            mo = s.split(":", 1)[1].strip()[:300]
            out.append({"ten": f"Cảnh {len(out) + 1}", "ti_le": "landscape", "mo_ta": mo, "loai": "video"})
        if len(out) >= 6:
            break
    return out


def _mon_du_phong(text: str, viec: dict, kind: str) -> list:
    raw = (text or "").strip() or str((viec or {}).get("brief") or "").strip()
    if not raw:
        return []
    if kind == "video":
        return [{"ten": "Video", "ti_le": "landscape", "mo_ta": raw[:400], "loai": "video"}]
    parts = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip() and not re.match(r"^MON:\s*", p.strip(), re.I)]
    if theo_bo(viec) and len(parts) < 3:
        cau = [c.strip() for c in re.split(r"[.。]\s+", raw) if len(c.strip()) > 20]
        if len(cau) >= 3:
            parts = cau
    parts = parts[:4] if theo_bo(viec) else parts[:1]
    return [
        {"ten": f"Món {i}", "ti_le": "landscape", "mo_ta": p[:400], "loai": "anh"}
        for i, p in enumerate(parts, 1)
    ]


async def _goi_ra(ra_file, viec_id, phong_slug, loai, ten, mo_ta, ti_le, script) -> dict:
    try:
        kq = ra_file(viec_id, phong_slug, loai, ten, mo_ta, ti_le, script)
        if hasattr(kq, "__await__"):
            kq = await kq
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return kq if isinstance(kq, dict) else {"ok": False, "error": "Không ra file."}


async def _nop_hang(kho: Kho, viec: dict, phong: dict, ra_file) -> None:
    """Một lần khi phòng làm xong: ảnh, video, hoặc không file nếu phòng chỉ viết chữ."""
    if ra_file is None:
        return
    kind = loai_hang(phong, viec)
    if not kind:
        return
    ban = (viec.get("ban") or {}).get(phong["slug"]) or ""
    items = doc_hang(ban, kind) or _mon_du_phong(ban, viec, kind)
    nop = []
    if kind == "video":
        script = "\n".join(it.get("mo_ta") or "" for it in items).strip()
        kq = await _goi_ra(ra_file, viec["id"], phong["slug"], "video", viec.get("tieu_de") or "Video", script, "landscape", script)
        nop.append({
            "ten": viec.get("tieu_de") or "Video",
            "loai": "video",
            "mo_ta": script,
            "file": kq.get("file") or "",
            "loi": "" if kq.get("ok") else (kq.get("error") or "Không ra video."),
        })
    else:
        for it in items[:6]:
            kq = await _goi_ra(
                ra_file, viec["id"], phong["slug"], "anh",
                it.get("ten") or "Món", it.get("mo_ta") or "", it.get("ti_le") or "landscape", "",
            )
            nop.append({
                "ten": it.get("ten") or "Món",
                "loai": "anh",
                "mo_ta": it.get("mo_ta") or "",
                "ti_le": it.get("ti_le") or "landscape",
                "file": kq.get("file") or "",
                "loi": "" if kq.get("ok") else (kq.get("error") or "Không ra ảnh."),
            })
    viec.setdefault("hang", {})[phong["slug"]] = nop
    kho.luu_viec(viec)


def muc_hang(viec: dict) -> str:
    hang = viec.get("hang") or {}
    if not hang:
        return ""
    dong = ["## Hàng đã nộp"]
    for slug in viec.get("phong") or list(hang):
        items = hang.get(slug) or []
        if not items:
            continue
        dong.append(f"### {slug}")
        for it in items:
            ten = it.get("ten") or "món"
            if it.get("file"):
                dong.append(f"- {ten}: {it['file']}")
            else:
                dong.append(f"- {ten}: chưa có file. {it.get('loi') or ''}".rstrip())
    return "\n".join(dong).strip()


def _gan_ket(viec: dict) -> None:
    phu = muc_hang(viec)
    if not phu:
        return
    co = (viec.get("ket_qua") or "").rstrip()
    if phu in co:
        return
    viec["ket_qua"] = (co + "\n\n" + phu).strip()


_CHO_QUA = {"x", "xx", "xxx", "...", ".", "-", "na", "n/a", "chua", "tbd", "todo", "ok", "yes", "no"}


def _du_truong(raw) -> bool:
    """Một chữ hoặc chữ giữ chỗ thì chưa phải nội dung. Số ngắn vẫn tính."""
    s = " ".join(str(raw or "").split())
    if not s:
        return False
    if _khong_dau(s).lower().strip(".") in _CHO_QUA:
        return False
    if any(ch.isdigit() for ch in s) and len(s) >= 2:
        return True
    return len(s) >= 4


def _gia_tri_khuon(ban: str) -> dict:
    """Giá trị từng trường trong bản. Chỉ giữ trường có nội dung thật."""
    co = {}
    for obj in _cac_obj(ban or ""):
        art = obj.get("artifact")
        if isinstance(art, dict):
            for k, v in art.items():
                s = slugify(str(k))
                if s and _du_truong(v):
                    co[s] = " ".join(str(v).split())[:200]
    for p in re.split(r"(?m)^##\s+", ban or "")[1:]:
        dong, _, than = p.partition("\n")
        s = slugify(dong)
        doan = than.strip().split("\n\n", 1)[0]
        dong_sach = [ln for ln in doan.splitlines() if not re.match(r"^\s*FACT\s*:", ln, re.I)]
        doan = "\n".join(dong_sach).strip()
        if s and _du_truong(doan):
            co[s] = " ".join(doan.split())[:200]
    return co


def _truong_khuon(phong: dict) -> list:
    can = []
    for t in ((phong or {}).get("khuon") or {}).get("truong") or []:
        s = slugify(str(t))
        if s and s not in can:
            can.append(s)
    return can


def thieu_khuon(phong: dict, ban: str) -> list:
    """Trường khuôn còn trống hoặc chỉ một chữ. Phòng không có khuôn thì không bắt."""
    can = _truong_khuon(phong)
    if not can:
        return []
    co = _gia_tri_khuon(ban)
    return [t for t in can if t not in co]


def doc_fact(text: str) -> list:
    """FACT: khoa = gia tri, hoặc JSON facts. Không suy diễn."""
    out = []
    for obj in _cac_obj(text or ""):
        for it in obj.get("facts") or []:
            if not isinstance(it, dict):
                continue
            k = slugify(str(it.get("khoa") or ""))
            v = str(it.get("gia_tri") or "").strip()[:200]
            if k and v:
                out.append({"khoa": k, "gia_tri": v})
    for ln in (text or "").splitlines():
        m = re.match(r"^FACT:\s*(.+?)\s*=\s*(.+)$", ln.strip(), re.I)
        if not m:
            continue
        k = slugify(m.group(1))
        v = m.group(2).strip()[:200]
        if k and v:
            out.append({"khoa": k, "gia_tri": v})
    return out


def gop_fact(viec: dict, nguon: str, text: str, phong: dict | None = None) -> None:
    """Sổ dùng chung. Trường khuôn vào sổ trước. Dòng FACT ghi đè nếu cùng khóa."""
    by = {f.get("khoa"): f for f in (viec.get("so") or []) if f.get("khoa")}
    gia = _gia_tri_khuon(text or "")
    for k in _truong_khuon(phong or {}):
        if k in gia:
            by[k] = {"khoa": k, "gia_tri": gia[k], "nguon": nguon}
    for f in doc_fact(text):
        by[f["khoa"]] = {"khoa": f["khoa"], "gia_tri": f["gia_tri"], "nguon": nguon}
    viec["so"] = list(by.values())[:12]


def _cho_cong(viec: dict, cong: str) -> bool:
    if not (viec or {}).get("bat_cong"):
        return False
    return cong not in ((viec or {}).get("da_duyet") or [])


def _giao_chua_lam(viec: dict, slug: str) -> bool:
    """Đã có lệnh giao mà người làm chưa nói. Cổng kế hoạch còn hiệu lực."""
    rows = [r for r in (viec.get("loi") or []) if r.get("phong") == slug]
    if not rows:
        return False
    vong = max(int(r.get("vong") or 1) for r in rows)
    cung = [r for r in rows if int(r.get("vong") or 1) == vong]
    return any(r.get("lop") == "giao" for r in cung) and not any(r.get("lop") == "lam" for r in cung)


def tin_cong(viec: dict) -> str:
    cong = (viec or {}).get("cong") or ""
    ten = "kế hoạch phân công" if cong == "ke_hoach" else "bản thảo trước thiết kế"
    tieu = (viec or {}).get("tieu_de") or "việc"
    vid = (viec or {}).get("id") or ""
    return (
        f"Nhạc trưởng chờ duyệt {ten}: {tieu} ({vid}). "
        "Bấm Đồng ý, hoặc nhắn \"đồng ý\" hay \"duyệt\" kèm một câu nếu muốn sửa hướng."
    )


def nut_duyet(viec: dict) -> dict | None:
    """Nút Telegram. Mã nút không được dài quá 64 byte."""
    vid = str((viec or {}).get("id") or "")
    data = f"ntd:{vid}"
    if not vid or len(data.encode()) > 64:
        return None
    return {"inline_keyboard": [[{"text": "Đồng ý", "callback_data": data}]]}


def la_dong_y(text: str) -> tuple[bool, str]:
    """Câu bắt đầu bằng đồng ý hoặc duyệt. Phần sau là góp ý."""
    raw = " ".join(str(text or "").split())
    if not raw:
        return False, ""
    tu = raw.split(" ")
    dau = _khong_dau(tu[0]).lower().strip(",:;")
    if dau == "duyet":
        return True, " ".join(tu[1:])[:300]
    if dau == "dong" and len(tu) > 1 and _khong_dau(tu[1]).lower().strip(",:;") == "y":
        return True, " ".join(tu[2:])[:300]
    return False, ""


def viec_dang_cho(kho: Kho) -> list:
    out = []
    thu = kho.goc / "viec"
    if not thu.is_dir():
        return out
    for p in sorted(thu.glob("*.json")):
        try:
            v = kho.doc_viec(p.stem)
        except LoiNhacTruong:
            continue
        if v.get("trang_thai") == "cho_duyet" and v.get("cong"):
            out.append(v)
    return out


def thu_duyet(kho: Kho, text: str):
    """Duyệt nếu đang có việc chờ. Không có việc thì trả (None, None) để chat đi tiếp."""
    ok, _y = la_dong_y(text)
    if not ok:
        return None, None
    try:
        return duyet_loi(kho, text), None
    except LoiNhacTruong as e:
        if str(e).startswith("Không có việc"):
            return None, None
        return None, str(e)


def duyet_loi(kho: Kho, text: str, vid: str = "") -> dict:
    """Duyệt việc đang chờ từ một câu đồng ý. Chưa chạy tiếp."""
    ok, y = la_dong_y(text)
    if vid:
        return duyet(kho, vid, y if ok else (text or "").strip()[:300])
    if not ok:
        raise LoiNhacTruong("Chưa phải câu duyệt. Nhắn \"đồng ý\" hoặc \"duyệt\" kèm một câu.")
    cho = viec_dang_cho(kho)
    if not cho:
        raise LoiNhacTruong("Không có việc nào đang chờ duyệt.")
    if len(cho) > 1:
        ds = ", ".join(f"{v.get('tieu_de')} ({v.get('id')})" for v in cho[:6])
        raise LoiNhacTruong("Có nhiều việc đang chờ. Nói rõ mã: " + ds)
    return duyet(kho, cho[0]["id"], y)


def duyet(kho: Kho, vid: str, y: str = "") -> dict:
    """Ghi cổng đã duyệt. Không xoá lời đã nói. Chưa chạy tiếp."""
    viec = kho.doc_viec(vid)
    if viec.get("trang_thai") != "cho_duyet":
        raise LoiNhacTruong("Việc không đang chờ duyệt.")
    cong = (viec.get("cong") or "").strip()
    if cong not in ("ke_hoach", "ban_thao"):
        raise LoiNhacTruong("Không rõ cổng cần duyệt.")
    da = list(viec.get("da_duyet") or [])
    if cong not in da:
        da.append(cong)
    viec["da_duyet"] = da
    y = (y or "").strip()[:300]
    if y:
        viec["y_kien"] = y
    viec["cong"] = ""
    viec["xin_y"] = ""
    kho.luu_viec(viec)
    return viec


def lap_prompt(loai: str, nguoi: dict, phong: dict, viec: dict, ban: str = "",
               lenh: str = "", cac_ban: dict | None = None, giao_cho: dict | None = None,
               thanh_vien: list | None = None, luot: int = 0) -> str:
    """Câu chat thì ngắn. Bản việc, tài liệu và kết quả cũ đi nguyên văn cho bước sau."""
    ban_day = ban or ""
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
    if viec.get("y_kien"):
        dong.append("Ý CHỈ ĐẠO, làm theo câu này, không làm lại từ đầu: " + str(viec.get("y_kien")))
    so = viec.get("so") or []
    if so:
        dong.append("SỔ VIỆC, số đã chốt, dùng lại, không phân tích lại:")
        for f in so[:12]:
            dong.append("- " + str(f.get("khoa") or "") + ": " + str(f.get("gia_tri") or "")
                        + " (nguồn: " + str(f.get("nguon") or "") + ")")
    khuon = (phong.get("khuon") or {}).get("truong") or []
    if khuon and loai in ("LAM", "GIAO", "KIEM"):
        dong.append("Khuôn bàn giao. Mỗi trường một đề mục ## đúng tên, không để trống: " + ", ".join(khuon))
        dong.append("Số đã kiểm thì thêm một dòng FACT: khoa = gia tri.")
    if viec.get("lenh_them"):
        dong.append("COMMENT MUỐN SỬA: " + str(viec.get("lenh_them")))
    if viec.get("ket_cu") and loai in ("KET", "THEM", "SUA", "LAM"):
        cu = str(viec.get("ket_cu") or "")
        dong.append("KẾT QUẢ CŨ, giữ phần comment không đụng:")
        dong.append(cu)
    tl = viec.get("tai_lieu") or []
    if tl and loai in ("LAM", "KET", "GIAO", "THEM", "CAP"):
        dong.append("TÀI LIỆU THAM KHẢO, tối đa 3 file, nguyên văn:")
        for f in tl[:3]:
            dong.append(str(f.get("ten") or "file") + ":\n" + str(f.get("noi_dung") or ""))
    if loai == "KET":
        dong.append("Viết bản kết quả cuối, đầy đủ, dùng được ngay. Không kể lại cuộc nói. Không cắt giữa chừng.")
    elif loai in ("LAM", "DOI", "CAP", "THEM"):
        dong.append("Câu NOI chỉ là lời bàn giao, ngắn. Bản dài để trong FILE, không viết vào câu nói.")
    elif loai == "NHAN":
        dong.append("Câu NOI là phản hồi ngắn. Chưa được thì gạch đầu dòng từng điểm. Không dán cả bài vào câu nói.")
    elif loai not in ("CAP", "THEM"):
        dong.append("Câu bạn nói thì một hoặc hai câu. Nêu chỗ thiếu hoặc chỗ cần sửa. Không dán bảng.")
        dong.append("File đính kèm là bản đủ. Không được kết luận là bị cắt ngắn.")
    if loai == "GIAO":
        dong.extend(_truoc(viec, phong.get("slug") or "", phong))
        dong.append("Vài dòng: ai làm gì. Không viết bài.")
        yeu = _yeu_cau_hang(phong, viec)
        if yeu:
            dong.append("Nếu phòng chưa có người làm, chính bạn viết các dòng MON hoặc CANH ở cuối.")
            dong.extend(yeu)
        if thanh_vien:
            khoa = bool(viec.get("xep_khoa"))
            dong.append("Thứ tự đã khóa, làm đúng:" if khoa else "Quy trình có sẵn của phòng:")
            for i, m in enumerate(thanh_vien, 1):
                dong.append(f"{i}. {_nhan(m)} | slug {m.get('slug')}")
            if khoa:
                dong.append("Không đảo thứ tự. Không viết dòng THU_TU.")
            else:
                dong.append("Việc đi đúng quy trình thì giữ thứ tự đó. Việc thực tế không cần ai, hoặc cần đảo bước, thì xếp lại.")
                dong.append("Kết thúc bằng đúng một dòng: THU_TU: slug > slug")
        elif giao_cho:
            dong.append("Bước 1 là " + _nhan(giao_cho) + ".")
    elif loai == "NHAN":
        dong += [
            "Bạn nhận bàn giao từ " + (_nhan(giao_cho) if giao_cho else "bước trước") + ".",
            "FILE ĐÍNH KÈM, đọc hết, đây là bản đủ:",
            "BẢN ĐANG NHẬN:",
            ban or "(trống)",
            "HẾT BẢN",
            "NOI: một câu nếu nhận. Nếu chưa, mỗi điểm một gạch đầu dòng, không tóm tắt lại bài.",
            "Chưa nhận thì chưa làm phần của bạn.",
            "Nếu chưa được, kèm FILE đã ghi note ngay chỗ cần sửa. Giữ nguyên phần còn lại của file.",
            "FILE: ten.md",
            "nội dung file đã note",
            "HET FILE",
            "Chỉ NHAN: CHUA khi còn một lỗi cụ thể: sai brief, thiếu ý, mâu thuẫn, hoặc câu bị cấm.",
            "Hết lỗi thì NHAN: OK ngay, kể cả lượt đầu. Không bịa chỗ chưa chắc để kéo dài. Lúc OK không cần FILE.",
            "Các dòng NHAN và SUA để sau HET FILE.",
            "NHAN: OK",
            "hoặc",
            "NHAN: CHUA",
            "SUA: một câu chỗ chưa ổn",
            "Có thể thêm một dòng JSON. Dòng này được đọc trước NHAN.",
            '{"nhan":"OK","sua":""}',
            "hoặc",
            '{"nhan":"CHUA","sua":"một câu chỗ chưa ổn"}',
        ]
    elif loai == "DOI":
        dong += [
            (_nhan(giao_cho) if giao_cho else "Bước sau") + " chưa nhận bài của bạn.",
            "Ý kiến của họ, gạch đầu dòng:",
            lenh or "chưa rõ.",
            "FILE HỌ ĐÃ NOTE:",
            ban or "(trống)",
            "HẾT BẢN",
            "NOI: một câu, đã sửa theo ý kiến và bàn giao lại.",
            "FILE: ban-da-sua.md",
            "Viết lại cả file cho đủ sau khi sửa, không chỉ liệt kê điểm đã đổi. Không cắt giữa chừng.",
            "HET FILE",
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
            "Có thể thêm một dòng JSON. Dòng này được đọc trước QUYET.",
            '{"quyet":"LAM","sua":"","tra":""}',
            "hoặc",
            '{"quyet":"SUA","sua":"một câu bước trước phải sửa","tra":""}',
        ]
    elif loai == "LAM":
        dong.extend(_truoc(viec, phong.get("slug") or "", phong))
        dong.extend(_yeu_cau_hang(phong, viec))
        dong += [
            "Đúng khuôn, câu nói trước, file sau:",
            "NOI: Tôi bàn giao. Ông đọc file. Lưu ý: việc bước sau cần làm.",
            "FILE: ban-buoc.md",
            "Nội dung đủ của bước này. Viết gọn, chia mục, không lặp, không cắt.",
            "HET FILE",
        ]
        if ban:
            dong += [
                "FILE BƯỚC TRƯỚC ĐÃ CHỐT, đọc hết:",
                ban,
                "HẾT BẢN",
                "Phần này đã được nhận. File của bạn là phần mới, không chép nguyên file trước vào câu nói.",
            ]
        else:
            dong.append("File là phần đủ của bạn. Người sau chỉ nêu điểm cần sửa, không viết lại hộ.")
        if giao_cho:
            dong.append("Trong NOI, nói rõ bàn giao cho " + _nhan(giao_cho) + " và điểm lưu ý họ cần làm.")
        if lenh:
            dong.append("LỆNH SỬA: " + lenh)
            dong.append("File lần này là bản đủ sau khi sửa đúng các điểm bị bắt.")
    elif loai == "KIEM":
        dong += [
            "Bạn đang kiểm bản phòng mình. Đọc để tìm lỗi cụ thể.",
            "BAN HIỆN TẠI:",
            ban or "(trống)",
            "HẾT BẢN",
            "Không viết lại bản vào câu nói. NOI là các gạch đầu dòng, mỗi lỗi một dòng, viết hết lỗi nhìn thấy.",
            "Người sửa chỉ nhận các dòng này và file. Viết đủ ý để họ sửa được, không rút một câu.",
            "Chỉ xét BAN HIỆN TẠI. Hết lỗi thì QUYET: DAT ngay, dù mới vòng 1 hoặc 2.",
            "Chỉ CHUA khi còn lỗi cụ thể chưa được sửa. Không lặp lỗi đã sửa. Không bịa lỗi để dùng hết số vòng.",
            "Kết thúc bằng đúng một trong hai:",
            "QUYET: DAT",
            "hoặc",
            "QUYET: CHUA",
            "SUA: ý chính của các dòng trên",
            "Có thể thêm một dòng JSON. Dòng này được đọc trước QUYET.",
            '{"quyet":"DAT","sua":"","tra":""}',
            "hoặc",
            '{"quyet":"CHUA","sua":"ý chính các lỗi","tra":""}',
        ]
    elif loai == "HOP":
        dong.append("HỌP TRƯỞNG. Chỉ các trưởng phòng. Bạn không sửa hộ phòng khác.")
        dong.append("Bạn chỉ ghi DAT khi tiêu chí phòng mình đạt trên các bản dưới đây.")
        dong.append("Hết lỗi thì DAT ngay, dù mới vòng 1 hoặc 2. Chỉ CHUA khi còn lỗi cụ thể chưa được sửa.")
        dong.append("Không lặp lại lỗi đã sửa. Không bịa lỗi để dùng hết số vòng.")
        dong.append("Không viết lại bản. NOI là gạch đầu dòng đủ từng lỗi. Rồi QUYET, SUA là ý chính, và TRA.")
        for slug, text in (cac_ban or {}).items():
            dong += [f"[{slug}]", text or "(trống)"]
        dong += [
            "Kết thúc bằng:",
            "QUYET: DAT",
            "hoặc",
            "QUYET: CHUA",
            "SUA: ý chính các lỗi",
            "TRA: slug phòng phải sửa",
            "Có thể thêm một dòng JSON. Dòng này được đọc trước QUYET.",
            '{"quyet":"DAT","sua":"","tra":""}',
            "hoặc",
            '{"quyet":"CHUA","sua":"ý chính các lỗi","tra":"slug-phong"}',
        ]
    elif loai == "KET":
        dong.append("Ghép các bản dưới đây thành một kết quả cho người giao việc.")
        dong.append("Giữ nội dung đã làm. Bỏ câu trao đổi. Không ghi QUYET.")
        if viec.get("mo"):
            dong.append("Còn lệch: " + "; ".join(viec.get("mo") or []))
        for slug, text in (cac_ban or {}).items():
            dong += [f"[{slug}]", text or "(trống)"]
        phu = muc_hang(viec)
        if phu:
            dong.append(phu)
            dong.append("Ghi đúng các file ở trên. Không bịa link.")
    elif loai == "CAP":
        dong.extend(_truoc(viec, phong.get("slug") or "", phong))
        dong.extend(_yeu_cau_hang(phong, viec))
        dong += [
            "Phòng trước vừa nộp lại hàng. Cập nhật phần phòng bạn cho khớp hàng mới.",
            "Giữ ý cũ nếu vẫn đúng. Không viết lại phần phòng trước.",
            "BẢN CŨ CỦA PHÒNG BẠN:",
            ban or "(trống)",
            "HẾT BẢN",
            "NOI: một câu đã cập nhật.",
            "FILE: ban-cap.md",
            "Bản đủ của phòng bạn sau khi khớp hàng mới. Không viết phần phòng trước.",
            "HET FILE",
        ]
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
            "Một hoặc hai câu. Điểm nào giữ, điểm nào sửa. Gạch đầu dòng. Không viết lại bài. Không viết QUYET.",
        ]
    elif loai == "THEM":
        dong += [
            "Chạy thêm trên kết quả cũ, theo comment. Không kể lại cuộc nói.",
            "BẢN PHÒNG HIỆN TẠI:",
            ban or "(trống)",
            "HẾT BẢN",
            "NOI: một câu, chỗ vừa đổi.",
            "FILE: ban-sua.md",
            "Viết lại đủ phần phòng bạn. Giữ chỗ comment không đụng.",
            "HET FILE",
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


_CANH_CAT = "Phản hồi bị cắt"


def _bo_canh_cat(text: str) -> str:
    t = str(text or "")
    t = re.sub(r"⚠️?\s*Phản hồi bị cắt do hết max_tokens\.[^\n]*", "", t)
    t = re.sub(r"(?m)^CON_TIEP\s*$", "", t)
    return t.strip()


def _ghep_manh(manh: list) -> str:
    """Ghép các lần viết tiếp thành một lời, giữ NOI và FILE của phần đầu."""
    sach = [_bo_canh_cat(m) for m in manh if _bo_canh_cat(m)]
    if not sach:
        return ""
    if len(sach) == 1:
        return sach[0]
    dau = sach[0]
    them = []
    for phan in sach[1:]:
        phan = re.sub(r"(?m)^NOI:.*(?:\n|$)", "", phan)
        phan = re.sub(r"(?m)^FILE:.*(?:\n|$)", "", phan, count=1)
        phan = phan.strip()
        if phan:
            them.append(phan)
    hop = dau.rstrip() + ("\n" + "\n".join(them) if them else "")
    if "HET FILE" in hop:
        than, _, cuoi = hop.rpartition("HET FILE")
        hop = than.rstrip() + "\nHET FILE" + cuoi.replace("HET FILE", "")
    return hop.strip()


async def _goi_du(noi, nguoi: dict, prompt: str, lan: int = 4) -> str:
    """Nếu model bị cắt giữa bản dài thì gọi viết tiếp và ghép lại."""
    manh = []
    yeu = prompt
    for _ in range(max(1, lan)):
        text = await _goi(noi, nguoi, yeu)
        bi_cat = _CANH_CAT in text or bool(re.search(r"(?m)^CON_TIEP\s*$", text))
        manh.append(_bo_canh_cat(text))
        if not bi_cat:
            break
        da = _ghep_manh(manh)
        yeu = (
            "Viết TIẾP đúng chỗ đang dừng. Không lặp phần đã có. Không mở đầu lại.\n"
            "Câu NOI giữ nguyên ý đã nói. Phần FILE viết tiếp cho đủ.\n"
            "Khi hết nội dung thì một dòng HET FILE.\n"
            "PHẦN ĐÃ CÓ, bám chữ cuối:\n"
            + da[-8000:]
        )
    return _cat(_ghep_manh(manh))


def _rows_phong(viec: dict, slug: str) -> list:
    return [r for r in (viec.get("loi") or []) if r.get("phong") == slug]


def _ban_row(row: dict) -> str:
    tep = (row.get("tep") or {}).get("noi_dung") if isinstance(row.get("tep"), dict) else ""
    return (tep or row.get("loi") or "").strip()


def _lenh_vong_truoc(rows: list, vong: int) -> str:
    if vong <= 1:
        return ""
    for r in reversed(rows):
        if int(r.get("vong") or 0) == vong - 1 and r.get("lop") == "kiem" and r.get("quyet") != "DAT":
            return y_phan_hoi(r.get("loi") or "") or "Sửa cho đúng tiêu chí phòng."
    return ""


async def _hoi_kiem(noi, truong: dict, phong: dict, viec: dict, ban: str) -> str:
    """Thiếu trường khuôn thì chưa gọi trưởng chấm."""
    thieu = thieu_khuon(phong, ban)
    if thieu:
        ds = ", ".join(thieu)
        return f"Thiếu trường bàn giao: {ds}\nQUYET: CHUA\nSUA: Điền đủ: {ds}"
    return await _goi_du(noi, truong, lap_prompt("KIEM", truong, phong, viec, ban=ban))


def _chot(viec: dict, phong: dict) -> None:
    slug = phong["slug"]
    viec["khoa"][slug] = True
    truong = _truong_khuon(phong)
    if truong:
        viec.setdefault("khuon_da", {})[slug] = truong
    gop_fact(viec, slug, (viec.get("ban") or {}).get(slug) or "", phong)


async def _kiem_mot(kho: Kho, viec: dict, phong: dict, noi, truong: dict, vong: int) -> tuple[str, str]:
    """Trưởng chấm bản đang có. Trả (dat|chua, lệnh sửa)."""
    _bao(kho, viec, phong, truong, "kiem")
    kiem = await _hoi_kiem(noi, truong, phong, viec, viec["ban"][phong["slug"]])
    q = doc_quyet(kiem)
    quyet = q["quyet"] or "CHUA"
    _ghi(kho, viec, phong, truong, "kiem", vong, kiem, quyet)
    if quyet == "DAT":
        _chot(viec, phong)
        return "dat", ""
    moi = y_phan_hoi(kiem) or q["sua"] or "Sửa cho đúng tiêu chí phòng."
    viec["mo"].append(f"{phong['ten']}: {moi}")
    return "chua", moi


async def _khep_song(kho: Kho, viec: dict, phong: dict, noi, vong: int, rows: list) -> tuple[str, str]:
    """Khép vòng đang dở khi mọi người làm cùng lúc. Trả (bo|dat|chua, lệnh)."""
    cung = [r for r in rows if int(r.get("vong") or 1) == vong]
    if not any(r.get("lop") == "giao" for r in cung):
        return "bo", ""
    truong = _truong(phong)
    mems = _mems(viec, phong)
    lenh = _lenh_vong_truoc(rows, vong)
    if not mems:
        if not (viec.get("ban") or {}).get(phong["slug"]):
            giao = next(r for r in cung if r.get("lop") == "giao")
            viec["ban"][phong["slug"]] = _ban_row(giao)
        if any(r.get("lop") == "kiem" for r in cung):
            return ("dat" if viec["khoa"].get(phong["slug"]) else "chua"), ""
        return await _kiem_mot(kho, viec, phong, noi, truong, vong)
    xong = {r.get("slug") for r in cung if r.get("lop") == "lam"}
    manh = []
    for mem in mems:
        if mem["slug"] in xong:
            cu = next(r for r in reversed(cung) if r.get("lop") == "lam" and r.get("slug") == mem["slug"])
            manh.append(_ban_row(cu))
            continue
        _bao(kho, viec, phong, mem, "lam")
        raw = await _goi_du(noi, mem, lap_prompt("LAM", mem, phong, viec, lenh=lenh))
        t = tach_tra_loi(raw, giau=True)
        _ghi(kho, viec, phong, mem, "lam", vong, t["noi"], tep=_tep_row(t))
        manh.append(t["ban"])
    hop = "\n\n".join(manh)
    if lenh:
        hop = _giu_ban(viec["ban"].get(phong["slug"]) or "", hop)
    viec["ban"][phong["slug"]] = hop
    if len(mems) > 1:
        da_gop = {r.get("slug") for r in cung if r.get("lop") == "gop"}
        for mem in mems:
            if mem["slug"] in da_gop:
                continue
            khac = next((m for m in mems if m["slug"] != mem["slug"]), None)
            _bao(kho, viec, phong, mem, "gop", khac)
            gop = await _goi_du(noi, mem, lap_prompt(
                "GOP", mem, phong, viec, ban=viec["ban"][phong["slug"]], giao_cho=khac))
            _ghi(kho, viec, phong, mem, "gop", vong, gop, giao_cho=_nhan(khac) if khac else "")
    if any(r.get("lop") == "kiem" for r in cung):
        return ("dat" if viec["khoa"].get(phong["slug"]) else "chua"), ""
    return await _kiem_mot(kho, viec, phong, noi, truong, vong)


async def _khep_lan(kho: Kho, viec: dict, phong: dict, noi, vong: int, rows: list) -> tuple[str, str]:
    """Khép vòng đang dở khi làm lần lượt. Người đã làm rồi thì không làm lại."""
    cung = [r for r in rows if int(r.get("vong") or 1) == vong]
    if not any(r.get("lop") == "giao" for r in cung):
        return "bo", ""
    truong = _truong(phong)
    mems = _mems(viec, phong)
    giao = next(r for r in cung if r.get("lop") == "giao")
    day = doc_thu_tu(giao.get("loi") or "", mems)
    if viec.get("xep_khoa") and (viec.get("xep") or {}).get(phong["slug"]):
        day = _theo_xep(viec, phong, mems)
    lenh = _lenh_vong_truoc(rows, vong)
    da_lam = {r.get("slug") for r in cung if r.get("lop") == "lam"}
    idx = 0
    while idx < len(day) and day[idx]["slug"] in da_lam:
        idx += 1
    manh_cu = []
    ban_san = ""
    for mem in day[:idx]:
        cu = next(r for r in reversed(cung) if r.get("lop") == "lam" and r.get("slug") == mem["slug"])
        ban_san = _ban_row(cu)
        manh_cu.append(f"[{_nhan(mem)}]\n{ban_san}")
    if idx < len(day):
        them = await _chuoi(
            kho, viec, phong, noi, day, lenh, vong,
            bat_dau=idx, ban_san=ban_san, manh_cu=manh_cu)
        hop = them
    else:
        hop = "\n\n".join(manh_cu)
    if lenh:
        hop = _giu_ban(viec["ban"].get(phong["slug"]) or "", hop)
    viec["ban"][phong["slug"]] = hop
    if any(r.get("lop") == "kiem" for r in cung):
        return ("dat" if viec["khoa"].get(phong["slug"]) else "chua"), ""
    return await _kiem_mot(kho, viec, phong, noi, truong, vong)


async def _tiep_phong(kho: Kho, viec: dict, phong: dict, noi, vmax: int) -> None:
    """Làm tiếp một phòng. Giữ người đã xong, giao lệnh sửa cho người kế."""
    slug = phong["slug"]
    if (viec.get("khoa") or {}).get(slug):
        return
    rows = _rows_phong(viec, slug)
    if not rows:
        await _noi_bo(kho, viec, phong, noi, vmax)
        return
    vong = max(int(r.get("vong") or 1) for r in rows)
    cung = [r for r in rows if int(r.get("vong") or 1) == vong]
    cuoi = cung[-1]
    lan = phong.get("cach_lam") == "lan_luot" and bool(_thanh_vien(phong))
    if cuoi.get("lop") == "kiem" and cuoi.get("quyet") == "DAT":
        viec.setdefault("khoa", {})[slug] = True
        return
    if cuoi.get("lop") == "kiem":
        lenh = y_phan_hoi(cuoi.get("loi") or "") or "Sửa cho đúng tiêu chí phòng."
        ban = (viec.get("ban") or {}).get(slug) or ""
        if lan:
            await _noi_bo_lan(kho, viec, phong, noi, vmax, tu=vong + 1, lenh0=lenh, ban0=ban)
        else:
            await _noi_bo(kho, viec, phong, noi, vmax, tu=vong + 1, lenh0=lenh, ban0=ban)
        return
    trang, lenh = await (_khep_lan if lan else _khep_song)(kho, viec, phong, noi, vong, rows)
    if trang == "bo":
        if lan:
            await _noi_bo_lan(kho, viec, phong, noi, vmax, tu=vong)
        else:
            await _noi_bo(kho, viec, phong, noi, vmax, tu=vong)
        return
    if trang != "chua" or vong >= vmax:
        if trang != "dat":
            viec["khoa"][slug] = False
        return
    ban = (viec.get("ban") or {}).get(slug) or ""
    if lan:
        await _noi_bo_lan(kho, viec, phong, noi, vmax, tu=vong + 1, lenh0=lenh, ban0=ban)
    else:
        await _noi_bo(kho, viec, phong, noi, vmax, tu=vong + 1, lenh0=lenh, ban0=ban)


async def chay(kho: Kho, vid: str, noi, ra_file=None, tu_dau: bool = False, bao=None) -> dict:
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
    # dang_chay mà không còn task (máy vừa khởi động lại) cũng là việc dở, không phải việc mới.
    # tu_dau là nút Chạy lại: xoá lời đã nói và làm từ đầu.
    tiep = (
        not tu_dau
        and bool(viec.get("loi"))
        and viec.get("trang_thai") in ("dung", "loi", "dang_chay", "cho_duyet")
    )
    viec["trang_thai"] = "dang_chay"
    viec["huy"] = False
    viec["loi_chay"] = ""
    viec["dang_lam"] = None
    if tiep:
        viec.setdefault("ban", {})
        viec.setdefault("hang", {})
        viec.setdefault("dat", {})
        viec.setdefault("khoa", {})
        viec.setdefault("mo", [])
        for p in phongs:
            viec["ban"].setdefault(p["slug"], "")
            viec["dat"].setdefault(p["slug"], False)
            viec["khoa"].setdefault(p["slug"], False)
    else:
        viec["loi"] = []
        viec["ban"] = {p["slug"]: "" for p in phongs}
        viec["hang"] = {}
        viec["dat"] = {p["slug"]: False for p in phongs}
        viec["khoa"] = {p["slug"]: False for p in phongs}
        viec["mo"] = []
        viec["ket_qua"] = ""
        viec["ket_cu"] = ""
        viec["lenh_them"] = ""
        viec["so"] = []
        viec["da_duyet"] = []
        viec["cong"] = ""
        viec["xin_y"] = ""
        viec["y_kien"] = ""
    kho.luu_viec(viec, tha_huy=True)
    vmax = min(VONG_TRAN, max(1, int(viec.get("vong_toi_da") or VONG_MAC_DINH)))
    try:
        for phong in phongs:
            if tiep and viec["khoa"].get(phong["slug"]):
                if not (viec.get("hang") or {}).get(phong["slug"]):
                    await _nop_hang(kho, viec, phong, ra_file)
                continue
            if _cho_cong(viec, "ke_hoach") and _giao_chua_lam(viec, phong["slug"]):
                raise LoiCong("ke_hoach")
            if (
                _cho_cong(viec, "ban_thao")
                and loai_hang(phong) in ("thiet_ke", "video")
                and any((viec.get("ban") or {}).get(s) for s in (viec.get("phong") or []) if s != phong["slug"])
            ):
                raise LoiCong("ban_thao")
            if tiep:
                await _tiep_phong(kho, viec, phong, noi, vmax)
            else:
                await _noi_bo(kho, viec, phong, noi, vmax)
            await _nop_hang(kho, viec, phong, ra_file)
        if len(phongs) == 1:
            viec["dat"][phongs[0]["slug"]] = bool(viec["khoa"][phongs[0]["slug"]])
        else:
            await _hop(kho, viec, phongs, noi, vmax, ra_file, tiep=tiep)
        await _ket(kho, viec, phongs, noi)
        _gan_ket(viec)
    except LoiCong as e:
        viec["trang_thai"] = "cho_duyet"
        viec["cong"] = e.cong
        viec["xin_y"] = tin_cong(viec)
        viec["dang_lam"] = None
        kho.luu_viec(viec)
        if bao is not None:
            try:
                kq = bao(viec)
                if hasattr(kq, "__await__"):
                    await kq
            except Exception:
                pass
        return viec
    except LoiDung:
        return _cham(kho, viec, "dung")
    except asyncio.CancelledError:
        _cham(kho, viec, "dung")
        raise
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
    if not (viec.get("ket_qua") or "").strip():
        viec["ket_qua"] = ket_phan(viec)
    if all(viec["dat"].get(p["slug"]) for p in phongs):
        viec["trang_thai"] = "xong"
        viec["mo"] = []
        viec["xin_y"] = ""
    else:
        viec["trang_thai"] = "lech"
        viec["xin_y"] = ("Cần một câu chỉ đạo. " + "; ".join(viec.get("mo") or []))[:300]
    viec["dang_lam"] = None
    kho.luu_viec(viec)
    return viec


async def _chan(kho: Kho, viec: dict, phong: dict, noi, truoc: dict, sau: dict, ban: str, vong: int) -> str:
    """Bước sau cãi với bước trước. Nhận rồi mới được làm. Hết lần thì trưởng phán."""
    truong = _truong(phong)
    vmax = min(VONG_TRAN, max(1, int(viec.get("vong_toi_da") or VONG_MAC_DINH)))
    sua_cu = ""
    ban_dung = False
    for i in range(vmax):
        _bao(kho, viec, phong, sau, "nhan", truoc)
        text = await _goi_du(noi, sau, lap_prompt(
            "NHAN", sau, phong, viec, ban=ban, giao_cho=truoc, luot=i + 1))
        t = tach_tra_loi(text, giau=True)
        nguon = t["ngoai"] if t["tep"] else text
        nhan = doc_nhan(nguon) or doc_nhan(text) or "CHUA"
        _ghi(kho, viec, phong, sau, "nhan", vong, t["noi"], nhan, _nhan(truoc), _tep_row(t))
        if nhan == "OK":
            return ban
        sua = y_phan_hoi(nguon) or y_phan_hoi(text) or "Làm rõ chỗ chưa ổn."
        if sua_cu and ban_dung and _trung_lenh(sua, sua_cu):
            break
        sua_cu = sua
        ban_note = t["ban"] if t["tep"] else ban
        ban_truoc = ban
        _bao(kho, viec, phong, truoc, "doi", sau)
        raw = await _goi_du(noi, truoc, lap_prompt(
            "DOI", truoc, phong, viec, ban=ban_note, lenh=sua, giao_cho=sau))
        td = tach_tra_loi(raw, giau=True)
        _ghi(kho, viec, phong, truoc, "doi", vong, td["noi"], giao_cho=_nhan(sau), tep=_tep_row(td))
        ban = _giu_ban(ban, td["ban"])
        ban_dung = _trung_lenh(ban, ban_truoc)
    _bao(kho, viec, phong, truong, "xu", sau)
    xu = await _goi_du(noi, truong, lap_prompt("XU", truong, phong, viec, ban=ban, giao_cho=sau))
    q = doc_quyet(xu)
    _ghi(kho, viec, phong, truong, "xu", vong, xu, q["quyet"] or "LAM")
    if q["quyet"] == "SUA":
        _bao(kho, viec, phong, truoc, "doi", sau)
        raw = await _goi_du(noi, truoc, lap_prompt(
            "DOI", truoc, phong, viec, ban=ban, lenh=y_phan_hoi(xu) or q["sua"] or "Sửa đúng chỗ trưởng chỉ.", giao_cho=sau))
        td = tach_tra_loi(raw, giau=True)
        _ghi(kho, viec, phong, truoc, "doi", vong, td["noi"], giao_cho=_nhan(sau), tep=_tep_row(td))
        ban = _giu_ban(ban, td["ban"])
    return ban


async def _chuoi(kho: Kho, viec: dict, phong: dict, noi, mems: list, lenh: str, vong: int,
                bat_dau: int = 0, ban_san: str = "", manh_cu: list | None = None) -> str:
    """Đi đúng thứ tự trưởng đã xếp. Bước sau chưa nhận thì chưa làm.

    bat_dau: người này trở đi mới làm. Phía trước đã có bản, truyền vào ban_san và manh_cu.
    """
    truong = _truong(phong)
    manh = list(manh_cu or [])
    ban_truoc = ban_san
    nguoi_truoc = mems[bat_dau - 1] if bat_dau > 0 and mems else None
    for i, mem in enumerate(mems):
        if i < bat_dau:
            continue
        sau = mems[i + 1] if i + 1 < len(mems) else truong
        if nguoi_truoc:
            ban_moi = await _chan(kho, viec, phong, noi, nguoi_truoc, mem, ban_truoc, vong)
            if manh:
                manh[-1] = f"[{_nhan(nguoi_truoc)}]\n{ban_moi}"
            ban_truoc = ban_moi
        _bao(kho, viec, phong, mem, "lam", sau)
        raw = await _goi_du(noi, mem, lap_prompt(
            "LAM", mem, phong, viec, ban=ban_truoc, lenh=lenh, giao_cho=sau))
        t = tach_tra_loi(raw, giau=True)
        _ghi(kho, viec, phong, mem, "lam", vong, t["noi"], giao_cho=_nhan(sau), tep=_tep_row(t))
        manh.append(f"[{_nhan(mem)}]\n{t['ban']}")
        ban_truoc = t["ban"]
        nguoi_truoc = mem
    return "\n\n".join(manh)


async def _noi_bo(kho: Kho, viec: dict, phong: dict, noi, vmax: int,
                 tu: int = 1, lenh0: str = "", ban0: str = "") -> None:
    if phong.get("cach_lam") == "lan_luot" and _thanh_vien(phong):
        await _noi_bo_lan(kho, viec, phong, noi, vmax, tu=tu, lenh0=lenh0, ban0=ban0)
        return
    truong = _truong(phong)
    mems = _mems(viec, phong)
    lenh = lenh0
    ban_cu = ban0
    for vong in range(max(1, int(tu or 1)), vmax + 1):
        _bao(kho, viec, phong, truong, "giao", mems[0] if mems else None)
        giao = await _goi_du(noi, truong, lap_prompt("GIAO", truong, phong, viec, lenh=lenh))
        _ghi(kho, viec, phong, truong, "giao", vong, giao)
        if _cho_cong(viec, "ke_hoach"):
            raise LoiCong("ke_hoach")
        if not mems:
            viec["ban"][phong["slug"]] = giao
        else:
            manh = []
            for mem in mems:
                _bao(kho, viec, phong, mem, "lam")
                raw = await _goi_du(noi, mem, lap_prompt("LAM", mem, phong, viec, lenh=lenh))
                t = tach_tra_loi(raw, giau=True)
                _ghi(kho, viec, phong, mem, "lam", vong, t["noi"], tep=_tep_row(t))
                manh.append(t["ban"])
            hop = "\n\n".join(manh)
            if lenh:
                hop = _giu_ban(viec["ban"].get(phong["slug"]) or "", hop)
            viec["ban"][phong["slug"]] = hop
            if len(mems) > 1:
                for mem in mems:
                    khac = next((m for m in mems if m["slug"] != mem["slug"]), None)
                    _bao(kho, viec, phong, mem, "gop", khac)
                    gop = await _goi_du(noi, mem, lap_prompt(
                        "GOP", mem, phong, viec, ban=viec["ban"][phong["slug"]], giao_cho=khac))
                    _ghi(kho, viec, phong, mem, "gop", vong, gop, giao_cho=_nhan(khac) if khac else "")
        _bao(kho, viec, phong, truong, "kiem")
        kiem = await _hoi_kiem(noi, truong, phong, viec, viec["ban"][phong["slug"]])
        q = doc_quyet(kiem)
        quyet = q["quyet"] or "CHUA"
        _ghi(kho, viec, phong, truong, "kiem", vong, kiem, quyet)
        if quyet == "DAT":
            _chot(viec, phong)
            return
        moi = y_phan_hoi(kiem) or q["sua"] or "Sửa cho đúng tiêu chí phòng."
        viec["mo"].append(f"{phong['ten']}: {moi}")
        ban_nay = viec["ban"].get(phong["slug"]) or ""
        if lenh and _trung_lenh(moi, lenh) and _trung_lenh(ban_nay, ban_cu):
            viec["khoa"][phong["slug"]] = False
            return
        ban_cu = ban_nay
        lenh = moi
    viec["khoa"][phong["slug"]] = False


async def _noi_bo_lan(kho: Kho, viec: dict, phong: dict, noi, vmax: int,
                     tu: int = 1, lenh0: str = "", ban0: str = "") -> None:
    truong = _truong(phong)
    mems = _mems(viec, phong)
    lenh = lenh0
    ban_cu = ban0
    for vong in range(max(1, int(tu or 1)), vmax + 1):
        _bao(kho, viec, phong, truong, "giao")
        giao = await _goi_du(noi, truong, lap_prompt(
            "GIAO", truong, phong, viec, lenh=lenh, thanh_vien=mems))
        day = doc_thu_tu(giao, mems)
        ep = bool(viec.get("xep_khoa") and (viec.get("xep") or {}).get(phong["slug"]))
        if ep:
            day = _theo_xep(viec, phong, mems)
        else:
            viec.setdefault("xep", {})[phong["slug"]] = [
                {"slug": m["slug"], "ten": m["ten"], "vi_tri": (m.get("vi_tri") or "").strip()} for m in day
            ]
        _ghi(kho, viec, phong, truong, "giao", vong, giao, giao_cho=_nhan(day[0]))
        if _cho_cong(viec, "ke_hoach"):
            raise LoiCong("ke_hoach")
        hop = await _chuoi(kho, viec, phong, noi, day, lenh, vong)
        if lenh:
            hop = _giu_ban(viec["ban"].get(phong["slug"]) or "", hop)
        viec["ban"][phong["slug"]] = hop
        _bao(kho, viec, phong, truong, "kiem")
        kiem = await _hoi_kiem(noi, truong, phong, viec, viec["ban"][phong["slug"]])
        q = doc_quyet(kiem)
        quyet = q["quyet"] or "CHUA"
        _ghi(kho, viec, phong, truong, "kiem", vong, kiem, quyet)
        if quyet == "DAT":
            _chot(viec, phong)
            return
        moi = y_phan_hoi(kiem) or q["sua"] or "Sửa cho đúng tiêu chí phòng."
        viec["mo"].append(f"{phong['ten']}: {moi}")
        ban_nay = viec["ban"].get(phong["slug"]) or ""
        if lenh and _trung_lenh(moi, lenh) and _trung_lenh(ban_nay, ban_cu):
            viec["khoa"][phong["slug"]] = False
            return
        ban_cu = ban_nay
        lenh = moi
    viec["khoa"][phong["slug"]] = False


async def _sua_phong(kho: Kho, viec: dict, phong: dict, noi, lenh: str, vong: int) -> None:
    truong = _truong(phong)
    mems = _mems(viec, phong)
    _bao(kho, viec, phong, truong, "sua", mems[0] if mems else None)
    ra_lenh = await _goi_du(noi, truong, lap_prompt("SUA", truong, phong, viec, lenh=lenh))
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
        raw = await _goi_du(noi, mem, lap_prompt("LAM", mem, phong, viec, lenh=lenh))
        t = tach_tra_loi(raw, giau=True)
        _ghi(kho, viec, phong, mem, "lam", vong, t["noi"], tep=_tep_row(t))
        manh.append(t["ban"])
    viec["ban"][phong["slug"]] = "\n\n".join(manh)
    kho.luu_viec(viec)


def _row_buoc(viec: dict, slug: str, lop: str, vong: int):
    for r in reversed(viec.get("loi") or []):
        if r.get("phong") == slug and r.get("lop") == lop and int(r.get("vong") or 0) == int(vong):
            return r
    return None


def _sau_sua(viec: dict, slug: str, vong: int):
    rows = viec.get("loi") or []
    idx = -1
    for i, r in enumerate(rows):
        if r.get("phong") == slug and r.get("lop") == "sua" and int(r.get("vong") or 0) == int(vong):
            idx = i
    if idx < 0:
        return None
    return rows[idx + 1:]


def _sua_xong(viec: dict, phong: dict, vong: int) -> bool:
    sau = _sau_sua(viec, phong["slug"], vong)
    if sau is None:
        return False
    mems = _mems(viec, phong)
    if not mems:
        return True
    da = {
        r.get("slug") for r in sau
        if r.get("phong") == phong["slug"] and r.get("lop") == "lam" and int(r.get("vong") or 0) == int(vong)
    }
    return all(m["slug"] in da for m in mems)


async def _tiep_sua(kho: Kho, viec: dict, phong: dict, noi, lenh: str, vong: int) -> None:
    """Lệnh sửa đã giao rồi thì chỉ người chưa viết mới làm."""
    if _row_buoc(viec, phong["slug"], "sua", vong) is None:
        await _sua_phong(kho, viec, phong, noi, lenh, vong)
        return
    if _sua_xong(viec, phong, vong):
        return
    mems = _mems(viec, phong)
    sau = _sau_sua(viec, phong["slug"], vong) or []
    da = {
        r.get("slug") for r in sau
        if r.get("phong") == phong["slug"] and r.get("lop") == "lam" and int(r.get("vong") or 0) == int(vong)
    }
    if phong.get("cach_lam") == "lan_luot":
        day = _theo_xep(viec, phong, mems)
        idx = 0
        while idx < len(day) and day[idx]["slug"] in da:
            idx += 1
        manh_cu = []
        ban_san = ""
        for mem in day[:idx]:
            cu = next(r for r in reversed(sau) if r.get("lop") == "lam" and r.get("slug") == mem["slug"])
            ban_san = _ban_row(cu)
            manh_cu.append(f"[{_nhan(mem)}]\n{ban_san}")
        if idx < len(day):
            hop = await _chuoi(
                kho, viec, phong, noi, day, lenh, vong,
                bat_dau=idx, ban_san=ban_san, manh_cu=manh_cu)
        else:
            hop = "\n\n".join(manh_cu)
    else:
        manh = []
        for mem in mems:
            if mem["slug"] in da:
                cu = next(r for r in reversed(sau) if r.get("lop") == "lam" and r.get("slug") == mem["slug"])
                manh.append(_ban_row(cu))
                continue
            _bao(kho, viec, phong, mem, "lam")
            raw = await _goi_du(noi, mem, lap_prompt("LAM", mem, phong, viec, lenh=lenh))
            t = tach_tra_loi(raw, giau=True)
            _ghi(kho, viec, phong, mem, "lam", vong, t["noi"], tep=_tep_row(t))
            manh.append(t["ban"])
        hop = "\n\n".join(manh)
    if lenh:
        hop = _giu_ban(viec["ban"].get(phong["slug"]) or "", hop)
    viec["ban"][phong["slug"]] = hop
    kho.luu_viec(viec)


async def _trao(kho: Kho, viec: dict, phongs: list, noi, vong: int, tiep: bool = False) -> None:
    """Trưởng phòng góp ý bản phòng kia, trưởng kia đáp. Rồi mới họp chốt."""
    if len(phongs) < 2:
        return
    for i, phong in enumerate(phongs):
        khac = phongs[(i + 1) % len(phongs)]
        truong = _truong(phong)
        kia = _truong(khac)
        ban_khac = (viec.get("ban") or {}).get(khac["slug"]) or ""
        cu_chia = _row_buoc(viec, phong["slug"], "chia", vong) if tiep else None
        if cu_chia:
            y = cu_chia.get("loi") or ""
        else:
            _bao(kho, viec, phong, truong, "chia", kia)
            y = await _goi_du(noi, truong, lap_prompt(
                "CHIA", truong, phong, viec, ban=ban_khac, giao_cho=kia))
            _ghi(kho, viec, phong, truong, "chia", vong, y, giao_cho=_nhan(kia))
        if tiep and _row_buoc(viec, khac["slug"], "dap", vong):
            continue
        _bao(kho, viec, khac, kia, "dap", truong)
        d = await _goi_du(noi, kia, lap_prompt(
            "DAP", kia, khac, viec, ban=(viec.get("ban") or {}).get(khac["slug"]) or "",
            lenh=y, giao_cho=truong))
        _ghi(kho, viec, khac, kia, "dap", vong, d, giao_cho=_nhan(truong))


async def _hop(kho: Kho, viec: dict, phongs: list, noi, vmax: int, ra_file=None, tiep: bool = False) -> None:
    by = {p["slug"]: p for p in phongs}
    slugs = [p["slug"] for p in phongs]
    lenh_cu = {}
    ban_cu = ""
    for vong in range(1, vmax + 1):
        await _trao(kho, viec, phongs, noi, vong, tiep=tiep)
        orders = []
        for phong in phongs:
            truong = _truong(phong)
            cu_hop = _row_buoc(viec, phong["slug"], "hop", vong) if tiep else None
            if cu_hop:
                text = cu_hop.get("loi") or ""
                quyet = cu_hop.get("quyet") or doc_quyet(text)["quyet"] or "CHUA"
            else:
                _bao(kho, viec, phong, truong, "hop")
                text = await _goi_du(noi, truong, lap_prompt(
                    "HOP", truong, phong, viec, cac_ban=viec["ban"]))
                q = doc_quyet(text)
                quyet = q["quyet"] or "CHUA"
                _ghi(kho, viec, phong, truong, "hop", vong, text, quyet)
            # Chỉ tiêu chí phòng mình. Không được gật hộ phòng khác.
            viec["dat"][phong["slug"]] = quyet == "DAT"
            if quyet != "DAT":
                q = doc_quyet(text)
                # Không ghi TRA thì lệnh về đúng phòng của người đang nói.
                tra = q["tra"] if q["tra"] in by else phong["slug"]
                orders.append((tra, y_phan_hoi(text) or q["sua"] or "Sửa cho đạt tiêu chí."))
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
        ban_nay = "\n".join(f"{k}:{viec['ban'].get(k) or ''}" for k in slugs)
        if lenh_cu and ban_cu and ban_nay == ban_cu and all(
                _trung_lenh(sua, lenh_cu.get(tra, "")) for tra, sua in seen.items()):
            return
        ban_cu = ban_nay
        for tra, sua in seen.items():
            lenh_cu[tra] = sua
            if tiep and _sua_xong(viec, by[tra], vong):
                continue
            if tiep:
                await _tiep_sua(kho, viec, by[tra], noi, sua, vong)
            else:
                await _sua_phong(kho, viec, by[tra], noi, sua, vong)
            await _nop_hang(kho, viec, by[tra], ra_file)


async def _ket(kho: Kho, viec: dict, phongs: list, noi) -> None:
    """Một bản kết quả đầy đủ sau khi các lượt trao đổi đã ngắn."""
    phong = phongs[0]
    truong = _truong(phong)
    nguon = {}
    for p in phongs:
        manh = []
        for row in viec.get("loi") or []:
            if row.get("phong") == p["slug"] and row.get("lop") == "lam":
                tep = ((row.get("tep") or {}).get("noi_dung") or "").strip()
                manh.append(tep or row.get("loi") or "")
        ban = (viec.get("ban") or {}).get(p["slug"]) or ""
        if ban and ban not in "\n".join(manh):
            manh.append(ban)
        nguon[p["slug"]] = "\n\n".join(x for x in manh if x)
    _bao(kho, viec, phong, truong, "ket")
    text = await _goi_du(noi, truong, lap_prompt("KET", truong, phong, viec, cac_ban=nguon))
    viec["ket_qua"] = text
    kho.luu_viec(viec)


def _cham(kho: Kho, viec: dict, trang: str) -> dict:
    """Chốt trạng thái khi dừng hoặc lỗi giữa chừng, vẫn để lại bản nhìn được."""
    viec["trang_thai"] = trang
    viec["huy"] = False
    viec["dang_lam"] = None
    if trang == "dung" and not (viec.get("ket_qua") or "").strip():
        viec["ket_qua"] = ket_phan(viec)
    kho.luu_viec(viec, tha_huy=True)
    return viec


async def chay_them(kho: Kho, vid: str, noi, comment: str, thu_tu: list | None = None,
                    phong_lai: str = "", ra_file=None) -> dict:
    """Lấy kết quả cũ, sửa theo comment, viết lại kết quả. Không xoá biên bản."""
    comment = (comment or "").strip()
    if not comment:
        raise LoiNhacTruong("Cần một câu muốn sửa thêm.")
    viec = kho.doc_viec(vid)
    if viec.get("trang_thai") == "dang_chay":
        raise LoiNhacTruong("Việc đang chạy. Dừng trước khi chạy thêm.")
    lai = str(phong_lai or "").strip()
    if lai and lai not in (viec.get("phong") or []):
        raise LoiNhacTruong("Phòng này không nằm trong việc.")
    if thu_tu:
        viec = dat_thu_tu_phong(kho, vid, thu_tu)
    viec["ket_cu"] = (viec.get("ket_qua") or "").strip()
    viec["lenh_them"] = comment[:LOI_TRAN]
    viec["trang_thai"] = "dang_chay"
    viec["huy"] = False
    viec["loi_chay"] = ""
    kho.luu_viec(viec, tha_huy=True)
    try:
        phongs = [kho.doc_phong(s) for s in viec["phong"]]
        for p in phongs:
            _truong(p)
    except LoiNhacTruong as e:
        viec["trang_thai"] = "loi"
        viec["loi_chay"] = str(e)
        kho.luu_viec(viec)
        return viec
    try:
        if lai:
            if lai not in (viec.get("phong") or []):
                raise LoiNhacTruong("Phòng này không nằm trong việc.")
            i = viec["phong"].index(lai)
            truoc = viec["phong"][:i]
            giu_ban = {s: (viec.get("ban") or {}).get(s, "") for s in truoc}
            giu_hang = {
                s: [dict(it) for it in ((viec.get("hang") or {}).get(s) or [])]
                for s in truoc
            }
            await _noi_bo(kho, viec, phongs[i], noi, min(VONG_TRAN, max(1, int(viec.get("vong_toi_da") or VONG_MAC_DINH))))
            for s, ban_cu in giu_ban.items():
                viec.setdefault("ban", {})[s] = ban_cu
            for s, hang_cu in giu_hang.items():
                if hang_cu:
                    viec.setdefault("hang", {})[s] = hang_cu
            await _nop_hang(kho, viec, phongs[i], ra_file)
            for sau in phongs[i + 1:]:
                truong = _truong(sau)
                ban_cu = (viec.get("ban") or {}).get(sau["slug"]) or ""
                _bao(kho, viec, sau, truong, "sua")
                raw = await _goi_du(noi, truong, lap_prompt(
                    "CAP", truong, sau, viec, ban=ban_cu, lenh=comment))
                t = tach_tra_loi(raw, giau=True)
                viec["ban"][sau["slug"]] = _giu_ban(ban_cu, t["ban"])
                _ghi(kho, viec, sau, truong, "sua", 1, t["noi"], tep=_tep_row(t))
                await _nop_hang(kho, viec, sau, ra_file)
        else:
            for phong in phongs:
                truong = _truong(phong)
                ban = (viec.get("ban") or {}).get(phong["slug"]) or viec.get("ket_cu") or ""
                _bao(kho, viec, phong, truong, "sua")
                raw = await _goi_du(noi, truong, lap_prompt(
                    "THEM", truong, phong, viec, ban=ban, lenh=comment))
                t = tach_tra_loi(raw, giau=True)
                viec["ban"][phong["slug"]] = _giu_ban(ban, t["ban"])
                _ghi(kho, viec, phong, truong, "sua", 1, t["noi"], tep=_tep_row(t))
                await _nop_hang(kho, viec, phong, ra_file)
        await _ket(kho, viec, phongs, noi)
        _gan_ket(viec)
    except LoiDung:
        return _cham(kho, viec, "dung")
    except asyncio.CancelledError:
        _cham(kho, viec, "dung")
        raise
    except LoiNhacTruong:
        raise
    except LoiNoi as e:
        viec["trang_thai"] = "loi"
        viec["loi_chay"] = str(e)
        viec["dang_lam"] = None
        kho.luu_viec(viec)
        return viec
    except Exception as e:
        viec["trang_thai"] = "loi"
        viec["loi_chay"] = str(e) or "Chạy thêm dừng giữa chừng."
        viec["dang_lam"] = None
        kho.luu_viec(viec)
        return viec
    if not (viec.get("ket_qua") or "").strip():
        viec["ket_qua"] = ket_phan(viec)
    _gan_ket(viec)
    viec["trang_thai"] = "xong"
    viec["dang_lam"] = None
    viec["lenh_them"] = ""
    kho.luu_viec(viec, tha_huy=True)
    return viec


def html_lien(text: str) -> str:
    """Chữ an toàn để in, URL thành link bấm được."""
    esc = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def mot(m):
        raw = m.group(0)
        u = raw.rstrip(".,;:)")
        if not u:
            return raw
        return f'<a href="{u}">{u}</a>{raw[len(u):]}'

    return re.sub(r"https?://[^\s<&]+", mot, esc)


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
        tep = row.get("tep") or {}
        if str(tep.get("noi_dung") or "").strip():
            d.append("")
            d.append(f"File đính kèm: {tep.get('ten') or 'tai-lieu.md'}")
            d.append("")
            d.append(tep.get("noi_dung") or "")
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
