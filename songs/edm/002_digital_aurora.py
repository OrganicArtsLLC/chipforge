"""
Digital Aurora — Progressive Trance with Mathematical Foundations
=================================================================

A progressive trance piece in Bb minor that fuses Euclidean rhythm
algorithms with Fibonacci velocity shaping and golden-ratio melody
construction. The aurora metaphor: slow luminous build, then waves
of color cascading across the sky.

MATHEMATICAL TECHNIQUES:
  1. Euclidean rhythms (Bjorklund algorithm) for all drum patterns
  2. Fibonacci velocity curves for dynamic arc shaping
  3. Golden ratio interval selection for lead melody
  4. Trance chord cycle: Bbm -> Gb -> Db -> Ab (i -> VI -> III -> VII)

SOUND DESIGN:
  - All melodic notes duration >= 2 (no staccato chirps)
  - All channels have reverb and/or delay
  - Velocities capped at 0.85
  - bass_growl for rich harmonic bass
  - saw_filtered for warm lead
  - pad_lush in every section
  - pulse_warm arp with tempo-synced delay

Key: Bb minor
BPM: 136
Channels: 7
  0 - Kick (kick_deep, Euclidean E(4,16))
  1 - Snare/Clap (noise_clap, Euclidean E(3,8))
  2 - Hi-hat (hat_crisp + hat_open_shimmer, Euclidean E(7,16))
  3 - Bass (bass_growl, root-fifth driving pattern)
  4 - Lead (saw_filtered, golden ratio intervals)
  5 - Pad (pad_lush, sustained warmth in every section)
  6 - Arp (pulse_warm, chord tone arpeggiation)

Structure (~20 seconds, 10 bars at 136 BPM):
  [0-7s]    BUILD     4 bars — Pad + arp + hats, kick enters bar 3
  [7-20s]   DROP      6 bars — Full groove, lead hook, driving bass
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 136
SPB = 4
BAR = 16
NUM_CH = 7

# -- Constants ----------------------------------------------------------------
PHI = (1 + math.sqrt(5)) / 2  # 1.6180339887...
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

# -- Helpers -------------------------------------------------------------------

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, midi: int, vel: float = 0.75, dur: int = 2) -> NoteEvent:
    """Create a note. Default duration=2 (no staccato chirps). Velocity capped at 0.85."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 2), instrument=inst)

