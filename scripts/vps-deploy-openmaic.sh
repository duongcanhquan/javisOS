#!/usr/bin/env bash
# Cài / cập nhật OpenMAIC trên VPS: TTS Edge-TTS VI qua Javis proxy (không Browser Native).
# Clone giọng: ElevenLabs / VoxCPM (tuỳ chọn, không bật mặc định).
# Chạy trên VPS (thường qua GitHub Action appleboy/ssh-action).
set -euo pipefail

OPENMAIC_DIR="${OPENMAIC_DIR:-$HOME/openmaic}"
OPENMAIC_DOMAIN="${OPENMAIC_DOMAIN:-openmaic.vietmycollege.com}"
OPENMAIC_PORT="${OPENMAIC_PORT:-3000}"
REPO_URL="${OPENMAIC_REPO:-https://github.com/THU-MAIC/OpenMAIC.git}"
JAVIS_CONTAINER="${JAVIS_CONTAINER:-javis}"
JAVIS_TTS_PORT="${JAVIS_TTS_PORT:-7777}"
# 0 = image community (nhanh, phù hợp VPS nhỏ). 1 = build upstream (nặng, dễ OOM).
OPENMAIC_BUILD="${OPENMAIC_BUILD:-0}"
# 1 = không có Gemini key vẫn đưa container lên (TTS vẫn dùng được; generate cần key sau).
OPENMAIC_ALLOW_NO_KEY="${OPENMAIC_ALLOW_NO_KEY:-1}"

echo "==> OpenMAIC dir: $OPENMAIC_DIR (BUILD=$OPENMAIC_BUILD)"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: thiếu lệnh $1" >&2
    exit 1
  }
}
need_cmd docker
need_cmd git
if ! command -v curl >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl
  else
    echo "ERROR: cần curl" >&2
    exit 1
  fi
fi

find_javis_container() {
  if docker ps --format '{{.Names}}' | grep -qx "$JAVIS_CONTAINER"; then
    echo "$JAVIS_CONTAINER"
    return
  fi
  docker ps --format '{{.Names}}' | grep -E '(^|-)javis$' | head -n1 || true
}

# --- Lấy Gemini key: secret env → Javis Models (decrypt) ---
resolve_google_key() {
  if [ -n "${OPENMAIC_GOOGLE_API_KEY:-}" ]; then
    echo "$OPENMAIC_GOOGLE_API_KEY"
    return
  fi
  if [ -n "${GOOGLE_API_KEY:-}" ]; then
    echo "$GOOGLE_API_KEY"
    return
  fi
  local jc
  jc="$(find_javis_container)"
  if [ -z "$jc" ]; then
    echo "==> Không thấy container Javis đang chạy (không lấy được key từ Models)." >&2
    return 0
  fi
  echo "==> Thử đọc gemini_api_key từ container: $jc" >&2
  docker exec -w /app "$jc" python3 - <<'PY' 2>/dev/null || true
from server.config import read_settings
m = (read_settings().get("model") or {})
k = (m.get("gemini_api_key") or "").strip()
if k and not str(k).startswith("enc:"):
    print(k)
else:
    import sys
    print("HAS_KEY=0", file=sys.stderr)
PY
}

KEY="$(resolve_google_key | tr -d '\r' | head -n1 || true)"
if [ "$KEY" = "HAS_KEY=0" ]; then KEY=""; fi

if [ -z "${KEY}" ]; then
  echo "WARN: chưa có GOOGLE/Gemini API key."
  echo "  Generate classroom sẽ lỗi cho đến khi có key."
  echo "  Sửa: Javis → Models → Google Gemini, hoặc secret OPENMAIC_GOOGLE_API_KEY, rồi chạy lại."
  if [ "$OPENMAIC_ALLOW_NO_KEY" != "1" ]; then
    exit 1
  fi
  echo "==> Tiếp tục deploy (ALLOW_NO_KEY=1) — TTS Edge proxy vẫn dùng được."
else
  echo "==> Có Gemini/Google API key (ẩn)."
fi

# --- Shared TTS proxy key (Javis ↔ OpenMAIC) ---
TTS_KEY_FILE="$OPENMAIC_DIR/.tts_proxy_key"
mkdir -p "$OPENMAIC_DIR"
umask 077
if [ -n "${OPENMAIC_TTS_PROXY_KEY:-}" ]; then
  printf '%s' "$OPENMAIC_TTS_PROXY_KEY" > "$TTS_KEY_FILE"
