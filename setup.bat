@echo off
chcp 65001 >nul
title Javis OS
echo.
echo  ==========================================
echo   JAVIS OS
echo  ==========================================
echo.

cd /d "%~dp0"

REM Check Python (khong dung ban Store stub / qua cu)
python --version >nul 2>&1
if errorlevel 1 (
  echo [LOI] Python chua cai. Tai tai python.org roi tick "Add to PATH".
  echo.
  pause
  exit /b 1
)
python -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
  echo [LOI] Python qua cu. Can 3.10 tro len, nen 3.11 hoac 3.12.
  echo Tai: https://www.python.org/downloads/windows/
  echo.
  pause
  exit /b 1
)

set "VPY=%~dp0.venv\Scripts\python.exe"

REM .venv cu / pip vo (_musllinux) -> xoa roi tao lai, khong dung tiep
if exist ".venv\" (
  if exist "%VPY%" (
    "%VPY%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)" >nul 2>&1
    if errorlevel 1 (
      echo .venv Python cu - xoa roi tao lai...
      rmdir /s /q .venv 2>nul
    ) else (
      "%VPY%" -m pip --version >nul 2>&1
      if errorlevel 1 (
        echo pip trong .venv hong - xoa roi tao lai...
        rmdir /s /q .venv 2>nul
      )
    )
  ) else (
    echo .venv thieu python.exe - xoa roi tao lai...
    rmdir /s /q .venv 2>nul
  )
)

if not exist ".venv\" (
  echo [1/4] Tao virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo [LOI] Tao .venv that bai. Cai Python 3.11+ tu python.org, tick PATH, mo cmd MOI.
    pause
    exit /b 1
  )
)

"%VPY%" -m pip --version >nul 2>&1
if errorlevel 1 (
  echo pip hong - khoi phuc ensurepip...
  "%VPY%" -m ensurepip --upgrade >nul 2>&1
)
"%VPY%" -m pip --version >nul 2>&1
if errorlevel 1 (
  echo [LOI] pip khong chay duoc (hay gap ImportError _musllinux).
  echo   1. Xoa thu muc .venv
  echo   2. Copy Javis ra D:\Javis ^(KHONG de Desktop OneDrive^)
  echo   3. Chay lai 1-Cai-dat.bat
  pause
  exit /b 1
)

echo [2/4] Cai thu vien...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [LOI] Cai thu vien THAT BAI. Khong khoi dong Javis.
  echo Neu thay _musllinux hoac No module named yaml:
  echo   1. Xoa thu muc .venv
  echo   2. Copy ra D:\Javis (KHONG de Desktop OneDrive)
  echo   3. Chay lai 1-Cai-dat.bat
  pause
  exit /b 1
)

"%VPY%" -c "import yaml, fastapi" >nul 2>&1
if errorlevel 1 (
  echo [LOI] Thieu yaml - cai dat chua xong. Xoa .venv roi chay lai 1-Cai-dat.bat
  pause
  exit /b 1
)

REM ---- CLI dang ky subscription (khong bat buoc API key) ----
REM Chi cai Claude Code + Codex (npm). Antigravity (`agy`) KHONG cai o day:
REM Google dung script rieng; user cai theo the Models trong app.
REM Chua co Node: bo qua - Javis van chay, chat bang API key o trang Models.
echo [3/4] Kiem tra cac bo nao CLI (Claude Code, Codex)...
where npm >nul 2>&1
if errorlevel 1 (
  echo     [!] Chua co Node.js nen bo qua buoc nay.
  echo         Muon Claude Code / ChatGPT-Codex: cai Node 22 o nodejs.org roi chay lai.
  echo         Muon Google Antigravity: xem the Models trong app ^(khong cai bang npm^).
) else (
  call :cai_cli @anthropic-ai/claude-code claude "Claude Code"
  call :cai_cli @openai/codex codex "Codex - goi ChatGPT"
  echo     - Antigravity CLI ^(agy^): khong cai o day - vao Models de lay lenh cai.
)

REM Giai phong port 7777 neu dang bi chiem
echo [4/4] Giai phong port 7777...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":7777" ^| findstr "LISTENING"') do (
  echo     Dang tat tien trinh cu PID %%a
  taskkill /F /PID %%a >nul 2>&1
)

echo.
echo  ==========================================
echo   Javis OS dang chay tai: http://localhost:7777
echo   Buoc tiep: mo trang Models, chon 1 bo nao roi chat.
echo   ^(Claude/Codex neu da cai; API key; hoac Antigravity `agy`^)
echo   File nay = nhan cua 1-Cai-dat.bat. Ngay sau: 2-Bat-Javis.bat
echo   Nhan Ctrl+C de dung.
echo  ==========================================
echo.

cd /d "%~dp0server"
"%VPY%" main.py

REM Neu python thoat (loi), giu cua so de doc loi
echo.
echo  [!] Server da dung. Xem loi o tren (neu co).
pause
exit /b 0

REM ============================ Ham phu ============================
REM %1 = goi npm, %2 = ten binary, %3 = ten hien thi. Da co thi bo qua, hong thi chi bao mot
REM dong roi di tiep - mot engine cai hong khong duoc chan ca lan cai.
REM LUU Y khi them dong goi moi: ten hien thi KHONG duoc chua dau ngoac don. No bi echo ben
REM trong khoi if(...) duoi day, ma batch bung %~3 luc phan tich khoi, nen mot dau ')' trong
REM ten se dong khoi som va lam hong ca ham.
:cai_cli
where %2 >nul 2>&1
if not errorlevel 1 (
  echo     - %~3: da co san
  goto :eof
)
echo     - %~3: dang cai (npm install -g %1)...
call npm install -g %1 >nul 2>&1
if errorlevel 1 (
  echo       [!] Chua cai duoc. Cai tay khi ranh: npm install -g %1
) else (
  echo       OK
)
goto :eof
