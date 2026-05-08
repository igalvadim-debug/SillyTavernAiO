#!/usr/bin/env python3
"""
Install script for SillyTavern AiO
This script installs:
- SillyTavern (cloned from GitHub)
- KoboldCPP (downloaded from GitHub releases)
- Silero TTS (Python dependencies and setup with Russian model v5_5_ru.pt)
"""

import os
import sys
import subprocess
import urllib.request
import json

# Configuration
BASE_DIR = r"D:\SillyTavernAiO"
KOBOLD_DIR = os.path.join(BASE_DIR, "KoboldCPP")
MODELS_DIR = os.path.join(KOBOLD_DIR, "models")
SILLYTAVERN_DIR = os.path.join(BASE_DIR, "SillyTavern")
SILERO_DIR = os.path.join(BASE_DIR, "SileroTTS")
SILERO_MODELS_DIR = os.path.join(SILERO_DIR, "models")
SILERO_MODEL_FILE = os.path.join(SILERO_MODELS_DIR, "v5_5_ru.pt")
SILERO_MODEL_URL = "https://models.silero.ai/models/tts/ru/v5_5_ru.pt"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def download_file(url, destination):
    if os.path.exists(destination):
        print(f"File already exists: {destination}")
        return
    
    print(f"Downloading {url} to {destination}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response, open(destination, 'wb') as out_file:
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            block_size = 8192
            
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                
                if total > 0:
                    percent = (downloaded / total) * 100
                    print(f"\rProgress: {percent:.2f}%", end='')
            print("\nDownload complete.")
    except Exception as e:
        print(f"Error downloading file: {e}")
        raise

def install_sillytavern():
    print("\n--- Installing SillyTavern ---")
    ensure_dir(SILLYTAVERN_DIR)
    
    if not os.path.exists(os.path.join(SILLYTAVERN_DIR, ".git")):
        print("Cloning SillyTavern repository...")
        try:
            subprocess.run(["git", "clone", "https://github.com/SillyTavern/SillyTavern.git", SILLYTAVERN_DIR], check=True)
        except subprocess.CalledProcessError:
            print("Failed to clone SillyTavern. Please check your internet connection and git installation.")
            return False
    else:
        print("SillyTavern repository already exists. Pulling latest changes...")
        try:
            subprocess.run(["git", "-C", SILLYTAVERN_DIR, "pull"], check=True)
        except subprocess.CalledProcessError:
            print("Failed to pull SillyTavern updates.")
    
    print("Installing Node.js dependencies for SillyTavern...")
    try:
        subprocess.run(["npm", "install"], cwd=SILLYTAVERN_DIR, check=True)
    except FileNotFoundError:
        print("ERROR: npm (Node.js) not found! Please install Node.js first.")
        return False
    except subprocess.CalledProcessError:
        print("Failed to install npm dependencies.")
        return False
        
    return True

def install_koboldcpp():
    print("\n--- Installing KoboldCPP ---")
    ensure_dir(KOBOLD_DIR)
    ensure_dir(MODELS_DIR)
    
    kobold_exe = os.path.join(KOBOLD_DIR, "koboldcpp.exe")
    if not os.path.exists(kobold_exe):
        print("Downloading KoboldCPP...")
        api_url = "https://api.github.com/repos/LostRuins/koboldcpp/releases/latest"
        try:
            with urllib.request.urlopen(api_url) as response:
                data = response.read().decode()
                release_data = json.loads(data)
                asset_url = None
                for asset in release_data.get("assets", []):
                    if asset["name"] == "koboldcpp.exe":
                        asset_url = asset["browser_download_url"]
                        break
                
                if asset_url:
                    download_file(asset_url, kobold_exe)
                else:
                    print("Could not find koboldcpp.exe in latest release assets.")
                    return False
        except Exception as e:
            print(f"Error fetching latest KoboldCPP release: {e}")
            print("Please download koboldcpp.exe manually to: " + KOBOLD_DIR)
            return False
    else:
        print("KoboldCPP already exists.")
        
    return True

def install_silero_tts():
    print("\n--- Installing Silero TTS Dependencies & Model ---")
    ensure_dir(SILERO_DIR)
    ensure_dir(SILERO_MODELS_DIR)
    
    # 1. CRITICAL: Install Python dependencies into the active virtual environment
    packages = ["torch", "torchaudio", "flask", "numpy", "scipy", "soundfile"]
    
    print(f"Installing required Python packages: {', '.join(packages)}")
    print(f"Using Python interpreter: {sys.executable}")
    
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + packages
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("ERROR: Failed to install Silero dependencies!")
        print("Please check your internet connection and pip configuration.")
        return False
    
    print("Silero dependencies installed successfully.")

    # 2. Download the specific Russian model v5_5_ru.pt
    if not os.path.exists(SILERO_MODEL_FILE):
        print(f"\nDownloading Silero Russian model (v5_5_ru.pt) to {SILERO_MODELS_DIR}...")
        try:
            download_file(SILERO_MODEL_URL, SILERO_MODEL_FILE)
        except Exception as e:
            print(f"Warning: Could not auto-download model. Error: {e}")
            print("You may need to download it manually.")
    else:
        print(f"Model already exists at {SILERO_MODEL_FILE}.")
    
    # 3. Create the Silero API Server Script
    server_script_path = os.path.join(SILERO_DIR, "silero_api_server.py")
    print(f"\nCreating Silero API Server script at {server_script_path}...")
    
    escaped_path = SILERO_MODEL_FILE.replace('\\', '\\\\')
    
    server_code = f'''import os
import sys
import torch
from flask import Flask, request, jsonify, send_file
import wave
import numpy as np
import io

app = Flask(__name__)

MODEL_PATH = r"{escaped_path}"
DEVICE = torch.device('cpu')

print(f"Loading Silero TTS model from: {{MODEL_PATH}}")

model = None

def load_model():
    global model
    try:
        print("Loading base model architecture from snakers4/silero-models (v5_ru)...")
        model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models', model='v5_ru', source='github', trust_repo=True)
        
        if os.path.exists(MODEL_PATH):
            print(f"Loading specific weights from local file: {{MODEL_PATH}}")
            checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
            if isinstance(checkpoint, dict):
                model.load_state_dict(checkpoint)
                print("Loaded state_dict from local file.")
            else:
                print("Local file format not directly compatible, using hub model.")
        
        model.to(DEVICE)
        model.eval()
        print("Silero Model loaded successfully on CPU.")
        return True
        
    except Exception as e:
        print(f"Error loading model: {{e}}")
        return False

if not load_model():
    print("Failed to load model. Exiting.")
    sys.exit(1)

@app.route('/tts', methods=['GET'])
def tts():
    text = request.args.get('text', '')
    speaker = request.args.get('speaker', 'aidar')
    sample_rate = request.args.get('sample_rate', '24000')
    sample_rate = int(sample_rate)
    
    if not text:
        return jsonify({{"error": "No text provided"}}), 400

    print(f"Generating audio for: {{text[:50]}}...")
    
    with torch.no_grad():
        try:
            audio = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)
        except Exception as e:
            return jsonify({{"error": str(e)}}), 500
            
    audio_np = audio.cpu().numpy().flatten()
    
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())
    
    buffer.seek(0)
    return send_file(buffer, mimetype="audio/wav", download_name="audio.wav")

@app.route('/')
def index():
    return "Silero TTS API (Russian v5.5) is running on Port 5002"

if __name__ == '__main__':
    print("Starting Silero TTS API on http://127.0.0.1:5002")
    app.run(host='127.0.0.1', port=5002, debug=False)
'''
    
    with open(server_script_path, 'w', encoding='utf-8') as f:
        f.write(server_code)
        
    print("Silero TTS installation complete.")
    return True

def main():
    print("============================================================")
    print("SillyTavern AiO - Python Installation Helper")
    print("============================================================")
    
    success = True
    
    if not install_sillytavern():
        success = False
        
    if not install_koboldcpp():
        success = False
        
    if not install_silero_tts():
        print("Warning: Silero setup had issues, but continuing...")

    print("\n============================================================")
    if success:
        print("Core components installed successfully!")
    else:
        print("Some components failed to install. Check errors above.")
    print("============================================================")

if __name__ == "__main__":
    main()
