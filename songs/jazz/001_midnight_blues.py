"""
Midnight Blues v2 — Smoky jazz club chip tune
==============================================

A ii-V-I-vi jazz cycle: Dm7 -> G7 -> Cmaj7 -> Am7
BPM 108. Key of C with blue notes (Eb, Ab, Bb).

Design philosophy: SPACE. Jazz lives in the silence between notes.
The melody breathes with 2-4 step rests between phrases.
The walking bass is melodic with chromatic passing tones.
The drums are brushes-on-snare quiet, not rock hits.

7 channels:
  0 - Kick   (kick_deep)           — sparse: beat 1 + "and" of 3 only
  1 - Snare  (noise_clap)          — lazy 2 and 4, brush dynamics vel=0.48
  2 - Hats   (hat_open_shimmer)    — ride cymbal every beat + ghost 16ths
  3 - Bass   (bass_smooth)         — walking line, chromatic passing tones
  4 - Lead   (lead_expressive)     — hand-crafted melody with blue notes + RESTS
  5 - Pad    (pad_glass)           — sustained 7th chord voicings, chorus
  6 - Arp    (pluck_mellow)        — gentle broken chords, quarter notes

Structure (~20 seconds at 108 BPM):
  [0-8.9s]    GROOVE   4 bars  — rhythm section establishes the pocket
  [8.9-22.2s] MELODY   6 bars  — lead enters, full ensemble, blues
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

# -- Helpers -----------------------------------------------------------------

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, midi: int, vel: float = 0.70, dur: int = 2) -> NoteEvent:
    """Create a note. Velocity capped at 0.85, minimum dur 1."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 1), instrument=inst)

def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]

# -- Instruments -------------------------------------------------------------

KICK   = 'kick_deep'
SNARE  = 'noise_clap'
HAT_RD = 'hat_open_shimmer'   # ride cymbal
HAT_GH = 'hat_crisp'          # ghost 16ths
BASS   = 'bass_smooth'
LEAD   = 'lead_expressive'
PAD    = 'pad_glass'
ARP    = 'pluck_mellow'

# -- MIDI note constants -----------------------------------------------------

# Bass register
D2 = 38; Eb2 = 39; E2 = 40; F2 = 41; Fs2 = 42; G2 = 43
Ab2 = 44; A2 = 45; Bb2 = 46; B2 = 47
C3 = 48; Cs3 = 49; D3 = 50; Eb3 = 51; E3 = 52; F3 = 53

# Mid register (pad / arp voicings)
G3 = 55; A3 = 57; Bb3 = 58; B3 = 59
C4 = 60; D4 = 62; Eb4 = 63; E4 = 64; F4 = 65; G4 = 67
A4 = 69; Bb4 = 70; B4 = 71

# Lead register
C5 = 72; D5 = 74; Eb5 = 75; E5 = 76; F5 = 77
G5 = 79; Ab5 = 80; A5 = 81; Bb5 = 82

# -- Chord voicings (7ths) --------------------------------------------------
# Dm7 = D F A C    G7 = G B D F    Cmaj7 = C E G B    Am7 = A C E G
CHORDS = [
    (D4, F4, A4, C5),      # Dm7
    (G3, B3, D4, F4),      # G7
    (C4, E4, G4, B4),      # Cmaj7
    (A3, C4, E4, G4),      # Am7
]

# -- Walking bass lines (the HEART of jazz) ----------------------------------
# Each entry: (midi, step_in_bar, duration)
# Chromatic passing tones connect chord tones melodically

