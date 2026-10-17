@echo off
chcp 65001 >nul
title SillyTavern AiO Launcher
echo ============================================
echo  SillyTavern AiO + F5-TTS + KoboldCPP
echo ============================================
echo.

set "HERE=%~dp0"
set "PY=C:\Users\Startklar\AppData\Local\Programs\Python\Python312\python.exe"
set "CONFIG=D:\SillyTavernAiO\SillyTavern\config.yaml"
if not exist "%PY%" set "PY=python"

:: config.yaml patchen (CSRF aus, Session ohne Timeout, Kobold-Endpoint)
if exist "%CONFIG%" (
    "%PY%" -c "import re; p=r'D:\SillyTavernAiO\SillyTavern\config.yaml'; c=open(p,'r',encoding='utf-8').read(); c=re.sub(r'disableCsrfProtection:\s*\S+','disableCsrfProtection: true',c); c=re.sub(r'sessionTimeout:\s*\S+','sessionTimeout: -1',c); c=re.sub(r'koboldAIEndpoint:\s*\S+','koboldAIEndpoint: http://127.0.0.1:5001',c); open(p,'w',encoding='utf-8').write(c); print('OK: config.yaml gepatcht.')"
) else (
    echo HINWEIS: config.yaml nicht gefunden.
)
echo.

:: Windows Terminal suchen: erst voller Pfad (PATH-unabhaengig), dann PATH
set "WT=%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe"
if exist "%WT%" goto :have_wt
where wt.exe >nul 2>&1
if errorlevel 1 goto :fallback
set "WT=wt.exe"

:have_wt
echo Starte alles in EINEM Fenster (Windows Terminal, 3 Tabs)...
"%WT%" -w new new-tab --title "F5-TTS" cmd /k %HERE%_tab_f5.bat ; new-tab --title "KoboldCPP" cmd /k %HERE%_tab_kobold.bat ; new-tab --title "SillyTavern" cmd /k %HERE%_tab_st.bat ; focus-tab -t 1
if errorlevel 1 goto :fallback
goto :done

:fallback
echo.
echo HINWEIS: Windows Terminal konnte nicht gestartet werden - starte 3 getrennte Fenster.
start "F5-TTS" cmd /k %HERE%_tab_f5.bat
start "KoboldCPP" cmd /k %HERE%_tab_kobold.bat
start "SillyTavern" cmd /k %HERE%_tab_st.bat

:done
echo.
echo ============================================
echo  Dienste gestartet!
echo   F5-TTS      -^> http://127.0.0.1:7868/v1
echo   KoboldCPP   -^> http://127.0.0.1:5001
echo   SillyTavern -^> http://127.0.0.1:8000
echo.
echo In SillyTavern: TTS-Provider = OpenAI Compatible,
echo Endpoint = http://127.0.0.1:7868/v1/audio/speech
echo ============================================
timeout /t 8 >nul
