@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ============================================
echo  SillyTavern AiO + F5-TTS auf Lenovo - Start
echo ============================================
echo.

set "BASE=D:\SillyTavernAiO"
set "TTS_BASE=%BASE%\TTS"
set "TTS_ACTIVATE=%TTS_BASE%\venv\Scripts\activate.bat"
set "PY=C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe"
set "KOBOLD_EXE=%BASE%\KoboldCPP\koboldcpp.exe"
set "KOBOLD_MODELS=%BASE%\KoboldCPP\models"
set "ST_DIR=%BASE%\SillyTavern"
set "CONFIG=%ST_DIR%\config.yaml"
set "F5_HOST=192.168.181.93"
set "F5_PORT=7868"

set "LLAMA_SERVER=D:\Unsloth\C-claude\llama.cpp\llama-server.exe"
set "MODELS_DIR=D:\SillyTavernNeurogen\kobold\models"
set "VLM_MODELS_DIR=D:\ComfyUiVid\models\LLM"

:: Presets
set "GEMMA_MODEL=%MODELS_DIR%\gemma-4-E4B-it-heretic-Q6_K.gguf"
set "GEMMA_MTP=%MODELS_DIR%\mtp-gemma-4-E4B-it-BF16.gguf"
set "QWEN_MODEL=%VLM_MODELS_DIR%\Qwen3-VL-4B-Instruct-abliterated.Q8_0.gguf"
set "QWEN_MMPROJ=%VLM_MODELS_DIR%\mmproj-F16.gguf"

:: Ports for the presets (free range 8510-8520, 8512+ available for more)
set "GEMMA_PORT=8510"
set "QWEN_PORT=8511"

if not exist "%PY%" set "PY=python"

:: ---- Schritt 1: F5-TTS auf Lenovo pruefen ----
echo [Schritt 1] Pruefe F5-TTS auf %F5_HOST%:%F5_PORT% ...
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 4 http://%F5_HOST%:%F5_PORT%/v1/audio/voices | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 goto :f5_down
echo OK: F5-TTS auf Lenovo erreichbar.
goto :step_llm
:f5_down
echo WARNUNG: F5-TTS auf %F5_HOST%:%F5_PORT% nicht erreichbar.
echo Lenovo an, im selben Netz und start_f5_solo.bat dort gestartet?
echo Es geht trotzdem weiter.

:: ---- Schritt 2: Sprachmodell ----
:step_llm
echo.
echo [Schritt 2] Sprachmodell waehlen
echo   1 = KoboldCPP, Modell aus Liste, Port 5001
echo   2 = llama-server Gemma-4-E4B, Port %GEMMA_PORT%
echo   3 = llama-server Qwen3-VL-4B, Port %QWEN_PORT%
echo   Enter = ueberspringen
set "LCHOICE="
set /p LCHOICE="Auswahl: "
if "!LCHOICE!"=="1" goto :kobold
if "!LCHOICE!"=="2" goto :gemma
if "!LCHOICE!"=="3" goto :qwen
goto :start_st

:gemma
if not exist "%LLAMA_SERVER%" echo FEHLER: llama-server.exe nicht gefunden. & goto :start_st
if not exist "%GEMMA_MODEL%" echo FEHLER: Gemma-Modell nicht gefunden: %GEMMA_MODEL% & goto :start_st
start "llama-server Gemma %GEMMA_PORT%" cmd /k ""%LLAMA_SERVER%" -m "%GEMMA_MODEL%" --host 127.0.0.1 --port %GEMMA_PORT% -ngl 99 -c 8192"
echo OK: Gemma gestartet auf http://127.0.0.1:%GEMMA_PORT%
goto :start_st

:qwen
if not exist "%LLAMA_SERVER%" echo FEHLER: llama-server.exe nicht gefunden. & goto :start_st
if not exist "%QWEN_MODEL%" echo FEHLER: Qwen-Modell nicht gefunden: %QWEN_MODEL% & goto :start_st
start "llama-server Qwen %QWEN_PORT%" cmd /k ""%LLAMA_SERVER%" -m "%QWEN_MODEL%" --mmproj "%QWEN_MMPROJ%" --host 127.0.0.1 --port %QWEN_PORT% -ngl 99 -c 8192"
echo OK: Qwen3-VL gestartet auf http://127.0.0.1:%QWEN_PORT%
goto :start_st

:kobold
if not exist "%KOBOLD_EXE%" echo FEHLER: koboldcpp.exe nicht gefunden. & goto :start_st
set "TMPLIST=%TEMP%\kobold_models.txt"
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
if !COUNT!==0 echo WARNUNG: Keine .gguf Modelle gefunden. & goto :start_st
echo ----------------------------------------
set "CHOICE="
set /p CHOICE="Nummer eingeben (1-!COUNT!), Enter = ueberspringen: "
if "!CHOICE!"=="" goto :start_st
set LINE=0
set "SELECTED="
for /f "usebackq delims=" %%L in ("%TMPLIST%") do (
    set /a LINE=!LINE!+1
    if !LINE!==!CHOICE! set "SELECTED=%%L"
)
del "%TMPLIST%"
if "!SELECTED!"=="" echo Ungueltige Auswahl: !CHOICE! & goto :start_st
echo Starte KoboldCPP mit: !SELECTED!
start "KoboldCPP" "%KOBOLD_EXE%" --model "!SELECTED!" --port 5001
echo OK: KoboldCPP gestartet, Port 5001.

:: ---- Schritt 3: config.yaml patchen ----
:start_st
echo.
echo [Schritt 3] Patche config.yaml...
if exist "%CONFIG%" (
    "%PY%" -c "import re; p=r'D:\SillyTavernAiO\SillyTavern\config.yaml'; c=open(p,'r',encoding='utf-8').read(); c=re.sub(r'disableCsrfProtection:\s*\S+','disableCsrfProtection: true',c); c=re.sub(r'sessionTimeout:\s*\S+','sessionTimeout: -1',c); c=re.sub(r'koboldAIEndpoint:\s*\S+','koboldAIEndpoint: http://127.0.0.1:5001',c); open(p,'w',encoding='utf-8').write(c); print('OK: config.yaml gepatcht.')"
) else (
    echo HINWEIS: config.yaml nicht gefunden.
)

:: ---- Schritt 4: SillyTavern ----
echo.
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
echo  Dienste gestartet!
echo.
echo   F5-TTS      -^> http://%F5_HOST%:%F5_PORT%/v1
echo   Stimmen     -^> http://%F5_HOST%:%F5_PORT%/v1/audio/voices
echo   SillyTavern -^> http://127.0.0.1:8000
echo.
echo In SillyTavern: TTS-Provider = OpenAI Compatible,
echo Endpoint = http://%F5_HOST%:%F5_PORT%/v1/audio/speech
echo ============================================
pause
endlocal