#!/usr/bin/env python3
"""
ChipForge — "Neural Cascade"
=============================
A 60-second bleeding-edge AI composition with viral beat drop.

Structure:
  Intro → Build → DROP 1 ×2 → Breakdown → Build 2 → DROP 2 ×2 → Outro

Key: D minor | BPM: 146 | Duration: ~59s | Channels: 7

Bleeding-edge elements:
  - Polyrhythmic hi-hats (3-against-4 accent pattern)
  - Genre shift between drops (four-on-floor → deconstructed breakbeat)
  - Strategic silence ("the gap") before each drop for maximum impact
  - Hand-crafted call-and-response hook with ascending peak variation
  - Chromatic riser builds for escalating tension
  - AI-generated counter-melody weaving around the hook in drop 2
  - Glitch percussion (probabilistic hat omission)
  - Octave-bounce bass with genre-adaptive density
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.dirname(__file__))

from src.instruments import PRESETS
from src.theory import (
    note_name_to_midi, generate_phrase_melody, generate_arpeggio,
    humanize_velocities, get_drum_groove,
)
from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

BPM = 146
STEPS = 64          # 4 bars per pattern (16 steps/bar × 4 bars)
NUM_CH = 7          # 0:kick 1:snare 2:hat 3:bass 4:lead 5:chord 6:arp
RNG = random.Random(42)


def n(name: str, octave: int = 4) -> int:
    """Shorthand: note name → MIDI number."""
    return note_name_to_midi(name, octave)


# Chord progression: Dm → Bb → C → Dm  (i → bVI → bVII → i)
CHORDS = [
    [n("D", 4), n("F", 4), n("A", 4)],
    [n("Bb", 3), n("D", 4), n("F", 4)],
    [n("C", 4), n("E", 4), n("G", 4)],
    [n("D", 4), n("F", 4), n("A", 4)],
]

# Chord roots for bass (one per bar)
BASS_ROOTS = [n("D", 2), n("Bb", 2), n("C", 2), n("D", 2)]

# ── THE HOOK ─────────────────────────────────────────────────────────────
# Hand-crafted for catchiness. Arch contour, call-and-response,
# ascending peak with Bb tension, resolves to root.
# Format: (step, note_name, octave, velocity)

HOOK_CALL = [
    # Bar 1: ascending run D→F→G→A
    (0, "D", 5, 0.85), (3, "F", 5, 0.75), (5, "G", 5, 0.80), (7, "A", 5, 0.90),
    # Bar 2: descending response A→G→F, land on D
    (10, "A", 5, 0.72), (12, "G", 5, 0.78), (14, "F", 5, 0.70),
    # Bar 2 second half: repeat ascending with Bb peak
    (16, "D", 5, 0.85), (19, "F", 5, 0.75), (21, "G", 5, 0.80), (23, "A", 5, 0.90),
    # Tension: Bb instead of A at peak, resolve to D
    (26, "Bb", 5, 0.88), (28, "A", 5, 0.75), (31, "D", 5, 0.80),
]

HOOK_RESPONSE = [
    # Bar 3: accelerated version (notes every 2 steps)
    (32, "D", 5, 0.82), (34, "F", 5, 0.73), (36, "G", 5, 0.78), (38, "A", 5, 0.88),
    (42, "A", 5, 0.70), (44, "G", 5, 0.76), (46, "F", 5, 0.68),
    # Bar 4: climax — goes up to C6! then resolves
    (48, "D", 5, 0.85), (50, "F", 5, 0.75), (52, "G", 5, 0.80), (54, "Bb", 5, 0.92),
    (57, "C", 6, 0.95), (59, "Bb", 5, 0.85), (61, "A", 5, 0.78), (63, "D", 5, 0.82),
]


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def new_grid() -> dict[int, dict[int, NoteEvent]]:
    """Empty sparse grid (dict of dicts)."""
    return {ch: {} for ch in range(NUM_CH)}


def to_list_grid(grid: dict, channels: int = NUM_CH, steps: int = STEPS):
    """Convert sparse dict-grid to list-of-lists for Pattern."""
    result: list[list[NoteEvent | None]] = []
    for ch in range(channels):
        row: list[NoteEvent | None] = [None] * steps
        for step, event in grid.get(ch, {}).items():
            if 0 <= step < steps:
                row[step] = event
        result.append(row)
    return result


def place_melody(grid: dict, channel: int, notes: list[tuple], instrument: str):
    """Place a list of (step, name, octave, velocity) into a grid channel."""
    for step, name, octave, vel in notes:
        grid[channel][step] = NoteEvent(
            midi_note=n(name, octave), velocity=vel, instrument=instrument,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 0: Intro / Outro — sparse, atmospheric, mysterious
# ═══════════════════════════════════════════════════════════════════════════

def build_intro() -> Pattern:
    grid = new_grid()

    # Arp: quarter-note chord tones, gentle pluck
    for bar in range(4):
        chord = CHORDS[bar]
        for beat in range(4):
            step = bar * 16 + beat * 4
            note = chord[beat % len(chord)]
            grid[6][step] = NoteEvent(
                midi_note=note, velocity=0.42, instrument="pluck_short",
            )

    # Sparse hat: soft shimmer every 8 steps
    for i in range(0, STEPS, 8):
        grid[2][i] = NoteEvent(
            midi_note=n("F#", 5), velocity=0.25, instrument="hat_open_shimmer",
        )

    # Melody tease: just the first 4 notes of the hook (bars 1 and 3)
    tease = HOOK_CALL[:4]
    for step, name, octave, vel in tease:
        grid[4][step] = NoteEvent(
            midi_note=n(name, octave), velocity=vel * 0.55,
            instrument="pluck_short",
        )
    for step, name, octave, vel in tease:
        grid[4][step + 32] = NoteEvent(
            midi_note=n(name, octave), velocity=vel * 0.48,
            instrument="pluck_short",
        )

    # Pad: sustained Dm — full pattern
    grid[5][0] = NoteEvent(
        midi_note=n("D", 4), velocity=0.28, instrument="pad_lush",
        duration_steps=64,
    )

    return Pattern(
        name="intro", bpm=BPM, num_steps=STEPS, num_channels=NUM_CH,
        grid=to_list_grid(grid),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 1: Build — snare roll, chromatic riser, THE GAP
# ═══════════════════════════════════════════════════════════════════════════

def build_build() -> Pattern:
    grid = new_grid()

    # Kick: half-time (every 8 steps), stop before gap
    for i in range(0, 56, 8):
        grid[0][i] = NoteEvent(
            midi_note=n("C", 2), velocity=0.68, instrument="kick_deep",
        )

    # Snare roll — accelerating density:
    #   Bar 1: beat 3 only
    #   Bar 2: beats 2 + 4
    #   Bar 3: every 2 steps
    #   Bar 4: every step, then SILENCE
    snare_hits = [8, 20, 28]
    snare_hits += list(range(32, 48, 2))
    snare_hits += list(range(48, 60))
    for i in snare_hits:
        vel = 0.52 + 0.38 * (i / 59)  # crescendo 0.52 → 0.90
        grid[1][i] = NoteEvent(
            midi_note=n("D", 3), velocity=min(vel, 0.92),
            instrument="snare_tight",
        )

    # Hat: 8th notes, stop before gap
    for i in range(0, 56, 2):
        grid[2][i] = NoteEvent(
            midi_note=n("F#", 5), velocity=0.35, instrument="hat_crisp",
        )

    # Chromatic riser on arp channel (quarter notes ascending)
    riser = [
        "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B", "C", "C#", "D",
    ]
    for i, note_name in enumerate(riser):
        step = i * 4
        if step >= 56:
            break
        octave = 4 if i < 7 else 5
        vel = 0.32 + 0.33 * (i / len(riser))
        grid[6][step] = NoteEvent(
            midi_note=n(note_name, octave), velocity=vel,
            instrument="pluck_short",
        )

    # Melody tease: first phrase only, with saw filter for edge
    for step, name, octave, vel in HOOK_CALL[:7]:
        grid[4][step] = NoteEvent(
            midi_note=n(name, octave), velocity=vel * 0.62,
            instrument="saw_filtered",
        )

    # Low bass drone: D2 whole notes, bars 1-2 only
    grid[3][0] = NoteEvent(
        midi_note=n("D", 2), velocity=0.40, instrument="bass_sub",
        duration_steps=32,
    )

    # ── THE GAP: steps 60-63 completely silent ──
    # Maximum contrast before the drop

    return Pattern(
        name="build", bpm=BPM, num_steps=STEPS, num_channels=NUM_CH,
        grid=to_list_grid(grid),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 2: DROP 1 — four-on-floor, full hook, octave bass, polyrhythm
# ═══════════════════════════════════════════════════════════════════════════

def build_drop1() -> Pattern:
    grid = new_grid()

    # KICK: four-on-floor (every 4 steps)
    for i in range(0, STEPS, 4):
        grid[0][i] = NoteEvent(
            midi_note=n("C", 2), velocity=0.92, instrument="kick_punchy",
        )

    # SNARE: beats 2 and 4 of each bar
    for bar in range(4):
        for beat_offset in [4, 12]:
            step = bar * 16 + beat_offset
            grid[1][step] = NoteEvent(
                midi_note=n("D", 3), velocity=0.85, instrument="snare_tight",
            )

    # HI-HAT: 16th notes with polyrhythmic accent (3-against-4)
    for i in range(STEPS):
        vel = 0.30
        if i % 4 == 0:
            vel = 0.60          # quarter note accent
        if i % 3 == 0:
            vel = max(vel, 0.50)  # triplet accent → polyrhythm!
        if i % 2 == 0:
            vel = max(vel, 0.38)
        grid[2][i] = NoteEvent(
            midi_note=n("F#", 5), velocity=vel, instrument="hat_crisp",
        )

    # BASS: octave bounce (root, octave up, root, octave up per bar)
    for bar in range(4):
        root = BASS_ROOTS[bar]
        for beat in range(4):
            step = bar * 16 + beat * 4
            note = root if beat % 2 == 0 else root + 12
            grid[3][step] = NoteEvent(
                midi_note=note, velocity=0.82, instrument="bass_growl",
            )

    # LEAD: full hook melody (call + response)
    place_melody(grid, 4, HOOK_CALL + HOOK_RESPONSE, "saw_filtered")

    # CHORDS: off-beat stabs cycling through chord tones
    for bar in range(4):
        chord = CHORDS[bar]
        for beat in range(4):
            step = bar * 16 + beat * 4 + 2
            note_idx = beat % len(chord)
            grid[5][step] = NoteEvent(
                midi_note=chord[note_idx], velocity=0.50,
                instrument="pulse_warm",
            )

    return Pattern(
        name="drop1", bpm=BPM, num_steps=STEPS, num_channels=NUM_CH,
        grid=to_list_grid(grid),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 3: Breakdown — stripped back, emotional, breathing room
# ═══════════════════════════════════════════════════════════════════════════

def build_breakdown() -> Pattern:
    grid = new_grid()

    # Sparse kick: beat 1 of bars 1 and 3
    grid[0][0] = NoteEvent(
        midi_note=n("C", 2), velocity=0.48, instrument="kick_deep",
    )
    grid[0][32] = NoteEvent(
        midi_note=n("C", 2), velocity=0.42, instrument="kick_deep",
    )

    # Rim: beat 3 of each bar
    for bar in range(4):
        grid[1][bar * 16 + 8] = NoteEvent(
            midi_note=n("D", 3), velocity=0.32, instrument="noise_rim",
        )

    # Soft hat: quarter notes
    for i in range(0, STEPS, 4):
        grid[2][i] = NoteEvent(
            midi_note=n("F#", 5), velocity=0.20, instrument="hat_open_shimmer",
        )

    # Melody: just the call phrase, quiet pluck
    for step, name, octave, vel in HOOK_CALL:
        grid[4][step] = NoteEvent(
            midi_note=n(name, octave), velocity=vel * 0.48,
            instrument="pluck_short",
        )

    # Pad: sustained Dm
    grid[5][0] = NoteEvent(
        midi_note=n("D", 4), velocity=0.38, instrument="pad_lush",
        duration_steps=64,
    )

    # Arp: updown, thinned to 8th notes (every 2 steps)
    arp_notes = generate_arpeggio(CHORDS, steps_per_chord=16, pattern_type="updown")
    for i, note in enumerate(arp_notes):
        if i < STEPS and note > 0 and i % 2 == 0:
            grid[6][i] = NoteEvent(
                midi_note=note, velocity=0.45, instrument="pluck_short",
            )

    return Pattern(
        name="breakdown", bpm=BPM, num_steps=STEPS, num_channels=NUM_CH,
        grid=to_list_grid(grid),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 4: Build 2 — more intense than build 1, longer gap
# ═══════════════════════════════════════════════════════════════════════════

def build_build2() -> Pattern:
    grid = new_grid()

    # Kick: quarter notes (every 4 steps), bars 1-3
    for i in range(0, 48, 4):
        grid[0][i] = NoteEvent(
            midi_note=n("C", 2), velocity=0.78, instrument="kick_punchy",
        )

    # Snare: intense roll from the start
    #   Bars 1-2: every 2 steps
    #   Bar 3: every step
    #   Bar 4: first 8 steps, then SILENCE
    snare_hits = list(range(0, 32, 2))   # bars 1-2: 16 hits
    snare_hits += list(range(32, 48))    # bar 3: 16 hits
    snare_hits += list(range(48, 56))    # bar 4 first half: 8 hits
    for i in snare_hits:
        vel = 0.58 + 0.37 * (i / 55)
        grid[1][i] = NoteEvent(
            midi_note=n("D", 3), velocity=min(vel, 0.95),
            instrument="snare_tight",
        )

    # Hat: 16ths, stop before gap
    for i in range(0, 52):
        grid[2][i] = NoteEvent(
            midi_note=n("F#", 5), velocity=0.42, instrument="hat_crisp",
        )

    # Bass: D2 on downbeats, bars 1-3
    for bar in range(3):
        grid[3][bar * 16] = NoteEvent(
            midi_note=n("D", 2), velocity=0.62, instrument="bass_sub",
        )

    # Riser: higher register, D minor scale ascending (quarter notes)
    riser = ["D", "E", "F", "G", "A", "Bb", "C", "D", "E", "F", "G", "A", "Bb"]
    for i, note_name in enumerate(riser):
        step = i * 4
        if step >= 52:
            break
        octave = 5 if i < 8 else 6
        vel = 0.38 + 0.42 * (i / len(riser))
        grid[6][step] = NoteEvent(
            midi_note=n(note_name, octave), velocity=vel,
            instrument="lead_bright",
        )

    # Melody: compressed hook fragment, faster rhythm
    fast_tease = [
        (0, "D", 5, 0.70), (2, "F", 5, 0.65), (4, "G", 5, 0.72),
        (6, "A", 5, 0.78), (8, "Bb", 5, 0.82),
        (16, "D", 5, 0.70), (18, "F", 5, 0.65), (20, "G", 5, 0.72),
        (22, "A", 5, 0.78), (24, "Bb", 5, 0.85), (26, "C", 6, 0.90),
    ]
    place_melody(grid, 4, fast_tease, "saw_filtered")

    # ── THE GAP: steps 56-63 — 8 steps of silence (half a bar) ──
    # Longer gap than build 1 → bigger impact on drop 2

    return Pattern(
        name="build2", bpm=BPM, num_steps=STEPS, num_channels=NUM_CH,
        grid=to_list_grid(grid),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Pattern 5: DROP 2 — breakbeat shift, counter-melody, maximum energy
# ═══════════════════════════════════════════════════════════════════════════

def build_drop2() -> Pattern:
    grid = new_grid()

    # GENRE SHIFT: breakbeat groove instead of four-on-floor
    groove = get_drum_groove("breakbeat", num_steps=STEPS, variation=0.05, rng=RNG)
    kick_vel = humanize_velocities(
        groove["kick"], base_velocity=115, swing=0.08, rng=RNG,
    )
    snare_vel = humanize_velocities(
        groove["snare"], base_velocity=100, swing=0.10, rng=RNG,
    )

    for i in range(STEPS):
        if kick_vel[i] > 0:
            grid[0][i] = NoteEvent(
                midi_note=n("C", 2), velocity=kick_vel[i] / 127.0,
                instrument="kick_punchy",
            )
        if snare_vel[i] > 0:
            grid[1][i] = NoteEvent(
                midi_note=n("D", 3), velocity=snare_vel[i] / 127.0,
                instrument="snare_tight",
            )

    # HI-HAT: 16ths with polyrhythm + glitch (probabilistic omission)
    for i in range(STEPS):
        vel = 0.28
        if i % 4 == 0:
            vel = 0.62
        if i % 3 == 0:
            vel = max(vel, 0.52)
        if i % 2 == 0:
            vel = max(vel, 0.36)
        # Glitch: randomly skip ~8% of hats
        if RNG.random() < 0.08:
            continue
        grid[2][i] = NoteEvent(
            midi_note=n("F#", 5), velocity=vel, instrument="hat_crisp",
        )

    # BASS: denser 8th-note bounce (twice as fast as drop 1)
    for bar in range(4):
        root = BASS_ROOTS[bar]
        for eighth in range(8):
            step = bar * 16 + eighth * 2
            note = root if eighth % 2 == 0 else root + 12
            grid[3][step] = NoteEvent(
                midi_note=note, velocity=0.85, instrument="bass_growl",
            )

    # LEAD: hook with boosted intensity
    intense_call = [
        (s, nm, o, min(v * 1.12, 0.98)) for s, nm, o, v in HOOK_CALL
    ]
    intense_resp = [
        (s, nm, o, min(v * 1.12, 0.98)) for s, nm, o, v in HOOK_RESPONSE
    ]
    place_melody(grid, 4, intense_call + intense_resp, "lead_bright")

    # CHORDS: aggressive off-beat stabs
    for bar in range(4):
        chord = CHORDS[bar]
        for beat in range(4):
            step = bar * 16 + beat * 4 + 2
            note_idx = beat % len(chord)
            grid[5][step] = NoteEvent(
                midi_note=chord[note_idx], velocity=0.58,
                instrument="pulse_warm",
            )

    # COUNTER-MELODY: AI-generated, weaving around the hook
    counter = generate_phrase_melody(
        root_midi=n("A", 5), scale_name="natural_minor",
        phrase_length=8, num_phrases=8, contour="wave",
        rest_probability=0.30, rng=RNG,
    )
    for i, note in enumerate(counter):
        if i < STEPS and note > 0 and i not in grid[6]:
            grid[6][i] = NoteEvent(
                midi_note=note, velocity=0.40,
                instrument="pluck_short",
            )

    return Pattern(
        name="drop2", bpm=BPM, num_steps=STEPS, num_channels=NUM_CH,
        grid=to_list_grid(grid),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Main — Assemble and Render
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    os.makedirs("output", exist_ok=True)

    print("=" * 60)
    print('  ChipForge — "Neural Cascade"')
    print("  Bleeding-edge AI composition with viral beat drop")
    print("=" * 60)

    t0 = time.time()

    # Build all 6 patterns
    print("\n▸ Building patterns...")
    intro     = build_intro()
    build     = build_build()
    drop1     = build_drop1()
    breakdown = build_breakdown()
    build2    = build_build2()
    drop2     = build_drop2()

    # Assemble song with arrangement
    song = Song(
        title="Neural Cascade",
        bpm=BPM,
        patterns=[intro, build, drop1, breakdown, build2, drop2],
        sequence=[
            0,        # Intro
            1,        # Build (snare roll → THE GAP)
            2, 2,     # ▼ DROP 1 ×2 (four-on-floor, full hook)
            3,        # Breakdown (breathe)
            4,        # Build 2 (intense → LONGER GAP)
            5, 5,     # ▼ DROP 2 ×2 (breakbeat shift, counter-melody)
            0,        # Outro (return to intro)
        ],
        panning={
            0: 0.0,     # kick — center
            1: 0.0,     # snare — center
            2: 0.30,    # hat — right
            3: -0.10,   # bass — slight left
            4: 0.15,    # lead — slight right
            5: -0.25,   # chord — left
            6: 0.40,    # arp — right
        },
        channel_effects={
            4: {"delay": 0.15, "delay_feedback": 0.22, "delay_mix": 0.20},
            5: {"reverb": 0.55, "reverb_damping": 0.45, "reverb_mix": 0.28},
            6: {"delay": 0.18, "delay_feedback": 0.35, "delay_mix": 0.35,
                "reverb": 0.4, "reverb_damping": 0.5, "reverb_mix": 0.2},
        },
        master_reverb=0.12,
        master_delay=0.05,
    )

    # Render
    print(f"▸ Rendering {len(song.sequence)} sections "
          f"({len(song.patterns)} unique patterns, {BPM} BPM)...")

    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    path = "output/neural_cascade.wav"
    export_wav(audio, path)

    duration = audio.shape[0] / 44100
    elapsed = time.time() - t0
    size_mb = os.path.getsize(path) / (1024 * 1024)

    # Timeline
    step_sec = 60.0 / (BPM * 4)
    pattern_sec = STEPS * step_sec

    print(f"\n  ✓ {path}")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Rendered in {elapsed:.1f}s")
    print(f"\n  ┌─ Timeline ─────────────────────────────────────┐")
    sections = [
        "Intro (sparse arp, melody tease)",
        "Build (snare roll, riser → THE GAP)",
        "▼ DROP 1 (four-on-floor, hook, bass bounce)",
        "  DROP 1 cont'd",
        "Breakdown (pad, arpeggios, breathe)",
        "Build 2 (intense, longer gap)",
        "▼ DROP 2 (breakbeat shift, counter-melody)",
        "  DROP 2 cont'd",
        "Outro (return to intro)",
    ]
    for i, label in enumerate(sections):
        t = i * pattern_sec
        print(f"  │ {t:5.1f}s  {label}")
    print(f"  └──────────────────────────────────────────────────┘")
    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
