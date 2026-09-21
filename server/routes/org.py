"""API tổ chức (/org/*). Chỉ sống khi JAVIS_ORG_MANAGER=true; không thì 404."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import org_docker
import org_tenants as ot


def _404():
    return JSONResponse({"ok": False, "error": "Không phải Javis gốc."}, status_code=404)


def _make_router() -> APIRouter:
    router = APIRouter()

    @router.get("/org/status")
    def org_status():
        return {"ok": True, "manager": ot.manager_enabled()}

    @router.get("/org/tenants")
    def org_list():
        if not ot.manager_enabled():
            return _404()
        data = ot.load()
        out = []
        for t in data["tenants"]:
            rec = dict(t)
            cname = str(rec.get("container") or "")
            if cname and org_docker.docker_available():
                rec["status"] = org_docker.container_status(cname)
            out.append(rec)
        return {"ok": True, "tenants": out}

    @router.post("/org/tenants")
    async def org_create(request: Request):
        if not ot.manager_enabled():
            return _404()
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        slug = str(body.get("slug") or "").strip().lower()
        err = ot.validate_slug(slug)
        if err:
            return JSONResponse({"ok": False, "error": err}, status_code=400)
        if ot.get(slug):
            return JSONResponse({"ok": False, "error": "Tên này đã có."}, status_code=409)
        try:
            quota = int(body.get("quota_gb") or 2)
        except (TypeError, ValueError):
            quota = 2
        quota = max(1, min(20, quota))
        name = str(body.get("name") or slug).strip()
        if not org_docker.docker_available():
            return JSONResponse(
                {"ok": False, "error": "Javis gốc chưa gắn Docker socket, không tạo được bản mới."},
                status_code=503,
            )
        try:
            rec = org_docker.create_and_start(slug, quota_gb=quota, name=name)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        return {"ok": True, "tenant": rec}

    @router.post("/org/tenants/{slug}/start")
    def org_start(slug: str):
        if not ot.manager_enabled():
            return _404()
        try:
            org_docker.start(slug)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        return {"ok": True}

    @router.post("/org/tenants/{slug}/stop")
    def org_stop(slug: str):
        if not ot.manager_enabled():
            return _404()
        rec = ot.get(slug)
        if rec and rec.get("protected"):
            return JSONResponse(
                {"ok": False, "error": "Không tắt bản quan từ đây - vào đúng link của bản đó."},
                status_code=400,
            )
        try:
            org_docker.stop(slug)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        return {"ok": True}

    return router


def register(app):
    app.include_router(_make_router())
