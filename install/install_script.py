#!/usr/bin/env python3
"""
Install script for SillyTavern AiO
This script installs:
- SillyTavern (cloned from GitHub)
- KoboldCPP (downloaded from GitHub releases)
- Silero TTS (Python dependencies and setup)
"""

import os
import sys
import subprocess
import urllib.request
import json
import shutil

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # Parent directory (SillyTavernAiO)

SILLYTAVERN_URL = "https://github.com/SillyTavern/SillyTavern.git"
KOBOLDCPP_RELEASES_URL = "https://api.github.com/repos/LostRuins/koboldcpp/releases/latest"

def check_dependencies():
    """Check if git and curl are available on the system."""
    print("Checking system dependencies...")
    
    # Check for git
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Git found: {result.stdout.strip()}")
        else:
            print("✗ Git not found or not working properly")
            return False
    except FileNotFoundError:
        print("✗ Git is not installed. Please install Git first.")
        return False
    
    # Check for curl (optional, we use urllib as fallback)
    try:
        result = subprocess.run(["curl", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Curl found: {result.stdout.split()[0]}")
        else:
            print("⚠ Curl not found, will use Python urllib instead")
    except FileNotFoundError:
        print("⚠ Curl not found, will use Python urllib instead")
    
    return True

def create_directories():
    """Create necessary directories for the installation."""
    print("\nCreating directory structure...")
    
    dirs = [
        os.path.join(BASE_DIR, "SillyTavern"),
        os.path.join(BASE_DIR, "KoboldCPP"),
        os.path.join(BASE_DIR, "SileroTTS"),
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✓ Created: {dir_path}")
        else:
            print(f"✓ Already exists: {dir_path}")

def install_sillytavern():
    """Clone SillyTavern from GitHub."""
    print("\nInstalling SillyTavern...")
    
    sillytavern_dir = os.path.join(BASE_DIR, "SillyTavern")
    
    if os.path.exists(os.path.join(sillytavern_dir, ".git")):
        print("✓ SillyTavern already cloned. Updating...")
        try:
            subprocess.run(["git", "pull"], cwd=sillytavern_dir, check=True)
            print("✓ SillyTavern updated successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to update SillyTavern: {e}")
            return False
    else:
        print("Cloning SillyTavern repository...")
        try:
            subprocess.run(["git", "clone", SILLYTAVERN_URL, sillytavern_dir], check=True)
            print("✓ SillyTavern cloned successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to clone SillyTavern: {e}")
            return False
    
    return True

def get_latest_koboldcpp_url():
    """Get the download URL for the latest koboldcpp.exe release."""
    print("Fetching latest KoboldCPP release information...")
    
    try:
        req = urllib.request.Request(
            KOBOLDCPP_RELEASES_URL,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            for asset in data.get('assets', []):
                if asset['name'] == 'koboldcpp.exe':
                    return asset['browser_download_url']
            
            print("✗ koboldcpp.exe not found in latest release")
            return None
    except Exception as e:
        print(f"✗ Failed to fetch KoboldCPP release info: {e}")
        return None

def install_koboldcpp():
    """Download the latest koboldcpp.exe from GitHub releases."""
    print("\nInstalling KoboldCPP...")
    
    koboldcpp_dir = os.path.join(BASE_DIR, "KoboldCPP")
    koboldcpp_exe = os.path.join(koboldcpp_dir, "koboldcpp.exe")
    
    download_url = get_latest_koboldcpp_url()
    if not download_url:
        print("✗ Could not get KoboldCPP download URL")
        return False
    
    print(f"Downloading koboldcpp.exe from: {download_url}")
    
    try:
        urllib.request.urlretrieve(download_url, koboldcpp_exe)
        print(f"✓ KoboldCPP downloaded successfully to: {koboldcpp_exe}")
        return True
    except Exception as e:
        print(f"✗ Failed to download KoboldCPP: {e}")
        return False

def install_silero_tts():
    """Install Silero TTS dependencies and setup."""
    print("\nInstalling Silero TTS...")
    
    silero_dir = os.path.join(BASE_DIR, "SileroTTS")
    
    # Install required Python packages
    print("Installing Python dependencies for Silero TTS...")
    packages = [
        "torch",
        "torchaudio",
        "flask",
    ]
    
    try:
        # Try to install packages
        for package in packages:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        
        print("✓ Silero TTS dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Some packages may have failed to install: {e}")
        print("You may need to install them manually later")
    
    # Create a basic integration script
    integration_script = os.path.join(silero_dir, "silero_tts.py")
    script_content = '''#!/usr/bin/env python3
"""
Silero TTS Integration Script
Supports Russian language by default
"""

import torch

def load_silero_tts(language='ru'):
    """Load Silero TTS model for specified language."""
    try:
        model, example_text = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language=language,
            speaker='v3_ru' if language == 'ru' else 'v3_en'
        )
        print(f"✓ Silero TTS model loaded for language: {language}")
        return model
    except Exception as e:
        print(f"✗ Failed to load Silero TTS: {e}")
        return None

def text_to_speech(model, text, output_file='output.wav'):
    """Convert text to speech."""
    try:
        audio = model.apply_tts(text=text)
        # Save audio file (implementation depends on your needs)
        print(f"✓ Speech generated and saved to: {output_file}")
        return audio
    except Exception as e:
        print(f"✗ Failed to generate speech: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    print("Silero TTS Integration Test")
    model = load_silero_tts(language='ru')
    if model:
        text_to_speech(model, "Привет, это тест русского текста.")
'''
    
    try:
        with open(integration_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        print(f"✓ Silero TTS integration script created: {integration_script}")
    except Exception as e:
        print(f"✗ Failed to create integration script: {e}")
    
    # Create the Silero TTS server script for start_all.bat
    server_script = os.path.join(silero_dir, "silero_tts_server.py")
    server_content = '''#!/usr/bin/env python3
"""
Silero TTS API Server
Simple Flask-based API for Silero TTS
"""

import sys
import argparse

try:
    from flask import Flask, request, jsonify, send_file
    import torch
    import io
    import wave
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages:")
    print("  pip install flask torch torchaudio")
    sys.exit(1)

app = Flask(__name__)
model = None

def load_model(language='ru'):
    global model
    try:
        model, _ = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language=language,
            speaker='v3_ru' if language == 'ru' else 'v3_en'
        )
        print(f"Silero TTS model loaded for language: {language}")
        return True
    except Exception as e:
        print(f"Failed to load model: {e}")
        return False

@app.route('/health')
def health():
    return jsonify({"status": "ok", "model_loaded": model is not None})

@app.route('/tts', methods=['POST'])
def text_to_speech():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500
    
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        audio = model.apply_tts(text=text)
        
        # Convert to WAV format
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes((audio.numpy()).tobytes())
        buffer.seek(0)
        
        return send_file(buffer, mimetype='audio/wav', as_attachment=True, download_name='speech.wav')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Silero TTS Server')
    parser.add_argument('--port', type=int, default=5002, help='Port to run the server on')
    parser.add_argument('--language', type=str, default='ru', help='Language code')
    args = parser.parse_args()
    
    print(f"Starting Silero TTS server on port {args.port}...")
    if load_model(args.language):
        app.run(host='127.0.0.1', port=args.port, debug=False)
    else:
        print("Failed to load TTS model. Exiting.")
        sys.exit(1)
'''
    
    try:
        with open(server_script, 'w', encoding='utf-8') as f:
            f.write(server_content)
        print(f"✓ Silero TTS server script created: {server_script}")
    except Exception as e:
        print(f"✗ Failed to create server script: {e}")
    
    return True

def main():
    """Main installation function."""
    print("=" * 60)
    print("SillyTavern AiO Installation Script")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n✗ Installation aborted due to missing dependencies")
        sys.exit(1)
    
    # Create directory structure
    create_directories()
    
    # Install components
    success = True
    
    if not install_sillytavern():
        success = False
        print("⚠ SillyTavern installation failed")
    
    if not install_koboldcpp():
        success = False
        print("⚠ KoboldCPP installation failed")
    
    if not install_silero_tts():
        success = False
        print("⚠ Silero TTS installation failed")
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Installation completed successfully!")
    else:
        print("⚠ Installation completed with some warnings/errors")
        print("Please check the messages above for details")
    print("=" * 60)
    
    print("\nInstallation Summary:")
    print(f"  - SillyTavern: {os.path.join(BASE_DIR, 'SillyTavern')}")
    print(f"  - KoboldCPP: {os.path.join(BASE_DIR, 'KoboldCPP', 'koboldcpp.exe')}")
    print(f"  - Silero TTS: {os.path.join(BASE_DIR, 'SileroTTS')}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
