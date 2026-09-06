#!/usr/bin/env bash
# Seed workflows/agents/skill xuat-goi (nghiên cứu + thiết kế) vào MỌI brain trong /brains trên VPS.
# Caps chuẩn dùng chung; Memory/Sources vẫn riêng từng brain. Idempotent (overwrite=True).
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE="$ROOT/deploy/caps-bundles/javis-workflows-nghien-cuu-va-thiet-ke.zip"

echo "==> container hint: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  CONTAINER=$(docker ps --format '{{.Names}}' | grep -E 'javis' | head -1 || true)
fi
if [ -z "${CONTAINER}" ]; then
  echo "ERROR: không thấy container javis đang chạy"
  exit 1
fi
echo "==> dùng container: $CONTAINER"

if [ ! -f "$BUNDLE" ]; then
  echo "ERROR: thiếu bundle $BUNDLE (cần git pull bản có deploy/caps-bundles/)"
  exit 1
fi

docker cp "$BUNDLE" "$CONTAINER:/tmp/javis-workflows-nghien-cuu-va-thiet-ke.zip"

docker exec -i -u javis "$CONTAINER" python - <<'PY'
from pathlib import Path
import os, sys
sys.path.insert(0, "/app/server")
import share_bundle
import system_sync

brains_root = Path(os.environ.get("BRAINS_DIR", "/brains"))
bundle = Path("/tmp/javis-workflows-nghien-cuu-va-thiet-ke.zip")
data = bundle.read_bytes()

# Mọi thư mục con của /brains (bỏ file lẻ). Brain mới tự nhận caps chuẩn.
dirs = sorted(
    p for p in brains_root.iterdir()
    if p.is_dir() and not p.name.startswith(".")
)
if not dirs:
    print(f"WARN: không thấy brain nào trong {brains_root}", flush=True)

for root in dirs:
    name = root.name
    for d in ("agents", "workflows", "skills", "memory", "sources", "attachments", "Javis"):
        (root / d).mkdir(parents=True, exist_ok=True)
    mem = root / "memory" / "MEMORY.md"
    if not mem.exists():
        mem.write_text(f"# MEMORY\n\nIndex ký ức - {name}.\n", encoding="utf-8")
    try:
        system_sync.sync_brain(str(root))
    except Exception as e:
        print(f"[sync] {name}: {e}", flush=True)
    result = share_bundle.import_bundle(
        data, bundle.name,
        agents_dir=root / "agents",
        workflows_dir=root / "workflows",
        skills_root=root / "skills",
        overwrite=True,
    )
    print(f"==> {name}: {result}", flush=True)

print("DONE", flush=True)
PY

echo "==> seed marketing/AI caps xong"
