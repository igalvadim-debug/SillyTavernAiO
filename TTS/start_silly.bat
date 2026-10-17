@echo off
setlocal enabledelayedexpansion
set "TTS_BASE=D:\SillyTavernAiO\TTS"
set "ST_BASE=D:\SillyTavernAiO"
set "ST_DIR=%ST_BASE%\SillyTavern"
set "KOBOLD_EXE=%ST_BASE%\KoboldCPP\koboldcpp.exe"
set "KOBOLD_MODELS=%ST_BASE%\KoboldCPP\models"
set "EMB_DIR=D:\Unsloth\C-claude\llama.cpp_embed"
set "EMB_MODEL=D:\claudeAgent\Coder\models\embeddinggemma-2-Q8_0\embeddinggemma-2-Q8_0.gguf"

cd /d "%TTS_BASE%"
call venv\Scripts\activate.bat
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

:menu
cls
echo ========================================
echo F5-TTS + KoboldCPP + SillyTavern  -  Launcher
echo ========================================
echo 1. Launch Gradio Web UI (infer-gradio)
echo 2. Launch Finetune Web UI (finetune-gradio)
echo 3. Open Command Prompt with venv
echo 4. Launch F5-TTS API only (own window, port 7868, LAN)
echo      -^> http://192.168.181.200:7868/v1
echo 5. Launch EVERYTHING: F5-TTS API (7868, own window)
echo    + Embedding server (embeddinggemma, local port 8080)
echo    + KoboldCPP (model choice, local port 5001)
echo    + SillyTavern (port 7869, LAN)
echo      -^> http://192.168.181.200:7869
echo 6. Stop all services
echo 7. Launch embedding server only (embeddinggemma, port 8080)
echo ========================================
set "choice="
set /p choice="Select option (1-7): "

if "%choice%"=="1" goto :gradio
if "%choice%"=="2" goto :finetune
if "%choice%"=="3" goto :shell
if "%choice%"=="4" goto :tts_only
if "%choice%"=="5" goto :st_stack
if "%choice%"=="6" goto :stopall
if "%choice%"=="7" goto :embed_only
echo Ungueltige Auswahl.
pause
goto :menu

:gradio
cd /d "%TTS_BASE%"
f5-tts_infer-gradio
pause
goto :menu

:finetune
cd /d "%TTS_BASE%"
f5-tts_finetune-gradio
pause
goto :menu

:shell
cd /d "%TTS_BASE%"
cmd /k
goto :menu

:tts_only
call :start_tts
echo.
pause
goto :menu

:embed_only
call :start_embed
echo.
pause
goto :menu

:: Subroutine: start F5-TTS API in its own window if port 7868 is not yet in use
:start_tts
netstat -ano | findstr ":7868 " | findstr LISTEN >nul
if not errorlevel 1 (
    echo F5-TTS API already running on port 7868.
    exit /b 0
)
echo Starting F5-TTS API on 0.0.0.0:7868 in its own window ...
start "F5-TTS API (7868)" cmd /k "chcp 65001 >nul && cd /d %TTS_BASE% && call venv\Scripts\activate.bat && set PYTHONIOENCODING=utf-8 && python -m f5_tts.serve_openai --host 0.0.0.0 --port 7868 --nfe-step 11"
echo OK: F5-TTS API window opened - model loading may take a moment.
echo Reachable from other PCs: http://192.168.181.200:7868/v1
exit /b 0

:: Subroutine: start the embedding server (llama.cpp + embeddinggemma) on port 8080
:start_embed
if not exist "%EMB_DIR%\llama-server.exe" (
    echo WARNING: llama-server.exe not found in %EMB_DIR% - skipping embedding server.
    exit /b 0
)
if not exist "%EMB_MODEL%" (
    echo WARNING: embedding model not found: %EMB_MODEL% - skipping embedding server.
    exit /b 0
)
netstat -ano | findstr ":8080 " | findstr LISTEN >nul
if not errorlevel 1 (
    echo Embedding server already running on port 8080.
    exit /b 0
)
echo Starting embedding server (embeddinggemma) on 0.0.0.0:8080 in its own window ...
start "Embedding Server (8080)" cmd /k "chcp 65001 >nul && cd /d %EMB_DIR% && llama-server.exe -m %EMB_MODEL% --embedding --host 0.0.0.0 --port 8080 -c 2048 -b 2048 -ub 2048 -ngl 99 --no-webui"
echo OK: embedding server window opened.
echo SillyTavern Vector Storage: source llama.cpp -^> http://127.0.0.1:8080
exit /b 0

:st_stack
echo.
if not exist "%ST_DIR%" (
    echo ERROR: SillyTavern directory not found: %ST_DIR%
    pause
    goto :menu
)
call :start_tts
call :start_embed
echo.
if not exist "%KOBOLD_EXE%" (
    echo WARNING: koboldcpp.exe not found - skipping KoboldCPP.
    goto :start_st
)
if not exist "%KOBOLD_MODELS%" mkdir "%KOBOLD_MODELS%"
set "TMPLIST=%TEMP%\kobold_models.txt"
if exist "%TMPLIST%" del "%TMPLIST%"
set COUNT=0
echo Available GGUF models:
echo ----------------------------------------
for %%f in ("%KOBOLD_MODELS%\*.gguf") do (
    set /a COUNT=!COUNT!+1
    echo %%f>> "%TMPLIST%"
    echo   [!COUNT!] %%~nxf
)
if !COUNT!==0 (
    echo WARNING: no .gguf models in %KOBOLD_MODELS% - skipping KoboldCPP.
    goto :start_st
)
echo ----------------------------------------
echo.
set "KCHOICE="
set /p KCHOICE="Enter number (1-!COUNT!), empty = skip KoboldCPP: "
if "!KCHOICE!"=="" goto :start_st
set LINE=0
set "SELECTED="
for /f "usebackq delims=" %%L in ("%TMPLIST%") do (
    set /a LINE=!LINE!+1
    if !LINE!==!KCHOICE! set "SELECTED=%%L"
)
del "%TMPLIST%"
if "!SELECTED!"=="" (
    echo Invalid selection: !KCHOICE!
    goto :start_st
)
echo Starting KoboldCPP with: !SELECTED!
start "KoboldCPP" "%KOBOLD_EXE%" --model "!SELECTED!" --port 5001
echo OK: KoboldCPP started - local port 5001.
echo.

:start_st
echo Starting SillyTavern on port 7869 - Ctrl+C to stop ...
echo Reachable from other PCs: http://192.168.181.200:7869
cd /d "%ST_DIR%"
call Start.bat
cd /d "%TTS_BASE%"
pause
goto :menu

:stopall
echo.
echo Stopping services...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { ($_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe') -and ($_.CommandLine -like '*serve_openai*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul
powershell -NoProfile -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -like '*SillyTavern*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul
powershell -NoProfile -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'koboldcpp.exe' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul
powershell -NoProfile -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'llama-server.exe' -and $_.CommandLine -like '*embeddinggemma*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul
echo OK: all services stopped.
pause
goto :menu
