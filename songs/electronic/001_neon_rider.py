"""
Neon Rider — Synthwave / Retrowave
====================================
1985. Neon-soaked highway. Top down. Endless horizon.

The synthwave aesthetic distilled: driving octave bass, heroic lead melody
with wide 4th/5th intervals, gated-reverb claps, and a hypnotic arp running
16th-note Am pentatonic in groups of 3 against the 4/4 beat (3-against-4
polyrhythm — the signature synthwave propulsion).

Key: A minor (natural)
BPM: 108 (synthwave sweet spot — driving but not rushed)
Channels: 7
  0 - Kick (kick_deep) — four-on-floor
  1 - Clap (noise_clap) — gated reverb feel, dur=2, sharp
  2 - Hi-hat (hat_crisp) — 8th notes, steady pulse
  3 - Bass (bass_growl) — octave bounce: root -> oct up -> root per bar
  4 - Lead (lead_bright) — heroic melody, wide 4ths and 5ths
  5 - Pad (pad_lush) — power chords (root + 5th + octave)
  6 - Arp (pulse_warm) — 16th Am pentatonic in groups-of-3 polyrhythm

Structure (~20 seconds at 108 BPM):
  [0-9s]    INTRO     4 bars — arp + bass + pad, no drums (atmosphere builds)
  [9-22s]   MAIN      6 bars — full groove + heroic lead melody
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 108
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

def note(inst: str, midi: int, vel: float = 0.80, dur: int = 2) -> NoteEvent:
    """Create a note. Default dur=2 (no staccato chirps). Vel capped at 0.85."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 2), instrument=inst)

def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]

# -- Instruments --------------------------------------------------------------
KICK   = 'kick_deep'
CLAP   = 'noise_clap'
HAT    = 'hat_crisp'
BASS   = 'bass_growl'
LEAD   = 'lead_bright'
PAD    = 'pad_lush'
ARP    = 'pulse_warm'
COUNTER = 'saw_dark'

# -- A minor note pool (MIDI numbers) ----------------------------------------
# A minor natural: A B C D E F G
A2 = 45;  B2 = 47;  C3 = 48;  D3 = 50;  E3 = 52;  F3 = 53;  G3 = 55
A3 = 57;  B3 = 59;  C4 = 60;  D4 = 62;  E4 = 64;  F4 = 65;  G4 = 67
A4 = 69;  B4 = 71;  C5 = 72;  D5 = 74;  E5 = 76;  F5 = 77;  G5 = 79
A5 = 81

# Am pentatonic for arp: A C D E G (repeating across octaves)
AM_PENT_ARP = [A4, C5, D5, E5, G5, A5, G5, E5, D5, C5, A4, C5]

# Power chord voicings: root + 5th + octave (not triads — the synthwave sound)
POWER_CHORDS = {
    'Am':  (A3, E4, A4),       # Am power
    'F':   (F3, C4, F4),       # F power
    'G':   (G3, D4, G4),       # G power
    'Em':  (E3, B3, E4),       # Em power
}
CHORD_CYCLE = ['Am', 'F', 'G', 'Em']
BASS_ROOTS  = {'Am': A2, 'F': F3, 'G': G3, 'Em': E3}

# -- THE LEAD MELODY ---------------------------------------------------------
# Heroic synthwave melody with wide intervals (4ths and 5ths)
# Format: (step_offset_in_2bars, midi, velocity, duration)
HERO_MELODY = [
    # Bar A: opening statement — leap up a 5th, then a 4th
    (0,  A4,  0.82, 4),    # root, strong downbeat
    (4,  E5,  0.78, 3),    # leap up a 5th — THE synthwave interval
    (7,  A5,  0.84, 3),    # leap up another 4th to the octave — heroic peak
    (10, G5,  0.72, 2),    # step down
    (12, E5,  0.75, 4),    # resolve to 5th, held

    # Bar B: descending answer, wider intervals
    (16, D5,  0.78, 3),    # 4th below the peak
    (19, A4,  0.80, 3),    # back to root — 4th down
    (22, C5,  0.74, 2),    # minor 3rd color
    (24, E5,  0.82, 4),    # leap up — 5th again, the hook
    (28, D5,  0.70, 4),    # step down, held for resolution
]

