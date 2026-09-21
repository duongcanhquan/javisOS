#!/usr/bin/env bash
# Xoá container / volume / image / thư mục Javis trên MÁY ĐANG CHẠY script.
# An toàn: từ chối nếu IP công của máy trùng WIPE_REFUSE_IP (VPS mới).
set -euo pipefail

if [ -n "${WIPE_REFUSE_IP:-}" ]; then
  MYIP="$(curl -4 -fsS -m 8 https://api.ipify.org 2>/dev/null || curl -4 -fsS -m 8 https://ifconfig.me 2>/dev/null || true)"
  if [ -n "$MYIP" ] && [ "$MYIP" = "$WIPE_REFUSE_IP" ]; then
    echo "REFUSE: máy này là VPS mới ($MYIP) - không xoá Javis"
    exit 1
  fi
  echo "wipe ok: public_ip=${MYIP:-unknown} != refuse"
fi

echo "== hostname $(hostname) =="

wipe_compose() {
  local d="$1"
  if [ -d "$d" ] && [ -f "$d/docker-compose.yml" ]; then
    echo "compose down -v: $d"
    (cd "$d" && docker compose down -v --remove-orphans) || true
    (cd "$d" && docker compose -f docker-compose.yml down -v --remove-orphans) || true
  fi
}

wipe_compose "${HOME}/javis-os"
wipe_compose /root/javis-os
wipe_compose "${HOME}/javis"
wipe_compose /root/javis
wipe_compose /opt/javis

if command -v docker >/dev/null 2>&1; then
  echo "== containers javis =="
  while read -r n; do
    [ -n "$n" ] || continue
    echo "rm -f $n"
    docker rm -f "$n" || true
  done < <(docker ps -a --format '{{.Names}}' | grep -E 'javis' || true)

  echo "== volumes javis =="
  while read -r v; do
    [ -n "$v" ] || continue
    echo "volume rm $v"
    docker volume rm -f "$v" || true
  done < <(docker volume ls -q | grep -E 'javis' || true)

  echo "== images javis =="
  while read -r spec id; do
    [ -n "${id:-}" ] || continue
    echo "rmi $spec"
    docker rmi -f "$id" || true
  done < <(docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -iE 'javis' || true)
fi

echo "== dirs =="
for d in "${HOME}/javis-os" /root/javis-os "${HOME}/javis" /root/javis /opt/javis; do
  if [ -e "$d" ]; then
    echo "rm -rf $d"
    rm -rf "$d"
  fi
done

if [ -d /etc/nginx/sites-enabled ]; then
  shopt -s nullglob
  for f in /etc/nginx/sites-enabled/*javis* /etc/nginx/sites-available/*javis*; do
    echo "nginx site $f"
    rm -f "$f"
  done
  shopt -u nullglob
  nginx -t >/dev/null 2>&1 && systemctl reload nginx || true
fi

echo "=== remaining javis containers ==="
if command -v docker >/dev/null 2>&1; then
  docker ps -a --format '{{.Names}} {{.Status}}' | grep -E 'javis' || echo none
  echo "=== remaining javis volumes ==="
  docker volume ls | grep -E 'javis' || echo none
fi
echo WIPE_JAVIS_DONE
