#!/usr/bin/env python3
"""
ChipForge Temperament Tests
============================
Verify historical tuning systems return musically correct frequencies.

Run:
    .venv/bin/python3 tests/test_temperament.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.temperament import (
    list_temperaments, temper_freq, temperament_description,
)
from src.synth import synthesize_note, note_to_freq

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


def approx(a: float, b: float, tol_cents: float = 0.1) -> bool:
    """Check that two frequencies are within `tol_cents` cents of each other."""
    if a <= 0 or b <= 0:
        return a == b
    import math
    cents = 1200.0 * abs(math.log2(a / b))
    return cents < tol_cents


# ---------------------------------------------------------------------------
# 1. Equal temperament regression — must match note_to_freq exactly
# ---------------------------------------------------------------------------
print("\nEqual temperament (regression vs note_to_freq):")
for midi in [21, 60, 69, 72, 88, 100]:
    eq = temper_freq(midi, "equal")
    ref = note_to_freq(midi)
    check(f"MIDI {midi} equal == note_to_freq", approx(eq, ref, 0.001),
          f"got {eq:.4f} vs {ref:.4f}")

# A4 should always equal 440 Hz across temperaments since they're anchored.
print("\nA4 anchor (440 Hz) across all temperaments:")
for t in list_temperaments():
    f = temper_freq(69, t, key_root_pc=9)
    check(f"{t} A4 == 440 Hz", approx(f, 440.0, 0.01), f"got {f:.4f}")


# ---------------------------------------------------------------------------
# 2. Just intonation — pure 5:4 major third in C major
# ---------------------------------------------------------------------------
print("\nJust intonation in C major (key_root_pc=0):")
c4 = temper_freq(60, "just", 0)
e4 = temper_freq(64, "just", 0)
g4 = temper_freq(67, "just", 0)
check("C4-E4 ratio is 5:4 (pure major third)",
      approx(e4 / c4, 5/4, 0.5), f"got ratio {e4/c4:.6f}")
check("C4-G4 ratio is 3:2 (pure perfect fifth)",
      approx(g4 / c4, 3/2, 0.5), f"got ratio {g4/c4:.6f}")


# ---------------------------------------------------------------------------
# 3. Pythagorean — pure 3:2 fifths but bright (sharp) major thirds
# ---------------------------------------------------------------------------
print("\nPythagorean tuning (C major):")
c4_p = temper_freq(60, "pythagorean", 0)
e4_p = temper_freq(64, "pythagorean", 0)
g4_p = temper_freq(67, "pythagorean", 0)
# Pythagorean C-E interval should be the ditone 81/64 = 1.265625 (~408¢),
# wider than the equal-temp major third (~400¢ = 1.2599).
ratio_pyth_third = e4_p / c4_p
check("Pythagorean fifth is pure 3:2", approx(g4_p / c4_p, 3/2, 0.5),
      f"got ratio {g4_p/c4_p:.6f}")
check("Pythagorean major 3rd is the ditone 81/64",
      approx(ratio_pyth_third, 81/64, 1.0),
      f"got ratio {ratio_pyth_third:.6f}")
check("Pythagorean major 3rd wider than equal-temp third",
      ratio_pyth_third > 2 ** (4/12) + 0.005,
      f"pyth ratio {ratio_pyth_third:.6f} vs equal {2**(4/12):.6f}")


# ---------------------------------------------------------------------------
# 4. Meantone — pure 5:4 thirds but tempered fifths
# ---------------------------------------------------------------------------
print("\n1/4-comma meantone (C major):")
c4_m = temper_freq(60, "meantone", 0)
e4_m = temper_freq(64, "meantone", 0)
g4_m = temper_freq(67, "meantone", 0)
check("Meantone major 3rd is pure 5:4", approx(e4_m / c4_m, 5/4, 1.0),
      f"got ratio {e4_m/c4_m:.6f}")
check("Meantone fifth is flatter than pure 3:2", g4_m / c4_m < 1.5,
      f"got ratio {g4_m/c4_m:.6f}")


# ---------------------------------------------------------------------------
# 5. Werckmeister III — well temperament (every key playable)
# ---------------------------------------------------------------------------
print("\nWerckmeister III well temperament:")
# All 12 chromatic notes in an octave from C should be unique and ascending.
prev = 0.0
ok = True
for pc in range(12):
    f = temper_freq(60 + pc, "werckmeister", 0)
    if f <= prev:
        ok = False
        break
    prev = f
check("Werckmeister chromatic scale ascends monotonically", ok)
# Werckmeister C-E should be slightly sharper than just (pure) but flatter
# than Pythagorean — it sits between.
e_w = temper_freq(64, "werckmeister", 0) / temper_freq(60, "werckmeister", 0)
check("Werckmeister C-E between pure and Pythagorean",
      5/4 < e_w < 81/64,
      f"got ratio {e_w:.6f}")


# ---------------------------------------------------------------------------
# 6. Octave equivalence — every temperament must double across octaves
# ---------------------------------------------------------------------------
print("\nOctave equivalence (every system must double across octaves):")
for t in list_temperaments():
    f4 = temper_freq(60, t, 0)
    f5 = temper_freq(72, t, 0)
    check(f"{t} octave = 2:1", approx(f5 / f4, 2.0, 0.01),
          f"got ratio {f5/f4:.6f}")


# ---------------------------------------------------------------------------
# 7. End-to-end — synthesize_note actually uses the temperament
# ---------------------------------------------------------------------------
print("\nsynthesize_note honours temperament parameter:")
import numpy as np
sig_eq = synthesize_note(64, 0.05, waveform="sine", temperament="equal")
sig_pt = synthesize_note(64, 0.05, waveform="sine",
                          temperament="pythagorean", key_root_pc=0)
# Different tuning → different waveform output
check("Pythagorean E differs from equal-temp E in waveform",
      not np.allclose(sig_eq, sig_pt))
check("Both signals have the right shape", len(sig_eq) == len(sig_pt))


# ---------------------------------------------------------------------------
# 8. Descriptions exist for all temperaments
# ---------------------------------------------------------------------------
print("\nDescriptions:")
for t in list_temperaments():
    desc = temperament_description(t)
    check(f"{t} has description", len(desc) > 10, desc)


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
print("All temperament tests passed.")
sys.exit(0)
