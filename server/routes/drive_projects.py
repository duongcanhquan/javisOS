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
        return {"ok": True, "project": item}
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
