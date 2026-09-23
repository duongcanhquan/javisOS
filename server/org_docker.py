"""Tạo/bật/tắt container Javis con qua Docker socket. Không đụng volume javis_javis-*."""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import org_coord as oc
import org_policy as op
import org_tenants as ot

_MEM = 1024 * 1024 * 1024
_NANO_CPUS = 750_000_000
_PIDS = 256
_LOCK = threading.Lock()
_WAKE_TS: dict[str, float] = {}
# Cache trạng thái container ngắn hạn: list tenants + tick_coord trước đây mỗi tên = 1 inspect
# (N Docker round-trip trên event loop). TTL 2.5s gom các lần gọi sát nhau thành 1 list.
_STATUS_TTL = 2.5
_STATUS_CACHE: dict[str, Any] = {"at": 0.0, "by_name": {}}
_MEM_TTL = 12.0
_MEM_CACHE: dict[str, Any] = {"at": 0.0, "by_name": {}}
# Đọc org-last-active bằng docker exec ~0.25s/máy; cache ngắn để GET /org/tenants
# (sau Lưu/bật-tắt) không đợi N lần exec nối tiếp.
_LAST_ACTIVE_TTL = 20.0
_LAST_ACTIVE_CACHE: dict[str, tuple[float, int]] = {}


def _docker_api(method: str, path: str, json_body: Any = None, timeout: float = 60.0):
    import httpx

    sock = "/var/run/docker.sock"
    if not Path(sock).exists():
        alt = "/run/docker.sock"
        if Path(alt).exists():
            sock = alt
        else:
            raise RuntimeError("Máy này không gắn Docker socket.")
    transport = httpx.HTTPTransport(uds=sock)
    with httpx.Client(transport=transport, base_url="http://localhost", timeout=timeout) as client:
        return client.request(method, path, json=json_body)


def docker_status() -> tuple[bool, str]:
    sock = Path("/var/run/docker.sock")
    if not sock.exists() and not Path("/run/docker.sock").exists():
        return False, "Javis gốc chưa gắn Docker socket, không tạo được bản mới."
    try:
        r = _docker_api("GET", "/_ping", timeout=5.0)
        if r.status_code == 200:
            return True, ""
        return False, f"Docker không trả lời (HTTP {r.status_code})."
    except PermissionError:
        return False, "Javis gốc chưa có quyền Docker. Cần DOCKER_GID đúng trên máy chủ."
    except Exception as e:
        msg = str(e).lower()
        if "permission" in msg or "13" in msg or "denied" in msg:
            return False, "Javis gốc chưa có quyền Docker. Cần DOCKER_GID đúng trên máy chủ."
        return False, "Javis gốc chưa gọi được Docker, không tạo được bản mới."


def docker_available() -> bool:
    ok, _ = docker_status()
    return ok


def memory_should_raise(current: int, target: int = _MEM) -> bool:
    """Trần đang thấp hơn mức máy người (hoặc chưa đặt) thì cần nâng."""
    try:
        cur = int(current or 0)
    except (TypeError, ValueError):
        cur = 0
    return cur != int(target)


_MEM_DONE: set[str] = set()
_MEM_BAO: set[str] = set()


def ensure_people_memory() -> int:
    """Nâng trần RAM mọi máy người lên 1024 MB. Không đụng manager, quan, proxy, park."""
    if not docker_available():
        return 0
    raised = 0
    try:
        r = _docker_api("GET", "/containers/json?all=true", timeout=15.0)
    except Exception as e:
        print(f"[org ram] list: {e}", flush=True)
        return 0
    if r.status_code != 200:
        return 0
    for item in (r.json() or []):
        if not isinstance(item, dict):
            continue
        name = ""
        for raw in item.get("Names") or []:
            n = str(raw or "").strip().lstrip("/")
            if n.startswith("javis-"):
                name = n
                break
        if not name or name in _MEM_DONE:
            continue
        slug = name[len("javis-"):].strip().lower()
        if (not slug or slug in ("manager", "proxy", "park")
                or slug in ot.PROTECTED_SLUGS or ot.validate_slug(slug)):
            _MEM_DONE.add(name)
            continue
        cid = str(item.get("Id") or name)
        try:
            ins = _docker_api("GET", f"/containers/{quote(cid)}/json", timeout=15.0)
        except Exception as e:
            print(f"[org ram] {name}: {e}", flush=True)
            continue
        if ins.status_code != 200:
            continue
        try:
            body = ins.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        hc = body.get("HostConfig") if isinstance(body.get("HostConfig"), dict) else {}
        mem = int(hc.get("Memory") or 0)
        if not memory_should_raise(mem):
            _MEM_DONE.add(name)
            continue
        try:
            upd = _docker_api(
                "POST", f"/containers/{quote(cid)}/update",
                json_body={"Memory": _MEM, "MemorySwap": _MEM}, timeout=30.0,
            )
        except Exception as e:
            if name not in _MEM_BAO:
                print(f"[org ram] {name}: {e}", flush=True)
                _MEM_BAO.add(name)
            continue
        if upd.status_code in (200, 204):
            _MEM_DONE.add(name)
            raised += 1
            print(f"[org ram] {name} trần {mem // (1024 * 1024)} -> 1024 MB", flush=True)
        elif name not in _MEM_BAO:
            print(f"[org ram] {name} HTTP {upd.status_code} {(upd.text or '')[:180]}", flush=True)
            _MEM_BAO.add(name)
    return raised


def heal_ledger() -> int:
    """Người còn container hoặc volume mà mất khỏi sổ thì thêm lại. Không xóa ai."""
    if not docker_available():
        return 0
    names: list[str] = []
    vols: list[str] = []
    try:
        r = _docker_api("GET", "/containers/json?all=true", timeout=15.0)
        if r.status_code == 200:
            for item in (r.json() or []):
                if not isinstance(item, dict):
                    continue
                for n in item.get("Names") or []:
                    names.append(str(n or ""))
    except Exception as e:
        print(f"[org heal] containers: {e}", flush=True)
    try:
        r = _docker_api("GET", "/volumes", timeout=20.0)
        if r.status_code == 200:
            body = r.json() or {}
            for v in body.get("Volumes") or []:
                if isinstance(v, dict):
                    vols.append(str(v.get("Name") or ""))
    except Exception as e:
        print(f"[org heal] volumes: {e}", flush=True)
    try:
        return ot.adopt_missing(ot.slugs_from_infra(names, vols))
    except Exception as e:
        print(f"[org heal] sổ: {e}", flush=True)
        return 0


def invalidate_status_cache(*names: str) -> None:
    """Gọi sau start/stop/remove để lần list kế không ăn trạng thái cũ."""
    if not names:
        _STATUS_CACHE["at"] = 0.0
        _STATUS_CACHE["by_name"] = {}
        return
    by = _STATUS_CACHE.get("by_name") or {}
    for n in names:
        by.pop(str(n or ""), None)


def _status_from_inspect(data: dict) -> str:
    if not data:
        return "missing"
    st = ((data.get("State") or {}) if isinstance(data.get("State"), dict) else {})
    if st.get("Running"):
        return "running"
    if st.get("Paused"):
        return "paused"
    return "stopped"


