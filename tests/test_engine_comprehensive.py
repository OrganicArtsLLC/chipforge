#!/usr/bin/env python3
"""
ChipForge Comprehensive Engine Test Suite
==========================================
Regression tests for every module. Run on every commit to catch breakage.

Usage:
    .venv/bin/python3 tests/test_engine_comprehensive.py
    .venv/bin/python3 -m pytest tests/  (if pytest installed)

Coverage:
    - synth.py: all waveform generators, filters, ADSR, modulation
    - instruments.py: all 146 presets render without error
    - mixer.py: pattern/song rendering, effects pipeline, panning
    - effects.py: all 20 effects produce valid output
    - theory.py: scales, chords, melody gen, counterpoint, tension
    - sequencer.py: data model integrity
    - export.py: WAV export roundtrip
    - catalog.py: scan and search
    - web_compiler.py: JS compilation
"""

import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.synth import (
    SAMPLE_RATE, synthesize_note, note_to_freq, generate_sine, generate_square,
    generate_sawtooth, generate_triangle, generate_lfsr_noise, generate_wavetable,
    generate_additive, generate_supersaw, generate_fm, generate_karplus_strong,
    generate_ring_mod, generate_granular, generate_pwm, generate_vocal,
    generate_vocal_choir, generate_vocal_chop, generate_power_chord,
    generate_guitar_lead, generate_guitar_trem, generate_additive_shaped,
    spectral_morph, apply_lowpass, apply_filter_sweep, apply_portamento,
    apply_harmonic_drift, ADSR, HARMONIC_PROFILES, SHAPED_PROFILES,
)
from src.instruments import PRESETS
from src.effects import (
    apply_compressor, apply_sidechain, apply_distortion, apply_parametric_eq,
    apply_stereo_widener, apply_master_bus, apply_multiband_compress,
    apply_phaser, apply_flanger, apply_transient_shaper, apply_tape_saturation,
    apply_gate, apply_amp_sim, auto_master, analyze_mix,
    MasterBusConfig, EQBand, GENRE_PROFILES,
)
from src.theory import (
    note_name_to_midi, midi_to_note_name, get_scale_notes, get_chord,
    build_chord_progression, generate_melody, generate_counterpoint,
    analyze_tension, generate_tension_curve, SCALES, CHORD_TYPES,
)
from src.sequencer import Song, Pattern, NoteEvent
from src.export import export_wav, audio_to_wav_bytes

PASS = 0
FAIL = 0
ERRORS = []


def test(name, condition, detail=""):
    global PASS, FAIL, ERRORS
    if condition:
        PASS += 1
    else:
        FAIL += 1
        ERRORS.append(f"{name}: {detail}")
        print(f"  FAIL: {name} — {detail}")


def valid_audio(arr, label=""):
    """Check audio array is valid: no NaN, no Inf, finite peak."""
    if len(arr) == 0:
        return False
    if np.any(np.isnan(arr)):
        return False
    if np.any(np.isinf(arr)):
        return False
    return True


# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("  ChipForge Comprehensive Test Suite")
print("=" * 60)
t_start = time.time()

# ─── SYNTH: Waveform Generators ──────────────────────────────
print("\n── Waveform Generators ──")
for name, fn, args in [
    ("sine", generate_sine, (440, 4410)),
    ("square", generate_square, (440, 4410)),
    ("sawtooth", generate_sawtooth, (440, 4410)),
    ("triangle", generate_triangle, (440, 4410)),
    ("lfsr_noise_7", generate_lfsr_noise, (4410, True)),
    ("lfsr_noise_15", generate_lfsr_noise, (4410, False)),
    ("additive", generate_additive, (440, 4410)),
    ("supersaw", generate_supersaw, (440, 4410)),
    ("fm", generate_fm, (440, 4410)),
    ("karplus", generate_karplus_strong, (440, 4410)),
    ("ring_mod", generate_ring_mod, (440, 4410)),
    ("granular", generate_granular, (440, 4410)),
    ("pwm", generate_pwm, (440, 4410)),
    ("vocal", generate_vocal, (440, 4410)),
    ("vocal_choir", generate_vocal_choir, (220, 8820)),
    ("vocal_chop", generate_vocal_chop, (440, 4410)),
    ("power_chord", generate_power_chord, (82, 4410)),
    ("guitar_lead", generate_guitar_lead, (440, 4410)),
    ("guitar_trem", generate_guitar_trem, (440, 4410)),
]:
    try:
        result = fn(*args)
        test(f"gen_{name}", valid_audio(result) and len(result) > 0,
             f"len={len(result)}, valid={valid_audio(result)}")
    except Exception as e:
        test(f"gen_{name}", False, str(e))

