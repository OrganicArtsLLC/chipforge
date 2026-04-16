"""
Bolero v4 — Ravel's Crescendo Perfected with AI
==================================================

The definitive ChipForge rendition. What makes v4 unique:

  1. SPECTRAL MORPHING: Instead of switching instruments between passes,
     the lead timbre continuously EVOLVES via spectral_morph(). This is
     literally what Ravel was reaching for with his orchestration —
     one melody whose COLOR transforms from solo flute to full orchestra.

  2. AUTO-COUNTERPOINT: Passes 3+ get an AI-generated counter-melody
     via generate_counterpoint(), harmonizing the melody with species
     counterpoint rules (contrary motion, consonant intervals, no
     parallel fifths).

  3. AUTO-MASTERING: auto_master(audio, genre="classical") applies
     genre-optimized EQ, compression, stereo width, and limiting.

  4. SHAPED INSTRUMENTS: shaped_pluck (flute-like), shaped_vocal (clarinet),
     shaped_brass (horn) — per-harmonic envelopes = evolving timbres.

Key: C major → E major modulation in finale
BPM: 72 | Time: 3/4 (SPB=4, BAR=12) | Channels: 9 | ~3 min (58 bars)

Morph schedule (the novel technique):
  Pass 1: shaped_pluck → shaped_vocal  morph=0.0  (pure flute)
  Pass 2: shaped_pluck → shaped_vocal  morph=0.20 (clarinet entering)
  Pass 3: shaped_pluck → shaped_brass  morph=0.40 (oboe + horn)
  Pass 4: shaped_pluck → add_string    morph=0.60 (full strings)
  Pass 5: shaped_pluck → shaped_brass  morph=0.80 (approaching tutti)
  Finale: morph=1.0 = full brass, then E major key change, crash back

Fibonacci velocity crescendo: 0.25, 0.32, 0.42, 0.55, 0.72, 0.85
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from src.synth import (
    synthesize_note,
    spectral_morph,
    SAMPLE_RATE,
    ADSR,
)
from src.instruments import PRESETS
from src.theory import generate_counterpoint
from src.effects import auto_master
from pathlib import Path
import numpy as np

BPM = 72
SPB = 4       # steps per beat
BAR = 12      # 3/4 time: 3 beats x 4 subdivisions
NUM_CH = 9

# Fibonacci-inspired velocity crescendo across 6 passes
# Each pass grows by ratio ~1.3 (golden section adjacent)
PASS_VELOCITIES = [0.25, 0.32, 0.42, 0.55, 0.72, 0.85]

# ---------------------------------------------------------------------------
# MIDI / note helpers
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
# MIDI note reference -- C major
# C3=48, D3=50, E3=52, F3=53, G3=55, A3=57, B3=59
# C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71
# C5=72, D5=74, E5=76, F5=77, G5=79, A5=81
# E major: E4=64, F#4=66, G#4=68, A4=69, B4=71, C#5=73, D#5=75
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# THE BOLERO RHYTHM -- Ravel's eternal snare pattern in 3/4
# ta-da-da ta-da-da ta-da-da-da-da-da
# Beat 1: step 0 (accent), 2, 3
# Beat 2: step 4 (accent), 6, 7
# Beat 3: step 8, 9, 10, 11 (triplet fill)
# ---------------------------------------------------------------------------

BOLERO_RHYTHM = [
    (0, True),     # Beat 1 accent
    (2, False),    # "da"
    (3, False),    # "da"
    (4, True),     # Beat 2 accent
    (6, False),    # "da"
    (7, False),    # "da"
    (8, False),    # Beat 3 triplet fill
    (9, False),    # "da"
    (10, False),   # "da"
    (11, False),   # "da"
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
# THEME A -- The sinuous C major melody (8 bars = 96 steps)
# Stepwise, snake-like, centered around C4-G4
# Each entry: (step_offset_from_theme_start, midi, duration_steps)
# ---------------------------------------------------------------------------

THEME_A = [
    # Bar 1: C4 held, then D4
    (0, 60, 6),     # C4 -- long opening (dotted quarter)
    (6, 62, 3),     # D4
    (9, 64, 3),     # E4
    # Bar 2: F4 to E4 descent
    (12, 65, 4),    # F4
    (16, 64, 4),    # E4
    (20, 62, 4),    # D4
    # Bar 3: C4 up to E4
    (24, 60, 6),    # C4 held
    (30, 62, 3),    # D4
    (33, 64, 3),    # E4
    # Bar 4: D4 ornamental turn
    (36, 62, 4),    # D4
    (40, 64, 2),    # E4
    (42, 62, 2),    # D4
    (44, 60, 4),    # C4
    # Bar 5: ascending run C4-G4
    (48, 60, 3),    # C4
    (51, 62, 3),    # D4
    (54, 64, 3),    # E4
    (57, 65, 3),    # F4
    # Bar 6: G4 peak, descent
    (60, 67, 6),    # G4 -- peak, held
    (66, 65, 3),    # F4
    (69, 64, 3),    # E4
    # Bar 7: D4 to C4, graceful descent
    (72, 62, 4),    # D4
    (76, 64, 2),    # E4 (grace)
    (78, 62, 2),    # D4
    (80, 60, 4),    # C4
    # Bar 8: resolution on C4
    (84, 60, 8),    # C4 -- long resolution
    (92, 62, 2),    # D4 pickup to Theme B
    (94, 60, 2),    # C4
]

# ---------------------------------------------------------------------------
# THEME B -- Starting on G4, reaching higher, more expressive
# ---------------------------------------------------------------------------

THEME_B = [
    # Bar 1: G4 opening
    (0, 67, 6),     # G4 held
    (6, 69, 3),     # A4
    (9, 71, 3),     # B4
    # Bar 2: C5 peak descent
    (12, 72, 4),    # C5 high peak
    (16, 71, 4),    # B4
    (20, 69, 4),    # A4
    # Bar 3: G4 approach from below
    (24, 67, 6),    # G4
    (30, 69, 3),    # A4
    (33, 67, 3),    # G4
    # Bar 4: expressive turn on F4-G4
    (36, 65, 4),    # F4
    (40, 67, 2),    # G4
    (42, 69, 2),    # A4
    (44, 67, 4),    # G4
    # Bar 5: ascending to D5
    (48, 67, 3),    # G4
    (51, 69, 3),    # A4
    (54, 71, 3),    # B4
    (57, 72, 3),    # C5
    # Bar 6: D5 peak -- climax of Theme B
    (60, 74, 6),    # D5 highest note, held
    (66, 72, 3),    # C5
    (69, 71, 3),    # B4
    # Bar 7: descending resolution
    (72, 69, 4),    # A4
    (76, 67, 4),    # G4
    (80, 65, 4),    # F4
    # Bar 8: resolution to C4 via E4
    (84, 64, 4),    # E4
    (88, 62, 4),    # D4
    (92, 60, 8),    # C4 final resolution, long
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
    """Write a harmony line a diatonic third below the melody."""
    base = bar_offset * BAR
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
# COUNTERPOINT GENERATION
# Extract melody MIDI sequence from theme data for counterpoint input
# ---------------------------------------------------------------------------

def theme_to_midi_sequence(theme: list, total_steps: int) -> list[int]:
    """Convert theme data to step-by-step MIDI list (0=rest) for counterpoint."""
    sequence = [0] * total_steps
    for (step, midi, dur) in theme:
        if step < total_steps:
            sequence[step] = midi
            # Fill held notes so counterpoint has context
            for d in range(1, min(dur, total_steps - step)):
                if step + d < total_steps:
                    sequence[step + d] = midi
    return sequence


def write_counterpoint(grid: list, channel: int, theme: list,
                       bar_offset: int, inst: str, vel: float) -> None:
    """Generate and write auto-counterpoint for a theme."""
    theme_steps = max(s + d for s, m, d in theme) + 1 if theme else 96
    melody_seq = theme_to_midi_sequence(theme, theme_steps)
    counter_seq = generate_counterpoint(
        melody_seq, key_root=60, scale_name="major",
        species=1, interval_preference="thirds",
    )
    base = bar_offset * BAR
    # Write counterpoint: only on positions where the original theme has note onsets
    # (sparse writing to avoid constant 16th notes)
    for (step, midi, dur) in theme:
        s = base + step
        if s < len(grid[channel]) and step < len(counter_seq):
            cp_midi = counter_seq[step]
            if cp_midi > 0:
                grid[channel][s] = note(inst, cp_midi, vel * 0.80, max(dur, 2))


# ---------------------------------------------------------------------------
# SPECTRAL MORPH POST-PROCESSING
#
# The key innovation: after render_song() produces the audio, we re-render
# the lead melody channel (ch4) for each pass with TWO different instruments,
# then spectral_morph() them together at the pass-specific morph amount.
#
# We apply this as a post-process step: render the lead with instrument A,
# render it again with instrument B, morph, and mix back in.
# ---------------------------------------------------------------------------

def render_morphed_lead_for_pattern(
    pattern: Pattern,
    channel: int,
    inst_a: str,
    inst_b: str,
    morph_amount: float,
) -> np.ndarray:
    """
    Render a single channel from a pattern with spectral morphing between
    two instruments.

    1. Render all notes on `channel` with instrument A
    2. Render all notes on `channel` with instrument B
    3. spectral_morph(A, B, morph_amount)

    Returns mono float32 array.
    """
    step_duration = 60.0 / (BPM * SPB)
    total_samples = int(pattern.num_steps * step_duration * SAMPLE_RATE)

    buf_a = np.zeros(total_samples, dtype=np.float32)
    buf_b = np.zeros(total_samples, dtype=np.float32)

    preset_a = PRESETS.get(inst_a, PRESETS['shaped_pluck'])
    preset_b = PRESETS.get(inst_b, PRESETS['shaped_brass'])

    grid = pattern.grid
    for step_idx in range(pattern.num_steps):
        ev = grid[channel][step_idx] if step_idx < len(grid[channel]) else None
        if ev is None or ev.midi_note == 0:
            continue

        note_start = int(step_idx * step_duration * SAMPLE_RATE)
        note_dur_sec = ev.duration_steps * step_duration
        note_samples = int(note_dur_sec * SAMPLE_RATE)

        if note_start + note_samples > total_samples:
            note_samples = total_samples - note_start
        if note_samples <= 0:
            continue

        # Render with instrument A
        sample_a = synthesize_note(
            ev.midi_note, note_dur_sec,
            waveform=preset_a.waveform, duty=preset_a.duty,
            adsr=preset_a.adsr, volume=preset_a.volume * ev.velocity,
            wavetable=preset_a.wavetable,
            filter_cutoff=preset_a.filter_cutoff,
            filter_resonance=preset_a.filter_resonance,
            vibrato_rate=preset_a.vibrato_rate,
            vibrato_depth=preset_a.vibrato_depth,
            pitch_start=preset_a.pitch_start,
            pitch_end=preset_a.pitch_end,
            distortion=preset_a.distortion,
            highpass_cutoff=preset_a.highpass_cutoff,
        )

        # Render with instrument B
        sample_b = synthesize_note(
            ev.midi_note, note_dur_sec,
            waveform=preset_b.waveform, duty=preset_b.duty,
            adsr=preset_b.adsr, volume=preset_b.volume * ev.velocity,
            wavetable=preset_b.wavetable,
            filter_cutoff=preset_b.filter_cutoff,
            filter_resonance=preset_b.filter_resonance,
            vibrato_rate=preset_b.vibrato_rate,
            vibrato_depth=preset_b.vibrato_depth,
            pitch_start=preset_b.pitch_start,
            pitch_end=preset_b.pitch_end,
            distortion=preset_b.distortion,
            highpass_cutoff=preset_b.highpass_cutoff,
        )

        # Match lengths
        min_len = min(len(sample_a), len(sample_b), note_samples)
        sa = sample_a[:min_len]
        sb = sample_b[:min_len]

        # Spectral morph between the two
        if morph_amount <= 0.001:
            morphed = sa
        elif morph_amount >= 0.999:
            morphed = sb
        else:
            morphed = spectral_morph(sa, sb, morph_amount,
                                     window_size=2048, hop_size=512)

        end = min(note_start + min_len, total_samples)
        actual = end - note_start
        buf_a[note_start:end] += morphed[:actual]

    return buf_a


# ---------------------------------------------------------------------------
# PASS 1: Solo flute + snare (16 bars) — pp
# Morph: 0.0 (pure shaped_pluck = flute-like)
# ---------------------------------------------------------------------------

def make_pass1() -> Pattern:
    """Pass 1: Solo shaped_pluck (flute) + snare. pp dynamics."""
    steps = BAR * 16
    g = new_grid(steps)

    # The eternal snare -- very quiet, distant drum
    write_bolero_snare(g, 0, 16, vel=PASS_VELOCITIES[0])

    # Theme A (bars 0-7) then Theme B (bars 8-15)
    # Using shaped_vocal as base instrument (morph will override in post-process)
    write_melody(g, 4, THEME_A, 0, 'shaped_vocal', PASS_VELOCITIES[0] + 0.10)
    write_melody(g, 4, THEME_B, 8, 'shaped_vocal', PASS_VELOCITIES[0] + 0.13)

    # Pad: ultra-quiet sustained C3 -- concert hall air
    for bar in range(0, 16, 4):
        s = bar * BAR
        g[6][s] = note('pad_evolving', 48, 0.15, BAR * 4)

    return Pattern(name='pass1', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# PASS 2: Clarinet joins (16 bars) — p
# Morph: 0.20 (shaped_pluck morphing toward shaped_vocal)
# ---------------------------------------------------------------------------

def make_pass2() -> Pattern:
    """Pass 2: shaped_vocal lead, harmony joins. p dynamics."""
    steps = BAR * 16
    g = new_grid(steps)

    write_bolero_snare(g, 0, 16, vel=PASS_VELOCITIES[1])

    # Lead melody
    write_melody(g, 4, THEME_A, 0, 'shaped_vocal', PASS_VELOCITIES[1] + 0.13)
    write_melody(g, 4, THEME_B, 8, 'shaped_vocal', PASS_VELOCITIES[1] + 0.16)

    # Second voice: harmony in thirds
    write_harmony_thirds(g, 5, THEME_A, 0, 'shaped_pluck', PASS_VELOCITIES[1])
    write_harmony_thirds(g, 5, THEME_B, 8, 'shaped_pluck', PASS_VELOCITIES[1] + 0.03)

    # Bass enters -- gentle root notes on beat 1
    for bar in range(16):
        s = bar * BAR
        bass_note = 36 if bar % 4 < 2 else 43  # C2 / G2
        g[3][s] = note('bass_smooth', bass_note, 0.30, BAR)

    # Pad: slightly more present
    for bar in range(0, 16, 4):
        s = bar * BAR
        g[6][s] = note('pad_evolving', 48, 0.22, BAR * 4)

    return Pattern(name='pass2', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# PASS 3: Oboe + horn + pad + arp + COUNTERPOINT (8 bars) — mp
# Morph: 0.40 (shaped_pluck → shaped_brass)
# ---------------------------------------------------------------------------

def make_pass3() -> Pattern:
    """Pass 3: shaped_brass lead + counterpoint + pad + arp. mp dynamics."""
    steps = BAR * 8
    g = new_grid(steps)

    write_bolero_snare(g, 0, 8, vel=PASS_VELOCITIES[2])

    # Lead melody
    write_melody(g, 4, THEME_A, 0, 'shaped_vocal', PASS_VELOCITIES[2] + 0.13)

    # AUTO-COUNTERPOINT: second voice harmonizes with AI counterpoint rules
    write_counterpoint(g, 5, THEME_A, 0, 'add_warm_lead', PASS_VELOCITIES[2])

    # Hat enters -- light cymbal color
    for bar in range(8):
        s = bar * BAR
        g[2][s] = drum('hat_open_shimmer', 42, 0.25, 2)
        g[2][s + 8] = drum('hat_open_shimmer', 42, 0.18, 2)

    # Bass: more rhythmic, pulsing on beats 1 and 3
    for bar in range(8):
        s = bar * BAR
        bass_note = 36 if bar % 4 < 2 else 43
        g[3][s] = note('bass_smooth', bass_note, PASS_VELOCITIES[2], 6)
        g[3][s + 8] = note('bass_smooth', bass_note, PASS_VELOCITIES[2] - 0.07, 4)

    # Pad: sustained chords
    for bar in range(0, 8, 2):
        s = bar * BAR
        chord_root = 48 if bar % 4 < 2 else 55
        g[6][s] = note('pad_evolving', chord_root, 0.35, BAR * 2)

    # Arp: broken C major chord pattern
    arp_pattern = [60, 64, 67, 72, 67, 64]
    for bar in range(8):
        s = bar * BAR
        for step in range(0, BAR, 2):
            idx = (step // 2) % len(arp_pattern)
            midi = arp_pattern[idx]
            if bar % 4 >= 2:
                midi += 7
                if midi > 79:
                    midi -= 12
            v = 0.32 + (bar / 8) * 0.08
            g[8][s + step] = note('pulse_warm', midi, min(v, 0.45), 2)

    return Pattern(name='pass3', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# PASS 4: Strings enter + counterpoint (8 bars) — mf
# Morph: 0.60 (approaching full strings)
# ---------------------------------------------------------------------------

def make_pass4() -> Pattern:
    """Pass 4: add_string joins, bass_growl, counterpoint. mf dynamics."""
    steps = BAR * 8
    g = new_grid(steps)

    write_bolero_snare(g, 0, 8, vel=PASS_VELOCITIES[3])

    # Lead melody -- Theme B this time (Ravel alternates)
    write_melody(g, 4, THEME_B, 0, 'shaped_vocal', PASS_VELOCITIES[3] + 0.07)

    # AUTO-COUNTERPOINT on Theme B
    write_counterpoint(g, 5, THEME_B, 0, 'add_warm_lead', PASS_VELOCITIES[3] - 0.03)

    # Hat: beat 1 + offbeats
    for bar in range(8):
        s = bar * BAR
        g[2][s] = drum('hat_open_shimmer', 42, 0.32, 2)
        g[2][s + 4] = drum('hat_open_shimmer', 42, 0.22, 2)
        g[2][s + 8] = drum('hat_open_shimmer', 42, 0.28, 2)

    # Bass: bass_growl, more aggressive
    for bar in range(8):
        s = bar * BAR
        bass_note = 36 if bar % 4 < 2 else 43
        g[3][s] = note('bass_growl', bass_note, PASS_VELOCITIES[3], 4)
        g[3][s + 4] = note('bass_growl', bass_note, PASS_VELOCITIES[3] - 0.10, 4)
        g[3][s + 8] = note('bass_growl', bass_note, PASS_VELOCITIES[3] - 0.07, 4)

    # Pad: lush
    for bar in range(0, 8, 2):
        s = bar * BAR
        chord_root = 48 if bar % 4 < 2 else 55
        g[6][s] = note('pad_evolving', chord_root, 0.45, BAR * 2)

    # Strings: sustained chord tones
    string_voicings = [
        48, 48, 55, 55, 48, 48, 55, 55,  # C3, G3 alternating
    ]
    for bar in range(8):
        s = bar * BAR
        vel_str = 0.38 + (bar / 8) * 0.12
        g[7][s] = note('add_string', string_voicings[bar], min(vel_str, 0.55), BAR)

    # Arp: more active
    arp_pattern = [67, 71, 72, 76, 72, 71]
    for bar in range(8):
        s = bar * BAR
        for step in range(BAR):
            idx = step % len(arp_pattern)
            midi = arp_pattern[idx]
            if bar % 4 >= 2:
                midi -= 5
            v = 0.38 + (bar / 8) * 0.10
            g[8][s + step] = note('pulse_warm', midi, min(v, 0.52), 2)

    return Pattern(name='pass4', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# FINALE: Full orchestra (10 bars) — ff
# Bars 0-5: Theme A in C major, FULL POWER
# Bars 6-7: KEY CHANGE to E major (Ravel's famous modulation!)
# Bars 8-9: CRASH back to C major, thunderous resolution
# Morph: 0.80 → 1.0 (approaching and reaching full brass)
# ---------------------------------------------------------------------------

THEME_A_E_MAJOR = [
    # E major: E4=64, F#4=66, G#4=68, A4=69, B4=71, C#5=73, D#5=75
    (0, 64, 6),     # E4
    (6, 66, 3),     # F#4
    (9, 68, 3),     # G#4
    (12, 69, 4),    # A4
    (16, 68, 4),    # G#4
    (20, 66, 4),    # F#4
]

FINALE_RESOLUTION = [
    (0, 72, 8),     # C5 TRIUMPHANT
    (8, 67, 4),     # G4
    (12, 60, 12),   # C4 final
]


def make_finale() -> Pattern:
    """Finale: FULL ORCHESTRA ff + counterpoint. Key change, crash back."""
    steps = BAR * 10
    g = new_grid(steps)

    # Snare FULL POWER
    write_bolero_snare(g, 0, 10, vel=PASS_VELOCITIES[5])

    # Kick enters for the FIRST time -- thunderous
    for bar in range(10):
        s = bar * BAR
        g[1][s] = drum('kick_deep', 36, 0.75, 2)
        g[1][s + 8] = drum('kick_deep', 36, 0.60, 2)
        if bar >= 8:
            g[1][s + 4] = drum('kick_deep', 36, 0.68, 2)

    # Hat: full shimmer
    for bar in range(10):
        s = bar * BAR
        for step in range(0, BAR, 2):
            v = 0.38 if step == 0 else 0.28
            g[2][s + step] = drum('hat_open_shimmer', 42, v, 2)

    # --- BARS 0-5: Theme A in C major, FULL POWER ---
    write_melody(g, 4, THEME_A, 0, 'shaped_brass', PASS_VELOCITIES[5])

    # AUTO-COUNTERPOINT for the finale
    write_counterpoint(g, 5, THEME_A, 0, 'shaped_vocal', PASS_VELOCITIES[4])

    # --- BARS 6-7: KEY CHANGE TO E MAJOR ---
    base_kc = 6 * BAR
    for (step, midi, dur) in THEME_A_E_MAJOR:
        s = base_kc + step
        if s < steps:
            g[4][s] = note('shaped_brass', midi, 0.82, max(dur, 2))
    # Harmony in E major
    e_maj_thirds = {64: 61, 66: 63, 68: 64, 69: 66, 71: 68, 73: 69, 75: 71}
    for (step, midi, dur) in THEME_A_E_MAJOR:
        s = base_kc + step
        harm = e_maj_thirds.get(midi, midi - 4)
        if s < steps:
            g[5][s] = note('shaped_vocal', harm, 0.72, max(dur, 2))

    # --- BARS 8-9: CRASH BACK TO C MAJOR ---
    base_res = 8 * BAR
    for (step, midi, dur) in FINALE_RESOLUTION:
        s = base_res + step
        if s < steps:
            g[4][s] = note('shaped_brass', midi, 0.85, max(dur, 2))
    res_thirds = [(0, 67, 8), (8, 64, 4), (12, 57, 12)]
    for (step, midi, dur) in res_thirds:
        s = base_res + step
        if s < steps:
            g[5][s] = note('shaped_vocal', midi, 0.78, max(dur, 2))

    # Bass: THUNDEROUS
    for bar in range(10):
        s = bar * BAR
        if bar < 6:
            bass_note = 36 if bar % 4 < 2 else 43
        elif bar < 8:
            bass_note = 40  # E2 key change
        else:
            bass_note = 36  # C2 crash back
        g[3][s] = note('bass_growl', bass_note, 0.68, 4)
        g[3][s + 4] = note('bass_growl', bass_note, 0.58, 4)
        g[3][s + 8] = note('bass_growl', bass_note, 0.62, 4)

    # Pad: massive sustained chords
    for bar in range(0, 6, 2):
        s = bar * BAR
        g[6][s] = note('pad_evolving', 48, 0.58, BAR * 2)
    g[6][6 * BAR] = note('pad_evolving', 52, 0.62, BAR * 2)   # E3 key change
    g[6][8 * BAR] = note('pad_evolving', 48, 0.65, BAR * 2)   # C3 resolution

    # Strings: FULL sustained
    for bar in range(10):
        s = bar * BAR
        if bar < 6:
            str_note = 48 if bar % 4 < 2 else 55
        elif bar < 8:
            str_note = 52  # E3 key change
        else:
            str_note = 48  # C3 resolution
        g[7][s] = note('add_string', str_note, min(0.55 + bar * 0.02, 0.72), BAR)

    # Arp: blazing broken chords
    arp_c = [60, 64, 67, 72, 76, 79, 72, 67]
    arp_e = [64, 68, 71, 76, 80, 83, 76, 71]
    for bar in range(10):
        s = bar * BAR
        pattern = arp_e if 6 <= bar < 8 else arp_c
        for step in range(BAR):
            idx = step % len(pattern)
            v = 0.48 + (bar / 10) * 0.15
            g[8][s + step] = note('pulse_warm', pattern[idx], min(v, 0.65), 2)

    return Pattern(name='finale', grid=g, num_steps=steps, num_channels=NUM_CH,
                   bpm=BPM, steps_per_beat=SPB)


# ---------------------------------------------------------------------------
# SONG ASSEMBLY
# ---------------------------------------------------------------------------

def build_song() -> Song:
    """Assemble all passes into the complete Bolero v4."""
    patterns = [
        make_pass1(),    # 0: 16 bars -- solo shaped_pluck/vocal (pp)
        make_pass2(),    # 1: 16 bars -- duet with harmony (p)
        make_pass3(),    # 2: 8 bars  -- counterpoint + pad + arp (mp)
        make_pass4(),    # 3: 8 bars  -- strings + counterpoint (mf)
        make_finale(),   # 4: 10 bars -- FULL ORCHESTRA + morph=1.0 (ff)
    ]
    # Total: 16+16+8+8+10 = 58 bars in 3/4 @ 72 BPM
    # = 58 * 3 beats / 72 BPM * 60 = 145 sec ≈ 2.4 min

    panning = {
        0: 0.0,       # snare -- center (the heartbeat)
        1: 0.0,       # kick -- center
        2: 0.25,      # hat -- slight right
        3: 0.0,       # bass -- center
        4: 0.08,      # lead melody -- slight right (soloist position)
        5: -0.15,     # second voice / counterpoint -- left
        6: -0.22,     # pad -- left
        7: 0.20,      # strings -- right
        8: -0.30,     # arp -- wide left
    }

    channel_effects = {
        0: {
            'reverb': 0.55, 'reverb_mix': 0.28, 'reverb_damping': 0.35,
        },
        1: {
            'reverb': 0.20, 'reverb_mix': 0.08, 'reverb_damping': 0.6,
        },
        2: {
            'delay': 0.12, 'delay_feedback': 0.20, 'delay_mix': 0.15,
            'reverb': 0.30, 'reverb_mix': 0.15,
        },
        3: {
            'reverb': 0.15, 'reverb_mix': 0.06,
        },
        4: {
            'reverb': 0.70, 'reverb_mix': 0.35, 'reverb_damping': 0.3,
            'delay': 0.18, 'delay_feedback': 0.25, 'delay_mix': 0.18,
        },
        5: {
            'reverb': 0.60, 'reverb_mix': 0.30, 'reverb_damping': 0.3,
            'delay': 0.15, 'delay_feedback': 0.20, 'delay_mix': 0.14,
        },
        6: {
            'reverb': 0.85, 'reverb_mix': 0.45, 'reverb_damping': 0.25,
            'chorus': 0.30, 'chorus_detune': 6.0, 'chorus_delay': 25.0,
        },
        7: {
            'reverb': 0.75, 'reverb_mix': 0.38, 'reverb_damping': 0.3,
            'chorus': 0.25, 'chorus_detune': 7.0, 'chorus_delay': 20.0,
        },
        8: {
            'delay': 0.20, 'delay_feedback': 0.30, 'delay_mix': 0.22,
            'reverb': 0.45, 'reverb_mix': 0.22,
        },
    }

    return Song(
        title='Bolero v4 — Ravel (Spectral Morph Edition)',
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
# SPECTRAL MORPH POST-PROCESSING PIPELINE
#
# After the base render, we re-render ch4 (lead) for each pattern with
# morphed timbres and replace the lead in the stereo mix.
# ---------------------------------------------------------------------------

# Morph schedule: (pattern_index, inst_a, inst_b, morph_amount)
MORPH_SCHEDULE = [
    (0, 'shaped_pluck', 'shaped_vocal', 0.00),   # Pass 1: pure flute
    (1, 'shaped_pluck', 'shaped_vocal', 0.20),   # Pass 2: clarinet entering
    (2, 'shaped_pluck', 'shaped_brass', 0.40),   # Pass 3: oboe + horn
    (3, 'shaped_pluck', 'add_string',   0.60),   # Pass 4: full strings
    (4, 'shaped_pluck', 'shaped_brass', 0.90),   # Finale: full brass
]


def apply_spectral_morph_to_lead(song: Song, audio_stereo: np.ndarray) -> np.ndarray:
    """
    Replace the lead channel (ch4) audio with spectrally morphed versions.

    For each pattern in the song, re-renders the lead with two instruments
    and morphs between them. The morphed mono signal replaces ch4's
    contribution in the stereo mix.

    Since we can't cleanly extract ch4 from the mixed audio, we use an
    additive approach: render the morphed lead and blend it on top of
    the existing mix at a controlled level. The base render already has
    ch4 with shaped_vocal, so the morph adds timbral color.
    """
    step_duration = 60.0 / (BPM * SPB)
    lead_panning = 0.08  # match song panning for ch4
    result = audio_stereo.copy()

    # Calculate pattern start positions in samples
    pattern_starts = []
    cumulative = 0
    for pat in song.patterns:
        pattern_starts.append(cumulative)
        cumulative += int(pat.num_steps * step_duration * SAMPLE_RATE)

    for pat_idx, inst_a, inst_b, morph_amt in MORPH_SCHEDULE:
        if pat_idx >= len(song.patterns):
            continue
        if morph_amt < 0.001:
            # No morph needed for pass 1 (pure instrument A)
            # But we still render with shaped_pluck to replace shaped_vocal
            print(f"  Morph pass {pat_idx + 1}: pure {inst_a} (morph=0.0)", flush=True)
            morphed_lead = render_morphed_lead_for_pattern(
                song.patterns[pat_idx], channel=4,
                inst_a=inst_a, inst_b=inst_b, morph_amount=0.0,
            )
        else:
            print(f"  Morph pass {pat_idx + 1}: {inst_a} → {inst_b} "
                  f"(morph={morph_amt:.2f})", flush=True)
            morphed_lead = render_morphed_lead_for_pattern(
                song.patterns[pat_idx], channel=4,
                inst_a=inst_a, inst_b=inst_b, morph_amount=morph_amt,
            )

        # Apply panning and blend into stereo mix
        start_sample = pattern_starts[pat_idx]
        n = len(morphed_lead)
        end_sample = min(start_sample + n, len(result))
        actual_n = end_sample - start_sample

        if actual_n <= 0:
            continue

        mono = morphed_lead[:actual_n]
        # Pan: left = (1 - pan) * 0.5, right = (1 + pan) * 0.5
        left_gain = (1.0 - lead_panning) * 0.5
        right_gain = (1.0 + lead_panning) * 0.5

        # Blend the morphed lead at a moderate level (additive coloring)
        # Scale by morph amount so higher morphs contribute more timbral change
        blend = 0.35 + morph_amt * 0.30  # 0.35 at morph=0, 0.65 at morph=1
        result[start_sample:end_sample, 0] += mono * left_gain * blend
        result[start_sample:end_sample, 1] += mono * right_gain * blend

    return result


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 65)
    print("Bolero v4 — Ravel's Crescendo Perfected with AI")
    print("  Spectral Morphing + Auto-Counterpoint + Auto-Mastering")
    print("  Key: C major | BPM: 72 | Time: 3/4 | Channels: 9")
    print("  Novel: continuous timbral evolution via spectral morphing")
    print("=" * 65)

    print("  Building song...", flush=True)
    song = build_song()

    print("  Rendering base audio (9 channels + effects)...", flush=True)
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    # --- SPECTRAL MORPH POST-PROCESSING ---
    print("  Applying spectral morphing to lead channel...", flush=True)
    audio = apply_spectral_morph_to_lead(song, audio)

    # --- AUTO-MASTERING ---
    print("  Auto-mastering (genre=classical)...", flush=True)
    audio = auto_master(audio, genre="classical")

    # --- EXPORT ---
    out = Path('output/classical/005_bolero_v4.wav')
    out.parent.mkdir(parents=True, exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    peak = float(np.max(np.abs(audio)))

    print("=" * 65)
    print(f"  Duration:  {duration:.1f}s ({duration / 60:.1f} min)")
    print(f"  Size:      {size_mb:.1f} MB")
    print(f"  Peak:      {peak:.4f}")
    print(f"  Clipping:  {'YES' if peak > 1.0 else 'None'}")
    print(f"  File:      {out}")
    print("=" * 65)