def containers_status_map(names: list[str] | None = None, force: bool = False) -> dict[str, str]:
    """Map tên container → running|paused|stopped|missing bằng MỘT lần list Docker.

    `names=None` trả toàn bộ đang biết trong cache/list. Tên không thấy trong list = missing.
    """
    now = time.time()
    cached = _STATUS_CACHE.get("by_name") or {}
    if (not force and now - float(_STATUS_CACHE.get("at") or 0) < _STATUS_TTL
            and cached):
        if names is None:
            return dict(cached)
        return {n: cached.get(n, "missing") for n in names}

    by: dict[str, str] = {}
    try:
        r = _docker_api("GET", "/containers/json?all=true", timeout=15.0)
        if r.status_code == 200:
            for item in (r.json() or []):
                if not isinstance(item, dict):
                    continue
                state = str(item.get("State") or "").lower()
                if state == "running":
                    status = "running"
                elif state == "paused":
                    status = "paused"
                else:
                    status = "stopped"
                for nm in item.get("Names") or []:
                    nm = str(nm or "").lstrip("/")
                    if nm:
                        by[nm] = status
    except Exception:
        # List hỏng: giữ cache cũ nếu còn, không xoá trắng (tránh báo missing hàng loạt).
        if cached:
            by = dict(cached)
    _STATUS_CACHE["at"] = now
    _STATUS_CACHE["by_name"] = by
    if names is None:
        return dict(by)
    return {n: by.get(n, "missing") for n in names}


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
    nm = str(name or "")
    if not nm:
        return "missing"
    now = time.time()
    cached = _STATUS_CACHE.get("by_name") or {}
    if now - float(_STATUS_CACHE.get("at") or 0) < _STATUS_TTL and nm in cached:
        return cached[nm]
    data = inspect_name(nm)
    st = _status_from_inspect(data)
    cached[nm] = st
    _STATUS_CACHE["by_name"] = cached
    if not _STATUS_CACHE.get("at"):
        _STATUS_CACHE["at"] = now
    return st


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


def _exec(cname: str, cmd: list[str], extra_env: list[str] | None = None, timeout: float = 45.0,
         user: str | None = None, exit_box: list | None = None) -> str:
    body = {
        "AttachStdout": True,
        "AttachStderr": True,
        "Tty": True,
        "Cmd": cmd,
    }
    if user:
        body["User"] = user
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
    if exit_box is not None:
        code = 0
        try:
            info = _docker_api("GET", f"/exec/{quote(eid)}/json", timeout=10.0)
            if info.status_code == 200:
                code = int((info.json() or {}).get("ExitCode") or 0)
        except Exception:
            code = 1
        exit_box[:] = [code]
    return (st.text or "")[-2000:]


def _health_inside(cname: str) -> bool:
    """Gọi /health từ bên trong máy con (127.0.0.1), không cần DNS giữa các container."""
    code = (
        "import os,sys,urllib.request\n"
        "u='http://127.0.0.1:'+os.getenv('JAVIS_PORT','7777')+'/health'\n"
        "sys.exit(0 if urllib.request.urlopen(u,timeout=4).status==200 else 1)\n"
    )
    body = {
        "AttachStdout": True,
        "AttachStderr": True,
        "Tty": False,
        "Cmd": ["python", "-c", code],
    }
    try:
        cr = _docker_api("POST", f"/containers/{quote(cname)}/exec", json_body=body, timeout=20.0)
        if cr.status_code not in (200, 201):
            return False
        eid = ((cr.json() or {}).get("Id") or "").strip()
        if not eid:
            return False
        _docker_api(
            "POST",
            f"/exec/{quote(eid)}/start",
            json_body={"Detach": False, "Tty": False},
            timeout=15.0,
        )
        inf = _docker_api("GET", f"/exec/{quote(eid)}/json", timeout=10.0)
        return int(((inf.json() or {}).get("ExitCode")) or 1) == 0
    except Exception:
        return False


def wait_health(cname: str, tries: int = 40) -> None:
    import time

    last = ""
    for _ in range(max(3, tries)):
        data = inspect_name(cname)
        if not data:
            last = "không thấy máy"
        else:
            st = data.get("State") if isinstance(data.get("State"), dict) else {}
            if not st.get("Running"):
                last = "máy chưa chạy"
            elif _health_inside(cname):
                return
            else:
                health = st.get("Health") if isinstance(st.get("Health"), dict) else {}
                last = str(health.get("Status") or "chưa trả lời /health")
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


# Phần chạy trên máy chủ, không nằm trong image. Trước đây deploy chỉ chép vào máy cá nhân
# (javis-quan). Máy người bị gắn lại từ image nên mất file. Javis gốc gắn cùng bộ, chỉ đọc,
# để mọi tenant chạy họp, sơ đồ và font như bản quan.
MOONSHINE_HOST = (os.getenv("JAVIS_MOONSHINE_DIR") or "/root/javis-data/moonshine-models").strip() or "/root/javis-data/moonshine-models"
MOONSHINE_DEST = "/app/dashboard/vendor/moonshine-models"
MOONSHINE_MARK = MOONSHINE_DEST + "/vi/decoder_model_merged.ort"
_SHARE_OK: set[str] = set()
_SHARE_NEXT = 0
_SHARE_COPYING = False
_SHARE_LOCK = threading.Lock()
_SHARE_COOL: dict[str, float] = {}


def dashboard_vendor_host() -> str:
    raw = (os.getenv("JAVIS_DASHBOARD_VENDOR_DIR") or "/root/javis-data/dashboard-vendor").strip()
    return raw or "/root/javis-data/dashboard-vendor"


def shared_runtime_specs() -> list[dict[str, str]]:
    """Những thư mục máy quan đang có để trang chạy tốt. Tenant phải có đúng các đường này."""
    vendor = dashboard_vendor_host()
    return [
        {
            "id": "moonshine",
            "host": MOONSHINE_HOST,
            "dest": MOONSHINE_DEST,
            "mark": MOONSHINE_MARK,
        },
        {
            "id": "mermaid",
            "host": vendor + "/mermaid",
            "dest": "/app/dashboard/vendor/mermaid",
            "mark": "/app/dashboard/vendor/mermaid/mermaid.min.js",
        },
        {
            "id": "turndown",
            "host": vendor + "/turndown",
            "dest": "/app/dashboard/vendor/turndown",
            "mark": "/app/dashboard/vendor/turndown/turndown.js",
        },
        {
            "id": "fonts",
            "host": vendor + "/fonts",
            "dest": "/app/dashboard/vendor/fonts",
            "mark": "/app/dashboard/vendor/fonts/montserrat.css",
        },
    ]


def moonshine_bind() -> str:
    """Thư mục model trên máy chủ, chỉ đọc, mọi tenant dùng chung."""
    return f"{MOONSHINE_HOST}:{MOONSHINE_DEST}:ro"


def _bind_dest(bind: str) -> str:
    parts = str(bind or "").split(":")
    if len(parts) >= 3:
        return parts[-2]
    if len(parts) == 2:
        return parts[-1]
    return ""


def attach_moonshine_bind(binds: list) -> list:
    out = [b for b in binds if _bind_dest(str(b)) != MOONSHINE_DEST]
    out.append(moonshine_bind())
    return out


def attach_shared_runtime_binds(binds: list) -> list:
    dests = {s["dest"] for s in shared_runtime_specs()}
    out = [b for b in binds if _bind_dest(str(b)) not in dests]
    for spec in shared_runtime_specs():
        out.append(f"{spec['host']}:{spec['dest']}:ro")
    return out


