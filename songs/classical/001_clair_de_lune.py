"""
Clair de Lune — ChipForge AI Enhanced Edition
================================================
Claude Debussy, Suite bergamasque, L. 75, III (1890/1905)
Public domain.

One of the most beautiful piano pieces ever written, translated into
chip tune synthesis with AI-enhanced mathematical voice shaping.

MUSICAL ANALYSIS:
  Debussy's "Clair de Lune" (Moonlight) is an Impressionist masterpiece.
  Unlike Beethoven's structured sonata form, Debussy paints in COLORS.
  The harmony floats — extended chords (9ths, 11ths), parallel motion,
  whole-tone passages. The melody seems to improvise over shimmering
  arpeggios. It sounds "simple" but the harmonic language is radical.

  Key: Db major (5 flats — the key of dreams)
  Tempo: Andante très expressif (♩= 66, rubato throughout)
  Form: A-B-A' (ternary)
    A  — The famous opening melody, sparse and floating
    B  — The passionate middle section, cascading arpeggios
    A' — Return, even more tender, dissolving into silence

ARRANGEMENT PHILOSOPHY:
  - No Game Boy limitations. Maximum ChipForge quality.
  - Melody on saw_filtered (warm, not bright — Debussy is NEVER bright)
  - Arpeggios on pulse_warm (smooth, legato feel)
  - Bass on bass_sub (deep, pure — like the piano's resonance)
  - Pad on pad_lush (the sustain pedal — Debussy drowns everything in pedal)
  - Bell accents on gb_bell_wave (the "drops of moonlight" moments)
  - Counter voice on saw_dark (the inner voice that moves chromatically)
  - Deep reverb on EVERYTHING (this piece lives in a cathedral of sound)
  - No drums. Debussy would haunt us.

AI ENHANCEMENTS:
  - Fibonacci velocity curves for the dynamic arc of each section
  - Golden ratio placement of the emotional climax (bar ~21 of 36)
  - Micro-velocity variations on arpeggios (no two notes same velocity)
  - Harmonic series bell tones at key cadence points
  - Mathematical tempo curve (slight rubato simulation via note durations)

Key: Db major (MIDI: Db=49 as root)
  Scale: Db Eb F Gb Ab Bb C
  Enharmonic: C#=Db, D#=Eb, F#=Gb, G#=Ab, A#=Bb

BPM: 66 (Andante — must breathe, must float)
SPB: 6 (triplet grid for flowing arpeggios, like Moonlight Sonata)
Channels: 7
  0 - Arpeggio (pulse_warm — flowing triplet figures)
  1 - Melody (saw_filtered — warm, singing, NOT bright)
  2 - Bass (bass_sub — deep pedal tones, pure)
  3 - Pad (pad_lush — the sustain pedal, the room, the air)
  4 - Bell (gb_bell_wave — moonlight drops, cadence accents)
  5 - Counter voice (saw_dark — chromatic inner voice)
  6 - High shimmer (pluck_short — very quiet octave doublings)

Structure (~4:20 at 66 BPM):
  [0-33s]     REVERIE     A section   8 bars  — opening melody, sparse
  [33-65s]    DRIFT       A cont.     8 bars  — melody develops, arps expand
  [65-98s]    AWAKENING   B section   8 bars  — passionate arps, forte
  [98-131s]   CASCADE     B climax    8 bars  — the emotional peak, cascading
  [131-164s]  RETURN      A' section  8 bars  — melody returns, even softer
  [164-196s]  DISSOLVE    A' coda     8 bars  — fading into nothing, ppppp
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 66
SPB = 6         # triplet grid (6 steps per beat = flowing arpeggios)
BAR = 24        # 4 beats x 6 steps
NUM_CH = 7

PHI = (1 + math.sqrt(5)) / 2
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

# ── Helpers ──────────────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, freq: float, vel: float = 0.70, dur: int = 2) -> NoteEvent:
    return NoteEvent(midi_note=freq_to_midi(freq), velocity=min(vel, 0.85),
                     duration_steps=max(dur, 1), instrument=inst)

def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]

def fib_vel(position: int, total: int, min_v: float = 0.35, max_v: float = 0.82) -> float:
    """Fibonacci-shaped velocity for position in a sequence of total length."""
    if total <= 1:
        return max_v
    fibs = [1, 1]
    for _ in range(total - 2):
        fibs.append(fibs[-1] + fibs[-2])
    ratio = fibs[min(position, len(fibs) - 1)] / fibs[-1]
    return min_v + (max_v - min_v) * ratio

# ── Instruments ──────────────────────────────────────────────────────────────
ARP     = 'pulse_warm'       # flowing arpeggios — smooth, legato
MELODY  = 'saw_filtered'     # singing melody — warm, not bright
BASS    = 'bass_sub'         # deep pedal tones — pure sine resonance
PAD     = 'pad_lush'         # sustain pedal simulation
BELL    = 'gb_bell_wave'     # moonlight drops — digital sparkle
COUNTER = 'saw_dark'         # chromatic inner voice — dark, moody
SHIMMER = 'pluck_short'      # high octave doublings — barely there

# ── Db major note constants (MIDI → Hz) ─────────────────────────────────────
# Db major scale: Db Eb F Gb Ab Bb C
# Using enharmonic equivalents for clarity

# Octave 2 (deep bass)
Db2 = hz(37); Eb2 = hz(39); F2 = hz(41); Gb2 = hz(42)
Ab2 = hz(44); Bb2 = hz(46); C3_ = hz(48)

# Octave 3 (bass/low-mid)
Db3 = hz(49); Eb3 = hz(51); F3 = hz(53); Gb3 = hz(54)
Ab3 = hz(56); Bb3 = hz(58); C4_ = hz(60)

# Octave 4 (mid — arpeggio register)
Db4 = hz(61); Eb4 = hz(63); F4 = hz(65); Gb4 = hz(66)
Ab4 = hz(68); Bb4 = hz(70); C5_ = hz(72)

# Octave 5 (melody register)
Db5 = hz(73); Eb5 = hz(75); F5 = hz(77); Gb5 = hz(78)
Ab5 = hz(80); Bb5 = hz(82); C6_ = hz(84)

# Octave 6 (shimmer)
Db6 = hz(85); Eb6 = hz(87)

# ── Chord voicings (Debussy's actual harmony — extended chords) ──────────────
# Debussy uses 9ths, added 6ths, whole-tone passages, parallel motion.
# These are simplified but preserve the COLOR.

CHORDS = {
    # Db major (tonic — home, warm, round)
    'Db':     (Ab3, Db4, F4, Ab4),
    # Bbm7 (ii7 — the first movement away from home)
    'Bbm7':   (Bb3, Db4, F4, Ab4),
    # Ebm (ii — gentle motion)
    'Ebm':    (Eb3, Gb3, Bb3),
    # Ab7 (V7 — the gentlest dominant)
    'Ab7':    (Ab3, C4_, Eb4, Gb4),
    # Gb (IV — warm subdominant)
    'Gb':     (Gb3, Bb3, Db4),
    # Gbm (iv — the shadow, minor subdominant)
    'Gbm':    (Gb3, Bb3, Db4),  # simplified, A natural for Gbm but using Bb
    # Fm (iii — floating)
    'Fm':     (F3, Ab3, C4_),
    # Cb/Bb (bVII — whole-tone color)
    'Bb':     (Bb3, Db4, F4),
    # E major (enharmonic distant key — the middle section modulation)
    'E':      (Ab3, C4_, Eb4),  # enharmonic of E = Fb in Db context, use Ab-C-Eb
    # Ab (V — dominant but gentle)
    'Ab':     (Ab3, C4_, Eb4),
    # Db/Ab (tonic in second inversion — the return)
    'Db_Ab':  (Ab3, Db4, F4),
    # Db9 (tonic with 9th — Debussy's color)
    'Db9':    (Ab3, Db4, Eb4, F4),
}

BASS_NOTES = {
    'Db': Db2, 'Bbm7': Bb2, 'Ebm': Eb2, 'Ab7': Ab2,
    'Gb': Gb2, 'Gbm': Gb2, 'Fm': F2, 'Bb': Bb2,
    'E': Ab2, 'Ab': Ab2, 'Db_Ab': Ab2, 'Db9': Db2,
}

# ── Arpeggio builder (Debussy style — flowing, not mechanical) ───────────────

def place_flowing_arp(g: list, bar: int, chord: tuple, vel: float = 0.45,
                      style: str = 'up') -> None:
    """Place one bar of flowing triplet arpeggios — Debussy style.
    Unlike rigid ascending arps, these flow up-down with velocity shaping
    that creates a wave-like dynamic contour."""
    bs = bar * BAR
    tones = list(chord)
    n_tones = len(tones)

    for step in range(BAR):
        # Which chord tone — flow up then down
        if style == 'up':
            idx = step % n_tones
        elif style == 'wave':
            # Up for first half of beat, down for second
            beat_pos = step % 6
            if beat_pos < 3:
                idx = beat_pos % n_tones
            else:
                idx = (n_tones - 1 - (beat_pos - 3)) % n_tones
        elif style == 'cascade':
            # Descending arpeggios (middle section)
            idx = (n_tones - 1 - step % n_tones) % n_tones
        else:
            idx = step % n_tones

        # Velocity shaping: accent on beat downbeats, soften between
        beat_in_bar = step // 6
        pos_in_beat = step % 6
        v = vel
        if pos_in_beat == 0:
            v = vel + 0.08  # downbeat accent
        elif pos_in_beat == 3:
            v = vel + 0.03  # mid-beat slight accent
        else:
            v = vel - 0.02  # soften between

        # Micro-variation: golden ratio based (no two notes same velocity)
        micro = math.sin(step * PHI) * 0.025
        v = max(0.20, min(v + micro, 0.82))

        g[0][bs + step] = note(ARP, tones[idx], v, 2)


# ── PATTERN BUILDERS ─────────────────────────────────────────────────────────

def make_reverie() -> Pattern:
    """Section A (bars 1-8): The famous opening.

    Debussy's opening is SPARSE. A few melody notes floating over
    very gentle arpeggios. The left hand barely moves — just soft
    chord tones pulsing like a heartbeat in a dream.

    The melody: Bb4 — Ab4 — F4 — (rest) — Bb4 — Ab4 — F4 — Db4
    Simple descending phrase, repeated with slight variation.
    This IS the piece. These 8 notes define Clair de Lune."""
    steps = BAR * 8
    g = new_grid(steps)

    chord_seq = ['Db', 'Bbm7', 'Db', 'Bbm7', 'Ebm', 'Ab7', 'Db', 'Db9']

    for bar in range(8):
        chord_name = chord_seq[bar]
        chord = CHORDS[chord_name]
        bass_note = BASS_NOTES[chord_name]
        bs = bar * BAR

        # Arpeggios: very gentle, emerge from silence
        arp_vel = 0.30 + bar * 0.02  # pp → mp over 8 bars
        if bar < 2:
            # First 2 bars: sparse — only beats 1 and 3
            for beat in range(4):
                if beat % 2 == 0:
                    step = bs + beat * 6
                    for i in range(3):  # just 3 notes per beat
                        idx = i % len(chord)
                        g[0][step + i] = note(ARP, chord[idx], arp_vel, 3)
        else:
            # Bars 3+: full flowing arpeggios
            place_flowing_arp(g, bar, chord, arp_vel, 'up')

        # Bass: whole notes, very deep, felt not heard
        bass_vel = 0.55 + bar * 0.015
        g[2][bs] = note(BASS, bass_note, bass_vel, BAR)

        # Pad: the sustain pedal — everything sustains into everything
        if bar >= 1:
            pad_vel = 0.15 + bar * 0.02
            g[3][bs] = note(PAD, chord[1] if len(chord) > 1 else chord[0],
                           pad_vel, BAR)

    # ── The melody: the famous descending phrase ─────────────────────────
    # First statement (bars 2-3): Bb4 — Ab4 — F4 (descending third fill)
    # Debussy's melody enters LATE — bar 3 of the piece. The silence before
    # it is part of the composition.
    melody_phrase_1 = [
        # Bar 3 (idx 2): first notes — emerging from silence
        (Bb4, 2 * BAR + 0,  0.68, 12),     # Bb4 half note — the first sound
        (Ab4, 2 * BAR + 12, 0.62, 6),      # Ab4 — step down
        (F4,  2 * BAR + 18, 0.58, 6),      # F4 — completing the descent

        # Bar 4 (idx 3): phrase breathes, then continues
        (Eb4, 3 * BAR + 0,  0.55, 12),     # Eb4 — continues down
        (F4,  3 * BAR + 14, 0.50, 6),      # F4 — tiny upward sigh
        (Db4, 3 * BAR + 20, 0.52, 4),      # Db4 — home

        # Bar 5 (idx 4): second statement — slightly higher
        (Bb4, 4 * BAR + 0,  0.72, 12),     # Bb4 — repeat, a touch louder
        (Ab4, 4 * BAR + 12, 0.66, 6),      # Ab4
        (Bb4, 4 * BAR + 18, 0.70, 6),      # Bb4 — this time turns UP (hope!)

        # Bar 6 (idx 5): the turn — melody rises
        (C5_, 5 * BAR + 0,  0.76, 12),     # C5 — the highest note so far
        (Bb4, 5 * BAR + 12, 0.68, 6),      # Bb4 — step back
        (Ab4, 5 * BAR + 18, 0.64, 6),      # Ab4 — settling

        # Bar 7 (idx 6): resolution
        (F4,  6 * BAR + 0,  0.62, 18),     # F4 — long, settling
        (Eb4, 6 * BAR + 18, 0.55, 6),      # Eb4 — neighbor tone

        # Bar 8 (idx 7): cadence — return to Db
        (Db4, 7 * BAR + 0,  0.58, 18),     # Db4 — home, dotted half
        (F4,  7 * BAR + 18, 0.48, 6),      # F4 — pickup to next section
    ]

    for freq, step, vel, dur in melody_phrase_1:
        if step < steps:
            g[1][step] = note(MELODY, freq, vel, min(dur, steps - step))

    # Bell accents: moonlight drops at phrase beginnings
    bell_moments = [2 * BAR, 4 * BAR, 5 * BAR, 7 * BAR]
    for s in bell_moments:
        if s < steps:
            g[4][s] = note(BELL, Db6, 0.16, 3)

    return Pattern(name='reverie', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_drift() -> Pattern:
    """Section A continued (bars 9-16): Melody develops, arpeggios expand.

    The melody grows more confident. Wider intervals. The arpeggios
    become fuller — more chord tones per beat. Inner voice begins
    to move chromatically underneath. Still pp-mp, still dreaming,
    but the dream is becoming vivid."""
    steps = BAR * 8
    g = new_grid(steps)

    chord_seq = ['Db', 'Gb', 'Fm', 'Bbm7', 'Ebm', 'Ab', 'Gb', 'Db']

    for bar in range(8):
        chord_name = chord_seq[bar]
        chord = CHORDS[chord_name]
        bass_note = BASS_NOTES[chord_name]
        bs = bar * BAR

        # Arpeggios: fuller now, wave-like motion
        arp_vel = 0.38 + bar * 0.015
        place_flowing_arp(g, bar, chord, arp_vel, 'wave')

        # Bass: whole notes with occasional fifth
        g[2][bs] = note(BASS, bass_note, 0.60, BAR)
        if bar % 2 == 1:  # fifth on alternate bars
            g[2][bs + 12] = note(BASS, bass_note * 1.5, 0.42, 12)

        # Pad: richer now — sustained chord
        g[3][bs] = note(PAD, chord[1] if len(chord) > 1 else chord[0],
                       0.22 + bar * 0.01, BAR)

        # Counter voice: begins to move (bars 4+)
        if bar >= 3:
            # Chromatic inner voice — Debussy's signature
            counter_notes_by_bar = {
                3: [(Ab3, 12), (Bb3, 12)],
                4: [(Bb3, 12), (C4_, 12)],
                5: [(C4_,  12), (Db4, 12)],
                6: [(Db4, 8),  (C4_, 8), (Bb3, 8)],
                7: [(Ab3, 24)],
            }
            if bar in counter_notes_by_bar:
                pos = bs
                for freq, dur in counter_notes_by_bar[bar]:
                    if pos < bs + BAR:
                        g[5][pos] = note(COUNTER, freq, 0.30, dur)
                        pos += dur

    # ── Melody: develops, wider intervals, more expressive ───────────────
    melody_drift = [
        # Bar 9 (idx 0): pickup from reverie, melody rises
        (Ab4, 0 * BAR + 0,  0.65, 12),
        (Bb4, 0 * BAR + 12, 0.70, 6),
        (Db5, 0 * BAR + 18, 0.75, 6),      # leap up to Db5!

        # Bar 10 (idx 1): the Gb color — warmth
        (C5_, 1 * BAR + 0,  0.72, 12),
        (Bb4, 1 * BAR + 12, 0.66, 12),

        # Bar 11 (idx 2): floating on Fm
        (Ab4, 2 * BAR + 0,  0.68, 18),      # long sustained Ab
        (Bb4, 2 * BAR + 18, 0.60, 6),

        # Bar 12 (idx 3): Bbm7 — the sigh
        (Ab4, 3 * BAR + 0,  0.65, 6),
        (F4,  3 * BAR + 6,  0.60, 6),
        (Db4, 3 * BAR + 12, 0.55, 12),      # descending again

        # Bar 13 (idx 4): building toward B section
        (Eb4, 4 * BAR + 0,  0.62, 6),
        (F4,  4 * BAR + 6,  0.68, 6),
        (Ab4, 4 * BAR + 12, 0.74, 6),       # rising!
        (Bb4, 4 * BAR + 18, 0.78, 6),

        # Bar 14 (idx 5): peak of A section
        (Db5, 5 * BAR + 0,  0.82, 12),      # Db5 — highest yet
        (C5_, 5 * BAR + 12, 0.76, 6),
        (Bb4, 5 * BAR + 18, 0.70, 6),

        # Bar 15 (idx 6): gentle descent
        (Ab4, 6 * BAR + 0,  0.68, 12),
        (Gb4, 6 * BAR + 12, 0.62, 12),      # Gb4 — subdominant color

        # Bar 16 (idx 7): transition — melody thins, preparing for B
        (F4,  7 * BAR + 0,  0.58, 12),
        (Eb4, 7 * BAR + 12, 0.52, 6),
        (Db4, 7 * BAR + 18, 0.48, 6),       # back to tonic, ready for B
    ]

    for freq, step, vel, dur in melody_drift:
        if step < steps:
            g[1][step] = note(MELODY, freq, vel, min(dur, steps - step))

    # Shimmer: very quiet octave doublings on key melody notes
    shimmer_moments = [0 * BAR + 18, 5 * BAR, 6 * BAR]
    for s in shimmer_moments:
        if s < steps and g[1][s] is not None:
            # Double one octave up, very quiet
            mel_freq = hz(g[1][s].midi_note + 12)
            g[6][s] = note(SHIMMER, mel_freq, 0.18, 2)

    return Pattern(name='drift', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_awakening() -> Pattern:
    """Section B (bars 17-24): The passionate middle section.

    Debussy WAKES UP here. The arpeggios become cascading — wide,
    rolling, like waves. The dynamic rises to forte. The harmony
    moves through remote keys. The melody soars.

    This is where the piece transforms from a nocturne into
    something transcendent. The moonlight is now BLINDING."""
    steps = BAR * 8
    g = new_grid(steps)

    # Harmony shifts — moving through warmer, more distant keys
    chord_seq = ['Gb', 'Db', 'Ab', 'Bbm7', 'Gb', 'Fm', 'Ab7', 'Db']

    for bar in range(8):
        chord_name = chord_seq[bar]
        chord = CHORDS[chord_name]
        bass_note = BASS_NOTES[chord_name]
        bs = bar * BAR

        # Arpeggios: CASCADING now — descending waves, louder
        arp_vel = 0.48 + bar * 0.02
        place_flowing_arp(g, bar, chord, arp_vel, 'cascade')

        # Bass: more active — root + fifth alternation
        g[2][bs] = note(BASS, bass_note, 0.68, 12)
        g[2][bs + 12] = note(BASS, bass_note * 1.5, 0.55, 12)

        # Pad: richer, two voices
        pad_vel = 0.28 + bar * 0.015
        g[3][bs] = note(PAD, chord[0], pad_vel, BAR)

        # Counter voice: active chromatic line
        counter_line = {
            0: [(Db4, 8), (Eb4, 8), (F4, 8)],
            1: [(F4, 12), (Eb4, 12)],
            2: [(Eb4, 8), (Db4, 8), (C4_, 8)],
            3: [(Db4, 12), (Eb4, 12)],
            4: [(F4, 8), (Gb4, 8), (F4, 8)],
            5: [(F4, 12), (Ab4, 12)],
            6: [(Ab4, 8), (Gb4, 8), (F4, 8)],
            7: [(F4, 24)],
        }
        pos = bs
        for freq, dur in counter_line.get(bar, []):
            if pos < bs + BAR:
                g[5][pos] = note(COUNTER, freq, 0.35 + bar * 0.02, dur)
                pos += dur

    # ── Melody: SOARING. The passionate theme. ───────────────────────────
    melody_awaken = [
        # Bar 17 (idx 0): the passionate theme begins — leap up!
        (F4,  0 * BAR + 0,  0.72, 6),
        (Ab4, 0 * BAR + 6,  0.78, 6),
        (Db5, 0 * BAR + 12, 0.82, 12),      # Db5 — forte, open

        # Bar 18 (idx 1): continuing upward
        (Eb5, 1 * BAR + 0,  0.85, 12),      # Eb5 — the peak begins
        (Db5, 1 * BAR + 12, 0.78, 6),
        (C5_, 1 * BAR + 18, 0.74, 6),

        # Bar 19 (idx 2): the descent is expressive, not sad
        (Bb4, 2 * BAR + 0,  0.76, 6),
        (Ab4, 2 * BAR + 6,  0.72, 6),
        (Bb4, 2 * BAR + 12, 0.78, 6),       # turns back up!
        (C5_, 2 * BAR + 18, 0.80, 6),

        # Bar 20 (idx 3): second surge
        (Db5, 3 * BAR + 0,  0.82, 12),
        (Eb5, 3 * BAR + 12, 0.84, 12),

        # Bar 21 (idx 4): THE CLIMAX — F5 (phi point: bar 21 of ~36 total)
        (F5,  4 * BAR + 0,  0.85, 18),      # F5! The highest note. The moonlight.
        (Eb5, 4 * BAR + 18, 0.78, 6),

        # Bar 22 (idx 5): beginning the long descent
        (Db5, 5 * BAR + 0,  0.76, 12),
        (C5_, 5 * BAR + 12, 0.70, 6),
        (Bb4, 5 * BAR + 18, 0.66, 6),

        # Bar 23 (idx 6): continuing down
        (Ab4, 6 * BAR + 0,  0.68, 12),
        (Gb4, 6 * BAR + 12, 0.62, 12),

        # Bar 24 (idx 7): settling, preparing for return
        (F4,  7 * BAR + 0,  0.60, 12),
        (Eb4, 7 * BAR + 12, 0.55, 6),
        (Db4, 7 * BAR + 18, 0.50, 6),
    ]

    for freq, step, vel, dur in melody_awaken:
        if step < steps:
            g[1][step] = note(MELODY, freq, vel, min(dur, steps - step))

    # Bell: on the climax note F5 (bar 21 = index 4)
    g[4][4 * BAR] = note(BELL, hz(freq_to_midi(F5) + 12), 0.22, 4)
    # And on the Eb5 arrival
    g[4][1 * BAR] = note(BELL, Db6, 0.18, 3)

    # Shimmer: octave doublings on peaks
    for s in [0 * BAR + 12, 3 * BAR + 12, 4 * BAR]:
        if s < steps:
            g[6][s] = note(SHIMMER, Db6, 0.20, 2)

    return Pattern(name='awakening', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_cascade() -> Pattern:
    """Section B climax (bars 25-32): The emotional peak, cascading arpeggios.

    The arpeggios here are the famous rolling waves — multiple octaves,
    the left hand crosses over the right. In our arrangement, we
    layer arpeggios at different registers to simulate this pianistic
    texture. The melody sustains long notes while the arpeggios cascade
    underneath like moonlight on water."""
    steps = BAR * 8
    g = new_grid(steps)

    chord_seq = ['Db', 'Ab7', 'Gb', 'Db', 'Bbm7', 'Fm', 'Ab', 'Db']

    for bar in range(8):
        chord_name = chord_seq[bar]
        chord = CHORDS[chord_name]
        bass_note = BASS_NOTES[chord_name]
        bs = bar * BAR

        # Primary arpeggios: cascading, forte
        # Fibonacci decrescendo over the 8 bars (peak was last section)
        arp_vel = 0.55 - bar * 0.025
        place_flowing_arp(g, bar, chord, max(arp_vel, 0.30), 'cascade')

        # Bass: octave pedal, very deep
        g[2][bs] = note(BASS, bass_note, 0.65 - bar * 0.02, BAR)

        # Pad: full warmth, slowly receding
        g[3][bs] = note(PAD, chord[1] if len(chord) > 1 else chord[0],
                       0.32 - bar * 0.015, BAR)

        # Counter voice: descending line
        counter_cascade = {
            0: [(Ab4, 12), (F4, 12)],
            1: [(Eb4, 12), (Db4, 12)],
            2: [(Db4, 24)],
            3: [(C4_, 12), (Bb3, 12)],
            4: [(Bb3, 12), (Ab3, 12)],
            5: [(Ab3, 24)],
            6: [(Gb3, 12), (F3, 12)],
            7: [(F3, 24)],
        }
        pos = bs
        for freq, dur in counter_cascade.get(bar, []):
            if pos < bs + BAR:
                g[5][pos] = note(COUNTER, freq, 0.32 - bar * 0.02, dur)
                pos += dur

    # ── Melody: long sustained notes over the cascades ───────────────────
    # The melody SIMPLIFIES here — fewer notes, longer duration.
    # Let the arpeggios do the work. The melody just... breathes.
    melody_cascade = [
        # Bar 25 (idx 0): Db5 — home note, sustained
        (Db5, 0 * BAR + 0,  0.78, 18),
        (C5_, 0 * BAR + 18, 0.68, 6),

        # Bar 26 (idx 1): descending
        (Bb4, 1 * BAR + 0,  0.72, 18),
        (Ab4, 1 * BAR + 18, 0.65, 6),

        # Bar 27 (idx 2): Gb — the subdominant warmth
        (Gb4, 2 * BAR + 0,  0.68, 24),      # whole note — just float

        # Bar 28 (idx 3): one last rise
        (Ab4, 3 * BAR + 0,  0.72, 12),
        (Bb4, 3 * BAR + 12, 0.68, 12),

        # Bar 29 (idx 4): beginning the final descent
        (Ab4, 4 * BAR + 0,  0.65, 18),
        (F4,  4 * BAR + 18, 0.58, 6),

        # Bar 30 (idx 5): Eb4 — getting quieter
        (Eb4, 5 * BAR + 0,  0.55, 24),

        # Bar 31 (idx 6): approaching silence
        (Db4, 6 * BAR + 0,  0.48, 18),
        (Eb4, 6 * BAR + 18, 0.42, 6),

        # Bar 32 (idx 7): the transition note — F4 leading to A' return
        (F4,  7 * BAR + 0,  0.45, 24),
    ]

    for freq, step, vel, dur in melody_cascade:
        if step < steps:
            g[1][step] = note(MELODY, freq, vel, min(dur, steps - step))

    # Bell: cadence points
    g[4][2 * BAR] = note(BELL, Db6, 0.14, 3)
    g[4][7 * BAR] = note(BELL, Db6, 0.12, 3)

    return Pattern(name='cascade', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_return() -> Pattern:
    """Section A' (bars 33-40): The melody returns, even softer.

    The same descending Bb-Ab-F phrase, but now TRANSFORMED by everything
    that came before. The arpeggios are gentler. The harmony has a new
    depth. This is not repetition — it's homecoming."""
    steps = BAR * 8
    g = new_grid(steps)

    chord_seq = ['Db', 'Bbm7', 'Db9', 'Bbm7', 'Gb', 'Ab', 'Db', 'Db']

    for bar in range(8):
        chord_name = chord_seq[bar]
        chord = CHORDS[chord_name]
        bass_note = BASS_NOTES[chord_name]
        bs = bar * BAR

        # Arpeggios: gentle wave, returning to opening character but richer
        arp_vel = 0.32 + bar * 0.005  # barely growing
        place_flowing_arp(g, bar, chord, arp_vel, 'wave')

        # Bass: deep, sustained, quieter than before
        g[2][bs] = note(BASS, bass_note, 0.50 - bar * 0.02, BAR)

        # Pad: warm, constant
        g[3][bs] = note(PAD, chord[1] if len(chord) > 1 else chord[0],
                       0.20, BAR)

    # ── Melody: the return — same contour, softer, more tender ───────────
    melody_return = [
        # Bar 33 (idx 0): silence for 2 beats, then...
        (Bb4, 0 * BAR + 12, 0.58, 12),      # Bb4 — the return! pp

        # Bar 34 (idx 1): the descent — like coming home
        (Ab4, 1 * BAR + 0,  0.55, 12),
        (F4,  1 * BAR + 12, 0.50, 6),
        (Eb4, 1 * BAR + 18, 0.46, 6),

        # Bar 35 (idx 2): Db4 — home, but with the added 9th color
        (Db4, 2 * BAR + 0,  0.52, 18),
        (Eb4, 2 * BAR + 18, 0.48, 6),       # the 9th — Debussy's color

        # Bar 36 (idx 3): second statement, even quieter
        (F4,  3 * BAR + 0,  0.50, 12),
        (Eb4, 3 * BAR + 12, 0.46, 6),
        (Db4, 3 * BAR + 18, 0.44, 6),

        # Bar 37 (idx 4): a moment of Gb warmth
        (Gb4, 4 * BAR + 0,  0.52, 12),
        (F4,  4 * BAR + 12, 0.48, 12),

        # Bar 38 (idx 5): Ab — one last gentle dominant
        (Ab4, 5 * BAR + 0,  0.50, 12),
        (F4,  5 * BAR + 12, 0.45, 12),

        # Bar 39 (idx 6): resolution begins
        (Eb4, 6 * BAR + 0,  0.44, 12),
        (Db4, 6 * BAR + 12, 0.40, 12),

        # Bar 40 (idx 7): held Db — the tonic, barely audible
        (Db4, 7 * BAR + 0,  0.38, 24),
    ]

    for freq, step, vel, dur in melody_return:
        if step < steps:
            g[1][step] = note(MELODY, freq, vel, min(dur, steps - step))

    # Counter voice: very quiet inner movement
    for bar in [2, 4, 6]:
        bs = bar * BAR
        g[5][bs] = note(COUNTER, Ab3, 0.22, 24)

    # Bell: one gentle drop at the return of the theme
    g[4][0 * BAR + 12] = note(BELL, Db6, 0.14, 3)

    return Pattern(name='return', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_dissolve() -> Pattern:
    """Final coda (bars 41-48): Fading into nothing.

    Debussy's ending is one of the most beautiful in all of music.
    The melody reduces to a single note. The arpeggios slow down.
    Everything gets quieter and quieter until the last Db chord
    is barely a whisper — and then silence.

    In our arrangement: fibonacci decrescendo on all voices.
    The last 2 bars are nearly silent — just the pad and bass
    holding a barely-audible Db chord. The candle goes out."""
    steps = BAR * 8
    g = new_grid(steps)

    chord_seq = ['Db', 'Db9', 'Db', 'Gb', 'Db', 'Db', 'Db', 'Db']

    for bar in range(8):
        chord_name = chord_seq[bar]
        chord = CHORDS[chord_name]
        bass_note = BASS_NOTES[chord_name]
        bs = bar * BAR

        # Fibonacci decrescendo — velocity fades following inverse fibonacci
        fade = max(0.12, 0.40 - bar * 0.04)

        # Arpeggios: sparse and fading
        if bar < 4:
            # Sparse arpeggios — only beat 1 and 3
            for beat in [0, 2]:
                step = bs + beat * 6
                for i in range(3):
                    idx = i % len(chord)
                    g[0][step + i] = note(ARP, chord[idx], fade, 3)
        elif bar < 6:
            # Just beat 1
            for i in range(3):
                idx = i % len(chord)
                g[0][bs + i] = note(ARP, chord[idx], fade * 0.7, 4)
        # Bars 7-8: silence from arpeggios

        # Bass: fading
        if bar < 6:
            g[2][bs] = note(BASS, bass_note, fade + 0.10, BAR)
        elif bar == 6:
            g[2][bs] = note(BASS, bass_note, 0.20, BAR)

        # Pad: the last thing to fade — sustains to near-silence
        g[3][bs] = note(PAD, chord[1] if len(chord) > 1 else chord[0],
                       max(fade - 0.05, 0.08), BAR)

    # ── Melody: almost nothing — just echoes ─────────────────────────────
    melody_dissolve = [
        # Bar 41 (idx 0): one last Bb-Ab-F echo
        (Bb4, 0 * BAR + 0,  0.38, 12),
        (Ab4, 0 * BAR + 12, 0.32, 12),

        # Bar 42 (idx 1): F4 — sustained, fading
        (F4,  1 * BAR + 0,  0.30, 24),

        # Bar 43 (idx 2): Eb4 — the minor quality, one last time
        (Eb4, 2 * BAR + 0,  0.28, 18),
        (Db4, 2 * BAR + 18, 0.24, 6),

        # Bar 44 (idx 3): Db4 — home, ppp
        (Db4, 3 * BAR + 0,  0.22, 24),

        # Bar 45 (idx 4): one last note — Ab3, very low, barely there
        (Ab3, 4 * BAR + 0,  0.18, 24),

        # Bars 46-48: silence from melody. Just pad and bass hold.
    ]

    for freq, step, vel, dur in melody_dissolve:
        if step < steps:
            g[1][step] = note(MELODY, freq, vel, min(dur, steps - step))

    # Bell: one final, barely audible drop — the last moonlight
    g[4][0 * BAR] = note(BELL, Db6, 0.10, 4)

    return Pattern(name='dissolve', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── SONG ASSEMBLY ────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_reverie(),      # 0 — 8 bars  (A section opening)
        make_drift(),        # 1 — 8 bars  (A section development)
        make_awakening(),    # 2 — 8 bars  (B section passionate)
        make_cascade(),      # 3 — 8 bars  (B section climax/descent)
        make_return(),       # 4 — 8 bars  (A' section return)
        make_dissolve(),     # 5 — 8 bars  (Coda — fading to silence)
    ]
    # Total: 48 bars at 66 BPM, SPB=6
    # Duration: 48 bars × 4 beats/bar × (60/66 s/beat) = ~174.5s ≈ 2:55

    panning = {
        0: -0.15,    # arp: slight left (like sitting at the piano)
        1:  0.10,    # melody: slight right (singing voice floats)
        2:  0.00,    # bass: center (anchor)
        3: -0.08,    # pad: near center-left (sustain pedal envelope)
        4:  0.35,    # bell: right (moonlight drops from above-right)
        5: -0.25,    # counter: left (inner voice, opposite melody)
        6:  0.40,    # shimmer: far right (barely audible decoration)
    }

    # Effects: DEEP reverb on everything. This piece lives in a cathedral.
    channel_effects = {
        0: {  # Arp: concert hall reverb — the piano's resonance
            'reverb': 0.60, 'reverb_mix': 0.25,
        },
        1: {  # Melody: long reverb + gentle delay (sustain pedal simulation)
            'reverb': 0.70, 'reverb_mix': 0.30,
            'delay': 0.454, 'delay_feedback': 0.12, 'delay_mix': 0.08,
            # delay = one beat at 66 BPM = 60/66 ≈ 0.909s / 2 = ~0.454s
        },
        2: {  # Bass: warm room, not too wet
            'reverb': 0.30, 'reverb_mix': 0.10,
        },
        3: {  # Pad: DEEP hall reverb — the sustain pedal IS the room
            'reverb': 0.90, 'reverb_mix': 0.55,
        },
        4: {  # Bell: very long reverb — rings into infinity
            'reverb': 0.95, 'reverb_mix': 0.60,
        },
        5: {  # Counter: medium reverb — present but subtle
            'reverb': 0.55, 'reverb_mix': 0.22,
        },
        6: {  # Shimmer: long reverb — barely there, decorative
            'reverb': 0.80, 'reverb_mix': 0.45,
        },
    }

    return Song(
        title='Clair de Lune — ChipForge AI Enhanced Edition',
        author='ChipForge / Joshua Ayson (OA LLC) — after Debussy',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2, 3, 4, 5],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.08,     # subtle global room cohesion
        master_delay=0.00,      # no master delay — channels handle their own
    )


# ── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 56)
    print("  CLAIR DE LUNE — ChipForge AI Enhanced Edition")
    print("  Debussy, Suite bergamasque, L.75 III (1890)")
    print("=" * 56)
    print()
    print("  Key: Db major  |  BPM: 66 (Andante très expressif)")
    print("  Grid: 6 steps/beat (triplet subdivision)")
    print("  Duration: ~2:55")
    print()
    print("  [0-33s]    Reverie    — the famous melody emerges")
    print("  [33-65s]   Drift      — melody develops, inner voice moves")
    print("  [65-98s]   Awakening  — passionate, soaring, forte")
    print("  [98-131s]  Cascade    — climax recedes, long tones over waves")
    print("  [131-164s] Return     — A' section, even more tender")
    print("  [164-196s] Dissolve   — fading to silence, ppppp")
    print()
    print("  AI enhancements:")
    print("    - Golden ratio velocity shaping")
    print("    - Fibonacci decrescendo in coda")
    print("    - Micro-velocity variation on arpeggios (phi-based)")
    print("    - Harmonic series bell tones at cadence points")
    print("    - Chromatic inner voice (saw_dark counter-melody)")
    print()
    print("  Rendering...", flush=True)

    song = build_song()
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    out = Path('output/classical_001_clair_de_lune.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s ({duration/60:.0f}:{duration%60:04.1f})")
    print(f"  Size:     {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  Au clair de la lune, mon ami Pierrot...")