elif [ -s "$TTS_KEY_FILE" ]; then
  echo "==> Dùng lại TTS proxy key đã có ($TTS_KEY_FILE)"
else
  echo "==> Tạo TTS proxy key mới"
  openssl rand -hex 24 > "$TTS_KEY_FILE" 2>/dev/null \
    || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > "$TTS_KEY_FILE"
fi
chmod 600 "$TTS_KEY_FILE"
TTS_PROXY_KEY="$(tr -d '\r\n' < "$TTS_KEY_FILE")"
if [ -z "$TTS_PROXY_KEY" ]; then
  echo "ERROR: không tạo được OPENMAIC_TTS_PROXY_KEY" >&2
  exit 1
fi

JC="$(find_javis_container)"
if [ -n "$JC" ]; then
  echo "==> Ghi key vào Javis container ($JC) /data/state/openmaic_tts_proxy.key"
  docker exec -u root "$JC" mkdir -p /data/state
  printf '%s' "$TTS_PROXY_KEY" | docker exec -i -u root "$JC" tee /data/state/openmaic_tts_proxy.key >/dev/null
  docker exec -u root "$JC" chown javis:javis /data/state/openmaic_tts_proxy.key
  docker exec -u root "$JC" chmod 600 /data/state/openmaic_tts_proxy.key
else
  echo "WARN: không thấy container Javis — ghi key vào state sau khi Javis lên."
fi

# --- Site ACCESS_CODE: tạo 1 lần, dùng mãi (cookie ~7 ngày mỗi trình duyệt) ---
# OPENMAIC_ACCESS_CODE=... → ghi đè
# OPENMAIC_ACCESS_CODE_DISABLED=1 → không bật cổng mật khẩu
# Mặc định: giữ ~/openmaic/.access_code, lần đầu tạo mã dễ nhớ
ACCESS_CODE_FILE="$OPENMAIC_DIR/.access_code"
ACCESS_CODE=""
if [ "${OPENMAIC_ACCESS_CODE_DISABLED:-0}" = "1" ]; then
  echo "==> ACCESS_CODE tắt (OPENMAIC_ACCESS_CODE_DISABLED=1) — site mở không hỏi mật khẩu"
  rm -f "$ACCESS_CODE_FILE" 2>/dev/null || true
elif [ -n "${OPENMAIC_ACCESS_CODE:-}" ]; then
  printf '%s' "$OPENMAIC_ACCESS_CODE" > "$ACCESS_CODE_FILE"
  chmod 600 "$ACCESS_CODE_FILE"
  ACCESS_CODE="$(tr -d '\r\n' < "$ACCESS_CODE_FILE")"
  echo "==> ACCESS_CODE từ env (đã lưu $ACCESS_CODE_FILE)"
elif [ -s "$ACCESS_CODE_FILE" ]; then
  ACCESS_CODE="$(tr -d '\r\n' < "$ACCESS_CODE_FILE")"
  echo "==> Dùng lại ACCESS_CODE đã có ($ACCESS_CODE_FILE)"
else
  ACCESS_CODE="vietmy-openmaic"
  printf '%s' "$ACCESS_CODE" > "$ACCESS_CODE_FILE"
  chmod 600 "$ACCESS_CODE_FILE"
  echo "==> Tạo ACCESS_CODE mặc định lần đầu → $ACCESS_CODE_FILE"
fi

# --- Clone / update source (cần cho BUILD=1; BUILD=0 cũng giữ thư mục + .env) ---
if [ ! -d "$OPENMAIC_DIR/.git" ]; then
  echo "==> Clone OpenMAIC"
  mkdir -p "$(dirname "$OPENMAIC_DIR")"
  git clone --depth 1 "$REPO_URL" "$OPENMAIC_DIR"
else
  echo "==> Pull OpenMAIC"
  git -C "$OPENMAIC_DIR" fetch --depth 1 origin main || true
  git -C "$OPENMAIC_DIR" reset --hard origin/main || true
fi

