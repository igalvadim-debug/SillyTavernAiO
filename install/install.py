import os, sys, subprocess, urllib.request, json

BASE          = r"D:\SillyTavernAiO"
SILERO_DIR    = os.path.join(BASE, "SileroTTS")
MODELS_DIR    = os.path.join(SILERO_DIR, "models")
ST_DIR        = os.path.join(BASE, "SillyTavern")
KOBOLD_DIR    = os.path.join(BASE, "KoboldCPP")
KOBOLD_MODELS = os.path.join(KOBOLD_DIR, "models")
RU_MODEL      = os.path.join(MODELS_DIR, "v5_5_ru.pt")

def run(cmd, cwd=None):
    print(f'>> {" ".join(cmd)}')
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        print(f"FEHLER: {cmd}")
        sys.exit(1)

def run_shell(cmd, cwd=None):
    print(f">> {cmd}")
    r = subprocess.run(cmd, cwd=cwd, shell=True)
    if r.returncode != 0:
        print(f"FEHLER: {cmd}")
        sys.exit(1)

def verify(module):
    r = subprocess.run([sys.executable, "-c",
                        f"import {module}; print('{module}:', {module}.__version__)"],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(f"FEHLER: {module} nicht importierbar!")
        print(r.stderr)
        sys.exit(1)

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}\n")

# ── Schritt 0: pip aktualisieren ──────────────────────────────
print("=== [0] pip aktualisieren ===")
run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

# ── [1/3] Silero TTS ──────────────────────────────────────────
print("\n=== [1/3] Silero TTS ===")
os.makedirs(MODELS_DIR, exist_ok=True)

# numpy 1.26.4 - NICHT 2.x!
# torch 2.4.0 ist mit numpy 2.x nicht kompatibel -> RuntimeError: Numpy is not available
print("Installiere numpy==1.26.4...")
run([sys.executable, "-m", "pip", "install", "numpy==1.26.4"])
verify("numpy")

print("Installiere flask...")
run([sys.executable, "-m", "pip", "install", "flask"])
verify("flask")

# torch 2.4.0 + torchaudio 2.4.0 (cu124 = kein torchcodec, kein FFmpeg-Problem)
print("Installiere torch==2.4.0 + torchaudio==2.4.0...")
run([sys.executable, "-m", "pip", "install",
     "torch==2.4.0", "torchaudio==2.4.0",
     "--index-url", "https://download.pytorch.org/whl/cu124"])
verify("torch")
verify("torchaudio")

# numpy nochmal pruefen - torch darf es nicht ueberschreiben!
print("\nnumpy nach torch-Installation pruefen...")
verify("numpy")

# Modell herunterladen
if not os.path.exists(RU_MODEL):
    print("Lade v5_5_ru.pt herunter...")
    urllib.request.urlretrieve(
        "https://models.silero.ai/models/tts/ru/v5_5_ru.pt", RU_MODEL)
    print("Modell heruntergeladen.")
else:
    print("v5_5_ru.pt bereits vorhanden, ueberspringe.")

# silero_api_server.py generieren
server_code = '''import os, sys
import numpy as np
import torch
from flask import Flask, request, send_file, jsonify

MODEL_PATH  = r"D:\\SillyTavernAiO\\SileroTTS\\models\\v5_5_ru.pt"
SAMPLE_RATE = 24000
PORT        = 5002
OUT_WAV     = r"D:\\SillyTavernAiO\\SileroTTS\\output.wav"
app         = Flask(__name__)

print("numpy:", np.__version__)
print("torch:", torch.__version__)

if not os.path.exists(MODEL_PATH):
    print("FEHLER: Modell nicht gefunden:", MODEL_PATH)
    sys.exit(1)

model = torch.package.PackageImporter(MODEL_PATH).load_pickle("tts_models", "model")
print("Modell geladen. Sprecher:", model.speakers)


def synthesize(text, speaker="xenia"):
    if speaker not in model.speakers:
        speaker = model.speakers[0]
    model.save_wav(text=text, speaker=speaker,
                   sample_rate=SAMPLE_RATE, audio_path=OUT_WAV)
    return OUT_WAV


@app.route("/tts", methods=["GET", "POST"])
def tts():
    d       = (request.get_json(silent=True) or {}) if request.method == "POST" else {}
    text    = d.get("text", "") or request.args.get("text", "")
    speaker = d.get("speaker", "xenia") or request.args.get("speaker", "xenia")
    if not text:
        return jsonify({"error": "No text"}), 400
    try:
        return send_file(synthesize(text, speaker), mimetype="audio/wav", as_attachment=False)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/v1/audio/speech", methods=["POST"])
def openai_tts():
    d       = request.get_json(silent=True) or {}
    text    = d.get("input", "")
    vm      = {"alloy": "xenia", "echo": "aidar", "fable": "baya",
               "onyx": "kseniya", "nova": "xenia", "shimmer": "eugene"}
    speaker = vm.get(d.get("voice", "").lower(), "xenia")
    print(f"[/v1/audio/speech] {text[:60]!r} -> {speaker}")
    if not text:
        return jsonify({"error": "No input"}), 400
    try:
        return send_file(synthesize(text, speaker), mimetype="audio/wav", as_attachment=False)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/v1/voices", methods=["GET"])
@app.route("/voices",    methods=["GET"])
def voices():
    return jsonify({"voices": model.speakers})


@app.route("/",    methods=["GET"])
@app.route("/v1/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "speakers": model.speakers})


if __name__ == "__main__":
    print(f"Silero TTS laeuft auf http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
'''

srv = os.path.join(SILERO_DIR, "silero_api_server.py")
with open(srv, "w", encoding="utf-8") as f:
    f.write(server_code)
print(f"silero_api_server.py erstellt: {srv}")

# ── [2/3] SillyTavern ─────────────────────────────────────────
print("\n=== [2/3] SillyTavern ===")
if not os.path.exists(os.path.join(ST_DIR, ".git")):
    run_shell(f'git clone "https://github.com/SillyTavern/SillyTavern.git" "{ST_DIR}"')
else:
    print("SillyTavern bereits geklont, ueberspringe.")
run_shell("npm install", cwd=ST_DIR)

# ── [3/3] KoboldCPP ───────────────────────────────────────────
print("\n=== [3/3] KoboldCPP ===")
os.makedirs(KOBOLD_DIR, exist_ok=True)
os.makedirs(KOBOLD_MODELS, exist_ok=True)
kobold_exe = os.path.join(KOBOLD_DIR, "koboldcpp.exe")
if not os.path.exists(kobold_exe):
    print("Ermittle neueste KoboldCPP Version...")
    with urllib.request.urlopen(
            "https://api.github.com/repos/LostRuins/koboldcpp/releases/latest") as r:
        release = json.loads(r.read())
    url = next((a["browser_download_url"] for a in release["assets"]
                if a["name"].lower() == "koboldcpp.exe"), None)
    if not url:
        print("FEHLER: koboldcpp.exe nicht im Release."); sys.exit(1)
    print(f"Lade herunter: {url}")
    urllib.request.urlretrieve(url, kobold_exe)
    print("koboldcpp.exe heruntergeladen.")
else:
    print("koboldcpp.exe vorhanden, ueberspringe.")

print("\n=== Installation erfolgreich abgeschlossen! ===")
print("Starte jetzt: start_all.bat")
