#!/usr/bin/env bash
# Clone upstream remotion-cuongit-template vào Javis state vendor (idempotent).
set -euo pipefail

REPO_URL="${REMOTION_CUONGIT_URL:-https://github.com/Cuongyd196/remotion-cuongit-template.git}"
STATE_ROOT="${JAVIS_STATE_DIR:-${HOME}/.javis}"
TARGET="${REMOTION_CUONGIT_DIR:-${STATE_ROOT}/vendor/remotion-cuongit-template}"

mkdir -p "$(dirname "$TARGET")"

if [[ -d "${TARGET}/.git" ]]; then
  echo "[remotion-topic-explainer] upstream already at: ${TARGET}"
  git -C "$TARGET" fetch --depth 1 origin 2>/dev/null || true
  echo "$TARGET"
  exit 0
fi

if [[ -e "$TARGET" ]]; then
  echo "[remotion-topic-explainer] path exists but is not a git repo: ${TARGET}" >&2
  echo "[remotion-topic-explainer] move it aside or set REMOTION_CUONGIT_DIR" >&2
  exit 1
fi

echo "[remotion-topic-explainer] cloning ${REPO_URL} -> ${TARGET}"
git clone --depth 1 "$REPO_URL" "$TARGET"
echo "$TARGET"
