"""
ChipForge FILM SCORE v4 for core_fable — melodic journey soundtrack.

Enhanced from v3: more singable melodies, recurring journey motif (E→G→A→B)
that evolves across acts, stronger rhythmic momentum, upbeat gift/journey feel.
Preserved: the arp-to-starlight fadeout ending.

Key: E natural minor (E F# G A B C D)
BPM: 126
Duration target: ~141s (covers 140s film)

Film arc:
  Act I   (0-35s):   Cosmic solitude — journey motif emerges from void
  Act II  (35-70s):  Wonder & gifts — motif blooms, rhythmic pulse builds
  Act III (70-100s): Labyrinth — driving determination, motif syncopated
  Act IV  (100-120s): Unraveling — motif fragments → blazing defiance
  Act V   (120-140s): The Return — motif soars home, dissolves to starlight

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
# ACT I: COSMIC SOLITUDE (0-35s) — journey motif emerges from void
# The motif (E→G→A→B) appears tentatively, like a question into darkness.
# ══════════════════════════════════════════════════════════════════════════════

def p_starfield(steps=96):
    """Opening — void wakes. Journey motif emerges tentatively."""
    g = new_grid(steps)

    # Pad: E minor — the cosmos breathing
    g[2][0]  = note(PAD, E3, vel=0.22, dur=16)
    g[2][16] = note(PAD, E3, vel=0.28, dur=16)
    g[2][32] = note(PAD, G3, vel=0.32, dur=16)
    g[2][48] = note(PAD, E3, vel=0.35, dur=16)
    g[2][64] = note(PAD, B3, vel=0.35, dur=16)
    g[2][80] = note(PAD, E3, vel=0.38, dur=16)

    # Chimes: stars appearing
    g[4][8]  = note(CHIME, B4, vel=0.18, dur=1)
    g[4][20] = note(CHIME, E5, vel=0.20, dur=1)
    g[4][38] = note(CHIME, G5, vel=0.22, dur=1)
    g[4][52] = note(CHIME, D5, vel=0.20, dur=1)
    g[4][68] = note(CHIME, A5, vel=0.25, dur=1)
    g[4][84] = note(CHIME, E5, vel=0.22, dur=1)

    # Lead: journey motif emerges — first just E→G, then E→G→A, then E→G→A→B
    # Fragment 1: just two notes — tentative
    g[0][24] = note(WARM, E4, vel=0.30, dur=3)
    g[0][28] = note(WARM, G4, vel=0.32, dur=3)

    # Fragment 2: three notes — growing
    g[0][48] = note(WARM, E4, vel=0.35, dur=3)
    g[0][52] = note(WARM, G4, vel=0.38, dur=3)
    g[0][56] = note(WARM, A4, vel=0.40, dur=3)

    # Fragment 3: full motif stated — the question rises
    g[0][72] = note(WARM, E4, vel=0.42, dur=3)
    g[0][76] = note(WARM, G4, vel=0.45, dur=2)
    g[0][80] = note(WARM, A4, vel=0.48, dur=2)
    g[0][84] = note(WARM, B4, vel=0.50, dur=4)  # hangs — longing

    # Counter: sparse star-pulse echoes
    g[1][32] = note(ARP_TEX, B4, vel=0.18, dur=2)
    g[1][60] = note(ARP_TEX, E4, vel=0.20, dur=2)
    g[1][88] = note(ARP_TEX, G4, vel=0.22, dur=2)

    return pat("starfield", steps, g)


def p_cosmic_grief(steps=128):
    """She let go — descending grief, but motif echoes rise back."""
    g = new_grid(steps)

    # Lead: descending grief melody with motif fragments rising back
    # Phrase 1: grief descends (B→A→G→E→D)
    g[0][0]  = note(WARM, B4, vel=0.55, dur=3)
    g[0][4]  = note(WARM, A4, vel=0.52, dur=3)
    g[0][8]  = note(WARM, G4, vel=0.50, dur=3)
    g[0][12] = note(WARM, E4, vel=0.48, dur=4)
    g[0][18] = note(WARM, D4, vel=0.45, dur=4)

    # Motif echo rises back (E→G→A) — hope not dead
    g[0][28] = note(WARM, E4, vel=0.40, dur=2)
    g[0][32] = note(WARM, G4, vel=0.42, dur=2)
    g[0][36] = note(WARM, A4, vel=0.44, dur=3)

    # Phrase 2: deeper grief (A→G→E→D→C)
    g[0][44] = note(WARM, A4, vel=0.52, dur=3)
    g[0][48] = note(WARM, G4, vel=0.48, dur=3)
    g[0][52] = note(WARM, E4, vel=0.45, dur=3)
    g[0][56] = note(WARM, D4, vel=0.42, dur=3)
    g[0][62] = note(WARM, C4, vel=0.40, dur=4)

    # Motif again, reaching higher (E→G→A→B) — resilience
    g[0][72] = note(WARM, E4, vel=0.48, dur=2)
    g[0][76] = note(WARM, G4, vel=0.50, dur=2)
    g[0][80] = note(WARM, A4, vel=0.52, dur=2)
    g[0][84] = note(WARM, B4, vel=0.55, dur=4)

    # Phrase 3: acceptance — new melody lifts (B→D5→E5)
    g[0][96]  = note(WARM, B4, vel=0.55, dur=3)
    g[0][100] = note(WARM, D5, vel=0.58, dur=3)
    g[0][104] = note(WARM, E5, vel=0.60, dur=4)    # first time reaching E5
    g[0][112] = note(WARM, D5, vel=0.52, dur=3)
    g[0][118] = note(WARM, B4, vel=0.48, dur=4)
    g[0][124] = note(WARM, A4, vel=0.45, dur=4)    # settles — ready

    # Counter: ghostly echoes of grief melody
    g[1][6]  = note(ARP_TEX, G4, vel=0.22, dur=2)
    g[1][20] = note(ARP_TEX, E4, vel=0.20, dur=2)
    g[1][40] = note(ARP_TEX, B4, vel=0.25, dur=2)
    g[1][58] = note(ARP_TEX, A4, vel=0.22, dur=2)
    g[1][78] = note(ARP_TEX, G4, vel=0.28, dur=2)
    g[1][98] = note(ARP_TEX, E4, vel=0.30, dur=2)
    g[1][108] = note(ARP_TEX, B4, vel=0.28, dur=2)
    g[1][120] = note(ARP_TEX, G4, vel=0.25, dur=2)

    # Pad: E minor shifting — emotional weight
    g[2][0]  = note(PAD, E3, vel=0.35, dur=16)
    g[2][16] = note(PAD, G3, vel=0.32, dur=16)
    g[2][32] = note(PAD, E3, vel=0.30, dur=16)
    g[2][48] = note(PAD, A3, vel=0.32, dur=16)
    g[2][64] = note(PAD, E3, vel=0.35, dur=16)
    g[2][80] = note(PAD, G3, vel=0.38, dur=16)
    g[2][96] = note(PAD, B3, vel=0.38, dur=16)
    g[2][112] = note(PAD, E3, vel=0.40, dur=16)

    # Chimes: tears
    g[4][14] = note(CHIME, E5, vel=0.22, dur=1)
    g[4][42] = note(CHIME, G5, vel=0.20, dur=1)
    g[4][70] = note(CHIME, B5, vel=0.25, dur=1)
    g[4][90] = note(CHIME, D5, vel=0.22, dur=1)
    g[4][110] = note(CHIME, E5, vel=0.28, dur=1)

    return pat("cosmic_grief", steps, g)


def p_search_begins(steps=80):
    """Quickening — journey motif confidently stated, bass enters, momentum."""
    g = new_grid(steps)

    # Lead: motif rings out clear: E→G→A→B, then extends upward (D5→E5)
    g[0][0]  = note(WARM, E4, vel=0.55, dur=3)
    g[0][4]  = note(WARM, G4, vel=0.58, dur=2)
    g[0][8]  = note(WARM, A4, vel=0.60, dur=2)
    g[0][12] = note(WARM, B4, vel=0.62, dur=3)
    # Extends: soaring to D5, E5
    g[0][18] = note(WARM, D5, vel=0.64, dur=3)
    g[0][22] = note(WARM, E5, vel=0.65, dur=4)

    # Second phrase: descending answer (E5→D5→B4→A4→G4)
    g[0][32] = note(WARM, E5, vel=0.62, dur=2)
    g[0][36] = note(WARM, D5, vel=0.58, dur=2)
    g[0][40] = note(WARM, B4, vel=0.55, dur=3)
    g[0][44] = note(WARM, A4, vel=0.52, dur=3)
    g[0][48] = note(WARM, G4, vel=0.50, dur=4)

    # Third phrase: motif again, pushing even higher (B4→D5→E5→G5)
    g[0][56] = note(WARM, B4, vel=0.58, dur=2)
    g[0][60] = note(WARM, D5, vel=0.62, dur=2)
    g[0][64] = note(WARM, E5, vel=0.65, dur=3)
    g[0][68] = note(BRIGHT, G5, vel=0.68, dur=4)   # bright for the peak
    g[0][74] = note(WARM, E5, vel=0.60, dur=3)     # resolves down

    # Counter: driving rhythmic arp (every 4 steps) — momentum
    arp_notes = [E4, G4, B4, A4]
    for i in range(0, 80, 4):
        g[1][i] = note(ARP_TEX, arp_notes[(i // 4) % 4],
                       vel=0.35 + (i * 0.002), dur=2)

    # Pad: brighter chord motion
    g[2][0]  = note(PAD, E3, vel=0.38, dur=16)
    g[2][16] = note(PAD, G3, vel=0.40, dur=16)
    g[2][32] = note(PAD, A3, vel=0.40, dur=16)
    g[2][48] = note(PAD, B3, vel=0.42, dur=16)
    g[2][64] = note(PAD, E3, vel=0.42, dur=16)

    # Bass enters — heartbeat pulse on E
    for i in range(0, 80, 8):
        bass = [E2, E2, G2, E2, A2, E2, G2, B2, E2, E2][min(i // 8, 9)]
        g[3][i] = note(DEEP, bass, vel=0.35 + (i * 0.002), dur=4)

    # Chimes: wonder sparks
    g[4][10] = note(CHIME, E5, vel=0.30, dur=1)
    g[4][28] = note(CHIME, B5, vel=0.28, dur=1)
    g[4][50] = note(CHIME, G5, vel=0.30, dur=1)
    g[4][70] = note(CHIME, D5, vel=0.32, dur=1)

    return pat("search_begins", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT II: WONDER & GIFTS (35-70s) — motif blooms into full melody
# Each gift has its own melodic character built on the motif foundation.
# Rhythmic arp drives momentum — sense of adventure building.
# ══════════════════════════════════════════════════════════════════════════════

def p_four_gifts(steps=176):
    """Four gifts — each with distinct melodic signature, motif as thread."""
    g = new_grid(steps)

    # ── LANTERN (steps 0-43): warm ascending — wonder, discovery ──
    # Motif stated warmly: E→G→A→B, then keeps climbing
    g[0][0]  = note(WARM, E4, vel=0.58, dur=3)
    g[0][4]  = note(WARM, G4, vel=0.60, dur=2)
    g[0][8]  = note(WARM, A4, vel=0.62, dur=2)
    g[0][12] = note(WARM, B4, vel=0.65, dur=3)
    g[0][16] = note(WARM, D5, vel=0.68, dur=3)
    g[0][20] = note(WARM, E5, vel=0.70, dur=4)     # peak — lantern lit
    # Gentle descent (contentment)
    g[0][28] = note(WARM, D5, vel=0.62, dur=3)
    g[0][32] = note(WARM, B4, vel=0.58, dur=3)
    g[0][36] = note(WARM, A4, vel=0.55, dur=3)
    g[0][40] = note(WARM, G4, vel=0.52, dur=4)

    # ── MIRROR (steps 44-87): reflective call-and-response ──
    # Call: motif ascending (E→G→A→B)
    g[0][44] = note(WARM, E4, vel=0.55, dur=3)
    g[0][48] = note(WARM, G4, vel=0.58, dur=2)
    g[0][52] = note(WARM, A4, vel=0.60, dur=2)
    g[0][56] = note(WARM, B4, vel=0.62, dur=3)
    # Response: reflection descending from higher (G5→E5→D5→B4)
    g[0][62] = note(BRIGHT, G5, vel=0.60, dur=2)
    g[0][66] = note(BRIGHT, E5, vel=0.58, dur=2)
    g[0][70] = note(BRIGHT, D5, vel=0.55, dur=2)
    g[0][74] = note(WARM, B4, vel=0.52, dur=3)
    # Second call: higher (G→A→B→D5)
    g[0][80] = note(WARM, G4, vel=0.58, dur=2)
    g[0][84] = note(WARM, B4, vel=0.60, dur=4)

    # ── HAMMER (steps 88-131): rhythmic, strong, 3-step driving pulse ──
    hammer_melody = [E4, G4, A4, B4, D5, E5, D5, B4, A4, G4, E4, G4, A4, B4]
    for i, m in enumerate(hammer_melody):
        step = 88 + i * 3
        if step < 132:
            g[0][step] = note(BRIGHT, m, vel=0.62 + (i % 3) * 0.03, dur=2)

    # ── CHAIN (steps 132-175): bittersweet, heavy, lower register ──
    # Motif inverted — descending weight: B→A→G→E
    g[0][132] = note(WARM, B4, vel=0.55, dur=4)
    g[0][138] = note(WARM, A4, vel=0.52, dur=4)
    g[0][144] = note(WARM, G4, vel=0.50, dur=4)
    g[0][150] = note(WARM, E4, vel=0.48, dur=4)
    # Then lifts — chain holds, gives strength
    g[0][158] = note(WARM, G4, vel=0.50, dur=3)
    g[0][162] = note(WARM, A4, vel=0.55, dur=3)
    g[0][166] = note(WARM, B4, vel=0.58, dur=4)
    g[0][172] = note(WARM, D5, vel=0.55, dur=4)    # reaches up — hope

    # Counter: driving arp throughout — adventure momentum
    arp_pattern = [E4, B4, G4, A4]
    for i in range(0, 88, 4):           # lantern + mirror: regular pulse
        g[1][i] = note(ARP_TEX, arp_pattern[(i // 4) % 4],
                       vel=0.35, dur=2)
    for i in range(88, 132, 3):         # hammer: match 3-step drive
        g[1][i] = note(ARP_TEX, arp_pattern[((i - 88) // 3) % 4],
                       vel=0.38, dur=2)
    for i in range(132, 176, 4):        # chain: slower pulse — weight
        g[1][i] = note(ARP_TEX, arp_pattern[((i - 132) // 4) % 4],
                       vel=0.32, dur=3)

    # Pad: chord progression — warm harmonic motion
    chords = [E3, G3, A3, E3, B3, G3, E3, A3, G3, E3, G3]
    for i, ch in enumerate(chords):
        step = i * 16
        if step < steps:
            g[2][step] = note(PAD, ch, vel=0.42, dur=16)

    # Bass: steady heartbeat
    bass_line = [E2, G2, A2, E2, B2, E2, G2, A2, E2, G2, E2,
                 E2, G2, A2, E2, B2, E2, G2, A2, B2, E2, G2]
    for i in range(0, 176, 8):
        idx = min(i // 8, len(bass_line) - 1)
        g[3][i] = note(DEEP, bass_line[idx], vel=0.42, dur=4)

    # Chimes: gift sparkles
    g[4][6]   = note(CHIME, E5, vel=0.35, dur=1)   # lantern spark
    g[4][22]  = note(CHIME, B5, vel=0.32, dur=1)
    g[4][50]  = note(CHIME, G5, vel=0.35, dur=1)   # mirror glint
    g[4][75]  = note(CHIME, D5, vel=0.30, dur=1)
    g[4][95]  = note(CHIME, E5, vel=0.38, dur=1)   # hammer ring
    g[4][115] = note(CHIME, A5, vel=0.35, dur=1)
    g[4][140] = note(CHIME, B5, vel=0.30, dur=1)   # chain shimmer
    g[4][168] = note(CHIME, E5, vel=0.35, dur=1)

    return pat("four_gifts", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT III: THE LABYRINTH (70-100s) — driving determination, motif syncopated
# Tension builds. Counter arp becomes relentless 8th-note drive.
# ══════════════════════════════════════════════════════════════════════════════

def p_labyrinth(steps=128):
    """Dark labyrinth — driving urgency, motif pushed into syncopation."""
    g = new_grid(steps)

    # Lead: DARK instrument — motif still there but pushed off-beat, urgent
    # Phrase 1: syncopated motif (off-beat starts)
    g[0][2]  = note(DARK, E4, vel=0.58, dur=2)     # off-beat entry
    g[0][6]  = note(DARK, G4, vel=0.60, dur=2)
    g[0][10] = note(DARK, A4, vel=0.62, dur=2)
    g[0][14] = note(DARK, B4, vel=0.65, dur=3)
    g[0][20] = note(DARK, D5, vel=0.68, dur=3)
    g[0][26] = note(DARK, E5, vel=0.70, dur=4)     # peak — labyrinth opens

    # Phrase 2: descending urgency (B→A→G→E→D)
    g[0][36] = note(DARK, B4, vel=0.62, dur=2)
    g[0][40] = note(DARK, A4, vel=0.60, dur=2)
    g[0][44] = note(DARK, G4, vel=0.58, dur=3)
    g[0][48] = note(DARK, E4, vel=0.55, dur=3)
    g[0][54] = note(DARK, D4, vel=0.52, dur=3)

    # Phrase 3: climbing again — determination (E→Fs→G→A→B→D5→E5)
    g[0][62] = note(DARK, E4, vel=0.58, dur=2)
    g[0][66] = note(DARK, Fs4, vel=0.60, dur=2)
    g[0][70] = note(DARK, G4, vel=0.62, dur=2)
    g[0][74] = note(DARK, A4, vel=0.65, dur=2)
    g[0][78] = note(DARK, B4, vel=0.68, dur=2)
    g[0][82] = note(DARK, D5, vel=0.70, dur=3)
    g[0][86] = note(DARK, E5, vel=0.72, dur=4)

    # Phrase 4: pushing through — repeated motif fragments
    g[0][96]  = note(DARK, E4, vel=0.60, dur=2)
    g[0][100] = note(DARK, G4, vel=0.62, dur=2)
    g[0][104] = note(DARK, B4, vel=0.65, dur=2)    # compressed motif
    g[0][108] = note(DARK, E5, vel=0.68, dur=3)    # reaching
    g[0][114] = note(DARK, D5, vel=0.62, dur=3)
    g[0][120] = note(DARK, B4, vel=0.58, dur=4)
    g[0][126] = note(DARK, A4, vel=0.55, dur=2)

    # Counter: relentless 8th-note arp — every 2 steps — driving pulse
    dark_arp = [E4, B4, G4, A4, E4, D5, B4, G4]
    for i in range(0, 128, 2):
        g[1][i] = note(ARP_TEX, dark_arp[(i // 2) % len(dark_arp)],
                       vel=0.38 + (i * 0.001), dur=1)

    # Pad: darker chords — tension
    g[2][0]  = note(PAD, E3, vel=0.40, dur=16)
    g[2][16] = note(PAD, D3, vel=0.38, dur=16)
    g[2][32] = note(PAD, E3, vel=0.42, dur=16)
    g[2][48] = note(PAD, A3, vel=0.38, dur=16)
    g[2][64] = note(PAD, E3, vel=0.42, dur=16)
    g[2][80] = note(PAD, D3, vel=0.40, dur=16)
    g[2][96] = note(PAD, E3, vel=0.42, dur=16)
    g[2][112] = note(PAD, G3, vel=0.40, dur=16)

    # Bass: insistent pulse — locked to E
    for i in range(0, 128, 4):
        bass = E2 if (i // 4) % 3 != 2 else G2
        g[3][i] = note(DEEP, bass, vel=0.45, dur=3)

    return pat("labyrinth", steps, g)


def p_thread_hope(steps=96):
    """Thread of hope in the labyrinth — DARK→WARM crossover moment."""
    g = new_grid(steps)

    # Lead: starts DARK, crosses over to WARM — transformation
    # Dark section: motif fragmented, uncertain
    g[0][0]  = note(DARK, E4, vel=0.52, dur=3)
    g[0][4]  = note(DARK, G4, vel=0.50, dur=2)
    g[0][8]  = note(DARK, A4, vel=0.48, dur=3)     # motif incomplete

    g[0][16] = note(DARK, B4, vel=0.50, dur=3)
    g[0][20] = note(DARK, A4, vel=0.48, dur=2)
    g[0][24] = note(DARK, G4, vel=0.45, dur=3)

    # Crossover moment — instrument changes mid-phrase: DARK → WARM
    g[0][32] = note(DARK, E4, vel=0.50, dur=2)
    g[0][36] = note(DARK, G4, vel=0.52, dur=2)
    g[0][40] = note(WARM, A4, vel=0.55, dur=3)     # WARM takes over!
    g[0][44] = note(WARM, B4, vel=0.58, dur=3)

    # Full WARM — motif soars, hope found
    g[0][52] = note(WARM, E4, vel=0.58, dur=2)
    g[0][56] = note(WARM, G4, vel=0.60, dur=2)
    g[0][60] = note(WARM, A4, vel=0.62, dur=2)
    g[0][64] = note(WARM, B4, vel=0.65, dur=2)
    g[0][68] = note(WARM, D5, vel=0.68, dur=3)
    g[0][72] = note(WARM, E5, vel=0.70, dur=4)     # triumph —
    g[0][80] = note(WARM, D5, vel=0.62, dur=3)
    g[0][84] = note(WARM, B4, vel=0.58, dur=3)
    g[0][88] = note(WARM, A4, vel=0.55, dur=4)
    g[0][94] = note(WARM, G4, vel=0.50, dur=2)

    # Counter: arp opens from 4-step to 3-step as hope builds
    arp = [E4, B4, G4, A4]
    for i in range(0, 48, 4):       # dark: sparse 4-step
        g[1][i] = note(ARP_TEX, arp[(i // 4) % 4], vel=0.30, dur=2)
    for i in range(48, 96, 3):      # warm: quicker 3-step — uplifting
        g[1][i] = note(ARP_TEX, arp[((i - 48) // 3) % 4], vel=0.38, dur=2)

    # Pad: D minor → E minor → G major feel
    g[2][0]  = note(PAD, D3, vel=0.38, dur=16)
    g[2][16] = note(PAD, E3, vel=0.38, dur=16)
    g[2][32] = note(PAD, E3, vel=0.40, dur=16)
    g[2][48] = note(PAD, G3, vel=0.42, dur=16)
    g[2][64] = note(PAD, B3, vel=0.42, dur=16)
    g[2][80] = note(PAD, E3, vel=0.40, dur=16)

    # Bass: gradual entrance
    g[3][32] = note(DEEP, E2, vel=0.35, dur=4)
    g[3][48] = note(DEEP, G2, vel=0.38, dur=4)
    g[3][56] = note(DEEP, E2, vel=0.40, dur=4)
    g[3][64] = note(DEEP, B2, vel=0.42, dur=4)
    g[3][72] = note(DEEP, E2, vel=0.45, dur=4)
    g[3][80] = note(DEEP, G2, vel=0.42, dur=4)
    g[3][88] = note(DEEP, E2, vel=0.40, dur=4)

    # Chimes: hope blooming
    g[4][24] = note(CHIME, G5, vel=0.28, dur=1)
    g[4][42] = note(CHIME, D5, vel=0.32, dur=1)
    g[4][60] = note(CHIME, E5, vel=0.35, dur=1)
    g[4][76] = note(CHIME, B5, vel=0.38, dur=1)

    return pat("thread_hope", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT IV: THE UNRAVELING (100-120s) — motif fragments → blazing defiance
# Things fall apart. Then the boy stands up anyway.
# ══════════════════════════════════════════════════════════════════════════════

def p_unraveling(steps=112):
    """Things break apart — motif dissolves into fragments, sparse, lost."""
    g = new_grid(steps)

    # Lead: motif fragments scattered — E, G, ... silence ... A, ... silence
    g[0][0]  = note(DARK, E4, vel=0.50, dur=2)
    g[0][8]  = note(DARK, G4, vel=0.45, dur=2)
    # silence — reaching for the next note
    g[0][20] = note(DARK, A4, vel=0.42, dur=3)
    # silence — can't complete the motif
    g[0][36] = note(DARK, E4, vel=0.38, dur=2)
    g[0][44] = note(DARK, B4, vel=0.40, dur=3)     # reaches, fails
    g[0][52] = note(DARK, A4, vel=0.35, dur=2)     # falling
    # Long silence — everything quiet (64-79 empty)
    g[0][80] = note(DARK, G4, vel=0.30, dur=4)     # ghost of motif
    g[0][92] = note(DARK, E4, vel=0.25, dur=4)     # barely audible
    g[0][104] = note(DARK, D4, vel=0.20, dur=6)    # lowest point

    # Counter: breaks apart — scattered fragments
    g[1][4]  = note(ARP_TEX, B4, vel=0.28, dur=1)
    g[1][16] = note(ARP_TEX, E4, vel=0.22, dur=1)
    g[1][32] = note(ARP_TEX, G4, vel=0.18, dur=2)
    g[1][48] = note(ARP_TEX, A4, vel=0.15, dur=2)
    g[1][72] = note(ARP_TEX, E4, vel=0.12, dur=2)
    g[1][96] = note(ARP_TEX, B4, vel=0.10, dur=3)

    # Pad: hollow, fading
    g[2][0]  = note(PAD, E3, vel=0.35, dur=16)
    g[2][16] = note(PAD, D3, vel=0.30, dur=16)
    g[2][32] = note(PAD, C3, vel=0.25, dur=16)
    g[2][48] = note(PAD, E3, vel=0.20, dur=16)
    g[2][64] = note(PAD, D3, vel=0.15, dur=16)
    # Pad fades to almost nothing
    g[2][80] = note(PAD, E3, vel=0.10, dur=16)

    # Bass: heartbeat slowing
    g[3][0]  = note(DEEP, E2, vel=0.38, dur=4)
    g[3][16] = note(DEEP, E2, vel=0.32, dur=4)
    g[3][36] = note(DEEP, E2, vel=0.25, dur=4)
    g[3][60] = note(DEEP, E2, vel=0.18, dur=6)
    # Bass stops — silence

    return pat("unraveling", steps, g)


def p_stood_up(steps=80):
    """DEFIANCE — 16 steps silence then BRIGHT motif EXPLODES."""
    g = new_grid(steps)

    # 0-15: SILENCE — the breath before

    # Step 16: DETONATION — motif blazes out in BRIGHT
    g[0][16] = note(BRIGHT, E4, vel=0.72, dur=2)
    g[0][20] = note(BRIGHT, G4, vel=0.75, dur=2)
    g[0][24] = note(BRIGHT, A4, vel=0.78, dur=2)
    g[0][28] = note(BRIGHT, B4, vel=0.80, dur=2)
    # Keep climbing — beyond where motif ever went
    g[0][32] = note(BRIGHT, D5, vel=0.80, dur=2)
    g[0][36] = note(BRIGHT, E5, vel=0.80, dur=3)
    g[0][40] = note(BRIGHT, G5, vel=0.80, dur=4)   # HIGHEST NOTE IN FILM

    # Descending resolution — confidence, not relief
    g[0][48] = note(BRIGHT, E5, vel=0.75, dur=3)
    g[0][52] = note(BRIGHT, D5, vel=0.72, dur=3)
    g[0][56] = note(BRIGHT, B4, vel=0.68, dur=3)
    g[0][60] = note(BRIGHT, A4, vel=0.65, dur=3)
    g[0][64] = note(BRIGHT, G4, vel=0.62, dur=3)
    g[0][68] = note(BRIGHT, E4, vel=0.58, dur=4)   # back to root — complete

    # Counter: tight 3-step burst arp from step 16
    arp = [E4, B4, G4, A4]
    for i in range(16, 76, 3):
        g[1][i] = note(ARP_TEX, arp[((i - 16) // 3) % 4],
                       vel=0.42 + ((i - 16) * 0.003), dur=1)

    # Pad: FULL CHORD — explosion of warmth
    g[2][16] = note(PAD, E3, vel=0.48, dur=16)
    g[2][32] = note(PAD, G3, vel=0.50, dur=16)
    g[2][48] = note(PAD, B3, vel=0.48, dur=16)
    g[2][64] = note(PAD, E3, vel=0.45, dur=16)

    # Bass: THUNDERCLAP entrance
    g[3][16] = note(DEEP, E2, vel=0.55, dur=4)
    g[3][24] = note(DEEP, G2, vel=0.52, dur=4)
    g[3][32] = note(DEEP, E2, vel=0.50, dur=4)
    g[3][40] = note(DEEP, B2, vel=0.48, dur=4)
    g[3][48] = note(DEEP, E2, vel=0.50, dur=4)
    g[3][56] = note(DEEP, G2, vel=0.48, dur=4)
    g[3][64] = note(DEEP, E2, vel=0.45, dur=4)

    # Chimes: stars igniting
    g[4][18] = note(CHIME, E5, vel=0.45, dur=1)
    g[4][30] = note(CHIME, B5, vel=0.42, dur=1)
    g[4][42] = note(CHIME, G5, vel=0.40, dur=1)
    g[4][58] = note(CHIME, D5, vel=0.38, dur=1)
    g[4][72] = note(CHIME, E5, vel=0.42, dur=1)

    return pat("stood_up", steps, g)


# ══════════════════════════════════════════════════════════════════════════════
# ACT V: THE RETURN (120-140s) — motif soars home, dissolves to starlight
# Definitive statement. Then the arp fadeout they loved.
# ══════════════════════════════════════════════════════════════════════════════

def p_return_glory(steps=96):
    """Full score triumph — biggest melodic moment, then warm transition."""
    g = new_grid(steps)

    # Lead: definitive motif — complete, warm, fully realized
    g[0][0]  = note(WARM, E4, vel=0.68, dur=3)
    g[0][4]  = note(WARM, G4, vel=0.70, dur=2)
    g[0][8]  = note(WARM, A4, vel=0.72, dur=2)
    g[0][12] = note(WARM, B4, vel=0.75, dur=3)
    g[0][16] = note(WARM, D5, vel=0.78, dur=3)
    g[0][20] = note(WARM, E5, vel=0.80, dur=4)     # --- BIG ARRIVAL

    # Second phrase: singing, lyrical — (E5→D5→E5→G5 → resolve)
    g[0][28] = note(WARM, D5, vel=0.72, dur=3)
    g[0][32] = note(WARM, E5, vel=0.75, dur=2)
    g[0][36] = note(WARM, G5, vel=0.78, dur=4)     # soaring peak
    g[0][42] = note(WARM, E5, vel=0.72, dur=3)
    g[0][48] = note(WARM, D5, vel=0.68, dur=3)
    g[0][52] = note(WARM, B4, vel=0.65, dur=3)

    # Third phrase: stepping down — the boy becomes the man
    g[0][60] = note(WARM, E5, vel=0.68, dur=3)
    g[0][64] = note(WARM, D5, vel=0.62, dur=3)
    g[0][68] = note(WARM, B4, vel=0.58, dur=3)
    g[0][72] = note(WARM, A4, vel=0.55, dur=3)

    # 'She was always there' — warm resolve, fading to transition
    g[0][78] = note(WARM, E4, vel=0.52, dur=4)
    g[0][84] = note(WARM, G4, vel=0.48, dur=3)
    g[0][88] = note(WARM, B4, vel=0.45, dur=4)
    g[0][94] = note(WARM, E4, vel=0.42, dur=2)     # home — settles

    # Counter: becoming the arp — transitioning to fadeout
    arp_notes = [E4, B4, G4, A4]
    for i in range(0, 64, 2):
        g[1][i] = note(ARP_TEX, arp_notes[(i // 2) % 4], vel=0.40, dur=1)
    # Slower in warm section
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
        p_starfield(96),        # 0: Act I — void wakes, motif emerges (11.4s)
        p_cosmic_grief(128),    # 1: Act I — she let go, grief + resilience (15.2s)
        p_search_begins(80),    # 2: Act I→II — quickening, bass enters (9.5s)
        p_four_gifts(176),      # 3: Act II — 4 gifts, full bloom (21.0s)
        p_labyrinth(128),       # 4: Act III — dark drive, syncopated (15.2s)
        p_thread_hope(96),      # 5: Act III — DARK→WARM crossover (11.4s)
        p_unraveling(112),      # 6: Act IV — things break, silence (13.3s)
        p_stood_up(80),         # 7: Act IV — DEFIANCE! (9.5s)
        p_return_glory(96),     # 8: Act V — full score triumph (11.4s)
        p_fadeout(128),         # 9: Act V — THE ENDING they loved (15.2s)
        p_silence(32),          # 10: clean tail (3.8s)
    ]

    sequence = list(range(len(patterns)))

    total_steps = sum(p.num_steps for p in patterns)
    duration_s = total_steps * 60.0 / (BPM * SPB)
    print(f"Melody v4: {len(patterns)} patterns, {total_steps} steps, "
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
"""
ChipForge FILM SCORE v4 for core_fable — melodic journey soundtrack.

Enhanced from v3: more singable melodies, recurring journey motif (E→G→A→B)
that evolves across acts, stronger rhythmic momentum, upbeat gift/journey feel.
Preserved: the arp-to-starlight fadeout ending.

Key: E natural minor (E F# G A B C D)
BPM: 126
Duration target: ~141s (covers 140s film)

Film arc:
  Act I   (0-35s):   Cosmic solitude — journey motif emerges from void
  Act II  (35-70s):  Wonder & gifts — motif blooms, rhythmic pulse builds
  Act III (70-100s): Labyrinth — driving determination, motif syncopated
  Act IV  (100-120s): Unraveling — motif fragments → blazing defiance
  Act V   (120-140s): The Return — motif soars home, dissolves to starlight

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
