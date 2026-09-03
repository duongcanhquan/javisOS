#!/bin/bash
# Double-click trên Mac để TẮT Javis.
cd "$(dirname "$0")"
clear
echo "Tat Javis OS..."

if [ -f server/javis.pid ]; then
  kill "$(cat server/javis.pid)" 2>/dev/null || true
  rm -f server/javis.pid
fi
if lsof -tiTCP:7777 -sTCP:LISTEN >/dev/null 2>&1; then
  lsof -tiTCP:7777 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
fi

echo "Xong."
sleep 2