def _person_slug(name: str) -> str:
    if not str(name or "").startswith("javis-"):
        return ""
    slug = str(name)[len("javis-"):].strip().lower()
    if (not slug or slug in ("manager", "proxy", "park")
            or slug in ot.PROTECTED_SLUGS or ot.validate_slug(slug)):
        return ""
    return slug


def _dest_mounted(cname: str, dest: str) -> bool:
    data = inspect_name(cname)
    for m in data.get("Mounts") or []:
        if isinstance(m, dict) and str(m.get("Destination") or "") == dest:
            return True
    return False


def moonshine_mounted(cname: str) -> bool:
    return _dest_mounted(cname, MOONSHINE_DEST)


def _mark_present(cname: str, mark: str) -> bool:
    box: list = []
    try:
        _exec(cname, ["test", "-s", mark], user="0", exit_box=box, timeout=20.0)
    except Exception:
        return False
    return bool(box) and int(box[0]) == 0


def moonshine_present(cname: str) -> bool:
    return _mark_present(cname, MOONSHINE_MARK)


def _running_person_names() -> list[str]:
    try:
        r = _docker_api("GET", "/containers/json", timeout=15.0)
    except Exception:
        return []
    if r.status_code != 200:
        return []
    out: list[str] = []
    for item in (r.json() or []):
        if not isinstance(item, dict):
            continue
        name = ""
        for raw in item.get("Names") or []:
            n = str(raw or "").strip().lstrip("/")
            if _person_slug(n):
                name = n
                break
        if name:
            out.append(name)
    return out


def _runtime_donor(dst: str, mark: str, asset_id: str) -> str:
    for name in ("javis-quan", "javis"):
        if name == dst:
            continue
        if _mark_present(name, mark):
            return name
    prefix = "|" + asset_id
    for key in _SHARE_OK:
        if not key.endswith(prefix):
            continue
        name = key.split("|", 1)[0]
        if name != dst and _mark_present(name, mark):
            return name
    return ""


def _stream_tree(src: str, src_path: str, dst: str, parent: str) -> bool:
    """Chép một thư mục từ container nguồn sang máy thiếu, qua Docker archive."""
    import tempfile

    import httpx

    sock = "/var/run/docker.sock"
    if not Path(sock).exists():
        sock = "/run/docker.sock"
    transport = httpx.HTTPTransport(uds=sock)
    tmp = ""
    try:
        with httpx.Client(transport=transport, base_url="http://localhost", timeout=600.0) as client:
            with client.stream(
                "GET",
                f"/containers/{quote(src)}/archive",
                params={"path": src_path},
            ) as resp:
                if resp.status_code != 200:
                    return False
                fd, tmp = tempfile.mkstemp(prefix="javis-share-", suffix=".tar")
                with os.fdopen(fd, "wb") as out:
                    for chunk in resp.iter_bytes(1024 * 1024):
                        if chunk:
                            out.write(chunk)

            def _chunks():
                with open(tmp, "rb") as inp:
                    while True:
                        blob = inp.read(1024 * 1024)
                        if not blob:
                            break
                        yield blob

            put = client.put(
                f"/containers/{quote(dst)}/archive",
                params={"path": parent},
                content=_chunks(),
            )
            if put.status_code not in (200, 201):
                return False
        _exec(dst, ["chmod", "-R", "a+rX", src_path], user="0", timeout=60.0)
        return True
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


def _copy_runtime_worker(dst: str, spec: dict[str, str]) -> None:
    global _SHARE_COPYING
    key = dst + "|" + spec["id"]
    try:
        if _dest_mounted(dst, spec["dest"]):
            print(
                f"[org share] {dst} đã gắn {spec['host']} nhưng thiếu file. "
                "Thư mục trên máy chủ đang trống.",
                flush=True,
            )
            _SHARE_COOL[key] = time.time() + 3600
            return
        src = _runtime_donor(dst, spec["mark"], spec["id"])
        if not src:
            print(f"[org share] không có máy nào đang giữ {spec['id']} để chép cho {dst}", flush=True)
            _SHARE_COOL[key] = time.time() + 600
            return
        parent = str(Path(spec["dest"]).parent)
        if _stream_tree(src, spec["dest"], dst, parent) and _mark_present(dst, spec["mark"]):
            _SHARE_OK.add(key)
            print(f"[org share] đã chép {spec['id']} vào {dst}", flush=True)
        else:
            print(f"[org share] chép {spec['id']} vào {dst} thất bại", flush=True)
            _SHARE_COOL[key] = time.time() + 600
    except Exception as e:
        print(f"[org share] {dst} {spec['id']}: {e}", flush=True)
        _SHARE_COOL[key] = time.time() + 600
    finally:
        with _SHARE_LOCK:
            _SHARE_COPYING = False


def ensure_shared_runtime() -> None:
    """Mỗi nhịp kiểm một phần (model họp, sơ đồ, font) trên một máy người.

    Thiếu thì chép nền từ máy đang có, ưu tiên javis-quan. Máy đã gắn thư mục máy chủ
    thì không ghi đè.
    """
    global _SHARE_NEXT, _SHARE_COPYING
    specs = shared_runtime_specs()
    pending: list[tuple[str, dict[str, str]]] = []
    for name in _running_person_names():
        for spec in specs:
            if (name + "|" + spec["id"]) not in _SHARE_OK:
                pending.append((name, spec))
    if not pending:
        return
    _SHARE_NEXT = _SHARE_NEXT % len(pending)
    name, spec = pending[_SHARE_NEXT]
    _SHARE_NEXT += 1
    key = name + "|" + spec["id"]
    if time.time() < float(_SHARE_COOL.get(key) or 0):
        return
    if _mark_present(name, spec["mark"]):
        _SHARE_OK.add(key)
        return
    with _SHARE_LOCK:
        if _SHARE_COPYING:
            return
        _SHARE_COPYING = True
    threading.Thread(target=_copy_runtime_worker, args=(name, spec), daemon=True).start()


def ensure_moonshine_models() -> None:
    """Tên cũ. Javis gốc nay rà cả bộ phần chạy chung, không chỉ model họp."""
    ensure_shared_runtime()


