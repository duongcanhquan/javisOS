"""API trang Nhạc trưởng.

Không import main. Não thật đi qua deps.noi. Chạy thử dùng người giả trong nhac_truong.
"""
from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import nhac_truong as nt

router = APIRouter()


@dataclass
class Deps:
    brain_root: Callable[[str], str]
    doc_agent: Optional[Callable[[str, str], tuple]] = None
    noi: Optional[Callable] = None


_DEPS: Optional[Deps] = None
_DANG: dict = {}


def register(app, deps: Deps) -> None:
    global _DEPS
    _DEPS = deps
    app.include_router(router)


def _kho(brain: str) -> nt.Kho:
    return nt.Kho(_DEPS.brain_root(brain or "brain"))


def _khoa_viec(brain: str, vid: str) -> str:
    """Một ổ khoá cho cả trang và chat, kể cả khi một bên gửi tên brain, bên kia gửi đường dẫn."""
    try:
        goc = Path(_kho(brain).goc).resolve()
    except Exception:
        goc = brain or "brain"
    return f"{goc}:{vid}"


def bat_chay(brain: str, vid: str) -> str:
    """Chạy thật ở nền, cùng đường với nút Chạy trên trang. Trả 'dang_chay' nếu đã chạy."""
    if _DEPS is None:
        raise nt.LoiNhacTruong("Nhạc trưởng chưa sẵn sàng.")
    khoa = _khoa_viec(brain, vid)
    dang = _DANG.get(khoa)
    if dang is not None and not dang.done():
        return "dang_chay"
    kho = _kho(brain)
    kho.doc_viec(vid)

    async def _nen():
        try:
            await nt.chay(
                kho, vid,
                lambda nguoi, prompt: (_DEPS.noi or _noi_that)(brain, nguoi, prompt),
                ra_file=_ra_file_cho(brain),
            )
        except Exception as e:
            _danh_loi(kho, vid, e)

    _DANG[khoa] = asyncio.create_task(_nen())
    return "bat"


def _ra_file_cho(brain: str):
    """Ảnh hoặc video thật, cất trong việc. Lỗi trả về cho trang, không nuốt im."""

    async def ra(viec_id, phong_slug, loai, ten, mo_ta, ti_le, script):
        import script_video
        goc = Path(_kho(brain).goc)
        thu = goc / "nhac-truong" / "viec" / viec_id / "hang" / phong_slug
        thu.mkdir(parents=True, exist_ok=True)
        ten_tep = nt.slugify(ten) or "mon"
        if loai == "video":
            res = await script_video.render_script_video(
                script=script or mo_ta or ten,
                title=ten or "Video",
                vault_root=str(goc),
                aspect="landscape",
                with_images=True,
                image_quality="low",
                require_images=False,
                filename=f"nt-{viec_id}-{phong_slug}"[:40],
            )
            if not res.get("ok") or not res.get("path"):
                return {"ok": False, "error": res.get("error") or "Không ra video."}
            dest = thu / f"{ten_tep}.mp4"
            shutil.copy2(res["path"], dest)
            return {"ok": True, "file": dest.relative_to(goc).as_posix(), "ten": ten}
        path, _nguon = await script_video._gen_anh_canh(
            mo_ta or ten, str(goc), ti_le or "landscape", "low", "", thu, 1,
        )
        if not path:
            return {"ok": False, "error": "Không tạo được ảnh."}
        src = Path(path)
        dest = thu / f"{ten_tep}{src.suffix.lower() or '.jpg'}"
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        return {"ok": True, "file": dest.relative_to(goc).as_posix(), "ten": ten}

    return ra


def _html_hang(viec: dict, brain: str) -> str:
    hang = viec.get("hang") or {}
    khoi = []
    for slug in viec.get("phong") or list(hang):
        for it in hang.get(slug) or []:
            ten = _html(it.get("ten") or "Món")
            if it.get("file"):
                src = (
                    "/nhac-truong/viec/" + quote(viec.get("id") or "")
                    + "/tep?brain=" + quote(brain) + "&p=" + quote(it["file"])
                )
                if it.get("loai") == "video":
                    khoi.append(f'<figure><video controls src="{src}"></video><figcaption>{ten}</figcaption></figure>')
                else:
                    khoi.append(f'<figure><img alt="{ten}" src="{src}"><figcaption>{ten}</figcaption></figure>')
            elif it.get("loi"):
                khoi.append(f"<p>{ten}: {_html(it.get('loi') or '')}</p>")
    if not khoi:
        return ""
    return '<h2>Hàng đã nộp</h2>' + "".join(khoi)


def _err(e: Exception, code: int = 400):
    return JSONResponse({"ok": False, "error": str(e)}, status_code=code)


