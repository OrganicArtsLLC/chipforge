"""
Velvet Lo-Fi Jam — Layer #4: Smoother, Wider, Lower Bells

Revision of layer 2's glass bells based on user feedback:
  "the bell sounds too high pitched and small and needs to expand
   and smoothen its sound and be more electronic"

Same bed + pad as layer 3. The bells are rebuilt:

  - "too high pitched" → entire melody drops one octave
                         (E5-A6 → E4-A5, stars A6 → A5)
  - "small"            → sawtooth body layer added; the bell is no
                         longer just sine harmonics floating in space
  - "expand"           → stereo width via ±5¢ twin sawtooth layers
                         and channel chorus; wider stereo placement
  - "smoothen"         → attack lengthened from 1 ms to 12 ms (no
                         more click onset), filter envelope opens
                         slowly during the attack
  - "more electronic" → lead with sawtooth, drop the brittle 7th
                         harmonic, keep the 5th for color

Output: output/velvet_lofi_smooth_bells.wav
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
# Custom instruments — bed bass + pad + REVISED bells
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
        VoiceLayer(waveform="sawtooth", gain=0.30, detune_cents=-3.0,
                   adsr=ADSR(attack=0.45, decay=0.30, sustain=0.85,
                             release=0.90, curve=1.2)),
        VoiceLayer(waveform="sawtooth", gain=0.30, detune_cents=+3.0,
                   adsr=ADSR(attack=0.45, decay=0.30, sustain=0.85,
                             release=0.90, curve=1.2)),
        VoiceLayer(waveform="sine", gain=0.35, detune_cents=-1200.0,
                   adsr=ADSR(attack=0.40, decay=0.30, sustain=0.88,
                             release=0.95, curve=1.2)),
        VoiceLayer(waveform="triangle", gain=0.14, detune_cents=+1902.0,
                   adsr=ADSR(attack=0.55, decay=0.30, sustain=0.75,
                             release=0.80, curve=1.3)),
    ],
)

# REVISED — smoother, wider, lower, more electronic.
# Sawtooth-led with a filter envelope for the open-and-close sweep.
# Long ringing sustain instead of plucky decay.
SMOOTH_BELL = Instrument(
    name="Smooth Electronic Bell",
    waveform="sawtooth",         # ← electronic body
    adsr=ADSR(attack=0.012, decay=0.40, sustain=0.55,
              release=0.55, curve=1.3),
    volume=0.62,
    filter_env=FilterEnvelope(
        # Slow open: dark on attack, brighter at sustain → smooth & wide
        base_hz=700.0,
        peak_hz=4200.0,
        sustain_hz=2200.0,
        attack_sec=0.10,
        decay_sec=0.25,
        release_sec=0.40,
        resonance=0.18,
    ),
    layers=[
        # Twin detuned saws for stereo expansion (the "expand")
        VoiceLayer(
            waveform="sawtooth", gain=0.32, detune_cents=-5.0,
            adsr=ADSR(attack=0.012, decay=0.40, sustain=0.55,
                      release=0.55, curve=1.3),
        ),
        VoiceLayer(
            waveform="sawtooth", gain=0.32, detune_cents=+5.0,
            adsr=ADSR(attack=0.012, decay=0.40, sustain=0.55,
                      release=0.55, curve=1.3),
        ),
        # Sine octave-up for the residual bell shimmer (kept from before
        # but quieter — the saws carry the body now)
        VoiceLayer(
            waveform="sine", gain=0.18, detune_cents=+1200.0,
            adsr=ADSR(attack=0.012, decay=0.50, sustain=0.30,
                      release=0.45, curve=1.5),
        ),
        # 5th harmonic for color (the metallic 7th is GONE)
        VoiceLayer(
            waveform="sine", gain=0.10, detune_cents=+1902.0,
            adsr=ADSR(attack=0.012, decay=0.35, sustain=0.20,
                      release=0.30, curve=1.7),
        ),
        # Sub-octave triangle to anchor the new lower register
        VoiceLayer(
            waveform="triangle", gain=0.16, detune_cents=-1200.0,
            adsr=ADSR(attack=0.012, decay=0.45, sustain=0.55,
                      release=0.50, curve=1.4),
        ),
    ],
)

# Star bell — same idea as before but moved down an octave to match the
# new bell register, slightly smoother attack, slightly more body.
STAR_BELL = Instrument(
    name="Star Bell (Smoother)",
    waveform="sawtooth",
    adsr=ADSR(attack=0.008, decay=0.30, sustain=0.0,
              release=0.18, curve=2.5),
    volume=0.50,
    filter_cutoff=3500.0,
    filter_resonance=0.12,
    layers=[
        VoiceLayer(
            waveform="sine", gain=0.45, detune_cents=+1200.0,
            adsr=ADSR(attack=0.008, decay=0.22, sustain=0.0,
                      release=0.12, curve=3.0),
        ),
        VoiceLayer(
            waveform="sine", gain=0.20, detune_cents=+1902.0,
            adsr=ADSR(attack=0.008, decay=0.16, sustain=0.0,
                      release=0.10, curve=3.5),
        ),
        VoiceLayer(
            waveform="triangle", gain=0.14, detune_cents=0.0,
            adsr=ADSR(attack=0.008, decay=0.28, sustain=0.0,
                      release=0.16, curve=2.8),
        ),
    ],
)

INSTRUMENTS: dict[str, Instrument] = {
    **PRESETS,
    "velvet_bass": VELVET_BASS,
    "velvet_pad":  VELVET_PAD,
    "glass_bell":  SMOOTH_BELL,   # rebound to the new instrument
    "star_bell":   STAR_BELL,
}


# ---------------------------------------------------------------------------
# Note shorthand
# ---------------------------------------------------------------------------

A1, C2, D2, E2, F1, G1 = 33, 36, 38, 40, 29, 31

# Bell register — ALL DROPPED ONE OCTAVE from layer 2
A4, C5, D5, E5, G5, A5 = 69, 72, 74, 76, 79, 81
G4, E4 = 67, 64

# Pad register
A3, B3, C4, D4, E4_pad, F3, G3 = 57, 59, 60, 62, 64, 53, 55

BPM = 108
BAR_STEPS = 16

PAD_CHORDS = {
    "Am": [A3, C4, E4_pad],   # 57 60 64
    "C":  [C4, E4_pad, 67],   # 60 64 G4
    "F":  [F3, A3, C4],       # 53 57 60
    "G":  [G3, B3, D4],       # 55 59 62
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
        num_channels=7,
        bpm=BPM,
        steps_per_beat=4,
        temperament="equal",
        key_root_pc=9,
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
            (0, A1, 0.78, 4), (4, A1, 0.62, 2), (6, C2, 0.68, 2),
            (8, E2, 0.72, 4), (12, G1, 0.66, 4),
        ]
    else:
        bassline = [
            (0, A1, 0.80, 4), (4, G1, 0.70, 2), (6, F1, 0.66, 2),
            (8, E2, 0.72, 2), (10, D2, 0.66, 2), (12, C2, 0.66, 4),
        ]
    for step, midi, vel, dur in bassline:
        pat.set_note(3, step, n(midi, vel, dur, "velvet_bass"))

    # ---- ch 4: SMOOTH BELL melody (one octave lower than v1) ----
    # Same shape, but every note dropped 12 semitones. Now sits in
    # E4-A5 instead of E5-A6 — much closer to the pad and the bass.
    if bar_idx_in_phrase == 0:
        bell_notes = [(4, E4, 0.70, 4), (8, G4, 0.72, 4),
                       (12, A4, 0.74, 4)]
    elif bar_idx_in_phrase == 1:
        bell_notes = [(0, C5, 0.74, 2), (2, E4, 0.65, 2),
                       (6, E5, 0.78, 2), (8, C5, 0.70, 2),
                       (12, G4, 0.68, 4)]
    elif bar_idx_in_phrase == 2:
        bell_notes = [(0, E5, 0.76, 2), (4, G5, 0.80, 2),
                       (6, E5, 0.72, 2), (8, C5, 0.68, 2),
                       (10, E5, 0.74, 2), (12, G5, 0.78, 4)]
    else:
        bell_notes = [(0, A5, 0.82, 2), (2, G5, 0.74, 2),
                       (4, E5, 0.70, 2), (6, C5, 0.66, 2),
                       (8, D5, 0.70, 2), (10, E5, 0.72, 2),
                       (12, A4, 0.74, 4)]
    for step, midi, vel, dur in bell_notes:
        pat.set_note(4, step, n(midi, vel, dur, "glass_bell"))

    # ---- ch 5: star bell sparkles (also dropped one octave) ----
    if bar_idx_in_phrase == 0:
        star_notes = [(13, A5, 0.42, 1)]
    elif bar_idx_in_phrase == 1:
        star_notes = [(13, G5, 0.40, 1), (14, A5, 0.45, 1)]
    elif bar_idx_in_phrase == 2:
        star_notes = []
    else:
        star_notes = [(5, A5, 0.38, 1), (7, C5, 0.34, 1),
                       (15, G5, 0.40, 1)]
    for step, midi, vel, dur in star_notes:
        pat.set_note(5, step, n(midi, vel, dur, "star_bell",
                                 artic="staccato"))

    # ---- ch 6: warm pad ----
    chord_for_bar = ["Am", "C", "F", "G"][bar_idx_in_phrase]
    for midi in PAD_CHORDS[chord_for_bar]:
        pat.set_note(6, 0, NoteEvent(
            midi_note=midi, velocity=0.42,
            duration_steps=BAR_STEPS, instrument="velvet_pad",
            articulation="tenuto",
        ))

    return pat


# ---------------------------------------------------------------------------
# Build the song
# ---------------------------------------------------------------------------

def build_song() -> Song:
    song = Song(
        title="Velvet Lo-Fi Jam — Layer 4 (Smoother, Wider, Lower Bells)",
        author="ChipForge directing session",
        bpm=BPM,
    )

    song.panning = {
        0:  0.00,
        1:  0.28,
        2: -0.22,
        3:  0.00,
        4: -0.25,    # bell pushed wider left now
        5:  0.40,    # stars wider right
        6:  0.00,
    }

    song.channel_effects = {
        0: {"reverb": 0.06, "reverb_damping": 0.65, "reverb_mix": 0.08},
        1: {"delay": 0.15, "delay_feedback": 0.25, "delay_mix": 0.20,
            "reverb": 0.10, "reverb_mix": 0.12},
        2: {"reverb": 0.18, "reverb_damping": 0.55, "reverb_mix": 0.22},
        3: {"delay": 0.30, "delay_feedback": 0.20, "delay_mix": 0.10,
            "reverb": 0.10, "reverb_mix": 0.10},
        # Smoother bell: chorus added for the "expand", less plinky reverb
        4: {"reverb": 0.42, "reverb_damping": 0.40, "reverb_mix": 0.32,
            "delay": 0.36, "delay_feedback": 0.28, "delay_mix": 0.20,
            "chorus": 0.30, "chorus_detune": 8.0, "chorus_delay": 24.0},
        5: {"reverb": 0.50, "reverb_damping": 0.30, "reverb_mix": 0.36,
            "delay": 0.27, "delay_feedback": 0.32, "delay_mix": 0.22},
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
    out = Path("output/velvet_lofi_smooth_bells.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print(f"32 bars at {BPM} BPM, A minor — bed + pad + smoother wider bells")
