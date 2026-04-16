#!/usr/bin/env python3
"""
ChipForge AI Engine Enhancement Tests
=======================================
Validates: spectral morphing, per-harmonic envelopes, shaped instruments,
and integration with the mixer pipeline.

Run: .venv/bin/python3 tests/test_ai_engine.py
"""

import sys
import os
import logging
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.synth import (
    SAMPLE_RATE, generate_sine, generate_sawtooth, generate_additive,
    generate_additive_shaped, spectral_morph, synthesize_note,
    HARMONIC_PROFILES, SHAPED_PROFILES, ADSR, note_to_freq,
)
from src.instruments import PRESETS, Instrument
from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')
logger = logging.getLogger("test_ai_engine")

PASS = 0
FAIL = 0
OUTPUT_DIR = Path("output/test-ai-engine")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} — {detail}")


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 1: Spectral Morphing
# ═══════════════════════════════════════════════════════════════

def test_spectral_morph():
    print("\n═══ Spectral Morphing Tests ═══")

    # Test 1: Basic morph produces valid output
    n = 44100
    saw = generate_sawtooth(440.0, n)
    sine = generate_sine(440.0, n)

    t0 = time.time()
    morphed = spectral_morph(saw, sine, 0.5)
    dt = time.time() - t0

    test("Morph output same length as input", len(morphed) == n)
    test("Morph output is float32", morphed.dtype == np.float32)
    test("Morph peak within [-1,1]", np.max(np.abs(morphed)) <= 1.05,
         f"peak={np.max(np.abs(morphed)):.4f}")
    test(f"Morph renders in reasonable time ({dt:.3f}s)", dt < 5.0,
         f"took {dt:.3f}s")

    # Test 2: Morph=0 should be close to wave_a
    morph_0 = spectral_morph(saw, sine, 0.0)
    corr_a = np.corrcoef(saw[:4096], morph_0[:4096])[0, 1]
    test("Morph=0.0 correlates with source (>0.8)", corr_a > 0.8,
         f"correlation={corr_a:.4f}")

    # Test 3: Morph=1 should be close to wave_b
    morph_1 = spectral_morph(saw, sine, 1.0)
    corr_b = np.corrcoef(sine[:4096], morph_1[:4096])[0, 1]
    test("Morph=1.0 correlates with target (>0.8)", corr_b > 0.8,
         f"correlation={corr_b:.4f}")

    # Test 4: Time-varying morph (gradual transition)
    curve = np.linspace(0, 1, n, dtype=np.float32)
    morphed_grad = spectral_morph(saw, sine, curve)
    test("Time-varying morph produces valid output", len(morphed_grad) == n)

    # Test 5: Morph between different harmonic profiles
    bell = generate_additive(440.0, n, harmonics=HARMONIC_PROFILES["bell"])
    warm = generate_additive(440.0, n, harmonics=HARMONIC_PROFILES["warm"])
    morphed_profiles = spectral_morph(bell, warm, 0.5)
    test("Profile-to-profile morph valid", len(morphed_profiles) == n)

    # Export test WAVs for listening
    stereo = lambda x: np.stack([x, x], axis=1)
    export_wav(stereo(saw), OUTPUT_DIR / "morph_01_source_saw.wav")
    export_wav(stereo(sine), OUTPUT_DIR / "morph_02_target_sine.wav")
    export_wav(stereo(morphed), OUTPUT_DIR / "morph_03_50pct.wav")
    export_wav(stereo(morphed_grad), OUTPUT_DIR / "morph_04_gradual.wav")
    export_wav(stereo(morphed_profiles), OUTPUT_DIR / "morph_05_bell_to_warm.wav")
    print(f"  → Exported 5 morph test WAVs to {OUTPUT_DIR}/")


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 2: Per-Harmonic Envelope Shaping
# ═══════════════════════════════════════════════════════════════

def test_per_harmonic_envelopes():
    print("\n═══ Per-Harmonic Envelope Tests ═══")

    # Test 1: Basic shaped note
    n = 44100
    t0 = time.time()
    shaped = generate_additive_shaped(440.0, n)
    dt = time.time() - t0

    test("Shaped output correct length", len(shaped) == n)
    test("Shaped output is float32", shaped.dtype == np.float32)
    test("Shaped peak within [-1,1]", np.max(np.abs(shaped)) <= 1.05)
    test(f"Shaped renders quickly ({dt:.3f}s)", dt < 2.0)

    # Test 2: Different profiles produce different outputs
    profiles_tested = 0
    for name, profile in SHAPED_PROFILES.items():
        result = generate_additive_shaped(
            440.0, n,
            harmonic_amplitudes=profile["amplitudes"],
            harmonic_envelopes=profile["envelopes"],
        )
        test(f"Profile '{name}' renders valid output", len(result) == n)
        profiles_tested += 1

    test(f"All {profiles_tested} shaped profiles render", profiles_tested == len(SHAPED_PROFILES))

    # Test 3: Shaped vs unshaped — they should differ
    unshaped = generate_additive(440.0, n, harmonics=SHAPED_PROFILES["evolving_bell"]["amplitudes"])
    shaped_bell = generate_additive_shaped(
        440.0, n,
        harmonic_amplitudes=SHAPED_PROFILES["evolving_bell"]["amplitudes"],
        harmonic_envelopes=SHAPED_PROFILES["evolving_bell"]["envelopes"],
    )
    # They start similarly but diverge as envelopes differ
    diff = np.mean(np.abs(unshaped - shaped_bell))
    test("Shaped differs from unshaped (envelopes have effect)", diff > 0.01,
         f"mean_diff={diff:.6f}")

    # Export test WAVs
    stereo = lambda x: np.stack([x, x], axis=1)
    for name, profile in SHAPED_PROFILES.items():
        result = generate_additive_shaped(
            440.0, n,
            harmonic_amplitudes=profile["amplitudes"],
            harmonic_envelopes=profile["envelopes"],
        )
        export_wav(stereo(result), OUTPUT_DIR / f"shaped_{name}.wav")
    print(f"  → Exported {len(SHAPED_PROFILES)} shaped profile WAVs to {OUTPUT_DIR}/")


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 3: New Instrument Presets
# ═══════════════════════════════════════════════════════════════

