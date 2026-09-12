@echo off
title Register SentinelFace Background Autostart
echo Registering SentinelFace in Windows Task Scheduler...
cd /d "E:\SentinelFace"
"E:\windows-face-unlock\.venv\Scripts\python.exe" main.py --autostart
echo.
echo [SUCCESS] SentinelFace will now start invisibly in the background whenever Windows boots up!
pause
