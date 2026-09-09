#!/usr/bin/env bash
# Xuất PDF hướng dẫn từ HTML (cần Google Chrome trên Mac).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIR="$ROOT/docs/huong-dan"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [[ ! -x "$CHROME" ]]; then
  echo "Không tìm thấy Google Chrome tại: $CHROME" >&2
  exit 1
fi
export_pdf() {
  local html="$1" pdf="$2"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$DIR/$pdf" "file://$DIR/$html"
  echo "OK $pdf ($(wc -c <"$DIR/$pdf") bytes)"
}
export_pdf "HUONG-DAN-CAI-DAT-Javis-OS.html" "HUONG-DAN-CAI-DAT-Javis-OS.pdf"
export_pdf "HUONG-DAN-SU-DUNG.html" "HUONG-DAN-SU-DUNG-Javis-OS.pdf"
echo "Xong. Thư mục: $DIR"
