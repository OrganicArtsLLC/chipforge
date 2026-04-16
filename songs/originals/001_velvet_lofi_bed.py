"""
Velvet Lo-Fi House Bed — Foundation Track #001 (Directing-Language Session)

The first piece of an open-ended composition session where the user
describes sound and Claude translates it to ChipForge. This file is the
**bed**: kick + sparse perc + a velvet 8-bit square-wave bass line meant
to run under everything else we add.

The user prompt was:
    "lay down a nice bass line and some drum beats also bass deep drum
     in the background. subtle, lo fi house. drum and bass line. very
     digital. rich and makes you think of velvet electronic 8 bit square
     wave goodness."

Translation:
- 108 BPM, 4/4, slight swing on the hats
- A minor pentatonic groove (the warmest sad-but-cool key for lo-fi)
- Custom inline 'velvet_bass' instrument: 50% square + sub-octave sine
  + narrow 25% pulse layer, low-passed to 900 Hz with a small
  resonance bump for character
- Four-on-the-floor kick_deep at velocity 0.58 — under the bass, not
  fighting it
- Off-beat hat_crisp with accent on the 'and' of 2 and 4 for the swing
- A clap on the 2 and the 4 of every other bar — sparse
- Master reverb 0.12 + master delay 0.18 for the lo-fi haze

The bass line walks A1 - C2 - E2 - G1 then varies on the 4th bar with
a descending tail (A1 - G1 - F1 - E1). 32 bars total, repeating the
4-bar phrase 8 times so we have a runway to layer onto.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.synth import ADSR
from src.sequencer import Song, Pattern, NoteEvent
from src.instruments import Instrument, VoiceLayer, PRESETS
from src.mixer import render_song
from src.export import export_wav


# ---------------------------------------------------------------------------
# Custom instruments — built inline so the bed has its own signature voice
# ---------------------------------------------------------------------------

VELVET_BASS = Instrument(
    name="Velvet 8-bit Bass",
    waveform="square",
    duty=0.50,                # full square = fattest pulse
    adsr=ADSR(attack=0.005, decay=0.10, sustain=0.72,
              release=0.18, curve=1.4),
    volume=0.78,
    filter_cutoff=900.0,      # warm low-pass — the "velvet"
    filter_resonance=0.20,    # gentle bump = chip-tune character
    layers=[
        # Sub-octave sine — body and weight
        VoiceLayer(
            waveform="sine",
            gain=0.32,
            detune_cents=-1200.0,
            adsr=ADSR(attack=0.005, decay=0.10, sustain=0.82,
                      release=0.22, curve=1.4),
        ),
        # Narrow pulse layer at +5¢ — adds digital edge + width
        VoiceLayer(
            waveform="square",
            gain=0.18,
            detune_cents=+5.0,
            duty=0.25,
            adsr=ADSR(attack=0.005, decay=0.10, sustain=0.62,
                      release=0.18, curve=1.4),
        ),
    ],
)

# Custom instrument dict — the song uses these names directly.
INSTRUMENTS: dict[str, Instrument] = {
    **PRESETS,
    "velvet_bass": VELVET_BASS,
}


# ---------------------------------------------------------------------------
# Note shorthand
# ---------------------------------------------------------------------------

# A minor pentatonic in the bass register
A1 = 33
C2 = 36
D2 = 38
E2 = 40
F1 = 29
G1 = 31

BPM = 108
BAR_STEPS = 16   # 4/4 with sixteenth-note grid


def n(midi: int, vel: float = 0.78, dur: int = 2,
      inst: str = "velvet_bass", artic: str = "normal") -> NoteEvent:
    """Build a NoteEvent with sensible bass-friendly defaults."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.95),
                     duration_steps=dur, instrument=inst, articulation=artic)


# ---------------------------------------------------------------------------
# The 4-bar phrase
# ---------------------------------------------------------------------------

