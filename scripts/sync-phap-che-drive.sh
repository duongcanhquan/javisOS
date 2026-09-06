#!/usr/bin/env bash
# Đồng bộ một chiều Google Drive (folder Phap-che) → thư mục local/VPS cho RAG / extract.
# Không commit PDF vào git brain. Cần rclone đã cấu hình remote.
#
# Ví dụ:
#   export RCLONE_REMOTE=gdrive:Phap-che
#   export PHAP_CHE_SYNC_DIR=/root/javis-data/phap-che-corpus
#   ./scripts/sync-phap-che-drive.sh
set -euo pipefail

REMOTE="${RCLONE_REMOTE:-gdrive:Phap-che}"
DEST="${PHAP_CHE_SYNC_DIR:-/root/javis-data/phap-che-corpus}"

if ! command -v rclone >/dev/null 2>&1; then
  echo "ERROR: chưa cài rclone. https://rclone.org/install/" >&2
  exit 1
fi

mkdir -p "$DEST"
echo "==> rclone sync $REMOTE → $DEST"
rclone sync "$REMOTE" "$DEST" \
  --create-empty-src-dirs \
  --fast-list \
  --transfers 4 \
  --checkers 8 \
  --exclude ".DS_Store" \
  --exclude "Thumbs.db" \
  -v

echo "OK — corpus tại $DEST"
echo "Gợi ý: trỏ RAG-Anything / LightRAG index vào thư mục này;"
echo "      set JAVIS_PHAP_CHE_RAG_URL=http://127.0.0.1:8001  (xem docs/28-phap-che-ca-nhan.md)"
