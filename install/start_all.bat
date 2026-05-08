@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo SillyTavern AiO - Start All Services
echo ============================================================
echo.

REM Configuration
SET BASE_DIR=%~dp0..
SET KOBOLDCPP_DIR=%BASE_DIR%\KoboldCPP
SET MODELS_DIR=D:\SillyTavernAiO\KoboldCPP\models
SET SILLYTAVERN_DIR=%BASE_DIR%\SillyTavern
SET SILERO_DIR=%BASE_DIR%\SileroTTS
SET VENV_DIR=%BASE_DIR%\install\venv

REM Check if running from install directory or base directory
if exist "%BASE_DIR%\install\install_script.py" (
    REM Running from install directory
    SET BASE_DIR=%BASE_DIR%
) else if exist "%CD%\install\install_script.py" (
    SET BASE_DIR=%CD%
    SET KOBOLDCPP_DIR=%BASE_DIR%\KoboldCPP
    SET MODELS_DIR=D:\SillyTavernAiO\KoboldCPP\models
    SET SILLYTAVERN_DIR=%BASE_DIR%\SillyTavern
    SET SILERO_DIR=%BASE_DIR%\SileroTTS
    SET VENV_DIR=%BASE_DIR%\install\venv
)

echo Base Directory: %BASE_DIR%
echo.

REM Step 1: Update SillyTavern settings.json
echo [1/4] Configuring SillyTavern settings...
call :update_sillytavern_settings
if errorlevel 1 (
    echo Warning: Could not update SillyTavern settings automatically.
    echo Please configure manually in SillyTavern UI.
)
echo.

REM Step 2: Scan for .gguf models and let user select
echo [2/4] Scanning for GGUF models...
SET MODEL_PATH=
call :scan_and_select_model
if "!MODEL_PATH!"=="" (
    echo No model selected. Exiting.
    pause
    exit /b 1
)
echo Selected model: !MODEL_PATH!
echo.

REM Step 3: Start Silero TTS in background
echo [3/4] Starting Silero TTS service...
call :start_silero_tts
echo.

REM Step 4: Start KoboldCPP with selected model
echo [4/4] Starting KoboldCPP...
call :start_koboldcpp "!MODEL_PATH!"
echo.

REM Step 5: Start SillyTavern
echo Starting SillyTavern...
call :start_sillytavern

pause
exit /b 0

:update_sillytavern_settings
    SET SETTINGS_FILE=%SILLYTAVERN_DIR%\config.yaml
    
    if not exist "%SETTINGS_FILE%" (
        echo Settings file not found at %SETTINGS_FILE%
        echo SillyTavern may need to be run once to generate config.
        exit /b 1
    )
    
    echo Updating API endpoints in config.yaml...
    
    REM Create a temporary PowerShell script to update YAML
    SET TEMP_PS=%TEMP%\update_st_config.ps1
    
    echo $configPath = "%SETTINGS_FILE%" > "%TEMP_PS%"
    echo if (Test-Path $configPath) { >> "%TEMP_PS%"
    echo     $config = Get-Content $configPath -Raw >> "%TEMP_PS%"
    echo. >> "%TEMP_PS%"
    echo     REM Update or add KoboldAI endpoint >> "%TEMP_PS%"
    echo     if ($config -match 'koboldAIEndpoint:') { >> "%TEMP_PS%"
    echo         $config = $config -replace 'koboldAIEndpoint:.*', 'koboldAIEndpoint: http://127.0.0.1:5001' >> "%TEMP_PS%"
    echo     } else { >> "%TEMP_PS%"
    echo         $config += "`nkoboldAIEndpoint: http://127.0.0.1:5001" >> "%TEMP_PS%"
    echo     } >> "%TEMP_PS%"
    echo. >> "%TEMP_PS%"
    echo     REM Update or add Silero TTS endpoint >> "%TEMP_PS%"
    echo     if ($config -match 'sileroEndpoint:') { >> "%TEMP_PS%"
    echo         $config = $config -replace 'sileroEndpoint:.*', 'sileroEndpoint: http://127.0.0.1:5002' >> "%TEMP_PS%"
    echo     } else { >> "%TEMP_PS%"
    echo         $config += "`nsileroEndpoint: http://127.0.0.1:5002" >> "%TEMP_PS%"
    echo     } >> "%TEMP_PS%"
    echo. >> "%TEMP_PS%"
    echo     Set-Content -Path $configPath -Value $config -NoNewline >> "%TEMP_PS%"
    echo     Write-Host "Config updated successfully" >> "%TEMP_PS%"
    echo } else { >> "%TEMP_PS%"
    echo     Write-Host "Config file not found" >> "%TEMP_PS%"
    echo     exit 1 >> "%TEMP_PS%"
    echo } >> "%TEMP_PS%"
    
    powershell -ExecutionPolicy Bypass -File "%TEMP_PS%"
    del "%TEMP_PS%" 2>nul
    
    exit /b 0

