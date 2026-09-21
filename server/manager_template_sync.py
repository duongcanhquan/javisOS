"""
manager_template_sync.py - Đồng bộ agents/workflows/skills từ Javis manager (gốc chuẩn)
sang Brain Default của các tenant.

Chính sách (giống tinh thần system_sync):
  - Thiếu trên tenant → cài từ manager
  - Có + hash khớp manifest (chưa sửa) → cập nhật bản manager mới
  - Có + hash lệch manifest hoặc lệch bản manager đã ghi → GIỮ nguyên (tenant đã sửa)
  - Skill đang ở skills/.disabled → không bật lại
  - Xóa trên manager → KHÔNG xóa trên tenant

Manifest: <brain>/.javis/manager-manifest.json
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

MANIFEST_REL = Path(".javis") / "manager-manifest.json"
TEMPLATE_SUBDIRS = ("agents", "workflows", "skills")
BRAIN_NAME = os.environ.get("JAVIS_TEMPLATE_BRAIN", "Brain Default")

_SKIP_DIR_NAMES = frozenset({
    "node_modules", ".git", "__pycache__", ".venv", "venv", ".tox", "dist", "build",
})
_SKIP_FILE_SUFFIXES = frozenset({
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".zip", ".tar", ".gz", ".tgz", ".7z",
    ".mp4", ".mov", ".webm", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf",
})

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _norm_text(text: str) -> str:
    t = (text or "").replace("\r\n", "\n").replace("\ufeff", "")
    t = _DATE_RE.sub("<DATE>", t)
    t = "\n".join(line.rstrip() for line in t.split("\n"))
    return t.strip() + "\n"


def content_hash(data: bytes) -> str:
    """Hash chuẩn hoá. Text UTF-8 → normalize; binary → hash raw."""
    try:
        text = data.decode("utf-8")
        return hashlib.sha256(_norm_text(text).encode("utf-8")).hexdigest()
    except UnicodeDecodeError:
        return hashlib.sha256(data).hexdigest()


def _should_skip_rel(rel: Path) -> bool:
    parts = rel.parts
    if any(p in _SKIP_DIR_NAMES for p in parts):
        return True
    if any(p.startswith(".") for p in parts):
        return True
    lower = rel.name.lower()
    for suf in _SKIP_FILE_SUFFIXES:
        if lower.endswith(suf):
            return True
    return False


def iter_template_files(root: Path) -> Iterable[tuple[str, Path, bytes]]:
    """Yield (manifest_key, abs_path, bytes) cho agents/workflows/skills dưới root."""
    root = Path(root)
    for sub in TEMPLATE_SUBDIRS:
        base = root / sub
        if not base.is_dir():
            continue
        if sub in ("agents", "workflows"):
            for f in sorted(base.glob("*.md")):
                if f.name.startswith(".") or " 2." in f.name:
                    continue
                key = f"{sub}/{f.stem}"
                yield key, f, f.read_bytes()
            continue
        for slug_dir in sorted(
            p for p in base.iterdir()
            if p.is_dir() and p.name != ".disabled" and not p.name.startswith(".")
        ):
            if not (slug_dir / "SKILL.md").is_file():
                continue
            for f in sorted(x for x in slug_dir.rglob("*") if x.is_file()):
                rel = f.relative_to(slug_dir)
                if _should_skip_rel(rel):
                    continue
                if rel.as_posix() == "SKILL.md":
                    key = f"skills/{slug_dir.name}"
                else:
                    key = f"skills/{slug_dir.name}/{rel.as_posix()}"
                yield key, f, f.read_bytes()


def _dest_path(root: Path, key: str) -> Path:
    if key.startswith("skills/"):
        rest = key[len("skills/"):]
        slug, _, rel = rest.partition("/")
        if rel:
            return root / "skills" / slug / rel
        return root / "skills" / slug / "SKILL.md"
    if key.startswith("agents/"):
        return root / "agents" / f"{key.split('/', 1)[1]}.md"
    if key.startswith("workflows/"):
        return root / "workflows" / f"{key.split('/', 1)[1]}.md"
    raise ValueError(f"unknown key: {key}")


def _skill_disabled(root: Path, key: str) -> bool:
    if not key.startswith("skills/"):
        return False
    slug = key.split("/")[1]
    return (root / "skills" / ".disabled" / slug).is_dir()


def _read_manifest(root: Path) -> dict:
    p = root / MANIFEST_REL
    try:
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("files", {})
                return data
    except Exception:
        pass
    return {"files": {}}


def _write_manifest(root: Path, data: dict) -> None:
    data["synced_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    path = root / MANIFEST_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def sync_brain(
    src_root: Path,
    dst_root: Path,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Đồng bộ template từ src Brain Default → dst Brain Default.

    force=True: ghi đè mọi file (promote vào manager).
    """
    src_root = Path(src_root)
    dst_root = Path(dst_root)
    stats: dict[str, Any] = {
        "installed": 0,
        "updated": 0,
        "skipped_user": 0,
        "skipped_disabled": 0,
        "skipped_same": 0,
        "errors": [],
        "keys": [],
    }
    if not src_root.is_dir():
        stats["errors"].append(f"src missing: {src_root}")
        return stats

    manifest = _read_manifest(dst_root)
    files_meta: dict = manifest.setdefault("files", {})
    new_files: dict = dict(files_meta)

    for key, _src_path, data in iter_template_files(src_root):
        src_hash = content_hash(data)
        dest = _dest_path(dst_root, key)
        try:
            if _skill_disabled(dst_root, key) and not force:
                stats["skipped_disabled"] += 1
                continue

            prev = files_meta.get(key) or {}
            prev_hash = (prev.get("hash") if isinstance(prev, dict) else None) or ""
            rel_path = key if key.startswith("skills/") and "/" in key[7:] else (
                str(_dest_path(Path("."), key)).replace("\\", "/")
            )
            # Prefer concrete relative path under brain
            try:
                rel_path = str(dest.relative_to(dst_root)).replace("\\", "/")
            except ValueError:
                pass

            if dest.is_file() and not force:
                cur = content_hash(dest.read_bytes())
                if cur == src_hash:
                    new_files[key] = {"hash": src_hash, "path": rel_path}
                    stats["skipped_same"] += 1
                    continue
                if prev_hash and cur != prev_hash:
                    stats["skipped_user"] += 1
                    continue
                if not prev_hash and cur != src_hash:
                    stats["skipped_user"] += 1
                    continue
                if not dry_run:
                    _atomic_write_bytes(dest, data)
                new_files[key] = {"hash": src_hash, "path": rel_path}
                stats["updated"] += 1
                stats["keys"].append(key)
                continue

            existed = dest.is_file()
            if not dry_run:
                _atomic_write_bytes(dest, data)
            new_files[key] = {"hash": src_hash, "path": rel_path}
            if force and existed:
                stats["updated"] += 1
            else:
                stats["installed"] += 1
            stats["keys"].append(key)
        except Exception as e:
            stats["errors"].append(f"{key}: {type(e).__name__}: {e}")

    if not dry_run:
        manifest["files"] = new_files
        manifest["source"] = "javis-manager"
        _write_manifest(dst_root, manifest)
        try:
            _mirror_skills_light(dst_root)
        except Exception as e:
            stats["errors"].append(f"mirror: {type(e).__name__}: {e}")

    return stats


