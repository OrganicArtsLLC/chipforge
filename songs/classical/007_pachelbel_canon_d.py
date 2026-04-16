"""
Pachelbel — Canon in D Major (Kanon und Gigue für 3 Violinen und Basso Continuo)

The most famous ground bass in Western music. A repeating 8-note pattern
in the cello supports a 3-voice canon entering at 2-bar intervals.

This rendering uses:
  - String quartet built from the new orchestral presets
    (violin / viola / cello / contrabass)
  - 5-limit just intonation in D major — pure 3:2 fifths and 5:4 thirds
    in the violin lines, the kind of bell-clear consonance you only get
    in tunings where intervals are integer ratios
  - Articulation: tenuto on the bass for held foundation, normal on
    the melodic voices
  - Long natural reverb (cathedral acoustic) on every channel

The 8-bar ground (D - A - Bm - F#m - G - D - G - A) repeats four times
in the score below, giving 32 bars (~80 seconds at 60 BPM).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav


# ---------------------------------------------------------------------------
# The eight chords of the ground bass cycle (D major)
# Each is (bass MIDI, chord-tone MIDI list for the inner voices)
# ---------------------------------------------------------------------------
GROUND = [
    (38, [50, 54, 57]),  # D  major     D2 / D3 F#3 A3
    (33, [49, 52, 57]),  # A  major     A1 / C#3 E3 A3
    (35, [50, 54, 59]),  # B  minor     B1 / D3 F#3 B3
    (30, [49, 54, 57]),  # F# minor     F#1 / C#3 F#3 A3
    (31, [50, 55, 59]),  # G  major     G1 / D3 G3 B3
    (38, [50, 54, 57]),  # D  major     D2 / D3 F#3 A3
    (31, [50, 55, 59]),  # G  major     G1 / D3 G3 B3
    (33, [49, 52, 57]),  # A  major     A1 / C#3 E3 A3
]


# ---------------------------------------------------------------------------
# Violin 1 melody — 32 bars of the iconic descending canon line
# Each entry is (midi_note, duration_steps). 16 steps per bar (4/4).
# Uses 4 quarter notes per bar most of the time, with eighth-note
# ornaments on the famous descending passages.
# ---------------------------------------------------------------------------
V1_MELODY: list[list[tuple[int, int]]] = [
    # Bars 1-8: simple half-note theme (entry 1)
    [(74, 8), (72, 8)],                                 # F#4 - E4    (bar 1: D)
    [(69, 8), (76, 8)],                                 # A4  - E5    (bar 2: A)
    [(74, 8), (78, 8)],                                 # F#4 - F#5   (bar 3: Bm)
    [(73, 8), (74, 8)],                                 # C#5 - D5    (bar 4: F#m)
    [(71, 8), (74, 8)],                                 # B4  - D5    (bar 5: G)
    [(69, 8), (66, 8)],                                 # A4  - F#4   (bar 6: D)
    [(67, 8), (71, 8)],                                 # G4  - B4    (bar 7: G)
    [(69, 16)],                                          # A4 (whole)  (bar 8: A)

    # Bars 9-16: quarter-note variation
    [(74, 4), (76, 4), (78, 4), (74, 4)],               # bar 9  D
    [(73, 4), (74, 4), (76, 4), (73, 4)],               # bar 10 A
    [(74, 4), (76, 4), (78, 4), (74, 4)],               # bar 11 Bm
    [(73, 4), (71, 4), (69, 4), (66, 4)],               # bar 12 F#m
    [(71, 4), (74, 4), (71, 4), (74, 4)],               # bar 13 G
    [(69, 4), (66, 4), (69, 4), (74, 4)],               # bar 14 D
    [(71, 4), (74, 4), (71, 4), (67, 4)],               # bar 15 G
    [(69, 4), (73, 4), (76, 4), (78, 16)],              # bar 16 A — (last note rings into bar 17 cycle restart)

    # Bars 17-24: eighth-note descending figure (the famous one)
    [(81, 2), (78, 2), (74, 2), (78, 2),
     (81, 2), (74, 2), (78, 2), (74, 2)],               # bar 17 D
    [(76, 2), (74, 2), (73, 2), (71, 2),
     (76, 2), (78, 2), (76, 2), (74, 2)],               # bar 18 A
    [(78, 2), (76, 2), (74, 2), (73, 2),
     (74, 2), (76, 2), (78, 2), (74, 2)],               # bar 19 Bm
    [(73, 2), (71, 2), (69, 2), (66, 2),
     (69, 2), (71, 2), (69, 2), (66, 2)],               # bar 20 F#m
    [(67, 2), (71, 2), (74, 2), (71, 2),
     (67, 2), (71, 2), (74, 2), (76, 2)],               # bar 21 G
    [(78, 2), (74, 2), (78, 2), (74, 2),
     (76, 2), (74, 2), (73, 2), (71, 2)],               # bar 22 D
    [(67, 2), (71, 2), (74, 2), (71, 2),
     (67, 2), (71, 2), (74, 2), (78, 2)],               # bar 23 G
    [(76, 4), (73, 4), (76, 4), (74, 4)],               # bar 24 A

    # Bars 25-32: lyrical recapitulation
    [(74, 8), (78, 8)],                                 # bar 25 D
    [(76, 8), (74, 8)],                                 # bar 26 A
    [(78, 8), (74, 8)],                                 # bar 27 Bm
    [(73, 8), (74, 8)],                                 # bar 28 F#m
    [(71, 8), (74, 8)],                                 # bar 29 G
    [(69, 8), (66, 8)],                                 # bar 30 D
    [(67, 8), (71, 8)],                                 # bar 31 G
    [(73, 16)],                                          # bar 32 A — final
]


def fill_bar(pat: Pattern, channel: int, instrument: str, notes: list[tuple[int, int]],
             velocity: float, articulation: str = "normal") -> None:
    """Place a sequence of (midi, duration_steps) notes starting at step 0."""
    cursor = 0
    for midi, dur in notes:
        if cursor >= 16:
            break
        pat.set_note(channel, cursor, NoteEvent(
            midi_note=midi, velocity=velocity,
            duration_steps=min(dur, 16 - cursor),
            instrument=instrument, articulation=articulation,
        ))
        cursor += dur


def make_bar(bar_idx: int) -> Pattern:
    """Build one bar of the Canon. bar_idx is 0-based (0..31)."""
    chord_idx = bar_idx % 8
    bass_midi, inner_notes = GROUND[chord_idx]

    pat = Pattern(
        name=f"bar{bar_idx + 1}",
        num_steps=16,
        num_channels=4,           # ch0 violin1, ch1 viola, ch2 cello, ch3 contrabass
        bpm=60,                   # canonical "tranquillo" tempo
        steps_per_beat=4,
        temperament="just",
        key_root_pc=2,            # D major
        time_sig_num=4,
        time_sig_den=4,
    )

    # Violin 1 — primary melodic voice. Enters at bar 3 (idx 2).
    if bar_idx >= 2:
        v1_idx = bar_idx - 2
        if 0 <= v1_idx < len(V1_MELODY):
            fill_bar(pat, 0, "violin", V1_MELODY[v1_idx], velocity=0.72)

    # Viola — inner voice arpeggio across the chord tones
    inner_pattern = [
        (inner_notes[0], 4),
        (inner_notes[1], 4),
        (inner_notes[2], 4),
        (inner_notes[1], 4),
    ]
    fill_bar(pat, 1, "viola", inner_pattern, velocity=0.55)

    # Cello — ground bass: half note on the chord root, then a passing tone
    cello_seq = [(bass_midi + 12, 8), (bass_midi + 12, 8)]
    fill_bar(pat, 2, "cello", cello_seq, velocity=0.65, articulation="tenuto")

    # Contrabass — true ground (octave below cello), held for the full bar
    pat.set_note(3, 0, NoteEvent(
        midi_note=bass_midi, velocity=0.62,
        duration_steps=16, instrument="contrabass",
        articulation="tenuto",
    ))

    return pat


def build_song() -> Song:
    song = Song(
        title="Pachelbel — Canon in D Major (32 bars)",
        author="Johann Pachelbel (rendered by ChipForge)",
        bpm=60,
    )

    # String quartet panning — wide stage
    song.panning = {
        0: -0.20,   # violin 1   (slight left)
        1: +0.10,   # viola      (slight right)
        2: +0.25,   # cello      (right)
        3: -0.05,   # contrabass (centre)
    }

    # Cathedral acoustic — deep reverb on every voice
    song.channel_effects = {
        0: {"reverb": 0.42, "reverb_damping": 0.45, "reverb_mix": 0.32},
        1: {"reverb": 0.40, "reverb_damping": 0.50, "reverb_mix": 0.30},
        2: {"reverb": 0.38, "reverb_damping": 0.55, "reverb_mix": 0.28},
        3: {"reverb": 0.35, "reverb_damping": 0.60, "reverb_mix": 0.25},
    }
    song.master_reverb = 0.20
    song.master_delay = 0.0

    # Classic Canon dynamics: very quiet entry, swell to fortissimo at the
    # eighth-note climax (bars 17-24), then ease back for the recap.
    song.dynamics_curve = [
        (0.0,   -10.0),    # tutti enters very quietly
        (16.0,  -4.0),     # bar 5 — violin 1 enters
        (64.0,  +0.0),     # bar 17 — fortissimo at the eighth-note climax
        (96.0,  -2.0),     # bar 25 — slight ease for the recap
        (128.0, -6.0),     # bar 33 — final taper
    ]

    for i in range(32):
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
    out = Path("output/pachelbel_canon_d.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print(f"Patterns: {len(song.patterns)} (32 bars), Tuning: just intonation in D")
