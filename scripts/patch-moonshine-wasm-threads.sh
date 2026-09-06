#!/usr/bin/env bash
# Moonshine 0.1.5: pthreadPoolSize = hardwareConcurrency → 8–16 worker, mỗi cái
# nạp lại moonshine.wasm → treo ở loadWasmModuleToAllWorkers (UI đếm giây mãi).
# Giới hạn 2 worker. Idempotent.
set -euo pipefail
CONTAINER="${JAVIS_CONTAINER:-javis}"
TARGET="/app/dashboard/vendor/moonshine-wasm/dist/moonshine.mjs"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "WARN: container $CONTAINER chưa chạy"
  exit 0
fi
docker exec -u root "$CONTAINER" python3 - <<'PY'
from pathlib import Path
p = Path("/app/dashboard/vendor/moonshine-wasm/dist/moonshine.mjs")
if not p.is_file():
    raise SystemExit("missing " + str(p))
t = p.read_text(encoding="utf-8", errors="ignore")
old = "var pthreadPoolSize=navigator.hardwareConcurrency;"
new = "var pthreadPoolSize=Math.min(2,navigator.hardwareConcurrency||2);"
if "Math.min(2,navigator.hardwareConcurrency" in t:
    print("moonshine pthread: already patched")
elif old not in t:
    raise SystemExit("moonshine pthread: pattern missing — kiểm tra version wasm")
else:
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("moonshine pthread: patched → max 2 workers")
PY
