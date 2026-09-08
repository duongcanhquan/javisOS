#!/usr/bin/env bash
# Đồng bộ một chiều Google Drive folder → thư mục corpus local/VPS.
# Dùng bởi Javis Kho Drive (server/drive_projects.py).
#
# Biến môi trường:
#   RCLONE_REMOTE     mặc định gdrive:
#   DRIVE_FOLDER_ID   ID thư mục Drive (bắt buộc)
#   DRIVE_SYNC_DIR    thư mục đích trên máy (bắt buộc)
#
# Ví dụ:
#   export RCLONE_REMOTE=gdrive:
#   export DRIVE_FOLDER_ID=1AbCdEf...
#   export DRIVE_SYNC_DIR=/data/state/drive-corpus/Brain-Default/khoa-hoc
#   ./scripts/sync-drive-project.sh
set -euo pipefail

REMOTE="${RCLONE_REMOTE:-gdrive:}"
DEST="${DRIVE_SYNC_DIR:-}"
FOLDER_ID="${DRIVE_FOLDER_ID:-}"

if [ -z "$DEST" ] || [ -z "$FOLDER_ID" ]; then
  echo "ERROR: cần DRIVE_SYNC_DIR và DRIVE_FOLDER_ID" >&2
  exit 2
fi

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
