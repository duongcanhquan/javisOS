#!/usr/bin/env bash
# Cài LeanCTX v3.12.0 trên HOST VPS (sandbox độc lập).
# KHÔNG chạy onboard / wrap. Telemetry tắt.
set -euo pipefail

VER="${LEANCTX_VERSION:-v3.12.0}"
DEST="${LEANCTX_DEST:-/data/leanctx_sandbox}"
BASE="https://github.com/yvgude/lean-ctx/releases/download/${VER}"

arch="$(uname -m)"
case "$arch" in
  x86_64|amd64) asset="lean-ctx-x86_64-unknown-linux-gnu.tar.gz" ;;
  aarch64|arm64) asset="lean-ctx-aarch64-unknown-linux-gnu.tar.gz" ;;
  *) echo "Kiến trúc chưa hỗ trợ: $arch" >&2; exit 1 ;;
esac

echo "==> LeanCTX ${VER} → ${DEST} (${arch} / ${asset})"
mkdir -p "$DEST/bin" "$DEST/cache"
tmp="$DEST/cache/${asset}"
if [[ ! -f "$tmp" ]]; then
  curl -fsSL -o "$tmp" "${BASE}/${asset}"
fi
find "$DEST/bin" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
tar -xzf "$tmp" -C "$DEST/bin"
bin="$(find "$DEST/bin" -type f -name 'lean-ctx' | head -n 1)"
if [[ -z "$bin" ]]; then
  echo "Không tìm thấy lean-ctx trong archive" >&2
  exit 1
fi
chmod +x "$bin"
ln -sfn "$bin" "$DEST/lean-ctx"

echo "==> telemetry off"
"$DEST/lean-ctx" telemetry off

echo "==> version"
"$DEST/lean-ctx" --version || true

# Verification Gate (không được làm fail lần cài)
set +e
SAMPLE=""
for cand in \
  /root/javis-os/server/main.py \
  /root/javis/server/main.py \
  "$HOME/javis-os/server/main.py"
do
  if [[ -f "$cand" ]]; then SAMPLE="$cand"; break; fi
done
if [[ -n "$SAMPLE" ]]; then
  echo "==> compress_gate sample=$SAMPLE"
  ORIG=$(wc -c < "$SAMPLE" | tr -d ' ')
  COMP=$("$DEST/lean-ctx" read "$SAMPLE" -m signatures 2>/dev/null | wc -c | tr -d ' ')
  COMP=${COMP:-0}
  ORIG=${ORIG:-0}
  if [[ "$ORIG" -gt 0 ]]; then
    # integer % save without python (tránh python3 - argv lệch trên một số image)
    SAVE=$(( (1000 * (ORIG - COMP) / ORIG) ))
    SAVE_PCT=$((SAVE / 10)).$((SAVE % 10))
    echo "compress_gate file_bytes=$ORIG signatures=$COMP save=${SAVE_PCT}%"
    if [[ "$SAVE" -ge 850 ]]; then
      echo "compress_gate PASS"
    else
      echo "compress_gate FAIL (cài vẫn OK)"
    fi
  fi
fi
set -e

echo "NHẮC: không chạy lean-ctx onboard / lean-ctx wrap."
echo "LEANCTX_INSTALL_DONE dest=$DEST"
