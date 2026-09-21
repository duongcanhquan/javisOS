"""Preflight/backup/proxy/split: chỉ đọc hoặc tar, không xóa volume não."""
from _paths import ROOT  # noqa: E402,F401

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


def body(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


pre = body("scripts/org_cutover_preflight.sh")
bak = body("scripts/org_backup_volumes.sh")
prox = body("scripts/org_cutover_to_proxy.sh")
spl = body("scripts/org_cutover_split_domains.sh")
cut = body("deploy/org/CUTOVER.md")

for name, txt in (
    ("preflight", pre),
    ("backup", bak),
    ("proxy", prox),
    ("split", spl),
):
    check(f"{name}: set -euo pipefail", "set -euo pipefail" in txt)
    check(f"{name}: không compose down -v", "down -v" not in txt)
    check(f"{name}: không volume rm javis_javis", "volume rm javis_javis" not in txt)

check("preflight: 4 volume não", "javis_javis-brains" in pre and "javis_javis-data" in pre)
check("preflight: PREFLIGHT_OK", "PREFLIGHT_OK" in pre)
check("backup: 4 volume", all(v in bak for v in (
    "javis_javis-data", "javis_javis-brains", "javis_claude-auth", "javis_codex-auth",
)))
check("backup: BACKUP_OK", "BACKUP_OK" in bak)
check("backup: scratch rm only", "javis_org_backup_scratch" in bak)
check("proxy: rollback caddy", "docker-compose.https.yml" in prox and "javis-caddy" in prox)
check("proxy: KEEP domain gốc lúc này", "javis.vietmycollege.com" in prox)
check("split: đòi DNS quan", "SPLIT_FAIL" in spl and "javis-quan.vietmycollege.com" in spl)
check("split: DNS không phụ thuộc dig", "getent ahostsv4" in spl and "dig +short" not in spl)
check("split: external overlay", "tenant-external.yml" in spl)
wf = body(".github/workflows/org-split-javis-quan.yml")
check("org-split workflow: VPS_HOST (máy hiện tại)", "secrets.VPS_HOST" in wf)
check("org-split workflow: không SSH máy cũ", "secrets.VPS_OLD" not in wf)
check("org-split workflow: confirm ORG_SPLIT_JAVIS", "ORG_SPLIT_JAVIS" in wf)
check("org-split workflow: phase backup/proxy/split", "backup" in wf and "proxy" in wf)

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_org_cutover_preflight")
