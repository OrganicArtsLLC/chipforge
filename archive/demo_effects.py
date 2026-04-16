"""
ADR-005 Effect Demos
=====================
Standalone demonstrations of production-grade DSP effects described in
ADR-005: The Future of Sound. Each demo generates a short WAV file in
output/demos/ showcasing one effect applied to a ChipForge synthesized source.

Run:
    .venv/bin/python3 demo_effects.py

Generates:
    output/demos/01_distortion_modes.wav      — 5 distortion flavors on a saw lead
    output/demos/02_sidechain_pump.wav         — EDM kick-ducking on a pad
    output/demos/03_stereo_widener.wav         — mono → narrow → normal → wide → ultra
    output/demos/04_bitcrush_sweep.wav         — 16-bit down to 2-bit in real time
    output/demos/05_master_bus_ab.wav          — same mix with and without master processing
    output/demos/06_flanger.wav               — jet-sweep flanger on an arpeggio
"""
import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from pathlib import Path
from src.synth import synthesize_note, SAMPLE_RATE
from src.export import export_wav

OUTPUT_DIR = Path("output/demos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# DSP Primitives (prototypes of what ADR-005 proposes)
# ============================================================================

def make_stereo(mono: np.ndarray) -> np.ndarray:
    """Convert mono to stereo."""
    return np.column_stack([mono, mono])


def generate_tone(freq: float, duration_sec: float, waveform: str = "sawtooth",
                  instrument: str = "saw_filtered") -> np.ndarray:
    """Generate a mono tone using ChipForge's synthesizer."""
    from src.instruments import PRESETS
    preset = PRESETS[instrument]
    midi_note = round(12 * math.log2(freq / 440.0) + 69) if freq > 0 else 0
    return synthesize_note(
        midi_note=midi_note,
        duration_sec=duration_sec,
        volume=0.75,
        waveform=preset.waveform,
        adsr=preset.adsr,
        duty=preset.duty,
        filter_cutoff=preset.filter_cutoff,
        filter_resonance=preset.filter_resonance,
    )


# ---------------------------------------------------------------------------
# Distortion
# ---------------------------------------------------------------------------

def apply_distortion(audio: np.ndarray, drive: float = 0.5,
                     mode: str = "soft") -> np.ndarray:
    """Waveshaping distortion with multiple modes."""
    if mode == "soft":
        driven = audio * (1.0 + drive * 10.0)
        return np.tanh(driven) * 0.9
    elif mode == "hard":
        driven = audio * (1.0 + drive * 10.0)
        return np.clip(driven, -1.0, 1.0)
    elif mode == "foldback":
        driven = audio * (1.0 + drive * 5.0)
        return 4.0 * (np.abs(0.25 * driven + 0.25 -
                       np.round(0.25 * driven + 0.25)) - 0.25)
    elif mode == "bitcrush":
        bits = max(2, int(16 - drive * 14))
        levels = 2 ** bits
        return np.round(audio * levels) / levels
    elif mode == "rectify":
        return np.abs(audio)
    return audio


# ---------------------------------------------------------------------------
# Sidechain Compressor
# ---------------------------------------------------------------------------

def apply_sidechain(audio: np.ndarray, sidechain_signal: np.ndarray,
                    threshold: float = 0.1, ratio: float = 8.0,
                    attack_ms: float = 1.0, release_ms: float = 100.0) -> np.ndarray:
    """Duck audio based on sidechain signal amplitude (EDM pump effect)."""
    n = len(audio)
    sc = np.abs(sidechain_signal[:n]) if len(sidechain_signal) >= n else np.pad(
        np.abs(sidechain_signal), (0, n - len(sidechain_signal)))

    attack_coeff = np.exp(-1.0 / (attack_ms * SAMPLE_RATE / 1000.0))
    release_coeff = np.exp(-1.0 / (release_ms * SAMPLE_RATE / 1000.0))

    envelope = np.zeros(n, dtype=np.float32)
    env = 0.0
    for i in range(n):
        if sc[i] > env:
            env = attack_coeff * env + (1 - attack_coeff) * sc[i]
        else:
            env = release_coeff * env + (1 - release_coeff) * sc[i]
        envelope[i] = env

    gain_reduction = np.ones(n, dtype=np.float32)
    above = envelope > threshold
    gain_reduction[above] = (threshold / envelope[above]) ** (1.0 - 1.0 / ratio)

    return audio * gain_reduction


# ---------------------------------------------------------------------------
# Stereo Widener (Mid/Side)
# ---------------------------------------------------------------------------

def apply_stereo_widener(stereo: np.ndarray, width: float = 1.0) -> np.ndarray:
    """Adjust stereo width. 0=mono, 1=unchanged, 2=extra wide."""
    mid = (stereo[:, 0] + stereo[:, 1]) * 0.5
    side = (stereo[:, 0] - stereo[:, 1]) * 0.5
    side *= width
    result = np.column_stack([mid + side, mid - side])
    return np.clip(result, -1.0, 1.0)


# ---------------------------------------------------------------------------
# Flanger
# ---------------------------------------------------------------------------

def apply_flanger(audio: np.ndarray, rate: float = 0.25, depth: float = 0.7,
                  feedback: float = 0.5, min_delay_ms: float = 0.1,
                  max_delay_ms: float = 5.0, mix: float = 0.5) -> np.ndarray:
    """LFO-modulated short delay (flanger / jet sweep)."""
    n = len(audio)
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    lfo = 0.5 * (1.0 + np.sin(2.0 * np.pi * rate * t))
    delay_samples = (min_delay_ms + depth * lfo * (max_delay_ms - min_delay_ms)) * SAMPLE_RATE / 1000.0

    output = np.zeros(n, dtype=np.float32)
    buf = np.zeros(n, dtype=np.float32)
    buf[:] = audio

    for i in range(n):
        d = delay_samples[i]
        idx = i - d
        if idx >= 1:
            lo = int(idx)
            frac = idx - lo
            if lo < n and lo - 1 >= 0:
                delayed = buf[lo] * (1 - frac) + buf[lo - 1] * frac
            else:
                delayed = 0.0
        else:
            delayed = 0.0
        output[i] = audio[i] + mix * delayed
        if i + 1 < n:
            fb_idx = i - d
            if fb_idx >= 1:
                lo = int(fb_idx)
                frac = fb_idx - lo
                if lo < n and lo - 1 >= 0:
                    buf[i] = audio[i] + feedback * (buf[lo] * (1 - frac) + buf[lo - 1] * frac)

    peak = np.max(np.abs(output))
    if peak > 1.0:
        output /= peak
    return output


# ---------------------------------------------------------------------------
# Simple Compressor
# ---------------------------------------------------------------------------

def apply_compressor(audio: np.ndarray, threshold_db: float = -12.0,
                     ratio: float = 4.0, attack_ms: float = 5.0,
                     release_ms: float = 50.0,
                     makeup_db: float = 0.0) -> np.ndarray:
    """RMS-based compressor with attack/release envelope."""
    threshold = 10.0 ** (threshold_db / 20.0)
    makeup = 10.0 ** (makeup_db / 20.0)
    attack_coeff = np.exp(-1.0 / (attack_ms * SAMPLE_RATE / 1000.0))
    release_coeff = np.exp(-1.0 / (release_ms * SAMPLE_RATE / 1000.0))

    n = len(audio)
    envelope = np.zeros(n, dtype=np.float32)
    env = 0.0
    rect = np.abs(audio)
    for i in range(n):
        if rect[i] > env:
            env = attack_coeff * env + (1 - attack_coeff) * rect[i]
        else:
            env = release_coeff * env + (1 - release_coeff) * rect[i]
        envelope[i] = env

    gain = np.ones(n, dtype=np.float32)
    above = envelope > threshold
    gain[above] = (threshold / envelope[above]) ** (1.0 - 1.0 / ratio)

    return audio * gain * makeup


# ---------------------------------------------------------------------------
# Simple EQ (high-pass via 1st order)
# ---------------------------------------------------------------------------

def apply_highpass(audio: np.ndarray, cutoff_hz: float = 30.0) -> np.ndarray:
    """Simple 1st-order high-pass filter."""
    rc = 1.0 / (2.0 * np.pi * cutoff_hz)
    alpha = rc / (rc + 1.0 / SAMPLE_RATE)
    output = np.zeros_like(audio)
    output[0] = audio[0]
    for i in range(1, len(audio)):
        output[i] = alpha * (output[i - 1] + audio[i] - audio[i - 1])
    return output


# ---------------------------------------------------------------------------
# Analog Warmth (subtle saturation + high-freq rolloff)
# ---------------------------------------------------------------------------

def apply_warmth(audio: np.ndarray, amount: float = 0.3) -> np.ndarray:
    """Subtle analog-style warmth: even-harmonic saturation."""
    driven = audio * (1.0 + amount * 3.0)
    warm = np.tanh(driven) * 0.95
    return warm


# ============================================================================
# Demo 1: Distortion Modes
# ============================================================================

def demo_distortion():
    """5 distortion flavors on the same C4 saw note, 1 second each."""
    print("  Demo 1: Distortion modes...")
    source = generate_tone(261.63, 1.0, instrument="saw_filtered")
    modes = ["soft", "hard", "foldback", "bitcrush", "rectify"]
    segments = []
    silence = np.zeros(int(SAMPLE_RATE * 0.3), dtype=np.float32)

    for mode in modes:
        dist = apply_distortion(source[:len(source)], drive=0.5, mode=mode)
        segments.append(dist)
        segments.append(silence)

    mono = np.concatenate(segments)
    stereo = make_stereo(mono * 0.7)
    path = OUTPUT_DIR / "01_distortion_modes.wav"
    export_wav(stereo, path)
    print(f"    → {path} ({len(mono)/SAMPLE_RATE:.1f}s)")


# ============================================================================
# Demo 2: Sidechain Pump
# ============================================================================

def demo_sidechain():
    """Pad note ducked by a kick drum pattern — classic EDM pump."""
    print("  Demo 2: Sidechain pump...")
    duration = 4.0
    n = int(SAMPLE_RATE * duration)

    # Generate a sustained pad
    pad = generate_tone(261.63, duration, instrument="pad_lush")
    if len(pad) < n:
        pad = np.pad(pad, (0, n - len(pad)))
    else:
        pad = pad[:n]

    # Generate kick trigger signal (short burst every beat at 130 BPM)
    bpm = 130
    beat_samples = int(SAMPLE_RATE * 60.0 / bpm)
    kick_trigger = np.zeros(n, dtype=np.float32)
    kick_dur = int(SAMPLE_RATE * 0.05)  # 50ms burst
    for beat in range(int(duration * bpm / 60)):
        start = beat * beat_samples
        end = min(start + kick_dur, n)
        if start < n:
            kick_trigger[start:end] = 1.0

    # Apply sidechain
    pumped = apply_sidechain(pad, kick_trigger, threshold=0.05, ratio=10.0,
                             attack_ms=1.0, release_ms=150.0)

    # A/B: first 2 seconds dry, next 2 seconds pumped
    output = np.zeros(n, dtype=np.float32)
    half = n // 2
    output[:half] = pad[:half] * 0.7
    output[half:] = pumped[half:] * 0.7

    stereo = make_stereo(output)
    path = OUTPUT_DIR / "02_sidechain_pump.wav"
    export_wav(stereo, path)
    print(f"    → {path} ({duration:.1f}s)")


# ============================================================================
# Demo 3: Stereo Widener
# ============================================================================

def demo_stereo_widener():
    """Same arpeggio played at 5 width settings: mono → ultra-wide."""
    print("  Demo 3: Stereo widener...")
    # Create a simple arpeggio with slight L/R offset for initial stereo content
    notes = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
    segment_dur = 1.0
    segments = []
    widths = [0.0, 0.5, 1.0, 1.5, 2.0]  # mono → ultra

    for width in widths:
        arp = np.zeros(int(SAMPLE_RATE * segment_dur), dtype=np.float32)
        note_dur = segment_dur / len(notes)
        for i, freq in enumerate(notes):
            tone = generate_tone(freq, note_dur, instrument="pulse_warm")
            start = int(i * note_dur * SAMPLE_RATE)
            end = min(start + len(tone), len(arp))
            arp[start:end] += tone[:end - start]

        # Create stereo with slight panning
        left_delay = int(SAMPLE_RATE * 0.0003)  # 0.3ms
        left = np.roll(arp, left_delay) * 0.8
        right = arp * 0.75
        stereo = np.column_stack([left, right])

        widened = apply_stereo_widener(stereo, width)
        segments.append(widened * 0.7)

    output = np.concatenate(segments, axis=0)
    path = OUTPUT_DIR / "03_stereo_widener.wav"
    export_wav(output, path)
    print(f"    → {path} ({len(output)/SAMPLE_RATE:.1f}s)")


# ============================================================================
# Demo 4: Bitcrush Sweep
# ============================================================================

def demo_bitcrush():
    """Continuous tone with bitcrushing sweeping from 16-bit to 2-bit."""
    print("  Demo 4: Bitcrush sweep...")
    duration = 4.0
    source = generate_tone(329.63, duration, instrument="saw_filtered")
    n = len(source)

    # Sweep bit depth from 16 to 2 over duration
    output = np.zeros(n, dtype=np.float32)
    for i in range(n):
        t = i / n
        bits = int(16 - t * 14)  # 16 → 2
        bits = max(2, bits)
        levels = 2 ** bits
        output[i] = np.round(source[i] * levels) / levels

    stereo = make_stereo(output * 0.7)
    path = OUTPUT_DIR / "04_bitcrush_sweep.wav"
    export_wav(stereo, path)
    print(f"    → {path} ({duration:.1f}s)")


# ============================================================================
# Demo 5: Master Bus A/B
# ============================================================================

def demo_master_bus():
    """Same mix played twice: raw, then with master bus processing."""
    print("  Demo 5: Master bus A/B...")
    duration = 3.0
    n = int(SAMPLE_RATE * duration)

    # Build a simple mix: bass + lead + hats
    bass = generate_tone(130.81, duration, instrument="bass_growl")
    lead = generate_tone(523.25, duration, instrument="saw_filtered")
    # Simple hat pattern (noise bursts)
    hats = np.zeros(n, dtype=np.float32)
    hat_interval = int(SAMPLE_RATE * 0.25)  # every quarter note at ~120 BPM
    hat_dur = int(SAMPLE_RATE * 0.02)
    for i in range(0, n, hat_interval):
        end = min(i + hat_dur, n)
        hats[i:end] = np.random.uniform(-0.3, 0.3, end - i).astype(np.float32)

    # Pad to same length
    bass = bass[:n] if len(bass) >= n else np.pad(bass, (0, n - len(bass)))
    lead = lead[:n] if len(lead) >= n else np.pad(lead, (0, n - len(lead)))

    raw_mix = bass * 0.5 + lead * 0.35 + hats * 0.4

    # "Mastered" version: high-pass → compression → warmth → limiter
    mastered = apply_highpass(raw_mix.copy(), cutoff_hz=40.0)
    mastered = apply_compressor(mastered, threshold_db=-10.0, ratio=3.0,
                                attack_ms=10.0, release_ms=80.0, makeup_db=3.0)
    mastered = apply_warmth(mastered, amount=0.2)
    peak = np.max(np.abs(mastered))
    if peak > 0.95:
        mastered = mastered * (0.95 / peak)

    # A/B: raw then mastered with gap
    gap = np.zeros(int(SAMPLE_RATE * 0.5), dtype=np.float32)
    combined = np.concatenate([raw_mix * 0.7, gap, mastered * 0.7])
    stereo = make_stereo(combined)
    path = OUTPUT_DIR / "05_master_bus_ab.wav"
    export_wav(stereo, path)
    print(f"    → {path} ({len(combined)/SAMPLE_RATE:.1f}s)")


# ============================================================================
# Demo 6: Flanger
# ============================================================================

def demo_flanger():
    """Arpeggio with jet-sweep flanger effect."""
    print("  Demo 6: Flanger...")
    duration = 4.0
    n = int(SAMPLE_RATE * duration)

    # Build repeating arpeggio
    notes = [261.63, 329.63, 392.00, 523.25, 392.00, 329.63]  # C E G C' G E
    note_dur = 0.2
    arp = np.zeros(n, dtype=np.float32)
    for i in range(int(duration / note_dur)):
        freq = notes[i % len(notes)]
        tone = generate_tone(freq, note_dur, instrument="pulse_warm")
        start = int(i * note_dur * SAMPLE_RATE)
        end = min(start + len(tone), n)
        arp[start:end] += tone[:end - start]

    # A/B: 2 seconds dry, 2 seconds flanged
    half = n // 2
    flanged_section = apply_flanger(arp[half:], rate=0.3, depth=0.8,
                                     feedback=0.6, mix=0.5)
    output = np.zeros(n, dtype=np.float32)
    output[:half] = arp[:half]
    output[half:half + len(flanged_section)] = flanged_section

    stereo = make_stereo(output * 0.7)
    path = OUTPUT_DIR / "06_flanger.wav"
    export_wav(stereo, path)
    print(f"    → {path} ({duration:.1f}s)")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("ChipForge ADR-005 Effect Demos")
    print("=" * 40)

    demo_distortion()
    demo_sidechain()
    demo_stereo_widener()
    demo_bitcrush()
    demo_master_bus()
    demo_flanger()

    print()
    print("All demos rendered to output/demos/")
    print("Listen to hear the future of ChipForge sound.")
