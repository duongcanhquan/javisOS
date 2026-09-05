#!/usr/bin/env bash
# Kiểm tra + tối ưu Javis trên VPS (cloud-first: Antigravity, không Ollama local).
# Idempotent. Chạy trên host trong thư mục repo sau deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTAINER="${JAVIS_CONTAINER:-javis}"

echo "============================================"
echo " Javis VPS optimize (cloud-first)"
echo "============================================"

RAM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
RAM_GB=$(awk -v m="$RAM_MB" 'BEGIN { printf "%.1f", m/1024 }')
FREE_GB=$(df -BG / 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}' || echo "?")
echo "RAM: ${RAM_GB} GB (${RAM_MB} MB) · đĩa trống: ~${FREE_GB} GB"

# Cleanup gộp: gỡ Ollama local, scrub Llama, routing, prune Docker, verify hàm sống.
if [ -f "$ROOT/scripts/cleanup-vps.sh" ]; then
  echo
  chmod +x "$ROOT/scripts/cleanup-vps.sh"
  bash "$ROOT/scripts/cleanup-vps.sh" || echo "WARN: cleanup-vps skipped"
elif [ -f "$ROOT/scripts/apply-model-routing-vps.sh" ]; then
  echo
  echo "==> Áp phân tầng model (fallback không có cleanup-vps.sh)"
  chmod +x "$ROOT/scripts/apply-model-routing-vps.sh"
  bash "$ROOT/scripts/apply-model-routing-vps.sh" || echo "WARN: apply-model-routing skipped"
fi

echo
echo "==> Health snapshot"
if [ -f "$ROOT/scripts/check-vps-health.sh" ]; then
  chmod +x "$ROOT/scripts/check-vps-health.sh"
  bash "$ROOT/scripts/check-vps-health.sh" 2>&1 | tail -50 || true
fi

echo
echo "============================================"
echo " XONG - gợi ý sử dụng (VPS ${RAM_GB}GB)"
echo "  Chat / MCP / việc nền  → Antigravity (Main)"
echo "  Nhắn tin nhanh         → Groq gpt-oss (nếu có key), không Llama"
echo "  Ghi họp               → Moonshine (browser)"
echo "  Tổng kết họp          → Antigravity"
echo "  Ollama local          → đã gỡ khỏi VPS"
echo "============================================"
