#!/usr/bin/env python3
"""
ChipForge Dynamics Curve Tests
===============================
Verify that Song.dynamics_curve produces an audible crescendo and that
diminuendo correctly reduces note amplitude over time.

Run:
    .venv/bin/python3 tests/test_dynamics_curve.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.synth import ADSR
from src.instruments import Instrument
from src.sequencer import Pattern, NoteEvent, Song
from src.mixer import render_song


PASS = 0
FAIL = 0
ERRORS: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"{name}: {detail}" if detail else name
        ERRORS.append(msg)
        print(f"  FAIL  {msg}")


sine = Instrument(
    name="sine",
    waveform="sine",
    adsr=ADSR(attack=0.005, decay=0.02, sustain=0.9, release=0.04),
    volume=0.7,
)
INSTS = {"sine": sine, "pulse_lead": sine}


def make_song_with_curve(curve: list[tuple[float, float]]) -> Song:
    """Build a 32-step song with a note every 4 steps, all the same velocity."""
    song = Song(title="dyn", bpm=120)
    pat = Pattern(num_steps=32, num_channels=1, bpm=120, steps_per_beat=4)
    for step in range(0, 32, 4):
        pat.set_note(0, step, NoteEvent(midi_note=69, velocity=0.7,
                                          duration_steps=4, instrument="sine"))
    song.patterns = [pat]
    song.sequence = [0]
    song.dynamics_curve = curve
    return song


# ---------------------------------------------------------------------------
# 1. Curve interpolation math
# ---------------------------------------------------------------------------
print("\nDynamics curve interpolation:")
song = Song(bpm=120)
song.dynamics_curve = [(0.0, -12.0), (8.0, 0.0), (16.0, -6.0)]

check("at beat 0 → -12 dB", abs(song.gain_db_at_beat(0.0) - (-12.0)) < 0.01)
check("at beat 8 → 0 dB", abs(song.gain_db_at_beat(8.0) - 0.0) < 0.01)
check("at beat 4 → -6 dB (linear midpoint)",
      abs(song.gain_db_at_beat(4.0) - (-6.0)) < 0.01,
      f"got {song.gain_db_at_beat(4.0)}")
check("before first keyframe → first value",
      abs(song.gain_db_at_beat(-3.0) - (-12.0)) < 0.01)
check("after last keyframe → last value",
      abs(song.gain_db_at_beat(99.0) - (-6.0)) < 0.01)
check("no curve → 0 dB",
      abs(Song(bpm=120).gain_db_at_beat(5.0)) < 0.001)
check("gain_lin_at_beat: 0 dB = unity",
      abs(Song(bpm=120).gain_lin_at_beat(0.0) - 1.0) < 0.001)
check("gain_lin_at_beat: -6 dB ≈ 0.501",
      abs(song.gain_lin_at_beat(4.0) - (10 ** (-6.0 / 20.0))) < 0.001)


# ---------------------------------------------------------------------------
# 2. Crescendo: end is louder than start
# ---------------------------------------------------------------------------
print("\nCrescendo (-18 dB → 0 dB):")
crescendo_song = make_song_with_curve([(0.0, -18.0), (8.0, 0.0)])
flat_song = make_song_with_curve([])

audio_cresc = render_song(crescendo_song, instruments=INSTS, normalize=False)
audio_flat = render_song(flat_song, instruments=INSTS, normalize=False)

check("crescendo render is finite", np.all(np.isfinite(audio_cresc)))

# RMS of first vs last quarter — crescendo should clearly increase
def rms_quarter(audio: np.ndarray, q: int) -> float:
    n = len(audio)
    s = (q * n) // 4
    e = ((q + 1) * n) // 4
    mono = audio[s:e].mean(axis=1) if audio.ndim == 2 else audio[s:e]
    return float(np.sqrt(np.mean(mono ** 2)))

cresc_q1 = rms_quarter(audio_cresc, 0)
cresc_q4 = rms_quarter(audio_cresc, 3)
flat_q1 = rms_quarter(audio_flat, 0)
flat_q4 = rms_quarter(audio_flat, 3)

check("crescendo Q4 RMS > Q1 RMS by at least 3x",
      cresc_q4 > cresc_q1 * 3.0,
      f"Q1 = {cresc_q1:.5f}, Q4 = {cresc_q4:.5f}")
check("flat song Q1 ≈ Q4 (within 30%)",
      abs(flat_q1 - flat_q4) < flat_q1 * 0.30,
      f"Q1 = {flat_q1:.5f}, Q4 = {flat_q4:.5f}")


# ---------------------------------------------------------------------------
# 3. Diminuendo: end is quieter than start
# ---------------------------------------------------------------------------
print("\nDiminuendo (0 dB → -18 dB):")
dim_song = make_song_with_curve([(0.0, 0.0), (8.0, -18.0)])
audio_dim = render_song(dim_song, instruments=INSTS, normalize=False)

dim_q1 = rms_quarter(audio_dim, 0)
dim_q4 = rms_quarter(audio_dim, 3)
check("diminuendo Q1 RMS > Q4 RMS by at least 3x",
      dim_q1 > dim_q4 * 3.0,
      f"Q1 = {dim_q1:.5f}, Q4 = {dim_q4:.5f}")


# ---------------------------------------------------------------------------
# 4. Curve doesn't change song length, only amplitude shape
# ---------------------------------------------------------------------------
print("\nCurve preserves song duration:")
check("crescendo duration matches flat duration",
      len(audio_cresc) == len(audio_flat),
      f"cresc = {len(audio_cresc)}, flat = {len(audio_flat)}")


# ---------------------------------------------------------------------------
# 5. Round-trip serialization preserves dynamics_curve
# ---------------------------------------------------------------------------
print("\nDynamics curve serialization round-trip:")
src = Song(bpm=120)
src.dynamics_curve = [(0.0, -12.0), (4.0, 0.0), (8.0, -6.0)]
restored = Song.from_dict(src.to_dict())
check("dynamics_curve preserved through to_dict/from_dict",
      restored.dynamics_curve == [(0.0, -12.0), (4.0, 0.0), (8.0, -6.0)])


# ---------------------------------------------------------------------------
# 6. Backwards compat — empty curve is a no-op
# ---------------------------------------------------------------------------
print("\nNo curve = no behaviour change:")
plain = make_song_with_curve([])
plain_audio = render_song(plain, instruments=INSTS, normalize=False)
check("plain render is finite", np.all(np.isfinite(plain_audio)))
check("plain audio is non-empty", len(plain_audio) > 0)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
print(f"  PASSED: {PASS}    FAILED: {FAIL}")
print(f"{'=' * 60}")
if FAIL:
    print("\nFailures:")
    for e in ERRORS:
        print(f"  - {e}")
    sys.exit(1)
print("All dynamics curve tests passed.")
sys.exit(0)
