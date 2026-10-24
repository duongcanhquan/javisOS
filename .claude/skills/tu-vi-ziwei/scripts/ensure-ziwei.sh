#!/usr/bin/env bash
# Clone ziwei-doushu (MIT) + cài runtime iztro nhẹ cho CLI lập lá số.
set -euo pipefail

STATE_ROOT="${JAVIS_STATE_DIR:-${HOME}/.javis}"
LIB="${ZIWEI_DOUSHU_HOME:-${STATE_ROOT}/vendor/ziwei-doushu}"
RUNTIME="${ZIWEI_RUNTIME_HOME:-${STATE_ROOT}/vendor/javis-ziwei-runtime}"
REPO="${ZIWEI_DOUSHU_REPO:-https://github.com/Renhuai123/ziwei-doushu.git}"
IZTRO_VER="${ZIWEI_IZTRO_VERSION:-2.5.8}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[tu-vi-ziwei] thiếu lệnh: $1" >&2
    exit 1
  }
}

need_cmd git
need_cmd node
need_cmd npm

mkdir -p "$(dirname "$LIB")" "$(dirname "$RUNTIME")"

if [[ ! -d "$LIB/.git" ]]; then
  echo "[tu-vi-ziwei] clone $REPO → $LIB"
  git clone --depth 1 "$REPO" "$LIB"
else
  echo "[tu-vi-ziwei] đã có clone: $LIB"
  if [[ "${1:-}" == "update" ]]; then
    git -C "$LIB" fetch --depth 1 origin
    git -C "$LIB" reset --hard FETCH_HEAD
    echo "[tu-vi-ziwei] đã cập nhật clone"
  fi
fi

if [[ ! -f "$RUNTIME/package.json" ]]; then
  mkdir -p "$RUNTIME"
  cat >"$RUNTIME/package.json" <<EOF
{
  "name": "javis-ziwei-runtime",
  "private": true,
  "version": "1.0.0",
  "dependencies": {
    "iztro": "${IZTRO_VER}"
  }
}
EOF
fi

if [[ ! -d "$RUNTIME/node_modules/iztro" ]]; then
  echo "[tu-vi-ziwei] npm install iztro@${IZTRO_VER} trong $RUNTIME"
  (cd "$RUNTIME" && npm install --omit=dev --no-audit --no-fund)
else
  echo "[tu-vi-ziwei] iztro đã sẵn trong runtime"
fi

echo "LIB=$LIB"
echo "RUNTIME=$RUNTIME"
echo "CLASSICS=$LIB/lib/classics"
echo "TIANJI=$LIB/docs/tianji-ziwei"
