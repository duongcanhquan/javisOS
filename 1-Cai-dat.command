#!/bin/bash
# Double-click trên Mac để CÀI lần đầu + chạy Javis.
cd "$(dirname "$0")"
clear
echo "=========================================="
echo " CAI DAT JAVIS (LAN DAU)"
echo " De may cua ban ~ 2-10 phut tuy mang"
echo "=========================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "[LOI] Chua co Python 3."
  echo "Cai tai: https://www.python.org/downloads/macos/"
  echo "Hoac: brew install python"
  read -r -p "Nhan Enter de dong..."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "[1/3] Tao moi truong ao..."
  python3 -m venv .venv
fi

echo "[2/3] Cai thu vien..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt -q

if command -v npm >/dev/null 2>&1; then
  echo "[3/3] Kiem tra Claude Code / Codex (neu can)..."
  command -v claude >/dev/null 2>&1 || npm install -g @anthropic-ai/claude-code >/dev/null 2>&1 || true
  command -v codex >/dev/null 2>&1 || npm install -g @openai/codex >/dev/null 2>&1 || true
else
  echo "[3/3] Chua co Node.js - bo qua CLI. Van chat duoc bang API key o trang Models."
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
echo "Nhan Ctrl+C de dung."
echo
(sleep 3 && open "http://localhost:7777") &
cd server
exec python main.py
