"""Xoá kết nối không được 500 vì thiếu method pool/hub/registry.

Chạy: python tests/run.py purge_connection
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import os
import tempfile
from pathlib import Path

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-purge-")

import config  # noqa: E402
import mcp_client  # noqa: E402
import mcp_hub  # noqa: E402
import mcp_store  # noqa: E402
import purge  # noqa: E402
from capability_registry import CapabilityRegistry  # noqa: E402

fails = []


def check(name, cond):
    print(("  OK   " if cond else "  FAIL ") + name)
    if not cond:
        fails.append(name)


check("pool có dang_ban_theo_key", callable(getattr(mcp_client.pool, "dang_ban_theo_key", None)))
check("pool có close_now", callable(getattr(mcp_client.pool, "close_now", None)))
check("dang_ban mặc định False", mcp_client.pool.dang_ban_theo_key("x") is False)
check("hub có forget_rate", callable(getattr(mcp_hub, "forget_rate", None)))
check("hub có audit_scrub", callable(getattr(mcp_hub, "audit_scrub", None)))
check("registry có drop_connection", callable(getattr(CapabilityRegistry, "drop_connection", None)))

# Thêm kết nối giả rồi purge
cid, err = mcp_store.add_connection(
    "google-chat",
    {"label": "Chat test xoá", "fields": {"client_id": "x", "client_secret": "y"}},
)
check("đã tạo kết nối giả", bool(cid) and not err and mcp_store.get_connection(cid) is not None)

bao = asyncio.run(purge.purge_connection(cid, mode="hard"))
check("purge không nổ, trả dict", isinstance(bao, dict))
check("purge ok", bao.get("ok") is True)
check("kết nối đã biến mất", mcp_store.get_connection(cid) is None)
check("đã ghi các bước dọn", "store" in (bao.get("removed") or []))

# close_now trên key trống
check("close_now key trống → False", asyncio.run(mcp_client.pool.close_now("khong-co")) is False)

# audit_scrub / forget_rate không nổ
mcp_hub.forget_rate("x")
n = mcp_hub.audit_scrub("x", drop=False)
check("audit_scrub trả số", isinstance(n, int))

print()
if fails:
    print(f"FAILED {len(fails)}: " + "; ".join(fails))
    raise SystemExit(1)
print("ALL OK")
