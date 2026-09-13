#!/bin/bash
# Double-click trên Mac để CÀI lần đầu + chạy Javis.
# Neu Apple bao khong xac minh duoc: mo Terminal, go "bash " (co dau cach),
# keo file nay tha vao cua so Terminal, Enter.
# Hoac: cd ~/Javis && xattr -c *.command && chmod +x *.command && bash ./1-Cai-dat.command
cd "$(dirname "$0")"
# shellcheck disable=SC1091
[ -f scripts/mo-khoa-mac.sh ] && . scripts/mo-khoa-mac.sh
clear
echo "=========================================="
echo " CAI DAT JAVIS (LAN DAU)"
echo " De may cua ban ~ 2-10 phut tuy mang"
echo "=========================================="
echo

if [ ! -f scripts/ensure-venv.sh ]; then
  echo "[LOI] Thieu scripts/ensure-venv.sh."
  echo "Giai nen SAI (chi lay mot file). Can CA folder ZIP, roi chay file nay trong do."
  read -r -p "Nhan Enter de dong..."
  exit 1
fi
# shellcheck disable=SC1091
source scripts/ensure-venv.sh

if ! javis_find_python; then
  echo "[LOI] Chua co Python 3.10+."
  echo "Cai tai: https://www.python.org/downloads/macos/"
  echo "Hoac: brew install python"
  read -r -p "Nhan Enter de dong..."
  exit 1
fi
echo "Dung: $PYTHON_BIN ($("$PYTHON_BIN" --version 2>/dev/null))"

if ! javis_ensure_venv "$PYTHON_BIN"; then
  read -r -p "Nhan Enter de dong..."
  exit 1
fi

if ! javis_cai_thu_vien; then
  echo
  echo "Cai dat CHUA XONG. Javis khong duoc mo (tranh loi No module named yaml)."
  read -r -p "Nhan Enter de dong..."
  exit 1
fi

if command -v npm >/dev/null 2>&1; then
  echo "[3/3] Kiem tra Claude Code / Codex (neu can)..."
  command -v claude >/dev/null 2>&1 || npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 || true
  command -v codex >/dev/null 2>&1 || npm install -g @openai/codex >/dev/null 2>&1 || true
  echo "     Antigravity (agy): KHONG cai o day - vao Models trong app de lay lenh."
else
  echo "[3/3] Chua co Node.js - bo qua Claude/Codex. Van chat bang API key o Models."
  echo "     Antigravity (agy) cung cai tay tu trang Models (khong qua npm)."
fi

[ -f .env ] || { cp env.example .env 2>/dev/null || true; }

# Giai phong cong 7777 neu dang chiem
if lsof -tiTCP:7777 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Dang tat tien trinh cu tren cong 7777..."
  lsof -tiTCP:7777 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
  sleep 1
fi

echo
echo "Javis dang chay tai: http://localhost:7777"
echo "Buoc tiep: Models -> chon 1 bo nao -> chat."
echo "Ngay sau: double-click 2-Bat-Javis.command"
echo "Nhan Ctrl+C de dung."
echo
(sleep 3 && open "http://localhost:7777") &
cd server
exec ../.venv/bin/python main.py
