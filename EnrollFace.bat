@echo off
title SentinelFace Face Enrollment
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py --enroll
) else if exist "E:\windows-face-unlock\.venv\Scripts\python.exe" (
    "E:\windows-face-unlock\.venv\Scripts\python.exe" main.py --enroll
) else (
    python main.py --enroll
)
pause
