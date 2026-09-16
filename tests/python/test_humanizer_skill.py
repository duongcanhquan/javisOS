"""Skill humanizer (check AI + rewrite) ship kèm app.

    python tests/run.py humanizer_skill
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

import skill_router  # noqa: E402

_fails: list[str] = []


def check(name: str, cond: bool, extra: str = "") -> None:
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        _fails.append(name)


skill = ROOT / ".claude" / "skills" / "humanizer"
check("có thư mục humanizer", skill.is_dir())
check("có SKILL.md", (skill / "SKILL.md").is_file())
check("có references/patterns.md", (skill / "references" / "patterns.md").is_file())

raw = (skill / "SKILL.md").read_text(encoding="utf-8")
check("không em dash", "\u2014" not in raw)
check("nhắc detect / điểm", "0-100" in raw and "detect" in raw.lower())
check("nhắc rewrite", "rewrite" in raw.lower())
check("nhắc tiếng Việt", "Tiếng Việt" in raw or "tiếng Việt" in raw)
check("có upstream Aboudjem", "Aboudjem/humanizer-skill" in raw)
check("không dán nguyên SKILL 39KB", len(raw) < 20_000, str(len(raw)))

meta, body = skill_router.split_frontmatter(raw)
vi = (meta.get("description") or "").strip()
en = (meta.get("description_en") or "").strip()
check("description ≤150", len(vi) <= skill_router.SKILL_DESC_MAX, str(len(vi)))
check("description_en ≤150", len(en) <= skill_router.SKILL_DESC_MAX, str(len(en)))
check("có description_en khác bản Việt", bool(en) and en != vi)
check("description hợp lệ", skill_router.validate_description(vi) is None,
      skill_router.validate_description(vi) or "")
check("group Nội dung", (meta.get("group") or "") in ("Nội dung", "Content", "Marketing"))

pat = (skill / "references" / "patterns.md").read_text(encoding="utf-8")
check("patterns có P1 và P55", "P1" in pat and "P55" in pat)
check("patterns có mục Việt", "Tiếng Việt" in pat)
check("patterns không em dash", "\u2014" not in pat)

# Router
metas = [
    {"slug": f"aaa-{i:02d}", "name": f"A{i}", "description": "sớm", "enabled": True}
    for i in range(22)
]
metas.append({
    "slug": "humanizer",
    "name": "Humanizer",
    "description": "Chấm điểm dấu viết AI",
    "enabled": True,
})
picked = skill_router.pick_for_router(metas, hint="Check AI đoạn này có dấu ChatGPT không")
check("hint check AI → humanizer", "humanizer" in [s["slug"] for s in picked])
picked2 = skill_router.pick_for_router(metas, hint="humanize giúp mình bài SEO")
check("hint humanize → humanizer", "humanizer" in [s["slug"] for s in picked2])
foot = skill_router.intent_router_footer()
check("footer nhắc humanizer", "humanizer" in foot)

if _fails:
    print(f"\n{len(_fails)} failed")
    sys.exit(1)
print("\nall ok")
