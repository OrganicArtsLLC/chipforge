"""quickdemo_score — 10s chiptune companion for napkinfilms/quickdemo.

5 bars at BPM 120 = 10 seconds. Upbeat, playful, curtain-raiser feel.

Run: .venv/bin/python3 quickdemo_score.py
Out: output/quickdemo_score.wav
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav

BPM = 120
BAR = 16
CH  = 5

# C major
C3, E3, G3 = 48, 52, 55
C4, D4, E4, F4, G4, A4, B4 = 60, 62, 64, 65, 67, 69, 71
C5, D5, E5, G5 = 72, 74, 76, 79


def n(inst, midi, vel=0.80, dur=2):
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=dur, instrument=inst)


def grid(steps):
    return [[None] * steps for _ in range(CH)]


def pat_intro():
    """Bars 1-2: whoosh-in feel, pad + rising arp, kick on 1."""
    g = grid(BAR * 2)
    g[0][0]  = n("kick_deep", 36, 0.55, 2)
    g[0][16] = n("kick_deep", 36, 0.50, 2)
    g[3][0]  = n("bass_sub", C3, 0.55, 16)
    g[3][16] = n("bass_sub", G3, 0.50, 16)
    rise = [C4, E4, G4, C5, E5, G5, E5, C5,
            D4, F4, A4, D5, E5, D5, C5, B4]
    for i, note in enumerate(rise):
        if i < BAR * 2:
            g[2][i * 2] = n("pulse_chime", note, 0.42, 2)
    g[4][4]  = n("pad_lush", C3, 0.35, 16)
    g[4][20] = n("pad_lush", G3, 0.32, 12)
    return Pattern(name="intro", num_steps=BAR * 2, num_channels=CH, grid=g)


def pat_groove():
    """Bars 3-4: full groove under the narrator line."""
    g = grid(BAR * 2)
    # Kick pulse
    for off in (0, 8, 16, 24):
        g[0][off] = n("kick_deep", 36, 0.50, 2)
    # Hat offbeats
    for i in range(2, BAR * 2, 4):
        g[1][i] = n("hat_crisp", 42, 0.28, 1)
    # Bass root-fifth-root-fourth walk
    g[3][0]  = n("bass_sub", C3, 0.55, 8)
    g[3][8]  = n("bass_sub", G3, 0.50, 8)
    g[3][16] = n("bass_sub", A4 - 24, 0.50, 8)  # A2
    g[3][24] = n("bass_sub", F4 - 24, 0.50, 8)  # F2
    # Lead melody — bright, singing
    lead = [(0, E5, 2), (3, G5, 2), (6, E5, 2), (9, C5, 3),
            (16, D5, 2), (18, E5, 2), (20, G5, 3), (24, E5, 4)]
    for step, note, dur in lead:
        g[2][step] = n("pulse_warm", note, 0.62, dur)
    # Pad
    g[4][0]  = n("pad_lush", C3, 0.38, 16)
    g[4][16] = n("pad_lush", E3, 0.36, 16)
    return Pattern(name="groove", num_steps=BAR * 2, num_channels=CH, grid=g)


def pat_fanfare():
    """Bar 5: fanfare + cadence to C."""
    g = grid(BAR)
    g[0][0]  = n("kick_deep", 36, 0.60, 2)
    g[0][8]  = n("kick_deep", 36, 0.55, 2)
    g[1][4]  = n("hat_crisp", 42, 0.40, 1)
    g[1][12] = n("hat_crisp", 42, 0.40, 1)
    # Fanfare: C E G C ascending, then held C
    g[2][0]  = n("pulse_warm", C5, 0.70, 2)
    g[2][3]  = n("pulse_warm", E5, 0.72, 2)
    g[2][6]  = n("pulse_warm", G5, 0.74, 2)
    g[2][9]  = n("pulse_warm", C5 + 12, 0.76, 6)  # high C hold
    g[3][0]  = n("bass_sub", C3, 0.60, 16)
    g[4][0]  = n("pad_lush", C3, 0.42, 16)
    g[4][0]  = n("pad_lush", E3, 0.38, 16)
    return Pattern(name="fanfare", num_steps=BAR, num_channels=CH, grid=g)


def build_song():
    return Song(
        title="QuickDemo Theme",
        bpm=BPM,
        patterns=[pat_intro(), pat_groove(), pat_fanfare()],
        sequence=[0, 1, 2],
        panning={0: 0.0, 1: 0.15, 2: -0.15, 3: 0.0, 4: 0.0},
        channel_effects={
            0: {"reverb": 0.08},
            1: {"reverb": 0.12},
            2: {"reverb": 0.25, "delay": 0.18, "delay_feedback": 0.25},
            3: {"reverb": 0.10},
            4: {"reverb": 0.40},
        },
        master_reverb=0.12,
        master_delay=0.06,
    )


if __name__ == "__main__":
    song = build_song()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb,
                        master_delay=song.master_delay)
    out = Path("output/quickdemo_score.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.2f}s → {out}")
