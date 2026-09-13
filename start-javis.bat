@echo off
chcp 65001 >nul
title Khoi dong Javis OS
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Chua cai lan dau. Hay chay 1-Cai-dat.bat truoc.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -c "import yaml" >nul 2>&1
if errorlevel 1 (
  echo Cai dat chua xong ^(thieu yaml^). Hay chay lai 1-Cai-dat.bat.
  echo Neu lan truoc loi pip/_musllinux: xoa .venv, copy ra D:\Javis, chay lai.
  pause
  exit /b 1
)

echo Bat Javis OS chay NEN - khong con cua so den (port 7777)...
REM Viec tat instance cu + chay server AN giao het cho start-javis.vbs (cua so an hoan toan).
REM Log ghi vao server\javis.log (mo file do neu can xem loi). Tat server: stop-javis.bat.
wscript //nologo start-javis.vbs

echo.
echo Da bat. Cho ~10 giay roi mo http://localhost:7777 va bam Ctrl+Shift+R.
echo (Tat server: chay stop-javis.bat. Xem loi: mo file server\javis.log)
timeout /t 4 >nul
