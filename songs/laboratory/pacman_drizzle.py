"""
Pac-Man Drizzle — West Coast G-funk meets arcade chip poetry
=============================================================

Inspired by:
  - Pac-Man (Namco, 1980)      — the wakka arp, chromatic runs, dot-eating joy
  - Snoop Dogg / Dr. Dre       — G-funk bass glide, half-time drag, west coast soul
  - Zapp & Roger Troutman      — talk-box filter bass, chromatic synth swagger
  - Music theory (Mozart tier) — chromatic passing tones, voice leading, G min modal mixture

Key: G minor (natural Aeolian)
BPM: 92  — the Snoop drag (slow enough to feel)
Scale: G  A  Bb  C  D  Eb  F  (with chromatic ornaments: Ab, A natural as blues note)

7 channels:
  0 - Kick   (syncopated G-funk pattern — not four-on-floor, it swings)
  1 - Snare  (backbeat 2 & 4, snares drag behind the beat via velocity)
  2 - Hi-hat (16th stream, velocity swing — heavy on the 1 and 3 downbeats)
  3 - Bass   (bass_growl — G-funk sawtooth filter glide, chromatic walk)
  4 - Wakka  (pulse_arp — the Pac-Man dot-eating arpeggio machine)
  5 - Lead   (lead_bright — the melodic hook, chromatic passing tones)
  6 - Ghost  (pluck_short → pad_lush in finale — the uncanny counter voice)

Structure (~62 seconds at 92 BPM):
  [0–10s]   INTRO    4 bars  — G-funk groove only. Bass leads. No melody.
  [10–31s]  WAKKA    8 bars  — Pac-Man chip arp enters. Dot-eating runs.
  [31–52s]  DROP     8 bars  — Lead melody drops. Ghost counter. Full groove.
  [52–62s]  FINALE   4 bars  — Power pellet moment. G5 peak. Resolution.

The "drizzle" technique (Snoop DNA):
  - Chromatic bass walk: G2→Ab2→Bb2 (glide simulation through fast steps)
  - Ab4 passing tone in the melody (not in Gm scale — the "computer glitch" ornament)
  - Half-time kick pattern: syncopation over the barline (Dre signature)
  - Wakka rests on steps 14-15 (the "mouth closing" silence creates rhythm)

Mozart would hear: chromatic voice leading, proper contrary motion, subdominant V7
Snoop would hear: the drizzle, the bounce, the G
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 92
SPB = 4        # steps per beat (16th-note grid)
BAR = 16       # steps per bar (4/4 time, 4 beats × 4)

# ── Frequency helpers ─────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    """MIDI note number → Hz (A4 = 440)."""
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    """Hz → nearest integer MIDI note number."""
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

# ── Complete note pool ────────────────────────────────────────────────────────
# Sub-bass register (MIDI 29–34)
F1  = hz(29);  G1  = hz(31);  Ab1 = hz(32);  Bb1 = hz(34)

# Bass register (MIDI 36–46)
C2  = hz(36);  D2  = hz(38);  Eb2 = hz(39);  F2  = hz(41)
G2  = hz(43);  Ab2 = hz(44);  A2  = hz(45);  Bb2 = hz(46)

# Low-mid register (MIDI 48–58)
C3  = hz(48);  D3  = hz(50);  Eb3 = hz(51);  F3  = hz(53)
G3  = hz(55);  Ab3 = hz(56);  A3  = hz(57);  Bb3 = hz(58)

# Mid register (MIDI 60–70)
C4  = hz(60);  D4  = hz(62);  Eb4 = hz(63);  F4  = hz(65)
G4  = hz(67);  Ab4 = hz(68);  A4  = hz(69);  Bb4 = hz(70)

# Upper register (MIDI 72–82)
C5  = hz(72);  D5  = hz(74);  Eb5 = hz(75);  F5  = hz(77)
G5  = hz(79);  A5  = hz(81);  Bb5 = hz(82)

# ── Instrument keys ───────────────────────────────────────────────────────────
KICK  = 'kick_deep'
SNARE = 'snare_tight'
HAT   = 'hat_crisp'
HATO  = 'hat_open_shimmer'
BASS  = 'bass_growl'        # sawtooth 800Hz filter — G-funk swagger
WAKKA = 'pulse_arp'         # square 25% staccato — the arcade chip mouth
LEAD  = 'lead_bright'       # sawtooth 5000Hz — searing G-funk synth lead
GHOST = 'pluck_short'       # short decay — ghost counter punctuation
PAD   = 'pad_lush'          # evolving pad — finale power pellet moment

# ── Helper constructors ───────────────────────────────────────────────────────

def note(inst: str, freq: float, vel: float = 0.80, dur: int = 1) -> NoteEvent:
    """Create a NoteEvent from Hz frequency (auto-converts to MIDI)."""
    midi = freq_to_midi(freq) if freq > 0 else 0
    return NoteEvent(midi_note=midi, velocity=vel, duration_steps=dur, instrument=inst)

def kick(vel: float = 0.90) -> NoteEvent:   return note(KICK,  hz(36), vel, 1)
def snare(vel: float = 0.82) -> NoteEvent:  return note(SNARE, hz(40), vel, 1)
def hat(vel: float = 0.55) -> NoteEvent:    return note(HAT,   hz(42), vel, 1)
def hat_o(vel: float = 0.62) -> NoteEvent:  return note(HATO,  hz(46), vel, 1)

def new_grid(channels: int, steps: int) -> list:
    return [[None] * steps for _ in range(channels)]

# ── G-funk bass templates (relative step positions within one bar) ─────────────
# 4 templates cycle through: Gm → Gm/F → Fadd9 → Cm (the classic i→♭VII→♭VI→iv G-funk walk)
# The chromatic approach notes (Ab2, Eb2) are the "glide" simulation 

BASS_TEMPLATES = [
    # Bar type 0 — Gm home: G2 glide up → Bb2 → G walking down
    [(G2,  0, 3), (Ab2, 3, 1), (Bb2, 4, 2),
     (G2,  6, 2), (D2,  8, 3), (C2,  11, 2), (G1, 13, 3)],

    # Bar type 1 — Gm/F: G2 → Bb2 → F2 (the ♭VII move — Snoop cadence)
    [(G2,  0, 2), (Bb2, 2, 3), (F2,  5, 4),
     (G2,  9, 3), (Eb2, 12, 3), (G1, 15, 1)],

    # Bar type 2 — F major (♭VII): F2 → A2 → C3 (the brightness before home)
    [(F2,  0, 3), (A2,  3, 2), (C3,  5, 3),
     (F2,  8, 2), (C2,  10, 3), (Bb1, 13, 3)],

    # Bar type 3 — Cm (iv): C2 → Eb2 → G2 → F1 (the tension before resolution)
    [(C2,  0, 3), (Eb2, 3, 2), (G2,  5, 3),
     (C2,  8, 2), (G1,  10, 3), (F1, 13, 3)],
]

def place_bass(g: list, bar: int, steps: int, vel_boost: float = 0.0) -> None:
    """Place one bar of bass using the 4-template cycle."""
    bs = bar * BAR
    template = BASS_TEMPLATES[bar % 4]
    for (freq, rel_step, dur) in template:
        s = bs + rel_step
        if s < steps:
            g[3][s] = note(BASS, freq, min(0.74 + vel_boost, 0.92),
                           min(dur, steps - s))

def place_gfunk_drums(g: list, bar: int, add_roll: bool = False) -> None:
    """G-funk kick/snare/hat for one bar. The Snoop syncopation pattern."""
    bs = bar * BAR

    # Kick: NOT four-on-floor — syncopated, that's the Dre/Snoop DNA
    g[0][bs]      = kick(0.90)      # beat 1 (the anchor)
    g[0][bs + 5]  = kick(0.46)      # & of 2 (ghost anticipation)
    g[0][bs + 6]  = kick(0.58)      # and-a of 2 (the drag pair)
    g[0][bs + 8]  = kick(0.88)      # beat 3
    g[0][bs + 11] = kick(0.48)      # e of 4 (subtle syncopation)

    # Snare: backbeats 2 and 4 with slight velocity drag (human feel)
    g[1][bs + 4]  = snare(0.84)     # beat 2
    g[1][bs + 12] = snare(0.80)     # beat 4

    # Snare roll on bar marker (every 4th bar)
    if add_roll:
        g[1][bs + 13] = snare(0.48)
        g[1][bs + 14] = snare(0.60)
        g[1][bs + 15] = snare(0.72)

    # Hi-hat: 16th stream, velocity swing simulates dotted feel
    # Heavy on beat 1/3, medium on 2/4, softer 16ths = perceived swing
    for s in range(BAR):
        step = bs + s
        if s % 8 == 6:              # open hat: & of 2 and & of 4
            g[2][step] = hat_o(0.52)
        elif s % 4 == 0:            # downbeats: strong
            g[2][step] = hat(0.62)
        elif s % 2 == 0:            # 8th upbeats: medium
            g[2][step] = hat(0.44)
        else:                        # 16th fills: soft
            g[2][step] = hat(0.26)

# ── Wakka arpeggio sequences (by harmonic area) ───────────────────────────────
# The Pac-Man "dot-eating" machine: ascend 6 notes (mouth opening), hold 2
# (dot consumed!), descend 6 (mouth closing), rest 2 (moving to next dot)
# Descents use chromatic passing tones for that "computer glitch" shimmer

WAKKA_SEQS = {
    0: {'up': [G3,  Bb3, C4,  D4,  F4,  G4 ], 'down': [F4,  Eb4, D4,  C4,  Bb3, Ab3]},  # Gm
    1: {'up': [G3,  Bb3, D4,  F4,  G4,  Bb4], 'down': [Bb4, G4,  F4,  D4,  Bb3, G3 ]},  # Gm hi
    2: {'up': [F3,  A3,  C4,  F4,  A4,  C5 ], 'down': [Bb4, A4,  G4,  F4,  Eb4, D4 ]},  # F major
    3: {'up': [C3,  Eb3, G3,  Bb3, C4,  Eb4], 'down': [Eb4, C4,  Bb3, G3,  Eb3, C3 ]},  # Cm
}

def place_wakka(g: list, bar: int, vel_base: float = 0.55) -> None:
    """Place one bar of Pac-Man arpeggio (wakka wakka pattern)."""
    bs = bar * BAR
    seq = WAKKA_SEQS[bar % 4]

    # Steps 0–5: ascending 16ths — mouth OPENING (dot in sight)
    for i, freq in enumerate(seq['up']):
        vel = vel_base + i * 0.025  # each note louder as mouth opens
        g[4][bs + i] = note(WAKKA, freq, min(vel, 0.88), 1)

    # Steps 6–7: hold peak — DOT CONSUMED (the satisfying "wakka!")
    g[4][bs + 6] = note(WAKKA, seq['up'][-1], min(vel_base + 0.25, 0.90), 1)
    g[4][bs + 7] = note(WAKKA, seq['up'][-1], min(vel_base + 0.18, 0.82), 1)

    # Steps 8–13: descend with chromatic ornament — mouth CLOSING (computer shimmer)
    for i, freq in enumerate(seq['down']):
        vel = (vel_base + 0.22) - i * 0.040
        g[4][bs + 8 + i] = note(WAKKA, freq, max(vel, 0.28), 1)

    # Steps 14–15: silence — the Pac-Man mouth "closed" pause
    # (no notes — the rhythm INFO lives in this rest)


# ── PATTERN: INTRO ────────────────────────────────────────────────────────────

def make_intro() -> Pattern:
    """4 bars: G-funk groove only. Bass and drums establish the swagger.
    The listener waits for the Wakka — tension is built through absence."""
    steps = BAR * 4
    g = new_grid(7, steps)

    for bar in range(4):
        place_gfunk_drums(g, bar)
        place_bass(g, bar, steps)

    return Pattern(name='intro', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── PATTERN: WAKKA ────────────────────────────────────────────────────────────

def make_wakka() -> Pattern:
    """8 bars: The Pac-Man arpeggio enters. Chromatic descents shimmer.
    Ghost notes appear on off-bars (faint pluck twinkle — heard subliminally).
    Bass follows the 4-bar harmonic cycle × 2."""
    steps = BAR * 8
    g = new_grid(7, steps)

    for bar in range(8):
        place_gfunk_drums(g, bar, add_roll=(bar % 4 == 3))
        place_bass(g, bar, steps, vel_boost=(bar / 16))
        vel = 0.52 + (bar / 8) * 0.22     # swell from 0.52 → 0.74
        place_wakka(g, bar, vel_base=vel)

        # Ghost notes: faint chromatic twinkle on odd bars (step 14-15)
        # Very low velocity — subliminal "there's a ghost nearby" effect
        if bar % 2 == 1:
            ghost_freqs = [D5, C5]
            for i, freq in enumerate(ghost_freqs):
                g[6][bar * BAR + 14 + i] = note(GHOST, freq, 0.24 + i * (-0.04), 1)

    return Pattern(name='wakka', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── PATTERN: DROP ─────────────────────────────────────────────────────────────

def make_drop() -> Pattern:
    """8 bars: THE DRIZZLE DROPS. Lead melody enters.
    
    The hook (2-bar phrase × 4 reps):
      Bar A: G4(Q)__  Bb4 A4 Ab4 (chrom approach)  D5(Q.)  F5(E) Eb5 D5
      Bar B: C5(E) Bb4 A4(chrom)  G4(Q)__  F4  G4(Q.)  A4  Bb4
    
    The Ab4 chromatic passing tone (NOT in G minor scale) is the melodic
    'computer glitch' — unexpected, beautiful, mathematically deliberate.
    It descends G4→Ab4 by half step, creating a tritone touch (the devil's
    interval — perfect for Pac-Man's spooky arcade DNA).
    
    Ghost counter-melody: slow chromatic descent G5→Ab4 (one octave) across
    the full drop — heard as a breathy pad layer behind the lead."""
    steps = BAR * 8
    g = new_grid(7, steps)

    # ── Lead melody: 4 repetitions of the 2-bar hook ─────────────────────────
    for rep in range(4):
        ba = rep * 2 * BAR       # bar A start
        bb = ba + BAR            # bar B start
        vb = rep * 0.014         # velocity lift per rep

        # ── BAR A: G4 → chromatic run → D5 peak ──────────────────────────────
        g[5][ba]      = note(LEAD, G4,  min(0.88 + vb, 1.0), 4)   # G4 quarter
        # chromatic approach to D5: Bb4 → A4 → Ab4 (three 16ths — the "glitch triplet")
        g[5][ba + 5]  = note(LEAD, Bb4, min(0.76 + vb, 1.0), 1)   # Bb4
        g[5][ba + 6]  = note(LEAD, A4,  min(0.72 + vb, 1.0), 1)   # A4 (blues note)
        g[5][ba + 7]  = note(LEAD, Ab4, min(0.68 + vb, 1.0), 1)   # Ab4 (the trick ♭2)
        g[5][ba + 8]  = note(LEAD, D5,  min(0.92 + vb, 1.0), 3)   # D5 dotted quarter
        g[5][ba + 11] = note(LEAD, F5,  min(0.82 + vb, 1.0), 2)   # F5 eighth
        g[5][ba + 13] = note(LEAD, Eb5, min(0.78 + vb, 1.0), 1)   # Eb5 16th (minor 6th)
        g[5][ba + 14] = note(LEAD, D5,  min(0.85 + vb, 1.0), 2)   # D5 resolve

        # ── BAR B: C5 → Bb4 → G4 → climbing to Bb4 (the Snoop drizzle tail) ──
        g[5][bb]      = note(LEAD, C5,  min(0.84 + vb, 1.0), 2)   # C5 eighth
        g[5][bb + 2]  = note(LEAD, Bb4, min(0.80 + vb, 1.0), 1)   # Bb4 16th
        g[5][bb + 3]  = note(LEAD, A4,  min(0.72 + vb, 1.0), 1)   # A4 chromatic pass
        g[5][bb + 4]  = note(LEAD, G4,  min(0.84 + vb, 1.0), 4)   # G4 quarter (home)
        g[5][bb + 8]  = note(LEAD, F4,  min(0.78 + vb, 1.0), 2)   # F4 eighth (♭7)
        g[5][bb + 10] = note(LEAD, G4,  min(0.80 + vb, 1.0), 3)   # G4 dotted q
        g[5][bb + 13] = note(LEAD, A4,  min(0.74 + vb, 1.0), 1)   # A4 pickup
        g[5][bb + 14] = note(LEAD, Bb4, min(0.84 + vb, 1.0), 2)   # Bb4 anticipation

        # ── Ghost counter-melody (chromatic descending, above the lead) ───────
        # Placed on bar A: slow whole/half note values — very different rhythm from lead
        # This creates the "two voices in conversation" (Mozart: Alberti bass style)
        ghost_bar_a = [
            (G5,  ba + 0,  3, 0.36),   # G5 — an octave + P5 above G4
            (F5,  ba + 4,  3, 0.32),   # F5 — ♭7 color, gentle
            (Eb5, ba + 8,  2, 0.29),   # Eb5 — ♭6, the melancholy note
            (D5,  ba + 10, 2, 0.27),   # D5 — P5, brief consonance
        ]
        ghost_bar_b = [
            (C5,  bb + 0,  3, 0.33),   # C5 — P4, IV chord color
            (Bb4, bb + 4,  3, 0.30),   # Bb4 — unison with melody (shadow)
            (A4,  bb + 8,  2, 0.26),   # A4 — chromatic passing (ghost blues note)
            (Ab4, bb + 11, 2, 0.22),   # Ab4 — the GHOST note — barely audible (spooky)
        ]
        for (freq, step, dur, vel) in ghost_bar_a + ghost_bar_b:
            if step < steps:
                g[6][step] = note(GHOST, freq, vel, dur)

    # ── Wakka arp continues under the melody ──────────────────────────────────
    for bar in range(8):
        place_wakka(g, bar, vel_base=0.38)   # quieter under the lead

    # ── Full G-funk drums + bass ───────────────────────────────────────────────
    for bar in range(8):
        place_gfunk_drums(g, bar, add_roll=(bar % 4 == 3))
        place_bass(g, bar, steps, vel_boost=0.06)

    return Pattern(name='drop', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── PATTERN: FINALE ───────────────────────────────────────────────────────────

def make_finale() -> Pattern:
    """4 bars: THE POWER PELLET. G5 peak on bar 3. Resolution.
    Ghost voice transforms from pluck to lush pad — the ghost is EATEN.
    Bass walks up a full octave (G2→Bb2→D3→G3) on bar 3 = triumph arch.
    Final bar: long G4 root note — the maze is clear."""
    steps = BAR * 4
    g = new_grid(7, steps)

    # ── Lead melody: hook × 2 + power pellet reach ───────────────────────────
    # Bar 0: Hook bar A (full velocity, the confidence)
    g[5][0]   = note(LEAD, G4,  0.95, 4)
    g[5][5]   = note(LEAD, Bb4, 0.86, 1)
    g[5][6]   = note(LEAD, A4,  0.82, 1)
    g[5][7]   = note(LEAD, Ab4, 0.78, 1)
    g[5][8]   = note(LEAD, D5,  0.95, 3)
    g[5][11]  = note(LEAD, F5,  0.90, 2)
    g[5][13]  = note(LEAD, Eb5, 0.86, 1)
    g[5][14]  = note(LEAD, D5,  0.92, 2)

    # Bar 1: Hook bar B
    g[5][16]  = note(LEAD, C5,  0.92, 2)
    g[5][18]  = note(LEAD, Bb4, 0.88, 1)
    g[5][19]  = note(LEAD, A4,  0.80, 1)
    g[5][20]  = note(LEAD, G4,  0.90, 4)
    g[5][24]  = note(LEAD, F4,  0.86, 2)
    g[5][26]  = note(LEAD, G4,  0.88, 3)
    g[5][29]  = note(LEAD, A4,  0.82, 1)
    g[5][30]  = note(LEAD, Bb4, 0.90, 2)

    # Bar 2: THE POWER PELLET ASCENT — chromatic climb to G5
    # D5→Eb5→F5→G5 = IV→♭V→♭VI→♭VII→i (chromatic arrival at octave peak)
    g[5][32]  = note(LEAD, D5,  0.92, 2)
    g[5][34]  = note(LEAD, Eb5, 0.88, 1)
    g[5][35]  = note(LEAD, F5,  0.90, 1)
    g[5][36]  = note(LEAD, F5,  0.92, 2)
    g[5][38]  = note(LEAD, G5,  1.00, 4)   # G5 — THE POWER PELLET. Maximum velocity.
    g[5][42]  = note(LEAD, F5,  0.90, 2)   # descent begins
    g[5][44]  = note(LEAD, Eb5, 0.86, 2)
    g[5][46]  = note(LEAD, D5,  0.88, 2)

    # Bar 3: Resolution — descend home, long final tone
    g[5][48]  = note(LEAD, C5,  0.86, 2)
    g[5][50]  = note(LEAD, Bb4, 0.84, 1)
    g[5][51]  = note(LEAD, A4,  0.80, 1)
    g[5][52]  = note(LEAD, G4,  0.95, 8)   # G4 long — HOME. The maze is clear.

    # ── Ghost transforms to pad_lush (ghost is eaten!) ────────────────────────
    # Wide intervals, slow moving, lush reverb = triumphant ghost chord
    pad_finale = [
        (Bb5, 8,  3, 0.40),    # Bb5 — high and luminous
        (A5,  11, 2, 0.36),    # A5 — chromatic approach down
        (G5,  13, 2, 0.34),
        (F5,  16, 3, 0.38),
        (Eb5, 20, 4, 0.34),
        (D5,  32, 4, 0.42),    # chord tone with the power pellet climb
        (G5,  38, 4, 0.54),    # harmonizes with G5 peak (unison → octave displacement)
        (F5,  42, 2, 0.40),
        (Eb5, 44, 2, 0.38),
        (D5,  46, 2, 0.36),
        (C5,  48, 4, 0.40),
        (Bb4, 52, 8, 0.36),    # Bb4 long — the Bb chord settles above the G4 root
    ]
    for (freq, step, dur, vel) in pad_finale:
        if step < steps:
            g[6][step] = note(PAD, freq, vel, min(dur, steps - step))

    # ── Wakka: final 4 bars at full velocity ─────────────────────────────────
    for bar in range(4):
        place_wakka(g, bar, vel_base=0.68)

    # ── Drums: tightest, most syncopated version ──────────────────────────────
    for bar in range(4):
        bs = bar * BAR
        g[0][bs]      = kick(0.95)
        g[0][bs + 3]  = kick(0.46)      # tight ghost before & of 1
        g[0][bs + 5]  = kick(0.50)
        g[0][bs + 6]  = kick(0.62)
        g[0][bs + 8]  = kick(0.93)
        g[0][bs + 11] = kick(0.52)
        g[0][bs + 14] = kick(0.48)

        g[1][bs + 4]  = snare(0.92)
        g[1][bs + 12] = snare(0.90)
        if bar == 3:                     # final bar: closing snare roll
            g[1][bs + 13] = snare(0.55)
            g[1][bs + 14] = snare(0.68)
            g[1][bs + 15] = snare(0.82)

        for s in range(BAR):
            step = bs + s
            if s % 8 == 6:
                g[2][step] = hat_o(0.60)
            elif s % 4 == 0:
                g[2][step] = hat(0.70)
            elif s % 2 == 0:
                g[2][step] = hat(0.50)
            else:
                g[2][step] = hat(0.30)

    # ── Bass: triumphant octave walk on bar 2, resolution on bar 3 ───────────
    finale_bass = [
        # Bar 0: standard Gm template
        [(G2, 0, 3), (Ab2, 3, 1), (Bb2, 4, 2), (G2, 6, 2),
         (D2, 8, 3), (C2, 11, 2), (G1, 13, 3)],
        # Bar 1: Gm/F
        [(G2, 0, 2), (Bb2, 2, 3), (F2, 5, 4),
         (G2, 9, 3), (Eb2, 12, 3), (G1, 15, 1)],
        # Bar 2: POWER PELLET BASS — ascending triumphal octave walk!
        # G2 → Bb2 → D3 → G3 (root → ♭3 → P5 → octave = the Gm triad unfolded)
        [(G2, 0, 4), (Bb2, 4, 4), (D3, 8, 4), (G3, 12, 4)],
        # Bar 3: Final long tones — resolution
        [(G2, 0, 8), (G1, 8, 8)],
    ]
    for bar, bdata in enumerate(finale_bass):
        bs = bar * BAR
        for (freq, rel_step, dur) in bdata:
            s = bs + rel_step
            if s < steps:
                g[3][s] = note(BASS, freq, 0.84, min(dur, steps - s))

    return Pattern(name='finale', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

# ── ASSEMBLE SONG ─────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_intro(),     # index 0 — 4 bars  ~10.4s
        make_wakka(),     # index 1 — 8 bars  ~20.9s
        make_drop(),      # index 2 — 8 bars  ~20.9s
        make_finale(),    # index 3 — 4 bars  ~10.4s
    ]
    # Total: 24 bars = ~62.6 seconds

    panning = {
        0:  0.00,    # kick: dead center (anchors the mix)
        1:  0.00,    # snare: dead center
        2:  0.16,    # hat: slight right (standard mix placement)
        3: -0.14,    # bass: left (G-funk bass sits in the left pocket)
        4:  0.32,    # wakka: right (the arcade machine is to your right)
        5: -0.06,    # lead: slight left-center (sits in front of everything)
        6: -0.38,    # ghost: left (the ghost creeps in from the left)
    }

    channel_effects = {
        # Wakka: punchy tape echo — 1/8 note delay at 92 BPM = 0.1630s
        4: {'delay': 0.163, 'delay_feedback': 0.22, 'delay_mix': 0.14,
            'reverb': 0.25, 'reverb_mix': 0.08},

        # Lead melody: slapback echo (very short, single repeat)
        5: {'delay': 0.054, 'delay_feedback': 0.12, 'delay_mix': 0.12,
            'reverb': 0.35, 'reverb_mix': 0.12},

        # Ghost/pad: ambient — lots of reverb, ghost voice floats in space
        6: {'reverb': 0.80, 'reverb_mix': 0.55},
    }

    return Song(
        title='Pac-Man Drizzle',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2, 3],   # integer indices — not names
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.04,   # very light room on master bus
        master_delay=0.00,    # no master delay
    )

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════════╗")
    print("║          PAC-MAN DRIZZLE                         ║")
    print("║  Key: G minor  |  BPM: 92  |  ~62 seconds       ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("West Coast G-funk × arcade chip poetry.")
    print("Influenced by:")
    print("  Snoop Dogg · Dr. Dre · Zapp & Roger")
    print("  Pac-Man (Namco 1980) · W. A. Mozart")
    print()
    print("Structure:")
    print("  [0-10s]   Intro   — G-funk groove, bass drizzle, no melody")
    print("  [10-31s]  Wakka   — Pac-Man arp enters (chromatic dot-eating)")
    print("  [31-52s]  Drop    — Lead melody + ghost counter (the Ab4 glitch)")
    print("  [52-62s]  Finale  — Power pellet G5 peak, octave bass walk")
    print()
    print("Music theory moves:")
    print("  · Ab4 passing tone: chromatic ♭2 ornament (Mozart + glitch)")
    print("  · A4 natural in G minor: the blues note (Snoop DNA)")
    print("  · i→♭VII→♭VI→iv bass cycle: G-funk harmonic signature")
    print("  · Wakka chromatic descent: Ab3 passing tone = spooky shimmer")
    print()
    print("Rendering...", flush=True)

    song = build_song()
    total_bars = 4 + 8 + 8 + 4
    est_sec = (total_bars * 4) / (BPM / 60.0)
    print(f"  Estimated: {est_sec:.0f}s")

    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    out = Path('output/pacman_drizzle.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Rendered:  {duration:.1f}s")
    print(f"  Size:      {size_mb:.1f} MB")
    print(f"  File:      {out}")
    print()
    print("WAKA WAKA. Drizzle drop. Certified.")
