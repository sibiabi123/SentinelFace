@echo off
title SentinelFace Dashboard
echo Opening SentinelFace Security Dashboard...
cd /d "E:\SentinelFace"
"E:\windows-face-unlock\.venv\Scripts\python.exe" main.py --dashboard