def phrase_bar(bar_idx_in_phrase: int) -> Pattern:
    """
    Build one bar of the 4-bar phrase.

    bar_idx_in_phrase = 0..3
        0: standard groove
        1: standard groove
        2: standard groove (with clap on 2 + 4)
        3: variation — descending tail
    """
    pat = Pattern(
        name=f"phrase_b{bar_idx_in_phrase}",
        num_steps=BAR_STEPS,
        num_channels=4,           # kick, hat, clap, bass
        bpm=BPM,
        steps_per_beat=4,
        temperament="equal",
        key_root_pc=9,            # A minor
        time_sig_num=4,
        time_sig_den=4,
    )

    # ---------- ch 0: kick (four on the floor, deep + subtle) ----------
    for step in (0, 4, 8, 12):
        pat.set_note(0, step, NoteEvent(
            midi_note=36,                 # not pitched — drum preset
            velocity=0.58,
            duration_steps=2,
            instrument="kick_deep",
            articulation="tenuto",
        ))

    # ---------- ch 1: hi-hat (off-beats with swung accent) ----------
    # Plain off-beats on 2, 6, 10, 14 (the "and" of each beat)
    # Add a subtle 16th-note ghost on the 'e' of beat 4 for groove
    for step, vel in [(2, 0.32), (6, 0.40), (10, 0.32),
                       (14, 0.42), (15, 0.22)]:
        pat.set_note(1, step, NoteEvent(
            midi_note=42,
            velocity=vel,
            duration_steps=1,
            instrument="hat_crisp",
            articulation="staccato",
        ))

    # ---------- ch 2: clap (sparse — only on bars 1 and 3 of the phrase) ----
    # Bars are 0-indexed within the phrase; bar 1 and bar 3 = the "2 and 4"
    if bar_idx_in_phrase % 2 == 1:
        for step in (4, 12):  # the 2 and the 4 of the bar
            pat.set_note(2, step, NoteEvent(
                midi_note=40,
                velocity=0.45,
                duration_steps=2,
                instrument="noise_clap",
            ))

    # ---------- ch 3: velvet bass line ----------
    if bar_idx_in_phrase < 3:
        # Standard groove
        bassline = [
            # (step, midi, velocity, duration_steps)
            (0,  A1, 0.78, 4),   # root, downbeat
            (4,  A1, 0.62, 2),   # subtle pickup
            (6,  C2, 0.68, 2),   # passing tone, the b3
            (8,  E2, 0.72, 4),   # the 5th, sustained
            (12, G1, 0.66, 4),   # the b7 below, completes the cell
        ]
    else:
        # Variation bar — descending tail
        bassline = [
            (0,  A1, 0.80, 4),
            (4,  G1, 0.70, 2),
            (6,  F1, 0.66, 2),
            (8,  E2, 0.72, 2),
            (10, D2, 0.66, 2),
            (12, C2, 0.66, 4),
        ]
    for step, midi, vel, dur in bassline:
        pat.set_note(3, step, n(midi, vel=vel, dur=dur))

    return pat


# ---------------------------------------------------------------------------
# Build the song — 8 repetitions of the 4-bar phrase = 32 bars
# ---------------------------------------------------------------------------

def build_song() -> Song:
    song = Song(
        title="Velvet Lo-Fi Bed (Foundation #001)",
        author="ChipForge directing session",
        bpm=BPM,
    )

    # Stereo placement — kick centered, perc wide, bass in the middle
    song.panning = {
        0:  0.00,    # kick centered
        1:  0.28,    # hat right
        2: -0.22,    # clap left
        3:  0.00,    # bass centered
    }

    # Per-channel effects: kick gets a touch of room, hats get rhythmic delay,
    # bass gets a slap-back delay for the lo-fi tape vibe
    song.channel_effects = {
        0: {"reverb": 0.06, "reverb_damping": 0.65, "reverb_mix": 0.08},
        1: {"delay": 0.15, "delay_feedback": 0.25, "delay_mix": 0.20,
            "reverb": 0.10, "reverb_mix": 0.12},
        2: {"reverb": 0.18, "reverb_damping": 0.55, "reverb_mix": 0.22},
        3: {"delay": 0.30, "delay_feedback": 0.20, "delay_mix": 0.10,
            "reverb": 0.10, "reverb_mix": 0.10},
    }

    # Master glue: gentle reverb + a slap delay = the lo-fi haze
    song.master_reverb = 0.12
    song.master_delay = 0.18

    # Build the 4-bar phrase as 4 distinct patterns
    phrase_patterns = [phrase_bar(i) for i in range(4)]
    for p in phrase_patterns:
        song.patterns.append(p)

    # Sequence the phrase 8 times = 32 bars (~71 seconds at 108 BPM)
    for _ in range(8):
        for i in range(4):
            song.append_to_sequence(i)

    # Subtle dynamics arc — fade in over the first 4 bars, fade out the last 4
    # So there's a hint of build/release even in the bed
    song.dynamics_curve = [
        (0.0,   -8.0),    # quiet entry
        (16.0,  -2.0),    # bar 5: settled in
        (96.0,  -2.0),    # most of the way through
        (128.0, -10.0),   # final 4 bars taper
    ]

    return song


if __name__ == "__main__":
    song = build_song()
    audio = render_song(
        song,
        instruments=INSTRUMENTS,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )
    out = Path("output/velvet_lofi_bed.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print(f"32 bars at {BPM} BPM, A minor pentatonic, kick + hat + clap + velvet bass")
