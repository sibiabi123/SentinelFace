@echo off
cd /d "%~dp0"
powershell -Command "(Get-Content 'config.json') -replace '\"presence_interval_s\": \d+', '\"presence_interval_s\": 120' | Set-Content 'config.json'"
echo Switched to 2-MINUTE TEST MODE.
pause
