#!/usr/bin/env bash
# Chỉ ĐỌC + đề xuất. Không xóa volume/container/image.
# Phân loại volume Javis: đang gắn / thuộc sổ / mồ côi / hệ thống.
set -euo pipefail

echo "=== DISK ==="
date -u
df -h / | head -2
echo
docker system df || true
echo

echo "=== CONTAINERS javis-* ==="
docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Image}}' | grep -E '^javis-|NAMES' || true
echo

echo "=== VOLUME STATS ==="
total=$(docker volume ls -q | wc -l | tr -d ' ')
dangling=$(docker volume ls -qf dangling=true | wc -l | tr -d ' ')
javis_n=$(docker volume ls -q | grep -E 'javis' | wc -l | tr -d ' ' || true)
echo "volumes_total=$total dangling_unused=$dangling javis_named=$javis_n"
echo

# Sổ người trên manager (nếu có)
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
  echo "=== REGISTRY SLUGS ==="
  echo "$SLUGS" | sed '/^$/d' | wc -l | awk '{print "tenants_in_registry",$1}'
  echo "$SLUGS" | sed '/^$/d' | head -40
  echo
fi

echo "=== VOLUME CLASSIFY (name only; size via system df above) ==="
# Hệ thống / quan / manager - CẤM xóa
protected='javis_javis-data|javis_javis-brains|javis_claude-auth|javis_codex-auth|caddy|javis_caddy'
keep=0; orphan_tenant=0; anon=0; other=0
while IFS= read -r v; do
  [ -n "$v" ] || continue
  if echo "$v" | grep -Eq "$protected"; then
    keep=$((keep+1))
    continue
  fi
  # volume tenant: javis-<slug>_javis-data|brains|claude-auth|codex-auth
  if echo "$v" | grep -Eq '^javis-[a-z0-9-]+_(javis-data|javis-brains|claude-auth|codex-auth)$'; then
    slug=$(echo "$v" | sed -E 's/^javis-//; s/_(javis-data|javis-brains|claude-auth|codex-auth)$//')
    if echo "$SLUGS" | grep -qx "$slug"; then
      keep=$((keep+1))
    else
      orphan_tenant=$((orphan_tenant+1))
      echo "ORPHAN_TENANT $v"
    fi
    continue
  fi
  # volume ẩn Docker (64 hex) thường là dangling
  if echo "$v" | grep -Eq '^[a-f0-9]{64}$'; then
    anon=$((anon+1))
    continue
  fi
  other=$((other+1))
  echo "OTHER $v"
done < <(docker volume ls -q)

echo
echo "=== SUMMARY ==="
echo "keep_or_protected≈$keep orphan_tenant_volumes=$orphan_tenant anon_hex=$anon other=$other dangling_flag=$dangling"
echo
echo "=== ĐỀ XUẤT (chưa làm gì) ==="
echo "1) An toàn: docker image prune -f + builder prune -af (đã có nút Dọn ổ)."
echo "2) Volume dangling/anon: có thể nhả ~phần RECLAIMABLE của Local Volumes - CẦN duyệt từng nhóm, không volume prune mù."
echo "3) ORPHAN_TENANT: volume máy không còn trong sổ - chỉ xóa khi xác nhận không cần khôi phục não."
echo "4) CẤM: volume prune -a; cấm xóa javis_javis-* / caddy / quan."
echo AUDIT_DOCKER_DISK_DONE
