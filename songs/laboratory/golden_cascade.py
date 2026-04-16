"""
Golden Cascade — Mathematically-Driven Electronic Composition
==============================================================

A spiritual successor to Cascade Protocol, reimagined through mathematics.
Same F#m trance DNA, completely different organism.

MATHEMATICAL TECHNIQUES USED:
  1. Euclidean rhythms (Bjorklund's algorithm) — mathematically optimal
     beat distributions. E(5,16) = the bossa nova, E(7,16) = West African bell.
  2. Golden ratio melody — intervals derived from φ (1.618...) applied to
     pitch selection, creating naturally pleasing melodic contours.
  3. Fibonacci velocity curves — dynamics follow Fibonacci sequence ratios
     for organic crescendo/decrescendo arcs.
  4. Polyrhythmic layering — 3-against-4, 5-against-4 cross-rhythms that
     create emergent accent patterns.
  5. Harmonic series overtones — bell/pad voices use natural overtone
     frequencies (2x, 3x, 5x fundamental) for acoustic richness.

Key: F# minor → modulates to B minor (subdominant) → returns
BPM: 134 (slightly faster than original — more urgent)
Channels: 8
  0 - Kick (Euclidean E(4,16) base + E(5,16) ghost layer)
  1 - Snare/Clap (E(3,8) pattern — displaced backbeat)
  2 - Hi-hat (E(7,16) — West African bell pattern on hats)
  3 - Sub bass (root motion, fibonacci-timed slides)
  4 - Arp layer 1 (chord tones, golden-ratio note selection)
  5 - Arp layer 2 (harmonic series overtones, ghostly)
  6 - Lead melody (golden ratio intervals, fibonacci dynamics)
  7 - Pad/Atmosphere (slow harmonic series swells)

Structure (~75 seconds at 134 BPM):
  [0-7s]    PULSE       4 bars  — Euclidean kick + hat only (mathematical heartbeat)
  [7-21s]   EMERGE      8 bars  — Bass enters, arp layer 1, polyrhythm builds
  [21-50s]  ASCEND     16 bars  — Full ensemble, golden melody, two drops
  [50-57s]  VOID        4 bars  — Stripped to overtones + euclidean percussion
  [57-72s]  TRANSCEND   8 bars  — Everything returns elevated, climax
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 134
SPB = 4
BAR = 16  # 4 beats × 4 steps

# ── Constants ─────────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2  # 1.6180339887...
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]  # first 11 fibonacci numbers

# ── Helpers ───────────────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, freq: float, vel: float = 0.80, dur: int = 1) -> NoteEvent:
    return NoteEvent(midi_note=freq_to_midi(freq), velocity=vel,
                     duration_steps=dur, instrument=inst)

def new_grid(channels: int, steps: int) -> list:
    return [[None] * steps for _ in range(channels)]


# ── MATHEMATICS ───────────────────────────────────────────────────────────────

def euclidean_rhythm(pulses: int, steps: int) -> list[bool]:
    """Bjorklund's algorithm: distribute `pulses` as evenly as possible
    across `steps`. Returns list of booleans.

    E(3,8)  = [x . . x . . x .]  — the Cuban tresillo
    E(4,16) = [x . . . x . . . x . . . x . . .]  — four-on-floor
    E(5,16) = [x . . x . . x . . x . . x . . .]  — bossa nova
    E(7,16) = [x . x . x x . x . x . x x . x .]  — West African bell
    """
    if pulses >= steps:
        return [True] * steps
    if pulses == 0:
        return [False] * steps

    # Bjorklund's algorithm (binary decomposition)
    groups: list[list[bool]] = [[True] for _ in range(pulses)]
    remainder: list[list[bool]] = [[False] for _ in range(steps - pulses)]

    while len(remainder) > 1:
        new_groups = []
        while groups and remainder:
            g = groups.pop(0)
            r = remainder.pop(0)
            new_groups.append(g + r)
        # Whatever is left becomes the new remainder
        if groups:
            remainder = groups
        new_groups.extend(remainder)
        groups = new_groups
        remainder = []
        # Split: groups = first min(len(new), len(rest)), remainder = rest
        # Actually, re-split based on pattern length
        if len(groups) <= 1:
            break
        # Find where patterns diverge
        first_len = len(groups[0])
        split_idx = len(groups)
        for i in range(1, len(groups)):
            if len(groups[i]) != first_len:
                split_idx = i
                break
        if split_idx < len(groups):
            remainder = groups[split_idx:]
            groups = groups[:split_idx]

    # Flatten
    result = []
    for g in groups:
        result.extend(g)
    for r in remainder:
        result.extend(r)
    return result[:steps]


def fibonacci_velocity_curve(n: int, min_vel: float = 0.4, max_vel: float = 0.95) -> list[float]:
    """Generate n velocity values following a fibonacci-ratio crescendo curve.
    Each value = fib(i)/fib(n-1), scaled to [min_vel, max_vel]."""
    if n <= 1:
        return [max_vel]
    # Generate fibonacci up to n terms
    fibs = [1, 1]
    for i in range(2, n):
        fibs.append(fibs[-1] + fibs[-2])
    max_fib = fibs[-1]
    return [min_vel + (max_vel - min_vel) * (f / max_fib) for f in fibs]


def golden_interval(base_midi: int, step: int) -> int:
    """Select a note from the scale using golden ratio spacing.
    Maps step through φ to pick scale degrees, creating non-repeating
    but harmonically coherent melody patterns."""
    # F# minor scale degrees (in semitones from root)
    scale = [0, 2, 3, 5, 7, 8, 10]  # natural minor
    # Golden ratio index: multiply step by φ, mod by scale length
    idx = int((step * PHI) % len(scale))
    octave_shift = int((step * PHI) / len(scale)) % 3  # span 3 octaves max
    return base_midi + scale[idx] + 12 * octave_shift


def harmonic_series_freqs(fundamental: float, partials: list[int]) -> list[float]:
    """Return frequencies from the harmonic series of a fundamental.
    partials=[2,3,5] gives octave, fifth, major third (just intonation)."""
    return [fundamental * p for p in partials]


# ── Instrument assignments ────────────────────────────────────────────────────
KICK   = 'kick_deep'
SNARE  = 'snare_tight'
CLAP   = 'noise_clap'
HAT_CL = 'hat_crisp'
HAT_OP = 'hat_open_shimmer'
BASS   = 'bass_sub'
ARP1   = 'pulse_arp'
ARP2   = 'pluck_short'
LEAD   = 'saw_filtered'
PAD    = 'pad_lush'

# ── Note constants (F# minor) ────────────────────────────────────────────────
# F#=42(MIDI), but we use hz() everywhere
Fs2 = hz(42); A2  = hz(45); B2  = hz(47); Cs3 = hz(49)
D3  = hz(50); E3  = hz(52); Fs3 = hz(54); A3  = hz(57)
B3  = hz(59); Cs4 = hz(61); D4  = hz(62); E4  = hz(64)
Fs4 = hz(66); Gs4 = hz(68); A4  = hz(69); B4  = hz(71)
Cs5 = hz(73); D5  = hz(74); E5  = hz(76); Fs5 = hz(78)
A5  = hz(81); B5  = hz(83); Cs6 = hz(85)

# Chord voicings (F#m → D → A → E — the trance cycle)
CHORDS = [
    (Fs3, A3,  Cs4),   # F#m
    (D3,  Fs3, A3),    # D
    (A3,  Cs4, E4),    # A
    (E3,  Gs4, B3),    # E  (Gs4 intentionally high for color)
]

# B minor modulation chords
CHORDS_BM = [
    (B3,  D4,  Fs4),   # Bm
    (Fs3, A3,  Cs4),   # F#m (pivot)
    (E3,  Gs4, B3),    # E
    (A3,  Cs4, E4),    # A
]

# ── Percussion builders ──────────────────────────────────────────────────────

def place_euclidean_kicks(g: list, bar: int, pulses: int = 4, vel: float = 0.88) -> None:
    """Place kicks using Euclidean rhythm E(pulses, 16)."""
    pattern = euclidean_rhythm(pulses, BAR)
    bs = bar * BAR
    for i, hit in enumerate(pattern):
        if hit:
            g[0][bs + i] = note(KICK, hz(36), vel, 1)


def place_euclidean_hats(g: list, bar: int, pulses: int = 7, vel: float = 0.50) -> None:
    """Place hats using Euclidean rhythm E(pulses, 16) — West African bell."""
    pattern = euclidean_rhythm(pulses, BAR)
    bs = bar * BAR
    for i, hit in enumerate(pattern):
        if hit:
            # Alternate closed/open for texture
            if i % 4 == 0:
                g[2][bs + i] = note(HAT_OP, hz(46), vel * 0.9, 1)
            else:
                g[2][bs + i] = note(HAT_CL, hz(42), vel, 1)


def place_snare_pattern(g: list, bar: int, pulses: int = 3, vel: float = 0.78) -> None:
    """Snare using E(3,8) displaced across the bar — the Cuban tresillo."""
    pattern = euclidean_rhythm(pulses, 8)
    bs = bar * BAR
    for i, hit in enumerate(pattern):
        if hit:
            step = bs + i * 2  # map 8-grid to 16-grid
            if step < bs + BAR:
                g[1][step] = note(SNARE, hz(40), vel, 1)


def place_golden_arp(g: list, bar: int, chord: tuple, channel: int = 4,
                     inst: str = 'pulse_arp', vel: float = 0.55, offset: int = 0) -> None:
    """Arpeggiate chord tones using golden-ratio step selection.
    Creates non-repeating but consonant patterns."""
    bs = bar * BAR
    chord_freqs = list(chord)
    for step in range(BAR):
        # Golden ratio selects which chord tone to play
        tone_idx = int(((step + offset) * PHI) % len(chord_freqs))
        # Fibonacci velocity shaping within the bar
        fib_pos = step % 8
        vel_mod = 0.85 + 0.15 * math.sin(fib_pos * PHI)  # golden oscillation
        s = bs + step
        g[channel][s] = note(inst, chord_freqs[tone_idx], vel * vel_mod, 1)


# ── PATTERN BUILDERS ─────────────────────────────────────────────────────────

def make_pulse() -> Pattern:
    """4 bars: Mathematical heartbeat. Euclidean kick E(4,16) + E(7,16) hats.
    Just rhythm — establishing the mathematical grid before harmony enters."""
    steps = BAR * 4
    g = new_grid(8, steps)

    for bar in range(4):
        # Kicks: standard four-on-floor E(4,16) with fibonacci velocity swell
        vels = fibonacci_velocity_curve(4, 0.70, 0.92)
        place_euclidean_kicks(g, bar, 4, vels[bar])

        # Hats: E(7,16) — the West African bell pattern
        hat_vel = 0.35 + bar * 0.05  # gradually more present
        place_euclidean_hats(g, bar, 7, hat_vel)

        # Ghost kick layer: E(5,16) at very low velocity (polyrhythmic)
        e5 = euclidean_rhythm(5, BAR)
        bs = bar * BAR
        for i, hit in enumerate(e5):
            if hit and g[0][bs + i] is None:  # don't override main kicks
                g[0][bs + i] = note(KICK, hz(36), 0.30, 1)

    return Pattern(name='pulse', num_steps=steps, num_channels=8,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_emerge() -> Pattern:
    """8 bars: Bass enters with fibonacci-timed root motion.
    Arp layer 1 begins with golden-ratio note selection.
    Snare enters with tresillo pattern E(3,8)."""
    steps = BAR * 8
    g = new_grid(8, steps)

    chord_seq = [0, 0, 1, 1, 2, 2, 3, 3]  # 2 bars per chord

    for bar in range(8):
        chord_idx = chord_seq[bar]
        chord = CHORDS[chord_idx]

        # Euclidean percussion: complexity grows
        kick_pulses = 4 if bar < 4 else 5  # E(4,16) → E(5,16)
        place_euclidean_kicks(g, bar, kick_pulses, 0.85)
        place_euclidean_hats(g, bar, 7, 0.45 + bar * 0.02)

        # Snare enters bar 4
        if bar >= 4:
            place_snare_pattern(g, bar, 3, 0.65 + (bar - 4) * 0.04)

        # Bass: root note, fibonacci duration pattern
        bs = bar * BAR
        bass_freq = chord[0]  # root of chord
        # Bass note duration uses fibonacci: 1,1,2,3,5... but clamped to bar
        fib_dur = min(FIB[bar % len(FIB)], 8)
        g[3][bs] = note(BASS, bass_freq, 0.78, fib_dur)
        # Second bass hit at fibonacci offset
        fib_offset = FIB[(bar + 2) % 7] % BAR
        if fib_offset > 0 and fib_offset != bs % BAR:
            g[3][bs + fib_offset] = note(BASS, bass_freq * 1.5, 0.60, 2)  # fifth

        # Arp layer 1: golden-ratio arpeggiation (enters bar 2)
        if bar >= 2:
            arp_vel = 0.40 + (bar - 2) * 0.04
            place_golden_arp(g, bar, chord, 4, ARP1, arp_vel, offset=bar)

        # Pad: slow swell (enters bar 6)
        if bar >= 6:
            pad_vel = 0.15 + (bar - 6) * 0.08
            g[7][bs] = note(PAD, chord[1], pad_vel, BAR)

    return Pattern(name='emerge', num_steps=steps, num_channels=8,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_ascend() -> Pattern:
    """16 bars: THE DROP. Full ensemble. Golden melody over Euclidean grooves.
    
    Bars 1-8:  F#m chord cycle with golden melody
    Bars 9-12: Modulate to B minor (the emotional shift)
    Bars 13-16: Return to F#m, melody reaches climax at F#5

    The melody uses golden_interval() — each note is φ steps apart
    on the scale, creating phrases that never literally repeat but
    always sound 'right'. This is why sunflowers are beautiful."""
    steps = BAR * 16
    g = new_grid(8, steps)

    for bar in range(16):
        # Chord selection: bars 0-7 = trance cycle, 8-11 = Bm, 12-15 = return
        if bar < 8:
            chord = CHORDS[bar % 4]
        elif bar < 12:
            chord = CHORDS_BM[(bar - 8) % 4]
        else:
            chord = CHORDS[(bar - 12) % 4]

        # Full Euclidean percussion
        place_euclidean_kicks(g, bar, 4, 0.90)
        place_euclidean_hats(g, bar, 7, 0.52)
        place_snare_pattern(g, bar, 3, 0.80)

        # Add clap on beat 2 and 4 (steps 4 and 12)
        bs = bar * BAR
        g[1][bs + 4] = note(CLAP, hz(40), 0.72, 1)
        g[1][bs + 12] = note(CLAP, hz(40), 0.68, 1)

        # Bass: driving root + fifth pattern
        g[3][bs] = note(BASS, chord[0], 0.82, 4)
        g[3][bs + 8] = note(BASS, chord[0] * 1.5, 0.68, 4)  # fifth up

        # Arp layer 1: golden arpeggiation (full velocity)
        place_golden_arp(g, bar, chord, 4, ARP1, 0.58, offset=bar * 3)

        # Arp layer 2: harmonic series overtones (ghostly shimmer)
        overtones = harmonic_series_freqs(chord[0], [3, 5, 7])  # 5th, M3, m7
        for i, ot_freq in enumerate(overtones):
            ot_midi = freq_to_midi(ot_freq)
            if 40 < ot_midi < 96:  # keep in reasonable range
                step_pos = bs + int((i * PHI * 4) % BAR)
                g[5][step_pos] = note(ARP2, ot_freq, 0.28 + i * 0.04, 2)

        # Pad: chord sustain
        g[7][bs] = note(PAD, chord[1], 0.30, BAR)

    # ── GOLDEN MELODY ─────────────────────────────────────────────────────
    # Uses golden_interval() to select pitches from F# minor scale
    # Base MIDI: 66 (F#4) — melody lives in octaves 4-5
    melody_base = 66  # F#4

    # Generate 64 melody notes (one per beat across 16 bars)
    for beat in range(64):
        bar_idx = beat // 4
        beat_in_bar = beat % 4

        # Golden interval selection
        midi_note = golden_interval(melody_base, beat)

        # Clamp to reasonable range
        midi_note = max(54, min(midi_note, 85))  # F#3 to C#6

        # Fibonacci velocity curve across the 16-bar arc
        # Peak at golden ratio point (bar 10 ≈ 16/φ)
        peak_bar = 16 / PHI  # ~9.9 — the golden climax point
        dist_from_peak = abs(bar_idx - peak_bar) / peak_bar
        vel = 0.90 - dist_from_peak * 0.30  # loudest at φ point
        vel = max(0.55, min(vel, 0.95))

        # Duration: mostly quarter notes, some half notes at phrase boundaries
        dur = 4  # quarter note
        if beat % 8 == 7:  # phrase endings
            dur = 6  # dotted quarter (lingering)
        if beat % 16 == 15:  # section endings
            dur = 8  # half note (breathing)

        step = beat * 4  # each beat = 4 steps on 16th grid
        if step < steps:
            g[6][step] = note(LEAD, hz(midi_note), vel, min(dur, steps - step))

    # Climax notes: force F#5 and A5 at the golden point (bar 10)
    climax_bar = 10
    cbs = climax_bar * BAR
    g[6][cbs] = note(LEAD, Fs5, 0.95, 6)
    g[6][cbs + 8] = note(LEAD, A5, 0.92, 4)
    g[6][cbs + 12] = note(LEAD, Fs5, 0.88, 4)

    return Pattern(name='ascend', num_steps=steps, num_channels=8,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_void() -> Pattern:
    """4 bars: The breakdown. Strip to overtones + sparse Euclidean percussion.
    Harmonic series pad swells. The silence between stars."""
    steps = BAR * 4
    g = new_grid(8, steps)

    fundamental = Fs3  # F# as root

    for bar in range(4):
        bs = bar * BAR

        # Sparse euclidean kicks: E(3,16) — just enough pulse
        place_euclidean_kicks(g, bar, 3, 0.55)

        # Very sparse hats: E(5,16) at whisper level
        place_euclidean_hats(g, bar, 5, 0.25)

        # Harmonic series pad: overtones 2,3,4,5 of F#
        partials = [2, 3, 4, 5]
        for i, p in enumerate(partials):
            freq = fundamental * p
            midi = freq_to_midi(freq)
            if 36 < midi < 96:
                # Stagger entries using fibonacci timing
                entry_step = FIB[i] % BAR
                vel = 0.18 + i * 0.04
                g[7][bs + entry_step] = note(PAD, freq, vel, BAR - entry_step)

        # Overtone arp: very quiet, using harmonic series [3,5,7,9]
        exotic_partials = harmonic_series_freqs(fundamental, [3, 5, 7])
        for i, freq in enumerate(exotic_partials):
            midi = freq_to_midi(freq)
            if 40 < midi < 90:
                pos = bs + int((i * PHI * 3) % BAR)
                g[5][pos] = note(ARP2, freq, 0.22, 3)

        # Counter melody hint: single note per bar, descending
        counter_notes = [Cs5, B4, A4, Fs4]
        g[6][bs + 8] = note(LEAD, counter_notes[bar], 0.50, 6)

    return Pattern(name='void', num_steps=steps, num_channels=8,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_transcend() -> Pattern:
    """8 bars: Everything returns elevated. The golden cascade resolves.
    
    Polyrhythmic climax: 3-against-4 kick/snare creates emergent accents.
    Melody peaks at highest golden interval. Bass walks through the
    full chord cycle twice. Fibonacci velocity crescendo to final bar."""
    steps = BAR * 8
    g = new_grid(8, steps)

    # Fibonacci velocity curve across all 8 bars
    bar_velocities = fibonacci_velocity_curve(8, 0.72, 0.98)

    for bar in range(8):
        chord = CHORDS[bar % 4]
        bv = bar_velocities[bar]
        bs = bar * BAR

        # POLYRHYTHM: kicks E(4,16) + E(3,16) simultaneously
        # The 4-and-3 cross-rhythm creates 12 unique accents per cycle
        e4 = euclidean_rhythm(4, BAR)
        e3 = euclidean_rhythm(3, BAR)
        for i in range(BAR):
            if e4[i] and e3[i]:
                # Both hit — ACCENT (strongest)
                g[0][bs + i] = note(KICK, hz(36), min(bv + 0.05, 0.98), 1)
            elif e4[i]:
                g[0][bs + i] = note(KICK, hz(36), bv * 0.85, 1)
            elif e3[i]:
                # Ghost from the 3-grid
                g[0][bs + i] = note(KICK, hz(36), bv * 0.45, 1)

        # Full hats + snare
        place_euclidean_hats(g, bar, 7, bv * 0.58)
        place_snare_pattern(g, bar, 3, bv * 0.85)

        # Clap accents
        g[1][bs + 4] = note(CLAP, hz(40), bv * 0.78, 1)
        g[1][bs + 12] = note(CLAP, hz(40), bv * 0.74, 1)

        # Bass: aggressive root-fifth-octave walk
        g[3][bs] = note(BASS, chord[0], bv * 0.88, 4)
        g[3][bs + 4] = note(BASS, chord[0] * 1.5, bv * 0.70, 4)  # fifth
        g[3][bs + 8] = note(BASS, chord[0] * 2, bv * 0.62, 4)    # octave
        g[3][bs + 12] = note(BASS, chord[0], bv * 0.78, 4)       # return

        # Arp layer 1: golden arp, full velocity
        place_golden_arp(g, bar, chord, 4, ARP1, bv * 0.62, offset=bar * 7)

        # Arp layer 2: harmonic overtones, brighter than void
        overtones = harmonic_series_freqs(chord[0], [2, 3, 5])
        for i, ot_freq in enumerate(overtones):
            midi = freq_to_midi(ot_freq)
            if 40 < midi < 96:
                pos = bs + int((i * PHI * 5) % BAR)
                g[5][pos] = note(ARP2, ot_freq, bv * 0.35, 2)

        # Pad: rich sustained chords
        g[7][bs] = note(PAD, chord[1], bv * 0.38, BAR)

    # ── TRANSCENDENCE MELODY ─────────────────────────────────────────────
    # Higher register, longer phrases, fibonacci dynamics
    melody_base = 66  # F#4
    for beat in range(32):  # 8 bars × 4 beats
        bar_idx = beat // 4

        # Golden interval, offset by 17 (prime number — no overlap with ascend)
        midi_note = golden_interval(melody_base, beat + 17)
        midi_note = max(60, min(midi_note, 90))  # higher range

        # Fibonacci crescendo to final beat
        vel = bar_velocities[bar_idx] * 0.92
        vel = max(0.58, min(vel, 0.98))

        dur = 4
        if beat % 8 == 7:
            dur = 6
        if beat >= 28:  # last bar: sustained climax
            dur = 8

        step = beat * 4
        if step < steps:
            g[6][step] = note(LEAD, hz(midi_note), vel, min(dur, steps - step))

    # FINAL CLIMAX: bars 7-8 — force the peak notes
    g[6][7 * BAR] = note(LEAD, Fs5, 0.98, 4)
    g[6][7 * BAR + 4] = note(LEAD, A5, 0.96, 4)
    g[6][7 * BAR + 8] = note(LEAD, Cs6, 0.98, 6)  # C#6 — highest note in piece
    g[6][7 * BAR + 14] = note(LEAD, Fs5, 0.85, 2)  # resolve

    return Pattern(name='transcend', num_steps=steps, num_channels=8,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── SONG ASSEMBLY ─────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_pulse(),        # 0 — 4 bars ~7.2s
        make_emerge(),       # 1 — 8 bars ~14.3s
        make_ascend(),       # 2 — 16 bars ~28.7s
        make_void(),         # 3 — 4 bars ~7.2s
        make_transcend(),    # 4 — 8 bars ~14.3s
    ]
    # Total: 40 bars ≈ 71.6 seconds at 134 BPM

    panning = {
        0:  0.00,    # kick: center
        1:  0.05,    # snare: near center
        2:  0.30,    # hats: right
        3:  0.00,    # bass: center
        4: -0.25,    # arp 1: left
        5:  0.35,    # arp 2 (overtones): right
        6:  0.10,    # lead: near center-right
        7: -0.15,    # pad: slight left
    }

    channel_effects = {
        3: {'reverb': 0.15, 'reverb_mix': 0.05},  # bass: mostly dry
        4: {'reverb': 0.45, 'reverb_mix': 0.20,    # arp 1: room reverb
            'delay': 0.112, 'delay_feedback': 0.30, 'delay_mix': 0.18},
        5: {'reverb': 0.70, 'reverb_mix': 0.40},   # arp 2: spacious
        6: {'reverb': 0.55, 'reverb_mix': 0.22,     # lead: presence
            'delay': 0.224, 'delay_feedback': 0.20, 'delay_mix': 0.12},
        7: {'reverb': 0.85, 'reverb_mix': 0.50},    # pad: deep hall
    }

    return Song(
        title='Golden Cascade — Mathematically-Driven Electronic',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2, 3, 4],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.04,
        master_delay=0.00,
    )


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("╔════════════════════════════════════════════════════╗")
    print("║  GOLDEN CASCADE                                   ║")
    print("║  Mathematics × Electronic Music × ChipForge       ║")
    print("╚════════════════════════════════════════════════════╝")
    print()
    print("  Mathematical techniques:")
    print("    φ  Euclidean rhythms (Bjorklund's algorithm)")
    print("    φ  Golden ratio melody (φ = 1.618... intervals)")
    print("    φ  Fibonacci velocity curves")
    print("    φ  Polyrhythmic layering (3-against-4)")
    print("    φ  Harmonic series overtones")
    print()
    print(f"  Key: F# minor → B minor → F# minor")
    print(f"  BPM: {BPM}")
    print()
    print("  [0-7s]    Pulse     — Euclidean heartbeat")
    print("  [7-21s]   Emerge    — Golden arpeggios awaken")
    print("  [21-50s]  Ascend    — Full ensemble, golden melody")
    print("  [50-57s]  Void      — Overtone meditation")
    print("  [57-72s]  Transcend — Fibonacci climax")
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

    out = Path('output/golden_cascade.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print(f"  φ = {PHI:.10f}")
    print("  The golden ratio is why sunflowers are beautiful.")
    print("  Now it's why this sounds right.")
