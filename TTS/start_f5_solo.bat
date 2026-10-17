@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
call venv\Scripts\activate.bat

echo ========================================
echo  F5-TTS Solo-Server (schnelle Einstellungen)
echo ========================================

netstat -ano | findstr ":7868 " | findstr LISTEN >nul
if not errorlevel 1 (
    echo HINWEIS: Port 7868 ist schon belegt - F5-TTS laeuft vermutlich bereits.
    pause
    exit /b 1
)

echo  Adresse im Heimnetz : http://192.168.181.200:7868/v1
echo  Stimmen             : http://192.168.181.200:7868/v1/audio/voices
echo  Schritte (nfe-step) : 11
echo  Beenden             : Ctrl+C oder Fenster schliessen
echo ========================================
echo.

python -m f5_tts.serve_openai --host 0.0.0.0 --port 7868 --nfe-step 11

echo.
echo F5-TTS Server wurde beendet.
pause