@router.get("/nhac-truong/phong")
async def ds_phong(brain: str = "brain"):
    return {"ok": True, "phong": _kho(brain).ds_phong()}


@router.post("/nhac-truong/phong")
async def tao_phong(request: Request):
    body = await request.json()
    try:
        phong = nt.tao_phong(_kho(body.get("brain") or "brain"), body.get("ten") or "",
                             body.get("tieu_chi") or "", body.get("cach_lam") or "")
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "phong": phong}


@router.delete("/nhac-truong/phong/{slug}")
async def xoa_phong(slug: str, brain: str = "brain"):
    try:
        _kho(brain).xoa_phong(slug)
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True}


@router.post("/nhac-truong/phong/{slug}")
async def sua_phong(slug: str, request: Request):
    body = await request.json()
    try:
        kho = _kho(body.get("brain") or "brain")
        phong = nt.sua_phong(
            kho, slug,
            tieu_chi=body.get("tieu_chi") if "tieu_chi" in body else None,
            cach_lam=body.get("cach_lam") if "cach_lam" in body else None,
            ten=body.get("ten") if "ten" in body else None,
        )
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "phong": phong}


@router.post("/nhac-truong/phong/{slug}/nguoi")
async def them_nguoi(slug: str, request: Request):
    body = await request.json()
    try:
        kho = _kho(body.get("brain") or "brain")
        nguoi = nt.them_nguoi(
            kho, slug,
            body.get("ten") or "", body.get("tinh_cach") or "",
            body.get("skills") or "", body.get("vai") or "thanh_vien",
            body.get("agent") or "", body.get("vi_tri") or "",
        )
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "nguoi": nguoi, "phong": kho.doc_phong(slug)}


@router.delete("/nhac-truong/phong/{slug}/nguoi/{ns}")
async def xoa_nguoi(slug: str, ns: str, brain: str = "brain"):
    try:
        nt.xoa_nguoi(_kho(brain), slug, ns)
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True}


@router.post("/nhac-truong/phong/{slug}/nguoi/{ns}")
async def sua_nguoi(slug: str, ns: str, request: Request):
    body = await request.json()
    try:
        kho = _kho(body.get("brain") or "brain")
        nguoi = nt.sua_nguoi(
            kho, slug, ns,
            tinh_cach=body.get("tinh_cach") if "tinh_cach" in body else None,
            skills=body.get("skills") if "skills" in body else None,
            vai=body.get("vai") if "vai" in body else None,
            vi_tri=body.get("vi_tri") if "vi_tri" in body else None,
            ten=body.get("ten") if "ten" in body else None,
        )
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "nguoi": nguoi, "phong": kho.doc_phong(slug)}


@router.post("/nhac-truong/phong/{slug}/nguoi/{ns}/thu-tu")
async def doi_cho(slug: str, ns: str, request: Request):
    body = await request.json()
    try:
        kho = _kho(body.get("brain") or "brain")
        phong = nt.doi_cho(kho, slug, ns, body.get("huong") or "")
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "phong": phong}


@router.get("/nhac-truong/viec")
async def ds_viec(brain: str = "brain"):
    return {"ok": True, "viec": _kho(brain).ds_viec()}


@router.post("/nhac-truong/viec")
async def tao_viec(request: Request):
    body = await request.json()
    try:
        viec = nt.tao_viec(
            _kho(body.get("brain") or "brain"),
            body.get("tieu_de") or "", body.get("brief") or "",
            body.get("phong") or [], body.get("vong") or nt.VONG_MAC_DINH,
            tai_lieu=body.get("tai_lieu"), xep=body.get("xep") if isinstance(body.get("xep"), dict) else None,
        )
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "viec": viec}


@router.post("/nhac-truong/viec/{vid}/sua")
async def sua_viec(vid: str, request: Request):
    body = await request.json()
    try:
        viec = nt.sua_viec(
            _kho(body.get("brain") or "brain"), vid,
            body.get("tieu_de") or "", body.get("brief") or "",
            body.get("phong") or [], body.get("vong") or nt.VONG_MAC_DINH,
            tai_lieu=body.get("tai_lieu") if "tai_lieu" in body else None,
            xep=body.get("xep") if isinstance(body.get("xep"), dict) else None,
            bo_xep=bool(body.get("bo_xep")),
        )
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "viec": viec}


@router.get("/nhac-truong/viec/{vid}")
async def doc_viec(vid: str, brain: str = "brain"):
    try:
        viec = _kho(brain).doc_viec(vid)
    except nt.LoiNhacTruong as e:
        return _err(e, 404)
    out = dict(viec)
    dang = _DANG.get(_khoa_viec(brain, vid))
    out["song"] = bool(dang is not None and not dang.done())
    return {"ok": True, "viec": out}


