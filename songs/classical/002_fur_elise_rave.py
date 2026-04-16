"""
Fur Elise — Rave Remix
=======================
Beethoven's iconic melody reimagined as a 138 BPM trance banger.
The famous E-D#-E-D#-E-B-D-C-A motif becomes the drop hook
over four-on-floor kicks, bass_growl, and full effects.

Key: A minor
BPM: 138
Channels: 7
  0 - Kick (kick_deep — four-on-floor)
  1 - Snare/Clap (noise_clap — fat backbeat)
  2 - Hi-hat (hat_crisp + hat_open_shimmer)
  3 - Bass (bass_growl — driving root-fifth)
  4 - Lead melody (saw_filtered — Fur Elise hook, warm)
  5 - Pad (pad_lush — Am warmth floor)
  6 - Arp (pulse_warm — chord tone arpeggios)

Structure (~18s at 138 BPM):
  [0-7s]   BUILD    4 bars — arp + hats + bass, melody teases
  [7-18s]  DROP     6 bars — full groove, Fur Elise hook DROPS
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 138
SPB = 4
BAR = 16

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0: return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst, freq, vel=0.80, dur=2):
    return NoteEvent(midi_note=freq_to_midi(freq), velocity=min(vel, 0.85),
                     duration_steps=dur, instrument=inst)

def new_grid(channels, steps):
    return [[None] * steps for _ in range(channels)]

# Instruments
KICK  = 'kick_deep'
SNARE = 'noise_clap'
HAT_CL = 'hat_crisp'
HAT_OP = 'hat_open_shimmer'
BASS  = 'bass_growl'
LEAD  = 'saw_filtered'
PAD   = 'pad_lush'
ARP   = 'pulse_warm'

# A minor notes
E3 = hz(52); A2 = hz(45); E2 = hz(40); B2 = hz(47); C3 = hz(48)
D3 = hz(50); F3 = hz(53); G3 = hz(55)
A3 = hz(57); B3 = hz(59); C4 = hz(60); D4 = hz(62); E4 = hz(64)
F4 = hz(65); G4 = hz(67); A4 = hz(69); B4 = hz(71); C5 = hz(72)
D5 = hz(74); Ds5 = hz(75); E5 = hz(76)

# Am chord voicings
CHORDS = {
    'Am': (A3, C4, E4),
    'E':  (E3, B3, E4),
    'F':  (F3, A3, C4),
    'C':  (C4, E4, G4),
}

def make_build() -> Pattern:
    """4 bars: Arp + hats + bass build. Melody teases last 2 bars."""
    steps = BAR * 4
    g = new_grid(7, steps)
    chord_seq = ['Am', 'E', 'Am', 'E']

    for bar in range(4):
        chord = CHORDS[chord_seq[bar]]
        bs = bar * BAR

        # Hats: 8th notes, building
        for s in range(0, BAR, 2):
            if s % 4 == 0:
                g[2][bs + s] = note(HAT_CL, hz(42), 0.40 + bar * 0.04, 2)
            else:
                g[2][bs + s] = note(HAT_OP, hz(46), 0.35 + bar * 0.03, 3)

        # Bass: enters bar 1
        if bar >= 1:
            root = A2 if 'Am' in chord_seq[bar] else E2
            g[3][bs] = note(BASS, root, 0.65 + bar * 0.04, 6)
            g[3][bs + 8] = note(BASS, root * 1.5, 0.52 + bar * 0.03, 4)

        # Arp: smooth chord tones
        tones = list(chord)
        arp_vel = 0.38 + bar * 0.05
        for s in range(0, BAR, 2):
            t = tones[s // 2 % len(tones)]
            g[6][bs + s] = note(ARP, t, arp_vel, 3)

        # Pad: warmth floor
        g[5][bs] = note(PAD, chord[1], 0.28 + bar * 0.03, BAR)

        # Kick: enters bar 2, half-time
        if bar >= 2:
            g[0][bs] = note(KICK, hz(36), 0.75, 2)
            g[0][bs + 8] = note(KICK, hz(36), 0.70, 2)

        # Melody tease: bars 2-3, just first 4 notes of Fur Elise
        if bar == 2:
            g[4][bs] = note(LEAD, E5, 0.65, 2)
            g[4][bs + 2] = note(LEAD, Ds5, 0.60, 2)
            g[4][bs + 4] = note(LEAD, E5, 0.65, 2)
            g[4][bs + 6] = note(LEAD, Ds5, 0.60, 2)

        # Snare roll bar 4 (tension!)
        if bar == 3:
            for s in range(0, BAR, 2):
                roll_vel = 0.40 + s * 0.025
                g[1][bs + s] = note(SNARE, hz(40), min(roll_vel, 0.80), 2)
            # THE GAP
            g[0][bs + 14] = None
            g[0][bs + 15] = None

    return Pattern(name='build', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_drop() -> Pattern:
    """6 bars: THE DROP. Full four-on-floor + Fur Elise melody as the hook.
    The famous E-D#-E-D#-E-B-D-C-A motif played twice with full groove."""
    steps = BAR * 6
    g = new_grid(7, steps)
    chord_seq = ['Am', 'E', 'Am', 'C', 'F', 'E']

    for bar in range(6):
        chord = CHORDS[chord_seq[bar]]
        bs = bar * BAR

        # Four-on-floor kick + ghost
        for beat in range(4):
            g[0][bs + beat * 4] = note(KICK, hz(36), 0.82, 2)
        g[0][bs + 7] = note(KICK, hz(36), 0.45, 1)  # ghost

        # Snare: beats 2 and 4
        g[1][bs + 4] = note(SNARE, hz(40), 0.78, 3)
        g[1][bs + 12] = note(SNARE, hz(40), 0.75, 3)

        # Hats: full 8th stream
        for s in range(0, BAR, 2):
            if s % 4 == 2:
                g[2][bs + s] = note(HAT_OP, hz(46), 0.50, 3)
            else:
                g[2][bs + s] = note(HAT_CL, hz(42), 0.45, 2)

        # Bass: driving root-fifth
        root = hz(45) if chord_seq[bar] == 'Am' else hz(40) if chord_seq[bar] == 'E' \
               else hz(48) if chord_seq[bar] == 'C' else hz(41)
        g[3][bs] = note(BASS, root, 0.80, 4)
        g[3][bs + 4] = note(BASS, root * 1.5, 0.62, 3)
        g[3][bs + 8] = note(BASS, root, 0.78, 4)
        g[3][bs + 12] = note(BASS, root * 2, 0.58, 3)

        # Arp: chord tones under melody
        tones = list(chord)
        for s in range(0, BAR, 2):
            t = tones[s // 2 % len(tones)]
            g[6][bs + s] = note(ARP, t, 0.42, 3)

        # Pad
        g[5][bs] = note(PAD, chord[1], 0.32, BAR)

    # ── FUR ELISE MELODY — the hook! ──────────────────────────────────
    # First statement (bars 0-2): E5-D#5-E5-D#5-E5-B4-D5-C5-A4
    hook1 = [
        (E5,  0,  0.82, 2), (Ds5, 2,  0.78, 2), (E5,  4,  0.82, 2),
        (Ds5, 6,  0.78, 2), (E5,  8,  0.82, 2), (B4,  10, 0.75, 2),
        (D5,  12, 0.78, 2), (C5,  14, 0.75, 2),
        # Bar 2: A4 resolves, then ascending response
        (A4,  16, 0.80, 4),
        (C4,  20, 0.65, 2), (E4,  22, 0.68, 2),
        (A4,  24, 0.72, 4),
        (B4,  28, 0.68, 2), (C5,  30, 0.72, 2),
    ]
    for freq, step, vel, dur in hook1:
        if step < steps:
            g[4][step] = note(LEAD, freq, vel, dur)

    # Second statement (bars 3-5): repeat with variation, peak higher
    hook2 = [
        (E5,  48, 0.85, 2), (Ds5, 50, 0.80, 2), (E5,  52, 0.85, 2),
        (Ds5, 54, 0.80, 2), (E5,  56, 0.85, 2), (B4,  58, 0.78, 2),
        (D5,  60, 0.80, 2), (C5,  62, 0.78, 2),
        # Resolution + climb
        (A4,  64, 0.82, 4),
        (E4,  68, 0.70, 2), (A4,  70, 0.75, 2),
        (C5,  72, 0.78, 4),
        (E5,  76, 0.85, 4),  # peak! held
        # Final descent
        (D5,  80, 0.78, 2), (C5,  82, 0.75, 2),
        (B4,  84, 0.72, 4),
        (A4,  88, 0.80, 6),  # resolve home, sustained
    ]
    for freq, step, vel, dur in hook2:
        if step < steps:
            g[4][step] = note(LEAD, freq, vel, dur)

    # Snare fills at transitions
    for bar in [2, 5]:
        bs = bar * BAR
        g[1][bs + 13] = note(SNARE, hz(40), 0.50, 2)
        g[1][bs + 14] = note(SNARE, hz(40), 0.60, 1)
        g[1][bs + 15] = note(SNARE, hz(40), 0.72, 1)

    return Pattern(name='drop', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def build_song() -> Song:
    return Song(
        title='Fur Elise — Rave Remix',
        author='ChipForge / Joshua Ayson (OA LLC) — after Beethoven',
        bpm=BPM,
        patterns=[make_build(), make_drop()],
        sequence=[0, 1],
        panning={
            0: 0.00, 1: 0.00, 2: 0.28, 3: 0.00,
            4: 0.12, 5: -0.20, 6: -0.30,
        },
        channel_effects={
            0: {'reverb': 0.08},
            1: {'reverb': 0.15},
            2: {'delay': 0.12, 'delay_feedback': 0.25, 'reverb': 0.10},
            3: {'reverb': 0.08},
            4: {'reverb': 0.30, 'delay': 0.217, 'delay_feedback': 0.25, 'delay_mix': 0.18},
            5: {'reverb': 0.45},
            6: {'delay': 0.18, 'delay_feedback': 0.30, 'reverb': 0.12},
        },
        master_reverb=0.10,
        master_delay=0.05,
    )

if __name__ == '__main__':
    print("Fur Elise — Rave Remix | 138 BPM | Am")
    print("Rendering...", flush=True)
    song = build_song()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb,
                        master_delay=song.master_delay)
    out = Path('output/classical_002_fur_elise_rave.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Done: {len(audio)/44100:.1f}s -> {out}")
