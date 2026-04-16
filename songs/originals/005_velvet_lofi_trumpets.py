"""
Velvet Lo-Fi Jam — Layer #5: Tijuana Brass Lead (Laser Scales of Fire)

Builds on layer 4 (smooth bells). Same bed + pad + smoothened bells.
Adds the "first chair" — two custom trumpets playing in parallel
diatonic thirds, Herb Alpert / Tijuana Brass style, with a 16th-note
ascending scalar run on the climax bar.

Translation of "first chair leading melody and instrument. trumpet?
laser scales of fire?? like tijuana brass":

  - "first chair leading"  → trumpet is the loudest melodic voice now;
                             bell velocities dropped ~30% so they back
                             off and let the trumpet sit on top
  - "trumpet"              → custom tijuana_trumpet: sawtooth body +
                             twin ±3¢ saws + octave overtone + subtle
                             pulse edge layer + brass filter envelope
                             swell + vibrato
  - "tijuana brass"        → TWO trumpets in parallel diatonic thirds
                             (the Herb Alpert signature). Lead carries
                             the melody, harmony plays a third below
                             in C major — sometimes major, sometimes
                             minor, all diatonic.
  - "laser scales of fire" → 16th-note ascending scalar run on bar 4
                             of the phrase (G5 → A5 → B5 → C6 → D6 →
                             E6), the harmony following in thirds.
                             Lands on a held A5 marcato.

Articulation:
  - marcato on downbeats (the Latin punch)
  - staccato on the off-beats and the run (the bounce)
  - accent on the syncopated anticipations

Output: output/velvet_lofi_trumpets.wav
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
# Custom instruments — bed bass + pad + smooth bell + NEW trumpet
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
        VoiceLayer(waveform="sine", gain=0.32, detune_cents=-1200.0,
                   adsr=ADSR(attack=0.005, decay=0.10, sustain=0.82,
                             release=0.22, curve=1.4)),
        VoiceLayer(waveform="square", gain=0.18, detune_cents=+5.0, duty=0.25,
                   adsr=ADSR(attack=0.005, decay=0.10, sustain=0.62,
                             release=0.18, curve=1.4)),
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
        attack_sec=0.50, decay_sec=0.40, release_sec=0.80, resonance=0.15,
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

SMOOTH_BELL = Instrument(
    name="Smooth Electronic Bell",
    waveform="sawtooth",
    adsr=ADSR(attack=0.012, decay=0.40, sustain=0.55,
              release=0.55, curve=1.3),
    volume=0.62,
    filter_env=FilterEnvelope(
        base_hz=700.0, peak_hz=4200.0, sustain_hz=2200.0,
        attack_sec=0.10, decay_sec=0.25, release_sec=0.40, resonance=0.18,
    ),
    layers=[
        VoiceLayer(waveform="sawtooth", gain=0.32, detune_cents=-5.0,
                   adsr=ADSR(attack=0.012, decay=0.40, sustain=0.55,
                             release=0.55, curve=1.3)),
        VoiceLayer(waveform="sawtooth", gain=0.32, detune_cents=+5.0,
                   adsr=ADSR(attack=0.012, decay=0.40, sustain=0.55,
                             release=0.55, curve=1.3)),
        VoiceLayer(waveform="sine", gain=0.18, detune_cents=+1200.0,
                   adsr=ADSR(attack=0.012, decay=0.50, sustain=0.30,
                             release=0.45, curve=1.5)),
        VoiceLayer(waveform="sine", gain=0.10, detune_cents=+1902.0,
                   adsr=ADSR(attack=0.012, decay=0.35, sustain=0.20,
                             release=0.30, curve=1.7)),
        VoiceLayer(waveform="triangle", gain=0.16, detune_cents=-1200.0,
                   adsr=ADSR(attack=0.012, decay=0.45, sustain=0.55,
                             release=0.50, curve=1.4)),
    ],
)

STAR_BELL = Instrument(
    name="Star Bell",
    waveform="sawtooth",
    adsr=ADSR(attack=0.008, decay=0.30, sustain=0.0,
              release=0.18, curve=2.5),
    volume=0.50,
    filter_cutoff=3500.0,
    filter_resonance=0.12,
    layers=[
        VoiceLayer(waveform="sine", gain=0.45, detune_cents=+1200.0,
                   adsr=ADSR(attack=0.008, decay=0.22, sustain=0.0,
                             release=0.12, curve=3.0)),
        VoiceLayer(waveform="sine", gain=0.20, detune_cents=+1902.0,
                   adsr=ADSR(attack=0.008, decay=0.16, sustain=0.0,
                             release=0.10, curve=3.5)),
        VoiceLayer(waveform="triangle", gain=0.14, detune_cents=0.0,
                   adsr=ADSR(attack=0.008, decay=0.28, sustain=0.0,
                             release=0.16, curve=2.8)),
    ],
)

# NEW — Tijuana brass trumpet. Sawtooth body + twin saws for ensemble
# width + octave overtone for the brass bell + a subtle pulse layer
# for the "laser" digital edge. Vibrato + filter envelope swell give
# the unmistakable brass blat on the attack.
TIJUANA_TRUMPET = Instrument(
    name="Tijuana Trumpet",
    waveform="sawtooth",
    adsr=ADSR(attack=0.012, decay=0.06, sustain=0.86,
              release=0.12, curve=1.4),
    volume=0.74,
    vibrato_rate=6.2,
    vibrato_depth=0.20,
    filter_env=FilterEnvelope(
        # Snappy filter blat — opens fast, settles bright. Higher
        # resonance than the orchestral trumpet for that brassy bite.
        base_hz=1100.0,
        peak_hz=6800.0,
        sustain_hz=3400.0,
        attack_sec=0.025,
        decay_sec=0.10,
        release_sec=0.08,
        resonance=0.32,
    ),
    layers=[
        # Twin ±3¢ saws for body and width
        VoiceLayer(
            waveform="sawtooth", gain=0.22, detune_cents=-3.0,
            adsr=ADSR(attack=0.012, decay=0.06, sustain=0.86,
                      release=0.12, curve=1.4),
        ),
        VoiceLayer(
            waveform="sawtooth", gain=0.22, detune_cents=+3.0,
            adsr=ADSR(attack=0.012, decay=0.06, sustain=0.86,
                      release=0.12, curve=1.4),
        ),
        # Octave-up triangle for the brass bell shimmer
        VoiceLayer(
            waveform="triangle", gain=0.14, detune_cents=+1200.0,
            adsr=ADSR(attack=0.012, decay=0.06, sustain=0.82,
                      release=0.12, curve=1.4),
        ),
        # Subtle 50% pulse layer — the "laser" digital edge
        VoiceLayer(
            waveform="square", gain=0.10, detune_cents=0.0, duty=0.50,
            adsr=ADSR(attack=0.012, decay=0.06, sustain=0.80,
                      release=0.10, curve=1.4),
        ),
    ],
)

INSTRUMENTS: dict[str, Instrument] = {
    **PRESETS,
    "velvet_bass":     VELVET_BASS,
    "velvet_pad":      VELVET_PAD,
    "glass_bell":      SMOOTH_BELL,
    "star_bell":       STAR_BELL,
    "tijuana_trumpet": TIJUANA_TRUMPET,
}


# ---------------------------------------------------------------------------
# Note shorthand
# ---------------------------------------------------------------------------

A1, C2, D2, E2, F1, G1 = 33, 36, 38, 40, 29, 31

# Bell register (lower since layer 4)
A4, C5, D5, E5, G5, A5 = 69, 72, 74, 76, 79, 81
G4, E4 = 67, 64
F5, B5, C6, D6, E6 = 77, 83, 84, 86, 88

# Pad register
A3, B3, C4, D4, E4_pad, F3, G3 = 57, 59, 60, 62, 64, 53, 55

BPM = 108
BAR_STEPS = 16

PAD_CHORDS = {
    "Am": [A3, C4, E4_pad],
    "C":  [C4, E4_pad, 67],
    "F":  [F3, A3, C4],
    "G":  [G3, B3, D4],
}


def n(midi: int, vel: float, dur: int, inst: str,
      artic: str = "normal") -> NoteEvent:
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.95),
                     duration_steps=dur, instrument=inst, articulation=artic)


# ---------------------------------------------------------------------------
# Tijuana lead lines per bar
# Each entry: (step, midi, dur_steps, velocity, articulation)
# Lead line — the principal voice
# Harmony  — a diatonic third below in C major (so it's sometimes major,
# sometimes minor, but always in key)
# ---------------------------------------------------------------------------

LEAD_BARS: list[list[tuple[int, int, int, float, str]]] = [
    # Bar 0 (Am chord) — Latin entry, syncopated
    [
        (0,  E5, 4, 0.82, "marcato"),    # downbeat anchor
        (6,  G5, 2, 0.74, "accent"),     # 'and of 2'
        (8,  A5, 4, 0.84, "marcato"),    # beat 3 anchor
        (14, G5, 2, 0.66, "staccato"),   # pickup to bar 2
    ],
    # Bar 1 (C chord) — chord-tone arpeggio with the C6 lift
    [
        (0,  E5, 2, 0.76, "marcato"),
        (4,  G5, 2, 0.72, "staccato"),
        (6,  C6, 2, 0.82, "accent"),     # the bright C6 lift
        (8,  G5, 4, 0.74, "tenuto"),
        (14, A5, 2, 0.68, "staccato"),   # pickup to F bar
    ],
    # Bar 2 (F chord) — leap and call
    [
        (0,  A5, 4, 0.84, "marcato"),    # the F's third
        (6,  C6, 2, 0.78, "accent"),
        (8,  F5, 4, 0.74, "normal"),     # drop to F root
        (12, A5, 4, 0.78, "tenuto"),     # back up
    ],
    # Bar 3 (G chord) — THE LASER SCALE OF FIRE
    [
        (0,  G5, 2, 0.84, "marcato"),    # anchor
        (2,  G5, 2, 0.72, "staccato"),   # repeat to launch the run
        (4,  G5, 1, 0.74, "staccato"),   # ascending 16ths begin
        (5,  A5, 1, 0.76, "staccato"),
        (6,  B5, 1, 0.78, "staccato"),
        (7,  C6, 1, 0.80, "staccato"),
        (8,  D6, 1, 0.82, "staccato"),
        (9,  E6, 2, 0.88, "accent"),     # PEAK — the laser lands
        (11, D6, 1, 0.74, "staccato"),
        (12, A5, 4, 0.82, "marcato"),    # marcato resolution
    ],
]


# Diatonic third below in C major. Build the harmony from the lead by
# transposing each note down a third within the C-major scale.
# Mapping (lead pitch class → harmony semitones below):
#   C  → A  (-3 semitones, m3)
#   D  → B  (-3, m3)
#   E  → C  (-4, M3)
#   F  → D  (-3, m3)
#   G  → E  (-3, m3)
#   A  → F  (-4, M3)
#   B  → G  (-4, M3)
_TIJUANA_THIRD_DOWN = {
    0: 3,   # C → A    (3 semitones below C)
    2: 3,   # D → B
    4: 4,   # E → C
    5: 3,   # F → D
    7: 3,   # G → E
    9: 4,   # A → F
    11: 4,  # B → G
}


def diatonic_third_below(midi: int) -> int:
    """Return the MIDI note a diatonic third below `midi` in C major."""
    pc = midi % 12
    drop = _TIJUANA_THIRD_DOWN.get(pc, 3)
    return midi - drop


def harmony_for_lead(events: list[tuple[int, int, int, float, str]]
                      ) -> list[tuple[int, int, int, float, str]]:
    """Build the harmony trumpet line: same rhythm, third below, slightly
    quieter so it sits under the lead."""
    out: list[tuple[int, int, int, float, str]] = []
    for step, midi, dur, vel, artic in events:
        out.append((step, diatonic_third_below(midi), dur,
                    max(0.0, vel - 0.18), artic))
    return out


HARMONY_BARS = [harmony_for_lead(b) for b in LEAD_BARS]


# ---------------------------------------------------------------------------
# Build a bar of the 4-bar phrase
# ---------------------------------------------------------------------------

def phrase_bar(bar_idx_in_phrase: int) -> Pattern:
    pat = Pattern(
        name=f"phrase_b{bar_idx_in_phrase}",
        num_steps=BAR_STEPS,
        num_channels=9,           # kick, hat, clap, bass, bell, star, pad,
                                   # trumpet_lead, trumpet_harm
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

    # ---- ch 4: smooth bell — DEMOTED to support voice ----
    # Velocities scaled to 0.70 of what they were so the trumpet leads.
    if bar_idx_in_phrase == 0:
        bell_notes = [(4, E4, 0.49, 4), (8, G4, 0.50, 4),
                       (12, A4, 0.52, 4)]
    elif bar_idx_in_phrase == 1:
        bell_notes = [(0, C5, 0.52, 2), (2, E4, 0.46, 2),
                       (6, E5, 0.55, 2), (8, C5, 0.49, 2),
                       (12, G4, 0.48, 4)]
    elif bar_idx_in_phrase == 2:
        bell_notes = [(0, E5, 0.53, 2), (4, G5, 0.56, 2),
                       (6, E5, 0.50, 2), (8, C5, 0.48, 2),
                       (10, E5, 0.52, 2), (12, G5, 0.55, 4)]
    else:
        bell_notes = [(0, A5, 0.57, 2), (2, G5, 0.52, 2),
                       (4, E5, 0.49, 2), (6, C5, 0.46, 2),
                       (8, D5, 0.49, 2), (10, E5, 0.50, 2),
                       (12, A4, 0.52, 4)]
    for step, midi, vel, dur in bell_notes:
        pat.set_note(4, step, n(midi, vel, dur, "glass_bell"))

    # ---- ch 5: star bell — also softened ----
    if bar_idx_in_phrase == 0:
        star_notes = [(13, A5, 0.32, 1)]
    elif bar_idx_in_phrase == 1:
        star_notes = [(13, G5, 0.30, 1), (14, A5, 0.34, 1)]
    elif bar_idx_in_phrase == 2:
        star_notes = []
    else:
        star_notes = [(5, A5, 0.28, 1), (7, C5, 0.26, 1),
                       (15, G5, 0.30, 1)]
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

    # ---- ch 7: TIJUANA TRUMPET — first chair lead ----
    for step, midi, dur, vel, artic in LEAD_BARS[bar_idx_in_phrase]:
        pat.set_note(7, step, n(midi, vel, dur,
                                 "tijuana_trumpet", artic=artic))

    # ---- ch 8: TIJUANA TRUMPET HARMONY — third below in C major ----
    for step, midi, dur, vel, artic in HARMONY_BARS[bar_idx_in_phrase]:
        pat.set_note(8, step, n(midi, vel, dur,
                                 "tijuana_trumpet", artic=artic))

    return pat


# ---------------------------------------------------------------------------
# Build the song
# ---------------------------------------------------------------------------

def build_song() -> Song:
    song = Song(
        title="Velvet Lo-Fi Jam — Layer 5 (Tijuana Brass Lead)",
        author="ChipForge directing session",
        bpm=BPM,
    )

    song.panning = {
        0:  0.00,    # kick centered
        1:  0.28,    # hat right
        2: -0.22,    # clap left
        3:  0.00,    # bass centered
        4: -0.25,    # bell left
        5:  0.40,    # star right
        6:  0.00,    # pad centered
        7: +0.12,    # lead trumpet slightly right of center
        8: -0.12,    # harmony trumpet slightly left — they hug each other
    }

    song.channel_effects = {
        0: {"reverb": 0.06, "reverb_damping": 0.65, "reverb_mix": 0.08},
        1: {"delay": 0.15, "delay_feedback": 0.25, "delay_mix": 0.20,
            "reverb": 0.10, "reverb_mix": 0.12},
        2: {"reverb": 0.18, "reverb_damping": 0.55, "reverb_mix": 0.22},
        3: {"delay": 0.30, "delay_feedback": 0.20, "delay_mix": 0.10,
            "reverb": 0.10, "reverb_mix": 0.10},
        4: {"reverb": 0.42, "reverb_damping": 0.40, "reverb_mix": 0.32,
            "delay": 0.36, "delay_feedback": 0.28, "delay_mix": 0.20,
            "chorus": 0.30, "chorus_detune": 8.0, "chorus_delay": 24.0},
        5: {"reverb": 0.50, "reverb_damping": 0.30, "reverb_mix": 0.36,
            "delay": 0.27, "delay_feedback": 0.32, "delay_mix": 0.22},
        6: {"reverb": 0.60, "reverb_damping": 0.40, "reverb_mix": 0.45,
            "chorus": 0.20, "chorus_detune": 5.0, "chorus_delay": 22.0},
        # Trumpets — relatively dry so the lead has presence. A short
        # slap delay (140 ms) for the iconic Tijuana Brass space.
        7: {"reverb": 0.18, "reverb_damping": 0.50, "reverb_mix": 0.18,
            "delay": 0.14, "delay_feedback": 0.18, "delay_mix": 0.14},
        8: {"reverb": 0.18, "reverb_damping": 0.50, "reverb_mix": 0.18,
            "delay": 0.14, "delay_feedback": 0.18, "delay_mix": 0.14},
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
    out = Path("output/velvet_lofi_trumpets.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered {len(audio) / 44100:.1f}s → {out}")
    print(f"32 bars at {BPM} BPM, 9 channels — bed + bells + pad + Tijuana brass lead")
