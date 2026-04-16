"""Core Fable Score — 300-second film score for 'The Boy Who Mapped the Maze'.

5-minute emotionally synced score in E natural minor:
  Act I   (0–60s)    → mist, wound, searching, purpose: lonely origin → determination
  Act II  (60–130s)  → gifts dawn, lantern, mirror, hammer, chain, carrying: warm discovery
  Act III (130–180s) → labyrinth, thread, mapping, confident: cautious → assured
  Act IV  (180–240s) → walls shift, fraying, crumbling, dark, stood up: loss → endurance
  Act V   (240–300s) → stars dying, empty hands, final walk, void: cosmic indifference

BPM 84, E natural minor, 7 channels, 1680 steps = 300.0 seconds.

Pattern step totals:
  Act I:   32 + 128 + 128 + 48           = 336 steps  (60.0s)
  Act II:  128 + 128 + 64 + 72           = 392 steps  (70.0s)
  Act III: 128 + 128 + 24                = 280 steps  (50.0s)
  Act IV:  128 + 128 + 80                = 336 steps  (60.0s)
  Act V:   128 + 128 + 80                = 336 steps  (60.0s)
  Total:   336 + 392 + 280 + 336 + 336   = 1680 steps (300.0s)
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 84
SPB = 4
BAR = 16

# --- MIDI note constants (E natural minor) ---
E2, Fs2, G2, A2, B2 = 40, 42, 43, 45, 47
C3, D3, E3, Fs3, G3, A3, B3 = 48, 50, 52, 54, 55, 57, 59
C4, D4, E4, Fs4, G4, A4, B4 = 60, 62, 64, 66, 67, 69, 71
C5, D5, E5 = 72, 74, 76

# --- Instruments ---
PAD  = "pad_lush"
PAD2 = "sine_pad"
BASS = "bass_growl"
LEAD = "saw_filtered"
DARK = "saw_dark"
ARP  = "pulse_warm"
BELL = "gb_bell_wave"

CH = 7  # pad_root, pad_harm, bass, lead, counter, arp, bell


def n(inst: str, midi: int, vel: float = 0.65, dur: int = 4) -> NoteEvent:
    """Create a note event from MIDI number."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 2), instrument=inst)


def g(steps: int) -> list[list[NoteEvent | None]]:
    """Create empty grid."""
    return [[None] * steps for _ in range(CH)]


# --- Helpers to reduce repetition ---

def pad_chord(gr: list, step: int, root: int, harm: int,
              vel: float = 0.48, dur: int = 16) -> None:
    """Set pad root + harmony at step."""
    gr[0][step] = n(PAD, root, vel, dur)
    gr[1][step] = n(PAD2, harm, vel - 0.10, dur)


def bass_note(gr: list, step: int, note: int,
              vel: float = 0.48, dur: int = 8) -> None:
    gr[2][step] = n(BASS, note, vel, dur)


# ============================================================
#  ACT I: THE BOY (0–60s, 336 steps)
#  Sparse → aching → walking → determined
# ============================================================

def p_mist() -> Pattern:
    """P0: Ethereal pad wash. 2 bars = 32 steps. [Opening titles]"""
    gr = g(32)
    pad_chord(gr, 0, E3, B3, 0.42, 16)
    pad_chord(gr, 16, E3, B3, 0.38, 16)
    gr[6][12] = n(BELL, E5, 0.22, 4)
    gr[6][28] = n(BELL, B4, 0.18, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=32,
                   num_channels=CH, bpm=BPM, name="mist")


def p_wound_search() -> Pattern:
    """P1: 8 bars = 128 steps. [Boy alone → two women → stumble → rise → searching]
    Dark, aching. Em → Am → Bm → Em → Am → Em → C → Em."""
    gr = g(128)
    # Bars 1-2: Boy alone — low pad, lonely bell
    pad_chord(gr, 0, E3, G3, 0.45, 16)
    pad_chord(gr, 16, E3, G3, 0.42, 16)
    gr[4][4]  = n(DARK, B3, 0.35, 8)    # lonely counter voice
    gr[4][16] = n(DARK, A3, 0.33, 8)
    gr[6][0]  = n(BELL, B4, 0.20, 6)
    gr[6][20] = n(BELL, G4, 0.18, 6)

    # Bars 3-4: Two women — tension rises. Am → Bm
    pad_chord(gr, 32, A2, C4, 0.48, 16)
    pad_chord(gr, 48, B2, D4, 0.50, 16)
    bass_note(gr, 32, A2, 0.38, 12)
    bass_note(gr, 48, B2, 0.42, 12)
    gr[4][32] = n(DARK, E3, 0.38, 6)
    gr[4][40] = n(DARK, G3, 0.40, 6)
    gr[4][48] = n(DARK, A3, 0.42, 6)
    gr[4][56] = n(DARK, B3, 0.44, 6)
    gr[6][36] = n(BELL, G4, 0.20, 4)   # cold — the letting go
    gr[6][52] = n(BELL, E5, 0.22, 4)   # warm — the holding on

    # Bars 5-6: Stumble, fall. Em dark → Am ache
    pad_chord(gr, 64, E3, B3, 0.50, 16)
    pad_chord(gr, 80, A2, C4, 0.52, 16)
    bass_note(gr, 64, E2, 0.42, 8)
    bass_note(gr, 76, A2, 0.45, 8)
    gr[3][68] = n(LEAD, E4, 0.42, 4)    # first lead — aching
    gr[3][72] = n(LEAD, D4, 0.45, 4)
    gr[3][76] = n(LEAD, C4, 0.42, 6)
    gr[3][84] = n(LEAD, B3, 0.40, 8)    # falls
    gr[4][64] = n(DARK, G3, 0.42, 8)
    gr[4][80] = n(DARK, E3, 0.38, 12)

    # Bars 7-8: Rise. Em → hope rising
    pad_chord(gr, 96, E3, B3, 0.48, 16)
    pad_chord(gr, 112, E3, G3, 0.46, 16)
    bass_note(gr, 96, E3, 0.44, 8)
    bass_note(gr, 104, E3, 0.40, 8)
    bass_note(gr, 112, E3, 0.42, 8)
    # Lead: rising — "So he searched"
    gr[3][96]  = n(LEAD, E4, 0.48, 4)
    gr[3][100] = n(LEAD, G4, 0.50, 4)
    gr[3][104] = n(LEAD, A4, 0.52, 4)
    gr[3][108] = n(LEAD, B4, 0.50, 8)
    gr[3][116] = n(LEAD, A4, 0.48, 4)
    gr[3][120] = n(LEAD, G4, 0.46, 4)
    gr[3][124] = n(LEAD, E4, 0.44, 4)
    gr[6][96]  = n(BELL, E5, 0.22, 4)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="wound_search")


