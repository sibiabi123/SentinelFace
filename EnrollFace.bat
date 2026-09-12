@echo off
title SentinelFace Face Enrollment
echo Starting Face Enrollment Wizard...
cd /d "E:\SentinelFace"
"E:\windows-face-unlock\.venv\Scripts\python.exe" main.py --enroll
pause