def _html(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@router.get("/nhac-truong/viec/{vid}/ket-qua", response_class=HTMLResponse)
async def trang_ket_qua(vid: str, brain: str = "brain"):
    """Trang in. Trình duyệt lưu thành PDF."""
    try:
        viec = _kho(brain).doc_viec(vid)
    except nt.LoiNhacTruong as e:
        return HTMLResponse(f"<p>{_html(str(e))}</p>", status_code=404)
    tieu = viec.get("tieu_de") or "Kết quả"
    than = nt.bien_ban(viec)
    vid_h = _html(vid)
    page = (
        "<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\">"
        f"<title>{_html(tieu)}</title><style>"
        "body{font:15px/1.5 system-ui,sans-serif;margin:32px auto;max-width:720px;color:#111}"
        "h1{font-size:22px}pre{white-space:pre-wrap;font:inherit}"
        "a{color:#0b57d0}.nut{margin-top:16px}img,video{max-width:100%;height:auto;border-radius:8px}"
        "figure{margin:12px 0}figcaption{font-size:13px;color:#444}@media print{.nut{display:none}}"
        "</style></head><body>"
        f"<h1>{_html(tieu)}</h1>"
        f"<p>Biên bản trong brain: nhac-truong/viec/{vid_h}.md</p>"
        f"{_html_hang(viec, brain)}"
        f"<pre>{nt.html_lien(than)}</pre>"
        "<p class=\"nut\"><button onclick=\"print()\">Lưu PDF</button></p>"
        "<script>addEventListener('load',function(){setTimeout(function(){print()},300)})</script>"
        "</body></html>"
    )
    return HTMLResponse(page)


@router.get("/nhac-truong/viec/{vid}/tep")
async def tep_hang(vid: str, p: str = "", brain: str = "brain"):
    goc = Path(_kho(brain).goc).resolve()
    thu = (goc / "nhac-truong" / "viec" / vid / "hang").resolve()
    duong = (goc / (p or "")).resolve()
    if thu not in duong.parents or not duong.is_file():
        return JSONResponse({"ok": False, "error": "Không có file."}, status_code=404)
    return FileResponse(duong)


@router.delete("/nhac-truong/viec/{vid}")
async def xoa_viec(vid: str, brain: str = "brain"):
    khoa = _khoa_viec(brain, vid)
    dang = _DANG.get(khoa)
    if dang is not None and not dang.done():
        return JSONResponse({"ok": False, "error": "Việc đang chạy."}, status_code=409)
    try:
        nt.xoa_viec(_kho(brain), vid, force=True)
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True}


@router.post("/nhac-truong/viec/{vid}/chay")
async def chay_viec(vid: str, request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}
    brain = body.get("brain") or "brain"
    thu = bool(body.get("thu"))
    khoa = _khoa_viec(brain, vid)
    dang = _DANG.get(khoa)
    if dang is not None and not dang.done():
        return JSONResponse({"ok": False, "error": "Việc đang chạy."}, status_code=409)
    kho = _kho(brain)
    try:
        kho.doc_viec(vid)
    except nt.LoiNhacTruong as e:
        return _err(e, 404)

    if thu:
        try:
            viec = await nt.chay(kho, vid, nt.noi_thu, ra_file=_ra_file_cho(brain))
        except nt.LoiNhacTruong as e:
            return _err(e)
        return {"ok": True, "viec": viec}

    bat_chay(brain, vid)
    return {"ok": True, "trang_thai": "dang_chay"}


@router.post("/nhac-truong/viec/{vid}/dung")
async def dung_viec(vid: str, request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}
    brain = (body or {}).get("brain") or "brain"
    kho = _kho(brain)
    try:
        viec = kho.doc_viec(vid)
    except nt.LoiNhacTruong as e:
        return _err(e, 404)
    viec["huy"] = True
    kho.luu_viec(viec)
    khoa = _khoa_viec(brain, vid)
    task = _DANG.get(khoa)
    if task is not None and not task.done():
        task.cancel()
        return {"ok": True, "trang_thai": "dang_dung"}
    viec["trang_thai"] = "dung"
    viec["huy"] = False
    viec["dang_lam"] = None
    if not (viec.get("ket_qua") or "").strip():
        viec["ket_qua"] = nt.ket_phan(viec)
    kho.luu_viec(viec)
    return {"ok": True, "viec": viec}


