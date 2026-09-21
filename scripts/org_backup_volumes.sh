#!/usr/bin/env bash
# Tar 4 volume não ra /var/backups. Không volume rm, không stop Javis (tar mount ro).
set -euo pipefail

need=(javis_javis-data javis_javis-brains javis_claude-auth javis_codex-auth)
for v in "${need[@]}"; do
  docker volume inspect "$v" >/dev/null
done

STAMP=$(date +%Y%m%d-%H%M%S)
OUT_DIR="${JAVIS_BACKUP_DIR:-/var/backups}"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/javis-quan-${STAMP}.tgz"
echo "== backup $OUT =="

# Cần vài GB trống.
avail_kb=$(df -Pk "$OUT_DIR" | awk 'NR==2 {print $4}')
if [ "${avail_kb:-0}" -lt 4000000 ]; then
  echo "BACKUP_FAIL: còn dưới ~4GB tại $OUT_DIR"
  exit 1
fi

docker volume rm javis_org_backup_scratch 2>/dev/null || true
docker volume create javis_org_backup_scratch >/dev/null
docker run --rm \
  -v javis_javis-data:/in/data:ro \
  -v javis_javis-brains:/in/brains:ro \
  -v javis_claude-auth:/in/claude:ro \
  -v javis_codex-auth:/in/codex:ro \
  -v javis_org_backup_scratch:/out \
  alpine sh -c 'set -e; tar -C /in -czf /out/javis-quan.tgz data brains claude codex; ls -lh /out/javis-quan.tgz'

docker run --rm -v javis_org_backup_scratch:/out -v "$OUT_DIR":/bak alpine \
  sh -c "cp /out/javis-quan.tgz /bak/javis-quan-${STAMP}.tgz && ls -lh /bak/javis-quan-${STAMP}.tgz"
docker volume rm javis_org_backup_scratch

ls -lh "$OUT"
echo "BACKUP_OK $OUT"
