#!/usr/bin/env bash
# Cài Ollama trên HOST VPS, kiểm tra dung lượng/RAM/GPU, kéo model mạnh nhất VỪA máy,
# rồi trỏ Javis (container) sang Ollama local.
#
# Chạy trên host (không phải trong container):
#   bash scripts/install-ollama-vps.sh
#
# Ép model cụ thể (bỏ qua chọn tự động):
#   JAVIS_OLLAMA_MODEL=qwen3:14b bash scripts/install-ollama-vps.sh
#
# Chỉ kiểm tra, không kéo:
#   JAVIS_OLLAMA_DRY_RUN=1 bash scripts/install-ollama-vps.sh
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
OLLAMA_HOST_BIND="${OLLAMA_HOST:-0.0.0.0}"
ENDPOINT_FROM_CONTAINER="${JAVIS_OLLAMA_ENDPOINT:-http://172.17.0.1:11434}"
DRY="${JAVIS_OLLAMA_DRY_RUN:-0}"
FORCE_MODEL="${JAVIS_OLLAMA_MODEL:-}"
# Giữ lại tối thiểu bao nhiêu GB trống sau khi kéo model
MIN_FREE_AFTER_GB="${JAVIS_OLLAMA_MIN_FREE_GB:-8}"

echo "============================================"
echo " Ollama trên VPS - kiểm tra tài nguyên"
echo "============================================"
echo

echo "==> Đĩa"
df -h / /var /usr 2>/dev/null | awk 'NR==1 || /^\/dev/ || $6=="/"'
echo
FREE_KB=$(df -Pk / | awk 'NR==2 {print $4}')
FREE_GB=$(awk -v k="$FREE_KB" 'BEGIN { printf "%.1f", k/1024/1024 }')
echo "Trống trên / : ${FREE_GB} GB"

echo
echo "==> RAM"
free -h || true
RAM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
RAM_GB=$(awk -v m="$RAM_MB" 'BEGIN { printf "%.1f", m/1024 }')
SWAP_MB=$(awk '/SwapTotal/ {print int($2/1024)}' /proc/meminfo)
echo "RAM vật lý : ${RAM_GB} GB (${RAM_MB} MB)"
echo "Swap       : ${SWAP_MB} MB"

echo
echo "==> CPU"
nproc
lscpu 2>/dev/null | awk -F: '/Model name|CPU\(s\)|Thread|Core/ { gsub(/^[ \t]+/, "", $2); print $1": "$2 }' | head -8 || true

echo
echo "==> GPU"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || true
  HAS_GPU=1
else
  echo "(không có nvidia-smi - coi như không GPU NVIDIA)"
  HAS_GPU=0
fi

# Bảng ứng viên: model | size_gb (ước lượng q4) | ram_min_gb | ghi chú
# Xếp mạnh → yếu. Script chọn cái MẠNH NHẤT còn vừa đĩa + RAM.
pick_model() {
  local free_gb="$1" ram_gb="$2" has_gpu="$3" min_free="$4"
  local budget
  budget=$(awk -v f="$free_gb" -v m="$min_free" 'BEGIN { printf "%.1f", f - m }')
  # RAM dùng được cho model: để ~2GB OS + Javis
  local ram_budget
  ram_budget=$(awk -v r="$ram_gb" 'BEGIN { v=r-2; if (v<1) v=1; printf "%.1f", v }')

  # Không GPU: model lớn hơn ~14B gần như không dùng nổi (quá chậm). Vẫn cho phép nếu RAM đủ.
  local candidates=(
    "llama3.3:70b|43|48|Rất mạnh - cần máy to + GPU"
    "qwen2.5:72b|47|48|Rất mạnh dòng Qwen"
    "deepseek-r1:70b|43|48|Suy luận sâu, rất nặng"
    "qwen3:32b|20|20|Mạnh, hợp máy 32GB"
    "deepseek-r1:32b|20|20|Suy luận mạnh 32B"
    "qwen3-coder:30b|19|20|Chuyên code"
    "gemma3:27b|17|18|Gemma lớn"
    "mistral-small:24b|14|16|Đa năng vừa"
    "qwen3:14b|9.3|12|Cân bằng tốt máy 16GB"
    "deepseek-r1:14b|9|12|Suy luận vừa"
    "phi4:14b|9.1|12|Logic/toán"
    "qwen3:8b|5.2|6|Nhẹ-vừa, hợp VPS phổ thông"
    "llama3.1:8b|4.9|6|Phổ thông Meta"
    "deepseek-r1:8b|5.2|6|Suy luận nhẹ"
    "qwen3:4b-instruct|2.5|2|Nhẹ nhất còn dùng được"
  )

  local best=""
  local line name size need_ram note ok
  for line in "${candidates[@]}"; do
    IFS='|' read -r name size need_ram note <<<"$line"
    ok=$(awk -v b="$budget" -v s="$size" 'BEGIN { print (b >= s) ? 1 : 0 }')
    [ "$ok" = "1" ] || continue
    ok=$(awk -v rb="$ram_budget" -v nr="$need_ram" 'BEGIN { print (rb >= nr) ? 1 : 0 }')
    [ "$ok" = "1" ] || continue
    # Không GPU + model lớn: cần RAM dư hơn mức tối thiểu
    if [ "$has_gpu" != "1" ]; then
      ok=$(awk -v s="$size" 'BEGIN { print (s > 15) ? 1 : 0 }')
      if [ "$ok" = "1" ]; then
        ok=$(awk -v rb="$ram_budget" -v nr="$need_ram" 'BEGIN { print (rb >= nr + 8) ? 1 : 0 }')
        [ "$ok" = "1" ] || continue
      fi
    fi
    best="$name|$size|$need_ram|$note"
    break
  done
  echo "$best"
}