@router.post("/nhac-truong/viec/{vid}/chay-them")
async def chay_them(vid: str, request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}
    brain = body.get("brain") or "brain"
    khoa = _khoa_viec(brain, vid)
    dang = _DANG.get(khoa)
    if dang is not None and not dang.done():
        return JSONResponse({"ok": False, "error": "Việc đang chạy."}, status_code=409)
    kho = _kho(brain)
    thu = bool(body.get("thu"))
    comment = body.get("comment") or ""
    thu_tu = body.get("thu_tu") if isinstance(body.get("thu_tu"), list) else None
    if thu:
        try:
            viec = await nt.chay_them(
                kho, vid, nt.noi_thu, comment, thu_tu,
                body.get("phong_lai") or "", _ra_file_cho(brain),
            )
        except nt.LoiNhacTruong as e:
            return _err(e)
        return {"ok": True, "viec": viec}

    async def _nen():
        try:
            await nt.chay_them(
                kho, vid, lambda nguoi, prompt: (_DEPS.noi or _noi_that)(brain, nguoi, prompt),
                comment, thu_tu, body.get("phong_lai") or "", _ra_file_cho(brain),
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            _danh_loi(kho, vid, e)

    _DANG[khoa] = asyncio.create_task(_nen())
    return {"ok": True, "trang_thai": "dang_chay"}


@router.post("/nhac-truong/viec/{vid}/thu-tu")
async def thu_tu_viec(vid: str, request: Request):
    body = await request.json()
    try:
        viec = nt.dat_thu_tu_phong(_kho(body.get("brain") or "brain"), vid, body.get("phong") or [])
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "viec": viec}


@router.post("/nhac-truong/phong/{slug}/icon")
async def icon_phong(slug: str, request: Request):
    body = await request.json()
    try:
        phong = nt.luu_icon(_kho(body.get("brain") or "brain"), slug, body.get("data") or "")
    except nt.LoiNhacTruong as e:
        return _err(e)
    return {"ok": True, "phong": phong}


def _danh_loi(kho, vid: str, e: Exception) -> None:
    """Việc kẹt dang_chay nếu task nền chết giữa chừng. Ghi lỗi để trang thôi xoay."""
    try:
        viec = kho.doc_viec(vid)
    except Exception:
        return
    if viec.get("trang_thai") != "dang_chay":
        return
    viec["trang_thai"] = "loi"
    viec["loi_chay"] = str(e) or "Việc dừng giữa chừng."
    kho.luu_viec(viec)


async def _noi_that(brain: str, nguoi: dict, prompt: str) -> str:
    """Một lượt, mức chỉ đọc. Không tool gửi tin hay chi tiền."""
    from claude_cli import claude_engine
    import aux_engine

    root = _DEPS.brain_root(brain or "brain")
    sysprompt = (
        f"Bạn là {nguoi.get('ten')}.\n"
        f"Tính cách: {nguoi.get('tinh_cach') or ''}\n"
        f"Skill: {', '.join(nguoi.get('skills') or []) or '(không)'}.\n"
        "Bạn đang nói trong Nhạc trưởng.\n"
        "Câu NOI chỉ nêu ý chính, ngắn, gạch đầu dòng nếu là phản hồi.\n"
        "Nội dung dài, kể cả dự án nhiều chữ, luôn viết đủ trong FILE. Viết gọn, chia mục, không lặp. Lượt ở giữa cũng vậy, không được viết cụt.\n"
        "Nếu hết lượt mà file chưa xong, dừng bằng đúng một dòng CON_TIEP. Không viết câu báo bị cắt.\n"
        "Không gửi tin, không đăng, không chi tiền, không bảo người khác tự đi làm.\n"
    )
    agent = (nguoi.get("agent") or "").strip()
    if agent and _DEPS.doc_agent:
        meta, body = _DEPS.doc_agent(brain, agent)
        if body or meta:
            sysprompt += f"\nVai trợ lý gốc {meta.get('name') or agent}: {meta.get('role') or ''}\n{body}\n"
    c = claude_engine(system_prompt=sysprompt, cwd=root, tag="nhac-truong", allowed_tools=["Read"])
    c.javis_mode = "suggest"
    c.javis_vault = root
    try:
        c = aux_engine.swap(c, mode="suggest", tag="nhac-truong", spec=aux_engine.research_spec())
    except Exception as e:
        raise nt.LoiNoi(f"Chưa gọi được model: {type(e).__name__}") from e
    out, err = "", ""
    async for ev in c.query(prompt):
        kind = ev.get("type")
        if kind == "final":
            out = ev.get("content") or out
        elif kind == "text" and not out:
            out = ev.get("content") or ""
        elif kind == "error":
            err = ev.get("content") or err
    if not (out or "").strip():
        raise nt.LoiNoi(err or "Model không trả lời.")
    return out
