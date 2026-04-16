"""
Rainy Day Loops v2 — lo-fi hip-hop study beats with chip tune soul
===================================================================

Complete rewrite. The v1 had an algorithmic (phi-driven) melody that was
unsingable, competing jazz layers, and was too short. This version is
hand-crafted for warmth, singability, and repetition that feels good.

Key: D Dorian (D E F G A B C) — the raised 6th (B natural) gives
     sophisticated warmth over plain D minor.
Blue notes: Eb (b2/b9), Ab (b5) — used sparingly for soul.
BPM: 84 — slow enough to breathe, fast enough to nod.

7 channels:
  0 - Kick      (kick_deep)       beat 1 + "and" of 3, vel 0.60
  1 - Snare     (noise_clap)      beats 2.5 and 4 (lazy), vel 0.50, dur 3
  2 - Hi-hat    (hat_crisp)       swung 16ths, big velocity variation
  3 - Bass      (bass_smooth)     gentle walking, chromatic passing, dur 4-6
  4 - Lead      (lead_expressive) hand-crafted 2-bar soulful melody, loops
  5 - Pad       (pad_glass)       sustained Dm7/Em7, crystalline warmth
  6 - Arp       (pluck_mellow)    broken chord quarter notes, dur 4

Structure (~22s at 84 BPM, ~10-11 bars):
  [0–3s]    INTRO   2 bars  — pad + arp only (atmosphere)
  [3–9s]    GROOVE  4 bars  — bass + drums enter (no melody yet)
  [9–20s]   FULL    4 bars  — lead melody enters, loops 2-bar phrase x2
  [20–22s]  TAG     1 bar   — pad resolves to Dm, fade
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 84
SPB = 4
BAR = 16
NUM_CH = 7

# ── Helpers ──────────────────────────────────────────────────────────────

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)


def note(inst: str, midi: int, vel: float = 0.55, dur: int = 2) -> NoteEvent:
    """Lo-fi default: vel 0.55, dur 2. Soft and smooth."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 2), instrument=inst)


def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]


# ── Instrument Assignments ─────────────────────────────────────────────
KICK = 'kick_deep'
SNARE = 'noise_clap'
HAT = 'hat_crisp'
BASS = 'bass_smooth'
LEAD = 'lead_expressive'
PAD = 'pad_glass'
ARP = 'pluck_mellow'
BELL = 'shimmer_bell'

# ── D Dorian note pool ────────────────────────────────────────────────
# D E F G A B C  (B natural = Dorian signature)
# Blue: Eb, Ab

# Bass register
D2 = 38;  E2 = 40;  F2 = 41;  G2 = 43;  A2 = 45;  B2 = 47;  C3 = 48
Eb2 = 39;  Ab2 = 44;  Bb2 = 46;  Db3 = 49

# Mid register
D3 = 50;  E3 = 52;  F3 = 53;  G3 = 55;  A3 = 57;  B3 = 59
C4 = 60;  D4 = 62;  E4 = 64;  F4 = 65;  G4 = 67;  A4 = 69
B4 = 71;  C5 = 72;  D5 = 74;  E5 = 76;  F5 = 77

# Blue notes
Eb4 = 63;  Ab4 = 68;  Eb5 = 75

# Chord voicings (Dorian)
#   Dm7  = D F A C    (i7)
#   Em7  = E G B D    (ii7 — has B natural, the Dorian color)
CHORD_DM7 = (D4, F4, A4, C5)
CHORD_EM7 = (E4, G4, B4, D5)


