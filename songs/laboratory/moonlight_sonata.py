"""
Moonlight Sonata — Thexder Edition
====================================
Beethoven's Piano Sonata No. 14 in C# minor, Op. 27 No. 2
First movement (Adagio sostenuto) — the iconic triplet arpeggios

Public domain (composed 1801, Beethoven died 1827).
Used as Thexder's theme music (Game Arts, 1985, PC-88/MSX).

This arrangement translates the first 24 bars into chip tune form:
  - Triplet arpeggios → pulse_arp (the Thexder DNA)
  - Melody (right hand top notes) → lead_bright
  - Bass octaves → bass_sub (deep sine, like the piano's lowest register)
  - Harmonic pad → pad_lush (sustained chords for warmth)
  - Light percussion → hat_crisp + kick_deep (very sparse, atmospheric)

Key: C# minor (enharmonic: Db minor for readability, but we use MIDI numbers)
BPM: 54 (Adagio sostenuto — this must BREATHE. Beethoven marked it.)
Time: 4/4, but the triplet arpeggios subdivide each beat into 3

Grid strategy: SPB=6 (6 steps per beat = triplet subdivision native)
  - Each step = one triplet 8th note
  - 1 bar = 4 beats × 6 steps = 24 steps
  - This lets us place triplet arpeggios naturally without hacks

The original uses G#(Ab) as the repeating triplet note — we keep that.
The melody floats above: G#4, C#5, E5 (the C#m triad, inverted).

Structure:
  [0-27s]  OPENING    6 bars — pure arpeggios + bass (the famous opening)
  [27-53s] MELODY     6 bars — top voice melody enters over arpeggios
  [53-80s] DEVELOP    6 bars — harmonic movement, modulation coloring
  [80-107s] RESOLVE   6 bars — return to C#m, final cadence, fadeout
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

# Adagio sostenuto — must be slow and breathing
BPM = 54
SPB = 6        # 6 steps per beat = TRIPLET grid (each step = triplet 8th)
BAR = 24       # 4 beats × 6 steps

# ── Helpers ───────────────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, freq: float, vel: float = 0.80, dur: int = 1) -> NoteEvent:
    midi = freq_to_midi(freq) if freq > 0 else 0
    return NoteEvent(midi_note=midi, velocity=vel, duration_steps=dur, instrument=inst)

def new_grid(channels: int, steps: int) -> list:
    return [[None] * steps for _ in range(channels)]

# ── MIDI note constants (C# minor key center) ────────────────────────────────
# Using MIDI numbers directly for precision — no enharmonic confusion

# Octave 1-2 (bass register)
Cs1 = hz(25);  Gs1 = hz(32);  B1  = hz(35)
Cs2 = hz(37);  Ds2 = hz(39);  E2  = hz(40);  Fs2 = hz(42)
Gs2 = hz(44);  A2  = hz(45);  B2  = hz(47)

# Octave 3 (low-mid)
Cs3 = hz(49);  Ds3 = hz(51);  E3  = hz(52);  Fs3 = hz(54)
Gs3 = hz(56);  A3  = hz(57);  B3  = hz(59)

# Octave 4 (mid — the arpeggio register)
Cs4 = hz(61);  D4  = hz(62);  Ds4 = hz(63);  E4  = hz(64);  Fs4 = hz(66)
Gs4 = hz(68);  A4  = hz(69);  B4  = hz(71)

# Octave 5 (melody register)
Cs5 = hz(73);  Ds5 = hz(75);  E5  = hz(76);  Fs5 = hz(78)
Gs5 = hz(80);  A5  = hz(81);  B5  = hz(83)

# Octave 6 (high color)
Cs6 = hz(85)

# ── Instrument assignments ────────────────────────────────────────────────────
ARP   = 'pulse_arp'       # triplet arpeggios (the heartbeat — Thexder DNA)
LEAD  = 'lead_bright'     # melody top voice
BASS  = 'bass_sub'        # deep sine octave bass
PAD   = 'pad_lush'        # sustained harmonic warmth
BELL  = 'gb_bell_wave'    # occasional bell accent (the "digital" touch)
KICK  = 'kick_deep'       # very sparse atmospheric pulse
HAT   = 'hat_crisp'       # whisper hi-hat (texture, not rhythm)

# ── Arpeggio pattern builder ─────────────────────────────────────────────────
# Beethoven's original: continuous triplet 8th notes, 3 notes per beat,
# always the same 3-note figure per chord: low-mid-high, low-mid-high...
# The repeated note (usually G#) is the hypnotic anchor.

def place_arp_bar(g: list, bar: int, notes_per_beat: list[tuple], vel: float = 0.48) -> None:
    """Place one bar of triplet arpeggios.
    
    notes_per_beat: list of 4 tuples, each (low, mid, high) for that beat.
    Each beat gets 6 steps: low-mid-high-low-mid-high (two full cycles).
    """
    bs = bar * BAR
    for beat_idx, (low, mid, high) in enumerate(notes_per_beat):
        beat_start = bs + beat_idx * 6
        # Two triplet cycles per beat (6 steps = 2 × 3)
        cycle = [low, mid, high]
        for i in range(6):
            s = beat_start + i
            # Slight velocity shape: accent beat 1, soften others
            v = vel
            if i == 0:
                v = vel + 0.08   # accent the downbeat of each beat
            elif i == 3:
                v = vel + 0.04   # slight accent on second cycle
            g[0][s] = note(ARP, cycle[i % 3], min(v, 0.82), 1)


# ── Chord progressions (Beethoven's actual harmony) ──────────────────────────
# Bars 1-4: C#m → C#m → C#m → C#m (tonic pedal — the famous static opening)
# Bars 5-8: C#m → B/D# → E → A (the first harmonic movement)
# Bars 9-12: F#m → C#m/G# → A → G#(→C#m)
# Bars 13-16: C#m → E → G#m → C#m (development)
# Bars 17-20: F#m → D → A → E/G#
# Bars 21-24: C#m → F#m/C# → G# → C#m (cadence)

# Arpeggio triads for each bar (low, mid, high per beat)
# The original: G#3-C#4-E4 repeating for the C#m bars
CHORDS = {
    # C#m (tonic) — the famous opening figure
    'Csm':     (Gs3, Cs4, E4),
    # C#m first inversion — slightly different voicing
    'Csm_1':   (E3,  Gs3, Cs4),
    # B major / D# bass
    'B_Ds':    (Ds3, Fs3, B3),
    # E major (relative major — the light)
    'E':       (E3,  Gs3, B3),
    # A major (subdominant — warmth)
    'A':       (A3,  Cs4, E4),
    # F#m (ii — gentle motion)
    'Fsm':     (Fs3, A3,  Cs4),
    # G# major (dominant — tension)
    'Gs':      (Gs3, B3,  Ds4),
    # D major (borrowed chord — Neapolitan hint — emotional peak)
    'D':       (Fs3, A3,  D4),
    # E/G# (dominant with bass)
    'E_Gs':    (Gs3, B3,  E4),
    # F#m/C# (ii in first inversion)
    'Fsm_Cs':  (Cs3, Fs3, A3),
}

# ── Bass note sequences (octave bass — left hand lowest notes) ────────────────
BASS_NOTES = {
    'Csm':    Cs2,  'Csm_1':  E2,   'B_Ds':   Ds2,
    'E':      E2,   'A':      A2,   'Fsm':    Fs2,
    'Gs':     Gs2,  'D':      Ds2,  'E_Gs':   Gs2,
    'Fsm_Cs': Cs2,
}

# ── Pattern definitions ──────────────────────────────────────────────────────

def make_opening() -> Pattern:
    """Bars 1-6: The famous opening. Pure triplet arpeggios over bass octaves.
    No melody — just the hypnotic C#m arpeggio pulsing in darkness.
    Bars 5-6 introduce the first chord movement (B/D# → E)."""
    steps = BAR * 6
    g = new_grid(7, steps)

    # 6 channels: 0=arp, 1=lead, 2=bass, 3=pad, 4=bell, 5=kick, 6=hat
    chord_seq = ['Csm', 'Csm', 'Csm', 'Csm', 'B_Ds', 'E']

    for bar in range(6):
        chord = chord_seq[bar]
        triad = CHORDS[chord]
        bass_note = BASS_NOTES[chord]

        # Arpeggio: same triad for all 4 beats of the bar
        vel = 0.40 + bar * 0.015  # very gradual swell
        place_arp_bar(g, bar, [triad] * 4, vel=vel)

        # Bass: whole note (sustained through bar)
        bs = bar * BAR
        g[2][bs] = note(BASS, bass_note, 0.70, BAR)

        # Pad: very soft sustained chord (enters bar 3)
        if bar >= 2:
            pad_vel = 0.18 + (bar - 2) * 0.04
            g[3][bs] = note(PAD, triad[1], pad_vel, BAR)  # mid note sustained

        # Atmospheric hat: one whisper per bar on beat 3
        if bar >= 1:
            g[6][bs + 12] = note(HAT, hz(42), 0.14, 1)

    return Pattern(name='opening', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_melody() -> Pattern:
    """Bars 7-12: The melody enters — Beethoven's iconic right-hand top voice.
    
    Original melody (simplified for chip tune clarity):
      Bar 7: G#4 ———— G#4 A4 (the first melodic breath — just two notes!)
      Bar 8: B4 ———— A4 G#4 (step down, the sigh)
      Bar 9: G#4 ———— F#4 (descent continues)
      Bar 10: E4 ———— F#4 G#4 (turn, rising hope)  
      Bar 11: A4 ———— G#4 F#4 (peak → descent)
      Bar 12: G#4 ———————— (resolve on dominant note)
    
    Beethoven's genius: the melody moves in HALF NOTES over TRIPLET 8ths.
    The melody breathes slowly while the arpeggios pulse fast underneath.
    This temporal contrast IS the Moonlight Sonata."""
    steps = BAR * 6
    g = new_grid(7, steps)

    chord_seq = ['Csm', 'A', 'Fsm', 'Csm', 'Gs', 'Csm']

    for bar in range(6):
        chord = chord_seq[bar]
        triad = CHORDS[chord]
        bass_note = BASS_NOTES[chord]
        bs = bar * BAR

        # Arpeggio continues throughout
        place_arp_bar(g, bar, [triad] * 4, vel=0.44)

        # Bass: whole notes
        g[2][bs] = note(BASS, bass_note, 0.72, BAR)

        # Pad: sustained chord tones
        g[3][bs] = note(PAD, triad[1], 0.24, BAR)

        # Hat texture
        g[6][bs + 12] = note(HAT, hz(42), 0.16, 1)

    # ── Melody: long tones floating above the arpeggios ───────────────────
    # Each melody note is a HALF note (12 steps in our grid)
    # This creates the famous "slow melody over fast arpeggios" effect
    melody_events = [
        # Bar 7 (idx 0): G#4 held, then A4 pickup
        (Gs4, 0,  0.82, 12),     # G#4 half note — the first sound
        (A4,  12, 0.74, 6),      # A4 — pickup (beat 3)
        (Gs4, 18, 0.70, 6),      # G#4 — neighbor tone (beat 4)

        # Bar 8 (idx 1): B4 peak, descend
        (B4,  24, 0.88, 12),     # B4 half note — the peak
        (A4,  36, 0.76, 6),      # A4 — stepping down
        (Gs4, 42, 0.72, 6),      # G#4 — the sigh

        # Bar 9 (idx 2): Sustained G#4, then F#4
        (Gs4, 48, 0.80, 12),     # G#4 half note
        (Fs4, 60, 0.74, 12),     # F#4 half note — descent deepens

        # Bar 10 (idx 3): E4 low point, rising
        (E4,  72, 0.78, 12),     # E4 half note — the emotional floor
        (Fs4, 84, 0.72, 6),      # F#4 — beginning to rise
        (Gs4, 90, 0.76, 6),      # G#4 — hope returns

        # Bar 11 (idx 4): A4 peak, descending
        (A4,  96,  0.86, 12),    # A4 half note — second peak
        (Gs4, 108, 0.78, 6),     # G#4 — falling
        (Fs4, 114, 0.74, 6),     # F#4 — continuing down

        # Bar 12 (idx 5): Resolution on G#4
        (Gs4, 120, 0.82, 18),    # G#4 dotted half — resolve, breathe
        (Gs4, 138, 0.68, 6),     # G#4 — echo (softer)
    ]

    for (freq, step, vel, dur) in melody_events:
        if step < steps:
            g[1][step] = note(LEAD, freq, vel, min(dur, steps - step))

    # Bell accents on key melody arrivals (the digital Thexder touch)
    bell_accents = [0, 24, 72, 96, 120]  # first note of each phrase
    for s in bell_accents:
        if s < steps:
            g[4][s] = note(BELL, Gs5, 0.22, 2)

    return Pattern(name='melody', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_develop() -> Pattern:
    """Bars 13-18: Harmonic development — modulation through related keys.
    This is where Beethoven's genius in voice leading shines.
    The arpeggios shift through F#m → D → A → E/G# (the Neapolitan hint).
    Melody rises to its highest point (Cs5, E5) then descends."""
    steps = BAR * 6
    g = new_grid(7, steps)

    chord_seq = ['Fsm', 'D', 'A', 'E_Gs', 'Csm', 'Gs']

    for bar in range(6):
        chord = chord_seq[bar]
        triad = CHORDS[chord]
        bass_note = BASS_NOTES[chord]
        bs = bar * BAR

        # Arpeggios: slightly louder — emotional intensity rising
        place_arp_bar(g, bar, [triad] * 4, vel=0.48 + bar * 0.012)

        # Bass
        g[2][bs] = note(BASS, bass_note, 0.74, BAR)

        # Pad: two chord tones for richer harmony
        g[3][bs] = note(PAD, triad[0], 0.22, BAR)
        g[3][bs + 12] = note(PAD, triad[2], 0.20, 12)

        # Hat: slightly more present
        g[6][bs + 6]  = note(HAT, hz(42), 0.12, 1)
        g[6][bs + 18] = note(HAT, hz(42), 0.14, 1)

    # ── Development melody: reaches higher, more expressive ───────────────
    dev_melody = [
        # Bar 13 (idx 0): A4 → C#5 — first leap upward
        (A4,  0,  0.82, 12),
        (Cs5, 12, 0.90, 12),     # C#5 — first time this high (emotional!)

        # Bar 14 (idx 1): D5 — the Neapolitan color (borrowed from D major)
        (Ds4, 24, 0.76, 6),      # D#4 — chromatic approach
        (E4,  30, 0.72, 6),
        (Fs4, 36, 0.78, 6),
        (A4,  42, 0.84, 6),      # rising through the D major arpeggio

        # Bar 15 (idx 2): E5 — the highest point (the emotional peak)
        (Cs5, 48, 0.86, 6),
        (E5,  54, 0.95, 12),     # E5 — THE PEAK. Maximum emotion.
        (Ds5, 66, 0.82, 6),      # D#5 — beginning the descent

        # Bar 16 (idx 3): Descent through B4 → G#4
        (Cs5, 72, 0.84, 6),
        (B4,  78, 0.80, 6),
        (Gs4, 84, 0.78, 12),     # G#4 — returning home
        (Fs4, 96, 0.72, 6),      # overlap into bar 17 area... no, 84+12=96

        # Bar 17 (idx 4): E4 → G#4 — gentle rise and fall
        (E4,  96,  0.76, 12),    # correction: Fs4 was at 96, let me fix overlap
        (Gs4, 108, 0.80, 12),

        # Bar 18 (idx 5): G#4 sustained → resolution tone
        (Gs4, 120, 0.84, 12),
        (Fs4, 132, 0.72, 6),
        (Gs4, 138, 0.78, 6),     # back to dominant
    ]

    for (freq, step, vel, dur) in dev_melody:
        if step < steps:
            g[1][step] = note(LEAD, freq, vel, min(dur, steps - step))

    # Bell accents on emotional peaks
    for s in [12, 54, 120]:
        if s < steps:
            g[4][s] = note(BELL, Cs6, 0.18, 2)

    # Kick: one deep pulse every 2 bars (the heartbeat in darkness)
    for bar in [1, 3, 5]:
        g[5][bar * BAR] = note(KICK, hz(36), 0.30, 1)

    return Pattern(name='develop', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_resolve() -> Pattern:
    """Bars 19-24: Return to C#m. The final cadence.
    Arpeggios gradually soften (morendo — dying away).
    Melody descends to its lowest register.
    Last bar: held C#m chord fading into silence — the Thexder game starts."""
    steps = BAR * 6
    g = new_grid(7, steps)

    chord_seq = ['Csm', 'Fsm_Cs', 'Gs', 'Csm', 'Csm', 'Csm']

    for bar in range(6):
        chord = chord_seq[bar]
        triad = CHORDS[chord]
        bass_note = BASS_NOTES[chord]
        bs = bar * BAR

        # Arpeggios: DECRESCENDO — fading from 0.48 → 0.28
        vel = 0.48 - bar * 0.035
        place_arp_bar(g, bar, [triad] * 4, vel=max(vel, 0.22))

        # Bass: long sustained, getting softer
        bass_vel = 0.72 - bar * 0.06
        g[2][bs] = note(BASS, bass_note, max(bass_vel, 0.36), BAR)

        # Pad: only first 3 bars, then silence (morendo)
        if bar < 3:
            pad_vel = 0.22 - bar * 0.04
            g[3][bs] = note(PAD, triad[1], max(pad_vel, 0.10), BAR)

    # ── Resolution melody: descends, simplifies, fades ────────────────────
    resolve_melody = [
        # Bar 19 (idx 0): G#4 — home, gentle
        (Gs4, 0,  0.78, 18),     # G#4 dotted half — settling
        (A4,  18, 0.62, 6),      # A4 — one last neighbor tone

        # Bar 20 (idx 1): F#4 → E4 — sinking lower
        (Fs4, 24, 0.72, 12),
        (E4,  36, 0.68, 12),     # E4 — the minor 3rd, deep sadness

        # Bar 21 (idx 2): G#4 → pause (the breath before the end)
        (Gs4, 48, 0.76, 12),     # G#4 — dominant, expectation
        # Steps 60-71: silence (the pause — Beethoven's famous fermata feel)

        # Bar 22 (idx 3): C#4 → E4 — the final C#m statement
        (Cs4, 72, 0.70, 12),     # C#4 — root, low, intimate
        (E4,  84, 0.64, 12),     # E4 — minor third (C#m identity)

        # Bar 23 (idx 4): G#4 — one last dominant note
        (Gs4, 96, 0.60, 18),     # G#4 — pppp, barely there
        # silence for last 6 steps

        # Bar 24 (idx 5): final C#4 — ppppp, the candle goes out
        (Cs4, 120, 0.48, 24),    # C#4 whole note — the last sound
    ]

    for (freq, step, vel, dur) in resolve_melody:
        if step < steps:
            g[1][step] = note(LEAD, freq, vel, min(dur, steps - step))

    # Bell: one final ring on the last C#4
    g[4][120] = note(BELL, Cs5, 0.16, 3)

    return Pattern(name='resolve', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── ASSEMBLE SONG ─────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_opening(),    # idx 0 — 6 bars ~26.7s
        make_melody(),     # idx 1 — 6 bars ~26.7s
        make_develop(),    # idx 2 — 6 bars ~26.7s
        make_resolve(),    # idx 3 — 6 bars ~26.7s
    ]
    # Total: 24 bars ≈ 106.7 seconds at 54 BPM

    panning = {
        0: -0.20,    # arp: slight left (like sitting at the piano — treble left)
        1:  0.10,    # lead: slight right (melody floats above)
        2:  0.00,    # bass: center (anchors everything)
        3: -0.05,    # pad: near center, slight left
        4:  0.35,    # bell: right (digital accent — the AI touch)
        5:  0.00,    # kick: center
        6:  0.25,    # hat: right (texture)
    }

    channel_effects = {
        # Arpeggio: subtle room reverb (like a concert hall)
        0: {'reverb': 0.50, 'reverb_mix': 0.18},

        # Lead melody: longer reverb + tiny delay (sustain pedal simulation)
        1: {'reverb': 0.65, 'reverb_mix': 0.25,
            'delay': 0.222, 'delay_feedback': 0.15, 'delay_mix': 0.10},

        # Bass: dry, centered
        2: {'reverb': 0.20, 'reverb_mix': 0.06},

        # Pad: deep reverb (the warmth)
        3: {'reverb': 0.85, 'reverb_mix': 0.45},

        # Bell: long reverb tail (rings out)
        4: {'reverb': 0.90, 'reverb_mix': 0.55},
    }

    return Song(
        title='Moonlight Sonata — Thexder Edition',
        author='ChipForge / Joshua Ayson (OA LLC) — after Beethoven',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2, 3],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.06,
        master_delay=0.00,
    )

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("═" * 56)
    print("  MOONLIGHT SONATA — Thexder Edition")
    print("  Beethoven, Op. 27 No. 2 (1801) → ChipForge (2026)")
    print("═" * 56)
    print()
    print("  Key: C# minor  |  BPM: 54 (Adagio sostenuto)")
    print("  Grid: 6 steps/beat (native triplet subdivision)")
    print()
    print("  [0-27s]   Opening  — triplet arpeggios in darkness")
    print("  [27-53s]  Melody   — the famous top voice enters")
    print("  [53-80s]  Develop  — harmonic journey, E5 peak")
    print("  [80-107s] Resolve  — morendo, candle fades")
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

    out = Path('output/moonlight_sonata.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s")
    print(f"  Size:     {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  Adagio sostenuto. Per Beethoven. Per Thexder.")
