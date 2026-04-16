"""
Chopin — Prelude in E Minor, Op. 28 No. 4 (Largo)

The "espressivo" prelude. A descending chromatic chord progression in
the left hand under a stark, slow-moving melody. Famous for its
desolate, almost funereal character — Chopin asked for it to be
played at his funeral.

This rendering uses:
  - piano_grand preset (the headline preset of the orchestral PR)
  - equal temperament in E minor
  - dramatic Song.dynamics_curve sweeping from pianissimo to forte and
    back to ppp — the entire emotional arc of the prelude in dB space
  - tempo curve (rubato) — slow at the opening, slight push through the
    climax, broad ritardando into the final chord
  - tenuto + fermata articulation on key notes for held expressivity

Score: hand-arranged from Henle Verlag urtext (Op. 28 No. 4, m. 1-25,
abridged to 16 phrase groups).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav


# ---------------------------------------------------------------------------
# Left hand — descending chromatic chord progression
# 16 chords, each held for one bar of 8 sixteenths (so the bar feels broad
# at largo). Each chord is [bass, mid1, mid2] in MIDI.
# ---------------------------------------------------------------------------
LH_CHORDS: list[list[int]] = [
    [40, 59, 64],  # bar 1   E minor          E2 / B3 E4
    [40, 59, 64],  # bar 2   E minor (sus)
    [40, 59, 63],  # bar 3   E minor7         E2 / B3 D#4
    [40, 58, 63],  # bar 4   E half-dim
    [40, 57, 62],  # bar 5
    [40, 57, 62],  # bar 6
    [40, 57, 61],  # bar 7
    [40, 56, 61],  # bar 8
    [40, 56, 60],  # bar 9
    [40, 55, 60],  # bar 10
    [40, 55, 59],  # bar 11
    [40, 54, 59],  # bar 12
    [40, 54, 59],  # bar 13
    [38, 54, 57],  # bar 14  V7 of i (B7)
    [38, 53, 57],  # bar 15
    [40, 52, 59],  # bar 16  back to i
]

# ---------------------------------------------------------------------------
# Right hand — sparse melodic line. Each entry is (start_step, midi, dur, artic)
# Many bars are just held single notes — that's the prelude's character.
# ---------------------------------------------------------------------------
RH: list[list[tuple[int, int, int, str]]] = [
    [(0, 71, 16, "tenuto")],                            # bar 1  B4 held
    [(0, 71, 16, "tenuto")],                            # bar 2
    [(0, 71, 16, "tenuto")],                            # bar 3
    [(0, 70, 16, "tenuto")],                            # bar 4  Bb4 (chromatic descent)
    [(0, 69, 16, "tenuto")],                            # bar 5  A4
    [(0, 69, 16, "tenuto")],                            # bar 6
    [(0, 69, 8, "normal"), (8, 71, 8, "tenuto")],       # bar 7
    [(0, 70, 16, "tenuto")],                            # bar 8
    [(0, 71, 16, "tenuto")],                            # bar 9
    [(0, 72, 16, "tenuto")],                            # bar 10  C5
    [(0, 71, 8, "normal"), (8, 70, 8, "normal")],       # bar 11
    [(0, 69, 16, "tenuto")],                            # bar 12
    [(0, 71, 8, "accent"), (8, 72, 8, "accent")],       # bar 13  the climax
    [(0, 74, 8, "marcato"), (8, 71, 8, "tenuto")],      # bar 14  D5 marcato
    [(0, 70, 16, "tenuto")],                            # bar 15
    [(0, 67, 16, "fermata")],                           # bar 16  G4 fermata final
]


def make_bar(bar_idx: int) -> Pattern:
    pat = Pattern(
        name=f"bar{bar_idx + 1}",
        num_steps=16,
        num_channels=2,           # ch0 RH, ch1 LH
        bpm=44,                   # very slow largo
        steps_per_beat=4,
        temperament="equal",
        key_root_pc=4,            # E minor
        time_sig_num=2,
        time_sig_den=2,
    )

    # Right hand — melody
    for step, midi, dur, artic in RH[bar_idx]:
        pat.set_note(0, step, NoteEvent(
            midi_note=midi, velocity=0.62,
            duration_steps=dur, instrument="piano_grand", articulation=artic,
        ))

    # Left hand — chord struck on beat 1, sustained, with subtle re-strikes
    bass, m1, m2 = LH_CHORDS[bar_idx]
    # Bass note rings the full bar
    pat.set_note(1, 0, NoteEvent(
        midi_note=bass, velocity=0.55,
        duration_steps=16, instrument="piano_grand", articulation="tenuto",
    ))
    # Inner voices — re-strike at the half bar to keep the chord present
    pat.set_note(1, 0, NoteEvent(
        midi_note=m1, velocity=0.42,
        duration_steps=8, instrument="piano_grand",
    ))
    pat.set_note(1, 8, NoteEvent(
        midi_note=m2, velocity=0.42,
        duration_steps=8, instrument="piano_grand",
    ))

    return pat


def build_song() -> Song:
    song = Song(
        title="Chopin — Prelude in E Minor, Op. 28 No. 4 (Largo)",
        author="Frédéric Chopin (rendered by ChipForge)",
        bpm=44,
    )

    song.panning = {0: -0.05, 1: +0.05}  # gentle stereo separation across the hands

    # Piano in a recital hall — moderate reverb, never washy
    song.channel_effects = {
        0: {"reverb": 0.32, "reverb_damping": 0.55, "reverb_mix": 0.26},
        1: {"reverb": 0.30, "reverb_damping": 0.55, "reverb_mix": 0.24},
    }
    song.master_reverb = 0.18
    song.master_delay = 0.0

    # Rubato tempo curve — slight relaxation at the start, push through the
    # climax (bars 12-14), broad ritardando into the final fermata.
    # Beat indices: 16 bars, 4 beats each = 64 beats total.
    song.tempo_curve = [
        (0.0,   42.0),     # opening: slightly slower than written
        (24.0,  46.0),     # middle: subtle push
        (48.0,  50.0),     # climax: forward motion
        (56.0,  40.0),     # ritardando into the final cadence
        (64.0,  32.0),     # broad fermata
    ]

    # Dynamics curve — Chopin's espressivo arc:
    # ppp opening, gradual swell to forte at the climax (bar 13-14),
    # then a long ppp diminuendo into silence.
    song.dynamics_curve = [
        (0.0,  -16.0),    # ppp
        (16.0, -10.0),    # piano
        (32.0,  -5.0),    # mezzo-piano
        (48.0,  +1.0),    # forte climax
        (56.0,  -8.0),    # piano subito
        (64.0, -20.0),    # ppppp final
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
    out = Path("output/chopin_prelude_e_minor.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print("Solo piano (piano_grand), 16 bars, rubato + dynamics curves active")
