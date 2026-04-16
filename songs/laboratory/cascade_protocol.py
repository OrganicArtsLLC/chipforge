"""
Cascade Protocol — 60-second rave masterpiece in ChipForge
============================================================

Inspired by:
  - Deadmau5 "Strobe"            — slow harmonic evolution, euphoric breakdown
  - Daft Punk "Around the World" — unstoppable grooves, perfect voice leading
  - Tune Up! "Raver's Fantasy"   — staccato hook, three-note inevitability
  - Tiësto "Adagio for Strings"  — stepwise melody, appoggiaturas, emotional arc

Key: F# minor (Aeolian)
BPM: 130
Chord cycle: i→VI→III→VII  (F#m→D→A→E) — the classic trance epic cycle

7 channels:
  0 - Kick drum         (four-on-floor + ghost notes)
  1 - Snare / clap      (backbeat 2 & 4, rolls)
  2 - Hi-hat            (closed 16ths, open hat on upbeats)
  3 - Sub bass          (root-fifth-octave walking line)
  4 - Arpeggio          (chord tones, staccato 16th notes)
  5 - Lead melody       (the hook: F#4→A4→C#5→D5→C#5→B4→A4→F#5)
  6 - Counter melody    (harmonic response, Tiësto-style breakdown voice)

Structure (~60 seconds total at 130 BPM):
  [0-7s]   INTRO       4 bars  — sub bass + hats only, tension
  [7-22s]  BUILD       8 bars  — arpeggios enter, kick on 1+3
  [22-51s] DROP 1     16 bars  — THE EUPHORIA. Full kit + lead melody
  [51-58s] BREAKDOWN   4 bars  — stripped back, counter melody exposed
  [58-65s] REBUILD     4 bars  — arpeggios return, energy rises
  [65-80s] DROP 2      8 bars  — everything + F#5 climax peaks
"""

import sys
import os
import math
sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 130
SPB = 4   # steps per beat (16th-note grid)
STEPS_PER_BAR = 16  # 4 beats × 4 subdivisions

# ── Frequency helpers ────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    """MIDI note number → Hz (A4=440)."""
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    """Hz → nearest MIDI note number."""
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

# ── Note frequency pool (F# minor scale) ─────────────────────────────────────
# Sub bass register (MIDI 30–42)
FS2 = hz(30);  A2  = hz(33);  B2  = hz(35);  CS3 = hz(37);  D3  = hz(38)
E3  = hz(40);  FS3 = hz(42)

# Mid register (MIDI 42–57)
GS3 = hz(44);  A3  = hz(45);  B3  = hz(47);  CS4 = hz(49);  D4  = hz(50)
E4  = hz(52);  FS4 = hz(54);  GS4 = hz(56);  A4  = hz(57)

# Upper register (MIDI 57–69)
B4  = hz(59);  CS5 = hz(61);  D5  = hz(62);  E5  = hz(64);  FS5 = hz(66)
GS5 = hz(68);  A5  = hz(69)

# ── Chord voicings ────────────────────────────────────────────────────────────
# i→VI→III→VII cycle: F#m → D → A → E
CHORDS = {
    'Fsm': [FS4, A4, CS5, FS5],    # F#m  — home, dark, deep
    'D':   [D4,  FS4,  A4, D5],    # D    — warm, VI lift
    'A':   [A4,  CS5,  E5, A5],    # A    — bright, III
    'E':   [E4,  GS4,  B4, E5],    # E    — tension, VII
}
CYCLE = ['Fsm', 'D', 'A', 'E']     # repeating 4-chord loop

# Sub bass roots per chord
SUB_ROOTS = {
    'Fsm': hz(30),   # F#2
    'D':   hz(26),   # D2
    'A':   hz(21),   # A1
    'E':   hz(28),   # E2
}

# ── Instrument keys (must match src/instruments.py PRESETS keys) ─────────────
KICK    = 'kick_deep'
SNARE   = 'snare_tight'
HAT_CL  = 'hat_crisp'
HAT_OP  = 'hat_open_shimmer'
BASS    = 'bass_sub'
ARP     = 'saw_filtered'
LEAD    = 'lead_bright'
COUNTER = 'pad_lush'

