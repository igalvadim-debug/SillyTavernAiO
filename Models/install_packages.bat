@echo off
title RAG Setup - Install Packages
setlocal

set "ROOT=%~dp0"
set "CONDA=%ROOT%miniforge"
set "ENV=%ROOT%env"
set "PIP=%ENV%\Scripts\pip.exe"
set "PYTHONNOUSERSITE=1"

echo --- Installiere Pakete direkt in %ENV% ---
echo.

"%PIP%" install gradio sentence-transformers chromadb requests

echo.
echo --- Fertig! ---
pause