def p_purpose() -> Pattern:
    """P2: 8 bars = 128 steps. [Walking with growing purpose into the unknown]
    Builds momentum. Em → G → C → Em → G → Am → Em → Em.
    Bass enters steady, arp sparkles appear, lead theme establishes."""
    gr = g(128)
    # Chord progression: two 4-bar cycles
    chords = [(E3, B3), (G3, D4), (C3, G3), (E3, B3),
              (G3, D4), (A3, E4), (E3, B3), (E3, G3)]
    for i, (root, harm) in enumerate(chords):
        pad_chord(gr, i * 16, root, harm, 0.48, 16)

    # Bass: steady pulse, building confidence
    bass_roots = [E3, G2, C3, E3, G2, A2, E3, E3]
    for i, br in enumerate(bass_roots):
        bass_note(gr, i * 16, br, 0.44 + i * 0.005, 8)
        bass_note(gr, i * 16 + 8, br, 0.40 + i * 0.005, 8)

    # Lead: THE THEME — ascending reach, falling home (bars 3-4)
    gr[3][32] = n(LEAD, E4, 0.50, 4)
    gr[3][36] = n(LEAD, G4, 0.52, 4)
    gr[3][40] = n(LEAD, A4, 0.55, 4)
    gr[3][44] = n(LEAD, B4, 0.52, 4)
    gr[3][48] = n(LEAD, A4, 0.50, 4)
    gr[3][52] = n(LEAD, G4, 0.48, 4)
    gr[3][56] = n(LEAD, E4, 0.46, 8)
    # Lead: theme variation (bars 7-8) — reaches higher
    gr[3][96]  = n(LEAD, G4, 0.52, 4)
    gr[3][100] = n(LEAD, A4, 0.55, 4)
    gr[3][104] = n(LEAD, B4, 0.58, 4)
    gr[3][108] = n(LEAD, D5, 0.55, 4)
    gr[3][112] = n(LEAD, B4, 0.52, 4)
    gr[3][116] = n(LEAD, A4, 0.50, 4)
    gr[3][120] = n(LEAD, G4, 0.48, 4)
    gr[3][124] = n(LEAD, E4, 0.45, 4)

    # Counter: answering phrases
    gr[4][36] = n(DARK, B3, 0.38, 6)
    gr[4][44] = n(DARK, A3, 0.36, 8)
    gr[4][56] = n(DARK, G3, 0.38, 8)
    gr[4][100] = n(DARK, D4, 0.38, 6)
    gr[4][108] = n(DARK, B3, 0.36, 8)

    # Arp: sparse sparks appearing (bars 5-8)
    arp_sparks = [(68, E4), (76, G4), (84, B4), (92, A4),
                  (104, E4), (112, B4), (120, G4)]
    for step, note in arp_sparks:
        gr[5][step] = n(ARP, note, 0.28, 3)

    # Bell accents
    gr[6][32] = n(BELL, E5, 0.22, 4)
    gr[6][96] = n(BELL, G4, 0.20, 4)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="purpose")


def p_crossing() -> Pattern:
    """P3: 3 bars = 48 steps. [Transition pad into Act II — warmth arriving]"""
    gr = g(48)
    pad_chord(gr, 0, E3, B3, 0.48, 16)
    pad_chord(gr, 16, C3, G3, 0.46, 16)
    pad_chord(gr, 32, E3, B3, 0.44, 16)
    bass_note(gr, 0, E3, 0.40, 12)
    bass_note(gr, 32, E3, 0.38, 12)
    gr[6][8]  = n(BELL, E5, 0.20, 4)
    gr[6][24] = n(BELL, G4, 0.18, 4)
    gr[6][40] = n(BELL, B4, 0.22, 4)   # warm bell — hope arriving
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=48,
                   num_channels=CH, bpm=BPM, name="crossing")


# ============================================================
#  ACT II: THE FOUR GIFTS (60–130s, 392 steps)
#  Warm discovery → each gift adds texture → carrying everything
# ============================================================

