"""
Final Boss — Intense Boss Battle Theme
=======================================

Heart-pounding chip tune battle music. The player is fighting for their life.

Key: B Phrygian Dominant (B-C-D#-E-F#-G-A)
  - The b2 (C natural) gives dread/darkness
  - The #3 (D#) gives that "evil villain" major-over-minor tension
  - Tritone B-F is the core tension interval

BPM: 155 (relentless, aggressive)

MATHEMATICAL TECHNIQUES:
  1. Euclidean E(5,16) for secondary percussion accents
  2. 3-against-4 polyrhythm on kick/snare for chaos
  3. Diminished arpeggio patterns (B-D-F tritone stack)
  4. Octave-pumping bass (aggressive 8th-note root-octave alternation)

7 channels:
  0 - Kick        (kick_deep)   — four-on-floor + ghost notes + 3-against-4 layer
  1 - Snare       (noise_clap)  — beats 2&4, 16th-note fill rolls every 4th bar
  2 - Hats        (hat_crisp)   — relentless 16th stream
  3 - Bass        (bass_growl)  — AGGRESSIVE octave pumping
  4 - Lead        (lead_bright) — wide leaps, tritones, rapid runs
  5 - Pad         (pad_lush)    — ominous diminished chord sustain
  6 - Arp/Counter (pulse_arp + saw_dark) — frantic diminished arpeggios + counter melody

Structure (~18 seconds at 155 BPM):
  [0-3s]   INTRO   2 bars  — ominous bass + arp, building dread
  [3-18s]  BATTLE  12 bars — full intensity, no letup, fighting for your life
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 155
SPB = 4
BAR = 16

# ── Helpers ──────────────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, freq: float, vel: float = 0.80, dur: int = 2) -> NoteEvent:
    """Create NoteEvent. Velocity capped at 0.85, melodic dur defaults to 2."""
    return NoteEvent(midi_note=freq_to_midi(freq), velocity=min(vel, 0.85),
                     duration_steps=dur, instrument=inst)

def new_grid(channels: int, steps: int) -> list:
    return [[None] * steps for _ in range(channels)]


# ── Euclidean Rhythm ─────────────────────────────────────────────────────────

def euclidean_rhythm(pulses: int, steps: int) -> list[bool]:
    """Bjorklund's algorithm: distribute pulses evenly across steps."""
    if pulses >= steps:
        return [True] * steps
    if pulses == 0:
        return [False] * steps

    groups: list[list[bool]] = [[True] for _ in range(pulses)]
    remainder: list[list[bool]] = [[False] for _ in range(steps - pulses)]

    while len(remainder) > 1:
        new_groups = []
        while groups and remainder:
            g = groups.pop(0)
            r = remainder.pop(0)
            new_groups.append(g + r)
        if groups:
            remainder = groups
        new_groups.extend(remainder)
        groups = new_groups
        remainder = []
        if len(groups) <= 1:
            break
        first_len = len(groups[0])
        split_idx = len(groups)
        for i in range(1, len(groups)):
            if len(groups[i]) != first_len:
                split_idx = i
                break
        if split_idx < len(groups):
            remainder = groups[split_idx:]
            groups = groups[:split_idx]

    result = []
    for g in groups:
        result.extend(g)
    for r in remainder:
        result.extend(r)
    return result[:steps]


# ── Instrument assignments ───────────────────────────────────────────────────
KICK    = 'kick_deep'
SNARE   = 'noise_clap'
HAT     = 'hat_crisp'
TOM     = 'tom_high'
BASS    = 'bass_growl'
LEAD    = 'lead_bright'
PAD     = 'pad_lush'
ARP     = 'pulse_arp'
COUNTER = 'saw_dark'

# ── B Phrygian Dominant note pool ────────────────────────────────────────────
# Scale: B-C-D#-E-F#-G-A  (1-b2-3-4-5-b6-b7)
# The b2 (C) and #3 (D#) create the "evil boss" sound
# Tritone: B-F (the core tension)
# Diminished arp: B-D-F (tritone stack)

# Sub/bass register
B1  = hz(35);  C2  = hz(36);  Ds2 = hz(39);  E2  = hz(40)
Fs2 = hz(42);  G2  = hz(43);  A2  = hz(45);  B2  = hz(47)

# Low register
C3  = hz(48);  Ds3 = hz(51);  E3  = hz(52);  F3  = hz(53)
Fs3 = hz(54);  G3  = hz(55);  A3  = hz(57);  B3  = hz(59)

