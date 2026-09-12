@echo off
title SentinelFace Autostart Removal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --remove-autostart
) else (
    python main.py --remove-autostart
)
pause
