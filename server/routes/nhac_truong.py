"""API trang Nhạc trưởng.

Không import main. Não thật đi qua deps.noi. Chạy thử dùng người giả trong nhac_truong.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

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
    return {"ok": True, "viec": viec}


@router.delete("/nhac-truong/viec/{vid}")
async def xoa_viec(vid: str, brain: str = "brain"):
    khoa = f"{brain}:{vid}"
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
    khoa = f"{brain}:{vid}"
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
            viec = await nt.chay(kho, vid, nt.noi_thu)
        except nt.LoiNhacTruong as e:
            return _err(e)
        return {"ok": True, "viec": viec}

    async def _nen():
        try:
            await nt.chay(kho, vid, lambda nguoi, prompt: (_DEPS.noi or _noi_that)(brain, nguoi, prompt))
        except Exception as e:
            _danh_loi(kho, vid, e)

    _DANG[khoa] = asyncio.create_task(_nen())
    return {"ok": True, "trang_thai": "dang_chay"}


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
        "Bạn đang nói trong Nhạc trưởng. Chỉ viết phần của lượt này.\n"
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
