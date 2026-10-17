"""OpenAI-compatible TTS HTTP server for F5-TTS (for SillyTavern et al.).

Implements the subset of the OpenAI Audio API that SillyTavern's
"OpenAI Compatible" TTS provider calls:

    POST /v1/audio/speech   {model, input, voice, response_format, speed, ...}
    GET  /v1/models
    GET  /v1/audio/voices   (extra: list of saved voice presets)
    GET  /health

Voices are read from the voices/ folder (see f5_tts.infer.voices_store) and
saved from the Gradio Web UI.

Run:
    python -m f5_tts.serve_openai --port 7868
"""

import argparse
import io
import re
import sys
import threading
from pathlib import Path

# Windows consoles may use a codepage that cannot encode Cyrillic (e.g. cp1252).
# utils_infer prints the reference text, which would then raise UnicodeEncodeError
# and turn every request into an HTTP 500. Make the console error-tolerant.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:  # noqa: BLE001
        pass
del _stream

import numpy as np
import soundfile as sf
from cached_path import cached_path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

import f5_tts.infer.utils_infer as utils_infer
from f5_tts.api import F5TTS
from f5_tts.infer import voices_store


def _patched_chunk_text(text, max_chars=135):
    """Chunking tuned for long Russian reference clips.

    The upstream formula derives max_chars from the reference audio; with 8-14 s refs
    it drops to ~20 *bytes* (~10 Cyrillic chars), which splits sentences mid-word and
    produces many audible cross-fade seams. We keep the same sentence-boundary logic
    but enforce a sane minimum of ~90 Cyrillic characters per chunk.
    """
    return utils_infer._orig_chunk_text(text, max_chars=max(max_chars, 170))


utils_infer._orig_chunk_text = utils_infer.chunk_text
utils_infer.chunk_text = _patched_chunk_text

DEFAULT_CKPT = "hf://Misha24-10/F5-TTS_RUSSIAN/F5TTS_v1_Base/model_240000_inference.safetensors"
DEFAULT_VOCAB = "hf://Misha24-10/F5-TTS_RUSSIAN/F5TTS_v1_Base/vocab.txt"

# Fine-tuned Russian checkpoint shipped *locally* with this repo (see TTS/F5-TTS/ckpts/README.md).
# serve_openai always resolves its model relative to the F5-TTS folder, independent of the
# Windows/Linux home directory or any HF cache - no path changes needed. If the file is not
# present yet, the server transparently falls back to the hf:// download above.
_LOCAL_CKPT = Path(__file__).resolve().parents[2] / "ckpts" / "F5TTS_v1_Base" / "model_240000_safetensors" / "F5TTS_v1_Base_model_240000.safetensors"
_LOCAL_VOCAB = Path(__file__).resolve().parents[2] / "ckpts" / "F5TTS_v1_Base" / "model_240000_safetensors" / "vocab.txt"

