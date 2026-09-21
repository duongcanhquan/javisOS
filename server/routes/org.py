"""API tổ chức (/org/*). Manager: cookie admin. Pool tenant: Bearer vé."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

import org_docker
import org_policy as op
import org_tenants as ot


def _404():
    return JSONResponse({"ok": False, "error": "Không phải Javis gốc."}, status_code=404)


def _need_manager(request: Request | None = None):
    if not ot.manager_enabled():
        return _404()
    if request is not None:
        import config as cfgmod
        if cfgmod.gate_active() and not cfgmod.valid_session(request.cookies.get("javis_session", "")):
            return JSONResponse(
                {"ok": False, "error": "Chỉ admin đăng nhập trên Javis gốc mới quản lý được."},
                status_code=403,
            )
    return None


def _ticket(request: Request) -> str:
    raw = (request.headers.get("authorization") or "")
    if raw[:7].lower() == "bearer ":
        return raw[7:].strip()
    return (request.headers.get("x-api-key") or "").strip()


def _int(v, default=0, lo=0, hi=10_000_000):
    try:
        n = int(v)
    except (TypeError, ValueError):
        n = default
    return max(lo, min(hi, n))


def _coord_public():
    import org_coord as oc
    try:
        n = len(org_docker.people_running()) if org_docker.docker_available() else 0
    except Exception:
        n = 0
    return oc.snapshot(n)


async def _proxy_upstream(provider: str, request: Request, rec: dict):
    key = op.pool_key(provider)
    if not key:
        return JSONResponse(
            {"ok": False, "error": f"Javis gốc chưa dán khóa {provider}."},
            status_code=503,
        )
    url = op.native_url(provider)
    if not url:
        return JSONResponse({"ok": False, "error": "Nhà cung cấp không hỗ trợ."}, status_code=400)
    body = await request.body()
    headers = {"Content-Type": request.headers.get("content-type") or "application/json"}
    if provider == "anthropic-api":
        headers["x-api-key"] = key
        headers["anthropic-version"] = request.headers.get("anthropic-version") or "2023-06-01"
    else:
        headers["Authorization"] = "Bearer " + key
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://javis.vietmycollege.com"
            headers["X-Title"] = "Javis OS org"
    import httpx

    stream = (request.headers.get("accept") or "").find("text/event-stream") >= 0
    try:
        payload_hint = (body or b"").lstrip()[:1]
        if payload_hint == b"{":
            import json as _json
            try:
                parsed = _json.loads(body)
                stream = bool(parsed.get("stream")) or stream
            except Exception:
                parsed = None
        else:
            parsed = None
    except Exception:
        parsed = None

    timeout = httpx.Timeout(180.0, connect=20.0)
    if stream:
        client = httpx.AsyncClient(timeout=timeout)

        async def gen():
            used = 0
            tail = b""
            try:
                async with client.stream("POST", url, headers=headers, content=body) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk
                        tail = (tail + chunk)[-12000:]
            finally:
                await client.aclose()
                try:
                    import json as _json
                    import re as _re
                    txt = tail.decode("utf-8", "ignore")
                    for m in _re.finditer(r'"usage"\s*:\s*\{[^}]+\}', txt):
                        blob = "{" + m.group(0) + "}"
                        usage = (_json.loads(blob) or {}).get("usage") or {}
                        used = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
                        used += int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
                except Exception:
                    used = 0
                if used:
                    op.add_tokens(str(rec.get("slug") or ""), used)

        return StreamingResponse(gen(), media_type="text/event-stream")

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, headers=headers, content=body)
    n = 0
    try:
        data = r.json()
        usage = data.get("usage") or {}
        n = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        n += int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    except Exception:
        data = None
    if n:
        op.add_tokens(str(rec.get("slug") or ""), n)
    return JSONResponse(
        content=data if isinstance(data, dict) else {"detail": (r.text or "")[:800]},
        status_code=r.status_code,
    )


def _make_router() -> APIRouter:
    router = APIRouter()

    @router.get("/org/status")
    def org_status():
        import org_coord as oc
        return {"ok": True, "manager": ot.manager_enabled(), "tenant": op.tenant_side(),
                "docker": org_docker.docker_available(),
                "host_prefix": ot.host_prefix(), "domain_suffix": ot.domain_suffix(),
                "coord": oc.coord()}

    @router.get("/org/settings/pool")
    def org_pool_get(request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        return {"ok": True, **op.pool_public()}

    @router.put("/org/settings/pool")
    async def org_pool_put(request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        return {"ok": True, **op.put_pool_keys(body)}

    @router.get("/org/settings/coord")
    def org_coord_get(request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        return {"ok": True, "coord": _coord_public()}

    @router.put("/org/settings/coord")
    async def org_coord_put(request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        import org_coord as oc
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        mx = body.get("max_running")
        idle = body.get("idle_minutes")
        oc.put_coord(
            max_running=None if mx is None else _int(mx, 6, 1, 20),
            idle_minutes=None if idle is None else _int(idle, 30, 0, 24 * 60),
        )
        try:
            org_docker.tick_coord()
        except Exception:
            pass
        return {"ok": True, "coord": _coord_public()}

    @router.get("/org/tenants")
    def org_list(request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        data = ot.load()
        out = []
        dk_ok = org_docker.docker_available()
        for t in data["tenants"]:
            rec = op.public_tenant(t)
            cname = str(t.get("container") or "")
            if cname and dk_ok:
                rec["status"] = org_docker.container_status(cname)
                if not t.get("protected"):
                    try:
                        org_docker.apply_public_hosts(str(t.get("slug") or ""))
                    except Exception:
                        pass
            out.append(rec)
        return {"ok": True, "tenants": out, "docker": dk_ok,
                "host_prefix": ot.host_prefix(), "domain_suffix": ot.domain_suffix(),
                "coord": _coord_public(),
                **op.pool_public()}

    @router.post("/org/tenants")
    async def org_create(request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
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
        login = str(body.get("login_user") or slug).strip() or slug
        err = op.validate_username(login)
        if err:
            return JSONResponse({"ok": False, "error": err}, status_code=400)
        password = str(body.get("password") or "")
        err = op.validate_password(password, login)
        if err:
            return JSONResponse({"ok": False, "error": err}, status_code=400)
        quota = _int(body.get("quota_gb"), 2, 1, 20)
        token_quota = _int(body.get("token_quota"), 0, 0, 50_000_000)
        shared = bool(body.get("shared_api"))
        name = str(body.get("name") or slug).strip()
        ok, why = org_docker.docker_status()
        if not ok:
            return JSONResponse(
                {"ok": False, "error": why or "Javis gốc chưa gắn Docker socket, không tạo được bản mới."},
                status_code=503,
            )
        if shared and not any(v.get("set") for v in op.pool_public()["providers"].values()):
            return JSONResponse(
                {"ok": False, "error": "Chưa dán khóa API chung ở tab Cài đặt chung."},
                status_code=400,
            )
        token = op.new_pool_token()
        try:
            rec = org_docker.create_and_start(
                slug,
                quota_gb=quota,
                name=name,
                login_user=login,
                password=password,
                shared_api=shared,
                token_quota=token_quota,
                pool_token=token,
            )
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        started = str(rec.get("status") or "") == "running"
        note = ""
        if not started:
            cap = _coord_public()
            note = (
                f"Máy đã tạo, đang tắt vì đủ trần {cap.get('max_running')} máy chạy. "
                "Não còn. Họ mở link là tự bật, hoặc bấm Bật máy khi có chỗ."
            )
        return {"ok": True, "tenant": op.public_tenant(rec), "started": started, "note": note}

    @router.patch("/org/tenants/{slug}")
    async def org_patch(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        rec = ot.get(slug)
        if not rec:
            return JSONResponse({"ok": False, "error": "Không có bản này."}, status_code=404)
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        if "name" in body:
            rec["name"] = str(body.get("name") or rec.get("name") or slug).strip()
        if "quota_gb" in body:
            rec["quota_gb"] = _int(body.get("quota_gb"), rec.get("quota_gb") or 0, 0, 20)
            cname = str(rec.get("container") or "")
            if cname and org_docker.docker_available() and org_docker.container_status(cname) == "running":
                try:
                    org_docker.write_quota(cname, rec["quota_gb"])
                except Exception:
                    pass
        if "shared_api" in body:
            rec["shared_api"] = bool(body.get("shared_api"))
        if "token_quota" in body:
            rec["token_quota"] = _int(body.get("token_quota"), 0, 0, 50_000_000)
        if "login_user" in body:
            login = str(body.get("login_user") or "").strip()
            err = op.validate_username(login)
            if err:
                return JSONResponse({"ok": False, "error": err}, status_code=400)
            rec["login_user"] = login
        ot.upsert(rec)
        return {"ok": True, "tenant": op.public_tenant(rec)}

    @router.post("/org/tenants/{slug}/password")
    async def org_password(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        rec = ot.get(slug)
        if not rec:
            return JSONResponse({"ok": False, "error": "Không có bản này."}, status_code=404)
        if rec.get("protected"):
            return JSONResponse(
                {"ok": False, "error": "Không đổi mật khẩu bản quan từ đây."},
                status_code=400,
            )
        try:
            body = await request.json()
        except Exception:
            body = {}
        password = str((body or {}).get("password") or "")
        login = str(rec.get("login_user") or "admin")
        err = op.validate_password(password, login)
        if err:
            return JSONResponse({"ok": False, "error": err}, status_code=400)
        cname = str(rec.get("container") or "")
        if not cname or not org_docker.docker_available():
            return JSONResponse({"ok": False, "error": "Không kết nối được máy của người này."}, status_code=503)
        try:
            org_docker.set_admin(cname, login, password)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        return {"ok": True}

    @router.get("/org/tenants/{slug}/usage")
    def org_usage(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        rec = ot.get(slug)
        if not rec:
            return JSONResponse({"ok": False, "error": "Không có bản này."}, status_code=404)
        op.reset_month_if_needed(rec)
        disk = 0
        cname = str(rec.get("container") or "")
        if cname and org_docker.docker_available() and org_docker.container_status(cname) != "missing":
            try:
                disk = org_docker.disk_usage_bytes(cname)
            except Exception:
                disk = 0
        ot.upsert(rec)
        return {
            "ok": True,
            "quota_gb": int(rec.get("quota_gb") or 0),
            "disk_bytes": disk,
            "token_quota": int(rec.get("token_quota") or 0),
            "tokens_used": int(rec.get("tokens_used") or 0),
            "tokens_month": rec.get("tokens_month") or "",
            "shared_api": bool(rec.get("shared_api")),
        }

    @router.post("/org/tenants/{slug}/start")
    def org_start(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        try:
            org_docker.start_with_capacity(slug)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        return {"ok": True, "coord": _coord_public()}

    @router.post("/org/tenants/{slug}/stop")
    def org_stop(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
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

    @router.get("/org/pool/me")
    def org_pool_me(request: Request):
        rec = op.find_by_token(_ticket(request))
        if not rec:
            return JSONResponse({"ok": False, "error": "Vé không hợp lệ."}, status_code=401)
        ok, why = op.quota_ok(rec)
        ready = [k for k, v in op.pool_public()["providers"].items() if v.get("set")]
        return {
            "ok": True,
            "shared_api": bool(rec.get("shared_api")) and ok,
            "reason": "" if ok else why,
            "providers": ready if rec.get("shared_api") else [],
        }

    @router.api_route("/org/pool/{provider}/chat", methods=["POST"])
    async def org_pool_chat(provider: str, request: Request):
        rec = op.find_by_token(_ticket(request))
        if not rec:
            return JSONResponse({"ok": False, "error": "Vé không hợp lệ."}, status_code=401)
        if provider not in op.POOL_PROVIDERS:
            return JSONResponse({"ok": False, "error": "Nhà cung cấp không hỗ trợ."}, status_code=400)
        ok, why = op.quota_ok(rec)
        if not ok:
            return JSONResponse({"ok": False, "error": why}, status_code=403)
        return await _proxy_upstream(provider, request, rec)

    return router


def register(app):
    app.include_router(_make_router())