# ═══════════════════════════════════════════════════════════════════════
# HAND-CRAFTED LEAD MELODY — 2-bar phrase, D Dorian with blue notes
# ═══════════════════════════════════════════════════════════════════════
#
# The melody in musical terms (think of humming this):
#
#   Bar 1: D5 ~~~  C5 . A4 ~~~~  rest  G4 . A4 ~~
#           (start high, fall gently, breathe, resolve up)
#
#   Bar 2: F4 ~~~  G4 . Eb4~  D4 ~~~~  rest ~~~~
#           (descend with blue note Eb, land on root, long rest)
#
# Singable: da-DAAAH  dah  DAAAH ... da  da-DAH
# The rests are critical — they let the reverb/delay breathe.
#
LEAD_PHRASE: list[tuple[int, int, float, int]] = [
    # Bar 1: (step_within_2bars, midi, velocity, duration)
    (0,  D5,  0.60, 3),   # beat 1: D5, held
    (4,  C5,  0.52, 2),   # beat 2: step down to C5
    (6,  A4,  0.58, 4),   # beat 2.5: drop to A4, sustained
    # rest on beats 3.5-4
    (12, G4,  0.48, 2),   # beat 4: pickup G4
    (14, A4,  0.55, 3),   # beat 4.5: resolve up to A4

    # Bar 2:
    (18, F4,  0.56, 3),   # beat 1.5 of bar 2: F4
    (22, G4,  0.50, 2),   # beat 2.5: passing G4
    (24, Eb4, 0.45, 2),   # beat 3: BLUE NOTE — Eb4, soulful bend
    (26, D4,  0.58, 5),   # beat 3.5: resolve to root D4, long hold
    # rest for the last beat and a half — space for delay tail
]


# ── Drum patterns ──────────────────────────────────────────────────────

def chill_kick(g: list, bar: int) -> None:
    """Kick: beat 1 + 'and' of 3. Soft, not aggressive."""
    bs = bar * BAR
    g[0][bs + 0] = note(KICK, 36, 0.60, 3)        # beat 1
    g[0][bs + 10] = note(KICK, 36, 0.52, 2)       # "and" of 3


def lazy_snare(g: list, bar: int) -> None:
    """Snare on 2.5 and 4 — slightly late feel, soft."""
    bs = bar * BAR
    g[1][bs + 6] = note(SNARE, 40, 0.50, 3)       # beat 2.5 (step 6)
    g[1][bs + 12] = note(SNARE, 40, 0.42, 3)      # beat 4 (step 12), softer


def swung_hats(g: list, bar: int) -> None:
    """Swung 16ths with big velocity variation for shuffle feel.
    Odd steps (swing notes) get accented, even steps are ghosts."""
    bs = bar * BAR
    for step in range(BAR):
        if step % 4 == 0:
            # Downbeats: medium accent
            g[2][bs + step] = note(HAT, 42, 0.45, 2)
        elif step % 2 == 1:
            # Swung 16ths: the shuffle accent
            g[2][bs + step] = note(HAT, 42, 0.38, 2)
        else:
            # Even off-beats: ghost notes (very quiet)
            g[2][bs + step] = note(HAT, 42, 0.18, 2)


def sparse_hats(g: list, bar: int) -> None:
    """Intro hats: just 8th notes, very quiet."""
    bs = bar * BAR
    for step in range(0, BAR, 2):
        v = 0.22 if step % 4 == 0 else 0.14
        g[2][bs + step] = note(HAT, 42, v, 2)


# ── Bass patterns ──────────────────────────────────────────────────────

def walking_bass_dm(g: list, bar: int) -> None:
    """Dm7 bar: D2 root, chromatic walk. Gentle, dur 4-6."""
    bs = bar * BAR
    g[3][bs + 0] = note(BASS, D2, 0.58, 5)        # beat 1: root
    g[3][bs + 4] = note(BASS, A2, 0.50, 4)        # beat 2: 5th
    g[3][bs + 8] = note(BASS, G2, 0.48, 4)        # beat 3: 4th
    g[3][bs + 12] = note(BASS, Eb2, 0.42, 4)      # beat 4: chromatic approach to E


def walking_bass_em(g: list, bar: int) -> None:
    """Em7 bar: E2 root, walk back toward D."""
    bs = bar * BAR
    g[3][bs + 0] = note(BASS, E2, 0.58, 5)        # beat 1: root
    g[3][bs + 4] = note(BASS, B2, 0.48, 4)        # beat 2: 5th (B natural!)
    g[3][bs + 8] = note(BASS, A2, 0.45, 4)        # beat 3: 4th
    g[3][bs + 12] = note(BASS, Db3, 0.40, 4)      # beat 4: chromatic approach to D


