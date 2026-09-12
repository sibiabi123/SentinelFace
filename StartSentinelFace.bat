@echo off
title SentinelFace System Tray & Scheduler
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else if exist "E:\windows-face-unlock\.venv\Scripts\python.exe" (
    "E:\windows-face-unlock\.venv\Scripts\python.exe" main.py
) else (
    python main.py
)
pause
