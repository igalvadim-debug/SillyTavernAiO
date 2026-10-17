@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title KoboldCPP
set "KOBOLD_DIR=D:\SillyTavernAiO\KoboldCPP"
set "KOBOLD_EXE=%KOBOLD_DIR%\koboldcpp.exe"
set "MODELS=%KOBOLD_DIR%\models"
set "LM=C:\Users\Startklar\.lmstudio\models\lmstudio-community"
set "KOBOLD_PORT=5001"
set "KOBOLD_CTX=16384"
set "DEFAULT=5"

netstat -ano | findstr ":%KOBOLD_PORT% " | findstr LISTEN >nul
if not errorlevel 1 goto :already
if not exist "%KOBOLD_EXE%" goto :noexe

:: ---- Modell-Liste (hier aendern/ergaenzen) ----
set "N1=Dolphin3.0-Llama3.1-8B-abliterated Q4_K_M"
set "P1=%MODELS%\Dolphin3.0-Llama3.1-8B-abliterated.i1-Q4_K_M.gguf"

set "N2=Gemma-4-26B-A4B heretic APEX-I Compact"
set "P2=%MODELS%\gemma-4-26B-A4B-heretic-APEX-I-Compact.gguf"

set "N3=Gemma-4-E2B Uncensored HauhauCS Q6_K_P (mit mmproj)"
set "P3=%MODELS%\Gemma-4-E2B-Uncensored-HauhauCS-Aggressive-Q6_K_P.gguf"
set "MM3=%MODELS%\mmproj-Gemma-4-E2B-Uncensored-HauhauCS-Aggressive-f16.gguf"

set "N4=Gemma-4-E4B heretic Q4_K_M"
set "P4=%MODELS%\gemma-4-E4B-it-heretic-Q4_K_M.gguf"

set "N5=Gemma-4-E4B heretic Q8_0 (Standard)"
set "P5=%MODELS%\gemma-4-E4B-it-heretic-Q8_0.gguf"

set "N6=L3-8B-Stheno-v3.2 Q4_K_M (LM Studio)"
set "P6=%LM%\L3-8B-Stheno-v3.2-Q4_K_M\L3-8B-Stheno-v3.2-Q4_K_M.gguf"

set "N7=Mistral-7B-Instruct-v0.3 abliterated Q5_K_S"
set "P7=%MODELS%\Mistral-7B-Instruct-v0.3-abliterated.Q5_K_S.gguf"

set "N8=Mistral-Nemo-12B-Instruct-2407 Q4_K_S (LM Studio)"
set "P8=%LM%\Mistral-Nemo-12B-Instruct-2407-Q4_K_S\Mistral-Nemo-12B-Instruct-2407-Q4_K_S.gguf"
set COUNT=8

echo ============================================
echo  KoboldCPP - Modell waehlen
echo ============================================
for /l %%i in (1,1,%COUNT%) do echo   [%%i] !N%%i!
echo ============================================
set "CHOICE="
set /p "CHOICE=Nummer 1-%COUNT%, Enter = %DEFAULT%: "
if "!CHOICE!"=="" set "CHOICE=%DEFAULT%"

set "KOBOLD_MODEL="
set "MMPROJ="
set "NAME="
for %%i in (!CHOICE!) do (
    set "KOBOLD_MODEL=!P%%i!"
    set "MMPROJ=!MM%%i!"
    set "NAME=!N%%i!"
)
if not defined KOBOLD_MODEL goto :badchoice
if not exist "!KOBOLD_MODEL!" goto :nofile

cd /d "%KOBOLD_DIR%"
echo.
echo KoboldCPP startet: !NAME!
echo Datei: !KOBOLD_MODEL!
echo Port %KOBOLD_PORT%, Kontext %KOBOLD_CTX%
echo.
if defined MMPROJ goto :run_mm
"%KOBOLD_EXE%" --model "!KOBOLD_MODEL!" --port %KOBOLD_PORT% --contextsize %KOBOLD_CTX% --usecuda --gpulayers 99 --skiplauncher
goto :ended

:run_mm
"%KOBOLD_EXE%" --model "!KOBOLD_MODEL!" --mmproj "!MMPROJ!" --port %KOBOLD_PORT% --contextsize %KOBOLD_CTX% --usecuda --gpulayers 99 --skiplauncher

:ended
echo.
echo KoboldCPP wurde beendet.
pause
exit /b 0

:already
echo KoboldCPP laeuft bereits auf Port %KOBOLD_PORT%.
timeout /t 5 >nul
exit /b 0

:noexe
echo FEHLER: koboldcpp.exe nicht gefunden: %KOBOLD_EXE%
pause
exit /b 1

:badchoice
echo Ungueltige Auswahl.
pause
exit /b 1

:nofile
echo FEHLER: Modelldatei nicht gefunden: !KOBOLD_MODEL!
pause
exit /b 1
