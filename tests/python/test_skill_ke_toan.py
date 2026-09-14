"""Gói kế toán: 4 skill từ repo + kế hoạch kỳ + agent/workflow ke-toan-chuan.

    python tests/run.py skill_ke_toan     (KHÔNG mạng)
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import sys

import skill_router

_fails = []
SK = ROOT / ".claude" / "skills"
AG = ROOT / "system" / "agents"
WF = ROOT / "system" / "workflows" / "ke-toan-chuan.md"


def check(name, cond, them=""):
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(them) + "]" if them and not cond else "")))
    if not cond:
        _fails.append(name)


def skill_ok(slug):
    p = SK / slug / "SKILL.md"
    check(f"{slug}: SKILL.md", p.is_file())
    if not p.is_file():
        return {}, ""
    text = p.read_text(encoding="utf-8")
    m, body = skill_router.split_frontmatter(text)
    vi = (m.get("description") or "").strip()
    en = (m.get("description_en") or "").strip()
    check(f"{slug}: desc ≤150", len(vi) <= skill_router.SKILL_DESC_MAX, str(len(vi)))
    check(f"{slug}: en ≤150", len(en) <= skill_router.SKILL_DESC_MAX, str(len(en)))
    check(f"{slug}: có description_en khác Việt", bool(en) and en != vi)
    check(f"{slug}: không sáo", skill_router.validate_description(vi) is None)
    check(f"{slug}: group Tài chính", (m.get("group") or "") == "Tài chính")
    check(f"{slug}: không em dash", "\u2014" not in text and "\u2013" not in text)
    check(f"{slug}: Dùng để làm gì / Khi nào dùng",
          "Dùng để làm gì" in body or "Khi nào dùng" in body)
    return m, body


m, body = skill_ok("doc-bao-cao-tai-chinh")
check("doc-bao-cao: 5 tỷ số / ROE", "ROE" in body or "ty-so" in body)
check("doc-bao-cao: Ruchas-lab", "Ruchas-lab" in body or "Financial-report-analyzer" in body)
check("doc-bao-cao: file ty-so.md", (SK / "doc-bao-cao-tai-chinh" / "references" / "ty-so.md").is_file())

m, body = skill_ok("so-ke-toan-kep")
check("so-kep: python-accounting", "python-accounting" in body)
check("so-kep: không tự pip", "không tự pip" in body.lower() or "Không tự pip" in body)
check("so-kep: P&L CĐKT", "IncomeStatement" in body or "P&L" in body)

m, body = skill_ok("doc-hoa-don")
check("hoa-don: DylanMerigaud", "DylanMerigaud" in body or "ai-invoice-parser" in body)
check("hoa-don: cờ line_items_sum_mismatch", "line_items_sum_mismatch" in body)
check("hoa-don: schema ref", (SK / "doc-hoa-don" / "references" / "schema-hoa-don.md").is_file())

m, body = skill_ok("tro-ly-thi-truong-chung-khoan")
check("ck: không phải kế toán", "không phải kế toán" in body.lower() or "Not bookkeeping" in (m.get("description_en") or ""))
check("ck: Finnhub hoặc get_price", "Finnhub" in body or "get_price" in body)
check("ck: Pyligent", "Pyligent" in body)

m, body = skill_ok("ke-hoach-ke-toan")
check("kh-kt: 05-plan.md", "05-plan.md" in body)
check("kh-kt: không SOM/MKT", "ke-hoach-kinh-doanh" in body)

for slug in ("trich-hoa-don", "ghi-so-ke-toan", "phan-tich-bao-cao-tai-chinh",
             "lap-ke-hoach-ke-toan", "kiem-chung-ke-toan"):
    p = AG / f"{slug}.md"
    check(f"agent {slug}", p.is_file())
    if p.is_file():
        t = p.read_text(encoding="utf-8")
        check(f"agent {slug}: type+group", "type: agent" in t and "group: Tài chính" in t)
        check(f"agent {slug}: không em dash", "\u2014" not in t and "\u2013" not in t)

wf = WF.read_text(encoding="utf-8") if WF.is_file() else ""
check("workflow ke-toan-chuan", WF.is_file())
check("workflow group Tài chính", "group: Tài chính" in wf)
check("workflow đủ 5 agent kế toán + xuất",
      all(s in wf for s in ("trich-hoa-don", "ghi-so-ke-toan", "phan-tich-bao-cao-tai-chinh",
                            "lap-ke-hoach-ke-toan", "kiem-chung-ke-toan", "xuat-goi-bao-cao")))
check("workflow sources/accounting", "sources/accounting" in wf)
check("workflow không em dash", "\u2014" not in wf and "\u2013" not in wf)
check("không đẻ agent trùng phan-tich-tai-chinh-marketing",
      "phan-tich-tai-chinh-marketing" not in wf)


if _fails:
    print(f"\nFAIL {len(_fails)}: " + "; ".join(_fails))
    sys.exit(1)
print("\nOK - test_skill_ke_toan: tất cả pass")
