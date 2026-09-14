"""Bốn skill rút từ GitHub Trending: VoiceStudio, Agent-Reach, open-code-review, cherry-pick.

    python tests/run.py skill_trending_voice_review     (KHÔNG mạng)

Mô tả phải nêu THẲNG skill dùng để làm gì (chuẩn javis-builder: ≤150 ký tự, không
cụm sáo). Không copy nguyên kho agent-skills. Không đẻ bản sao agent-reach.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import sys

import skill_router

_fails = []
SKILLS = ROOT / ".claude" / "skills"


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(them) + "]" if them and not cond else "")))
    if not cond:
        _fails.append(name)


def meta(slug):
    p = SKILLS / slug / "SKILL.md"
    check(f"{slug}: có SKILL.md", p.is_file())
    if not p.is_file():
        return {}, ""
    text = p.read_text(encoding="utf-8")
    m, body = skill_router.split_frontmatter(text)
    vi = (m.get("description") or "").strip()
    en = (m.get("description_en") or "").strip()
    check(f"{slug}: description ≤150", len(vi) <= skill_router.SKILL_DESC_MAX, str(len(vi)))
    check(f"{slug}: description_en ≤150", len(en) <= skill_router.SKILL_DESC_MAX, str(len(en)))
    check(f"{slug}: có description_en khác bản Việt", bool(en) and en != vi)
    check(f"{slug}: không sáo rỗng", skill_router.validate_description(vi) is None,
          skill_router.validate_description(vi) or "")
    check(f"{slug}: không sáo rỗng (en)", skill_router.validate_description(en) is None,
          skill_router.validate_description(en) or "")
    check(f"{slug}: có group", bool((m.get("group") or "").strip()))
    check(f"{slug}: không em dash", "\u2014" not in text and "\u2013" not in text)
    check(f"{slug}: có mục dùng để làm gì / khi nào dùng",
          "Khi nào dùng" in body or "Dùng để làm gì" in body)
    return m, body


# ---- VoiceStudio ----
m, body = meta("voicestudio")
check("voicestudio: TTS / lồng tiếng / chép lời",
      "TTS" in (m.get("description") or "") or "lồng" in (m.get("description") or "").lower()
      or "chép" in (m.get("description") or ""))
check("voicestudio: API localhost:3900", "3900" in body)
check("voicestudio: không clone giọng người thật khi chưa đồng ý",
      "đồng ý" in body.lower() or "consent" in body.lower())
check("voicestudio: không tự cài app",
      "không tự cài" in body.lower() or "Không tự cài" in body)

# ---- Agent-Reach (đã có, làm rõ năng lực, không clone) ----
m, body = meta("agent-reach")
check("agent-reach: mô tả nêu kênh MXH/video/RSS/web",
      any(k in (m.get("description") or "").lower() for k in ("mxh", "rss", "video", "kênh")))
check("agent-reach: mục Dùng để làm gì", "Dùng để làm gì" in body)
check("không đẻ slug trùng agent-reach-2", not (SKILLS / "agent-reach-2").exists())

# ---- open-code-review ----
m, body = meta("open-code-review")
check("open-code-review: ruleset trong mô tả",
      "ruleset" in (m.get("description") or "").lower() or "rule" in (m.get("description") or "").lower())
check("open-code-review: có khung severity",
      "critical" in body.lower() and "security" in body.lower())
check("open-code-review: fallback khi chưa có ocr",
      "chưa cài" in body.lower() or "không có ocr" in body.lower() or "fallback" in body.lower())
check("open-code-review: file ruleset Javis",
      (SKILLS / "open-code-review" / "references" / "ruleset.md").is_file())

# ---- cherry-pick agent-skills ----
m, body = meta("cherry-pick-agent-skills")
check("cherry-pick: cấm import cả kho",
      "không import cả" in body.lower() or "cấm import cả" in body.lower())
check("cherry-pick: một SKILL.md một lần",
      "một SKILL.md" in body or "đúng một" in body.lower() or "từng SKILL.md" in body)
check("cherry-pick: viết lại chuẩn Javis (150 / group)",
      "150" in body and "group" in body.lower())
check("cherry-pick: không bảo copy nguyên văn kho ngoài",
      "nguyên văn" in body.lower() or "viết lại" in body.lower())


if _fails:
    print(f"\nFAIL {len(_fails)}: " + "; ".join(_fails))
    sys.exit(1)
print("\nOK - test_skill_trending_voice_review: tất cả pass")
