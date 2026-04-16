"""
Mozart — Eine kleine Nachtmusik, K. 525 (I. Allegro, opening 16 bars)

The opening "rocket" theme of Mozart's most famous string serenade. Two
violins drive the melody, viola plays the harmonic filler, cello +
contrabass anchor the bass with the iconic walking quarter notes.

This rendering uses:
  - Full string ensemble (violin x2, viola, cello, contrabass) from the
    new orchestral presets
  - Equal temperament (Mozart's late-classical tuning)
  - Marcato + accent articulation on the famous downward turn motif
  - 4/4 allegro at 132 BPM
  - Concert hall acoustic via per-channel reverb and master reverb
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav


# 16 steps per bar (4/4 with sixteenth-note grid)
STEPS_PER_BAR = 16


# ---------------------------------------------------------------------------
# Violin 1 — primary melody
# Each entry is (start_step, midi_note, duration_steps, articulation)
# Bars 1-4 = the famous "rocket" theme (G-D-G-D arpeggio in dotted rhythm)
# Bars 5-8 = downward turn / cadence
# Bars 9-12 = repeat the opening
# Bars 13-16 = closing cadence
# ---------------------------------------------------------------------------
V1: list[list[tuple[int, int, int, str]]] = [
    # bar 1 — G major rocket: G3 quarter, D4 quarter, G4 quarter, D4 eighth, B4 eighth
    [(0, 67, 4, "marcato"), (4, 74, 4, "marcato"),
     (8, 79, 4, "marcato"), (12, 74, 2, "normal"), (14, 83, 2, "accent")],
    # bar 2 — same shape, descending closing turn
    [(0, 79, 4, "normal"), (4, 78, 2, "normal"), (6, 79, 2, "normal"),
     (8, 81, 4, "normal"), (12, 79, 4, "normal")],
    # bar 3 — repeat rocket
    [(0, 67, 4, "marcato"), (4, 74, 4, "marcato"),
     (8, 79, 4, "marcato"), (12, 74, 2, "normal"), (14, 83, 2, "accent")],
    # bar 4 — closing turn
    [(0, 79, 4, "normal"), (4, 78, 2, "normal"), (6, 79, 2, "normal"),
     (8, 81, 4, "normal"), (12, 79, 4, "normal")],

    # bar 5 — downward fanfare
    [(0, 79, 2, "accent"), (2, 78, 2, "normal"), (4, 79, 4, "normal"),
     (8, 78, 2, "accent"), (10, 79, 2, "normal"), (12, 81, 4, "normal")],
    # bar 6 — descending scale
    [(0, 83, 2, "normal"), (2, 81, 2, "normal"), (4, 79, 2, "normal"),
     (6, 78, 2, "normal"), (8, 79, 4, "normal"), (12, 74, 4, "normal")],
    # bar 7 — repeat the descending phrase, slightly varied
    [(0, 83, 2, "normal"), (2, 81, 2, "normal"), (4, 79, 2, "normal"),
     (6, 78, 2, "normal"), (8, 76, 4, "normal"), (12, 74, 4, "normal")],
    # bar 8 — half cadence
    [(0, 74, 4, "tenuto"), (4, 74, 4, "normal"),
     (8, 74, 8, "tenuto")],

    # bar 9 — repeat opening (rocket)
    [(0, 67, 4, "marcato"), (4, 74, 4, "marcato"),
     (8, 79, 4, "marcato"), (12, 74, 2, "normal"), (14, 83, 2, "accent")],
    # bar 10
    [(0, 79, 4, "normal"), (4, 78, 2, "normal"), (6, 79, 2, "normal"),
     (8, 81, 4, "normal"), (12, 79, 4, "normal")],
    # bar 11
    [(0, 67, 4, "marcato"), (4, 74, 4, "marcato"),
     (8, 79, 4, "marcato"), (12, 74, 2, "normal"), (14, 83, 2, "accent")],
    # bar 12
    [(0, 79, 4, "normal"), (4, 78, 2, "normal"), (6, 79, 2, "normal"),
     (8, 81, 4, "normal"), (12, 79, 4, "normal")],

    # bar 13 — final ascent
    [(0, 79, 2, "normal"), (2, 81, 2, "normal"), (4, 83, 2, "normal"),
     (6, 84, 2, "normal"), (8, 86, 4, "marcato"), (12, 83, 4, "normal")],
    # bar 14
    [(0, 81, 2, "normal"), (2, 79, 2, "normal"), (4, 78, 2, "normal"),
     (6, 79, 2, "normal"), (8, 81, 4, "normal"), (12, 78, 4, "normal")],
    # bar 15 — penultimate cadence
    [(0, 79, 2, "accent"), (2, 78, 2, "normal"), (4, 76, 2, "normal"),
     (6, 74, 2, "normal"), (8, 76, 4, "normal"), (12, 74, 4, "tenuto")],
    # bar 16 — final tonic
    [(0, 79, 16, "fermata")],
]

# ---------------------------------------------------------------------------
# Violin 2 — harmonic doubling (a third below V1 most of the time)
# We'll just play the same rhythm at a lower pitch.
# ---------------------------------------------------------------------------
V2: list[list[tuple[int, int, int, str]]] = [
    [(0, 62, 4, "marcato"), (4, 67, 4, "marcato"),
     (8, 71, 4, "marcato"), (12, 67, 2, "normal"), (14, 74, 2, "accent")],
    [(0, 71, 4, "normal"), (4, 71, 2, "normal"), (6, 71, 2, "normal"),
     (8, 74, 4, "normal"), (12, 71, 4, "normal")],
    [(0, 62, 4, "marcato"), (4, 67, 4, "marcato"),
     (8, 71, 4, "marcato"), (12, 67, 2, "normal"), (14, 74, 2, "accent")],
    [(0, 71, 4, "normal"), (4, 71, 2, "normal"), (6, 71, 2, "normal"),
     (8, 74, 4, "normal"), (12, 71, 4, "normal")],

    [(0, 71, 8, "normal"), (8, 71, 8, "normal")],
    [(0, 74, 8, "normal"), (8, 71, 4, "normal"), (12, 67, 4, "normal")],
    [(0, 74, 8, "normal"), (8, 71, 4, "normal"), (12, 67, 4, "normal")],
    [(0, 67, 4, "tenuto"), (4, 67, 4, "normal"), (8, 67, 8, "tenuto")],

    [(0, 62, 4, "marcato"), (4, 67, 4, "marcato"),
     (8, 71, 4, "marcato"), (12, 67, 2, "normal"), (14, 74, 2, "accent")],
    [(0, 71, 4, "normal"), (4, 71, 2, "normal"), (6, 71, 2, "normal"),
     (8, 74, 4, "normal"), (12, 71, 4, "normal")],
    [(0, 62, 4, "marcato"), (4, 67, 4, "marcato"),
     (8, 71, 4, "marcato"), (12, 67, 2, "normal"), (14, 74, 2, "accent")],
    [(0, 71, 4, "normal"), (4, 71, 2, "normal"), (6, 71, 2, "normal"),
     (8, 74, 4, "normal"), (12, 71, 4, "normal")],

    [(0, 74, 8, "normal"), (8, 76, 8, "normal")],
    [(0, 74, 8, "normal"), (8, 71, 8, "normal")],
    [(0, 71, 8, "normal"), (8, 67, 8, "normal")],
    [(0, 71, 16, "fermata")],
]

# ---------------------------------------------------------------------------
# Viola — held chord tones (one chord per bar)
# ---------------------------------------------------------------------------
VIOLA_NOTES: list[int] = [
    55, 55, 55, 55,    # G major
    62, 62, 62, 62,    # D major
    55, 55, 55, 55,
    62, 62, 55, 55,
]

# ---------------------------------------------------------------------------
# Cello + Contrabass — walking quarters, four per bar
# ---------------------------------------------------------------------------
BASS_LINE: list[list[int]] = [
    [43, 43, 43, 43],  # bar 1: G G G G
    [50, 50, 50, 50],  # bar 2: D D D D
    [43, 43, 43, 43],  # bar 3
    [50, 50, 50, 50],  # bar 4
    [50, 47, 50, 47],  # bar 5: D B D B
    [50, 47, 50, 50],  # bar 6
    [50, 47, 50, 50],  # bar 7
    [50, 50, 50, 50],  # bar 8
    [43, 43, 43, 43],  # bar 9
    [50, 50, 50, 50],  # bar 10
    [43, 43, 43, 43],  # bar 11
    [50, 50, 50, 50],  # bar 12
    [50, 47, 50, 47],  # bar 13
    [50, 47, 50, 47],  # bar 14
    [50, 47, 50, 50],  # bar 15
    [43, 43, 43, 43],  # bar 16
]


def add_voice(pat: Pattern, ch: int, instrument: str,
              events: list[tuple[int, int, int, str]],
              base_velocity: float) -> None:
    for step, midi, dur, artic in events:
        pat.set_note(ch, step, NoteEvent(
            midi_note=midi, velocity=base_velocity,
            duration_steps=dur, instrument=instrument, articulation=artic,
        ))


def make_bar(bar_idx: int) -> Pattern:
    pat = Pattern(
        name=f"bar{bar_idx + 1}",
        num_steps=STEPS_PER_BAR,
        num_channels=5,           # v1, v2, viola, cello, contrabass
        bpm=132,
        steps_per_beat=4,
        temperament="equal",
        key_root_pc=7,            # G major
        time_sig_num=4,
        time_sig_den=4,
    )

    add_voice(pat, 0, "violin", V1[bar_idx], base_velocity=0.72)
    add_voice(pat, 1, "violin", V2[bar_idx], base_velocity=0.62)

    # Viola: hold the chord tone for the full bar
    pat.set_note(2, 0, NoteEvent(
        midi_note=VIOLA_NOTES[bar_idx], velocity=0.50,
        duration_steps=STEPS_PER_BAR, instrument="viola",
        articulation="tenuto",
    ))

    # Cello: walking quarters
    for q, midi in enumerate(BASS_LINE[bar_idx]):
        pat.set_note(3, q * 4, NoteEvent(
            midi_note=midi + 12, velocity=0.62,
            duration_steps=4, instrument="cello", articulation="marcato",
        ))

    # Contrabass: same line, octave below
    for q, midi in enumerate(BASS_LINE[bar_idx]):
        pat.set_note(4, q * 4, NoteEvent(
            midi_note=midi, velocity=0.58,
            duration_steps=4, instrument="contrabass", articulation="marcato",
        ))

    return pat


def build_song() -> Song:
    song = Song(
        title="Mozart — Eine kleine Nachtmusik (K. 525, I. Allegro, m. 1-16)",
        author="W.A. Mozart (rendered by ChipForge)",
        bpm=132,
    )

    song.panning = {
        0: -0.30,   # violin 1   (left)
        1: -0.10,   # violin 2   (slight left)
        2: +0.15,   # viola      (slight right)
        3: +0.30,   # cello      (right)
        4: 0.00,    # contrabass (centre)
    }

    song.channel_effects = {
        0: {"reverb": 0.30, "reverb_damping": 0.45, "reverb_mix": 0.24},
        1: {"reverb": 0.30, "reverb_damping": 0.45, "reverb_mix": 0.24},
        2: {"reverb": 0.28, "reverb_damping": 0.50, "reverb_mix": 0.22},
        3: {"reverb": 0.25, "reverb_damping": 0.55, "reverb_mix": 0.18},
        4: {"reverb": 0.22, "reverb_damping": 0.60, "reverb_mix": 0.15},
    }
    song.master_reverb = 0.15
    song.master_delay = 0.0

    # Mozart classical dynamics — strong opening, lighter middle, robust ending
    song.dynamics_curve = [
        (0.0,  +0.0),
        (16.0, -3.0),
        (32.0, -1.0),
        (48.0, +0.0),
        (64.0, -2.0),
    ]

    for i in range(16):
        pat = make_bar(i)
        idx = len(song.patterns)
        song.patterns.append(pat)
        song.append_to_sequence(idx)

    return song


if __name__ == "__main__":
    song = build_song()
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )
    out = Path("output/mozart_eine_kleine.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print(f"String ensemble: 5 voices, 16 bars at 132 BPM allegro")
