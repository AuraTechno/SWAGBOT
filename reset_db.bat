@echo off
chcp 65001 >nul
title SWAG VPN - Reset Database

cd /d "%~dp0"

if exist "data\bot.db" (
    del /f /q "data\bot.db"
    echo [OK] Database deleted
) else (
    echo [OK] No database found
)

pause