def p_gifts_warm() -> Pattern:
    """P4: 8 bars = 128 steps. [Lantern discovery → mirror confrontation]
    Warmth arrives. Full arrangement starts building.
    Em → C → Am → Em → Em → G → C → Em."""
    gr = g(128)
    chords = [(E3, B3), (C3, G3), (A3, E4), (E3, B3),
              (E3, B3), (G3, D4), (C3, G3), (E3, B3)]
    for i, (root, harm) in enumerate(chords):
        pad_chord(gr, i * 16, root, harm, 0.50, 16)

    # Bass: gentle, grounding
    bass_r = [E3, C3, A2, E3, E3, G2, C3, E3]
    for i, br in enumerate(bass_r):
        bass_note(gr, i * 16, br, 0.44, 8)
        if i >= 4:
            bass_note(gr, i * 16 + 8, br, 0.40, 8)

    # Lead: LANTERN theme — curiosity, burning question (bars 1-4)
    gr[3][0]  = n(LEAD, E4, 0.50, 4)
    gr[3][4]  = n(LEAD, G4, 0.52, 4)
    gr[3][8]  = n(LEAD, A4, 0.55, 4)
    gr[3][12] = n(LEAD, B4, 0.55, 4)
    gr[3][16] = n(LEAD, G4, 0.52, 4)
    gr[3][20] = n(LEAD, A4, 0.55, 6)
    gr[3][28] = n(LEAD, E4, 0.48, 4)
    gr[3][32] = n(LEAD, A4, 0.52, 4)
    gr[3][36] = n(LEAD, G4, 0.50, 4)
    gr[3][40] = n(LEAD, E4, 0.48, 8)
    gr[3][48] = n(LEAD, B4, 0.50, 4)
    gr[3][52] = n(LEAD, A4, 0.48, 4)
    gr[3][56] = n(LEAD, G4, 0.46, 8)

    # Lead: MIRROR theme — call and response (bars 5-8)
    gr[3][64] = n(LEAD, E4, 0.52, 4)    # call
    gr[3][68] = n(LEAD, G4, 0.55, 4)
    gr[3][72] = n(LEAD, A4, 0.58, 8)    # holds
    gr[3][96] = n(LEAD, A4, 0.55, 4)    # responding
    gr[3][100] = n(LEAD, B4, 0.58, 4)
    gr[3][104] = n(LEAD, D5, 0.60, 4)
    gr[3][108] = n(LEAD, B4, 0.55, 4)
    gr[3][112] = n(LEAD, G4, 0.52, 4)
    gr[3][116] = n(LEAD, E4, 0.48, 8)

    # Counter: mirror response (descending where lead ascends)
    gr[4][80] = n(DARK, D4, 0.45, 4)
    gr[4][84] = n(DARK, C4, 0.42, 4)
    gr[4][88] = n(DARK, B3, 0.40, 8)    # falls
    gr[4][112] = n(DARK, B4, 0.45, 4)
    gr[4][116] = n(DARK, A4, 0.42, 4)
    gr[4][120] = n(DARK, G4, 0.40, 8)

    # Arp: gentle running (bars 3-8)
    arp_notes = [E4, B4, G4, E5, B4, G4, E4, B3,
                 D4, B4, G4, D5, B4, G4, D4, B3]
    for i, mn in enumerate(arp_notes):
        gr[5][32 + i * 4] = n(ARP, mn, 0.30, 3)
    # Continue arp bars 7-8
    for i in range(8):
        note = [E4, G4, B4, E5, G4, B4, E4, G4][i]
        gr[5][96 + i * 4] = n(ARP, note, 0.28, 3)

    # Bell: duality tones
    gr[6][0]  = n(BELL, E5, 0.24, 4)
    gr[6][32] = n(BELL, G4, 0.20, 4)
    gr[6][64] = n(BELL, E5, 0.22, 4)    # warm
    gr[6][80] = n(BELL, C5, 0.20, 4)    # cool
    gr[6][96] = n(BELL, E5, 0.22, 4)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="gifts_warm")


def p_gifts_build() -> Pattern:
    """P5: 8 bars = 128 steps. [Hammer building → chain weight]
    Full arrangement. Arp running, lead builds then sinks.
    Em → G → C → Em → Am → Em → Bm → Em."""
    gr = g(128)
    chords = [(E3, B3), (G3, D4), (C3, G3), (E3, B3),
              (A3, C4), (E3, B3), (B2, D4), (E3, G3)]
    for i, (root, harm) in enumerate(chords):
        pad_chord(gr, i * 16, root, harm, 0.50, 16)

    # Bass: strong, grounding
    bass_r = [E3, G2, C3, E3, A2, E3, B2, E3]
    for i, br in enumerate(bass_r):
        bass_note(gr, i * 16, br, 0.50, 8)
        bass_note(gr, i * 16 + 8, br, 0.46, 8)

    # Lead: HAMMER theme (bars 1-4) — building, reaching, stacking
    gr[3][0]  = n(LEAD, G4, 0.55, 4)
    gr[3][4]  = n(LEAD, B4, 0.58, 2)
    gr[3][6]  = n(LEAD, A4, 0.55, 2)
    gr[3][8]  = n(LEAD, B4, 0.58, 4)
    gr[3][12] = n(LEAD, D5, 0.60, 4)
    gr[3][16] = n(LEAD, B4, 0.55, 4)
    gr[3][20] = n(LEAD, A4, 0.52, 4)
    gr[3][24] = n(LEAD, G4, 0.50, 8)
    gr[3][32] = n(LEAD, A4, 0.55, 4)
    gr[3][36] = n(LEAD, B4, 0.58, 4)
    gr[3][40] = n(LEAD, E5, 0.60, 4)
    gr[3][44] = n(LEAD, D5, 0.55, 4)
    gr[3][48] = n(LEAD, B4, 0.52, 4)
    gr[3][52] = n(LEAD, G4, 0.48, 4)
    gr[3][56] = n(LEAD, E4, 0.46, 8)

    # Lead: CHAIN theme (bars 5-8) — heavier, sinking, burdened
    gr[3][64] = n(LEAD, E4, 0.50, 6)
    gr[3][72] = n(LEAD, D4, 0.48, 6)
    gr[3][80] = n(LEAD, C4, 0.46, 6)
    gr[3][88] = n(LEAD, B3, 0.44, 8)
    gr[3][96] = n(LEAD, A3, 0.42, 8)
    gr[3][106] = n(LEAD, B3, 0.44, 6)
    gr[3][112] = n(LEAD, E4, 0.46, 8)
    gr[3][120] = n(LEAD, D4, 0.44, 8)

    # Counter: supporting weight
    gr[4][4]  = n(DARK, B3, 0.40, 6)
    gr[4][12] = n(DARK, A3, 0.38, 8)
    gr[4][24] = n(DARK, G3, 0.40, 8)
    gr[4][68] = n(DARK, G3, 0.42, 8)
    gr[4][80] = n(DARK, E3, 0.44, 8)
    gr[4][96] = n(DARK, C4, 0.42, 8)
    gr[4][112] = n(DARK, B3, 0.40, 8)

    # Arp: running through all 8 bars
    full_arp = [E4, B4, G4, E5, B4, G4, E4, B3,
                D4, B4, G4, D5, B4, G4, D4, B3,
                E4, G4, B4, G4, A4, C5, A4, E4,
                B3, D4, Fs4, D4, E4, G4, E4, B3]
    for i, mn in enumerate(full_arp):
        if i < len(full_arp):
            gr[5][i * 4] = n(ARP, mn, 0.32, 3)

    # Bell accents
    gr[6][0]  = n(BELL, E5, 0.24, 4)
    gr[6][32] = n(BELL, G4, 0.22, 4)
    gr[6][64] = n(BELL, C5, 0.20, 4)    # darkens with chain
    gr[6][96] = n(BELL, A4, 0.18, 4)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="gifts_build")


