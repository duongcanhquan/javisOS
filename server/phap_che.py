"""Tìm kiếm kho pháp chế trong brain + (tuỳ chọn) RAG sidecar.

Local: quét `sources/phap-che/**/*.md` và trang wiki có từ khóa pháp chế.
Sidecar: POST {JAVIS_PHAP_CHE_RAG_URL}/retrieve với JSON {query, top_k}.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional
from urllib import error as urlerror
from urllib import request as urlrequest

_WORD = re.compile(r"[^\W\d_]+|\d+", re.UNICODE)


def _tokens(q: str) -> list[str]:
    return [t.lower() for t in _WORD.findall(q or "") if len(t) >= 2]


def _score(text: str, toks: list[str]) -> int:
    low = (text or "").lower()
    return sum(low.count(t) for t in toks)


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _iter_md(root: Path, sub: str) -> list[Path]:
    base = root / sub
    if not base.is_dir():
        return []
    out: list[Path] = []
    for p in base.rglob("*.md"):
        if p.name.startswith("."):
            continue
        out.append(p)
    return out


def search_local(brain_root: str | Path, query: str, *, top_k: int = 8) -> list[dict[str, Any]]:
    """BM25-lite: đếm token trong path+nội dung, ưu tiên sources/phap-che rồi wiki."""
    root = Path(brain_root)
    toks = _tokens(query)
    if not toks:
        return []
    top_k = max(1, min(int(top_k or 8), 20))
    cands: list[tuple[int, Path, str]] = []

    paths = _iter_md(root, "sources/phap-che")
    # Dedup
    seen = set()
    uniq = []
    for p in paths:
        rp = str(p.resolve())
        if rp in seen:
            continue
        seen.add(rp)
        uniq.append(p)

    wiki_paths = []
    for wname in ("wiki", "07 - Wiki", "07-Wiki"):
        wiki_paths.extend(_iter_md(root, wname))

    for p in uniq + wiki_paths:
        try:
            body = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Wiki: chỉ giữ trang có dấu pháp chế / legal / nghị định / điều
        rel = _rel(root, p)
        if "/wiki" in f"/{rel.lower()}" or rel.lower().startswith("07"):
            low = (rel + "\n" + body[:2000]).lower()
            if not any(k in low for k in (
                "pháp chế", "phap-che", "phap che", "nghị định", "nghi dinh",
                "thông tư", "thong tu", "luật", "luat", "legal", "điều ", "dieu ",
            )):
                # Vẫn cho qua nếu token query trùng mạnh trong path
                if _score(rel, toks) < 2:
                    continue
        sc = _score(rel, toks) * 3 + _score(body, toks)
        if sc <= 0:
            continue
        cands.append((sc, p, body))

    cands.sort(key=lambda x: (-x[0], str(x[1])))
    hits = []
    for sc, p, body in cands[:top_k]:
        # Đoạn trích quanh token đầu
        snippet = body.strip().replace("\r\n", "\n")
        low = snippet.lower()
        pos = -1
        for t in toks:
            pos = low.find(t)
            if pos >= 0:
                break
        if pos < 0:
            excerpt = snippet[:400]
        else:
            a = max(0, pos - 120)
            b = min(len(snippet), pos + 280)
            excerpt = ("…" if a else "") + snippet[a:b] + ("…" if b < len(snippet) else "")
        hits.append({
            "score": sc,
            "path": _rel(root, p),
            "source": "local",
            "excerpt": excerpt[:600],
        })
    return hits


def search_sidecar(query: str, *, top_k: int = 8, timeout: float = 12.0) -> list[dict[str, Any]]:
    """Gọi RAG sidecar nếu JAVIS_PHAP_CHE_RAG_URL được set."""
    base = (os.getenv("JAVIS_PHAP_CHE_RAG_URL") or "").strip().rstrip("/")
    if not base:
        return []
    url = base + "/retrieve"
    payload = json.dumps({"query": query, "top_k": top_k}, ensure_ascii=False).encode("utf-8")
    req = urlrequest.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except (urlerror.URLError, urlerror.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as e:
        return [{"score": 0, "path": "", "source": "sidecar_error", "excerpt": str(e)[:300]}]

    items = data.get("results") or data.get("chunks") or data.get("hits") or []
    out = []
    for it in items[:top_k]:
        if not isinstance(it, dict):
            continue
        out.append({
            "score": it.get("score") or it.get("relevance") or 0,
            "path": it.get("path") or it.get("source") or it.get("file") or "",
            "source": "sidecar",
            "excerpt": (it.get("text") or it.get("excerpt") or it.get("content") or "")[:600],
        })
    return out


def search(brain_root: str | Path, query: str, *, top_k: int = 8,
           include_sidecar: bool = True) -> dict[str, Any]:
    local = search_local(brain_root, query, top_k=top_k)
    side: list[dict[str, Any]] = []
    if include_sidecar:
        side = search_sidecar(query, top_k=top_k)
    return {
        "ok": True,
        "query": query,
        "local": local,
        "sidecar": [h for h in side if h.get("source") != "sidecar_error"],
        "sidecar_error": next((h.get("excerpt") for h in side if h.get("source") == "sidecar_error"), None),
        "rag_url_configured": bool((os.getenv("JAVIS_PHAP_CHE_RAG_URL") or "").strip()),
    }


def status() -> dict[str, Any]:
    url = (os.getenv("JAVIS_PHAP_CHE_RAG_URL") or "").strip()
    return {
        "ok": True,
        "rag_url": url or None,
        "rag_configured": bool(url),
        "sync_hint": "scripts/sync-phap-che-drive.sh",
        "docs": "docs/28-phap-che-ca-nhan.md",
    }
