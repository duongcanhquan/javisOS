"""Lọc noise + ẩn orphan trên đồ thị tri thức.

Chạy: python tests/python/test_graph_noise.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from graph_builder import build_graph, is_graph_noise  # noqa: E402

fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


# ---- is_graph_noise ----
check("README.ja-JP là noise", is_graph_noise("README.ja-JP"))
check("README là noise", is_graph_noise("README"))
check("DESIGN-pl là noise", is_graph_noise("DESIGN-pl"))
check("DESIGN là noise", is_graph_noise("DESIGN"))
check("guide.zh-CN là noise (locale stem)", is_graph_noise("guide.zh-CN"))
check("wiki note thường KHÔNG noise", not is_graph_noise("Du-An-Truong-Nghe-Thuat"))
check("path .git/... là noise", is_graph_noise("index", ".git/hooks/index.md"))
check("path vendor/... là noise", is_graph_noise("foo", "vendor/pkg/foo.md"))


# ---- build_graph: orphans + noise ----
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    wiki = root / "wiki"
    wiki.mkdir()
    (wiki / "A.md").write_text("xem [[B]]\n", encoding="utf-8")
    (wiki / "B.md").write_text("xem [[A]]\n", encoding="utf-8")
    (wiki / "orphan-alone.md").write_text("không link ai\n", encoding="utf-8")
    (wiki / "README.ja-JP.md").write_text("[[A]]\n", encoding="utf-8")  # dù có link vẫn noise
    (wiki / "DESIGN-pl.md").write_text("x\n", encoding="utf-8")

    g0 = build_graph([str(root)], include_orphans=False)
    ids0 = {n["id"] for n in g0["nodes"]}
    check("mặc định chỉ còn A và B (có wikilink)", ids0 == {"a", "b"})
    check("orphan-alone bị ẩn", "orphan-alone" not in ids0)
    check("README.ja-JP không lên đồ thị", "readme.ja-jp" not in ids0)
    check("DESIGN-pl không lên đồ thị", "design-pl" not in ids0)
    check("stats.skipped_noise >= 2", g0["stats"].get("skipped_noise", 0) >= 2)
    check("có đúng 1 cạnh A-B", g0["stats"]["total_links"] == 1)

    g1 = build_graph([str(root)], include_orphans=True)
    ids1 = {n["id"] for n in g1["nodes"]}
    check("orphans=1 hiện orphan-alone", "orphan-alone" in ids1)
    check("orphans=1 VẪN ẩn README.ja-JP", "readme.ja-jp" not in ids1)
    check("orphans=1 VẪN ẩn DESIGN-pl", "design-pl" not in ids1)

# ---- dashboard không còn ép orphans=1 ----
gj = (ROOT / "dashboard" / "graph.js").read_text(encoding="utf-8")
check("graph.js mặc định orphans=0", "orphans=0" in gj)
check("graph.js không còn orphans=1 cứng", "&orphans=1" not in gj)


print("")
if fails:
    print(f"THAT BAI {len(fails)}: " + ", ".join(fails))
    sys.exit(1)
print("OK - test_graph_noise: tat ca pass")
