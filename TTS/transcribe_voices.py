import glob
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

import numpy as np
import soundfile as sf
import torch
from transformers import pipeline

VOICES_DIR = r"D:\SillyTavernAiO\TTS\F5-TTS\voices"
MODEL = "openai/whisper-large-v3-turbo"
OUT = os.path.join(VOICES_DIR, "_transcripts.json")
LANG = "ru"

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

print(f"Loading ASR model {MODEL} on {device} ({dtype}) ...", flush=True)
pipe = pipeline(
    "automatic-speech-recognition",
    model=MODEL,
    torch_dtype=dtype,
    device=device,
)
print("Model ready.", flush=True)

results = {}
for path in sorted(glob.glob(os.path.join(VOICES_DIR, "*.wav"))):
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        audio, sr = sf.read(path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        out = pipe(
            {"array": audio, "sampling_rate": sr},
            chunk_length_s=30,
            batch_size=8,
            generate_kwargs={"task": "transcribe", "language": LANG},
            return_timestamps=False,
        )
        text = out["text"].strip()
        results[name] = text
        print(f"{name}: {text}", flush=True)
    except Exception as e:  # noqa: BLE001
        results[name] = None
        print(f"{name}: ERROR {e}", flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("DONE -> " + OUT, flush=True)
