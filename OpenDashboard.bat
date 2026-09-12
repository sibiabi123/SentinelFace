@echo off
title SentinelFace Dashboard
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --dashboard
) else if exist "E:\windows-face-unlock\.venv\Scripts\python.exe" (
    "E:\windows-face-unlock\.venv\Scripts\python.exe" main.py --dashboard
) else (
    python main.py --dashboard
)
pause
