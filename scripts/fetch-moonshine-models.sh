#!/usr/bin/env bash
# Nạp sẵn model Moonshine (các ngôn ngữ họp) lên VPS — browser tải cùng origin, không CDN ngoài.
# Không commit .ort vào git. Persist: /root/javis-data/moonshine-models → docker cp vào container.
#
# Dùng:
#   ./scripts/fetch-moonshine-models.sh           # tải thiếu + copy vào container javis
#   ./scripts/fetch-moonshine-models.sh --copy-only  # sau deploy: vẫn tải file THIẾU, rồi copy
#                                                   # (không tải lại file đã có trên persist)
set -euo pipefail

CONTAINER="${JAVIS_CONTAINER:-javis}"
PERSIST="${JAVIS_MOONSHINE_DIR:-/root/javis-data/moonshine-models}"
HF="https://huggingface.co/moonshine-ai/moonshine-voice-assets/resolve/main/model"
DEST_IN="/app/dashboard/vendor/moonshine-models"
COPY_ONLY=0
[[ "${1:-}" == "--copy-only" ]] && COPY_ONLY=1
# COPY_ONLY giữ tương thích caller (vps-deploy): vẫn tải file thiếu, không tải lại file đã có.

# lang|hf_subdir|files (comma-separated)
# Base / Tiny: encoder_model.ort,decoder_model_merged.ort,tokenizer.bin
# EN: Base (cùng layout VI) — TinyStreaming từng tải được nhưng live STT WASM không ổn.
SPECS=(
  "vi|base-vi/quantized/base-vi|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "zh|base-zh/quantized/base-zh|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "ja|base-ja/quantized/base-ja|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "ar|base-ar/quantized/base-ar|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "uk|base-uk/quantized/base-uk|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "es|base-es/quantized/base-es|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "ko|tiny-ko/quantized/tiny-ko|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
  "en|base-en/quantized/base-en|encoder_model.ort,decoder_model_merged.ort,tokenizer.bin"
)

download_one() {
  local lang="$1" sub="$2" files_csv="$3"
  local dir="$PERSIST/$lang"
  mkdir -p "$dir"
  # EN đổi TinyStreaming → Base: xóa file kiến trúc cũ để không nhầm khi copy.
  if [[ "$lang" == "en" ]]; then
    local stale
    for stale in frontend.ort encoder.ort adapter.ort cross_kv.ort decoder_kv.ort streaming_config.json; do
      if [[ -e "$dir/$stale" ]]; then
        echo "  rm stale en/$stale (TinyStreaming cũ)"
        rm -f "$dir/$stale"
      fi
    done
  fi
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
    # EN: dọn TinyStreaming cũ trong container (persist có thể còn file cũ).
    if [[ "$lang" == "en" ]]; then
      docker exec -u root "$CONTAINER" sh -c \
        "cd '$DEST_IN/en' 2>/dev/null && rm -f frontend.ort encoder.ort adapter.ort cross_kv.ort decoder_kv.ort streaming_config.json" \
        || true
    fi
    # shellcheck disable=SC2045
    for f in "$src"/*; do
      [[ -f "$f" ]] || continue
      # Bỏ qua file TinyStreaming còn sót trên disk persist
      case "$(basename "$f")" in
        frontend.ort|encoder.ort|adapter.ort|cross_kv.ort|decoder_kv.ort|streaming_config.json)
          if [[ "$lang" == "en" ]]; then
            echo "  skip stale en/$(basename "$f")"
            continue
          fi
          ;;
      esac
      docker cp "$f" "$CONTAINER:$DEST_IN/$lang/$(basename "$f")"
    done
  done
  docker exec -u root "$CONTAINER" chmod -R a+rX "$DEST_IN"
  echo "==> trong container:"
  docker exec "$CONTAINER" sh -c "du -sh $DEST_IN/* 2>/dev/null || true"
  # Fail soft nhưng rõ ràng nếu VI/EN thiếu (deploy hay quên copy → STT treo).
  if ! docker exec "$CONTAINER" test -s "$DEST_IN/vi/decoder_model_merged.ort"; then
    echo "ERROR: thiếu $DEST_IN/vi/decoder_model_merged.ort trong container — Moonshine VI sẽ 404."
    return 1
  fi
  if ! docker exec "$CONTAINER" test -s "$DEST_IN/en/decoder_model_merged.ort"; then
    echo "WARN: thiếu $DEST_IN/en/decoder_model_merged.ort — Moonshine EN sẽ 404 (chạy lại script không --copy-only)."
  fi
}

mkdir -p "$PERSIST"
# Luôn đảm bảo file SPECS có trên persist (download_one bỏ qua file đã có).
# --copy-only trước đây bỏ qua bước này → EN Base mới không bao giờ vào VPS sau deploy.
if [[ "$COPY_ONLY" -eq 1 ]]; then
  echo "==> đảm bảo model Moonshine (thiếu thì tải) → $PERSIST"
else
  echo "==> tải model Moonshine → $PERSIST"
fi
for spec in "${SPECS[@]}"; do
  IFS='|' read -r lang sub files_csv <<< "$spec"
  echo "-- $lang ($sub)"
  download_one "$lang" "$sub" "$files_csv"
done

echo "==> copy vào container $CONTAINER"
copy_into_container
echo "OK — browser: /static/vendor/moonshine-models/<lang>/*"
