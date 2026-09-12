@echo off
powershell -Command "(Get-Content 'E:\SentinelFace\config.json') -replace '\"presence_interval_s\": \d+', '\"presence_interval_s\": 120' | Set-Content 'E:\SentinelFace\config.json'"
echo SentinelFace switched to 2-MINUTE TEST MODE!
pause
