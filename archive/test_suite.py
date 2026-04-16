"""
ChipForge Test Suite & Benchmark
=================================
Renders test cases at increasing complexity, measures performance and
audio quality, and tracks engine version across runs.

Usage:
    python test_suite.py               # Run all tests
    python test_suite.py --quick       # Skip long song renders (T08, T09)
    python test_suite.py --compare     # Show comparison with previous run

Output:
    output/test-suite/*.wav            # Rendered audio for each test
    output/test-suite/results.json     # Latest run results
    output/test-suite/history.jsonl    # Append-only run history
"""

import sys
import os
import time
import json
import math
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from dataclasses import dataclass, asdict

import numpy as np

from src.synth import (
    synthesize_note, SAMPLE_RATE, apply_lowpass, apply_filter_sweep,
    generate_lfsr_noise, _HAS_SCIPY,
)
from src.mixer import (
    render_song, render_pattern, apply_reverb, apply_delay,
    _HAS_SCIPY as _MIXER_HAS_SCIPY,
)
from src.sequencer import Song, Pattern, NoteEvent
from src.instruments import PRESETS
from src.export import export_wav
from src.version import __version__, get_build_id, get_version_string

OUT_DIR = Path("output/test-suite")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)


def note(inst: str, freq: float, vel: float = 0.80, dur: int = 2) -> NoteEvent:
    return NoteEvent(
        midi_note=freq_to_midi(freq),
        velocity=min(vel, 0.85),
        duration_steps=dur,
        instrument=inst,
    )


def make_stereo(mono: np.ndarray) -> np.ndarray:
    """Convert mono to stereo for export."""
    if mono.ndim == 1:
        return np.column_stack([mono, mono]).astype(np.float32)
    return mono


@dataclass
class TestResult:
    name: str
    audio_duration_sec: float
    render_time_sec: float
    realtime_ratio: float
    peak_amplitude: float
    rms_level: float
    clip_percent: float
    channels: int
    effects: str


def analyze_audio(audio: np.ndarray) -> dict:
    """Compute audio quality metrics."""
    if audio.ndim == 2:
        mono = audio.mean(axis=1)
    else:
        mono = audio
    return {
        "peak": float(np.max(np.abs(audio))),
        "rms": float(np.sqrt(np.mean(mono.astype(np.float64) ** 2))),
        "clip_pct": float(np.mean(np.abs(audio) > 0.95) * 100),
    }


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def t01_bare_note() -> tuple[str, np.ndarray, dict]:
    """T01: Single note, no filter, no effects — raw synthesis baseline."""
    audio = synthesize_note(
        midi_note=60, duration_sec=2.0,
        waveform="square", duty=0.5,
        adsr=PRESETS["pulse_lead"].adsr,
        volume=0.7,
    )
    return "T01_bare_note", make_stereo(audio), {"channels": 1, "effects": "none"}


def t02_filtered_note() -> tuple[str, np.ndarray, dict]:
    """T02: Single note with static lowpass filter — tests scipy biquad."""
    audio = synthesize_note(
        midi_note=60, duration_sec=2.0,
        waveform="sawtooth", volume=0.7,
    )
    audio = apply_lowpass(audio, cutoff_hz=2000.0, resonance=0.4)
    return "T02_filtered_note", make_stereo(audio), {"channels": 1, "effects": "lowpass"}


def t03_filter_sweep() -> tuple[str, np.ndarray, dict]:
    """T03: Single note with filter sweep 200->8000 Hz — tests chunked biquad."""
    audio = synthesize_note(
        midi_note=48, duration_sec=3.0,
        waveform="sawtooth", volume=0.7,
    )
    audio = apply_filter_sweep(audio, start_hz=200.0, end_hz=8000.0, resonance=0.5)
    return "T03_filter_sweep", make_stereo(audio), {"channels": 1, "effects": "filter_sweep"}


def t04_reverb_isolated() -> tuple[str, np.ndarray, dict]:
    """T04: Reverb on 3s of noise — pure reverb performance test."""
    audio = generate_lfsr_noise(SAMPLE_RATE * 3, short_mode=False).astype(np.float32) * 0.3
    audio = apply_reverb(audio, room_size=0.6, damping=0.4, mix=0.3)
    return "T04_reverb_isolated", make_stereo(audio), {"channels": 1, "effects": "reverb"}


