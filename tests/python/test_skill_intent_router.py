"""Router skill: ưu tiên slide-wright / proposal khi câu user khớp ý định.

    python tests/run.py skill_intent_router
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

import skill_router  # noqa: E402

_fails: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


metas = [
    {"slug": f"aaa-{i:02d}", "name": f"A{i}", "description": "skill alphabet sớm", "enabled": True}
    for i in range(25)
]
metas += [
    {
        "slug": "slide-wright",
        "name": "Slide Wright",
        "description": "Slide/pitch HTML đẹp",
        "enabled": True,
    },
    {
        "slug": "proposal-chien-luoc",
        "name": "Proposal",
        "description": "Soạn proposal chiến lược",
        "enabled": True,
    },
    {
        "slug": "zzz-cuoi",
        "name": "Cuối",
        "description": "skill alphabet muộn",
        "enabled": True,
    },
]

no_hint = skill_router.pick_for_router(metas, hint="")
check("không hint: cắt đúng cap", len(no_hint) == skill_router.SKILL_LIST_MAX)
check(
    "không hint: chưa tới slide-wright (alphabet)",
    "slide-wright" not in [s["slug"] for s in no_hint],
)

picked = skill_router.pick_for_router(metas, hint="Làm giúp mình pitch deck và slide trình chiếu")
slugs = [s["slug"] for s in picked]
check("có hint: vẫn ≤ cap", len(picked) <= skill_router.SKILL_LIST_MAX)
check("hint slide → slide-wright trong top", "slide-wright" in slugs)
check("hint slide → slide-wright đứng đầu hoặc gần đầu", slugs.index("slide-wright") < 5)

prop = skill_router.pick_for_router(metas, hint="Viết proposal chiến lược GTM")
check("hint proposal → proposal-chien-luoc", "proposal-chien-luoc" in [s["slug"] for s in prop])

foot = skill_router.intent_router_footer()
check("footer nhắc slide-wright", "slide-wright" in foot)
check("footer nhắc proposal", "proposal-chien-luoc" in foot)
check("footer không em dash", "\u2014" not in foot)

# Agent wiring
for path, needle in (
    (ROOT / "system" / "agents" / "soan-proposal-chien-luoc.md", "slide-wright"),
    (ROOT / "system" / "agents" / "xuat-goi-bao-cao.md", "slide-wright"),
    (ROOT / "system" / "agents" / "mkt-nghien-cuu.md", "slide-wright"),
    (ROOT / "system" / "agents" / "soan-ke-hoach-marketing.md", "slide-wright"),
    (ROOT / "system" / "agents" / "thiet-ke-do-hoa-minh-hoa.md", "slide-wright"),
):
    check(f"{path.name} gắn slide-wright", needle in path.read_text(encoding="utf-8"))

if _fails:
    print("FAILED:", ", ".join(_fails))
    raise SystemExit(1)
print("ALL PASS")