# Shaped profiles
for profile in SHAPED_PROFILES:
    p = SHAPED_PROFILES[profile]
    result = generate_additive_shaped(440, 4410, p["amplitudes"], p["envelopes"])
    test(f"shaped_{profile}", valid_audio(result))

# Spectral morph
saw = generate_sawtooth(440, 4410)
sine = generate_sine(440, 4410)
morphed = spectral_morph(saw, sine, 0.5)
test("spectral_morph", valid_audio(morphed) and len(morphed) == 4410)

# ─── SYNTH: Filters & Modulation ─────────────────────────────
print("\n── Filters & Modulation ──")
test_buf = generate_sawtooth(440, 4410)
lp = apply_lowpass(test_buf, 1000.0, 0.3)
test("lowpass", valid_audio(lp))

sweep = apply_filter_sweep(test_buf, 4000, 400, 0.3)
test("filter_sweep", valid_audio(sweep))

port = apply_portamento(test_buf, 220, 440, 0.1)
test("portamento", valid_audio(port))

drift = apply_harmonic_drift(test_buf, 3.0, 0.5)
test("harmonic_drift", valid_audio(drift))

# ADSR
adsr = ADSR(0.01, 0.05, 0.5, 0.1)
env = adsr.apply(test_buf)
test("adsr_apply", valid_audio(env) and np.max(np.abs(env)) <= np.max(np.abs(test_buf)) * 1.01)

# ─── INSTRUMENTS: All Presets ─────────────────────────────────
print(f"\n── Instrument Presets ({len(PRESETS)}) ──")
preset_failures = []
for name, inst in PRESETS.items():
    try:
        note = synthesize_note(60, 0.3, waveform=inst.waveform, adsr=inst.adsr, volume=inst.volume)
        if not valid_audio(note) or len(note) == 0:
            preset_failures.append(name)
    except Exception as e:
        preset_failures.append(f"{name}: {e}")
test(f"all_{len(PRESETS)}_presets", len(preset_failures) == 0,
     f"failures: {preset_failures[:5]}")

# ─── EFFECTS: All Effects ────────────────────────────────────
print("\n── Effects ──")
mono = np.random.randn(4410).astype(np.float32) * 0.3
stereo = np.stack([mono, mono], axis=1)

for name, fn, args in [
    ("compressor", apply_compressor, (mono,)),
    ("sidechain", apply_sidechain, (mono, mono)),
    ("distortion_soft", apply_distortion, (mono, 0.5, "soft")),
    ("distortion_hard", apply_distortion, (mono, 0.5, "hard")),
    ("distortion_foldback", apply_distortion, (mono, 0.5, "foldback")),
    ("multiband", apply_multiband_compress, (mono,)),
    ("phaser", apply_phaser, (mono,)),
    ("flanger", apply_flanger, (mono,)),
    ("transient", apply_transient_shaper, (mono,)),
    ("tape_sat", apply_tape_saturation, (mono,)),
    ("gate", apply_gate, (mono,)),
    ("amp_sim_metal", apply_amp_sim, (mono, 0.8, "metal")),
    ("amp_sim_clean", apply_amp_sim, (mono, 0.3, "clean")),
    ("stereo_widen", apply_stereo_widener, (stereo, 1.3)),
]:
    try:
        result = fn(*args)
        test(f"fx_{name}", valid_audio(result))
    except Exception as e:
        test(f"fx_{name}", False, str(e))

# EQ
eq_bands = [EQBand(1000.0, 3.0, 1.0, "peak")]
eq_result = apply_parametric_eq(mono, eq_bands)
test("fx_parametric_eq", valid_audio(eq_result))

# Master bus
mb_result = apply_master_bus(stereo.copy(), MasterBusConfig())
test("fx_master_bus", valid_audio(mb_result))

# Auto-master (all genres)
for genre in GENRE_PROFILES:
    result = auto_master(stereo.copy(), genre=genre)
    test(f"auto_master_{genre}", valid_audio(result))

# Mix analysis
metrics = analyze_mix(stereo)
test("analyze_mix", "peak_db" in metrics and "spectral_centroid_hz" in metrics)

# ─── THEORY: Scales, Chords, Melody ──────────────────────────
print("\n── Music Theory ──")
test("note_to_midi", note_name_to_midi("C", 4) == 60)
test("midi_to_note", midi_to_note_name(60) == "C4")
test("scales_exist", len(SCALES) >= 12)
test("chord_types", len(CHORD_TYPES) >= 11)

scale = get_scale_notes(60, "natural_minor")
test("get_scale", len(scale) > 0 and 60 in scale)

chord = get_chord(60, "major")
test("get_chord", chord == [60, 64, 67])

melody = generate_melody(60, "pentatonic_minor", num_steps=16)
test("generate_melody", len(melody) == 16)

