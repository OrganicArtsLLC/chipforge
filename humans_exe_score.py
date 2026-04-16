"""humans_exe_score — four-theme comedy mashup for napkinfilms/humans_exe.

Each vignette gets a recognizable comedy theme reimagined as rave/electronic:
  P1 Pink Panther (sneak)      — V1 The ADR             0-24s
  P2 Axel F (Beverly Hills Cop) — V2 The Misdirect       24-48s
  P3 Yakety Sax (gentle half)   — V3 Amanda Callback     48-72s
  P4 Hall of the Mountain King  — V4 Escalation Ladder   72-102s (builds!)
  P5 Pink Panther (minor)       — V5 Scorpio Moon        102-126s
  P6 Axel F (full-tilt)         — V6 Kids Roast          126-156s
  P7 Yakety Sax (bureaucratic)  — V7 Spreadsheet         156-180s
  P8 Pink Panther (pad stripped) — V8 Warm Close          180-204s
  P9 Medley (all four)          — V9 Wrap                 204-222s

Unified BPM 120 throughout. Keys: F-based (F major / F minor / Bb major).
Honours the "not annoying" brief via sectional variation — same themes,
different orchestrations, dynamics, registers.

Run: .venv/bin/python3 humans_exe_score.py
Out: output/humans_exe_score.wav  (~222s)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav

BPM = 120
BAR = 16
CH  = 8   # 0 kick | 1 clap/snare | 2 hat | 3 arp | 4 lead | 5 bass | 6 pad | 7 bell/stab


# ── Notes (MIDI) ──────────────────────────────────────────────────────────────
# F minor / F major palette
F2, Bb2, C3 = 29, 34, 36
F3, G3, Ab3, Bb3, C4, Db4, Eb4, F4 = 41, 43, 44, 46, 48, 49, 51, 53
G4, A4, Ab4, Bb4, C5, Db5, D5, Eb5, E5, F5 = 55, 57, 56, 58, 60, 61, 62, 63, 64, 65
G5, Ab5, A5, Bb5, C6, Db6, D6, Eb6, F6 = 67, 68, 69, 70, 72, 73, 74, 75, 77

# Pink Panther native is Eb minor; we transpose to F minor (up 2 semitones)
# Axel F native is F minor (keep)
# Yakety Sax native is Bb major / F major — keep in F major
# Hall of the Mountain King native is B minor; transpose to F minor


def n(inst, midi, vel=0.80, dur=2, art="normal"):
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.92),
                     duration_steps=dur, instrument=inst, articulation=art)


def grid(steps):
    return [[None] * steps for _ in range(CH)]


# ══════════════════════════════════════════════════════════════════════════════
# P1 — PINK PANTHER (sneak) — V1 The ADR, 12 bars
# Signature: descending chromatic bass pizz + sly flute-like melody
# ══════════════════════════════════════════════════════════════════════════════
def pat_pink_panther_sneak():
    g = grid(BAR * 12)
    # Sneaky bass_pluck ostinato (the "dum da dum-dum" walk).
    # Original pattern: F, F#, G, F  (chromatic quarter-note walk)
    # In F minor: F, Gb, G, F
    bass_walk = [F2, F2+1, G3-12, F2, F2+1, G3-12, F2, F2, F2-2]  # 8 notes per bar
    for bar in range(12):
        off = bar * BAR
        # Quarter notes on beats
        for beat in (0, 4, 8, 12):
            idx = ((bar * 4) + (beat // 4)) % len(bass_walk)
            g[5][off + beat] = n("bass_pluck", bass_walk[idx], 0.60, 3, art="staccato")
        # Offbeat pings (the sneak accent)
        g[2][off + 2]  = n("hat_crisp", 42, 0.22, 1)
        g[2][off + 6]  = n("hat_crisp", 42, 0.22, 1)
        g[2][off + 10] = n("hat_crisp", 42, 0.22, 1)
        g[2][off + 14] = n("hat_crisp", 42, 0.22, 1)

    # Flute-like melody (saw_lead, quiet) — Pink Panther motif
    # Phrase: D5 Eb5 E5 C5 Db5 (approx)
    # In F minor: Ab4 Bb4 C5 ... Db5
    melody_notes = [
        (2,  F5,  3), (6,  Ab5, 2), (10, G5,  2), (14, F5,  4),   # bar 1
        (18, Eb5, 2), (20, F5,  3), (24, Ab5, 2), (28, G5,  4),   # bar 2
    ]
    # Repeat this 2-bar phrase 6 times = 12 bars
    for cycle in range(6):
        base = cycle * BAR * 2
        for step, note, dur in melody_notes:
            g[4][base + step] = n("saw_lead", note, 0.50, dur, art="legato")

    # Light pad bed
    for bar in range(12):
        off = bar * BAR
        g[6][off] = n("supersaw_pad", F3, 0.20, 16)
        g[6][off + 2] = n("supersaw_pad", Ab3, 0.14, 14)

    return Pattern(name="pink_panther_sneak", num_steps=BAR * 12,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# P2 — AXEL F — V2 The Misdirect, 12 bars
# Signature: iconic synth riff, 80s drums
# ══════════════════════════════════════════════════════════════════════════════
def pat_axel_f():
    g = grid(BAR * 12)
    # The iconic Axel F riff (8 steps per phrase, F minor):
    # F4, F4, Ab4, F4, Bb4, F4, Eb4, F4, C5, F4, Db5, C5, Ab4, F4, Eb4, F4
    riff = [(0, F4, 2, "marcato"), (4, F4, 2, "normal"),
            (6, Ab4, 2, "normal"), (8, F4, 2, "normal"),
            (10, Bb4, 2, "accent"), (12, F4, 2, "normal"),
            (14, Eb4, 2, "accent")]
    riff2 = [(0, F4, 2, "normal"), (2, C5, 2, "accent"),
             (4, F4, 2, "normal"), (6, Db5, 3, "tenuto"),
             (8, C5, 2, "normal"), (10, Ab4, 2, "normal"),
             (12, F4, 2, "normal"), (14, Eb4, 2, "accent")]
    for bar in range(12):
        off = bar * BAR
        # Alternate riff phrases
        phrase = riff if bar % 2 == 0 else riff2
        for step, note, dur, art in phrase:
            g[4][off + step] = n("supersaw_lead", note, 0.72, dur, art=art)

        # Drums — 4-on-the-floor + snare on 2/4
        for beat in (0, 4, 8, 12):
            g[0][off + beat] = n("kick_deep", 36, 0.72, 2, art="marcato")
        g[1][off + 4]  = n("clap_tight", 38, 0.60, 2, art="accent")
        g[1][off + 12] = n("clap_tight", 38, 0.60, 2, art="accent")
        # Hats offbeat
        for step in (2, 6, 10, 14):
            g[2][off + step] = n("hat_tight", 42, 0.35, 1)

        # Bass pumping F
        for beat in (0, 8):
            g[5][off + beat] = n("fm_bass", F2, 0.65, 4, art="marcato")

        # Pad
        g[6][off] = n("supersaw_pad", F3, 0.28, 16)
        g[6][off + 1] = n("supersaw_pad", Ab3, 0.22, 15)
        g[6][off + 2] = n("supersaw_pad", C4, 0.20, 14)

    # Bell sparkle on the "pizza moment" (around bar 6-7)
    g[7][BAR * 6 + 8] = n("shimmer_bell", F6, 0.55, 4)
    g[7][BAR * 7 + 0] = n("shimmer_bell", C6, 0.50, 4)

    return Pattern(name="axel_f", num_steps=BAR * 12,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# P3 — YAKETY SAX (gentle half-time) — V3 Amanda Callback, 12 bars
# Signature: descending staccato sax-like riff, but mellow, half-speed feel
# ══════════════════════════════════════════════════════════════════════════════
def pat_yakety_gentle():
    g = grid(BAR * 12)
    # Yakety Sax riff in F major — the descending 8-note figure
    # F5 D5 C5 F4 -- F5 D5 Bb4 A4 (approx)
    sax_bar = [
        (0, F5, 2), (2, D5, 2), (4, C5, 2), (6, F4, 2),
        (8, F5, 2), (10, D5, 2), (12, Bb4, 2), (14, A4, 3),
    ]
    for bar in range(12):
        off = bar * BAR
        # Only every other bar plays the riff (half-time feel)
        if bar % 2 == 0:
            for step, note, dur in sax_bar:
                g[4][off + step] = n("saw_lead", note, 0.45, dur, art="staccato")
        # Gentle kick on 1 and 3 only
        g[0][off] = n("kick_deep", 36, 0.50, 2)
        g[0][off + 8] = n("kick_deep", 36, 0.45, 2)
        # Soft hats
        for step in (4, 12):
            g[2][off + step] = n("hat_tight", 42, 0.22, 1)
        # Honky-tonk bass walking (root-fifth)
        bass_notes = [F2, C3, F2, C3]  # root fifth root fifth
        for i, bn in enumerate(bass_notes):
            g[5][off + i * 4] = n("bass_pluck", bn, 0.48, 3, art="staccato")
        # Warm pad
        g[6][off] = n("supersaw_pad", F3, 0.30, 16)
        g[6][off + 1] = n("supersaw_pad", A4 - 12, 0.22, 15)
        g[6][off + 2] = n("supersaw_pad", C4, 0.18, 14)

    return Pattern(name="yakety_gentle", num_steps=BAR * 12,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# P4 — HALL OF THE MOUNTAIN KING — V4 Escalation, 15 bars
# Famous descending motif. Starts quiet+slow-feel, BUILDS to climax.
# ══════════════════════════════════════════════════════════════════════════════
def pat_mountain_king():
    g = grid(BAR * 15)
    # Grieg's motif, transposed to F minor:
    # Original (B minor): B C D B D C E D F#  (descending-ascending twist)
    # F minor: F Gb Ab F Ab Gb Bb Ab C
    # Actual pattern is: descend through the minor scale then do the "answer" up
    motif = [F4, G3+1, Ab4, F4, Ab4, G3+1, Bb4, Ab4]        # 8-note motif
    # Repeats: each repeat adds density & intensity

    for bar in range(15):
        off = bar * BAR
        # Intensity tier by bar group
        if bar < 3:       tier = 0    # whispering pizz
        elif bar < 7:     tier = 1    # adding drums
        elif bar < 11:    tier = 2    # full build
        else:             tier = 3    # climax + release

        # Motif plays every bar, on 8th notes (2 steps each)
        for i, note in enumerate(motif):
            step = i * 2
            inst = ["bass_pluck", "bass_pluck", "saw_lead", "supersaw_lead"][tier]
            vel = [0.40, 0.55, 0.72, 0.85][tier]
            # Octave up each tier
            note_shifted = note + tier * 12 if tier >= 2 else note
            g[4][off + step] = n(inst, note_shifted, vel, 2,
                                  art="staccato" if tier < 2 else "marcato")

        # Bass — sustained root
        root = F2 if bar % 2 == 0 else C3
        g[5][off] = n("fm_bass", root, 0.50 + 0.15 * tier, 16,
                       art="tenuto" if tier < 2 else "marcato")

        # Drums come in at tier 1
        if tier >= 1:
            g[0][off] = n("kick_deep", 36, 0.55, 2)
            g[0][off + 8] = n("kick_deep", 36, 0.50, 2)
        if tier >= 2:
            for beat in (0, 4, 8, 12):
                g[0][off + beat] = n("kick_deep", 36, 0.72, 2, art="marcato")
            g[1][off + 4] = n("clap_tight", 38, 0.55, 2)
            g[1][off + 12] = n("clap_tight", 38, 0.55, 2)
        if tier >= 2:
            for step in (2, 6, 10, 14):
                g[2][off + step] = n("hat_tight", 42, 0.32, 1)
        if tier >= 3:
            # Full rave — 16th hats, big lead doubled
            for s in range(16):
                g[2][off + s] = n("hat_tight", 42, 0.38, 1)
            # Doubled motif up an octave in arp channel
            for i, note in enumerate(motif):
                g[3][off + i * 2] = n("arp_shimmer", note + 24, 0.60, 2)

        # Pad swells
        g[6][off] = n("supersaw_pad", F3, 0.30 + 0.10 * tier, 16)
        g[6][off + 1] = n("supersaw_pad", Ab3, 0.24 + 0.08 * tier, 15)
        g[6][off + 2] = n("supersaw_pad", C4, 0.18 + 0.08 * tier, 14)

    # Abrupt cadence — bell hit on the final "STOP"
    g[7][BAR * 14 + 0] = n("fx_drop", F3, 0.80, 2)
    g[7][BAR * 14 + 8] = n("shimmer_bell", F6, 0.70, 8, art="fermata")
    return Pattern(name="mountain_king", num_steps=BAR * 15,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# P5 — PINK PANTHER (minor / darker) — V5 Scorpio Moon, 12 bars
# ══════════════════════════════════════════════════════════════════════════════
def pat_pink_panther_dark():
    g = grid(BAR * 12)
    bass_walk = [F2, F2+1, G3-12, F2, F2+1, Eb4-24, F2, F2]
    for bar in range(12):
        off = bar * BAR
        for beat in (0, 4, 8, 12):
            idx = ((bar * 4) + (beat // 4)) % len(bass_walk)
            g[5][off + beat] = n("bass_pluck", bass_walk[idx], 0.55, 3, art="staccato")
        # Sparser hats
        g[2][off + 6]  = n("hat_crisp", 42, 0.20, 1)
        g[2][off + 14] = n("hat_crisp", 42, 0.20, 1)

    # Darker melody — minor intervals
    melody_notes = [
        (2,  F5,  3), (6,  G5,  2), (10, Ab5, 2), (14, F5, 4),
        (18, Eb5, 2), (20, Db5, 3), (24, F5,  2), (28, Eb5, 4),
    ]
    for cycle in range(6):
        base = cycle * BAR * 2
        for step, note, dur in melody_notes:
            g[4][base + step] = n("saw_lead", note, 0.45, dur, art="legato")

    # Pad
    for bar in range(12):
        off = bar * BAR
        g[6][off] = n("supersaw_pad", F3, 0.25, 16)
        g[6][off + 1] = n("supersaw_pad", Ab3, 0.18, 15)

    return Pattern(name="pink_panther_dark", num_steps=BAR * 12,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# P6 — AXEL F (full-tilt) — V6 Kids Roast, 15 bars
# Everything cranked — maximum 80s chase energy.
# ══════════════════════════════════════════════════════════════════════════════
def pat_axel_f_full():
    g = grid(BAR * 15)
    riff = [(0, F4, 2, "marcato"), (4, F4, 2, "normal"),
            (6, Ab4, 2, "accent"), (8, F4, 2, "normal"),
            (10, Bb4, 2, "accent"), (12, F4, 2, "normal"),
            (14, Eb4, 2, "accent")]
    riff_high = [(0, F5, 2, "marcato"), (2, C5, 2, "accent"),
                 (4, F5, 2, "tenuto"), (6, Db6, 3, "tenuto"),
                 (8, C5, 2, "normal"), (10, Ab4, 2, "normal"),
                 (12, F4, 2, "normal"), (14, Eb4, 2, "accent")]
    for bar in range(15):
        off = bar * BAR
        phrase = riff if bar % 2 == 0 else riff_high
        for step, note, dur, art in phrase:
            g[4][off + step] = n("supersaw_lead", note, 0.82, dur, art=art)

        for beat in (0, 4, 8, 12):
            g[0][off + beat] = n("kick_deep", 36, 0.80, 2, art="marcato")
        g[1][off + 4]  = n("clap_tight", 38, 0.70, 2, art="accent")
        g[1][off + 12] = n("clap_tight", 38, 0.70, 2, art="accent")
        # Fast hats — 16ths
        for s in range(16):
            g[2][off + s] = n("hat_tight", 42, 0.30 + (0.15 if s % 4 == 0 else 0), 1)
        # Bass pumping hard
        for beat in (0, 4, 8, 12):
            g[5][off + beat] = n("fm_bass", F2, 0.75, 3, art="marcato")
        # Arp twirling
        arp_pat = [F4, Ab4, C5, F5, Ab4, C5, F5, Ab5,
                   Eb4, G4, Bb4, Eb5, G4, Bb4, Eb5, G5]
        for i, note in enumerate(arp_pat):
            g[3][off + i] = n("arp_shimmer", note, 0.55, 2)
        # Pad
        g[6][off] = n("supersaw_pad", F3, 0.35, 16)
        g[6][off + 1] = n("supersaw_pad", Ab3, 0.28, 15)

        # Bell accents on every 4 bars
        if bar % 4 == 0:
            g[7][off] = n("shimmer_bell", F6, 0.55, 4)

    return Pattern(name="axel_f_full", num_steps=BAR * 15,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# P7 — YAKETY SAX (bureaucratic accordion) — V7 Spreadsheet, 12 bars
# Fast, mocking, on organ/brass instead of saw
# ══════════════════════════════════════════════════════════════════════════════
def pat_yakety_bureaucratic():
    g = grid(BAR * 12)
    sax_bar = [
        (0, F5, 2), (2, D5, 2), (4, C5, 2), (6, F4, 2),
        (8, F5, 2), (10, D5, 2), (12, Bb4, 2), (14, A4, 2),
    ]
    for bar in range(12):
        off = bar * BAR
        # Full riff every bar — this is the "chase" feel
        for step, note, dur in sax_bar:
            # Use fm_organ for the mockingly-bureaucratic voice
            g[4][off + step] = n("fm_organ", note, 0.60, dur, art="staccato")
        # Brass stab punctuation
        g[7][off] = n("brass_stab", F3, 0.50, 2, art="marcato")
        g[7][off + 8] = n("brass_stab", C4, 0.45, 2, art="marcato")
        # Walking bass
        bass_notes = [F2, C3, F2, Bb2]
        for i, bn in enumerate(bass_notes):
            g[5][off + i * 4] = n("bass_pluck", bn, 0.55, 3, art="staccato")
        # Kick + snare typewriter
        for beat in (0, 4, 8, 12):
            g[0][off + beat] = n("kick_deep", 36, 0.60, 2)
        g[1][off + 4] = n("snare_tight", 38, 0.50, 1)
        g[1][off + 12] = n("snare_tight", 38, 0.50, 1)
        # Busy hats
        for s in (2, 6, 10, 14):
            g[2][off + s] = n("hat_tight", 42, 0.30, 1)

    return Pattern(name="yakety_bureaucratic", num_steps=BAR * 12,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# P8 — PINK PANTHER (pad stripped, warm) — V8 Warm Close, 12 bars
# Just pad + a single gentle pluck of the melody, no drums. Earned quiet.
# ══════════════════════════════════════════════════════════════════════════════
def pat_pink_panther_warm():
    g = grid(BAR * 12)
    for bar in range(12):
        off = bar * BAR
        # Rich pad bed
        g[6][off] = n("supersaw_pad", F3, 0.40, 16, art="fermata")
        g[6][off + 1] = n("supersaw_pad", Ab3, 0.32, 15)
        g[6][off + 2] = n("supersaw_pad", C4, 0.28, 14)
        g[6][off + 3] = n("supersaw_pad", F4, 0.22, 13)

        # Single melody pluck every 2 bars
        if bar % 2 == 0:
            g[4][off + 4] = n("fm_bell", F5, 0.40, 8, art="fermata")
        else:
            g[4][off + 4] = n("fm_bell", Ab5, 0.38, 8, art="fermata")

        # Very distant bell every 4 bars
        if bar % 4 == 0 and bar > 0:
            g[7][off] = n("shimmer_bell", F6, 0.28, 12, art="fermata")

        # Soft bass drone
        g[5][off] = n("bass_pluck", F2, 0.30, 16, art="tenuto")

    return Pattern(name="pink_panther_warm", num_steps=BAR * 12,
                   num_channels=CH, grid=g, bpm=BPM)


# ══════════════════════════════════════════════════════════════════════════════
# P9 — MEDLEY (all four themes, quick cuts) — V9 Wrap, 8 bars
# Each theme gets ~2 bars, then a big unified cadence.
# ══════════════════════════════════════════════════════════════════════════════
def pat_medley():
    g = grid(BAR * 8)

    # Unified backbone: kick + clap all 8 bars
    for bar in range(8):
        off = bar * BAR
        for beat in (0, 4, 8, 12):
            g[0][off + beat] = n("kick_deep", 36, 0.78, 2, art="marcato")
        g[1][off + 4]  = n("clap_tight", 38, 0.68, 2, art="accent")
        g[1][off + 12] = n("clap_tight", 38, 0.68, 2, art="accent")
        for s in (2, 6, 10, 14):
            g[2][off + s] = n("hat_tight", 42, 0.38, 1)
        g[5][off]     = n("fm_bass", F2, 0.72, 4, art="marcato")
        g[5][off + 8] = n("fm_bass", F2, 0.70, 4)
        g[6][off]     = n("supersaw_pad", F3, 0.40, 16)
        g[6][off + 1] = n("supersaw_pad", Ab3, 0.30, 15)

    # Bars 1-2: Pink Panther
    g[4][0]  = n("saw_lead", F5, 0.70, 3, art="staccato")
    g[4][4]  = n("saw_lead", Ab5, 0.72, 2)
    g[4][8]  = n("saw_lead", G5, 0.70, 2)
    g[4][12] = n("saw_lead", F5, 0.72, 4, art="tenuto")
    g[4][16] = n("saw_lead", Eb5, 0.68, 2)
    g[4][20] = n("saw_lead", F5, 0.72, 2)
    g[4][24] = n("saw_lead", Ab5, 0.74, 2)
    g[4][28] = n("saw_lead", G5, 0.72, 4, art="tenuto")

    # Bars 3-4: Axel F
    g[4][BAR * 2 + 0]  = n("supersaw_lead", F4,  0.80, 2, art="marcato")
    g[4][BAR * 2 + 6]  = n("supersaw_lead", Ab4, 0.82, 2, art="accent")
    g[4][BAR * 2 + 10] = n("supersaw_lead", Bb4, 0.85, 2, art="accent")
    g[4][BAR * 2 + 14] = n("supersaw_lead", Eb4, 0.80, 2, art="accent")
    g[4][BAR * 3 + 0]  = n("supersaw_lead", F4,  0.80, 2)
    g[4][BAR * 3 + 2]  = n("supersaw_lead", C5,  0.85, 2, art="accent")
    g[4][BAR * 3 + 6]  = n("supersaw_lead", Db5, 0.82, 3, art="tenuto")
    g[4][BAR * 3 + 12] = n("supersaw_lead", F4,  0.78, 4)

    # Bars 5-6: Yakety Sax
    for cycle in range(2):
        off = (BAR * 4) + cycle * BAR
        riff_notes = [(0, F5, 2), (2, D5, 2), (4, C5, 2), (6, F4, 2),
                      (8, F5, 2), (10, D5, 2), (12, Bb4, 2), (14, A4, 3)]
        for step, note, dur in riff_notes:
            g[4][off + step] = n("saw_lead", note, 0.68, dur, art="staccato")

    # Bars 7-8: Hall of the Mountain King climax
    motif = [F4, G3+1, Ab4, F4, Ab4, G3+1, Bb4, Ab4]
    for cycle in range(2):
        off = (BAR * 6) + cycle * BAR
        for i, note in enumerate(motif):
            g[4][off + i * 2] = n("supersaw_lead", note + 12, 0.85, 2,
                                   art="marcato")
        # Arp doubling
        for i, note in enumerate(motif):
            g[3][off + i * 2] = n("arp_shimmer", note + 24, 0.70, 2)

    # Huge bell cadence on final beat
    g[7][BAR * 7 + 12] = n("shimmer_bell", F6, 0.80, 4, art="fermata")
    g[7][BAR * 7 + 14] = n("fx_drop", F3, 0.75, 2)

    return Pattern(name="medley", num_steps=BAR * 8,
                   num_channels=CH, grid=g, bpm=BPM)


def build_song():
    return Song(
        title="HUMANS.EXE Soundtrack",
        bpm=BPM,
        patterns=[
            pat_pink_panther_sneak(),    # 0
            pat_axel_f(),                # 1
            pat_yakety_gentle(),         # 2
            pat_mountain_king(),         # 3
            pat_pink_panther_dark(),     # 4
            pat_axel_f_full(),           # 5
            pat_yakety_bureaucratic(),   # 6
            pat_pink_panther_warm(),     # 7
            pat_medley(),                # 8
        ],
        sequence=[0, 1, 2, 3, 4, 5, 6, 7, 8],
        panning={
            0: 0.0,   1: 0.0,    2: 0.20,
            3: -0.25, 4: 0.10,   5: 0.0,
            6: 0.0,   7: 0.25,
        },
        channel_effects={
            0: {"reverb": 0.08},
            1: {"reverb": 0.20},
            2: {"reverb": 0.15, "delay": 0.12, "delay_feedback": 0.20},
            3: {"reverb": 0.28, "delay": 0.18, "delay_feedback": 0.25},
            4: {"reverb": 0.22, "delay": 0.10, "delay_feedback": 0.18},
            5: {"reverb": 0.10},
            6: {"reverb": 0.35},
            7: {"reverb": 0.40, "delay": 0.22, "delay_feedback": 0.30},
        },
        master_reverb=0.15,
        master_delay=0.06,
    )


if __name__ == "__main__":
    song = build_song()
    audio = render_song(song, panning=song.panning,
                        channel_effects=song.channel_effects,
                        master_reverb=song.master_reverb,
                        master_delay=song.master_delay)
    out = Path("output/humans_exe_score.wav")
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)
    dur = len(audio) / 44100
    print(f"Rendered: {dur:.2f}s → {out}")
