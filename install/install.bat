@echo off
SET PYTHON_EXE="C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe"

REM Check if Python exists at the specified path
if not exist %PYTHON_EXE% (
    echo ERROR: Python not found at %PYTHON_EXE%
    echo Please install Python 3.12 or update the path in this script.
    pause
    exit /b 1
)

echo ============================================================
echo SillyTavern AiO - Installation Script
echo ============================================================
echo.

REM Check if venv exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_EXE% -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Running Python installation script...
python install_script.py
if errorlevel 1 (
    echo WARNING: Installation script completed with errors.
    echo Check the output above for details.
)

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo You can now run start_all.bat to launch all services.
echo.
pause
