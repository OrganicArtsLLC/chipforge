"""
G-Funk Bounce — West Coast Chip Swagger
=========================================
In the DNA of Pac-Man Drizzle. Syncopated groove, chromatic bass walks,
half-time drag. The head-nod tempo.

Key: G minor
BPM: 96
Channels: 7

Structure (~50s, 20 bars):
  [0-10s]   INTRO      4 bars — bass + pad + arp, no drums, establishing the groove
  [10-20s]  GROOVE     4 bars — the bounce establishes, bass leads
  [20-30s]  HOOK       4 bars — melody drops, full swagger
  [30-40s]  BREAKDOWN  4 bars — breathe moment, stripped to pad + filtered arp + sparse kick
  [40-50s]  HOOK       4 bars — melody returns for the closer
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 96
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
BASS='bass_growl'; LEAD='lead_bright'; PAD='pad_lush'; ARP='pulse_arp'

# G minor
G2=hz(43); Ab2=hz(44); A2=hz(45); Bb2=hz(46); C3=hz(48); D3=hz(50); Eb3=hz(51)
F3=hz(53); G3=hz(55); Ab3=hz(56); Bb3=hz(58); C4=hz(60); D4=hz(62); Eb4=hz(63)
F4=hz(65); G4=hz(67); Ab4=hz(68); Bb4=hz(70); C5=hz(72); D5=hz(74); Eb5=hz(75)
G5=hz(79)

def make_intro() -> Pattern:
    """4 bars: No drums. Bass + pad + arp establish the groove before the beat drops."""
    steps = BAR * 4
    g = new_grid(7, steps)
    bass_roots = [G2, Bb2, C3, D3]

    for bar in range(4):
        bs = bar * BAR
        root = bass_roots[bar]

        # Bass: same chromatic walk as groove, slightly quieter
        g[3][bs] = note(BASS, root, 0.72, 4)
        chromatic = root * (2 ** (1/12))
        g[3][bs+4] = note(BASS, chromatic, 0.55, 2)
        g[3][bs+6] = note(BASS, root * 1.5, 0.60, 4)
        g[3][bs+10] = note(BASS, root, 0.64, 4)
        g[3][bs+14] = note(BASS, root * (2**(2/12)), 0.48, 2)

        # Pad: Gm warmth, slightly louder to fill the space without drums
        chord_notes = [(G3, Bb3, D4), (Bb3, D4, F4), (C4, Eb4, G4), (D4, F4, Bb4)]
        g[5][bs] = note(PAD, chord_notes[bar][1], 0.38, BAR)

        # Arp: Pac-Man style but sparse — only first half of each bar, building
        arp_notes = [G4, Bb4, D5, Bb4, G4, D4, G4, Bb4,
                     None, None, None, None, None, None, None, None]
        # Bars 2-3: fill in more arp notes to build anticipation
        if bar >= 2:
            arp_notes = [G4, Bb4, D5, Bb4, G4, D4, G4, Bb4,
                         D5, Eb5, D5, Bb4, None, None, None, None]
        for s, n_freq in enumerate(arp_notes):
            if n_freq is not None:
                v = 0.35 + (s % 4 == 0) * 0.08 + bar * 0.02
                g[6][bs+s] = note(ARP, n_freq, v, 2)

    return Pattern(name='intro', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_groove() -> Pattern:
    """4 bars: The bounce. Syncopated kick, chromatic bass, lazy hats."""
    steps = BAR * 4
    g = new_grid(7, steps)
    bass_roots = [G2, Bb2, C3, D3]

    for bar in range(4):
        bs = bar * BAR
        root = bass_roots[bar]

        # Syncopated kick — G-funk style (NOT four-on-floor)
        g[0][bs] = note(KICK, hz(36), 0.82, 2)
        g[0][bs+6] = note(KICK, hz(36), 0.68, 2)     # syncopated!
        g[0][bs+10] = note(KICK, hz(36), 0.72, 2)

        # Snare: beats 2 and 4, beat 4 drags (lower vel)
        g[1][bs+4] = note(SNARE, hz(40), 0.78, 3)
        g[1][bs+12] = note(SNARE, hz(40), 0.72, 3)    # drag

        # Hats: 16th stream with swing accents (all dur=2 minimum)
        for s in range(BAR):
            if s % 4 == 0:
                g[2][bs+s] = note(HAT_CL, hz(42), 0.52, 2)
            elif s % 2 == 0:
                g[2][bs+s] = note(HAT_CL, hz(42), 0.35, 2)
            else:
                g[2][bs+s] = note(HAT_CL, hz(42), 0.22, 2)

        # Bass: chromatic walk — the drizzle
        g[3][bs] = note(BASS, root, 0.80, 4)
        # Chromatic passing tone (half step up from root)
        chromatic = root * (2 ** (1/12))  # one semitone up
        g[3][bs+4] = note(BASS, chromatic, 0.62, 2)
        g[3][bs+6] = note(BASS, root * 1.5, 0.68, 4)  # fifth
        g[3][bs+10] = note(BASS, root, 0.72, 4)
        g[3][bs+14] = note(BASS, root * (2**(2/12)), 0.55, 2)  # whole step walk

        # Pad: Gm warmth
        chord_notes = [(G3, Bb3, D4), (Bb3, D4, F4), (C4, Eb4, G4), (D4, F4, Bb4)]
        chord = chord_notes[bar]
        g[5][bs] = note(PAD, chord[1], 0.30, BAR)

        # Wakka arp: Pac-Man style 16th note runs
        arp_notes = [G4, Bb4, D5, Bb4, G4, D4, G4, Bb4,
                     D5, Eb5, D5, Bb4, G4, Bb4, None, None]  # mouth closes!
        for s, n_freq in enumerate(arp_notes):
            if n_freq is not None:
                v = 0.42 + (s % 4 == 0) * 0.10
                g[6][bs+s] = note(ARP, n_freq, v + bar*0.02, 2)

    # THE GAP — clear last 2 kick hits in final bar so the hook drop hits harder
    last_bar_start = 3 * BAR
    g[0][last_bar_start + 6] = None   # remove syncopated kick
    g[0][last_bar_start + 10] = None  # remove late kick

    return Pattern(name='groove', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_hook() -> Pattern:
    """4 bars: Lead melody drops. Full G-funk swagger."""
    steps = BAR * 4
    g = new_grid(7, steps)
    bass_roots = [G2, Bb2, C3, D3]

    for bar in range(4):
        bs = bar * BAR
        root = bass_roots[bar]

        # Same groove foundation
        g[0][bs] = note(KICK, hz(36), 0.84, 2)
        g[0][bs+6] = note(KICK, hz(36), 0.70, 2)
        g[0][bs+10] = note(KICK, hz(36), 0.74, 2)

        g[1][bs+4] = note(SNARE, hz(40), 0.80, 3)
        g[1][bs+12] = note(SNARE, hz(40), 0.74, 3)

        for s in range(BAR):
            if s % 4 == 0:
                g[2][bs+s] = note(HAT_CL, hz(42), 0.55, 2)
            elif s % 2 == 0:
                g[2][bs+s] = note(HAT_CL, hz(42), 0.38, 2)
            else:
                g[2][bs+s] = note(HAT_CL, hz(42), 0.24, 2)

        # Bass: same chromatic walk
        g[3][bs] = note(BASS, root, 0.82, 4)
        g[3][bs+4] = note(BASS, root * (2**(1/12)), 0.64, 2)
        g[3][bs+6] = note(BASS, root * 1.5, 0.70, 4)
        g[3][bs+10] = note(BASS, root, 0.74, 4)
        g[3][bs+14] = note(BASS, root * (2**(2/12)), 0.58, 2)

        chord_notes = [(G3, Bb3, D4), (Bb3, D4, F4), (C4, Eb4, G4), (D4, F4, Bb4)]
        g[5][bs] = note(PAD, chord_notes[bar][1], 0.34, BAR)

        # Arp continues but quieter under melody
        arp_notes = [G4, Bb4, D5, Bb4, G4, D4, G4, Bb4,
                     D5, Eb5, D5, Bb4, G4, Bb4, None, None]
        for s, n_freq in enumerate(arp_notes):
            if n_freq is not None:
                g[6][bs+s] = note(ARP, n_freq, 0.35, 2)

    # LEAD HOOK — bluesy G minor melody with chromatic swagger
    hook = [
        # Bar 0: opening phrase — G5 announce
        (G5,  0,  0.85, 4), (D5,  4,  0.78, 2), (Eb5, 6,  0.75, 2),
        (D5,  8,  0.80, 4), (Bb4, 12, 0.72, 4),
        # Bar 1: response — chromatic passing (Ab4!)
        (C5,  16, 0.78, 4), (Bb4, 20, 0.72, 2), (Ab4, 22, 0.68, 2),  # Ab = the drizzle
        (G4,  24, 0.75, 4), (Bb4, 28, 0.70, 4),
        # Bar 2: builds back up
        (C5,  32, 0.78, 2), (D5,  34, 0.80, 2), (Eb5, 36, 0.82, 4),
        (D5,  40, 0.78, 2), (C5,  42, 0.75, 2), (Bb4, 44, 0.72, 4),
        # Bar 3: resolve with style
        (D5,  48, 0.82, 4), (C5,  52, 0.78, 2), (Bb4, 54, 0.75, 2),
        (G4,  56, 0.80, 6),  # home, sustained
        (G5,  62, 0.70, 2),  # pickup — swagger!
    ]
    for freq, step, vel, dur in hook:
        if step < steps:
            g[4][step] = note(LEAD, freq, vel, dur)

    return Pattern(name='hook', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_breakdown() -> Pattern:
    """4 bars: The breathe moment. Pad + filtered arp + sparse kick only."""
    steps = BAR * 4
    g = new_grid(7, steps)
    bass_roots = [G2, Bb2, C3, D3]

    for bar in range(4):
        bs = bar * BAR
        root = bass_roots[bar]

        # Sparse kick — just beat 1, quiet, like a heartbeat
        g[0][bs] = note(KICK, hz(36), 0.58, 2)
        # Ghost kick on bar 2 and 4 for subtle motion
        if bar % 2 == 1:
            g[0][bs+8] = note(KICK, hz(36), 0.42, 2)

        # Bass: simplified, sustained — just roots, no chromatic walk
        g[3][bs] = note(BASS, root, 0.60, 8)
        g[3][bs+8] = note(BASS, root, 0.52, 8)

        # Pad: louder here, it's the star of the breakdown
        chord_notes = [(G3, Bb3, D4), (Bb3, D4, F4), (C4, Eb4, G4), (D4, F4, Bb4)]
        g[5][bs] = note(PAD, chord_notes[bar][1], 0.42, BAR)

        # Arp: sparse, every other beat, ghostly
        sparse_arp = [G4, None, None, None, Bb4, None, None, None,
                      D5, None, None, None, Bb4, None, None, None]
        # Bars 2-3: fill in slightly more to rebuild energy
        if bar >= 2:
            sparse_arp = [G4, None, Bb4, None, D5, None, Bb4, None,
                          G4, None, D4, None, G4, None, None, None]
        for s, n_freq in enumerate(sparse_arp):
            if n_freq is not None:
                g[6][bs+s] = note(ARP, n_freq, 0.30 + bar * 0.03, 2)

    return Pattern(name='breakdown', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def build_song() -> Song:
    return Song(
        title='G-Funk Bounce', author='ChipForge / OA LLC', bpm=BPM,
        patterns=[make_intro(), make_groove(), make_hook(), make_breakdown()],
        sequence=[0, 1, 2, 3, 2],  # intro, groove, hook, breakdown, hook
        panning={0:0.00, 1:0.05, 2:0.28, 3:-0.08, 4:0.12, 5:-0.20, 6:-0.30},
        channel_effects={
            0: {'reverb': 0.06},
            1: {'reverb': 0.12},
            2: {'delay': 0.156, 'delay_feedback': 0.22, 'reverb': 0.08},
            3: {'reverb': 0.10},
            4: {'reverb': 0.28, 'delay': 0.312, 'delay_feedback': 0.20, 'delay_mix': 0.15},
            5: {'reverb': 0.40},
            6: {'delay': 0.156, 'delay_feedback': 0.30, 'reverb': 0.12},
        },
        master_reverb=0.10, master_delay=0.04,
    )

if __name__ == '__main__':
    print("G-Funk Bounce | 96 BPM | Gm | Rendering...", flush=True)
    song = build_song()
    audio = render_song(song, panning=song.panning, channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb, master_delay=song.master_delay)
    out = Path('output/hiphop_001_gfunk_bounce.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    print(f"Done: {len(audio)/44100:.1f}s -> {out}")
