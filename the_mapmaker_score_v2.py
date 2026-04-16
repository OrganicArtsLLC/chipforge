"""The Mapmaker's Score v2 — emotionally synced to 'Core of Who I Am'.

Full 200-second film score in E minor, mapped to each film section:
  Opening (0-12.9s)     → mist: ethereal pad only
  The Wound (13-37.9s)  → wound: dark, aching, low tension
  Archetypes (38-73.9s) → dawn → theme → bloom: building, varied
  Struggle (74-96.9s)   → shadow → struggle: conflict, pulse, restless
  Paradoxes (97-124.9s) → mirror → mirror_deep: duality, call-and-response
  Labyrinth (125-154.9s)→ labyrinth → storm: driving journey to climax
  The Meta (155-178.9s) → light → warmth: warm resolution, arms open
  Epilogue (179-200s)   → resolve → fade → silence: walk toward dawn

BPM 84, E natural minor, 7 channels, 1120 steps = 200.0 seconds.
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


# ============================================================
#  PATTERNS — each function returns a Pattern
#  Emotional territories mapped to film sections
# ============================================================

def p_mist() -> Pattern:
    """P0: Ethereal pad wash. Em sustained. 2 bars. [Opening titles]"""
    gr = g(32)
    gr[0][0]  = n(PAD, E3, 0.45, 16)
    gr[0][16] = n(PAD, E3, 0.42, 16)
    gr[1][4]  = n(PAD2, B3, 0.35, 14)
    gr[1][20] = n(PAD2, B3, 0.32, 12)
    gr[6][12] = n(BELL, E5, 0.25, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=32,
                   num_channels=CH, bpm=BPM, name="mist")


def p_wound() -> Pattern:
    """P1: Dark aching tension. 4 bars. Em → Am → Bm → Em. [The Wound]
    Low pads, sub bass barely stirring, descending bell tones.
    Childhood abandonment — pressure without release."""
    gr = g(64)
    # Pad root: low E, swelling into darker chords
    gr[0][0]  = n(PAD, E3, 0.50, 16)
    gr[0][16] = n(PAD, A2, 0.52, 16)    # Am — drop to low A
    gr[0][32] = n(PAD, B2, 0.55, 16)    # Bm — tension builds
    gr[0][48] = n(PAD, E3, 0.48, 16)    # back home, unresolved
    # Pad harmony: minor intervals, dissonant close voicings
    gr[1][0]  = n(PAD2, G3, 0.38, 16)   # minor 3rd
    gr[1][16] = n(PAD2, C4, 0.40, 16)   # tension: C over Am
    gr[1][32] = n(PAD2, D4, 0.42, 16)   # minor 3rd of Bm
    gr[1][48] = n(PAD2, G3, 0.36, 16)   # settle
    # Bass: barely there, sub pulses
    gr[2][0]  = n(BASS, E2, 0.35, 12)
    gr[2][32] = n(BASS, B2, 0.40, 12)
    # Counter: slow descending lament (saw_dark)
    gr[4][4]  = n(DARK, B3, 0.38, 8)
    gr[4][16] = n(DARK, A3, 0.36, 8)
    gr[4][32] = n(DARK, G3, 0.38, 8)
    gr[4][48] = n(DARK, E3, 0.34, 8)
    # Bell: descending, distant, lonely
    gr[6][0]  = n(BELL, B4, 0.22, 6)
    gr[6][24] = n(BELL, A4, 0.20, 6)
    gr[6][48] = n(BELL, G4, 0.18, 6)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="wound")


def p_wound_deep() -> Pattern:
    """P2: Wound intensifies. 4 bars. Am → Em → C → Bm. [Given away / Chosen]
    Fork in the road — bass enters more, counter voice rises with pain."""
    gr = g(64)
    gr[0][0]  = n(PAD, A2, 0.52, 16)
    gr[0][16] = n(PAD, E3, 0.50, 16)
    gr[0][32] = n(PAD, C3, 0.52, 16)
    gr[0][48] = n(PAD, B2, 0.55, 16)    # unresolved
    gr[1][0]  = n(PAD2, C4, 0.40, 16)
    gr[1][16] = n(PAD2, B3, 0.38, 16)
    gr[1][32] = n(PAD2, E4, 0.40, 16)
    gr[1][48] = n(PAD2, D4, 0.42, 16)   # yearning upward
    # Bass: heavier, more present
    gr[2][0]  = n(BASS, A2, 0.42, 8)
    gr[2][8]  = n(BASS, A2, 0.38, 8)
    gr[2][16] = n(BASS, E2, 0.40, 8)
    gr[2][32] = n(BASS, C3, 0.44, 8)
    gr[2][40] = n(BASS, C3, 0.40, 8)
    gr[2][48] = n(BASS, B2, 0.46, 8)
    # Counter: rising ache
    gr[4][0]  = n(DARK, E3, 0.40, 6)
    gr[4][8]  = n(DARK, G3, 0.42, 6)
    gr[4][16] = n(DARK, A3, 0.40, 6)
    gr[4][28] = n(DARK, B3, 0.44, 6)
    gr[4][40] = n(DARK, C4, 0.42, 6)
    gr[4][52] = n(DARK, D4, 0.40, 8)    # reaches up, doesn't resolve
    # Bell: two tones alternating — "given away / chosen"
    gr[6][8]  = n(BELL, G4, 0.22, 4)   # cold
    gr[6][20] = n(BELL, B4, 0.24, 4)   # warm
    gr[6][40] = n(BELL, G4, 0.20, 4)   # cold
    gr[6][52] = n(BELL, E5, 0.22, 4)   # warm, higher
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="wound_deep")


def p_dawn() -> Pattern:
    """P3: Gentle lifting. 4 bars. Em → C → Am → Em. [Archetypes begin]
    Bass stirs, first arpeggios. The Seeker lights a lantern."""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.48, 16)
    gr[0][16] = n(PAD, C3, 0.48, 16)
    gr[0][32] = n(PAD, A3, 0.48, 16)
    gr[0][48] = n(PAD, E3, 0.46, 16)
    gr[1][0]  = n(PAD2, B3, 0.38, 16)
    gr[1][16] = n(PAD2, G3, 0.36, 16)
    gr[1][32] = n(PAD2, E4, 0.38, 16)
    gr[1][48] = n(PAD2, B3, 0.36, 16)
    # Bass enters gently
    gr[2][32] = n(BASS, A2, 0.40, 8)
    gr[2][40] = n(BASS, A2, 0.38, 8)
    gr[2][48] = n(BASS, E3, 0.42, 8)
    gr[2][56] = n(BASS, E3, 0.38, 8)
    # First arp hints — sparse, like sparks
    gr[5][16] = n(ARP, E4, 0.28, 3)
    gr[5][24] = n(ARP, G4, 0.25, 3)
    gr[5][40] = n(ARP, B4, 0.28, 3)
    gr[5][52] = n(ARP, A4, 0.25, 3)
    # Bell accents
    gr[6][8]  = n(BELL, E5, 0.22, 4)
    gr[6][44] = n(BELL, G4, 0.20, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="dawn")


def p_theme() -> Pattern:
    """P4: Main theme melody. 4 bars. Em → G → Am → Em. [Archetypes: Seeker/Contrarian]
    The ascending-reach, falling-home motif. Determined curiosity."""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.48, 16)
    gr[0][16] = n(PAD, G3, 0.46, 16)
    gr[0][32] = n(PAD, A3, 0.48, 16)
    gr[0][48] = n(PAD, E3, 0.46, 16)
    gr[1][0]  = n(PAD2, B3, 0.38, 16)
    gr[1][16] = n(PAD2, D4, 0.36, 16)
    gr[1][32] = n(PAD2, E4, 0.38, 16)
    gr[1][48] = n(PAD2, B3, 0.36, 16)
    # Bass: steady, grounding
    for bar in range(4):
        root = [E3, G2, A2, E3][bar]
        gr[2][bar * 16]     = n(BASS, root, 0.48, 8)
        gr[2][bar * 16 + 8] = n(BASS, root, 0.44, 8)
    # Lead: THE THEME — ascending reach, falling home
    gr[3][0]  = n(LEAD, E4, 0.52, 4)
    gr[3][4]  = n(LEAD, G4, 0.55, 4)
    gr[3][8]  = n(LEAD, A4, 0.58, 4)
    gr[3][12] = n(LEAD, B4, 0.56, 4)
    gr[3][16] = n(LEAD, A4, 0.54, 4)
    gr[3][20] = n(LEAD, G4, 0.52, 4)
    gr[3][24] = n(LEAD, E4, 0.50, 8)
    gr[3][32] = n(LEAD, G4, 0.55, 4)
    gr[3][36] = n(LEAD, A4, 0.58, 4)
    gr[3][40] = n(LEAD, B4, 0.60, 4)
    gr[3][44] = n(LEAD, D5, 0.58, 4)
    gr[3][48] = n(LEAD, B4, 0.56, 4)
    gr[3][52] = n(LEAD, A4, 0.52, 4)
    gr[3][56] = n(LEAD, G4, 0.50, 4)
    gr[3][60] = n(LEAD, E4, 0.48, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="theme")


def p_bloom() -> Pattern:
    """P5: Full arrangement. 4 bars. Em → G → C → Em. [Archetypes: Builder/Loyal Son]
    All channels active. Arp running, counter voice, blocks being stacked."""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.50, 16)
    gr[0][16] = n(PAD, G3, 0.48, 16)
    gr[0][32] = n(PAD, C3, 0.50, 16)
    gr[0][48] = n(PAD, E3, 0.48, 16)
    gr[1][0]  = n(PAD2, B3, 0.40, 16)
    gr[1][16] = n(PAD2, D4, 0.38, 16)
    gr[1][32] = n(PAD2, G3, 0.40, 16)
    gr[1][48] = n(PAD2, B3, 0.38, 16)
    for bar in range(4):
        root = [E3, G2, C3, E3][bar]
        gr[2][bar * 16]     = n(BASS, root, 0.50, 8)
        gr[2][bar * 16 + 8] = n(BASS, root, 0.46, 8)
    # Lead: theme variation — reaching higher, yearning
    gr[3][0]  = n(LEAD, G4, 0.58, 4)
    gr[3][4]  = n(LEAD, B4, 0.60, 2)
    gr[3][6]  = n(LEAD, A4, 0.58, 2)
    gr[3][8]  = n(LEAD, B4, 0.60, 4)
    gr[3][12] = n(LEAD, D5, 0.62, 4)
    gr[3][16] = n(LEAD, B4, 0.58, 4)
    gr[3][20] = n(LEAD, A4, 0.55, 4)
    gr[3][24] = n(LEAD, G4, 0.53, 8)
    gr[3][32] = n(LEAD, A4, 0.58, 4)
    gr[3][36] = n(LEAD, B4, 0.60, 4)
    gr[3][40] = n(LEAD, E5, 0.62, 4)
    gr[3][44] = n(LEAD, D5, 0.58, 4)
    gr[3][48] = n(LEAD, B4, 0.56, 4)
    gr[3][52] = n(LEAD, G4, 0.52, 4)
    gr[3][56] = n(LEAD, E4, 0.50, 4)
    gr[3][60] = n(LEAD, D4, 0.48, 4)
    # Counter: answering
    gr[4][4]  = n(DARK, B3, 0.40, 6)
    gr[4][12] = n(DARK, A3, 0.38, 8)
    gr[4][24] = n(DARK, G3, 0.40, 8)
    gr[4][36] = n(DARK, A3, 0.38, 6)
    gr[4][44] = n(DARK, B3, 0.40, 8)
    gr[4][56] = n(DARK, G3, 0.38, 8)
    # Arp: gentle running
    arp_notes = [E4, B4, G4, E5, B4, G4, E4, B3,
                 D4, B4, G4, D5, B4, G4, D4, B3]
    for i, mn in enumerate(arp_notes):
        gr[5][i * 4] = n(ARP, mn, 0.32, 3)
    gr[6][0]  = n(BELL, E5, 0.25, 4)
    gr[6][32] = n(BELL, G4, 0.22, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="bloom")


def p_shadow() -> Pattern:
    """P6: Dark tension. 4 bars. Am → Em → Bdim → Em. [The Struggle begins]
    Background pulses. Balance feels unsafe. Restless oscillation."""
    gr = g(64)
    gr[0][0]  = n(PAD, A3, 0.50, 16)
    gr[0][16] = n(PAD, E3, 0.52, 16)
    gr[0][32] = n(PAD, B3, 0.50, 16)
    gr[0][48] = n(PAD, E3, 0.48, 16)
    gr[1][0]  = n(PAD2, C4, 0.40, 16)
    gr[1][16] = n(PAD2, B3, 0.42, 16)
    gr[1][32] = n(PAD2, D4, 0.42, 16)
    gr[1][48] = n(PAD2, G3, 0.38, 16)
    # Bass: heavier, insistent
    for bar in range(4):
        root = [A2, E3, B2, E3][bar]
        gr[2][bar * 16]      = n(BASS, root, 0.55, 6)
        gr[2][bar * 16 + 8]  = n(BASS, root, 0.50, 6)
        gr[2][bar * 16 + 12] = n(BASS, root + 7, 0.42, 4)
    # Lead: fragmented, searching
    gr[3][2]  = n(LEAD, E4, 0.50, 3)
    gr[3][8]  = n(LEAD, D4, 0.52, 3)
    gr[3][14] = n(LEAD, C4, 0.48, 2)
    gr[3][20] = n(LEAD, B3, 0.50, 6)
    gr[3][28] = n(LEAD, A3, 0.48, 4)
    gr[3][36] = n(LEAD, D4, 0.52, 4)
    gr[3][40] = n(LEAD, Fs4, 0.55, 4)
    gr[3][44] = n(LEAD, E4, 0.50, 4)
    gr[3][52] = n(LEAD, B3, 0.48, 8)
    gr[3][60] = n(LEAD, E4, 0.45, 4)
    # Counter: descending
    gr[4][0]  = n(DARK, E4, 0.45, 4)
    gr[4][4]  = n(DARK, D4, 0.43, 4)
    gr[4][8]  = n(DARK, C4, 0.42, 4)
    gr[4][12] = n(DARK, B3, 0.40, 4)
    gr[4][32] = n(DARK, Fs4, 0.45, 4)
    gr[4][36] = n(DARK, E4, 0.43, 4)
    gr[4][40] = n(DARK, D4, 0.42, 4)
    gr[4][44] = n(DARK, B3, 0.40, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="shadow")


def p_struggle() -> Pattern:
    """P7: Restless intensity. 4 bars. Em → Am → B → Em. [Intensity feels alive]
    Faster arp, driving bass, lead oscillates between high and low.
    Not yet a storm — a body pacing, unable to stop moving."""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.52, 16)
    gr[0][16] = n(PAD, A3, 0.52, 16)
    gr[0][32] = n(PAD, B3, 0.55, 16)
    gr[0][48] = n(PAD, E3, 0.50, 16)
    gr[1][0]  = n(PAD2, G3, 0.42, 16)
    gr[1][16] = n(PAD2, C4, 0.42, 16)
    gr[1][32] = n(PAD2, Fs4, 0.44, 16)
    gr[1][48] = n(PAD2, B3, 0.40, 16)
    # Bass: restless eighths
    bass_seq = [E3, E3, A2, A2, B2, B2, E3, E3]
    for i, br in enumerate(bass_seq):
        gr[2][i * 8] = n(BASS, br, 0.52, 6)
    # Lead: oscillating high-low, unable to settle
    gr[3][0]  = n(LEAD, E4, 0.55, 3)
    gr[3][4]  = n(LEAD, B4, 0.58, 3)
    gr[3][8]  = n(LEAD, E4, 0.52, 3)
    gr[3][12] = n(LEAD, A4, 0.55, 3)
    gr[3][16] = n(LEAD, D4, 0.52, 4)
    gr[3][20] = n(LEAD, G4, 0.55, 4)
    gr[3][24] = n(LEAD, B4, 0.58, 4)
    gr[3][28] = n(LEAD, A4, 0.55, 4)
    gr[3][32] = n(LEAD, Fs4, 0.58, 3)
    gr[3][36] = n(LEAD, B4, 0.60, 3)
    gr[3][40] = n(LEAD, D5, 0.58, 3)
    gr[3][44] = n(LEAD, B4, 0.55, 3)
    gr[3][48] = n(LEAD, E4, 0.52, 4)
    gr[3][52] = n(LEAD, G4, 0.50, 4)
    gr[3][56] = n(LEAD, A4, 0.52, 4)
    gr[3][60] = n(LEAD, E4, 0.48, 4)
    # Arp: restless, faster pattern
    arp_r = [E4, G4, B4, G4, A4, C5, A4, E4,
             B3, D4, Fs4, D4, E4, G4, E4, B3]
    for i, mn in enumerate(arp_r):
        gr[5][i * 4] = n(ARP, mn, 0.35, 2)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="struggle")


def p_mirror() -> Pattern:
    """P8: Duality and paradox. 4 bars. Em → Cmaj7 → Am → Em. [The Paradoxes]
    Call and response between lead and counter. Two figures approaching.
    Lead ascends where counter descends. Mirror image."""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.50, 16)
    gr[0][16] = n(PAD, C3, 0.48, 16)
    gr[0][32] = n(PAD, A3, 0.50, 16)
    gr[0][48] = n(PAD, E3, 0.48, 16)
    gr[1][0]  = n(PAD2, B3, 0.40, 16)
    gr[1][16] = n(PAD2, B3, 0.38, 16)   # Cmaj7: B over C
    gr[1][32] = n(PAD2, C4, 0.40, 16)
    gr[1][48] = n(PAD2, B3, 0.38, 16)
    # Bass: deliberate, contemplative
    gr[2][0]  = n(BASS, E3, 0.45, 12)
    gr[2][16] = n(BASS, C3, 0.43, 12)
    gr[2][32] = n(BASS, A2, 0.45, 12)
    gr[2][48] = n(BASS, E3, 0.43, 12)
    # Lead (warm voice): ascending call
    gr[3][0]  = n(LEAD, E4, 0.52, 4)    # "I am..."
    gr[3][4]  = n(LEAD, G4, 0.55, 4)    # "...both..."
    gr[3][8]  = n(LEAD, A4, 0.58, 8)    # "...abandoned"
    gr[3][32] = n(LEAD, A4, 0.55, 4)
    gr[3][36] = n(LEAD, B4, 0.58, 4)
    gr[3][40] = n(LEAD, D5, 0.60, 8)    # reaches up
    # Counter (cool voice): descending response — mirror image
    gr[4][16] = n(DARK, D4, 0.48, 4)    # "and..."
    gr[4][20] = n(DARK, C4, 0.45, 4)    # "...chosen"
    gr[4][24] = n(DARK, B3, 0.42, 8)    # falls
    gr[4][48] = n(DARK, B4, 0.48, 4)
    gr[4][52] = n(DARK, A4, 0.45, 4)
    gr[4][56] = n(DARK, G4, 0.42, 8)    # responds down
    # Arp: alternating between warm and cool register
    for i in range(8):
        note_up = [E4, G4, B4, E5, G4, B4, E4, G4][i]
        gr[5][i * 8] = n(ARP, note_up, 0.30, 3)
    # Bell: two alternating tones — duality
    gr[6][0]  = n(BELL, E5, 0.22, 4)    # warm
    gr[6][16] = n(BELL, C5, 0.20, 4)    # cool
    gr[6][32] = n(BELL, E5, 0.22, 4)
    gr[6][48] = n(BELL, C5, 0.20, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="mirror")


def p_mirror_deep() -> Pattern:
    """P9: Paradoxes intensify — the two voices merge. 4 bars.
    Lead and counter converge, arp tightens. 'Native language.'"""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.52, 16)
    gr[0][16] = n(PAD, G3, 0.50, 16)
    gr[0][32] = n(PAD, A3, 0.52, 16)
    gr[0][48] = n(PAD, E3, 0.50, 16)
    gr[1][0]  = n(PAD2, G3, 0.42, 16)
    gr[1][16] = n(PAD2, B3, 0.40, 16)
    gr[1][32] = n(PAD2, E4, 0.42, 16)
    gr[1][48] = n(PAD2, G3, 0.40, 16)
    gr[2][0]  = n(BASS, E3, 0.48, 8)
    gr[2][8]  = n(BASS, E3, 0.44, 8)
    gr[2][16] = n(BASS, G2, 0.46, 8)
    gr[2][24] = n(BASS, G2, 0.42, 8)
    gr[2][32] = n(BASS, A2, 0.48, 8)
    gr[2][40] = n(BASS, A2, 0.44, 8)
    gr[2][48] = n(BASS, E3, 0.46, 8)
    gr[2][56] = n(BASS, E3, 0.42, 8)
    # Lead and counter now move TOGETHER — convergence
    # Lead
    gr[3][0]  = n(LEAD, E4, 0.55, 4)
    gr[3][4]  = n(LEAD, G4, 0.58, 4)
    gr[3][8]  = n(LEAD, A4, 0.60, 4)
    gr[3][12] = n(LEAD, B4, 0.58, 4)
    gr[3][16] = n(LEAD, G4, 0.55, 4)
    gr[3][20] = n(LEAD, B4, 0.58, 4)
    gr[3][24] = n(LEAD, A4, 0.55, 8)
    gr[3][32] = n(LEAD, B4, 0.58, 4)
    gr[3][36] = n(LEAD, D5, 0.60, 4)
    gr[3][40] = n(LEAD, E5, 0.62, 4)
    gr[3][44] = n(LEAD, D5, 0.58, 4)
    gr[3][48] = n(LEAD, B4, 0.55, 4)
    gr[3][52] = n(LEAD, A4, 0.52, 4)
    gr[3][56] = n(LEAD, G4, 0.50, 4)
    gr[3][60] = n(LEAD, E4, 0.48, 4)
    # Counter: parallel thirds/sixths — walking together
    gr[4][0]  = n(DARK, B3, 0.42, 4)
    gr[4][4]  = n(DARK, D4, 0.44, 4)
    gr[4][8]  = n(DARK, E4, 0.46, 4)
    gr[4][12] = n(DARK, G4, 0.44, 4)
    gr[4][16] = n(DARK, D4, 0.42, 4)
    gr[4][20] = n(DARK, G4, 0.44, 4)
    gr[4][24] = n(DARK, E4, 0.42, 8)
    gr[4][32] = n(DARK, G4, 0.44, 4)
    gr[4][36] = n(DARK, A4, 0.46, 4)
    gr[4][40] = n(DARK, B4, 0.48, 4)
    gr[4][44] = n(DARK, A4, 0.44, 4)
    gr[4][48] = n(DARK, G4, 0.42, 4)
    gr[4][52] = n(DARK, E4, 0.40, 4)
    gr[4][56] = n(DARK, D4, 0.38, 4)
    gr[4][60] = n(DARK, B3, 0.36, 4)
    # Arp: tighter, every 2 steps
    tight_arp = [E4, G4, B4, E5, D5, B4, G4, E4,
                 A4, C5, E5, C5, A4, G4, E4, A3,
                 B4, D5, G4, B4, A4, E4, G4, B3,
                 E4, G4, A4, B4, D5, E5, D5, B4]
    for i, mn in enumerate(tight_arp[:32]):
        if i < 64:
            gr[5][i * 2] = n(ARP, mn, 0.30, 2)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="mirror_deep")


def p_labyrinth() -> Pattern:
    """P10: Driving journey. 4 bars. Em → Am → C → Bm. [Theseus in the Labyrinth]
    Purposeful walking bass, determined arp, lead steps forward.
    Red thread trailing behind. Maze walls scrolling past."""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.48, 16)
    gr[0][16] = n(PAD, A3, 0.48, 16)
    gr[0][32] = n(PAD, C3, 0.50, 16)
    gr[0][48] = n(PAD, B2, 0.50, 16)
    gr[1][0]  = n(PAD2, G3, 0.38, 16)
    gr[1][16] = n(PAD2, C4, 0.38, 16)
    gr[1][32] = n(PAD2, E4, 0.40, 16)
    gr[1][48] = n(PAD2, D4, 0.40, 16)
    # Bass: WALKING — steady quarter notes, like footsteps
    bass_walk = [E3, E3, G3, G2, A2, A2, C3, C3,
                 C3, C3, E3, E3, B2, B2, D3, D3]
    for i, bn in enumerate(bass_walk):
        gr[2][i * 4] = n(BASS, bn, 0.50, 3)
    # Lead: stepwise, determined, mapping the maze
    gr[3][0]  = n(LEAD, E4, 0.55, 4)
    gr[3][4]  = n(LEAD, Fs4, 0.55, 4)
    gr[3][8]  = n(LEAD, G4, 0.58, 4)
    gr[3][12] = n(LEAD, A4, 0.58, 4)
    gr[3][16] = n(LEAD, B4, 0.60, 4)
    gr[3][20] = n(LEAD, A4, 0.55, 4)
    gr[3][24] = n(LEAD, G4, 0.52, 8)
    gr[3][32] = n(LEAD, A4, 0.55, 4)
    gr[3][36] = n(LEAD, B4, 0.58, 4)
    gr[3][40] = n(LEAD, C5, 0.60, 4)
    gr[3][44] = n(LEAD, D5, 0.62, 4)
    gr[3][48] = n(LEAD, E5, 0.65, 8)    # highest point — seeing the path
    gr[3][56] = n(LEAD, D5, 0.58, 4)
    gr[3][60] = n(LEAD, B4, 0.55, 4)
    # Counter: echoing the path behind (delayed motif)
    gr[4][8]  = n(DARK, E4, 0.40, 4)
    gr[4][12] = n(DARK, Fs4, 0.40, 4)
    gr[4][20] = n(DARK, G4, 0.42, 4)
    gr[4][28] = n(DARK, A4, 0.42, 4)
    gr[4][40] = n(DARK, A4, 0.40, 4)
    gr[4][48] = n(DARK, B4, 0.42, 4)
    gr[4][56] = n(DARK, C5, 0.40, 4)
    # Arp: forward momentum, ascending patterns
    lab_arp = [E4, G4, B4, E5, A4, C5, E5, A4,
               C5, E5, G4, C5, B4, D5, G4, B4]
    for i, mn in enumerate(lab_arp):
        gr[5][i * 4] = n(ARP, mn, 0.34, 3)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="labyrinth")


def p_storm() -> Pattern:
    """P11: Peak intensity / CLIMAX. 4 bars. Em → Am → B → Em.
    [Labyrinth peak: 'I am mapping it so others can follow.']
    All channels at full. Theme transformed into triumphant declaration."""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.55, 16)
    gr[0][16] = n(PAD, A3, 0.55, 16)
    gr[0][32] = n(PAD, B3, 0.58, 16)
    gr[0][48] = n(PAD, E3, 0.55, 16)
    gr[1][0]  = n(PAD2, G3, 0.45, 16)
    gr[1][16] = n(PAD2, C4, 0.45, 16)
    gr[1][32] = n(PAD2, Fs4, 0.48, 16)
    gr[1][48] = n(PAD2, B3, 0.45, 16)
    # Bass: driving eighths
    bass_roots = [E3, E3, A2, A2, B2, B2, E3, E3]
    for i, br in enumerate(bass_roots):
        gr[2][i * 8] = n(BASS, br, 0.58, 6)
    # Lead: climactic theme — triumphant ascending arc
    gr[3][0]  = n(LEAD, E4, 0.62, 4)
    gr[3][4]  = n(LEAD, G4, 0.65, 4)
    gr[3][8]  = n(LEAD, B4, 0.68, 4)
    gr[3][12] = n(LEAD, D5, 0.70, 4)
    gr[3][16] = n(LEAD, E5, 0.72, 8)    # PEAK — the declaration
    gr[3][24] = n(LEAD, D5, 0.68, 4)
    gr[3][28] = n(LEAD, B4, 0.65, 4)
    gr[3][32] = n(LEAD, Fs4, 0.62, 4)
    gr[3][36] = n(LEAD, A4, 0.65, 4)
    gr[3][40] = n(LEAD, B4, 0.68, 8)
    gr[3][48] = n(LEAD, G4, 0.60, 4)
    gr[3][52] = n(LEAD, E4, 0.55, 4)
    gr[3][56] = n(LEAD, D4, 0.52, 4)
    gr[3][60] = n(LEAD, E4, 0.55, 4)
    # Counter: urgent repeated motif
    for bar in range(4):
        gr[4][bar * 16]      = n(DARK, B3, 0.48, 4)
        gr[4][bar * 16 + 4]  = n(DARK, E4, 0.50, 4)
        gr[4][bar * 16 + 8]  = n(DARK, D4, 0.48, 4)
        gr[4][bar * 16 + 12] = n(DARK, B3, 0.45, 4)
    # Arp: rapid climbing
    arp_seq = [E4, G4, B4, E5, G4, B4, E4, G4,
               A3, C4, E4, A4, C4, E4, A3, C4]
    for i, mn in enumerate(arp_seq):
        gr[5][i * 4] = n(ARP, mn, 0.38, 3)
    # Bell: climax hits
    gr[6][16] = n(BELL, E5, 0.35, 8)
    gr[6][40] = n(BELL, B4, 0.30, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="storm")


def p_light() -> Pattern:
    """P12: Warmth returns. 4 bars. C → G → Am → Em. [The Meta]
    Theme restated gently. Arms open. Belonging is built. Dawn coming."""
    gr = g(64)
    gr[0][0]  = n(PAD, C3, 0.50, 16)
    gr[0][16] = n(PAD, G3, 0.48, 16)
    gr[0][32] = n(PAD, A3, 0.50, 16)
    gr[0][48] = n(PAD, E3, 0.48, 16)
    gr[1][0]  = n(PAD2, E4, 0.40, 16)
    gr[1][16] = n(PAD2, D4, 0.38, 16)
    gr[1][32] = n(PAD2, E4, 0.40, 16)
    gr[1][48] = n(PAD2, B3, 0.38, 16)
    for bar in range(4):
        root = [C3, G2, A2, E3][bar]
        gr[2][bar * 16] = n(BASS, root, 0.45, 12)
    # Lead: theme gently restated
    gr[3][0]  = n(LEAD, E4, 0.50, 4)
    gr[3][4]  = n(LEAD, G4, 0.52, 4)
    gr[3][8]  = n(LEAD, A4, 0.55, 4)
    gr[3][12] = n(LEAD, B4, 0.52, 4)
    gr[3][16] = n(LEAD, A4, 0.50, 4)
    gr[3][20] = n(LEAD, G4, 0.48, 4)
    gr[3][24] = n(LEAD, E4, 0.50, 8)
    gr[3][32] = n(LEAD, G4, 0.52, 4)
    gr[3][36] = n(LEAD, A4, 0.55, 4)
    gr[3][40] = n(LEAD, B4, 0.58, 8)
    gr[3][48] = n(LEAD, A4, 0.52, 4)
    gr[3][52] = n(LEAD, G4, 0.50, 4)
    gr[3][56] = n(LEAD, E4, 0.48, 8)
    # Counter: warm answering
    gr[4][8]  = n(DARK, B3, 0.35, 8)
    gr[4][24] = n(DARK, A3, 0.33, 8)
    gr[4][40] = n(DARK, G3, 0.35, 8)
    gr[4][56] = n(DARK, B3, 0.33, 8)
    # Arp: sparse, like stars fading into sunrise
    for i, mn in enumerate([E4, B4, G4, E5, B4, G4]):
        gr[5][i * 8 + 4] = n(ARP, mn, 0.28, 4)
    gr[6][0]  = n(BELL, E5, 0.22, 8)
    gr[6][48] = n(BELL, B4, 0.20, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="light")


def p_warmth() -> Pattern:
    """P13: Deep warmth, arms open. 4 bars. G → C → Em → Em. [Meta: dance partners]
    Brighter voicings. Lead sings the theme one last time with conviction.
    The score 'opens up' — wider intervals, more light."""
    gr = g(64)
    gr[0][0]  = n(PAD, G3, 0.50, 16)
    gr[0][16] = n(PAD, C3, 0.50, 16)
    gr[0][32] = n(PAD, E3, 0.52, 16)
    gr[0][48] = n(PAD, E3, 0.48, 16)
    gr[1][0]  = n(PAD2, D4, 0.40, 16)
    gr[1][16] = n(PAD2, E4, 0.40, 16)
    gr[1][32] = n(PAD2, G4, 0.42, 16)   # wide, bright
    gr[1][48] = n(PAD2, B3, 0.38, 16)
    gr[2][0]  = n(BASS, G2, 0.44, 12)
    gr[2][16] = n(BASS, C3, 0.44, 12)
    gr[2][32] = n(BASS, E3, 0.46, 12)
    gr[2][48] = n(BASS, E3, 0.42, 12)
    # Lead: final theme statement — richer, more open
    gr[3][0]  = n(LEAD, G4, 0.55, 4)
    gr[3][4]  = n(LEAD, B4, 0.58, 4)
    gr[3][8]  = n(LEAD, D5, 0.60, 4)
    gr[3][12] = n(LEAD, E5, 0.62, 8)    # soaring
    gr[3][20] = n(LEAD, D5, 0.58, 4)
    gr[3][24] = n(LEAD, B4, 0.55, 8)
    gr[3][32] = n(LEAD, E4, 0.52, 4)
    gr[3][36] = n(LEAD, G4, 0.55, 4)
    gr[3][40] = n(LEAD, A4, 0.58, 4)
    gr[3][44] = n(LEAD, B4, 0.60, 8)
    gr[3][52] = n(LEAD, A4, 0.55, 4)
    gr[3][56] = n(LEAD, G4, 0.52, 4)
    gr[3][60] = n(LEAD, E4, 0.50, 4)
    # Counter: gentle harmonics
    gr[4][4]  = n(DARK, D4, 0.35, 8)
    gr[4][16] = n(DARK, E4, 0.33, 8)
    gr[4][32] = n(DARK, B3, 0.35, 8)
    gr[4][48] = n(DARK, G3, 0.33, 8)
    # Arp: wide, gentle
    for i, mn in enumerate([G4, D5, B4, G4, E4, B4, G4, D4]):
        gr[5][i * 8] = n(ARP, mn, 0.26, 4)
    gr[6][8]  = n(BELL, D5, 0.22, 8)
    gr[6][40] = n(BELL, E5, 0.20, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="warmth")


def p_resolve() -> Pattern:
    """P14: Sparse resolution. 4 bars. Em → C → G → Em. [Epilogue: The Weaver]
    Figure walking toward dawn. Layers strip away. Just pad + bell + bass."""
    gr = g(64)
    gr[0][0]  = n(PAD, E3, 0.42, 16)
    gr[0][16] = n(PAD, C3, 0.40, 16)
    gr[0][32] = n(PAD, G3, 0.38, 16)
    gr[0][48] = n(PAD, E3, 0.36, 16)
    gr[1][0]  = n(PAD2, B3, 0.32, 16)
    gr[1][16] = n(PAD2, G3, 0.30, 16)
    gr[1][32] = n(PAD2, B3, 0.30, 16)
    gr[1][48] = n(PAD2, B3, 0.28, 16)
    gr[2][0]  = n(BASS, E3, 0.38, 16)
    gr[2][32] = n(BASS, G2, 0.35, 16)
    # Lead: just the opening motif fragment, fragile
    gr[3][0]  = n(LEAD, E4, 0.42, 4)
    gr[3][4]  = n(LEAD, G4, 0.44, 4)
    gr[3][8]  = n(LEAD, A4, 0.42, 8)
    gr[3][48] = n(LEAD, E4, 0.38, 8)
    gr[3][56] = n(LEAD, D4, 0.35, 8)
    gr[6][16] = n(BELL, E5, 0.18, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64,
                   num_channels=CH, bpm=BPM, name="resolve")


def p_fade() -> Pattern:
    """P15: Silence approaches. 2 bars. Em only. [Final fade to black]"""
    gr = g(32)
    gr[0][0]  = n(PAD, E3, 0.35, 16)
    gr[0][16] = n(PAD, E3, 0.28, 16)
    gr[1][8]  = n(PAD2, B3, 0.25, 12)
    gr[6][0]  = n(BELL, E5, 0.15, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=32,
                   num_channels=CH, bpm=BPM, name="fade")


def p_silence() -> Pattern:
    """P16: Near silence. 2 bars. Just whisper of E. [Black screen]"""
    gr = g(32)
    gr[0][0]  = n(PAD, E3, 0.22, 16)
    gr[0][16] = n(PAD, E3, 0.15, 16)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=32,
                   num_channels=CH, bpm=BPM, name="silence")


# ============================================================
#  BUILD SONG — emotionally synced to film sections
# ============================================================

def build_song() -> Song:
    """Assemble all patterns into the film-synced score.

    Total: 1120 steps = 200.0 seconds at BPM 84 / SPB 4

    Sequence mapping to film sections:
      Idx  Pattern       Steps  Cumul  Time    Film Section
      ───  ────────────  ─────  ─────  ──────  ──────────────────────
       0   mist           32     32    5.7s    Opening: title cards
       1   mist           32     64   11.4s    Opening: subtitle
       2   wound          64    128   22.9s    Wound: 'forged in complexity'
       3   wound_deep     64    192   34.3s    Wound: 'given away / chosen'
       4   dawn           64    256   45.7s    Archetypes: Seeker's lantern
       5   theme          64    320   57.1s    Archetypes: Contrarian/Builder
       6   bloom          64    384   68.6s    Archetypes: Loyal Son
       7   shadow         64    448   80.0s    Struggle: 'balance unsafe'
       8   struggle       64    512   91.4s    Struggle: 'intensity alive'
       9   mirror         64    576  102.9s    Paradoxes: 'abandoned/chosen'
      10   mirror_deep    64    640  114.3s    Paradoxes: 'native language'
      11   labyrinth      64    704  125.7s    Labyrinth: 'maze at birth'
      12   storm          64    768  137.1s    Labyrinth: CLIMAX 'mapping it'
      13   light          64    832  148.6s    Labyrinth → Meta transition
      14   warmth         64    896  160.0s    Meta: 'belonging you build'
      15   resolve        64    960  171.4s    Meta → Epilogue: 'the weaver'
      16   fade           32    992  177.1s    Epilogue: walking to dawn
      17   fade           32   1024  182.9s    Epilogue: figure fading
      18   silence        32   1056  188.6s    Epilogue: dawn glow
      19   silence        32   1088  194.3s    Black, credits
      20   silence        32   1120  200.0s    Held silence to picture end
    """
    patterns = [
        p_mist(),         # 0
        p_wound(),        # 1
        p_wound_deep(),   # 2
        p_dawn(),         # 3
        p_theme(),        # 4
        p_bloom(),        # 5
        p_shadow(),       # 6
        p_struggle(),     # 7
        p_mirror(),       # 8
        p_mirror_deep(),  # 9
        p_labyrinth(),    # 10
        p_storm(),        # 11
        p_light(),        # 12
        p_warmth(),       # 13
        p_resolve(),      # 14
        p_fade(),         # 15
        p_silence(),      # 16
    ]

    # 21 slots: 7 × 32-step + 14 × 64-step = 224 + 896 = 1120 steps = 200.0s
    sequence = [
        0,              # mist (32)
        0,              # mist (32)
        1,              # wound (64)
        2,              # wound_deep (64)
        3,              # dawn (64)
        4,              # theme (64)
        5,              # bloom (64)
        6,              # shadow (64)
        7,              # struggle (64)
        8,              # mirror (64)
        9,              # mirror_deep (64)
        10,             # labyrinth (64)
        11,             # storm (64)     <-- CLIMAX
        12,             # light (64)
        13,             # warmth (64)
        14,             # resolve (64)
        15,             # fade (32)
        15,             # fade (32)
        16,             # silence (32)
        16,             # silence (32)
        16,             # silence (32)  — held to picture end
    ]

    # Effects: film-score atmosphere, deep reverb
    channel_effects = {
        0: {"reverb": 0.45},                                             # Pad root
        1: {"reverb": 0.40},                                             # Pad harm
        2: {"reverb": 0.10},                                             # Bass
        3: {"reverb": 0.32, "delay": 0.20, "delay_feedback": 0.28},     # Lead
        4: {"reverb": 0.35, "delay": 0.18, "delay_feedback": 0.25},     # Counter
        5: {"delay": 0.22, "delay_feedback": 0.30, "reverb": 0.18},     # Arp
        6: {"reverb": 0.50, "delay": 0.25, "delay_feedback": 0.20},     # Bell
    }

    panning = {0: -0.25, 1: 0.25, 2: 0.0, 3: 0.08, 4: -0.15, 5: 0.30, 6: -0.20}

    song = Song(
        title="The Mapmaker's Score v2",
        bpm=BPM,
        patterns=patterns,
        sequence=sequence,
        channel_effects=channel_effects,
        panning=panning,
        master_reverb=0.15,
        master_delay=0.08,
    )
    return song


if __name__ == "__main__":
    song = build_song()
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )
    out = Path("output/the_mapmaker_score_v2.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.1f}s ({dur/60:.1f}min) → {out}")