def t05_4ch_dry() -> tuple[str, np.ndarray, dict]:
    """T05: 4-channel pattern, 32 steps, no effects — multi-channel baseline."""
    grid = [[None] * 32 for _ in range(4)]

    # Kick on beats
    for s in range(0, 32, 8):
        grid[0][s] = note("kick_deep", 55.0, 0.85, 2)
    # Snare on 2 and 4
    for s in [8, 24]:
        grid[1][s] = note("noise_snare", 200.0, 0.7, 2)
    # Bass line
    bass_notes = [65.41, 65.41, 82.41, 73.42]
    for i, s in enumerate(range(0, 32, 8)):
        grid[2][s] = note("bass_growl", bass_notes[i], 0.7, 4)
    # Lead melody
    melody = [261.63, 293.66, 329.63, 349.23, 392.0, 349.23, 329.63, 293.66]
    for i, s in enumerate(range(0, 32, 4)):
        grid[3][s] = note("saw_filtered", melody[i], 0.65, 2)

    pat = Pattern(num_steps=32, bpm=140, steps_per_beat=4, grid=grid)
    song = Song(
        patterns=[pat],
        sequence=[0],
        panning={0: 0.0, 1: 0.1, 2: -0.05, 3: 0.15},
    )
    audio = render_song(song, panning=song.panning)
    return "T05_4ch_dry", audio, {"channels": 4, "effects": "none"}


def t06_4ch_wet() -> tuple[str, np.ndarray, dict]:
    """T06: 4-channel pattern, 32 steps, reverb+delay — tests per-channel effects."""
    grid = [[None] * 32 for _ in range(4)]

    for s in range(0, 32, 8):
        grid[0][s] = note("kick_deep", 55.0, 0.85, 2)
    for s in [8, 24]:
        grid[1][s] = note("noise_clap", 200.0, 0.7, 3)
    bass_notes = [65.41, 65.41, 82.41, 73.42]
    for i, s in enumerate(range(0, 32, 8)):
        grid[2][s] = note("bass_growl", bass_notes[i], 0.7, 4)
    melody = [523.25, 587.33, 659.25, 698.46, 783.99, 698.46, 659.25, 587.33]
    for i, s in enumerate(range(0, 32, 4)):
        grid[3][s] = note("saw_filtered", melody[i], 0.65, 2)

    pat = Pattern(num_steps=32, bpm=140, steps_per_beat=4, grid=grid)
    ch_fx = {
        0: {"reverb": 0.06},
        1: {"reverb": 0.12},
        2: {"reverb": 0.08},
        3: {"reverb": 0.25, "delay": 0.20, "delay_feedback": 0.30},
    }
    song = Song(
        patterns=[pat],
        sequence=[0],
        panning={0: 0.0, 1: 0.1, 2: -0.05, 3: 0.15},
        channel_effects=ch_fx,
    )
    audio = render_song(song, panning=song.panning, channel_effects=ch_fx)
    return "T06_4ch_wet", audio, {"channels": 4, "effects": "reverb+delay"}


def t07_7ch_full() -> tuple[str, np.ndarray, dict]:
    """T07: 7-channel pattern, 32 steps, full effects chain — production test."""
    grid = [[None] * 32 for _ in range(7)]

    # Ch0: Kick
    for s in range(0, 32, 8):
        grid[0][s] = note("kick_deep", 50.0, 0.85, 2)
    # Ch1: Snare
    for s in [8, 24]:
        grid[1][s] = note("noise_clap", 250.0, 0.7, 3)
    # Ch2: Hats
    for s in range(0, 32, 2):
        grid[2][s] = note("hat_crisp", 8000.0, 0.4, 1)
    # Ch3: Bass
    bass = [55.0, 55.0, 73.42, 65.41]
    for i, s in enumerate(range(0, 32, 8)):
        grid[3][s] = note("bass_growl", bass[i], 0.75, 4)
    # Ch4: Lead
    lead = [440.0, 493.88, 523.25, 587.33, 659.25, 587.33, 523.25, 493.88]
    for i, s in enumerate(range(0, 32, 4)):
        grid[4][s] = note("saw_filtered", lead[i], 0.65, 2)
    # Ch5: Pad
    grid[5][0] = note("pad_lush", 261.63, 0.5, 16)
    grid[5][16] = note("pad_lush", 293.66, 0.5, 16)
    # Ch6: Arp
    arp = [523.25, 659.25, 783.99, 659.25] * 4
    for i, s in enumerate(range(0, 32, 2)):
        grid[6][s] = note("pulse_warm", arp[i], 0.5, 1)

    pat = Pattern(num_steps=32, bpm=140, steps_per_beat=4, grid=grid)
    ch_fx = {
        0: {"reverb": 0.06},
        1: {"reverb": 0.12},
        2: {"delay": 0.18, "delay_feedback": 0.25, "reverb": 0.08},
        3: {"reverb": 0.08},
        4: {"reverb": 0.28, "delay": 0.20, "delay_feedback": 0.30},
        5: {"reverb": 0.40},
        6: {"delay": 0.22, "delay_feedback": 0.35, "reverb": 0.10},
    }
    song = Song(
        patterns=[pat],
        sequence=[0],
        panning={0: 0.0, 1: 0.05, 2: 0.28, 3: -0.08, 4: 0.12, 5: -0.20, 6: -0.30},
        channel_effects=ch_fx,
    )
    audio = render_song(
        song, panning=song.panning, channel_effects=ch_fx, master_reverb=0.12,
    )
    return "T07_7ch_full", audio, {"channels": 7, "effects": "full(reverb+delay+master)"}