WALKS = {
    # Dm7 variations — root D, chord tones D F A C
    'Dm7_a': [(D2, 0, 4), (F2, 4, 4), (A2, 8, 4), (Ab2, 12, 4)],
    'Dm7_b': [(D3, 0, 4), (C3, 4, 4), (A2, 8, 4), (Bb2, 12, 4)],
    'Dm7_c': [(D2, 0, 4), (E2, 4, 4), (F2, 8, 4), (Fs2, 12, 4)],

    # G7 variations — root G, chord tones G B D F
    'G7_a':  [(G2, 0, 4), (A2, 4, 4), (B2, 8, 4), (Bb2, 12, 4)],
    'G7_b':  [(G2, 0, 4), (F2, 4, 4), (E2, 8, 4), (Eb2, 12, 4)],
    'G7_c':  [(G2, 0, 4), (B2, 4, 4), (D3, 8, 4), (Cs3, 12, 4)],

    # Cmaj7 variations — root C, chord tones C E G B
    'Cmaj7_a': [(C3, 0, 4), (D3, 4, 4), (E3, 8, 4), (Eb3, 12, 4)],
    'Cmaj7_b': [(C3, 0, 4), (B2, 4, 4), (A2, 8, 4), (Bb2, 12, 4)],

    # Am7 variations — root A, chord tones A C E G
    'Am7_a': [(A2, 0, 4), (B2, 4, 4), (C3, 8, 4), (Cs3, 12, 4)],
    'Am7_b': [(A2, 0, 4), (G2, 4, 4), (F2, 8, 4), (Fs2, 12, 4)],
}

# Walk sequences per pattern
GROOVE_WALKS = ['Dm7_a', 'G7_a', 'Cmaj7_a', 'Am7_a']
MELODY_WALKS_1 = ['Dm7_b', 'G7_b', 'Cmaj7_b', 'Am7_b']
MELODY_WALKS_2 = ['Dm7_c', 'G7_c']


# -- Drum helpers ------------------------------------------------------------

def jazz_kick(g: list, bar: int) -> None:
    """Sparse kick: beat 1 and 'and' of 3. That's it. Jazz is space."""
    bs = bar * BAR
    g[0][bs] = note(KICK, 36, 0.55, 2)          # beat 1
    g[0][bs + 10] = note(KICK, 36, 0.50, 2)     # "and" of 3


def jazz_snare(g: list, bar: int) -> None:
    """Brush snare on 2 and 4. Lazy, behind the beat. vel=0.48."""
    bs = bar * BAR
    g[1][bs + 4] = note(SNARE, 40, 0.48, 3)     # beat 2
    g[1][bs + 12] = note(SNARE, 40, 0.45, 3)    # beat 4


def jazz_ride(g: list, bar: int) -> None:
    """Ride cymbal on every beat (vel=0.35) + ghost 16th hats (vel=0.18).
    The ride is the jazz clock. Ghost hats add subtle texture."""
    bs = bar * BAR
    for beat in range(4):
        s = bs + beat * 4
        # Ride on the beat
        g[2][s] = note(HAT_RD, 46, 0.35, 3)
        # Ghost hat on the "e" (one 16th after the beat) — very quiet
        if s + 1 < len(g[2]):
            g[2][s + 1] = note(HAT_GH, 42, 0.18, 1)
        # Ghost hat on the "a" (three 16ths after) — every other beat
        if beat % 2 == 0 and s + 3 < len(g[2]):
            g[2][s + 3] = note(HAT_GH, 42, 0.15, 1)


def walking_bass(g: list, bar: int, key: str, vel: float = 0.72) -> None:
    """Place a walking bass pattern for one bar."""
    bs = bar * BAR
    for midi, step, dur in WALKS[key]:
        idx = bs + step
        if idx < len(g[3]):
            g[3][idx] = note(BASS, midi, vel, dur)


def pad_voicing(g: list, bar: int, chord_idx: int, vel: float = 0.38) -> None:
    """Sustained 7th chord voicing. Full bar. Guide tones (3rd + 7th)."""
    bs = bar * BAR
    chord = CHORDS[chord_idx]
    g[5][bs] = note(PAD, chord[1], vel, BAR)           # 3rd
    g[5][bs + 1] = note(PAD, chord[3], vel * 0.80, BAR - 1)  # 7th


