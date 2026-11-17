@echo off
chcp 65001 > nul
title HuaHW-Tracker (Debug)
cd /d "%~dp0"

set PYTHON_EXE="%~dp0python-3.12.7-embed-amd64\python.exe"

if not exist %PYTHON_EXE% (
    echo [ERROR] Python not found!
    pause
    exit /b
)

%PYTHON_EXE% "%~dp0Main.py"
if %errorlevel% neq 0 pause