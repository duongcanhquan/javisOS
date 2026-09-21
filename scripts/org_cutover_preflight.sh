#!/usr/bin/env bash
# Chỉ ĐỌC. Exit 1 nếu thiếu 4 volume não. Không rm volume, không down.
set -euo pipefail

echo "== org cutover preflight =="
hostname
date -Is

need=(javis_javis-data javis_javis-brains javis_claude-auth javis_codex-auth)
miss=0
for v in "${need[@]}"; do
  if docker volume inspect "$v" >/dev/null 2>&1; then
    echo "OK volume $v"
  else
    echo "MISSING volume $v"
    miss=1
  fi
done
if [ "$miss" != 0 ]; then
  echo "PREFLIGHT_FAIL: thiếu volume não"
  exit 1
fi

CNAME=javis
if ! docker ps --format '{{.Names}}' | grep -qx javis; then
  if docker ps --format '{{.Names}}' | grep -qx javis-quan; then
    CNAME=javis-quan
  else
    CNAME=$(docker ps --format '{{.Names}}' | grep -E '^javis' | head -1 || true)
  fi
fi
echo "CONTAINER=${CNAME:-none}"
if [ -n "${CNAME:-}" ]; then
  docker inspect "$CNAME" --format '{{range .Mounts}}{{.Name}} {{.Destination}}{{println}}{{end}}' || true
  docker ps --filter "name=^${CNAME}$" --format '{{.Names}} {{.Status}} {{.Image}}'
fi

echo "=== caddy / proxy ==="
docker ps -a --format '{{.Names}} {{.Status}}' | grep -E 'caddy|proxy|javis' || true

echo "=== disk ==="
df -h / | tail -1

echo "PREFLIGHT_OK"