def t08_mini_song() -> tuple[str, np.ndarray, dict]:
    """T08: 8-pattern mini song, 7 channels — real composition test."""
    patterns = []

    for p_idx in range(8):
        grid = [[None] * 32 for _ in range(7)]

        # Kick (varies by pattern)
        if p_idx >= 2:
            for s in range(0, 32, 8):
                grid[0][s] = note("kick_deep", 50.0, 0.85, 2)
            if p_idx >= 4:
                grid[0][16] = note("kick_deep", 50.0, 0.75, 2)

        # Snare (enters at pattern 2)
        if p_idx >= 2:
            for s in [8, 24]:
                grid[1][s] = note("noise_clap", 250.0, 0.7, 3)

        # Hats
        step_interval = 4 if p_idx < 4 else 2
        for s in range(0, 32, step_interval):
            grid[2][s] = note("hat_crisp", 8000.0, 0.35, 1)

        # Bass (present in all patterns)
        root = [55.0, 55.0, 73.42, 65.41][p_idx % 4]
        for s in range(0, 32, 8):
            grid[3][s] = note("bass_growl", root, 0.7, 4)

        # Lead (varies per section)
        if p_idx >= 1:
            base = 440.0 * (1.0 + (p_idx % 4) * 0.05)
            for i, s in enumerate(range(0, 32, 4)):
                freq = base * (2 ** ((i % 5 - 2) / 12.0))
                grid[4][s] = note("saw_filtered", freq, 0.6, 2)

        # Pad (always present for warmth)
        pad_freq = [261.63, 293.66, 329.63, 349.23][p_idx % 4]
        grid[5][0] = note("pad_lush", pad_freq, 0.45, 16)
        grid[5][16] = note("pad_lush", pad_freq * 1.25, 0.45, 16)

        # Arp (enters at pattern 3)
        if p_idx >= 3:
            arp_base = pad_freq * 2
            for s in range(0, 32, 2):
                arp_freq = arp_base * (2 ** ([0, 4, 7, 12, 7, 4, 0, -5][s % 8] / 12.0))
                grid[6][s] = note("pulse_warm", arp_freq, 0.45, 1)

        patterns.append(Pattern(num_steps=32, bpm=140, steps_per_beat=4, grid=grid))

    ch_fx = {
        0: {"reverb": 0.06},
        1: {"reverb": 0.12},
        2: {"delay": 0.18, "delay_feedback": 0.25, "reverb": 0.08},
        3: {"reverb": 0.08},
        4: {"reverb": 0.28, "delay": 0.20, "delay_feedback": 0.30},
        5: {"reverb": 0.40},
        6: {"delay": 0.22, "delay_feedback": 0.35, "reverb": 0.10},
    }
    song = Song(
        patterns=patterns,
        sequence=list(range(8)),
        panning={0: 0.0, 1: 0.05, 2: 0.28, 3: -0.08, 4: 0.12, 5: -0.20, 6: -0.30},
        channel_effects=ch_fx,
        master_reverb=0.12,
    )
    audio = render_song(
        song, panning=song.panning, channel_effects=ch_fx,
        master_reverb=0.12,
    )
    return "T08_mini_song", audio, {"channels": 7, "effects": "full+master_reverb"}


