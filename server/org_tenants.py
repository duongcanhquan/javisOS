"""Sổ Javis con (tenant) trên Javis gốc. Chỉ dùng khi JAVIS_ORG_MANAGER=true."""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path

import config as cfgmod

PROTECTED_SLUGS = frozenset({
    "quan", "manager", "proxy", "caddy", "web", "javis", "www", "mail", "ns",
})
PROTECTED_VOLUMES = frozenset({
    "javis_javis-data", "javis_javis-brains", "javis_claude-auth", "javis_codex-auth",
})
# Xóa mềm: giữ volume, tự xóa hẳn sau 72 giờ (tinh thần NĐ 13 / design Tổ chức).
SOFT_DELETE_SEC = 72 * 3600
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PREFIX_RE = re.compile(r"^[a-z][a-z0-9]{0,15}$")


def manager_enabled() -> bool:
    v = (os.getenv("JAVIS_ORG_MANAGER") or "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    name = (os.getenv("JAVIS_NAME") or "").strip().lower()
    if name == "javis-manager":
        return True
    domain = (os.getenv("DOMAIN_NAME") or "").strip().lower()
    return domain == "javis.vietmycollege.com"


def store_path() -> Path:
    return cfgmod.STATE_DIR / "org-tenants.json"


def domain_suffix() -> str:
    return (os.getenv("JAVIS_ORG_DOMAIN_SUFFIX") or "vietmycollege.com").strip().lower()


def host_prefix() -> str:
    v = (os.getenv("JAVIS_ORG_HOST_PREFIX") or "javis").strip().lower()
    if not _PREFIX_RE.match(v):
        return "javis"
    return v


def tenant_domain(slug: str) -> str:
    s = (slug or "").strip().lower()
    return f"{host_prefix()}-{s}.{domain_suffix()}"


def public_hosts(slug: str) -> list[str]:
    """Tên mở trên trình duyệt. Prefix mới (vd vmos) vẫn giữ alias javis- để link cũ vào được."""
    s = (slug or "").strip().lower()
    primary = tenant_domain(s)
    out = [primary]
    alt = f"javis-{s}.{domain_suffix()}"
    if alt not in out:
        out.append(alt)
    return out


def validate_slug(slug: str) -> str | None:
    s = (slug or "").strip().lower()
    if not s:
        return "Thiếu tên (slug)."
    if not _SLUG_RE.match(s) or len(s) > 32:
        return "Tên chỉ gồm a-z, 0-9 và gạch nối (vd lan, aiot-01)."
    if s in PROTECTED_SLUGS:
        return f"Tên '{s}' đã dành cho hệ thống."
    return None


def volume_names(slug: str) -> list[str]:
    prefix = f"javis-{slug}_"
    names = [
        f"{prefix}javis-data",
        f"{prefix}javis-brains",
        f"{prefix}claude-auth",
        f"{prefix}codex-auth",
    ]
    for n in names:
        if n in PROTECTED_VOLUMES:
            raise ValueError(f"Từ chối volume hệ thống: {n}")
    return names


def _empty() -> dict:
    return {"tenants": []}


def load() -> dict:
    """Đọc sổ. Lỗi JSON / thiếu file KHÔNG được ghi đè sổ cũ bằng chỉ quan.

    Trước đây parse lỗi → `_empty()` + `ensure_quan` + `save` → xóa sạch mọi tenant
    dù volume/container vẫn còn (sự cố 2026-09-22).
    """
    p = store_path()
    if not p.is_file():
        restored = _best_backup_doc()
        data = restored if restored is not None else _empty()
        if not isinstance(data.get("tenants"), list):
            data = _empty()
        ensure_quan(data)
        save(data)
        return data
    raw = ""
    try:
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        # Giữ nguyên file hỏng. Không chuyển file đi, không ghi đè bằng chỉ quan.
        bad = p.with_name(f"org-tenants.bad-{int(time.time())}.json")
        try:
            if raw and not bad.exists():
                bad.write_text(raw, encoding="utf-8")
        except Exception:
            pass
        print(f"[org-tenants] đọc lỗi ({type(e).__name__}: {e}); giữ sổ cũ; không ghi đè.", flush=True)
        data = _empty()
        ensure_quan(data)
        data["_do_not_save"] = True
        return data
    if not isinstance(data, dict):
        bad = p.with_name(f"org-tenants.bad-{int(time.time())}.json")
        try:
            bad.write_text(raw if raw else json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
        print("[org-tenants] sổ không phải object JSON; không ghi đè.", flush=True)
        data = _empty()
        ensure_quan(data)
        data["_do_not_save"] = True
        return data
    data.setdefault("tenants", [])
    if not isinstance(data["tenants"], list):
        print("[org-tenants] trường tenants không phải list; không ghi đè sổ.", flush=True)
        empty = _empty()
        ensure_quan(empty)
        empty["_do_not_save"] = True
        return empty
    changed = ensure_quan(data)
    if _sync_domains(data):
        changed = True
    if changed:
        save(data)
    return data


def _slugs(tenants: list) -> set[str]:
    out = set()
    for t in tenants:
        if not isinstance(t, dict):
            continue
        s = str(t.get("slug") or "").strip().lower()
        if s:
            out.add(s)
    return out


def save(data: dict, *, allow_drop: set[str] | None = None, allow_rebuild: bool = False) -> None:
    """Ghi sổ atomic. Không được làm mất slug đang có, trừ khi allow_drop nêu đúng tên xóa."""
    if isinstance(data, dict) and data.get("_do_not_save") and not allow_rebuild:
        raise RuntimeError("Sổ đọc lỗi, từ chối ghi để không xóa người.")
    p = store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    new_tenants = data.get("tenants") if isinstance(data, dict) else None
    if not isinstance(new_tenants, list):
        raise ValueError("org-tenants: tenants phải là list")
    if p.is_file():
        try:
            old = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(old, dict):
                raise ValueError("sổ cũ không phải object")
            if "tenants" not in old:
                old_tenants = []
            else:
                old_tenants = old.get("tenants")
                if not isinstance(old_tenants, list):
                    raise ValueError("tenants cũ không phải list")
        except Exception:
            if not allow_rebuild:
                raise RuntimeError(
                    "Sổ org-tenants hiện không đọc được, từ chối ghi đè. "
                    "Giữ file cũ để còn khôi phục."
                )
            bak = p.with_name(f"org-tenants.bad-{int(time.time())}.json")
            try:
                if not bak.exists():
                    bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass
            old_tenants = []
        dropped = _slugs(old_tenants) - _slugs(new_tenants)
        allowed = {str(s or "").strip().lower() for s in (allow_drop or set()) if str(s or "").strip()}
        extra = dropped - allowed
        if extra:
            bak = p.with_name(f"org-tenants.blocked-{int(time.time())}.json")
            try:
                bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass
            raise RuntimeError(
                f"Từ chối ghi org-tenants: sắp mất {', '.join(sorted(extra))}. "
                f"Đã giữ bản cũ tại {bak.name}."
            )
    clean = {k: v for k, v in data.items() if k != "_do_not_save"}
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def _sync_domains(data: dict) -> bool:
    changed = False
    for t in data.get("tenants") or []:
        slug = str(t.get("slug") or "")
        if not slug:
            continue
        want = tenant_domain(slug)
        if str(t.get("domain") or "") != want:
            t["domain"] = want
            changed = True
    return changed


def ensure_quan(data: dict) -> bool:
    tenants = data.setdefault("tenants", [])
    if any(str(t.get("slug") or "") == "quan" for t in tenants):
        return False
    tenants.insert(0, {
        "id": "quan",
        "slug": "quan",
        "name": "Javis Quan",
        "domain": tenant_domain("quan"),
        "container": "javis-quan",
        "volumes": sorted(PROTECTED_VOLUMES),
        "quota_gb": 0,
        "brain_mode": "both",
        "protected": True,
        "status": "unknown",
    })
    return True


_INFRA_SKIP = frozenset({"manager", "proxy", "park", "javis"})


def slugs_from_infra(container_names: list[str], volume_names_in: list[str]) -> list[str]:
    """Slug còn container javis-<slug> hoặc volume javis-<slug>_javis-brains."""
    found: set[str] = set()
    for raw in container_names:
        n = str(raw or "").strip().lstrip("/")
        if not n.startswith("javis-"):
            continue
        slug = n[len("javis-"):].strip().lower()
        if not slug or slug in _INFRA_SKIP or slug in PROTECTED_SLUGS or validate_slug(slug):
            continue
        found.add(slug)
    suffix = "_javis-brains"
    for raw in volume_names_in:
        v = str(raw or "").strip()
        if not (v.startswith("javis-") and v.endswith(suffix)):
            continue
        slug = v[len("javis-"):-len(suffix)].strip().lower()
        if not slug or slug in _INFRA_SKIP or slug in PROTECTED_SLUGS or validate_slug(slug):
            continue
        found.add(slug)
    return sorted(found)


def _backup_files() -> list[Path]:
    parent = store_path().parent
    return list(parent.glob("org-tenants.bad-*.json")) + list(parent.glob("org-tenants.blocked-*.json"))


def _best_backup_doc() -> dict | None:
    """Bản sao nhiều người nhất. Hòa nhau thì lấy file mới hơn."""
    best: dict | None = None
    best_key = (-1, -1.0)
    for f in _backup_files():
        try:
            parsed = json.loads(f.read_text(encoding="utf-8"))
            tenants = parsed.get("tenants") if isinstance(parsed, dict) else None
            if not isinstance(tenants, list) or not tenants:
                continue
            key = (len(_slugs(tenants)), f.stat().st_mtime)
            if key > best_key:
                best_key = key
                best = parsed
        except Exception:
            continue
    return best


def _backup_by_slug() -> dict[str, dict]:
    """Bản ghi trong file bad/blocked. File mới hơn thắng trên cùng một slug."""
    ranked: list[tuple[float, list]] = []
    for f in _backup_files():
        try:
            parsed = json.loads(f.read_text(encoding="utf-8"))
            tenants = parsed.get("tenants") if isinstance(parsed, dict) else None
            if not isinstance(tenants, list):
                continue
            ranked.append((f.stat().st_mtime, tenants))
        except Exception:
            continue
    ranked.sort()
    out: dict[str, dict] = {}
    for _mtime, tenants in ranked:
        for t in tenants:
            if not isinstance(t, dict):
                continue
            s = str(t.get("slug") or "").strip().lower()
            if s:
                out[s] = t
    return out


def _stub_tenant(slug: str) -> dict:
    return {
        "id": uuid.uuid4().hex[:12],
        "slug": slug,
        "name": slug,
        "domain": tenant_domain(slug),
        "container": f"javis-{slug}",
        "volumes": volume_names(slug),
        "quota_gb": 2,
        "protected": False,
        "status": "unknown",
    }


def adopt_missing(slugs: list[str]) -> int:
    """Thêm người còn máy hoặc volume nhưng mất khỏi sổ. Không xóa ai đang có."""
    p = store_path()
    readable = False
    data: dict = _empty()
    if p.is_file():
        try:
            parsed = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and isinstance(parsed.get("tenants"), list):
                data = parsed
                readable = True
        except Exception:
            readable = False
    if not isinstance(data.get("tenants"), list):
        data = _empty()
        readable = False
    ensure_quan(data)
    known = _slugs(data["tenants"])
    backups = _backup_by_slug()
    added = 0
    for slug in slugs:
        s = str(slug or "").strip().lower()
        if not s or s in known or s in PROTECTED_SLUGS or validate_slug(s):
            continue
        src = backups.get(s)
        if isinstance(src, dict):
            rec = dict(src)
            rec["slug"] = s
            rec["container"] = rec.get("container") or f"javis-{s}"
            rec["domain"] = tenant_domain(s)
            rec["volumes"] = rec.get("volumes") or volume_names(s)
            rec["protected"] = False
        else:
            rec = _stub_tenant(s)
        data["tenants"].append(rec)
        known.add(s)
        added += 1
    if added == 0 and readable:
        return 0
    if not readable:
        if added == 0:
            return 0
        save(data, allow_rebuild=True)
        return added
    save(data)
    return added


def get(slug: str) -> dict | None:
    s = (slug or "").strip().lower()
    for t in load()["tenants"]:
        if str(t.get("slug") or "") == s:
            return t
    return None


def upsert(rec: dict) -> dict:
    data = load()
    slug = str(rec.get("slug") or "")
    found = False
    for i, t in enumerate(data["tenants"]):
        if str(t.get("slug") or "") == slug:
            data["tenants"][i] = rec
            found = True
            break
    if not found:
        rec.setdefault("id", uuid.uuid4().hex[:12])
        data["tenants"].append(rec)
    save(data)
    return rec


def remove(slug: str) -> None:
    s = (slug or "").strip().lower()
    if s in PROTECTED_SLUGS:
        raise ValueError("Không xóa tên hệ thống.")
    data = load()
    data["tenants"] = [t for t in (data.get("tenants") or []) if str(t.get("slug") or "") != s]
    save(data, allow_drop={s})


def is_soft_deleted(rec: dict | None) -> bool:
    if not isinstance(rec, dict):
        return False
    try:
        return int(rec.get("deleted_at") or 0) > 0
    except (TypeError, ValueError):
        return False


def soft_delete_mark(slug: str) -> dict:
    """Đánh dấu chờ xóa 72h. Không gỡ volume."""
    rec = get(slug)
    if not rec:
        raise ValueError("Không có bản này.")
    s = str(rec.get("slug") or "").strip().lower()
    if rec.get("protected") or s in PROTECTED_SLUGS:
        raise ValueError("Không xóa bản hệ thống.")
    if is_soft_deleted(rec):
        return rec
    import time
    rec["deleted_at"] = int(time.time())
    rec["paused"] = True
    rec["status"] = "stopped"
    return upsert(rec)


def restore_mark(slug: str) -> dict:
    """Gỡ cờ chờ xóa. Não còn. Không tự bật máy."""
    rec = get(slug)
    if not rec:
        raise ValueError("Không có bản này.")
    if not is_soft_deleted(rec):
        raise ValueError("Máy này không đang chờ xóa.")
    rec.pop("deleted_at", None)
    # Giữ paused=True — admin bấm Chạy lại khi sẵn sàng.
    rec["paused"] = True
    return upsert(rec)


def purge_due_slugs(now: int | None = None) -> list[str]:
    """Slug đã hết hạn 72h, cần destroy thật."""
    import time
    ts = int(now if now is not None else time.time())
    out = []
    for t in load().get("tenants") or []:
        if t.get("protected"):
            continue
        try:
            da = int(t.get("deleted_at") or 0)
        except (TypeError, ValueError):
            da = 0
        if da > 0 and ts - da >= SOFT_DELETE_SEC:
            slug = str(t.get("slug") or "").strip().lower()
            if slug:
                out.append(slug)
    return out


def audit(action: str, slug: str, extra: str = "") -> None:
    import time
    p = cfgmod.STATE_DIR / "org-audit.jsonl"
    line = json.dumps({
        "ts": int(time.time()),
        "action": str(action or ""),
        "slug": str(slug or ""),
        "extra": str(extra or ""),
    }, ensure_ascii=False)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def audit_tail(limit: int = 80, slug: str = "") -> list[dict]:
    """Đọc cuối file audit (mới nhất trước)."""
    import time
    p = cfgmod.STATE_DIR / "org-audit.jsonl"
    if not p.is_file():
        return []
    try:
        n = max(1, min(500, int(limit or 80)))
    except (TypeError, ValueError):
        n = 80
    want = (slug or "").strip().lower()
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out = []
    for line in reversed(lines):
        line = (line or "").strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if not isinstance(row, dict):
            continue
        if want and str(row.get("slug") or "").lower() != want:
            continue
        try:
            row["ts"] = int(row.get("ts") or 0)
        except (TypeError, ValueError):
            row["ts"] = 0
        out.append({
            "ts": row["ts"],
            "action": str(row.get("action") or ""),
            "slug": str(row.get("slug") or ""),
            "extra": str(row.get("extra") or ""),
        })
        if len(out) >= n:
            break
    return out
