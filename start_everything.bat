@echo off
title Whisper Flow Ultimate Launcher
color 0B

echo ===================================================
echo      🚀 STARTING WHISPER FLOW SYSTEM
echo ===================================================

:: 1. Pehle Docker ko background mein start karo
echo.
echo [1/2] Starting Docker Backend...
docker compose up -d

:: Check agar docker fail hua
if %errorlevel% neq 0 (
    echo ❌ Error: Docker start nahi hua. Please Docker Desktop open karein.
    pause
    exit
)

:: 2. Server ke ready hone ka wait karo
echo.
echo [2/2] Waiting for AI Server to wake up...
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://localhost:5000 >nul
if %errorlevel% neq 0 (
    echo    ... connecting ...
    goto wait_loop
)
echo ✅ Connected!

:: 3. Ab Hotkey Client chalao (Ye aapke keyboard ko sunega)
echo.
echo ===================================================
echo    🎙️  SYSTEM IS LIVE!
echo    👉 Press F4 to Record anywhere.
echo    👉 Press F4 again to Paste.
echo    (Close this window to stop everything)
echo ===================================================
echo.

python global_client.py

:: 4. Jab ye window band ho, Docker bhi band kar do
echo.
echo 🛑 Stopping Docker...
docker compose down