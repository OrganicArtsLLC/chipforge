"""
Bach Toccata Rave — BWV 565 reimagined as a 140 BPM rave banger
================================================================

The most recognizable organ piece in history meets four-on-floor kicks.

The famous D-C#-D mordent motif becomes the drop hook on saw_filtered.
The descending flourish (D5-C#5-D5...A4-G4-F4-E4-D4) drives the lead.
Euclidean E(7,16) West African bell pattern on hi-hats for rhythmic depth.

Key: D minor (Aeolian)
BPM: 140
Duration: ~20 seconds (10-12 bars)

8 channels:
  0 - Kick (kick_deep, four-on-floor)
  1 - Clap (noise_clap dur=3, fat backbeat)
  2 - Hi-hats (hat_crisp + hat_open_shimmer, Euclidean E(7,16))
  3 - Bass (bass_growl, aggressive walking line)
  4 - Lead (saw_filtered, Bach toccata motifs)
  5 - Pad (pad_lush, warmth floor)
  6 - Arp (pulse_arp, 16th note Dm chord tone runs — the organ arpeggios)
  7 - Counter-melody (saw_dark, weaving around lead in drop bars 4-6)

Structure:
  [0-~7s]   BUILD   4 bars  — organ arp alone, building intensity
  [~7-20s]  DROP    7 bars  — full groove + Bach hook on saw_filtered
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 140
SPB = 4
BAR = 16

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


# ── Euclidean rhythm (Bjorklund's algorithm) ─────────────────────────────────

def euclidean_rhythm(pulses: int, steps: int) -> list[bool]:
    """E(pulses, steps) — mathematically optimal beat distribution."""
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


# ── Instrument assignments ───────────────────────────────────────────────────
KICK   = 'kick_deep'
CLAP   = 'noise_clap'
HAT_CL = 'hat_crisp'
HAT_OP = 'hat_open_shimmer'
BASS   = 'bass_growl'
LEAD   = 'saw_filtered'
PAD    = 'pad_lush'
ARP    = 'pulse_arp'
COUNTER = 'saw_dark'

# ── D minor note pool ────────────────────────────────────────────────────────
# D minor scale: D E F G A Bb C
D2  = hz(38);  E2  = hz(40);  F2  = hz(41);  G2  = hz(43);  A2  = hz(45)
Bb2 = hz(46);  C3  = hz(48);  D3  = hz(50);  E3  = hz(52);  F3  = hz(53)
G3  = hz(55);  A3  = hz(57);  Bb3 = hz(58);  C4  = hz(60);  D4  = hz(62)
E4  = hz(64);  F4  = hz(65);  G4  = hz(67);  A4  = hz(69);  Bb4 = hz(70)
C5  = hz(72);  D5  = hz(74);  E5  = hz(76);  F5  = hz(77)
# Chromatic: C#5 for the toccata mordent
Cs5 = hz(73)

# Dm chord tones for arp: D F A (+ octave variants)
DM_CHORD_TONES = [D4, F4, A4, D5, A4, F4]  # ascending/descending organ pattern


# ── PATTERN: BUILD (4 bars) ─────────────────────────────────────────────────

def make_build() -> Pattern:
    """4 bars: organ arp alone, building from sparse to dense.
    Emulates the opening of BWV 565 — the arpeggio rising from silence.
    Pad enters bar 2 for warmth. No drums yet."""
    steps = BAR * 4
    g = new_grid(8, steps)

    for bar in range(4):
        bs = bar * BAR

        # Arp channel (6): 16th note runs through Dm chord tones
        # Velocity builds across the 4-bar intro
        vel_base = 0.40 + bar * 0.10  # 0.40 → 0.70

        # Bar 0-1: sparse (every other step), bars 2-3: full 16ths
        for s in range(BAR):
            if bar < 2 and s % 2 != 0:
                continue  # sparse in first 2 bars

            tone_idx = s % len(DM_CHORD_TONES)
            vel = vel_base + (s % 4 == 0) * 0.06
            g[6][bs + s] = note(ARP, DM_CHORD_TONES[tone_idx], vel, 2)

        # Pad enters bar 2 — D minor whole notes for warmth floor
        if bar >= 2:
            pad_vel = 0.20 + (bar - 2) * 0.10
            g[5][bs] = note(PAD, D3, pad_vel, BAR)

        # Lead teaser: the mordent motif in bar 3 only (D5-C#5-D5)
        # This foreshadows the drop — BWV 565 opening gesture
        if bar == 3:
            g[4][bs]     = note(LEAD, D5,  0.65, 2)
            g[4][bs + 2] = note(LEAD, Cs5, 0.60, 2)
            g[4][bs + 4] = note(LEAD, D5,  0.70, 4)
            # Pause (steps 8-11), then the descending flourish preview
            g[4][bs + 12] = note(LEAD, A4, 0.60, 2)
            g[4][bs + 14] = note(LEAD, G4, 0.55, 2)

    return Pattern(name='build', num_steps=steps, num_channels=8,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── PATTERN: DROP (7 bars) ──────────────────────────────────────────────────

def make_drop() -> Pattern:
    """7 bars: Full rave groove with Bach toccata hook.
    Four-on-floor kicks, fat clap backbeat, E(7,16) hats,
    aggressive bass_growl walking line, saw_filtered lead playing
    the iconic D-C#-D mordent and descending flourish."""
    steps = BAR * 7
    g = new_grid(8, steps)

    # E(7,16) hat pattern — West African bell, computed once
    hat_pattern = euclidean_rhythm(7, BAR)

    for bar in range(7):
        bs = bar * BAR

        # ── Channel 0: Kick — four-on-floor ─────────────────────────────
        g[0][bs]      = note(KICK, hz(36), 0.85, 1)
        g[0][bs + 4]  = note(KICK, hz(36), 0.82, 1)
        g[0][bs + 8]  = note(KICK, hz(36), 0.85, 1)
        g[0][bs + 12] = note(KICK, hz(36), 0.82, 1)

        # ── Channel 1: Clap — backbeat 2 & 4, dur=3 for fat body ────────
        g[1][bs + 4]  = note(CLAP, hz(40), 0.78, 3)
        g[1][bs + 12] = note(CLAP, hz(40), 0.78, 3)
        # Snare roll on last bar for energy
        if bar == 6:
            g[1][bs + 13] = note(CLAP, hz(40), 0.55, 2)
            g[1][bs + 14] = note(CLAP, hz(40), 0.65, 2)
            g[1][bs + 15] = note(CLAP, hz(40), 0.75, 1)

        # ── Channel 2: Hi-hats — Euclidean E(7,16) ──────────────────────
        for s in range(BAR):
            if hat_pattern[s]:
                # Alternate closed/open for texture
                if s % 4 == 0:
                    g[2][bs + s] = note(HAT_OP, hz(46), 0.50, 1)
                else:
                    g[2][bs + s] = note(HAT_CL, hz(42), 0.45, 1)

        # ── Channel 3: Bass — aggressive walking bass_growl ──────────────
        # D minor root motion: D-F-A-D pattern with chromatic approach
        bass_patterns = [
            # pattern A: root-driven
            [(0, D2, 0.82, 4), (4, F2, 0.75, 3), (8, A2, 0.78, 3),
             (12, Bb2, 0.72, 2), (14, A2, 0.70, 2)],
            # pattern B: walking with chromatic approach
            [(0, D2, 0.82, 3), (3, E2, 0.70, 2), (6, F2, 0.75, 2),
             (8, G2, 0.72, 3), (12, A2, 0.78, 2), (14, D3, 0.72, 2)],
            # pattern C: octave jumps
            [(0, D2, 0.85, 2), (2, D3, 0.70, 2), (4, A2, 0.75, 4),
             (8, F2, 0.78, 4), (12, D2, 0.80, 2), (14, C3, 0.68, 2)],
        ]
        bp = bass_patterns[bar % 3]
        for (step_off, freq, vel, dur) in bp:
            g[3][bs + step_off] = note(BASS, freq, vel, dur)

        # ── Channel 5: Pad — D minor warmth floor every bar ─────────────
        g[5][bs] = note(PAD, D3, 0.30, BAR)

        # ── Channel 6: Arp — 16th note organ runs through Dm ────────────
        for s in range(BAR):
            tone_idx = s % len(DM_CHORD_TONES)
            # Velocity accents on beat positions
            arp_vel = 0.50 + (s % 4 == 0) * 0.08
            g[6][bs + s] = note(ARP, DM_CHORD_TONES[tone_idx], arp_vel, 2)

    # ── Channel 4: Lead — Bach toccata motifs across the drop ────────────
    # The lead plays the famous BWV 565 themes as 2-bar phrases

    # Bars 0-1: The mordent + descending flourish (THE iconic opening)
    # D5-C#5-D5 ... pause ... A4-G4-F4-E4-D4
    b = 0 * BAR
    g[4][b]      = note(LEAD, D5,  0.85, 3)   # D5 — the bell tone
    g[4][b + 3]  = note(LEAD, Cs5, 0.78, 2)   # C#5 — the mordent turn
    g[4][b + 5]  = note(LEAD, D5,  0.82, 4)   # D5 — resolution, held
    # pause at steps 9-11 (dramatic silence, just like the organ)
    g[4][b + 12] = note(LEAD, A4,  0.75, 2)   # begin descending flourish
    g[4][b + 14] = note(LEAD, G4,  0.72, 2)   # G4

    b = 1 * BAR
    g[4][b]      = note(LEAD, F4,  0.75, 2)   # F4
    g[4][b + 2]  = note(LEAD, E4,  0.72, 2)   # E4
    g[4][b + 4]  = note(LEAD, D4,  0.80, 6)   # D4 — flourish resolves, held long
    # Second half: the mordent again, higher energy
    g[4][b + 10] = note(LEAD, D5,  0.82, 2)
    g[4][b + 12] = note(LEAD, Cs5, 0.78, 2)
    g[4][b + 14] = note(LEAD, D5,  0.85, 2)

    # Bars 2-3: Repeat the hook with variation — descend further
    b = 2 * BAR
    g[4][b]      = note(LEAD, D5,  0.85, 2)
    g[4][b + 2]  = note(LEAD, Cs5, 0.80, 2)
    g[4][b + 4]  = note(LEAD, D5,  0.82, 2)
    g[4][b + 6]  = note(LEAD, Cs5, 0.78, 2)
    g[4][b + 8]  = note(LEAD, D5,  0.85, 4)   # double mordent resolves
    g[4][b + 12] = note(LEAD, A4,  0.78, 4)   # held A4 — dramatic

    b = 3 * BAR
    g[4][b]      = note(LEAD, G4,  0.75, 2)
    g[4][b + 2]  = note(LEAD, F4,  0.72, 2)
    g[4][b + 4]  = note(LEAD, E4,  0.75, 2)
    g[4][b + 6]  = note(LEAD, D4,  0.80, 4)   # resolve low
    g[4][b + 10] = note(LEAD, A4,  0.72, 2)   # pickup
    g[4][b + 12] = note(LEAD, Bb4, 0.75, 2)   # chromatic tension
    g[4][b + 14] = note(LEAD, A4,  0.78, 2)   # resolve

    # Bars 4-5: The organ pedal point — driving repeated D with rhythm
    b = 4 * BAR
    g[4][b]      = note(LEAD, D5,  0.85, 3)
    g[4][b + 3]  = note(LEAD, Cs5, 0.78, 2)
    g[4][b + 5]  = note(LEAD, D5,  0.82, 3)
    g[4][b + 8]  = note(LEAD, F5,  0.85, 4)   # reach up to F5 — new peak!
    g[4][b + 12] = note(LEAD, E5,  0.80, 2)
    g[4][b + 14] = note(LEAD, D5,  0.78, 2)

    b = 5 * BAR
    g[4][b]      = note(LEAD, Cs5, 0.78, 2)
    g[4][b + 2]  = note(LEAD, D5,  0.82, 2)
    g[4][b + 4]  = note(LEAD, A4,  0.75, 4)
    g[4][b + 8]  = note(LEAD, D5,  0.85, 2)
    g[4][b + 10] = note(LEAD, Cs5, 0.78, 2)
    g[4][b + 12] = note(LEAD, D5,  0.85, 4)   # mordent resolves into final bar

    # Bar 6: Climax — the big D5 sustained, then final mordent flourish
    b = 6 * BAR
    g[4][b]      = note(LEAD, D5,  0.85, 4)   # held forte
    g[4][b + 4]  = note(LEAD, F5,  0.85, 4)   # highest note — climax peak
    g[4][b + 8]  = note(LEAD, D5,  0.82, 2)   # mordent one last time
    g[4][b + 10] = note(LEAD, Cs5, 0.78, 2)
    g[4][b + 12] = note(LEAD, D5,  0.85, 4)   # final resolution

    # ── Channel 7: Counter-melody — saw_dark weaving around the lead ──────
    # Bars 4-6 (drop bars 4-8 of the song = bars 4,5,6 of the drop)
    # Plays complementary phrases in the gaps of the main lead melody
    # Lower register (A3-F4 range), darker timbre to contrast saw_filtered

    # Bar 4: counter-melody fills around the lead's D5-Cs5-D5...F5 phrase
    b = 4 * BAR
    g[7][b + 2]  = note(COUNTER, A3,  0.60, 3)   # fills the gap after lead D5
    g[7][b + 6]  = note(COUNTER, F4,  0.58, 2)   # answers the lead's D5 resolve
    g[7][b + 10] = note(COUNTER, E4,  0.55, 2)   # leads into lead's F5 peak
    g[7][b + 14] = note(COUNTER, D4,  0.60, 2)   # resolves under lead's D5

    # Bar 5: more active, trading phrases with the lead
    b = 5 * BAR
    g[7][b + 1]  = note(COUNTER, F4,  0.58, 3)   # weaves under lead's Cs5-D5
    g[7][b + 5]  = note(COUNTER, G4,  0.55, 3)   # fills the A4 hold gap
    g[7][b + 9]  = note(COUNTER, Bb3, 0.60, 3)   # dark chromatic tension
    g[7][b + 13] = note(COUNTER, A3,  0.58, 3)   # resolves before lead's final D5

    # Bar 6 (climax): counter-melody doubles energy with pedal tones
    b = 6 * BAR
    g[7][b + 1]  = note(COUNTER, A3,  0.62, 3)   # under the held D5 forte
    g[7][b + 5]  = note(COUNTER, D4,  0.60, 3)   # octave answer under F5 climax
    g[7][b + 9]  = note(COUNTER, F4,  0.58, 3)   # chromatic climb
    g[7][b + 13] = note(COUNTER, D4,  0.65, 3)   # final resolution with lead

    return Pattern(name='drop', num_steps=steps, num_channels=8,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── SONG ASSEMBLY ────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_build(),   # 0 — 4 bars  ~6.9s
        make_drop(),    # 1 — 7 bars  ~12.0s
    ]
    # Total: 11 bars ~ 18.9 seconds at 140 BPM

    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # clap: near center
        2:  0.28,    # hats: right (standard drum mix)
        3: -0.08,    # bass: slight left
        4:  0.12,    # lead: slight right
        5: -0.20,    # pad: left
        6: -0.30,    # arp: wider left (opposite of hats)
        7:  0.22,    # counter-melody: right (opposite of arp)
    }

    channel_effects = {
        0: {'reverb': 0.06},                                          # kick: subtle room
        1: {'reverb': 0.12},                                          # clap: medium room
        2: {'delay': 0.18, 'delay_feedback': 0.25, 'reverb': 0.08},  # hats: rhythmic space
        3: {'reverb': 0.08},                                          # bass: tight low-end
        4: {'reverb': 0.28, 'delay': 0.20, 'delay_feedback': 0.30},  # lead: rich + slapback
        5: {'reverb': 0.40},                                          # pad: deep hall
        6: {'delay': 0.22, 'delay_feedback': 0.35, 'reverb': 0.10},  # arp: rhythmic echo
        7: {'reverb': 0.25, 'delay': 0.15, 'delay_feedback': 0.20},  # counter: dark space
    }

    return Song(
        title='Bach Toccata Rave — BWV 565 at 140 BPM',
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
    print("╔════════════════════════════════════════════════════╗")
    print("║  BACH TOCCATA RAVE — BWV 565                      ║")
    print("║  D minor | 140 BPM | ~20 seconds                  ║")
    print("╚════════════════════════════════════════════════════╝")
    print()
    print("  The most recognizable organ piece meets four-on-floor.")
    print()
    print("  Structure:")
    print("    [0-7s]   Build  — organ arp rising from silence")
    print("    [7-19s]  Drop   — D-C#-D mordent hook + full rave kit")
    print()
    print("  Rendering...", flush=True)

    song = build_song()

    total_bars = 4 + 7
    beats = total_bars * 4
    est_sec = beats / (BPM / 60.0)
    print(f"  Estimated: {est_sec:.0f}s")

    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    out = Path('output/classical_003_bach_toccata_rave.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Rendered:  {duration:.1f}s")
    print(f"  Size:      {size_mb:.1f} MB")
    print(f"  File:      {out}")
    print()
    print("  Da-da-DAAAA... da da da da da da DAAAA.")
    print("  Bach would have been a raver.")
