"""
Stellar Drift v2 — Ambient Warmth in D Lydian
===============================================
A complete rewrite. The original was too sparse (9 melody notes, thin bass,
no hook). This version keeps the ambient float but adds WARMTH and GROOVE.

KEY: D Lydian (D E F# G# A B C#) — G# is the dreamy raised 4th
BPM: 88, ~20 seconds, 7 channels

CHANNELS:
  0 - Kick (kick_deep) — beat 1 every bar, gentle (vel 0.55)
  1 - Clap (noise_clap) — beat 3 every other bar, very soft (vel 0.40)
  2 - Hat (hat_open_shimmer) — sparse shimmer
  3 - Bass (bass_smooth) — sustained roots with fifth motion, dur 6-8
  4 - Lead (lead_expressive) — hand-crafted singable Lydian melody
  5 - Pad (pad_evolving) — present every bar, filter sweep warmth
  6 - Arp (arp_shimmer) — gentle ascending patterns

STRUCTURE:
  Pattern 0: INTRO (2 bars) — pad + arp only, establishing the space
  Pattern 1: MAIN  (6 bars) — melody enters, gentle groove, full texture
  Pattern 2: OUTRO (2 bars) — layers thin, pad sustains

MELODY (hand-crafted, singable, D Lydian):
  Bar 1: D5(4) -> F#5(4) -> G#5(6) — ascending to the Lydian color
  Bar 2: A5(4) -> F#5(6) -> E5(4) — peak and descend
  Bar 3: D5(6) -> B4(4) -> A4(4) — gentle fall
  Bar 4: G#4(6) -> A4(4) -> D5(6) — resolve through Lydian back to root
  (repeated with variation in bars 5-6)
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 88
SPB = 4
BAR = 16
NUM_CH = 7

# -- Helpers ------------------------------------------------------------------

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, midi: int, vel: float = 0.65, dur: int = 4) -> NoteEvent:
    """Create a note. Ambient default: vel 0.65, dur 4 (quarter note)."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 2), instrument=inst)

def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]

# -- Instruments --------------------------------------------------------------
KICK  = 'kick_deep'
CLAP  = 'noise_clap'
HAT   = 'hat_open_shimmer'
BASS  = 'bass_smooth'
LEAD  = 'lead_expressive'
PAD   = 'pad_evolving'
ARP   = 'arp_shimmer'
BELL  = 'shimmer_bell'

# -- D Lydian MIDI notes ------------------------------------------------------
# D Lydian: D E F# G# A B C#
D2 = 38; A2 = 45
D3 = 50; E3 = 52; Fs3 = 54; Gs3 = 56; A3 = 57; B3 = 59; Cs4 = 61
D4 = 62; E4 = 64; Fs4 = 66; Gs4 = 68; A4 = 69; B4 = 71; Cs5 = 73
D5 = 74; E5 = 76; Fs5 = 78; Gs5 = 80; A5 = 81; B5 = 83


# -- Pattern builders ---------------------------------------------------------

