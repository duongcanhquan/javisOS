"""Smoke: skill slide-wright đã ship + gắn bài giảng slide.

    python tests/run.py slide_wright_skill
"""
from __future__ import annotations

import re
from pathlib import Path

from _paths import ROOT

_fails: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


skill = ROOT / ".claude" / "skills" / "slide-wright"
check("có folder skill", skill.is_dir())
check("có SKILL.md", (skill / "SKILL.md").is_file())
check("có AGENTS.md", (skill / "AGENTS.md").is_file())
check("có LICENSE MIT", (skill / "LICENSE").is_file())
for ref in (
    "deck-template.md",
    "design-aesthetics.md",
    "theme-generation.md",
    "motion-recipes.md",
    "export-pdf.md",
    "deploy.md",
):
    check(f"reference {ref}", (skill / "references" / ref).is_file())

raw = (skill / "SKILL.md").read_text(encoding="utf-8")
check("không em dash trong SKILL", "\u2014" not in raw)
check("không en dash trong SKILL", "\u2013" not in raw)
check("ghi exports/slides", "exports/slides/" in raw)
check("có gate preview", "preview" in raw.lower() or "duyệt" in raw.lower())
m = re.search(r'^description:\s*"([^"]+)"\s*$', raw, re.M)
check("có description quoted", bool(m))
if m:
    check("description ≤150", len(m.group(1)) <= 150)
check("có group Nội dung", "group: Nội dung" in raw or 'group: "Nội dung"' in raw)
check("ghi upstream slide-wright", "arifszn/slide-wright" in raw)

# Cây references không dính em dash
for p in (skill / "references").glob("*.md"):
    t = p.read_text(encoding="utf-8")
    check(f"{p.name} không em dash", "\u2014" not in t)

bg = (ROOT / "system" / "agents" / "bg-slide.md").read_text(encoding="utf-8")
check("bg-slide gắn slide-wright", "slide-wright" in bg)
check("bg-slide vẫn có bai-giang-slide", "bai-giang-slide" in bg)

vid = (ROOT / "dashboard" / "baigiang.js").read_text(encoding="utf-8")
check("UI Bài giảng nhắc Deck HTML", "Deck HTML" in vid)

bai = (ROOT / ".claude" / "skills" / "bai-giang-slide" / "SKILL.md").read_text(encoding="utf-8")
check("bai-giang-slide trỏ slide-wright", "slide-wright" in bai)

if _fails:
    print("FAILED:", ", ".join(_fails))
    raise SystemExit(1)
print("ALL PASS")