def test_shaped_instruments():
    print("\n═══ Shaped Instrument Preset Tests ═══")

    shaped_presets = [k for k in PRESETS if k.startswith("shaped_")]
    test(f"Shaped presets exist ({len(shaped_presets)})", len(shaped_presets) >= 4,
         f"found: {shaped_presets}")

    for name in shaped_presets:
        inst = PRESETS[name]
        note = synthesize_note(60, 1.0, waveform=inst.waveform,
                               adsr=inst.adsr, volume=inst.volume)
        test(f"Preset '{name}' synthesizes OK", len(note) > 0 and np.max(np.abs(note)) > 0,
             f"len={len(note)}, peak={np.max(np.abs(note)):.4f}")


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 4: Integration — Full Song Render with New Features
# ═══════════════════════════════════════════════════════════════

def test_integration_render():
    print("\n═══ Integration Render Test ═══")

    BPM = 130
    SPB = 4
    BAR = 16

    def note(inst, midi, vel=0.75, dur=2):
        return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                         duration_steps=max(dur, 2), instrument=inst)

    # 4-bar test pattern using new instruments
    steps = BAR * 4
    grid = [[None] * steps for _ in range(7)]

    # CH0: Kick
    for bar in range(4):
        for beat in range(4):
            grid[0][bar * BAR + beat * 4] = note('kick_deep', 36, 0.78)

    # CH1: Snare
    for bar in range(4):
        grid[1][bar * BAR + 4] = note('noise_clap', 38, 0.72, 3)
        grid[1][bar * BAR + 12] = note('noise_clap', 38, 0.70, 3)

    # CH2: Shaped bell melody
    melody = [60, 64, 67, 72, 67, 64, 60, 62, 64, 67, 72, 76, 72, 67, 64, 60]
    for i, m in enumerate(melody):
        grid[2][i * 4] = note('shaped_bell', m, 0.65, 4)

    # CH3: Shaped brass pad
    for bar in range(4):
        grid[3][bar * BAR] = note('shaped_brass', 48, 0.50, BAR)

    # CH4: Shaped vocal lead
    vocal_melody = [72, 74, 76, 74, 72, 71, 69, 67]
    for i, m in enumerate(vocal_melody):
        grid[4][i * 8] = note('shaped_vocal', m, 0.70, 6)

    # CH5: Bass
    for bar in range(4):
        grid[5][bar * BAR] = note('bass_growl', 36, 0.78, 6)
        grid[5][bar * BAR + 8] = note('bass_growl', 43, 0.62, 4)

    # CH6: Shaped pluck arp
    arp = [60, 64, 67, 72, 67, 64]
    for step in range(steps):
        grid[6][step] = note('shaped_pluck', arp[step % len(arp)], 0.45, 2)

    pattern = Pattern(name='ai_test', num_steps=steps, num_channels=7,
                      steps_per_beat=SPB, bpm=BPM, grid=grid)

    song = Song(
        title='AI Engine Test — Shaped Instruments',
        bpm=BPM,
        patterns=[pattern],
        sequence=[0],
        panning={0: 0.0, 1: 0.0, 2: 0.30, 3: -0.20, 4: 0.12, 5: 0.0, 6: -0.30},
        channel_effects={
            0: {'reverb': 0.08},
            1: {'reverb': 0.15},
            2: {'reverb': 0.40, 'delay': 0.23, 'delay_feedback': 0.20},
            3: {'reverb': 0.50, 'chorus': 0.25},
            4: {'reverb': 0.35, 'delay': 0.15},
            5: {'reverb': 0.08},
            6: {'reverb': 0.20, 'delay': 0.18, 'delay_feedback': 0.30},
        },
        master_reverb=0.10,
    )

    t0 = time.time()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb)
    dt = time.time() - t0

    duration = len(audio) / SAMPLE_RATE
    peak = float(np.max(np.abs(audio)))

    test("Integration render produces audio", len(audio) > 0)
    test("Audio is stereo", audio.shape[1] == 2)
    test(f"Duration reasonable ({duration:.1f}s)", 5 < duration < 30)
    test(f"Peak level OK ({peak:.4f})", 0.1 < peak <= 1.0)
    test(f"Render time OK ({dt:.1f}s)", dt < 120)
    test("No NaN in output", not np.any(np.isnan(audio)))
    test("No Inf in output", not np.any(np.isinf(audio)))

    out = OUTPUT_DIR / "integration_shaped_instruments.wav"
    export_wav(audio, out)
    print(f"  → Integration test WAV: {out} ({duration:.1f}s, {peak:.4f} peak, {dt:.1f}s render)")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("  ChipForge AI Engine Enhancement Tests")
    print("  Testing: spectral morph, per-harmonic envelopes, shaped instruments")
    print("=" * 60)

    test_spectral_morph()
    test_per_harmonic_envelopes()
    test_shaped_instruments()
    test_integration_render()

    print("\n" + "=" * 60)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print(f"  Test WAVs in: {OUTPUT_DIR}/")
    print("=" * 60)

    sys.exit(1 if FAIL > 0 else 0)
