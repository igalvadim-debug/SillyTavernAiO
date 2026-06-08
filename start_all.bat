@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ============================================
echo  SillyTavern AiO - Start
echo ============================================
echo.

set BASE=C:\SillyTavernAiO
set VENV_ACTIVATE=%BASE%\venv\Scripts\activate.bat
set SILERO_SERVER=%BASE%\SileroTTS\silero_api_server.py
set KOBOLD_EXE=%BASE%\KoboldCPP\koboldcpp.exe
set KOBOLD_MODELS=%BASE%\KoboldCPP\models
set ST_DIR=%BASE%\SillyTavern
set CONFIG=%ST_DIR%\config.yaml

if not exist "%VENV_ACTIVATE%" (
    echo FEHLER: venv nicht gefunden. Bitte zuerst install.bat ausfuehren.
    pause & exit /b 1
)

:: ── Schritt 1: Silero TTS ────────────────────────────────────
echo [Schritt 1] Starte Silero TTS (Port 5002)...
if not exist "%SILERO_SERVER%" (
    echo FEHLER: silero_api_server.py nicht gefunden.
    pause & exit /b 1
)
start "Silero TTS" cmd /k "call %VENV_ACTIVATE% && python %SILERO_SERVER%"
echo OK: Silero TTS gestartet.
echo.

:: ── Schritt 2: KoboldCPP Modellauswahl ──────────────────────
echo [Schritt 2] KoboldCPP Modellauswahl...
if not exist "%KOBOLD_EXE%" (
    echo FEHLER: koboldcpp.exe nicht gefunden.
    pause & exit /b 1
)

set TMPLIST=%TEMP%\kobold_models.txt
if exist "%TMPLIST%" del "%TMPLIST%"
set COUNT=0

echo.
echo Verfuegbare GGUF-Modelle:
echo ----------------------------------------
for %%f in ("%KOBOLD_MODELS%\*.gguf") do (
    set /a COUNT=!COUNT!+1
    echo %%f>> "%TMPLIST%"
    echo   [!COUNT!] %%~nxf
)

if !COUNT!==0 (
    echo WARNUNG: Keine .gguf Modelle gefunden. KoboldCPP wird uebersprungen.
    goto :start_st
)

echo ----------------------------------------
echo.
set /p CHOICE="Nummer eingeben (1-!COUNT!): "

if "!CHOICE!"=="" goto :start_st

:: Gewaehlte Zeile aus Temp-Datei lesen
set LINE=0
set SELECTED=
for /f "usebackq delims=" %%L in ("%TMPLIST%") do (
    set /a LINE=!LINE!+1
    if !LINE!==!CHOICE! set "SELECTED=%%L"
)
del "%TMPLIST%"

if "!SELECTED!"=="" (
    echo Ungueltige Auswahl: !CHOICE!
    pause & exit /b 1
)

echo.
echo Starte KoboldCPP mit: !SELECTED!
start "KoboldCPP" "%KOBOLD_EXE%" --model "!SELECTED!" --port 5001
echo OK: KoboldCPP gestartet (Port 5001).
echo.

:start_st
:: ── Schritt 3: config.yaml patchen ──────────────────────────
echo [Schritt 3] Patche config.yaml...
call "%VENV_ACTIVATE%"
if exist "%CONFIG%" (
    python -c "import re; p=r'C:\SillyTavernAiO\SillyTavern\config.yaml'; c=open(p,'r',encoding='utf-8').read(); c=re.sub(r'disableCsrfProtection:\s*\S+','disableCsrfProtection: true',c); c=re.sub(r'sessionTimeout:\s*\S+','sessionTimeout: -1',c); c=re.sub(r'koboldAIEndpoint:\s*\S+','koboldAIEndpoint: http://127.0.0.1:5001',c); c=re.sub(r'sileroEndpoint:\s*\S+','sileroEndpoint: http://127.0.0.1:5002',c); open(p,'w',encoding='utf-8').write(c); print('OK: config.yaml gepacht.')"
) else (
    echo HINWEIS: config.yaml nicht gefunden.
)
echo.

:: ── Schritt 4: SillyTavern ───────────────────────────────────
echo [Schritt 4] Starte SillyTavern...
if not exist "%ST_DIR%" (
    echo FEHLER: SillyTavern-Verzeichnis nicht gefunden.
    pause & exit /b 1
)
if exist "%ST_DIR%\Start.bat" (
    start "SillyTavern" cmd /k "cd /d %ST_DIR% && call Start.bat"
) else (
    start "SillyTavern" cmd /k "cd /d %ST_DIR% && node server.js"
)

echo.
echo ============================================
echo  Alle Dienste gestartet!
echo   Silero TTS  -^> http://127.0.0.1:5002
echo   KoboldCPP   -^> http://127.0.0.1:5001
echo   SillyTavern -^> http://127.0.0.1:8000
echo ============================================
pause
endlocal
