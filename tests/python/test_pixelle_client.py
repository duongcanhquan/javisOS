"""pixelle_client - không cần server thật.

    python tests/python/test_pixelle_client.py
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import asyncio
import os

import pixelle_client as px

loi = []


def check(ten, dieu, them=""):
    print(("ok   " if dieu else "FAIL ") + ten + (f"  [{them}]" if them and not dieu else ""))
    if not dieu:
        loi.append(ten)


os.environ.pop("PIXELLE_API_BASE", None)
check("api_base trống", px.api_base() == "")
h = asyncio.run(px.health())
check("health khi trống → ok False", h.get("ok") is False)

os.environ["PIXELLE_API_BASE"] = "http://127.0.0.1:9"
h2 = asyncio.run(px.health())
check("health cổng chết → ok False", h2.get("ok") is False)
check("error có chữ", bool(h2.get("error")))

print()
if loi:
    print("ĐỎ:", ", ".join(loi))
    raise SystemExit(1)
print("ALL PASS")
