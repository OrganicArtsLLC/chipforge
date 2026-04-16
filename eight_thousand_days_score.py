"""eight_thousand_days_score — Gladiator × Star Trek for napkinfilms/eight_thousand_days.

Arc (D minor → D major, 60s at BPM 78):
  Pattern 1 — Ancient Stars      (bars  1-4)  pad + distant bell, space, mystery
  Pattern 2 — The Question       (bars  5-8)  heartbeat kick, bass enters, theme emerges
  Pattern 3 — Rising             (bars  9-12) hat + arp, melody climbs, starlight
  Pattern 4 — The Future Arrives (bars 13-16) CLIMAX — full fanfare, modulates to D major
  Pattern 5 — Afterglow          (bars 17-20) drums drop, pad + lone melody + distant bell

Run: .venv/bin/python3 eight_thousand_days_score.py
Out: output/eight_thousand_days_score.wav  (≈60s)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav

BPM = 78
BAR = 16
CH  = 7   # 0 kick | 1 hat | 2 arp | 3 bass | 4 lead | 5 pad | 6 bell

# D minor / D major MIDI notes
D2, A2 = 38, 45
D3, E3, F3, G3, A3, Bb3, C4 = 50, 52, 53, 55, 57, 58, 60
D4, E4, F4, Fs4, G4, A4, Bb4, C5, Cs5, D5 = 62, 64, 65, 66, 67, 69, 70, 72, 73, 74
E5, F5, Fs5, G5, A5, Bb5, C6, D6 = 76, 77, 78, 79, 81, 82, 84, 86


def n(inst, midi, vel=0.80, dur=2, art="normal"):
    v = min(vel, 0.90)
    return NoteEvent(midi_note=midi, velocity=v,
                     duration_steps=dur, instrument=inst, articulation=art)


def grid(steps):
    return [[None] * steps for _ in range(CH)]


# ═════════════════════════════════════════════════════════════════════════
# Pattern 1 — Ancient Stars (bars 1-4, 0-12s)
# ═════════════════════════════════════════════════════════════════════════
def pat_ancient_stars():
    g = grid(BAR * 4)
    # Pad: D minor chord held across bar 1-2, shifts to Bb major chord bar 3-4
    g[5][0]  = n("pad_lush", D3,  0.32, 32)
    g[5][0]  = n("pad_lush", F3,  0.28, 32)  # overwrites, but mixer picks one per step
    # Actually add separate steps so both voices sound
    g[5][1]  = n("pad_lush", F3,  0.28, 31)
    g[5][2]  = n("pad_lush", A3,  0.26, 30)
    g[5][32] = n("pad_lush", Bb3, 0.30, 32)
    g[5][33] = n("pad_lush", D4,  0.26, 31)
    g[5][34] = n("pad_lush", F4,  0.24, 30)

    # Distant bells — lonely, haunting
    g[6][8]  = n("gb_bell_wave", D5, 0.32, 8, art="fermata")
    g[6][24] = n("gb_bell_wave", A4, 0.28, 8, art="fermata")
    g[6][40] = n("gb_bell_wave", F5, 0.30, 10, art="fermata")
    g[6][56] = n("gb_bell_wave", D5, 0.26, 10, art="fermata")

    # Sparse chime echoes
    g[2][12] = n("pulse_chime", D4, 0.35, 3)
    g[2][28] = n("pulse_chime", F4, 0.32, 3)
    g[2][44] = n("pulse_chime", A4, 0.33, 3)
    g[2][60] = n("pulse_chime", D5, 0.30, 4)
    return Pattern(name="ancient_stars", num_steps=BAR * 4, num_channels=CH, grid=g, bpm=BPM)


# ═════════════════════════════════════════════════════════════════════════
# Pattern 2 — The Question (bars 5-8, 12-24s)
# ═════════════════════════════════════════════════════════════════════════
def pat_the_question():
    g = grid(BAR * 4)
    # Heartbeat kick on beat 1 of each bar — Gladiator slow pulse
    for bar in range(4):
        off = bar * BAR
        g[0][off] = n("kick_deep", 36, 0.55, 3, art="tenuto")

    # Bass: classic i-v-VI-III progression (D minor — Am — Bb — F)
    g[3][0]       = n("bass_sub", D2, 0.60, 16, art="tenuto")
    g[3][BAR]     = n("bass_sub", A2, 0.55, 16, art="tenuto")
    g[3][BAR * 2] = n("bass_sub", Bb3 - 24, 0.58, 16, art="tenuto")  # Bb2
    g[3][BAR * 3] = n("bass_sub", F3 - 12, 0.55, 16, art="tenuto")   # F2

    # Pad — continuous emotional wash, chord-tone oriented
    g[5][0]       = n("pad_lush", D3, 0.32, 16)
    g[5][1]       = n("pad_lush", A3, 0.26, 15)
    g[5][BAR]     = n("pad_lush", C4, 0.30, 16)
    g[5][BAR + 1] = n("pad_lush", E4, 0.24, 15)
    g[5][BAR * 2] = n("pad_lush", Bb3, 0.32, 16)
    g[5][BAR * 2 + 1] = n("pad_lush", D4, 0.26, 15)
    g[5][BAR * 3] = n("pad_lush", F3, 0.30, 16)
    g[5][BAR * 3 + 1] = n("pad_lush", A3, 0.24, 15)

    # Lead: the THEME emerges — noble, simple, ascending
    # Bar 5: rest
    # Bar 6:   D4 .. F4 ... A4 .. G4 .
    g[4][BAR + 0]  = n("pulse_warm", D4, 0.55, 3, art="tenuto")
    g[4][BAR + 4]  = n("pulse_warm", F4, 0.58, 3, art="tenuto")
    g[4][BAR + 9]  = n("pulse_warm", A4, 0.62, 3, art="tenuto")
    g[4][BAR + 13] = n("pulse_warm", G4, 0.55, 3)
    # Bar 7:  F4 .. E4 ... D4 .... (reflective descent)
    g[4][BAR * 2 + 0] = n("pulse_warm", F4, 0.58, 3)
    g[4][BAR * 2 + 4] = n("pulse_warm", E4, 0.55, 3)
    g[4][BAR * 2 + 9] = n("pulse_warm", D4, 0.60, 6, art="fermata")
    # Bar 8:  A3 .. C4 .. D4 held
    g[4][BAR * 3 + 0] = n("pulse_warm", A3, 0.55, 3)
    g[4][BAR * 3 + 4] = n("pulse_warm", C4, 0.58, 3)
    g[4][BAR * 3 + 9] = n("pulse_warm", D4, 0.62, 6, art="fermata")

    # Chime counter — very sparse
    g[2][BAR * 2 + 14] = n("pulse_chime", D5, 0.40, 2)
    g[2][BAR * 3 + 14] = n("pulse_chime", F5, 0.38, 2)

    # Distant bell on bar 6 offering
    g[6][BAR + 10] = n("gb_bell_wave", A5, 0.22, 6)
    return Pattern(name="the_question", num_steps=BAR * 4, num_channels=CH, grid=g, bpm=BPM)


# ═════════════════════════════════════════════════════════════════════════
# Pattern 3 — Rising (bars 9-12, 24-36s)
# ═════════════════════════════════════════════════════════════════════════
def pat_rising():
    g = grid(BAR * 4)
    # Kick on 1 and 3 (march intensifies)
    for bar in range(4):
        off = bar * BAR
        g[0][off]     = n("kick_deep", 36, 0.60, 2, art="marcato")
        g[0][off + 8] = n("kick_deep", 36, 0.50, 2)

    # Hat: ticking 16ths, building
    for i in range(0, BAR * 4, 2):
        vel = 0.28 + 0.10 * (i / (BAR * 4))   # crescendo
        g[1][i + 1] = n("hat_crisp", 42, vel, 1)

    # Bass: walking, more active
    bass_walk = [D2, D2, F3 - 12, A2, Bb3 - 24, Bb3 - 24, D3, F3 - 12,
                 G3 - 12, G3 - 12, Bb3 - 12, D3, A2, C4 - 12, D3, F3]
    for i, note in enumerate(bass_walk):
        g[3][i * 4] = n("bass_sub", note, 0.55, 4)

    # Chime: ascending 16th arpeggios (rising tension)
    arp_notes = [D4, F4, A4, D5, F5, A4, D5, F4,
                 E4, G4, Bb4, E5, G5, Bb4, E5, G4,
                 D4, F4, A4, D5, F5, A5, G5, F5,
                 E5, D5, C5, Bb4, A4, G4, F4, E4]
    for i, note in enumerate(arp_notes):
        if i < BAR * 2:  # first 2 bars of pattern
            g[2][i] = n("pulse_chime", note, 0.48, 2)
    # Bars 11-12 of this section — use the same riff but higher
    for i, note in enumerate(arp_notes):
        if i < BAR * 2:
            g[2][BAR * 2 + i] = n("pulse_chime", note + 5, 0.52, 2)

    # Lead: theme repeats higher (up an octave-ish)
    g[4][0]       = n("pulse_warm", D5, 0.62, 3, art="tenuto")
    g[4][4]       = n("pulse_warm", F5, 0.64, 3, art="tenuto")
    g[4][9]       = n("pulse_warm", A5, 0.68, 3, art="tenuto")
    g[4][13]      = n("pulse_warm", G5, 0.62, 3)
    g[4][BAR]     = n("pulse_warm", F5, 0.64, 3)
    g[4][BAR + 4] = n("pulse_warm", E5, 0.60, 3)
    g[4][BAR + 9] = n("pulse_warm", D5, 0.66, 6, art="fermata")
    # Bars 11-12: a LIFT — start reaching for the climax
    g[4][BAR * 2 + 0]  = n("pulse_warm", G5, 0.68, 3, art="accent")
    g[4][BAR * 2 + 4]  = n("pulse_warm", F5, 0.65, 3)
    g[4][BAR * 2 + 8]  = n("pulse_warm", E5, 0.60, 3)
    g[4][BAR * 2 + 12] = n("pulse_warm", D5, 0.64, 4, art="tenuto")
    g[4][BAR * 3 + 0]  = n("pulse_warm", A5, 0.72, 3, art="marcato")
    g[4][BAR * 3 + 4]  = n("pulse_warm", G5, 0.66, 3)
    g[4][BAR * 3 + 8]  = n("pulse_warm", A5, 0.70, 3)
    g[4][BAR * 3 + 12] = n("pulse_warm", Cs5, 0.68, 4)  # leading tone into D major!

    # Pad: richer voicing, chord on downbeats
    for bar in range(4):
        off = bar * BAR
        root = [D3, Bb3 - 12, G3, A2][bar]
        g[5][off]     = n("pad_lush", root, 0.36, 16)
        g[5][off + 1] = n("pad_lush", root + 4, 0.28, 15)
        g[5][off + 2] = n("pad_lush", root + 7, 0.24, 14)

    # Bells: starlight sparkles on accent points
    g[6][12]           = n("gb_bell_wave", D6, 0.28, 4)
    g[6][BAR + 12]     = n("gb_bell_wave", F5, 0.26, 4)
    g[6][BAR * 2 + 12] = n("gb_bell_wave", A5, 0.30, 4)
    g[6][BAR * 3 + 8]  = n("gb_bell_wave", D6, 0.34, 6)
    g[6][BAR * 3 + 14] = n("gb_bell_wave", Fs5, 0.32, 4)  # D major preview
    return Pattern(name="rising", num_steps=BAR * 4, num_channels=CH, grid=g, bpm=BPM)


# ═════════════════════════════════════════════════════════════════════════
# Pattern 4 — The Future Arrives (bars 13-16, 36-48s) — CLIMAX, D major
# ═════════════════════════════════════════════════════════════════════════
def pat_future_arrives():
    g = grid(BAR * 4)
    # Driving kick: every beat, with off-kicks for drive
    for bar in range(4):
        off = bar * BAR
        for beat in (0, 4, 8, 12):
            g[0][off + beat] = n("kick_deep", 36, 0.65, 2, art="marcato")
        g[0][off + 6]  = n("kick_deep", 36, 0.45, 1)
        g[0][off + 14] = n("kick_deep", 36, 0.50, 1)

    # Hat: active 8ths
    for i in range(0, BAR * 4, 2):
        g[1][i] = n("hat_crisp", 42, 0.38, 1)

    # Bass: D major octave jumps, heroic
    for bar in range(4):
        off = bar * BAR
        root = [D2, A2, Bb3 - 24, D2][bar]
        g[3][off]      = n("bass_sub", root, 0.65, 4, art="marcato")
        g[3][off + 4]  = n("bass_sub", root + 12, 0.60, 4)
        g[3][off + 8]  = n("bass_sub", root, 0.62, 4)
        g[3][off + 12] = n("bass_sub", root + 7, 0.58, 4)

    # Pad: HUGE D major chord (D-F#-A), modulating
    for bar in range(4):
        off = bar * BAR
        if bar == 0 or bar == 3:
            notes = (D3, Fs4, A3)
        elif bar == 1:
            notes = (A3, Cs5 - 12, E4)
        else:
            notes = (Bb3, D4, F4)   # plagal
        for k, nt in enumerate(notes):
            g[5][off + k] = n("pad_lush", nt, 0.42 - k * 0.04, 16)

    # Lead: THE HEROIC FANFARE — D major ascending + held high D
    # Bar 13: D5 .. Fs5 .. A5 .. D6 (ascending)
    g[4][0]  = n("pulse_warm", D5,  0.72, 3, art="marcato")
    g[4][4]  = n("pulse_warm", Fs5, 0.76, 3, art="tenuto")
    g[4][8]  = n("pulse_warm", A5,  0.80, 3, art="tenuto")
    g[4][12] = n("pulse_warm", D6,  0.85, 4, art="fermata")
    # Bar 14: Cs5 .. E5 .. A4 .. D5 (answer phrase)
    g[4][BAR + 0]  = n("pulse_warm", Cs5, 0.72, 3)
    g[4][BAR + 4]  = n("pulse_warm", E5,  0.74, 3)
    g[4][BAR + 8]  = n("pulse_warm", A4,  0.72, 3)
    g[4][BAR + 12] = n("pulse_warm", D5,  0.78, 4, art="tenuto")
    # Bar 15: ascending again, bigger
    g[4][BAR * 2 + 0]  = n("pulse_warm", Fs5, 0.76, 3, art="accent")
    g[4][BAR * 2 + 3]  = n("pulse_warm", G5,  0.74, 2)
    g[4][BAR * 2 + 6]  = n("pulse_warm", A5,  0.80, 3, art="tenuto")
    g[4][BAR * 2 + 10] = n("pulse_warm", Fs5, 0.72, 3)
    g[4][BAR * 2 + 13] = n("pulse_warm", G5,  0.70, 3)
    # Bar 16: PEAK — held high D, then held A (open ending, unresolved majesty)
    g[4][BAR * 3 + 0]  = n("pulse_warm", D6,  0.88, 6, art="fermata")
    g[4][BAR * 3 + 8]  = n("pulse_warm", A5,  0.82, 6, art="fermata")

    # Chime: cascading D major arpeggios
    climax_arp = [D4, Fs4, A4, D5, Fs5, A5, D6, A5, Fs5, D5, A4, Fs4, D4, A4, D5, Fs5]
    for i, note in enumerate(climax_arp):
        if i < BAR:
            g[2][i] = n("pulse_chime", note, 0.52, 2)
            g[2][BAR + i] = n("pulse_chime", note, 0.54, 2)
            g[2][BAR * 2 + i] = n("pulse_chime", note + 2, 0.56, 2)
    # Bar 16: slower cascade for the peak hold
    for i, note in enumerate([D5, Fs5, A5, D6, D5, Fs5, A5, D6]):
        g[2][BAR * 3 + i * 2] = n("pulse_chime", note, 0.58, 2)

    # Bells: bright cosmic shimmer on accents
    g[6][0]           = n("gb_bell_wave", D6, 0.42, 4)
    g[6][8]           = n("gb_bell_wave", Fs5, 0.38, 4)
    g[6][BAR]         = n("gb_bell_wave", A5, 0.36, 4)
    g[6][BAR + 8]     = n("gb_bell_wave", D6, 0.44, 5)
    g[6][BAR * 2]     = n("gb_bell_wave", Fs5, 0.38, 4)
    g[6][BAR * 2 + 8] = n("gb_bell_wave", A5, 0.40, 5)
    g[6][BAR * 3]     = n("gb_bell_wave", D6, 0.48, 8, art="fermata")
    g[6][BAR * 3 + 8] = n("gb_bell_wave", A5, 0.42, 8, art="fermata")

    return Pattern(name="future_arrives", num_steps=BAR * 4, num_channels=CH, grid=g, bpm=BPM)


# ═════════════════════════════════════════════════════════════════════════
# Pattern 5 — Afterglow (bars 17-20, 48-60s) — drums drop, reflective
# ═════════════════════════════════════════════════════════════════════════
def pat_afterglow():
    g = grid(BAR * 4)
    # NO kick or hat — dramatic dropout

    # Bass: one long sustained D2 (drone of gratitude)
    g[3][0]       = n("bass_sub", D2, 0.42, 32, art="fermata")
    g[3][BAR * 2] = n("bass_sub", D2, 0.36, 32, art="fermata")

    # Pad: sustained D major chord, slowly voicing down to open D-A
    g[5][0]       = n("pad_lush", D3, 0.38, 32)
    g[5][1]       = n("pad_lush", Fs4, 0.30, 31)
    g[5][2]       = n("pad_lush", A3,  0.28, 30)
    g[5][BAR * 2] = n("pad_lush", D3, 0.34, 32)
    g[5][BAR * 2 + 1] = n("pad_lush", A3, 0.28, 31)  # open 5th — cosmic
    g[5][BAR * 2 + 2] = n("pad_lush", D4, 0.24, 30)

    # Lead: echo of the theme, descending and softening
    g[4][4]         = n("pulse_warm", D5,  0.55, 4, art="tenuto")
    g[4][12]        = n("pulse_warm", Fs5, 0.50, 4, art="tenuto")
    g[4][BAR + 4]   = n("pulse_warm", A5,  0.48, 4, art="tenuto")
    g[4][BAR + 12]  = n("pulse_warm", Fs5, 0.45, 4)
    # Bars 19-20: single long held note, the final breath
    g[4][BAR * 2 + 0]  = n("pulse_warm", D5, 0.42, 10, art="fermata")
    g[4][BAR * 2 + 14] = n("pulse_warm", A4, 0.38, 8, art="fermata")
    g[4][BAR * 3 + 8]  = n("pulse_warm", D5, 0.36, 8, art="fermata")

    # Chime: farewell notes, spacious
    g[2][8]        = n("pulse_chime", D6, 0.38, 6)
    g[2][BAR + 8]  = n("pulse_chime", A5, 0.34, 8)
    g[2][BAR * 2 + 4] = n("pulse_chime", Fs5, 0.30, 8)
    g[2][BAR * 3 + 0] = n("pulse_chime", D5, 0.28, 12, art="fermata")

    # Distant bells — stars fading
    g[6][0]            = n("gb_bell_wave", D6, 0.28, 10, art="fermata")
    g[6][BAR + 4]      = n("gb_bell_wave", A5, 0.22, 10, art="fermata")
    g[6][BAR * 2 + 8]  = n("gb_bell_wave", Fs5, 0.20, 12, art="fermata")
    g[6][BAR * 3 + 4]  = n("gb_bell_wave", D6, 0.18, 14, art="fermata")
    return Pattern(name="afterglow", num_steps=BAR * 4, num_channels=CH, grid=g, bpm=BPM)


def build_song():
    return Song(
        title="Eight Thousand Days",
        bpm=BPM,
        patterns=[
            pat_ancient_stars(),
            pat_the_question(),
            pat_rising(),
            pat_future_arrives(),
            pat_afterglow(),
        ],
        sequence=[0, 1, 2, 3, 4],
        panning={
            0: 0.0,     # kick  center
            1: 0.15,    # hat   slight R
            2: -0.25,   # chime L
            3: 0.0,     # bass  center
            4: 0.10,    # lead  slight R (horn-like)
            5: -0.10,   # pad   slight L
            6: 0.30,    # bell  R (starlight)
        },
        channel_effects={
            0: {"reverb": 0.18},
            1: {"reverb": 0.22, "delay": 0.12, "delay_feedback": 0.20},
            2: {"reverb": 0.40, "delay": 0.25, "delay_feedback": 0.30},
            3: {"reverb": 0.15},
            4: {"reverb": 0.45, "delay": 0.22, "delay_feedback": 0.30},   # lead: wide, cinematic
            5: {"reverb": 0.55},                                           # pad: cavernous
            6: {"reverb": 0.60, "delay": 0.35, "delay_feedback": 0.45},   # bells: cosmic
        },
        master_reverb=0.22,
        master_delay=0.10,
    )


if __name__ == "__main__":
    song = build_song()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb,
                        master_delay=song.master_delay)
    out = Path("output/eight_thousand_days_score.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.2f}s → {out}")
