#!/usr/bin/env python3
"""
ChipForge Demo
==============
Builds a complete GB-style chip tune in C minor pentatonic at 140 BPM,
exports the audio to output/demo.wav, and optionally plays it back.

Run:
    python demo.py

Requires:
    pip install -r requirements.txt
    (sounddevice optional — skipped gracefully if not installed)
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── make sure src/ is importable ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    Song, Pattern, NoteEvent,
    PRESETS, SCALES,
    render_song,
    export_wav, save_song,
)

try:
    from src.mixer import play_audio
    from src.synth import SAMPLE_RATE
except ImportError:
    play_audio = None
    SAMPLE_RATE = 44100

OUTPUT_DIR = Path("output")
SONGS_DIR = Path("songs")
OUTPUT_DIR.mkdir(exist_ok=True)
SONGS_DIR.mkdir(exist_ok=True)

# ── Song parameters ───────────────────────────────────────────────────────────
BPM = 140
STEPS = 16  # 16th-note grid — one bar at 4/4

# C minor pentatonic:  C  Eb  F  G  Bb
# Root C5 = MIDI 72, relative to octave 4 (C4 = MIDI 60)
#
# Octave 5 melody notes:
#   C5  = 72
#   Eb5 = 75
#   F5  = 77
#   G5  = 79
#   Bb5 = 82
#
# Octave 4 bass notes:
#   C4  = 60
#   Eb4 = 63
#   F4  = 65
#   G4  = 67
#   Bb4 = 70

R = 0   # Rest shorthand


def make_pattern_a(bpm: float) -> Pattern:
    """
    Pattern A — main groove.
    
    Ch 0  pulse_lead 25%  — lead melody
    Ch 1  pulse_bass 50%  — bass line
    Ch 2  noise_hat       — eight-note hi-hats
    Ch 3  noise_kick      — kick on beats 1 & 3
    Ch 4  noise_snare     — snare on beats 2 & 4
    """
    pattern = Pattern(name="Pattern A", num_steps=STEPS, num_channels=5, bpm=bpm)

    # Lead: bouncy C pentatonic line with rests for breathing
    lead = [72, R,  75, R,  77, 79, 77, R,  75, 72, R,  75, 77, R,  R,  R ]
    for step, note in enumerate(lead):
        if note:
            pattern.set_note(0, step, NoteEvent(note, velocity=0.80, duration_steps=1, instrument="pulse_chime"))

    # Bass: root + 5th movement
    bass = [60, R,  R,  R,  60, R,  R,  R,  63, R,  R,  R,  65, R,  R,  R ]
    for step, note in enumerate(bass):
        if note:
            pattern.set_note(1, step, NoteEvent(note, velocity=0.85, duration_steps=2, instrument="pulse_bass"))

    # Hi-hat: every other step (8th notes)
    for step in range(0, STEPS, 2):
        pattern.set_note(2, step, NoteEvent(60, velocity=0.55, duration_steps=1, instrument="noise_hat"))

    # Kick: beats 1 and 3 (steps 0 and 8)
    for step in [0, 8]:
        pattern.set_note(3, step, NoteEvent(60, velocity=0.90, duration_steps=1, instrument="noise_kick"))

    # Snare: beats 2 and 4 (steps 4 and 12)
    for step in [4, 12]:
        pattern.set_note(4, step, NoteEvent(60, velocity=0.75, duration_steps=1, instrument="noise_snare"))

    return pattern


def make_pattern_b(bpm: float) -> Pattern:
    """
    Pattern B — variation using the wave channel for a softer melodic feel.
    Same rhythm section, different harmony up top.
    """
    pattern = Pattern(name="Pattern B", num_steps=STEPS, num_channels=5, bpm=bpm)

    # Wave melody — descending then ascending
    lead = [82, R,  79, R,  77, R,  75, R,  72, R,  75, 77, 79, R,  R,  R ]
    for step, note in enumerate(lead):
        if note:
            pattern.set_note(0, step, NoteEvent(note, velocity=0.75, duration_steps=1, instrument="wave_melody"))

    # Bass: walks down from G to C
    bass = [67, R,  R,  R,  65, R,  R,  R,  63, R,  R,  R,  60, R,  R,  R ]
    for step, note in enumerate(bass):
        if note:
            pattern.set_note(1, step, NoteEvent(note, velocity=0.80, duration_steps=2, instrument="wave_bass"))

    # Hi-hat: every step (16th notes — denser)
    for step in range(STEPS):
        vel = 0.45 if step % 2 else 0.60
        pattern.set_note(2, step, NoteEvent(60, velocity=vel, duration_steps=1, instrument="noise_hat"))

    # Kick
    for step in [0, 6, 8, 14]:
        pattern.set_note(3, step, NoteEvent(60, velocity=0.88, duration_steps=1, instrument="noise_kick"))

    # Snare
    for step in [4, 12]:
        pattern.set_note(4, step, NoteEvent(60, velocity=0.72, duration_steps=1, instrument="noise_snare"))

    return pattern


def build_demo_song() -> Song:
    song = Song(title="ChipForge Demo", bpm=BPM, author="ChipForge")

    pattern_a = make_pattern_a(BPM)
    pattern_b = make_pattern_b(BPM)

    song.patterns.append(pattern_a)   # index 0: Pattern A
    song.patterns.append(pattern_b)   # index 1: Pattern B

    # Arrangement:  A  A  B  A  A
    song.sequence = [0, 0, 1, 0, 0]

    return song


def main() -> None:
    print("ChipForge Demo")
    print("=" * 50)
    print(f"  BPM:   {BPM}")
    print(f"  Steps: {STEPS} per pattern")
    print(f"  Key:   C minor pentatonic")

    song = build_demo_song()
    total_dur = song.total_duration_sec()
    print(f"  Arrangement: A A B A A  ({total_dur:.1f}s, {total_dur / 60:.1f} min)")

    # ── Render ──────────────────────────────────────────────────────────────
    print("\nRendering audio … ", end="", flush=True)
    audio = render_song(song)
    print("done.")

    wav_path = OUTPUT_DIR / "demo.wav"
    export_wav(audio, wav_path)
    print(f"  WAV saved → {wav_path}")

    json_path = SONGS_DIR / "demo.chipforge.json"
    save_song(song, json_path)
    print(f"  Song saved → {json_path}")

    # ── Playback (optional) ─────────────────────────────────────────────────
    print("\nAttempting playback … ", end="", flush=True)
    try:
        if play_audio:
            play_audio(audio, SAMPLE_RATE)
            print("done.")
        else:
            print("skipped (play_audio not available).")
    except Exception as exc:  # noqa: BLE001
        print(f"skipped ({exc}).")
        print(f"  You can play the WAV manually: open {wav_path.resolve()}")

    print("\nDone.  Start the agent API with:")
    print("  uvicorn api.main:app --reload --port 8765")
    print("  then open http://localhost:8765/docs")


if __name__ == "__main__":
    main()
