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
# 0 = bắt buộc có Gemini/Google key (generate classroom cần). 1 = vẫn lên khi thiếu key.
OPENMAIC_ALLOW_NO_KEY="${OPENMAIC_ALLOW_NO_KEY:-0}"
# 1 = chỉ cập nhật GOOGLE_API_KEY trong .env.local + restart (không pull/rebuild).
OPENMAIC_SYNC_KEY_ONLY="${OPENMAIC_SYNC_KEY_ONLY:-0}"

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
  # Bắt buộc -i (stdin heredoc) + JAVIS_STATE_DIR=/data/state.
  # Thiếu -i thì python nhận script rỗng → tưởng như chưa có key dù Models đã nối.
  docker exec -i -e JAVIS_STATE_DIR=/data/state -e PYTHONUNBUFFERED=1 -w /app "$jc" python3 - <<'PY' || true
import os, sys, json
os.environ["JAVIS_STATE_DIR"] = "/data/state"
from pathlib import Path
try:
    from server import config as cfgmod
except Exception as e:
    print(f"IMPORT_ERR={type(e).__name__}:{e}", file=sys.stderr)
    raise SystemExit(0)
print(f"state_dir={cfgmod.STATE_DIR} settings={cfgmod.SETTINGS_PATH} exists={cfgmod.SETTINGS_PATH.exists()}", file=sys.stderr)
sk = Path("/data/state/.secret_key")
print(f"secret_key_exists={sk.exists()}", file=sys.stderr)
try:
    raw = json.loads(cfgmod.SETTINGS_PATH.read_text(encoding="utf-8")) if cfgmod.SETTINGS_PATH.exists() else {}
except Exception as e:
    raw = {}
    print(f"raw_json_err={type(e).__name__}", file=sys.stderr)
raw_m = (raw.get("model") or {}) if isinstance(raw, dict) else {}
raw_k = str(raw_m.get("gemini_api_key") or "")
print(f"raw_gemini_len={len(raw_k)} raw_prefix={raw_k[:6]!r}", file=sys.stderr)
for fld in ("openrouter_key", "openai_api_key", "anthropic_api_key"):
    print(f"raw_{fld}_len={len(str(raw_m.get(fld) or ''))}", file=sys.stderr)
m = (cfgmod.read_settings().get("model") or {})
k = (m.get("gemini_api_key") or "").strip()
print(f"decrypted_len={len(k)}", file=sys.stderr)
if k.startswith("enc:"):
    try:
        import secrets_store
        k = (secrets_store.decrypt(k) or "").strip()
    except Exception as e:
        print(f"decrypt_err={type(e).__name__}", file=sys.stderr)
        k = ""
if k and not k.startswith("enc:"):
    print(k)
else:
    print(f"HAS_KEY=0 plain_len={len(k)}", file=sys.stderr)
PY
}

KEY="$(resolve_google_key | tr -d '\r' | head -n1 || true)"
if [ "$KEY" = "HAS_KEY=0" ]; then KEY=""; fi

if [ -z "${KEY}" ]; then
  echo "ERROR: chưa có GOOGLE/Gemini API key — OpenMAIC sẽ báo:"
  echo "  API key required for provider: google"
  echo "Sửa một trong hai:"
  echo "  1) Javis → Models → Google Gemini → dán key (AI Studio), rồi chạy lại deploy"
  echo "  2) GitHub secret OPENMAIC_GOOGLE_API_KEY rồi chạy Deploy OpenMAIC to VPS"
  if [ "$OPENMAIC_ALLOW_NO_KEY" != "1" ]; then
    exit 1
  fi
  echo "==> Tiếp tục (ALLOW_NO_KEY=1) — generate classroom sẽ FAIL cho đến khi có key."
else
  echo "==> Có Gemini/Google API key (ẩn, len=${#KEY})."
fi

# --- Chỉ sync key (sửa nhanh lỗi generate) ---
if [ "$OPENMAIC_SYNC_KEY_ONLY" = "1" ]; then
  ENV_FILE="$OPENMAIC_DIR/.env.local"
  if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: thiếu $ENV_FILE — chạy full deploy trước." >&2
    exit 1
  fi
  if [ -z "${KEY}" ]; then
    echo "ERROR: SYNC_KEY_ONLY cần Gemini key." >&2
    exit 1
  fi
  echo "==> Cập nhật GOOGLE_API_KEY trong $ENV_FILE"
  export OPENMAIC_DIR _OM_KEY="$KEY"
  python3 - <<'PY'
