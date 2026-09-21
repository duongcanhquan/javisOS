"""Overlay volume external cho javis-quan: đúng 4 volume, không down -v."""
from _paths import ROOT  # noqa: E402,F401

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


yml = (ROOT / "deploy" / "org" / "docker-compose.tenant-external.yml").read_text(encoding="utf-8")
lim = (ROOT / "deploy" / "org" / "docker-compose.tenant-limits.yml").read_text(encoding="utf-8")
envq = (ROOT / "deploy" / "org" / "env.quan.example").read_text(encoding="utf-8")
envm = (ROOT / "deploy" / "org" / "env.manager.example").read_text(encoding="utf-8")
envt = (ROOT / "deploy" / "org" / "env.tenant.example").read_text(encoding="utf-8")

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
check("env.manager: prefix vmos", "JAVIS_ORG_HOST_PREFIX=vmos" in envm)
compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
check("compose nhét prefix host vào container",
      "JAVIS_ORG_HOST_PREFIX: ${JAVIS_ORG_HOST_PREFIX:-javis}" in compose)
check("compose nhét JAVIS_ORG_MANAGER vào container",
      "JAVIS_ORG_MANAGER: ${JAVIS_ORG_MANAGER:-false}" in compose)
check("compose nhét WORKSPACE_NAME", "WORKSPACE_NAME: ${WORKSPACE_NAME:-}" in compose)
check("env.manager: catalog brain", "org-catalog" in envm)
check("tenant-limits: mem_limit", "mem_limit" in lim)
check("tenant-limits: cpus", "cpus:" in lim)
check("tenant-limits: plugin tắt", "JAVIS_ENABLE_USER_PLUGINS" in lim)
check("tenant-limits: không lệnh down -v", " down -v" not in lim and "volume rm" not in lim)
check("env.tenant: quota 2GB", "JAVIS_QUOTA_GB=2" in envt)
check("env.tenant: plugin tắt", "JAVIS_ENABLE_USER_PLUGINS=false" in envt)

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_org_tenant_volumes")
