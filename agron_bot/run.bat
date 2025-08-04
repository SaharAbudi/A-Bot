@echo off
title Agron Bot Starter
cls

set SCRIPT_PATH=C:\Users\USER\Desktop\אגרון\agron-bot\agron_bot\main.py

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH!
    pause
    exit /b
)

echo ✅ Python is installed.

echo Checking if %SCRIPT_PATH% exists...
if not exist "%SCRIPT_PATH%" (
    echo ❌ File not found at:
    echo %SCRIPT_PATH%
    pause
    exit /b
)

echo ✅ Found main.py

echo 🔄 Starting Agron Bot...
python "%SCRIPT_PATH%"

echo 🔚 Bot finished running (or crashed).
pause