import os, re
from pathlib import Path
path = Path(os.environ["OPENMAIC_DIR"]) / ".env.local"
key = os.environ["_OM_KEY"]
text = path.read_text(encoding="utf-8")
if re.search(r"(?m)^GOOGLE_API_KEY=", text):
    text = re.sub(r"(?m)^GOOGLE_API_KEY=.*$", f"GOOGLE_API_KEY={key}", text)
else:
    text = f"GOOGLE_API_KEY={key}\n" + text
if not re.search(r"(?m)^DEFAULT_PROVIDER=", text):
    text += "\nDEFAULT_PROVIDER=google\nDEFAULT_MODEL=google:gemini-2.5-flash\n"
path.write_text(text, encoding="utf-8")
path.chmod(0o600)
print("updated", path, "key_len=", len(key))
PY
  unset _OM_KEY
  if docker ps --format '{{.Names}}' | grep -qx openmaic; then
    echo "==> Restart container openmaic"
    docker restart openmaic
  elif [ -f "$OPENMAIC_DIR/docker-compose.yml" ]; then
    (cd "$OPENMAIC_DIR" && docker compose up -d openmaic) || true
  else
    echo "WARN: không thấy container openmaic — chạy full deploy."
  fi
  sleep 3
  curl -fsS "http://127.0.0.1:${OPENMAIC_PORT}/api/health" || true
  echo
  echo "==> XONG sync key. Chạy lại generate classroom trên Javis."
  exit 0
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

# --- Site ACCESS_CODE ---
# Mặc định TẮT: cửa chính là Javis (đã đăng nhập) → /openmaic/generate qua localhost.
# Bật lại: OPENMAIC_ACCESS_CODE='ma-bi-mat' bash scripts/vps-deploy-openmaic.sh
# Ép tắt khi đã có file cũ: OPENMAIC_ACCESS_CODE_DISABLED=1
ACCESS_CODE_FILE="$OPENMAIC_DIR/.access_code"
ACCESS_CODE=""
if [ -n "${OPENMAIC_ACCESS_CODE:-}" ]; then
  printf '%s' "$OPENMAIC_ACCESS_CODE" > "$ACCESS_CODE_FILE"
  chmod 600 "$ACCESS_CODE_FILE"
  ACCESS_CODE="$(tr -d '\r\n' < "$ACCESS_CODE_FILE")"
  echo "==> ACCESS_CODE từ env (đã lưu $ACCESS_CODE_FILE)"
elif [ "${OPENMAIC_ACCESS_CODE_DISABLED:-1}" = "1" ]; then
  echo "==> ACCESS_CODE tắt (mặc định) — Javis Bài giảng không cần gõ mã site"
  rm -f "$ACCESS_CODE_FILE" 2>/dev/null || true
elif [ -s "$ACCESS_CODE_FILE" ]; then
  ACCESS_CODE="$(tr -d '\r\n' < "$ACCESS_CODE_FILE")"
  echo "==> Dùng lại ACCESS_CODE đã có ($ACCESS_CODE_FILE)"
else
  echo "==> ACCESS_CODE tắt (chưa đặt OPENMAIC_ACCESS_CODE)"
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

# --- Public URL trình duyệt mở được (KHÔNG dùng host.docker.internal) ---
# OpenMAIC gắn audioUrl theo origin của request generate. Nếu origin là
# host.docker.internal thì Chrome không tải MP3 → fallback Browser Native
# (giọng Trung/Anh đọc Việt). Javis gửi X-Forwarded-Host từ URL này.
resolve_openmaic_public_url() {
  if [ -n "${OPENMAIC_PUBLIC_URL:-}" ]; then
    echo "${OPENMAIC_PUBLIC_URL}"
    return
  fi
  if getent hosts "$OPENMAIC_DOMAIN" >/dev/null 2>&1; then
    echo "https://${OPENMAIC_DOMAIN}"
    return
  fi
  local ip=""
  ip="$(curl -4 -fsS --max-time 4 https://ifconfig.me 2>/dev/null || true)"
  if [ -z "$ip" ]; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  fi
  if [ -n "$ip" ]; then
    echo "http://${ip}:${OPENMAIC_PORT}"
  else
    echo "http://127.0.0.1:${OPENMAIC_PORT}"
  fi
}
OPENMAIC_PUBLIC_URL="$(resolve_openmaic_public_url)"
echo "==> OPENMAIC_PUBLIC_URL=$OPENMAIC_PUBLIC_URL (audioUrl/media phải dùng host này)"

