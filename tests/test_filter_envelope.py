#!/usr/bin/env python3
"""
ChipForge Filter Envelope Tests
================================
Verify that ADSR-shaped filter cutoff envelopes produce a cutoff curve
with the right shape and that the filtered audio sounds different from
a static-cutoff baseline.

Run:
    .venv/bin/python3 tests/test_filter_envelope.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.synth import (
    SAMPLE_RATE, FilterEnvelope,
    apply_filter_envelope, build_filter_envelope_curve,
    apply_lowpass, generate_sawtooth, synthesize_note, ADSR,
)
from src.instruments import Instrument
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
# 1. Curve shape — attack rises, decay falls to sustain, release falls to base
# ---------------------------------------------------------------------------
print("\nFilter envelope curve shape:")
env = FilterEnvelope(
    base_hz=300.0, peak_hz=4000.0, sustain_hz=1000.0,
    attack_sec=0.02, decay_sec=0.08, release_sec=0.05,
)
n = int(0.5 * SAMPLE_RATE)
curve = build_filter_envelope_curve(env, n)

a_idx = int(0.02 * SAMPLE_RATE)        # end of attack
d_idx = int(0.10 * SAMPLE_RATE)        # end of decay
r_start = n - int(0.05 * SAMPLE_RATE)   # start of release

check("curve length matches num_samples", len(curve) == n)
check("starts at base", abs(curve[0] - 300.0) < 50, f"got {curve[0]:.1f}")
check("reaches near-peak by end of attack",
      curve[a_idx - 1] > 3500.0, f"got {curve[a_idx - 1]:.1f}")
check("decays toward sustain by end of decay",
      900.0 < curve[d_idx - 1] < 1100.0, f"got {curve[d_idx - 1]:.1f}")
check("holds sustain in middle",
      900.0 < curve[(d_idx + r_start) // 2] < 1100.0)
check("returns near base at end",
      curve[-1] < 400.0, f"got {curve[-1]:.1f}")


# ---------------------------------------------------------------------------
# 2. Output differs from static cutoff
# ---------------------------------------------------------------------------
print("\nADSR filter changes the audio compared to a static lowpass:")
saw = generate_sawtooth(220.0, n)
filtered_env = apply_filter_envelope(saw, env)
filtered_static = apply_lowpass(saw, 1000.0, resonance=0.3)
check("filter_envelope output is the same length", len(filtered_env) == n)
check("filter_envelope differs from static lowpass",
      not np.allclose(filtered_env, filtered_static, atol=1e-3))
check("output is finite (no NaN/Inf)",
      np.all(np.isfinite(filtered_env)))


# ---------------------------------------------------------------------------
# 3. Spectral check — RMS of attack region should exceed RMS near base
# ---------------------------------------------------------------------------
print("\nAttack region brighter than tail (more high-freq energy):")
# Compute RMS of high-pass-filtered signal in attack vs end
from src.synth import apply_highpass
hp = apply_highpass(filtered_env, 2000.0)
attack_rms = float(np.sqrt(np.mean(hp[: a_idx + 200] ** 2)))
end_rms = float(np.sqrt(np.mean(hp[-2000:] ** 2)))
check("attack region has more energy above 2 kHz than tail",
      attack_rms > end_rms,
      f"attack RMS {attack_rms:.5f}, tail RMS {end_rms:.5f}")


# ---------------------------------------------------------------------------
# 4. End-to-end via render_pattern
# ---------------------------------------------------------------------------
print("\nrender_pattern picks up filter_env from instrument:")
inst = Instrument(
    name="env-saw",
    waveform="sawtooth",
    adsr=ADSR(attack=0.005, decay=0.05, sustain=0.7, release=0.1),
    volume=0.7,
    filter_env=FilterEnvelope(
        base_hz=400.0, peak_hz=5000.0, sustain_hz=900.0,
        attack_sec=0.02, decay_sec=0.10, release_sec=0.05,
        resonance=0.4,
    ),
)
inst_dry = Instrument(
    name="dry-saw",
    waveform="sawtooth",
    adsr=ADSR(attack=0.005, decay=0.05, sustain=0.7, release=0.1),
    volume=0.7,
)

pat = Pattern(num_steps=4, num_channels=1, bpm=120, steps_per_beat=4)
pat.set_note(0, 0, NoteEvent(midi_note=57, velocity=0.8, duration_steps=4,
                              instrument="env_saw"))

audio_env = render_pattern(pat, instruments={"env_saw": inst, "pulse_lead": inst})
audio_dry = render_pattern(pat, instruments={"env_saw": inst_dry, "pulse_lead": inst_dry})

check("filter_env output is finite", np.all(np.isfinite(audio_env)))
check("filter_env output differs from dry sawtooth",
      not np.allclose(audio_env, audio_dry, atol=1e-3))
check("filter_env output peaks below clip",
      np.max(np.abs(audio_env)) < 1.0)


# ---------------------------------------------------------------------------
# 5. Edge cases
# ---------------------------------------------------------------------------
print("\nEdge cases:")
empty = apply_filter_envelope(np.zeros(0, dtype=np.float32), env)
check("empty input returns empty output", len(empty) == 0)

# Curve shorter than ADSR sum should still work
tiny_env = FilterEnvelope(
    base_hz=200, peak_hz=2000, sustain_hz=500,
    attack_sec=0.5, decay_sec=0.5, release_sec=0.5,
)
tiny_curve = build_filter_envelope_curve(tiny_env, 100)
check("curve shorter than ADSR is truncated cleanly",
      len(tiny_curve) == 100)
check("truncated curve is finite", np.all(np.isfinite(tiny_curve)))


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
print("All filter envelope tests passed.")
sys.exit(0)
