@echo off
title SentinelFace Setup
cd /d "%~dp0"
echo Creating virtual environment...
py -3 -m venv .venv
call .venv\Scripts\activate.bat
echo Installing dependencies (this can take a few minutes, deepface pulls in TensorFlow)...
pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Setup complete. Next: run EnrollFace.bat
pause
