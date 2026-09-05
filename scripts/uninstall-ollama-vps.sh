#!/usr/bin/env bash
# Gỡ Ollama local trên VPS: dừng service, xóa model (giải phóng đĩa), xóa cấu hình Javis.
# Idempotent. Chạy trên host trong thư mục repo.
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"

echo "============================================"
echo " Gỡ Ollama local khỏi VPS"
echo "============================================"

# --- Dừng và tắt systemd ---
if systemctl list-unit-files ollama.service 2>/dev/null | grep -q ollama; then
  echo "==> Dừng ollama.service"
  systemctl stop ollama 2>/dev/null || true
  systemctl disable ollama 2>/dev/null || true
fi

# --- Xóa model (giải phóng vài GB) ---
if command -v ollama >/dev/null 2>&1; then
  echo "==> Xóa model Ollama"
  ollama list 2>/dev/null | awk 'NR>1 {print $1}' | while read -r _m; do
    [ -n "$_m" ] || continue
    echo "  - rm $_m"
    ollama rm "$_m" 2>/dev/null || true
  done
  ollama ps 2>/dev/null | awk 'NR>1 {print $1}' | while read -r _m; do
    [ -n "$_m" ] || continue
    ollama stop "$_m" 2>/dev/null || true
  done
fi

# --- Xóa drop-in systemd tối ưu Javis ---
if [ -f /etc/systemd/system/ollama.service.d/javis-optimize.conf ]; then
  rm -f /etc/systemd/system/ollama.service.d/javis-optimize.conf
  systemctl daemon-reload 2>/dev/null || true
  echo "==> Đã xóa javis-optimize.conf"
fi

# --- Gỡ binary (tuỳ chọn, giữ lại nếu không có) ---
if command -v ollama >/dev/null 2>&1 && [ "${JAVIS_OLLAMA_PURGE_BINARY:-1}" = "1" ]; then
  echo "==> Gỡ binary Ollama"
  if [ -x /usr/local/bin/ollama ]; then
    rm -f /usr/local/bin/ollama 2>/dev/null || true
  fi
  if [ -d /usr/share/ollama ]; then
    rm -rf /usr/share/ollama 2>/dev/null || true
  fi
  if [ -d "${HOME}/.ollama" ]; then
    echo "==> Xóa ~/.ollama (model cache)"
    rm -rf "${HOME}/.ollama" 2>/dev/null || true
  fi
  if [ -d /root/.ollama ]; then
    rm -rf /root/.ollama 2>/dev/null || true
  fi
fi

# --- Xóa cấu hình Ollama trong Javis ---
if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "==> Xóa ollama_local_* trong settings Javis"
  docker exec -i -u javis "$CONTAINER" python - <<'PY'
import sys
sys.path.insert(0, "/app/server")
import config as cfg

s = cfg.read_settings()
m = s.setdefault("model", {})
cleared = []
for k in (
    "ollama_local_endpoint",
    "ollama_local_key",
    "ollama_local_num_ctx",
    "ollama_local_keep_alive",
    "ollama_local_max_tool_rounds",
    "ollama_local_specs",
    "ollama_local_http_timeout",
):
    if m.pop(k, None) is not None:
        cleared.append(k)
if cleared:
    cfg.write_settings(s)
    print("cleared:", ", ".join(cleared))
else:
    print("settings: không có ollama_local_*")
PY
else
  echo "WARN: container '$CONTAINER' không chạy - bỏ qua xóa settings"
fi

echo
echo "==> Đĩa sau gỡ"
df -h / 2>/dev/null | awk 'NR==1 || /^\/dev/'
echo
echo "XONG - Ollama local đã gỡ. Dùng Antigravity / model cloud ở trang Models."