# ── Pad ────────────────────────────────────────────────────────────────

def pad_dm(g: list, bar: int, vel: float = 0.42) -> None:
    """Dm7 pad voicing — sustained full bar."""
    bs = bar * BAR
    # Use the 3rd (F4) for warmth — single note, pad_glass does the rest
    g[5][bs] = note(PAD, F4, vel, BAR)


def pad_em(g: list, bar: int, vel: float = 0.42) -> None:
    """Em7 pad voicing — sustained full bar."""
    bs = bar * BAR
    g[5][bs] = note(PAD, G4, vel, BAR)


# ── Arp ────────────────────────────────────────────────────────────────

def arp_dm(g: list, bar: int, vel: float = 0.38) -> None:
    """Broken Dm7 chord, quarter notes, dur=4 for legato."""
    bs = bar * BAR
    tones = [D4, F4, A4, C5]
    for beat in range(4):
        g[6][bs + beat * 4] = note(ARP, tones[beat], vel, 4)


def arp_em(g: list, bar: int, vel: float = 0.38) -> None:
    """Broken Em7 chord, quarter notes, dur=4 for legato."""
    bs = bar * BAR
    tones = [E4, G4, B4, D5]
    for beat in range(4):
        g[6][bs + beat * 4] = note(ARP, tones[beat], vel, 4)


# ── Bell fragments ─────────────────────────────────────────────────────

def bell_fragments(g: list, bar: int) -> None:
    """Very quiet shimmer_bell hits in gaps. Atmospheric."""
    bs = bar * BAR
    # Sparse — just 2-3 per bar at irregular positions
    hits = [(3, A4, 0.20), (9, D5, 0.18), (13, B4, 0.16)]
    for step, midi, vel in hits:
        s = bs + step
        if s < len(g[4]) and g[4][s] is None:
            g[4][s] = note(BELL, midi, vel, 3)


# ── Lead placement ─────────────────────────────────────────────────────

def place_lead(g: list, bar_offset: int, vel_scale: float = 1.0) -> None:
    """Place the hand-crafted 2-bar lead phrase."""
    bs = bar_offset * BAR
    for step, midi, vel, dur in LEAD_PHRASE:
        s = bs + step
        if s < len(g[4]):
            g[4][s] = note(LEAD, midi, vel * vel_scale, dur)