def p_carrying() -> Pattern:
    """P6: 4 bars = 64 steps. [Walking with everything]
    Full, warm, determined. All channels active."""
    gr = g(64)
    chords = [(E3, B3), (G3, D4), (C3, G3), (E3, B3)]
    for i, (root, harm) in enumerate(chords):
        pad_chord(gr, i * 16, root, harm, 0.50, 16)

    bass_r = [E3, G2, C3, E3]
    for i, br in enumerate(bass_r):
        bass_note(gr, i * 16, br, 0.50, 8)
        bass_note(gr, i * 16 + 8, br, 0.46, 8)

    # Lead: main theme confident version
    gr[3][0]  = n(LEAD, E4, 0.55, 4)
    gr[3][4]  = n(LEAD, G4, 0.58, 4)
    gr[3][8]  = n(LEAD, A4, 0.60, 4)
    gr[3][12] = n(LEAD, B4, 0.58, 4)
    gr[3][16] = n(LEAD, D5, 0.60, 4)
    gr[3][20] = n(LEAD, B4, 0.55, 4)
    gr[3][24] = n(LEAD, A4, 0.52, 4)
    gr[3][28] = n(LEAD, G4, 0.50, 4)
    gr[3][32] = n(LEAD, A4, 0.55, 4)
    gr[3][36] = n(LEAD, B4, 0.58, 4)
    gr[3][40] = n(LEAD, E5, 0.62, 4)
    gr[3][44] = n(LEAD, D5, 0.58, 4)
    gr[3][48] = n(LEAD, B4, 0.55, 4)
    gr[3][52] = n(LEAD, A4, 0.52, 4)
    gr[3][56] = n(LEAD, G4, 0.50, 4)
    gr[3][60] = n(LEAD, E4, 0.48, 4)

    # Counter: warm answering
    gr[4][4]  = n(DARK, B3, 0.40, 6)
    gr[4][12] = n(DARK, A3, 0.38, 6)
    gr[4][36] = n(DARK, G3, 0.40, 6)
    gr[4][48] = n(DARK, A3, 0.38, 8)

    # Full arp
    arp = [E4, B4, G4, E5, B4, G4, E4, B3,
           D4, B4, G4, D5, B4, G4, D4, B3]
    for i, mn in enumerate(arp):
        gr[5][i * 4] = n(ARP, mn, 0.32, 3)

    gr[6][0]  = n(BELL, E5, 0.24, 4)
    gr[6][32] = n(BELL, G4, 0.22, 4)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="carrying")


def p_carrying_bridge() -> Pattern:
    """P7: 4.5 bars = 72 steps. [Bridge to labyrinth — momentum → caution]
    Starts warm, arp thins, lead drops octave. Arriving at the maze."""
    gr = g(72)
    pad_chord(gr, 0, E3, B3, 0.48, 16)
    pad_chord(gr, 16, G3, D4, 0.46, 16)
    pad_chord(gr, 32, A3, E4, 0.44, 16)
    pad_chord(gr, 48, E3, B3, 0.42, 16)
    gr[1][64] = n(PAD2, G3, 0.35, 8)    # thinning

    bass_note(gr, 0, E3, 0.46, 12)
    bass_note(gr, 16, G2, 0.44, 12)
    bass_note(gr, 32, A2, 0.42, 12)
    bass_note(gr, 48, E3, 0.40, 16)

    # Lead: descending, slowing — approaching the maze
    gr[3][0]  = n(LEAD, B4, 0.52, 4)
    gr[3][4]  = n(LEAD, A4, 0.50, 4)
    gr[3][8]  = n(LEAD, G4, 0.48, 8)
    gr[3][16] = n(LEAD, E4, 0.46, 4)
    gr[3][20] = n(LEAD, D4, 0.44, 4)
    gr[3][24] = n(LEAD, E4, 0.42, 8)
    gr[3][48] = n(LEAD, G4, 0.40, 6)
    gr[3][56] = n(LEAD, E4, 0.38, 8)

    # Arp: thinning out
    for i, mn in enumerate([E4, G4, B4, E5]):
        gr[5][i * 4] = n(ARP, mn, 0.30, 3)
    gr[5][32] = n(ARP, E4, 0.25, 3)
    gr[5][40] = n(ARP, B4, 0.22, 3)

    gr[6][16] = n(BELL, G4, 0.18, 4)
    gr[6][48] = n(BELL, E5, 0.16, 4)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=72,
                   num_channels=CH, bpm=BPM, name="carrying_bridge")


# ============================================================
#  ACT III: THE LABYRINTH (130–180s, 280 steps)
#  Cautious → thread → mapping → confident → still
# ============================================================

