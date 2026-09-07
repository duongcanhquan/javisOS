#!/usr/bin/env python3
"""Canh seed Bộ Bài giảng ghi đúng agents/skills/workflows Gemini vào brain tạm.

Gọi thẳng handler (không qua HTTP) vì máy có auth gate - TestClient sẽ 401.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

_tmp = Path(tempfile.mkdtemp(prefix="javis-seed-baigiang-"))
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


body = asyncio.run(main.studio_seed_bai_giang(brain="brain"))
check("seed-bai-giang ok", body.get("ok") is True)
check("4 workflows", len(body.get("workflows") or []) == 4, str(body.get("workflows")))
for slug in (
    "bo-bai-giang-lop-hoc",
    "bo-bai-giang-video",
    "bo-bai-giang-slide",
    "bo-bai-giang-van-ban",
):
    check(f"workflow {slug} trong response", slug in (body.get("workflows") or []))

agents_dir = main._agents_dir("brain")
wf_dir = main._workflows_dir("brain")
sk_dir = main._skills_dir("brain")

for slug in (
    "bg-nghien-cuu",
    "bg-lop-hoc",
    "bg-video",
    "bg-slide",
    "bg-van-ban",
    "bg-kiem-chung",
):
    p = agents_dir / f"{slug}.md"
    check(f"có agent {slug}", p.is_file())
    text = p.read_text(encoding="utf-8")
    check(f"{slug} gemini provider", "model_provider: gemini" in text)
    check(f"{slug} model flash", "gemini-2.5-flash" in text)

for slug in body["workflows"]:
    check(f"file workflow {slug}", (wf_dir / f"{slug}.md").is_file())

for sk in ("tao-bai-giang", "bai-giang-lop-hoc", "bai-giang-slide", "bai-giang-van-ban"):
    check(f"skill brain {sk}", (sk_dir / sk / "SKILL.md").is_file())
    check(
        f"skill hệ thống {sk}",
        (ROOT / ".claude" / "skills" / sk / "SKILL.md").is_file(),
    )

ag = (agents_dir / "bg-nghien-cuu.md").read_text(encoding="utf-8")
check("nghiên cứu gắn deep-research", "deep-research" in ag)
check("nghiên cứu cổng brief", "cổng brief" in ag.lower() or "Cổng brief" in ag)

# description ≤ 150 ký tự (router cắt im lặng)
for sk in ("tao-bai-giang", "bai-giang-lop-hoc", "bai-giang-slide", "bai-giang-van-ban"):
    raw = (ROOT / ".claude" / "skills" / sk / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r'^description:\s*"?([^"\n]+)"?\s*$', raw, re.M)
    check(f"{sk} có description", bool(m))
    if m:
        check(f"{sk} description ≤150", len(m.group(1).strip()) <= 150, str(len(m.group(1))))

print("OK - test_seed_bai_giang")
