"""
ChipForge FILM SCORE for core_fable — orchestral electronic soundtrack.

This is a composed score, not a DJ loop. Each section uses different instruments,
melodic ideas, rhythms, and textures to match the story and visuals.

Approach: Film soundtrack — think Hans Zimmer meets Vangelis meets chiptune
  - 5 channels: lead melody, counter/texture, pad atmosphere, bass, accent
  - Instruments change per section to match mood
  - Real composed melodic phrases, not cycling arpeggios
  - Ending: the arp-to-sparse fadeout (the good part!)

Key: E natural minor (E F# G A B C D)
BPM: 126
Duration target: ~141s (covers 140s film)

Film arc:
  Act I   (0-35s):   Cosmic solitude — sparse, ethereal, lonely stars
  Act II  (35-70s):  Wonder & gifts — warmth builds, melody blooms
  Act III (70-100s): Labyrinth — rhythmic tension, groove, hope
  Act IV  (100-120s): Unraveling & defiance — dark, fragmented → triumphant
  Act V   (120-140s): The Return — warm resolution, arp thins to starlight

Run:
    .venv/bin/python3 core_fable_melody.py
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 126
SPB = 4
BAR = 16

# ── E natural minor MIDI notes ────────────────────────────────────────────────
E2, G2, A2, B2 = 40, 43, 45, 47
C3, D3, E3, Fs3, G3, A3, B3 = 48, 50, 52, 54, 55, 57, 59
C4, D4, E4, Fs4, G4, A4, B4 = 60, 62, 64, 66, 67, 69, 71
C5, D5, E5, G5, A5, B5 = 72, 74, 76, 79, 81, 83

# ── Instruments per emotional color ──────────────────────────────────────────
PAD      = "pad_lush"       # sustained warmth floor
WARM     = "saw_filtered"   # warm melodic lead — emotional sections
BRIGHT   = "lead_bright"    # bright lead — hopeful, triumphant, the ending arp
DARK     = "saw_dark"       # dark filtered — tension, loss, unraveling
CHIME    = "pulse_chime"    # bell-like accents — stars, wonder
ARP_TEX  = "pulse_warm"     # textural arpeggiation
DEEP     = "bass_growl"     # deep bass foundation
SUB      = "bass_sub"       # sub bass for gravity

CHANNELS = 5
# 0: Lead melody (changes instrument per section)
# 1: Counter / arp texture
# 2: Pad atmosphere
# 3: Bass
# 4: Accent / chime / texture

def note(inst: str, midi: int, vel: float = 0.70, dur: int = 2) -> NoteEvent:
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.80),
                     duration_steps=dur, instrument=inst)

def new_grid(steps: int) -> list[list]:
    return [[None] * steps for _ in range(CHANNELS)]

def pat(name: str, steps: int, g: list[list]) -> Pattern:
    return Pattern(name=name, bpm=BPM, steps_per_beat=SPB,
                   num_steps=steps, num_channels=CHANNELS, grid=g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT I: COSMIC SOLITUDE (0-35s) — boy alone under infinite stars
# Sparse, ethereal, lonely. Pad hums. Chimes twinkle like stars.
# Single melody notes drift in saw_filtered — aching, exposed.
# ══════════════════════════════════════════════════════════════════════════════

def p_starfield(steps=96):
    """Opening — void wakes. Pad fades in. Chimes appear like stars."""
    g = new_grid(steps)
    # Pad: E minor chord sustained — the cosmos breathing
    g[2][0]  = note(PAD, E3, vel=0.25, dur=16)
    g[2][16] = note(PAD, E3, vel=0.30, dur=16)
    g[2][32] = note(PAD, B3, vel=0.32, dur=16)
    g[2][48] = note(PAD, E3, vel=0.35, dur=16)
    g[2][64] = note(PAD, G3, vel=0.38, dur=16)
    g[2][80] = note(PAD, E3, vel=0.40, dur=16)
    # Accent: star chimes — isolated, pure, high
    g[4][8]  = note(CHIME, E5, vel=0.35, dur=2)
    g[4][24] = note(CHIME, B4, vel=0.30, dur=2)
    g[4][44] = note(CHIME, G4, vel=0.35, dur=2)
    g[4][60] = note(CHIME, D5, vel=0.32, dur=2)
    g[4][76] = note(CHIME, E5, vel=0.38, dur=2)
    g[4][88] = note(CHIME, A4, vel=0.30, dur=2)
    # Lead: first melody fragment — a question in the dark
    g[0][32] = note(WARM, E4, vel=0.40, dur=6)
    g[0][48] = note(WARM, G4, vel=0.45, dur=4)
    g[0][56] = note(WARM, A4, vel=0.45, dur=4)
    g[0][64] = note(WARM, B4, vel=0.48, dur=6)
    g[0][80] = note(WARM, A4, vel=0.42, dur=4)
    g[0][88] = note(WARM, E4, vel=0.38, dur=6)
    return pat("starfield", steps, g)


def p_cosmic_grief(steps=128):
    """Universe lets go — descending melody, aching. 'She let go.'
    Melody in saw_filtered descends. Pad shifts to minor chord.
    Counter-melody enters as ghostly echo."""
    g = new_grid(steps)
    # Lead: the descending grief melody — she let him go
    g[0][0]  = note(WARM, B4, vel=0.52, dur=4)
    g[0][6]  = note(WARM, A4, vel=0.52, dur=4)
    g[0][12] = note(WARM, G4, vel=0.50, dur=6)     # lingers
    g[0][24] = note(WARM, E4, vel=0.48, dur=4)
    g[0][30] = note(WARM, D4, vel=0.48, dur=4)
    g[0][36] = note(WARM, C4, vel=0.50, dur=8)     # minor 6 — grief
    # Second phrase: tries to rise, falls back
    g[0][52] = note(WARM, E4, vel=0.50, dur=3)
    g[0][56] = note(WARM, G4, vel=0.52, dur=3)
    g[0][60] = note(WARM, A4, vel=0.55, dur=4)     # reaching...
    g[0][68] = note(WARM, G4, vel=0.48, dur=4)     # falls
    g[0][76] = note(WARM, E4, vel=0.45, dur=6)     # settles
    # Third phrase: acceptance — sustained resolve
    g[0][92]  = note(WARM, E4, vel=0.50, dur=4)
    g[0][98]  = note(WARM, Fs3, vel=0.48, dur=4)   # Fs in the minor
    g[0][104] = note(WARM, G3, vel=0.45, dur=6)
    g[0][116] = note(WARM, E3, vel=0.40, dur=10)   # dissolves low
    # Counter: ghostly echo, delayed fragments
    g[1][8]  = note(ARP_TEX, E5, vel=0.28, dur=3)
    g[1][20] = note(ARP_TEX, B4, vel=0.25, dur=3)
    g[1][40] = note(ARP_TEX, G4, vel=0.28, dur=4)
    g[1][64] = note(ARP_TEX, A4, vel=0.25, dur=3)
    g[1][84] = note(ARP_TEX, E4, vel=0.22, dur=4)
    g[1][108] = note(ARP_TEX, B4, vel=0.20, dur=4)
    # Pad: shifts to sadder voicing
    g[2][0]  = note(PAD, E3, vel=0.40, dur=16)
    g[2][16] = note(PAD, C3, vel=0.38, dur=16)     # C natural — darker
    g[2][32] = note(PAD, A2, vel=0.35, dur=16)
    g[2][48] = note(PAD, E3, vel=0.38, dur=16)
    g[2][64] = note(PAD, C3, vel=0.35, dur=16)
    g[2][80] = note(PAD, G2, vel=0.32, dur=16)
    g[2][96] = note(PAD, A2, vel=0.30, dur=16)
    g[2][112] = note(PAD, E3, vel=0.28, dur=16)
    # Chimes: fewer, fading
    g[4][16] = note(CHIME, D5, vel=0.25, dur=2)
    g[4][48] = note(CHIME, B4, vel=0.22, dur=2)
    g[4][80] = note(CHIME, G4, vel=0.20, dur=2)
    return pat("cosmic_grief", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT II: WONDER & GIFTS (35-70s) — melody blooms, instruments layer in
# Warmth builds. Saw_filtered melody becomes flowing. Counter arpeggiates.
# Bass enters. Pad fullens. Chimes dance. This is the heart of the score.
# ══════════════════════════════════════════════════════════════════════════════

def p_search_begins(steps=80):
    """'So he searched.' — melody quickens, pulse enters, hope.
    Short energetic phrases. Counter starts rhythmic pattern. Bass drops in."""
    g = new_grid(steps)
    # Lead: ascending phrases — determination
    g[0][0]  = note(WARM, E4, vel=0.55, dur=2)
    g[0][3]  = note(WARM, G4, vel=0.55, dur=2)
    g[0][6]  = note(WARM, A4, vel=0.58, dur=3)
    g[0][10] = note(WARM, B4, vel=0.60, dur=4)
    g[0][18] = note(WARM, A4, vel=0.55, dur=2)
    g[0][21] = note(WARM, B4, vel=0.58, dur=2)
    g[0][24] = note(WARM, D5, vel=0.62, dur=4)     # higher! searching
    # Second phrase — more confident
    g[0][32] = note(WARM, E4, vel=0.58, dur=2)
    g[0][35] = note(WARM, B4, vel=0.60, dur=2)
    g[0][38] = note(WARM, D5, vel=0.62, dur=3)
    g[0][42] = note(WARM, E5, vel=0.65, dur=4)     # soaring
    g[0][50] = note(WARM, D5, vel=0.60, dur=3)
    g[0][54] = note(WARM, B4, vel=0.58, dur=3)
    g[0][58] = note(WARM, A4, vel=0.55, dur=4)
    # Resolve
    g[0][66] = note(WARM, G4, vel=0.55, dur=3)
    g[0][70] = note(WARM, E4, vel=0.52, dur=4)
    # Counter: rhythmic arpeggio starts — energy underneath
    arp_notes = [E4, G4, B4, E4, A4, G4, E4, B4]
    for i, m in enumerate(arp_notes):
        g[1][i * 8] = note(ARP_TEX, m, vel=0.38, dur=2)
    # Pad continues, brightening
    g[2][0]  = note(PAD, E3, vel=0.35, dur=16)
    g[2][16] = note(PAD, G3, vel=0.38, dur=16)
    g[2][32] = note(PAD, A3, vel=0.40, dur=16)
    g[2][48] = note(PAD, E3, vel=0.38, dur=16)
    g[2][64] = note(PAD, G3, vel=0.38, dur=16)
    # Bass enters — gentle foundation
    g[3][0]  = note(DEEP, E2, vel=0.35, dur=4)
    g[3][16] = note(DEEP, E2, vel=0.35, dur=4)
    g[3][32] = note(DEEP, G2, vel=0.38, dur=4)
    g[3][48] = note(DEEP, A2, vel=0.38, dur=4)
    g[3][64] = note(DEEP, E2, vel=0.35, dur=4)
    return pat("search_begins", steps, g)


def p_four_gifts(steps=176):
    """The Four Gifts — melody at its most beautiful and varied.
    Each gift gets its own melodic phrase and texture.
    Lantern → Mirror → Hammer → Chain of stars."""
    g = new_grid(steps)

    # ── Lantern (0-44): ascending wonder, chimes sparkle ──
    g[0][0]  = note(WARM, E4, vel=0.58, dur=2)
    g[0][3]  = note(WARM, G4, vel=0.60, dur=2)
    g[0][6]  = note(WARM, B4, vel=0.62, dur=3)
    g[0][10] = note(WARM, D5, vel=0.65, dur=3)
    g[0][14] = note(WARM, E5, vel=0.68, dur=6)     # lantern lights up
    g[0][24] = note(WARM, D5, vel=0.62, dur=3)
    g[0][28] = note(WARM, B4, vel=0.60, dur=3)
    g[0][32] = note(WARM, A4, vel=0.58, dur=4)
    g[0][38] = note(WARM, G4, vel=0.55, dur=4)

    g[4][2]  = note(CHIME, E5, vel=0.40, dur=1)    # sparkles
    g[4][8]  = note(CHIME, B5, vel=0.35, dur=1)
    g[4][16] = note(CHIME, G5, vel=0.38, dur=1)
    g[4][26] = note(CHIME, D5, vel=0.35, dur=1)

    # ── Mirror (44-88): reflective, oscillating melody ──
    g[0][44] = note(WARM, A4, vel=0.58, dur=3)
    g[0][48] = note(WARM, B4, vel=0.60, dur=3)
    g[0][52] = note(WARM, A4, vel=0.55, dur=3)
    g[0][56] = note(WARM, G4, vel=0.55, dur=3)
    g[0][60] = note(WARM, A4, vel=0.58, dur=4)     # back and forth
    g[0][66] = note(WARM, B4, vel=0.60, dur=3)
    g[0][70] = note(WARM, D5, vel=0.62, dur=4)
    g[0][76] = note(WARM, B4, vel=0.58, dur=3)
    g[0][80] = note(WARM, A4, vel=0.55, dur=4)

    # Counter: mirror reflection — plays inverted fragments
    g[1][48] = note(ARP_TEX, D5, vel=0.35, dur=3)
    g[1][56] = note(ARP_TEX, E5, vel=0.35, dur=3)
    g[1][64] = note(ARP_TEX, D5, vel=0.32, dur=3)
    g[1][72] = note(ARP_TEX, B4, vel=0.32, dur=3)

    # ── Hammer (88-132): rhythmic, percussive melody — building ──
    g[0][88]  = note(BRIGHT, E4, vel=0.62, dur=2)  # switch to bright!
    g[0][91]  = note(BRIGHT, G4, vel=0.62, dur=2)
    g[0][94]  = note(BRIGHT, A4, vel=0.65, dur=2)
    g[0][97]  = note(BRIGHT, B4, vel=0.65, dur=2)
    g[0][100] = note(BRIGHT, D5, vel=0.68, dur=3)  # hammering upward
    g[0][104] = note(BRIGHT, E5, vel=0.70, dur=4)  # strike!
    g[0][112] = note(BRIGHT, D5, vel=0.65, dur=2)
    g[0][115] = note(BRIGHT, B4, vel=0.62, dur=2)
    g[0][118] = note(BRIGHT, A4, vel=0.62, dur=2)
    g[0][121] = note(BRIGHT, G4, vel=0.60, dur=2)
    g[0][124] = note(BRIGHT, E4, vel=0.58, dur=3)

    # Counter: rhythmic pulse underneath hammer — driving energy
    for i in range(88, 132, 4):
        m = [E3, G3, A3, B3][((i - 88) // 4) % 4]
        g[1][i] = note(ARP_TEX, m, vel=0.40, dur=2)

    # ── Chain of stars (132-176): warm, heavy, love's weight ──
    g[0][132] = note(WARM, E4, vel=0.58, dur=6)    # back to warm
    g[0][140] = note(WARM, G4, vel=0.55, dur=6)
    g[0][148] = note(WARM, A4, vel=0.52, dur=4)
    g[0][154] = note(WARM, B4, vel=0.55, dur=8)    # long sustain — weight
    g[0][164] = note(WARM, A4, vel=0.50, dur=4)
    g[0][170] = note(WARM, E4, vel=0.48, dur=6)    # resolves

    # Pad: warm throughout, shifting chords
    for i in range(0, steps, 16):
        chord = [E3, G3, A3, B3, E3, G3, A3, E3, B3, G3, E3][min(i // 16, 10)]
        g[2][i] = note(PAD, chord, vel=0.40, dur=16)

    # Bass: steady foundation
    for i in range(0, steps, 16):
        bass = [E2, E2, G2, A2, E2, G2, A2, E2, B2, G2, E2][min(i // 16, 10)]
        g[3][i] = note(DEEP, bass, vel=0.40, dur=4)

    # Chimes scattered through — wonder moments
    g[4][48] = note(CHIME, A5, vel=0.32, dur=1)
    g[4][76] = note(CHIME, E5, vel=0.30, dur=1)
    g[4][108] = note(CHIME, B5, vel=0.35, dur=1)
    g[4][140] = note(CHIME, G4, vel=0.28, dur=2)
    return pat("four_gifts", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT III: THE LABYRINTH (70-100s) — rhythmic, tense, groovy, then hope
# Different feel entirely — pulse_warm drives, melody gets syncopated.
# Bass gets groovy. Pad drops. Tension and release.
# ══════════════════════════════════════════════════════════════════════════════

def p_labyrinth(steps=128):
    """Labyrinth groove — rhythmic, syncopated, tension.
    Lead switches to saw_dark for the maze feel.
    Counter becomes a driving arpeggio. Bass gets syncopated."""
    g = new_grid(steps)
    # Lead: dark syncopated maze melody — disorientation
    g[0][0]  = note(DARK, E4, vel=0.58, dur=2)
    g[0][3]  = note(DARK, G4, vel=0.58, dur=2)
    g[0][7]  = note(DARK, E4, vel=0.55, dur=2)     # syncopated!
    g[0][10] = note(DARK, B4, vel=0.60, dur=3)
    g[0][16] = note(DARK, A4, vel=0.58, dur=2)
    g[0][19] = note(DARK, G4, vel=0.55, dur=2)
    g[0][23] = note(DARK, A4, vel=0.58, dur=2)
    g[0][26] = note(DARK, B4, vel=0.60, dur=4)
    # Second phrase — variation, more urgent
    g[0][32] = note(DARK, D5, vel=0.62, dur=2)
    g[0][35] = note(DARK, B4, vel=0.58, dur=2)
    g[0][39] = note(DARK, A4, vel=0.55, dur=2)
    g[0][42] = note(DARK, G4, vel=0.55, dur=3)
    g[0][48] = note(DARK, E4, vel=0.58, dur=2)
    g[0][51] = note(DARK, G4, vel=0.58, dur=2)
    g[0][55] = note(DARK, B4, vel=0.60, dur=2)
    g[0][58] = note(DARK, E5, vel=0.65, dur=4)     # finding a path?
    # Third phrase — lost again, descending
    g[0][64] = note(DARK, E5, vel=0.60, dur=2)
    g[0][67] = note(DARK, D5, vel=0.58, dur=2)
    g[0][71] = note(DARK, B4, vel=0.55, dur=2)
    g[0][76] = note(DARK, A4, vel=0.55, dur=3)
    g[0][82] = note(DARK, G4, vel=0.52, dur=3)
    g[0][88] = note(DARK, E4, vel=0.50, dur=4)
    # Fourth phrase — persistent, mapping the walls
    g[0][96]  = note(DARK, E4, vel=0.55, dur=2)
    g[0][99]  = note(DARK, G4, vel=0.55, dur=2)
    g[0][102] = note(DARK, A4, vel=0.58, dur=2)
    g[0][106] = note(DARK, B4, vel=0.58, dur=2)
    g[0][110] = note(DARK, A4, vel=0.55, dur=2)
    g[0][114] = note(DARK, G4, vel=0.55, dur=2)
    g[0][118] = note(DARK, E4, vel=0.52, dur=3)
    g[0][124] = note(DARK, E4, vel=0.48, dur=4)

    # Counter: driving 8th note arp — the relentless maze
    maze_arp = [E3, B3, G3, A3, E3, A3, G3, B3]
    for bar in range(8):
        base = bar * 16
        for beat in range(0, 16, 2):
            s = base + beat
            if s < steps:
                g[1][s] = note(ARP_TEX, maze_arp[(bar * 4 + beat // 2) % 8],
                               vel=0.42, dur=2)

    # Pad: drops to single low note — claustrophobia
    g[2][0]  = note(PAD, E2, vel=0.25, dur=32)
    g[2][32] = note(PAD, E2, vel=0.28, dur=32)
    g[2][64] = note(PAD, E2, vel=0.25, dur=32)
    g[2][96] = note(PAD, E2, vel=0.22, dur=32)

    # Bass: syncopated groove — not straight
    for i in range(0, steps, 8):
        g[3][i] = note(DEEP, E2, vel=0.45, dur=3)
        if i + 3 < steps:
            g[3][i + 3] = note(DEEP, G2, vel=0.38, dur=2)
    return pat("labyrinth", steps, g)


def p_thread_hope(steps=96):
    """Thread found — light breaks in. Melody rises from dark to warm.
    Instrument transition: saw_dark → saw_filtered (hope dawns).
    Pad opens up. Bass steadies."""
    g = new_grid(steps)
    # Lead: starts dark, transitions to warm — hope dawns
    g[0][0]  = note(DARK, B4, vel=0.55, dur=3)     # still dark
    g[0][4]  = note(DARK, D5, vel=0.58, dur=3)
    g[0][8]  = note(DARK, E5, vel=0.60, dur=6)     # reaching...
    # Shift! Warm voice enters — thread found
    g[0][20] = note(WARM, D5, vel=0.60, dur=3)     # transition!
    g[0][24] = note(WARM, B4, vel=0.58, dur=3)
    g[0][28] = note(WARM, A4, vel=0.60, dur=4)
    # Soaring phrase — the thread glows
    g[0][36] = note(WARM, E4, vel=0.58, dur=2)
    g[0][39] = note(WARM, G4, vel=0.60, dur=2)
    g[0][42] = note(WARM, B4, vel=0.62, dur=3)
    g[0][46] = note(WARM, D5, vel=0.65, dur=4)
    g[0][52] = note(WARM, E5, vel=0.68, dur=6)     # soaring — found it
    # Warm resolve — 'this was enough'
    g[0][62] = note(WARM, D5, vel=0.62, dur=3)
    g[0][66] = note(WARM, B4, vel=0.58, dur=4)
    g[0][72] = note(WARM, A4, vel=0.55, dur=3)
    g[0][76] = note(WARM, G4, vel=0.55, dur=4)
    g[0][82] = note(WARM, E4, vel=0.50, dur=6)     # rests
    g[0][90] = note(WARM, E4, vel=0.45, dur=6)     # exhale

    # Counter: gentle arpeggio — supporting the hope
    for i in range(0, 48, 8):
        g[1][i + 4] = note(ARP_TEX, [G4, B4, D5, E5, G4, B4][i // 8],
                           vel=0.30, dur=3)
    for i in range(48, 96, 8):
        g[1][i + 4] = note(ARP_TEX, [E4, G4, B4, A4, G4, E4][min((i - 48) // 8, 5)],
                           vel=0.28, dur=4)

    # Pad: opens from low drone to warm chord
    g[2][0]  = note(PAD, E2, vel=0.28, dur=16)
    g[2][16] = note(PAD, G3, vel=0.32, dur=16)     # opens up!
    g[2][32] = note(PAD, E3, vel=0.38, dur=16)
    g[2][48] = note(PAD, G3, vel=0.40, dur=16)
    g[2][64] = note(PAD, A3, vel=0.42, dur=16)
    g[2][80] = note(PAD, E3, vel=0.38, dur=16)

    # Bass: steady now — ground beneath his feet
    for i in range(0, steps, 16):
        g[3][i] = note(DEEP, E2, vel=0.38, dur=4)

    # Chimes: sparkle of hope
    g[4][12] = note(CHIME, E5, vel=0.35, dur=2)
    g[4][36] = note(CHIME, B5, vel=0.38, dur=1)
    g[4][56] = note(CHIME, G5, vel=0.40, dur=1)
    g[4][76] = note(CHIME, D5, vel=0.35, dur=2)
    return pat("thread_hope", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT IV: UNRAVELING & DEFIANCE (100-120s) — dark, fragmented → triumphant
# Everything breaks. Melody stutters. Then: he stands up. Lead_bright blazes.
# ══════════════════════════════════════════════════════════════════════════════

def p_unraveling(steps=112):
    """Things fall apart. Melody fragments. Gaps. Silence. Descending.
    Saw_dark stutters. Pad crumbles. Counter goes silent.
    The darkest moment before defiance."""
    g = new_grid(steps)
    # Lead: fragmented, gaps, stuttering — things breaking
    g[0][0]  = note(DARK, B4, vel=0.50, dur=2)
    g[0][6]  = note(DARK, A4, vel=0.48, dur=2)
    g[0][14] = note(DARK, G4, vel=0.45, dur=2)     # gaps!
    g[0][24] = note(DARK, E4, vel=0.45, dur=3)     # isolated
    g[0][36] = note(DARK, D4, vel=0.42, dur=2)     # descending
    g[0][44] = note(DARK, C4, vel=0.42, dur=4)     # C natural — despair
    # More fragments — barely there
    g[0][56] = note(DARK, E4, vel=0.40, dur=2)
    g[0][64] = note(DARK, D4, vel=0.38, dur=2)
    g[0][72] = note(DARK, C4, vel=0.38, dur=3)     # hanging
    g[0][84] = note(DARK, B3, vel=0.35, dur=3)     # almost gone
    # silence... then
    g[0][100] = note(DARK, E4, vel=0.30, dur=3)    # whisper of life

    # Pad: crumbling
    g[2][0]  = note(PAD, E3, vel=0.30, dur=16)
    g[2][16] = note(PAD, C3, vel=0.25, dur=16)     # dark
    g[2][32] = note(PAD, A2, vel=0.22, dur=16)
    g[2][48] = note(PAD, E2, vel=0.18, dur=16)     # almost silent
    # Pad stops after bar 4 — emptiness

    # Counter: nothing. It's gone.
    # Bass: nothing. Ground is gone.
    # Chimes: one single dying chime
    g[4][8]  = note(CHIME, C5, vel=0.20, dur=4)    # wrong note, eerie
    g[4][40] = note(CHIME, B4, vel=0.15, dur=4)    # fading
    return pat("unraveling", steps, g)


def p_stood_up(steps=80):
    """'He stood up anyway.' — silence then DEFIANCE. Lead_bright blazes.
    The moment the score transforms. Bass returns. Pad swells. Everything returns."""
    g = new_grid(steps)
    # Silence... 16 steps of nothing (dramatic pause)
    # Then: DEFIANT. Lead_bright enters like sunrise.
    g[0][16] = note(BRIGHT, E4, vel=0.65, dur=3)   # stood UP
    g[0][20] = note(BRIGHT, G4, vel=0.68, dur=3)
    g[0][24] = note(BRIGHT, B4, vel=0.70, dur=4)   # ascending!
    g[0][30] = note(BRIGHT, D5, vel=0.72, dur=3)
    g[0][34] = note(BRIGHT, E5, vel=0.75, dur=6)   # BLAZING
    # Building phrase — all instruments return
    g[0][44] = note(BRIGHT, D5, vel=0.72, dur=2)
    g[0][47] = note(BRIGHT, E5, vel=0.75, dur=2)
    g[0][50] = note(BRIGHT, D5, vel=0.70, dur=2)
    g[0][53] = note(BRIGHT, B4, vel=0.68, dur=3)
    g[0][58] = note(BRIGHT, D5, vel=0.72, dur=2)
    g[0][61] = note(BRIGHT, E5, vel=0.75, dur=4)   # soaring again
    g[0][68] = note(BRIGHT, D5, vel=0.70, dur=3)
    g[0][72] = note(BRIGHT, B4, vel=0.68, dur=4)
    g[0][78] = note(BRIGHT, E4, vel=0.65, dur=2)   # grounded

    # Counter: arpeggio returns with force
    for i in range(16, 80, 4):
        m = [E4, G4, B4, D5, E4, A4, B4, G4][(i // 4) % 8]
        g[1][i] = note(ARP_TEX, m, vel=0.42, dur=2)

    # Pad: SURGES BACK
    g[2][16] = note(PAD, E3, vel=0.35, dur=16)
    g[2][32] = note(PAD, G3, vel=0.42, dur=16)
    g[2][48] = note(PAD, B3, vel=0.45, dur=16)
    g[2][64] = note(PAD, E3, vel=0.42, dur=16)

    # Bass: triumphant return
    g[3][16] = note(DEEP, E2, vel=0.50, dur=4)
    g[3][24] = note(DEEP, G2, vel=0.50, dur=4)
    g[3][32] = note(DEEP, A2, vel=0.52, dur=4)
    g[3][40] = note(DEEP, E2, vel=0.48, dur=4)
    g[3][48] = note(DEEP, G2, vel=0.50, dur=4)
    g[3][56] = note(DEEP, B2, vel=0.52, dur=4)
    g[3][64] = note(DEEP, E2, vel=0.48, dur=4)
    g[3][72] = note(DEEP, E2, vel=0.45, dur=4)

    # Chimes: celebration
    g[4][20] = note(CHIME, E5, vel=0.40, dur=1)
    g[4][32] = note(CHIME, B5, vel=0.42, dur=1)
    g[4][48] = note(CHIME, G5, vel=0.38, dur=1)
    g[4][64] = note(CHIME, D5, vel=0.40, dur=1)
    return pat("stood_up", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT V: THE RETURN (120-140s) — warm resolution, then the arp fadeout
# Full glory → warmth → the arp-to-sparse ending they loved.
# Everything converges then gradually dissolves back to starlight.
# ══════════════════════════════════════════════════════════════════════════════

def p_return_glory(steps=96):
    """The Return — full score, all instruments playing, warm triumph.
    'She waits.' Stars call him home. Music at its fullest."""
    g = new_grid(steps)
    # Lead: soaring warm melody — coming home
    g[0][0]  = note(BRIGHT, E4, vel=0.70, dur=2)
    g[0][3]  = note(BRIGHT, G4, vel=0.72, dur=2)
    g[0][6]  = note(BRIGHT, B4, vel=0.75, dur=3)
    g[0][10] = note(BRIGHT, D5, vel=0.75, dur=3)
    g[0][14] = note(BRIGHT, E5, vel=0.78, dur=6)   # she waits
    g[0][24] = note(BRIGHT, D5, vel=0.72, dur=2)
    g[0][27] = note(BRIGHT, E5, vel=0.75, dur=2)
    g[0][30] = note(BRIGHT, D5, vel=0.72, dur=2)
    g[0][33] = note(BRIGHT, B4, vel=0.70, dur=3)
    # 'Toward the light' — the biggest melodic moment
    g[0][40] = note(BRIGHT, E4, vel=0.72, dur=2)
    g[0][43] = note(BRIGHT, G4, vel=0.72, dur=2)
    g[0][46] = note(BRIGHT, B4, vel=0.75, dur=2)
    g[0][49] = note(BRIGHT, D5, vel=0.75, dur=2)
    g[0][52] = note(BRIGHT, E5, vel=0.78, dur=4)   # PEAK
    g[0][58] = note(BRIGHT, D5, vel=0.75, dur=2)
    g[0][61] = note(BRIGHT, E5, vel=0.78, dur=2)
    g[0][64] = note(BRIGHT, D5, vel=0.72, dur=3)
    g[0][68] = note(BRIGHT, B4, vel=0.70, dur=4)
    # 'She was always there' — warm resolve
    g[0][76] = note(WARM, E5, vel=0.65, dur=4)     # shift to warm for resolve
    g[0][82] = note(WARM, D5, vel=0.62, dur=3)
    g[0][86] = note(WARM, B4, vel=0.60, dur=4)
    g[0][92] = note(WARM, E4, vel=0.55, dur=4)     # home

    # Counter: becoming the arp — transitioning to what they loved
    arp_notes = [E4, B4, G4, A4]
    for i in range(0, 64, 2):
        g[1][i] = note(ARP_TEX, arp_notes[(i // 2) % 4], vel=0.40, dur=1)
    # Counter continues but slower in warm section
    for i in range(64, 96, 4):
        g[1][i] = note(ARP_TEX, arp_notes[((i - 64) // 4) % 4], vel=0.35, dur=2)

    # Pad: full warm chord — everything together
    g[2][0]  = note(PAD, E3, vel=0.45, dur=16)
    g[2][16] = note(PAD, G3, vel=0.45, dur=16)
    g[2][32] = note(PAD, B3, vel=0.45, dur=16)
    g[2][48] = note(PAD, E3, vel=0.42, dur=16)
    g[2][64] = note(PAD, G3, vel=0.40, dur=16)
    g[2][80] = note(PAD, E3, vel=0.38, dur=16)

    # Bass: confident
    for i in range(0, 80, 8):
        bass = [E2, G2, B2, E2, G2, A2, E2, G2, E2, E2][min(i // 8, 9)]
        g[3][i] = note(DEEP, bass, vel=0.48, dur=4)

    # Chimes: stars blazing
    g[4][4]  = note(CHIME, E5, vel=0.42, dur=1)
    g[4][16] = note(CHIME, B5, vel=0.40, dur=1)
    g[4][36] = note(CHIME, G5, vel=0.38, dur=1)
    g[4][56] = note(CHIME, D5, vel=0.40, dur=1)
    g[4][72] = note(CHIME, E5, vel=0.35, dur=1)
    return pat("return_glory", steps, g)


def p_fadeout(steps=128):
    """THE ENDING — the part they loved. Arp thins to starlight.
    Full arp → half density → quarter → isolated notes → whisper → void.
    This is the classy, perfect way to end."""
    g = new_grid(steps)
    HOOK = [E4, B4, G4, A4]

    # Bars 1-2 (0-31): full arp, bright, resolving
    for i in range(0, 32):
        g[0][i] = note(BRIGHT, HOOK[i % 4], vel=0.65 - (i * 0.003), dur=1)

    # Bars 3-4 (32-63): half density — thinning
    for i in range(32, 64, 2):
        g[0][i] = note(BRIGHT, HOOK[((i - 32) // 2) % 4],
                       vel=0.52 - ((i - 32) * 0.003), dur=1)

    # Bars 5-6 (64-95): quarter — dissolving to individual stars
    for i in range(64, 96, 4):
        g[0][i] = note(BRIGHT, HOOK[((i - 64) // 4) % 4],
                       vel=0.38 - ((i - 64) * 0.003), dur=2)

    # Bars 7-8 (96-127): isolated long notes — stars fading out
    g[0][96]  = note(WARM, E4, vel=0.28, dur=6)    # warm for final notes
    g[0][104] = note(WARM, B4, vel=0.22, dur=6)
    g[0][112] = note(WARM, E4, vel=0.15, dur=8)    # barely there
    g[0][122] = note(WARM, E4, vel=0.08, dur=6)    # whisper

    # Pad: long fade
    g[2][0]  = note(PAD, E3, vel=0.35, dur=16)
    g[2][16] = note(PAD, E3, vel=0.30, dur=16)
    g[2][32] = note(PAD, E3, vel=0.25, dur=16)
    g[2][48] = note(PAD, E3, vel=0.18, dur=16)
    g[2][64] = note(PAD, E3, vel=0.12, dur=16)
    # Pad fades out — silence

    # Counter: sparse echoes
    g[1][8]  = note(ARP_TEX, G4, vel=0.25, dur=2)
    g[1][24] = note(ARP_TEX, E4, vel=0.20, dur=2)
    g[1][40] = note(ARP_TEX, B4, vel=0.15, dur=3)
    g[1][64] = note(ARP_TEX, E4, vel=0.10, dur=4)

    # One final chime — the last star
    g[4][80] = note(CHIME, E5, vel=0.18, dur=4)
    return pat("fadeout", steps, g)


def p_silence(steps=32):
    """Clean silence tail."""
    g = new_grid(steps)
    return pat("silence_tail", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# SONG ASSEMBLY
# ══════════════════════════════════════════════════════════════════════════════

def build_song() -> Song:
    patterns = [
        p_starfield(96),        # 0: Act I — void wakes, stars, pad (11.4s)
        p_cosmic_grief(128),    # 1: Act I — she let go, descending (15.2s)
        p_search_begins(80),    # 2: Act I→II — quickening, bass enters (9.5s)
        p_four_gifts(176),      # 3: Act II — 4 gifts, full bloom (21.0s)
        p_labyrinth(128),       # 4: Act III — dark groove, tension (15.2s)
        p_thread_hope(96),      # 5: Act III — hope, dark→warm (11.4s)
        p_unraveling(112),      # 6: Act IV — things break (13.3s)
        p_stood_up(80),         # 7: Act IV — DEFIANCE! (9.5s)
        p_return_glory(96),     # 8: Act V — full score triumph (11.4s)
        p_fadeout(128),         # 9: Act V — THE ENDING they loved (15.2s)
        p_silence(32),          # 10: clean tail (3.8s)
    ]

    sequence = list(range(len(patterns)))

    total_steps = sum(p.num_steps for p in patterns)
    duration_s = total_steps * 60.0 / (BPM * SPB)
    print(f"Melody: {len(patterns)} patterns, {total_steps} steps, "
          f"{duration_s:.1f}s at {BPM} BPM")
    print(f"Channels: {CHANNELS} (lead, counter, pad, bass, accent)")

    song = Song(
        title="core_fable_melody",
        bpm=BPM,
        patterns=patterns,
        sequence=sequence,
        channel_effects={
            0: {"reverb": 0.22, "delay": 0.15, "delay_feedback": 0.25},  # lead
            1: {"reverb": 0.18, "delay": 0.12, "delay_feedback": 0.20},  # counter
            2: {"reverb": 0.40},                                          # pad: deep hall
            3: {"reverb": 0.08},                                          # bass: tight
            4: {"reverb": 0.30, "delay": 0.20, "delay_feedback": 0.15},  # chimes: spacious
        },
        panning={0: 0.10, 1: -0.18, 2: -0.05, 3: 0.0, 4: 0.25},
        master_reverb=0.12,
    )
    return song


if __name__ == '__main__':
    song = build_song()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb)
    out = Path('output/core_fable_melody.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered: {len(audio)/44100:.1f}s → {out}")
