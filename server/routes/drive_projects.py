"""REST /drive-projects — Kho tri thức Google Drive."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import drive_projects as dp

router = APIRouter(prefix="/drive-projects", tags=["drive-projects"])


@dataclass
class DriveProjectsDeps:
    brain_root: Callable[[str], str]
    get_sessions_store: Callable
    sync_script: Path


_DEPS: DriveProjectsDeps | None = None


def register(app, deps: DriveProjectsDeps):
    global _DEPS
    _DEPS = deps
    dp.configure(
        brain_root=deps.brain_root,
        get_sessions_store=deps.get_sessions_store,
        sync_script=deps.sync_script,
    )
    app.include_router(router)


def _brain_from(request: Request, body: dict | None = None) -> str:
    body = body or {}
    q = request.query_params.get("brain") or ""
    return (body.get("brain") or q or "brain").strip() or "brain"


@router.get("")
async def drive_projects_list(request: Request):
    brain = request.query_params.get("brain") or None
    return dp.status_payload(brain)


@router.get("/status")
async def drive_projects_status(request: Request):
    brain = request.query_params.get("brain") or None
    return dp.status_payload(brain)


@router.post("/rclone/authorize/start")
async def drive_rclone_authorize_start(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    remote = str(body.get("remote_name") or body.get("remote") or "gdrive")
    res = dp.authorize_start(remote_name=remote)
    code = 200 if res.get("ok") else 400
    return JSONResponse(res, status_code=code)


@router.get("/rclone/authorize/poll")
async def drive_rclone_authorize_poll(request: Request):
    sid = request.query_params.get("session") or request.query_params.get("session_id") or ""
    res = dp.authorize_poll(sid)
    code = 200 if res.get("ok") else 400
    return JSONResponse(res, status_code=code)


@router.post("/rclone/connect")
async def drive_rclone_connect(request: Request):
    """Kết nối bằng token JSON (paste) hoặc body {token}."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    token = str(body.get("token") or body.get("token_json") or "")
    remote = str(body.get("remote_name") or "gdrive")
    try:
        st = dp.save_gdrive_token(token, remote_name=remote)
        return {"ok": True, "rclone": st, "google_connected": bool(st.get("google_connected"))}
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/rclone/upload-config")
async def drive_rclone_upload_config(request: Request):
    """Nhận nội dung rclone.conf (JSON {content} hoặc text/plain)."""
    ctype = (request.headers.get("content-type") or "").lower()
    text = ""
    if "application/json" in ctype:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if isinstance(body, dict):
            text = str(body.get("content") or body.get("text") or body.get("conf") or "")
    else:
        raw = await request.body()
        try:
            text = raw.decode("utf-8")
        except Exception:
            return JSONResponse({"ok": False, "error": "File không phải UTF-8"}, status_code=400)
    try:
        st = dp.save_rclone_conf_text(text)
        return {"ok": True, "rclone": st, "google_connected": bool(st.get("google_connected"))}
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/rclone/disconnect")
async def drive_rclone_disconnect(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    remote = str(body.get("remote_name") or "gdrive")
    st = dp.disconnect_gdrive(remote_name=remote)
    return {"ok": True, "rclone": st, "google_connected": bool(st.get("google_connected"))}


def _public_base(request: Request) -> str:
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "http").split(",")[0].strip()
    host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(",")[0].strip()
    if not host:
        host = request.url.netloc
    return f"{proto}://{host}".rstrip("/")


@router.post("/rclone/pair/start")
async def drive_rclone_pair_start(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    base = str(body.get("base_url") or "").strip() or _public_base(request)
    try:
        return dp.pair_start(base_url=base)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.get("/rclone/pair/{pair_id}/poll")
async def drive_rclone_pair_poll(pair_id: str):
    return dp.pair_poll(pair_id)


@router.get("/rclone/pair/{pair_id}/mac.command")
async def drive_rclone_pair_mac(pair_id: str, request: Request):
    secret = request.query_params.get("secret") or ""
    sess = dp._pair_get(pair_id, secret)
    if not sess:
        return JSONResponse({"ok": False, "error": "Mã hết hạn hoặc sai"}, status_code=404)
    script = dp.mac_pair_script(
        pair_id=pair_id, secret=secret, base_url=str(sess.get("base_url") or _public_base(request))
    )
    from fastapi.responses import Response

    return Response(
        content=script,
        media_type="application/x-sh; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="Ket-noi-Google-Drive-Javis.command"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/rclone/pair/{pair_id}/win.bat")
async def drive_rclone_pair_win(pair_id: str, request: Request):
    secret = request.query_params.get("secret") or ""
    sess = dp._pair_get(pair_id, secret)
    if not sess:
        return JSONResponse({"ok": False, "error": "Mã hết hạn hoặc sai"}, status_code=404)
    script = dp.win_pair_script(
        pair_id=pair_id, secret=secret, base_url=str(sess.get("base_url") or _public_base(request))
    )
    from fastapi.responses import Response

    return Response(
        content=script.encode("utf-8"),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="Ket-noi-Google-Drive-Javis.bat"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/rclone/pair/{pair_id}/complete")
async def drive_rclone_pair_complete(pair_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    secret = str(body.get("secret") or "")
    token = str(body.get("token") or body.get("token_json") or "")
    try:
        return dp.pair_complete(pair_id, secret, token)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("")
async def drive_projects_create(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    try:
        item = dp.create_project(
            name=str(body.get("name") or ""),
            brain=_brain_from(request, body),
            drive_folder_id=str(body.get("drive_folder_id") or body.get("folder_id") or ""),
            rclone_remote=str(body.get("rclone_remote") or "gdrive:"),
            schedule=str(body.get("schedule") or ""),
            slug=str(body.get("slug") or ""),
        )
        out: dict = {"ok": True, "project": item}
        if body.get("sync_now") or body.get("sync"):
            sync_res = dp.sync_project(item["id"])
            out["sync"] = sync_res
            if not sync_res.get("ok"):
                out["ok"] = False
                out["error"] = sync_res.get("error") or "Tạo kho xong nhưng sync thất bại"
                return JSONResponse(out, status_code=502)
        return out
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.get("/{project_id}")
async def drive_projects_get(project_id: str):
    item = dp.get_project(project_id)
    if not item:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    return {
        "ok": True,
        "project": item,
        "corpus_dir": str(dp.corpus_dir(item)),
        "sources_rel": f"sources/drive/{item.get('slug')}/",
    }


@router.post("/{project_id}/update")
async def drive_projects_update(project_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    try:
        item = dp.update_project(project_id, body)
        return {"ok": True, "project": item}
    except KeyError:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/{project_id}/delete")
async def drive_projects_delete(project_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    delete_sources = bool((body or {}).get("delete_sources"))
    try:
        return dp.delete_project(project_id, delete_sources=delete_sources)
    except KeyError:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)


@router.post("/{project_id}/sync")
async def drive_projects_sync(project_id: str):
    try:
        result = dp.sync_project(project_id)
    except KeyError:
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    code = 200 if result.get("ok") else 502
    return JSONResponse(result, status_code=code)
