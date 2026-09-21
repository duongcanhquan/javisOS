"""Chính sách tổ chức: mật khẩu mạnh, kho API chung, vé tenant. Không đưa master key xuống Javis con."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
from pathlib import Path

import config as cfgmod
import org_tenants as ot

POOL_PROVIDERS = (
    "openrouter", "openai", "anthropic-api", "gemini", "groq", "deepseek",
)
_USER_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9._-]{2,31}$")
_WEAK = frozenset({
    "admin", "password", "password1", "password12", "12345678", "1234567890",
    "qwerty1234", "admin12345", "admin1234", "javis12345", "vietmycollege",
    "changeme12", "welcome123",
})
_LOCK = threading.Lock()
_ME_CACHE: dict = {"t": 0.0, "v": None}


def validate_username(user: str) -> str | None:
    s = (user or "").strip()
    if not s:
        return "Thiếu tên đăng nhập."
    if not _USER_RE.match(s):
        return "Tên đăng nhập 3-32 ký tự, bắt đầu bằng chữ, chỉ a-z 0-9 . _ -"
    if s.lower() in ("root", "administrator"):
        return "Tên đăng nhập này không dùng được."
    return None


def validate_password(password: str, username: str = "") -> str | None:
    pw = password or ""
    if len(pw) < 10:
        return "Mật khẩu tối thiểu 10 ký tự."
    if len(pw) > 128:
        return "Mật khẩu quá dài."
    if pw.lower() in _WEAK or pw.lower() == (username or "").strip().lower():
        return "Mật khẩu quá dễ đoán."
    has_letter = any(c.isalpha() for c in pw)
    has_digit = any(c.isdigit() for c in pw)
    if not has_letter or not has_digit:
        return "Mật khẩu cần cả chữ và số."
    if pw.strip() != pw:
        return "Mật khẩu không được bắt đầu/kết thúc bằng khoảng trắng."
    if any(ord(c) < 32 for c in pw):
        return "Mật khẩu không hợp lệ."
    return None


def new_pool_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()


def pool_path() -> Path:
    return cfgmod.STATE_DIR / "org-pool.json"


def load_pool() -> dict:
    p = pool_path()
    if not p.is_file():
        return {"keys": {k: "" for k in POOL_PROVIDERS}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    keys = data.setdefault("keys", {})
    if not isinstance(keys, dict):
        keys = {}
        data["keys"] = keys
    for k in POOL_PROVIDERS:
        keys.setdefault(k, "")
        if not isinstance(keys[k], str):
            keys[k] = ""
    return data


def save_pool(data: dict) -> None:
    p = pool_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(p)
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass


def mask_key(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    if len(s) <= 8:
        return "••••"
    return s[:3] + "…" + s[-4:]


def pool_public() -> dict:
    keys = load_pool()["keys"]
    return {
        "providers": {
            k: {"set": bool((keys.get(k) or "").strip()), "mask": mask_key(keys.get(k) or "")}
            for k in POOL_PROVIDERS
        }
    }


def put_pool_keys(body: dict) -> dict:
    data = load_pool()
    keys = data["keys"]
    for k in POOL_PROVIDERS:
        if k not in body:
            continue
        val = body.get(k)
        if val is None:
            keys[k] = ""
            continue
        s = str(val).strip()
        if not s:
            continue
        keys[k] = s
    save_pool(data)
    return pool_public()


def pool_key(provider: str) -> str:
    return (load_pool()["keys"].get(provider) or "").strip()


def find_by_token(raw: str) -> dict | None:
    h = hash_token(raw or "")
    if not h or h == hash_token(""):
        return None
    for t in ot.load()["tenants"]:
        if str(t.get("pool_token_hash") or "") == h:
            return t
    return None


def month_key() -> str:
    import localefmt
    return localefmt.now().strftime("%Y-%m")


def reset_month_if_needed(rec: dict) -> bool:
    mk = month_key()
    if str(rec.get("tokens_month") or "") == mk:
        return False
    rec["tokens_month"] = mk
    rec["tokens_used"] = 0
    return True


def add_tokens(slug: str, n: int) -> None:
    rec = ot.get(slug)
    if not rec:
        return
    reset_month_if_needed(rec)
    rec["tokens_used"] = int(rec.get("tokens_used") or 0) + max(0, int(n or 0))
    ot.upsert(rec)


def quota_ok(rec: dict) -> tuple[bool, str]:
    if rec.get("protected") and not rec.get("shared_api"):
        return False, "Bản này không dùng API chung."
    if not rec.get("shared_api"):
        return False, "Quản trị chưa bật API chung cho người này."
    reset_month_if_needed(rec)
    cap = int(rec.get("token_quota") or 0)
    used = int(rec.get("tokens_used") or 0)
    if cap > 0 and used >= cap:
        return False, f"Hết hạn mức token tháng này ({used}/{cap})."
    return True, ""


def native_url(provider: str) -> str:
    return {
        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
        "openai": "https://api.openai.com/v1/chat/completions",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "deepseek": "https://api.deepseek.com/chat/completions",
        "anthropic-api": "https://api.anthropic.com/v1/messages",
    }.get(provider) or ""


def tenant_side() -> bool:
    v = (os.getenv("JAVIS_ORG_TENANT") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def pool_base() -> str:
    return (os.getenv("JAVIS_ORG_POOL_URL") or "").strip().rstrip("/")


def pool_token() -> str:
    return (os.getenv("JAVIS_ORG_POOL_TOKEN") or "").strip()


def _fetch_me() -> dict:
    now = time.time()
    cached = _ME_CACHE.get("v")
    if cached is not None and now - float(_ME_CACHE.get("t") or 0) < 30:
        return cached
    base, tok = pool_base(), pool_token()
    if not base or not tok:
        _ME_CACHE["t"] = now
        _ME_CACHE["v"] = {"shared_api": False}
        return _ME_CACHE["v"]
    try:
        import httpx
        r = httpx.get(
            base + "/me",
            headers={"Authorization": "Bearer " + tok},
            timeout=4.0,
        )
        data = r.json() if r.status_code == 200 else {}
        if not isinstance(data, dict):
            data = {}
        val = {"shared_api": data.get("shared_api") is True,
               "providers": data.get("providers") or []}
    except Exception:
        val = {"shared_api": False}
    with _LOCK:
        _ME_CACHE["t"] = now
        _ME_CACHE["v"] = val
    return val


def tenant_uses_pool(provider: str) -> bool:
    if not tenant_side() or not pool_base() or not pool_token():
        return False
    if provider not in POOL_PROVIDERS:
        return False
    info = _fetch_me()
    if not info.get("shared_api"):
        return False
    allow = info.get("providers")
    if isinstance(allow, list):
        return provider in allow
    return True


def chat_url(provider: str, native: str) -> str:
    if not tenant_uses_pool(provider):
        return native
    return f"{pool_base()}/{provider}/chat"


def public_tenant(rec: dict) -> dict:
    out = {k: rec.get(k) for k in (
        "id", "slug", "name", "domain", "container", "quota_gb", "brain_mode",
        "protected", "status", "login_user", "shared_api", "token_quota",
        "tokens_used", "tokens_month",
    )}
    out["login_user"] = rec.get("login_user") or "admin"
    out["shared_api"] = bool(rec.get("shared_api"))
    try:
        out["quota_gb"] = int(rec.get("quota_gb") or 0)
    except (TypeError, ValueError):
        out["quota_gb"] = 0
    try:
        out["token_quota"] = int(rec.get("token_quota") or 0)
    except (TypeError, ValueError):
        out["token_quota"] = 0
    try:
        out["tokens_used"] = int(rec.get("tokens_used") or 0)
    except (TypeError, ValueError):
        out["tokens_used"] = 0
    return out
