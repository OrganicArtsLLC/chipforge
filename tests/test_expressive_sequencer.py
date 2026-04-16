#!/usr/bin/env python3
"""
ChipForge Expressive Sequencer Tests
=====================================
Verify articulation flags, portamento glide, time signature, and song-
level tempo curves all behave correctly end-to-end.

Run:
    .venv/bin/python3 tests/test_expressive_sequencer.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.synth import ADSR, SAMPLE_RATE
from src.instruments import Instrument
from src.sequencer import Pattern, NoteEvent, Song
from src.mixer import render_pattern, render_song


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
    adsr=ADSR(attack=0.005, decay=0.02, sustain=0.85, release=0.04),
    volume=0.7,
)
INSTS = {"sine": sine, "pulse_lead": sine}


def make_pat(events: list[NoteEvent], bpm: float = 120.0) -> Pattern:
    pat = Pattern(num_steps=8, num_channels=1, bpm=bpm, steps_per_beat=4)
    for i, ev in enumerate(events):
        pat.set_note(0, i, ev)
    return pat


# ---------------------------------------------------------------------------
# 1. Articulation: staccato shortens, marcato accents
# ---------------------------------------------------------------------------
print("\nArticulation modifies note duration and velocity:")

# A long sustained note with various articulations. Use a high-sustain ADSR
# wired to the test instrument so it actually rings the full duration_steps.
sustained = Instrument(
    name="sus",
    waveform="sine",
    adsr=ADSR(attack=0.005, decay=0.02, sustain=0.95, release=0.02),
    volume=0.7,
)
SUS_INSTS = {"sus": sustained, "pulse_lead": sustained}

def render_one(artic: str) -> np.ndarray:
    pat = Pattern(num_steps=16, num_channels=1, bpm=120, steps_per_beat=4)
    pat.set_note(0, 0, NoteEvent(midi_note=69, velocity=0.7,
                                  duration_steps=16, instrument="sus",
                                  articulation=artic))
    return render_pattern(pat, instruments=SUS_INSTS).mean(axis=1)

normal = render_one("normal")
staccato = render_one("staccato")
marcato = render_one("marcato")
fermata = render_one("fermata")

def rms_window(sig: np.ndarray, start: int, end: int) -> float:
    return float(np.sqrt(np.mean(sig[start:end] ** 2)))

# Staccato should cut the note off at ~50% of its written duration.
# Compare RMS in the 60-90% region of the pattern: normal still rings,
# staccato is silent.
n = len(normal)
late_start = int(n * 0.60)
late_end = int(n * 0.90)
check("staccato silences late region (ends early)",
      rms_window(staccato, late_start, late_end) <
        rms_window(normal, late_start, late_end) * 0.3,
      f"normal RMS = {rms_window(normal, late_start, late_end):.5f}, "
      f"stacc RMS = {rms_window(staccato, late_start, late_end):.5f}")
check("marcato is louder than normal at peak",
      float(np.max(np.abs(marcato))) > float(np.max(np.abs(normal))) * 1.05,
      f"normal peak {np.max(np.abs(normal)):.4f}, marcato peak {np.max(np.abs(marcato)):.4f}")
check("fermata still ringing in late region",
      rms_window(fermata, late_start, late_end) >
        rms_window(staccato, late_start, late_end))


# ---------------------------------------------------------------------------
# 2. Glide: portamento creates audible pitch transition
# ---------------------------------------------------------------------------
print("\nPortamento glide between notes:")
events_no_glide = [
    NoteEvent(midi_note=60, velocity=0.7, duration_steps=4, instrument="sine"),
    NoteEvent(midi_note=72, velocity=0.7, duration_steps=4, instrument="sine"),
]
events_glide = [
    NoteEvent(midi_note=60, velocity=0.7, duration_steps=4, instrument="sine"),
    NoteEvent(midi_note=72, velocity=0.7, duration_steps=4,
              instrument="sine", glide_ms=120.0),
]
pat_no = Pattern(num_steps=8, num_channels=1, bpm=120, steps_per_beat=4)
pat_no.set_note(0, 0, events_no_glide[0])
pat_no.set_note(0, 4, events_no_glide[1])
pat_glide = Pattern(num_steps=8, num_channels=1, bpm=120, steps_per_beat=4)
pat_glide.set_note(0, 0, events_glide[0])
pat_glide.set_note(0, 4, events_glide[1])

audio_no = render_pattern(pat_no, instruments=INSTS)
audio_glide = render_pattern(pat_glide, instruments=INSTS)

check("glide output is finite", np.all(np.isfinite(audio_glide)))
check("glide audio differs from un-glided audio",
      not np.allclose(audio_no, audio_glide, atol=1e-4))
# The first ~120ms of the second note should be different — that's the glide
sec_note_start = int(4 * (60 / 120 / 4) * SAMPLE_RATE)  # 4 steps in
glide_window = slice(sec_note_start, sec_note_start + int(0.12 * SAMPLE_RATE))
diff = float(np.mean(np.abs(
    audio_glide.mean(axis=1)[glide_window] - audio_no.mean(axis=1)[glide_window]
)))
check("glide window contains audible pitch transition",
      diff > 1e-3, f"avg diff in glide window = {diff:.6f}")


# ---------------------------------------------------------------------------
# 3. Time signature stored on pattern
# ---------------------------------------------------------------------------
print("\nTime signature on Pattern:")
waltz = Pattern(num_steps=12, num_channels=1, bpm=120, steps_per_beat=4,
                time_sig_num=3, time_sig_den=4)
check("default pattern is 4/4", Pattern().time_sig_num == 4)
check("waltz pattern stores 3/4", waltz.time_sig_num == 3 and waltz.time_sig_den == 4)
roundtrip = Pattern.from_dict(waltz.to_dict())
check("time signature round-trips through to_dict/from_dict",
      roundtrip.time_sig_num == 3 and roundtrip.time_sig_den == 4)


# ---------------------------------------------------------------------------
# 4. Tempo curve interpolation
# ---------------------------------------------------------------------------
print("\nSong.tempo_at_beat interpolation:")
song = Song(title="curve test", bpm=120)
song.tempo_curve = [(0.0, 60.0), (16.0, 120.0), (32.0, 80.0)]

check("at beat 0 → 60 BPM", abs(song.tempo_at_beat(0.0) - 60.0) < 0.01)
check("at beat 16 → 120 BPM", abs(song.tempo_at_beat(16.0) - 120.0) < 0.01)
check("at beat 8 → linearly interpolated to 90 BPM",
      abs(song.tempo_at_beat(8.0) - 90.0) < 0.01,
      f"got {song.tempo_at_beat(8.0):.2f}")
check("at beat 24 → halfway between 120 and 80 = 100",
      abs(song.tempo_at_beat(24.0) - 100.0) < 0.01,
      f"got {song.tempo_at_beat(24.0):.2f}")
check("before first keyframe → first keyframe value",
      abs(song.tempo_at_beat(-5.0) - 60.0) < 0.01)
check("after last keyframe → last keyframe value",
      abs(song.tempo_at_beat(99.0) - 80.0) < 0.01)
check("no curve → song.bpm",
      abs(Song(bpm=140).tempo_at_beat(10.0) - 140.0) < 0.01)


# ---------------------------------------------------------------------------
# 5. End-to-end: tempo curve actually changes audio length
# ---------------------------------------------------------------------------
print("\nrender_song honours tempo curve at pattern boundaries:")
fast_pat = Pattern(num_steps=16, num_channels=1, bpm=120, steps_per_beat=4)
fast_pat.set_note(0, 0, NoteEvent(midi_note=60, velocity=0.7,
                                    duration_steps=4, instrument="sine"))
slow_pat = Pattern(num_steps=16, num_channels=1, bpm=120, steps_per_beat=4)
slow_pat.set_note(0, 0, NoteEvent(midi_note=64, velocity=0.7,
                                    duration_steps=4, instrument="sine"))

base_song = Song(title="no curve", bpm=120)
base_song.patterns = [fast_pat, slow_pat]
base_song.sequence = [0, 1]

curve_song = Song(title="with curve", bpm=120)
curve_song.patterns = [
    Pattern(num_steps=16, num_channels=1, bpm=120, steps_per_beat=4,
            grid=[[NoteEvent(midi_note=60, velocity=0.7, duration_steps=4,
                              instrument="sine")] + [None] * 15]),
    Pattern(num_steps=16, num_channels=1, bpm=120, steps_per_beat=4,
            grid=[[NoteEvent(midi_note=64, velocity=0.7, duration_steps=4,
                              instrument="sine")] + [None] * 15]),
]
curve_song.sequence = [0, 1]
# First pattern at 60 BPM (slower → longer), second at 240 BPM (faster → shorter).
# Pattern starts at beats 0 and 4, so curve [(0, 60), (4, 240)] gives those bpms.
curve_song.tempo_curve = [(0.0, 60.0), (4.0, 240.0)]

audio_base = render_song(base_song, instruments=INSTS)
audio_curve = render_song(curve_song, instruments=INSTS)
check("base render has nonzero length", len(audio_base) > 0)
check("curve render has nonzero length", len(audio_curve) > 0)
# Both renders should have different lengths because tempo changes the
# step duration, which changes the pattern duration.
check("tempo curve changes total duration",
      len(audio_curve) != len(audio_base),
      f"base = {len(audio_base)}, curve = {len(audio_curve)}")


# ---------------------------------------------------------------------------
# 6. Song.to_dict / from_dict round-trip preserves all expressive metadata
# ---------------------------------------------------------------------------
print("\nSong serialization preserves panning, FX, tempo curve, articulation:")
src_song = Song(title="round", author="test", bpm=110)
src_song.panning = {0: -0.3, 1: 0.5}
src_song.channel_effects = {0: {"reverb": 0.2}}
src_song.master_reverb = 0.15
src_song.master_delay = 0.2
src_song.tempo_curve = [(0, 110), (8, 90)]
p = Pattern(num_steps=4, num_channels=1, bpm=110, steps_per_beat=4,
            time_sig_num=3, time_sig_den=4, temperament="just", key_root_pc=2)
p.set_note(0, 0, NoteEvent(midi_note=62, velocity=0.7, duration_steps=2,
                            instrument="sine", articulation="staccato",
                            glide_ms=80.0))
src_song.patterns = [p]
src_song.sequence = [0]

dump = src_song.to_dict()
restored = Song.from_dict(dump)
check("panning preserved",
      restored.panning.get(0) == -0.3 and restored.panning.get(1) == 0.5)
check("channel_effects preserved",
      restored.channel_effects.get(0, {}).get("reverb") == 0.2)
check("master_reverb preserved", restored.master_reverb == 0.15)
check("tempo_curve preserved", restored.tempo_curve == [(0, 110), (8, 90)])
check("pattern temperament preserved", restored.patterns[0].temperament == "just")
check("pattern key_root_pc preserved", restored.patterns[0].key_root_pc == 2)
check("pattern time signature preserved",
      restored.patterns[0].time_sig_num == 3 and
      restored.patterns[0].time_sig_den == 4)
ev = restored.patterns[0].grid[0][0]
check("note articulation preserved", ev.articulation == "staccato")
check("note glide_ms preserved", ev.glide_ms == 80.0)


# ---------------------------------------------------------------------------
# 7. Backwards compat — bare NoteEvent still works
# ---------------------------------------------------------------------------
print("\nBackwards compat — minimal NoteEvent still renders:")
plain_pat = Pattern(num_steps=4, num_channels=1, bpm=120, steps_per_beat=4)
plain_pat.set_note(0, 0, NoteEvent(midi_note=60, velocity=0.7,
                                     duration_steps=2, instrument="sine"))
plain_audio = render_pattern(plain_pat, instruments=INSTS)
check("plain note renders without crash", np.all(np.isfinite(plain_audio)))


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
print("All expressive sequencer tests passed.")
sys.exit(0)
