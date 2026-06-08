@echo off
chcp 65001 >nul
echo ============================================
echo  SillyTavern AiO - Installer
echo ============================================
echo.

set PYTHON=C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe
set BASE=C:\SillyTavernAiO
set VENV=%BASE%\venv

echo [1/3] Pruefe Python...
if not exist "%PYTHON%" (
    echo FEHLER: Python nicht gefunden: %PYTHON%
    pause & exit /b 1
)
echo OK: %PYTHON%
echo.

echo [2/3] Erstelle venv in %VENV%...
if not exist "%VENV%" (
    "%PYTHON%" -m venv "%VENV%"
    if errorlevel 1 ( echo FEHLER: venv konnte nicht erstellt werden. & pause & exit /b 1 )
)
echo OK: venv bereit.
echo.

echo [3/3] Aktiviere venv und starte install.py...
call "%VENV%\Scripts\activate.bat"
python "%~dp0install.py"
if errorlevel 1 ( echo FEHLER: Installation fehlgeschlagen. & pause & exit /b 1 )

echo.
echo ============================================
echo  Installation abgeschlossen!
echo  Starte taeglich mit: start_all.bat
echo ============================================
pause
