"""Overlay volume external cho javis-quan: đúng 4 volume, không down -v."""
from _paths import ROOT  # noqa: E402,F401

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


yml = (ROOT / "deploy" / "org" / "docker-compose.tenant-external.yml").read_text(encoding="utf-8")
envq = (ROOT / "deploy" / "org" / "env.quan.example").read_text(encoding="utf-8")
envm = (ROOT / "deploy" / "org" / "env.manager.example").read_text(encoding="utf-8")

check("tenant-external: external true", "external: true" in yml)
for name in (
    "javis_javis-data",
    "javis_javis-brains",
    "javis_claude-auth",
    "javis_codex-auth",
):
    check(f"tenant-external: {name}", name in yml)
check("tenant-external: không lệnh down -v", " down -v" not in yml and "volume rm" not in yml)
check("env.quan: JAVIS_NAME=javis-quan", "JAVIS_NAME=javis-quan" in envq)
check("env.quan: domain quan", "javis-quan.vietmycollege.com" in envq)
check("env.manager: không trỏ volume quan", "javis_javis-data" not in envm)
check("env.manager: JAVIS_ORG_MANAGER", "JAVIS_ORG_MANAGER=true" in envm)

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_org_tenant_volumes")
