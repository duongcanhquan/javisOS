#!/usr/bin/env bash
# Clone upstream video-shotcraft into Javis state vendor (idempotent).
set -euo pipefail

REPO_URL="${POSTCARD_SHOTCRAFT_URL:-https://github.com/Vincentwei1021/video-shotcraft.git}"
STATE_ROOT="${JAVIS_STATE_DIR:-${HOME}/.javis}"
TARGET="${POSTCARD_SHOTCRAFT_DIR:-${STATE_ROOT}/vendor/video-shotcraft}"

mkdir -p "$(dirname "$TARGET")"

if [[ -d "${TARGET}/.git" ]]; then
  echo "[postcard-video] upstream already at: ${TARGET}"
  git -C "$TARGET" fetch --depth 1 origin 2>/dev/null || true
  # Stay on whatever branch clone used (usually main/master); do not reset user edits.
  echo "$TARGET"
  exit 0
fi

if [[ -e "$TARGET" ]]; then
  echo "[postcard-video] path exists but is not a git repo: ${TARGET}" >&2
  echo "[postcard-video] move it aside or set POSTCARD_SHOTCRAFT_DIR" >&2
  exit 1
fi

echo "[postcard-video] cloning ${REPO_URL} -> ${TARGET}"
git clone --depth 1 "$REPO_URL" "$TARGET"
echo "$TARGET"