def t09_stress() -> tuple[str, np.ndarray, dict]:
    """T09: 8 channels, 64 steps, 4 patterns, all effects — stress test."""
    patterns = []

    for p_idx in range(4):
        grid = [[None] * 64 for _ in range(8)]

        # Ch0: Heavy kick pattern
        for s in range(0, 64, 4):
            grid[0][s] = note("kick_punchy", 45.0, 0.85, 2)
        # Ch1: Layered snare
        for s in range(2, 64, 8):
            grid[1][s] = note("noise_clap", 300.0, 0.7, 3)
        # Ch2: 16th-note hats
        for s in range(0, 64):
            grid[2][s] = note("hat_crisp", 9000.0, 0.3, 1)
        # Ch3: Pulsing bass
        for s in range(0, 64, 4):
            root = 55.0 * (2 ** ([0, 0, 3, 5][p_idx] / 12.0))
            grid[3][s] = note("bass_growl", root, 0.7, 3)
        # Ch4: Lead melody (every pattern unique)
        for i, s in enumerate(range(0, 64, 2)):
            freq = 440.0 * (2 ** (((i + p_idx * 3) % 12 - 6) / 12.0))
            grid[4][s] = note("lead_bright", freq, 0.55, 2)
        # Ch5: Deep pad
        pad_f = 220.0 * (2 ** (p_idx * 2 / 12.0))
        grid[5][0] = note("pad_lush", pad_f, 0.4, 32)
        grid[5][32] = note("pad_lush", pad_f * 1.189, 0.4, 32)
        # Ch6: Fast arp
        for s in range(0, 64, 2):
            arp_f = 880.0 * (2 ** ([0, 3, 7, 12, 15, 12, 7, 3][s % 8] / 12.0))
            grid[6][s] = note("pulse_warm", arp_f, 0.4, 1)
        # Ch7: Counter melody (saw_dark)
        for s in range(0, 64, 4):
            cf = 330.0 * (2 ** (((s // 4 + p_idx) % 7 - 3) / 12.0))
            grid[7][s] = note("saw_dark", cf, 0.5, 3)

        patterns.append(Pattern(num_steps=64, bpm=145, steps_per_beat=4, grid=grid))

    ch_fx = {
        0: {"reverb": 0.06},
        1: {"reverb": 0.12},
        2: {"delay": 0.15, "delay_feedback": 0.20, "reverb": 0.08},
        3: {"reverb": 0.08},
        4: {"reverb": 0.30, "delay": 0.22, "delay_feedback": 0.35},
        5: {"reverb": 0.45},
        6: {"delay": 0.25, "delay_feedback": 0.40, "reverb": 0.12},
        7: {"reverb": 0.20, "delay": 0.18, "delay_feedback": 0.25},
    }
    song = Song(
        patterns=patterns,
        sequence=[0, 1, 2, 3],
        panning={0: 0.0, 1: 0.05, 2: 0.30, 3: -0.08, 4: 0.15, 5: -0.25, 6: -0.35, 7: 0.20},
        channel_effects=ch_fx,
        master_reverb=0.15,
    )
    audio = render_song(
        song, panning=song.panning, channel_effects=ch_fx,
        master_reverb=0.15,
    )
    return "T09_stress", audio, {"channels": 8, "effects": "full+master(stress)"}


# ---------------------------------------------------------------------------
# Effects-only tests (showcase new effects module)
# ---------------------------------------------------------------------------

def t10_effects_chain() -> tuple[str, np.ndarray, dict]:
    """T10: Effects chain — compressor + EQ + distortion on a note."""
    from src.effects import apply_compressor, apply_parametric_eq, apply_distortion, EQBand

    audio = synthesize_note(
        midi_note=48, duration_sec=3.0,
        waveform="sawtooth", volume=0.7,
    )
    # Filter
    audio = apply_lowpass(audio, cutoff_hz=3000.0, resonance=0.3)
    # Distortion (subtle warmth)
    audio = apply_distortion(audio, drive=0.15, mode="soft")
    # EQ: scoop mids, add presence
    eq_bands = [
        EQBand(freq_hz=400.0, gain_db=-3.0, q=1.0, band_type="peak"),
        EQBand(freq_hz=3500.0, gain_db=2.0, q=1.5, band_type="peak"),
        EQBand(freq_hz=80.0, gain_db=2.0, q=0.7, band_type="lowshelf"),
    ]
    audio = apply_parametric_eq(audio, eq_bands)
    # Compress
    audio = apply_compressor(audio, threshold_db=-10.0, ratio=3.0)
    # Reverb
    audio = apply_reverb(audio, room_size=0.5, damping=0.4, mix=0.25)

    return "T10_effects_chain", make_stereo(audio), {"channels": 1, "effects": "dist+eq+comp+reverb"}


def t11_master_bus() -> tuple[str, np.ndarray, dict]:
    """T11: Full master bus processing on a 7-channel pattern."""
    from src.effects import apply_master_bus, MasterBusConfig

    # Render a 7-channel pattern first
    _, audio_7ch, _ = t07_7ch_full()

    # Apply master bus
    config = MasterBusConfig(
        highpass_hz=35.0,
        low_shelf_db=1.5,
        presence_db=1.0,
        air_shelf_db=0.5,
        comp_threshold_db=-10.0,
        comp_ratio=2.5,
        stereo_width=1.3,
        analog_warmth=0.1,
        limiter_ceiling_db=-0.3,
    )
    mastered = apply_master_bus(audio_7ch, config)
    return "T11_master_bus", mastered, {"channels": 7, "effects": "master_bus(full)"}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

ALL_TESTS = [
    t01_bare_note,
    t02_filtered_note,
    t03_filter_sweep,
    t04_reverb_isolated,
    t05_4ch_dry,
    t06_4ch_wet,
    t07_7ch_full,
    t08_mini_song,
    t09_stress,
    t10_effects_chain,
    t11_master_bus,
]

QUICK_TESTS = ALL_TESTS[:7] + [ALL_TESTS[9], ALL_TESTS[10]]  # Skip T08, T09


def run_suite(tests: list, verbose: bool = True) -> list[dict]:
    """Run all tests, save WAVs, collect results."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for test_fn in tests:
        name = test_fn.__doc__.split(":")[0] if test_fn.__doc__ else test_fn.__name__
        if verbose:
            print(f"\n{'='*60}")
            print(f"  Running: {test_fn.__name__}")
            print(f"{'='*60}")

        t0 = time.perf_counter()
        test_name, audio, meta = test_fn()
        render_time = time.perf_counter() - t0

        # Save WAV
        wav_path = OUT_DIR / f"{test_name}.wav"
        export_wav(audio, wav_path)

        # Analyze
        metrics = analyze_audio(audio)
        audio_duration = len(audio) / SAMPLE_RATE

        result = TestResult(
            name=test_name,
            audio_duration_sec=round(audio_duration, 2),
            render_time_sec=round(render_time, 3),
            realtime_ratio=round(audio_duration / max(render_time, 0.001), 1),
            peak_amplitude=round(metrics["peak"], 4),
            rms_level=round(metrics["rms"], 4),
            clip_percent=round(metrics["clip_pct"], 2),
            channels=meta.get("channels", 1),
            effects=meta.get("effects", "none"),
        )
        results.append(asdict(result))

        if verbose:
            rt = result.realtime_ratio
            speed_tag = "FAST" if rt > 10 else ("OK" if rt > 1 else "SLOW")
            print(f"  {result.render_time_sec:7.3f}s render | "
                  f"{result.audio_duration_sec:5.1f}s audio | "
                  f"{rt:6.1f}x realtime [{speed_tag}] | "
                  f"peak={result.peak_amplitude:.3f} | "
                  f"rms={result.rms_level:.3f}")

    return results


def print_table(results: list[dict]) -> None:
    """Print ASCII summary table."""
    print(f"\n{'='*100}")
    print(f"  ChipForge Test Suite Results — {get_version_string()}")
    print(f"  scipy: {'YES' if _HAS_SCIPY else 'NO (Python fallback)'}")
    print(f"{'='*100}")
    print(f"{'Test':<22} {'Render':>8} {'Audio':>7} {'RT Ratio':>9} "
          f"{'Peak':>6} {'RMS':>6} {'Clip%':>6} {'Ch':>3} {'Effects'}")
    print(f"{'-'*22} {'-'*8} {'-'*7} {'-'*9} {'-'*6} {'-'*6} {'-'*6} {'-'*3} {'-'*20}")

    total_render = 0.0
    total_audio = 0.0

    for r in results:
        rt = r["realtime_ratio"]
        speed = "FAST" if rt > 10 else ("OK" if rt > 1 else "SLOW")
        print(f"{r['name']:<22} {r['render_time_sec']:>7.3f}s {r['audio_duration_sec']:>6.1f}s "
              f"{rt:>7.1f}x{speed:>3} "
              f"{r['peak_amplitude']:>5.3f} {r['rms_level']:>5.3f} {r['clip_percent']:>5.1f}% "
              f"{r['channels']:>3} {r['effects']}")
        total_render += r["render_time_sec"]
        total_audio += r["audio_duration_sec"]

    print(f"{'-'*22} {'-'*8} {'-'*7} {'-'*9} {'-'*6} {'-'*6} {'-'*6} {'-'*3} {'-'*20}")
    total_rt = total_audio / max(total_render, 0.001)
    print(f"{'TOTAL':<22} {total_render:>7.3f}s {total_audio:>6.1f}s "
          f"{total_rt:>7.1f}x     {'':>5} {'':>5} {'':>5}    {'':>3}")


def save_results(results: list[dict]) -> None:
    """Save results.json and append to history.jsonl."""
    run_data = {
        "version": __version__,
        "build_id": get_build_id(),
        "version_string": get_version_string(),
        "scipy_available": _HAS_SCIPY,
        "sample_rate": SAMPLE_RATE,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "results": results,
        "totals": {
            "render_time": round(sum(r["render_time_sec"] for r in results), 3),
            "audio_duration": round(sum(r["audio_duration_sec"] for r in results), 2),
        },
    }

    # Latest results
    results_path = OUT_DIR / "results.json"
    results_path.write_text(json.dumps(run_data, indent=2))

    # Append to history
    history_path = OUT_DIR / "history.jsonl"
    with history_path.open("a") as f:
        f.write(json.dumps(run_data) + "\n")

    print(f"\nResults saved: {results_path}")
    print(f"History appended: {history_path}")


def compare_with_previous(results: list[dict]) -> None:
    """Show comparison with last run from history."""
    history_path = OUT_DIR / "history.jsonl"
    if not history_path.exists():
        print("\nNo previous runs to compare with.")
        return

    lines = history_path.read_text().strip().split("\n")
    if len(lines) < 2:
        print("\nOnly one run in history, nothing to compare yet.")
        return

    # Second-to-last line is previous run
    prev = json.loads(lines[-2])
    prev_results = {r["name"]: r for r in prev["results"]}

    print(f"\n{'='*80}")
    print(f"  Comparison: {prev['version_string']} -> {get_version_string()}")
    print(f"{'='*80}")
    print(f"{'Test':<22} {'Prev':>8} {'Now':>8} {'Change':>10} {'Speedup':>8}")
    print(f"{'-'*22} {'-'*8} {'-'*8} {'-'*10} {'-'*8}")

    for r in results:
        name = r["name"]
        if name in prev_results:
            prev_time = prev_results[name]["render_time_sec"]
            curr_time = r["render_time_sec"]
            diff = curr_time - prev_time
            speedup = prev_time / max(curr_time, 0.001)
            sign = "+" if diff > 0 else ""
            arrow = "FASTER" if speedup > 1.1 else ("SLOWER" if speedup < 0.9 else "~same")
            print(f"{name:<22} {prev_time:>7.3f}s {curr_time:>7.3f}s "
                  f"{sign}{diff:>8.3f}s {speedup:>6.1f}x {arrow}")
        else:
            print(f"{name:<22} {'N/A':>8} {r['render_time_sec']:>7.3f}s {'new':>10} {'---':>8}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="ChipForge Test Suite & Benchmark")
    parser.add_argument("--quick", action="store_true", help="Skip long renders (T08, T09)")
    parser.add_argument("--compare", action="store_true", help="Compare with previous run")
    args = parser.parse_args()

    print(f"\n{'#'*60}")
    print(f"  ChipForge Test Suite")
    print(f"  {get_version_string()}")
    print(f"  scipy: {'YES' if _HAS_SCIPY else 'NO (Python fallback — expect slower renders)'}")
    print(f"{'#'*60}")

    tests = QUICK_TESTS if args.quick else ALL_TESTS
    results = run_suite(tests)
    print_table(results)
    save_results(results)

    if args.compare:
        compare_with_previous(results)

    print(f"\nWAV files: {OUT_DIR}/")
    print(f"Done.\n")


if __name__ == "__main__":
    main()
