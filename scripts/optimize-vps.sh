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

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

# --- Gỡ Ollama local (nếu còn) ---
if [ -f "$ROOT/scripts/uninstall-ollama-vps.sh" ]; then
  echo
  echo "==> Gỡ Ollama local (giải phóng RAM + đĩa)"
  chmod +x "$ROOT/scripts/uninstall-ollama-vps.sh"
  bash "$ROOT/scripts/uninstall-ollama-vps.sh" || echo "WARN: uninstall-ollama skipped"
fi

# --- Javis settings: routing cloud ---
echo
echo "==> Áp phân tầng model (Main + Việc nền = Antigravity)"
if [ -f "$ROOT/scripts/apply-model-routing-vps.sh" ]; then
  chmod +x "$ROOT/scripts/apply-model-routing-vps.sh"
  bash "$ROOT/scripts/apply-model-routing-vps.sh" || echo "WARN: apply-model-routing skipped"
fi

echo
echo "==> Kiểm tra settings trong container"
docker exec -i -u javis "$CONTAINER" python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import config as cfg

s = cfg.read_settings()
m = s.get("model") or {}
print("main:", m.get("main"))
print("auxiliary:", m.get("auxiliary"))
ep = (m.get("ollama_local_endpoint") or "").strip()
print("ollama_local_endpoint:", ep or "(đã xóa - OK)")
if ep:
    print("WARN: vẫn còn ollama_local_endpoint - chạy lại uninstall-ollama-vps.sh")
PY

echo
echo "==> Health snapshot"
if [ -f "$ROOT/scripts/check-vps-health.sh" ]; then
  chmod +x "$ROOT/scripts/check-vps-health.sh"
  bash "$ROOT/scripts/check-vps-health.sh" 2>&1 | tail -40 || true
fi

echo
echo "============================================"
echo " XONG - gợi ý sử dụng (VPS ${RAM_GB}GB)"
echo "  Chat / MCP / việc nền  → Antigravity (Main)"
echo "  Ghi họp               → Moonshine (browser)"
echo "  Tổng kết họp          → Antigravity (nhanh hơn Ollama CPU)"
echo "  Ollama local          → đã gỡ khỏi VPS"
echo "============================================"
