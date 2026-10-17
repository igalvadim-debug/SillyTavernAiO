@echo off
chcp 65001 >nul
title F5-TTS
set "TTS_BASE=D:\SillyTavernAiO\TTS"
set "F5_PORT=7868"

netstat -ano | findstr ":%F5_PORT% " | findstr LISTEN >nul
if not errorlevel 1 goto :already

if not exist "%TTS_BASE%\venv\Scripts\activate.bat" goto :novenv
cd /d "%TTS_BASE%"
call venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
echo F5-TTS Server startet auf Port %F5_PORT% ...
echo Im Browser pruefen: http://127.0.0.1:%F5_PORT%/v1/audio/voices
echo.
python -m f5_tts.serve_openai --host 0.0.0.0 --port %F5_PORT% --nfe-step 11
echo.
echo F5-TTS wurde beendet.
pause
exit /b 0

:already
echo F5-TTS laeuft bereits auf Port %F5_PORT%.
timeout /t 5 >nul
exit /b 0

:novenv
echo FEHLER: TTS-venv nicht gefunden: %TTS_BASE%\venv
pause
exit /b 1
