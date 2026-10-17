@echo off
chcp 65001 >nul
title SillyTavern
set "ST_DIR=D:\SillyTavernAiO\SillyTavern"

netstat -ano | findstr ":8000 " | findstr LISTEN >nul
if not errorlevel 1 goto :already

if not exist "%ST_DIR%" goto :nodir
cd /d "%ST_DIR%"
if exist "%ST_DIR%\Start.bat" (
    call Start.bat
) else (
    node server.js
)
echo.
echo SillyTavern wurde beendet.
pause
exit /b 0

:already
echo SillyTavern laeuft bereits auf Port 8000: http://127.0.0.1:8000
timeout /t 5 >nul
exit /b 0

:nodir
echo FEHLER: SillyTavern-Verzeichnis nicht gefunden: %ST_DIR%
pause
exit /b 1
