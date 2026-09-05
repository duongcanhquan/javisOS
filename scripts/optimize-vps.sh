#!/usr/bin/env bash
# Kiểm tra + tối ưu Javis trên VPS (cloud-first: Antigravity, không Ollama local).
# Idempotent. Chạy trên host trong thư mục repo sau deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTAINER="${JAVIS_CONTAINER:-javis}"
ENV_FILE="${JAVIS_ENV_FILE:-$ROOT/.env}"

echo "============================================"
echo " Javis VPS optimize (cloud-first)"
echo "============================================"

RAM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
RAM_GB=$(awk -v m="$RAM_MB" 'BEGIN { printf "%.1f", m/1024 }')
FREE_GB=$(df -BG / 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}' || echo "?")
echo "RAM: ${RAM_GB} GB (${RAM_MB} MB) · đĩa trống: ~${FREE_GB} GB"

# Pixelle (2 container + build nặng) mặc định TẮT trên VPS để nhường RAM/CPU cho chat + UI.
# Bật lại: đặt JAVIS_ENABLE_PIXELLE=true trong .env rồi redeploy.
echo
echo "==> Pixelle off (giải phóng RAM/CPU)"
touch "$ENV_FILE"
if grep -q '^JAVIS_ENABLE_PIXELLE=' "$ENV_FILE" 2>/dev/null; then
  sed -i.bak 's/^JAVIS_ENABLE_PIXELLE=.*/JAVIS_ENABLE_PIXELLE=false/' "$ENV_FILE" && rm -f "$ENV_FILE.bak"
else
  printf '\nJAVIS_ENABLE_PIXELLE=false\n' >> "$ENV_FILE"
fi
docker rm -f javis-pixelle-api javis-pixelle-web 2>/dev/null || true
if command -v docker >/dev/null 2>&1 && [ -f "$ROOT/docker-compose.yml" ]; then
  (cd "$ROOT" && docker compose -f docker-compose.yml -f docker-compose.pixelle.yml --profile pixelle stop 2>/dev/null) || true
fi

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
echo "  Nhắn tin Telegram/Zalo → cùng Main (Antigravity)"
echo "  Ghi họp               → Moonshine (browser)"
echo "  Tổng kết họp          → Antigravity"
echo "  Pixelle video         → tắt (bật lại bằng JAVIS_ENABLE_PIXELLE=true)"
echo "  Ollama local          → đã gỡ khỏi VPS"
echo "============================================"
