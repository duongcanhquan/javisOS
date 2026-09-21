"""Tạo/bật/tắt container Javis con qua Docker socket. Không đụng volume javis_javis-*."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import org_policy as op
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


def _exec(cname: str, cmd: list[str], extra_env: list[str] | None = None, timeout: float = 45.0) -> str:
    body = {
        "AttachStdout": True,
        "AttachStderr": True,
        "Tty": True,
        "Cmd": cmd,
    }
    if extra_env:
        body["Env"] = list(extra_env)
    cr = _docker_api("POST", f"/containers/{quote(cname)}/exec", json_body=body, timeout=20.0)
    if cr.status_code not in (200, 201):
        raise RuntimeError(f"exec create HTTP {cr.status_code}: {(cr.text or '')[:200]}")
    eid = ((cr.json() or {}).get("Id") or "").strip()
    if not eid:
        raise RuntimeError("exec không có id")
    st = _docker_api(
        "POST",
        f"/exec/{quote(eid)}/start",
        json_body={"Detach": False, "Tty": True},
        timeout=timeout,
    )
    if st.status_code not in (200, 201, 204):
        raise RuntimeError(f"exec start HTTP {st.status_code}: {(st.text or '')[:200]}")
    return (st.text or "")[-2000:]


def wait_health(cname: str, tries: int = 40) -> None:
    import time
    import httpx

    url = f"http://{cname}:7777/health"
    last = ""
    for _ in range(max(3, tries)):
        try:
            r = httpx.get(url, timeout=3.0)
            if r.status_code == 200:
                return
            last = f"HTTP {r.status_code}"
        except Exception as e:
            last = str(e)[:120]
        time.sleep(2)
    raise RuntimeError(f"Javis con chưa sẵn sàng ({last}).")


def set_admin(cname: str, username: str, password: str) -> None:
    code = (
        "import os,sys\n"
        "sys.path.insert(0,'/app/server')\n"
        "import config as c\n"
        "user=(os.environ.get('ORG_USER') or 'admin').strip() or 'admin'\n"
        "pw=os.environ.get('ORG_PW') or ''\n"
        "if len(pw)<10: raise SystemExit('pw')\n"
        "cfg=c.read_settings()\n"
        "h,s=c.hash_password(pw)\n"
        "a=dict(cfg.get('auth') or {})\n"
        "a['username']=user; a['password_hash']=h; a['salt']=s\n"
        "cfg['auth']=a; c.write_settings(cfg)\n"
        "print('OK')\n"
    )
    out = _exec(
        cname,
        ["python", "-c", code],
        extra_env=[f"ORG_USER={username}", f"ORG_PW={password}"],
    )
    if "OK" not in out:
        raise RuntimeError("Không đặt được mật khẩu trên Javis con.")


def disk_usage_bytes(cname: str) -> int:
    out = _exec(cname, ["python", "-c",
                        "import os\n"
                        "n=0\n"
                        "for root in ('/data','/brains'):\n"
                        "  for dp, dns, fns in os.walk(root):\n"
                        "    dns[:]=[d for d in dns if d not in ('.git','__pycache__')]\n"
                        "    for fn in fns:\n"
                        "      try: n+=os.path.getsize(os.path.join(dp,fn))\n"
                        "      except OSError: pass\n"
                        "print(n)\n"])
    for line in reversed((out or "").splitlines()):
        line = line.strip()
        if line.isdigit():
            return int(line)
    return 0


def create_and_start(
    slug: str,
    quota_gb: int = 2,
    name: str = "",
    login_user: str = "admin",
    password: str = "",
    shared_api: bool = False,
    token_quota: int = 0,
    pool_token: str = "",
) -> dict:
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
    import secrets as _secrets
    bootstrap = _secrets.token_urlsafe(24)
    mgr = (os.getenv("JAVIS_NAME") or "").strip() or "javis-manager"
    login = (login_user or "admin").strip() or "admin"
    env = [
        f"DOMAIN_NAME={domain}",
        "JAVIS_HOST=0.0.0.0",
        "JAVIS_PORT=7777",
        f"JAVIS_NAME={cname}",
        f"TZ={tz}",
        f"JAVIS_ADMIN_USER={login}",
        f"JAVIS_ADMIN_PASSWORD={bootstrap}",
        "JAVIS_ENABLE_USER_PLUGINS=false",
        "JAVIS_KANBAN_MAX_WORKERS=1",
        "JAVIS_ENABLE_PIXELLE=false",
        "JAVIS_ORG_MANAGER=false",
        "JAVIS_ORG_TENANT=true",
        f"JAVIS_QUOTA_GB={int(quota_gb)}",
        f"JAVIS_ORG_POOL_URL=http://{mgr}:7777/org/pool",
        f"JAVIS_ORG_POOL_TOKEN={pool_token}",
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
    wait_health(cname)
    if password:
        set_admin(cname, login, password)
    write_quota(cname, int(quota_gb))
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
        "login_user": login,
        "shared_api": bool(shared_api),
        "token_quota": int(token_quota or 0),
        "tokens_used": 0,
        "tokens_month": "",
        "pool_token_hash": op.hash_token(pool_token) if pool_token else "",
    }
    return ot.upsert(rec)


def write_quota(cname: str, quota_gb: int) -> None:
    gb = int(quota_gb)
    _exec(cname, ["python", "-c",
                  "from pathlib import Path; Path('/data/state').mkdir(parents=True, exist_ok=True); "
                  f"Path('/data/state/org-quota').write_text('{gb}')"])


def start(slug: str) -> None:
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    cname = str(rec.get("container") or f"javis-{slug}")
    r = _docker_api("POST", f"/containers/{quote(cname)}/start", timeout=60.0)
    if r.status_code not in (204, 200, 304):
        raise RuntimeError(f"start HTTP {r.status_code}: {(r.text or '')[:300]}")
    try:
        wait_health(cname)
        write_quota(cname, int(rec.get("quota_gb") or 0))
    except Exception:
        pass


def stop(slug: str) -> None:
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    cname = str(rec.get("container") or f"javis-{slug}")
    r = _docker_api("POST", f"/containers/{quote(cname)}/stop", timeout=60.0)
    if r.status_code not in (204, 200, 304):
        raise RuntimeError(f"stop HTTP {r.status_code}: {(r.text or '')[:300]}")
