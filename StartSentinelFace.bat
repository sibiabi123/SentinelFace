@echo off
title SentinelFace System Tray & Scheduler
echo Starting SentinelFace Continuous Authentication...
cd /d "E:\SentinelFace"
"E:\windows-face-unlock\.venv\Scripts\python.exe" main.py
pause
