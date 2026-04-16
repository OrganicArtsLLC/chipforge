"""
Vivaldi Summer Storm — Four Seasons "Summer" 3rd Movement (Presto)
===================================================================

Vivaldi's relentless Presto reimagined as a 142 BPM EDM banger in G minor.
The famous descending scale runs become saw_filtered lead hooks over a
four-on-floor groove with bass_growl driving the i-iv-V-i progression.

MATHEMATICAL TECHNIQUES:
  - Fibonacci velocity curves on descending scale runs (natural dynamics)
  - Golden ratio climax placement (G5 peak at phi point ~bar 7.4 of 12)
  - Euclidean rhythm influence on hat patterns

Key: G minor (natural)
BPM: 142
Duration: ~20 seconds (12 bars)
Channels: 7
  0 - Kick (kick_deep, four-on-floor)
  1 - Snare/Clap (noise_clap, backbeat)
  2 - Hi-hat (hat_crisp, 16th stream)
  3 - Bass (bass_growl, Gm-Cm-D-Gm progression)
  4 - Lead (saw_filtered, Vivaldi Presto descending runs)
  5 - Pad (pad_lush, harmonic warmth floor)
  6 - Arp (pulse_arp, tremolo violin simulation)

Structure:
  [0-6.8s]   BUILD   4 bars — arp tremolo + pad + hats, tension building
  [6.8-20.3s] DROP    8 bars — full groove + Vivaldi descending hook
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 142
SPB = 4
BAR = 16

# ── Constants ────────────────────────────────────────────────────────────────
PHI = (1 + math.sqrt(5)) / 2  # 1.6180339887...

# ── Helpers ──────────────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, freq: float, vel: float = 0.80, dur: int = 2) -> NoteEvent:
    """Create NoteEvent. Default dur=2 per sound quality rules."""
    return NoteEvent(midi_note=freq_to_midi(freq), velocity=min(vel, 0.85),
                     duration_steps=dur, instrument=inst)

def new_grid(channels: int, steps: int) -> list:
    return [[None] * steps for _ in range(channels)]


def fibonacci_velocity_curve(n: int, min_vel: float = 0.45,
                             max_vel: float = 0.85) -> list[float]:
    """N velocity values following fibonacci-ratio crescendo curve."""
    if n <= 1:
        return [max_vel]
    fibs = [1, 1]
    for i in range(2, n):
        fibs.append(fibs[-1] + fibs[-2])
    max_fib = fibs[-1]
    return [min_vel + (max_vel - min_vel) * (f / max_fib) for f in fibs]


def fibonacci_velocity_arc(n: int, min_vel: float = 0.50,
                           max_vel: float = 0.85) -> list[float]:
    """N velocity values: crescendo to peak then decrescendo (arch shape).
    Peak at the golden ratio point for natural phrasing."""
    if n <= 1:
        return [max_vel]
    peak_idx = int(n / PHI)  # golden ratio placement of peak
    # Build up
    up = fibonacci_velocity_curve(peak_idx + 1, min_vel, max_vel)
    # Come down (reverse fibonacci)
    down_len = n - peak_idx - 1
    if down_len > 0:
        down = fibonacci_velocity_curve(down_len, min_vel, max_vel * 0.9)
        down.reverse()
    else:
        down = []
    return up + down


# ── Instrument assignments ───────────────────────────────────────────────────
KICK   = 'kick_deep'
CLAP   = 'noise_clap'
HAT    = 'hat_crisp'
BASS   = 'bass_growl'
LEAD   = 'saw_filtered'
PAD    = 'pad_lush'
ARP    = 'pulse_arp'

# ── G minor note pool (MIDI numbers) ────────────────────────────────────────
# G minor scale: G A Bb C D Eb F G
# MIDI: G2=43, A2=45, Bb2=46, C3=48, D3=50, Eb3=51, F3=53, G3=55
#       G3=55, A3=57, Bb3=58, C4=60, D4=62, Eb4=63, F4=65, G4=67
#       G4=67, A4=69, Bb4=70, C5=72, D5=74, Eb5=75, F5=77, G5=79

G2  = hz(43);  Bb2 = hz(46);  D3  = hz(50)
G3  = hz(55);  Bb3 = hz(58);  C3  = hz(48);  D3_ = hz(50)
C4  = hz(60);  D4  = hz(62);  Eb4 = hz(63);  F4  = hz(65);  G4  = hz(67)
A4  = hz(69);  Bb4 = hz(70)
C5  = hz(72);  D5  = hz(74);  Eb5 = hz(75);  F5  = hz(77);  G5  = hz(79)

# Bass roots for i-iv-V-i: Gm, Cm, D, Gm
BASS_ROOTS = [hz(43), hz(48), hz(50), hz(43)]  # G2, C3, D3, G2

# Chord voicings for arp/pad
CHORDS = [
    [G3, Bb3, hz(62)],        # Gm: G3-Bb3-D4
    [hz(48), hz(51), G3],     # Cm: C3-Eb3-G3
    [hz(50), hz(54), hz(57)], # D:  D3-F#3-A3
    [G3, Bb3, hz(62)],        # Gm: G3-Bb3-D4 (repeat)
]

# Higher voicings for arp tremolo (violin register)
CHORDS_HIGH = [
    [G4, Bb4, hz(74)],        # Gm: G4-Bb4-D5
    [C5, Eb5, G5],            # Cm: C5-Eb5-G5
    [hz(74), hz(66), A4],     # D:  D5-F#4-A4
    [G4, Bb4, hz(74)],        # Gm: G4-Bb4-D5
]

# ── The Vivaldi Presto descending scale run ──────────────────────────────────
# G5-F5-Eb5-D5-C5-Bb4-A4-G4 (descending G minor scale)
DESCENDING_RUN = [G5, F5, Eb5, D5, C5, Bb4, A4, G4]
# Answering phrase: D5-Eb5-F5-G5 (ascending response)
ASCENDING_RESPONSE = [D5, Eb5, F5, G5]


# ── PATTERN: BUILD (4 bars) ─────────────────────────────────────────────────

def make_build() -> Pattern:
    """4 bars: Arp tremolo (Vivaldi's violin tremolo), pad swell, hats build.
    No kick or snare yet — pure string-section energy building."""
    steps = BAR * 4
    g = new_grid(7, steps)

    for bar in range(4):
        bs = bar * BAR
        chord_idx = bar % 4
        chord_high = CHORDS_HIGH[chord_idx]
        chord_low = CHORDS[chord_idx]

        # Hi-hat: starts sparse, builds to 16th stream
        # Bar 0: quarter notes, Bar 1: 8ths, Bar 2-3: 16ths
        for s in range(BAR):
            step = bs + s
            if bar == 0 and s % 4 == 0:
                g[2][step] = note(HAT, hz(42), 0.35, 1)
            elif bar == 1 and s % 2 == 0:
                g[2][step] = note(HAT, hz(42), 0.40 + (s % 4 == 0) * 0.08, 1)
            elif bar >= 2:
                vel = 0.42 + (s % 4 == 0) * 0.10 + (bar - 2) * 0.04
                g[2][step] = note(HAT, hz(42), min(vel, 0.58), 1)

        # Arp: Vivaldi tremolo simulation — rapid chord tone cycling
        # Velocity builds each bar (fibonacci curve across 4 bars)
        arp_vels = fibonacci_velocity_curve(4, 0.35, 0.65)
        for s in range(BAR):
            step = bs + s
            tone_idx = int((s * PHI) % len(chord_high))  # golden selection
            vel = arp_vels[bar] + (s % 4 == 0) * 0.06
            g[6][step] = note(ARP, chord_high[tone_idx], min(vel, 0.70), 1)

        # Pad: long sustained chords, growing in volume
        pad_vel = 0.20 + bar * 0.08
        g[5][bs] = note(PAD, chord_low[0], min(pad_vel, 0.45), BAR)

        # Bass: subtle root entry in bars 2-3 (foreshadowing the drop)
        if bar >= 2:
            bass_vel = 0.35 + (bar - 2) * 0.12
            g[3][bs] = note(BASS, BASS_ROOTS[chord_idx], min(bass_vel, 0.55), 8)

    return Pattern(name='build', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── PATTERN: DROP (8 bars) ──────────────────────────────────────────────────

def make_drop() -> Pattern:
    """8 bars: THE DROP. Full four-on-floor groove + Vivaldi Presto hook.

    Bars 0-1: Descending Gm scale run (the famous opening)
    Bars 2-3: Ascending response + descending again
    Bars 4-5: Variation with fibonacci velocity arc (climax at phi point)
    Bars 6-7: Final statement, G5 peak, resolution

    The golden ratio places the climax (G5 at max velocity) at bar ~5
    (8/phi = 4.94), which is the start of the second-half intensification."""
    steps = BAR * 8
    g = new_grid(7, steps)

    # ── LEAD MELODY: Vivaldi Presto runs ─────────────────────────────────
    # Each descending run = 8 notes across 8 steps (rapid 16th notes)
    # With fibonacci velocity shaping for natural bow dynamics

    def place_descending_run(start_step: int, vel_base: float = 0.70) -> None:
        """Place the 8-note descending G minor scale run."""
        vels = fibonacci_velocity_arc(8, vel_base * 0.75, vel_base)
        for i, freq in enumerate(DESCENDING_RUN):
            s = start_step + i
            if s < steps:
                g[4][s] = note(LEAD, freq, min(vels[i], 0.85), 2)

    def place_ascending_response(start_step: int, vel_base: float = 0.68) -> None:
        """Place the 4-note ascending answer phrase."""
        vels = fibonacci_velocity_curve(4, vel_base * 0.8, vel_base)
        for i, freq in enumerate(ASCENDING_RESPONSE):
            s = start_step + i
            if s < steps:
                g[4][s] = note(LEAD, freq, min(vels[i], 0.85), 2)

    # -- Bar 0: descending run on beat 1
    place_descending_run(0, 0.72)
    # -- Bar 0 beat 3: ascending response
    place_ascending_response(8, 0.68)
    # -- Bar 0 beat 4 + bar 1 beat 1: second descending run
    place_descending_run(12, 0.75)

    # -- Bar 1: ascending response, then sustained G5 (breath)
    place_ascending_response(BAR + 4, 0.70)
    g[4][BAR + 8] = note(LEAD, G5, 0.78, 4)  # sustained peak
    g[4][BAR + 12] = note(LEAD, D5, 0.65, 4)  # resolve down

    # -- Bars 2-3: call and response intensifies
    place_descending_run(BAR * 2, 0.78)
    place_ascending_response(BAR * 2 + 8, 0.74)
    place_descending_run(BAR * 2 + 12, 0.80)
    place_ascending_response(BAR * 3 + 4, 0.76)
    # Sustained notes to close phrase
    g[4][BAR * 3 + 8] = note(LEAD, G5, 0.82, 4)
    g[4][BAR * 3 + 12] = note(LEAD, F5, 0.72, 4)

    # -- Bars 4-5: GOLDEN RATIO CLIMAX ZONE (bar 4.94 = phi point of 8 bars)
    # Highest energy runs, fibonacci arc velocity peaks here
    place_descending_run(BAR * 4, 0.82)
    place_ascending_response(BAR * 4 + 8, 0.80)
    # Bar 5 beat 1: THE CLIMAX — G5 at maximum velocity, sustained
    g[4][BAR * 5] = note(LEAD, G5, 0.85, 6)  # golden ratio peak note
    g[4][BAR * 5 + 6] = note(LEAD, F5, 0.78, 2)
    place_descending_run(BAR * 5 + 8, 0.83)

    # -- Bars 6-7: final statement, resolution
    place_descending_run(BAR * 6, 0.78)
    place_ascending_response(BAR * 6 + 8, 0.75)
    place_descending_run(BAR * 6 + 12, 0.76)
    # Bar 7: final resolution phrase
    place_ascending_response(BAR * 7, 0.72)
    g[4][BAR * 7 + 4] = note(LEAD, G5, 0.80, 4)   # final G5
    g[4][BAR * 7 + 8] = note(LEAD, D5, 0.70, 4)   # resolve to V
    g[4][BAR * 7 + 12] = note(LEAD, G4, 0.68, 4)  # resolve to root

    # ── DRUMS + BASS + ARP (per bar) ─────────────────────────────────────
    for bar in range(8):
        bs = bar * BAR
        chord_idx = bar % 4  # i-iv-V-i cycles every 4 bars
        bass_root = BASS_ROOTS[chord_idx]
        chord_high = CHORDS_HIGH[chord_idx]
        chord_low = CHORDS[chord_idx]

        # Kick: four-on-floor
        g[0][bs] = note(KICK, hz(36), 0.85, 1)
        g[0][bs + 4] = note(KICK, hz(36), 0.82, 1)
        g[0][bs + 8] = note(KICK, hz(36), 0.85, 1)
        g[0][bs + 12] = note(KICK, hz(36), 0.82, 1)

        # Snare/clap: backbeat on 2 and 4 (with rolls every 4th bar)
        g[1][bs + 4] = note(CLAP, hz(40), 0.78, 3)
        g[1][bs + 12] = note(CLAP, hz(40), 0.78, 3)
        if bar % 4 == 3:
            # Snare roll build (Vivaldi's orchestral crescendo)
            g[1][bs + 13] = note(CLAP, hz(40), 0.52, 1)
            g[1][bs + 14] = note(CLAP, hz(40), 0.62, 1)
            g[1][bs + 15] = note(CLAP, hz(40), 0.74, 1)

        # Hi-hat: full 16th stream (driving Presto energy)
        for s in range(BAR):
            step = bs + s
            if s % 4 == 0:
                g[2][step] = note(HAT, hz(42), 0.55, 1)
            elif s % 2 == 0:
                g[2][step] = note(HAT, hz(42), 0.45, 1)
            else:
                g[2][step] = note(HAT, hz(42), 0.32, 1)

        # Bass: driving Gm-Cm-D-Gm root motion
        g[3][bs] = note(BASS, bass_root, 0.80, 4)
        g[3][bs + 4] = note(BASS, bass_root * 1.5, 0.62, 2)  # fifth
        g[3][bs + 6] = note(BASS, bass_root * 2, 0.55, 2)    # octave
        g[3][bs + 8] = note(BASS, bass_root, 0.78, 4)
        g[3][bs + 12] = note(BASS, bass_root * 4/3, 0.58, 2)  # fourth
        g[3][bs + 14] = note(BASS, bass_root * 1.5, 0.55, 2)  # fifth pickup

        # Pad: sustained chord warmth floor (present in every section)
        g[5][bs] = note(PAD, chord_low[0], 0.35, BAR)

        # Arp: Vivaldi tremolo continues underneath the lead
        # Golden ratio tone selection, quieter than build (supporting role)
        for s in range(BAR):
            step = bs + s
            if g[4][step] is None:  # don't clash with lead
                tone_idx = int((s * PHI) % len(chord_high))
                vel = 0.38 + (s % 4 == 0) * 0.06
                g[6][step] = note(ARP, chord_high[tone_idx], min(vel, 0.50), 1)

    return Pattern(name='drop', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── SONG ASSEMBLY ────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_build(),   # 0 — 4 bars  ~6.8s
        make_drop(),    # 1 — 8 bars  ~13.5s
    ]
    # Total: 12 bars ~ 20.3 seconds at 142 BPM

    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # clap: near center
        2:  0.28,    # hats: right (standard drum mix)
        3: -0.08,    # bass: near center-left
        4:  0.12,    # lead: slight right
        5: -0.20,    # pad: left (opposite arp)
        6: -0.30,    # arp: left-wide (tremolo violin section)
    }

    channel_effects = {
        0: {'reverb': 0.06},                                          # kick: subtle room
        1: {'reverb': 0.12},                                          # clap: medium room
        2: {'delay': 0.18, 'delay_feedback': 0.25, 'reverb': 0.08},  # hats: rhythmic space
        3: {'reverb': 0.08},                                          # bass: tight low-end
        4: {'reverb': 0.28, 'delay': 0.20, 'delay_feedback': 0.30},  # lead: rich + slapback
        5: {'reverb': 0.40},                                          # pad: deep hall
        6: {'delay': 0.22, 'delay_feedback': 0.35, 'reverb': 0.10},  # arp: rhythmic echo
    }

    return Song(
        title='Vivaldi Summer Storm — Presto EDM',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.10,
        master_delay=0.0,
    )


# ── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("╔════════════════════════════════════════════════════════╗")
    print("║  VIVALDI SUMMER STORM                                 ║")
    print("║  Four Seasons 'Summer' Presto x EDM x ChipForge      ║")
    print("╚════════════════════════════════════════════════════════╝")
    print()
    print(f"  Key: G minor | BPM: {BPM} | ~20 seconds")
    print()
    print("  Mathematical techniques:")
    print("    - Fibonacci velocity curves on descending scale runs")
    print("    - Golden ratio climax placement (G5 at phi point)")
    print("    - Golden ratio arp tone selection (tremolo pattern)")
    print()
    print("  Structure:")
    print("    [0-6.8s]    Build  — arp tremolo + pad swell, tension")
    print("    [6.8-20.3s] Drop   — four-on-floor + Vivaldi Presto hook")
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

    out = Path('output/classical_004_vivaldi_summer_storm.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  Vivaldi knew the storm was coming.")
    print("  Now it drops at 142 BPM.")
