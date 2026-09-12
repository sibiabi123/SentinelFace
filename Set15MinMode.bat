@echo off
cd /d "%~dp0"
powershell -Command "(Get-Content 'config.json') -replace '\"presence_interval_s\": \d+', '\"presence_interval_s\": 900' | Set-Content 'config.json'"
echo Switched to 15-MINUTE MODE.
pause
