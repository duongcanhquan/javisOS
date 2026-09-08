#!/usr/bin/env python3
"""Canh seed Bộ Trường = Bộ Bài giảng + agent gv-huong-dan + source mẫu."""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

_tmp = Path(tempfile.mkdtemp(prefix="javis-seed-truong-"))
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


body = asyncio.run(main.studio_seed_truong(brain="brain"))
check("seed-truong ok", body.get("ok") is True)
check("pack truong", body.get("pack") == "truong")
check("4 workflows bài giảng", len(body.get("workflows") or []) == 4, str(body.get("workflows")))
check("có gv-huong-dan", "gv-huong-dan" in (body.get("agents") or []))

agents_dir = main._agents_dir("brain")
p = agents_dir / "gv-huong-dan.md"
check("file agent gv-huong-dan", p.is_file())
text = p.read_text(encoding="utf-8")
check("gemini provider", "model_provider: gemini" in text)
check("nói Models", "Models" in text)

src = Path(main._brain_root("brain")) / "sources" / "goi-truong-bat-dau.md"
check("source goi-truong-bat-dau", src.is_file())
check("source nhắc Bộ Trường", "Bộ Trường" in src.read_text(encoding="utf-8"))

# Idempotent: chạy lại không fail
body2 = asyncio.run(main.studio_seed_truong(brain="brain"))
check("seed lần 2 ok", body2.get("ok") is True)

print("OK - test_seed_truong")