app = FastAPI(title="F5-TTS OpenAI-compatible API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_tts = None
_infer_lock = threading.Lock()
_default_nfe = 11
_length_scale = 1.06


# ---- text hygiene for chat clients (SillyTavern) ------------------------------
# SillyTavern sends markdown / roleplay noise (**bold**, *italics*, `code`, > quotes,
# [brackets], (actions), emojis...). F5-TTS reads such characters literally or gets
# confused by them. We clean the incoming text so speech sounds natural - without
# touching any paths or the model itself.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)
_MD_BOLD_RE = re.compile(r"(\*{2,3}|_{2,3})(.+?)\1", flags=re.DOTALL)
_MD_ITAL_RE = re.compile(r"(?<![\w])([*_])(?![*_\s])([^*_\n]+?)(?<=[^\s*_])\1(?![\w*])", flags=re.DOTALL)


def _clean_text(text):
    """Make chat/markdown text speakable (Russian-friendly)."""
    if not text:
        return ""
    # code blocks and inline code -> drop entirely (never meant to be spoken)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`\n]*)`", r"\1", text)
    # headers / blockquotes / horizontal rules
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>+\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*([-*_])\s*(\1\s*){2,}$", "", text, flags=re.MULTILINE)
    # links [label](url) -> label; bare urls get spelled badly -> drop
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    # bold first (**text**), then *roleplay emotes* (multi-word asterisk segments are
    # actions in SillyTavern style - they must not be spoken), then single-word italics.
    text = _MD_BOLD_RE.sub(r"\2", text)
    text = re.sub(r"(?<!\*)\*[^*\n]*?\s[^*\n]*?\*(?!\*)", " ", text)  # emotes with a space
    text = _MD_ITAL_RE.sub(r"\2", text)
    text = text.replace("~~", "")
    # any leftover stray asterisks / underscores used as emphasis markers
    text = re.sub(r"(?<!\d)[*_](?!\d)", "", text)
    # stage directions / system notes in brackets and parentheses are not speech
    text = re.sub(r"\[[^\]\n]*\]", "", text)
    text = re.sub(r"\(([^()\n]{0,120})\)", r" \1 ", text)
    # emojis and other symbol noise
    text = _EMOJI_RE.sub("", text)
    # collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", " ", text)
    text = text.replace("\n", " ").strip()
    # ensure it ends with sentence punctuation, otherwise the last phoneme gets cut
    if text and text[-1] not in ".!?…;:，。！？；：":
        text += "."
    return text


def _sanitize_segments(segments):
    """Post-process the upstream chunking result.

    Two problems with the default chunking when the reference clip is long (our local
    voices are 8-14 s of Russian speech):
      1. max_chars becomes tiny (~20 chars for a 12 s ref) -> dozens of micro-batches,
         each synthesized separately -> choppy delivery and audible cross-fade seams.
      2. chunks may end mid-word or without terminal punctuation -> clipped endings.
    We merge short neighbours up to ~90 chars and make sure every piece ends cleanly.
    """
    if not segments:
        return segments
    merged = []
    buf = ""
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        if buf and len(buf.encode("utf-8")) + len(seg.encode("utf-8")) <= 90 * 2:  # ~90 Cyrillic chars
            buf = f"{buf} {seg}".strip()
        else:
            if buf:
                merged.append(buf)
            buf = seg
    if buf:
        merged.append(buf)
    out = []
    for seg in merged:
        if seg[-1] not in ".!?…;:，。！？；：":
            # prefer ending at a comma/period boundary; otherwise append a period so
            # the model does not trail off mid-phoneme
            seg = seg.rstrip(",;: ") 
            if seg and seg[-1] not in ".!?…":
                seg += "."
        if seg:
            out.append(seg)
    return out or segments


class SpeechRequest(BaseModel):
    model: str = "f5-tts"
    input: str
    voice: str | None = None
    response_format: str = "mp3"
    speed: float = 1.0
    # F5-TTS extras (optional, ignored by OpenAI clients)
    nfe_step: int | None = None
    cfg_strength: float = 2.0
    sway_sampling_coef: float = -1.0
    seed: int | None = None
    remove_silence: bool = False
    length_scale: float | None = None


def _normalize_voice_name(name):
    """Strip client-side noise from a requested voice name.

    Some clients (notably SillyTavern with a hand-edited "Available voices" list)
    send the preset wrapped in whitespace and quotes, e.g. ``" 'David'"`` instead
    of ``"David"``. Without this, every such request misses voices.json and the
    server silently falls back to the default voice -> every character sounds the
    same, which is almost impossible to diagnose from the audio alone.
    """
    if not name:
        return name
    cleaned = name.strip()
    while len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in ("'", '"'):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _resolve_voice(name):
    if name:
        voice = voices_store.get_voice(name)
        if voice is None:
            cleaned = _normalize_voice_name(name)
            if cleaned != name:
                voice = voices_store.get_voice(cleaned)
            if voice is None and cleaned:
                # case-insensitive fallback ("david" -> "David")
                lowered = cleaned.casefold()
                for candidate in voices_store.list_voice_names():
                    if candidate.casefold() == lowered:
                        voice = voices_store.get_voice(candidate)
                        break
        if voice is not None:
            return voice
        # Requested voice is not in voices.json -> fall back to the default, but say
        # so loudly. A *silent* fallback makes every character sound identical, which
        # is almost impossible to diagnose from the audio alone.
        available = voices_store.list_voice_names()
        print(
            f"[serve_openai] WARNING: requested voice {name!r} not found in voices.json; "
            f"using default {voices_store.get_default_name()!r}. "
            f"Available voices: {', '.join(available) if available else '(none)'}",
            file=sys.stderr,
            flush=True,
        )
    voice = voices_store.get_voice(voices_store.get_default_name())
    if voice is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No voice preset available. Save a reference voice first in the Web UI "
                f"(start.bat -> 1), it is stored in: {voices_store.VOICES_DIR}"
            ),
        )
    return voice