# ── Helper constructors ───────────────────────────────────────────────────────

def note(inst: str, freq: float, vel: float = 0.8, dur: int = 1) -> NoteEvent:
    """Create a NoteEvent from an Hz frequency (converts to MIDI note number)."""
    midi = freq_to_midi(freq) if freq > 0 else 0
    return NoteEvent(midi_note=midi, velocity=vel, duration_steps=dur, instrument=inst)

def kick(vel: float = 0.90) -> NoteEvent:  return note(KICK,   hz(36), vel, 1)
def snare(vel: float = 0.80) -> NoteEvent: return note(SNARE,  hz(40), vel, 1)
def hat(vel: float = 0.55) -> NoteEvent:   return note(HAT_CL, hz(42), vel, 1)
def hat_op(vel: float = 0.65) -> NoteEvent: return note(HAT_OP, hz(46), vel, 1)

def new_grid(channels: int, steps: int) -> list:
    return [[None] * steps for _ in range(channels)]

# ── PATTERN: INTRO ────────────────────────────────────────────────────────────

def make_intro() -> Pattern:
    """4 bars: sub bass root pulses + sparse offbeat hats. Pure tension."""
    steps = STEPS_PER_BAR * 4
    g = new_grid(7, steps)

    for s in range(steps):
        # Hi-hat: offbeat 8th notes only (the 'and' of each beat)
        if s % 4 == 2:
            g[2][s] = hat(0.38 + (s / steps) * 0.10)

    for bar in range(4):
        bs = bar * STEPS_PER_BAR
        cname = CYCLE[bar % 4]
        r = SUB_ROOTS[cname]
        # Sub bass: root whole-note pulse + fifth on beat 3
        g[3][bs]     = note(BASS, r,       0.70, 4)
        g[3][bs + 8] = note(BASS, r * 1.5, 0.52, 3)   # perfect fifth

    return Pattern(name='intro', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── PATTERN: BUILD ────────────────────────────────────────────────────────────

def make_build() -> Pattern:
    """8 bars: arpeggios enter, kick on beats 1+3, bass walk begins.
    No snare yet — withholding the backbeat builds anticipation."""
    steps = STEPS_PER_BAR * 8
    g = new_grid(7, steps)

    for bar in range(8):
        bs = bar * STEPS_PER_BAR
        cname = CYCLE[bar % 4]
        chord_notes = CHORDS[cname]
        r = SUB_ROOTS[cname]

        # Kick: half-time feel — beats 1 and 3 only
        g[0][bs]     = kick(0.82 + bar * 0.01)
        g[0][bs + 8] = kick(0.78 + bar * 0.01)

        # Hi-hat: 8th notes, velocity swells as bar progresses
        for s in range(STEPS_PER_BAR):
            if s % 2 == 0:
                g[2][bs + s] = hat(0.50 + (s == 0) * 0.12 + (bar / 8) * 0.08)

        # Arpeggio: ascending 16th staccato — the Raver's Fantasy trigger
        # Pattern cycles through chord tones in a rising wave
        arp_seq = [0, 1, 2, 3, 2, 1, 0, 1, 2, 3, 1, 2, 3, 2, 1, 0]
        for s in range(STEPS_PER_BAR):
            deg = arp_seq[s] % len(chord_notes)
            vel = 0.42 + (bar / 8) * 0.28 + (s % 4 == 0) * 0.08
            g[4][bs + s] = note(ARP, chord_notes[deg], min(vel, 0.82), 1)

        # Sub bass: root + fifth walk
        g[3][bs]      = note(BASS, r,       0.78, 3)
        g[3][bs + 4]  = note(BASS, r * 1.5, 0.58, 2)
        g[3][bs + 8]  = note(BASS, r,       0.74, 3)
        g[3][bs + 12] = note(BASS, r * 4/3, 0.55, 2)   # fourth

    return Pattern(name='build', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── PATTERN: DROP 1 ───────────────────────────────────────────────────────────

def make_drop1() -> Pattern:
    """16 bars: THE EUPHORIA DROP.
    Full four-on-floor kit. Lead melody enters. Bass walking line.
    2-bar hook repeats 8 times with slight velocity lift each pass."""
    steps = STEPS_PER_BAR * 16
    g = new_grid(7, steps)

    # ── LEAD MELODY ──────────────────────────────────────────────────────────
    # The 2-bar hook: bar A + bar B
    #   Bar A: F#4(Q) — A4(Q) — C#5(Q.) — A4(E)
    #   Bar B: D5(Q.) — CS5(E) — B4(Q) — A4(Q)
    # Each rep gains +1% velocity → subtle swell across 16 bars (Strobe technique)
    for rep in range(8):
        ba = rep * 2 * STEPS_PER_BAR        # bar A start step
        bb = ba + STEPS_PER_BAR             # bar B start step
        vb = rep * 0.012                    # velocity boost per rep

        # Bar A placement
        g[5][ba]      = note(LEAD, FS4, min(0.88 + vb, 1.0), 4)
        g[5][ba + 4]  = note(LEAD, A4,  min(0.80 + vb, 1.0), 3)
        g[5][ba + 8]  = note(LEAD, CS5, min(0.86 + vb, 1.0), 5)
        g[5][ba + 13] = note(LEAD, A4,  min(0.76 + vb, 1.0), 3)

        # Bar B placement
        g[5][bb]      = note(LEAD, D5,  min(0.90 + vb, 1.0), 6)
        g[5][bb + 6]  = note(LEAD, CS5, min(0.78 + vb, 1.0), 2)
        g[5][bb + 8]  = note(LEAD, B4,  min(0.76 + vb, 1.0), 4)
        g[5][bb + 12] = note(LEAD, A4,  min(0.84 + vb, 1.0), 4)

        # Climax note: F#5 on the final beat of bar B, reps 3 and 7
        # (bars 8 and 16 — the "lift" moment every 4 bars like Strobe's peak)
        if rep in (3, 7):
            g[5][bb + 2] = note(LEAD, FS5, min(0.95 + vb, 1.0), 4)

    # ── DRUMS + BASS (per bar) ────────────────────────────────────────────────
    for bar in range(16):
        bs = bar * STEPS_PER_BAR
        cname = CYCLE[bar % 4]
        chord_notes = CHORDS[cname]
        r = SUB_ROOTS[cname]

        # Four-on-floor kick + ghost kick before beat 3
        g[0][bs]      = kick(0.92)
        g[0][bs + 4]  = kick(0.90)
        g[0][bs + 7]  = kick(0.52)    # ghost — syncopation
        g[0][bs + 8]  = kick(0.92)
        g[0][bs + 12] = kick(0.90)

        # Snare: backbeat 2 & 4, snare roll buildup every 4th bar
        g[1][bs + 4]  = snare(0.85)
        g[1][bs + 12] = snare(0.85)
        if bar % 4 == 3:
            g[1][bs + 13] = snare(0.48)
            g[1][bs + 14] = snare(0.60)
            g[1][bs + 15] = snare(0.72)

        # Hi-hat: 16th stream, open hat on off-beat 8ths (& of 2, & of 4)
        for s in range(STEPS_PER_BAR):
            step = bs + s
            if s in (6, 14):
                g[2][step] = hat_op(0.55)
            elif s % 2 == 0:
                g[2][step] = hat(0.48 + (s % 4 == 0) * 0.10)
            else:
                g[2][step] = hat(0.32)

        # Bass: Around the World-style walking line
        g[3][bs]      = note(BASS, r,       0.84, 3)
        g[3][bs + 3]  = note(BASS, r * 1.5, 0.64, 2)   # P5
        g[3][bs + 5]  = note(BASS, r * 2,   0.58, 2)   # oct
        g[3][bs + 8]  = note(BASS, r,       0.80, 3)
        g[3][bs + 11] = note(BASS, r * 4/3, 0.60, 2)   # P4
        g[3][bs + 13] = note(BASS, r * 9/8, 0.55, 2)   # M2
        g[3][bs + 15] = note(BASS, r * 1.5, 0.58, 1)   # P5 pickup

        # Arpeggio: fills gaps the melody leaves (quieter — under the lead)
        arp_pat = [0, 2, 1, 3, 0, 3, 2, 1, 0, 1, 3, 2, 1, 0, 2, 3]
        for s in range(STEPS_PER_BAR):
            step = bs + s
            if g[5][step] is None:
                deg = arp_pat[s] % len(chord_notes)
                g[4][step] = note(ARP, chord_notes[deg], 0.38, 1)

    return Pattern(name='drop1', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── PATTERN: BREAKDOWN ────────────────────────────────────────────────────────

def make_breakdown() -> Pattern:
    """4 bars: everything stripped. Only sub bass root + sparse hat +
    sweeping counter-melody pad. The Strobe breakdown — make it ache."""
    steps = STEPS_PER_BAR * 4
    g = new_grid(7, steps)

    # Counter-melody: stepwise descending line, Tiësto-style
    # C#5 → B4 → A4 → G#4 → F#4 (resolves home after the journey)
    counter_phrases = [
        [(CS5, 0.55, 8),  (A4, 0.50, 7)],           # bar 0
        [(B4,  0.52, 7),  (GS4, 0.48, 8)],           # bar 1
        [(A4,  0.58, 8),  (FS4, 0.52, 7)],           # bar 2
        [(E4,  0.50, 6),  (FS4, 0.55, 4), (A4, 0.60, 4)],  # bar 3: resolve up
    ]

    for bar in range(4):
        bs = bar * STEPS_PER_BAR
        cname = CYCLE[bar % 4]
        r = SUB_ROOTS[cname]

        # Sub bass: root held for 8 steps (half bar)
        g[3][bs] = note(BASS, r, 0.62, 8)

        # Sparse hat: beats 1 and 3 only
        g[2][bs]     = hat(0.32)
        g[2][bs + 8] = hat(0.28)

        # Counter melody placed sequentially
        step = bs
        for (freq, vel, dur) in counter_phrases[bar]:
            if step < bs + STEPS_PER_BAR:
                g[6][step] = note(COUNTER, freq, vel, min(dur, bs + STEPS_PER_BAR - step))
                step += dur

    return Pattern(name='breakdown', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── PATTERN: REBUILD ─────────────────────────────────────────────────────────

def make_rebuild() -> Pattern:
    """4 bars: arpeggios return immediately, kick phases back in bar 2,
    bass gets busier, snare holds off until bar 3. Building to Drop 2."""
    steps = STEPS_PER_BAR * 4
    g = new_grid(7, steps)

    for bar in range(4):
        bs = bar * STEPS_PER_BAR
        cname = CYCLE[bar % 4]
        chord_notes = CHORDS[cname]
        r = SUB_ROOTS[cname]

        # Kick: enter on bars 1+ (half-time first, then four-on-floor bar 3)
        if bar >= 1:
            g[0][bs]     = kick(0.78 + bar * 0.04)
            g[0][bs + 8] = kick(0.76 + bar * 0.04)
        if bar >= 3:
            g[0][bs + 4]  = kick(0.84)
            g[0][bs + 12] = kick(0.82)

        # Snare: bar 3 only (the anticipation withhold)
        if bar >= 3:
            g[1][bs + 4]  = snare(0.82)
            g[1][bs + 12] = snare(0.84)

        # Hi-hat: density ramps up bar by bar
        for s in range(STEPS_PER_BAR):
            if bar == 0:
                if s % 4 == 0: g[2][bs + s] = hat(0.40)
            elif bar <= 1:
                if s % 2 == 0: g[2][bs + s] = hat(0.48)
            else:
                if s % 2 == 0: g[2][bs + s] = hat(0.55)
                else:           g[2][bs + s] = hat(0.30)

        # Bass: progressively busier
        g[3][bs] = note(BASS, r, 0.72, 4)
        if bar >= 1: g[3][bs + 4]  = note(BASS, r * 1.5, 0.58, 2)
        if bar >= 2: g[3][bs + 8]  = note(BASS, r,       0.70, 4)
        if bar >= 3:
            g[3][bs + 12] = note(BASS, r * 4/3, 0.58, 2)
            g[3][bs + 14] = note(BASS, r * 1.5, 0.60, 2)

        # Arpeggio: comes back strong from bar 0
        vel_base = 0.40 + (bar / 4) * 0.30
        arp_pat  = [0, 2, 1, 3, 2, 0, 3, 1, 0, 3, 1, 2, 3, 0, 2, 1]
        for s in range(STEPS_PER_BAR):
            deg = arp_pat[s] % len(chord_notes)
            g[4][bs + s] = note(ARP, chord_notes[deg], min(vel_base, 0.78), 1)

    return Pattern(name='rebuild', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── PATTERN: DROP 2 ───────────────────────────────────────────────────────────

def make_drop2() -> Pattern:
    """8 bars: MAXIMUM ENERGY. Same hook. Counter melody joins the lead.
    F#5 climax fires every 2 bars — no withholding, full euphoria."""
    steps = STEPS_PER_BAR * 8
    g = new_grid(7, steps)

    # ── Lead melody: same 2-bar hook, now with every rep maxed out ────────────
    for rep in range(4):
        ba = rep * 2 * STEPS_PER_BAR
        bb = ba + STEPS_PER_BAR
        vb = 0.04 + rep * 0.015

        g[5][ba]      = note(LEAD, FS4, min(0.93 + vb, 1.0), 4)
        g[5][ba + 4]  = note(LEAD, A4,  min(0.85 + vb, 1.0), 3)
        g[5][ba + 8]  = note(LEAD, CS5, min(0.90 + vb, 1.0), 5)
        g[5][ba + 13] = note(LEAD, A4,  min(0.82 + vb, 1.0), 3)

        g[5][bb]      = note(LEAD, D5,  min(0.95 + vb, 1.0), 6)
        g[5][bb + 6]  = note(LEAD, CS5, min(0.84 + vb, 1.0), 2)
        g[5][bb + 8]  = note(LEAD, B4,  min(0.82 + vb, 1.0), 4)
        g[5][bb + 12] = note(LEAD, A4,  min(0.90 + vb, 1.0), 4)

        # F#5 fires every rep (not just occasionally — we're at the peak)
        g[5][bb + 2] = note(LEAD, FS5, min(0.97 + vb, 1.0), 4)

        # Counter melody joins: fills the harmonic space between melody notes
        counter_drop2 = [(CS5, 0.42, 4), (E5, 0.40, 4)]
        c_step = ba
        for (freq, vel, dur) in counter_drop2:
            if c_step < ba + STEPS_PER_BAR and g[6][c_step] is None:
                g[6][c_step] = note(COUNTER, freq, vel, dur)
            c_step += dur

    # ── Drums + bass per bar ──────────────────────────────────────────────────
    for bar in range(8):
        bs = bar * STEPS_PER_BAR
        cname = CYCLE[bar % 4]
        chord_notes = CHORDS[cname]
        r = SUB_ROOTS[cname]

        # Kick: four-on-floor + tighter ghost notes
        g[0][bs]      = kick(0.94)
        g[0][bs + 4]  = kick(0.92)
        g[0][bs + 7]  = kick(0.55)     # ghost before beat 3
        g[0][bs + 8]  = kick(0.94)
        g[0][bs + 11] = kick(0.48)     # ghost before beat 4
        g[0][bs + 12] = kick(0.92)

        # Snare: backbeat + roll every 4th bar
        g[1][bs + 4]  = snare(0.90)
        g[1][bs + 12] = snare(0.90)
        if bar % 4 == 3:
            for rs in range(11, 16):
                g[1][bs + rs] = snare(min(0.38 + rs * 0.06, 0.92))

        # Hi-hat: full 16th stream with open shimmers
        for s in range(STEPS_PER_BAR):
            step = bs + s
            if s in (6, 14):
                g[2][step] = hat_op(0.62)
            elif s % 2 == 0:
                g[2][step] = hat(0.54 + (s % 4 == 0) * 0.12)
            else:
                g[2][step] = hat(0.36)

        # Bass: fullest version — 8th-note walk
        g[3][bs]      = note(BASS, r,       0.88, 2)
        g[3][bs + 2]  = note(BASS, r * 1.5, 0.70, 2)
        g[3][bs + 4]  = note(BASS, r * 2,   0.64, 2)
        g[3][bs + 6]  = note(BASS, r * 1.5, 0.62, 2)
        g[3][bs + 8]  = note(BASS, r,       0.86, 2)
        g[3][bs + 10] = note(BASS, r * 4/3, 0.66, 2)
        g[3][bs + 12] = note(BASS, r * 9/8, 0.60, 2)
        g[3][bs + 14] = note(BASS, r * 1.5, 0.66, 2)

        # Arpeggio: alternating direction for extra energy
        arp_up   = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
        arp_down = [3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0]
        arp_pick = arp_up if bar % 2 == 0 else arp_down
        for s in range(STEPS_PER_BAR):
            step = bs + s
            if g[5][step] is None and g[6][step] is None:
                deg = arp_pick[s] % len(chord_notes)
                g[4][step] = note(ARP, chord_notes[deg], 0.46, 1)

    return Pattern(name='drop2', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── ASSEMBLE SONG ─────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_intro(),       # index 0 — 4 bars  ~7.4s
        make_build(),       # index 1 — 8 bars  ~14.8s
        make_drop1(),       # index 2 — 16 bars ~29.5s
        make_breakdown(),   # index 3 — 4 bars  ~7.4s
        make_rebuild(),     # index 4 — 4 bars  ~7.4s
        make_drop2(),       # index 5 — 8 bars  ~14.8s
    ]
    # Sequence: list of pattern indices (not names)
    sequence = [0, 1, 2, 3, 4, 5]   # ~81 seconds total

    panning = {
        0: 0.00,   # kick: dead center
        1: 0.00,   # snare: dead center
        2: 0.22,   # hi-hat: slightly right (standard drum mix convention)
        3: -0.10,  # sub bass: just left of center (warmth)
        4: 0.35,   # arpeggio: right channel (spatial width)
        5: -0.08,  # lead melody: slight left (sits in front, perceived louder)
        6: 0.42,   # counter melody: right (harmonic depth, wide)
    }
    channel_effects = {
        4: {'delay': 0.115, 'delay_feedback': 0.28, 'delay_mix': 0.22,
            'reverb': 0.4, 'reverb_mix': 0.15},   # arpeggio: tempo-synced 1/8 delay
        5: {'delay': 0.092, 'delay_feedback': 0.22, 'delay_mix': 0.18,
            'reverb': 0.5, 'reverb_mix': 0.18},   # lead: subtle tape echo
        6: {'reverb': 0.7, 'reverb_mix': 0.38},   # counter: lush reverb pad
    }

    return Song(
        title='Cascade Protocol',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=sequence,
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.06,  # subtle room on master bus
        master_delay=0.0,     # no master delay (channels handle their own)
    )

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════╗")
    print("║          CASCADE PROTOCOL                        ║")
    print("║  Key: F# minor  |  BPM: 130  |  ~81 seconds     ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("Influences: Deadmau5 Strobe · Daft Punk ATWRL")
    print("            Raver's Fantasy · Tiësto Adagio for Strings")
    print()
    print("Structure:")
    print("  [0-7s]   Intro      — sub + hats, raw tension")
    print("  [7-22s]  Build      — arpeggios enter, kick half-time")
    print("  [22-51s] Drop 1     — THE EUPHORIA. Full kit + melody")
    print("  [51-58s] Breakdown  — stripped bare, counter melody aches")
    print("  [58-65s] Rebuild    — energy returns, snare withheld")
    print("  [65-81s] Drop 2     — everything, F#5 peak every 2 bars")
    print()
    print("Rendering...", flush=True)

    song = build_song()

    # Estimated duration before render
    total_bars = 4 + 8 + 16 + 4 + 4 + 8
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

    out = Path('output/cascade_protocol.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Rendered:  {duration:.1f}s")
    print(f"  Size:      {size_mb:.1f} MB")
    print(f"  File:      {out}")
    print()
    print("Done. Open the WAV and let it RAAAAVE.")
