@echo off
title SentinelFace Face Enrollment
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --enroll
) else (
    python main.py --enroll
)
pause
