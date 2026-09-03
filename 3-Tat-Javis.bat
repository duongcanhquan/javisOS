@echo off
chcp 65001 >nul
title Tat Javis OS
cd /d "%~dp0"
call "%~dp0stop-javis.bat"
echo.
echo Da tat Javis. Co the dong cua so nay.
timeout /t 3 >nul
