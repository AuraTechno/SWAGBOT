@echo off
chcp 65001 >nul
title SWAG VPN Bot

cd /d "%~dp0"

if exist ".env" (
    echo [OK] .env found
) else (
    echo [ERROR] .env not found!
    pause
    exit /b 1
)

if exist "venv\Scripts\python.exe" (
    echo [OK] Virtual environment found
) else (
    echo Creating virtual environment...
    python -m venv venv
)

echo Installing dependencies...
call venv\Scripts\pip.exe install -r requirements.txt >nul 2>&1

echo Starting bot...
venv\Scripts\python.exe -m bot.main

pause
