@echo off
powershell -Command "(Get-Content 'E:\SentinelFace\config.json') -replace '\"presence_interval_s\": \d+', '\"presence_interval_s\": 900' | Set-Content 'E:\SentinelFace\config.json'"
echo SentinelFace switched to 15-MINUTE MODE!
pause
