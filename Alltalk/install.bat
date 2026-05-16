@echo off
setlocal enabledelayedexpansion

REM Alltalk Installation Script for Windows
REM This script creates a virtual environment and installs Alltalk TTS

set PYTHON_EXE=C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe
set INSTALL_DIR=D:\Alltalk
set VENV_DIR=%INSTALL_DIR%\venv

echo ============================================
echo Alltalk TTS Installation Script
echo ============================================
echo.

REM Check if Python exists
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python not found at %PYTHON_EXE%
    echo Please install Python 3.12 or update the path in this script.
    pause
    exit /b 1
)

echo Python found: %PYTHON_EXE%
echo.

REM Create installation directory
if not exist "%INSTALL_DIR%" (
    echo Creating installation directory: %INSTALL_DIR%
    mkdir "%INSTALL_DIR%"
)

cd /d "%INSTALL_DIR%"

REM Create virtual environment
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Clone Alltalk TTS repository
if not exist "%INSTALL_DIR%\alltalk_tts" (
    echo Cloning Alltalk TTS repository...
    git clone https://github.com/erew123/alltalk_tts.git
    if errorlevel 1 (
        echo ERROR: Failed to clone Alltalk TTS repository
        pause
        exit /b 1
    )
) else (
    echo Alltalk TTS repository already exists. Updating...
    cd alltalk_tts
    git pull
    cd ..
)

REM Download and extract Voices.zip
echo.
echo Downloading Voices package...
if not exist "%INSTALL_DIR%\Voices.zip" (
    curl -L -o "%INSTALL_DIR%\Voices.zip" "https://github.com/igalvadim-debug/SillyTavernAiO/raw/main/Voices.zip"
    if errorlevel 1 (
        echo WARNING: Failed to download Voices.zip with curl, trying with PowerShell...
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/igalvadim-debug/SillyTavernAiO/raw/main/Voices.zip' -OutFile '%INSTALL_DIR%\Voices.zip'"
    )
) else (
    echo Voices.zip already exists.
)

REM Extract Voices.zip
echo.
echo Extracting Voices...
if exist "%INSTALL_DIR%\Voices.zip" (
    powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\Voices.zip' -DestinationPath '%INSTALL_DIR%' -Force"
)

REM Install Python dependencies
echo.
echo Installing Python dependencies...
cd "%INSTALL_DIR%\alltalk_tts"
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================
echo Installation completed successfully!
echo ============================================
echo.
echo To start Alltalk, run:
echo   cd %INSTALL_DIR%\alltalk_tts
echo   call %VENV_DIR%\Scripts\activate.bat
echo   python main.py
echo.

pause
