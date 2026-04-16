#!/usr/bin/env python3
"""
ChipForge Orchestral Preset Tests
==================================
Smoke-test every new orchestral preset (piano, harpsichord, organ, strings,
winds, brass) and verify each one renders clean, finite, non-clipping audio
through render_pattern.

Run:
    .venv/bin/python3 tests/test_orchestral_presets.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.instruments import PRESETS
from src.sequencer import Pattern, NoteEvent
from src.mixer import render_pattern


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


ORCHESTRAL_PRESETS = [
    "piano_grand", "piano_upright", "piano_concert",
    "harpsichord", "pipe_organ",
    "violin", "viola", "cello", "cello_pizz", "contrabass",
    "strings_ensemble",
    "flute", "oboe", "clarinet", "bassoon",
    "trumpet", "french_horn", "trombone",
    "harp",
]

# A reasonable middle-register MIDI note for each family
NOTE_FOR = {
    "piano_grand": 60, "piano_upright": 60, "piano_concert": 60,
    "harpsichord": 62, "pipe_organ": 60,
    "violin": 76, "viola": 67, "cello": 55, "cello_pizz": 55, "contrabass": 40,
    "strings_ensemble": 67,
    "flute": 79, "oboe": 70, "clarinet": 65, "bassoon": 50,
    "trumpet": 72, "french_horn": 60, "trombone": 53,
    "harp": 67,
}


# ---------------------------------------------------------------------------
# 1. Every orchestral preset is registered
# ---------------------------------------------------------------------------
print("\nOrchestral presets registered in PRESETS dict:")
for key in ORCHESTRAL_PRESETS:
    check(f"{key} in PRESETS", key in PRESETS)


# ---------------------------------------------------------------------------
# 2. Each preset renders a clean middle-register note
# ---------------------------------------------------------------------------
print("\nEach preset renders without crash, NaN, or clipping:")
for key in ORCHESTRAL_PRESETS:
    if key not in PRESETS:
        continue
    pat = Pattern(num_steps=8, num_channels=1, bpm=80, steps_per_beat=4)
    pat.set_note(0, 0, NoteEvent(midi_note=NOTE_FOR[key], velocity=0.8,
                                   duration_steps=8, instrument=key))
    audio = render_pattern(pat)
    finite = bool(np.all(np.isfinite(audio)))
    peak = float(np.max(np.abs(audio))) if finite else float("inf")
    rms = float(np.sqrt(np.mean(audio.mean(axis=1) ** 2))) if finite else 0.0
    check(f"{key} renders finite audio", finite)
    check(f"{key} peak < 1.0 (no clip)", peak < 1.0,
          f"peak = {peak:.4f}")
    check(f"{key} produces audible RMS", rms > 0.005,
          f"rms = {rms:.5f}")


# ---------------------------------------------------------------------------
# 3. Specific timbral checks
# ---------------------------------------------------------------------------
print("\nFamily-level timbral expectations:")

def render(key: str, midi: int, dur_steps: int = 8) -> np.ndarray:
    pat = Pattern(num_steps=16, num_channels=1, bpm=80, steps_per_beat=4)
    pat.set_note(0, 0, NoteEvent(midi_note=midi, velocity=0.8,
                                   duration_steps=dur_steps, instrument=key))
    return render_pattern(pat).mean(axis=1)


def spectral_centroid(sig: np.ndarray) -> float:
    spec = np.abs(np.fft.rfft(sig))
    freqs = np.fft.rfftfreq(len(sig), 1 / 44100)
    s = spec.sum()
    return float((spec * freqs).sum() / s) if s else 0.0


# Piano should decay toward silence (low sustain, no held tone)
piano_audio = render("piano_grand", 60, dur_steps=16)
mid_idx = len(piano_audio) // 4
end_idx = len(piano_audio) - 1
piano_attack_rms = float(np.sqrt(np.mean(piano_audio[:mid_idx] ** 2)))
piano_tail_rms = float(np.sqrt(np.mean(piano_audio[mid_idx:end_idx] ** 2)))
check("piano_grand decays (attack RMS > tail RMS)",
      piano_attack_rms > piano_tail_rms * 1.3,
      f"attack={piano_attack_rms:.5f}, tail={piano_tail_rms:.5f}")

# Pipe organ should sustain (attack RMS ≈ tail RMS within 50%)
organ_audio = render("pipe_organ", 60, dur_steps=16)
mid_o = len(organ_audio) // 4
organ_attack = float(np.sqrt(np.mean(organ_audio[:mid_o] ** 2)))
organ_tail = float(np.sqrt(np.mean(organ_audio[mid_o:mid_o * 3] ** 2)))
ratio = organ_tail / max(organ_attack, 1e-9)
check("pipe_organ sustains (tail RMS within 0.4-3.0x of attack)",
      0.4 < ratio < 3.0, f"ratio = {ratio:.3f}")

# Violin should be brighter than cello at the same MIDI note
violin_c4 = render("violin", 60, dur_steps=8)
cello_c4 = render("cello", 60, dur_steps=8)
vc = spectral_centroid(violin_c4)
cc = spectral_centroid(cello_c4)
check("violin centroid > cello centroid at C4",
      vc > cc, f"violin={vc:.0f}Hz, cello={cc:.0f}Hz")

# Trumpet should be brighter than french horn at the same note
trumpet_c5 = render("trumpet", 72, dur_steps=8)
horn_c5 = render("french_horn", 72, dur_steps=8)
tc = spectral_centroid(trumpet_c5)
hc = spectral_centroid(horn_c5)
check("trumpet centroid > french_horn centroid at C5",
      tc > hc, f"trumpet={tc:.0f}Hz, horn={hc:.0f}Hz")

# Harpsichord should decay (no sustain) similar to piano
harp_audio = render("harpsichord", 62, dur_steps=16)
mid_h = len(harp_audio) // 4
harp_attack = float(np.sqrt(np.mean(harp_audio[:mid_h] ** 2)))
harp_tail = float(np.sqrt(np.mean(harp_audio[mid_h * 3:] ** 2)))
check("harpsichord decays (tail much quieter than attack)",
      harp_attack > harp_tail * 2.0,
      f"attack={harp_attack:.5f}, tail={harp_tail:.5f}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print(f"\n{'=' * 60}")
print(f"  PASSED: {PASS}    FAILED: {FAIL}")
print(f"  Orchestral presets: {len(ORCHESTRAL_PRESETS)}")
print(f"{'=' * 60}")
if FAIL:
    print("\nFailures:")
    for e in ERRORS:
        print(f"  - {e}")
    sys.exit(1)
print("All orchestral preset tests passed.")
sys.exit(0)
