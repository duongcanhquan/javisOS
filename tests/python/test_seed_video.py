#!/usr/bin/env python3
"""Canh endpoint Bộ Video / Bộ Proposal tồn tại và ghi đúng file vào brain tạm."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

_tmp = Path(tempfile.mkdtemp(prefix="javis-seed-video-"))
(_tmp / "brain").mkdir()
os.environ["BRAINS_DIR"] = str(_tmp)

from starlette.testclient import TestClient  # noqa: E402
import main  # noqa: E402

if hasattr(main, "BRAINS_DIR"):
    main.BRAINS_DIR = _tmp


def check(msg, cond):
    print(("ok  " if cond else "FAIL") + " " + msg)
    if not cond:
        raise SystemExit(1)


client = TestClient(main.app, base_url="http://127.0.0.1")

r = client.post("/studio/seed-video", data={"brain": "brain"})
check(f"POST /studio/seed-video trả 200 (thật: {r.status_code})", r.status_code == 200)
body = r.json()
check("seed-video ok", body.get("ok") is True)
check("workflow slug đúng", body.get("workflow") == "bo-video-da-pipeline")

agents_dir = main._agents_dir("brain")
wf_dir = main._workflows_dir("brain")
for slug in ("nghien-cuu-chu-de-video", "bien-kich-video", "dao-dien-video", "kiem-chung-video"):
    check(f"có agent {slug}", (agents_dir / f"{slug}.md").is_file())
check("có workflow bo-video-da-pipeline", (wf_dir / "bo-video-da-pipeline.md").is_file())

sk = ROOT / ".claude" / "skills" / "lam-video" / "SKILL.md"
check("skill lam-video tồn tại", sk.is_file())
text = sk.read_text(encoding="utf-8")
check("lam-video có group Nội dung", "group: Nội dung" in text)
check("catalog pipeline đi kèm",
      (ROOT / ".claude/skills/lam-video/references/catalog.md").is_file())

r2 = client.post("/studio/seed-strategy", data={"brain": "brain"})
check(f"POST /studio/seed-strategy trả 200 (thật: {r2.status_code})", r2.status_code == 200)

print("OK - test_seed_video")
