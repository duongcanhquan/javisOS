#!/usr/bin/env bash
# Gỡ Ollama local trên VPS: dừng service, xóa model (giải phóng đĩa), xóa cấu hình Javis.
# Idempotent. Chạy trên host trong thư mục repo.
# KHÔNG gọi `ollama rm` qua API (dễ treo khi service đã stop) — xóa thư mục trực tiếp.
set -uo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
HOST_ONLY="${JAVIS_OLLAMA_HOST_ONLY:-0}"

echo "============================================"
echo " Gỡ Ollama local khỏi VPS"
echo "============================================"

# --- Dừng và tắt systemd ---
if command -v systemctl >/dev/null 2>&1; then
  if systemctl list-unit-files ollama.service 2>/dev/null | grep -q ollama; then
    echo "==> Dừng ollama.service"
    timeout 30 systemctl stop ollama 2>/dev/null || true
    timeout 15 systemctl disable ollama 2>/dev/null || true
  fi
fi

# --- Xóa drop-in systemd tối ưu Javis ---
if [ -f /etc/systemd/system/ollama.service.d/javis-optimize.conf ]; then
  rm -f /etc/systemd/system/ollama.service.d/javis-optimize.conf
  systemctl daemon-reload 2>/dev/null || true
  echo "==> Đã xóa javis-optimize.conf"
fi

# --- Xóa model cache + binary (nhanh, không qua API) ---
if [ -d /root/.ollama ]; then
  echo "==> Xóa /root/.ollama (model cache)"
  rm -rf /root/.ollama 2>/dev/null || true
fi
if [ -n "${HOME:-}" ] && [ -d "${HOME}/.ollama" ] && [ "${HOME}/.ollama" != "/root/.ollama" ]; then
  echo "==> Xóa ${HOME}/.ollama"
  rm -rf "${HOME}/.ollama" 2>/dev/null || true
fi
if [ -d /usr/share/ollama ]; then
  echo "==> Xóa /usr/share/ollama"
  rm -rf /usr/share/ollama 2>/dev/null || true
fi
if [ -x /usr/local/bin/ollama ] || command -v ollama >/dev/null 2>&1; then
  echo "==> Gỡ binary Ollama"
  rm -f /usr/local/bin/ollama 2>/dev/null || true
fi

# --- Xóa cấu hình Ollama trong Javis (cần container đang chạy) ---
if [ "$HOST_ONLY" = "1" ]; then
  echo "==> host-only: bỏ qua docker exec settings"
elif docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
  echo "==> Xóa ollama_local_* trong settings Javis"
  timeout 30 docker exec -i -u javis "$CONTAINER" python - <<'PY' || echo "WARN: docker exec settings failed"
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
  echo "WARN: container '$CONTAINER' chưa chạy - settings xóa ở bước apply-model-routing"
fi

echo
echo "==> Đĩa sau gỡ"
df -h / 2>/dev/null | awk 'NR==1 || /^\/dev/' || true
echo
echo "XONG - Ollama local đã gỡ. Dùng Antigravity / model cloud ở trang Models."
