@echo off
chcp 65001 > nul
cd /d "%~dp0"

set PYTHONW_EXE="%~dp0python-3.12.7-embed-amd64\pythonw.exe"

if not exist %PYTHONW_EXE% (
    echo [ERROR] pythonw.exe not found!
    pause
    exit /b
)

:: Запускаем в фоне и сразу выходим
start "" %PYTHONW_EXE% "%~dp0Main.py"
exit