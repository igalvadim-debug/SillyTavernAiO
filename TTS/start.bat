@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo ========================================
echo F5-TTS Environment Activated
echo ========================================
echo 1. Launch Gradio Web UI (infer-gradio)
echo 2. Launch Finetune Web UI (finetune-gradio)
echo 3. Open Command Prompt with venv
echo 4. Launch OpenAI-compatible TTS API (SillyTavern) on port 7868
echo ========================================

set /p choice="Select option (1-4): "

if "%choice%"=="1" (
    f5-tts_infer-gradio
) else if "%choice%"=="2" (
    f5-tts_finetune-gradio
) else if "%choice%"=="4" (
    echo Starting OpenAI-compatible TTS API on http://127.0.0.1:7868/v1 ...
    python -m f5_tts.serve_openai --port 7868 --nfe-step 11
) else (
    cmd /k
)
pause