def _trim_edges(wav, sr, max_head=0.25, max_tail=0.45, thresh_db=-45.0):
    """Trim leading/trailing silence of the *generated* audio (in-memory).

    duration_scale > 1 deliberately adds tail room; without a trim that becomes
    dead air before SillyTavern plays the next line. We keep at most max_head /
    max_tail seconds of edge silence so breaths/intro reverb survive but long gaps
    disappear. Pure signal processing - no paths, no model changes.
    """
    arr = np.asarray(wav, dtype=np.float32).reshape(-1)
    if arr.size == 0:
        return arr
    frame = max(1, int(sr * 0.01))  # 10 ms granularity
    n_frames = max(1, arr.size // frame)
    rms = np.sqrt((arr[: n_frames * frame].reshape(n_frames, frame) ** 2).mean(axis=1))
    thr = (10.0 ** (thresh_db / 20.0)) * float(np.abs(arr).max()) + 1e-9
    voiced = np.nonzero(rms > thr)[0]
    if voiced.size == 0:
        return arr
    head_keep = int(max_head * sr)
    tail_keep = int(max_tail * sr)
    start = max(0, int(voiced[0] * frame) - head_keep)
    end = min(arr.size, int((voiced[-1] + 1) * frame) + tail_keep)
    return arr[start:end]


def _encode(wav, sr, fmt):
    fmt = (fmt or "wav").lower()
    arr = np.asarray(wav, dtype=np.float32).reshape(-1)
    if fmt in ("wav", "pcm"):
        buf = io.BytesIO()
        sf.write(buf, arr, sr, format="WAV")
        return buf.getvalue(), "audio/wav"
    if fmt in ("mp3", "opus", "aac", "flac", "ogg"):
        try:
            from pydub import AudioSegment

            pcm = (np.clip(arr, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
            seg = AudioSegment(pcm, frame_rate=sr, sample_width=2, channels=1)
            buf = io.BytesIO()
            seg.export(buf, format=fmt)
            mime = "audio/mpeg" if fmt == "mp3" else f"audio/{fmt}"
            return buf.getvalue(), mime
        except Exception as e:  # ffmpeg missing / export failed -> fall back to wav
            print(f"[serve_openai] {fmt} encode failed ({e}); returning wav", file=sys.stderr)
    buf = io.BytesIO()
    sf.write(buf, arr, sr, format="WAV")
    return buf.getvalue(), "audio/wav"


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _tts is not None}


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": "f5-tts", "object": "model", "owned_by": "f5-tts"}]}


@app.get("/v1/audio/voices")
def list_voices():
    return {
        "voices": voices_store.list_voice_names(),
        "default": voices_store.get_default_name(),
        "dir": str(voices_store.VOICES_DIR),
    }


@app.post("/v1/audio/speech")
def speech(req: SpeechRequest, request: Request):
    if _tts is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    text = _clean_text(req.input)
    if not text:
        raise HTTPException(status_code=400, detail="`input` is empty")
    client = request.client.host if request.client else "?"
    print(
        f"[serve_openai] REQ from {client}: voice={req.voice!r} "
        f"format={req.response_format!r} nfe={req.nfe_step or _default_nfe} chars={len(text)}",
        file=sys.stderr,
        flush=True,
    )
    voice = _resolve_voice(req.voice)
    # The F5-TTS model is NOT thread-safe, but FastAPI runs this sync endpoint in a
    # thread pool. Without a lock, two overlapping requests (SillyTavern often sends
    # several lines back-to-back) run inference on the same model at once and corrupt
    # each other -> hiss / crackle / roar over the speech. Serialize them here.
    if not _infer_lock.acquire(blocking=False):
        print(f"[serve_openai] {client}: GPU busy, queued behind another request", file=sys.stderr, flush=True)
        _infer_lock.acquire()
    nfe = req.nfe_step or _default_nfe
    try:
        wav, sr, _spec = _tts.infer(
            ref_file=voice["path"],
            ref_text=voice["ref_text"],
            gen_text=text,
            show_info=lambda *a, **k: None,
            progress=None,
            nfe_step=nfe,
            cfg_strength=req.cfg_strength,
            sway_sampling_coef=req.sway_sampling_coef,
            speed=req.speed,
            remove_silence=req.remove_silence,
            seed=req.seed,
            duration_scale=req.length_scale if req.length_scale is not None else _length_scale,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"synthesis failed: {e}") from e
    finally:
        _infer_lock.release()
    wav = _trim_edges(wav, sr)
    data, mime = _encode(wav, sr, req.response_format)
    print(
        f"[serve_openai] -> {client}: resolved_voice={voice['name']!r} bytes={len(data)} "
        f"mime={mime} dur={len(wav) / sr:.2f}s nfe={nfe}",
        file=sys.stderr,
        flush=True,
    )
    return Response(content=data, media_type=mime)


def _warmup():
    """Run one short synthesis so the first real request is not slow.

    Fills the reference-audio cache in utils_infer and lets CUDA allocate its
    kernels/buffers up front. Uses the default voice; skipped silently if none
    is available.
    """
    if _tts is None:
        return
    try:
        voice = _resolve_voice(None)
    except HTTPException:
        voice = None
    if voice is None:
        print("[serve_openai] Warmup skipped (no voice preset available).")
        return
    print("Warming up (first inference)...")
    try:
        _tts.infer(
            ref_file=voice["path"],
            ref_text=voice["ref_text"],
            gen_text="Проверка.",
            show_info=lambda *a, **k: None,
            progress=None,
            nfe_step=_default_nfe,
            cfg_strength=2.0,
            sway_sampling_coef=-1.0,
            speed=1.0,
            remove_silence=False,
            seed=0,
            duration_scale=_length_scale,
        )
        print("Warmup done.")
    except Exception as e:  # noqa: BLE001
        print(f"[serve_openai] Warmup failed ({e}); continuing.", file=sys.stderr)


def main():
    global _tts, _default_nfe, _length_scale
    parser = argparse.ArgumentParser(description="OpenAI-compatible F5-TTS server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7868)
    parser.add_argument("--ckpt", default=DEFAULT_CKPT, help="model checkpoint path or hf:// URL")
    parser.add_argument("--vocab", default=DEFAULT_VOCAB, help="vocab.txt path or hf:// URL")
    parser.add_argument("--model", default="F5TTS_v1_Base", help="config name (configs/<model>.yaml)")
    parser.add_argument("--nfe-step", type=int, default=11)
    parser.add_argument(
        "--length-pad",
        type=float,
        default=1.06,
        help="scale the estimated generation length; >1 adds tail room so the "
        "last phoneme is not cut off (1.0 = old behaviour)",
    )
    parser.add_argument("--device", default=None)
    parser.add_argument(
        "--no-warmup",
        action="store_true",
        help="skip the short warmup inference at startup",
    )
    args = parser.parse_args()

    _default_nfe = args.nfe_step
    _length_scale = args.length_pad

    # Locale first: if the fine-tuned Russian checkpoint is stored locally in the
    # F5-TTS folder (ckpts/...), use it and never depend on the HF cache / home dir.
    # Otherwise fall back to the hf:// URL (cached_path downloads it once).
    ckpt_arg, vocab_arg = args.ckpt, args.vocab
    if _LOCAL_CKPT.exists():
        if args.ckpt == DEFAULT_CKPT:
            ckpt_arg = str(_LOCAL_CKPT)
            print(f"Using local checkpoint: {ckpt_arg}")
        if args.vocab == DEFAULT_VOCAB and _LOCAL_VOCAB.exists():
            vocab_arg = str(_LOCAL_VOCAB)
    else:
        print(
            f"[serve_openai] note: local checkpoint not found ({_LOCAL_CKPT}); "
            "downloading/loading from Huggingface instead."
        )

    print("Loading F5-TTS model (this may take a moment)...")
    _tts = F5TTS(
        model=args.model,
        ckpt_file=str(cached_path(ckpt_arg)),
        vocab_file=str(cached_path(vocab_arg)),
        device=args.device,
    )

    if not args.no_warmup:
        _warmup()

    print(f"Voices dir : {voices_store.VOICES_DIR}")
    print(f"Voices     : {voices_store.list_voice_names() or '(none yet)'}")
    print(f"Endpoint   : http://{"127.0.0.1" if args.host == "0.0.0.0" else args.host}:{args.port}/v1/audio/speech  (OpenAI-compatible)")

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
