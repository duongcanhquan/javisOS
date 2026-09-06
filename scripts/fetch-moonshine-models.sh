#!/usr/bin/env bash
# Nạp sẵn model Moonshine (các ngôn ngữ họp) lên VPS — browser tải cùng origin, không CDN ngoài.
# Không commit .ort vào git. Persist: /root/javis-data/moonshine-models → docker cp vào container.
#
# Dùng:
#   ./scripts/fetch-moonshine-models.sh           # tải thiếu + copy vào container javis
#   ./scripts/fetch-moonshine-models.sh --copy-only  # chỉ copy từ persist vào container (sau deploy)
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PERSIST="${JAVIS_MOONSHINE_DIR:-/root/javis-data/moonshine-models}"
HF="https://huggingface.co/moonshine-ai/moonshine-voice-assets/resolve/main/model"
DEST_IN="/app/dashboard/vendor/moonshine-models"
COPY_ONLY=0
[[ "${1:-}" == "--copy-only" ]] && COPY_ONLY=1

# lang|hf_subdir|files (comma-separated)
# Base / Tiny: encoder_model.ort,decoder_model_merged.ort,tokenizer.bin
# TinyStreaming EN: frontend.ort,encoder.ort,adapter.ort,cross_kv.ort,decoder_kv.ort,streaming_config.json,tokenizer.bin
SPECS=(
  "vi|base-vi/quantized/base-vi|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "zh|base-zh/quantized/base-zh|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "ja|base-ja/quantized/base-ja|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "ar|base-ar/quantized/base-ar|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "uk|base-uk/quantized/base-uk|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "es|base-es/quantized/base-es|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "ko|tiny-ko/quantized/tiny-ko|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  # 26_08_21 tách frontend.model.ort + frontend.weights.ort — WASM 0.1.5 cần frontend.ort (bản 26_07_30)
  "en|tiny-streaming-en/quantized_26_07_30|frontend.ort,encoder.ort,adapter.ort,cross_kv.ort,decoder_kv.ort,streaming_config.json,tokenizer.bin"
)

download_one() {
  local lang="$1" sub="$2" files_csv="$3"
  local dir="$PERSIST/$lang"
  mkdir -p "$dir"
  IFS=',' read -ra files <<< "$files_csv"
  for f in "${files[@]}"; do
    local out="$dir/$f"
    if [[ -s "$out" ]]; then
      echo "  have $lang/$f ($(wc -c <"$out") bytes)"
      continue
    fi
    echo "  GET $lang/$f"
    curl -L --fail --retry 5 --retry-delay 3 -o "$out.part" "$HF/$sub/$f"
    mv "$out.part" "$out"
  done
}

copy_into_container() {
  if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    echo "WARN: container $CONTAINER chưa chạy — bỏ qua docker cp"
    return 0
  fi
  docker exec -u root "$CONTAINER" mkdir -p "$DEST_IN"
  for spec in "${SPECS[@]}"; do
    IFS='|' read -r lang sub files_csv <<< "$spec"
    local src="$PERSIST/$lang"
    [[ -d "$src" ]] || continue
    docker exec -u root "$CONTAINER" mkdir -p "$DEST_IN/$lang"
    # shellcheck disable=SC2045
    for f in "$src"/*; do
      [[ -f "$f" ]] || continue
      docker cp "$f" "$CONTAINER:$DEST_IN/$lang/$(basename "$f")"
    done
  done
  docker exec -u root "$CONTAINER" chmod -R a+rX "$DEST_IN"
  echo "==> trong container:"
  docker exec "$CONTAINER" sh -c "du -sh $DEST_IN/* 2>/dev/null || true"
}

mkdir -p "$PERSIST"
if [[ "$COPY_ONLY" -eq 0 ]]; then
  echo "==> tải model Moonshine → $PERSIST"
  for spec in "${SPECS[@]}"; do
    IFS='|' read -r lang sub files_csv <<< "$spec"
    echo "-- $lang ($sub)"
    download_one "$lang" "$sub" "$files_csv"
  done
fi

echo "==> copy vào container $CONTAINER"
copy_into_container
echo "OK — browser: /static/vendor/moonshine-models/<lang>/*"
