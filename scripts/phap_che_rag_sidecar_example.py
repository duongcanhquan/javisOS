#!/usr/bin/env python3
"""Ví dụ tối giản API /retrieve cho JAVIS_PHAP_CHE_RAG_URL.

Không thay RAG-Anything / LightRAG. Chỉ minh họa hợp đồng JSON mà Javis gọi:
  POST /retrieve  {"query": "...", "top_k": 8}
  → {"results": [{"path": "...", "text": "...", "score": 1.0}]}

Chạy thử (thư mục corpus đã rclone sync):
  export PHAP_CHE_SYNC_DIR=/root/javis-data/phap-che-corpus
  pip install fastapi uvicorn
  uvicorn scripts.phap_che_rag_sidecar_example:app --host 127.0.0.1 --port 8001

Hoặc chạy file này trực tiếp:
  python scripts/phap_che_rag_sidecar_example.py
"""
from __future__ import annotations

import os
import re
from pathlib import Path

try:
    from fastapi import FastAPI
    from pydantic import BaseModel, Field
except ImportError as e:
    raise SystemExit("Cần: pip install fastapi uvicorn pydantic") from e

ROOT = Path(os.getenv("PHAP_CHE_SYNC_DIR") or os.getenv("PHAP_CHE_CORPUS") or ".").resolve()
_WORD = re.compile(r"[^\W\d_]+|\d+", re.UNICODE)

app = FastAPI(title="phap-che-rag-sidecar-example", version="0.1.0")


class RetrieveIn(BaseModel):
    query: str = ""
    top_k: int = Field(default=8, ge=1, le=40)


def _tokens(q: str) -> list[str]:
    return [t.lower() for t in _WORD.findall(q or "") if len(t) >= 2]


def _score(text: str, toks: list[str]) -> int:
    low = (text or "").lower()
    return sum(low.count(t) for t in toks)


@app.get("/health")
def health():
    return {"ok": True, "corpus": str(ROOT), "exists": ROOT.is_dir()}


@app.post("/retrieve")
def retrieve(body: RetrieveIn):
    toks = _tokens(body.query)
    if not toks or not ROOT.is_dir():
        return {"results": []}
    cands: list[tuple[int, Path, str]] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".md", ".txt", ".csv"):
            # PDF thật sự cần RAG-Anything; stub chỉ đọc text
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        sc = _score(str(p), toks) * 2 + _score(text, toks)
        if sc > 0:
            cands.append((sc, p, text))
    cands.sort(key=lambda x: (-x[0], str(x[1])))
    out = []
    for sc, p, text in cands[: body.top_k]:
        low = text.lower()
        pos = next((low.find(t) for t in toks if low.find(t) >= 0), -1)
        if pos < 0:
            excerpt = text[:500]
        else:
            a, b = max(0, pos - 100), min(len(text), pos + 400)
            excerpt = text[a:b]
        out.append({"path": str(p), "text": excerpt, "score": sc})
    return {"results": out}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8001")))