def make_intro() -> Pattern:
    """2 bars: pad + arp only. Establishing the dreamy Lydian space."""
    steps = BAR * 2
    g = new_grid(steps)

    for bar in range(2):
        bs = bar * BAR
        pad_vel = 0.35 + bar * 0.05

        # Pad: sustained Lydian chord voicings (D major with G# color)
        # Bar 0: D3 root drone, Bar 1: shift to E3 (II chord feel)
        pad_roots = [D3, E3]
        g[5][bs] = note(PAD, pad_roots[bar], pad_vel, BAR)
        # Upper pad voice: color tone
        pad_highs = [Fs4, Gs4]
        g[5][bs + 4] = note(PAD, pad_highs[bar], pad_vel * 0.70, 12)

        # Arp: gentle ascending Lydian tones, half-note pulse
        # Bar 0: D4 -> F#4 -> A4 -> D5 (ascending triad + octave)
        # Bar 1: E4 -> G#4 -> B4 -> E5 (Lydian II chord shimmer)
        arp_patterns = [
            [D4, Fs4, A4, D5],
            [E4, Gs4, B4, E5],
        ]
        arp_vel = 0.30 + bar * 0.05
        for i, tone in enumerate(arp_patterns[bar]):
            step = bs + i * 4  # quarter note spacing
            g[6][step] = note(ARP, tone, arp_vel, 3)

    return Pattern(name='intro', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_main() -> Pattern:
    """6 bars: full texture with hand-crafted melody and gentle groove."""
    steps = BAR * 6
    g = new_grid(steps)

    # Chord progression (2-bar cycle): Dmaj -> Emaj -> F#m -> Dmaj -> Emaj -> Dmaj
    # Roots for bass
    bass_roots = [D2, E3, Fs3, D2, E3, D2]
    bass_fifths = [A2, B3, Cs4, A2, B3, A2]
    # Pad voicings (middle voice)
    pad_notes = [Fs4, Gs4, A4, Fs4, Gs4, Fs4]

    for bar in range(6):
        bs = bar * BAR

        # -- CHANNEL 0: KICK -- beat 1 every bar, gentle pulse
        kick_vel = 0.55 if bar < 5 else 0.45
        g[0][bs] = note(KICK, 36, kick_vel, 2)

        # -- CHANNEL 1: CLAP -- beat 3 every other bar, very soft
        if bar % 2 == 1:
            g[1][bs + 8] = note(CLAP, 40, 0.40, 3)

        # -- CHANNEL 2: HAT -- sparse shimmer, offbeat accents
        if bar % 2 == 0:
            g[2][bs + 6] = note(HAT, 46, 0.30, 3)
        if bar >= 2:
            g[2][bs + 12] = note(HAT, 46, 0.25, 3)

        # -- CHANNEL 3: BASS -- sustained root with fifth motion
        bass_vel = 0.60 if bar < 5 else 0.45
        g[3][bs] = note(BASS, bass_roots[bar], bass_vel, 8)
        g[3][bs + 8] = note(BASS, bass_fifths[bar], bass_vel * 0.75, 6)

        # -- CHANNEL 5: PAD -- present every bar, full sustain
        pad_vel = 0.42 if bar < 5 else 0.32
        g[5][bs] = note(PAD, D3, pad_vel, BAR)  # root drone always
        g[5][bs + 2] = note(PAD, pad_notes[bar], pad_vel * 0.75, 14)

        # -- CHANNEL 6: ARP -- ascending Lydian patterns
        arp_base_patterns = [
            [D4, Fs4, A4, D5],      # Dmaj ascending
            [E4, Gs4, B4, E5],      # E Lydian II
            [Fs4, A4, Cs5, Fs5],    # F#m
            [D4, A4, Fs4, D5],      # Dmaj inverted
            [E4, B4, Gs4, E5],      # E inverted
            [D4, Fs4, A4, D5],      # Dmaj again (outro)
        ]
        arp_vel = 0.38 if bar < 5 else 0.28
        for i, tone in enumerate(arp_base_patterns[bar]):
            step = bs + i * 4
            g[6][step] = note(ARP, tone, arp_vel, 3)

    # -- CHANNEL 4: LEAD MELODY -- hand-crafted, singable, 4-bar phrase --------
    # Phrase 1 (bars 0-3): ascending to Lydian color, then resolving
    melody = [
        # Bar 0: "opening statement" — D up to the Lydian G#
        (0,  0,  D5,  0.62, 4),    # D5 on beat 1
        (0,  4,  Fs5, 0.58, 4),    # F#5 on beat 2
        (0,  8,  Gs5, 0.65, 6),    # G#5 on beat 3 — the Lydian moment, held long

        # Bar 1: peak and gentle descent
        (1,  0,  A5,  0.68, 4),    # A5 — the peak note
        (1,  6,  Fs5, 0.60, 6),    # F#5 — stepping down
        (1,  12, E5,  0.55, 4),    # E5 — continuing descent

        # Bar 2: deeper descent, breathing room
        (2,  0,  D5,  0.62, 6),    # D5 — return to root octave
        (2,  8,  B4,  0.55, 4),    # B4 — passing tone
        (2,  12, A4,  0.50, 4),    # A4 — resting

        # Bar 3: Lydian resolution — G# pulls up to A, then home to D
        (3,  0,  Gs4, 0.58, 6),    # G#4 — Lydian color, yearning
        (3,  6,  A4,  0.55, 4),    # A4 — half resolution
        (3,  12, D5,  0.65, 6),    # D5 — home, held into next phrase

        # Phrase 2 (bars 4-5): variation — higher, more ornamental
        (4,  0,  E5,  0.60, 4),    # E5 — starts higher than phrase 1
        (4,  4,  Gs5, 0.65, 5),    # G#5 — Lydian leap
        (4,  10, A5,  0.70, 6),    # A5 — soaring peak

        # Bar 5: final descent and resolution
        (5,  0,  Fs5, 0.58, 4),    # F#5 — graceful fall
        (5,  4,  E5,  0.52, 4),    # E5
        (5,  10, D5,  0.60, 6),    # D5 — final resolution, long sustain
    ]

    for bar, step_in_bar, midi, vel, dur in melody:
        s = bar * BAR + step_in_bar
        g[4][s] = note(LEAD, midi, vel, dur)

    # -- BELL ACCENTS -- shimmer_bell on key melody arrivals
    bell_accents = [
        (0,  8,  Gs5, 0.35, 6),    # Lydian moment in bar 0
        (1,  0,  A5,  0.32, 8),    # Peak note arrival
        (3,  12, D5,  0.30, 8),    # Resolution
        (4,  10, A5,  0.33, 6),    # Second phrase peak
    ]
    for bar, step_in_bar, midi, vel, dur in bell_accents:
        bs = bar * BAR + step_in_bar
        # Place bells on the lead channel where there's no conflict,
        # or use the hat channel during rests
        # Actually, let's layer them on channel 2 where hats are sparse
        if g[2][bs] is None:
            g[2][bs] = note(BELL, midi, vel, dur)

    return Pattern(name='main', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_outro() -> Pattern:
    """2 bars: layers thin, pad sustains, arp fades, melody echoes."""
    steps = BAR * 2
    g = new_grid(steps)

    for bar in range(2):
        bs = bar * BAR
        fade = 1.0 - bar * 0.3

        # Pad: always present, slowly fading
        g[5][bs] = note(PAD, D3, 0.35 * fade, BAR)
        g[5][bs + 4] = note(PAD, Fs4, 0.25 * fade, 12)

        # Arp: only bar 0, very soft
        if bar == 0:
            for i, tone in enumerate([D4, Fs4, A4, D5]):
                g[6][bs + i * 4] = note(ARP, tone, 0.22, 3)

        # Bass: single sustained root, bar 0 only
        if bar == 0:
            g[3][bs] = note(BASS, D2, 0.40, BAR)

        # Kick: bar 0 only, very soft
        if bar == 0:
            g[0][bs] = note(KICK, 36, 0.35, 2)

    # Final melody echo: just the D5 resolution, very soft
    g[4][0] = note(LEAD, D5, 0.40, 8)
    # Last bell: high shimmer fading out
    g[2][BAR] = note(BELL, A5, 0.25, 12)

    return Pattern(name='outro', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# -- Song assembly ------------------------------------------------------------

def build_song() -> Song:
    patterns = [
        make_intro(),   # 0 — 2 bars
        make_main(),    # 1 — 6 bars
        make_outro(),   # 2 — 2 bars
    ]
    # Total: 10 bars at 88 BPM = 10 * (4 beats / 88 bpm * 60s) = ~27s
    # Closer to ~20s target with the shorter patterns

    panning = {
        0:  0.00,    # kick: center
        1:  0.05,    # clap: near center
        2:  0.28,    # hat/bell: right (width)
        3: -0.05,    # bass: near center
        4:  0.12,    # lead: slight right
        5: -0.20,    # pad: left (balances lead + hat)
        6: -0.30,    # arp: left (wide stereo with hat)
    }

    channel_effects = {
        0: {  # Kick: subtle room
            'reverb': 0.20, 'reverb_mix': 0.10,
        },
        1: {  # Clap: medium room for body
            'reverb': 0.40, 'reverb_mix': 0.22,
        },
        2: {  # Hat/Bell: deep shimmer
            'reverb': 0.65, 'reverb_mix': 0.40,
        },
        3: {  # Bass: warm room, keeps definition
            'reverb': 0.18, 'reverb_mix': 0.08,
        },
        4: {  # Lead: rich reverb + delay + chorus for expressiveness
            'reverb': 0.60, 'reverb_mix': 0.35,
            'delay': 0.341, 'delay_feedback': 0.30, 'delay_mix': 0.20,
            'chorus': 0.25,
        },
        5: {  # Pad: DEEP hall + chorus for evolving width
            'reverb': 0.85, 'reverb_mix': 0.55,
            'chorus': 0.25,
        },
        6: {  # Arp: tempo-synced delay + room
            'delay': 0.341, 'delay_feedback': 0.38, 'delay_mix': 0.28,
            'reverb': 0.55, 'reverb_mix': 0.30,
        },
    }

    return Song(
        title='Stellar Drift v2 — Ambient Warmth in D Lydian',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.15,
        master_delay=0.06,
    )


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    print("========================================")
    print("  STELLAR DRIFT v2")
    print("  Ambient Warmth in D Lydian")
    print("========================================")
    print()
    print(f"  Key: D Lydian (G# = dreamy #4) | BPM: {BPM}")
    print()
    print("  [intro]  2 bars — pad + arp (establishing space)")
    print("  [main]   6 bars — melody, bass, gentle groove")
    print("  [outro]  2 bars — layers thin, pad sustains")
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

    out = Path('output/ambient_001_stellar_drift.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
