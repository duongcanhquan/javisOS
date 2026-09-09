"""Kho tri thức Google Drive: sync rclone → corpus → mirror sources/drive/<slug>/.

Lưu registry tại STATE_DIR/drive_projects.json (sống qua update Docker).
Corpus nhị phân: STATE_DIR/drive-corpus/<brain-safe>/<slug>/
Brain làm việc: <brain>/sources/drive/<slug>/
"""
from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import threading
import time
import unicodedata
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

import config as cfgmod
import winproc

_LOCK = threading.RLock()
_STORE_NAME = "drive_projects.json"
_TEXT_EXT = {".md", ".txt", ".markdown", ".csv", ".json", ".yaml", ".yml"}
_DOC_EXT = {".pdf", ".docx", ".doc", ".pptx", ".xlsx"}
_SKIP_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}

# Injected by routes.register — avoid importing main.
_brain_root_fn: Optional[Callable[[str], str]] = None
_sessions_fn: Optional[Callable[[], Any]] = None
_script_path: Optional[Path] = None


def configure(
    *,
    brain_root: Callable[[str], str],
    get_sessions_store: Callable[[], Any],
    sync_script: Path | None = None,
) -> None:
    global _brain_root_fn, _sessions_fn, _script_path
    _brain_root_fn = brain_root
    _sessions_fn = get_sessions_store
    _script_path = sync_script


def _store_path() -> Path:
    return cfgmod.STATE_DIR / _STORE_NAME


def _brain_safe(brain: str) -> str:
    raw = (brain or "brain").strip() or "brain"
    # Absolute path → last folder name; else ascii slug of the string.
    try:
        p = Path(raw)
        if p.is_absolute() or "/" in raw or "\\" in raw:
            name = p.name or "brain"
        else:
            name = raw
    except Exception:
        name = "brain"
    return _ascii_slug(name) or "brain"


def _ascii_slug(s: str) -> str:
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s)
    return (s[:60] or "kho").strip("-") or "kho"


def _folder_id_ok(fid: str) -> bool:
    f = (fid or "").strip()
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{10,128}", f))


def parse_drive_folder_ref(raw: str) -> str:
    """Nhận ID thuần hoặc URL Drive → folder id. Raise ValueError nếu không hợp lệ."""
    s = (raw or "").strip()
    if not s:
        raise ValueError("Thiếu link hoặc Folder ID thư mục Drive")
    m = re.search(r"/folders/([A-Za-z0-9_-]+)", s)
    if m:
        fid = m.group(1)
    else:
        m = re.search(r"[?&]id=([A-Za-z0-9_-]+)", s)
        fid = m.group(1) if m else s
    fid = fid.strip()
    if not _folder_id_ok(fid):
        raise ValueError(
            "Folder ID/URL không hợp lệ. Dán URL dạng "
            "https://drive.google.com/drive/folders/FOLDER_ID hoặc chỉ FOLDER_ID."
        )
    return fid


def _extract_token_json(text: str) -> str | None:
    """Lấy khối JSON token từ output rclone authorize / paste người dùng."""
    if not text:
        return None
    s = text.strip()
    # Bỏ khung "Paste the following... ---> ... <---End paste"
    m = re.search(
        r"---+>\s*(\{.*?\})\s*<---+",
        s,
        flags=re.S,
    )
    if m:
        cand = m.group(1).strip()
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict) and obj.get("access_token"):
                return json.dumps(obj, separators=(",", ":"))
        except Exception:
            pass
    # JSON object có access_token (lấy khối lớn nhất hợp lệ)
    for m in re.finditer(r"\{[^{}]*\"access_token\"[^{}]*\}", s, flags=re.S):
        cand = m.group(0)
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict) and obj.get("access_token"):
                return json.dumps(obj, separators=(",", ":"))
        except Exception:
            continue
    # Nested / multiline: tìm từ { đầu tiên chứa access_token
    idx = s.find('"access_token"')
    if idx >= 0:
        start = s.rfind("{", 0, idx)
        if start >= 0:
            depth = 0
            for i in range(start, len(s)):
                if s[i] == "{":
                    depth += 1
                elif s[i] == "}":
                    depth -= 1
                    if depth == 0:
                        cand = s[start : i + 1]
                        try:
                            obj = json.loads(cand)
                            if isinstance(obj, dict) and obj.get("access_token"):
                                return json.dumps(obj, separators=(",", ":"))
                        except Exception:
                            break
    return None


def _load() -> dict:
    p = _store_path()
    if not p.is_file():
        return {"version": 1, "projects": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "projects": []}
    if not isinstance(data, dict):
        return {"version": 1, "projects": []}
    projects = data.get("projects")
    if not isinstance(projects, list):
        projects = []
    data["projects"] = projects
    data["version"] = 1
    return data


def _save(data: dict) -> None:
    p = _store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def list_projects(brain: str | None = None) -> list[dict]:
    with _LOCK:
        data = _load()
        items = list(data.get("projects") or [])
    if brain:
        bkey = (brain or "").strip()
        # Match exact brain string OR same resolved folder name.
        safe = _brain_safe(bkey)
        out = []
        for it in items:
            ib = str(it.get("brain") or "")
            if ib == bkey or _brain_safe(ib) == safe:
                out.append(it)
        return out
    return items


