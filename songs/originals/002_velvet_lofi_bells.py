"""
Velvet Lo-Fi Jam — Layer #2: Glass Bells (Stars Bouncing, Yellow, Lifting)

Builds on 001_velvet_lofi_bed.py. Same kick + hat + clap + velvet bass.
Adds a glass bell melody in the upper register that bounces like stars
and lifts each phrase higher than the last.

Directing-language translation:
  "next i want some bright sound like stars bouncing, yellow and like
   glass bells. these are melodic and lift you up."

  - "stars bouncing"  → sparse scattered rhythm, skips not steps,
                        occasional 16th-note plink-plink twinkles
  - "yellow"          → upper register E5-A6, lean on C/E/G (the major
                        side of A minor pentatonic) for the bright color
  - "glass bells"     → custom glass_bell instrument: sine fundamental +
                        5th harmonic + 7th harmonic, sharp attack +
                        ringing decay, no sustain
  - "melodic"         → real 4-bar tune that develops
  - "lift you up"     → each phrase resolves higher than where it began;
                        final bar reaches G6 / A6

Output: output/velvet_lofi_bells.wav
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
# Custom instruments — bed bass + new glass bell
# ---------------------------------------------------------------------------

VELVET_BASS = Instrument(
    name="Velvet 8-bit Bass",
    waveform="square",
    duty=0.50,
    adsr=ADSR(attack=0.005, decay=0.10, sustain=0.72,
              release=0.18, curve=1.4),
    volume=0.78,
    filter_cutoff=900.0,
    filter_resonance=0.20,
    layers=[
        VoiceLayer(
            waveform="sine", gain=0.32, detune_cents=-1200.0,
            adsr=ADSR(attack=0.005, decay=0.10, sustain=0.82,
                      release=0.22, curve=1.4),
        ),
        VoiceLayer(
            waveform="square", gain=0.18, detune_cents=+5.0, duty=0.25,
            adsr=ADSR(attack=0.005, decay=0.10, sustain=0.62,
                      release=0.18, curve=1.4),
        ),
    ],
)

# Glass bell — sine fundamental + 5th harmonic + 7th harmonic.
# Sharp attack so the strike is felt. No sustain — pure decay tail.
# The 5th and 7th harmonic give it that crystalline rim-of-the-glass color.
GLASS_BELL = Instrument(
    name="Glass Bell",
    waveform="sine",
    adsr=ADSR(attack=0.001, decay=0.80, sustain=0.0,
              release=0.30, curve=2.5),
    volume=0.62,
    layers=[
        # 5th harmonic (octave + perfect 5th above) — the "ring"
        VoiceLayer(
            waveform="sine", gain=0.42, detune_cents=1902.0,
            adsr=ADSR(attack=0.001, decay=0.50, sustain=0.0,
                      release=0.20, curve=3.0),
        ),
        # 7th harmonic (octave + minor 7th above) — the metallic edge
        VoiceLayer(
            waveform="sine", gain=0.22, detune_cents=2786.0,
            adsr=ADSR(attack=0.001, decay=0.30, sustain=0.0,
                      release=0.15, curve=3.5),
        ),
        # Octave below — gentle body to anchor the bright top
        VoiceLayer(
            waveform="sine", gain=0.18, detune_cents=-1200.0,
            adsr=ADSR(attack=0.001, decay=0.90, sustain=0.0,
                      release=0.32, curve=2.5),
        ),
    ],
)

# Stars — sparser, even sparklier accent voice. Just a sine fundamental
# with a single octave-up overtone, very short decay = a literal "plink".
STAR_BELL = Instrument(
    name="Star Bell",
    waveform="sine",
    adsr=ADSR(attack=0.001, decay=0.25, sustain=0.0,
              release=0.10, curve=3.5),
    volume=0.50,
    layers=[
        VoiceLayer(
            waveform="sine", gain=0.40, detune_cents=+1200.0,
            adsr=ADSR(attack=0.001, decay=0.18, sustain=0.0,
                      release=0.08, curve=3.5),
        ),
        VoiceLayer(
            waveform="sine", gain=0.20, detune_cents=+1902.0,
            adsr=ADSR(attack=0.001, decay=0.14, sustain=0.0,
                      release=0.06, curve=4.0),
        ),
    ],
)

INSTRUMENTS: dict[str, Instrument] = {
    **PRESETS,
    "velvet_bass": VELVET_BASS,
    "glass_bell":  GLASS_BELL,
    "star_bell":   STAR_BELL,
}


# ---------------------------------------------------------------------------
# Note shorthand
# ---------------------------------------------------------------------------

# Bass register (matches the bed)
A1, C2, D2, E2, F1, G1 = 33, 36, 38, 40, 29, 31

# Bell register — upper, bright. A minor pentatonic notes only so we
# stay diatonic with the bed: A C D E G across octaves 5-6.
A5, C6, D6, E6, G6, A6 = 81, 84, 86, 88, 91, 93
G5 = 79
E5 = 76

BPM = 108
BAR_STEPS = 16


def n(midi: int, vel: float, dur: int, inst: str,
      artic: str = "normal") -> NoteEvent:
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.95),
                     duration_steps=dur, instrument=inst, articulation=artic)


# ---------------------------------------------------------------------------
# Build a bar of the 4-bar phrase (bed + bells)
# ---------------------------------------------------------------------------

def phrase_bar(bar_idx_in_phrase: int) -> Pattern:
    pat = Pattern(
        name=f"phrase_b{bar_idx_in_phrase}",
        num_steps=BAR_STEPS,
        num_channels=6,           # kick, hat, clap, bass, glass_bell, star_bell
        bpm=BPM,
        steps_per_beat=4,
        temperament="equal",
        key_root_pc=9,            # A minor
        time_sig_num=4,
        time_sig_den=4,
    )

    # ---- ch 0: kick (four on the floor, deep + subtle) ----
    for step in (0, 4, 8, 12):
        pat.set_note(0, step, NoteEvent(
            midi_note=36, velocity=0.58, duration_steps=2,
            instrument="kick_deep", articulation="tenuto",
        ))

    # ---- ch 1: hi-hat ----
    for step, vel in [(2, 0.32), (6, 0.40), (10, 0.32),
                       (14, 0.42), (15, 0.22)]:
        pat.set_note(1, step, NoteEvent(
            midi_note=42, velocity=vel, duration_steps=1,
            instrument="hat_crisp", articulation="staccato",
        ))

    # ---- ch 2: clap (sparse — only on bars 1 and 3 of the phrase) ----
    if bar_idx_in_phrase % 2 == 1:
        for step in (4, 12):
            pat.set_note(2, step, NoteEvent(
                midi_note=40, velocity=0.45, duration_steps=2,
                instrument="noise_clap",
            ))

    # ---- ch 3: velvet bass line ----
    if bar_idx_in_phrase < 3:
        bassline = [
            (0,  A1, 0.78, 4),
            (4,  A1, 0.62, 2),
            (6,  C2, 0.68, 2),
            (8,  E2, 0.72, 4),
            (12, G1, 0.66, 4),
        ]
    else:
        bassline = [
            (0,  A1, 0.80, 4),
            (4,  G1, 0.70, 2),
            (6,  F1, 0.66, 2),
            (8,  E2, 0.72, 2),
            (10, D2, 0.66, 2),
            (12, C2, 0.66, 4),
        ]
    for step, midi, vel, dur in bassline:
        pat.set_note(3, step, n(midi, vel, dur, "velvet_bass"))

    # ---- ch 4: GLASS BELL melody (the lifting tune) ----
    # Each bar has a different melodic shape. Across the 4 bars the
    # phrase climbs: bar 0 starts at E5, bar 3 reaches G6.
    if bar_idx_in_phrase == 0:
        # Bar 0 — gentle entry, mid register, ascending steps
        bell_notes = [
            (4,  E5, 0.70, 4),    # the 'and' of beat 1
            (8,  G5, 0.72, 4),
            (12, A5, 0.74, 4),
        ]
    elif bar_idx_in_phrase == 1:
        # Bar 1 — bouncing, wider intervals
        bell_notes = [
            (0,  C6, 0.74, 2),
            (2,  E5, 0.65, 2),    # the bounce — drops then leaps
            (6,  E6, 0.78, 2),
            (8,  C6, 0.70, 2),
            (12, G5, 0.68, 4),
        ]
    elif bar_idx_in_phrase == 2:
        # Bar 2 — climbing, more notes (the lift)
        bell_notes = [
            (0,  E6, 0.76, 2),
            (4,  G6, 0.80, 2),    # peak so far
            (6,  E6, 0.72, 2),
            (8,  C6, 0.68, 2),
            (10, E6, 0.74, 2),
            (12, G6, 0.78, 4),    # held — the lift moment
        ]
    else:
        # Bar 3 — climax + descending tail to match bass variation
        bell_notes = [
            (0,  A6, 0.82, 2),    # the highest note in the whole phrase
            (2,  G6, 0.74, 2),
            (4,  E6, 0.70, 2),
            (6,  C6, 0.66, 2),
            (8,  D6, 0.70, 2),
            (10, E6, 0.72, 2),
            (12, A5, 0.74, 4),    # back home
        ]
    for step, midi, vel, dur in bell_notes:
        pat.set_note(4, step, n(midi, vel, dur, "glass_bell",
                                 artic="normal"))

    # ---- ch 5: STAR BELL accents — the bouncing twinkle ----
    # Sparse, scattered. Different positions per bar so it feels
    # unpredictable. Always upper register (octave above the melody).
    if bar_idx_in_phrase == 0:
        # one little plink near the end of the bar
        star_notes = [(13, A6, 0.42, 1)]
    elif bar_idx_in_phrase == 1:
        # twinkle pair on the 'e a' of beat 4
        star_notes = [(13, G6, 0.40, 1), (14, A6, 0.45, 1)]
    elif bar_idx_in_phrase == 2:
        # nothing — let the climbing bell breathe
        star_notes = []
    else:
        # the bar 3 climax — three rapid stars over the held high A6
        star_notes = [
            (5,  A6, 0.38, 1),
            (7,  C6, 0.34, 1),
            (15, G6, 0.40, 1),
        ]
    for step, midi, vel, dur in star_notes:
        pat.set_note(5, step, n(midi, vel, dur, "star_bell",
                                 artic="staccato"))

    return pat


# ---------------------------------------------------------------------------
# Build the song
# ---------------------------------------------------------------------------

def build_song() -> Song:
    song = Song(
        title="Velvet Lo-Fi Jam — Layer 2 (Glass Bell Stars)",
        author="ChipForge directing session",
        bpm=BPM,
    )

    song.panning = {
        0:  0.00,    # kick centered
        1:  0.28,    # hat right
        2: -0.22,    # clap left
        3:  0.00,    # bass centered
        4: -0.18,    # glass bell slightly left
        5:  0.32,    # star bell wide right (the twinkles ping out wide)
    }

    song.channel_effects = {
        0: {"reverb": 0.06, "reverb_damping": 0.65, "reverb_mix": 0.08},
        1: {"delay": 0.15, "delay_feedback": 0.25, "delay_mix": 0.20,
            "reverb": 0.10, "reverb_mix": 0.12},
        2: {"reverb": 0.18, "reverb_damping": 0.55, "reverb_mix": 0.22},
        3: {"delay": 0.30, "delay_feedback": 0.20, "delay_mix": 0.10,
            "reverb": 0.10, "reverb_mix": 0.10},
        # Glass bell wants long, bright reverb — hall not room
        4: {"reverb": 0.45, "reverb_damping": 0.30, "reverb_mix": 0.32,
            "delay": 0.36, "delay_feedback": 0.28, "delay_mix": 0.18},
        # Stars want even more wash — they should sparkle and trail
        5: {"reverb": 0.55, "reverb_damping": 0.25, "reverb_mix": 0.40,
            "delay": 0.27, "delay_feedback": 0.32, "delay_mix": 0.22},
    }

    song.master_reverb = 0.12
    song.master_delay = 0.18

    phrase_patterns = [phrase_bar(i) for i in range(4)]
    for p in phrase_patterns:
        song.patterns.append(p)

    # 8 reps of the 4-bar phrase = 32 bars
    for _ in range(8):
        for i in range(4):
            song.append_to_sequence(i)

    # Same dynamics arc as the bed — fade in, hold, taper out.
    # The bells naturally inherit it.
    song.dynamics_curve = [
        (0.0,   -8.0),
        (16.0,  -2.0),
        (96.0,  -2.0),
        (128.0, -10.0),
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
    out = Path("output/velvet_lofi_bells.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print(f"32 bars at {BPM} BPM, A minor pentatonic, "
          f"bed + glass bell stars overlay")
