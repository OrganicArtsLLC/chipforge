"""
Voices from the Grid — Vocal synthesis showcase after formant engine fix.

Tests all core vocal presets at realistic velocities and durations.
Uses Palette 4: Organic — vocal_lead_ah over vocal_choir, ks_bass,
grain_shimmer texture, vocal_chop percussion.

BPM 100 — slow enough to hear formants ring.
Key: C minor — warm and introspective.
Structure: 4-bar atmosphere → 4-bar melody + choir → 4-bar full → 4-bar resolve
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 100
SPB = 4
BAR = 16

# C Natural Minor scale: C D Eb F G Ab Bb
C_MIN = [60, 62, 63, 65, 67, 68, 70, 72, 74, 75, 77, 79]

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0: return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst, midi, vel=0.75, dur=4):
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.83),
                     duration_steps=dur, instrument=inst)

def rest():
    return None

def new_grid(channels, steps):
    return [[None] * steps for _ in range(channels)]

# ---------------------------------------------------------------------------
# Channel assignment
# CH 0: vocal_lead_ah   — melody
# CH 1: vocal_choir     — pad/harmony
# CH 2: ks_bass         — bass
# CH 3: grain_shimmer   — air texture
# CH 4: vocal_chop      — percussive rhythm
# CH 5: vocal_ensemble  — slow swell (enters later)
# ---------------------------------------------------------------------------

def pattern_atmosphere() -> Pattern:
    """4 bars: choir pad swells in, grain shimmer, no lead yet."""
    g = new_grid(6, 4 * BAR)
    steps = 4 * BAR

    # CH 1: choir — long notes, C minor chord
    for midi, start in [(60, 0), (63, 0), (67, 0),    # C Eb G (Cm)
                        (60, 32), (65, 32), (70, 32)]:  # C F Bb (Fm)
        if start < steps:
            g[1][start] = note("vocal_choir", midi, vel=0.68, dur=28)

    # CH 2: bass — slow movement
    for midi, start in [(48, 0), (48, 16), (53, 32), (53, 48)]:
        if start < steps:
            g[2][start] = note("ks_bass", midi, vel=0.72, dur=14)

    # CH 3: grain shimmer — sparse high notes
    for start in [0, 8, 19, 31, 40, 55]:
        if start < steps:
            g[3][start] = note("grain_shimmer", 79, vel=0.45, dur=6)

    return Pattern(grid=g, num_steps=4 * BAR, num_channels=6)


def pattern_melody_enters() -> Pattern:
    """4 bars: vocal lead melody enters above the choir."""
    g = new_grid(6, 4 * BAR)
    steps = 4 * BAR

    # CH 0: vocal_lead_ah melody — C minor pentatonic gesture
    melody = [
        (67, 0, 4), (67, 5, 3), (65, 9, 4),           # G G F (bar 1)
        (63, 14, 6), (60, 21, 4),                       # Eb C   (bar 2)
        (62, 26, 3), (63, 30, 3), (65, 34, 6),          # D Eb F  (bar 3)
        (63, 41, 8),                                     # Eb held (bar 4)
    ]
    for midi, start, dur in melody:
        if start < steps:
            g[0][start] = note("vocal_lead_ah", midi, vel=0.78, dur=dur)

    # CH 1: choir — same as atmosphere but Eb stays
    for midi, start in [(60, 0), (63, 0), (67, 0)]:
        g[1][start] = note("vocal_choir", midi, vel=0.65, dur=30)

    # CH 2: bass — more active
    for midi, start in [(48, 0), (48, 12), (51, 16), (56, 28), (53, 44)]:
        if start < steps:
            g[2][start] = note("ks_bass", midi, vel=0.74, dur=10)

    # CH 3: grain texture continues
    for start in [3, 14, 29, 43, 57]:
        if start < steps:
            g[3][start] = note("grain_shimmer", 77, vel=0.42, dur=5)

    # CH 4: vocal_chop enters — 3-note pulse pattern
    for start in [0, 8, 24, 32, 48]:
        if start < steps:
            g[4][start] = note("vocal_chop", 60, vel=0.72, dur=2)

    return Pattern(grid=g, num_steps=4 * BAR, num_channels=6)


def pattern_full_voice() -> Pattern:
    """4 bars: full texture — lead + choir + bass + chop + ensemble swell."""
    g = new_grid(6, 4 * BAR)
    steps = 4 * BAR

    # CH 0: melodic phrase — more movement
    melody = [
        (72, 0, 3), (70, 4, 3), (68, 8, 4),           # C Bb Ab
        (67, 13, 6),                                    # G held
        (65, 20, 3), (67, 24, 3), (70, 28, 5),         # F G Bb
        (72, 34, 6), (70, 41, 5), (68, 47, 8),         # C Bb Ab
    ]
    for midi, start, dur in melody:
        if start < steps:
            g[0][start] = note("vocal_lead_ah", midi, vel=0.80, dur=dur)

    # CH 1: choir — higher voicing
    for midi, start in [(67, 0), (70, 0), (75, 0),
                        (65, 32), (68, 32), (72, 32)]:
        if start < steps:
            g[1][start] = note("vocal_choir_ee", midi, vel=0.68, dur=28)

    # CH 2: bass — descent
    for midi, start in [(48, 0), (46, 16), (44, 32), (43, 48)]:
        if start < steps:
            g[2][start] = note("ks_bass", midi, vel=0.76, dur=14)

    # CH 3: grain — more active
    for start in [0, 6, 13, 22, 31, 38, 45, 55]:
        if start < steps:
            g[3][start] = note("grain_shimmer", 84, vel=0.40, dur=4)

    # CH 4: chop — syncopated
    for start in [0, 5, 8, 16, 21, 32, 37, 48, 53]:
        if start < steps:
            g[4][start] = note("vocal_chop", 67, vel=0.74, dur=2)

    # CH 5: vocal_ensemble slow swell
    for midi, start in [(60, 0), (63, 0), (67, 0)]:
        g[5][start] = note("vocal_ensemble", midi, vel=0.62, dur=55)

    return Pattern(grid=g, num_steps=4 * BAR, num_channels=6)


def pattern_resolve() -> Pattern:
    """4 bars: resolution — melody descends to C, layers drop away."""
    g = new_grid(6, 4 * BAR)
    steps = 4 * BAR

    # CH 0: descending resolve
    melody = [
        (67, 0, 4), (65, 5, 4), (63, 10, 5),  # G F Eb
        (62, 16, 4), (60, 21, 12),              # D → C (long)
    ]
    for midi, start, dur in melody:
        if start < steps:
            g[0][start] = note("vocal_lead_ah", midi, vel=0.74, dur=dur)

    # CH 1: choir fades — just root
    g[1][0] = note("vocal_choir", 60, vel=0.58, dur=50)

    # CH 2: bass holds root
    g[2][0] = note("ks_bass", 48, vel=0.70, dur=48)

    # CH 3: grain sparse — just a few
    for start in [12, 40]:
        g[3][start] = note("grain_shimmer", 72, vel=0.35, dur=6)

    # CH 4: chop stops — just one closing hit
    g[4][0] = note("vocal_chop", 60, vel=0.65, dur=2)

    # CH 5: ensemble holds long
    g[5][0] = note("vocal_ensemble", 60, vel=0.58, dur=60)

    return Pattern(grid=g, num_steps=4 * BAR, num_channels=6)


def build_song() -> Song:
    p0 = pattern_atmosphere()
    p1 = pattern_melody_enters()
    p2 = pattern_full_voice()
    p3 = pattern_resolve()

    song = Song(
        patterns=[p0, p1, p2, p3],
        sequence=[0, 1, 2, 3],
        bpm=BPM,
    )

    song.panning = {0: 0.08, 1: -0.15, 2: 0.0, 3: 0.25, 4: -0.10, 5: 0.05}

    song.channel_effects = {
        0: {"reverb": 0.35},                                         # Lead: room + tail
        1: {"reverb": 0.50},                                         # Choir: cathedral
        2: {"reverb": 0.10},                                         # Bass: tight
        3: {"reverb": 0.45, "delay": 0.28, "delay_feedback": 0.35}, # Shimmer: diffuse
        4: {"delay": 0.15, "delay_feedback": 0.20, "reverb": 0.12}, # Chop: bounce
        5: {"reverb": 0.55},                                         # Ensemble: hall
    }
    song.master_reverb = 0.18

    return song


if __name__ == '__main__':
    song = build_song()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb)
    out = Path('output/voices_from_the_grid.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Rendered: {len(audio)/44100:.1f}s → {out}")
    print("Vocal formant test complete.")