def get_project(pid: str) -> Optional[dict]:
    pid = (pid or "").strip()
    if not pid:
        return None
    with _LOCK:
        for it in _load().get("projects") or []:
            if it.get("id") == pid:
                return dict(it)
    return None


def create_project(
    *,
    name: str,
    brain: str,
    drive_folder_id: str,
    rclone_remote: str = "gdrive:",
    schedule: str = "",
    slug: str = "",
) -> dict:
    name = (name or "").strip()[:80]
    if not name:
        raise ValueError("Thiếu tên kho")
    fid = parse_drive_folder_ref(drive_folder_id)
    brain = (brain or "brain").strip() or "brain"
    slug = _ascii_slug(slug or name)
    remote = (rclone_remote or "gdrive:").strip() or "gdrive:"
    if not remote.endswith(":"):
        remote = remote.rstrip("/") + ":"

    with _LOCK:
        data = _load()
        # Unique slug per brain
        for it in data["projects"]:
            if _brain_safe(it.get("brain") or "") == _brain_safe(brain) and it.get("slug") == slug:
                raise ValueError(f"Slug đã dùng trong brain này: {slug}")
        now = time.time()
        item = {
            "id": uuid.uuid4().hex,
            "name": name,
            "slug": slug,
            "brain": brain,
            "drive_folder_id": fid,
            "rclone_remote": remote,
            "enabled": True,
            "schedule": (schedule or "").strip()[:80],
            "chat_project_id": "",
            "last_sync_at": None,
            "last_sync_ok": None,
            "last_sync_error": "",
            "last_sync_stats": {},
            "created_at": now,
            "updated_at": now,
        }
        data["projects"].append(item)
        _save(data)

    _ensure_sources_scaffold(item)
    chat_id = _ensure_chat_project(item)
    if chat_id:
        with _LOCK:
            data = _load()
            for it in data["projects"]:
                if it.get("id") == item["id"]:
                    it["chat_project_id"] = chat_id
                    item = dict(it)
                    break
            _save(data)
    return item


def update_project(pid: str, patch: dict) -> dict:
    with _LOCK:
        data = _load()
        found = None
        for it in data["projects"]:
            if it.get("id") == pid:
                found = it
                break
        if not found:
            raise KeyError("not found")
        if "name" in patch and patch["name"] is not None:
            n = str(patch["name"]).strip()[:80]
            if n:
                found["name"] = n
        if "drive_folder_id" in patch and patch["drive_folder_id"] is not None:
            found["drive_folder_id"] = parse_drive_folder_ref(str(patch["drive_folder_id"]))
        if "rclone_remote" in patch and patch["rclone_remote"] is not None:
            remote = str(patch["rclone_remote"]).strip() or "gdrive:"
            if not remote.endswith(":"):
                remote = remote.rstrip("/") + ":"
            found["rclone_remote"] = remote
        if "schedule" in patch and patch["schedule"] is not None:
            found["schedule"] = str(patch["schedule"]).strip()[:80]
        if "enabled" in patch and patch["enabled"] is not None:
            found["enabled"] = bool(patch["enabled"])
        found["updated_at"] = time.time()
        _save(data)
        item = dict(found)
    _ensure_chat_project(item)
    return get_project(pid) or item


def delete_project(pid: str, *, delete_sources: bool = False) -> dict:
    with _LOCK:
        data = _load()
        kept, removed = [], None
        for it in data["projects"]:
            if it.get("id") == pid:
                removed = it
            else:
                kept.append(it)
        if not removed:
            raise KeyError("not found")
        data["projects"] = kept
        _save(data)
    if delete_sources:
        try:
            root = Path(_brain_root(removed.get("brain") or "brain"))
            src = root / "sources" / "drive" / (removed.get("slug") or "x")
            if src.is_dir() and "sources/drive" in str(src).replace("\\", "/"):
                shutil.rmtree(src, ignore_errors=True)
        except Exception:
            pass
    return {"ok": True, "id": pid, "slug": removed.get("slug")}


def corpus_dir(item: dict) -> Path:
    return (
        cfgmod.STATE_DIR
        / "drive-corpus"
        / _brain_safe(item.get("brain") or "brain")
        / (item.get("slug") or "kho")
    )


def sources_dir(item: dict) -> Path:
    root = Path(_brain_root(item.get("brain") or "brain"))
    return root / "sources" / "drive" / (item.get("slug") or "kho")


def _brain_root(brain: str) -> str:
    if _brain_root_fn:
        return _brain_root_fn(brain)
    # Fallback for tests
    return brain if os.path.isdir(brain) else str(cfgmod.STATE_DIR / "test-brain")


def _rclone_env() -> dict:
    env = os.environ.copy()
    # Giữ config rclone trong STATE_DIR (volume Docker) thay vì ~/.config mất khi recreate.
    conf = cfgmod.STATE_DIR / "rclone.conf"
    env.setdefault("RCLONE_CONFIG", str(conf))
    return env