def p_labyrinth() -> Pattern:
    """P8: 8 bars = 128 steps. [Enter maze → find thread → begin mapping]
    Mysterious. Em → D → C → Bm → Em → C → G → Em."""
    gr = g(128)
    chords = [(E3, B3), (D3, A3), (C3, G3), (B2, Fs3),
              (E3, G3), (C3, E4), (G3, B3), (E3, B3)]
    for i, (root, harm) in enumerate(chords):
        pad_chord(gr, i * 16, root, harm, 0.46, 16)

    # Bass: deliberate, mapping rhythm
    bass_r = [E3, D3, C3, B2, E3, C3, G2, E3]
    for i, br in enumerate(bass_r):
        bass_note(gr, i * 16, br, 0.44, 12)

    # Lead: cautious probing → thread discovery → following
    # Bars 1-2: cautious
    gr[3][4]  = n(LEAD, E4, 0.42, 3)
    gr[3][12] = n(LEAD, D4, 0.40, 3)
    gr[3][20] = n(LEAD, C4, 0.38, 4)
    gr[3][28] = n(LEAD, B3, 0.36, 4)
    # Bars 3-4: thread found — more confident
    gr[3][32] = n(LEAD, E4, 0.48, 4)
    gr[3][36] = n(LEAD, G4, 0.50, 4)
    gr[3][40] = n(LEAD, A4, 0.52, 4)
    gr[3][44] = n(LEAD, G4, 0.48, 4)
    gr[3][48] = n(LEAD, B4, 0.50, 4)
    gr[3][52] = n(LEAD, A4, 0.48, 4)
    gr[3][56] = n(LEAD, G4, 0.46, 4)
    gr[3][60] = n(LEAD, E4, 0.44, 4)
    # Bars 5-6: mapping — purposeful
    gr[3][64] = n(LEAD, G4, 0.50, 4)
    gr[3][68] = n(LEAD, A4, 0.52, 4)
    gr[3][72] = n(LEAD, B4, 0.55, 4)
    gr[3][76] = n(LEAD, D5, 0.52, 4)
    gr[3][80] = n(LEAD, B4, 0.50, 4)
    gr[3][84] = n(LEAD, A4, 0.48, 4)
    gr[3][88] = n(LEAD, G4, 0.46, 8)
    # Bars 7-8: reaching stride
    gr[3][96]  = n(LEAD, A4, 0.52, 4)
    gr[3][100] = n(LEAD, B4, 0.55, 4)
    gr[3][104] = n(LEAD, E5, 0.58, 4)
    gr[3][108] = n(LEAD, D5, 0.55, 4)
    gr[3][112] = n(LEAD, B4, 0.52, 4)
    gr[3][116] = n(LEAD, G4, 0.50, 4)
    gr[3][120] = n(LEAD, E4, 0.48, 4)
    gr[3][124] = n(LEAD, D4, 0.46, 4)

    # Counter: echoing, mapping
    gr[4][8]  = n(DARK, B3, 0.35, 6)
    gr[4][24] = n(DARK, A3, 0.33, 6)
    gr[4][68] = n(DARK, E4, 0.38, 4)
    gr[4][76] = n(DARK, D4, 0.36, 4)
    gr[4][88] = n(DARK, B3, 0.35, 8)
    gr[4][104] = n(DARK, A3, 0.38, 6)
    gr[4][116] = n(DARK, B3, 0.36, 8)

    # Arp: building steadily from bar 3
    for i in range(16):
        notes = [E4, G4, B4, E5, G4, B4, E4, B3,
                 D4, B4, G4, D5, B4, G4, D4, B3]
        gr[5][32 + i * 4] = n(ARP, notes[i], 0.26 + i * 0.005, 3)

    gr[6][0]  = n(BELL, B4, 0.20, 4)
    gr[6][32] = n(BELL, E5, 0.22, 4)
    gr[6][64] = n(BELL, G4, 0.20, 4)
    gr[6][96] = n(BELL, B4, 0.22, 4)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="labyrinth")


def p_mapping_pride() -> Pattern:
    """P9: 8 bars = 128 steps. [Confident mapping → 'this was enough']
    Brightest moment of the film. Full arrangement, theme at peak.
    Em → G → Am → Em → C → G → Am → Em."""
    gr = g(128)
    chords = [(E3, B3), (G3, D4), (A3, E4), (E3, B3),
              (C3, G3), (G3, D4), (A3, E4), (E3, B3)]
    for i, (root, harm) in enumerate(chords):
        pad_chord(gr, i * 16, root, harm, 0.52, 16)

    bass_r = [E3, G2, A2, E3, C3, G2, A2, E3]
    for i, br in enumerate(bass_r):
        bass_note(gr, i * 16, br, 0.50, 8)
        bass_note(gr, i * 16 + 8, br, 0.46, 8)

    # Lead: PEAK THEME — highest, most confident
    gr[3][0]  = n(LEAD, B4, 0.58, 4)
    gr[3][4]  = n(LEAD, D5, 0.60, 4)
    gr[3][8]  = n(LEAD, E5, 0.62, 4)
    gr[3][12] = n(LEAD, D5, 0.58, 4)
    gr[3][16] = n(LEAD, B4, 0.55, 4)
    gr[3][20] = n(LEAD, G4, 0.52, 4)
    gr[3][24] = n(LEAD, A4, 0.55, 8)
    gr[3][32] = n(LEAD, B4, 0.58, 4)
    gr[3][36] = n(LEAD, D5, 0.60, 4)
    gr[3][40] = n(LEAD, E5, 0.65, 4)
    gr[3][44] = n(LEAD, D5, 0.60, 4)
    gr[3][48] = n(LEAD, B4, 0.55, 8)
    gr[3][56] = n(LEAD, A4, 0.52, 8)
    # Bars 5-8: "this was enough" — settling, satisfied
    gr[3][64] = n(LEAD, G4, 0.52, 4)
    gr[3][68] = n(LEAD, A4, 0.55, 4)
    gr[3][72] = n(LEAD, B4, 0.52, 8)
    gr[3][80] = n(LEAD, A4, 0.50, 4)
    gr[3][84] = n(LEAD, G4, 0.48, 4)
    gr[3][88] = n(LEAD, E4, 0.45, 8)
    gr[3][96] = n(LEAD, G4, 0.48, 4)
    gr[3][100] = n(LEAD, A4, 0.50, 4)
    gr[3][104] = n(LEAD, B4, 0.52, 4)
    gr[3][108] = n(LEAD, A4, 0.48, 4)
    gr[3][112] = n(LEAD, G4, 0.46, 4)
    gr[3][116] = n(LEAD, E4, 0.44, 8)

    # Counter: warm duet
    gr[4][8]  = n(DARK, G3, 0.42, 6)
    gr[4][20] = n(DARK, D4, 0.40, 6)
    gr[4][40] = n(DARK, A3, 0.42, 6)
    gr[4][56] = n(DARK, G3, 0.40, 8)
    gr[4][72] = n(DARK, D4, 0.38, 6)
    gr[4][88] = n(DARK, B3, 0.36, 8)
    gr[4][104] = n(DARK, G3, 0.38, 6)
    gr[4][116] = n(DARK, E3, 0.36, 8)

    # Full arp
    for i in range(32):
        notes = [E4, B4, G4, E5] * 8
        gr[5][i * 4] = n(ARP, notes[i], 0.32, 3)

    gr[6][0]  = n(BELL, E5, 0.26, 4)
    gr[6][32] = n(BELL, G4, 0.24, 4)
    gr[6][64] = n(BELL, B4, 0.22, 4)
    gr[6][96] = n(BELL, E5, 0.24, 4)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="mapping_pride")


