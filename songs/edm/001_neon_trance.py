"""
Neon Trance — Original ChipForge Banger
=========================================
Original composition in the Cascade Protocol / Neural Cascade DNA.
Pure euphoric trance. Four-on-floor. Arp machine. The hook.

Key: E minor (i → VI → III → VII = Em → C → G → D)
BPM: 140
Channels: 7

Structure (~15s):
  [0-7s]   BUILD   4 bars — arp + bass + hats, energy rising
  [7-15s]  DROP    4 bars — full groove, lead hook, peak energy
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 140
SPB = 4
BAR = 16

def hz(m): return 440.0 * (2 ** ((m - 69) / 12.0))
def f2m(f):
    if f <= 0: return 0
    return round(12 * math.log2(f / 440.0) + 69)
def note(inst, freq, vel=0.80, dur=2):
    return NoteEvent(midi_note=f2m(freq), velocity=min(vel, 0.85),
                     duration_steps=dur, instrument=inst)
def new_grid(ch, st): return [[None] * st for _ in range(ch)]

KICK='kick_deep'; SNARE='noise_clap'; HAT_CL='hat_crisp'; HAT_OP='hat_open_shimmer'
BASS='bass_growl'; LEAD='saw_filtered'; PAD='pad_lush'; ARP='pulse_warm'

# E minor
E2=hz(40); G2=hz(43); B2=hz(47); C3=hz(48); D3=hz(50)
E3=hz(52); G3=hz(55); B3=hz(59); C4=hz(60); D4=hz(62)
E4=hz(64); G4=hz(67); B4=hz(71); C5=hz(72); D5=hz(74)
E5=hz(76); G5=hz(79)

CHORDS = [(E3, G3, B3), (C3, E3, G3), (G3, B3, D4), (D3, G3, B3)]
BASS_ROOTS = [E2, hz(36), G2, D3]

def make_build() -> Pattern:
    steps = BAR * 4
    g = new_grid(7, steps)
    for bar in range(4):
        chord = CHORDS[bar % 4]
        bs = bar * BAR
        # Hats building
        for s in range(0, BAR, 2):
            v = 0.35 + bar * 0.05
            if s % 4 == 2:
                g[2][bs+s] = note(HAT_OP, hz(46), v, 3)
            else:
                g[2][bs+s] = note(HAT_CL, hz(42), v*0.85, 2)
        # Bass enters bar 1
        if bar >= 1:
            r = BASS_ROOTS[bar % 4]
            g[3][bs] = note(BASS, r, 0.68+bar*0.04, 6)
            g[3][bs+8] = note(BASS, r*1.5, 0.55+bar*0.03, 4)
        # Arp: ascending chord tones, building velocity
        tones = list(chord) + [chord[0]*2]
        for s in range(BAR):
            t = tones[s % len(tones)]
            v = 0.35 + bar*0.06 + (s%4==0)*0.08
            g[6][bs+s] = note(ARP, t, min(v, 0.72), 2)
        # Pad
        g[5][bs] = note(PAD, chord[1], 0.28+bar*0.03, BAR)
        # Kick enters bar 2
        if bar >= 2:
            g[0][bs] = note(KICK, hz(36), 0.72+bar*0.04, 2)
            g[0][bs+8] = note(KICK, hz(36), 0.68+bar*0.04, 2)
        # Snare roll bar 4
        if bar == 3:
            for s in range(0, BAR, 2):
                g[1][bs+s] = note(SNARE, hz(40), 0.40+s*0.025, 2)
            g[0][bs+14] = None; g[0][bs+15] = None  # THE GAP

    return Pattern(name='build', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

def make_drop() -> Pattern:
    steps = BAR * 4
    g = new_grid(7, steps)
    for bar in range(4):
        chord = CHORDS[bar % 4]
        bs = bar * BAR
        # Four-on-floor + ghost
        for beat in range(4):
            g[0][bs+beat*4] = note(KICK, hz(36), 0.84, 2)
        g[0][bs+7] = note(KICK, hz(36), 0.48, 1)
        # Snare backbeat
        g[1][bs+4] = note(SNARE, hz(40), 0.80, 3)
        g[1][bs+12] = note(SNARE, hz(40), 0.78, 3)
        # Full hats
        for s in range(0, BAR, 2):
            if s in (6, 14):
                g[2][bs+s] = note(HAT_OP, hz(46), 0.55, 3)
            else:
                g[2][bs+s] = note(HAT_CL, hz(42), 0.48, 2)
        # Bass: driving
        r = BASS_ROOTS[bar % 4]
        g[3][bs] = note(BASS, r, 0.82, 4)
        g[3][bs+4] = note(BASS, r*1.5, 0.65, 3)
        g[3][bs+8] = note(BASS, r, 0.80, 4)
        g[3][bs+12] = note(BASS, r*2, 0.58, 3)
        # Arp: under melody
        tones = list(chord) + [chord[0]*2]
        for s in range(BAR):
            if g[4].count(None) > 0:  # fill gaps
                t = tones[s % len(tones)]
                g[6][bs+s] = note(ARP, t, 0.42, 2)
        # Pad
        g[5][bs] = note(PAD, chord[1], 0.34, BAR)

    # LEAD HOOK — original trance melody
    # E5(Q) G5(Q) E5(E) D5(E) C5(Q) B4(Q) — call
    # C5(Q.) B4(E) E5(H) — response (soars!)
    hook = [
        (E5, 0, 0.82, 4), (G5, 4, 0.85, 4), (E5, 8, 0.80, 2),
        (D5, 10, 0.78, 2), (C5, 12, 0.82, 4),
        (B4, 16, 0.78, 4), (C5, 20, 0.80, 6), (B4, 26, 0.75, 2),
        (E5, 28, 0.85, 8),  # soar!
        # Second phrase with peak
        (E5, 36, 0.82, 4), (G5, 40, 0.85, 4), (E5, 44, 0.82, 2),
        (D5, 46, 0.80, 2), (E5, 48, 0.85, 4),
        (D5, 52, 0.78, 2), (C5, 54, 0.80, 2), (B4, 56, 0.75, 4),
        (E5, 60, 0.85, 4),  # resolve
    ]
    for freq, step, vel, dur in hook:
        if step < steps:
            g[4][step] = note(LEAD, freq, vel, dur)

    return Pattern(name='drop', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)

def build_song() -> Song:
    return Song(
        title='Neon Trance', author='ChipForge / OA LLC', bpm=BPM,
        patterns=[make_build(), make_drop()], sequence=[0, 1],
        panning={0:0.00, 1:0.00, 2:0.28, 3:0.00, 4:0.12, 5:-0.20, 6:-0.30},
        channel_effects={
            0: {'reverb': 0.06},
            1: {'reverb': 0.15},
            2: {'delay': 0.107, 'delay_feedback': 0.25, 'reverb': 0.10},
            3: {'reverb': 0.08},
            4: {'reverb': 0.35, 'delay': 0.214, 'delay_feedback': 0.28, 'delay_mix': 0.20},
            5: {'reverb': 0.45},
            6: {'delay': 0.161, 'delay_feedback': 0.30, 'reverb': 0.15},
        },
        master_reverb=0.12, master_delay=0.06,
    )

if __name__ == '__main__':
    print("Neon Trance | 140 BPM | Em | Rendering...", flush=True)
    song = build_song()
    audio = render_song(song, panning=song.panning, channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb, master_delay=song.master_delay)
    out = Path('output/edm_001_neon_trance.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Done: {len(audio)/44100:.1f}s -> {out}")