# Mid register
C4  = hz(60);  D4  = hz(62);  Ds4 = hz(63);  E4  = hz(64)
F4  = hz(65);  Fs4 = hz(66);  G4  = hz(67);  A4  = hz(69)
B4  = hz(71)

# Upper register
C5  = hz(72);  Ds5 = hz(75);  E5  = hz(76);  F5  = hz(77)
Fs5 = hz(78);  G5  = hz(79);  A5  = hz(81);  B5  = hz(83)


# ── Percussion helpers ───────────────────────────────────────────────────────

def kick(vel: float = 0.85) -> NoteEvent:
    return note(KICK, hz(36), vel, 1)

def snare(vel: float = 0.80) -> NoteEvent:
    return note(SNARE, hz(40), vel, 3)

def hat(vel: float = 0.50) -> NoteEvent:
    return note(HAT, hz(42), vel, 2)

def tom(vel: float = 0.70) -> NoteEvent:
    return note(TOM, hz(48), vel, 2)


# ── PATTERN: INTRO (2 bars) ─────────────────────────────────────────────────

def make_intro() -> Pattern:
    """2 bars: Ominous bass octave pump + frantic diminished arp.
    Building dread before all hell breaks loose."""
    steps = BAR * 2
    g = new_grid(7, steps)

    # E(5,16) accent pattern for secondary percussion
    e5_pattern = euclidean_rhythm(5, BAR)

    for bar in range(2):
        bs = bar * BAR

        # Sparse hats: E(5,16) pattern only — eerie, not driving yet
        for i, hit in enumerate(e5_pattern):
            if hit:
                g[2][bs + i] = hat(0.30 + bar * 0.08)

        # Bass: octave pumping begins (8th notes = every 2 steps)
        # Root-octave-root-octave... the heartbeat of dread
        for s in range(0, BAR, 2):
            if s % 4 == 0:
                g[3][bs + s] = note(BASS, B1, 0.75 + bar * 0.05, 2)  # root
            else:
                g[3][bs + s] = note(BASS, B2, 0.65 + bar * 0.05, 2)  # octave up

        # Arp: diminished triad B-D-F (tritone stack) — frantic 16ths
        dim_arp = [B3, D4, F4, B4, F4, D4, B3, F3,
                   B3, F4, D4, B4, D4, F4, B3, D4]
        arp_vel = 0.35 + bar * 0.12  # crescendo across intro
        for s in range(BAR):
            g[6][bs + s] = note(ARP, dim_arp[s % len(dim_arp)], arp_vel, 2)

        # Pad: ominous diminished chord, whole bar sustain
        # B-D-F diminished triad spread across the register
        g[5][bs] = note(PAD, B3, 0.40 + bar * 0.08, BAR)

    # Bar 2: single menacing kick on beat 1 to signal the storm
    g[0][BAR] = kick(0.80)
    g[0][BAR + 8] = kick(0.70)

    return Pattern(name='intro', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── PATTERN: BATTLE (12 bars) ───────────────────────────────────────────────

def make_battle() -> Pattern:
    """12 bars: FULL INTENSITY. No letup. The player is fighting for their life.

    Kick: four-on-floor + ghost notes on "and" of beats + 3-against-4 layer
    Snare: beats 2&4, 16th-note crescendo fills every 4th bar
    Hats: relentless 16th stream
    Bass: aggressive octave pumping (8th notes)
    Lead: wide leaps (minor 6ths, tritones), rapid runs
    Pad: sustained diminished warmth floor
    Arp/Counter: frantic diminished arps + menacing counter-melody
    """
    steps = BAR * 12
    g = new_grid(7, steps)

    # E(5,16) for secondary percussion accents (tom hits)
    e5_pattern = euclidean_rhythm(5, BAR)
    # E(3,16) for 3-against-4 polyrhythm layer
    e3_pattern = euclidean_rhythm(3, BAR)

    # ── LEAD MELODY ──────────────────────────────────────────────────────────
    # Aggressive, wide-leaping phrases in B Phrygian Dominant
    # Uses tritones (B-F), minor 6ths (B-G), rapid scalar runs
    # 4-bar phrases that repeat with variation

    # Phrase A (bars 0-3): Ascending menace — tritone leaps + scalar burst
    lead_phrase_a = [
        # bar 0: Opening threat — tritone leap up, minor 6th down
        (0,  B4,  0.82, 3),   # B4 — statement
        (3,  F5,  0.85, 3),   # F5 — tritone leap UP (evil interval)
        (6,  G4,  0.78, 2),   # G4 — minor 6th leap DOWN (dramatic)
        (8,  Ds5, 0.83, 4),   # D#5 — the major 3rd (villain's theme note)
        (12, C5,  0.80, 2),   # C5 — b2 (Phrygian darkness)
        (14, B4,  0.75, 2),   # B4 — resolve to root

        # bar 1: Rapid descending run — 16th note flurry
        (16, B5,  0.85, 2),   # B5 — high octave strike
        (18, A5,  0.78, 2),   # A5 — b7 descending
        (20, G5,  0.80, 2),   # G5 — b6
        (22, Fs5, 0.75, 2),   # F#5 — 5
        (24, E5,  0.82, 3),   # E5 — 4 (landing note, longer)
        (27, Ds5, 0.85, 3),   # D#5 — #3 (the evil note)
        (30, C5,  0.78, 2),   # C5 — b2 (Phrygian bite)

        # bar 2: Tritone oscillation — frantic back and forth
        (32, B4,  0.80, 2),   # B-F-B-F rapid oscillation
        (34, F5,  0.83, 2),
        (36, B4,  0.78, 2),
        (38, F5,  0.85, 2),
        (40, Ds5, 0.82, 4),   # D#5 — break the oscillation, villain laughs
        (44, C5,  0.80, 2),   # C — Phrygian dread
        (46, B4,  0.75, 2),

        # bar 3: Ascending climax run
        (48, B4,  0.78, 2),
        (50, C5,  0.80, 2),   # b2
        (52, Ds5, 0.82, 2),   # #3
        (54, E5,  0.80, 2),   # 4
        (56, Fs5, 0.83, 2),   # 5
        (58, G5,  0.80, 2),   # b6
        (60, A5,  0.82, 2),   # b7
        (62, B5,  0.85, 2),   # octave — peak!
    ]

    # Phrase B (bars 4-7): Response phrase — more rhythmic, syncopated
    lead_phrase_b = [
        # bar 4: Syncopated stabs
        (0,  Ds5, 0.85, 3),   # D#5 — villain theme
        (4,  B4,  0.78, 2),   # drop to root
        (6,  F5,  0.83, 2),   # tritone again
        (8,  None, 0, 0),     # REST — the silence is terrifying
        (10, G5,  0.85, 3),   # G5 — b6, high drama
        (13, Fs5, 0.80, 3),   # F#5 — resolve down

        # bar 5: Call and response with counter-melody
        (16, B5,  0.85, 4),   # B5 — sustained high scream
        (20, A5,  0.78, 2),   # step down
        (22, G5,  0.80, 2),   # continuing down
        (24, F5,  0.85, 4),   # F5 — tritone landing, evil grin
        (28, E5,  0.78, 2),
        (30, Ds5, 0.82, 2),   # #3

        # bar 6: Mirror of bar 2 but higher
        (32, Ds5, 0.80, 2),
        (34, A5,  0.83, 2),   # tritone from D# (A-D# = tritone)
        (36, Ds5, 0.78, 2),
        (38, A5,  0.85, 2),
        (40, B5,  0.85, 4),   # B5 — climax hold
        (44, G5,  0.80, 2),
        (46, Fs5, 0.78, 2),

        # bar 7: Descending doom — final phrase resolution
        (48, B5,  0.85, 2),   # high B
        (50, A5,  0.82, 2),   # step down
        (52, Fs5, 0.80, 2),
        (54, Ds5, 0.83, 2),   # #3
        (56, C5,  0.85, 4),   # C — Phrygian darkness, sustained
        (60, B4,  0.78, 4),   # resolve to root, held
    ]

    # Place phrase A (bars 0-3), phrase B (bars 4-7), phrase A variant (bars 8-11)
    for (step_offset, freq, vel, dur) in lead_phrase_a:
        if freq is not None:
            g[4][step_offset] = note(LEAD, freq, vel, dur)

    for (rel_step, freq, vel, dur) in lead_phrase_b:
        abs_step = 4 * BAR + rel_step
        if freq is not None and dur > 0:
            g[4][abs_step] = note(LEAD, freq, vel, dur)

    # Phrase A variant for bars 8-11: same shape, higher intensity
    for (step_offset, freq, vel, dur) in lead_phrase_a:
        abs_step = 8 * BAR + step_offset
        if freq is not None and abs_step < steps:
            # Shift some notes up for climax feel
            boosted_freq = freq
            if step_offset >= 48:  # last bar of phrase — push higher
                boosted_freq = freq * 2 if freq_to_midi(freq) < 78 else freq
            g[4][abs_step] = note(LEAD, boosted_freq, min(vel + 0.03, 0.85), dur)

    # ── COUNTER-MELODY (channel 6, bars 4-11) ────────────────────────────────
    # saw_dark, menacing, a tritone away from the lead
    counter_phrases = [
        # bars 4-5: tritone shadow of the lead
        (4 * BAR + 0,  F4,  0.65, 4),
        (4 * BAR + 4,  E4,  0.60, 4),
        (4 * BAR + 8,  C4,  0.65, 4),
        (4 * BAR + 12, Ds4, 0.62, 4),
        (5 * BAR + 0,  F4,  0.68, 4),
        (5 * BAR + 4,  Ds4, 0.62, 4),
        (5 * BAR + 8,  C4,  0.65, 4),
        (5 * BAR + 12, B3,  0.60, 4),
        # bars 6-7: climbing menace
        (6 * BAR + 0,  B3,  0.65, 3),
        (6 * BAR + 3,  C4,  0.68, 3),
        (6 * BAR + 6,  Ds4, 0.70, 3),
        (6 * BAR + 9,  F4,  0.72, 3),
        (6 * BAR + 12, G4,  0.70, 4),
        (7 * BAR + 0,  F4,  0.68, 4),
        (7 * BAR + 4,  Ds4, 0.65, 4),
        (7 * BAR + 8,  C4,  0.62, 4),
        (7 * BAR + 12, B3,  0.60, 4),
        # bars 8-11: intensified shadow
        (8 * BAR + 0,  F4,  0.72, 3),
        (8 * BAR + 3,  G4,  0.70, 3),
        (8 * BAR + 6,  A4,  0.72, 2),
        (8 * BAR + 8,  F4,  0.68, 4),
        (8 * BAR + 12, Ds4, 0.70, 4),
        (9 * BAR + 0,  C4,  0.72, 4),
        (9 * BAR + 4,  Ds4, 0.68, 4),
        (9 * BAR + 8,  F4,  0.72, 4),
        (9 * BAR + 12, G4,  0.70, 4),
        (10 * BAR + 0,  A4,  0.72, 3),
        (10 * BAR + 3,  G4,  0.68, 3),
        (10 * BAR + 6,  F4,  0.72, 2),
        (10 * BAR + 8,  Ds4, 0.70, 4),
        (10 * BAR + 12, C4,  0.68, 4),
        (11 * BAR + 0,  B3,  0.70, 4),
        (11 * BAR + 4,  Ds4, 0.72, 4),
        (11 * BAR + 8,  F4,  0.75, 4),
        (11 * BAR + 12, B4,  0.72, 4),
    ]
    for (step, freq, vel, dur) in counter_phrases:
        if step < steps and g[6][step] is None:
            g[6][step] = note(COUNTER, freq, vel, dur)

    # ── DRUMS + BASS + ARP (per bar) ─────────────────────────────────────────
    for bar in range(12):
        bs = bar * BAR

        # ── KICK: four-on-floor + ghost notes + 3-against-4 polyrhythm ──────
        # Main four-on-floor
        g[0][bs]      = kick(0.85)
        g[0][bs + 4]  = kick(0.83)
        g[0][bs + 8]  = kick(0.85)
        g[0][bs + 12] = kick(0.83)

        # Ghost kicks on the "and" of beats (steps 2, 6, 10, 14)
        g[0][bs + 2]  = kick(0.40)
        g[0][bs + 6]  = kick(0.38)
        g[0][bs + 10] = kick(0.42)
        g[0][bs + 14] = kick(0.40)

        # 3-against-4 polyrhythm: E(3,16) layer — additional accents
        for i, hit in enumerate(e3_pattern):
            if hit and g[0][bs + i] is None:
                g[0][bs + i] = note(KICK, hz(36), 0.35, 1)

        # ── SNARE: beats 2 & 4, fills every 4th bar ─────────────────────────
        g[1][bs + 4]  = snare(0.82)
        g[1][bs + 12] = snare(0.82)

        # 16th-note crescendo fill every 4th bar (bars 3, 7, 11)
        if bar % 4 == 3:
            for s in range(12, 16):
                fill_vel = 0.45 + (s - 12) * 0.10  # 0.45 → 0.75 crescendo
                g[1][bs + s] = snare(fill_vel)

        # E(5,16) tom accents for extra chaos
        for i, hit in enumerate(e5_pattern):
            if hit and g[1][bs + i] is None:
                # Only place toms where snare isn't — sparse accents
                if i not in (4, 12):
                    g[1][bs + i] = tom(0.40 + (bar / 12) * 0.15)

        # ── HATS: relentless 16th stream ─────────────────────────────────────
        for s in range(BAR):
            if s % 4 == 0:
                g[2][bs + s] = hat(0.60)  # downbeat accent
            elif s % 2 == 0:
                g[2][bs + s] = hat(0.48)  # 8th note
            else:
                g[2][bs + s] = hat(0.32)  # ghost 16th

        # ── BASS: aggressive octave pumping ──────────────────────────────────
        # 8th notes alternating root (B1) and octave (B2)
        # With Phrygian chromatic passing tones on phrase transitions
        for s in range(0, BAR, 2):
            if bar % 4 == 3 and s >= 12:
                # Chromatic run-up in last beat of every 4th bar: B-C-D#-E
                chromatic = [B1, C2, Ds2, E2]
                idx = (s - 12) // 2
                if idx < len(chromatic):
                    g[3][bs + s] = note(BASS, chromatic[idx], 0.82, 2)
            elif s % 4 == 0:
                g[3][bs + s] = note(BASS, B1, 0.82, 2)   # root LOW
            else:
                g[3][bs + s] = note(BASS, B2, 0.72, 2)   # octave UP

        # ── PAD: sustained diminished chord (warmth floor) ───────────────────
        # B diminished: B-D-F — the tritone tension sustained underneath
        g[5][bs] = note(PAD, B3, 0.35, BAR)

        # ── ARP: frantic diminished arpeggios (where counter-melody isn't) ───
        # B-D-F diminished triad, cycling through inversions
        dim_notes = [B3, D4, F4, B4, F4, D4, B3, F3,
                     D4, F4, B4, D4, F3, B3, D4, F4]
        for s in range(BAR):
            step = bs + s
            if g[6][step] is None:  # don't overwrite counter-melody
                g[6][step] = note(ARP, dim_notes[s % len(dim_notes)],
                                  0.45 + (s % 4 == 0) * 0.10, 2)

    return Pattern(name='battle', num_steps=steps, num_channels=7,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── SONG ASSEMBLY ────────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_intro(),    # 0 — 2 bars  ~3.1s
        make_battle(),   # 1 — 12 bars ~18.6s
    ]

    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # snare: near center
        2:  0.28,    # hats: right (standard kit position)
        3: -0.08,    # bass: just left of center
        4:  0.12,    # lead: slight right (sits in front)
        5: -0.20,    # pad: left (warmth floor)
        6: -0.30,    # arp/counter: left (opposite hats)
    }

    channel_effects = {
        0: {'reverb': 0.08},                                         # kick: subtle room
        1: {'reverb': 0.15},                                         # snare: medium room
        2: {'delay': 0.18, 'delay_feedback': 0.25, 'reverb': 0.10}, # hats: rhythmic space
        3: {'reverb': 0.08},                                         # bass: tight low-end
        4: {'reverb': 0.28, 'delay': 0.20, 'delay_feedback': 0.30}, # lead: rich + slapback
        5: {'reverb': 0.40},                                         # pad: deep hall
        6: {'delay': 0.22, 'delay_feedback': 0.35, 'reverb': 0.10}, # arp: rhythmic echo
    }

    return Song(
        title='Final Boss',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.08,
        master_delay=0.0,
    )


# ── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("╔════════════════════════════════════════════════════╗")
    print("║  FINAL BOSS — Intense Battle Theme                 ║")
    print("║  Key: B Phrygian Dominant  |  BPM: 155             ║")
    print("╚════════════════════════════════════════════════════╝")
    print()
    print("  Channels:")
    print("    0  Kick        (kick_deep)    — four-on-floor + 3-against-4")
    print("    1  Snare/Tom   (noise_clap)   — backbeat + fills + E(5,16)")
    print("    2  Hats        (hat_crisp)    — relentless 16ths")
    print("    3  Bass        (bass_growl)   — octave pumping aggression")
    print("    4  Lead        (lead_bright)  — tritones, wide leaps, runs")
    print("    5  Pad         (pad_lush)     — diminished chord warmth")
    print("    6  Arp/Counter (pulse_arp)    — diminished arps + saw_dark")
    print()
    print("  [0-3s]   INTRO  — ominous bass + arp, building dread")
    print("  [3-18s]  BATTLE — full intensity, fighting for your life")
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

    out = Path('output/soundtrack_001_final_boss.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  The boss awaits. Fight for your life.")