def p_stillness() -> Pattern:
    """P10: 1.5 bars = 24 steps. [Moment of peace before the storm]
    Pad only. Breathing space."""
    gr = g(24)
    pad_chord(gr, 0, E3, B3, 0.42, 16)
    gr[1][8] = n(PAD2, G3, 0.30, 12)
    gr[6][4] = n(BELL, E5, 0.18, 6)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=24,
                   num_channels=CH, bpm=BPM, name="stillness")


# ============================================================
#  ACT IV: THE UNRAVELING (180–240s, 336 steps)
#  Walls shift → thread frays → everything crumbles → rises anyway
# ============================================================

def p_unraveling() -> Pattern:
    """P11: 8 bars = 128 steps. [Walls shift → thread frays → blocks crumble]
    Dark tension returns. Em → Am → Bdim → Em → Am → B → C → Em.
    Everything comes undone. Not from neglect — from time."""
    gr = g(128)
    chords = [(E3, B3), (A2, C4), (B2, D4), (E3, G3),
              (A3, C4), (B2, Fs3), (C3, E4), (E3, B3)]
    for i, (root, harm) in enumerate(chords):
        v = 0.52 + i * 0.005
        pad_chord(gr, i * 16, root, harm, v, 16)

    bass_r = [E3, A2, B2, E3, A2, B2, C3, E3]
    for i, br in enumerate(bass_r):
        bass_note(gr, i * 16, br, 0.50 + i * 0.005, 8)
        bass_note(gr, i * 16 + 8, br + 7, 0.40, 4)

    # Lead: fragmented, searching, losing grip
    # Bars 1-2: "The universe is patient" — ominous calm
    gr[3][4]  = n(LEAD, E4, 0.48, 3)
    gr[3][10] = n(LEAD, D4, 0.46, 3)
    gr[3][16] = n(LEAD, C4, 0.44, 4)
    gr[3][24] = n(LEAD, B3, 0.42, 6)
    # Bars 3-4: "Walls shifted" — jarring intervals
    gr[3][32] = n(LEAD, Fs4, 0.52, 3)
    gr[3][36] = n(LEAD, E4, 0.48, 3)
    gr[3][40] = n(LEAD, D4, 0.46, 4)
    gr[3][48] = n(LEAD, B3, 0.44, 4)
    gr[3][52] = n(LEAD, C4, 0.42, 8)
    # Bars 5-6: "Thread began to fray" — descending chromatically
    gr[3][64] = n(LEAD, A4, 0.50, 4)
    gr[3][68] = n(LEAD, G4, 0.48, 4)
    gr[3][72] = n(LEAD, Fs4, 0.46, 4)
    gr[3][76] = n(LEAD, E4, 0.44, 4)
    gr[3][80] = n(LEAD, D4, 0.42, 4)
    gr[3][84] = n(LEAD, C4, 0.40, 4)
    gr[3][88] = n(LEAD, B3, 0.38, 8)
    # Bars 7-8: "Things he built crumbled" — fragments
    gr[3][96]  = n(LEAD, E4, 0.45, 3)
    gr[3][100] = n(LEAD, D4, 0.42, 2)
    gr[3][104] = n(LEAD, B3, 0.40, 4)
    gr[3][112] = n(LEAD, G3, 0.38, 4)
    gr[3][120] = n(LEAD, E4, 0.35, 8)

    # Counter: descending weight
    gr[4][0]  = n(DARK, E4, 0.45, 4)
    gr[4][4]  = n(DARK, D4, 0.43, 4)
    gr[4][8]  = n(DARK, C4, 0.42, 4)
    gr[4][12] = n(DARK, B3, 0.40, 4)
    gr[4][32] = n(DARK, Fs4, 0.45, 4)
    gr[4][36] = n(DARK, E4, 0.43, 4)
    gr[4][40] = n(DARK, D4, 0.42, 4)
    gr[4][44] = n(DARK, B3, 0.40, 8)
    gr[4][64] = n(DARK, G3, 0.42, 8)
    gr[4][80] = n(DARK, E3, 0.40, 8)
    gr[4][96] = n(DARK, D4, 0.38, 8)
    gr[4][112] = n(DARK, B3, 0.36, 8)

    # Arp: restless, erratic (skipping steps)
    arp_r = [E4, G4, B4, G4, A4, C5, A4, E4,
             B3, D4, Fs4, D4, E4, G4, E4, B3]
    for i, mn in enumerate(arp_r):
        gr[5][i * 4 + 32] = n(ARP, mn, 0.30, 2)  # shorter, more urgent

    gr[6][0]  = n(BELL, C5, 0.22, 4)   # cold
    gr[6][32] = n(BELL, A4, 0.20, 4)
    gr[6][64] = n(BELL, Fs4, 0.18, 4)  # darker
    gr[6][96] = n(BELL, D4, 0.16, 4)   # lowest

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="unraveling")


def p_darkness() -> Pattern:
    """P12: 8 bars = 128 steps. [Lantern dims → chain holds → despair]
    Near-silence in places. The deepest low.
    Em → Am → Em → Bm → Am → Em → Em → Em."""
    gr = g(128)
    chords = [(E3, G3), (A2, C4), (E3, B3), (B2, D4),
              (A2, C4), (E3, G3), (E3, B3), (E3, G3)]
    for i, (root, harm) in enumerate(chords):
        v = max(0.35, 0.50 - i * 0.015)
        pad_chord(gr, i * 16, root, harm, v, 16)

    # Bass: sparse, heavy
    bass_note(gr, 0, E2, 0.45, 16)
    bass_note(gr, 32, E2, 0.42, 16)
    bass_note(gr, 64, A2, 0.44, 16)
    bass_note(gr, 96, E2, 0.40, 16)

    # Lead: barely there — "the lantern dimmed"
    gr[3][0]  = n(LEAD, E4, 0.40, 8)
    gr[3][12] = n(LEAD, D4, 0.38, 4)
    gr[3][16] = n(LEAD, C4, 0.36, 8)
    gr[3][32] = n(LEAD, B3, 0.34, 8)
    # Bars 3-4: "The dark was deeper" — lower, quieter
    gr[3][48] = n(LEAD, A3, 0.32, 8)
    gr[3][60] = n(LEAD, E3, 0.30, 4)
    # Bars 5-6: "The chain held" — single repeated note, stuck
    gr[3][64] = n(LEAD, E4, 0.35, 6)
    gr[3][72] = n(LEAD, E4, 0.33, 6)
    gr[3][80] = n(LEAD, E4, 0.30, 6)
    # Bars 7-8: near silence
    gr[3][112] = n(LEAD, E4, 0.28, 8)

    # Counter: heavy, anchoring
    gr[4][0]  = n(DARK, G3, 0.40, 12)
    gr[4][16] = n(DARK, E3, 0.38, 12)
    gr[4][48] = n(DARK, D3, 0.36, 12)
    gr[4][64] = n(DARK, C3, 0.38, 12)
    gr[4][96] = n(DARK, B2, 0.35, 16)

    # No arp — stripped bare

    # Bell: mournful, sparse
    gr[6][8]  = n(BELL, C5, 0.16, 6)
    gr[6][40] = n(BELL, A4, 0.14, 6)
    gr[6][72] = n(BELL, G4, 0.12, 6)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="darkness")


