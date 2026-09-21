"""Tạo/bật/tắt container Javis con qua Docker socket. Không đụng volume javis_javis-*."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import org_tenants as ot

_MEM = 768 * 1024 * 1024
_NANO_CPUS = 750_000_000
_PIDS = 256


def _docker_api(method: str, path: str, json_body: Any = None, timeout: float = 60.0):
    import httpx

    sock = "/var/run/docker.sock"
    if not Path(sock).exists():
        raise RuntimeError("Máy này không gắn Docker socket.")
    transport = httpx.HTTPTransport(uds=sock)
    with httpx.Client(transport=transport, base_url="http://localhost", timeout=timeout) as client:
        return client.request(method, path, json=json_body)


def docker_available() -> bool:
    try:
        r = _docker_api("GET", "/_ping", timeout=5.0)
        return r.status_code == 200 and (r.text or "").strip() == "OK"
    except Exception:
        return False


def inspect_name(name: str) -> dict[str, Any]:
    try:
        r = _docker_api("GET", f"/containers/{quote(name)}/json", timeout=20.0)
        if r.status_code != 200:
            return {}
        data = r.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def container_status(name: str) -> str:
    data = inspect_name(name)
    if not data:
        return "missing"
    st = ((data.get("State") or {}) if isinstance(data.get("State"), dict) else {})
    if st.get("Running"):
        return "running"
    if st.get("Paused"):
        return "paused"
    return "stopped"


def _self_inspect() -> dict[str, Any]:
    me = (os.getenv("JAVIS_NAME") or "").strip() or "javis-manager"
    return inspect_name(me)


def _self_image() -> str:
    data = _self_inspect()
    img = ((data.get("Config") or {}) if isinstance(data.get("Config"), dict) else {}).get("Image")
    if isinstance(img, str) and img.strip():
        return img.strip()
    env = (os.getenv("JAVIS_IMAGE") or "").strip()
    return env or "ghcr.io/duongcanhquan/javisos:latest"


def _ensure_volume(name: str) -> None:
    if name in ot.PROTECTED_VOLUMES:
        raise RuntimeError(f"Cấm tạo/xóa volume {name}")
    r = _docker_api("POST", "/volumes/create", json_body={"Name": name}, timeout=30.0)
    if r.status_code not in (201, 200, 409):
        raise RuntimeError(f"volume {name}: HTTP {r.status_code} {(r.text or '')[:200]}")


def create_and_start(slug: str, quota_gb: int = 2, name: str = "") -> dict:
    err = ot.validate_slug(slug)
    if err:
        raise ValueError(err)
    slug = slug.strip().lower()
    vols = ot.volume_names(slug)
    cname = f"javis-{slug}"
    domain = ot.tenant_domain(slug)
    if inspect_name(cname):
        raise RuntimeError(f"Container {cname} đã tồn tại.")
    for v in vols:
        _ensure_volume(v)
    img = _self_image()
    tz = (os.getenv("TZ") or "Asia/Ho_Chi_Minh").strip() or "Asia/Ho_Chi_Minh"
    env = [
        f"DOMAIN_NAME={domain}",
        "JAVIS_HOST=0.0.0.0",
        "JAVIS_PORT=7777",
        f"JAVIS_NAME={cname}",
        f"TZ={tz}",
        "JAVIS_ADMIN_USER=admin",
        "JAVIS_ADMIN_PASSWORD=admin",
        "JAVIS_ENABLE_USER_PLUGINS=false",
        "JAVIS_KANBAN_MAX_WORKERS=1",
        "JAVIS_ENABLE_PIXELLE=false",
        "JAVIS_ORG_MANAGER=false",
        "JAVIS_ORG_TENANT=true",
        f"JAVIS_QUOTA_GB={int(quota_gb)}",
        "WATCHTOWER_TOKEN=",
    ]
    body = {
        "Image": img,
        "Hostname": cname,
        "Env": env,
        "Labels": {
            "caddy": domain,
            "caddy.reverse_proxy": "{{upstreams 7777}}",
            "javis.org.tenant": slug,
        },
        "HostConfig": {
            "Memory": _MEM,
            "MemorySwap": _MEM,
            "NanoCpus": _NANO_CPUS,
            "PidsLimit": _PIDS,
            "RestartPolicy": {"Name": "unless-stopped"},
            "Binds": [
                f"{vols[0]}:/data",
                f"{vols[1]}:/brains",
                f"{vols[2]}:/home/javis/.claude",
                f"{vols[3]}:/home/javis/.codex",
            ],
            "NetworkMode": "javis-web",
        },
    }
    me = _self_inspect()
    cfg = me.get("Config") if isinstance(me.get("Config"), dict) else {}
    user = cfg.get("User")
    if isinstance(user, str) and user.strip():
        body["User"] = user.strip()
    cr = _docker_api("POST", f"/containers/create?name={quote(cname)}", json_body=body, timeout=120.0)
    if cr.status_code not in (200, 201):
        raise RuntimeError(f"create HTTP {cr.status_code}: {(cr.text or '')[:400]}")
    cid = (cr.json() or {}).get("Id") or ""
    st = _docker_api("POST", f"/containers/{quote(cid or cname)}/start", timeout=60.0)
    if st.status_code not in (204, 200):
        raise RuntimeError(f"start HTTP {st.status_code}: {(st.text or '')[:400]}")
    rec = {
        "id": cid[:12] if cid else slug,
        "slug": slug,
        "name": (name or slug).strip() or slug,
        "domain": domain,
        "container": cname,
        "volumes": vols,
        "quota_gb": int(quota_gb),
        "brain_mode": "school",
        "protected": False,
        "status": "running",
    }
    return ot.upsert(rec)


def start(slug: str) -> None:
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    cname = str(rec.get("container") or f"javis-{slug}")
    r = _docker_api("POST", f"/containers/{quote(cname)}/start", timeout=60.0)
    if r.status_code not in (204, 200, 304):
        raise RuntimeError(f"start HTTP {r.status_code}: {(r.text or '')[:300]}")


def stop(slug: str) -> None:
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    cname = str(rec.get("container") or f"javis-{slug}")
    r = _docker_api("POST", f"/containers/{quote(cname)}/stop", timeout=60.0)
    if r.status_code not in (204, 200, 304):
        raise RuntimeError(f"stop HTTP {r.status_code}: {(r.text or '')[:300]}")
