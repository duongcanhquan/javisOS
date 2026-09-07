"""OpenMAIC URL helpers — public origin + rewrite media/audio URLs.

Khi Javis gọi OpenMAIC qua host.docker.internal, OpenMAIC gắn audioUrl kiểu
http://host.docker.internal:3000/api/classroom-media/... Trình duyệt user không
resolve được host đó → không tải được MP3 Edge → fallback Browser Native
(giọng Trung/Anh đọc tiếng Việt, nghe ngọng).

Luật: mọi URL media/audio trong payload phải dùng OPENMAIC_PUBLIC_URL
(trình duyệt mở được), không phải URL nội bộ Docker.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


# Host nội bộ Docker / loopback — trình duyệt user không dùng được.
_INTERNAL_HOST_FRAGMENTS = (
    "host.docker.internal",
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
)


def normalize_base(url: str) -> str:
    return (url or "").strip().rstrip("/")


def public_forward_headers(public_url: str) -> dict[str, str]:
    """Header để OpenMAIC buildRequestOrigin() gắn đúng host công khai vào audioUrl."""
    pub = normalize_base(public_url)
    if not pub:
        return {}
    parsed = urlparse(pub if "://" in pub else f"http://{pub}")
    host = parsed.netloc or parsed.path.split("/")[0]
    if not host:
        return {}
    proto = (parsed.scheme or "http").lower()
    if proto not in ("http", "https"):
        proto = "http"
    return {
        "X-Forwarded-Host": host,
        "X-Forwarded-Proto": proto,
    }


def _host_of(url: str) -> str:
    try:
        p = urlparse(url if "://" in url else f"http://{url}")
        return (p.hostname or "").lower()
    except Exception:
        return ""


def is_internal_openmaic_url(url: str, extra_bases: list[str] | None = None) -> bool:
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")):
        return False
    host = _host_of(u)
    if any(frag in host for frag in _INTERNAL_HOST_FRAGMENTS):
        return True
    for base in extra_bases or []:
        b = normalize_base(base)
        if b and (u == b or u.startswith(b + "/")):
            # Chỉ coi là nội bộ nếu base cũng trỏ host nội bộ
            if any(frag in _host_of(b) for frag in _INTERNAL_HOST_FRAGMENTS):
                return True
    return False


def replace_url_origin(url: str, public_url: str) -> str:
    """Đổi origin của URL tuyệt đối sang public_url, giữ path + query."""
    pub = normalize_base(public_url)
    u = (url or "").strip()
    if not pub or not u.startswith(("http://", "https://")):
        return u
    try:
        src = urlparse(u)
        dst = urlparse(pub if "://" in pub else f"http://{pub}")
        if not src.path and not src.query:
            return pub
        path = src.path or ""
        query = f"?{src.query}" if src.query else ""
        frag = f"#{src.fragment}" if src.fragment else ""
        return f"{dst.scheme}://{dst.netloc}{path}{query}{frag}"
    except Exception:
        return u


def rewrite_openmaic_payload(
    payload: Any,
    public_url: str,
    internal_bases: list[str] | None = None,
) -> Any:
    """Đệ quy đổi mọi URL nội bộ Docker/loopback → public_url.

    Giữ nguyên kiểu (dict/list/str). Không đụng chuỗi không phải URL http(s).
    """
    pub = normalize_base(public_url)
    if not pub:
        return payload
    bases = [normalize_base(b) for b in (internal_bases or []) if normalize_base(b)]

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, str):
            s = node.strip()
            if not s.startswith(("http://", "https://")):
                return node
            # Đổi nếu khớp base nội bộ tường minh hoặc host nội bộ.
            for b in bases:
                if s == b or s.startswith(b + "/"):
                    return replace_url_origin(s, pub)
            if is_internal_openmaic_url(s):
                return replace_url_origin(s, pub)
            return node
        return node

    return walk(payload)


def rewrite_classroom_json_text(
    text: str,
    public_url: str,
    internal_bases: list[str] | None = None,
) -> str:
    """Sửa file classroom JSON trên đĩa (deploy/repair). Trả text mới."""
    import json

    pub = normalize_base(public_url)
    if not pub or not (text or "").strip():
        return text
    try:
        data = json.loads(text)
    except Exception:
        # Fallback thô: thay origin nội bộ thường gặp
        out = text
        for old in (
            "http://host.docker.internal:3000",
            "https://host.docker.internal:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ):
            out = out.replace(old, pub)
        for b in internal_bases or []:
            nb = normalize_base(b)
            if nb and nb != pub:
                out = out.replace(nb, pub)
        return out
    fixed = rewrite_openmaic_payload(data, pub, internal_bases)
    return json.dumps(fixed, ensure_ascii=False, indent=2) + "\n"
