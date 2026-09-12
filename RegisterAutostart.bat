@echo off
title SentinelFace Autostart
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --register-autostart
) else (
    python main.py --register-autostart
)
pause
