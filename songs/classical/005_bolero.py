"""
Bolero — Maurice Ravel (1928, Public Domain)
=============================================

The greatest crescendo in all of music. One melody, one rhythm, repeated
endlessly with ever-growing instrumentation. 15 minutes in the original --
we capture the essence in ~3.5 minutes.

The ENTIRE piece is mathematically simple:
  - One snare pattern that NEVER changes (the bolero rhythm)
  - Theme A (8 bars) + Theme B (8 bars) = 16-bar cycle
  - Each cycle adds instruments and raises velocity
  - The ONLY thing that changes is orchestration and dynamics
  - Final 4 bars: key change to E major, then crash back to C

Ravel called it "a piece for orchestra without music" -- pure orchestration
and crescendo. Perfect for AI to compute mathematically.

Key: C major (Ravel's original)
BPM: 72 (the original's hypnotic tempo)
Time: 3/4 (BAR = 12 steps = 3 beats x 4 subdivisions)
Channels: 9
  0 - Snare/rhythm  (noise_clap -- the eternal bolero pattern)
  1 - Kick           (kick_deep -- enters pass 5)
  2 - Hat            (hat_open_shimmer -- enters pass 3 as cymbal color)
  3 - Bass           (bass_smooth -> bass_growl as it grows)
  4 - Lead melody    (rotates: pluck_mellow -> add_warm_lead -> lead_expressive)
  5 - Second voice   (enters pass 2, harmonizes in thirds)
  6 - Pad            (pad_evolving -- enters pass 3)
  7 - Strings        (add_string -- enters pass 4)
  8 - Counter/Arp    (pulse_warm -- rhythmic figuration, enters pass 3)

Structure (42 bars total):
  Pass 1: Theme A+B (16 bars) -- solo flute (pluck_mellow), pp
  Pass 2: Theme A+B (16 bars) -- clarinet joins (add_warm_lead), p
  Pass 3: Theme A   (8 bars)  -- oboe (lead_expressive) + pad + arp, mp
  Pass 4: Theme B   (8 bars)  -- strings + full winds, mf (SKIPPED A -- Ravel does this)
           [We use A from pass 3 + B from pass 4 = 16 bars total for passes 3-4]
  Finale:  10 bars  -- FULL ORCHESTRA ff, key change to E major bar 7, crash back

Total: 42 bars x 12 steps = 504 steps @ 72 BPM in 3/4 = ~3.5 min
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from src.effects import (
    apply_compressor,
    apply_sidechain,
    apply_distortion,
    apply_parametric_eq,
    apply_stereo_widener,
    apply_master_bus,
    MasterBusConfig,
    EQBand,
)
from pathlib import Path
import numpy as np

BPM = 72
SPB = 4       # steps per beat
BAR = 12      # 3/4 time: 3 beats x 4 subdivisions
NUM_CH = 9

# ---------------------------------------------------------------------------
# MIDI helpers
# ---------------------------------------------------------------------------

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))


def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)


def note(inst: str, midi: int, vel: float = 0.50, dur: int = 2) -> NoteEvent:
    """Create a melodic note event. Velocity capped at 0.85, duration >= 2."""
    return NoteEvent(
        midi_note=midi,
        velocity=min(vel, 0.85),
        duration_steps=max(dur, 2),
        instrument=inst,
    )


def drum(inst: str, midi: int, vel: float = 0.50, dur: int = 1) -> NoteEvent:
    """Create a percussion note event. Velocity capped at 0.85."""
    return NoteEvent(
        midi_note=midi,
        velocity=min(vel, 0.85),
        duration_steps=max(dur, 1),
        instrument=inst,
    )


def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]


# ---------------------------------------------------------------------------
# MIDI note definitions -- C major
# C3=48, D3=50, E3=52, F3=53, G3=55, A3=57, B3=59
# C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71
# C5=72, D5=74, E5=76, F5=77, G5=79, A5=81
# E major key change: E4=64, F#4=66, G#4=68, A4=69, B4=71, C#5=73, D#5=75
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# THE BOLERO RHYTHM -- The iconic snare pattern in 3/4
# ta-da-da ta-da-da ta-da-da-da-da-da
# In 12 steps (3 beats x 4 subdivisions):
#   Beat 1: step 0 (accent), step 2, step 3
#   Beat 2: step 4 (accent), step 6, step 7
#   Beat 3: step 8, step 9, step 10, step 11 (triplet fill subdivision)
# The pattern is: ONE-rest-two-three | ONE-rest-two-three | one-two-three-four
# ---------------------------------------------------------------------------

BOLERO_RHYTHM = [
    (0, True),    # Beat 1 -- accent
    (2, False),   # "da"
    (3, False),   # "da"
    (4, True),    # Beat 2 -- accent
    (6, False),   # "da"
    (7, False),   # "da"
    (8, False),   # Beat 3 -- triplet fill begins
    (9, False),   # "da"
    (10, False),  # "da"
    (11, False),  # "da"
]


def write_bolero_snare(grid: list, bar_offset: int, num_bars: int,
                       vel: float) -> None:
    """Write the unchanging bolero snare pattern across bars."""
    for bar in range(num_bars):
        s = (bar_offset + bar) * BAR
        for (step, accent) in BOLERO_RHYTHM:
            v = vel * (1.15 if accent else 0.80)
            grid[0][s + step] = drum('noise_clap', 38, min(v, 0.85), 2)


# ---------------------------------------------------------------------------
# THEME A -- The sinuous C major melody (8 bars)
# Ravel's Theme A: stepwise, snake-like, centered around C4-G4
# Each bar = 12 steps (3 beats). Notes are (bar_relative_step, midi, duration)
# ---------------------------------------------------------------------------

THEME_A = [
    # Bar 1: C4 held, then D4
    (0, 60, 6),    # C4 -- long opening note (dotted quarter)
    (6, 62, 3),    # D4
    (9, 64, 3),    # E4
    # Bar 2: F4 to E4 descent
    (12, 65, 4),   # F4
    (16, 64, 4),   # E4
    (20, 62, 4),   # D4
    # Bar 3: C4 up to E4
    (24, 60, 6),   # C4 -- held
    (30, 62, 3),   # D4
    (33, 64, 3),   # E4
    # Bar 4: D4 ornamental turn
    (36, 62, 4),   # D4
    (40, 64, 2),   # E4
    (42, 62, 2),   # D4
    (44, 60, 4),   # C4
    # Bar 5: ascending run C4-G4
    (48, 60, 3),   # C4
    (51, 62, 3),   # D4
    (54, 64, 3),   # E4
    (57, 65, 3),   # F4
    # Bar 6: G4 peak, descent
    (60, 67, 6),   # G4 -- peak, held
    (66, 65, 3),   # F4
    (69, 64, 3),   # E4
    # Bar 7: D4 to C4, graceful descent
    (72, 62, 4),   # D4
    (76, 64, 2),   # E4 (grace)
    (78, 62, 2),   # D4
    (80, 60, 4),   # C4
    # Bar 8: resolution on C4
    (84, 60, 8),   # C4 -- long resolution
    (92, 62, 2),   # D4 pickup to Theme B
    (94, 60, 2),   # C4
]

# ---------------------------------------------------------------------------
# THEME B -- Starting on G4, reaching higher, more expressive
# ---------------------------------------------------------------------------

THEME_B = [
    # Bar 1: G4 opening
    (0, 67, 6),    # G4 -- held
    (6, 69, 3),    # A4
    (9, 71, 3),    # B4
    # Bar 2: C5 peak descent
    (12, 72, 4),   # C5 -- high peak
    (16, 71, 4),   # B4
    (20, 69, 4),   # A4
    # Bar 3: G4 approach from below
    (24, 67, 6),   # G4
    (30, 69, 3),   # A4
    (33, 67, 3),   # G4
    # Bar 4: expressive turn on F4-G4
    (36, 65, 4),   # F4
    (40, 67, 2),   # G4
    (42, 69, 2),   # A4
    (44, 67, 4),   # G4
    # Bar 5: ascending to D5
    (48, 67, 3),   # G4
    (51, 69, 3),   # A4
    (54, 71, 3),   # B4
    (57, 72, 3),   # C5
    # Bar 6: D5 peak -- the climax of Theme B
    (60, 74, 6),   # D5 -- highest note, held
    (66, 72, 3),   # C5
    (69, 71, 3),   # B4
    # Bar 7: descending resolution
    (72, 69, 4),   # A4
    (76, 67, 4),   # G4
    (80, 65, 4),   # F4
    # Bar 8: resolution to C4 via E4
    (84, 64, 4),   # E4
    (88, 62, 4),   # D4
    (92, 60, 8),   # C4 -- final resolution, long
]


def write_melody(grid: list, channel: int, theme: list, bar_offset: int,
                 inst: str, vel: float) -> None:
    """Write a theme melody into a grid channel at the given bar offset."""
    base = bar_offset * BAR
    for (step, midi, dur) in theme:
        s = base + step
        if s < len(grid[channel]):
            grid[channel][s] = note(inst, midi, vel, max(dur, 2))


def write_harmony_thirds(grid: list, channel: int, theme: list,
                         bar_offset: int, inst: str, vel: float) -> None:
    """Write a harmony line a third below the melody."""
    base = bar_offset * BAR
    # In C major, a diatonic third below:
    # C->A(-3), D->B(-3), E->C(-4), F->D(-3), G->E(-3), A->F(-4), B->G(-3)
    # Simplification: subtract 3 or 4 semitones depending on scale degree
    # Major thirds below for most notes in C major
    third_map = {
        60: 57, 62: 59, 64: 60, 65: 62, 67: 64, 69: 65, 71: 67,
        72: 69, 74: 71, 76: 72, 77: 74, 79: 76, 81: 77,
        # E major key change notes
        66: 64, 68: 64, 73: 69, 75: 72,
    }
    for (step, midi, dur) in theme:
        s = base + step
        harm_midi = third_map.get(midi, midi - 3)
        if s < len(grid[channel]):
            grid[channel][s] = note(inst, harm_midi, vel * 0.85, max(dur, 2))


# ---------------------------------------------------------------------------
# PASS 1: Solo voice -- the lonely flute (16 bars)
# Like Ravel's opening: a single instrument against the snare drum
# ---------------------------------------------------------------------------

def make_pass1() -> Pattern:
    """Pass 1: Solo pluck_mellow (flute) + snare. pp dynamics."""
    steps = BAR * 16
    g = new_grid(steps)

    # The eternal snare -- very quiet, like a distant drum
    write_bolero_snare(g, 0, 16, vel=0.28)

    # Theme A (bars 0-7) then Theme B (bars 8-15)
    write_melody(g, 4, THEME_A, 0, 'pluck_mellow', 0.35)
    write_melody(g, 4, THEME_B, 8, 'pluck_mellow', 0.38)

    # Pad: ultra-quiet sustained C3 chord, barely there -- concert hall air
    for bar in range(0, 16, 4):
        s = bar * BAR
        g[6][s] = note('pad_evolving', 48, 0.15, BAR * 4)  # C3

    return Pattern(name='pass1', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# PASS 2: Clarinet joins -- two voices (16 bars)
# ---------------------------------------------------------------------------

def make_pass2() -> Pattern:
    """Pass 2: add_warm_lead (clarinet) takes melody, pluck harmonizes. p dynamics."""
    steps = BAR * 16
    g = new_grid(steps)

    # Snare -- slightly louder
    write_bolero_snare(g, 0, 16, vel=0.35)

    # Lead: add_warm_lead takes the melody
    write_melody(g, 4, THEME_A, 0, 'add_warm_lead', 0.45)
    write_melody(g, 4, THEME_B, 8, 'add_warm_lead', 0.48)

    # Second voice: harmony in thirds (the joining clarinet duet)
    write_harmony_thirds(g, 5, THEME_A, 0, 'pluck_mellow', 0.35)
    write_harmony_thirds(g, 5, THEME_B, 8, 'pluck_mellow', 0.38)

    # Bass enters -- very gentle, root notes only on beat 1
    for bar in range(16):
        s = bar * BAR
        # Alternate C2 and G2 (tonic and dominant)
        bass_note = 36 if bar % 4 < 2 else 43  # C2 / G2
        g[3][s] = note('bass_smooth', bass_note, 0.30, BAR)

    # Pad: slightly more present
    for bar in range(0, 16, 4):
        s = bar * BAR
        g[6][s] = note('pad_evolving', 48, 0.22, BAR * 4)  # C3

    return Pattern(name='pass2', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# PASS 3: Oboe + pad + arp join -- Theme A only (8 bars)
# The orchestration thickens. Three new voices enter.
# ---------------------------------------------------------------------------

def make_pass3() -> Pattern:
    """Pass 3: lead_expressive (oboe) + pad + arp. mp dynamics. Theme A only."""
    steps = BAR * 8
    g = new_grid(steps)

    # Snare -- growing
    write_bolero_snare(g, 0, 8, vel=0.42)

    # Lead: expressive saw with vibrato and filter envelope
    write_melody(g, 4, THEME_A, 0, 'lead_expressive', 0.55)

    # Second voice: warm lead harmonizes
    write_harmony_thirds(g, 5, THEME_A, 0, 'add_warm_lead', 0.45)

    # Hat enters -- light cymbal color on beat 1 of each bar
    for bar in range(8):
        s = bar * BAR
        g[2][s] = drum('hat_open_shimmer', 42, 0.25, 2)
        # Add a light tap on beat 3
        g[2][s + 8] = drum('hat_open_shimmer', 42, 0.18, 2)

    # Bass: more rhythmic, pulsing on beats 1 and 3
    for bar in range(8):
        s = bar * BAR
        bass_note = 36 if bar % 4 < 2 else 43
        g[3][s] = note('bass_smooth', bass_note, 0.42, 6)
        g[3][s + 8] = note('bass_smooth', bass_note, 0.35, 4)

    # Pad: full sustained chords now
    # C major: C-E-G voiced as C3-G3 (root + fifth, pad fills the rest)
    for bar in range(0, 8, 2):
        s = bar * BAR
        chord_root = 48 if bar % 4 < 2 else 55  # C3 or G3
        g[6][s] = note('pad_evolving', chord_root, 0.35, BAR * 2)

    # Arp: rhythmic figuration -- C major broken chord pattern
    arp_pattern_a = [60, 64, 67, 72, 67, 64]  # C4 E4 G4 C5 G4 E4
    for bar in range(8):
        s = bar * BAR
        for step in range(0, BAR, 2):
            idx = (step // 2) % len(arp_pattern_a)
            midi = arp_pattern_a[idx]
            # Shift arp for dominant bars
            if bar % 4 >= 2:
                midi += 7  # up a fifth for G-based bars
                if midi > 79:
                    midi -= 12
            v = 0.32 + (bar / 8) * 0.08
            g[8][s + step] = note('pulse_warm', midi, min(v, 0.45), 2)

    return Pattern(name='pass3', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# PASS 4: Strings enter -- Theme B (8 bars)
# Now we have full winds + strings. The sound is getting BIG.
# ---------------------------------------------------------------------------

def make_pass4() -> Pattern:
    """Pass 4: add_string joins, bass_growl takes over. mf dynamics. Theme B only."""
    steps = BAR * 8
    g = new_grid(steps)

    # Snare -- strong now
    write_bolero_snare(g, 0, 8, vel=0.52)

    # Lead: expressive, louder
    write_melody(g, 4, THEME_B, 0, 'lead_expressive', 0.62)

    # Second voice: add_warm_lead harmony
    write_harmony_thirds(g, 5, THEME_B, 0, 'add_warm_lead', 0.52)

    # Hat: beat 1 + offbeats
    for bar in range(8):
        s = bar * BAR
        g[2][s] = drum('hat_open_shimmer', 42, 0.32, 2)
        g[2][s + 4] = drum('hat_open_shimmer', 42, 0.22, 2)
        g[2][s + 8] = drum('hat_open_shimmer', 42, 0.28, 2)

    # Bass: bass_growl now, more aggressive
    for bar in range(8):
        s = bar * BAR
        bass_note = 36 if bar % 4 < 2 else 43
        g[3][s] = note('bass_growl', bass_note, 0.52, 4)
        g[3][s + 4] = note('bass_growl', bass_note, 0.42, 4)
        g[3][s + 8] = note('bass_growl', bass_note, 0.48, 4)

    # Pad: lush, wide
    for bar in range(0, 8, 2):
        s = bar * BAR
        chord_root = 48 if bar % 4 < 2 else 55
        g[6][s] = note('pad_evolving', chord_root, 0.45, BAR * 2)

    # Strings: sustained chord tones, entering majestically
    # Strings play long notes: root + third + fifth across bars
    string_voicings = [
        (48, 52, 55),  # C3 E3 G3 (C major)
        (48, 52, 55),
        (55, 59, 62),  # G3 B3 D4 (G major)
        (55, 59, 62),
        (48, 52, 55),
        (48, 52, 55),
        (55, 59, 62),
        (55, 59, 62),
    ]
    for bar in range(8):
        s = bar * BAR
        voicing = string_voicings[bar]
        vel_str = 0.38 + (bar / 8) * 0.12
        # Root note as the string voice
        g[7][s] = note('add_string', voicing[0], min(vel_str, 0.55), BAR)

    # Arp: more active, 16th-note feel
    arp_pattern_b = [67, 71, 72, 76, 72, 71]  # G4 B4 C5 E5 C5 B4
    for bar in range(8):
        s = bar * BAR
        for step in range(BAR):
            idx = step % len(arp_pattern_b)
            midi = arp_pattern_b[idx]
            if bar % 4 >= 2:
                midi -= 5  # shift down for variety
            v = 0.38 + (bar / 8) * 0.10
            g[8][s + step] = note('pulse_warm', midi, min(v, 0.52), 2)

    return Pattern(name='pass4', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# FINALE: Full orchestra -- 10 bars
# Bars 1-6: FULL POWER in C major, ff
# Bar 7-8: THE KEY CHANGE to E major (Ravel's famous modulation!)
# Bar 9-10: CRASH back to C major, final thunderous resolution
# ---------------------------------------------------------------------------

# Theme A fragment for the finale (first 4 bars only, transposed to E major for key change)
THEME_A_E_MAJOR = [
    # E major: E4=64, F#4=66, G#4=68, A4=69, B4=71, C#5=73, D#5=75
    # Bar 1: E4 held, then F#4
    (0, 64, 6),    # E4
    (6, 66, 3),    # F#4
    (9, 68, 3),    # G#4
    # Bar 2: A4 to G#4 descent
    (12, 69, 4),   # A4
    (16, 68, 4),   # G#4
    (20, 66, 4),   # F#4
]

# Final resolution: crashing back to C
FINALE_RESOLUTION = [
    # Bar 1: C5 held triumphantly
    (0, 72, 8),    # C5 -- TRIUMPHANT
    (8, 67, 4),    # G4
    # Bar 2: Final C4 -- the piece ends
    (12, 60, 12),  # C4 -- long, final
]


def make_finale() -> Pattern:
    """Finale: FULL ORCHESTRA ff. Key change to E major, crash back to C."""
    steps = BAR * 10
    g = new_grid(steps)

    # Snare -- FULL POWER, the bolero rhythm at its loudest
    write_bolero_snare(g, 0, 10, vel=0.65)

    # Kick enters for the first time! -- thunderous on beats 1 and 3
    for bar in range(10):
        s = bar * BAR
        g[1][s] = drum('kick_deep', 36, 0.75, 2)
        g[1][s + 8] = drum('kick_deep', 36, 0.60, 2)
        # Bar 9-10: kick on every beat for maximum impact
        if bar >= 8:
            g[1][s + 4] = drum('kick_deep', 36, 0.68, 2)

    # Hat: full shimmer
    for bar in range(10):
        s = bar * BAR
        for step in range(0, BAR, 2):
            v = 0.38 if step == 0 else 0.28
            g[2][s + step] = drum('hat_open_shimmer', 42, v, 2)

    # --- BARS 0-5: Theme A in C major, FULL POWER ---
    # Lead: lead_expressive at peak velocity
    write_melody(g, 4, THEME_A, 0, 'lead_expressive', 0.78)
    # (Theme A is 8 bars but we only use first 6 bars before key change)

    # Second voice: add_warm_lead harmony, loud
    write_harmony_thirds(g, 5, THEME_A, 0, 'add_warm_lead', 0.65)

    # --- BARS 6-7: KEY CHANGE TO E MAJOR ---
    base_kc = 6 * BAR
    for (step, midi, dur) in THEME_A_E_MAJOR:
        s = base_kc + step
        if s < steps:
            g[4][s] = note('lead_expressive', midi, 0.82, max(dur, 2))
    # Harmony in E major (third below: E->C#, F#->D#, G#->E, A->F#, B->G#)
    e_maj_thirds = {64: 61, 66: 63, 68: 64, 69: 66, 71: 68, 73: 69, 75: 71}
    for (step, midi, dur) in THEME_A_E_MAJOR:
        s = base_kc + step
        harm = e_maj_thirds.get(midi, midi - 4)
        if s < steps:
            g[5][s] = note('add_warm_lead', harm, 0.72, max(dur, 2))

    # --- BARS 8-9: CRASH BACK TO C MAJOR ---
    base_res = 8 * BAR
    for (step, midi, dur) in FINALE_RESOLUTION:
        s = base_res + step
        if s < steps:
            g[4][s] = note('lead_expressive', midi, 0.85, max(dur, 2))
    # Resolution harmony
    res_thirds = [(0, 67, 8), (8, 64, 4), (12, 57, 12)]  # G4, E4, A3
    for (step, midi, dur) in res_thirds:
        s = base_res + step
        if s < steps:
            g[5][s] = note('add_warm_lead', midi, 0.78, max(dur, 2))

    # Bass: THUNDEROUS -- bass_growl, driving rhythm
    for bar in range(10):
        s = bar * BAR
        if bar < 6:
            bass_note = 36 if bar % 4 < 2 else 43  # C2 / G2
        elif bar < 8:
            bass_note = 40  # E2 -- key change!
        else:
            bass_note = 36  # C2 -- crash back
        g[3][s] = note('bass_growl', bass_note, 0.68, 4)
        g[3][s + 4] = note('bass_growl', bass_note, 0.58, 4)
        g[3][s + 8] = note('bass_growl', bass_note, 0.62, 4)

    # Pad: massive sustained chords
    # C major section
    for bar in range(0, 6, 2):
        s = bar * BAR
        g[6][s] = note('pad_evolving', 48, 0.58, BAR * 2)  # C3
    # E major key change
    g[6][6 * BAR] = note('pad_evolving', 52, 0.62, BAR * 2)  # E3
    # Resolution
    g[6][8 * BAR] = note('pad_evolving', 48, 0.65, BAR * 2)  # C3

    # Strings: FULL, sustained, rich
    for bar in range(10):
        s = bar * BAR
        if bar < 6:
            str_note = 48 if bar % 4 < 2 else 55  # C3 / G3
        elif bar < 8:
            str_note = 52  # E3 -- key change
        else:
            str_note = 48  # C3 -- resolution
        g[7][s] = note('add_string', str_note, min(0.55 + bar * 0.02, 0.72), BAR)

    # Arp: blazing fast broken chords
    arp_c = [60, 64, 67, 72, 76, 79, 72, 67]  # C major up and down
    arp_e = [64, 68, 71, 76, 80, 83, 76, 71]  # E major up and down
    for bar in range(10):
        s = bar * BAR
        pattern = arp_e if 6 <= bar < 8 else arp_c
        for step in range(BAR):
            idx = step % len(pattern)
            v = 0.48 + (bar / 10) * 0.15
            g[8][s + step] = note('pulse_warm', pattern[idx], min(v, 0.65), 2)

    # Final bar: everything sustains, then silence
    # Last 2 steps of bar 10 are empty (the music stops, the hall resonates)

    return Pattern(name='finale', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# SONG ASSEMBLY
# ---------------------------------------------------------------------------

def build_song() -> Song:
    """Assemble all passes into the complete Bolero."""
    patterns = [
        make_pass1(),    # 0: 16 bars -- solo flute + snare (pp)
        make_pass2(),    # 1: 16 bars -- clarinet duet (p)
        make_pass3(),    # 2: 8 bars  -- oboe + pad + arp (mp)
        make_pass4(),    # 3: 8 bars  -- strings enter (mf)
        make_finale(),   # 4: 10 bars -- FULL ORCHESTRA (ff)
    ]
    # Total: 16+16+8+8+10 = 58 bars in 3/4 @ 72 BPM
    # = 58 * 3 beats / 72 BPM * 60 = 145 sec = ~2.4 min
    # (compact but captures the full arc)

    panning = {
        0: 0.0,      # snare -- center (the heartbeat)
        1: 0.0,      # kick -- center
        2: 0.25,     # hat -- slight right
        3: 0.0,      # bass -- center
        4: 0.08,     # lead melody -- slight right (soloist position)
        5: -0.15,    # second voice -- left (duet partner)
        6: -0.22,    # pad -- left
        7: 0.20,     # strings -- right
        8: -0.30,    # arp -- wide left
    }

    channel_effects = {
        # Snare: concert hall reverb -- the snare should echo in the space
        0: {
            'reverb': 0.55, 'reverb_mix': 0.28, 'reverb_damping': 0.35,
        },
        # Kick: tight but present
        1: {
            'reverb': 0.20, 'reverb_mix': 0.08, 'reverb_damping': 0.6,
        },
        # Hat: shimmer with delay
        2: {
            'delay': 0.12, 'delay_feedback': 0.20, 'delay_mix': 0.15,
            'reverb': 0.30, 'reverb_mix': 0.15,
        },
        # Bass: controlled room
        3: {
            'reverb': 0.15, 'reverb_mix': 0.06,
        },
        # Lead melody: the STAR -- concert hall reverb + gentle delay
        4: {
            'reverb': 0.70, 'reverb_mix': 0.35, 'reverb_damping': 0.3,
            'delay': 0.18, 'delay_feedback': 0.25, 'delay_mix': 0.18,
        },
        # Second voice: similar to lead but slightly less reverb
        5: {
            'reverb': 0.60, 'reverb_mix': 0.30, 'reverb_damping': 0.3,
            'delay': 0.15, 'delay_feedback': 0.20, 'delay_mix': 0.14,
        },
        # Pad: DEEP hall reverb -- orchestral warmth
        6: {
            'reverb': 0.85, 'reverb_mix': 0.45, 'reverb_damping': 0.25,
            'chorus': 0.30, 'chorus_detune': 6.0, 'chorus_delay': 25.0,
        },
        # Strings: rich hall reverb + chorus for ensemble width
        7: {
            'reverb': 0.75, 'reverb_mix': 0.38, 'reverb_damping': 0.3,
            'chorus': 0.25, 'chorus_detune': 7.0, 'chorus_delay': 20.0,
        },
        # Arp: rhythmic delay + moderate reverb
        8: {
            'delay': 0.20, 'delay_feedback': 0.30, 'delay_mix': 0.22,
            'reverb': 0.45, 'reverb_mix': 0.22,
        },
    }

    return Song(
        title='Bolero -- Maurice Ravel (1928)',
        author='ChipForge v0.4.0 / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=list(range(5)),
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.15,
        master_delay=0.08,
    )


# ---------------------------------------------------------------------------
# POST-PROCESSING: Concert hall mastering chain
# ---------------------------------------------------------------------------

def post_process(audio: np.ndarray) -> np.ndarray:
    """Apply production-grade post-processing for orchestral clarity."""
    print("  Post-processing: EQ...", flush=True)

    # 1. Parametric EQ -- sculpt the orchestral sound
    eq_bands = [
        EQBand(freq_hz=30.0, gain_db=0.0, q=0.707, band_type="highpass"),   # Sub-rumble cut
        EQBand(freq_hz=80.0, gain_db=1.5, q=0.8, band_type="lowshelf"),     # Warm bass shelf
        EQBand(freq_hz=300.0, gain_db=-1.0, q=1.0, band_type="peak"),       # Cut muddiness
        EQBand(freq_hz=2500.0, gain_db=2.0, q=1.2, band_type="peak"),       # Woodwind presence
        EQBand(freq_hz=5000.0, gain_db=1.5, q=1.5, band_type="peak"),       # String brilliance
        EQBand(freq_hz=12000.0, gain_db=1.5, q=0.7, band_type="highshelf"), # Air/hall shimmer
    ]
    for ch in range(2):
        audio[:, ch] = apply_parametric_eq(audio[:, ch], eq_bands)

    # 2. Subtle tape saturation -- warm analog character
    print("  Post-processing: saturation...", flush=True)
    for ch in range(2):
        audio[:, ch] = apply_distortion(audio[:, ch], drive=0.06, mode="soft")

    # 3. Sidechain from low-end -- subtle orchestral pump
    print("  Post-processing: sidechain...", flush=True)
    lp_bands = [EQBand(freq_hz=120.0, gain_db=0.0, q=0.707, band_type="lowpass")]
    lp_for_sc = []
    for ch in range(2):
        lp_ch = apply_parametric_eq(audio[:, ch].copy(), lp_bands)
        lp_for_sc.append(lp_ch)
    sc_signal = (lp_for_sc[0] + lp_for_sc[1]) * 0.5
    for ch in range(2):
        audio[:, ch] = apply_sidechain(
            audio[:, ch], sc_signal,
            threshold_db=-20.0, ratio=2.5,
            attack_ms=3.0, release_ms=120.0,
        )

    # 4. Glue compression -- hold the crescendo together
    print("  Post-processing: bus compression...", flush=True)
    for ch in range(2):
        audio[:, ch] = apply_compressor(
            audio[:, ch],
            threshold_db=-12.0, ratio=2.0,
            attack_ms=15.0, release_ms=100.0,
            makeup_db=1.5, knee_db=8.0,
        )

    # 5. Stereo widening -- concert hall spaciousness
    print("  Post-processing: stereo widening...", flush=True)
    audio = apply_stereo_widener(audio, width=1.40)

    # 6. Master bus chain -- final mastering
    print("  Post-processing: master bus...", flush=True)
    master_config = MasterBusConfig(
        highpass_hz=28.0,
        low_shelf_hz=80.0,
        low_shelf_db=1.0,
        presence_hz=3500.0,
        presence_db=1.5,
        air_shelf_hz=11000.0,
        air_shelf_db=1.5,
        comp_threshold_db=-8.0,
        comp_ratio=1.8,
        comp_attack_ms=12.0,
        comp_release_ms=100.0,
        stereo_width=1.0,          # already widened above
        analog_warmth=0.04,        # gentle final warmth
        limiter_ceiling_db=-0.3,
    )
    audio = apply_master_bus(audio, master_config)

    return audio


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("Bolero -- Maurice Ravel (1928)")
    print("  The greatest crescendo in all of music")
    print("  Key: C major | BPM: 72 | Time: 3/4 | Channels: 9")
    print("  Features: 5-pass crescendo, E major key change,")
    print("            concert hall reverb, full mastering chain")
    print("=" * 60)
    print("  Building song...", flush=True)

    song = build_song()

    print("  Rendering audio...", flush=True)
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    # Apply the full post-processing chain
    audio = post_process(audio)

    out = Path('output/classical/005_bolero.wav')
    out.parent.mkdir(parents=True, exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    peak = float(np.max(np.abs(audio)))

    print("=" * 60)
    print(f"  Duration:  {duration:.1f}s ({duration/60:.1f} min)")
    print(f"  Size:      {size_mb:.1f} MB")
    print(f"  Peak:      {peak:.4f}")
    print(f"  Clipping:  {'YES' if peak > 1.0 else 'None'}")
    print(f"  File:      {out}")
    print("=" * 60)
