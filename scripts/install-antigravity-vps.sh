#!/usr/bin/env bash
# Cài Antigravity CLI (`agy`) vào container Javis trên Ubuntu/VPS.
# Binary + đăng nhập được giữ qua update nhờ docker/entrypoint.sh (symlink /data/home).
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy. Bật Javis trước: docker compose up -d"
  exit 1
fi

echo "==> đảm bảo bash trong container"
docker exec -u root "$CONTAINER" sh -c '
  command -v bash >/dev/null 2>&1 || {
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq bash ca-certificates curl
  }
'

echo "==> cài agy (user javis, persist ~/.local → /data/home)"
docker exec -u javis "$CONTAINER" bash -lc '
  export PATH="$HOME/.local/bin:$PATH"
  if command -v agy >/dev/null 2>&1; then
    echo "agy đã có: $(agy --version 2>&1 | head -1)"
    exit 0
  fi
  curl -fsSL https://antigravity.google/cli/install.sh | bash
  export PATH="$HOME/.local/bin:$PATH"
  command -v agy >/dev/null 2>&1 || { echo "ERROR: cài xong mà không thấy agy"; exit 1; }
  agy --version | head -1
'

echo "==> kiểm tra Javis thấy binary"
docker exec -u javis "$CONTAINER" bash -lc '
  test -x "$HOME/.local/bin/agy" && echo "OK: $HOME/.local/bin/agy"
'

echo ""
echo "==> XONG cài agy."
echo "    Bước tiếp (đăng nhập Google 1 lần):"
echo "      docker exec -it -u javis $CONTAINER bash -lc agy"
echo "    Hoặc trong Javis: App terminal → gõ: agy"
echo "    Xong quay lại Models → Antigravity CLI → Kiểm tra lại"