counter = generate_counterpoint([60, 64, 67, 72, 67, 64, 60, 62])
test("counterpoint", len(counter) == 8 and all(isinstance(n, int) for n in counter))

tension = analyze_tension([60, 64, 67, 72])
test("tension_analysis", len(tension) == 4 and all(0 <= t <= 1 for t in tension))

for shape in ["build_drop", "verse_chorus", "continuous_rise", "arch", "waves"]:
    tc = generate_tension_curve(8, shape=shape)
    test(f"tension_curve_{shape}", len(tc) == 128 and all(0 <= v <= 1.01 for v in tc))

# ─── SEQUENCER: Data Model ───────────────────────────────────
print("\n── Sequencer ──")
ne = NoteEvent(midi_note=60, velocity=0.8, duration_steps=4, instrument="sine_pad")
test("note_event", ne.midi_note == 60 and ne.velocity == 0.8)

grid = [[None] * 16 for _ in range(4)]
grid[0][0] = ne
p = Pattern(name="test", num_steps=16, num_channels=4, bpm=120, grid=grid)
test("pattern_create", p.num_steps == 16 and p.num_channels == 4)
test("pattern_duration", abs(p.total_duration_sec() - 2.0) < 0.01)

s = Song(title="Test", bpm=120, patterns=[p], sequence=[0])
test("song_create", s.title == "Test" and len(s.patterns) == 1)

# Serialization roundtrip
d = p.to_dict()
p2 = Pattern.from_dict(d)
test("pattern_serialize", p2.num_steps == 16 and p2.grid[0][0].midi_note == 60)

# ─── MIXER: Rendering ────────────────────────────────────────
print("\n── Mixer ──")
from src.mixer import render_pattern, render_song

audio = render_pattern(p)
test("render_pattern", valid_audio(audio) and audio.shape[1] == 2)

song_audio = render_song(s)
test("render_song", valid_audio(song_audio) and song_audio.shape[1] == 2)

# With effects
s_fx = Song(title="FX", bpm=120, patterns=[p], sequence=[0],
            panning={0: 0.0, 1: 0.3, 2: -0.3, 3: 0.0},
            channel_effects={0: {"reverb": 0.3}, 1: {"delay": 0.2}},
            master_reverb=0.1)
fx_audio = render_song(s_fx, panning=s_fx.panning,
                       channel_effects=s_fx.channel_effects,
                       master_reverb=s_fx.master_reverb)
test("render_with_effects", valid_audio(fx_audio))

# ─── EXPORT ──────────────────────────────────────────────────
print("\n── Export ──")
wav_bytes = audio_to_wav_bytes(song_audio)
test("wav_bytes", len(wav_bytes) > 44)  # WAV header is 44 bytes

import tempfile
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    export_wav(song_audio, f.name)
    test("export_wav", os.path.getsize(f.name) > 44)
    os.unlink(f.name)

# ─── CATALOG ─────────────────────────────────────────────────
print("\n── Catalog ──")
from src.catalog import scan_songs_directory, Catalog
catalog = scan_songs_directory()
test("catalog_scan", len(catalog.songs) > 100)
edm = catalog.find(genre="edm")
test("catalog_filter", len(edm) > 30)
v4 = catalog.find(version="v4")
test("catalog_version_filter", len(v4) > 0)

# ─── WEB COMPILER ────────────────────────────────────────────
print("\n── Web Compiler ──")
from src.web_compiler import compile_to_js
js = compile_to_js(s, minify=True)
test("web_compile", len(js) > 100 and "AudioContext" in js)
js_readable = compile_to_js(s, minify=False)
test("web_compile_readable", len(js_readable) > len(js))

# ─── PERFORMANCE ─────────────────────────────────────────────
print("\n── Performance ──")
t0 = time.time()
for _ in range(100):
    synthesize_note(60, 0.1, waveform="sawtooth")
synth_time = (time.time() - t0) / 100
test(f"synth_speed ({synth_time*1000:.1f}ms/note)", synth_time < 0.1)

t0 = time.time()
for _ in range(10):
    render_song(s)
render_time = (time.time() - t0) / 10
test(f"render_speed ({render_time*1000:.0f}ms/song)", render_time < 2.0)

# ═══════════════════════════════════════════════════════════════
total_time = time.time() - t_start
print("\n" + "=" * 60)
print(f"  Results: {PASS} passed, {FAIL} failed ({total_time:.1f}s)")
if ERRORS:
    print(f"  Failures:")
    for e in ERRORS:
        print(f"    - {e}")
print(f"  Engine: {len(PRESETS)} presets, {len(SCALES)} scales, {len(GENRE_PROFILES)} genres")
print("=" * 60)

sys.exit(1 if FAIL > 0 else 0)