# --- .env.local: Edge-TTS qua Javis ---
ENV_FILE="$OPENMAIC_DIR/.env.local"
echo "==> Write $ENV_FILE (Edge-TTS via Javis OpenAI proxy)"
umask 077
export OPENMAIC_DIR
export _OM_KEY="${KEY}"
export _OM_VOX="${TTS_VOXCPM_BASE_URL:-}"
export _OM_TTS_KEY="${TTS_PROXY_KEY}"
export _OM_TTS_BASE="${OPENMAIC_TTS_BASE_URL:-http://host.docker.internal:${JAVIS_TTS_PORT}/v1}"
export _OM_ACCESS="${ACCESS_CODE}"
python3 - <<'PY'
import os
from pathlib import Path
key = os.environ.get("_OM_KEY") or ""
vox = os.environ.get("_OM_VOX") or ""
tts_key = os.environ.get("_OM_TTS_KEY") or ""
tts_base = os.environ.get("_OM_TTS_BASE") or "http://host.docker.internal:7777/v1"
access = (os.environ.get("_OM_ACCESS") or "").strip()
path = Path(os.environ["OPENMAIC_DIR"]) / ".env.local"
lines = [
    "# Generated by scripts/vps-deploy-openmaic.sh — do not commit",
    f"GOOGLE_API_KEY={key}",
    "DEFAULT_PROVIDER=google",
    "DEFAULT_MODEL=google:gemini-2.5-flash",
    "TTS_BROWSER_NATIVE_ENABLED=false",
    "TTS_OPENAI_ENABLED=true",
    f"TTS_OPENAI_API_KEY={tts_key}",
    f"TTS_OPENAI_BASE_URL={tts_base}",
    "NODE_ENV=production",
    "PORT=3000",
]
if access:
    lines.append(f"ACCESS_CODE={access}")
else:
    lines.append("# ACCESS_CODE=  (tắt — không hỏi mật khẩu site)")
if vox:
    lines.append(f"TTS_VOXCPM_BASE_URL={vox}")
else:
    lines.append("# TTS_VOXCPM_BASE_URL=http://127.0.0.1:8000/v1")
    lines.append("# TTS_ELEVENLABS_API_KEY=")
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
path.chmod(0o600)
print(
    "wrote", path,
    "key_len=", len(key),
    "tts_key_len=", len(tts_key),
    "tts_base=", tts_base,
    "access_code=", "yes" if access else "off",
)
PY
unset _OM_KEY _OM_VOX _OM_TTS_KEY _OM_TTS_BASE _OM_ACCESS

if [ -n "${TTS_VOXCPM_BASE_URL:-}" ]; then
  echo "==> VoxCPM clone URL đã gắn"
else
  echo "==> Clone giọng: chưa bật. TTS mặc định = Javis Edge (Hoài My / Nam Minh)."
fi

cd "$OPENMAIC_DIR"

docker rm -f openmaic 2>/dev/null || true
if [ -f "$OPENMAIC_DIR/docker-compose.yml" ]; then
  (cd "$OPENMAIC_DIR" && docker compose down 2>/dev/null) || true
fi

JAVIS_OS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$JAVIS_OS_ROOT/deploy/openmaic/docker-compose.yml" ] && [ "$OPENMAIC_BUILD" = "1" ]; then
  cp -f "$JAVIS_OS_ROOT/deploy/openmaic/docker-compose.yml" "$OPENMAIC_DIR/docker-compose.yml" || true
fi

if [ "$OPENMAIC_BUILD" = "1" ]; then
  echo "==> docker compose build upstream (có thể 15–40 phút, cần RAM lớn)"
  docker compose build
  docker compose up -d openmaic
else
  echo "==> Image community + host.docker.internal → Javis TTS"
  docker pull devprincekumar/openmaic:latest
  docker run -d --name openmaic --restart unless-stopped \
    -p "${OPENMAIC_PORT}:3000" \
    --add-host=host.docker.internal:host-gateway \
    --env-file "$ENV_FILE" \
    -v openmaic_data:/app/data \
    devprincekumar/openmaic:latest
fi

echo "==> Chờ health http://127.0.0.1:${OPENMAIC_PORT}/api/health"
ok=0
for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${OPENMAIC_PORT}/api/health" >/tmp/openmaic-health.json 2>/dev/null; then
    ok=1
    break
  fi
  echo "  … chờ ($i/60)"
  sleep 5
