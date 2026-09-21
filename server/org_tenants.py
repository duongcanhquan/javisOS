"""Sổ Javis con (tenant) trên Javis gốc. Chỉ dùng khi JAVIS_ORG_MANAGER=true."""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path

import config as cfgmod

PROTECTED_SLUGS = frozenset({
    "quan", "manager", "proxy", "caddy", "web", "javis", "www", "mail", "ns",
})
PROTECTED_VOLUMES = frozenset({
    "javis_javis-data", "javis_javis-brains", "javis_claude-auth", "javis_codex-auth",
})
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
    p = store_path()
    if not p.is_file():
        data = _empty()
        ensure_quan(data)
        save(data)
        return data
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = _empty()
    if not isinstance(data, dict):
        data = _empty()
    data.setdefault("tenants", [])
    changed = ensure_quan(data)
    if _sync_domains(data):
        changed = True
    if changed:
        save(data)
    return data


def save(data: dict) -> None:
    p = store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
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
    save(data)


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
