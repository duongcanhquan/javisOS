#!/usr/bin/env python3
"""Canh endpoint Bộ Video / Proposal / Poster ghi đúng agent+workflow vào brain tạm."""
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
for slug in (
    "nghien-cuu-chu-de-video",
    "bien-kich-video",
    "minh-hoa-canh-video",
    "dao-dien-video",
    "kiem-chung-video",
):
    check(f"có agent {slug}", (agents_dir / f"{slug}.md").is_file())
check("có workflow bo-video-da-pipeline", (wf_dir / "bo-video-da-pipeline.md").is_file())

wf_video = (wf_dir / "bo-video-da-pipeline.md").read_text(encoding="utf-8")
check("workflow video có bước minh họa cảnh", "minh-hoa-canh-video" in wf_video)

sk = ROOT / ".claude" / "skills" / "lam-video" / "SKILL.md"
check("skill lam-video tồn tại", sk.is_file())
text = sk.read_text(encoding="utf-8")
check("lam-video có group Nội dung", "group: Nội dung" in text)
check("lam-video có cổng brief", "Cổng brief" in text or "cổng brief" in text.lower())
check("catalog pipeline đi kèm",
      (ROOT / ".claude/skills/lam-video/references/catalog.md").is_file())
check("brief-checklist đi kèm",
      (ROOT / ".claude/skills/lam-video/references/brief-checklist.md").is_file())

sk_img = ROOT / ".claude" / "skills" / "tao-anh-minh-hoa" / "SKILL.md"
check("skill tao-anh-minh-hoa tồn tại", sk_img.is_file())
img_txt = sk_img.read_text(encoding="utf-8")
check("tao-anh-minh-hoa nhắc javis_generate_image", "javis_generate_image" in img_txt)
check("tao-anh-minh-hoa có references/che-do.md",
      (ROOT / ".claude/skills/tao-anh-minh-hoa/references/che-do.md").is_file())

ag = (agents_dir / "nghien-cuu-chu-de-video.md").read_text(encoding="utf-8")
check("agent nghiên cứu video gắn deep-research", "deep-research" in ag)
check("agent nghiên cứu bắt buộc cổng brief", "CỔNG BRIEF" in ag or "cổng brief" in ag.lower())
check("agent nghiên cứu CẤM giả định brief", "CẤM giả định" in ag)
check("skill deep-research tồn tại", (ROOT / ".claude/skills/deep-research/SKILL.md").is_file())

ag_img = (agents_dir / "minh-hoa-canh-video.md").read_text(encoding="utf-8")
check("agent minh họa cảnh gắn tao-anh-minh-hoa", "tao-anh-minh-hoa" in ag_img)
check("agent minh họa cảnh gọi javis_generate_image", "javis_generate_image" in ag_img)

r2 = client.post("/studio/seed-strategy", data={"brain": "brain"})
check(f"POST /studio/seed-strategy trả 200 (thật: {r2.status_code})", r2.status_code == 200)
body2 = r2.json()
check("seed-strategy ok", body2.get("ok") is True)
check("workflow proposal đúng", body2.get("workflow") == "bo-proposal-chien-luoc")
for slug in (
    "nghien-cuu-thi-truong",
    "chien-luoc-kinh-doanh",
    "chien-luoc-marketing",
    "minh-hoa-proposal",
    "soan-proposal",
    "kiem-chung-proposal",
):
    check(f"có agent proposal {slug}", (agents_dir / f"{slug}.md").is_file())
wf_prop = (wf_dir / "bo-proposal-chien-luoc.md").read_text(encoding="utf-8")
check("workflow proposal có bước minh họa", "minh-hoa-proposal" in wf_prop)
ag_prop = (agents_dir / "minh-hoa-proposal.md").read_text(encoding="utf-8")
check("agent minh họa proposal gắn tao-anh-minh-hoa", "tao-anh-minh-hoa" in ag_prop)

r3 = client.post("/studio/seed-poster", data={"brain": "brain"})
check(f"POST /studio/seed-poster trả 200 (thật: {r3.status_code})", r3.status_code == 200)
body3 = r3.json()
check("seed-poster ok", body3.get("ok") is True)
check("workflow poster đúng", body3.get("workflow") == "bo-poster-minh-hoa")
for slug in ("brief-poster", "thiet-ke-poster", "kiem-chung-poster"):
    check(f"có agent poster {slug}", (agents_dir / f"{slug}.md").is_file())
check("có workflow bo-poster-minh-hoa", (wf_dir / "bo-poster-minh-hoa.md").is_file())
ag_poster = (agents_dir / "thiet-ke-poster.md").read_text(encoding="utf-8")
check("thiết kế poster gọi javis_generate_image", "javis_generate_image" in ag_poster)

print("OK - test_seed_video")