def p_stood_up() -> Pattern:
    """P13: 5 bars = 80 steps. ['He stood up anyway.']
    Rises from deepest point. Lead climbs from E3 to E4.
    The most important moment in the score."""
    gr = g(80)
    # Bars 1-2: still down, minimal
    pad_chord(gr, 0, E3, B3, 0.38, 16)
    pad_chord(gr, 16, E3, G3, 0.40, 16)
    bass_note(gr, 0, E2, 0.38, 16)
    bass_note(gr, 16, E2, 0.40, 16)

    # Bars 3-5: RISING — everything gradually returns
    pad_chord(gr, 32, E3, B3, 0.44, 16)
    pad_chord(gr, 48, G3, D4, 0.46, 16)
    pad_chord(gr, 64, E3, B3, 0.48, 16)
    bass_note(gr, 32, E3, 0.42, 8)
    bass_note(gr, 40, E3, 0.44, 8)
    bass_note(gr, 48, G2, 0.46, 8)
    bass_note(gr, 56, G2, 0.44, 8)
    bass_note(gr, 64, E3, 0.48, 8)
    bass_note(gr, 72, E3, 0.46, 8)

    # Lead: THE RISING — ascending from nothing
    gr[3][8]  = n(LEAD, E3, 0.30, 4)    # barely audible
    gr[3][16] = n(LEAD, G3, 0.34, 4)
    gr[3][24] = n(LEAD, A3, 0.38, 4)
    gr[3][32] = n(LEAD, B3, 0.42, 4)
    gr[3][36] = n(LEAD, C4, 0.44, 4)
    gr[3][40] = n(LEAD, D4, 0.46, 4)
    gr[3][44] = n(LEAD, E4, 0.48, 4)    # arrives at E4
    gr[3][48] = n(LEAD, G4, 0.50, 4)
    gr[3][52] = n(LEAD, A4, 0.52, 4)
    gr[3][56] = n(LEAD, B4, 0.55, 4)    # theme motif returns
    gr[3][60] = n(LEAD, A4, 0.52, 4)
    gr[3][64] = n(LEAD, G4, 0.50, 4)
    gr[3][68] = n(LEAD, E4, 0.48, 4)
    gr[3][72] = n(LEAD, D4, 0.46, 8)

    # Counter: supporting the rise
    gr[4][32] = n(DARK, G3, 0.35, 8)
    gr[4][48] = n(DARK, D4, 0.38, 8)
    gr[4][64] = n(DARK, B3, 0.36, 8)

    # Arp returns faintly
    for i, mn in enumerate([E4, G4, B4, E5]):
        gr[5][48 + i * 4] = n(ARP, mn, 0.22, 3)
    for i, mn in enumerate([E4, G4, B4, E5]):
        gr[5][64 + i * 4] = n(ARP, mn, 0.25, 3)

    gr[6][64] = n(BELL, E5, 0.20, 4)   # hope bell

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=80,
                   num_channels=CH, bpm=BPM, name="stood_up")


# ============================================================
#  ACT V: THE UNIVERSE WINS (240–300s, 336 steps)
#  Stars dying → empty hands → final walk → void
# ============================================================

def p_cosmos_dims() -> Pattern:
    """P14: 8 bars = 128 steps. [Stars dying → reaching → empty hands]
    Cosmic indifference. Not hatred. Forgetting.
    Instruments dropping out one by one."""
    gr = g(128)
    # Pad: slowly fading
    chords = [(E3, B3), (E3, G3), (A2, E4), (E3, B3),
              (E3, G3), (E3, B3), (E3, G3), (E3, B3)]
    for i, (root, harm) in enumerate(chords):
        v = max(0.25, 0.45 - i * 0.025)
        pad_chord(gr, i * 16, root, harm, v, 16)

    # Bass: dying
    bass_note(gr, 0, E2, 0.42, 16)
    bass_note(gr, 32, A2, 0.38, 16)
    bass_note(gr, 64, E2, 0.34, 16)
    # Bass gone after bar 5

    # Lead: reaching up at stars, then falling
    # Bars 1-2: looks up — ascending
    gr[3][0]  = n(LEAD, E4, 0.45, 4)
    gr[3][4]  = n(LEAD, G4, 0.48, 4)
    gr[3][8]  = n(LEAD, A4, 0.50, 4)
    gr[3][12] = n(LEAD, B4, 0.52, 4)
    gr[3][16] = n(LEAD, D5, 0.50, 4)
    gr[3][20] = n(LEAD, E5, 0.48, 4)
    gr[3][24] = n(LEAD, D5, 0.45, 8)   # reaches highest point
    # Bars 3-4: "Stars went out" — descending, losing
    gr[3][32] = n(LEAD, B4, 0.42, 4)
    gr[3][36] = n(LEAD, A4, 0.40, 4)
    gr[3][40] = n(LEAD, G4, 0.38, 4)
    gr[3][44] = n(LEAD, E4, 0.36, 4)
    gr[3][48] = n(LEAD, D4, 0.34, 4)
    gr[3][52] = n(LEAD, C4, 0.32, 4)
    gr[3][56] = n(LEAD, B3, 0.30, 8)
    # Bars 5-6: "The boy kept walking" — single note, tired
    gr[3][64] = n(LEAD, E4, 0.32, 8)
    gr[3][76] = n(LEAD, E4, 0.30, 8)
    # Bars 7-8: fading
    gr[3][96]  = n(LEAD, E4, 0.28, 8)
    gr[3][112] = n(LEAD, E4, 0.25, 8)

    # Counter: descending with the stars
    gr[4][0]  = n(DARK, B3, 0.38, 8)
    gr[4][16] = n(DARK, A3, 0.35, 8)
    gr[4][32] = n(DARK, G3, 0.32, 8)
    gr[4][48] = n(DARK, E3, 0.30, 12)
    gr[4][64] = n(DARK, D3, 0.28, 12)
    # Counter gone after bar 5

    # Bell: dying chimes — each one quieter
    gr[6][8]  = n(BELL, E5, 0.20, 6)
    gr[6][32] = n(BELL, B4, 0.16, 6)
    gr[6][56] = n(BELL, G4, 0.12, 6)
    gr[6][80] = n(BELL, E4, 0.10, 6)
    # Gone after

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="cosmos_dims")


