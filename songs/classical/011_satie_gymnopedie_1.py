"""
Satie — Gymnopédie No. 1 (Lent et douloureux)

Erik Satie's first Gymnopédie, 1888. Quintessentially modernist:
3/4 time, sparse melody, gently swaying left-hand pattern. The most
recognizable piece of "ambient" music ever written.

This rendering uses:
  - piano_grand preset
  - equal temperament in D major
  - 3/4 time signature (Pattern.time_sig_num = 3)
  - 12 steps per bar (4 sixteenths × 3 beats)
  - Dynamics curve held very quiet — pp throughout, the piece never
    crescendos beyond mp
  - Light rubato — Satie's music breathes, but unlike Chopin it stays
    very steady. Just the smallest tempo nudges.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav


# ---------------------------------------------------------------------------
# Left hand — gently rolling 3/4 pattern: bass note on beat 1, chord on
# beat 2 and beat 3. The bass alternates between two notes per phrase.
# Each bar = 12 sixteenth steps (3 beats × 4 subdivisions).
# Format per bar: (bass_midi, chord_lo_midi, chord_hi_midi)
# ---------------------------------------------------------------------------
LH_BARS: list[tuple[int, int, int]] = [
    # bars 1-8: G2 → A2 alternation (modal G - A pattern)
    (43, 62, 66),    # G2 / Dm/F# → like a Gmaj7 root pos: G B D F#
    (45, 64, 68),    # A2 / chord on Em7 voicing
    (43, 62, 66),
    (45, 64, 68),
    (43, 62, 66),
    (45, 64, 68),
    (43, 62, 66),
    (45, 64, 68),

    # bars 9-16: down a step — F2 → G2
    (41, 60, 65),    # F2 / Fmaj9
    (43, 62, 66),    # G2
    (41, 60, 65),
    (43, 62, 66),
    (41, 60, 65),
    (43, 62, 66),
    (41, 60, 65),
    (43, 62, 66),

    # bars 17-24: back to opening
    (43, 62, 66),
    (45, 64, 68),
    (43, 62, 66),
    (45, 64, 68),
    (43, 62, 66),
    (45, 64, 68),
    (43, 62, 66),
    (45, 64, 68),
]

# ---------------------------------------------------------------------------
# Right hand — sparse melody. Most bars have one or two long notes.
# Format per bar: list of (start_step, midi, dur_steps)
# ---------------------------------------------------------------------------
RH_MELODY: list[list[tuple[int, int, int]]] = [
    # Bars 1-2: silence (the bass + chord plays alone)
    [], [],
    # Bars 3-8: the famous melody enters slowly
    [(0, 81, 4), (4, 78, 4), (8, 76, 4)],         # bar 3: A5 - F#5 - E5
    [(0, 74, 12)],                                 # bar 4: D5 (whole)
    [(0, 81, 4), (4, 78, 4), (8, 76, 4)],         # bar 5: A5 - F#5 - E5
    [(0, 74, 8), (8, 78, 4)],                      # bar 6: D5 → F#5
    [(0, 79, 4), (4, 78, 4), (8, 76, 4)],         # bar 7: G5 - F#5 - E5
    [(0, 74, 12)],                                 # bar 8: D5 fermata feel

    # bars 9-12: contrasting phrase, descending
    [(0, 78, 4), (4, 76, 4), (8, 74, 4)],         # bar 9
    [(0, 72, 12)],                                 # bar 10: C5
    [(0, 76, 4), (4, 74, 4), (8, 72, 4)],         # bar 11
    [(0, 71, 12)],                                 # bar 12: B4

    # bars 13-16: continued
    [(0, 74, 4), (4, 76, 4), (8, 78, 4)],         # bar 13: ascending response
    [(0, 79, 12)],                                 # bar 14
    [(0, 78, 4), (4, 76, 4), (8, 74, 4)],         # bar 15
    [(0, 72, 12)],                                 # bar 16

    # bars 17-22: melody returns, like an A' section
    [(0, 81, 4), (4, 78, 4), (8, 76, 4)],
    [(0, 74, 12)],
    [(0, 81, 4), (4, 78, 4), (8, 76, 4)],
    [(0, 74, 8), (8, 78, 4)],
    [(0, 79, 4), (4, 78, 4), (8, 76, 4)],
    [(0, 74, 12)],

    # bars 23-24: gentle close
    [(0, 71, 6), (6, 74, 6)],
    [(0, 72, 12)],
]


def make_bar(bar_idx: int) -> Pattern:
    pat = Pattern(
        name=f"bar{bar_idx + 1}",
        num_steps=12,             # 3 beats × 4 sixteenths
        num_channels=2,
        bpm=70,                   # lent et douloureux
        steps_per_beat=4,
        temperament="equal",
        key_root_pc=2,            # D major
        time_sig_num=3,           # waltz / gymnopédie meter
        time_sig_den=4,
    )

    bass, chord_lo, chord_hi = LH_BARS[bar_idx]

    # Bass note on beat 1, sustains the full bar
    pat.set_note(1, 0, NoteEvent(
        midi_note=bass, velocity=0.50,
        duration_steps=12, instrument="piano_grand", articulation="tenuto",
    ))
    # Chord on beat 2 (step 4) — held until end of bar
    pat.set_note(1, 4, NoteEvent(
        midi_note=chord_lo, velocity=0.42,
        duration_steps=8, instrument="piano_grand",
    ))
    pat.set_note(1, 4, NoteEvent(
        midi_note=chord_hi, velocity=0.42,
        duration_steps=8, instrument="piano_grand",
    ))

    # Right hand melody
    if bar_idx < len(RH_MELODY):
        for step, midi, dur in RH_MELODY[bar_idx]:
            pat.set_note(0, step, NoteEvent(
                midi_note=midi, velocity=0.55,
                duration_steps=dur, instrument="piano_grand",
                articulation="tenuto",
            ))

    return pat


def build_song() -> Song:
    song = Song(
        title="Satie — Gymnopédie No. 1 (Lent et douloureux, 24 bars)",
        author="Erik Satie (rendered by ChipForge)",
        bpm=70,
    )

    song.panning = {0: 0.0, 1: 0.0}  # solo piano, centered

    song.channel_effects = {
        0: {"reverb": 0.36, "reverb_damping": 0.55, "reverb_mix": 0.30},
        1: {"reverb": 0.34, "reverb_damping": 0.58, "reverb_mix": 0.28},
    }
    song.master_reverb = 0.20
    song.master_delay = 0.0

    # Very gentle rubato — Satie's music almost doesn't breathe.
    # Just a tiny bit of give at the end.
    song.tempo_curve = [
        (0.0,  70.0),
        (54.0, 70.0),    # bar 19: still steady
        (66.0, 64.0),    # bar 23: small ritardando
        (72.0, 58.0),    # final bar: broader
    ]

    # Dynamics: pianissimo throughout, never louder than mezzo-piano
    song.dynamics_curve = [
        (0.0,  -14.0),    # ppp
        (24.0,  -8.0),    # bar 9: pp at the contrasting phrase
        (48.0, -10.0),    # bar 17: settle back
        (72.0, -16.0),    # final taper
    ]

    for i in range(24):
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
    out = Path("output/satie_gymnopedie_1.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print("Solo piano (piano_grand), 24 bars in 3/4, lent et douloureux")
