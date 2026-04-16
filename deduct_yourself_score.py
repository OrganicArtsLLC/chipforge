"""deduct_yourself_score — Grieg "In the Hall of the Mountain King" as a
chiptune rave. Accompanies the Napkin Films scene of the same name.

Foundation: Edvard Grieg, Peer Gynt Suite No. 1, "In the Hall of the Mountain
King" (1875). Original B minor → transposed to A minor (chiptune-friendly,
matches Fur Elise rave, mixes better with saw leads).

The iconic Grieg trick is a single ostinato motif repeated at rising registers
and intensity — literally the "creeping → chase → explosion" arc. We honour
that exactly across 4 cycles × 8 bars × 1.875s (128 BPM) = 60.0s.

  Cycle 1 (bars  1-8,  0-15s)   CREEP   — pizz bass + pad whisper, no drums
  Cycle 2 (bars  9-16, 15-30s)  BUILD   — drums enter, motif on lead, arp shimmer
                                          last 2 bars: riser + snare roll (pre-drop)
  Cycle 3 (bars 17-24, 30-45s)  DROP    — supersaw lead up an octave, full rave,
                                          bass pump, heavy kick, bells
  Cycle 4 (bars 25-32, 45-60s)  CHORUS  — motif in canon (lead + arp + bells),
                                          drums thin across the last 2 bars

Strict A harmonic minor (G# leading tone). BPM 128 everywhere — ChipForge's
Pattern class silently defaults to 120 unless told otherwise.

Run: .venv/bin/python3 deduct_yourself_score.py
Out: output/deduct_yourself_score.wav
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav

BPM = 128
BAR = 16
CH  = 8    # 0 kick | 1 clap/snare | 2 hat | 3 arp | 4 lead | 5 bass | 6 pad | 7 bell/fx


def n(inst, midi, vel=0.80, dur=2, art="normal"):
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.92),
                     duration_steps=dur, instrument=inst, articulation=art)


def grid(steps, channels=CH):
    return [[None] * steps for _ in range(channels)]


# ══════════════════════════════════════════════════════════════════════════════
# MOUNTAIN KING MOTIF — A minor, 8 eighth-notes per bar (steps 0,2,4,...14)
# ══════════════════════════════════════════════════════════════════════════════
# A harmonic minor: A, B, C, D, E, F, G#, A   (G# = leading tone, that's the
# magic Grieg ingredient)
#
# MIDI:  A3=57  B3=59  C4=60  D4=62  E4=64  F4=65  Gs4=68  A4=69
#        G3=55  Gs3=56  F3=53  E3=52  D3=50  C3=48  B2=47  A2=45
#
# The original theme sketched in 8 per-bar eighths (motif contour):
#   Bar 1: up-down on Am triad with G# leading — A C E A G# E C A
#   Bar 2: same shape shifted up — B D F B A F D B (hints at F major)
#   Bar 3: Am triad ascending — A C E A C E A C
#   Bar 4: resolve — E G# A E D C B A
#   Bar 5-8: same 4 repeated a tritone of intensity higher (octave shift +12)
# ══════════════════════════════════════════════════════════════════════════════

# A harmonic minor MIDI numbers — one octave below for bass creep
A2, B2, C3, D3, E3, F3, Gs3, A3 = 45, 47, 48, 50, 52, 53, 56, 57
B3, C4, D4, E4, F4, Gs4, A4 = 59, 60, 62, 64, 65, 68, 69
C5, D5, E5, F5, Gs5, A5 = 72, 74, 76, 77, 80, 81

# Eight-note motif per bar (to be placed on even 16th-steps)
MOTIF_BARS = [
    # Bar 1 — Am triad with G# leading
    [A3, C4, E4, A4, Gs4, E4, C4, A3],
    # Bar 2 — shifted up (transition to F-ish feel)
    [B3, D4, F4, A4, Gs4, F4, D4, B3],
    # Bar 3 — climbing Am stack
    [A3, C4, E4, A4, C5, A4, E4, C4],
    # Bar 4 — descend home
    [E4, Gs4, A4, E4, D4, C4, B3, A3],
    # Bar 5 — repeat up one step (the famous rising tension)
    [A3, C4, E4, A4, Gs4, E4, C4, A3],
    # Bar 6
    [B3, D4, F4, A4, Gs4, F4, D4, B3],
    # Bar 7 — burst upward
    [C4, E4, A4, C5, E5, C5, A4, E4],
    # Bar 8 — final lunge back to A
    [A4, Gs4, F4, E4, D4, C4, B3, A3],
]

# Bass root per bar (creeping pizz — the "footsteps")
BASS_ROOTS = [A2, B2, A2, E2 if False else E3, A2, B2, A2, E3]
# Simplify: pedal between A2 and E3 with leading-tone lift
BASS_ROOTS = [A2, B2, A2, E3, A2, B2, A2, E3]

# Pad chord per bar (three-voice hold)
PAD_CHORDS = [
    (A3, C4, E4),     # Am
    (B2, D4, F4),     # Bm7♭5 / dim — the Grieg tension
    (A3, C4, E4),     # Am
    (E3, Gs3, B3),    # E (dominant) — leading back to Am
    (A3, C4, E4),     # Am
    (B2, D4, F4),
    (C4, E4, A4),     # Am first inversion — brighter
    (E3, Gs3, B3),    # E
]


# ══════════════════════════════════════════════════════════════════════════════
# Placement helpers
# ══════════════════════════════════════════════════════════════════════════════
def place_motif(g, bar_off, bar_idx, octave_shift=0, vel=0.60, inst="supersaw_lead"):
    """Place the 8-note motif on even 16th steps (0,2,4,...14)."""
    notes = MOTIF_BARS[bar_idx]
    for i, midi in enumerate(notes):
        step = i * 2
        art = "accent" if i == 0 else ("tenuto" if i == 4 else "normal")
        g[4][bar_off + step] = n(inst, midi + octave_shift, vel, 2, art=art)

def place_motif_on(g, channel, bar_off, bar_idx, octave_shift=0, vel=0.45,
                   inst="arp_shimmer", step_stride=2):
    """Place the motif on an arbitrary channel (e.g. arp canon line)."""
    notes = MOTIF_BARS[bar_idx]
    for i, midi in enumerate(notes):
        step = i * step_stride
        if step >= BAR: break
        g[channel][bar_off + step] = n(inst, midi + octave_shift, vel, 2)

def place_pad(g, bar_off, chord, vel_scale=1.0):
    r, t, f = chord
    g[6][bar_off]     = n("supersaw_pad", r, 0.34 * vel_scale, 16)
    g[6][bar_off + 1] = n("supersaw_pad", t, 0.26 * vel_scale, 15)
    g[6][bar_off + 2] = n("supersaw_pad", f, 0.22 * vel_scale, 14)

def place_pizz_bass(g, bar_off, root, vel_scale=1.0):
    """Light pizzicato creep — one bass note per beat (on-beat, short)."""
    for beat in (0, 4, 8, 12):
        note = root if beat < 8 else root + 7   # alternate root / fifth
        g[5][bar_off + beat] = n("supersaw_bass", note, 0.42 * vel_scale, 1,
                                 art="staccato")

def place_pump_bass(g, bar_off, root, vel_scale=1.0):
    """Octave-pumping rave bass for the drop."""
    for beat in (0, 4, 8, 12):
        note = root if beat < 8 else root + 12
        g[5][bar_off + beat] = n("supersaw_bass", note, 0.64 * vel_scale, 3,
                                 art="marcato")

def place_drums(g, bar_off, clap=True, open_hat_end=False, vel_scale=1.0):
    for beat in (0, 4, 8, 12):
        g[0][bar_off + beat] = n("kick_deep", 36, 0.74 * vel_scale, 2, art="marcato")
    for step in (2, 6, 10, 14):
        g[2][bar_off + step] = n("hat_tight", 42, 0.32 * vel_scale, 1)
    if clap:
        g[1][bar_off + 8] = n("clap_tight", 38, 0.62 * vel_scale, 2, art="accent")
    if open_hat_end:
        g[2][bar_off + 14] = n("hat_open_shimmer", 42, 0.44 * vel_scale, 2)

def place_arp_16ths(g, bar_off, chord, vel=0.46):
    """16-step ascending chord-tone arp — the rave twirl."""
    r, t, f = chord
    seq = [r, t, f, r+12, t, f, r+12, t+12,
           f, r+12, t+12, f+12, r+12, t+12, f+12, r+24]
    for i, midi in enumerate(seq):
        g[3][bar_off + i] = n("arp_shimmer", midi, vel, 2)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 1 — CREEP (bars 1-8, 0-15s)
#   Pad + pizz bass only. No drums. Motif whispers on the final two bars.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle1():
    g = grid(BAR * 8)
    # ── OPENING IMPACT (bar 1 beat 1) — hard hit so the intro punches ───────
    # fx_drop + kick + bell stab + marcato bass chord on the downbeat.
    g[7][0] = n("fx_drop", 62, 0.95, 4, art="marcato")
    g[0][0] = n("kick_deep", 36, 0.92, 3, art="marcato")
    g[7][2] = n("shimmer_bell", 88, 0.55, 6, art="accent")
    # A one-bar riser to establish the creep arriving out of impact
    g[7][4] = n("fx_riser", 60, 0.40, 12)
    for bar in range(8):
        off = bar * BAR
        # Louder pad for first two bars (hit territory), then settle
        if bar < 2:
            place_pad(g, off, PAD_CHORDS[bar], vel_scale=1.0)
        else:
            place_pad(g, off, PAD_CHORDS[bar], vel_scale=0.55)
        # Louder pizz bass for first bar, else normal
        place_pizz_bass(g, off, BASS_ROOTS[bar],
                        vel_scale=1.1 if bar == 0 else 0.70)
        # Motif enters as a whisper on bars 7-8 (the taxman approaches)
        if bar >= 6:
            place_motif(g, off, bar, octave_shift=-12, vel=0.32,
                        inst="supersaw_lead")
    # A faint bell on the final downbeat (foreshadow)
    g[7][BAR * 7] = n("shimmer_bell", 81, 0.22, 6)
    return Pattern(name="c1_creep", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 2 — BUILD (bars 9-16, 15-30s)
#   Drums on. Motif on lead at original octave. Arp shimmer joins bar 3+.
#   Bars 7-8 are the pre-drop: riser + snare roll, kick thins.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle2():
    g = grid(BAR * 8)
    for bar in range(8):
        off = bar * BAR
        place_pad(g, off, PAD_CHORDS[bar], vel_scale=0.8)
        if bar < 6:
            place_pizz_bass(g, off, BASS_ROOTS[bar], vel_scale=1.0)
            place_drums(g, off, clap=(bar >= 2),
                        open_hat_end=(bar % 2 == 1), vel_scale=0.85)
            place_motif(g, off, bar, octave_shift=0, vel=0.60)
            if bar >= 2:
                place_arp_16ths(g, off, PAD_CHORDS[bar], vel=0.40)
        else:
            # Pre-drop bars 7-8: classic riser/snare roll
            # Kick still on 1 and 3, hats go 16th
            g[0][off]     = n("kick_deep", 36, 0.70, 2)
            g[0][off + 8] = n("kick_deep", 36, 0.68, 2)
            for s in range(16):
                g[2][off + s] = n("hat_tight", 42, 0.28 + 0.015 * s, 1)
            place_pizz_bass(g, off, BASS_ROOTS[bar], vel_scale=0.60)
            place_motif(g, off, bar, octave_shift=0, vel=0.55)
            place_arp_16ths(g, off, PAD_CHORDS[bar], vel=0.48)
    # Riser over bars 5-8
    g[7][BAR * 4] = n("fx_riser", 62, 0.55, BAR * 4, art="fermata")
    # Snare roll in final bar — tax-day acceleration
    roll_off = BAR * 7
    for i, s in enumerate([0, 4, 8, 10, 12, 13, 14, 15]):
        g[1][roll_off + s] = n("snare_tight", 38, 0.38 + 0.07 * i, 1, art="accent")
    return Pattern(name="c2_build", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 3 — THE DROP (bars 17-24, 30-45s)
#   Supersaw lead plays motif UP ONE OCTAVE. Pump bass. Full drums. Bells.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle3():
    g = grid(BAR * 8)
    # Impact on downbeat
    g[7][0] = n("fx_drop", 62, 0.88, 2, art="marcato")

    for bar in range(8):
        off = bar * BAR
        place_pad(g, off, PAD_CHORDS[bar], vel_scale=1.15)
        place_pump_bass(g, off, BASS_ROOTS[bar], vel_scale=1.05)

        # Heavy drums
        for beat in (0, 4, 8, 12):
            g[0][off + beat] = n("kick_deep", 36, 0.84, 2, art="marcato")
        g[1][off + 8]  = n("clap_tight", 38, 0.76, 2, art="accent")
        g[1][off + 12] = n("clap_tight", 38, 0.50, 1)
        for s in (2, 6, 10, 14):
            g[2][off + s] = n("hat_tight", 42, 0.44, 1)
        g[2][off + 14] = n("hat_open_shimmer", 42, 0.54, 2)

        # Arp 16ths — full shimmer
        place_arp_16ths(g, off, PAD_CHORDS[bar], vel=0.60)

        # MOTIF UP ONE OCTAVE — the Mountain King lead screams
        place_motif(g, off, bar, octave_shift=12, vel=0.85)

        # Bell on every chord change (bar downbeat)
        bell = PAD_CHORDS[bar][2] + 24
        g[7][off + 0] = n("shimmer_bell", bell, 0.50, 4)
    # Big bell at the peak (bar 6 downbeat)
    g[7][BAR * 5 + 8] = n("shimmer_bell", 88, 0.58, 6, art="fermata")
    return Pattern(name="c3_drop", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 4 — CHORUS RIDE-OUT (bars 25-32, 45-60s)
#   Motif stays on the lead at original octave. Arp plays the SAME motif one
#   bar late (canon!) up an octave. Drums thin on bars 7-8. Final A held.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle4():
    g = grid(BAR * 8)

    for bar in range(8):
        off = bar * BAR
        place_pad(g, off, PAD_CHORDS[bar],
                  vel_scale=1.0 - 0.07 * max(0, bar - 4))

        # Bass full through bar 5, then sustain only
        if bar < 6:
            place_pump_bass(g, off, BASS_ROOTS[bar], vel_scale=1.0 - 0.03 * bar)
        else:
            g[5][off] = n("supersaw_bass", BASS_ROOTS[bar], 0.42, 16)

        # Drums full through bar 3, thin 4-5, gone 6-7
        if bar < 4:
            place_drums(g, off, clap=True,
                        open_hat_end=(bar == 1), vel_scale=0.85)
        elif bar < 6:
            g[0][off]     = n("kick_deep", 36, 0.50, 2)
            g[0][off + 8] = n("kick_deep", 36, 0.45, 2)
            g[2][off + 10] = n("hat_tight", 42, 0.22, 1)

        # Main motif on lead — original octave
        if bar < 7:
            place_motif(g, off, bar, octave_shift=0, vel=0.62)
        else:
            # Final bar — hold final A4
            g[4][off]     = n("supersaw_lead", A4, 0.60, 8, art="fermata")
            g[4][off + 8] = n("supersaw_lead", A5, 0.55, 8, art="fermata")

        # CANON — arp plays the motif from one bar ago, up an octave
        canon_bar = (bar - 1) % 8
        if bar >= 1 and bar < 7:
            place_motif_on(g, 3, off, canon_bar, octave_shift=12,
                           vel=0.40, inst="arp_shimmer", step_stride=2)

        # Bells every other bar
        if bar % 2 == 0 and bar < 7:
            g[7][off + 12] = n("shimmer_bell", PAD_CHORDS[bar][2] + 24, 0.34, 4)

    # Final bell cascade on the very last bar
    g[7][BAR * 7]     = n("shimmer_bell", 88, 0.35, 12, art="fermata")
    g[7][BAR * 7 + 8] = n("shimmer_bell", 81, 0.28, 8, art="fermata")
    return Pattern(name="c4_chorus", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 5 — OUTRO FADE (bars 33-36, 60-67.5s)
#   4 bars of sustained Am chord for the video outro / end-card fade.
#   No drums, no arp, no bass pump — just pad + fading bells. The finalmix
#   applies a 6-second master fade over the last 4 seconds of this cycle.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle5():
    g = grid(BAR * 4)
    # Sustained Am pad across all 4 bars, gently decreasing velocity
    for bar in range(4):
        off = bar * BAR
        vel = 0.80 - 0.15 * bar                           # 0.80 → 0.35
        place_pad(g, off, PAD_CHORDS[0], vel_scale=vel)   # Am
        # Low root sustain in bass for tonal centre
        g[5][off] = n("supersaw_bass", A2, 0.38 - 0.08 * bar, 16,
                      art="fermata")
    # Bells — one per bar for the first two, last bar is a long fermata
    g[7][BAR * 0 + 0] = n("shimmer_bell", 81, 0.40, 12, art="fermata")
    g[7][BAR * 1 + 8] = n("shimmer_bell", 88, 0.32, 12, art="fermata")
    g[7][BAR * 2 + 0] = n("shimmer_bell", 76, 0.26, 16, art="fermata")
    # Final A4 held note on the last bar — the "home" chord anchor
    g[4][BAR * 3 + 0] = n("supersaw_lead", A4, 0.34, BAR, art="fermata")
    g[7][BAR * 3 + 8] = n("shimmer_bell", 69, 0.22, 8,  art="fermata")
    return Pattern(name="c5_outro", num_steps=BAR * 4,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# CYCLE 6 — TWINKLE TWINKLE OUTRO (bars 37-41, 67.5-76.875s)
#   Public-domain Twinkle Twinkle Little Star (French folk c.1761, Mozart
#   variations K.265 1781). C major — the relative major of our A minor
#   Mountain King — which lands as natural resolution. 5 bars of pluck
#   melody over soft pad + a final shimmer bell on the held C.
#
#   Runs under the Napkin Films credits card (72-78s) so music never stops.
#   Math: 5 bars × 1.875s @ BPM 128 = 9.375s. Ends at 76.875s, right before
#   the final angelic sigh at 77.3s. Crisp.
# ══════════════════════════════════════════════════════════════════════════════
def pat_cycle6():
    g = grid(BAR * 5)

    # Twinkle melody on lead (arp_shimmer gives a music-box pluck that reads
    # as "light piano" against the rave cycles).
    # Bar 1: "Twinkle twinkle"   — C5 C5 G5 G5
    g[4][0]  = n("arp_shimmer", 72, 0.68, 3)
    g[4][4]  = n("arp_shimmer", 72, 0.68, 3)
    g[4][8]  = n("arp_shimmer", 79, 0.68, 3)
    g[4][12] = n("arp_shimmer", 79, 0.68, 3)
    # Bar 2: "little star"        — A5 A5 G5 (half note)
    g[4][16] = n("arp_shimmer", 81, 0.68, 3)
    g[4][20] = n("arp_shimmer", 81, 0.68, 3)
    g[4][24] = n("arp_shimmer", 79, 0.62, 8, art="tenuto")
    # Bar 3: "How I wonder"       — F5 F5 E5 E5
    g[4][32] = n("arp_shimmer", 77, 0.66, 3)
    g[4][36] = n("arp_shimmer", 77, 0.66, 3)
    g[4][40] = n("arp_shimmer", 76, 0.66, 3)
    g[4][44] = n("arp_shimmer", 76, 0.66, 3)
    # Bar 4: "what you are"       — D5 D5 C5 (half note)
    g[4][48] = n("arp_shimmer", 74, 0.66, 3)
    g[4][52] = n("arp_shimmer", 74, 0.66, 3)
    g[4][56] = n("arp_shimmer", 72, 0.62, 8, art="tenuto")
    # Bar 5: final held C5 (whole note fermata) + an E5 third on the half
    g[4][64] = n("arp_shimmer", 72, 0.58, 16, art="fermata")
    g[4][72] = n("arp_shimmer", 76, 0.42, 8,  art="fermata")

    # Pad bed — I-I-IV-V-I in C major (classic Twinkle harmony)
    # Uses low velocity so the lead sings through.
    place_pad(g, 0 * BAR, (60, 64, 67), vel_scale=0.45)   # C major
    place_pad(g, 1 * BAR, (60, 64, 67), vel_scale=0.45)   # C major
    place_pad(g, 2 * BAR, (65, 69, 72), vel_scale=0.48)   # F major
    place_pad(g, 3 * BAR, (67, 71, 74), vel_scale=0.50)   # G major (V)
    place_pad(g, 4 * BAR, (60, 64, 67), vel_scale=0.42)   # C major resolve

    # Shimmer bells — sparkle on downbeat of bars 1, 3, 5 and the final
    # half beat of bar 5. Mathematically: each bell hits a structural
    # moment (phrase start / IV chord / resolution / half-note landing).
    g[7][0]        = n("shimmer_bell", 84, 0.34, 6)            # bar 1 C6
    g[7][2 * BAR]  = n("shimmer_bell", 89, 0.34, 6)            # bar 3 F6
    g[7][4 * BAR]  = n("shimmer_bell", 84, 0.36, 12,           # bar 5 C6 held
                        art="fermata")
    g[7][4 * BAR + 8] = n("shimmer_bell", 91, 0.30, 8,         # bar 5 G6 accent
                           art="fermata")

    return Pattern(name="c6_twinkle_outro", num_steps=BAR * 5,
                   num_channels=CH, grid=g, bpm=BPM)


def build_song():
    return Song(
        title="Deduct Yourself (on Grieg's Mountain King + Twinkle coda)",
        bpm=BPM,
        patterns=[pat_cycle1(), pat_cycle2(), pat_cycle3(),
                  pat_cycle4(), pat_cycle5(), pat_cycle6()],
        sequence=[0, 1, 2, 3, 4, 5],
        panning={
            0: 0.0,     # kick center
            1: 0.0,     # clap/snare center
            2: 0.25,    # hat R
            3: -0.30,   # arp L (canon voice)
            4: 0.10,    # lead R (Mountain King motif)
            5: 0.0,     # bass center
            6: 0.0,     # pad wide
            7: 0.30,    # bell/fx R
        },
        channel_effects={
            0: {"reverb": 0.12},
            1: {"reverb": 0.24},
            2: {"reverb": 0.18, "delay": 0.14, "delay_feedback": 0.22},
            3: {"reverb": 0.34, "delay": 0.20, "delay_feedback": 0.32},
            4: {"reverb": 0.30, "delay": 0.16, "delay_feedback": 0.28},
            5: {"reverb": 0.12},
            6: {"reverb": 0.44},
            7: {"reverb": 0.50, "delay": 0.30, "delay_feedback": 0.38},
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
    out = Path("output/deduct_yourself_score.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.2f}s → {out}")
