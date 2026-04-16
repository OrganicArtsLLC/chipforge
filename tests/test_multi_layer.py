#!/usr/bin/env python3
"""
ChipForge Multi-Layer Voice Tests
==================================
Verify that stacked VoiceLayer instruments produce a richer, detuned sum
than a single-waveform instrument and don't clip.

Run:
    .venv/bin/python3 tests/test_multi_layer.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.synth import ADSR, synthesize_note, note_to_freq
from src.instruments import Instrument, VoiceLayer
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


# ---------------------------------------------------------------------------
# 1. freq_override forces a known frequency
# ---------------------------------------------------------------------------
print("\nfreq_override on synthesize_note:")
note_a4 = synthesize_note(69, 0.1, waveform="sine")  # MIDI A4 = 440
note_440 = synthesize_note(60, 0.1, waveform="sine", freq_override=440.0)
# Both should peak around the same frequency. Verify zero-crossings match
def zero_crossings(sig: np.ndarray) -> int:
    return int(np.sum((sig[:-1] * sig[1:]) < 0))
zc_a4 = zero_crossings(note_a4)
zc_440 = zero_crossings(note_440)
check("freq_override 440 produces same zero-crossing count as MIDI 69",
      abs(zc_a4 - zc_440) <= 2, f"a4 zc={zc_a4}, override zc={zc_440}")


# ---------------------------------------------------------------------------
# 2. Layered instrument has more spectral content than single waveform
# ---------------------------------------------------------------------------
print("\nLayered instrument is spectrally richer than single sine:")
single = Instrument(
    name="single-sine",
    waveform="sine",
    adsr=ADSR(attack=0.005, decay=0.05, sustain=0.7, release=0.1),
    volume=0.7,
)
layered = Instrument(
    name="layered-sine",
    waveform="sine",
    adsr=ADSR(attack=0.005, decay=0.05, sustain=0.7, release=0.1),
    volume=0.5,
    layers=[
        VoiceLayer(waveform="sawtooth", gain=0.3, detune_cents=-7.0),
        VoiceLayer(waveform="square",   gain=0.2, detune_cents=+7.0, duty=0.5),
    ],
)

pat = Pattern(num_steps=4, num_channels=1, bpm=120, steps_per_beat=4)
pat.set_note(0, 0, NoteEvent(midi_note=57, velocity=0.8, duration_steps=4,
                              instrument="layered"))

audio_single = render_pattern(pat, instruments={"layered": single, "pulse_lead": single})
audio_layered = render_pattern(pat, instruments={"layered": layered, "pulse_lead": layered})

# Layered should have more spectral spread (not just a single sine)
def spectral_centroid(sig: np.ndarray) -> float:
    mono = sig.mean(axis=1) if sig.ndim == 2 else sig
    spec = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(len(mono), 1 / 44100)
    if spec.sum() == 0:
        return 0.0
    return float((spec * freqs).sum() / spec.sum())

cs_single = spectral_centroid(audio_single)
cs_layered = spectral_centroid(audio_layered)
check("layered output is finite", np.all(np.isfinite(audio_layered)))
check("layered output is non-trivially different",
      not np.allclose(audio_single, audio_layered, atol=1e-3))
check("layered spectral centroid > single sine centroid",
      cs_layered > cs_single * 1.5,
      f"single={cs_single:.1f} Hz, layered={cs_layered:.1f} Hz")


# ---------------------------------------------------------------------------
# 3. Detuned layer beats with primary (creates chorusing)
# ---------------------------------------------------------------------------
print("\nDetuned layer creates audible beating with primary:")
beat_inst = Instrument(
    name="beating",
    waveform="sine",
    adsr=ADSR(attack=0.005, decay=0.0, sustain=1.0, release=0.05),
    volume=0.5,
    layers=[
        VoiceLayer(waveform="sine", gain=0.5, detune_cents=10.0),  # ~2.5 Hz beat at A4
    ],
)
pat2 = Pattern(num_steps=4, num_channels=1, bpm=120, steps_per_beat=4)
# Whole note at A4 (MIDI 69)
pat2.set_note(0, 0, NoteEvent(midi_note=69, velocity=0.8, duration_steps=16,
                                instrument="beat"))
audio_beat = render_pattern(pat2, instruments={"beat": beat_inst, "pulse_lead": beat_inst})
mono = audio_beat.mean(axis=1)
# RMS in 50 ms windows — should oscillate (beat) over time
window = int(0.05 * 44100)
rms_chunks = [
    float(np.sqrt(np.mean(mono[i:i + window] ** 2)))
    for i in range(0, len(mono) - window, window)
]
rms_arr = np.array(rms_chunks)
rms_var = float(rms_arr.std()) / max(float(rms_arr.mean()), 1e-9)
check("RMS varies over time (chorusing/beating present)",
      rms_var > 0.05, f"rms variation = {rms_var:.4f}")


# ---------------------------------------------------------------------------
# 4. Layered instruments survive existing temperament + filter env stack
# ---------------------------------------------------------------------------
print("\nLayered instruments compose with temperament + filter env:")
from src.synth import FilterEnvelope
combo = Instrument(
    name="combo",
    waveform="sawtooth",
    adsr=ADSR(attack=0.005, decay=0.05, sustain=0.7, release=0.1),
    volume=0.5,
    filter_env=FilterEnvelope(
        base_hz=400, peak_hz=4000, sustain_hz=900,
        attack_sec=0.02, decay_sec=0.10, release_sec=0.05,
    ),
    layers=[VoiceLayer(waveform="square", gain=0.3, detune_cents=5.0, duty=0.5)],
)
pat3 = Pattern(num_steps=4, num_channels=1, bpm=120, steps_per_beat=4,
                temperament="just", key_root_pc=0)
pat3.set_note(0, 0, NoteEvent(midi_note=60, velocity=0.8, duration_steps=4,
                                instrument="combo"))
audio_combo = render_pattern(pat3, instruments={"combo": combo, "pulse_lead": combo})
check("combo output is finite", np.all(np.isfinite(audio_combo)))
check("combo output peaks below clip",
      float(np.max(np.abs(audio_combo))) < 1.0)


# ---------------------------------------------------------------------------
# 5. Backwards compat — instruments with no layers field still work
# ---------------------------------------------------------------------------
print("\nBackwards compat — no layers field:")
plain = Instrument(
    name="plain",
    waveform="square",
    adsr=ADSR(attack=0.005, decay=0.05, sustain=0.7, release=0.1),
    volume=0.7,
)
pat4 = Pattern(num_steps=4, num_channels=1, bpm=120, steps_per_beat=4)
pat4.set_note(0, 0, NoteEvent(midi_note=60, velocity=0.8, duration_steps=4,
                                instrument="plain"))
audio_plain = render_pattern(pat4, instruments={"plain": plain, "pulse_lead": plain})
check("plain instrument still renders without crash",
      np.all(np.isfinite(audio_plain)))


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
print("All multi-layer tests passed.")
sys.exit(0)
