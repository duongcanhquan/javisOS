#!/usr/bin/env bash
# Cài GitHub Copilot CLI (`copilot`) vào container Javis trên Ubuntu/VPS.
# Binary nằm ~/.local/bin (persist qua /data/home). Phiên/MCP ở ~/.copilot cũng persist
# sau bản entrypoint có symlink .copilot.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"

echo "==> container: $CONTAINER"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy. Bật Javis trước: docker compose up -d"
  exit 1
fi

echo "==> đảm bảo bash + npm trong container"
docker exec -u root "$CONTAINER" sh -c '
  command -v bash >/dev/null 2>&1 || {
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq bash ca-certificates curl
  }
  command -v npm >/dev/null 2>&1 || { echo "ERROR: container thiếu npm"; exit 1; }
'

echo "==> cài copilot (user javis, prefix ~/.local → persist)"
docker exec -u javis "$CONTAINER" bash -lc '
  set -euo pipefail
  export PATH="$HOME/.local/bin:$PATH"
  mkdir -p "$HOME/.local/bin" "$HOME/.copilot"
  if command -v copilot >/dev/null 2>&1; then
    echo "copilot đã có: $(command -v copilot)"
    copilot --version 2>&1 | head -3 || true
    exit 0
  fi
  # Cài vào ~/.local để sống qua update image (entrypoint link ~/.local → /data/home).
  npm install -g @github/copilot --prefix "$HOME/.local"
  export PATH="$HOME/.local/bin:$PATH"
  command -v copilot >/dev/null 2>&1 || { echo "ERROR: cài xong mà không thấy copilot"; exit 1; }
  copilot --version 2>&1 | head -5 || true
'

echo "==> kiểm tra Javis thấy binary"
docker exec -u javis "$CONTAINER" bash -lc '
  export PATH="$HOME/.local/bin:$PATH"
  test -x "$HOME/.local/bin/copilot" && echo "OK: $HOME/.local/bin/copilot"
  command -v copilot && copilot --help 2>&1 | head -8 || true
'

echo ""
echo "==> XONG cài GitHub Copilot CLI."
echo "    Đăng nhập (bạn tự làm trên Javis / VPS):"
echo "      docker exec -it -u javis $CONTAINER bash -lc '\''export PATH=\"\$HOME/.local/bin:\$PATH\"; copilot login'\''"
echo "    Hoặc tab Code → Terminal trong Javis: copilot login"
echo "    (Hoặc đặt env COPILOT_GITHUB_TOKEN / GH_TOKEN rồi restart container.)"
echo "    Xong: Models → GitHub Copilot CLI → Kiểm tra lại"
