#!/usr/bin/env bash
# Tạo / sửa .venv rồi cài requirements. Gọi từ thư mục gốc repo:
#   source scripts/ensure-venv.sh
#   javis_find_python || exit 1
#   javis_ensure_venv || exit 1
#   javis_cai_thu_vien || exit 1
#
# KHÔNG nâng pip trước khi cài gói: `pip install --upgrade pip` hay làm vỡ
# pip._vendor.packaging._musllinux, rồi bước sau nổ `No module named yaml`.

javis_py_ok() {
  [ -x "$1" ] && "$1" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' >/dev/null 2>&1
}

javis_pip_ok() {
  [ -x "$1" ] && "$1" -m pip --version >/dev/null 2>&1
}

javis_find_python() {
  local c d cand
  PYTHON_BIN=""
  for c in python3.12 python3.11 python3.13 python3.10 python3 python3.14 python; do
    cand="$(command -v "$c" 2>/dev/null || true)"
    if [ -n "$cand" ] && javis_py_ok "$cand"; then
      PYTHON_BIN="$cand"
      return 0
    fi
  done
  for d in /opt/homebrew/bin /usr/local/bin \
           /Library/Frameworks/Python.framework/Versions/Current/bin \
           /Library/Frameworks/Python.framework/Versions/3.12/bin \
           /Library/Frameworks/Python.framework/Versions/3.11/bin; do
    for c in python3.12 python3.11 python3.13 python3.10 python3.14 python3; do
      if javis_py_ok "$d/$c"; then
        PYTHON_BIN="$d/$c"
        return 0
      fi
    done
  done
  return 1
}

javis_loi_pip() {
  cat <<'EOF'

[LOI] pip/venv hong - khong cai duoc thu vien.
Hay gap: ImportError _musllinux, roi sau do No module named yaml.

Thuong do:
  - lan cai truoc dut giua chung (thu muc .venv con do)
  - giai nen ZIP tren Desktop iCloud / OneDrive (file pip bi cat)

Lam lan luot:
  1. Xoa thu muc .venv trong folder Javis
  2. Copy CA folder ra cho khac (Mac: ~/Javis) - KHONG de tren Desktop iCloud
  3. Chay lai 1-Cai-dat.command

Can Python 3.11 hoac 3.12: https://www.python.org/downloads/macos/

EOF
}

javis_ensure_venv() {
  local py="${1:-${PYTHON_BIN:-}}"
  if [ -z "$py" ]; then
    echo "[LOI] Chua chon Python."
    return 1
  fi
  if [ -d .venv ]; then
    if [ ! -x .venv/bin/python ] || ! javis_py_ok .venv/bin/python || ! javis_pip_ok .venv/bin/python; then
      echo "Moi truong ao (.venv) hong - xoa roi tao lai..."
      rm -rf .venv
    fi
  fi
  if [ ! -d .venv ]; then
    echo "[1/3] Tao moi truong ao bang $($py --version 2>/dev/null)..."
    if ! "$py" -m venv .venv; then
      echo "[LOI] Tao .venv that bai. Cai Python 3.11+ roi chay lai."
      return 1
    fi
  fi
  if ! javis_pip_ok .venv/bin/python; then
    echo "pip hong - khoi phuc bang ensurepip..."
    .venv/bin/python -m ensurepip --upgrade >/dev/null 2>&1 || true
  fi
  if ! javis_pip_ok .venv/bin/python; then
    echo "pip van hong - tao lai .venv..."
    rm -rf .venv
    "$py" -m venv .venv || return 1
    .venv/bin/python -m ensurepip --upgrade >/dev/null 2>&1 || true
  fi
  if ! javis_pip_ok .venv/bin/python; then
    javis_loi_pip
    return 1
  fi
  return 0
}

javis_cai_thu_vien() {
  echo "[2/3] Cai thu vien (co the 2-10 phut)..."
  if ! .venv/bin/python -m pip install -r requirements.txt; then
    javis_loi_pip
    echo "Neu mang on: .venv/bin/python -m pip install --no-cache-dir -r requirements.txt"
    return 1
  fi
  if ! .venv/bin/python -c "import yaml, fastapi" >/dev/null 2>&1; then
    echo "[LOI] Cai xong nhung van thieu yaml/fastapi."
    javis_loi_pip
    return 1
  fi
  return 0
}
