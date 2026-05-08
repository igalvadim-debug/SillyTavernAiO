@echo off
SET PYTHON_EXE="C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe"

REM Check if venv exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_EXE% -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Run the Python installation script
python install_script.py

pause
