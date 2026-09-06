#!/usr/bin/env bash
# Nạp model Moonshine tiếng Việt (Base) lên máy chủ để browser tải cùng origin.
# Không commit file .ort vào git (~140MB). Chạy trên VPS sau deploy / lần đầu.
set -euo pipefail
DIR="${1:-/tmp/moonshine-vi}"
DEST_IN_CONTAINER="/app/dashboard/vendor/moonshine-models/vi"
BASE="https://huggingface.co/moonshine-ai/moonshine-voice-assets/resolve/main/model/base-vi/quantized/base-vi"
CONTAINER="${JAVIS_CONTAINER:-javis}"

mkdir -p "$DIR"
cd "$DIR"
for f in encoder_model.ort decoder_model_merged.ort tokenizer.bin; do
  if [[ -s "$f" ]]; then
    echo "have $f ($(wc -c <"$f") bytes)"
  else
    echo "GET $f"
    curl -L --fail --retry 5 --retry-delay 2 -o "$f" "$BASE/$f"
  fi
done
ls -lh

docker exec -u root "$CONTAINER" mkdir -p "$DEST_IN_CONTAINER"
docker cp "$DIR/encoder_model.ort" "$CONTAINER:$DEST_IN_CONTAINER/encoder_model.ort"
docker cp "$DIR/decoder_model_merged.ort" "$CONTAINER:$DEST_IN_CONTAINER/decoder_model_merged.ort"
docker cp "$DIR/tokenizer.bin" "$CONTAINER:$DEST_IN_CONTAINER/tokenizer.bin"
docker exec -u root "$CONTAINER" chmod -R a+rX /app/dashboard/vendor/moonshine-models
docker exec "$CONTAINER" ls -lh "$DEST_IN_CONTAINER"
echo "OK — browser dùng /static/vendor/moonshine-models/vi/*"
