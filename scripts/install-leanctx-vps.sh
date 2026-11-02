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
# Làm sạch binary cũ trong bin rồi giải nén
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
"$DEST/lean-ctx" --version

# Verification Gate: nén signature một file lớn nếu có sẵn mã nguồn
SAMPLE=""
for cand in \
  /root/javis-os/server/main.py \
  /root/javis/server/main.py \
  "$HOME/javis-os/server/main.py"
do
  if [[ -f "$cand" ]]; then SAMPLE="$cand"; break; fi
done
if [[ -n "$SAMPLE" ]]; then
  ORIG=$(wc -c < "$SAMPLE" | tr -d ' ' || echo 0)
  # pipefail: lean-ctx read lỗi không được làm hỏng cả lần cài
  COMP=$("$DEST/lean-ctx" read "$SAMPLE" -m signatures 2>/dev/null | wc -c | tr -d ' ' || true)
  COMP="${COMP:-0}"
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$ORIG" "$COMP" <<'PY' || true
import sys
o, c = int(sys.argv[1] or 0), int(sys.argv[2] or 0)
r = (1 - c / o) * 100 if o else 0
print(f"compress_gate file_bytes={o} signatures={c} save={r:.2f}%")
print("compress_gate", "PASS" if r >= 85 else "FAIL")
PY
  else
    echo "compress_gate skipped (no python3) orig=$ORIG out=$COMP"
  fi
fi

echo "NHẮC: không chạy lean-ctx onboard / lean-ctx wrap."
echo "LEANCTX_INSTALL_DONE dest=$DEST"
