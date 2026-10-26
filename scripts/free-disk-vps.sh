#!/usr/bin/env bash
# Nhả ổ đĩa trên VPS. AN TOÀN: không xóa container tenant (não giữ trong volume,
# nhưng mất container → bấm Bật máy bị start HTTP 404).
set -euo pipefail

echo "=== DISK TRƯỚC ==="
date -u
df -h / | head -2
docker system df || true

echo "=== Dọn journal / tmp / apt ==="
journalctl --vacuum-size=80M 2>/dev/null || true
rm -rf /tmp/javis-* /tmp/*.tar.gz 2>/dev/null || true
apt-get clean 2>/dev/null || true
rm -rf /var/cache/apt/archives/*.deb 2>/dev/null || true

echo "=== Docker: image treo + build cache (KHÔNG container prune) ==="
docker image prune -f || true
docker builder prune -af || true

echo "=== Cắt log container >50MB ==="
find /var/lib/docker/containers -name '*-json.log' -size +50M 2>/dev/null | while read -r f; do
  echo "truncate $f"
  : > "$f" || true
done

echo "=== DISK SAU ==="
df -h / | head -2
docker system df || true
echo FREE_DISK_DONE
