"""Kho tri thức Google Drive: sync rclone → corpus → mirror sources/drive/<slug>/.

Lưu registry tại STATE_DIR/drive_projects.json (sống qua update Docker).
Corpus nhị phân: STATE_DIR/drive-corpus/<brain-safe>/<slug>/
Brain làm việc: <brain>/sources/drive/<slug>/
"""
from __future__ import annotations

import json
import os
import re
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
    fid = (drive_folder_id or "").strip()
    if not _folder_id_ok(fid):
        raise ValueError("drive_folder_id không hợp lệ (lấy từ URL thư mục Drive)")
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
            fid = str(patch["drive_folder_id"]).strip()
            if not _folder_id_ok(fid):
                raise ValueError("drive_folder_id không hợp lệ")
            found["drive_folder_id"] = fid
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


def rclone_status() -> dict:
    rclone = shutil.which("rclone")
    conf = cfgmod.STATE_DIR / "rclone.conf"
    out = {
        "rclone_installed": bool(rclone),
        "rclone_path": rclone or "",
        "rclone_config": str(conf),
        "remotes": [],
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
    return out


def status_payload(brain: str | None = None) -> dict:
    rs = rclone_status()
    projects = list_projects(brain)
    return {
        "ok": True,
        "rclone": rs,
        "projects": projects,
        "corpus_root": str(cfgmod.STATE_DIR / "drive-corpus"),
        "hint": (
            "Cần rclone + remote Google Drive trên máy/VPS chạy Javis. "
            "Xem docs/29-kho-drive.md hoặc scripts/setup-rclone-drive-vps.sh"
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
