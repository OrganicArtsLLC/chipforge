"""
ChipForge Export
=================
WAV file export and JSON song save/load.

WAV output is 16-bit signed PCM stereo — no external libraries required,
uses the stdlib `wave` module exclusively.
"""

from __future__ import annotations

import io
import json
import wave
from pathlib import Path

import numpy as np

from .sequencer import Song
from .synth import SAMPLE_RATE


# ---------------------------------------------------------------------------
# WAV Export
# ---------------------------------------------------------------------------

def _float32_to_pcm16(audio: np.ndarray) -> bytes:
    """Convert float32 audio array to 16-bit PCM bytes."""
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    return pcm.tobytes()


def audio_to_wav_bytes(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> bytes:
    """
    Render a float32 audio buffer to raw WAV bytes (in-memory, no file written).

    Useful for the API render endpoint which streams WAV data without
    creating a temporary file.

    Args:
        audio: Float32 array, shape (num_samples, 2) for stereo or (num_samples,) for mono.
        sample_rate: Sample rate in Hz.

    Returns:
        Raw WAV file bytes.
    """
    buf = io.BytesIO()
    num_channels = 2 if (audio.ndim == 2 and audio.shape[1] == 2) else 1
    pcm_bytes = _float32_to_pcm16(audio)

    with wave.open(buf, "w") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(2)       # 16-bit = 2 bytes per sample
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)

    return buf.getvalue()


def export_wav(
    audio: np.ndarray,
    filepath: str | Path,
    sample_rate: int = SAMPLE_RATE,
) -> Path:
    """
    Export a float32 audio buffer to a 16-bit stereo WAV file.

    Creates parent directories if they do not exist.

    Args:
        audio: Float32 array, shape (num_samples, 2).
        filepath: Output file path.
        sample_rate: Sample rate in Hz.

    Returns:
        Resolved Path of the written file.
    """
    filepath = Path(filepath).resolve()
    filepath.parent.mkdir(parents=True, exist_ok=True)

    wav_bytes = audio_to_wav_bytes(audio, sample_rate)
    filepath.write_bytes(wav_bytes)
    return filepath


# ---------------------------------------------------------------------------
# Song JSON Persistence
# ---------------------------------------------------------------------------

def save_song(song: Song, filepath: str | Path) -> Path:
    """
    Save a Song to a human-readable JSON file.

    Creates parent directories if they do not exist.

    Args:
        song: Song instance to serialize.
        filepath: Output file path.

    Returns:
        Resolved Path of the written file.
    """
    filepath = Path(filepath).resolve()
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(song.to_dict(), fh, indent=2)
    return filepath


def load_song(filepath: str | Path) -> Song:
    """
    Load a Song from a JSON file.

    Args:
        filepath: Path to a .chipforge.json or .json file.

    Returns:
        Deserialized Song instance.
    """
    with open(filepath, encoding="utf-8") as fh:
        data = json.load(fh)
    return Song.from_dict(data)


def song_to_dict(song: Song) -> dict:
    """
    Serialize a Song to a plain Python dict (JSON-serializable).

    Convenience wrapper around Song.to_dict() for use in the API layer.
    """
    return song.to_dict()


def dict_to_song(data: dict) -> Song:
    """
    Deserialize a Song from a plain Python dict.

    Convenience wrapper around Song.from_dict() for use in the API layer.
    """
    return Song.from_dict(data)