done
if [ "$ok" != 1 ]; then
  echo "ERROR: /api/health không lên sau ~5 phút."
  docker ps -a --filter name=openmaic || true
  docker logs openmaic --tail 100 2>/dev/null || true
  (cd "$OPENMAIC_DIR" && docker compose logs --tail 80 openmaic 2>/dev/null) || true
  exit 1
fi
echo "==> Health OK:"
cat /tmp/openmaic-health.json
echo

echo "==> Smoke Javis Edge TTS proxy"
if curl -fsS -m 60 -X POST "http://127.0.0.1:${JAVIS_TTS_PORT}/v1/audio/speech" \
  -H "Authorization: Bearer ${TTS_PROXY_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"input":"Xin chào. Đây là giọng tiếng Việt chuẩn.","voice":"nova"}' \
  -o /tmp/openmaic-tts-smoke.mp3 2>/dev/null; then
  sz=$(wc -c </tmp/openmaic-tts-smoke.mp3 | tr -d ' ')
  echo "  OK — /tmp/openmaic-tts-smoke.mp3 ($sz bytes)"
else
  echo "  WARN: proxy TTS chưa OK (cần Javis >= 0.55.124 với /v1/audio/speech + key)."
fi

if command -v nginx >/dev/null 2>&1; then
  echo "==> Cấu hình nginx $OPENMAIC_DOMAIN → 127.0.0.1:${OPENMAIC_PORT}"
  cat > /etc/nginx/sites-available/openmaic <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${OPENMAIC_DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://127.0.0.1:${OPENMAIC_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        # PDF / media / ZIP classroom — paste & upload video tài liệu dễ hơn
        client_max_body_size 512m;
    }
}
EOF
  ln -sfn /etc/nginx/sites-available/openmaic /etc/nginx/sites-enabled/openmaic
  nginx -t && systemctl reload nginx
  if command -v certbot >/dev/null 2>&1; then
    if getent hosts "$OPENMAIC_DOMAIN" >/dev/null 2>&1; then
      certbot --nginx -d "$OPENMAIC_DOMAIN" --non-interactive --agree-tos \
        --register-unsafely-without-email --redirect || true
    else
      echo "DNS chưa trỏ $OPENMAIC_DOMAIN → IP VPS. Sau khi DNS OK chạy:"
      echo "  certbot --nginx -d $OPENMAIC_DOMAIN --non-interactive --agree-tos --register-unsafely-without-email --redirect"
    fi
  fi
else
  echo "==> Không có nginx — dùng http://<IP-VPS>:${OPENMAIC_PORT}"
fi

if command -v ufw >/dev/null 2>&1; then
  if ufw status 2>/dev/null | grep -qi "Status: active"; then
    ufw allow "${OPENMAIC_PORT}/tcp" comment "openmaic" || true
  fi
fi

cat <<EOF

==> XONG OpenMAIC (Edge-TTS tiếng Việt qua Javis)
URL nội bộ: http://127.0.0.1:${OPENMAIC_PORT}
Domain:     https://${OPENMAIC_DOMAIN}  (khi DNS + SSL OK)

ACCESS_CODE:  ${ACCESS_CODE:-OFF — không hỏi mật khẩu}
  (lưu tại $ACCESS_CODE_FILE — đổi: OPENMAIC_ACCESS_CODE='ma-moi' bash scripts/vps-deploy-openmaic.sh)
  (tắt hẳn: OPENMAIC_ACCESS_CODE_DISABLED=1 bash scripts/vps-deploy-openmaic.sh)
  Nhập 1 lần trên trình duyệt → cookie ~7 ngày, không tạo mã mỗi bài giảng.

TTS mặc định: OpenAI provider → Javis Edge (Hoài My / Nam Minh)
Settings:     Text-to-Speech → OpenAI (không dùng Browser Native)
Clone giọng:  ElevenLabs / VoxCPM khi có key hoặc GPU
LLM:          Gemini key ${KEY:+đã có}${KEY:-CHƯA có — dán vào Models rồi chạy lại deploy}

Tạo bài nhanh: mở site → dán đề cương / paste văn bản / upload PDF → Generate classroom
  (không dùng open.maic.chat hosted — mã cloud hết hạn từng lần)
EOF