:scan_and_select_model
    REM Check if models directory exists
    if not exist "%MODELS_DIR%" (
        echo Models directory not found: %MODELS_DIR%
        echo Please place .gguf models in this directory.
        exit /b 1
    )
    
    REM Find all .gguf files and display numbered list
    SET count=0
    echo.
    echo Found GGUF models:
    echo -------------------
    
    for %%f in ("%MODELS_DIR%\*.gguf") do (
        set /a count+=1
        set "model_!count!=%%f"
        echo !count!. %%~nxf
    )
    
    if !count! equ 0 (
        echo No .gguf files found in %MODELS_DIR%
        exit /b 1
    )
    
    echo.
    set /p selection="Enter the number of the model to use (1-%count%): "
    
    if "!selection!"=="" (
        echo No selection made.
        exit /b 1
    )
    
    if !selection! gtr !count! (
        echo Invalid selection.
        exit /b 1
    )
    
    SET MODEL_PATH=!model_%selection%!
    exit /b 0

:start_silero_tts
    REM Activate virtual environment and start Silero TTS server
    if not exist "%VENV_DIR%" (
        echo Virtual environment not found at %VENV_DIR%
        echo Please run install.bat first.
        exit /b 1
    )
    
    REM Check if silero_tts_server.py exists, if not create it
    if not exist "%SILERO_DIR%\silero_tts_server.py" (
        echo Creating Silero TTS server script...
        call :create_silero_server_script
    )
    
    echo Starting Silero TTS on port 5002...
    start "Silero TTS" cmd /k "call "%VENV_DIR%\Scripts\activate.bat" ^&^& python "%SILERO_DIR%\silero_tts_server.py" --port 5002"
    
    REM Wait a moment for the server to start
    timeout /t 3 /nobreak >nul
    
    exit /b 0

