@echo off
title RAG WebUI
setlocal

set "ROOT=%~dp0"
set "CONDA=%ROOT%miniforge"
set "ENV=%ROOT%env"

:: Отключаем пользовательские пакеты из AppData\Roaming
:: (они конфликтуют с portable окружением)
set "PYTHONNOUSERSITE=1"

if not exist "%ENV%\python.exe" (
    echo [FEHLER] Umgebung nicht gefunden. Bitte zuerst setup.bat ausfuhren.
    pause
    exit /b 1
)

echo --- RAG WebUI ---
echo Adresse: http://127.0.0.1:7860
echo KoboldCpp auf Port 5001 wird automatisch erkannt.
echo.

"%CONDA%\Scripts\conda.exe" run -p "%ENV%" --no-capture-output python -s "%ROOT%webui.py"

pause