def rclone_config_path() -> Path:
    return cfgmod.STATE_DIR / "rclone.conf"


def rclone_status() -> dict:
    rclone = shutil.which("rclone")
    conf = rclone_config_path()
    out = {
        "rclone_installed": bool(rclone),
        "rclone_path": rclone or "",
        "rclone_config": str(conf),
        "remotes": [],
        "google_connected": False,
        "default_remote": "gdrive:",
    }
    if not rclone:
        return out
    try:
        r = subprocess.run(
            [rclone, "listremotes"],
            capture_output=True,
            text=True,
            timeout=15,
            env=_rclone_env(),
            creationflags=winproc.no_window(),
        )
        if r.returncode == 0:
            out["remotes"] = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
        else:
            out["listremotes_error"] = (r.stderr or r.stdout or "")[:400]
    except Exception as e:
        out["listremotes_error"] = f"{type(e).__name__}: {e}"
    remotes = out["remotes"]
    out["google_connected"] = "gdrive:" in remotes or any(
        (x or "").rstrip(":").lower() == "gdrive" for x in remotes
    )
    return out


# --- Wizard kết nối Google (authorize / paste token / upload conf) ---

_AUTH_LOCK = threading.Lock()
_AUTH_SESSIONS: dict[str, dict[str, Any]] = {}
_AUTH_TTL_SEC = 600


def _auth_cleanup_locked() -> None:
    now = time.time()
    dead = []
    for sid, sess in _AUTH_SESSIONS.items():
        if now - float(sess.get("started_at") or 0) > _AUTH_TTL_SEC:
            dead.append(sid)
            proc = sess.get("proc")
            if proc and proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
    for sid in dead:
        _AUTH_SESSIONS.pop(sid, None)


def save_gdrive_token(token_raw: str, *, remote_name: str = "gdrive") -> dict:
    """Ghi remote Google Drive từ token JSON (rclone authorize)."""
    rclone = shutil.which("rclone")
    if not rclone:
        raise ValueError("Chưa cài rclone trên máy chạy Javis")
    token = _extract_token_json(token_raw) or ""
    if not token:
        raise ValueError(
            "Token không hợp lệ. Dán cả khối JSON có access_token "
            "(output của rclone authorize \"drive\")."
        )
    name = (remote_name or "gdrive").strip().rstrip(":") or "gdrive"
    env = _rclone_env()
    rclone_config_path().parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [rclone, "config", "delete", name],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        creationflags=winproc.no_window(),
    )
    r = subprocess.run(
        [
            rclone,
            "config",
            "create",
            name,
            "drive",
            "scope",
            "drive",
            "token",
            token,
            "--non-interactive",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        creationflags=winproc.no_window(),
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "rclone config create thất bại").strip()[:500]
        raise ValueError(err)
    st = rclone_status()
    if not st.get("google_connected") and f"{name}:" not in (st.get("remotes") or []):
        # Một số bản rclone vẫn tạo remote dù list lệch tên
        st["google_connected"] = True
        if f"{name}:" not in st.get("remotes", []):
            st.setdefault("remotes", []).append(f"{name}:")
    return st


def save_rclone_conf_text(text: str) -> dict:
    """Ghi đè rclone.conf (upload từ máy đã cấu hình sẵn)."""
    body = (text or "").strip()
    if not body:
        raise ValueError("File rclone.conf trống")
    low = body.lower()
    if "type = drive" not in low and "type=drive" not in low:
        raise ValueError("File không có remote Google Drive (thiếu type = drive)")
    path = rclone_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + ("\n" if not body.endswith("\n") else ""), encoding="utf-8")
    try:
        path.chmod(0o600)
    except Exception:
        pass
    return rclone_status()


def disconnect_gdrive(*, remote_name: str = "gdrive") -> dict:
    rclone = shutil.which("rclone")
    name = (remote_name or "gdrive").strip().rstrip(":") or "gdrive"
    if rclone:
        subprocess.run(
            [rclone, "config", "delete", name],
            capture_output=True,
            text=True,
            timeout=30,
            env=_rclone_env(),
            creationflags=winproc.no_window(),
        )
    return rclone_status()


