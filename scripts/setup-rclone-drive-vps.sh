#!/usr/bin/env bash
# Cài rclone trên VPS và hướng dẫn cấu hình remote Google Drive cho Kho Drive Javis.
# Chạy trên host VPS (không trong container), với quyền root hoặc user có PATH rclone.
#
#   bash scripts/setup-rclone-drive-vps.sh
set -euo pipefail

echo "==> Kiểm tra / cài rclone"
if ! command -v rclone >/dev/null 2>&1; then
  curl -fsSL https://rclone.org/install.sh | bash
else
  echo "    rclone đã có: $(command -v rclone) ($(rclone version 2>/dev/null | head -1))"
fi

echo ""
echo "==> Cấu hình remote (một lần)"
echo "    Chạy:  rclone config"
echo "    - n (new remote)"
echo "    - name: gdrive   (Javis mặc định remote gdrive:)"
echo "    - Storage: Google Drive"
echo "    - client_id/secret: để trống (dùng mặc định rclone) hoặc OAuth của bạn"
echo "    - scope: 1 (Full access) hoặc 2 (Drive) tùy nhu cầu"
echo "    - Trên VPS headless: chọn auto config = n, rồi dán token từ máy có browser"
echo ""
echo "    Kiểm tra:  rclone listremotes"
echo "               rclone lsd gdrive: --drive-root-folder-id <FOLDER_ID>"
echo ""
echo "==> Trong Javis"
echo "    Bộ não → Kho Drive → tạo kho với đúng Folder ID → Đồng bộ ngay"
echo "    Corpus: /data/state/drive-corpus/… (volume STATE)"
echo "    Sources: <brain>/sources/drive/<slug>/"
echo "    Chi tiết: docs/29-kho-drive.md"
echo ""
echo "OK — xong bước cài. Còn lại là rclone config + tạo kho trong dashboard."
