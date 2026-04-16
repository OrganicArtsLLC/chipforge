#!/usr/bin/env python3
"""
ChipForge Demo Reel v2 — AI Super Powered
==========================================
5 tracks showcasing the upgraded engine:
  1. Neon Pulse    — electro banger, four-on-floor, filtered saw lead
  2. Moonlit Waltz — 3/4 waltz, warm pulse chords, phrase melody
  3. Iron Circuit  — breakbeat industrial, growl bass, pluck arpeggios
  4. Crystal Rain  — ambient chiptune, arpeggiated chords, lush pad
  5. Voltage Rush  — high-energy chase, trap groove, pitch-sweep kicks

Each track uses: stereo panning, per-channel effects, master reverb,
genre-specific drum grooves, phrase-aware melodies, humanized velocity,
and the new filtered/pitch-sweep instruments.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from src.synth import ADSR, note_to_freq, synthesize_note
from src.instruments import PRESETS
from src.theory import (
    note_name_to_midi, get_scale_notes, build_chord_progression,
    get_drum_groove, generate_phrase_melody, humanize_velocities,
    generate_bass_line, generate_arpeggio,
)
from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav


def n(name: str, octave: int = 4) -> int:
    """Shorthand: note name to MIDI."""
    return note_name_to_midi(name, octave)


def dict_grid_to_list(
    grid: dict[int, dict[int, NoteEvent]], num_channels: int, num_steps: int
) -> list[list[NoteEvent | None]]:
    """Convert sparse dict-of-dicts grid to list-of-lists for Pattern."""
    result: list[list[NoteEvent | None]] = []
    for ch in range(num_channels):
        row: list[NoteEvent | None] = [None] * num_steps
        for step, event in grid.get(ch, {}).items():
            if 0 <= step < num_steps:
                row[step] = event
        result.append(row)
    return result


# ═══════════════════════════════════════════════════════════════════════════
# Track 1: Neon Pulse — electro four-on-floor
# ═══════════════════════════════════════════════════════════════════════════

def build_neon_pulse() -> Song:
    """Electro banger with filtered saw lead, sub bass, four-on-floor groove."""
    bpm = 128
    steps = 32

    # Drum groove — electro template with 16th hat
    groove = get_drum_groove("electro", num_steps=steps, variation=0.05)
    kick_vel = humanize_velocities(groove["kick"], base_velocity=110, swing=0.1)
    snare_vel = humanize_velocities(groove["snare"], base_velocity=95, swing=0.15)
    hat_vel = humanize_velocities(groove["hat"], base_velocity=65, swing=0.2)

    # Chord progression — E minor: i - VI - VII - iv
    chords = build_chord_progression(n("E", 3), "i_VII_VI_VII", "natural_minor")

    # Bass follows chords
    bass_notes = generate_bass_line(chords, steps_per_chord=8, style="root_fifth")

    # Melody — phrase-aware, pentatonic minor
    melody = generate_phrase_melody(
        root_midi=n("E", 5), scale_name="pentatonic_minor",
        phrase_length=8, num_phrases=4, contour="arch",
    )

    # Build pattern: ch0=kick, ch1=snare, ch2=hat, ch3=bass, ch4=lead, ch5=chords
    grid: dict[int, dict[int, NoteEvent]] = {i: {} for i in range(6)}

    for i in range(steps):
        if kick_vel[i] > 0:
            grid[0][i] = NoteEvent(midi_note=n("C", 2), velocity=kick_vel[i] / 127.0, instrument="kick_deep")
        if snare_vel[i] > 0:
            grid[1][i] = NoteEvent(midi_note=n("D", 3), velocity=snare_vel[i] / 127.0, instrument="snare_tight")
        if hat_vel[i] > 0:
            grid[2][i] = NoteEvent(midi_note=n("F#", 5), velocity=hat_vel[i] / 127.0, instrument="hat_crisp")

        # Bass — every note from generator
        if i < len(bass_notes) and bass_notes[i] > 0:
            grid[3][i] = NoteEvent(midi_note=bass_notes[i], velocity=0.75, instrument="bass_sub")

        # Lead melody
        if i < len(melody) and melody[i] > 0:
            grid[4][i] = NoteEvent(midi_note=melody[i], velocity=0.72, instrument="saw_filtered")

        # Chord hits on beats 1 and 3
        chord_idx = min(i // 8, len(chords) - 1)
        if i % 8 == 0:
            for cn in chords[chord_idx]:
                grid[5][i] = NoteEvent(midi_note=cn, velocity=0.55, instrument="pulse_warm")

    pattern = Pattern(name="neon_pulse", bpm=bpm, num_steps=steps, num_channels=6,
                      grid=dict_grid_to_list(grid, 6, steps))

    return Song(
        title="Neon Pulse",
        bpm=bpm,
        patterns=[pattern],
        sequence=[0, 0],
        panning={0: 0.0, 1: 0.0, 2: 0.3, 3: -0.1, 4: 0.25, 5: -0.3},
        channel_effects={
            4: {"delay": 0.18, "delay_feedback": 0.25, "delay_mix": 0.2},
            5: {"reverb": 0.6, "reverb_damping": 0.5, "reverb_mix": 0.25},
        },
        master_reverb=0.15,
        master_delay=0.08,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Track 2: Moonlit Waltz — 3/4 time, warm and gentle
# ═══════════════════════════════════════════════════════════════════════════

def build_moonlit_waltz() -> Song:
    """Gentle waltz in C major with arpeggiated chords and phrase melody."""
    bpm = 108
    steps = 24  # 2 bars of 3/4 (12 steps per bar)

    # Waltz groove
    groove = get_drum_groove("waltz", num_steps=steps)
    kick_vel = humanize_velocities(groove["kick"], base_velocity=80, swing=0.2)
    snare_vel = humanize_velocities(groove["snare"], base_velocity=65, swing=0.2)
    hat_vel = humanize_velocities(groove["hat"], base_velocity=50, swing=0.25)

    # Chords — C major: I - vi - IV - V
    chords = build_chord_progression(n("C", 4), "I_vi_IV_V", "major")

    # Arpeggio through chord tones
    arp = generate_arpeggio(chords, steps_per_chord=6, pattern_type="updown")

    # Melody — ascending phrase, gentle
    melody = generate_phrase_melody(
        root_midi=n("C", 5), scale_name="major",
        phrase_length=12, num_phrases=2, contour="wave",
        rest_probability=0.2,
    )

    grid: dict[int, dict[int, NoteEvent]] = {i: {} for i in range(5)}

    for i in range(steps):
        if kick_vel[i] > 0:
            grid[0][i] = NoteEvent(midi_note=n("C", 2), velocity=kick_vel[i] / 127.0, instrument="kick_punchy")
        if snare_vel[i] > 0:
            grid[1][i] = NoteEvent(midi_note=n("D", 3), velocity=snare_vel[i] / 127.0, instrument="noise_rim")
        if hat_vel[i] > 0:
            grid[2][i] = NoteEvent(midi_note=n("F#", 5), velocity=hat_vel[i] / 127.0, instrument="hat_crisp")
        if i < len(arp) and arp[i] > 0:
            grid[3][i] = NoteEvent(midi_note=arp[i], velocity=0.57, instrument="pluck_short")
        if i < len(melody) and melody[i] > 0:
            grid[4][i] = NoteEvent(midi_note=melody[i], velocity=0.63, instrument="pulse_warm")

    pattern = Pattern(name="moonlit_waltz", bpm=bpm, num_steps=steps, num_channels=5,
                      grid=dict_grid_to_list(grid, 5, steps))

    return Song(
        title="Moonlit Waltz",
        bpm=bpm,
        patterns=[pattern],
        sequence=[0, 0, 0],
        panning={0: 0.0, 1: 0.1, 2: -0.4, 3: 0.5, 4: -0.2},
        channel_effects={
            3: {"delay": 0.25, "delay_feedback": 0.3, "delay_mix": 0.3},
            4: {"reverb": 0.7, "reverb_damping": 0.4, "reverb_mix": 0.35},
        },
        master_reverb=0.25,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Track 3: Iron Circuit — breakbeat industrial
# ═══════════════════════════════════════════════════════════════════════════

def build_iron_circuit() -> Song:
    """Industrial breakbeat with growl bass, bright lead, punchy drums."""
    bpm = 140
    steps = 32

    groove = get_drum_groove("breakbeat", num_steps=steps, variation=0.08)
    kick_vel = humanize_velocities(groove["kick"], base_velocity=115, swing=0.1)
    snare_vel = humanize_velocities(groove["snare"], base_velocity=100, swing=0.1)
    hat_vel = humanize_velocities(groove["hat"], base_velocity=60, swing=0.15)

    # Dark minor chords — A minor: i - iv - VII - III
    chords = build_chord_progression(n("A", 3), "i_iv_VII_III", "natural_minor")

    bass = generate_bass_line(chords, steps_per_chord=8, style="walking")

    melody = generate_phrase_melody(
        root_midi=n("A", 4), scale_name="blues",
        phrase_length=8, num_phrases=4, contour="descending",
        rest_probability=0.15,
    )

    grid: dict[int, dict[int, NoteEvent]] = {i: {} for i in range(5)}

    for i in range(steps):
        if kick_vel[i] > 0:
            grid[0][i] = NoteEvent(midi_note=n("C", 2), velocity=kick_vel[i] / 127.0, instrument="kick_punchy")
        if snare_vel[i] > 0:
            grid[1][i] = NoteEvent(midi_note=n("D", 3), velocity=snare_vel[i] / 127.0, instrument="snare_tight")
        if hat_vel[i] > 0:
            grid[2][i] = NoteEvent(midi_note=n("F#", 5), velocity=hat_vel[i] / 127.0, instrument="hat_open_shimmer")
        if i < len(bass) and bass[i] > 0:
            grid[3][i] = NoteEvent(midi_note=bass[i], velocity=0.80, instrument="bass_growl")
        if i < len(melody) and melody[i] > 0:
            grid[4][i] = NoteEvent(midi_note=melody[i], velocity=0.75, instrument="lead_bright")

    pattern = Pattern(name="iron_circuit", bpm=bpm, num_steps=steps, num_channels=5,
                      grid=dict_grid_to_list(grid, 5, steps))

    return Song(
        title="Iron Circuit",
        bpm=bpm,
        patterns=[pattern],
        sequence=[0, 0],
        panning={0: 0.0, 1: 0.0, 2: 0.4, 3: -0.15, 4: 0.35},
        channel_effects={
            3: {"reverb": 0.3, "reverb_damping": 0.7, "reverb_mix": 0.15},
            4: {"delay": 0.14, "delay_feedback": 0.3, "delay_mix": 0.25},
        },
        master_reverb=0.12,
        master_delay=0.06,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Track 4: Crystal Rain — ambient chiptune
# ═══════════════════════════════════════════════════════════════════════════

def build_crystal_rain() -> Song:
    """Ambient chiptune with lush pad, arpeggio rain, half-time drums."""
    bpm = 90
    steps = 32

    groove = get_drum_groove("half_time", num_steps=steps)
    kick_vel = humanize_velocities(groove["kick"], base_velocity=70, swing=0.25)
    snare_vel = humanize_velocities(groove["snare"], base_velocity=55, swing=0.3)
    hat_vel = humanize_velocities(groove["hat"], base_velocity=40, swing=0.3)

    # Dreamy — D major: I - IV - V - I
    chords = build_chord_progression(n("D", 4), "I_IV_V_I", "major")

    arp = generate_arpeggio(chords, steps_per_chord=8, pattern_type="up")

    melody = generate_phrase_melody(
        root_midi=n("D", 5), scale_name="pentatonic_major",
        phrase_length=16, num_phrases=2, contour="arch",
        rest_probability=0.25,
    )

    grid: dict[int, dict[int, NoteEvent]] = {i: {} for i in range(6)}

    for i in range(steps):
        if kick_vel[i] > 0:
            grid[0][i] = NoteEvent(midi_note=n("C", 2), velocity=kick_vel[i] / 127.0, instrument="kick_deep")
        if snare_vel[i] > 0:
            grid[1][i] = NoteEvent(midi_note=n("D", 3), velocity=snare_vel[i] / 127.0, instrument="noise_snare")
        if hat_vel[i] > 0:
            grid[2][i] = NoteEvent(midi_note=n("F#", 5), velocity=hat_vel[i] / 127.0, instrument="hat_crisp")
        if i < len(arp) and arp[i] > 0:
            grid[3][i] = NoteEvent(midi_note=arp[i], velocity=0.52, instrument="pluck_short")
        # Pad — sustained chord hits
        chord_idx = min(i // 8, len(chords) - 1)
        if i % 16 == 0:
            grid[4][i] = NoteEvent(midi_note=chords[chord_idx][0], velocity=0.43, instrument="pad_lush")
        # Melody
        if i < len(melody) and melody[i] > 0:
            grid[5][i] = NoteEvent(midi_note=melody[i], velocity=0.60, instrument="wave_melody")

    pattern = Pattern(name="crystal_rain", bpm=bpm, num_steps=steps, num_channels=6,
                      grid=dict_grid_to_list(grid, 6, steps))

    return Song(
        title="Crystal Rain",
        bpm=bpm,
        patterns=[pattern],
        sequence=[0, 0, 0],
        panning={0: 0.0, 1: 0.0, 2: -0.5, 3: 0.6, 4: -0.3, 5: 0.15},
        channel_effects={
            3: {"delay": 0.3, "delay_feedback": 0.35, "delay_mix": 0.4},
            4: {"reverb": 0.8, "reverb_damping": 0.35, "reverb_mix": 0.5},
            5: {"delay": 0.22, "delay_feedback": 0.2, "delay_mix": 0.25,
                "reverb": 0.5, "reverb_damping": 0.4, "reverb_mix": 0.3},
        },
        master_reverb=0.30,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Track 5: Voltage Rush — high-energy chase
# ═══════════════════════════════════════════════════════════════════════════

def build_voltage_rush() -> Song:
    """High-energy chase track with trap groove, dark saw, fast melody."""
    bpm = 155
    steps = 32

    groove = get_drum_groove("trap", num_steps=steps, variation=0.06)
    kick_vel = humanize_velocities(groove["kick"], base_velocity=118, swing=0.08)
    snare_vel = humanize_velocities(groove["snare"], base_velocity=105, swing=0.1)
    hat_vel = humanize_velocities(groove["hat"], base_velocity=55, swing=0.2)

    # Dark and aggressive — F# minor
    chords = build_chord_progression(n("F#", 3), "i_iv_VII_III", "harmonic_minor")

    bass = generate_bass_line(chords, steps_per_chord=8, style="octave")

    melody = generate_phrase_melody(
        root_midi=n("F#", 5), scale_name="harmonic_minor",
        phrase_length=8, num_phrases=4, contour="descending",
        rest_probability=0.1,
    )

    grid: dict[int, dict[int, NoteEvent]] = {i: {} for i in range(5)}

    for i in range(steps):
        if kick_vel[i] > 0:
            grid[0][i] = NoteEvent(midi_note=n("C", 2), velocity=kick_vel[i] / 127.0, instrument="kick_punchy")
        if snare_vel[i] > 0:
            grid[1][i] = NoteEvent(midi_note=n("D", 3), velocity=snare_vel[i] / 127.0, instrument="snare_tight")
        if hat_vel[i] > 0:
            grid[2][i] = NoteEvent(midi_note=n("F#", 5), velocity=hat_vel[i] / 127.0, instrument="hat_crisp")
        if i < len(bass) and bass[i] > 0:
            grid[3][i] = NoteEvent(midi_note=bass[i], velocity=0.82, instrument="saw_dark")
        if i < len(melody) and melody[i] > 0:
            grid[4][i] = NoteEvent(midi_note=melody[i], velocity=0.78, instrument="lead_bright")

    pattern = Pattern(name="voltage_rush", bpm=bpm, num_steps=steps, num_channels=5,
                      grid=dict_grid_to_list(grid, 5, steps))

    return Song(
        title="Voltage Rush",
        bpm=bpm,
        patterns=[pattern],
        sequence=[0, 0],
        panning={0: 0.0, 1: 0.0, 2: -0.35, 3: 0.2, 4: -0.25},
        channel_effects={
            3: {"reverb": 0.25, "reverb_damping": 0.6, "reverb_mix": 0.12},
            4: {"delay": 0.10, "delay_feedback": 0.2, "delay_mix": 0.18},
        },
        master_reverb=0.10,
        master_delay=0.05,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Main — Render All Tracks
# ═══════════════════════════════════════════════════════════════════════════

TRACKS = [
    ("01_neon_pulse",    build_neon_pulse),
    ("02_moonlit_waltz", build_moonlit_waltz),
    ("03_iron_circuit",  build_iron_circuit),
    ("04_crystal_rain",  build_crystal_rain),
    ("05_voltage_rush",  build_voltage_rush),
]


def main() -> None:
    os.makedirs("output", exist_ok=True)
    total_start = time.time()

    print("=" * 60)
    print("  ChipForge Demo Reel v2 — AI Super Powered")
    print("=" * 60)

    for filename, builder in TRACKS:
        print(f"\n▸ Building {filename}...")
        t0 = time.time()
        song = builder()

        print(f"  Rendering ({song.bpm} BPM, {len(song.sequence)} sections)...")
        audio = render_song(
            song,
            panning=getattr(song, "panning", None),
            channel_effects=getattr(song, "channel_effects", None),
            master_reverb=getattr(song, "master_reverb", None),
            master_delay=getattr(song, "master_delay", None),
        )

        path = f"output/{filename}.wav"
        export_wav(audio, path)
        duration = audio.shape[0] / 44100
        elapsed = time.time() - t0
        size_kb = os.path.getsize(path) / 1024

        print(f"  ✓ {path} — {duration:.1f}s, {size_kb:.0f}KB ({elapsed:.1f}s to render)")

    total = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"  All 5 tracks rendered in {total:.1f}s")
    print(f"  Output: output/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