:create_silero_server_script
    SET SERVER_SCRIPT=%SILERO_DIR%\silero_tts_server.py
    
    echo ^#!/usr/bin/env python3 > "%SERVER_SCRIPT%"
    echo """ >> "%SERVER_SCRIPT%"
    echo Silero TTS API Server >> "%SERVER_SCRIPT%"
    echo Simple Flask-based API for Silero TTS >> "%SERVER_SCRIPT%"
    echo """ >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo import sys >> "%SERVER_SCRIPT%"
    echo import argparse >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo try: >> "%SERVER_SCRIPT%"
    echo     from flask import Flask, request, jsonify, send_file >> "%SERVER_SCRIPT%"
    echo     import torch >> "%SERVER_SCRIPT%"
    echo     import io >> "%SERVER_SCRIPT%"
    echo     import wave >> "%SERVER_SCRIPT%"
    echo except ImportError as e: >> "%SERVER_SCRIPT%"
    echo     print(f"Missing dependency: {e}") >> "%SERVER_SCRIPT%"
    echo     print("Please install required packages:") >> "%SERVER_SCRIPT%"
    echo     print("  pip install flask torch torchaudio") >> "%SERVER_SCRIPT%"
    echo     sys.exit(1) >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo app = Flask(__name__) >> "%SERVER_SCRIPT%"
    echo model = None >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo def load_model^(language='ru'^): >> "%SERVER_SCRIPT%"
    echo     global model >> "%SERVER_SCRIPT%"
    echo     try: >> "%SERVER_SCRIPT%"
    echo         model, _ = torch.hub.load( >> "%SERVER_SCRIPT%"
    echo             repo_or_dir='snakers4/silero-models', >> "%SERVER_SCRIPT%"
    echo             model='silero_tts', >> "%SERVER_SCRIPT%"
    echo             language=language, >> "%SERVER_SCRIPT%"
    echo             speaker='v3_ru' if language == 'ru' else 'v3_en' >> "%SERVER_SCRIPT%"
    echo         ^) >> "%SERVER_SCRIPT%"
    echo         print(f"Silero TTS model loaded for language: {language}") >> "%SERVER_SCRIPT%"
    echo         return True >> "%SERVER_SCRIPT%"
    echo     except Exception as e: >> "%SERVER_SCRIPT%"
    echo         print(f"Failed to load model: {e}") >> "%SERVER_SCRIPT%"
    echo         return False >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo @app.route^('/health'^): >> "%SERVER_SCRIPT%"
    echo def health^(: >> "%SERVER_SCRIPT%"
    echo     return jsonify^{^{"status": "ok", "model_loaded": model is not None}^} >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo @app.route^('/tts', methods=['POST'^]): >> "%SERVER_SCRIPT%"
    echo def text_to_speech^(: >> "%SERVER_SCRIPT%"
    echo     if model is None: >> "%SERVER_SCRIPT%"
    echo         return jsonify^{^{"error": "Model not loaded"}^}, 500 >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo     data = request.get_json^(^) >> "%SERVER_SCRIPT%"
    echo     text = data.get^('text', ''^) >> "%SERVER_SCRIPT%"
    echo     if not text: >> "%SERVER_SCRIPT%"
    echo         return jsonify^{^{"error": "No text provided"}^}, 400 >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo     try: >> "%SERVER_SCRIPT%"
    echo         audio = model.apply_tts^text=text^) >> "%SERVER_SCRIPT%"
    echo         >> "%SERVER_SCRIPT%"
    echo         REM Convert to WAV format >> "%SERVER_SCRIPT%"
    echo         buffer = io.BytesIO^^) >> "%SERVER_SCRIPT%"
    echo         with wave.open^buffer, 'wb'^) as wf: >> "%SERVER_SCRIPT%"
    echo             wf.setnchannels^1^) >> "%SERVER_SCRIPT%"
    echo             wf.setsampwidth^2^) >> "%SERVER_SCRIPT%"
    echo             wf.setframerate^48000^) >> "%SERVER_SCRIPT%"
    echo             wf.writeframes^^(audio.numpy^.^).tobytes^)^) >> "%SERVER_SCRIPT%"
    echo         buffer.seek^0^) >> "%SERVER_SCRIPT%"
    echo         >> "%SERVER_SCRIPT%"
    echo         return send_file^buffer, mimetype='audio/wav', as_attachment=True, download_name='speech.wav'^) >> "%SERVER_SCRIPT%"
    echo     except Exception as e: >> "%SERVER_SCRIPT%"
    echo         return jsonify^{^{"error": str^e^)}^}, 500 >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo if __name__ == '__main__': >> "%SERVER_SCRIPT%"
    echo     parser = argparse.ArgumentParser^description='Silero TTS Server'^) >> "%SERVER_SCRIPT%"
    echo     parser.add_argument^('--port', type=int, default=5002, help='Port to run the server on'^) >> "%SERVER_SCRIPT%"
    echo     parser.add_argument^('--language', type=str, default='ru', help='Language code'^) >> "%SERVER_SCRIPT%"
    echo     args = parser.parse_args^)^) >> "%SERVER_SCRIPT%"
    echo. >> "%SERVER_SCRIPT%"
    echo     print^f"Starting Silero TTS server on port {args.port}..."^) >> "%SERVER_SCRIPT%"
    echo     if load_model^args.language^): >> "%SERVER_SCRIPT%"
    echo         app.run^host='127.0.0.1', port=args.port, debug=False^) >> "%SERVER_SCRIPT%"
    echo     else: >> "%SERVER_SCRIPT%"
    echo         print^"Failed to load TTS model. Exiting."^) >> "%SERVER_SCRIPT%"
    echo         sys.exit^1^) >> "%SERVER_SCRIPT%"
    
    exit /b 0

:start_koboldcpp
    SET MODEL_ARG=%~1
    
    if not exist "%KOBOLDCPP_DIR%\koboldcpp.exe" (
        echo KoboldCPP executable not found at %KOBOLDCPP_DIR%\koboldcpp.exe
        echo Please run install.bat first.
        exit /b 1
    )
    
    echo Starting KoboldCPP with model: %MODEL_ARG%
    start "KoboldCPP" cmd /k ""%KOBOLDCPP_DIR%\koboldcpp.exe" --model "%MODEL_ARG%" --port 5001 --usecublas"
    
    REM Wait for KoboldCPP to initialize
    timeout /t 5 /nobreak >nul
    
    exit /b 0

:start_sillytavern
    if not exist "%SILLYTAVERN_DIR%\server.js" (
        echo SillyTavern server.js not found at %SILLYTAVERN_DIR%\server.js
        echo Please run install.bat first.
        exit /b 1
    )
    
    echo Starting SillyTavern on port 8000...
    start "SillyTavern" cmd /k "cd /d "%SILLYTAVERN_DIR%" ^&^& node server.js"
    
    echo.
    echo ============================================================
    echo All services starting...
    echo ============================================================
    echo - Silero TTS:    http://127.0.0.1:5002
    echo - KoboldCPP:     http://127.0.0.1:5001
    echo - SillyTavern:   http://127.0.0.1:8000
    echo ============================================================
    echo.
    echo Open your browser and navigate to http://127.0.0.1:8000
    echo.
    
    exit /b 0