def gentle_arp(g: list, bar: int, chord_idx: int, vel: float = 0.40) -> None:
    """Gentle broken chords. Quarter notes, dur=4. Ascending through voicing."""
    bs = bar * BAR
    chord = CHORDS[chord_idx]
    for beat in range(4):
        s = bs + beat * 4
        tone = chord[beat % 4]
        # Slight velocity variation for life
        v = vel * (0.92 + 0.08 * ((beat + 1) % 2))
        g[6][s] = note(ARP, tone, v, 4)


# -- PATTERN: GROOVE (4 bars) -----------------------------------------------

def make_groove() -> Pattern:
    """4 bars: establish the jazz pocket. Walking bass + drums.
    No melody. Pad fades in bar 3. Arp teases bar 4."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        chord_idx = bar % 4

        # Full drum kit from bar 0
        jazz_kick(g, bar)
        jazz_snare(g, bar)
        jazz_ride(g, bar)

        # Walking bass: the foundation
        walking_bass(g, bar, GROOVE_WALKS[chord_idx], 0.68 + bar * 0.02)

        # Pad enters softly on bar 2
        if bar >= 2:
            pad_voicing(g, bar, chord_idx, 0.25 + (bar - 2) * 0.06)

        # Arp teases in bar 3 only
        if bar == 3:
            gentle_arp(g, bar, chord_idx, 0.30)

    return Pattern(name='groove', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# -- PATTERN: MELODY (6 bars) -----------------------------------------------
# Hand-crafted melody with RESTS. Jazz breathes.
# Blue notes: Eb (b3), Ab (b5 area), Bb (b7)
# Structure: 2 phrases of 2 bars each, then a 2-bar resolution.
# Each phrase has 2-4 steps of rest between melodic fragments.

def place_lead(g: list, bar_offset: int, phrases: list) -> None:
    """Place lead melody notes. Each entry: (step_from_bar_start, midi, vel, dur)"""
    bs = bar_offset * BAR
    for step, midi, vel, dur in phrases:
        idx = bs + step
        if idx < len(g[4]):
            g[4][idx] = note(LEAD, midi, vel, dur)


def make_melody() -> Pattern:
    """6 bars: Full ensemble with bluesy lead melody.
    Melody is hand-crafted with rests between phrases.
    Two ii-V-I-vi cycles: one with melody, one for resolution."""
    steps = BAR * 6
    g = new_grid(steps)

    for bar in range(6):
        chord_idx = bar % 4

        # Drums
        jazz_kick(g, bar)
        jazz_snare(g, bar)
        jazz_ride(g, bar)

        # Walking bass: alternate lines for variety
        if bar < 4:
            walking_bass(g, bar, MELODY_WALKS_1[chord_idx], 0.75)
        else:
            walking_bass(g, bar, MELODY_WALKS_2[bar - 4], 0.72)

        # Pad: sustained warmth throughout
        pad_voicing(g, bar, chord_idx, 0.36)

        # Arp: gentle pulse
        arp_vel = 0.38 if bar < 4 else 0.42
        gentle_arp(g, bar, chord_idx, arp_vel)

    # ── LEAD MELODY ────────────────────────────────────────────────────
    # Hand-crafted. The RESTS are as important as the notes.
    # Format: (step_from_phrase_start, midi, velocity, duration)

    # Phrase 1 (bars 0-1, over Dm7 -> G7): opening call
    # Short motif, then SILENCE, then answer
    place_lead(g, 0, [
        (0,  D5,  0.60, 3),     # D — root, gentle entrance
        (3,  F5,  0.65, 3),     # F — minor 3rd, reaching up
        (6,  Eb5, 0.70, 4),     # Eb — BLUE NOTE, the smoky color
        # ---- REST steps 10-15 (6 steps of silence = breathing room) ----
        (16, G5,  0.72, 3),     # G — dominant root (bar 1 = G7)
        (19, F5,  0.65, 2),     # F — 7th of G7
        (22, E5,  0.60, 3),     # E — resolving down
        # ---- REST steps 25-31 (7 steps of silence) ----
    ])

    # Phrase 2 (bars 2-3, over Cmaj7 -> Am7): lyrical response
    # Higher, more expressive, then descends to resolve
    place_lead(g, 2, [
        (2,  G5,  0.68, 3),     # G — 5th of C, confident entry
        (5,  A5,  0.75, 2),     # A — peak of the phrase
        (8,  Ab5, 0.72, 3),     # Ab — BLUE NOTE, bending down
        (11, G5,  0.65, 3),     # G — settle
        # ---- REST steps 14-17 (4 steps of silence) ----
        (18, E5,  0.60, 3),     # E — 5th of Am, new phrase start
        (21, D5,  0.55, 2),     # D — stepping down
        (24, C5,  0.58, 4),     # C — resolution to root, long note
        # ---- REST steps 28-31 (4 steps of silence) ----
    ])

    # Phrase 3 (bars 4-5, over Dm7 -> G7): closing statement
    # Sparse, bluesy, final. More space than notes.
    place_lead(g, 4, [
        (0,  Bb5, 0.70, 4),     # Bb — BLUE NOTE (b7), bold opening
        (4,  A5,  0.68, 3),     # A — step down
        (7,  G5,  0.65, 3),     # G — settling
        # ---- REST steps 10-15 (6 steps of silence) ----
        (16, F5,  0.62, 3),     # F — 7th of G7
        (20, Eb5, 0.60, 3),     # Eb — BLUE NOTE, last taste of blues
        (24, D5,  0.55, 6),     # D — long final resolve, fading out
        # ---- silence to end ----
    ])

    return Pattern(name='melody', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# -- SONG ASSEMBLY -----------------------------------------------------------

def build_song() -> Song:
    patterns = [
        make_groove(),   # 0 — 4 bars (~8.9s at 108)
        make_melody(),   # 1 — 6 bars (~13.3s at 108)
    ]
    # Total: 10 bars ~ 22.2 seconds

    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # snare: barely right
        2:  0.28,    # ride/hats: right (jazz ride position)
        3: -0.08,    # bass: near center, slight left
        4:  0.12,    # lead: slight right (soloist position)
        5: -0.22,    # pad: left (warmth counterbalance)
        6: -0.30,    # arp: left (wide stereo with ride)
    }

    channel_effects = {
        0: {  # Kick: subtle room
            'reverb': 0.06,
        },
        1: {  # Snare/brushes: medium room
            'reverb': 0.18,
        },
        2: {  # Ride + ghost hats: shimmer space
            'delay': 0.12, 'delay_feedback': 0.18,
            'reverb': 0.15,
        },
        3: {  # Bass: tight room, warm
            'reverb': 0.08,
        },
        4: {  # Lead: smoky reverb + delay for that jazz club tail
            'reverb': 0.40,
            'delay': 0.22, 'delay_feedback': 0.28,
        },
        5: {  # Pad: deep reverb + chorus for crystalline width
            'reverb': 0.50,
            'chorus': 0.30,
        },
        6: {  # Arp: spacious delay + room
            'delay': 0.18, 'delay_feedback': 0.30,
            'reverb': 0.20,
        },
    }

    return Song(
        title='Midnight Blues v2 — Smoky Jazz Club Chip Tune',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.12,
        master_delay=0.06,
    )


# -- MAIN -------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 52)
    print("  MIDNIGHT BLUES v2 — Smoky Jazz Club Chip Tune")
    print("  ii-V-I-vi: Dm7 -> G7 -> Cmaj7 -> Am7")
    print("=" * 52)
    print()
    print(f"  BPM: {BPM}")
    print(f"  Key: C major / blue notes (Eb, Ab, Bb)")
    print()
    print("  [0-8.9s]    Groove  — Walking bass + jazz drums")
    print("  [8.9-22.2s] Melody  — Bluesy lead, full ensemble")
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

    out = Path('output/jazz_001_midnight_blues.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  2AM. Smoky jazz club. Game Boy on a tube amp.")
