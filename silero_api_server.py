import os, sys
import re
import numpy as np
import torch
from flask import Flask, request, send_file, jsonify

MODEL_PATH  = r"D:\SillyTavernAiO\SileroTTS\models\v5_5_ru.pt"
SAMPLE_RATE = 24000
PORT        = 5002
OUT_WAV     = r"D:\SillyTavernAiO\SileroTTS\output.wav"
app         = Flask(__name__)

print("numpy:", np.__version__)
print("torch:", torch.__version__)

if not os.path.exists(MODEL_PATH):
    print("FEHLER: Modell nicht gefunden:", MODEL_PATH)
    sys.exit(1)

model = torch.package.PackageImporter(MODEL_PATH).load_pickle("tts_models", "model")
model.to('cpu')
print("Modell geladen (CPU). Sprecher:", model.speakers)


def synthesize(text, speaker="xenia"):
    # Скобки с содержимым убираем
    clean_text = re.sub(r'\(.*?\)', '', text)
    clean_text = re.sub(r'\[.*?\]', '', clean_text)
    # Убираем только мусор: эмодзи и нераспознаваемые символы
    clean_text = re.sub(r'[^\w\s.,!?;:\-—]', ' ', clean_text, flags=re.UNICODE)
    # Чистим лишние пробелы
    clean_text = re.sub(r' +', ' ', clean_text).strip()

    if not clean_text:
        print(f"Пропускаем TTS: '{text}'")
        return OUT_WAV

    if speaker not in model.speakers:
        speaker = model.speakers[0]

    print(f"[TTS] '{clean_text[:80]}' -> {speaker}")
    model.save_wav(text=clean_text, speaker=speaker,
                   sample_rate=SAMPLE_RATE, audio_path=OUT_WAV)
    return OUT_WAV


@app.route("/tts", methods=["GET", "POST"])
def tts():
    d       = (request.get_json(silent=True) or {}) if request.method == "POST" else {}
    text    = d.get("text", "") or request.args.get("text", "")
    speaker = d.get("speaker", "xenia") or request.args.get("speaker", "xenia")
    print(f"[RAW INPUT] {repr(text)}")
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