def p_final_walk() -> Pattern:
    """P15: 8 bars = 128 steps. [Last steps → shrinking → no moral]
    Almost empty. Pad barely audible. Single lead note repeating.
    The boy walking into the void."""
    gr = g(128)
    # Pad: nearly gone
    for i in range(8):
        v = max(0.15, 0.35 - i * 0.025)
        pad_chord(gr, i * 16, E3, B3, v, 16)

    # Bass: one bar at start, then gone
    bass_note(gr, 0, E2, 0.30, 16)

    # Lead: walking rhythm — E4 repeated, getting quieter
    for i in range(8):
        v = max(0.15, 0.30 - i * 0.02)
        gr[3][i * 16] = n(LEAD, E4, v, 6)

    # Bars 5-6: "And the moral of the story is this"
    gr[3][64] = n(LEAD, G4, 0.25, 4)
    gr[3][68] = n(LEAD, A4, 0.22, 4)
    gr[3][72] = n(LEAD, B4, 0.20, 8)

    # Bars 7-8: "There is no moral" — theme fragment, dying
    gr[3][96]  = n(LEAD, E4, 0.20, 4)
    gr[3][100] = n(LEAD, G4, 0.18, 4)
    gr[3][104] = n(LEAD, A4, 0.16, 4)
    gr[3][108] = n(LEAD, G4, 0.14, 8)
    gr[3][120] = n(LEAD, E4, 0.12, 8)

    # Counter: single note, distant
    gr[4][0]  = n(DARK, B3, 0.22, 16)
    gr[4][32] = n(DARK, G3, 0.18, 16)

    # Bell: final chimes
    gr[6][4]  = n(BELL, E5, 0.14, 8)
    gr[6][36] = n(BELL, B4, 0.10, 8)

    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=128,
                   num_channels=CH, bpm=BPM, name="final_walk")


def p_void() -> Pattern:
    """P16: 5 bars = 80 steps. [Walking into void → silence]
    Pad dissolves. Last bell. Nothing."""
    gr = g(80)
    # Pad: barely there
    gr[0][0]  = n(PAD, E3, 0.20, 16)
    gr[0][16] = n(PAD, E3, 0.15, 16)
    gr[0][32] = n(PAD, E3, 0.10, 16)
    # silence after bar 3

    # Lead: one last note
    gr[3][0]  = n(LEAD, E4, 0.15, 8)
    gr[3][16] = n(LEAD, E4, 0.10, 8)

    # Bell: last chime
    gr[6][8]  = n(BELL, E5, 0.10, 8)

    # Everything else: silence
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=80,
                   num_channels=CH, bpm=BPM, name="void")


# ============================================================
#  BUILD SONG
# ============================================================

def build_song() -> Song:
    """Assemble all patterns into the complete 300-second score."""
    patterns = [
        p_mist(),            # 0: 32 steps   Act I
        p_wound_search(),    # 1: 128 steps  Act I
        p_purpose(),         # 2: 128 steps  Act I
        p_crossing(),        # 3: 48 steps   Act I
        p_gifts_warm(),      # 4: 128 steps  Act II
        p_gifts_build(),     # 5: 128 steps  Act II
        p_carrying(),        # 6: 64 steps   Act II
        p_carrying_bridge(), # 7: 72 steps   Act II
        p_labyrinth(),       # 8: 128 steps  Act III
        p_mapping_pride(),   # 9: 128 steps  Act III
        p_stillness(),       # 10: 24 steps  Act III
        p_unraveling(),      # 11: 128 steps Act IV
        p_darkness(),        # 12: 128 steps Act IV
        p_stood_up(),        # 13: 80 steps  Act IV
        p_cosmos_dims(),     # 14: 128 steps Act V
        p_final_walk(),      # 15: 128 steps Act V
        p_void(),            # 16: 80 steps  Act V
    ]

    # Verify total: 32+128+128+48 + 128+128+64+72 + 128+128+24
    #              + 128+128+80 + 128+128+80 = 1680 steps = 300.0s
    total = sum(p.num_steps for p in patterns)
    assert total == 1680, f"Expected 1680 steps, got {total}"

    return Song(
        title="Core Fable Score",
        bpm=BPM,
        patterns=patterns,
        sequence=list(range(17)),
        panning={
            0: -0.20,   # pad root: left
            1:  0.20,   # pad harmony: right
            2:  0.00,   # bass: center
            3:  0.10,   # lead: slight right
            4: -0.15,   # counter: slight left
            5:  0.30,   # arp: right
            6: -0.25,   # bell: left
        },
        channel_effects={
            0: {"reverb": 0.40},
            1: {"reverb": 0.35},
            2: {"reverb": 0.08},
            3: {"reverb": 0.28, "delay": 0.20, "delay_feedback": 0.30},
            4: {"reverb": 0.25, "delay": 0.18, "delay_feedback": 0.25},
            5: {"delay": 0.22, "delay_feedback": 0.35, "reverb": 0.12},
            6: {"reverb": 0.30, "delay": 0.15, "delay_feedback": 0.20},
        },
        master_reverb=0.15,
        master_delay=0.08,
    )


if __name__ == "__main__":
    song = build_song()
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )
    out = Path("output/core_fable_score.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.1f}s → {out}  ({out.stat().st_size / 1024 / 1024:.1f} MB)")
