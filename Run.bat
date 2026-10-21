@echo off
chcp 65001 > nul
"%~dp0python-3.12.7-embed-amd64\python.exe" "%~dp0Main.py" %*
if %errorlevel% neq 0 pause