def _mirror_skills_light(root: Path) -> None:
    src = root / "skills"
    dst = root / ".claude" / "skills"
    if not src.is_dir():
        return
    for slug_dir in src.iterdir():
        if not slug_dir.is_dir() or slug_dir.name.startswith(".") or slug_dir.name == ".disabled":
            continue
        if not (slug_dir / "SKILL.md").is_file():
            continue
        out = dst / slug_dir.name
        out.mkdir(parents=True, exist_ok=True)
        for f in slug_dir.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(slug_dir)
            if _should_skip_rel(rel):
                continue
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(f), str(target))


def pack_template_tgz(src_root: Path, out_tgz: Path) -> int:
    src_root = Path(src_root)
    out_tgz = Path(out_tgz)
    out_tgz.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with tarfile.open(out_tgz, "w:gz") as tar:
        for _key, path, _data in iter_template_files(src_root):
            arc = path.relative_to(src_root).as_posix()
            tar.add(str(path), arcname=arc)
            n += 1
        man = src_root / MANIFEST_REL
        if man.is_file():
            tar.add(str(man), arcname=MANIFEST_REL.as_posix())
    return n


def promote(src_root: Path, dst_root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    return sync_brain(src_root, dst_root, dry_run=dry_run, force=True)


def _docker_bin() -> str:
    return os.environ.get("DOCKER_BIN", "docker")


def docker_ok() -> bool:
    import subprocess
    try:
        r = subprocess.run(
            [_docker_bin(), "version", "--format", "{{.Server.Version}}"],
            capture_output=True, text=True, timeout=15,
        )
        return r.returncode == 0
    except Exception:
        return False


def list_javis_containers(*, exclude: Optional[set[str]] = None) -> list[str]:
    import subprocess
    exclude = exclude or set()
    r = subprocess.run(
        [_docker_bin(), "ps", "--format", "{{.Names}}"],
        capture_output=True, text=True, timeout=30, check=True,
    )
    names = []
    for line in r.stdout.splitlines():
        n = line.strip()
        if not n.startswith("javis-"):
            continue
        if n in exclude or n == "javis-proxy" or "proxy" in n:
            continue
        names.append(n)
    return sorted(names)


def docker_exec(container: str, args: list[str], *, timeout: int = 300) -> tuple[int, str]:
    import subprocess
    r = subprocess.run(
        [_docker_bin(), "exec", container, *args],
        capture_output=True, text=True, timeout=timeout,
    )
    out = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
    return r.returncode, out


def _docker_cp(src: str, dst: str, timeout: int = 300) -> int:
    import subprocess
    r = subprocess.run(
        [_docker_bin(), "cp", src, dst],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.returncode


def sync_via_docker(
    *,
    manager: str = "javis-manager",
    brain: str = BRAIN_NAME,
    dry_run: bool = False,
    tenants: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Pack template từ manager, apply vào từng tenant qua docker cp."""
    if not docker_ok():
        return {"ok": False, "error": "docker không dùng được trên máy này"}

    targets = tenants or [
        n for n in list_javis_containers(exclude={manager, "javis-proxy"}) if n != manager
    ]
    report: dict[str, Any] = {
        "ok": True, "manager": manager, "brain": brain, "tenants": {}, "dry_run": dry_run,
    }

    with tempfile.TemporaryDirectory(prefix="javis-mgr-sync-") as td:
        td_path = Path(td)
        tgz = td_path / "template.tgz"
        code, out = docker_exec(
            manager,
            [
                "python", "-c",
                "import sys; sys.path.insert(0,'/app/server'); "
                "from pathlib import Path; import manager_template_sync as m; "
                f"print(m.pack_template_tgz(Path('/brains/{brain}'), "
                "Path('/tmp/javis-manager-template.tgz')))",
            ],
            timeout=180,
        )
        if code != 0:
            code2, out2 = docker_exec(
                manager,
                [
                    "sh", "-c",
                    f'cd "/brains/{brain}" && tar -czf /tmp/javis-manager-template.tgz '
                    "agents workflows skills 2>/dev/null; "
                    "ls -la /tmp/javis-manager-template.tgz",
                ],
                timeout=180,
            )
            if code2 != 0:
                report["ok"] = False
                report["error"] = f"pack failed: {out}\n{out2}"
                return report

        if _docker_cp(f"{manager}:/tmp/javis-manager-template.tgz", str(tgz)) != 0:
            report["ok"] = False
            report["error"] = "docker cp template failed"
            return report

        src_unpacked = td_path / "src"
        src_unpacked.mkdir()
        with tarfile.open(tgz, "r:gz") as tar:
            tar.extractall(src_unpacked)

        for name in targets:
            try:
                t_root = td_path / f"dst-{name}"
                t_root.mkdir()
                for sub in (*TEMPLATE_SUBDIRS, ".javis"):
                    _docker_cp(f"{name}:/brains/{brain}/{sub}", str(t_root / sub))
                t_stats = sync_brain(src_unpacked, t_root, dry_run=dry_run, force=False)
                if not dry_run:
                    for sub in TEMPLATE_SUBDIRS:
                        local_sub = t_root / sub
                        if not local_sub.exists():
                            continue
                        docker_exec(name, ["mkdir", "-p", f"/brains/{brain}/{sub}"], timeout=30)
                        _docker_cp(f"{local_sub}/.", f"{name}:/brains/{brain}/{sub}/")
                    javis_dir = t_root / ".javis"
                    if javis_dir.exists():
                        docker_exec(name, ["mkdir", "-p", f"/brains/{brain}/.javis"], timeout=30)
                        _docker_cp(f"{javis_dir}/.", f"{name}:/brains/{brain}/.javis/")
                    docker_exec(
                        name,
                        [
                            "python", "-c",
                            "import sys; sys.path.insert(0,'/app/server');\n"
                            "from pathlib import Path\n"
                            "try:\n"
                            " import manager_template_sync as m\n"
                            f" m._mirror_skills_light(Path('/brains/{brain}'))\n"
                            "except Exception as e:\n"
                            " print('mirror skip', e)\n",
                        ],
                        timeout=60,
                    )
                report["tenants"][name] = t_stats
            except Exception as e:
                report["tenants"][name] = {"errors": [f"{type(e).__name__}: {e}"]}
                report["ok"] = False

    return report


def promote_via_docker(
    *,
    source: str = "javis-quan",
    manager: str = "javis-manager",
    brain: str = BRAIN_NAME,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Copy agents/workflows/skills từ source → manager (force)."""
    if not docker_ok():
        return {"ok": False, "error": "docker không dùng được"}

    with tempfile.TemporaryDirectory(prefix="javis-mgr-promote-") as td:
        td_path = Path(td)
        src = td_path / "src"
        dst = td_path / "dst"
        src.mkdir()
        dst.mkdir()
        for sub in TEMPLATE_SUBDIRS:
            _docker_cp(f"{source}:/brains/{brain}/{sub}", str(src / sub))
            _docker_cp(f"{manager}:/brains/{brain}/{sub}", str(dst / sub))
        stats = promote(src, dst, dry_run=dry_run)
        if not dry_run:
            for sub in TEMPLATE_SUBDIRS:
                local_sub = dst / sub
                if not local_sub.exists():
                    continue
                docker_exec(manager, ["mkdir", "-p", f"/brains/{brain}/{sub}"], timeout=30)
                _docker_cp(f"{local_sub}/.", f"{manager}:/brains/{brain}/{sub}/")
            javis_dir = dst / ".javis"
            if javis_dir.exists():
                docker_exec(manager, ["mkdir", "-p", f"/brains/{brain}/.javis"], timeout=30)
                _docker_cp(f"{javis_dir}/.", f"{manager}:/brains/{brain}/.javis/")
            docker_exec(
                manager,
                [
                    "python", "-c",
                    "import sys; sys.path.insert(0,'/app/server');\n"
                    "from pathlib import Path\n"
                    "try:\n"
                    " import manager_template_sync as m\n"
                    f" m._mirror_skills_light(Path('/brains/{brain}'))\n"
                    "except Exception as e:\n"
                    " print('mirror skip', e)\n",
                ],
                timeout=60,
            )
        return {"ok": not bool(stats.get("errors")), "stats": stats, "source": source, "manager": manager}


def is_manager_role() -> bool:
    role = (os.environ.get("JAVIS_ROLE") or "").strip().lower()
    if role == "manager":
        return True
    flag = (os.environ.get("JAVIS_TEMPLATE_SOURCE") or "").strip().lower()
    return flag in ("1", "true", "yes", "on")


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Sync Javis manager template → tenants")
    p.add_argument("--promote-from", metavar="CONTAINER", help="Promote template vào manager")
    p.add_argument("--manager", default=os.environ.get("JAVIS_MANAGER_NAME", "javis-manager"))
    p.add_argument("--brain", default=BRAIN_NAME)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sync", action="store_true", help="Sync manager → mọi tenant")
    p.add_argument("--tenant", action="append", default=[], help="Chỉ sync tenant này")
    p.add_argument("--src", type=Path, help="path→path: nguồn Brain Default")
    p.add_argument("--dst", type=Path, help="path→path: đích Brain Default")
    p.add_argument("--force", action="store_true", help="Ghi đè (path mode)")
    args = p.parse_args(argv)

    if args.src and args.dst:
        fn = promote if args.force else sync_brain
        stats = fn(args.src, args.dst, dry_run=args.dry_run)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0 if not stats.get("errors") else 1

    if args.promote_from:
        report = promote_via_docker(
            source=args.promote_from, manager=args.manager, brain=args.brain, dry_run=args.dry_run,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("ok") else 1

    if args.sync:
        report = sync_via_docker(
            manager=args.manager, brain=args.brain, dry_run=args.dry_run,
            tenants=args.tenant or None,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("ok") else 1

    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
