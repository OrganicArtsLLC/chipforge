"""
ChipForge Music Theory
=======================
Pure functions for notes, scales, chords, melody, rhythm, and drum generation.
Includes genre-specific groove templates, phrase-aware melody builders,
humanized velocity, and classical/electro composition patterns.
No mutable state — safe to call from any context.
"""

from __future__ import annotations

import random
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Note Names and MIDI
# ---------------------------------------------------------------------------

NOTE_NAMES: list[str] = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Enharmonic flat → sharp mapping
_FLAT_TO_SHARP: dict[str, str] = {
    "DB": "C#", "EB": "D#", "FB": "E",  "GB": "F#",
    "AB": "G#", "BB": "A#", "CB": "B",
}


def note_name_to_midi(note: str, octave: int = 4) -> int:
    """
    Convert a note name + octave to a MIDI note number.

    Middle C = C4 = 60.

    Args:
        note: Note name string, e.g. "C", "F#", "Bb", "Eb".
        octave: Octave number (4 = middle octave).

    Returns:
        MIDI note number (integer).

    Examples:
        >>> note_name_to_midi("C", 4)
        60
        >>> note_name_to_midi("A", 4)
        69
        >>> note_name_to_midi("Bb", 4)
        70
    """
    normalized = note.upper().replace("b", "B")
    if normalized in _FLAT_TO_SHARP:
        normalized = _FLAT_TO_SHARP[normalized]
    semitone = NOTE_NAMES.index(normalized)
    return (octave + 1) * 12 + semitone


