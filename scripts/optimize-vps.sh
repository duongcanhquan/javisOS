#!/usr/bin/env bash
# Kiểm tra + tối ưu Javis trên VPS theo RAM thật (12GB: javis-qwen3-8b, ctx 8192).
# Idempotent. Chạy trên host trong thư mục repo sau deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTAINER="${JAVIS_CONTAINER:-javis}"
MIN_RAM_MB_FOR_8B=10000

echo "============================================"
echo " Javis VPS optimize"
echo "============================================"

RAM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
RAM_GB=$(awk -v m="$RAM_MB" 'BEGIN { printf "%.1f", m/1024 }')
FREE_GB=$(df -BG / 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}' || echo "?")
echo "RAM: ${RAM_GB} GB (${RAM_MB} MB) · đĩa trống: ~${FREE_GB} GB"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' không chạy."
  exit 1
fi

# --- Ollama host ---
if command -v ollama >/dev/null 2>&1; then
  echo
  echo "==> Ollama host"
  ollama --version 2>&1 | head -1 || true
  if curl -fsS -m 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "API: OK"
    ollama list 2>/dev/null | head -8 || true
  else
    echo "WARN: Ollama API chưa lên - thử restart"
    systemctl restart ollama 2>/dev/null || service ollama restart 2>/dev/null || true
    sleep 2
  fi

  # Tối ưu systemd Ollama: 1 model, không parallel (ổn định RAM)
  if [ -d /etc/systemd/system ]; then
    mkdir -p /etc/systemd/system/ollama.service.d
    NUM_CTX=8192
    if [ "$RAM_MB" -lt "$MIN_RAM_MB_FOR_8B" ]; then
      NUM_CTX=4096
    fi
    cat >/etc/systemd/system/ollama.service.d/javis-optimize.conf <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_CONTEXT_LENGTH=${NUM_CTX}"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
EOF
    systemctl daemon-reload 2>/dev/null || true
    systemctl restart ollama 2>/dev/null || true
    echo "systemd: OLLAMA_CONTEXT_LENGTH=${NUM_CTX}, parallel=1"
  fi

  NEED_INSTALL=0
  if [ "$RAM_MB" -ge "$MIN_RAM_MB_FOR_8B" ]; then
    if ! ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "javis-qwen3-8b"; then
      if ! ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "qwen3:8b"; then
        NEED_INSTALL=1
      fi
    fi
  fi
  if [ "$NEED_INSTALL" = "1" ] && [ -f "$ROOT/scripts/install-ollama-vps.sh" ]; then
    echo
    echo "==> Chưa có javis-qwen3-8b → cài Ollama model (12GB)"
    chmod +x "$ROOT/scripts/install-ollama-vps.sh"
    bash "$ROOT/scripts/install-ollama-vps.sh" || echo "WARN: install-ollama skipped"
  fi
else
  echo
  echo "WARN: chưa có lệnh ollama trên host"
  if [ -f "$ROOT/scripts/install-ollama-vps.sh" ]; then
    echo "==> Cài Ollama + model"
    chmod +x "$ROOT/scripts/install-ollama-vps.sh"
    bash "$ROOT/scripts/install-ollama-vps.sh" || echo "WARN: install-ollama failed"
  fi
fi

# --- Javis settings: routing + Ollama tuning ---
echo
echo "==> Áp phân tầng model (Main Antigravity + Ollama việc nền)"
if [ -f "$ROOT/scripts/apply-model-routing-vps.sh" ]; then
  chmod +x "$ROOT/scripts/apply-model-routing-vps.sh"
  bash "$ROOT/scripts/apply-model-routing-vps.sh" || echo "WARN: apply-model-routing skipped"
fi

echo
echo "==> Kiểm tra settings trong container"
docker exec -i -u javis "$CONTAINER" python - <<'PY'
import json, sys
sys.path.insert(0, "/app/server")
import config as cfg
import engine as eng

s = cfg.read_settings()
m = s.get("model") or {}
ram_mb = 0
try:
    with open("/proc/meminfo", encoding="utf-8") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                ram_mb = int(line.split()[1]) // 1024
                break
except OSError:
    pass

print("RAM (container view):", ram_mb, "MB")
print("main:", m.get("main"))
print("auxiliary:", m.get("auxiliary"))
print("ollama_local_endpoint:", m.get("ollama_local_endpoint") or "(trống)")
print("ollama_local_num_ctx:", m.get("ollama_local_num_ctx"), "→ engine:", eng.ollama_local_num_ctx())
print("ollama_local_max_tool_rounds:", m.get("ollama_local_max_tool_rounds"),
      "→ engine:", eng.ollama_local_max_tool_rounds())
print("ollama_local_keep_alive:", m.get("ollama_local_keep_alive") or "(auto)",
      "→ engine:", eng.ollama_local_keep_alive())

# Smoke Ollama
ep = (m.get("ollama_local_endpoint") or "").rstrip("/")
aux = (m.get("auxiliary") or {})
mdl = (aux.get("model") or "").strip()
if ep and mdl:
    import urllib.request
    try:
        with urllib.request.urlopen(ep + "/api/tags", timeout=8) as r:
            tags = (json.loads(r.read().decode()) or {}).get("models") or []
        names = {x.get("name", "").split(":")[0] for x in tags}
        base = mdl.split(":")[0]
        ok = any(mdl in (x.get("name") or "") for x in tags) or base in names
        print("ollama tags:", "OK" if ok else f"WARN: không thấy {mdl}")
    except Exception as e:
        print("ollama tags: FAIL", type(e).__name__, e)
PY

# Preload model (giảm cold start lần tổng kết / nhắc hẹn đầu)
if command -v ollama >/dev/null 2>&1 && [ "$RAM_MB" -ge "$MIN_RAM_MB_FOR_8B" ]; then
  echo "==> Warm-up model"
  curl -fsS -m 120 http://127.0.0.1:11434/api/generate \
    -d '{"model":"javis-qwen3-8b","prompt":"ok","stream":false,"keep_alive":"30m"}' \
    >/dev/null 2>&1 || \
  curl -fsS -m 120 http://127.0.0.1:11434/api/generate \
    -d '{"model":"qwen3:8b","prompt":"ok","stream":false,"keep_alive":"30m"}' \
    >/dev/null 2>&1 || \
    echo "WARN: warm-up skipped"
fi

echo
echo "==> Health snapshot"
if [ -f "$ROOT/scripts/check-vps-health.sh" ]; then
  chmod +x "$ROOT/scripts/check-vps-health.sh"
  bash "$ROOT/scripts/check-vps-health.sh" 2>&1 | tail -40 || true
fi

echo
echo "============================================"
echo " XONG - gợi ý sử dụng (VPS ${RAM_GB}GB)"
echo "  Chat / MCP phức tạp  → Main Antigravity"
echo "  Ghi họp + tổng kết   → Moonshine + Ollama local"
echo "  Nhắc hẹn / việc nền  → Ollama (chậm CPU, bình thường)"
echo "  Cài đặt → Tối ưu / Siêu tiết kiệm token (chat Main nhanh hơn Đầy đủ)"
echo "============================================"
