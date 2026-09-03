#!/bin/bash
# Double-click trên Mac để BẬT Javis (chạy nền).
cd "$(dirname "$0")"
clear
echo "Bat Javis OS..."

if [ ! -d .venv ]; then
  echo "Chua cai lan dau. Hay double-click 1-Cai-dat.command truoc."
  read -r -p "Nhan Enter de dong..."
  exit 1
fi

# Tat ban cu neu co
if lsof -tiTCP:7777 -sTCP:LISTEN >/dev/null 2>&1; then
  lsof -tiTCP:7777 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
  sleep 1
fi

mkdir -p server
# shellcheck disable=SC1091
source .venv/bin/activate
nohup .venv/bin/python server/main.py >server/javis.log 2>&1 &
echo $! >server/javis.pid
echo
echo "Da bat. Mo: http://localhost:7777"
echo "Log: server/javis.log"
echo "Tat: double-click 3-Tat-Javis.command"
(sleep 2 && open "http://localhost:7777") &
sleep 2