echo
echo "==> Chọn model"
if [ -n "$FORCE_MODEL" ]; then
  CHOSEN="$FORCE_MODEL"
  CHOSEN_SIZE="?"
  CHOSEN_NOTE="ép bởi JAVIS_OLLAMA_MODEL"
  echo "Ép model: $CHOSEN"
else
  PICK=$(pick_model "$FREE_GB" "$RAM_GB" "$HAS_GPU" "$MIN_FREE_AFTER_GB")
  if [ -z "$PICK" ]; then
    echo "ERROR: Đĩa/RAM không đủ để kéo bất kỳ model nào trong danh sách."
    echo "       Trống=${FREE_GB}GB, RAM=${RAM_GB}GB, giữ lại tối thiểu ${MIN_FREE_AFTER_GB}GB."
    exit 1
  fi
  IFS='|' read -r CHOSEN CHOSEN_SIZE _need CHOSEN_NOTE <<<"$PICK"
  echo "Model mạnh nhất vừa máy: $CHOSEN (~${CHOSEN_SIZE} GB) - $CHOSEN_NOTE"
fi

echo
echo "Tóm tắt quyết định:"
echo "  - Đĩa trống : ${FREE_GB} GB (giữ lại >= ${MIN_FREE_AFTER_GB} GB)"
echo "  - RAM       : ${RAM_GB} GB (GPU=$HAS_GPU)"
echo "  - Model     : $CHOSEN"
echo "  - Endpoint Javis sẽ trỏ : $ENDPOINT_FROM_CONTAINER"
echo

if [ "$DRY" = "1" ]; then
  echo "DRY_RUN=1 - dừng trước khi cài/kéo."
  exit 0
fi

echo "==> Cài Ollama trên host (nếu chưa có)"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "ollama đã có: $(ollama --version 2>&1 | head -1)"
fi

# Cho phép container Docker gọi vào Ollama trên host
mkdir -p /etc/systemd/system/ollama.service.d 2>/dev/null || true
if [ -d /etc/systemd/system ]; then
  cat >/etc/systemd/system/ollama.service.d/override.conf <<EOF
[Service]
Environment="OLLAMA_HOST=${OLLAMA_HOST_BIND}:11434"
EOF
  systemctl daemon-reload 2>/dev/null || true
  systemctl enable ollama 2>/dev/null || true
  systemctl restart ollama 2>/dev/null || service ollama restart 2>/dev/null || true
fi

# Đợi API lên
echo "==> Chờ Ollama API"
ok=0
for i in $(seq 1 30); do
  if curl -fsS -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 1
done
if [ "$ok" != "1" ]; then
  # Thử start thủ công
  nohup ollama serve >/var/log/ollama-serve.log 2>&1 &
  sleep 3
  curl -fsS -m 5 http://127.0.0.1:11434/api/tags >/dev/null || {
    echo "ERROR: Ollama API không lên được ở :11434"
    exit 1
  }
fi
echo "Ollama API OK"

echo
echo "==> Kéo model $CHOSEN (có thể mất nhiều phút / GB)"
# Kiểm tra đã có chưa
if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx "$CHOSEN"; then
  echo "Model đã có sẵn: $CHOSEN"
else
  ollama pull "$CHOSEN"
fi

echo
echo "==> Model đã cài"
ollama list || true

echo
echo "==> Trỏ Javis container sang Ollama local"
if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  docker exec -i -u javis "$CONTAINER" python - <<PY
import sys
sys.path.insert(0, "/app/server")
import config as cfg
s = cfg.read_settings()
m = s.setdefault("model", {})
m["ollama_local_endpoint"] = "${ENDPOINT_FROM_CONTAINER}"
# Việc nền: ưu tiên ollama-local nếu đã đặt; không xoá ollama cloud key nếu có
aux = dict(m.get("auxiliary") or {})
# Giữ cloud nếu user muốn - nhưng yêu cầu lần này là dùng bản tải về → chuyển việc nền sang local
m["auxiliary"] = {"provider": "ollama-local", "model": "${CHOSEN}"}
cfg.write_settings(s)
print("ollama_local_endpoint =", m.get("ollama_local_endpoint"))
print("auxiliary =", m.get("auxiliary"))
print("OK")
PY
else
  echo "WARN: không thấy container $CONTAINER - bỏ qua bước ghi settings Javis"
fi

echo
echo "============================================"
echo " XONG"
echo "  Model : $CHOSEN"
echo "  Thử   : curl http://127.0.0.1:11434/api/tags"
echo "  Chat  : ollama run $CHOSEN"
echo "  Javis Models → Ollama (Local) → ${ENDPOINT_FROM_CONTAINER}"
echo "============================================"