# Ghi vào Javis state để /openmaic/* gửi đúng X-Forwarded-Host
if [ -n "$JC" ]; then
  printf '%s' "$OPENMAIC_PUBLIC_URL" | docker exec -i -u root "$JC" tee /data/state/openmaic_public_url >/dev/null
  docker exec -u root "$JC" chown javis:javis /data/state/openmaic_public_url 2>/dev/null || true
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
    # CẤM Browser Native — tránh giọng Trung/Anh đọc Việt khi audioUrl lỗi.
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

# server-providers.yml: force-disable browser-native (server precedence)
SP_FILE="$OPENMAIC_DIR/server-providers.yml"
cat > "$SP_FILE" <<'YAML'
# Generated by scripts/vps-deploy-openmaic.sh — do not commit
# Browser Native OFF: chỉ TTS OpenAI → Javis Edge (Hoài My / Nam Minh).
tts:
  browser-native-tts:
    enabled: false
YAML
echo "==> Wrote $SP_FILE (browser-native disabled)"

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

# SP_FILE đã ghi sẵn tại $OPENMAIC_DIR/server-providers.yml (dòng trên) —
# không cp tự copy (cp báo "are the same file" và exit 1 với set -e).
# Image community mount file đó vào /app; build=1 dùng file trong thư mục compose.

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
    -v "$OPENMAIC_DIR/server-providers.yml:/app/server-providers.yml:ro" \
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

echo "==> Smoke Javis Edge TTS proxy (host)"
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

echo "==> Smoke TTS từ trong container OpenMAIC → Javis (host.docker.internal)"
if docker exec openmaic sh -c "command -v wget >/dev/null || command -v curl >/dev/null" 2>/dev/null; then
  if docker exec openmaic sh -c \
    "wget -q -O /tmp/tts.mp3 --header='Authorization: Bearer ${TTS_PROXY_KEY}' \
      --header='Content-Type: application/json' \
      --post-data='{\"input\":\"Xin chao tu OpenMAIC\",\"voice\":\"nova\"}' \
      http://host.docker.internal:${JAVIS_TTS_PORT}/v1/audio/speech \
    || curl -fsS -m 60 -X POST http://host.docker.internal:${JAVIS_TTS_PORT}/v1/audio/speech \
      -H 'Authorization: Bearer ${TTS_PROXY_KEY}' -H 'Content-Type: application/json' \
      -d '{\"input\":\"Xin chao tu OpenMAIC\",\"voice\":\"nova\"}' -o /tmp/tts.mp3"; then
    echo "  OK — OpenMAIC container gọi được Javis Edge TTS"
  else
    echo "  WARN: container OpenMAIC không gọi được Javis TTS — kiểm tra --add-host host-gateway."
  fi
else
  echo "  (bỏ qua — image không có wget/curl)"
fi

# Sửa classroom JSON cũ: đổi host.docker.internal → PUBLIC_URL (MP3 Edge đã có trên đĩa)
echo "==> Repair audioUrl/media URL trong classroom JSON cũ → $OPENMAIC_PUBLIC_URL"
export _OM_PUB="$OPENMAIC_PUBLIC_URL"
python3 - <<'PY'
import json, os, subprocess, tempfile
from pathlib import Path

pub = (os.environ.get("_OM_PUB") or "").rstrip("/")
if not pub:
    print("  skip: no public url")
    raise SystemExit(0)

