#!/usr/bin/env bash
# Đồng bộ một chiều Google Drive (folder pháp chế) → thư mục local/VPS cho RAG / extract.
# Không commit PDF vào git brain. Cần rclone đã cấu hình remote.
#
# Folder mặc định: RAG VĂN BẢN
#   https://drive.google.com/drive/folders/1NwpPUVxnGJfQER-5qKg0ejw7ry57pcGM
#
# Ví dụ:
#   export RCLONE_REMOTE=gdrive:          # remote đã rclone config
#   export PHAP_CHE_DRIVE_FOLDER_ID=1NwpPUVxnGJfQER-5qKg0ejw7ry57pcGM
#   export PHAP_CHE_SYNC_DIR=/root/javis-data/phap-che-corpus
#   ./scripts/sync-phap-che-drive.sh
set -euo pipefail

REMOTE="${RCLONE_REMOTE:-gdrive:}"
DEST="${PHAP_CHE_SYNC_DIR:-/root/javis-data/phap-che-corpus}"
FOLDER_ID="${PHAP_CHE_DRIVE_FOLDER_ID:-1NwpPUVxnGJfQER-5qKg0ejw7ry57pcGM}"

if ! command -v rclone >/dev/null 2>&1; then
  echo "ERROR: chưa cài rclone. https://rclone.org/install/" >&2
  exit 1
fi

mkdir -p "$DEST"
echo "==> rclone sync $REMOTE (folder-id=$FOLDER_ID) → $DEST"
rclone sync "$REMOTE" "$DEST" \
  --drive-root-folder-id "$FOLDER_ID" \
  --create-empty-src-dirs \
  --fast-list \
  --transfers 4 \
  --checkers 8 \
  --exclude ".DS_Store" \
  --exclude "Thumbs.db" \
  -v

echo "OK — corpus tại $DEST"
echo "Gợi ý Pha A: extract PDF → sources/phap-che/<linh-vuc>/*.md rồi ingest."
echo "Gợi ý Pha B: index RAG rồi set JAVIS_PHAP_CHE_RAG_URL (docs/28-phap-che-ca-nhan.md)."
