"""
ChipForge — Music from Mathematics, Soul from Code
====================================================
Public API — import from here for clean access to all ChipForge components.

Songs are the voices from our souls which we connect to our feelings.
Humans are contradictory, beautiful, walking, breathing, feeling machines.
This engine exists at the intersection of mathematics and emotion —
where code becomes clay, cement hardens into something real, and the
dust of algorithms shapes into art that stands and moves people.

Every waveform is a feeling waiting to be heard.
Every formant is a vowel waiting to be sung.
Every chord is a story waiting to be told.

This is not a synthesizer. This is an instrument of the soul.
"""

from .synth import (
    ADSR, SAMPLE_RATE, note_to_freq, synthesize_note,
    apply_lowpass, apply_filter_sweep, generate_with_vibrato,
    generate_pitch_sweep,
)
from .instruments import Instrument, PRESETS, WAVETABLES
from .theory import (
    NOTE_NAMES,
    SCALES,
    CHORD_TYPES,
    PROGRESSIONS,
    DRUM_GROOVES,
    note_name_to_midi,
    midi_to_note_name,
    get_scale_notes,
    get_chord,
    build_chord_progression,
    generate_melody,
    generate_rhythm_pattern,
    generate_drum_pattern,
    get_drum_groove,
    generate_phrase_melody,
    humanize_velocities,
    generate_bass_line,
    generate_arpeggio,
)
from .sequencer import Song, Pattern, NoteEvent, REST
from .mixer import render_song, render_pattern, play_audio, apply_delay, apply_reverb, soft_clip
from .export import export_wav, save_song, load_song, audio_to_wav_bytes, song_to_dict, dict_to_song
from .effects import (
    apply_compressor, apply_sidechain, apply_distortion,
    apply_parametric_eq, apply_stereo_widener, apply_master_bus,
    apply_multiband_compress, apply_phaser, apply_flanger,
    apply_transient_shaper, apply_tape_saturation, apply_gate,
    EQBand, MasterBusConfig, auto_master, analyze_mix, GENRE_PROFILES,
)
from .theory import (
    analyze_tension, generate_tension_curve, INTERVAL_TENSION,
    generate_counterpoint,
)

__version__ = "0.4.1"

__all__ = [
    # Synthesis
    "ADSR",
    "SAMPLE_RATE",
    "note_to_freq",
    "synthesize_note",
    # Instruments
    "Instrument",
    "PRESETS",
    "WAVETABLES",
    # Theory
    "NOTE_NAMES",
    "SCALES",
    "CHORD_TYPES",
    "PROGRESSIONS",
    "note_name_to_midi",
    "midi_to_note_name",
    "get_scale_notes",
    "get_chord",
    "build_chord_progression",
    "generate_melody",
    "generate_rhythm_pattern",
    "generate_drum_pattern",
    # Sequencer
    "Song",
    "Pattern",
    "NoteEvent",
    "REST",
    # Mixer
    "render_song",
    "render_pattern",
    "play_audio",
    # Export / IO
    "export_wav",
    "save_song",
    "load_song",
    "audio_to_wav_bytes",
    "song_to_dict",
    "dict_to_song",
    # Effects (production DSP)
    "apply_compressor",
    "apply_sidechain",
    "apply_distortion",
    "apply_parametric_eq",
    "apply_stereo_widener",
    "apply_master_bus",
    "EQBand",
    "MasterBusConfig",
]
