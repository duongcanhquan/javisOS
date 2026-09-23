#!/usr/bin/env bash
# Moonshine 0.1.5: pthreadPoolSize = hardwareConcurrency → 8–16 worker, mỗi cái
# nạp lại moonshine.wasm → treo ở loadWasmModuleToAllWorkers (UI đếm giây mãi).
# Giới hạn 2 worker. Idempotent. Chạy trên máy cá nhân và mọi container javis-* đang chạy
# (trừ proxy/park) để tenant không bị treo trong khi máy quan thì không.
set -euo pipefail
CONTAINER="${JAVIS_CONTAINER:-${JAVIS_NAME:-javis}}"

patch_one() {
  local name="$1"
  if ! docker ps --format '{{.Names}}' | grep -qx "$name"; then
    echo "WARN: container $name chưa chạy"
    return 0
  fi
  echo "==> patch Moonshine WASM $name"
  docker exec -u root "$name" python3 - <<'PY'
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
    raise SystemExit("moonshine pthread: pattern missing, kiem tra version wasm")
else:
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("moonshine pthread: patched, max 2 workers")
PY
}

patch_one "$CONTAINER"
while IFS= read -r name; do
  [ -n "$name" ] || continue
  case "$name" in
    javis-proxy|javis-park|"$CONTAINER") continue ;;
  esac
  patch_one "$name" || echo "WARN: patch $name"
done < <(docker ps --format '{{.Names}}' 2>/dev/null | grep -E '^javis-' || true)
