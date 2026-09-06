"""Plugin bundled: tìm kho pháp chế (local markdown + RAG sidecar tuỳ chọn)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Cho phép `import phap_che` khi plugin chạy trong process server (sys.path đã có /app/server)
# hoặc khi cwd khác: thêm parent server vào path.
_SERVER = Path(__file__).resolve().parents[3] / "server"
if _SERVER.is_dir() and str(_SERVER) not in sys.path:
    sys.path.insert(0, str(_SERVER))


def _search(args, ctx):
    args = args or {}
    q = (args.get("query") or args.get("q") or "").strip()
    if not q:
        return "ERROR: thiếu query (câu hỏi / số hiệu / từ khóa Điều)."
    try:
        top_k = int(args.get("top_k") or 8)
    except (TypeError, ValueError):
        top_k = 8
    include = str(args.get("include_sidecar", "true")).lower() not in ("0", "false", "no")
    root = getattr(ctx, "vault_root", None) or getattr(ctx, "brain_root", None)
    if not root:
        return "ERROR: không xác định được vault_root."
    import phap_che
    data = phap_che.search(root, q, top_k=top_k, include_sidecar=include)
    return json.dumps(data, ensure_ascii=False, indent=2)


def _status(args, ctx):
    import phap_che
    data = phap_che.status()
    root = getattr(ctx, "vault_root", None)
    if root:
        from pathlib import Path as P
        p = P(root) / "sources" / "phap-che"
        n = 0
        if p.is_dir():
            n = sum(1 for _ in p.rglob("*.md"))
        data["local_md_files"] = n
        data["local_dir"] = str(p)
    return json.dumps(data, ensure_ascii=False, indent=2)


def register(ctx):
    ctx.register_tool(
        name="phap_che_search",
        description=(
            "Tìm văn bản pháp lý trong sources/phap-che và wiki pháp chế; "
            "nếu có JAVIS_PHAP_CHE_RAG_URL thì hỏi thêm RAG sidecar. "
            "Tham số: query (bắt buộc), top_k, include_sidecar."
        ),
        handler=_search, min_mode="readonly",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Câu hỏi, số hiệu, hoặc từ khóa Điều/Khoản"},
                "top_k": {"type": "integer", "description": "Số kết quả tối đa (1-20)"},
                "include_sidecar": {"type": "boolean", "description": "Gọi RAG sidecar nếu đã cấu hình"},
            },
            "required": ["query"],
        },
    )
    ctx.register_tool(
        name="phap_che_status",
        description="Trạng thái kho pháp chế: RAG URL đã cấu hình chưa, số file md local.",
        handler=_status, min_mode="readonly",
        schema={"type": "object", "properties": {}},
    )
