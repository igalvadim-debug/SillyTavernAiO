@echo off
title RAG Setup
setlocal

set "ROOT=%~dp0"
set "CONDA=%ROOT%miniforge"
set "ENV=%ROOT%env"
set "INSTALLER=%ROOT%Miniforge3-installer.exe"

echo --- RAG Setup ---

:: 1. Miniforge uже есть?
if exist "%CONDA%\Scripts\conda.exe" (
    echo [OK] Miniforge найден.
    goto :create_env
)

echo [1/4] Скачиваю Miniforge3...
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe' -OutFile '%INSTALLER%'"

if not exist "%INSTALLER%" (
    echo [ОШИБКА] Не удалось скачать. Проверь интернет.
    pause
    exit /b 1
)

echo [2/4] Устанавливаю Miniforge в %CONDA%...
"%INSTALLER%" /InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /S /D=%CONDA%

if not exist "%CONDA%\Scripts\conda.exe" (
    echo [ОШИБКА] Miniforge не установился.
    pause
    exit /b 1
)
echo [OK] Miniforge установлен.
del "%INSTALLER%" 2>nul

:create_env
:: 2. Окружение уже есть?
if exist "%ENV%\python.exe" (
    echo [OK] Окружение найдено.
    goto :install_packages
)

echo [3/4] Создаю окружение Python 3.11 в %ENV%...
"%CONDA%\Scripts\conda.exe" create -p "%ENV%" python=3.11 -y --no-default-packages

if not exist "%ENV%\python.exe" (
    echo [ОШИБКА] Окружение не создалось.
    pause
    exit /b 1
)
echo [OK] Окружение создано.

:install_packages
echo [4/4] Устанавливаю пакеты...
"%CONDA%\Scripts\conda.exe" run -p "%ENV%" pip install -r "%ROOT%requirements.txt"

echo.
echo --- Готово! Запускай start.bat ---
echo.
pause