def authorize_start(*, remote_name: str = "gdrive") -> dict:
    """Chạy rclone authorize trên máy Javis (localhost). Trả auth_url để mở trình duyệt."""
    rclone = shutil.which("rclone")
    if not rclone:
        return {
            "ok": False,
            "error": "Chưa cài rclone trên máy chạy Javis. Image Docker từ 0.55.154 có sẵn rclone.",
        }
    with _AUTH_LOCK:
        _auth_cleanup_locked()
        # Huỷ session pending cũ
        for sid, sess in list(_AUTH_SESSIONS.items()):
            if sess.get("status") == "pending":
                proc = sess.get("proc")
                if proc and proc.poll() is None:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                _AUTH_SESSIONS.pop(sid, None)

        session_id = uuid.uuid4().hex[:12]
        try:
            proc = subprocess.Popen(
                [rclone, "authorize", "drive", "--auth-no-open-browser"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=_rclone_env(),
                creationflags=winproc.no_window(),
            )
        except Exception as e:
            return {"ok": False, "error": f"Không chạy được rclone authorize: {e}"}

        sess: dict[str, Any] = {
            "id": session_id,
            "proc": proc,
            "log": [],
            "auth_url": None,
            "status": "pending",
            "error": "",
            "remote_name": (remote_name or "gdrive").strip().rstrip(":") or "gdrive",
            "started_at": time.time(),
        }
        _AUTH_SESSIONS[session_id] = sess

    def _reader() -> None:
        buf: list[str] = []
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                buf.append(line)
                with _AUTH_LOCK:
                    sess["log"].append(line)
                    if not sess.get("auth_url"):
                        m = re.search(r"https://accounts\.google\.com\S+", line)
                        if not m:
                            m = re.search(r"https://\S*google\S+/o/oauth2\S+", line)
                        if m:
                            sess["auth_url"] = m.group(0).rstrip(").,\"'")
        except Exception:
            pass
        try:
            proc.wait(timeout=30)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        with _AUTH_LOCK:
            full = "".join(sess.get("log") or []) or "".join(buf)
        token = _extract_token_json(full)
        with _AUTH_LOCK:
            if token:
                try:
                    save_gdrive_token(token, remote_name=str(sess.get("remote_name") or "gdrive"))
                    sess["status"] = "done"
                    sess["error"] = ""
                except Exception as e:
                    sess["status"] = "error"
                    sess["error"] = str(e)
            elif sess.get("status") == "pending":
                code = proc.poll()
                sess["status"] = "error"
                sess["error"] = (
                    "Không nhận được token. Nếu Javis chạy trên VPS, "
                    "dùng «Dán token» hoặc upload rclone.conf thay vì đăng nhập tự động."
                    + (f" (exit {code})" if code not in (None, 0) else "")
                )

    threading.Thread(target=_reader, daemon=True, name=f"rclone-auth-{session_id}").start()

    # Chờ URL xuất hiện vài giây
    auth_url = None
    for _ in range(40):
        with _AUTH_LOCK:
            auth_url = sess.get("auth_url")
            if auth_url or sess.get("status") != "pending":
                break
        time.sleep(0.15)

    with _AUTH_LOCK:
        return {
            "ok": True,
            "session_id": session_id,
            "auth_url": sess.get("auth_url"),
            "status": sess.get("status"),
            "error": sess.get("error") or "",
            "hint": (
                "Chỉ dùng khi trình duyệt mở trên CÙNG máy chạy Javis (localhost). "
                "VPS: hãy dán token hoặc upload rclone.conf."
            ),
        }


def authorize_poll(session_id: str) -> dict:
    sid = (session_id or "").strip()
    with _AUTH_LOCK:
        _auth_cleanup_locked()
        sess = _AUTH_SESSIONS.get(sid)
        if not sess:
            return {"ok": False, "status": "error", "error": "Phiên đăng nhập hết hạn hoặc không tồn tại"}
        return {
            "ok": True,
            "session_id": sid,
            "status": sess.get("status") or "pending",
            "auth_url": sess.get("auth_url"),
            "error": sess.get("error") or "",
            "google_connected": bool(rclone_status().get("google_connected"))
            if sess.get("status") == "done"
            else False,
        }


# --- Pair: tải 1 file Mac/Windows → double-click → Allow Google → gửi về Javis (VPS) ---

_PAIR_LOCK = threading.Lock()
_PAIR_SESSIONS: dict[str, dict[str, Any]] = {}
_PAIR_TTL_SEC = 900


def _pair_cleanup_locked() -> None:
    now = time.time()
    for pid in [k for k, v in _PAIR_SESSIONS.items() if now - float(v.get("started_at") or 0) > _PAIR_TTL_SEC]:
        _PAIR_SESSIONS.pop(pid, None)


def pair_start(*, base_url: str) -> dict:
    """Tạo phiên kết nối từ máy Mac/Windows (tool tải về)."""
    base = (base_url or "").strip().rstrip("/")
    if not base.startswith("http"):
        raise ValueError("Thiếu địa chỉ Javis (base_url)")
    with _PAIR_LOCK:
        _pair_cleanup_locked()
        pair_id = uuid.uuid4().hex[:12]
        secret = secrets.token_urlsafe(18)
        _PAIR_SESSIONS[pair_id] = {
            "id": pair_id,
            "secret": secret,
            "status": "pending",
            "error": "",
            "started_at": time.time(),
            "base_url": base,
        }
    q = f"secret={secret}"
    return {
        "ok": True,
        "pair_id": pair_id,
        "secret": secret,
        "expires_in_sec": _PAIR_TTL_SEC,
        "mac_url": f"{base}/drive-projects/rclone/pair/{pair_id}/mac.command?{q}",
        "win_url": f"{base}/drive-projects/rclone/pair/{pair_id}/win.bat?{q}",
    }


def _pair_get(pair_id: str, secret: str) -> dict[str, Any] | None:
    with _PAIR_LOCK:
        _pair_cleanup_locked()
        sess = _PAIR_SESSIONS.get((pair_id or "").strip())
        if not sess:
            return None
        if not secrets.compare_digest(str(sess.get("secret") or ""), str(secret or "")):
            return None
        return sess


def pair_poll(pair_id: str) -> dict:
    with _PAIR_LOCK:
        _pair_cleanup_locked()
        sess = _PAIR_SESSIONS.get((pair_id or "").strip())
        if not sess:
            return {"ok": False, "status": "error", "error": "Phiên hết hạn — bấm kết nối lại"}
        return {
            "ok": True,
            "pair_id": pair_id,
            "status": sess.get("status") or "pending",
            "error": sess.get("error") or "",
            "google_connected": bool(rclone_status().get("google_connected"))
            if sess.get("status") == "done"
            else False,
        }


def pair_complete(pair_id: str, secret: str, token_raw: str) -> dict:
    sess = _pair_get(pair_id, secret)
    if not sess:
        raise ValueError("Mã kết nối sai hoặc hết hạn. Quay lại Javis bấm kết nối lại.")
    st = save_gdrive_token(token_raw)
    with _PAIR_LOCK:
        sess["status"] = "done"
        sess["error"] = ""
    return {"ok": True, "rclone": st, "google_connected": bool(st.get("google_connected"))}


def mac_pair_script(*, pair_id: str, secret: str, base_url: str) -> str:
    """Script .command: double-click trên Mac → đăng nhập Google → gửi về Javis."""
    base = base_url.rstrip("/")
    tpl = r'''#!/bin/bash
# Ket noi Google Drive -> Javis (double-click tren Mac)
set -euo pipefail
clear
echo "=========================================="
echo "  Ket noi Google Drive voi Javis"
echo "=========================================="
echo
JAVIS_URL="__BASE__"
PAIR_ID="__PAIR__"
SECRET="__SECRET__"
COMPLETE_URL="$JAVIS_URL/drive-projects/rclone/pair/$PAIR_ID/complete"

RCLONE=""
if command -v rclone >/dev/null 2>&1; then RCLONE="$(command -v rclone)"
elif [ -x "$HOME/.local/bin/rclone" ]; then RCLONE="$HOME/.local/bin/rclone"
fi
if [ -z "$RCLONE" ]; then
  echo "Dang tai rclone (mot lan)..."
  TMP=$(mktemp -d)
  (
    cd "$TMP"
    curl -fsSL -A "Mozilla/5.0" -o gh.json https://api.github.com/repos/rclone/rclone/releases/latest
    ASSET=$(python3 - <<'PY2'
import json, platform
d = json.load(open("gh.json"))
want = "osx-arm64" if platform.machine() == "arm64" else "osx-amd64"
print(next(a["browser_download_url"] for a in d["assets"] if want in a["name"] and a["name"].endswith(".zip")))
PY2
)
    curl -fsSL -L -A "Mozilla/5.0" -o rclone.zip "$ASSET"
    unzip -qo rclone.zip
  )
  BIN=$(find "$TMP" -type f -name rclone | head -1)
  mkdir -p "$HOME/.local/bin"
  cp "$BIN" "$HOME/.local/bin/rclone"
  chmod +x "$HOME/.local/bin/rclone"
  RCLONE="$HOME/.local/bin/rclone"
  rm -rf "$TMP"
fi

echo "1) Mo trinh duyet dang nhap Google"
echo "2) Bam Allow"
echo
CONF=$(mktemp)
LOG=$(mktemp)
export RCLONE_CONFIG="$CONF"
"$RCLONE" authorize "drive" --auth-no-open-browser >"$LOG" 2>&1 &
PID=$!
for i in 1 2 3 4 5 6 7 8 9 10; do
  URL=$(python3 -c "import re; t=open('$LOG').read(); m=re.search(r'https://\\S+', t); print(m.group(0) if m else '')")
  if [ -n "$URL" ]; then open "$URL" 2>/dev/null || true; echo "Da mo dang nhap Google."; break; fi
  sleep 1
done
echo "Dang cho ban Allow..."
for i in $(seq 1 90); do
  if ! kill -0 "$PID" 2>/dev/null; then break; fi
  sleep 2
done
wait "$PID" 2>/dev/null || true

TOKEN=$(LOGFILE="$LOG" python3 - <<'PY2'
import json, os, sys
t = open(os.environ["LOGFILE"]).read()
idx = t.find('"access_token"')
if idx < 0:
    sys.stderr.write("Khong thay token. Chay lai file nay.\n")
    sys.exit(1)
start = t.rfind("{", 0, idx)
depth = 0
end = None
for i in range(start, len(t)):
    if t[i] == "{":
        depth += 1
    elif t[i] == "}":
        depth -= 1
        if depth == 0:
            end = i
            break
if end is None:
    sys.exit(1)
json.loads(t[start:end+1])
print(t[start:end+1])
PY2
)
rm -f "$CONF" "$LOG"

echo "Dang gui ve Javis..."
BODY=$(SECRET="$SECRET" TOKEN="$TOKEN" python3 -c 'import json,os; print(json.dumps({"secret":os.environ["SECRET"],"token":os.environ["TOKEN"]}))')
HTTP=$(curl -sS -o /tmp/javis-drive-pair.json -w "%{http_code}" -X POST "$COMPLETE_URL" \
  -H "Content-Type: application/json" \
  -d "$BODY")
echo "HTTP $HTTP"
python3 - <<'PY2'
import json
d = json.load(open("/tmp/javis-drive-pair.json"))
if d.get("ok"):
    print("OK — quay lai Javis, trang Kho Drive (F5 neu can).")
else:
    print(d.get("error") or d)
    raise SystemExit(1)
PY2
echo
read -r -p "Nhan Enter de dong..."
'''
    return (
        tpl.replace("__BASE__", base.replace('"', ""))
        .replace("__PAIR__", pair_id.replace('"', ""))
        .replace("__SECRET__", secret.replace('"', ""))
    )


def win_pair_script(*, pair_id: str, secret: str, base_url: str) -> str:
    """Script .bat: double-click trên Windows → đăng nhập Google → gửi về Javis."""
    base = base_url.rstrip("/")
    tpl = r'''@echo off
chcp 65001 >nul
title Ket noi Google Drive - Javis
echo ==========================================
echo   Ket noi Google Drive voi Javis
echo ==========================================
echo.
set "JAVIS_URL=__BASE__"
set "PAIR_ID=__PAIR__"
set "SECRET=__SECRET__"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ErrorActionPreference='Stop'; ^
$javis=$env:JAVIS_URL.TrimEnd('/'); $pair=$env:PAIR_ID; $secret=$env:SECRET; ^
$rclone=(Get-Command rclone -ErrorAction SilentlyContinue).Source; ^
if(-not $rclone){ ^
  Write-Host 'Dang tai rclone...'; ^
  $dir=Join-Path $env:TEMP 'javis-rclone'; New-Item -ItemType Directory -Force -Path $dir|Out-Null; ^
  $zip=Join-Path $dir 'rclone.zip'; ^
  $rel=Invoke-RestMethod https://api.github.com/repos/rclone/rclone/releases/latest; ^
  $asset=$rel.assets | Where-Object { $_.name -match 'windows-amd64.zip$' } | Select-Object -First 1; ^
  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip; ^
  Expand-Archive -Path $zip -DestinationPath $dir -Force; ^
  $rclone=(Get-ChildItem -Path $dir -Recurse -Filter rclone.exe | Select-Object -First 1).FullName; ^
}; ^
Write-Host '1) Mo trinh duyet dang nhap Google'; Write-Host '2) Bam Allow'; ^
$conf=Join-Path $env:TEMP ('rclone-javis-'+[guid]::NewGuid()+'.conf'); ^
$env:RCLONE_CONFIG=$conf; ^
$log=Join-Path $env:TEMP ('rclone-auth-'+[guid]::NewGuid()+'.log'); ^
$p=Start-Process -FilePath $rclone -ArgumentList @('authorize','drive','--auth-no-open-browser') -RedirectStandardOutput $log -RedirectStandardError $log -PassThru -WindowStyle Hidden; ^
Start-Sleep 2; ^
for($i=0;$i -lt 15;$i++){ Start-Sleep 1; if(Test-Path $log){ $txt=Get-Content -Raw $log; if($txt -match 'https://\S+'){ Start-Process $Matches[0]; break } } }; ^
Write-Host 'Dang cho ban Allow...'; ^
Wait-Process -Id $p.Id -Timeout 180 -ErrorAction SilentlyContinue; Start-Sleep 1; ^
$txt=Get-Content -Raw $log; ^
$idx=$txt.IndexOf('"access_token"'); if($idx -lt 0){ throw 'Khong thay token. Chay lai.' }; ^
$start=$txt.LastIndexOf('{',$idx); $depth=0; $end=-1; ^
for($i=$start;$i -lt $txt.Length;$i++){ if($txt[$i] -eq '{'){$depth++} elseif($txt[$i] -eq '}'){ $depth--; if($depth -eq 0){$end=$i; break} } }; ^
$token=$txt.Substring($start,$end-$start+1); ^
$body=@{secret=$secret; token=$token} | ConvertTo-Json -Compress; ^
$resp=Invoke-RestMethod -Method Post -Uri ($javis+'/drive-projects/rclone/pair/'+$pair+'/complete') -ContentType 'application/json; charset=utf-8' -Body $body; ^
if($resp.ok){ Write-Host 'OK - quay lai Javis, trang Kho Drive.' } else { throw ($resp.error) }; ^
Remove-Item $conf,$log -ErrorAction SilentlyContinue"
echo.
pause
'''
    return (
        tpl.replace("__BASE__", base.replace('"', ""))
        .replace("__PAIR__", pair_id.replace('"', ""))
        .replace("__SECRET__", secret.replace('"', ""))
    )


def status_payload(brain: str | None = None) -> dict:
    rs = rclone_status()
    projects = list_projects(brain)
    connected = bool(rs.get("google_connected"))
    return {
        "ok": True,
        "rclone": rs,
        "projects": projects,
        "corpus_root": str(cfgmod.STATE_DIR / "drive-corpus"),
        "google_connected": connected,
        "hint": (
            "Bấm «Kết nối Google Drive»."
            if not connected
            else "Đã kết nối. Tạo kho bằng tên + link thư mục Drive."
        ),
    }


def _ensure_sources_scaffold(item: dict) -> Path:
    dest = sources_dir(item)
    dest.mkdir(parents=True, exist_ok=True)
    readme = dest / "README.md"
    if not readme.is_file():
        readme.write_text(
            _readme_body(item, mirrored=[], stubs=[], note="Chưa sync. Bấm Đồng bộ trên trang Kho Drive."),
            encoding="utf-8",
        )
    return dest


def _readme_body(item: dict, *, mirrored: list, stubs: list, note: str = "") -> str:
    lines = [
        f"# Kho Drive: {item.get('name') or item.get('slug')}",
        "",
        f"- Slug: `{item.get('slug')}`",
        f"- Folder ID: `{item.get('drive_folder_id')}`",
        f"- Remote: `{item.get('rclone_remote')}`",
        f"- Corpus (nhị phân): `{corpus_dir(item)}`",
        f"- Sources: `sources/drive/{item.get('slug')}/`",
        "",
        "## Cách dùng",
        "",
        "1. Đồng bộ từ trang **Kho Drive** (hoặc API sync).",
        "2. Mở Dự án chat gắn kho này.",
        "3. Bảo Javis: *ingest-source file …* rồi *viết skill từ wiki*.",
        "",
        "Không mass-ingest cả kho trong một lượt. Chọn file quan trọng.",
        "",
    ]
    if note:
        lines += ["## Trạng thái", "", note, ""]
    if mirrored:
        lines += ["## File text đã mirror", ""]
        for p in mirrored[:200]:
            lines.append(f"- `{p}`")
        lines.append("")
    if stubs:
        lines += ["## Tài liệu chờ extract (PDF/DOCX…)", ""]
        for p in stubs[:200]:
            lines.append(f"- `{p}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def _ensure_chat_project(item: dict) -> str:
    """Tạo/cập nhật Dự án hội thoại gắn kho; pin README. Trả chat_project_id."""
    if not _sessions_fn:
        return str(item.get("chat_project_id") or "")
    store = _sessions_fn()
    name = f"Kho Drive · {item.get('name') or item.get('slug')}"
    instructions = (
        f"Đây là Dự án Kho Drive «{item.get('name')}».\n"
        f"Nguồn làm việc: sources/drive/{item.get('slug')}/ (README + file đã mirror).\n"
        f"Corpus nhị phân (PDF gốc) nằm ngoài brain: drive-corpus — không sửa tay.\n"
        f"Folder Drive ID: {item.get('drive_folder_id')}.\n"
        "Khi user muốn học/tri thức: đọc sources đã mirror, dùng ingest-source cho file quan trọng, "
        "rồi viết skill. Không bịa nội dung không có trong kho. Không em dash."
    )
    pid = (item.get("chat_project_id") or "").strip()
    if pid and store.get_project(pid):
        store.update_project(pid, name=name, icon="hard-drive", instructions=instructions)
    else:
        pid = store.create_project(name, icon="hard-drive", brain=item.get("brain") or "brain")
        store.update_project(pid, instructions=instructions)
    rel = f"sources/drive/{item.get('slug')}/README.md"
    fid = store.add_project_file(pid, rel, name="README.md")
    if fid:
        try:
            store.set_project_file_pinned(pid, fid, True)
        except Exception:
            pass
    return pid


def _extract_pdf_text(path: Path, limit: int = 12000) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return ""
    try:
        reader = PdfReader(str(path))
        chunks = []
        n = 0
        for page in reader.pages[:40]:
            t = page.extract_text() or ""
            if not t.strip():
                continue
            chunks.append(t)
            n += len(t)
            if n >= limit:
                break
        return "\n\n".join(chunks)[:limit]
    except Exception:
        return ""


def mirror_corpus_to_sources(item: dict) -> dict:
    """Copy text + stub/extract docs từ corpus → sources/drive/<slug>/."""
    corpus = corpus_dir(item)
    dest = _ensure_sources_scaffold(item)
    mirrored: list[str] = []
    stubs: list[str] = []
    if not corpus.is_dir():
        (dest / "README.md").write_text(
            _readme_body(item, mirrored=[], stubs=[], note="Corpus trống — rclone chưa kéo được file."),
            encoding="utf-8",
        )
        return {"mirrored": 0, "stubs": 0, "files": []}

    for src in corpus.rglob("*"):
        if not src.is_file():
            continue
        if src.name.lower() in _SKIP_NAMES:
            continue
        try:
            rel = src.relative_to(corpus)
        except ValueError:
            continue
        rel_s = str(rel).replace("\\", "/")
        ext = src.suffix.lower()
        if ext in _TEXT_EXT:
            out = dest / rel
            if ext == ".txt":
                out = out.with_suffix(".md")
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                text = src.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if not text.lstrip().startswith("---"):
                fm = (
                    f"---\ntype: source\ndrive_slug: {item.get('slug')}\n"
                    f"corpus_rel: {rel_s}\nupdated: {time.strftime('%Y-%m-%d')}\n---\n\n"
                )
                text = fm + text
            out.write_text(text, encoding="utf-8")
            mirrored.append(str(out.relative_to(dest)).replace("\\", "/"))
        elif ext in _DOC_EXT:
            stub_name = rel.with_suffix(".md")
            out = dest / stub_name
            out.parent.mkdir(parents=True, exist_ok=True)
            body = ""
            status = "pending_extract"
            if ext == ".pdf":
                body = _extract_pdf_text(src)
                if body.strip():
                    status = "extracted"
            fm = (
                f"---\ntype: source\ndrive_slug: {item.get('slug')}\n"
                f"corpus_rel: {rel_s}\nstatus: {status}\n"
                f"updated: {time.strftime('%Y-%m-%d')}\n---\n\n"
                f"# {src.name}\n\n"
                f"Bản gốc trong corpus: `{corpus / rel}`\n\n"
            )
            if body.strip():
                fm += "## Nội dung đã extract\n\n" + body + "\n"
            else:
                fm += (
                    "_Chưa extract được text (cần mở PDF thủ công hoặc cài pypdf). "
                    "Dùng ingest-source sau khi có .md đầy đủ._\n"
                )
            out.write_text(fm, encoding="utf-8")
            stubs.append(str(out.relative_to(dest)).replace("\\", "/"))

    note = (
        f"Sync mirror xong: {len(mirrored)} text, {len(stubs)} tài liệu. "
        f"Lúc: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    (dest / "README.md").write_text(
        _readme_body(item, mirrored=mirrored, stubs=stubs, note=note),
        encoding="utf-8",
    )
    return {
        "mirrored": len(mirrored),
        "stubs": len(stubs),
        "files": mirrored[:50] + stubs[:50],
        "sources_rel": f"sources/drive/{item.get('slug')}/",
    }


def run_rclone_sync(item: dict, *, timeout_sec: int = 600) -> dict:
    """Chạy rclone sync vào corpus. Trả {ok, log, error}."""
    if not shutil.which("rclone"):
        return {
            "ok": False,
            "error": "Chưa cài rclone trên máy chạy Javis. Xem docs/29-kho-drive.md",
        }
    dest = corpus_dir(item)
    dest.mkdir(parents=True, exist_ok=True)
    remote = item.get("rclone_remote") or "gdrive:"
    fid = item.get("drive_folder_id") or ""
    script = _script_path
    env = _rclone_env()
    if script and script.is_file():
        env["RCLONE_REMOTE"] = remote
        env["DRIVE_FOLDER_ID"] = fid
        env["DRIVE_SYNC_DIR"] = str(dest)
        try:
            r = subprocess.run(
                ["bash", str(script)],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=env,
                creationflags=winproc.no_window(),
            )
            log = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()[-4000:]
            if r.returncode != 0:
                return {"ok": False, "error": f"rclone exit {r.returncode}", "log": log}
            return {"ok": True, "log": log}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"rclone quá {timeout_sec}s"}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    # Inline fallback (tests / missing script)
    cmd = [
        "rclone",
        "sync",
        remote,
        str(dest),
        "--drive-root-folder-id",
        fid,
        "--create-empty-src-dirs",
        "--fast-list",
        "--transfers",
        "4",
        "--checkers",
        "8",
        "--exclude",
        ".DS_Store",
        "--exclude",
        "Thumbs.db",
        "-v",
    ]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
            creationflags=winproc.no_window(),
        )
        log = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()[-4000:]
        if r.returncode != 0:
            return {"ok": False, "error": f"rclone exit {r.returncode}", "log": log}
        return {"ok": True, "log": log}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def sync_project(pid: str) -> dict:
    item = get_project(pid)
    if not item:
        raise KeyError("not found")
    if not item.get("enabled", True):
        raise ValueError("Kho đang tắt (enabled=false)")

    rclone_res = run_rclone_sync(item)
    stats: dict[str, Any] = {}
    ok = bool(rclone_res.get("ok"))
    err = str(rclone_res.get("error") or "")
    if ok:
        stats = mirror_corpus_to_sources(item)
        chat_id = _ensure_chat_project(item)
        if chat_id:
            item["chat_project_id"] = chat_id

    with _LOCK:
        data = _load()
        for it in data["projects"]:
            if it.get("id") == pid:
                it["last_sync_at"] = time.time()
                it["last_sync_ok"] = ok
                it["last_sync_error"] = err if not ok else ""
                it["last_sync_stats"] = stats if ok else {}
                if item.get("chat_project_id"):
                    it["chat_project_id"] = item["chat_project_id"]
                it["updated_at"] = time.time()
                item = dict(it)
                break
        _save(data)

    return {
        "ok": ok,
        "project": item,
        "rclone": rclone_res,
        "stats": stats,
        "error": err if not ok else "",
    }
