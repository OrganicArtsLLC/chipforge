"""The Mapmaker's Score — emotional film underscoring in E minor.

Atmospheric chip tune score for the Napkin Films short 'The Mapmaker'.
Builds from quiet pads through gentle theme to dark labyrinth passage
and warm resolution. Background level — designed to sit under narration.

Arc: mist → dawn → gentle theme → full bloom → shadow → storm → light → resolve
Duration: ~3:30 at BPM 84
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
# ============================================================

def p_mist() -> Pattern:
    """P0: Ethereal pad wash. Em sustained. 2 bars (32 steps)."""
    gr = g(32)
    # Pad root: E3 held
    gr[0][0]  = n(PAD, E3, 0.45, 16)
    gr[0][16] = n(PAD, E3, 0.42, 16)
    # Pad harmony: B3, gentle swell
    gr[1][4]  = n(PAD2, B3, 0.35, 14)
    gr[1][20] = n(PAD2, B3, 0.32, 12)
    # Bell: single high note, distant
    gr[6][12] = n(BELL, E5, 0.25, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=32, num_channels=CH, bpm=BPM, name="mist")


def p_dawn() -> Pattern:
    """P1: Pad + bass stirs. 4 bars. Em → C → Am → Em."""
    gr = g(64)
    # Pad root
    gr[0][0]  = n(PAD, E3, 0.48, 16)
    gr[0][16] = n(PAD, C3, 0.48, 16)
    gr[0][32] = n(PAD, A3, 0.48, 16)
    gr[0][48] = n(PAD, E3, 0.46, 16)
    # Pad harmony
    gr[1][0]  = n(PAD2, B3, 0.38, 16)
    gr[1][16] = n(PAD2, G3, 0.36, 16)
    gr[1][32] = n(PAD2, E4, 0.38, 16)
    gr[1][48] = n(PAD2, B3, 0.36, 16)
    # Bass enters bar 3
    gr[2][32] = n(BASS, A2, 0.40, 8)
    gr[2][40] = n(BASS, A2, 0.38, 8)
    gr[2][48] = n(BASS, E3, 0.42, 8)
    gr[2][56] = n(BASS, E3, 0.38, 8)
    # Bell accents
    gr[6][8]  = n(BELL, E5, 0.22, 4)
    gr[6][44] = n(BELL, G4, 0.20, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64, num_channels=CH, bpm=BPM, name="dawn")


def p_theme() -> Pattern:
    """P2: Theme melody enters. 4 bars. Em → G → Am → Em."""
    gr = g(64)
    # Pad root
    gr[0][0]  = n(PAD, E3, 0.48, 16)
    gr[0][16] = n(PAD, G3, 0.46, 16)
    gr[0][32] = n(PAD, A3, 0.48, 16)
    gr[0][48] = n(PAD, E3, 0.46, 16)
    # Pad harmony
    gr[1][0]  = n(PAD2, B3, 0.38, 16)
    gr[1][16] = n(PAD2, D4, 0.36, 16)
    gr[1][32] = n(PAD2, E4, 0.38, 16)
    gr[1][48] = n(PAD2, B3, 0.36, 16)
    # Bass: steady pulse
    for bar in range(4):
        root = [E3, G2, A2, E3][bar]
        gr[2][bar*16]     = n(BASS, root, 0.48, 8)
        gr[2][bar*16 + 8] = n(BASS, root, 0.44, 8)
    # Lead: THE THEME — ascending reach, falling home
    # Bar 1: E4 . G4 . A4 . B4 .
    gr[3][0]  = n(LEAD, E4, 0.52, 4)
    gr[3][4]  = n(LEAD, G4, 0.55, 4)
    gr[3][8]  = n(LEAD, A4, 0.58, 4)
    gr[3][12] = n(LEAD, B4, 0.56, 4)
    # Bar 2: A4 . G4 . E4 ----
    gr[3][16] = n(LEAD, A4, 0.54, 4)
    gr[3][20] = n(LEAD, G4, 0.52, 4)
    gr[3][24] = n(LEAD, E4, 0.50, 8)
    # Bar 3: G4 . A4 . B4 . D5 .
    gr[3][32] = n(LEAD, G4, 0.55, 4)
    gr[3][36] = n(LEAD, A4, 0.58, 4)
    gr[3][40] = n(LEAD, B4, 0.60, 4)
    gr[3][44] = n(LEAD, D5, 0.58, 4)
    # Bar 4: B4 . A4 . G4 . E4 ---- (resolve)
    gr[3][48] = n(LEAD, B4, 0.56, 4)
    gr[3][52] = n(LEAD, A4, 0.52, 4)
    gr[3][56] = n(LEAD, G4, 0.50, 4)
    gr[3][60] = n(LEAD, E4, 0.48, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64, num_channels=CH, bpm=BPM, name="theme")


def p_bloom() -> Pattern:
    """P3: Full arrangement with arp + counter. 4 bars. Em → G → C → Em."""
    gr = g(64)
    # Pad root
    gr[0][0]  = n(PAD, E3, 0.50, 16)
    gr[0][16] = n(PAD, G3, 0.48, 16)
    gr[0][32] = n(PAD, C3, 0.50, 16)
    gr[0][48] = n(PAD, E3, 0.48, 16)
    # Pad harmony
    gr[1][0]  = n(PAD2, B3, 0.40, 16)
    gr[1][16] = n(PAD2, D4, 0.38, 16)
    gr[1][32] = n(PAD2, G3, 0.40, 16)
    gr[1][48] = n(PAD2, B3, 0.38, 16)
    # Bass
    for bar in range(4):
        root = [E3, G2, C3, E3][bar]
        gr[2][bar*16]     = n(BASS, root, 0.50, 8)
        gr[2][bar*16 + 8] = n(BASS, root, 0.46, 8)
    # Lead: theme variation — higher, more yearning
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
    # Counter: saw_dark, slower answering line
    gr[4][4]  = n(DARK, B3, 0.40, 6)
    gr[4][12] = n(DARK, A3, 0.38, 8)
    gr[4][24] = n(DARK, G3, 0.40, 8)
    gr[4][36] = n(DARK, A3, 0.38, 6)
    gr[4][44] = n(DARK, B3, 0.40, 8)
    gr[4][56] = n(DARK, G3, 0.38, 8)
    # Arp: gentle pulse_warm arpeggios (every 4 steps)
    arp_notes = [E4, B4, G4, E5, B4, G4, E4, B3,
                 D4, B4, G4, D5, B4, G4, D4, B3]
    for i, mn in enumerate(arp_notes):
        gr[5][i * 4] = n(ARP, mn, 0.32, 3)
    # Bell
    gr[6][0]  = n(BELL, E5, 0.25, 4)
    gr[6][32] = n(BELL, 79, 0.22, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64, num_channels=CH, bpm=BPM, name="bloom")


def p_shadow() -> Pattern:
    """P4: Dark shift. 4 bars. Am → Em → Bdim → Em. Tension builds."""
    gr = g(64)
    # Pad root: darker voicings
    gr[0][0]  = n(PAD, A3, 0.50, 16)
    gr[0][16] = n(PAD, E3, 0.52, 16)
    gr[0][32] = n(PAD, B3, 0.50, 16)
    gr[0][48] = n(PAD, E3, 0.48, 16)
    # Pad harmony: minor seconds, dissonance
    gr[1][0]  = n(PAD2, C4, 0.40, 16)
    gr[1][16] = n(PAD2, B3, 0.42, 16)
    gr[1][32] = n(PAD2, D4, 0.42, 16)
    gr[1][48] = n(PAD2, G3, 0.38, 16)
    # Bass: heavier, more insistent
    for bar in range(4):
        root = [A2, E3, B2, E3][bar]
        gr[2][bar*16]     = n(BASS, root, 0.55, 6)
        gr[2][bar*16 + 8] = n(BASS, root, 0.50, 6)
        gr[2][bar*16 + 12]= n(BASS, root + 7, 0.42, 4)  # 5th pulse
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
    # Counter: dark descending motif
    gr[4][0]  = n(DARK, E4, 0.45, 4)
    gr[4][4]  = n(DARK, D4, 0.43, 4)
    gr[4][8]  = n(DARK, C4, 0.42, 4)
    gr[4][12] = n(DARK, B3, 0.40, 4)
    gr[4][32] = n(DARK, Fs4, 0.45, 4)
    gr[4][36] = n(DARK, E4, 0.43, 4)
    gr[4][40] = n(DARK, D4, 0.42, 4)
    gr[4][44] = n(DARK, B3, 0.40, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64, num_channels=CH, bpm=BPM, name="shadow")


def p_storm() -> Pattern:
    """P5: Peak intensity. 4 bars. Em → Am → B → Em. All channels active."""
    gr = g(64)
    # Pad root: full voiced
    gr[0][0]  = n(PAD, E3, 0.55, 16)
    gr[0][16] = n(PAD, A3, 0.55, 16)
    gr[0][32] = n(PAD, B3, 0.58, 16)
    gr[0][48] = n(PAD, E3, 0.55, 16)
    # Pad harmony
    gr[1][0]  = n(PAD2, G3, 0.45, 16)
    gr[1][16] = n(PAD2, C4, 0.45, 16)
    gr[1][32] = n(PAD2, Fs4, 0.48, 16)
    gr[1][48] = n(PAD2, B3, 0.45, 16)
    # Bass: driving eighths
    bass_roots = [E3, E3, A2, A2, B2, B2, E3, E3]
    for i, br in enumerate(bass_roots):
        gr[2][i * 8] = n(BASS, br, 0.58, 6)
    # Lead: climactic arc
    gr[3][0]  = n(LEAD, E4, 0.62, 4)
    gr[3][4]  = n(LEAD, G4, 0.65, 4)
    gr[3][8]  = n(LEAD, B4, 0.68, 4)
    gr[3][12] = n(LEAD, D5, 0.70, 4)
    gr[3][16] = n(LEAD, E5, 0.72, 8)
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
        gr[4][bar*16]     = n(DARK, B3, 0.48, 4)
        gr[4][bar*16 + 4] = n(DARK, E4, 0.50, 4)
        gr[4][bar*16 + 8] = n(DARK, D4, 0.48, 4)
        gr[4][bar*16 + 12]= n(DARK, B3, 0.45, 4)
    # Arp: rapid arpeggios
    arp_seq = [E4, G4, B4, E5, G4, B4, E4, G4,
               A3, C4, E4, A4, C4, E4, A3, C4]
    for i, mn in enumerate(arp_seq[:16]):
        gr[5][i * 4] = n(ARP, mn, 0.38, 3)
    # Bell: climax hit
    gr[6][16] = n(BELL, E5, 0.35, 8)
    gr[6][40] = n(BELL, B4, 0.30, 4)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64, num_channels=CH, bpm=BPM, name="storm")


def p_light() -> Pattern:
    """P6: Theme returns warmly. 4 bars. C → G → Am → Em. Resolution begins."""
    gr = g(64)
    # Pad root: brighter voicings
    gr[0][0]  = n(PAD, C3, 0.50, 16)
    gr[0][16] = n(PAD, G3, 0.48, 16)
    gr[0][32] = n(PAD, A3, 0.50, 16)
    gr[0][48] = n(PAD, E3, 0.48, 16)
    # Pad harmony
    gr[1][0]  = n(PAD2, E4, 0.40, 16)
    gr[1][16] = n(PAD2, D4, 0.38, 16)
    gr[1][32] = n(PAD2, E4, 0.40, 16)
    gr[1][48] = n(PAD2, B3, 0.38, 16)
    # Bass: gentle
    for bar in range(4):
        root = [C3, G2, A2, E3][bar]
        gr[2][bar*16] = n(BASS, root, 0.45, 12)
    # Lead: theme restated gently
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
    # Arp: sparse, winding down
    for i, mn in enumerate([E4, B4, G4, E5, B4, G4]):
        gr[5][i * 8 + 4] = n(ARP, mn, 0.28, 4)
    # Bell: peaceful
    gr[6][0]  = n(BELL, E5, 0.22, 8)
    gr[6][48] = n(BELL, B4, 0.20, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64, num_channels=CH, bpm=BPM, name="light")


def p_resolve() -> Pattern:
    """P7: Fading resolution. 4 bars. Em → C → G → Em. Sparse, peaceful."""
    gr = g(64)
    # Pad root: barely there
    gr[0][0]  = n(PAD, E3, 0.42, 16)
    gr[0][16] = n(PAD, C3, 0.40, 16)
    gr[0][32] = n(PAD, G3, 0.38, 16)
    gr[0][48] = n(PAD, E3, 0.36, 16)
    # Pad harmony
    gr[1][0]  = n(PAD2, B3, 0.32, 16)
    gr[1][16] = n(PAD2, G3, 0.30, 16)
    gr[1][32] = n(PAD2, B3, 0.30, 16)
    gr[1][48] = n(PAD2, B3, 0.28, 16)
    # Bass: single notes per bar
    gr[2][0]  = n(BASS, E3, 0.38, 16)
    gr[2][32] = n(BASS, G2, 0.35, 16)
    # Lead: just the opening motif, fragile
    gr[3][0]  = n(LEAD, E4, 0.42, 4)
    gr[3][4]  = n(LEAD, G4, 0.44, 4)
    gr[3][8]  = n(LEAD, A4, 0.42, 8)
    gr[3][48] = n(LEAD, E4, 0.38, 8)
    gr[3][56] = n(LEAD, D4, 0.35, 8)
    # Bell: final whisper
    gr[6][16] = n(BELL, E5, 0.18, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=64, num_channels=CH, bpm=BPM, name="resolve")


def p_fade() -> Pattern:
    """P8: Silence approaches. 2 bars. Em only. Pad and bell."""
    gr = g(32)
    gr[0][0]  = n(PAD, E3, 0.35, 16)
    gr[0][16] = n(PAD, E3, 0.28, 16)
    gr[1][8]  = n(PAD2, B3, 0.25, 12)
    gr[6][0]  = n(BELL, E5, 0.15, 8)
    return Pattern(grid=gr, steps_per_beat=SPB, num_steps=32, num_channels=CH, bpm=BPM, name="fade")


# ============================================================
#  BUILD SONG
# ============================================================

def build_song() -> Song:
    """Assemble all patterns into the scored film arc."""
    patterns = [
        p_mist(),    # 0 — 2 bars
        p_dawn(),    # 1 — 4 bars
        p_theme(),   # 2 — 4 bars
        p_bloom(),   # 3 — 4 bars
        p_shadow(),  # 4 — 4 bars
        p_storm(),   # 5 — 4 bars
        p_light(),   # 6 — 4 bars
        p_resolve(), # 7 — 4 bars
        p_fade(),    # 8 — 2 bars
    ]

    # Film arc sequence (~100 bars ≈ 3:34 at BPM 84)
    # mist → mist → dawn → dawn → theme → bloom → theme → shadow → storm →
    # shadow → light → bloom → theme → light → resolve → resolve → fade → fade
    sequence = [0, 0, 1, 1, 2, 3, 2, 4, 5, 4, 6, 3, 2, 6, 7, 7, 8, 8]

    # Effects: heavy reverb, film-score atmosphere
    channel_effects = {
        0: {"reverb": 0.45},                                             # Pad root: deep hall
        1: {"reverb": 0.40},                                             # Pad harm: deep hall
        2: {"reverb": 0.10},                                             # Bass: tight room
        3: {"reverb": 0.32, "delay": 0.20, "delay_feedback": 0.28},     # Lead: slapback + hall
        4: {"reverb": 0.35, "delay": 0.18, "delay_feedback": 0.25},     # Counter: dark space
        5: {"delay": 0.22, "delay_feedback": 0.30, "reverb": 0.18},     # Arp: rhythmic echo
        6: {"reverb": 0.50, "delay": 0.25, "delay_feedback": 0.20},     # Bell: cavernous
    }

    # Stereo: pads wide, lead center, bass center
    panning = {0: -0.25, 1: 0.25, 2: 0.0, 3: 0.08, 4: -0.15, 5: 0.30, 6: -0.20}

    song = Song(
        title="The Mapmaker's Score",
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
    out = Path("output/the_mapmaker_score.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.1f}s ({dur/60:.1f}min) → {out}")