olds = [
    "http://host.docker.internal:3000",
    "https://host.docker.internal:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

def rewrite_obj(node):
    if isinstance(node, dict):
        return {k: rewrite_obj(v) for k, v in node.items()}
    if isinstance(node, list):
        return [rewrite_obj(v) for v in node]
    if isinstance(node, str) and node.startswith(("http://", "https://")):
        for o in olds:
            if node == o or node.startswith(o + "/"):
                return pub + node[len(o):]
    return node

# Copy JSON ra host qua docker volume mount path nếu có; fallback docker cp
fixed = 0
# Thử đọc qua docker exec
try:
    listing = subprocess.check_output(
        ["docker", "exec", "openmaic", "sh", "-c",
         "ls /app/data/classrooms/*.json 2>/dev/null || true"],
        text=True,
    )
except Exception as e:
    print("  skip list:", e)
    listing = ""

for line in listing.splitlines():
    path = line.strip()
    if not path.endswith(".json"):
        continue
    try:
        raw = subprocess.check_output(["docker", "exec", "openmaic", "cat", path], text=True)
        data = json.loads(raw)
    except Exception as e:
        print("  skip", path, e)
        continue
    new = rewrite_obj(data)
    if new == data:
        continue
    text = json.dumps(new, ensure_ascii=False, indent=2) + "\n"
    # Ghi lại bằng docker exec
    proc = subprocess.run(
        ["docker", "exec", "-i", "openmaic", "sh", "-c", f"cat > {path}"],
        input=text,
        text=True,
    )
    if proc.returncode == 0:
        fixed += 1
        print("  fixed", path)
    else:
        print("  FAIL write", path)
print(f"  repaired {fixed} classroom file(s)")
PY
unset _OM_PUB

# Smoke: generate/tts với X-Forwarded-Host công khai (giống Javis sẽ gửi)
echo "==> Smoke OpenMAIC /api/generate/tts (Edge VI)"
pub_host="$(python3 - <<PY
from urllib.parse import urlparse
u = "${OPENMAIC_PUBLIC_URL}"
p = urlparse(u if "://" in u else "http://"+u)
print(p.netloc)
PY
)"
pub_proto="$(python3 - <<PY
from urllib.parse import urlparse
u = "${OPENMAIC_PUBLIC_URL}"
p = urlparse(u if "://" in u else "http://"+u)
print(p.scheme or "http")
PY
)"
if curl -fsS -m 60 -X POST "http://127.0.0.1:${OPENMAIC_PORT}/api/generate/tts" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-Host: ${pub_host}" \
  -H "X-Forwarded-Proto: ${pub_proto}" \
  -d '{"text":"Xin chào học viên. Đây là giọng tiếng Việt chuẩn.","audioId":"javis-smoke","ttsProviderId":"openai-tts","ttsVoice":"nova"}' \
  -o /tmp/openmaic-api-tts.json 2>/dev/null; then
  python3 - <<'PY'
import json, base64, pathlib
d=json.loads(pathlib.Path("/tmp/openmaic-api-tts.json").read_text())
b=base64.b64decode(d.get("base64") or d.get("data",{}).get("base64") or "")
print(f"  OK — TTS API bytes={len(b)} success={d.get('success')}")
if len(b) < 1000:
    raise SystemExit("TTS audio too small")
PY
else
  echo "  WARN: /api/generate/tts chưa OK"
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
        # Cho phép nhúng iframe từ Javis (Bài giảng → Tạo lớp OpenMAIC)
        proxy_hide_header X-Frame-Options;
        add_header Content-Security-Policy "frame-ancestors 'self' https://javis.vietmycollege.com https://*.vietmycollege.com http://127.0.0.1:7777 http://localhost:7777" always;
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
Public URL: ${OPENMAIC_PUBLIC_URL}
  (Javis ghi vào /data/state/openmaic_public_url — audioUrl/media dùng host này)
Domain:     https://${OPENMAIC_DOMAIN}  (khi DNS + SSL OK)

ACCESS_CODE:  ${ACCESS_CODE:-OFF — cửa chính = Javis Bài giảng (không hỏi mã)}
  (bật lại: OPENMAIC_ACCESS_CODE='ma-moi' bash scripts/vps-deploy-openmaic.sh)
  Trong Javis: Việc → Bài giảng → Lớp học → «Tạo lớp OpenMAIC» (iframe, không mở domain).

TTS mặc định: OpenAI provider → Javis Edge (Hoài My / Nam Minh)
  Browser Native: TẮT (env + server-providers.yml)
  Lớp cũ: đã rewrite audioUrl host.docker.internal → PUBLIC_URL
Clone giọng:  ElevenLabs / VoxCPM khi có key hoặc GPU
LLM:          Gemini key ${KEY:+đã có}${KEY:-CHƯA có — dán vào Models rồi chạy lại deploy}

Nếu giọng vẫn sai: tạo LẠI lớp (lớp cũ trong trình duyệt có thể còn cache IndexedDB —
  mở classroom → Settings → TTS → OpenAI, hoặc xoá site data của OpenMAIC).
EOF
