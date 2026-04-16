"""ten_thousand_days_score — Pachelbel's Canon in D, orchestrated as a rave.

Foundation: Johann Pachelbel, Canon in D (c.1680). Eight-bar ground bass
progression:  D | A | Bm | F#m | G | D | G | A.  The soprano line descends
stepwise through each chord's tones.  In the original the bass repeats
unchanged while successive voices enter with increasing rhythmic subdivision
(a literal canon). We honour that structure exactly: 4 cycles, each a new
"voice" of complexity layered on the same ground bass.

  Cycle 1 (bars  1–8,  0–15s)   pad + bass only, classical introduction
  Cycle 2 (bars  9–16, 15–30s)  drums enter, arp 16ths, soprano states the melody;
                                last 2 bars = riser + snare roll (pre-drop)
  Cycle 3 (bars 17–24, 30–45s)  THE DROP — melody up an octave on supersaw
                                lead, full arp, bells on every chord change
  Cycle 4 (bars 25–32, 45–60s)  ride out: drums slowly thin, melody returns
                                to the original octave, final D major held

BPM 128, 32 bars × 1.875s = 60.0s exactly. Strict D major throughout.

Run: .venv/bin/python3 ten_thousand_days_score.py
Out: output/ten_thousand_days_score.wav
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav

BPM = 128
BAR = 16
CH  = 8   # 0 kick | 1 clap/snare | 2 hat | 3 arp | 4 lead | 5 bass | 6 pad | 7 bell/fx


def n(inst, midi, vel=0.80, dur=2, art="normal"):
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.92),
                     duration_steps=dur, instrument=inst, articulation=art)


def grid(steps, channels=CH):
    return [[None] * steps for _ in range(channels)]


# ══════════════════════════════════════════════════════════════════════════════
# PACHELBEL GROUND — one entry per bar in the 8-bar cycle
# ══════════════════════════════════════════════════════════════════════════════
# Per bar: (bass root MIDI, chord tones (root3,third3,fifth3) in octave 3,
#          soprano line = 4 quarter-note melody notes)

PACHELBEL = [
    # D major — F#5 E5 D5 C#5
    {"bass": 38, "chord": (50, 54, 57), "melody": [78, 76, 74, 73], "tag": "D"},
    # A major — B4 A4 G4 F#4
    {"bass": 45, "chord": (57, 61, 64), "melody": [71, 69, 67, 66], "tag": "A"},
    # B minor — A4 G4 F#4 E4
    {"bass": 47, "chord": (59, 62, 66), "melody": [69, 67, 66, 64], "tag": "Bm"},
    # F# minor — F#4 E4 D4 C#4
    {"bass": 42, "chord": (54, 57, 61), "melody": [66, 64, 62, 61], "tag": "F#m"},
    # G major — B4 A4 G4 F#4
    {"bass": 43, "chord": (55, 59, 62), "melody": [71, 69, 67, 66], "tag": "G"},
    # D major — A4 G4 F#4 E4
    {"bass": 38, "chord": (50, 54, 57), "melody": [69, 67, 66, 64], "tag": "D"},
    # G major — G4 F#4 E4 D4
    {"bass": 43, "chord": (55, 59, 62), "melody": [67, 66, 64, 62], "tag": "G"},
    # A major — A4 B4 C#5 E5  (turnaround ascending)
    {"bass": 45, "chord": (57, 61, 64), "melody": [69, 71, 73, 76], "tag": "A"},
]


def arp_bar(chord):
    """16-step ascending chord-tone spiral for one bar (the twirl)."""
    r, t, f = chord
    return [r, t, f, r+12, t, f, r+12, t+12,
            f, r+12, t+12, f+12, r+12, t+12, f+12, r+24]


def place_pad(g, bar_off, chord, vel_scale=1.0):
    """Hold the chord for 16 steps using three stacked supersaw_pad voices."""
    r, t, f = chord
    g[6][bar_off]     = n("supersaw_pad", r, 0.36 * vel_scale, 16)
    g[6][bar_off + 1] = n("supersaw_pad", t, 0.28 * vel_scale, 15)
    g[6][bar_off + 2] = n("supersaw_pad", f, 0.24 * vel_scale, 14)


def place_bass(g, bar_off, root, vel_scale=1.0, pump=True):
    """Octave-pumping bass.  If pump=False, sustain root across the bar."""
    if not pump:
        g[5][bar_off] = n("supersaw_bass", root, 0.50 * vel_scale, 16)
        return
    for beat in (0, 4, 8, 12):
        note = root if beat < 8 else root + 12
        g[5][bar_off + beat] = n("supersaw_bass", note, 0.62 * vel_scale, 3,
                                 art="marcato")


def place_drums(g, bar_off, clap=True, open_hat_end=False, vel_scale=1.0):
    """4-on-the-floor kick + offbeat hats + (optional) clap on beat 3."""
    for beat in (0, 4, 8, 12):
        g[0][bar_off + beat] = n("kick_deep", 36, 0.72 * vel_scale, 2, art="marcato")
    for step in (2, 6, 10, 14):
        g[2][bar_off + step] = n("hat_tight", 42, 0.34 * vel_scale, 1)
    if clap:
        g[1][bar_off + 8] = n("clap_tight", 38, 0.62 * vel_scale, 2, art="accent")
    if open_hat_end:
        g[2][bar_off + 14] = n("hat_open_shimmer", 42, 0.42 * vel_scale, 2)


def place_melody(g, bar_off, melody, octave_shift=0, vel=0.62, articulate=True):
    """Pachelbel soprano — one quarter-note per beat (steps 0,4,8,12)."""
    for i, midi in enumerate(melody):
        note = midi + octave_shift
        art = "tenuto" if articulate and i % 2 == 0 else "normal"
        g[4][bar_off + i * 4] = n("supersaw_lead", note, vel, 3, art=art)


def place_arp(g, bar_off, chord, vel=0.52):
    """16-step shimmer arp for one bar."""
    for i, midi in enumerate(arp_bar(chord)):
        g[3][bar_off + i] = n("arp_shimmer", midi, vel, 2)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 1 — CLASSICAL INTRODUCTION (bars 1-8, 0-15s)
#   Pad + bass only.  No drums, no arp, no melody.  States the progression.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle1():
    g = grid(BAR * 8)
    for bar, step in enumerate(PACHELBEL):
        off = bar * BAR
        place_pad(g, off, step["chord"], vel_scale=0.8)
        place_bass(g, off, step["bass"], vel_scale=0.85, pump=False)
        # Subtle single bell on the final chord (bar 8) to foreshadow
        if bar == 7:
            g[7][off + 8] = n("shimmer_bell", step["chord"][0] + 24, 0.30, 6)
    return Pattern(name="cycle1_intro", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 2 — GROOVE ENTERS (bars 9-16, 15-30s)
#   Drums on, arp on, MELODY stated.  Bars 15-16 = pre-drop: riser + snare roll.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle2():
    g = grid(BAR * 8)
    for bar, step in enumerate(PACHELBEL):
        off = bar * BAR
        place_pad(g, off, step["chord"])
        # Bars 0-5: full pump + drums. Bars 6-7 (= bars 15-16 = pre-drop):
        # drums stay but bass thins, riser + snare roll take over.
        if bar < 6:
            place_bass(g, off, step["bass"])
            place_drums(g, off, clap=True, open_hat_end=(bar % 2 == 1))
            place_arp(g, off, step["chord"], vel=0.50)
            place_melody(g, off, step["melody"], octave_shift=0, vel=0.60)
        else:
            # Pre-drop bars: kick continues, hats go to 16ths (tension)
            for beat in (0, 4, 8, 12):
                g[0][off + beat] = n("kick_deep", 36, 0.70, 2)
            # 16th-note hats for the build
            for s in range(16):
                g[2][off + s] = n("hat_tight", 42, 0.30 + 0.015 * s, 1)
            place_bass(g, off, step["bass"], vel_scale=0.7)
            # Melody whispers in upper arp register
            place_arp(g, off, step["chord"], vel=0.54)
            place_melody(g, off, step["melody"], octave_shift=0, vel=0.55)

    # Riser over the final 4 bars (bars 13-16, i.e. last half of cycle)
    g[7][BAR * 4] = n("fx_riser", 62, 0.50, BAR * 4, art="fermata")

    # Snare roll accelerating in the last bar (bar 16)
    roll_off = BAR * 7
    roll_steps = [0, 4, 8, 10, 12, 13, 14, 15]
    for i, s in enumerate(roll_steps):
        g[1][roll_off + s] = n("snare_tight", 38, 0.42 + 0.06 * i, 1,
                                art="accent")
    # Kick drops out the last two 16ths for tension — already not placed there
    return Pattern(name="cycle2_groove", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 3 — THE DROP (bars 17-24, 30-45s)
#   Full rave. Melody up one octave. Arp 16ths. Bells on every chord change.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle3():
    g = grid(BAR * 8)

    # Drop impact on bar 1 downbeat of this pattern (bar 17 of song)
    g[7][0] = n("fx_drop", 62, 0.85, 2, art="marcato")

    for bar, step in enumerate(PACHELBEL):
        off = bar * BAR
        place_pad(g, off, step["chord"], vel_scale=1.15)
        # Bass: syncopated pump for the drop
        g[5][off]      = n("supersaw_bass", step["bass"], 0.78, 2, art="marcato")
        g[5][off + 4]  = n("supersaw_bass", step["bass"] + 12, 0.72, 2)
        g[5][off + 8]  = n("supersaw_bass", step["bass"], 0.75, 2)
        g[5][off + 12] = n("supersaw_bass", step["bass"] + 12, 0.70, 2)

        # Drums: heavy
        for beat in (0, 4, 8, 12):
            g[0][off + beat] = n("kick_deep", 36, 0.82, 2, art="marcato")
        g[1][off + 8]  = n("clap_tight", 38, 0.72, 2, art="accent")
        g[1][off + 12] = n("clap_tight", 38, 0.55, 1)
        for s in (2, 6, 10, 14):
            g[2][off + s] = n("hat_tight", 42, 0.42, 1)
        g[2][off + 14] = n("hat_open_shimmer", 42, 0.50, 2)

        # Arp — full 16ths, strong
        place_arp(g, off, step["chord"], vel=0.62)

        # Melody — UP ONE OCTAVE (the soprano rings out)
        place_melody(g, off, step["melody"], octave_shift=12,
                     vel=0.82, articulate=True)

        # Bell on chord downbeat (one per bar = per chord change)
        bell_note = step["chord"][2] + 24   # fifth up two octaves, bright
        g[7][off + 0] = n("shimmer_bell", bell_note, 0.48, 4)

    # A bigger bell on the cycle's strongest bar (bar 6 of this pattern = bar 22)
    strong_off = BAR * 5
    g[7][strong_off + 8] = n("shimmer_bell", 86, 0.55, 6, art="fermata")
    return Pattern(name="cycle3_drop", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 4 — RIDE OUT (bars 25-32, 45-60s)
#   Drums slowly thin. Melody returns to original octave. Final D held.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle4():
    g = grid(BAR * 8)

    for bar, step in enumerate(PACHELBEL):
        off = bar * BAR

        # Pad stays, always.
        place_pad(g, off, step["chord"], vel_scale=1.0 - 0.08 * max(0, bar - 3))

        # Bass: full through bar 5, then simplify to sustained roots bar 6-7
        if bar < 6:
            place_bass(g, off, step["bass"], vel_scale=1.0 - 0.04 * bar)
        else:
            place_bass(g, off, step["bass"], vel_scale=0.6, pump=False)

        # Drums: full through bar 3, thin through bar 5, gone bar 6-7
        if bar < 4:
            place_drums(g, off, clap=True, open_hat_end=(bar == 1),
                        vel_scale=0.85)
        elif bar < 6:
            # Just kick on beats 1 and 3, softer
            g[0][off] = n("kick_deep", 36, 0.50, 2)
            g[0][off + 8] = n("kick_deep", 36, 0.45, 2)
            # Clap pulled, only a single hat
            g[2][off + 10] = n("hat_tight", 42, 0.22, 1)

        # Arp — full through bar 5, then thins
        if bar < 6:
            place_arp(g, off, step["chord"], vel=0.50)
        elif bar == 6:
            # Sparse arp — half density
            for i, midi in enumerate(arp_bar(step["chord"])):
                if i % 2 == 0:
                    g[3][off + i] = n("arp_shimmer", midi, 0.35, 2)

        # Melody — full through bar 5 at original octave, then a final
        # held high note in bars 6-7 that descends to D.
        if bar < 6:
            place_melody(g, off, step["melody"], octave_shift=0, vel=0.60)
        elif bar == 6:
            # Long held D5 with descent, like a soprano closing
            g[4][off] = n("supersaw_lead", 74, 0.55, 8, art="fermata")
            g[4][off + 8] = n("supersaw_lead", 71, 0.50, 8, art="fermata")
        else:  # bar 7 — final bar of the whole song
            # Hold A4 then final D5 (tonic)
            g[4][off] = n("supersaw_lead", 69, 0.45, 8, art="fermata")
            g[4][off + 8] = n("supersaw_lead", 74, 0.42, 8, art="fermata")

        # Bell accents every other bar, getting sparser
        if bar % 2 == 0 and bar < 6:
            g[7][off + 12] = n("shimmer_bell", step["chord"][2] + 24, 0.32, 4)

    # Final bell on the last bar's downbeat — the fade-out gesture
    g[7][BAR * 7] = n("shimmer_bell", 86, 0.30, 12, art="fermata")
    g[7][BAR * 7 + 8] = n("shimmer_bell", 81, 0.22, 8, art="fermata")
    return Pattern(name="cycle4_rideout", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


def build_song():
    return Song(
        title="Ten Thousand Days (on Pachelbel's Canon)",
        bpm=BPM,
        patterns=[pat_cycle1(), pat_cycle2(), pat_cycle3(), pat_cycle4()],
        sequence=[0, 1, 2, 3],
        panning={
            0: 0.0,     # kick center
            1: 0.0,     # clap/snare center
            2: 0.25,    # hat R
            3: -0.30,   # arp L (twirl on left)
            4: 0.10,    # lead slight R (soprano)
            5: 0.0,     # bass center
            6: 0.0,     # pad wide
            7: 0.30,    # bell/fx R
        },
        channel_effects={
            0: {"reverb": 0.10},
            1: {"reverb": 0.22},
            2: {"reverb": 0.16, "delay": 0.12, "delay_feedback": 0.20},
            3: {"reverb": 0.32, "delay": 0.18, "delay_feedback": 0.30},
            4: {"reverb": 0.28, "delay": 0.15, "delay_feedback": 0.28},
            5: {"reverb": 0.10},
            6: {"reverb": 0.42},    # pad cavernous — classical string-section feel
            7: {"reverb": 0.48, "delay": 0.28, "delay_feedback": 0.35},
        },
        master_reverb=0.18,
        master_delay=0.08,
    )


if __name__ == "__main__":
    song = build_song()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb,
                        master_delay=song.master_delay)
    out = Path("output/ten_thousand_days_score.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.2f}s → {out}")
