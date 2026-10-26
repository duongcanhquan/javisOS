#!/usr/bin/env bash
# Nhả ổ đĩa gấp trên VPS (100% full → scp/wake/agy đều chết).
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

echo "=== Docker: container dừng + image treo + build cache ==="
# Không xóa volume tenant (não).
docker container prune -f || true
docker image prune -af || true
docker builder prune -af || true
# Xóa image tag cũ ghcr không còn container dùng (giữ latest đang gắn)
docker images 'ghcr.io/duongcanhquan/javisos' --format '{{.ID}} {{.Repository}}:{{.Tag}} {{.CreatedSince}}' || true

echo "=== Log container lớn ==="
du -sh /var/lib/docker/containers/*/*-json.log 2>/dev/null | sort -hr | head -15 || true
# Cắt log JSON Docker quá 50MB
find /var/lib/docker/containers -name '*-json.log' -size +50M 2>/dev/null | while read -r f; do
  echo "truncate $f"
  : > "$f" || true
done

echo "=== Thư mục nặng ==="
du -xhd1 / 2>/dev/null | sort -hr | head -15 || true
du -xhd1 /var 2>/dev/null | sort -hr | head -10 || true
du -xhd1 /var/lib/docker 2>/dev/null | sort -hr | head -10 || true

echo "=== DISK SAU ==="
df -h / | head -2
docker system df || true
echo FREE_DISK_DONE
