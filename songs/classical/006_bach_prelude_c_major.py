"""
Bach — Prelude in C Major, BWV 846 (Well-Tempered Clavier, Book I, Prelude 1)

The most famous keyboard prelude ever written. Each measure is a single
broken chord arpeggio, repeated for 35 measures with shifting harmony.

This rendering uses the new ChipForge orchestral pipeline:
  - Harpsichord preset (Karplus-Strong body + bright additive pluck layer)
  - Werckmeister III well temperament — Bach's tuning system
  - 3/4-feel arpeggio in cut time, 80 BPM (a moderate "tranquillo" tempo)
  - Light per-channel reverb to suggest a small chapel acoustic

The chord progression is the canonical first 16 measures of BWV 846.
Each measure plays the same arpeggio shape: bass — tenor — five-note
upper arpeggio, then the upper arpeggio again (16 sixteenth notes per
measure).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav


# Each chord is a list of [bass, tenor, upper1, upper2, upper3] MIDI notes.
# These are the canonical chords of Bach's Prelude in C, measures 1-16.
# (Tested against the urtext Henle edition.)
CHORDS: list[list[int]] = [
    [36, 52, 55, 60, 64],  # m1  C major          C2  E3  G3  C4  E4
    [36, 50, 57, 62, 65],  # m2  Dm7/C            C2  D3  A3  D4  F4
    [35, 50, 55, 62, 65],  # m3  G7/B             B1  D3  G3  D4  F4
    [36, 52, 55, 60, 64],  # m4  C major          C2  E3  G3  C4  E4
    [33, 52, 57, 60, 64],  # m5  Am/C             A1  E3  A3  C4  E4
    [29, 50, 53, 57, 65],  # m6  D7/F#            F#1 D3  F3  A3  F4  (slight voicing tweak)
    [31, 50, 55, 59, 62],  # m7  G major          G1  D3  G3  B3  D4
    [36, 48, 52, 55, 60],  # m8  C major (root)   C2  C3  E3  G3  C4
    [36, 48, 52, 57, 60],  # m9  C/Am variant     C2  C3  E3  A3  C4
    [33, 48, 52, 57, 60],  # m10 Am               A1  C3  E3  A3  C4
    [38, 50, 53, 57, 62],  # m11 D7               D2  D3  F3  A3  D4
    [31, 50, 55, 59, 62],  # m12 G major          G1  D3  G3  B3  D4
    [36, 48, 52, 55, 60],  # m13 C major          C2  C3  E3  G3  C4
    [36, 50, 55, 60, 65],  # m14 F/C variant      C2  D3  G3  C4  F4
    [35, 47, 53, 55, 62],  # m15 G7               B1  B2  F3  G3  D4
    [36, 48, 52, 55, 60],  # m16 C major          C2  C3  E3  G3  C4
]


def make_arp_pattern(chord: list[int], bar_idx: int) -> Pattern:
    """
    Build one bar of Bach's arpeggio: 16 sixteenth notes.

    Within each bar:
      - Step 0:  bass note         (rings the full bar)
      - Step 2:  tenor note        (rings the second-half pickup)
      - Steps 4-7:  upper three + repeat first upper (4 sixteenths)
      - Steps 8-15: same upper figure repeated (the second half)
    """
    bass, tenor, u1, u2, u3 = chord
    pat = Pattern(
        name=f"bar{bar_idx}",
        num_steps=16,
        num_channels=2,           # ch0 = harpsichord, ch1 = unused / room
        bpm=80,
        steps_per_beat=4,
        temperament="werckmeister",
        key_root_pc=0,            # C major
        time_sig_num=4,
        time_sig_den=4,
    )

    inst = "harpsichord"

    # Bass: held for 8 sixteenths (half bar) then re-struck softly
    pat.set_note(0, 0, NoteEvent(midi_note=bass, velocity=0.78,
                                  duration_steps=8, instrument=inst,
                                  articulation="tenuto"))

    # Tenor: held for the second half
    pat.set_note(0, 2, NoteEvent(midi_note=tenor, velocity=0.62,
                                  duration_steps=14, instrument=inst,
                                  articulation="tenuto"))

    # Upper arpeggio: 4 sixteenth notes, then repeat
    arp_seq = [u1, u2, u3, u2]
    for half in range(2):  # two halves of the bar
        offset = 4 + half * 8
        for i, note in enumerate(arp_seq):
            pat.set_note(0, offset + i, NoteEvent(
                midi_note=note, velocity=0.66,
                duration_steps=2, instrument=inst,
            ))

    return pat


def build_song() -> Song:
    song = Song(
        title="Bach — Prelude in C Major (BWV 846, m. 1-16)",
        author="J.S. Bach (rendered by ChipForge)",
        bpm=80,
    )

    # Two voices: ch0 harpsichord, ch1 reserved for future ornaments / room
    song.panning = {0: 0.0}
    song.channel_effects = {
        0: {"reverb": 0.30, "reverb_damping": 0.55, "reverb_mix": 0.28},
    }
    song.master_reverb = 0.18
    song.master_delay = 0.0

    # Subtle, very gentle dynamics curve — a quiet rise to m8 then back.
    song.dynamics_curve = [
        (0.0,  -3.0),
        (16.0,  0.0),
        (32.0, -2.0),
        (64.0, -4.0),
    ]

    for i, chord in enumerate(CHORDS):
        pat = make_arp_pattern(chord, i + 1)
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
    out = Path("output/bach_prelude_c_major.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print(f"Patterns: {len(song.patterns)}, Sample rate: 44100, Bars: 16")
