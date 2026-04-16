"""Moonlight Waltz — A dreamy, whimsical chiptune for the moonlight dance scene.

Musical design:
  - Key: G major (innocent, warm, open)
  - BPM: 108 (gentle waltz feel, 3/4 adapted to 4/4 grid)
  - Mood: Music box + starlight + gentle wonder
  - Structure: Intro shimmer → dancing melody → quiet moongazing outro
  - 15 seconds of scene, but we give ~20s of music (trimmed by scorer)

Channels:
  0: Soft kick (kick_deep, sparse, felt not heard)
  1: Gentle hat (hat_crisp, quiet ticks like a music box mechanism)
  2: Music box arpeggio (pulse_chime, the main sparkle)
  3: Warm bass (bass_sub, gentle root notes)
  4: Lead melody (pulse_warm, sweet and singing)
  5: Pad (pad_lush, dreamy wash underneath everything)
  6: Counter melody / bells (gb_bell_wave, high twinkling)
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 108
SPB = 4
BAR = 16

# G major scale MIDI notes
# G A B C D E F#
G2, A2, B2 = 43, 45, 47
C3, D3, E3, Fs3, G3, A3, B3 = 48, 50, 52, 54, 55, 57, 59
C4, D4, E4, Fs4, G4, A4, B4 = 60, 62, 64, 66, 67, 69, 71
C5, D5, E5, Fs5, G5 = 72, 74, 76, 78, 79

CH = 7


def n(inst: str, midi: int, vel: float = 0.80, dur: int = 2) -> NoteEvent:
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=dur, instrument=inst)


def new_grid(channels: int, steps: int) -> list[list[NoteEvent | None]]:
    return [[None] * steps for _ in range(channels)]


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def pat_intro_shimmer() -> Pattern:
    """Bars 1-2: Pad fades in with music box sparkle. No drums. Dreamy."""
    g = new_grid(CH, BAR * 2)
    # Pad: sustained G major chord
    g[5][0] = n("pad_lush", G3, 0.35, 16)
    g[5][8] = n("pad_lush", B3, 0.30, 16)
    g[5][16] = n("pad_lush", D4, 0.32, 16)

    # Music box: gentle descending arpeggio, spaced out
    arp_notes = [G5, E5, D5, B4, G4, D5, E5, G5]
    for i, note in enumerate(arp_notes):
        step = i * 4
        if step < BAR * 2:
            g[2][step] = n("pulse_chime", note, 0.40 + i * 0.03, 3)

    # Bell accents
    g[6][6] = n("gb_bell_wave", B4, 0.30, 4)
    g[6][18] = n("gb_bell_wave", D5, 0.28, 4)
    g[6][26] = n("gb_bell_wave", G5, 0.25, 6)
    return Pattern(name="intro_shimmer", num_steps=BAR * 2, num_channels=CH, grid=g)


def pat_dance_a() -> Pattern:
    """Bars 3-4: Dance begins. Light kick, arp picks up, melody enters."""
    g = new_grid(CH, BAR * 2)
    # Kick: gentle on 1 and 9 (waltz-ish: beat 1 and 3)
    for bar in range(2):
        off = bar * BAR
        g[0][off] = n("kick_deep", 36, 0.45, 2)
        g[0][off + 8] = n("kick_deep", 36, 0.35, 2)

    # Hat: every 4th step, very soft (music box ticking)
    for i in range(0, BAR * 2, 4):
        g[1][i + 2] = n("hat_crisp", 42, 0.25, 1)

    # Bass: root movement G → D
    g[3][0] = n("bass_sub", G2, 0.55, 8)
    g[3][8] = n("bass_sub", D3, 0.50, 8)
    g[3][16] = n("bass_sub", E3, 0.52, 8)
    g[3][24] = n("bass_sub", D3, 0.50, 8)

    # Music box arp: flowing sixteenths, G major arpeggios
    arp = [G4, B4, D5, G5, D5, B4, E4, G4, B4, E5, B4, G4,
           D4, Fs4, A4, D5, A4, Fs4, G4, B4, D5, G5, D5, B4,
           E4, G4, B4, E5, B4, G4, D4, A4]
    for i, note in enumerate(arp):
        if i < BAR * 2:
            g[2][i] = n("pulse_chime", note, 0.45, 2)

    # Lead melody: sweet, singable (the dance tune)
    # Bar 1: G4. B4.. D5. E5 D5..
    g[4][0] = n("pulse_warm", G4, 0.60, 2)
    g[4][3] = n("pulse_warm", B4, 0.62, 3)
    g[4][6] = n("pulse_warm", D5, 0.65, 2)
    g[4][9] = n("pulse_warm", E5, 0.63, 2)
    g[4][11] = n("pulse_warm", D5, 0.60, 3)
    # Bar 2: B4. A4 G4.. E4. G4...
    g[4][16] = n("pulse_warm", B4, 0.62, 2)
    g[4][18] = n("pulse_warm", A4, 0.58, 2)
    g[4][20] = n("pulse_warm", G4, 0.60, 3)
    g[4][24] = n("pulse_warm", E4, 0.55, 2)
    g[4][27] = n("pulse_warm", G4, 0.58, 4)

    # Pad: sustained warmth
    g[5][0] = n("pad_lush", G3, 0.38, 16)
    g[5][16] = n("pad_lush", D3, 0.35, 16)

    # Bells: high sparkle accents
    g[6][4] = n("gb_bell_wave", G5, 0.28, 3)
    g[6][14] = n("gb_bell_wave", E5, 0.25, 3)
    g[6][20] = n("gb_bell_wave", D5, 0.27, 4)
    g[6][28] = n("gb_bell_wave", B4, 0.24, 4)
    return Pattern(name="dance_a", num_steps=BAR * 2, num_channels=CH, grid=g)


def pat_dance_b() -> Pattern:
    """Bars 5-6: Dance intensifies. Rising melody, fuller arp, twirl energy."""
    g = new_grid(CH, BAR * 2)
    # Kick
    for bar in range(2):
        off = bar * BAR
        g[0][off] = n("kick_deep", 36, 0.50, 2)
        g[0][off + 6] = n("kick_deep", 36, 0.35, 2)
        g[0][off + 12] = n("kick_deep", 36, 0.40, 2)

    # Hat: more active (the twirl section)
    for i in range(0, BAR * 2, 2):
        g[1][i + 1] = n("hat_crisp", 42, 0.28, 1)

    # Bass: ascending (builds energy)
    g[3][0] = n("bass_sub", C3, 0.55, 8)
    g[3][8] = n("bass_sub", D3, 0.55, 8)
    g[3][16] = n("bass_sub", E3, 0.55, 8)
    g[3][24] = n("bass_sub", G3, 0.58, 8)

    # Music box: faster sparkle pattern
    arp = [C4, E4, G4, C5, E5, G5, E5, C5, D4, Fs4, A4, D5,
           Fs5, D5, A4, Fs4, E4, G4, B4, E5, G5, E5, B4, G4,
           G4, B4, D5, G5, B4, D5, G5, D5]
    for i, note in enumerate(arp):
        if i < BAR * 2:
            g[2][i] = n("pulse_chime", note, 0.48, 2)

    # Lead melody: higher, joyful (the twirl & kick)
    g[4][0] = n("pulse_warm", E5, 0.65, 2)
    g[4][2] = n("pulse_warm", D5, 0.62, 2)
    g[4][4] = n("pulse_warm", E5, 0.65, 2)
    g[4][6] = n("pulse_warm", G5, 0.68, 3)
    g[4][10] = n("pulse_warm", E5, 0.63, 2)
    g[4][12] = n("pulse_warm", D5, 0.60, 4)
    # Bar 2: descending, landing from the spin
    g[4][16] = n("pulse_warm", G5, 0.70, 3)
    g[4][20] = n("pulse_warm", E5, 0.65, 2)
    g[4][22] = n("pulse_warm", D5, 0.62, 2)
    g[4][24] = n("pulse_warm", B4, 0.58, 3)
    g[4][28] = n("pulse_warm", G4, 0.55, 4)

    # Pad: richer chord (C major → G major)
    g[5][0] = n("pad_lush", C3, 0.40, 16)
    g[5][16] = n("pad_lush", G3, 0.42, 16)

    # Bells: cascading down (post-twirl sparkle)
    g[6][2] = n("gb_bell_wave", G5, 0.32, 2)
    g[6][5] = n("gb_bell_wave", E5, 0.30, 2)
    g[6][8] = n("gb_bell_wave", D5, 0.28, 2)
    g[6][11] = n("gb_bell_wave", B4, 0.26, 3)
    g[6][18] = n("gb_bell_wave", G5, 0.30, 3)
    g[6][24] = n("gb_bell_wave", D5, 0.28, 4)
    return Pattern(name="dance_b", num_steps=BAR * 2, num_channels=CH, grid=g)


def pat_moongazing() -> Pattern:
    """Bars 7-8: Everything quiets down. Character sees the moon.
    Drums drop out. Just pad, one lonely melody note, and bells."""
    g = new_grid(CH, BAR * 2)

    # No kick, no hat — sudden stillness

    # Bass: single low G, very soft, long
    g[3][0] = n("bass_sub", G2, 0.35, 16)
    g[3][16] = n("bass_sub", D3, 0.30, 16)

    # Music box: slowing down... just a few notes, spaced wide
    g[2][0] = n("pulse_chime", G5, 0.35, 4)
    g[2][8] = n("pulse_chime", D5, 0.30, 4)
    g[2][16] = n("pulse_chime", B4, 0.28, 6)
    g[2][26] = n("pulse_chime", G4, 0.25, 6)

    # Lead: one long, tender note — the "...oh." moment
    g[4][4] = n("pulse_warm", B4, 0.50, 8)
    g[4][18] = n("pulse_warm", G4, 0.45, 10)

    # Pad: wide, warm, enveloping
    g[5][0] = n("pad_lush", G3, 0.42, 16)
    g[5][4] = n("pad_lush", B3, 0.38, 12)
    g[5][16] = n("pad_lush", G3, 0.40, 16)
    g[5][20] = n("pad_lush", D4, 0.36, 12)

    # Bell: distant, high, like a star
    g[6][2] = n("gb_bell_wave", G5, 0.22, 6)
    g[6][12] = n("gb_bell_wave", D5, 0.20, 6)
    g[6][22] = n("gb_bell_wave", B4, 0.18, 8)
    return Pattern(name="moongazing", num_steps=BAR * 2, num_channels=CH, grid=g)


def pat_outro() -> Pattern:
    """Bars 9-10: Final fade. Just pad and one last bell."""
    g = new_grid(CH, BAR * 2)

    # Pad: final G major chord, slowly dying
    g[5][0] = n("pad_lush", G3, 0.35, 16)
    g[5][4] = n("pad_lush", B3, 0.30, 16)
    g[5][8] = n("pad_lush", D4, 0.28, 16)
    g[5][16] = n("pad_lush", G3, 0.20, 16)

    # One last bell — goodnight
    g[6][4] = n("gb_bell_wave", G5, 0.20, 8)
    g[6][20] = n("gb_bell_wave", D5, 0.12, 8)

    # One last music box note
    g[2][0] = n("pulse_chime", B4, 0.22, 6)
    return Pattern(name="outro", num_steps=BAR * 2, num_channels=CH, grid=g)


# ══════════════════════════════════════════════════════════════════════════════
# BUILD SONG
# ══════════════════════════════════════════════════════════════════════════════

def build_song() -> Song:
    patterns = [
        pat_intro_shimmer(),   # 0 — bars 1-2: shimmer in
        pat_dance_a(),         # 1 — bars 3-4: dance begins
        pat_dance_b(),         # 2 — bars 5-6: twirl energy
        pat_moongazing(),      # 3 — bars 7-8: stillness, wonder
        pat_outro(),           # 4 — bars 9-10: fade
    ]

    song = Song(
        title="Moonlight Waltz",
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2, 3, 4],
        panning={
            0: 0.0,    # kick: center
            1: 0.15,   # hat: slight right
            2: -0.25,  # music box: left
            3: 0.0,    # bass: center
            4: 0.10,   # lead: slight right
            5: -0.15,  # pad: slight left
            6: 0.30,   # bells: right
        },
        channel_effects={
            0: {"reverb": 0.08},
            1: {"reverb": 0.15, "delay": 0.12, "delay_feedback": 0.20},
            2: {"reverb": 0.35, "delay": 0.25, "delay_feedback": 0.35},
            3: {"reverb": 0.10},
            4: {"reverb": 0.30, "delay": 0.18, "delay_feedback": 0.25},
            5: {"reverb": 0.45},
            6: {"reverb": 0.40, "delay": 0.30, "delay_feedback": 0.40},
        },
        master_reverb=0.15,
        master_delay=0.08,
    )
    return song


if __name__ == '__main__':
    song = build_song()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb,
                        master_delay=song.master_delay)
    out = Path('output/moonlight_waltz.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.1f}s → {out}")
