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
    import org_pool_guard as opg

    key = op.pool_key(provider)
    if not key:
        return JSONResponse(
            {"ok": False, "error": f"Javis gốc chưa dán khóa {provider}."},
            status_code=503,
        )
    url = op.native_url(provider)
    if not url:
        return JSONResponse({"ok": False, "error": "Nhà cung cấp không hỗ trợ."}, status_code=400)
    slug = str(rec.get("slug") or "").strip()

    body = await request.body()
    headers = {"Content-Type": request.headers.get("content-type") or "application/json"}
    if provider == "anthropic-api":
        headers["x-api-key"] = key
        headers["anthropic-version"] = request.headers.get("anthropic-version") or "2023-06-01"
    else:
        headers["Authorization"] = "Bearer " + key
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://javis.vietmycollege.com"
            headers["X-Title"] = "VMOS org"
    import httpx
    from starlette.background import BackgroundTask

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
    # Concurrency trước RPM: từ chối vì quá tải không đốt hạn mức phút.
    slot = opg.Inflight(slug)
    slot.__enter__()
    if not slot.ok:
        return JSONResponse({"ok": False, "error": slot.error}, status_code=429)
    rate_err = opg.check_rate(slug)
    if rate_err:
        slot.__exit__(None, None, None)
        return JSONResponse({"ok": False, "error": rate_err}, status_code=429)

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
                try:
                    await client.aclose()
                except Exception:
                    pass
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
                slot.__exit__(None, None, None)

        # BackgroundTask: nếu ASGI không bao giờ iterate gen(), vẫn nhả slot.
        return StreamingResponse(
            gen(),
            media_type="text/event-stream",
            background=BackgroundTask(slot.__exit__, None, None, None),
        )

    try:
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
    finally:
        slot.__exit__(None, None, None)


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
        names = [str(t.get("container") or "") for t in data["tenants"] if t.get("container")]
        st_map = org_docker.containers_status_map(names) if (dk_ok and names) else {}
        for t in data["tenants"]:
            rec = op.public_tenant(t)
            cname = str(t.get("container") or "")
            if cname and dk_ok:
                rec["status"] = st_map.get(cname, "missing")
            if ot.is_soft_deleted(t):
                rec["status"] = "deleted"
                rec["paused"] = True
            elif rec.get("paused"):
                rec["status"] = "paused"
            # Digest image: chỉ khi đang chạy và sổ chưa có - tránh inspect hàng loạt.
            if cname and dk_ok and rec.get("status") == "running" and not rec.get("image_digest"):
                try:
                    dig = org_docker.image_short(cname)
                    if dig:
                        rec["image_digest"] = dig
                        t2 = ot.get(str(t.get("slug") or "")) or t
                        t2["image_digest"] = dig
                        ot.upsert(t2)
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
        if not bool(body.get("consent")):
            return JSONResponse(
                {"ok": False, "error": "Cần tích đồng ý xử lý dữ liệu cá nhân trước khi tạo."},
                status_code=400,
            )
        if "brain_mode" in body:
            brain_mode = op.normalize_brain_mode(body.get("brain_mode"))
        else:
            brain_mode = "both" if body.get("shared_api") else "byo"
        providers = op.normalize_providers(body.get("providers"))
        shared = op.mode_uses_pool(brain_mode)
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
                brain_mode=brain_mode,
                providers=providers,
            )
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        import time as _time
        rec = ot.get(slug) or rec
        rec["consent_at"] = int(_time.time())
        rec["consent_version"] = op.CONSENT_VERSION
        op.apply_policy(rec, brain_mode=brain_mode, providers=providers)
        ot.upsert(rec)
        try:
            ot.audit("create", slug, f"mode={brain_mode}")
        except Exception:
            pass
        started = str(rec.get("status") or "") == "running"
        note = ""
        if not started:
            cap = _coord_public()
            note = (
                f"Máy đã tạo, đang tắt vì đủ trần {cap.get('effective_max') or cap.get('max_running')} máy chạy. "
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
        if "shared_api" in body or "brain_mode" in body or "providers" in body:
            mode = body.get("brain_mode") if "brain_mode" in body else None
            prov = body.get("providers") if "providers" in body else None
            shared = body.get("shared_api") if "shared_api" in body else None
            op.apply_policy(rec, brain_mode=mode, providers=prov, shared_api=shared)
            try:
                ot.audit(
                    "policy",
                    slug,
                    f"mode={rec.get('brain_mode')} providers={','.join(rec.get('providers') or [])}",
                )
            except Exception:
                pass
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
        try:
            disk = org_docker.cache_disk_usage(slug, force=True)
            rec = ot.get(slug) or rec
        except Exception:
            disk = int(rec.get("disk_bytes") or 0)
        return {
            "ok": True,
            "quota_gb": int(rec.get("quota_gb") or 0),
            "disk_bytes": disk,
            "disk_checked_at": int(rec.get("disk_checked_at") or 0),
            "token_quota": int(rec.get("token_quota") or 0),
            "tokens_used": int(rec.get("tokens_used") or 0),
            "tokens_month": rec.get("tokens_month") or "",
            "shared_api": bool(rec.get("shared_api")),
            "last_active": int(rec.get("last_active") or 0),
            "image_digest": str(rec.get("image_digest") or ""),
            "deleted_at": int(rec.get("deleted_at") or 0),
        }

    @router.post("/org/tenants/{slug}/start")
    def org_start(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        rec = ot.get(slug)
        if rec and ot.is_soft_deleted(rec):
            return JSONResponse(
                {"ok": False, "error": "Máy đang chờ xóa. Bấm Khôi phục trước."},
                status_code=400,
            )
        if rec:
            rec["paused"] = False
            ot.upsert(rec)
        try:
            org_docker.start_with_capacity(slug)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        return {"ok": True, "coord": _coord_public()}

    @router.post("/org/tenants/{slug}/pause")
    def org_pause(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        rec = ot.get(slug)
        if not rec:
            return JSONResponse({"ok": False, "error": "Không có bản này."}, status_code=404)
        if rec.get("protected"):
            return JSONResponse(
                {"ok": False, "error": "Không tạm dừng bản quan từ đây."},
                status_code=400,
            )
        try:
            org_docker.pause_account(slug)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        try:
            ot.audit("pause", slug)
        except Exception:
            pass
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

    @router.post("/org/tenants/{slug}/restore")
    def org_restore(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        try:
            rec = org_docker.restore_account(slug)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        try:
            ot.audit("restore", slug)
        except Exception:
            pass
        return {"ok": True, "tenant": op.public_tenant(rec), "coord": _coord_public()}

    @router.delete("/org/tenants/{slug}")
    async def org_delete(slug: str, request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        rec = ot.get(slug)
        if not rec:
            return JSONResponse({"ok": False, "error": "Không có bản này."}, status_code=404)
        if rec.get("protected"):
            return JSONResponse(
                {"ok": False, "error": "Không xóa bản quan / não hệ thống."},
                status_code=400,
            )
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        confirm = str(body.get("confirm") or "").strip().lower()
        slug = str(rec.get("slug") or "").strip().lower()
        if confirm != slug:
            return JSONResponse(
                {"ok": False, "error": f"Gõ đúng tên máy «{slug}» để xóa."},
                status_code=400,
            )
        purge_now = bool(body.get("purge_now"))
        # Đã soft-delete + purge_now, hoặc purge_now lần đầu → xóa hẳn
        if purge_now or (ot.is_soft_deleted(rec) and body.get("force")):
            try:
                org_docker.destroy(slug)
            except Exception as e:
                return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
            try:
                ot.audit("delete", slug, "purge_now")
            except Exception:
                pass
            return {"ok": True, "purged": True, "coord": _coord_public()}
        # Mặc định: xóa mềm 72h
        try:
            org_docker.soft_delete(slug)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
        try:
            ot.audit("soft_delete", slug)
        except Exception:
            pass
        return {"ok": True, "soft": True, "purge_after_hours": 72, "coord": _coord_public()}

    @router.get("/org/pool/me")
    def org_pool_me(request: Request):
        rec = op.find_by_token(_ticket(request))
        if not rec:
            return JSONResponse({"ok": False, "error": "Vé không hợp lệ."}, status_code=401)
        ok, why = op.quota_ok(rec)
        ready = op.allowed_pool_providers(rec) if ok else []
        return {
            "ok": True,
            "shared_api": bool(ok and op.mode_uses_pool(
                op.normalize_brain_mode(rec.get("brain_mode"), bool(rec.get("shared_api")))
            )),
            "reason": "" if ok else why,
            "providers": ready,
            "brain_mode": op.normalize_brain_mode(rec.get("brain_mode"), bool(rec.get("shared_api"))),
        }

    @router.api_route("/org/pool/{provider}/chat", methods=["POST"])
    async def org_pool_chat(provider: str, request: Request):
        rec = op.find_by_token(_ticket(request))
        if not rec:
            return JSONResponse({"ok": False, "error": "Vé không hợp lệ."}, status_code=401)
        if provider not in op.POOL_PROVIDERS:
            return JSONResponse({"ok": False, "error": "Nhà cung cấp không hỗ trợ."}, status_code=400)
        if rec.get("paused") or ot.is_soft_deleted(rec):
            return JSONResponse(
                {"ok": False, "error": "Máy đang tạm dừng hoặc chờ xóa - không dùng được API pool."},
                status_code=403,
            )
        ok, why = op.quota_ok(rec)
        if not ok:
            return JSONResponse({"ok": False, "error": why}, status_code=403)
        allowed = op.allowed_pool_providers(rec)
        if provider not in allowed:
            return JSONResponse(
                {"ok": False, "error": f"Provider «{provider}» chưa được bật cho máy này."},
                status_code=403,
            )
        return await _proxy_upstream(provider, request, rec)

    @router.get("/org/audit")
    def org_audit(request: Request, limit: int = 80, slug: str = ""):
        if (deny := _need_manager(request)) is not None:
            return deny
        rows = ot.audit_tail(limit=limit, slug=slug)
        return {"ok": True, "rows": rows}

    @router.get("/org/catalog/status")
    def org_catalog_status(request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        try:
            import manager_template_sync as mts
        except Exception as e:
            return {"ok": False, "error": str(e), "docker": False, "tenants": []}
        docker = False
        tenants = []
        try:
            docker = mts.docker_ok()
            if docker:
                tenants = [
                    n for n in mts.list_javis_containers(
                        exclude={"javis-manager", "javis-proxy", "javis-park"}
                    )
                ]
        except Exception as e:
            return {"ok": True, "docker": False, "error": str(e), "tenants": [],
                    "brain": getattr(mts, "BRAIN_NAME", "Brain Default"),
                    "manager_role": mts.is_manager_role()}
        return {
            "ok": True,
            "docker": docker,
            "brain": getattr(mts, "BRAIN_NAME", "Brain Default"),
            "tenants": tenants,
            "manager_role": mts.is_manager_role(),
        }

    @router.post("/org/catalog/push")
    async def org_catalog_push(request: Request):
        if (deny := _need_manager(request)) is not None:
            return deny
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        dry = bool(body.get("dry_run"))
        try:
            import manager_template_sync as mts
            import asyncio
            import os as _os
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
        if not mts.docker_ok():
            return JSONResponse({
                "ok": False,
                "error": "Docker không dùng được. Gắn docker.sock hoặc chạy scripts/sync_manager_template.py --sync trên VPS.",
            }, status_code=503)
        manager_name = (
            _os.environ.get("JAVIS_MANAGER_NAME")
            or _os.environ.get("JAVIS_NAME")
            or "javis-manager"
        )
        report = await asyncio.to_thread(
            mts.sync_via_docker,
            manager=manager_name,
            dry_run=dry,
        )
        try:
            ot.audit("catalog_push", "", "dry" if dry else "sync")
        except Exception:
            pass
        code = 200 if report.get("ok") else 500
        return JSONResponse(report, status_code=code)

    return router


def register(app):
    app.include_router(_make_router())
