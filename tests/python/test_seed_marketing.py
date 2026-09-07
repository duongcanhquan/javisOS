#!/usr/bin/env python3
"""Canh seed Bộ Marketing: SEO + Page FB + báo cáo Ads."""
from __future__ import annotations

import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

_tmp = Path(tempfile.mkdtemp(prefix="javis-seed-mkt-"))
(_tmp / "brain").mkdir()
os.environ["BRAINS_DIR"] = str(_tmp)
os.environ.setdefault("JAVIS_STATE_DIR", str(_tmp / "state"))
(_tmp / "state").mkdir(exist_ok=True)

import main  # noqa: E402

if hasattr(main, "BRAINS_DIR"):
    main.BRAINS_DIR = _tmp


def check(msg, cond, detail=""):
    print(("ok  " if cond else "FAIL") + " " + msg + ((" " + detail) if detail else ""))
    if not cond:
        raise SystemExit(1)


body = asyncio.run(main.studio_seed_marketing(brain="brain"))
check("seed-marketing ok", body.get("ok") is True)
check("5 workflows", len(body.get("workflows") or []) == 5, str(body.get("workflows")))
for slug in (
    "bo-marketing-kiem-seo",
    "bo-marketing-viet-seo",
    "bo-marketing-nghien-cuu",
    "bo-marketing-facebook",
    "bo-marketing-ads",
):
    check(f"workflow {slug}", slug in (body.get("workflows") or []))

agents_dir = main._agents_dir("brain")
for slug in (
    "mkt-nghien-cuu",
    "mkt-kiem-seo",
    "mkt-viet-seo",
    "mkt-facebook",
    "mkt-ads",
    "mkt-kiem-chung",
):
    p = agents_dir / f"{slug}.md"
    check(f"agent {slug}", p.is_file())
    text = p.read_text(encoding="utf-8")
    check(f"{slug} gemini", "model_provider: gemini" in text)

ads = (agents_dir / "mkt-ads.md").read_text(encoding="utf-8")
check("mkt-ads gắn bao-cao-facebook-ads", "bao-cao-facebook-ads" in ads)
check("mkt-ads gọi insights campaign", "level=campaign" in ads)

for sk in (
    "marketing-hub",
    "kiem-tra-seo",
    "viet-bai-seo",
    "tong-ket-facebook",
    "bao-cao-facebook-ads",
):
    check(f"skill hệ thống {sk}", (ROOT / ".claude" / "skills" / sk / "SKILL.md").is_file())
    check(f"skill brain {sk}", (main._skills_dir("brain") / sk / "SKILL.md").is_file())
    raw = (ROOT / ".claude" / "skills" / sk / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r'^description:\s*"?([^"\n]+)"?\s*$', raw, re.M)
    check(
        f"{sk} description ≤150",
        m and len(m.group(1).strip()) <= 150,
        str(len(m.group(1)) if m else 0),
    )

print("OK - test_seed_marketing")
