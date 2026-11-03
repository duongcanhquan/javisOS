#!/usr/bin/env bash
# Nhả ổ đĩa trên VPS — bản sâu.
# AN TOÀN: không container prune; không xóa volume tên javis/caddy đang gắn hoặc còn trong sổ.
set -euo pipefail

echo "=== DISK TRƯỚC ==="
date -u
df -h / | head -2
docker system df || true
echo

echo "=== TOP /var/lib/docker ==="
du -xh /var/lib/docker --max-depth=1 2>/dev/null | sort -h | tail -12 || true
echo

echo "=== journal / apt / tmp / var-log ==="
journalctl --vacuum-size=50M 2>/dev/null || true
apt-get clean 2>/dev/null || true
rm -rf /var/cache/apt/archives/*.deb /tmp/javis-* /tmp/*.tar.gz /tmp/drone-* 2>/dev/null || true
find /var/log -type f \( -name '*.gz' -o -name '*.old' \) -delete 2>/dev/null || true
find /var/log -type f -size +30M -print -exec truncate -s 0 {} \; 2>/dev/null || true

echo "=== truncate docker json logs >10M ==="
nlog=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  echo "truncate $f"
  : > "$f" || true
  nlog=$((nlog + 1))
done < <(find /var/lib/docker/containers -name '*-json.log' -size +10M 2>/dev/null || true)
echo "truncated_logs=$nlog"

echo "=== docker: image KHÔNG dùng + build cache (KHÔNG container prune) ==="
# -a: mọi image không gắn container (kể cả tagged cũ). Image đang dùng bởi
# container tắt/chạy vẫn giữ — máy người Exited vẫn start được.
docker image prune -af || true
docker builder prune -af || true

echo "=== volume anon dangling (hex 64) — CẤM tên javis/caddy/proxy ==="
mapfile -t ALL_DANGLE < <(docker volume ls -qf dangling=true || true)
SAFE=()
BLOCKED=0
for v in "${ALL_DANGLE[@]+"${ALL_DANGLE[@]}"}"; do
  [ -n "$v" ] || continue
  if echo "$v" | grep -Eiq 'javis|caddy|proxy|quan|manager|moonshine|ollama'; then
    BLOCKED=$((BLOCKED + 1))
    continue
  fi
  if echo "$v" | grep -Eq '^[a-f0-9]{64}$'; then
    SAFE+=("$v")
  fi
done
deleted=0
fail=0
for v in "${SAFE[@]+"${SAFE[@]}"}"; do
  if docker volume rm "$v" >/dev/null 2>&1; then
    deleted=$((deleted + 1))
  else
    fail=$((fail + 1))
  fi
done
echo "anon_deleted=$deleted anon_fail=$fail named_dangling_kept=$BLOCKED"

echo "=== sổ người (manager) — volume tenant mồ côi tên javis-<slug>_* ==="
SLUGS=""
if docker ps --format '{{.Names}}' | grep -qx javis-manager; then
  SLUGS=$(docker exec javis-manager python -c '
import sys
sys.path.insert(0,"/app/server")
import org_tenants as ot
for t in (ot.load().get("tenants") or []):
    s=(t.get("slug") or "").strip().lower()
    if s: print(s)
' 2>/dev/null || true)
fi
# Volume gắn bất kỳ container nào (kể cả Exited) — giữ
MOUNTED=""
for c in $(docker ps -a --format '{{.Names}}' 2>/dev/null || true); do
  MOUNTED="$MOUNTED $(docker inspect -f '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}} {{end}}{{end}}' "$c" 2>/dev/null || true)"
done
orphan_rm=0
orphan_keep=0
while IFS= read -r v; do
  [ -n "$v" ] || continue
  # chỉ tenant named: javis-<slug>_javis-data|brains|claude-auth|codex-auth
  if ! echo "$v" | grep -Eq '^javis-[a-z0-9-]+_(javis-data|javis-brains|claude-auth|codex-auth)$'; then
    continue
  fi
  slug=$(echo "$v" | sed -E 's/^javis-//; s/_(javis-data|javis-brains|claude-auth|codex-auth)$//')
  # hệ thống / quan
  if echo "$slug" | grep -Eq '^(quan|manager|park|proxy)$'; then
    continue
  fi
  if echo " $MOUNTED " | grep -q " $v "; then
    continue
  fi
  if echo "$SLUGS" | grep -qx "$slug"; then
    orphan_keep=$((orphan_keep + 1))
    continue
  fi
  # Không còn trong sổ + không gắn container → xóa volume mồ côi
  sz=$(du -sh "/var/lib/docker/volumes/$v/_data" 2>/dev/null | awk '{print $1}' || echo "?")
  if docker volume rm "$v" >/dev/null 2>&1; then
    echo "ORPHAN_RM $sz $v"
    orphan_rm=$((orphan_rm + 1))
  else
    echo "ORPHAN_FAIL $v"
  fi
done < <(docker volume ls -q | grep -E '^javis-' || true)
echo "orphan_tenant_removed=$orphan_rm orphan_named_in_registry_unmounted=$orphan_keep"

echo "=== TOP volume javis theo dung lượng (báo cáo) ==="
while IFS= read -r v; do
  [ -n "$v" ] || continue
  sz=$(du -sb "/var/lib/docker/volumes/$v/_data" 2>/dev/null | awk '{print $1}' || echo 0)
  echo "$sz $v"
done < <(docker volume ls -q | grep -E 'javis' || true) \
  | sort -n | tail -20 \
  | while read -r b name; do
      awk -v b="$b" -v n="$name" 'BEGIN{
        if (b>=1073741824) printf "%.1fG %s\n", b/1073741824, n;
        else if (b>=1048576) printf "%.0fM %s\n", b/1048576, n;
        else printf "%dK %s\n", (b+1023)/1024, n;
      }'
    done

echo "=== bật lịch dọn tuần (CN 03:00) nếu manager sống ==="
if docker ps --format '{{.Names}}' | grep -qx javis-manager; then
  docker exec javis-manager python -c '
import sys
sys.path.insert(0,"/app/server")
import org_coord as oc
s = oc.put_disk_cleanup(weekly=True, mode="daily", weekday=6, hour=3)
print("disk_cleanup", s.get("weekly"), "mode", s.get("mode"), "hour", s.get("hour"),
      "last_run", s.get("last_run_at"))
' 2>/dev/null || echo "WARN enable daily cleanup failed"
fi

echo "=== DISK SAU ==="
df -h / | head -2
docker system df || true
echo FREE_DISK_DONE
