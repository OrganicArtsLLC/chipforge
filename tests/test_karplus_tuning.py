#!/usr/bin/env python3
"""
ChipForge Karplus-Strong Tuning Tests
======================================
Verify that the Karplus-Strong plucked string stays in tune across the
full musical register. The naive integer-only delay length was sharp by
+6 cents at C5 and +23 cents at E6 — this test pins the fix.

Run:
    .venv/bin/python3 tests/test_karplus_tuning.py
"""

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.synth import (
    SAMPLE_RATE, generate_karplus_strong, note_to_freq,
)


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


def detect_fundamental(signal: np.ndarray, sr: int = SAMPLE_RATE) -> float:
    """
    Estimate the fundamental frequency of a steady-state monophonic signal
    via autocorrelation. Robust enough for our register; we don't need
    musical-instrument-grade pitch detection here.
    """
    # Trim attack transient — only analyse the middle of the signal
    n = len(signal)
    middle = signal[n // 4: 3 * n // 4]
    if len(middle) == 0:
        return 0.0
    middle = middle - np.mean(middle)

    # Autocorrelation
    corr = np.correlate(middle, middle, mode="full")
    corr = corr[len(corr) // 2:]

    # Find the first peak after the zero-lag (skip the first ~50 samples)
    min_lag = int(sr / 5000)   # cap at 5 kHz fundamental
    max_lag = int(sr / 60)     # floor at 60 Hz fundamental
    if max_lag >= len(corr):
        max_lag = len(corr) - 1
    if min_lag >= max_lag:
        return 0.0
    search = corr[min_lag:max_lag]
    if len(search) == 0:
        return 0.0
    peak_lag = int(np.argmax(search)) + min_lag
    if peak_lag <= 0:
        return 0.0

    # Parabolic interpolation around the peak for sub-sample accuracy
    if 1 <= peak_lag < len(corr) - 1:
        a = float(corr[peak_lag - 1])
        b = float(corr[peak_lag])
        c = float(corr[peak_lag + 1])
        denom = (a - 2 * b + c)
        if denom != 0:
            offset = 0.5 * (a - c) / denom
            peak_lag = peak_lag + offset

    return float(sr / peak_lag)


def cents_off(actual_hz: float, target_hz: float) -> float:
    if actual_hz <= 0 or target_hz <= 0:
        return float("inf")
    return 1200.0 * math.log2(actual_hz / target_hz)


# ---------------------------------------------------------------------------
# Tuning sweep across the keyboard register
# ---------------------------------------------------------------------------
print("\nKarplus pitch accuracy across the keyboard:")

# MIDI 36 = C2 (low cello), 48 = C3, 60 = C4 (middle C), 72 = C5,
# 84 = C6, 88 = E6, 96 = C7. Test the full piano register.
test_notes = [36, 43, 48, 55, 60, 64, 67, 72, 76, 79, 84, 88, 91, 96]

worst_cents = 0.0
worst_note = 0
for midi in test_notes:
    target = note_to_freq(midi)
    sig = generate_karplus_strong(target, num_samples=int(0.6 * SAMPLE_RATE),
                                    decay=0.998, brightness=0.4)
    detected = detect_fundamental(sig)
    err = cents_off(detected, target)
    if abs(err) > abs(worst_cents):
        worst_cents = err
        worst_note = midi
    check(f"MIDI {midi:3d} ({target:.2f} Hz) within ±5¢ of equal temp",
          abs(err) < 5.0,
          f"detected {detected:.2f} Hz, error {err:+.2f}¢")

print(f"\n  Worst-case error across the register: "
      f"MIDI {worst_note} = {worst_cents:+.2f}¢")
check("Worst-case error across full register stays under ±5 cents",
      abs(worst_cents) < 5.0,
      f"worst was MIDI {worst_note} at {worst_cents:+.2f}¢")


# ---------------------------------------------------------------------------
# Regression: very high notes (E6, G6) used to be ~20 cents sharp
# ---------------------------------------------------------------------------
print("\nUpper register regression (E6 was +23¢ sharp before):")
for midi in [88, 91]:  # E6, G6
    target = note_to_freq(midi)
    sig = generate_karplus_strong(target, num_samples=int(0.6 * SAMPLE_RATE),
                                    decay=0.998, brightness=0.4)
    detected = detect_fundamental(sig)
    err = cents_off(detected, target)
    check(f"MIDI {midi} no longer +20¢ sharp",
          abs(err) < 5.0,
          f"err {err:+.2f}¢")


# ---------------------------------------------------------------------------
# A4 = 440 still sounds at 440 (sanity check)
# ---------------------------------------------------------------------------
print("\nA4 sanity check:")
sig = generate_karplus_strong(440.0, num_samples=int(0.6 * SAMPLE_RATE),
                                decay=0.998, brightness=0.4)
detected = detect_fundamental(sig)
err = cents_off(detected, 440.0)
check("Karplus at 440 Hz detects ~440 Hz",
      abs(err) < 5.0, f"detected {detected:.2f} Hz, err {err:+.2f}¢")


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
print("All Karplus tuning tests passed.")
sys.exit(0)