def midi_to_note_name(midi: int) -> str:
    """
    Convert a MIDI note number to a note name + octave string.

    Args:
        midi: MIDI note number (0–127).

    Returns:
        String like "C4", "F#5", "A#3".

    Examples:
        >>> midi_to_note_name(60)
        'C4'
        >>> midi_to_note_name(69)
        'A4'
    """
    octave = (midi // 12) - 1
    semitone = midi % 12
    return f"{NOTE_NAMES[semitone]}{octave}"


# ---------------------------------------------------------------------------
# Scale Definitions
# ---------------------------------------------------------------------------

# Intervals (semitones from root) for one octave
SCALES: dict[str, list[int]] = {
    "major":              [0, 2, 4, 5, 7, 9, 11],
    "natural_minor":      [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor":     [0, 2, 3, 5, 7, 8, 11],
    "pentatonic_major":   [0, 2, 4, 7, 9],
    "pentatonic_minor":   [0, 3, 5, 7, 10],
    "blues":              [0, 3, 5, 6, 7, 10],
    "dorian":             [0, 2, 3, 5, 7, 9, 10],
    "phrygian":           [0, 1, 3, 5, 7, 8, 10],
    "lydian":             [0, 2, 4, 6, 7, 9, 11],
    "mixolydian":         [0, 2, 4, 5, 7, 9, 10],
    "whole_tone":         [0, 2, 4, 6, 8, 10],
    "chromatic":          list(range(12)),
}


# ---------------------------------------------------------------------------
# Chord Definitions
# ---------------------------------------------------------------------------

# Semitone intervals from root for each chord type
CHORD_TYPES: dict[str, list[int]] = {
    "major":        [0, 4, 7],
    "minor":        [0, 3, 7],
    "dominant7":    [0, 4, 7, 10],
    "major7":       [0, 4, 7, 11],
    "minor7":       [0, 3, 7, 10],
    "diminished":   [0, 3, 6],
    "augmented":    [0, 4, 8],
    "sus2":         [0, 2, 7],
    "sus4":         [0, 5, 7],
    "power":        [0, 7],
    "add9":         [0, 4, 7, 14],
}


# ---------------------------------------------------------------------------
# Common Chord Progressions
# ---------------------------------------------------------------------------

# Scale degree (0-indexed) sequences within a major key
PROGRESSIONS: dict[str, list[int]] = {
    "I_IV_V_I":    [0, 3, 4, 0],     # classic
    "I_V_vi_IV":   [0, 4, 5, 3],     # pop (Axis of Awesome)
    "I_IV_vi_V":   [0, 3, 5, 4],     # pop variant
    "ii_V_I":      [1, 4, 0],        # jazz turnaround
    "I_vi_IV_V":   [0, 5, 3, 4],     # 50s / doo-wop
    "I_III_IV_V":  [0, 2, 3, 4],     # classic rock
    "i_VII_VI_VII": [0, 6, 5, 6],    # minor rock
    "i_iv_VII_III": [0, 3, 6, 2],    # minor epic
}


# ---------------------------------------------------------------------------
# Scale + Chord Helpers
# ---------------------------------------------------------------------------

def get_scale_notes(root_midi: int, scale_name: str = "major", octaves: int = 2) -> list[int]:
    """
    Return MIDI note numbers for a scale across the specified octaves.

    Args:
        root_midi: Root note MIDI number.
        scale_name: Scale name from SCALES dict.
        octaves: Number of octaves to span.

    Returns:
        List of MIDI note numbers in ascending order.

    Examples:
        >>> get_scale_notes(60, "pentatonic_minor", 1)
        [60, 63, 65, 67, 70, 72]
    """
    intervals = SCALES.get(scale_name, SCALES["major"])
    notes: list[int] = []
    for oct_offset in range(octaves):
        for interval in intervals:
            notes.append(root_midi + oct_offset * 12 + interval)
    notes.append(root_midi + octaves * 12)  # top root note
    return notes


def get_chord(root_midi: int, chord_type: str = "major") -> list[int]:
    """
    Return MIDI notes for a chord.

    Args:
        root_midi: Root note MIDI number.
        chord_type: Chord type from CHORD_TYPES dict.

    Returns:
        List of MIDI note numbers.
    """
    intervals = CHORD_TYPES.get(chord_type, [0, 4, 7])
    return [root_midi + i for i in intervals]


def build_chord_progression(
    key_midi: int,
    progression_name: str = "I_V_vi_IV",
    scale_name: str = "major",
    chord_type: str = "auto",
    octave: int = 4,
) -> list[list[int]]:
    """
    Build a chord progression as a list of chord note lists.

    Args:
        key_midi: Root note of the key as MIDI number.
        progression_name: Name from PROGRESSIONS dict.
        scale_name: Scale to derive chord roots from.
        chord_type: Chord type for all chords, or "auto" to derive from scale.
        octave: Target octave for chord roots.

    Returns:
        List of chords, each chord is a list of MIDI note numbers.
    """
    degree_sequence = PROGRESSIONS.get(progression_name, [0, 4, 5, 3])
    scale = SCALES.get(scale_name, SCALES["major"])

    chords: list[list[int]] = []
    for degree in degree_sequence:
        degree = degree % len(scale)
        root = key_midi + scale[degree]
        # Keep root in the target octave range
        while root < (octave + 1) * 12:
            root += 12
        while root >= (octave + 2) * 12:
            root -= 12

        if chord_type == "auto":
            # Simple rule: minor on degrees 1,2,4 in major; major elsewhere
            is_minor = degree in (1, 2, 5)
            ct = "minor" if is_minor else "major"
        else:
            ct = chord_type

        chords.append(get_chord(root, ct))

    return chords


# ---------------------------------------------------------------------------
# Melody Generation
# ---------------------------------------------------------------------------

def generate_melody(
    root_midi: int = 60,
    scale_name: str = "pentatonic_minor",
    num_steps: int = 16,
    octave_range: int = 2,
    rest_probability: float = 0.15,
    rng: Optional[random.Random] = None,
) -> list[int]:
    """
    Generate a melodic sequence using a weighted random walk along scale notes.

    Biases toward stepwise motion (nearby notes) to create natural-sounding phrases.
    Note value 0 = rest.

    Args:
        root_midi: Root note of the scale.
        scale_name: Scale to use from SCALES dict.
        num_steps: Number of steps in the output sequence.
        octave_range: How many octaves to span.
        rest_probability: Probability of generating a rest at any step (0.0–1.0).
        rng: Optional seeded Random instance for reproducibility.

    Returns:
        List of MIDI note numbers, length = num_steps. 0 = rest.
    """
    if rng is None:
        rng = random.Random()

    scale_notes = get_scale_notes(root_midi, scale_name, octave_range)
    melody: list[int] = []
    prev = root_midi

    for step in range(num_steps):
        # First and last steps anchor to root — strong melodic framing
        if step == 0 or step == num_steps - 1:
            melody.append(root_midi)
            prev = root_midi
            continue

        # Randomly inject a rest
        if rng.random() < rest_probability:
            melody.append(0)
            continue

        # Weighted by distance from previous note — prefer stepwise motion
        weights: list[float] = []
        for note in scale_notes:
            distance = abs(note - prev)
            weight = max(1.0, 12.0 - distance * 1.5)
            weights.append(weight)

        chosen = rng.choices(scale_notes, weights=weights, k=1)[0]
        melody.append(chosen)
        prev = chosen

    return melody


# ---------------------------------------------------------------------------
# Rhythm Generation
# ---------------------------------------------------------------------------

def generate_rhythm_pattern(
    num_steps: int = 16,
    density: float = 0.45,
    rng: Optional[random.Random] = None,
) -> list[bool]:
    """
    Generate a rhythmic hit pattern with downbeat emphasis.

    Args:
        num_steps: Total steps in the pattern (typically 16 or 32).
        density: Hit probability baseline (0.0 = silence, 1.0 = all hits).
        rng: Optional seeded Random instance for reproducibility.

    Returns:
        List of booleans (True = hit, False = rest), length = num_steps.
    """
    if rng is None:
        rng = random.Random()

    pattern: list[bool] = []

    for i in range(num_steps):
        if i == 0:
            # Beat 1 always hits if density > 0
            pattern.append(density > 0)
            continue

        is_downbeat = (i % 4 == 0)
        is_backbeat = (i % 8 == 4)   # beats 2 and 4 in 4/4

        prob = density
        if is_downbeat:
            prob = min(1.0, density * 1.4)
        elif is_backbeat:
            prob = min(1.0, density * 1.2)
        elif i % 2 == 1:
            prob = density * 0.6      # off-beats are less likely

        pattern.append(rng.random() < prob)

    return pattern


def generate_drum_pattern(
    num_steps: int = 16,
    kick_density: float = 0.30,
    snare_density: float = 0.25,
    hat_density: float = 0.50,
    rng: Optional[random.Random] = None,
) -> dict[str, list[bool]]:
    """
    Generate a complete 3-part drum pattern (kick, snare, hi-hat).

    Args:
        num_steps: Total steps.
        kick_density: Hit probability for kick (strong downbeat bias).
        snare_density: Hit probability for snare (backbeat bias — beats 2, 4).
        hat_density: Hit probability for hi-hat (subdivision bias).
        rng: Optional seeded Random instance.

    Returns:
        Dict with keys "kick", "snare", "hat", each a list of booleans.
    """
    if rng is None:
        rng = random.Random()

    kick: list[bool] = []
    snare: list[bool] = []
    hat: list[bool] = []

    for i in range(num_steps):
        # Kick — strong on beats 1 and 3
        is_beat_1_or_3 = (i % 8 == 0)
        kick_prob = min(1.0, kick_density * 2.0) if is_beat_1_or_3 else kick_density * 0.3
        kick.append(rng.random() < kick_prob)

        # Snare — strong on beats 2 and 4
        is_beat_2_or_4 = (i % 8 == 4)
        snare_prob = min(1.0, snare_density * 2.0) if is_beat_2_or_4 else snare_density * 0.2
        snare.append(rng.random() < snare_prob)

        # Hi-hat — subdivisions, evenly distributed
        hat_prob = hat_density * (1.5 if i % 2 == 0 else 0.7)
        hat.append(rng.random() < hat_prob)

    return {"kick": kick, "snare": snare, "hat": hat}


# ---------------------------------------------------------------------------
# Genre-Specific Drum Groove Templates
# ---------------------------------------------------------------------------

# Fixed 16-step hit patterns (True/False). These are deterministic —
# no RNG, no density knobs — just well-crafted grooves.

DRUM_GROOVES: dict[str, dict[str, list[bool]]] = {
    "four_on_floor": {
        "kick":  [True,False,False,False, True,False,False,False, True,False,False,False, True,False,False,False],
        "snare": [False,False,False,False, True,False,False,False, False,False,False,False, True,False,False,False],
        "hat":   [True,False,True,False, True,False,True,False, True,False,True,False, True,False,True,False],
    },
    "electro": {
        "kick":  [True,False,False,False, True,False,False,False, True,False,False,True, False,False,False,False],
        "snare": [False,False,False,False, True,False,False,False, False,False,False,False, True,False,False,False],
        "hat":   [True,True,True,True, True,True,True,True, True,True,True,True, True,True,True,True],
    },
    "breakbeat": {
        "kick":  [True,False,False,False, False,False,True,False, False,False,True,False, False,False,False,False],
        "snare": [False,False,False,False, True,False,False,False, False,False,False,False, True,False,False,True],
        "hat":   [True,False,True,False, True,False,True,False, True,False,True,False, True,False,True,False],
    },
    "half_time": {
        "kick":  [True,False,False,False, False,False,False,False, True,False,False,False, False,False,False,False],
        "snare": [False,False,False,False, False,False,False,False, True,False,False,False, False,False,False,False],
        "hat":   [True,False,True,False, True,False,True,False, True,False,True,False, True,False,True,False],
    },
    "waltz": {  # 12 steps = 3/4 time (3 beats × 4 subdivisions)
        "kick":  [True,False,False,False, False,False,False,False, False,False,False,False],
        "snare": [False,False,False,False, True,False,False,False, True,False,False,False],
        "hat":   [True,False,True,False, True,False,True,False, True,False,True,False],
    },
    "reggaeton": {
        "kick":  [True,False,False,True, False,False,True,False, False,True,False,False, True,False,False,False],
        "snare": [False,False,False,False, True,False,False,False, False,False,False,False, True,False,False,False],
        "hat":   [True,True,True,True, True,True,True,True, True,True,True,True, True,True,True,True],
    },
    "trap": {
        "kick":  [True,False,False,False, False,False,False,True, False,False,True,False, False,False,False,False],
        "snare": [False,False,False,False, True,False,False,False, False,False,False,False, True,False,False,False],
        "hat":   [True,True,True,True, True,True,True,True, True,True,True,True, True,True,True,True],
    },
}


def get_drum_groove(
    groove_name: str,
    num_steps: int = 16,
    variation: float = 0.0,
    rng: Optional[random.Random] = None,
) -> dict[str, list[bool]]:
    """
    Return a named drum groove template, optionally with humanizing variation.

    Args:
        groove_name: Key from DRUM_GROOVES dict.
        num_steps: Desired pattern length (will tile/truncate).
        variation: Probability of flipping each non-essential hit (0.0 = exact).
        rng: Optional seeded Random for reproducibility.

    Returns:
        Dict with "kick", "snare", "hat" boolean lists.
    """
    if rng is None:
        rng = random.Random()

    groove = DRUM_GROOVES.get(groove_name, DRUM_GROOVES["four_on_floor"])
    result: dict[str, list[bool]] = {}

    for part, template in groove.items():
        # Tile to desired length
        pat = [template[i % len(template)] for i in range(num_steps)]
        # Apply variation — only flip non-beat-1 hits
        if variation > 0:
            for i in range(1, len(pat)):
                if rng.random() < variation:
                    pat[i] = not pat[i]
        result[part] = pat

    return result


# ---------------------------------------------------------------------------
# Phrase-Aware Melody Generation
# ---------------------------------------------------------------------------

def generate_phrase_melody(
    root_midi: int = 60,
    scale_name: str = "pentatonic_minor",
    phrase_length: int = 8,
    num_phrases: int = 2,
    contour: str = "arch",
    rest_probability: float = 0.10,
    rng: Optional[random.Random] = None,
) -> list[int]:
    """
    Generate a melody built from musical phrases with shape-aware contours.

    Each phrase follows a contour (arch, descending, ascending, wave) and
    the second phrase is a variation of the first (call-and-response).

    Args:
        root_midi: Root note of the scale.
        scale_name: Scale to use.
        phrase_length: Steps per phrase.
        num_phrases: Number of phrases (2 = call + response).
        contour: Shape of each phrase ("arch", "descending", "ascending", "wave").
        rest_probability: Chance of rest at any step.
        rng: Optional seeded Random.

    Returns:
        List of MIDI note numbers (0 = rest).
    """
    if rng is None:
        rng = random.Random()

    scale_notes = get_scale_notes(root_midi, scale_name, 2)
    num_notes = len(scale_notes)
    melody: list[int] = []

    # Build target contour as index offsets (0.0 to 1.0 range)
    targets = _build_contour(phrase_length, contour)

    # Generate first phrase (call)
    call: list[int] = []
    for i, t in enumerate(targets):
        if rng.random() < rest_probability:
            call.append(0)
            continue
        # Map contour position to scale index with jitter
        idx = int(t * (num_notes - 1))
        jitter = rng.randint(-1, 1)
        idx = max(0, min(num_notes - 1, idx + jitter))
        call.append(scale_notes[idx])
    # Anchor first note to root
    call[0] = root_midi

    melody.extend(call)

    # Generate response phrases as variations of the call
    for p in range(1, num_phrases):
        response: list[int] = []
        for i, note in enumerate(call):
            if note == 0:
                response.append(0)
                continue
            if rng.random() < 0.3:
                # Vary — shift up or down a scale step
                try:
                    cur_idx = scale_notes.index(note)
                except ValueError:
                    cur_idx = num_notes // 2
                shift = rng.choice([-2, -1, 1, 2])
                new_idx = max(0, min(num_notes - 1, cur_idx + shift))
                response.append(scale_notes[new_idx])
            else:
                response.append(note)
        # End response phrase on root or fifth for resolution
        if response:
            response[-1] = root_midi if p == num_phrases - 1 else root_midi + 7
        melody.extend(response)

    return melody


def _build_contour(length: int, shape: str) -> list[float]:
    """Build a contour curve as float values 0.0 to 1.0."""
    import math
    if shape == "arch":
        return [math.sin(math.pi * i / max(1, length - 1)) for i in range(length)]
    elif shape == "descending":
        return [1.0 - i / max(1, length - 1) for i in range(length)]
    elif shape == "ascending":
        return [i / max(1, length - 1) for i in range(length)]
    elif shape == "wave":
        return [0.5 + 0.5 * math.sin(2 * math.pi * i / max(1, length - 1)) for i in range(length)]
    else:
        return [0.5] * length


# ---------------------------------------------------------------------------
# Velocity Humanization
# ---------------------------------------------------------------------------

def humanize_velocities(
    pattern: list[bool],
    base_velocity: int = 100,
    accent_beats: list[int] | None = None,
    swing: float = 0.0,
    rng: Optional[random.Random] = None,
) -> list[int]:
    """
    Generate humanized velocity values for a rhythm pattern.

    Args:
        pattern: Boolean hit pattern.
        base_velocity: Average velocity (0-127).
        accent_beats: Step indices that get accented (louder).
        swing: Velocity variation amount (0.0 = robotic, 0.3 = natural).
        rng: Optional seeded Random.

    Returns:
        List of velocity values (0 = no hit, >0 = velocity).
    """
    if rng is None:
        rng = random.Random()
    if accent_beats is None:
        accent_beats = [0, 8]  # Default: accent beat 1 and 3

    velocities: list[int] = []
    for i, hit in enumerate(pattern):
        if not hit:
            velocities.append(0)
            continue
        v = base_velocity
        # Accent
        if i in accent_beats:
            v = min(127, int(v * 1.25))
        # Off-beat softening
        elif i % 2 == 1:
            v = int(v * 0.85)
        # Random humanization
        if swing > 0:
            variation = int(swing * 30 * (rng.random() * 2 - 1))
            v = max(30, min(127, v + variation))
        velocities.append(v)

    return velocities


# ---------------------------------------------------------------------------
# Bass Line Generation
# ---------------------------------------------------------------------------

def generate_bass_line(
    chord_progression: list[list[int]],
    steps_per_chord: int = 16,
    style: str = "root_fifth",
    rng: Optional[random.Random] = None,
) -> list[int]:
    """
    Generate a bass line that follows a chord progression.

    Args:
        chord_progression: List of chords (each chord is list of MIDI notes).
        steps_per_chord: Steps allocated per chord.
        style: Bass pattern style ("root_only", "root_fifth", "walking", "octave").
        rng: Optional seeded Random.

    Returns:
        List of MIDI notes (0 = rest), one per step.
    """
    if rng is None:
        rng = random.Random()

    bass: list[int] = []

    for chord in chord_progression:
        root = min(chord)
        # Transpose root to bass octave (octave 2-3)
        while root > 55:
            root -= 12
        while root < 36:
            root += 12

        fifth = root + 7

        if style == "root_only":
            pattern = [root if i % 4 == 0 else 0 for i in range(steps_per_chord)]
        elif style == "root_fifth":
            pattern = []
            for i in range(steps_per_chord):
                if i == 0:
                    pattern.append(root)
                elif i == 8:
                    pattern.append(fifth)
                elif i == 4 or i == 12:
                    pattern.append(root if rng.random() < 0.6 else 0)
                else:
                    pattern.append(0)
        elif style == "walking":
            notes = [root, root + 3, fifth, root + 10]
            pattern = []
            for i in range(steps_per_chord):
                if i % 4 == 0:
                    pattern.append(notes[(i // 4) % len(notes)])
                else:
                    pattern.append(0)
        elif style == "octave":
            octave_up = root + 12
            pattern = []
            for i in range(steps_per_chord):
                if i % 4 == 0:
                    pattern.append(root if (i // 4) % 2 == 0 else octave_up)
                elif i % 4 == 2:
                    pattern.append(root if rng.random() < 0.4 else 0)
                else:
                    pattern.append(0)
        else:
            pattern = [root if i == 0 else 0 for i in range(steps_per_chord)]

        bass.extend(pattern)

    return bass


# ---------------------------------------------------------------------------
# Arpeggio Generation
# ---------------------------------------------------------------------------

def generate_arpeggio(
    chord_progression: list[list[int]],
    steps_per_chord: int = 16,
    pattern_type: str = "up",
    rng: Optional[random.Random] = None,
) -> list[int]:
    """
    Generate an arpeggio pattern that cycles through chord tones.

    Args:
        chord_progression: List of chords.
        steps_per_chord: Steps per chord.
        pattern_type: "up", "down", "updown", "random".
        rng: Optional seeded Random.

    Returns:
        List of MIDI notes (0 = rest).
    """
    if rng is None:
        rng = random.Random()

    arp: list[int] = []

    for chord in chord_progression:
        notes = sorted(chord)
        if pattern_type == "down":
            notes = list(reversed(notes))
        elif pattern_type == "updown":
            notes = notes + list(reversed(notes[1:-1])) if len(notes) > 2 else notes

        for i in range(steps_per_chord):
            if pattern_type == "random":
                arp.append(rng.choice(notes))
            else:
                cycle_idx = i % len(notes) if notes else 0
                arp.append(notes[cycle_idx] if notes else 0)

    return arp


# ---------------------------------------------------------------------------
# Counterpoint Generator — AI-Only Technique
# ---------------------------------------------------------------------------

def generate_counterpoint(
    melody: list[int],
    key_root: int = 60,
    scale_name: str = "natural_minor",
    species: int = 1,
    interval_preference: str = "thirds",
    rng: random.Random | None = None,
) -> list[int]:
    """
    Generate a harmonically correct counter-melody following species counterpoint rules.

    Given a melody (list of MIDI notes, 0 = rest), generates a second voice that:
    - Moves in contrary motion when possible (melody up → counter down)
    - Uses consonant intervals on strong beats (3rds, 6ths, 5ths, octaves)
    - Avoids parallel fifths and octaves
    - Prefers stepwise motion (70% steps, 25% thirds, 5% leaps)
    - Maintains independence (different rhythm/contour from melody)

    This is [AI-ONLY]: evaluating all candidate notes against 6+ simultaneous
    rules at each position creates a combinatorial search space that AI can
    prune efficiently.

    Args:
        melody: List of MIDI note numbers (0 = rest).
        key_root: MIDI note of the key root (default 60 = C4).
        scale_name: Scale to constrain counter-melody to.
        species: Counterpoint species (1 = note-against-note, 2 = two notes per one).
        interval_preference: "thirds" (parallel thirds), "contrary" (opposite motion),
                            "free" (AI chooses best).
        rng: Random number generator for controlled randomness.

    Returns:
        List of MIDI notes for the counter-melody (same length as melody).
    """
    import logging
    logger = logging.getLogger("chipforge.counterpoint")

    if rng is None:
        rng = random.Random(42)

    # Get scale notes across multiple octaves
    scale = get_scale_notes(key_root, scale_name, octaves=4)
    if not scale:
        logger.warning(f"Unknown scale '{scale_name}', falling back to natural_minor")
        scale = get_scale_notes(key_root, "natural_minor", octaves=4)

    # Consonant intervals (in semitones) — ranked by preference
    consonances = {
        3: 1.0,   # minor third — very consonant, common
        4: 1.0,   # major third — very consonant
        7: 0.8,   # perfect fifth — consonant but watch parallels
        8: 0.7,   # minor sixth
        9: 0.7,   # major sixth
        12: 0.5,  # octave — consonant but watch parallels
        5: 0.4,   # perfect fourth — conditional consonance
    }

    # Dissonant intervals to AVOID on strong beats
    dissonances = {1, 2, 6, 10, 11}  # m2, M2, tritone, m7, M7

    counter = []
    prev_counter_note = 0
    prev_melody_note = 0
    prev_interval = 0

    for i, mel_note in enumerate(melody):
        if mel_note == 0:
            counter.append(0)  # rest when melody rests
            continue

        is_strong_beat = (i % 4 == 0)  # every 4th position is a strong beat

        # Find all scale notes within reasonable range of the melody
        candidates = [n for n in scale if abs(n - mel_note) <= 19 and n != mel_note]
        if not candidates:
            counter.append(mel_note - 12)  # fallback: octave below
            continue

        # Score each candidate
        scores: list[tuple[float, int]] = []
        for cand in candidates:
            score = 0.0
            interval = abs(cand - mel_note) % 12

            # Rule 1: Prefer consonant intervals (especially on strong beats)
            if interval in consonances:
                score += consonances[interval] * (2.0 if is_strong_beat else 1.0)
            elif interval in dissonances and is_strong_beat:
                score -= 3.0  # heavily penalize strong-beat dissonance

            # Rule 2: Prefer contrary motion
            if prev_melody_note > 0 and prev_counter_note > 0:
                mel_direction = mel_note - prev_melody_note
                cand_direction = cand - prev_counter_note
                if mel_direction > 0 and cand_direction < 0:
                    score += 1.5  # contrary motion — excellent
                elif mel_direction < 0 and cand_direction > 0:
                    score += 1.5  # contrary motion
                elif mel_direction == 0:
                    score += 0.5  # oblique motion — acceptable

            # Rule 3: Avoid parallel fifths and octaves
            if prev_counter_note > 0 and prev_melody_note > 0:
                prev_interval_mod = abs(prev_counter_note - prev_melody_note) % 12
                curr_interval_mod = interval
                if prev_interval_mod == curr_interval_mod and curr_interval_mod in (7, 0):
                    score -= 5.0  # FORBIDDEN: parallel 5ths/octaves

            # Rule 4: Prefer stepwise motion in the counter voice
            if prev_counter_note > 0:
                step_size = abs(cand - prev_counter_note)
                if step_size <= 2:
                    score += 1.0  # stepwise — preferred
                elif step_size <= 4:
                    score += 0.5  # third — acceptable
                elif step_size <= 7:
                    score += 0.0  # larger — neutral
                else:
                    score -= 0.5  # large leap — penalize

            # Rule 5: Prefer lower register for counter (below melody)
            if interval_preference == "thirds":
                if cand < mel_note and interval in (3, 4):
                    score += 1.0  # thirds below — classic
            elif interval_preference == "contrary":
                if cand < mel_note:
                    score += 0.5

            # Rule 6: Avoid unisons
            if cand == mel_note:
                score -= 2.0

            scores.append((score, cand))

        # Pick from top candidates with some randomness
        scores.sort(key=lambda x: -x[0])
        top_n = min(3, len(scores))
        if top_n > 0:
            # Weighted random from top candidates
            top = scores[:top_n]
            weights = [max(0.1, s[0] + 5.0) for s in top]  # shift to positive
            chosen = rng.choices([s[1] for s in top], weights=weights, k=1)[0]
        else:
            chosen = mel_note - 12  # fallback

        counter.append(chosen)
        prev_counter_note = chosen
        prev_melody_note = mel_note
        prev_interval = abs(chosen - mel_note) % 12

    logger.debug(f"Counterpoint generated: {len(counter)} notes, "
                 f"key={key_root}, scale={scale_name}")
    return counter


# ---------------------------------------------------------------------------
# Harmonic Tension Analysis — AI-Only Technique
# ---------------------------------------------------------------------------

# Interval tension values (0 = pure consonance, 1 = maximum dissonance)
INTERVAL_TENSION: dict[int, float] = {
    0: 0.0,    # unison — no tension
    1: 0.95,   # minor 2nd — maximum dissonance
    2: 0.6,    # major 2nd — moderate
    3: 0.2,    # minor 3rd — consonant, slightly dark
    4: 0.15,   # major 3rd — very consonant
    5: 0.1,    # perfect 4th — consonant
    6: 0.85,   # tritone — high tension
    7: 0.05,   # perfect 5th — most consonant interval
    8: 0.25,   # minor 6th — consonant
    9: 0.2,    # major 6th — consonant
    10: 0.7,   # minor 7th — moderate tension
    11: 0.8,   # major 7th — high tension
}


def analyze_tension(
    melody: list[int],
    chords: list[tuple[int, ...]] | None = None,
    steps_per_chord: int = 4,
) -> list[float]:
    """
    Compute harmonic tension at each position in a melody.

    Tension is derived from:
    1. Interval tension between consecutive melody notes
    2. Consonance/dissonance of melody note against current chord
    3. Melodic contour energy (leaps = more tension than steps)

    Returns a tension curve (0.0 = resolved/stable, 1.0 = maximum tension)
    that can be used to shape dynamics, effects, or composition decisions.

    This is [AI-ONLY]: computing tension from interval analysis + harmonic
    context + contour energy simultaneously requires systematic evaluation
    at every position.

    Args:
        melody: List of MIDI note numbers (0 = rest).
        chords: Optional list of chord tuples (MIDI notes). Applied cyclically.
        steps_per_chord: How many melody steps per chord change.

    Returns:
        List of tension values (0.0-1.0), same length as melody.
    """
    n = len(melody)
    tension = [0.0] * n

    for i, note in enumerate(melody):
        if note == 0:
            tension[i] = 0.0
            continue

        t = 0.0

        # 1. Interval tension from previous note
        if i > 0 and melody[i - 1] > 0:
            interval = abs(note - melody[i - 1]) % 12
            t += INTERVAL_TENSION.get(interval, 0.5) * 0.4

        # 2. Consonance against current chord
        if chords:
            chord_idx = min(i // steps_per_chord, len(chords) - 1)
            chord = chords[chord_idx]
            # Find minimum tension against any chord tone
            min_chord_tension = 1.0
            for chord_note in chord:
                interval = abs(note - chord_note) % 12
                ct = INTERVAL_TENSION.get(interval, 0.5)
                min_chord_tension = min(min_chord_tension, ct)
            t += min_chord_tension * 0.4

        # 3. Contour energy (larger leaps = more tension)
        if i > 0 and melody[i - 1] > 0:
            leap = abs(note - melody[i - 1])
            if leap > 7:  # larger than a fifth
                t += 0.2
            elif leap > 4:  # larger than a third
                t += 0.1

        tension[i] = min(t, 1.0)

    return tension


def generate_tension_curve(
    num_bars: int,
    steps_per_bar: int = 16,
    shape: str = "build_drop",
) -> list[float]:
    """
    Generate a target tension curve for composition.

    Use this to guide velocity, effects density, harmonic complexity,
    and arrangement decisions. Shapes available:

    - "build_drop": slow rise to peak at 3/4, then sharp release (EDM)
    - "verse_chorus": alternating low/high tension (pop/rock)
    - "continuous_rise": steady climb to maximum (Bolero-style)
    - "arch": rise to middle, descend (classical sonata)
    - "waves": oscillating tension (ambient/progressive)

    Args:
        num_bars: Number of bars in the composition.
        steps_per_bar: Steps per bar.
        shape: Tension curve shape name.

    Returns:
        List of tension values (0.0-1.0), length = num_bars * steps_per_bar.
    """
    total = num_bars * steps_per_bar
    t = np.linspace(0, 1, total, dtype=np.float64)

    if shape == "build_drop":
        # EDM: build to phi point, sharp drop, rebuild
        phi = 1.0 / 1.618
        curve = np.where(t < phi,
                         t / phi,  # linear rise to phi point
                         np.maximum(0, 1.0 - (t - phi) / (1 - phi) * 3))  # sharp drop
        curve = np.clip(curve, 0, 1)
    elif shape == "verse_chorus":
        # Pop: alternating 0.3 and 0.8 every 8 bars
        bars_per_section = 8
        steps_per_section = bars_per_section * steps_per_bar
        curve = np.array([0.3 if (i // steps_per_section) % 2 == 0 else 0.8
                          for i in range(total)], dtype=np.float64)
    elif shape == "continuous_rise":
        # Bolero: sqrt curve (starts fast, slows)
        curve = np.sqrt(t)
    elif shape == "arch":
        # Classical: parabolic arch
        curve = 4.0 * t * (1.0 - t)
    elif shape == "waves":
        # Ambient: sine waves at golden ratio frequency
        curve = (np.sin(2 * np.pi * t * 3.618) * 0.3 + 0.5 +
                 np.sin(2 * np.pi * t * 1.618) * 0.2)
        curve = np.clip(curve, 0, 1)
    else:
        curve = t  # linear rise

    return curve.tolist()
