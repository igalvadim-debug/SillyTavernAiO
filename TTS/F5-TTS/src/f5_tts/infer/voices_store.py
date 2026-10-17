"""Persistent storage for cloned voices (zero-shot reference clips).

A "voice" is just the pair (reference audio clip, exact transcript of that clip)
that F5-TTS needs to clone a timbre. This module keeps them on disk so both the
Gradio UI and the OpenAI-compatible API server can reuse them.

Layout (default repo root /voices):
    voices/
      voices.json          # index: {"default": <name>, "voices": {<name>: {...}}}
      <name>.wav           # the reference clip
"""

import json
import re
import shutil
from pathlib import Path

_PKG_FILE = Path(__file__).resolve()  # .../src/f5_tts/infer/voices_store.py
_REPO_ROOT = None
for _up in (_PKG_FILE.parents[3], _PKG_FILE.parents[2], _PKG_FILE.parents[1]):
    if (_up / "pyproject.toml").exists() or (_up / "src").is_dir():
        _REPO_ROOT = _up
        break
if _REPO_ROOT is None:
    _REPO_ROOT = _PKG_FILE.parents[3]

VOICES_DIR = _REPO_ROOT / "voices"
_INDEX_FILE = VOICES_DIR / "voices.json"


def _empty_index():
    return {"default": None, "voices": {}}


def _load():
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    if _INDEX_FILE.exists():
        try:
            data = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "voices" in data:
                return {"default": data.get("default"), "voices": data.get("voices", {})}
        except (json.JSONDecodeError, OSError):
            pass
    return _empty_index()


def _store(index):
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    _INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def list_voice_names():
    return sorted(_load()["voices"].keys())


def get_default_name():
    index = _load()
    names = sorted(index["voices"].keys())
    default = index.get("default")
    if default in names:
        return default
    return names[0] if names else None


def get_voice(name):
    if not name:
        return None
    index = _load()
    entry = index["voices"].get(name)
    if not entry:
        return None
    path = VOICES_DIR / entry["file"]
    if not path.exists():
        return None
    return {"name": name, "path": str(path), "ref_text": entry.get("ref_text", "")}


def _slugify(name):
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_.")
    return slug or "voice"


def save_voice(name, ref_audio_path, ref_text="", set_default=False):
    name = (name or "").strip()
    if not name:
        raise ValueError("Voice name is empty")
    if not ref_audio_path:
        raise ValueError("Reference audio is required")
    src = Path(ref_audio_path)
    if not src.exists():
        raise ValueError(f"Reference audio not found: {ref_audio_path}")

    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    ext = src.suffix or ".wav"
    filename = f"{_slugify(name)}{ext}"
    shutil.copyfile(src, VOICES_DIR / filename)

    index = _load()
    index["voices"][name] = {"file": filename, "ref_text": ref_text or ""}
    if set_default or not index.get("default") or index.get("default") not in index["voices"]:
        index["default"] = name
    _store(index)
    return get_voice(name)


def set_default(name):
    index = _load()
    if name not in index["voices"]:
        return False
    index["default"] = name
    _store(index)
    return True


def delete_voice(name):
    index = _load()
    entry = index["voices"].pop(name, None)
    if entry is None:
        return False
    path = VOICES_DIR / entry["file"]
    if path.exists():
        path.unlink()
    if index.get("default") == name:
        remaining = sorted(index["voices"].keys())
        index["default"] = remaining[0] if remaining else None
    _store(index)
    return True
