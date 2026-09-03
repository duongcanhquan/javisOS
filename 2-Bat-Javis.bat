@echo off
chcp 65001 >nul
title Bat Javis OS
cd /d "%~dp0"
call "%~dp0start-javis.bat"
REM Mo trinh duyet sau ~8 giay
start "" cmd /c "timeout /t 8 /nobreak >nul & start http://localhost:7777"
