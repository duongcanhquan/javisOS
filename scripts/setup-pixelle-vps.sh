#!/usr/bin/env bash
# Clone + cấu hình Pixelle-Video cạnh Javis để docker-compose.pixelle.yml build được.
# Idempotent: chạy lại an toàn.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PIXELLE_DIR="${PIXELLE_DIR:-$ROOT/vendor/Pixelle-Video}"
REPO_URL="${PIXELLE_REPO_URL:-https://github.com/ATH-MaaS/Pixelle-Video.git}"
ENV_FILE="$ROOT/.env"
TEMPLATE="$ROOT/deploy/pixelle/config.template.yaml"

echo "==> Pixelle setup"
echo "    dir=$PIXELLE_DIR"

mkdir -p "$(dirname "$PIXELLE_DIR")"
if [ ! -d "$PIXELLE_DIR/.git" ]; then
  echo "==> clone Pixelle-Video"
  git clone --depth 1 "$REPO_URL" "$PIXELLE_DIR"
else
  echo "==> cập nhật Pixelle-Video"
  git -C "$PIXELLE_DIR" fetch --depth 1 origin main 2>/dev/null || true
  git -C "$PIXELLE_DIR" reset --hard origin/main 2>/dev/null || true
fi

# Đọc biến từ .env (không source để tránh side-effect).
_get_env() {
  local key="$1" def="${2:-}"
  local val=""
  if [ -f "$ENV_FILE" ]; then
    val=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | sed 's/^["'\'']//;s/["'\'']$//' || true)
  fi
  if [ -z "$val" ]; then
    val="${!key:-}"
  fi
  if [ -z "$val" ]; then
    val="$def"
  fi
  printf '%s' "$val"
}

LLM_KEY="$(_get_env PIXELLE_LLM_API_KEY "")"
LLM_BASE="$(_get_env PIXELLE_LLM_BASE_URL "")"
LLM_MODEL="$(_get_env PIXELLE_LLM_MODEL "")"
RH_KEY="$(_get_env RUNNINGHUB_API_KEY "$(_get_env PIXELLE_RUNNINGHUB_API_KEY "")")"

# Fallback: OpenAI / OpenRouter / Ollama nếu user đã có trong .env Javis.
if [ -z "$LLM_KEY" ]; then
  LLM_KEY="$(_get_env OPENAI_API_KEY "")"
fi
if [ -z "$LLM_KEY" ]; then
  LLM_KEY="$(_get_env OPENROUTER_API_KEY "")"
  if [ -n "$LLM_KEY" ] && [ -z "$LLM_BASE" ]; then
    LLM_BASE="https://openrouter.ai/api/v1"
  fi
  if [ -n "$LLM_KEY" ] && [ -z "$LLM_MODEL" ]; then
    LLM_MODEL="openai/gpt-4o-mini"
  fi
fi

# Ollama trên host (meetings / local) - không cần key.
if [ -z "$LLM_BASE" ]; then
  if curl -fsS -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    LLM_BASE="http://host.docker.internal:11434/v1"
    LLM_KEY="${LLM_KEY:-ollama}"
    LLM_MODEL="${LLM_MODEL:-$(_get_env PIXELLE_LLM_MODEL qwen3:4b)}"
    echo "==> dùng Ollama host → $LLM_MODEL"
  fi
fi

if [ -z "$LLM_BASE" ]; then
  LLM_BASE="https://api.openai.com/v1"
fi
if [ -z "$LLM_MODEL" ]; then
  LLM_MODEL="gpt-4o-mini"
fi

DEFAULT_TEMPLATE="1080x1920/static_default.html"
if [ -n "$RH_KEY" ]; then
  DEFAULT_TEMPLATE="1080x1920/image_default.html"
  echo "==> có RunningHub → template ảnh AI"
else
  echo "==> chưa có RunningHUB_API_KEY → template static (vẫn ra video + TTS)"
fi

if [ ! -f "$TEMPLATE" ]; then
  echo "ERROR: thiếu $TEMPLATE" >&2
  exit 1
fi

CFG="$PIXELLE_DIR/config.yaml"
# Luôn ghi lại từ template để đồng bộ biến .env (trừ khi user khóa bằng PIXELLE_KEEP_CONFIG=1).
if [ "${PIXELLE_KEEP_CONFIG:-0}" = "1" ] && [ -f "$CFG" ]; then
  echo "==> giữ config.yaml hiện có (PIXELLE_KEEP_CONFIG=1)"
else
  echo "==> ghi $CFG"
  python3 - "$TEMPLATE" "$CFG" "$LLM_KEY" "$LLM_BASE" "$LLM_MODEL" "$RH_KEY" "$DEFAULT_TEMPLATE" <<'PY'
import sys
from pathlib import Path
src, dst, key, base, model, rh, tmpl = sys.argv[1:8]
text = Path(src).read_text(encoding="utf-8")
for a, b in (
    ("__LLM_API_KEY__", key),
    ("__LLM_BASE_URL__", base),
    ("__LLM_MODEL__", model),
    ("__RUNNINGHUB_API_KEY__", rh),
    ("__DEFAULT_TEMPLATE__", tmpl),
):
    text = text.replace(a, b)
Path(dst).write_text(text, encoding="utf-8")
PY
fi

# Ghi PIXELLE_* vào .env Javis nếu chưa có.
touch "$ENV_FILE"
_ensure_env() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    return 0
  fi
  echo "${key}=${val}" >> "$ENV_FILE"
}
_ensure_env PIXELLE_DIR "$PIXELLE_DIR"
_ensure_env PIXELLE_API_BASE "http://pixelle-api:8000"
_ensure_env JAVIS_ENABLE_PIXELLE "true"

if [ -z "$LLM_KEY" ] || [ "$LLM_KEY" = "ollama" ]; then
  echo "WARN: LLM key trống hoặc đang trỏ Ollama. Fixed+static vẫn render được;"
  echo "      muốn AI viết lại script / ảnh AI thì thêm vào .env:"
  echo "        PIXELLE_LLM_API_KEY=...   PIXELLE_LLM_BASE_URL=...   PIXELLE_LLM_MODEL=..."
  echo "        RUNNINGHUB_API_KEY=...    # để bật template image_*"
fi

echo "==> Pixelle sẵn sàng build/up (profile pixelle)"
echo "    PIXELLE_DIR=$PIXELLE_DIR"
echo "    template=$DEFAULT_TEMPLATE"