# Counter-melody: dark octave-below echo (saw_dark)
COUNTER_MELODY = [
    (2,  A3,  0.55, 3),
    (6,  E4,  0.52, 3),
    (10, G4,  0.50, 2),
    (13, E4,  0.48, 3),
    (18, D4,  0.55, 3),
    (22, A3,  0.52, 4),
    (27, C4,  0.50, 3),
    (30, D4,  0.48, 2),
]


# -- PATTERN: INTRO -----------------------------------------------------------

def make_intro() -> Pattern:
    """4 bars: Arp + bass + pad. No drums. Night highway establishing shot.
    The arp polyrhythm (groups of 3 in 16th notes) creates hypnotic pulse."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        bs = bar * BAR
        cname = CHORD_CYCLE[bar % 4]
        root = BASS_ROOTS[cname]
        chord = POWER_CHORDS[cname]

        # Pad: sustained power chord, building velocity
        pad_vel = 0.35 + bar * 0.04
        g[5][bs] = note(PAD, chord[0], pad_vel, BAR)

        # Bass: octave bounce pattern (root -> octave up -> root)
        g[3][bs]      = note(BASS, root, 0.72, 4)      # root
        g[3][bs + 4]  = note(BASS, root + 12, 0.58, 3) # octave up
        g[3][bs + 8]  = note(BASS, root, 0.68, 4)      # root
        g[3][bs + 12] = note(BASS, root + 12, 0.55, 3) # octave up again

        # Arp: 16th notes in GROUPS OF 3 (3-against-4 polyrhythm)
        # Every 3 steps gets an accent, creating cross-rhythm against 4/4
        arp_vel_base = 0.35 + bar * 0.05
        for s in range(BAR):
            pent_idx = s % len(AM_PENT_ARP)
            # Accent every 3rd note for polyrhythm feel
            accent = 0.10 if (s % 3 == 0) else 0.0
            vel = arp_vel_base + accent
            g[6][bs + s] = note(ARP, AM_PENT_ARP[pent_idx], vel, 2)

        # Soft hat shimmer in bars 2-3 (foreshadowing the groove)
        if bar >= 2:
            for s in range(0, BAR, 4):
                g[2][bs + s] = note(HAT, 42, 0.22 + bar * 0.03, 2)

    return Pattern(name='intro', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# -- PATTERN: MAIN GROOVE -----------------------------------------------------

def make_main() -> Pattern:
    """6 bars: Full synthwave groove. Four-on-floor kick, gated claps,
    8th-note hats, octave bass, heroic lead, power chord pads, poly arp.
    The melody plays 3 times across 6 bars (2-bar hook x3)."""
    steps = BAR * 6
    g = new_grid(steps)

    for bar in range(6):
        bs = bar * BAR
        cname = CHORD_CYCLE[bar % 4]
        root = BASS_ROOTS[cname]
        chord = POWER_CHORDS[cname]

        # -- KICK: four-on-floor, the heartbeat --
        for beat in range(4):
            g[0][bs + beat * 4] = note(KICK, 36, 0.82, 2)

        # -- CLAP: beats 2 and 4, gated reverb feel (dur=2, sharp attack) --
        g[1][bs + 4]  = note(CLAP, 40, 0.78, 3)
        g[1][bs + 12] = note(CLAP, 40, 0.75, 3)
        # Ghost clap before beat 4 on every other bar (groove variation)
        if bar % 2 == 1:
            g[1][bs + 10] = note(CLAP, 40, 0.42, 3)

        # -- HATS: 8th notes, steady motorik pulse --
        for s in range(0, BAR, 2):
            hat_vel = 0.52 if (s % 4 == 0) else 0.40
            g[2][bs + s] = note(HAT, 42, hat_vel, 2)

        # -- BASS: octave bounce (root -> oct -> root -> oct) --
        g[3][bs]      = note(BASS, root, 0.78, 4)
        g[3][bs + 4]  = note(BASS, root + 12, 0.62, 3)
        g[3][bs + 8]  = note(BASS, root, 0.74, 4)
        g[3][bs + 12] = note(BASS, root + 12, 0.58, 3)

        # -- PAD: sustained power chords (root + 5th + octave) --
        g[5][bs] = note(PAD, chord[0], 0.38, BAR)

        # -- ARP: 16th-note polyrhythm (groups of 3 against 4/4) --
        for s in range(BAR):
            pent_idx = s % len(AM_PENT_ARP)
            # Accent pattern: every 3 steps = polyrhythm accent
            accent = 0.12 if (s % 3 == 0) else 0.0
            vel = 0.45 + accent
            g[6][bs + s] = note(ARP, AM_PENT_ARP[pent_idx], vel, 2)

    # -- LEAD MELODY: heroic theme plays 3x across 6 bars --
    for rep in range(3):
        bar_off = rep * 2
        bs = bar_off * BAR
        vel_boost = rep * 0.02  # slight swell each repetition
        for step, midi, vel, dur in HERO_MELODY:
            s = bs + step
            if s < steps:
                g[4][s] = note(LEAD, midi, vel + vel_boost, dur)

    # -- COUNTER-MELODY: dark saw_dark an octave below, reps 1 and 2 --
    for rep in range(1, 3):
        bar_off = rep * 2
        bs = bar_off * BAR
        for step, midi, vel, dur in COUNTER_MELODY:
            s = bs + step
            if s < steps:
                # Only place if lead isn't there (don't clash)
                if g[4][s] is None:
                    g[4][s] = note(COUNTER, midi, vel, dur)

    # -- FILL: snare roll into final bar for energy --
    fill_bar = 5
    fbs = fill_bar * BAR
    for s in range(8, BAR, 2):
        roll_vel = 0.45 + s * 0.02
        g[1][fbs + s] = note(CLAP, 40, min(roll_vel, 0.78), 3)

    return Pattern(name='main', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# -- SONG ASSEMBLY ------------------------------------------------------------

def build_song() -> Song:
    patterns = [
        make_intro(),   # 0 -- 4 bars (~8.9s)
        make_main(),    # 1 -- 6 bars (~13.3s)
    ]
    # Total: 10 bars ~ 22.2 seconds at 108 BPM

    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # clap: just off center
        2:  0.28,    # hats: right (width)
        3: -0.08,    # bass: near center
        4:  0.12,    # lead: slight right
        5: -0.20,    # pad: left (balances hats)
        6: -0.30,    # arp: left (wide stereo with hats)
    }

    # Effects on ALL channels -- warm, spacious synthwave sound
    channel_effects = {
        0: {  # Kick: subtle room
            'reverb': 0.06, 'reverb_mix': 0.05,
        },
        1: {  # Clap: gated reverb feel (medium room, sharp)
            'reverb': 0.30, 'reverb_mix': 0.20,
        },
        2: {  # Hats: rhythmic space
            'delay': 0.139, 'delay_feedback': 0.25, 'delay_mix': 0.18,
            'reverb': 0.15, 'reverb_mix': 0.10,
        },
        3: {  # Bass: tight low-end
            'reverb': 0.08, 'reverb_mix': 0.05,
        },
        4: {  # Lead: rich reverb + slapback delay (the 80s sound)
            'reverb': 0.55, 'reverb_mix': 0.35,
            'delay': 0.278, 'delay_feedback': 0.30, 'delay_mix': 0.22,
        },
        5: {  # Pad: deep hall (the night sky)
            'reverb': 0.85, 'reverb_mix': 0.45,
        },
        6: {  # Arp: tempo-synced delay + room (rhythmic shimmer)
            # At 108 BPM, 16th note = 60/108/4 = 0.139s
            'delay': 0.139, 'delay_feedback': 0.35, 'delay_mix': 0.25,
            'reverb': 0.40, 'reverb_mix': 0.20,
        },
    }

    return Song(
        title='Neon Rider',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.12,
        master_delay=0.0,
    )


# -- MAIN ---------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 52)
    print("  NEON RIDER -- Synthwave / Retrowave")
    print("  Key: A minor | BPM: 108 | ~22s")
    print("=" * 52)
    print()
    print("  Channels:")
    print("    0  Kick (kick_deep) -- four-on-floor")
    print("    1  Clap (noise_clap) -- gated reverb feel")
    print("    2  Hat (hat_crisp) -- 8th note pulse")
    print("    3  Bass (bass_growl) -- octave bounce")
    print("    4  Lead (lead_bright) -- heroic 4ths/5ths melody")
    print("    5  Pad (pad_lush) -- power chords")
    print("    6  Arp (pulse_warm) -- 3-against-4 polyrhythm")
    print()
    print("  Structure:")
    print("    [0-9s]   Intro -- arp + bass + pad (no drums)")
    print("    [9-22s]  Main  -- full groove + heroic melody")
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

    out = Path('output/electronic_001_neon_rider.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  Neon lights. Open highway. Infinite horizon.")
