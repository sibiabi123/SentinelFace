@echo off
title SentinelFace Dashboard
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --dashboard
) else (
    python main.py --dashboard
)
