"""
Debussy — Clair de Lune (Suite bergamasque, III), opening section

The most famous piano piece of the Impressionist era. The opening 16
bars of Clair de Lune — a slow, dreamlike Db major melody hovering
above gently rolling left-hand chords.

This rendering uses:
  - piano_grand preset for both hands
  - equal temperament in Db major (the original key — bracingly hard
    to play, hauntingly beautiful)
  - dramatic rubato via Song.tempo_curve
  - Song.dynamics_curve for the long pianissimo arch (ppp ─→ pp ─→ ppp)
  - extensive use of tenuto + fermata articulation for the held melody

This is an abridged transcription of the opening melodic phrases (m. 1-16
of the Henle urtext, simplified to a single rolling left-hand pattern).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav


# ---------------------------------------------------------------------------
# Right hand — the famous Db major melody
# Db = MIDI 61. The melody hovers around F4-Ab4-Bb4 (high register).
# Each entry: (start_step, midi, dur_steps, articulation)
# 16 steps per bar, 9/8 time written but we render it as 12 steps per bar
# (4-beat dotted half feel).
# ---------------------------------------------------------------------------
RH_PHRASES: list[list[tuple[int, int, int, str]]] = [
    # bar 1 — opening: F4 - Ab4 - Bb4 (the 3-note motive)
    [(0, 65, 4, "tenuto"), (4, 68, 4, "tenuto"),
     (8, 70, 8, "tenuto")],
    # bar 2 — Ab4 - Db5 - Eb5 (rises)
    [(0, 68, 4, "tenuto"), (4, 73, 4, "tenuto"),
     (8, 75, 8, "tenuto")],
    # bar 3 — Db5 sustained
    [(0, 73, 16, "tenuto")],
    # bar 4 — F4 - Ab4 - Bb4 again (motive return)
    [(0, 65, 4, "tenuto"), (4, 68, 4, "tenuto"),
     (8, 70, 8, "tenuto")],
    # bar 5 — descending: F5 - Eb5 - Db5
    [(0, 77, 4, "normal"), (4, 75, 4, "normal"),
     (8, 73, 8, "tenuto")],
    # bar 6 — Bb4 - Ab4 - F4 (continued descent)
    [(0, 70, 4, "normal"), (4, 68, 4, "normal"),
     (8, 65, 8, "tenuto")],
    # bar 7 — F4 - Eb4 - Db4
    [(0, 65, 4, "normal"), (4, 63, 4, "normal"),
     (8, 61, 8, "tenuto")],
    # bar 8 — Db4 sustained (cadence)
    [(0, 61, 16, "fermata")],

    # bars 9-12: variation of the opening, slightly higher
    [(0, 68, 4, "tenuto"), (4, 70, 4, "tenuto"),
     (8, 73, 8, "tenuto")],
    [(0, 70, 4, "tenuto"), (4, 73, 4, "tenuto"),
     (8, 75, 8, "tenuto")],
    [(0, 75, 16, "tenuto")],
    [(0, 73, 4, "normal"), (4, 70, 4, "normal"),
     (8, 68, 8, "tenuto")],

    # bars 13-16: closing recapitulation
    [(0, 68, 4, "normal"), (4, 65, 4, "normal"),
     (8, 63, 8, "tenuto")],
    [(0, 61, 4, "normal"), (4, 63, 4, "normal"),
     (8, 65, 8, "tenuto")],
    [(0, 68, 4, "tenuto"), (4, 65, 4, "tenuto"),
     (8, 61, 8, "tenuto")],
    [(0, 61, 16, "fermata")],
]

# ---------------------------------------------------------------------------
# Left hand — rolling chords. Db major broken triads in 3-note groups.
# Each bar plays an arpeggio across 12 sixteenth notes.
# Format per bar: list of (step, midi) tuples.
# ---------------------------------------------------------------------------
LH_BARS: list[list[tuple[int, int]]] = [
    # Db major: Db-F-Ab-Db-F-Ab-Db-F-Ab (broken)
    [(0, 49), (2, 53), (4, 56), (6, 49), (8, 53), (10, 56), (12, 49), (14, 53)],
    # Ab major: Ab-C-Eb pattern
    [(0, 44), (2, 48), (4, 51), (6, 44), (8, 48), (10, 51), (12, 44), (14, 48)],
    # Db major
    [(0, 49), (2, 53), (4, 56), (6, 49), (8, 53), (10, 56), (12, 49), (14, 53)],
    # Bbm (vi): Bb-Db-F
    [(0, 46), (2, 49), (4, 53), (6, 46), (8, 49), (10, 53), (12, 46), (14, 49)],
    # F major (V/V): F-A-C
    [(0, 41), (2, 45), (4, 48), (6, 41), (8, 45), (10, 48), (12, 41), (14, 45)],
    # Bbm
    [(0, 46), (2, 49), (4, 53), (6, 46), (8, 49), (10, 53), (12, 46), (14, 49)],
    # Eb minor (predominant)
    [(0, 39), (2, 42), (4, 46), (6, 39), (8, 42), (10, 46), (12, 39), (14, 42)],
    # Ab7 (V): Ab-C-Eb-Gb
    [(0, 44), (2, 48), (4, 51), (6, 54), (8, 44), (10, 48), (12, 51), (14, 54)],

    # bars 9-16 — variation
    [(0, 49), (2, 53), (4, 56), (6, 49), (8, 53), (10, 56), (12, 49), (14, 53)],
    [(0, 44), (2, 48), (4, 51), (6, 44), (8, 48), (10, 51), (12, 44), (14, 48)],
    [(0, 51), (2, 56), (4, 60), (6, 51), (8, 56), (10, 60), (12, 51), (14, 56)],
    [(0, 49), (2, 53), (4, 56), (6, 49), (8, 53), (10, 56), (12, 49), (14, 53)],
    [(0, 44), (2, 48), (4, 51), (6, 44), (8, 48), (10, 51), (12, 44), (14, 48)],
    [(0, 39), (2, 42), (4, 46), (6, 39), (8, 42), (10, 46), (12, 39), (14, 42)],
    [(0, 44), (2, 48), (4, 51), (6, 54), (8, 44), (10, 48), (12, 51), (14, 54)],
    [(0, 49), (2, 53), (4, 56), (6, 49), (8, 53), (10, 56), (12, 49), (14, 56)],
]


def make_bar(bar_idx: int) -> Pattern:
    pat = Pattern(
        name=f"bar{bar_idx + 1}",
        num_steps=16,
        num_channels=2,
        bpm=50,
        steps_per_beat=4,
        temperament="equal",
        key_root_pc=1,            # Db major (pitch class 1)
        time_sig_num=9,
        time_sig_den=8,
    )

    # Right hand
    for step, midi, dur, artic in RH_PHRASES[bar_idx]:
        pat.set_note(0, step, NoteEvent(
            midi_note=midi, velocity=0.55,
            duration_steps=dur, instrument="piano_grand", articulation=artic,
        ))

    # Left hand — broken chord arpeggio
    for step, midi in LH_BARS[bar_idx]:
        pat.set_note(1, step, NoteEvent(
            midi_note=midi, velocity=0.40,
            duration_steps=2, instrument="piano_grand",
        ))

    return pat


def build_song() -> Song:
    song = Song(
        title="Debussy — Clair de Lune (opening, m. 1-16)",
        author="Claude Debussy (rendered by ChipForge)",
        bpm=50,
    )

    song.panning = {0: -0.10, 1: +0.10}

    song.channel_effects = {
        0: {"reverb": 0.38, "reverb_damping": 0.50, "reverb_mix": 0.30},
        1: {"reverb": 0.36, "reverb_damping": 0.55, "reverb_mix": 0.28},
    }
    song.master_reverb = 0.22
    song.master_delay = 0.0

    # Long Impressionist rubato — gentle ebb and flow throughout
    song.tempo_curve = [
        (0.0,   46.0),    # opening: held back
        (16.0,  52.0),    # bar 5: gentle forward motion
        (32.0,  48.0),    # bar 9: settle
        (48.0,  54.0),    # bar 13: small swell
        (56.0,  44.0),    # ritardando into the final cadence
        (64.0,  38.0),    # broad final
    ]

    # Dynamics — pianississimo throughout, with one gentle swell mid-piece
    song.dynamics_curve = [
        (0.0,  -14.0),    # ppp
        (16.0,  -8.0),    # pp
        (32.0,  -4.0),    # mp swell
        (48.0,  -8.0),    # back to pp
        (64.0, -16.0),    # ppppp final
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
    out = Path("output/debussy_clair_de_lune.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print("Solo piano (piano_grand), 16 bars, Db major, rubato active")