def note_drum(inst: str, midi: int, vel: float = 0.75, dur: int = 1) -> NoteEvent:
    """Drum note — short duration is OK for percussion."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 1), instrument=inst)

def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]


# -- Bjorklund's Euclidean Rhythm Algorithm ------------------------------------

def euclidean_rhythm(pulses: int, steps: int) -> list[bool]:
    """Bjorklund's algorithm: distribute pulses as evenly as possible
    across steps. Returns list of booleans.

    E(3,8)  = Cuban tresillo
    E(4,16) = four-on-the-floor
    E(5,16) = bossa nova
    E(7,16) = West African bell
    """
    if pulses >= steps:
        return [True] * steps
    if pulses == 0:
        return [False] * steps

    groups: list[list[bool]] = [[True] for _ in range(pulses)]
    remainder: list[list[bool]] = [[False] for _ in range(steps - pulses)]

    while len(remainder) > 1:
        new_groups = []
        while groups and remainder:
            g = groups.pop(0)
            r = remainder.pop(0)
            new_groups.append(g + r)
        if groups:
            remainder = groups
        new_groups.extend(remainder)
        groups = new_groups
        remainder = []
        if len(groups) <= 1:
            break
        first_len = len(groups[0])
        split_idx = len(groups)
        for i in range(1, len(groups)):
            if len(groups[i]) != first_len:
                split_idx = i
                break
        if split_idx < len(groups):
            remainder = groups[split_idx:]
            groups = groups[:split_idx]

    result = []
    for g in groups:
        result.extend(g)
    for r in remainder:
        result.extend(r)
    return result[:steps]


# -- Fibonacci Velocity Curve --------------------------------------------------

def fibonacci_velocity_curve(n: int, min_vel: float = 0.45, max_vel: float = 0.85) -> list[float]:
    """Generate n velocity values following fibonacci-ratio crescendo.
    Each value = fib(i)/fib(n-1), scaled to [min_vel, max_vel]."""
    if n <= 1:
        return [max_vel]
    fibs = [1, 1]
    for i in range(2, n):
        fibs.append(fibs[-1] + fibs[-2])
    max_fib = fibs[-1]
    return [min_vel + (max_vel - min_vel) * (f / max_fib) for f in fibs]


# -- Golden Ratio Melody -------------------------------------------------------

def golden_interval(base_midi: int, step: int) -> int:
    """Select note from Bb minor scale using golden ratio spacing.
    Creates non-repeating but harmonically coherent melody."""
    # Bb minor scale degrees (semitones from root)
    scale = [0, 2, 3, 5, 7, 8, 10]  # natural minor
    idx = int((step * PHI) % len(scale))
    octave_shift = int((step * PHI) / len(scale)) % 2  # span 2 octaves
    return base_midi + scale[idx] + 12 * octave_shift


# -- Instrument Assignments (warm palette) -------------------------------------
KICK   = 'kick_deep'
SNARE  = 'noise_clap'       # fat body, not paper-thin
HAT_CL = 'hat_crisp'
HAT_OP = 'hat_open_shimmer'
BASS   = 'bass_growl'        # rich harmonics
LEAD   = 'saw_filtered'      # warm, filtered
PAD    = 'pad_lush'          # sustained warmth
ARP    = 'pulse_warm'        # smooth, not plucky

# -- Bb minor note constants (MIDI) -------------------------------------------
# Bb minor scale: Bb C Db Eb F Gb Ab
Bb1 = 34; Db2 = 37; Eb2 = 39; F2 = 41; Gb2 = 42; Ab2 = 44
Bb2 = 46; C3 = 48; Db3 = 49; Eb3 = 51; F3 = 53; Gb3 = 54; Ab3 = 56
Bb3 = 58; C4 = 60; Db4 = 61; Eb4 = 63; F4 = 65; Gb4 = 66; Ab4 = 68
Bb4 = 70; C5 = 72; Db5 = 73; Eb5 = 75; F5 = 77; Gb5 = 78; Ab5 = 80
Bb5 = 82

# Chord voicings: Bbm -> Gb -> Db -> Ab (i -> VI -> III -> VII)
CHORDS = [
    (Bb3, Db4, F4),     # Bbm
    (Gb3, Bb3, Db4),    # Gb
    (Db4, F4, Ab4),     # Db
    (Ab3, C4, Eb4),     # Ab
]

BASS_ROOTS = [Bb1, Gb2, Db2, Ab2]


# -- Percussion Builders (Euclidean) -------------------------------------------

def place_euclidean_kicks(g: list, bar: int, pulses: int = 4, vel: float = 0.78) -> None:
    """Kicks using Euclidean rhythm E(pulses, 16)."""
    pattern = euclidean_rhythm(pulses, BAR)
    bs = bar * BAR
    for i, hit in enumerate(pattern):
        if hit:
            g[0][bs + i] = note_drum(KICK, 36, vel, 2)


def place_euclidean_hats(g: list, bar: int, pulses: int = 7, vel: float = 0.45) -> None:
    """Hats using Euclidean E(pulses, 16) — West African bell pattern."""
    pattern = euclidean_rhythm(pulses, BAR)
    bs = bar * BAR
    for i, hit in enumerate(pattern):
        if hit:
            if i % 4 == 0:
                g[2][bs + i] = note_drum(HAT_OP, 46, vel * 0.90, 3)
            else:
                g[2][bs + i] = note_drum(HAT_CL, 42, vel, 2)


def place_euclidean_snare(g: list, bar: int, pulses: int = 3, vel: float = 0.72) -> None:
    """Snare using E(pulses, 8) mapped to 16-step grid — tresillo feel."""
    pattern = euclidean_rhythm(pulses, 8)
    bs = bar * BAR
    for i, hit in enumerate(pattern):
        if hit:
            step = bs + i * 2
            if step < bs + BAR:
                g[1][step] = note_drum(SNARE, 40, vel, 3)


# -- Harmonic Builders ---------------------------------------------------------

def warm_pad(g: list, bar: int, chord: tuple, vel: float = 0.40) -> None:
    """Sustained pad chord — the warmth floor. Full bar duration."""
    bs = bar * BAR
    g[5][bs] = note(PAD, chord[1], vel, BAR)


def smooth_arp(g: list, bar: int, chord: tuple, vel: float = 0.45) -> None:
    """Arpeggiate chord tones as smooth 8th notes with legato overlap."""
    bs = bar * BAR
    tones = list(chord) + [chord[0] + 12]  # add octave for 4 tones
    for step in range(0, BAR, 2):  # 8th note pulse
        tone = tones[step // 2 % len(tones)]
        g[6][bs + step] = note(ARP, tone, vel, 3)


def driving_bass(g: list, bar: int, root: int, vel: float = 0.78) -> None:
    """Root-fifth driving bass pattern. Sustained notes."""
    bs = bar * BAR
    g[3][bs] = note(BASS, root, vel, 6)              # root: sustained
    g[3][bs + 8] = note(BASS, root + 7, vel * 0.70, 4)  # fifth up


# -- PATTERN BUILDERS ----------------------------------------------------------

def make_build() -> Pattern:
    """4 bars: Aurora gathering. Pad wash + filtered arp + Euclidean hats.
    Kick enters bar 3 to set up the drop. Fibonacci velocity swell."""
    steps = BAR * 4
    g = new_grid(steps)

    fib_vels = fibonacci_velocity_curve(4, 0.30, 0.75)

    for bar in range(4):
        chord = CHORDS[bar % 4]

        # Pad: always present, swelling with fibonacci curve
        pad_vel = 0.28 + fib_vels[bar] * 0.25
        warm_pad(g, bar, chord, pad_vel)

        # Arp: filtered, legato, gradually more present
        arp_vel = 0.25 + fib_vels[bar] * 0.22
        smooth_arp(g, bar, chord, arp_vel)

        # Hats: Euclidean E(5,16) — sparse bossa pattern, building
        hat_vel = 0.22 + fib_vels[bar] * 0.18
        place_euclidean_hats(g, bar, 5, hat_vel)

        # Kick: enters bar 3 with E(4,16) four-on-floor
        if bar >= 3:
            place_euclidean_kicks(g, bar, 4, 0.65)

        # Bass: gentle root note enters bar 2
        if bar >= 2:
            root = BASS_ROOTS[bar % 4]
            bs = bar * BAR
            g[3][bs] = note(BASS, root, 0.45 + (bar - 2) * 0.10, 8)

        # Lead tease: single golden-ratio notes in bars 2-3
        if bar >= 2:
            bs = bar * BAR
            midi = golden_interval(Bb4, bar * 3)
            midi = max(Bb3, min(midi, Bb5))
            g[4][bs + 8] = note(LEAD, midi, 0.45, 4)

    return Pattern(name='build', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_drop() -> Pattern:
    """6 bars: THE DROP. Full Euclidean groove. Golden-ratio lead melody.
    Driving bass_growl root-fifth. Pad floor underneath everything.
    Fibonacci velocity crescendo across the 6 bars to peak at bar 5."""
    steps = BAR * 6
    g = new_grid(steps)

    # Fibonacci velocity arc across 6 bars — peaks at end
    bar_vels = fibonacci_velocity_curve(6, 0.65, 0.85)

    for bar in range(6):
        chord = CHORDS[bar % 4]
        root = BASS_ROOTS[bar % 4]
        bv = bar_vels[bar]

        # -- Euclidean drums: full groove --
        # Kicks: E(4,16) four-on-floor with fibonacci velocity
        place_euclidean_kicks(g, bar, 4, bv)

        # Snare: E(3,8) tresillo mapped to 16-grid
        place_euclidean_snare(g, bar, 3, bv * 0.90)

        # Hats: E(7,16) West African bell — complex groove
        place_euclidean_hats(g, bar, 7, bv * 0.62)

        # Ghost kick layer: E(5,16) at low velocity for polyrhythmic texture
        e5 = euclidean_rhythm(5, BAR)
        bs = bar * BAR
        for i, hit in enumerate(e5):
            if hit and g[0][bs + i] is None:
                g[0][bs + i] = note_drum(KICK, 36, bv * 0.35, 1)

        # -- Bass: driving root-fifth --
        driving_bass(g, bar, root, bv * 0.95)

        # -- Pad: sustained warmth floor --
        warm_pad(g, bar, chord, bv * 0.45)

        # -- Arp: full groove, tempo-synced feel --
        smooth_arp(g, bar, chord, bv * 0.55)

        # Clap accents on beats 2 and 4
        g[1][bs + 4] = note_drum(SNARE, 40, bv * 0.78, 3)
        g[1][bs + 12] = note_drum(SNARE, 40, bv * 0.72, 3)

    # -- Golden Ratio Lead Melody --
    # Base: Bb4 (MIDI 70). Melody spans 6 bars = 24 beats.
    melody_base = Bb4  # MIDI 70
    for beat in range(24):
        bar_idx = beat // 4
        bv = bar_vels[bar_idx]

        # Golden interval selection from Bb minor scale
        midi = golden_interval(melody_base, beat)
        midi = max(Bb3, min(midi, Bb5))  # clamp to reasonable range

        # Fibonacci velocity shaping — peak at golden ratio point
        peak_beat = 24 / PHI  # ~14.8
        dist = abs(beat - peak_beat) / peak_beat
        vel = bv * (0.95 - dist * 0.25)
        vel = max(0.55, min(vel, 0.85))

        # Duration: quarter notes with lingering phrase endings
        dur = 3  # default: dotted 8th
        if beat % 4 == 3:
            dur = 4  # phrase boundary: quarter note
        if beat % 8 == 7:
            dur = 6  # section boundary: dotted quarter

        step = beat * 4
        if step < steps:
            g[4][step] = note(LEAD, midi, vel, min(dur, steps - step))

    # Climax: force peak notes at the golden point (bar 4, ~beat 16)
    climax_bar = 4
    cbs = climax_bar * BAR
    g[4][cbs] = note(LEAD, F5, 0.85, 4)
    g[4][cbs + 4] = note(LEAD, Ab5, 0.82, 3)
    g[4][cbs + 8] = note(LEAD, Bb5, 0.85, 6)
    g[4][cbs + 14] = note(LEAD, F5, 0.78, 2)

    # Fill: snare roll in final bar for energy
    final_bs = 5 * BAR
    for step in range(0, BAR, 2):
        roll_vel = 0.50 + step * 0.02
        g[1][final_bs + step] = note_drum(SNARE, 40, min(roll_vel, 0.82), 2)

    return Pattern(name='drop', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# -- SONG ASSEMBLY -------------------------------------------------------------

def build_song() -> Song:
    patterns = [
        make_build(),   # 0 — 4 bars ~7.1s
        make_drop(),    # 1 — 6 bars ~10.6s
    ]
    # Total: 10 bars ~ 17.6 seconds at 136 BPM

    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # snare: near center
        2:  0.28,    # hats: right (space for arp on left)
        3: -0.08,    # bass: near center (slight left for width)
        4:  0.12,    # lead: slight right
        5: -0.20,    # pad: left (balances hats)
        6: -0.30,    # arp: left (wide stereo field)
    }

    channel_effects = {
        0: {  # Kick: subtle room
            'reverb': 0.15, 'reverb_mix': 0.06,
        },
        1: {  # Snare/Clap: medium room for body
            'reverb': 0.30, 'reverb_mix': 0.15,
        },
        2: {  # Hats: rhythmic delay + room
            'delay': 0.110, 'delay_feedback': 0.25, 'delay_mix': 0.18,
            'reverb': 0.25, 'reverb_mix': 0.12,
        },
        3: {  # Bass: tight, mostly dry
            'reverb': 0.10, 'reverb_mix': 0.05,
        },
        4: {  # Lead: rich reverb + slapback delay
            'reverb': 0.50, 'reverb_mix': 0.25,
            'delay': 0.220, 'delay_feedback': 0.30, 'delay_mix': 0.18,
        },
        5: {  # Pad: deep hall reverb
            'reverb': 0.80, 'reverb_mix': 0.45,
        },
        6: {  # Arp: tempo-synced delay + spacious room
            'delay': 0.165, 'delay_feedback': 0.35, 'delay_mix': 0.22,
            'reverb': 0.40, 'reverb_mix': 0.20,
        },
    }

    return Song(
        title='Digital Aurora — Progressive Trance',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.12,
        master_delay=0.06,
    )


# -- MAIN ----------------------------------------------------------------------

if __name__ == '__main__':
    print("╔════════════════════════════════════════════════════╗")
    print("║  DIGITAL AURORA — Progressive Trance              ║")
    print("║  Euclidean Rhythms + Fibonacci Dynamics + Golden  ║")
    print("║  Ratio Melody in Bb Minor                         ║")
    print("╚════════════════════════════════════════════════════╝")
    print()
    print("  Mathematical techniques:")
    print("    E  Euclidean rhythms (Bjorklund's algorithm)")
    print("    F  Fibonacci velocity curves")
    print("    G  Golden ratio melody intervals")
    print()
    print(f"  Key: Bb minor (i->VI->III->VII trance cycle)")
    print(f"  BPM: {BPM}")
    print()
    print("  [0-7s]    Build — Aurora gathering, pad + arp + hats")
    print("  [7-20s]   Drop  — Full Euclidean groove, golden lead")
    print()
    print("  Rendering...", flush=True)

    song = build_song()
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    out = Path('output/edm_002_digital_aurora.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print(f"  phi = {PHI:.10f}")
    print("  The aurora dances in golden ratios.")
