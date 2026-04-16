"""
Velvet Lo-Fi Jam — Layer #3: Warm Pad (Am - C - F - G)

Builds on 002_velvet_lofi_bells.py. Same kick + hat + clap + velvet
bass + glass bell stars. Adds a slow-swelling warm pad behind
everything that finally gives the floating bells real harmonic
context.

Why this layer matters:
  Layers 1+2 had a low end (bass), a top (bells), and rhythm (drums)
  but nothing in the middle filling out the harmony. The bells were
  floating in space. This pad fills the entire missing midrange in
  one move and turns the bells into the top of a real chord rather
  than isolated notes.

Translation of "warm pad behind everything — slow swelling Am C F G
chords":
  - Custom velvet_pad instrument: filtered saw + sub octave + 5th
    overtone, slow attack (~0.45 s), long sustain, long release
  - Mid register voicings (C3-G4) — out of the way of bass and bells
  - Heavy hall reverb (0.55) so it sits FAR back in the mix
  - Master volume scaled down via velocities so it never competes
  - Am - C - F - G progression: i - III - VI - VII in A minor.
    The canonical "lift" progression that pairs perfectly with the
    bells already climbing each bar.

Output: output/velvet_lofi_pad.wav
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.synth import ADSR, FilterEnvelope
from src.sequencer import Song, Pattern, NoteEvent
from src.instruments import Instrument, VoiceLayer, PRESETS
from src.mixer import render_song
from src.export import export_wav


# ---------------------------------------------------------------------------
# Custom instruments — bed bass + bells from layer 2 + new warm pad
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

GLASS_BELL = Instrument(
    name="Glass Bell",
    waveform="sine",
    adsr=ADSR(attack=0.001, decay=0.80, sustain=0.0,
              release=0.30, curve=2.5),
    volume=0.62,
    layers=[
        VoiceLayer(
            waveform="sine", gain=0.42, detune_cents=1902.0,
            adsr=ADSR(attack=0.001, decay=0.50, sustain=0.0,
                      release=0.20, curve=3.0),
        ),
        VoiceLayer(
            waveform="sine", gain=0.22, detune_cents=2786.0,
            adsr=ADSR(attack=0.001, decay=0.30, sustain=0.0,
                      release=0.15, curve=3.5),
        ),
        VoiceLayer(
            waveform="sine", gain=0.18, detune_cents=-1200.0,
            adsr=ADSR(attack=0.001, decay=0.90, sustain=0.0,
                      release=0.32, curve=2.5),
        ),
    ],
)

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

# NEW: Velvet warm pad. Sits FAR back in the mix.
#  - filtered saw primary for body
#  - sub octave for warmth
#  - 5th-overtone overlay for a faint shimmer
#  - filter envelope opens slowly during the chord swell
VELVET_PAD = Instrument(
    name="Velvet Warm Pad",
    waveform="sawtooth",
    adsr=ADSR(attack=0.45, decay=0.30, sustain=0.85,
              release=0.90, curve=1.2),
    volume=0.46,
    filter_cutoff=1400.0,
    filter_resonance=0.12,
    filter_env=FilterEnvelope(
        base_hz=600.0, peak_hz=1800.0, sustain_hz=1200.0,
        attack_sec=0.50, decay_sec=0.40, release_sec=0.80,
        resonance=0.15,
    ),
    layers=[
        # Detuned twin saw for stereo width — ±3¢ to keep intonation tight
        VoiceLayer(
            waveform="sawtooth", gain=0.30, detune_cents=-3.0,
            adsr=ADSR(attack=0.45, decay=0.30, sustain=0.85,
                      release=0.90, curve=1.2),
        ),
        VoiceLayer(
            waveform="sawtooth", gain=0.30, detune_cents=+3.0,
            adsr=ADSR(attack=0.45, decay=0.30, sustain=0.85,
                      release=0.90, curve=1.2),
        ),
        # Sub octave sine for warmth and weight
        VoiceLayer(
            waveform="sine", gain=0.35, detune_cents=-1200.0,
            adsr=ADSR(attack=0.40, decay=0.30, sustain=0.88,
                      release=0.95, curve=1.2),
        ),
        # 5th-harmonic triangle for the faint pad shimmer
        VoiceLayer(
            waveform="triangle", gain=0.14, detune_cents=+1902.0,
            adsr=ADSR(attack=0.55, decay=0.30, sustain=0.75,
                      release=0.80, curve=1.3),
        ),
    ],
)

INSTRUMENTS: dict[str, Instrument] = {
    **PRESETS,
    "velvet_bass": VELVET_BASS,
    "glass_bell":  GLASS_BELL,
    "star_bell":   STAR_BELL,
    "velvet_pad":  VELVET_PAD,
}


# ---------------------------------------------------------------------------
# Note shorthand
# ---------------------------------------------------------------------------

# Bass register
A1, C2, D2, E2, F1, G1 = 33, 36, 38, 40, 29, 31

# Bell register
A5, C6, D6, E6, G6, A6 = 81, 84, 86, 88, 91, 93
G5, E5 = 79, 76

# Pad register (mid — C3 to G4)
A3, B3, C4, D4, E4, F3, G3 = 57, 59, 60, 62, 64, 53, 55

BPM = 108
BAR_STEPS = 16

# Am C F G chord voicings (close position, mid register)
# Each is the 3 notes of the chord that the pad will hold for the full bar.
PAD_CHORDS = {
    "Am": [A3, C4, E4],   # 57 60 64
    "C":  [C4, E4, G3 + 12],   # 60 64 67  (G4)
    "F":  [F3, A3, C4],   # 53 57 60
    "G":  [G3, B3, D4],   # 55 59 62
}


def n(midi: int, vel: float, dur: int, inst: str,
      artic: str = "normal") -> NoteEvent:
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.95),
                     duration_steps=dur, instrument=inst, articulation=artic)


# ---------------------------------------------------------------------------
# Build a bar of the 4-bar phrase
# ---------------------------------------------------------------------------

def phrase_bar(bar_idx_in_phrase: int) -> Pattern:
    pat = Pattern(
        name=f"phrase_b{bar_idx_in_phrase}",
        num_steps=BAR_STEPS,
        num_channels=7,           # kick, hat, clap, bass, bell, star, pad
        bpm=BPM,
        steps_per_beat=4,
        temperament="equal",
        key_root_pc=9,            # A minor
        time_sig_num=4,
        time_sig_den=4,
    )

    # ---- ch 0: kick ----
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

    # ---- ch 2: clap ----
    if bar_idx_in_phrase % 2 == 1:
        for step in (4, 12):
            pat.set_note(2, step, NoteEvent(
                midi_note=40, velocity=0.45, duration_steps=2,
                instrument="noise_clap",
            ))

    # ---- ch 3: velvet bass ----
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

    # ---- ch 4: glass bell melody ----
    if bar_idx_in_phrase == 0:
        bell_notes = [(4, E5, 0.70, 4), (8, G5, 0.72, 4),
                       (12, A5, 0.74, 4)]
    elif bar_idx_in_phrase == 1:
        bell_notes = [(0, C6, 0.74, 2), (2, E5, 0.65, 2),
                       (6, E6, 0.78, 2), (8, C6, 0.70, 2),
                       (12, G5, 0.68, 4)]
    elif bar_idx_in_phrase == 2:
        bell_notes = [(0, E6, 0.76, 2), (4, G6, 0.80, 2),
                       (6, E6, 0.72, 2), (8, C6, 0.68, 2),
                       (10, E6, 0.74, 2), (12, G6, 0.78, 4)]
    else:
        bell_notes = [(0, A6, 0.82, 2), (2, G6, 0.74, 2),
                       (4, E6, 0.70, 2), (6, C6, 0.66, 2),
                       (8, D6, 0.70, 2), (10, E6, 0.72, 2),
                       (12, A5, 0.74, 4)]
    for step, midi, vel, dur in bell_notes:
        pat.set_note(4, step, n(midi, vel, dur, "glass_bell"))

    # ---- ch 5: star bell sparkles ----
    if bar_idx_in_phrase == 0:
        star_notes = [(13, A6, 0.42, 1)]
    elif bar_idx_in_phrase == 1:
        star_notes = [(13, G6, 0.40, 1), (14, A6, 0.45, 1)]
    elif bar_idx_in_phrase == 2:
        star_notes = []
    else:
        star_notes = [(5, A6, 0.38, 1), (7, C6, 0.34, 1),
                       (15, G6, 0.40, 1)]
    for step, midi, vel, dur in star_notes:
        pat.set_note(5, step, n(midi, vel, dur, "star_bell",
                                 artic="staccato"))

    # ---- ch 6: WARM PAD — Am C F G across the 4-bar phrase ----
    chord_for_bar = ["Am", "C", "F", "G"][bar_idx_in_phrase]
    chord_notes = PAD_CHORDS[chord_for_bar]
    # Hold each chord tone for the full bar so the pad swells in slowly
    # and rings into the next bar via its long release.
    for midi in chord_notes:
        pat.set_note(6, 0, NoteEvent(
            midi_note=midi,
            velocity=0.42,                # quiet — pad sits FAR back
            duration_steps=BAR_STEPS,     # holds the whole bar
            instrument="velvet_pad",
            articulation="tenuto",
        ))

    return pat


# ---------------------------------------------------------------------------
# Build the song
# ---------------------------------------------------------------------------

def build_song() -> Song:
    song = Song(
        title="Velvet Lo-Fi Jam — Layer 3 (Warm Pad)",
        author="ChipForge directing session",
        bpm=BPM,
    )

    song.panning = {
        0:  0.00,    # kick centered
        1:  0.28,    # hat right
        2: -0.22,    # clap left
        3:  0.00,    # bass centered
        4: -0.18,    # glass bell slightly left
        5:  0.32,    # star bell wide right
        6:  0.00,    # pad centered (the bed of the mix)
    }

    song.channel_effects = {
        0: {"reverb": 0.06, "reverb_damping": 0.65, "reverb_mix": 0.08},
        1: {"delay": 0.15, "delay_feedback": 0.25, "delay_mix": 0.20,
            "reverb": 0.10, "reverb_mix": 0.12},
        2: {"reverb": 0.18, "reverb_damping": 0.55, "reverb_mix": 0.22},
        3: {"delay": 0.30, "delay_feedback": 0.20, "delay_mix": 0.10,
            "reverb": 0.10, "reverb_mix": 0.10},
        4: {"reverb": 0.45, "reverb_damping": 0.30, "reverb_mix": 0.32,
            "delay": 0.36, "delay_feedback": 0.28, "delay_mix": 0.18},
        5: {"reverb": 0.55, "reverb_damping": 0.25, "reverb_mix": 0.40,
            "delay": 0.27, "delay_feedback": 0.32, "delay_mix": 0.22},
        # PAD: deep hall reverb so it sits BEHIND everything else
        6: {"reverb": 0.60, "reverb_damping": 0.40, "reverb_mix": 0.45,
            "chorus": 0.20, "chorus_detune": 5.0, "chorus_delay": 22.0},
    }

    song.master_reverb = 0.12
    song.master_delay = 0.18

    phrase_patterns = [phrase_bar(i) for i in range(4)]
    for p in phrase_patterns:
        song.patterns.append(p)

    for _ in range(8):
        for i in range(4):
            song.append_to_sequence(i)

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
    out = Path("output/velvet_lofi_pad.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print(f"32 bars at {BPM} BPM, A minor — bed + bells + warm Am-C-F-G pad")