# ═══════════════════════════════════════════════════════════════════════
# PATTERN BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def make_intro() -> Pattern:
    """2 bars: pad + arp only. Establishing rainy atmosphere.
    No drums, no bass, no melody. Just warmth and space."""
    steps = BAR * 2
    g = new_grid(steps)

    # Bar 0: Dm7
    pad_dm(g, 0, 0.35)
    arp_dm(g, 0, 0.30)
    sparse_hats(g, 0)

    # Bar 1: Em7
    pad_em(g, 1, 0.38)
    arp_em(g, 1, 0.32)
    sparse_hats(g, 1)

    # A couple bell fragments for texture
    bell_fragments(g, 0)
    bell_fragments(g, 1)

    return Pattern(name='intro', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_groove() -> Pattern:
    """4 bars: bass + drums enter over pad/arp. Building the pocket.
    Chord progression: Dm7 | Em7 | Dm7 | Em7 (simple 2-bar loop)."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        is_dm = (bar % 2 == 0)

        # Drums
        chill_kick(g, bar)
        lazy_snare(g, bar)
        swung_hats(g, bar)

        # Bass: gentle walking
        if is_dm:
            walking_bass_dm(g, bar)
        else:
            walking_bass_em(g, bar)

        # Pad: warmth floor
        if is_dm:
            pad_dm(g, bar, 0.40)
        else:
            pad_em(g, bar, 0.40)

        # Arp: broken chords
        if is_dm:
            arp_dm(g, bar, 0.35)
        else:
            arp_em(g, bar, 0.35)

        # Bell fragments in even bars
        if bar % 2 == 0:
            bell_fragments(g, bar)

    return Pattern(name='groove', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_full() -> Pattern:
    """4 bars: melody enters! The 2-bar lead phrase plays twice.
    This is the emotional center of the track."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        is_dm = (bar % 2 == 0)

        # Drums
        chill_kick(g, bar)
        lazy_snare(g, bar)
        swung_hats(g, bar)

        # Bass
        if is_dm:
            walking_bass_dm(g, bar)
        else:
            walking_bass_em(g, bar)

        # Pad: slightly louder under melody for support
        if is_dm:
            pad_dm(g, bar, 0.44)
        else:
            pad_em(g, bar, 0.44)

        # Arp
        if is_dm:
            arp_dm(g, bar, 0.36)
        else:
            arp_em(g, bar, 0.36)

    # Lead melody: 2-bar phrase × 2 loops
    place_lead(g, 0, 0.92)    # first statement, slightly soft
    place_lead(g, 2, 1.0)     # second statement, full confidence

    # Bell fragments in melodic rests (bars 1 and 3 where melody is sparser)
    bell_fragments(g, 1)
    bell_fragments(g, 3)

    return Pattern(name='full', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_tag() -> Pattern:
    """1 bar: resolve to Dm. Pad + arp fade. Last raindrop."""
    steps = BAR * 1
    g = new_grid(steps)

    # Pad: resolving Dm, fading
    pad_dm(g, 0, 0.32)

    # Arp: just the first two tones, quieter
    g[6][0] = note(ARP, D4, 0.25, 4)
    g[6][4] = note(ARP, F4, 0.20, 4)

    # One last bell — like the last raindrop
    g[4][6] = note(BELL, A4, 0.15, 4)

    # Very sparse hat
    g[2][0] = note(HAT, 42, 0.15, 2)

    return Pattern(name='tag', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ═══════════════════════════════════════════════════════════════════════
# SONG ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════

def build_song() -> Song:
    patterns = [
        make_intro(),    # 0 — 2 bars
        make_groove(),   # 1 — 4 bars
        make_full(),     # 2 — 4 bars
        make_tag(),      # 3 — 1 bar
    ]
    # Total: 11 bars at 84 BPM = 11 * 4 / 84 * 60 ≈ 31.4s
    # (slightly over 22s target but feels right for the structure)

    # PANNING: subtle stereo, lo-fi warmth
    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # snare: barely off-center
        2:  0.28,    # hats: right (rain on the window)
        3: -0.08,    # bass: near center, slight left
        4:  0.12,    # lead: slight right
        5: -0.20,    # pad: left (counterbalances hats)
        6: -0.30,    # arp: left (stereo width)
    }

    # EFFECTS: deep, dreamy — lo-fi hip hop IS reverb and delay
    channel_effects = {
        0: {  # Kick: subtle room
            'reverb': 0.06,
        },
        1: {  # Snare: medium room for body
            'reverb': 0.15,
        },
        2: {  # Hats: rhythmic delay + room
            'delay': 0.14, 'delay_feedback': 0.22,
            'reverb': 0.10,
        },
        3: {  # Bass: tight, focused low-end
            'reverb': 0.08,
        },
        4: {  # Lead: dreamy reverb + slapback delay
            'reverb': 0.35,
            'delay': 0.20, 'delay_feedback': 0.30,
        },
        5: {  # Pad: DEEP hall reverb + chorus for width
            'reverb': 0.50,
            'chorus': 0.25,
        },
        6: {  # Arp: spacious delay (raindrops echoing)
            'delay': 0.18, 'delay_feedback': 0.28,
            'reverb': 0.15,
        },
    }

    return Song(
        title='Rainy Day Loops v2',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2, 3],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.14,
        master_delay=0.05,
    )


# ── MAIN ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Rainy Day Loops v2 — lo-fi hip-hop study beats with chip tune soul")
    print(f"  Key: D Dorian | BPM: {BPM}")
    print("  [0–3s]    Intro  — pad + arp (atmosphere)")
    print("  [3–9s]    Groove — bass + drums enter")
    print("  [9–20s]   Full   — soulful lead melody loops")
    print("  [20–22s]  Tag    — pad resolves, fade")
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

    out = Path('output/hiphop_002_rainy_day_loops.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