def create_and_start(
    slug: str,
    quota_gb: int = 2,
    name: str = "",
    login_user: str = "admin",
    password: str = "",
    shared_api: bool = False,
    token_quota: int = 0,
    pool_token: str = "",
    brain_mode: str = "",
    providers: list | None = None,
) -> dict:
    err = ot.validate_slug(slug)
    if err:
        raise ValueError(err)
    slug = slug.strip().lower()
    vols = ot.volume_names(slug)
    cname = f"javis-{slug}"
    domain = ot.tenant_domain(slug)
    existing = inspect_name(cname)
    if existing and ot.get(slug):
        raise RuntimeError(f"Container {cname} đã tồn tại.")
    tz = (os.getenv("TZ") or "Asia/Ho_Chi_Minh").strip() or "Asia/Ho_Chi_Minh"
    import secrets as _secrets
    bootstrap = _secrets.token_urlsafe(24)
    mgr = (os.getenv("JAVIS_NAME") or "").strip() or "javis-manager"
    login = (login_user or "admin").strip() or "admin"
    cid = ""
    if not existing:
        for v in vols:
            _ensure_volume(v)
        img = _self_image()
        env = [
            f"DOMAIN_NAME={domain}",
            "JAVIS_HOST=0.0.0.0",
            "JAVIS_PORT=7777",
            f"JAVIS_NAME={cname}",
            f"TZ={tz}",
            f"JAVIS_ADMIN_USER={login}",
            f"JAVIS_ADMIN_PASSWORD={bootstrap}",
            "GEMINI_FORCE_FILE_STORAGE=true",
            "JAVIS_TERMINAL_REMOTE=1",
            "JAVIS_ENABLE_USER_PLUGINS=false",
            "JAVIS_KANBAN_MAX_WORKERS=1",
            "JAVIS_ENABLE_PIXELLE=false",
            "JAVIS_ORG_MANAGER=false",
            "JAVIS_ORG_TENANT=true",
            "WORKSPACE_NAME=VietMy OS",
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
                "Binds": attach_shared_runtime_binds([
                    f"{vols[0]}:/data",
                    f"{vols[1]}:/brains",
                    f"{vols[2]}:/home/javis/.claude",
                    f"{vols[3]}:/home/javis/.codex",
                ]),
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
    else:
        cid = str(existing.get("Id") or "")
        if container_status(cname) != "running":
            st = _docker_api("POST", f"/containers/{quote(cname)}/start", timeout=60.0)
            if st.status_code not in (204, 200, 304):
                raise RuntimeError(f"start HTTP {st.status_code}: {(st.text or '')[:400]}")
    rec = {
        "id": cid[:12] if cid else slug,
        "slug": slug,
        "name": (name or slug).strip() or slug,
        "domain": domain,
        "container": cname,
        "volumes": vols,
        "quota_gb": int(quota_gb),
        "protected": False,
        "status": container_status(cname),
        "login_user": login,
        "token_quota": int(token_quota or 0),
        "tokens_used": 0,
        "tokens_month": "",
        "pool_token_hash": op.hash_token(pool_token) if pool_token else "",
    }
    mode = brain_mode or ("both" if shared_api else "byo")
    op.apply_policy(rec, brain_mode=mode, providers=providers if providers is not None else [],
                    shared_api=shared_api if not brain_mode else None)
    ot.upsert(rec)
    boot_warn = ""
    try:
        wait_health(cname)
        if password:
            set_admin(cname, login, password)
        write_quota(cname, int(quota_gb))
        rec["status"] = "running"
        rec["last_active"] = int(time.time())
        rec = ot.upsert(rec)
        try:
            _park_new_if_over_cap(slug)
        except Exception:
            pass
        try:
            sync_park()
        except Exception:
            pass
        rec = ot.get(slug) or rec
        rec["status"] = container_status(cname)
        return ot.upsert(rec)
    except Exception as e:
        # Máy đã ghi sổ + container thường đã tạo. Health/mật khẩu chậm không được
        # trả 400 làm UI báo "tạo hỏng" trong khi tenant vẫn nằm trong sổ.
        rec["status"] = container_status(cname)
        ot.upsert(rec)
        if not inspect_name(cname):
            raise
        boot_warn = str(e)[:240].strip() or "khởi động chậm"
        if password:
            try:
                set_admin(cname, login, password)
                write_quota(cname, int(quota_gb))
            except Exception as e2:
                boot_warn = str(e2)[:240].strip() or boot_warn
        rec = ot.get(slug) or rec
        rec["status"] = container_status(cname)
        rec["boot_warn"] = boot_warn
        try:
            _park_new_if_over_cap(slug)
        except Exception:
            pass
        try:
            sync_park()
        except Exception:
            pass
        rec = ot.get(slug) or rec
        rec["status"] = container_status(cname)
        rec["boot_warn"] = boot_warn
        return ot.upsert(rec)


def apply_public_hosts(slug: str) -> None:
    """Cập nhật nhãn Caddy sang prefix mới (vd vmos-), không đụng volume. Không đụng bản quan."""
    rec = ot.get(slug)
    if not rec or rec.get("protected"):
        return
    cname = str(rec.get("container") or f"javis-{slug}")
    wanted = ot.tenant_domain(slug).strip()
    if not wanted:
        return
    data = inspect_name(cname)
    if not data:
        return
    was_running = container_status(cname) == "running"
    cfg = data.get("Config") if isinstance(data.get("Config"), dict) else {}
    labels = dict(cfg.get("Labels") or {})
    old = (labels.get("caddy") or "").strip()
    have_id = str(data.get("Image") or "")
    want_id = str(_self_inspect().get("Image") or "")
    img = _self_image()
    if old == wanted and have_id and want_id and have_id == want_id:
        return
    hc = data.get("HostConfig") if isinstance(data.get("HostConfig"), dict) else {}
    env = [e for e in (cfg.get("Env") or [])
           if not str(e).startswith("DOMAIN_NAME=") and not str(e).startswith("WORKSPACE_NAME=")]
    env.append("DOMAIN_NAME=" + wanted)
    env.append("WORKSPACE_NAME=VietMy OS")
    # Đăng nhập agy trên VPS: lưu token ra file + terminal khai phiên từ xa (SSH_CONNECTION).
    if not any(str(e).startswith("GEMINI_FORCE_FILE_STORAGE=") for e in env):
        env.append("GEMINI_FORCE_FILE_STORAGE=true")
    if not any(str(e).startswith("JAVIS_TERMINAL_REMOTE=") for e in env):
        env.append("JAVIS_TERMINAL_REMOTE=1")
    labels["caddy"] = wanted
    labels["caddy.reverse_proxy"] = "{{upstreams 7777}}"
    try:
        vols = ot.volume_names(str(rec.get("slug") or slug))
        binds = [
            f"{vols[0]}:/data",
            f"{vols[1]}:/brains",
            f"{vols[2]}:/home/javis/.claude",
            f"{vols[3]}:/home/javis/.codex",
        ]
    except Exception:
        binds = list(hc.get("Binds") or [])
    if not binds:
        raise RuntimeError("Từ chối gắn lại máy không có ổ não.")
    binds = attach_shared_runtime_binds(binds)
    body = {
        "Image": img,
        "Hostname": cfg.get("Hostname") or cname,
        "Env": env,
        "Labels": labels,
        "HostConfig": {
            "Memory": _MEM,
            "MemorySwap": _MEM,
            "NanoCpus": hc.get("NanoCpus") or _NANO_CPUS,
            "PidsLimit": hc.get("PidsLimit") or _PIDS,
            "RestartPolicy": hc.get("RestartPolicy") or {"Name": "unless-stopped"},
            "Binds": binds,
            "NetworkMode": hc.get("NetworkMode") or "javis-web",
        },
    }
    user = cfg.get("User")
    if isinstance(user, str) and user.strip():
        body["User"] = user.strip()
    # Xóa container, GIỮ volume (không gắn cờ xóa volume).
    _docker_api("POST", f"/containers/{quote(cname)}/stop", timeout=60.0)
    rm = _docker_api("DELETE", f"/containers/{quote(cname)}?force=true", timeout=30.0)
    if rm.status_code not in (204, 200, 404):
        raise RuntimeError(f"gỡ máy cũ HTTP {rm.status_code}: {(rm.text or '')[:200]}")
    cr = _docker_api("POST", f"/containers/create?name={quote(cname)}", json_body=body, timeout=120.0)
    if cr.status_code not in (200, 201):
        raise RuntimeError(f"gắn tên miền mới HTTP {cr.status_code}: {(cr.text or '')[:400]}")
    cid = (cr.json() or {}).get("Id") or cname
    if was_running:
        st = _docker_api("POST", f"/containers/{quote(cid)}/start", timeout=60.0)
        if st.status_code not in (204, 200):
            raise RuntimeError(f"bật lại HTTP {st.status_code}: {(st.text or '')[:300]}")


def write_quota(cname: str, quota_gb: int) -> None:
    gb = int(quota_gb)
    _exec(cname, ["python", "-c",
                  "from pathlib import Path; Path('/data/state').mkdir(parents=True, exist_ok=True); "
                  f"Path('/data/state/org-quota').write_text('{gb}')"])


def start(slug: str, *, wait_ready: bool = False) -> None:
    """Bật container. Mặc định KHÔNG chờ /health (tránh treo manager ~1 phút).

    Admin bấm Bật máy / wake link: trả lời ngay khi Docker start xong; máy còn
    khởi động vài giây. create_and_start vẫn wait_ready=True.
    """
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    cname = str(rec.get("container") or f"javis-{slug}")
    r = _docker_api("POST", f"/containers/{quote(cname)}/start", timeout=60.0)
    if r.status_code not in (204, 200, 304):
        raise RuntimeError(f"start HTTP {r.status_code}: {(r.text or '')[:300]}")
    invalidate_status_cache(cname)
    if wait_ready:
        try:
            wait_health(cname, tries=20)
        except Exception:
            pass
    try:
        write_quota(cname, int(rec.get("quota_gb") or 0))
    except Exception:
        pass


def stop(slug: str, park: bool = True) -> None:
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    cname = str(rec.get("container") or f"javis-{slug}")
    try:
        rec["last_active"] = read_last_active(cname, rec)
        ot.upsert(rec)
    except Exception:
        pass
    r = _docker_api("POST", f"/containers/{quote(cname)}/stop", timeout=60.0)
    if r.status_code not in (204, 200, 304):
        raise RuntimeError(f"stop HTTP {r.status_code}: {(r.text or '')[:300]}")
    invalidate_status_cache(cname)
    rec["status"] = "stopped"
    ot.upsert(rec)
    if park:
        try:
            sync_park()
        except Exception:
            pass


def pause_account(slug: str) -> None:
    """Tắt máy và khóa tự bật. Não còn. Chỉ vào lại khi quản trị bấm Chạy lại."""
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    slug = str(rec.get("slug") or "").strip().lower()
    if rec.get("protected") or slug in ot.PROTECTED_SLUGS:
        raise RuntimeError("Không tạm dừng bản hệ thống.")
    if ot.is_soft_deleted(rec):
        raise RuntimeError("Máy đang chờ xóa. Bấm Khôi phục trước, hoặc đợi hết 72 giờ.")
    rec["paused"] = True
    rec["status"] = "stopped"
    ot.upsert(rec)
    cname = str(rec.get("container") or f"javis-{slug}")
    if docker_available() and inspect_name(cname) and container_status(cname) == "running":
        stop(slug)
        rec = ot.get(slug) or rec
        rec["paused"] = True
        ot.upsert(rec)
        return
    try:
        sync_park()
    except Exception:
        pass


def soft_delete(slug: str) -> dict:
    """Tắt máy, đánh dấu chờ xóa 72h. Giữ volume / não. Không tự bật khi mở link."""
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    slug = str(rec.get("slug") or "").strip().lower()
    if rec.get("protected") or slug in ot.PROTECTED_SLUGS:
        raise RuntimeError("Không xóa bản hệ thống.")
    err = ot.validate_slug(slug)
    if err:
        raise RuntimeError(err)
    if ot.is_soft_deleted(rec):
        return rec
    cname = str(rec.get("container") or f"javis-{slug}")
    if docker_available() and inspect_name(cname) and container_status(cname) == "running":
        try:
            stop(slug, park=False)
        except Exception:
            pass
    rec = ot.soft_delete_mark(slug)
    oc.clear_wait(slug)
    try:
        sync_park()
    except Exception:
        pass
    return rec


def restore_account(slug: str) -> dict:
    """Gỡ chờ xóa. Não còn. Vẫn tạm dừng đến khi bấm Chạy lại."""
    rec = ot.restore_mark(slug)
    try:
        sync_park()
    except Exception:
        pass
    return rec


def destroy(slug: str) -> None:
    """Xóa máy người: container + 4 volume tenant. Không đụng volume quan / manager."""
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    slug = str(rec.get("slug") or "").strip().lower()
    if rec.get("protected") or slug in ot.PROTECTED_SLUGS:
        raise RuntimeError("Không xóa bản hệ thống.")
    err = ot.validate_slug(slug)
    if err:
        raise RuntimeError(err)
    vols = ot.volume_names(slug)
    for v in vols:
        if v in ot.PROTECTED_VOLUMES:
            raise RuntimeError(f"Từ chối xóa volume hệ thống: {v}")
    cname = str(rec.get("container") or f"javis-{slug}")
    if cname in ("javis-quan", "javis-manager", "javis-proxy", "javis-park"):
        raise RuntimeError("Không xóa máy hệ thống.")
    if docker_available() and inspect_name(cname):
        _docker_api("POST", f"/containers/{quote(cname)}/stop", timeout=60.0)
        rm = _docker_api("DELETE", f"/containers/{quote(cname)}?force=true", timeout=30.0)
        if rm.status_code not in (204, 200, 404):
            raise RuntimeError(f"gỡ máy HTTP {rm.status_code}: {(rm.text or '')[:200]}")
    if docker_available():
        for v in vols:
            vr = _docker_api("DELETE", f"/volumes/{quote(v)}", timeout=30.0)
            if vr.status_code not in (204, 200, 404):
                raise RuntimeError(f"xóa ổ {v}: HTTP {vr.status_code} {(vr.text or '')[:200]}")
    oc.clear_wait(slug)
    ot.remove(slug)
    try:
        sync_park()
    except Exception:
        pass


def purge_soft_deleted() -> list[str]:
    """Hủy hẳn các máy đã hết hạn 72h. Gọi từ tick_coord."""
    done = []
    for slug in ot.purge_due_slugs():
        try:
            destroy(slug)
            ot.audit("purge", slug, "soft-delete 72h")
            done.append(slug)
        except Exception as e:
            print(f"[org purge] {slug}: {e}", flush=True)
    return done


def people_running() -> list[dict]:
    out = []
    if not docker_available():
        return out
    tenants = [t for t in (ot.load().get("tenants") or [])
               if not t.get("protected") and not ot.is_soft_deleted(t)]
    names = [str(t.get("container") or "") for t in tenants if t.get("container")]
    st_map = containers_status_map(names) if names else {}
    for t in tenants:
        cname = str(t.get("container") or "")
        if cname and st_map.get(cname) == "running":
            out.append(t)
    return out


def container_mem_mb(cname: str) -> tuple[int, int]:
    """(usage_mb, limit_mb) từ Docker stats. (0,0) nếu lỗi.

    Dùng one-shot=true (API ≥1.41): một mẫu ngay, không đợi ~1s/máy như stream=false.
    """
    name = (cname or "").strip()
    if not name or not docker_available():
        return 0, 0
    now = time.time()
    by = _MEM_CACHE.get("by_name") or {}
    if now - float(_MEM_CACHE.get("at") or 0) < _MEM_TTL and name in by:
        u, lim = by[name]
        return int(u), int(lim)
    try:
        path = f"/containers/{quote(name)}/stats?stream=false&one-shot=true"
        r = _docker_api("GET", path, timeout=4.0)
        if r.status_code != 200:
            # Docker cũ không biết one-shot → thử lại không one-shot (chậm hơn).
            r = _docker_api("GET", f"/containers/{quote(name)}/stats?stream=false", timeout=8.0)
        if r.status_code != 200:
            return 0, 0
        data = r.json() or {}
        ms = data.get("memory_stats") if isinstance(data.get("memory_stats"), dict) else {}
        usage = int(ms.get("usage") or 0)
        stats = ms.get("stats") if isinstance(ms.get("stats"), dict) else {}
        cache = int(stats.get("total_inactive_file") or stats.get("inactive_file") or 0)
        if cache and cache < usage:
            usage = usage - cache
        limit = int(ms.get("limit") or 0)
        if limit <= 0 or limit > 256 * 1024 * 1024 * 1024:
            limit = _MEM
        u_mb = max(0, usage // (1024 * 1024))
        lim_mb = max(0, limit // (1024 * 1024))
    except Exception:
        return 0, 0
    if now - float(_MEM_CACHE.get("at") or 0) >= _MEM_TTL:
        _MEM_CACHE["at"] = now
        _MEM_CACHE["by_name"] = {}
        by = _MEM_CACHE["by_name"]
    by[name] = (u_mb, lim_mb)
    return u_mb, lim_mb


def ram_live_report(running: list[dict] | None = None) -> dict:
    """RAM thật các máy người đang mở; tách máy đang dùng / đang nghỉ.

    `running`: danh sách đã lọc (tránh gọi lại people_running). Đo mem + last-active
    song song để GET sổ tổ chức không xếp hàng N Docker round-trip.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    now = int(time.time())
    idle_m = int(oc.coord().get("idle_minutes") or 0)
    grace = oc.idle_sec(idle_m) if idle_m > 0 else oc.HANDOFF_CAP_SEC
    tenants = list(running) if running is not None else people_running()
    machines = []
    used = 0
    idle_used = 0
    active_n = idle_n = 0

    def _row(t: dict) -> dict:
        slug = str(t.get("slug") or "")
        cname = str(t.get("container") or "")
        u, lim = container_mem_mb(cname) if cname else (0, 0)
        ts = read_last_active(cname, t, assume_running=True) if cname else 0
        age = (now - ts) if ts > 0 else 10**9
        is_idle = age >= grace
        return {
            "slug": slug,
            "mem_mb": u,
            "limit_mb": lim or oc.RAM_MB,
            "idle": is_idle,
            "idle_sec": int(age) if age < 10**9 else None,
            "_u": u,
            "_idle": is_idle,
        }

    rows: list[dict] = []
    if tenants:
        workers = min(8, len(tenants))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_row, t): t for t in tenants}
            for fut in as_completed(futs):
                try:
                    rows.append(fut.result())
                except Exception:
                    t = futs[fut]
                    rows.append({
                        "slug": str(t.get("slug") or ""),
                        "mem_mb": 0,
                        "limit_mb": oc.RAM_MB,
                        "idle": True,
                        "idle_sec": None,
                        "_u": 0,
                        "_idle": True,
                    })
        rows.sort(key=lambda m: str(m.get("slug") or ""))
    for m in rows:
        u = int(m.pop("_u", 0) or 0)
        is_idle = bool(m.pop("_idle", False))
        if is_idle:
            idle_n += 1
            idle_used += u
        else:
            active_n += 1
        used += u
        machines.append(m)
    _tot, avail = oc.host_mem_mb()
    budget = max(0, int(avail or 0) + idle_used - oc.KEEP_FREE_MB)
    fit_more = budget // max(1, oc.RAM_MB)
    return {
        "machines": machines,
        "people_used_mb": used,
        "people_idle_mb": idle_used,
        "people_active_n": active_n,
        "people_idle_n": idle_n,
        "ram_limit_mb": oc.RAM_MB,
        "fit_more_est": int(fit_more),
        "note": "Máy bật vẫn tốn RAM app. Nghỉ từ 15 phút thì tự nhả cache file. Tắt máy mới trả hết.",
    }


def image_short(cname: str) -> str:
    """Digest/ID ngắn của image container (hiển thị trên card)."""
    data = inspect_name(cname)
    if not data:
        return ""
    iid = str(data.get("Image") or "").strip()
    if iid.startswith("sha256:"):
        return iid[7:19]
    if len(iid) > 12 and ":" not in iid[:20]:
        return iid[:12]
    # Config.Image thường là tag; ImageID mới là digest
    iid2 = str(data.get("ImageID") or (data.get("Config") or {}).get("Image") or "").strip()
    if isinstance(data.get("ImageID"), str) and data["ImageID"].startswith("sha256:"):
        return data["ImageID"][7:19]
    cfg = data.get("Config") if isinstance(data.get("Config"), dict) else {}
    tag = str(cfg.get("Image") or iid or "").strip()
    if "@sha256:" in tag:
        return tag.split("@sha256:", 1)[1][:12]
    if tag:
        # rút gọn tag dài: lấy phần sau dấu : cuối hoặc 20 ký tự đầu
        if ":" in tag and "/" in tag:
            return tag.rsplit(":", 1)[-1][:20]
        return tag[-20:] if len(tag) > 20 else tag
    return (iid2[:12] if iid2 else "")


def cache_disk_usage(slug: str, force: bool = False) -> int:
    """Đọc ổ và ghi cache trên ledger (TTL ~120s)."""
    rec = ot.get(slug)
    if not rec:
        return 0
    now = int(time.time())
    try:
        checked = int(rec.get("disk_checked_at") or 0)
        cached = int(rec.get("disk_bytes") or 0)
    except (TypeError, ValueError):
        checked, cached = 0, 0
    if not force and checked and now - checked < oc.DISK_CACHE_SEC:
        return cached
    cname = str(rec.get("container") or "")
    disk = cached
    if cname and docker_available() and container_status(cname) != "missing":
        try:
            disk = disk_usage_bytes(cname)
        except Exception:
            disk = cached
    rec["disk_bytes"] = int(disk or 0)
    rec["disk_checked_at"] = now
    dig = ""
    if cname and docker_available() and container_status(cname) != "missing":
        try:
            dig = image_short(cname)
        except Exception:
            dig = ""
    if dig:
        rec["image_digest"] = dig
    ot.upsert(rec)
    return int(disk or 0)


def read_last_active(cname: str, rec: dict | None = None, *,
                     force: bool = False, assume_running: bool = False) -> int:
    """Thời điểm hoạt động gần nhất của người (để tắt máy nghỉ / nhả chỗ).

    Chỉ tin file org-last-active trong máy (mỗi request có người ghi) hoặc last_active
    trên sổ. KHÔNG dùng StartedAt của Docker: giờ bật container ≠ người đang dùng -
    sau deploy cả đám máy «vừa bật» sẽ không ai bị tắt → xếp hàng oan.

    `assume_running`: bỏ inspect lại khi caller đã biết máy đang chạy (ram_live_report).
    """
    name = (cname or "").strip()
    now = time.time()
    if name and not force:
        hit = _LAST_ACTIVE_CACHE.get(name)
        if hit and now - float(hit[0]) < _LAST_ACTIVE_TTL:
            return int(hit[1])
    ts = 0
    if name and docker_available() and (
        assume_running or container_status(name) == "running"
    ):
        try:
            # cat nhanh hơn python -c; file thiếu → stdout rỗng.
            out = _exec(
                name,
                ["sh", "-c", "cat /data/state/org-last-active 2>/dev/null || true"],
                timeout=8.0,
            )
            for line in reversed((out or "").splitlines()):
                line = line.strip()
                if line.isdigit():
                    ts = int(line)
                    break
        except Exception:
            ts = 0
    if ts <= 0:
        try:
            ts = int((rec or {}).get("last_active") or 0)
        except (TypeError, ValueError):
            ts = 0
    if name:
        _LAST_ACTIVE_CACHE[name] = (now, int(ts or 0))
    return int(ts or 0)


def _started_unix(raw: str) -> int:
    s = (raw or "").strip()
    if not s or s.startswith("0001"):
        return 0
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        from datetime import datetime
        if "." in s:
            i = s.find(".")
            j = i + 1
            while j < len(s) and s[j].isdigit():
                j += 1
            digits = s[i + 1:j][:6].ljust(6, "0")
            s = s[:i] + "." + digits + s[j:]
        return int(datetime.fromisoformat(s).timestamp())
    except Exception:
        return 0


def _evict_grace_sec(pressure: bool = False) -> int:
    return oc.evict_grace_sec(pressure=pressure)


def _handoff_grace_sec() -> int:
    return oc.handoff_grace_sec()


def _pick_evict(except_slug: str, grace_sec: int | None = None) -> str:
    now = int(time.time())
    grace = int(grace_sec) if grace_sec is not None else _evict_grace_sec()
    best_slug = ""
    best_ts = now + 1
    for t in people_running():
        slug = str(t.get("slug") or "")
        if not slug or slug == except_slug or t.get("protected") or t.get("paused"):
            continue
        cname = str(t.get("container") or "")
        ts = read_last_active(cname, t)
        if ts <= 0:
            ts = 1
        if now - ts < grace:
            continue
        if ts < best_ts:
            best_ts = ts
            best_slug = slug
    return best_slug


def _acquire_slot(slug: str) -> None:
    """Không tắt máy khác để lấy chỗ. Tenant được bật và giữ chạy."""
    return


def _park_new_if_over_cap(slug: str) -> None:
    """Không tắt máy vừa tạo vì vượt trần. Quản trị tắt tay nếu cần."""
    return


def start_with_capacity(slug: str) -> dict:
    rec = ot.get(slug)
    if not rec:
        raise RuntimeError("Không có bản này.")
    if ot.is_soft_deleted(rec):
        raise RuntimeError("Máy đang chờ xóa. Bấm Khôi phục trên Tổ chức trước.")
    if rec.get("paused"):
        raise RuntimeError("Tài khoản đang tạm dừng. Bấm Chạy lại trên Tổ chức.")
    cname = str(rec.get("container") or f"javis-{slug}")
    if rec.get("protected"):
        start(slug)
        rec["status"] = container_status(cname)
        return ot.upsert(rec)
    with _LOCK:
        if container_status(cname) == "running":
            rec["last_active"] = int(time.time())
            rec["status"] = "running"
            rec = ot.upsert(rec)
            oc.clear_wait(slug)
            return rec
        _acquire_slot(slug)
        start(slug)
    rec = ot.get(slug) or rec
    rec["last_active"] = int(time.time())
    rec["status"] = container_status(cname)
    rec = ot.upsert(rec)
    oc.clear_wait(slug)
    try:
        sync_park()
    except Exception:
        pass
    return rec


# Máy nghỉ lâu thì nhả cache file (cgroup memory.reclaim). Không tắt app, không đụng RAM tiến trình.
_CACHE_IDLE_SEC = 15 * 60
_CACHE_MIN_BYTES = 64 * 1024 * 1024
_CACHE_EVERY_SEC = 30 * 60
_CACHE_LAST: dict[str, float] = {}
_CACHE_CURSOR = 0
_CACHE_BAO: set[str] = set()


def parse_cgroup_memory_stat(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for raw in (text or "").replace("\r", "\n").splitlines():
        parts = raw.split()
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        out[parts[0]] = int(parts[1])
    return out


def file_cache_reclaim_bytes(stat: dict | None, *, min_bytes: int = _CACHE_MIN_BYTES) -> int:
    """Byte cache file nên nhả. 0 nếu dưới ngưỡng (khỏi quét máy gần như trống)."""
    try:
        file_b = int((stat or {}).get("file") or 0)
    except (TypeError, ValueError):
        return 0
    if file_b < int(min_bytes):
        return 0
    return file_b


def cache_reclaim_due(idle_age_sec: int, last_reclaim: float, now: float,
                      *, idle_need: int = _CACHE_IDLE_SEC,
                      every: int = _CACHE_EVERY_SEC) -> bool:
    """Chỉ nhả khi người đã vắng đủ lâu và lần nhả trước đã qua."""
    try:
        age = int(idle_age_sec)
    except (TypeError, ValueError):
        return False
    if age < int(idle_need):
        return False
    try:
        last = float(last_reclaim or 0)
    except (TypeError, ValueError):
        last = 0.0
    return (float(now) - last) >= int(every)


def reclaim_idle_file_cache() -> int:
    """Mỗi nhịp xét một máy người đang bật. Nghỉ >= 15 phút và cache file >= 64 MB thì nhả.

    Không restart, không tắt. Kernel lấy lại trang file; lần đọc sau có thể cache lại.
    """
    global _CACHE_CURSOR
    tenants = people_running()
    if not tenants:
        return 0
    t = tenants[_CACHE_CURSOR % len(tenants)]
    _CACHE_CURSOR += 1
    slug = str(t.get("slug") or "")
    cname = str(t.get("container") or "")
    if not cname or not slug:
        return 0
    now = time.time()
    ts = read_last_active(cname, t, assume_running=True)
    age = int(now - ts) if ts > 0 else 10**9
    if not cache_reclaim_due(age, _CACHE_LAST.get(cname, 0.0), now):
        return 0
    try:
        raw = _exec(cname, ["cat", "/sys/fs/cgroup/memory.stat"], timeout=12.0)
    except Exception as e:
        if cname not in _CACHE_BAO:
            print(f"[org cache] {slug}: {e}", flush=True)
            _CACHE_BAO.add(cname)
        _CACHE_LAST[cname] = now
        return 0
    nbytes = file_cache_reclaim_bytes(parse_cgroup_memory_stat(raw))
    if nbytes <= 0:
        return 0
    box: list[int] = []
    try:
        _exec(
            cname,
            ["sh", "-c", f"echo {int(nbytes)} > /sys/fs/cgroup/memory.reclaim"],
            timeout=20.0,
            user="0",
            exit_box=box,
        )
    except Exception as e:
        if cname not in _CACHE_BAO:
            print(f"[org cache] {slug}: {e}", flush=True)
            _CACHE_BAO.add(cname)
        _CACHE_LAST[cname] = now
        return 0
    if box and box[0] != 0:
        if cname not in _CACHE_BAO:
            print(f"[org cache] {slug}: nhả cache lỗi {box[0]}", flush=True)
            _CACHE_BAO.add(cname)
        _CACHE_LAST[cname] = now
        return 0
    _CACHE_LAST[cname] = now
    _CACHE_BAO.discard(cname)
    _MEM_CACHE["at"] = 0.0
    _MEM_CACHE["by_name"] = {}
    mb = nbytes // (1024 * 1024)
    print(f"[org cache] {slug} nhả {mb} MB cache file", flush=True)
    return 1


def tick_coord() -> None:
    if not ot.manager_enabled() or not docker_available():
        return
    try:
        n = heal_ledger()
        if n:
            print(f"[org heal] gắn lại {n} người còn máy hoặc ổ não", flush=True)
    except Exception as e:
        print(f"[org heal] {e}", flush=True)
    try:
        ensure_people_memory()
    except Exception as e:
        print(f"[org ram] {e}", flush=True)
    try:
        ensure_shared_runtime()
    except Exception as e:
        print(f"[org moon] {e}", flush=True)
    try:
        reclaim_idle_file_cache()
    except Exception as e:
        print(f"[org cache] {e}", flush=True)
    try:
        purge_soft_deleted()
    except Exception as e:
        print(f"[org purge] {e}", flush=True)
    # Không tự tắt tenant theo giờ vắng, trần chỗ hay RAM. Chỉ tắt khi quản trị bấm.
    try:
        if int(oc.coord().get("idle_minutes") or 0) != 0:
            oc.put_coord(idle_minutes=0)
    except Exception as e:
        print(f"[org coord] ghi idle 0: {e}", flush=True)
    w = oc.peek_waiter()
    if w:
        rec = ot.get(w)
        if rec and not rec.get("paused") and not rec.get("protected") and not ot.is_soft_deleted(rec):
            try:
                start_with_capacity(w)
            except Exception:
                pass
        else:
            oc.clear_wait(w)
    try:
        sync_park()
    except Exception as e:
        print(f"[org park] {e}", flush=True)


def sync_park() -> None:
    """Nhãn Caddy cho máy ĐÃ TẮT: mở link vẫn vào Javis gốc để tự bật. Không volume."""
    if not docker_available():
        return
    hosts = []
    tenants = ot.load().get("tenants") or []
    names = [str(t.get("container") or "") for t in tenants
             if t.get("container") and not t.get("protected")]
    st_map = containers_status_map(names) if names else {}
    for t in tenants:
        if t.get("protected"):
            continue
        slug = str(t.get("slug") or "")
        cname = str(t.get("container") or "")
        if not slug or not cname:
            continue
        if st_map.get(cname) == "running":
            continue
        hosts.append(ot.tenant_domain(slug))
    wanted = "|".join(hosts)
    data = inspect_name(oc.PARK_NAME)
    labels = {}
    if data:
        cfg = data.get("Config") if isinstance(data.get("Config"), dict) else {}
        labels = dict(cfg.get("Labels") or {})
    old = (labels.get("javis.org.park.hosts") or "").strip()
    if old == wanted and data and ((data.get("State") or {}).get("Running") if isinstance(data.get("State"), dict) else False):
        return
    if data:
        _docker_api("POST", f"/containers/{quote(oc.PARK_NAME)}/stop", timeout=30.0)
        rm = _docker_api("DELETE", f"/containers/{quote(oc.PARK_NAME)}?force=true", timeout=30.0)
        if rm.status_code not in (204, 200, 404):
            raise RuntimeError(f"gỡ park HTTP {rm.status_code}")
    if not hosts:
        return
    mgr = (os.getenv("JAVIS_NAME") or "").strip() or "javis-manager"
    plabels = {
        "javis.org.park": "1",
        "javis.org.park.hosts": wanted,
    }
    for i, h in enumerate(hosts):
        plabels[f"caddy_{i}"] = h
        plabels[f"caddy_{i}.reverse_proxy"] = f"{mgr}:7777"
    body = {
        "Image": _self_image(),
        "Hostname": oc.PARK_NAME,
        "Cmd": ["python", "-c", "import time; time.sleep(10**9)"],
        "Labels": plabels,
        "HostConfig": {
            "Memory": 32 * 1024 * 1024,
            "MemorySwap": 32 * 1024 * 1024,
            "PidsLimit": 32,
            "RestartPolicy": {"Name": "unless-stopped"},
            "NetworkMode": "javis-web",
        },
        "User": "javis",
    }
    cr = _docker_api("POST", f"/containers/create?name={quote(oc.PARK_NAME)}", json_body=body, timeout=60.0)
    if cr.status_code not in (200, 201):
        raise RuntimeError(f"tạo park HTTP {cr.status_code}: {(cr.text or '')[:300]}")
    cid = (cr.json() or {}).get("Id") or oc.PARK_NAME
    st = _docker_api("POST", f"/containers/{quote(cid)}/start", timeout=30.0)
    if st.status_code not in (204, 200):
        raise RuntimeError(f"bật park HTTP {st.status_code}: {(st.text or '')[:200]}")


def wake_or_wait(slug: str, host: str) -> tuple[str, int]:
    rec = ot.get(slug)
    if not rec or rec.get("protected"):
        title = "Không có Javis này"
        body = "Tên máy không có trên tổ chức. Hỏi quản trị tạo lại trên Javis gốc."
        return oc.wake_html(host, title, body, 8), 404
    if ot.is_soft_deleted(rec):
        try:
            left = max(0, int(rec.get("deleted_at") or 0) + ot.SOFT_DELETE_SEC - int(time.time()))
            hrs = max(1, (left + 3599) // 3600)
        except Exception:
            hrs = 72
        return oc.wake_html(
            host, "Máy đang chờ xóa",
            f"Quản trị đã đánh dấu xóa. Não còn khoảng {hrs} giờ nữa rồi mới xóa hẳn. "
            "Bấm Khôi phục trên Tổ chức nếu cần giữ lại.",
            0,
        ), 403
    if rec.get("paused"):
        return oc.wake_html(
            host, "Tài khoản tạm dừng",
            "Quản trị đã tạm dừng máy này. Não và file còn, không xóa. Bấm Chạy lại trên Tổ chức mới vào được.",
            0,
        ), 403
    cname = str(rec.get("container") or f"javis-{slug}")
    if docker_available() and container_status(cname) == "running":
        return oc.wake_html(
            host, "Đang nối vào máy của bạn",
            "Máy đã bật. Não và API ở đây, không chung người khác.",
            3,
        ), 200
    now = time.time()
    last = float(_WAKE_TS.get(slug) or 0)
    if now - last < 20 and docker_available() and container_status(cname) != "running":
        return oc.wake_html(
            host, "Đang bật máy",
            "Javis đang mở máy của bạn. Não và ổ giữ nguyên, không xóa.",
            4,
        ), 200
    _WAKE_TS[slug] = now
    try:
        start_with_capacity(slug)
    except Exception as e:
        pos = oc.enqueue_wait(slug)
        detail = str(e).strip()
        if len(detail) > 280:
            detail = detail[:277] + "…"
        return oc.wake_html(
            host, "Đang xếp lượt mở máy",
            f"{detail} Bạn đứng hàng thứ {pos}. Não và file không mất - không phải lỗi.",
            8,
        ), 503
    return oc.wake_html(
        host, "Đang bật máy",
        "Javis đang mở máy của bạn. Não, mật khẩu và API riêng giữ nguyên.",
        4,
    ), 200
