#!/usr/bin/env bash
# Đặt LEMO_OPUSCAR_HOME dưới Javis state rồi gọi setup sparse của upstream.
set -euo pipefail

STATE_ROOT="${JAVIS_STATE_DIR:-${HOME}/.javis}"
export LEMO_OPUSCAR_HOME="${LEMO_OPUSCAR_HOME:-${STATE_ROOT}/vendor/lemo-opuscar}"
export LEMO_OPUSCAR_REPO="${LEMO_OPUSCAR_REPO:-https://github.com/lemomo-ai/lemo-opuscar.git}"

HERE="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM="${HERE}/setup-upstream.sh"
if [[ ! -f "$UPSTREAM" ]]; then
  echo "[lemo-opuscar] missing setup-upstream.sh next to ensure-lemo.sh" >&2
  exit 1
fi

mkdir -p "$(dirname "$LEMO_OPUSCAR_HOME")"
# shellcheck disable=SC1090
# Upstream script is POSIX sh; invoke with sh for portability.
exec sh "$UPSTREAM" "$@"
