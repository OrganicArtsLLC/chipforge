"""
Fractal Break v2 — Musical Drum & Bass in A minor (Aeolian)
============================================================

A complete rewrite. The original was BPM 174 with dur=1 everywhere — a wall
of clicks. This version proves that DnB energy comes from SYNCOPATION, not
speed. At BPM 140, every note has room to breathe.

Key: Am (A Aeolian) — dark, moody, classic minor
BPM: 140 (moderate — syncopation creates the urgency)
Channels: 7
  0 - Kick         (kick_deep, syncopated breakbeat — NOT four-on-floor)
  1 - Snare/Clap   (noise_clap dur=3, beats 2 & 4 + ghost on "and" of 1)
  2 - Hi-hats      (hat_crisp 8ths dur=2 + hat_open_shimmer off-beat 8ths)
  3 - Bass          (acid_bass, root notes with octave jumps, dur=4-6)
  4 - Lead          (lead_vibrato, hand-crafted dark Am melody, dur=3-4)
  5 - Pad           (pad_lush, warmth floor in every section)
  6 - Arp           (pulse_warm, 8th-note Am chord tones, dur=2)

Structure (~20 seconds at 140 BPM):
  [0-6.9s]   INTRO      4 bars  — drums + bass establishing the break
  [6.9-7.6s] THE GAP    half bar — silence, tension before the drop
  [7.6-17.9s] DROP      6 bars  — full ensemble, dark Am melody
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
BAR = 16  # 4 beats x 4 steps

# ── Helpers ──────────────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, freq: float, vel: float = 0.80, dur: int = 2) -> NoteEvent:
    return NoteEvent(midi_note=freq_to_midi(freq), velocity=min(vel, 0.85),
                     duration_steps=dur, instrument=inst)

def new_grid(channels: int, steps: int) -> list:
    return [[None] * steps for _ in range(channels)]


# ── Instrument Assignments ───────────────────────────────────────────────────

KICK    = 'kick_deep'
SNARE   = 'noise_clap'       # noise_clap has body (dur=3)
HAT_CL  = 'hat_crisp'
HAT_OP  = 'hat_open_shimmer'
BASS    = 'acid_bass'         # filter sweep Reese bass
LEAD    = 'lead_vibrato'      # built-in vibrato for expressiveness
PAD     = 'pad_lush'          # warmth floor
ARP     = 'pulse_warm'        # smooth 8th-note arpeggios

# ── Note Constants (A Aeolian: A B C D E F G) ──────────────────────────────

A1 = hz(33);  B1 = hz(35);  C2 = hz(36);  D2 = hz(38);  E2 = hz(40)
F2 = hz(41);  G2 = hz(43);  A2 = hz(45);  B2 = hz(47);  C3 = hz(48)
D3 = hz(50);  E3 = hz(52);  F3 = hz(53);  G3 = hz(55);  A3 = hz(57)
B3 = hz(59);  C4 = hz(60);  D4 = hz(62);  E4 = hz(64);  F4 = hz(65)
G4 = hz(67);  A4 = hz(69);  B4 = hz(71);  C5 = hz(72);  D5 = hz(74)
E5 = hz(76);  F5 = hz(77);  G5 = hz(79)

# Am chord tones for arp: A3, C4, E4, A4
ARP_TONES = [A3, C4, E4, A4]

# ── Shortcut constructors ───────────────────────────────────────────────────

def kick(vel: float = 0.82) -> NoteEvent:
    return note(KICK, hz(36), vel, 2)

def snare(vel: float = 0.80) -> NoteEvent:
    return note(SNARE, hz(40), vel, 3)  # dur 3 for body

def hat_cl(vel: float = 0.55) -> NoteEvent:
    return note(HAT_CL, hz(42), vel, 2)  # 8th note duration

def hat_op(vel: float = 0.60) -> NoteEvent:
    return note(HAT_OP, hz(46), vel, 2)


# ── PATTERN: INTRO (4 bars) ────────────────────────────────────────────────
# Drums + bass only. Establishing the syncopated breakbeat groove.
# No melody yet — let the rhythm speak.

def make_intro() -> Pattern:
    """4 bars: drums + bass establishing the syncopated breakbeat.
    Kick: beat 1, 'and' of 2, beat 4. Snare: 2 & 4 + ghost.
    Bass enters bar 2 with acid_bass root pulses."""
    steps = BAR * 4
    g = new_grid(7, steps)

    for bar in range(4):
        bs = bar * BAR

        # ── Kick: syncopated breakbeat (NOT four-on-floor) ──
        # beat 1 (step 0), "and" of 2 (step 6), beat 4 (step 12)
        g[0][bs + 0]  = kick(0.85)      # beat 1 — anchor
        g[0][bs + 6]  = kick(0.75)      # "and" of 2 — syncopation!
        g[0][bs + 12] = kick(0.80)      # beat 4
        # Bar 3-4: add extra ghost kick on "and" of 3 for buildup
        if bar >= 2:
            g[0][bs + 10] = kick(0.55)  # ghost — building tension

        # ── Snare: beats 2 & 4 + ghost on "and" of 1 ──
        g[1][bs + 4]  = snare(0.82)     # beat 2
        g[1][bs + 12] = snare(0.80)     # beat 4
        g[1][bs + 2]  = snare(0.35)     # ghost on "and" of 1
        # Bars 3-4: add extra ghost for buildup
        if bar >= 2:
            g[1][bs + 10] = snare(0.30) # ghost on "and" of 3

        # ── Hats: 8th notes (every 2 steps), open hat on off-beat 8ths ──
        for i in range(0, BAR, 2):
            if i % 4 == 2:
                # Off-beat 8ths get open hat
                g[2][bs + i] = hat_op(0.52 + bar * 0.04)
            else:
                # On-beat 8ths get closed hat
                vel = 0.58 if i % 4 == 0 else 0.45
                g[2][bs + i] = hat_cl(min(vel + bar * 0.03, 0.85))

        # ── Bass: enters bar 2, acid_bass root with octave jumps ──
        if bar >= 2:
            g[3][bs + 0]  = note(BASS, A1, 0.82, 6)  # root sustained
            g[3][bs + 8]  = note(BASS, A2, 0.75, 4)   # octave jump
            if bar == 3:
                g[3][bs + 12] = note(BASS, E2, 0.72, 4)  # fifth pickup

        # ── Pad: enters bar 3 (subtle, preparing for drop) ──
        if bar == 3:
            g[5][bs] = note(PAD, A3, 0.25, BAR)  # whisper of warmth

    return Pattern(name='intro', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── PATTERN: THE GAP (half bar = 8 steps of silence) ───────────────────────
# Total tension release before the drop. Everything cuts out.

def make_gap() -> Pattern:
    """Half bar of near-silence. Just a single fading hat tap.
    The void before the storm."""
    steps = 8  # half a bar
    g = new_grid(7, steps)
    # One lonely closed hat at the start, quiet — the last breath
    g[2][0] = hat_cl(0.25)
    return Pattern(name='gap', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── PATTERN: THE DROP (6 bars) ─────────────────────────────────────────────
# Full ensemble. Dark Am melody with minor 3rds and descending phrases.
# The breakbeat continues but now with full harmonic support.

def make_drop() -> Pattern:
    """6 bars: full ensemble drop. Hand-crafted Am melody over syncopated
    breakbeat. Bass gets busier. Pad and arp provide harmonic bed.
    Lead uses lead_vibrato for dark, expressive phrases."""
    steps = BAR * 6
    g = new_grid(7, steps)

    # ── Hand-crafted lead melody (lead_vibrato) ──
    # Dark Am: minor 3rds, descending phrases, occasional leap up a 5th
    # Phrase layout across 6 bars:
    #   Bars 0-1: Descending phrase A→E, with minor 3rd intervals
    #   Bars 2-3: Response phrase, leap up to E5 then descend
    #   Bars 4-5: Climax — highest note, resolving back down to A

    # Bar 0: A4 → C5 (minor 3rd up) → B4 → A4 (stepwise descent)
    g[4][0]  = note(LEAD, A4,  0.78, 4)   # A4 quarter note
    g[4][4]  = note(LEAD, C5,  0.82, 4)   # C5 — minor 3rd leap up
    g[4][8]  = note(LEAD, B4,  0.75, 3)   # B4 passing tone
    g[4][12] = note(LEAD, A4,  0.72, 4)   # resolve back to A

    # Bar 1: G4 → F4 → E4 (descending, darker) → rest
    g[4][16] = note(LEAD, G4,  0.78, 3)   # G4
    g[4][20] = note(LEAD, F4,  0.75, 3)   # F4 — getting dark
    g[4][24] = note(LEAD, E4,  0.80, 4)   # E4 — the fifth below, strong
    # steps 28-31: rest — let it breathe

    # Bar 2: LEAP! E4 → E5 (octave jump for drama) → D5 → C5
    g[4][32] = note(LEAD, E4,  0.72, 3)   # pickup from E4
    g[4][36] = note(LEAD, E5,  0.85, 4)   # LEAP up an octave! Drama!
    g[4][40] = note(LEAD, D5,  0.78, 3)   # D5 stepwise down
    g[4][44] = note(LEAD, C5,  0.75, 4)   # C5 — minor 3rd above A

    # Bar 3: B4 → A4 → G4 → A4 (resolving phrase, ending on tonic)
    g[4][48] = note(LEAD, B4,  0.78, 3)   # B4
    g[4][52] = note(LEAD, A4,  0.75, 3)   # tonic touch
    g[4][56] = note(LEAD, G4,  0.72, 4)   # dip down
    g[4][60] = note(LEAD, A4,  0.80, 4)   # resolve to A

    # Bar 4: Climax phrase — C5 → E5 → (leap up 5th) → D5 → C5
    g[4][64] = note(LEAD, C5,  0.80, 3)   # C5 launch
    g[4][68] = note(LEAD, E5,  0.85, 4)   # E5 — the fifth, soaring
    g[4][72] = note(LEAD, D5,  0.78, 3)   # D5 descent begins
    g[4][76] = note(LEAD, C5,  0.75, 4)   # C5

    # Bar 5: Final descent — B4 → A4 → E4 (leap down 5th) → A4 resolve
    g[4][80] = note(LEAD, B4,  0.78, 3)   # B4
    g[4][84] = note(LEAD, A4,  0.80, 4)   # tonic
    g[4][88] = note(LEAD, E4,  0.72, 4)   # leap DOWN a 4th — gravity
    g[4][92] = note(LEAD, A4,  0.82, 4)   # final resolve on A

    # ── Per-bar elements: drums, bass, pad, arp ──
    # Bass riffs cycle through Am-rooted patterns with acid_bass filter sweep
    bass_riffs = [
        # Riff A: root drone with fifth jump
        [(0, A1, 0.82, 6), (8, E2, 0.75, 4), (12, A1, 0.78, 4)],
        # Riff B: walking descent A→G→F→E
        [(0, A1, 0.80, 4), (4, G2, 0.72, 4), (8, F2, 0.75, 4), (12, E2, 0.78, 4)],
        # Riff C: octave jump energy
        [(0, A1, 0.82, 4), (4, A2, 0.78, 4), (8, A1, 0.75, 4), (12, E2, 0.72, 4)],
    ]

    # Arp patterns cycling through Am chord tones (A C E A) at 8th notes
    arp_patterns = [
        [0, 1, 2, 3, 2, 1, 0, 1],  # ascending-descending wave
        [0, 2, 1, 3, 0, 2, 1, 3],  # skip pattern
        [3, 2, 1, 0, 1, 2, 3, 2],  # descending wave
    ]

    for bar in range(6):
        bs = bar * BAR

        # ── Kick: syncopated breakbeat ──
        # beat 1 (step 0), "and" of 2 (step 6), beat 4 (step 12)
        g[0][bs + 0]  = kick(0.85)
        g[0][bs + 6]  = kick(0.75)      # syncopated!
        g[0][bs + 12] = kick(0.80)
        # Every other bar: add ghost on "and" of 3 for variation
        if bar % 2 == 1:
            g[0][bs + 10] = kick(0.50)

        # ── Snare: beats 2 & 4 + ghost on "and" of 1 ──
        g[1][bs + 4]  = snare(0.82)
        g[1][bs + 12] = snare(0.80)
        g[1][bs + 2]  = snare(0.35)     # ghost — "and" of 1
        # Snare roll buildup on last bar
        if bar == 5:
            g[1][bs + 13] = snare(0.45)
            g[1][bs + 14] = snare(0.58)
            g[1][bs + 15] = snare(0.72)

        # ── Hats: 8th notes (dur=2) + open hat on off-beat 8ths ──
        for i in range(0, BAR, 2):
            if i % 4 == 2:
                g[2][bs + i] = hat_op(0.55)
            else:
                vel = 0.60 if i % 4 == 0 else 0.48
                g[2][bs + i] = hat_cl(vel)

        # ── Bass: acid_bass riffs cycling ──
        riff = bass_riffs[bar % len(bass_riffs)]
        for (step_offset, freq, vel, dur) in riff:
            g[3][bs + step_offset] = note(BASS, freq, vel, dur)

        # ── Pad: sustained Am warmth floor (always present) ──
        # Alternate between Am root and relative major C for color
        if bar % 4 < 3:
            g[5][bs] = note(PAD, A3, 0.35, BAR)
        else:
            g[5][bs] = note(PAD, C4, 0.32, BAR)

        # ── Arp: 8th-note Am chord tones (dur=2, NOT 16ths) ──
        arp_pat = arp_patterns[bar % len(arp_patterns)]
        for i in range(8):  # 8 eighth notes per bar
            step = bs + i * 2
            tone_idx = arp_pat[i] % len(ARP_TONES)
            arp_vel = 0.58 if i % 2 == 0 else 0.45
            g[6][step] = note(ARP, ARP_TONES[tone_idx], arp_vel, 2)

    return Pattern(name='drop', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── SONG ASSEMBLY ────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_intro(),   # 0 — 4 bars  ~6.9s
        make_gap(),     # 1 — 0.5 bar ~0.9s  (THE GAP)
        make_drop(),    # 2 — 6 bars  ~10.3s
    ]
    # Total: 10.5 bars ~ 18 seconds at 140 BPM

    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # snare: near center
        2:  0.28,    # hats: right (wide)
        3: -0.08,    # bass: near center-left
        4:  0.12,    # lead: slight right
        5: -0.20,    # pad: left (opposite side from arp)
        6: -0.30,    # arp: left-wide
    }

    channel_effects = {
        0: {'reverb': 0.06},                                          # kick: subtle room
        1: {'reverb': 0.12},                                          # snare: medium room
        2: {'delay': 0.18, 'delay_feedback': 0.25, 'reverb': 0.08},  # hats: rhythmic space
        3: {'reverb': 0.10},                                          # bass: tight low-end
        4: {'reverb': 0.30, 'delay': 0.20, 'delay_feedback': 0.30},  # lead: rich + delay
        5: {'reverb': 0.40},                                          # pad: deep hall
        6: {'delay': 0.22, 'delay_feedback': 0.35, 'reverb': 0.10},  # arp: rhythmic echo
    }

    return Song(
        title='Fractal Break v2 — Musical DnB in Am',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.10,
        master_delay=0.00,
    )


# ── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════╗")
    print("║  FRACTAL BREAK v2                                ║")
    print("║  Musical DnB in Am  |  BPM: 140  |  ~20s         ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("  Philosophy: DnB energy from SYNCOPATION, not speed.")
    print("  Every note breathes. Every channel has effects.")
    print()
    print("  Structure:")
    print("  [0-6.9s]    Intro    — drums + bass, breakbeat groove")
    print("  [6.9-7.6s]  The Gap  — silence before the storm")
    print("  [7.6-18s]   Drop     — full ensemble, dark Am melody")
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

    out = Path('output/edm_003_fractal_break.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  Syncopation > Speed. Minor 3rds > Phrygian b2 spam.")
