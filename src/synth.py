"""
ChipForge Core Synthesis Engine
================================
Waveform generators, ADSR envelope, filters, and modulation — all synthesis
from first principles using numpy.

Inspired by the Game Boy DMG APU:
  - CH1/CH2: Square waves with 4 duty cycles (12.5%, 25%, 50%, 75%)
  - CH3:     Wave channel — custom 32-sample wavetable
  - CH4:     LFSR noise — 7-bit (metallic) or 15-bit (white-ish)

Enhanced with:
  - Resonant low-pass filter (2-pole state-variable)
  - Vibrato (LFO pitch modulation)
  - Pitch sweep (for kick drums and effects)
  - Exponential ADSR curves
  - PolyBLEP anti-aliasing for square/saw

No external audio libraries. Everything is a numpy float32 array.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import math

import numpy as np

try:
    from scipy.signal import sosfilt as _sosfilt
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE: int = 44100  # Hz — standard CD quality


# ---------------------------------------------------------------------------
# LFSR Noise — precomputed at module load for zero runtime cost
# ---------------------------------------------------------------------------

def _precompute_lfsr(bits: int) -> np.ndarray:
    """
    Compute one full LFSR sequence (period = 2^bits - 1).

    Game Boy CH4 uses an XOR LFSR:
      new_bit = bit[0] XOR bit[1]
      register shifts right, new_bit placed at MSB

    Args:
        bits: Register width (7 for metallic noise, 15 for white noise).

    Returns:
        Float32 array of +1.0/-1.0 values, length = 2^bits - 1.
    """
    period = (1 << bits) - 1
    mask = period  # e.g. 0x7F for 7-bit, 0x7FFF for 15-bit
    register = mask  # start all-ones
    sequence = np.empty(period, dtype=np.float32)

    for i in range(period):
        xor_bit = (register ^ (register >> 1)) & 1
        register = ((register >> 1) | (xor_bit << (bits - 1))) & mask
        sequence[i] = 1.0 if (register & 1) else -1.0

    return sequence


# Precomputed — done once at import time
_LFSR_7: np.ndarray = _precompute_lfsr(7)    # period 127  — metallic, hat-like
_LFSR_15: np.ndarray = _precompute_lfsr(15)   # period 32767 — near-white, kick/snare


# ---------------------------------------------------------------------------
# Waveform Generators
# ---------------------------------------------------------------------------

def generate_sine(freq: float, num_samples: int) -> np.ndarray:
    """
    Generate a pure sine wave.

    Args:
        freq: Frequency in Hz.
        num_samples: Number of output samples.

    Returns:
        Float32 array in range [-1, 1].
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    return np.sin(2.0 * np.pi * freq * t).astype(np.float32)


def _polyblep(t_val: np.ndarray, dt: float) -> np.ndarray:
    """PolyBLEP correction — reduces aliasing at waveform discontinuities."""
    result = np.zeros_like(t_val)
    # Rising edge (t near 0)
    mask1 = t_val < dt
    t1 = t_val[mask1] / dt
    result[mask1] = 2.0 * t1 - t1 * t1 - 1.0
    # Falling edge (t near 1)
    mask2 = t_val > 1.0 - dt
    t2 = (t_val[mask2] - 1.0) / dt
    result[mask2] = t2 * t2 + 2.0 * t2 + 1.0
    return result


def generate_square(freq: float, num_samples: int, duty: float = 0.5) -> np.ndarray:
    """
    Generate a square wave with variable duty cycle and PolyBLEP anti-aliasing.

    Game Boy authentic duty cycles: 0.125, 0.25, 0.5, 0.75.

    Args:
        freq: Frequency in Hz.
        num_samples: Number of output samples.
        duty: Duty cycle in range (0, 1). Default 0.5 = symmetric square.

    Returns:
        Float32 array of +1.0/-1.0 values (band-limited).
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    phase = (freq * t) % 1.0
    dt = freq / SAMPLE_RATE
    naive = np.where(phase < duty, 1.0, -1.0)
    # Apply PolyBLEP at both edges
    naive += _polyblep(phase, dt)
    naive -= _polyblep((phase + 1.0 - duty) % 1.0, dt)
    return naive.astype(np.float32)


def generate_sawtooth(freq: float, num_samples: int) -> np.ndarray:
    """
    Generate a rising sawtooth wave with PolyBLEP anti-aliasing.

    Args:
        freq: Frequency in Hz.
        num_samples: Number of output samples.

    Returns:
        Float32 array in range [-1, 1].
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    phase = (freq * t) % 1.0
    dt = freq / SAMPLE_RATE
    naive = 2.0 * phase - 1.0
    naive -= _polyblep(phase, dt)
    return naive.astype(np.float32)


def generate_triangle(freq: float, num_samples: int) -> np.ndarray:
    """
    Generate a triangle wave. Smooth and mellow — similar to Game Boy CH3 wave.

    Args:
        freq: Frequency in Hz.
        num_samples: Number of output samples.

    Returns:
        Float32 array in range [-1, 1].
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    phase = (freq * t) % 1.0
    return (2.0 * np.abs(2.0 * phase - 1.0) - 1.0).astype(np.float32)


def generate_wavetable(wavetable: list[float], freq: float, num_samples: int) -> np.ndarray:
    """
    Game Boy CH3 style wavetable synthesis.

    Cycles through a custom waveform array at the target frequency.
    Classic GB CH3 uses 32 4-bit samples; here we accept any list of floats.

    Args:
        wavetable: Sample values in range [-1, 1]. Typically 32 entries.
        freq: Playback frequency in Hz.
        num_samples: Number of output samples.

    Returns:
        Float32 array in range [-1, 1].
    """
    wt = np.array(wavetable, dtype=np.float32)
    wt_len = len(wt)
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    indices = (freq * t * wt_len).astype(np.int64) % wt_len
    return wt[indices]


def generate_lfsr_noise(num_samples: int, short_mode: bool = False) -> np.ndarray:
    """
    Game Boy CH4 style LFSR noise.

    Tiles a precomputed LFSR sequence to the required length.

    Args:
        num_samples: Number of output samples.
        short_mode: True = 7-bit LFSR (period 127, metallic / hi-hat-like).
                    False = 15-bit LFSR (period 32767, near-white noise).

    Returns:
        Float32 array of +1.0/-1.0 values.
    """
    template = _LFSR_7 if short_mode else _LFSR_15
    repeats = (num_samples // len(template)) + 1
    return np.tile(template, repeats)[:num_samples]


# ---------------------------------------------------------------------------
# Resonant Low-Pass Filter
# ---------------------------------------------------------------------------

def _design_lowpass_biquad(cutoff_hz: float, resonance: float) -> np.ndarray:
    """Design 2nd-order resonant lowpass biquad (Audio EQ Cookbook).

    Returns SOS array for use with scipy.signal.sosfilt.
    """
    cutoff_hz = max(20.0, min(cutoff_hz, SAMPLE_RATE * 0.45))
    resonance = max(0.0, min(resonance, 0.95))
    w0 = 2.0 * math.pi * cutoff_hz / SAMPLE_RATE
    Q = 0.5 / max(1.0 - resonance * 0.99, 0.01)
    alpha = math.sin(w0) / (2.0 * Q)
    cos_w0 = math.cos(w0)
    b0 = (1.0 - cos_w0) / 2.0
    b1 = 1.0 - cos_w0
    b2 = (1.0 - cos_w0) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha
    return np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]])


def _apply_lowpass_python(samples: np.ndarray, cutoff_hz: float,
                          resonance: float = 0.0) -> np.ndarray:
    """Python fallback: 2-pole SVF per-sample loop."""
    cutoff_hz = max(20.0, min(cutoff_hz, SAMPLE_RATE * 0.45))
    resonance = max(0.0, min(resonance, 0.95))
    f = 2.0 * np.sin(np.pi * cutoff_hz / SAMPLE_RATE)
    q = 1.0 - resonance
    out = np.empty_like(samples)
    low = 0.0
    band = 0.0
    for i in range(len(samples)):
        low += f * band
        high = float(samples[i]) - low - q * band
        band += f * high
        out[i] = low
    return out.astype(np.float32)


def apply_lowpass(samples: np.ndarray, cutoff_hz: float,
                  resonance: float = 0.0) -> np.ndarray:
    """
    Apply a 2-pole resonant low-pass filter.

    Uses scipy biquad when available (100-1000x faster), otherwise falls
    back to a per-sample state-variable filter in Python.

    Args:
        samples: Mono float32 audio buffer.
        cutoff_hz: Filter cutoff frequency in Hz (20-20000).
        resonance: Resonance amount (0.0 = none, 0.95 = self-oscillation).

    Returns:
        Filtered float32 array, same length.
    """
    if _HAS_SCIPY:
        sos = _design_lowpass_biquad(cutoff_hz, resonance)
        return _sosfilt(sos, samples).astype(np.float32)
    return _apply_lowpass_python(samples, cutoff_hz, resonance)


def _apply_filter_sweep_python(samples: np.ndarray, start_hz: float,
                               end_hz: float,
                               resonance: float = 0.3) -> np.ndarray:
    """Python fallback: per-sample SVF with varying cutoff."""
    n = len(samples)
    resonance = max(0.0, min(resonance, 0.95))
    q = 1.0 - resonance
    cutoffs = np.logspace(
        np.log10(max(20, start_hz)), np.log10(max(20, end_hz)), n
    )
    out = np.empty_like(samples)
    low = 0.0
    band = 0.0
    for i in range(n):
        f = 2.0 * np.sin(
            np.pi * min(cutoffs[i], SAMPLE_RATE * 0.45) / SAMPLE_RATE
        )
        low += f * band
        high = float(samples[i]) - low - q * band
        band += f * high
        out[i] = low
    return out.astype(np.float32)


# ---------------------------------------------------------------------------
# Filter Envelope (ADSR on cutoff)
# ---------------------------------------------------------------------------

@dataclass
class FilterEnvelope:
    """
    ADSR envelope applied to a low-pass filter cutoff over a note's lifecycle.

    Unlike a static cutoff, this lets the filter "open" on attack (bright)
    and "close" toward sustain (warm) — the classic Moog/303 sound that
    transforms a flat sawtooth into a liquid lead or acid bass.

    The cutoff curve is:
        rest                              → base_hz
        attack    (0 → attack_sec)        → ramps to peak_hz
        decay     (attack_sec → +decay)   → ramps to sustain_hz
        sustain   (until release)         → holds at sustain_hz
        release   (last release_sec)      → ramps back to base_hz

    Attributes:
        base_hz: Cutoff before the note begins and after release ends.
        peak_hz: Maximum cutoff reached at end of attack stage.
        sustain_hz: Cutoff held during sustain stage.
        attack_sec: Time from base → peak (seconds).
        decay_sec: Time from peak → sustain (seconds).
        release_sec: Time from sustain → base (seconds).
        resonance: Filter resonance (0.0 → 0.95).
    """

    base_hz: float = 400.0
    peak_hz: float = 4000.0
    sustain_hz: float = 1200.0
    attack_sec: float = 0.01
    decay_sec: float = 0.15
    release_sec: float = 0.10
    resonance: float = 0.3


def build_filter_envelope_curve(
    env: FilterEnvelope,
    num_samples: int,
) -> np.ndarray:
    """
    Build the per-sample cutoff frequency curve for a filter envelope.

    Curves are linear in log-frequency space so they sound musically even
    (a sweep from 200 → 4000 Hz feels uniform rather than back-loaded).

    Args:
        env: FilterEnvelope describing the ADSR shape.
        num_samples: Length of the note buffer in samples.

    Returns:
        Float32 array of cutoff frequencies, length = num_samples.
    """
    if num_samples <= 0:
        return np.zeros(0, dtype=np.float32)

    sr = SAMPLE_RATE
    a_n = max(1, int(env.attack_sec * sr))
    d_n = max(1, int(env.decay_sec * sr))
    r_n = max(1, int(env.release_sec * sr))
    s_n = max(0, num_samples - a_n - d_n - r_n)

    log_base = math.log(max(20.0, env.base_hz))
    log_peak = math.log(max(20.0, env.peak_hz))
    log_sus = math.log(max(20.0, env.sustain_hz))

    parts: list[np.ndarray] = []
    if a_n:
        parts.append(np.exp(np.linspace(log_base, log_peak, a_n, endpoint=False)))
    if d_n:
        parts.append(np.exp(np.linspace(log_peak, log_sus, d_n, endpoint=False)))
    if s_n:
        parts.append(np.full(s_n, math.exp(log_sus), dtype=np.float64))
    if r_n:
        parts.append(np.exp(np.linspace(log_sus, log_base, r_n, endpoint=True)))

    curve = np.concatenate(parts) if parts else np.array([], dtype=np.float64)

    # Pad / truncate to exact num_samples (off-by-one safety).
    if len(curve) < num_samples:
        pad = np.full(num_samples - len(curve), curve[-1] if len(curve) else env.base_hz)
        curve = np.concatenate([curve, pad])
    elif len(curve) > num_samples:
        curve = curve[:num_samples]

    return curve.astype(np.float32)


def apply_filter_envelope(
    samples: np.ndarray,
    env: FilterEnvelope,
) -> np.ndarray:
    """
    Apply a low-pass filter whose cutoff follows an ADSR envelope.

    Uses block-wise biquad processing (~256 samples / ~5.8 ms per block) so
    the filter coefficients update smoothly over the note's lifecycle while
    keeping CPU cost low. Falls back to per-sample SVF if scipy is missing.

    Args:
        samples: Mono float32 audio buffer.
        env: FilterEnvelope describing how the cutoff should move.

    Returns:
        Filtered float32 array, same length as input.
    """
    n = len(samples)
    if n == 0:
        return samples.astype(np.float32)

    cutoff_curve = build_filter_envelope_curve(env, n)

    if not _HAS_SCIPY:
        # Per-sample SVF fallback.
        out = np.empty_like(samples)
        low = 0.0
        band = 0.0
        q = 1.0 - max(0.0, min(env.resonance, 0.95))
        for i in range(n):
            f = 2.0 * math.sin(
                math.pi * min(float(cutoff_curve[i]), SAMPLE_RATE * 0.45) / SAMPLE_RATE
            )
            low += f * band
            high = float(samples[i]) - low - q * band
            band += f * high
            out[i] = low
        return out.astype(np.float32)

    BLOCK = 256
    output = np.empty(n, dtype=np.float64)
    zi = None
    for s in range(0, n, BLOCK):
        e = min(s + BLOCK, n)
        block = samples[s:e].astype(np.float64)
        # Use the cutoff at the centre of the block for stable, smooth filtering.
        mid_cutoff = float(cutoff_curve[(s + e - 1) // 2])
        sos = _design_lowpass_biquad(mid_cutoff, env.resonance)
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        filtered, zi = _sosfilt(sos, block, zi=zi)
        output[s:e] = filtered

    return output.astype(np.float32)


def apply_filter_sweep(
    samples: np.ndarray,
    start_hz: float,
    end_hz: float,
    resonance: float = 0.3,
) -> np.ndarray:
    """
    Apply low-pass filter with cutoff sweeping from start_hz to end_hz.

    Uses chunked scipy biquad when available (~50x faster), otherwise
    falls back to per-sample Python SVF.

    Args:
        samples: Mono float32 audio buffer.
        start_hz: Starting cutoff frequency.
        end_hz: Ending cutoff frequency.
        resonance: Filter resonance (0.0-0.95).

    Returns:
        Filtered float32 array.
    """
    if not _HAS_SCIPY:
        return _apply_filter_sweep_python(samples, start_hz, end_hz, resonance)

    BLOCK = 256  # ~5.8 ms at 44100 Hz
    n = len(samples)
    output = np.empty(n, dtype=np.float64)
    num_blocks = (n + BLOCK - 1) // BLOCK
    cutoffs = np.geomspace(
        max(start_hz, 20.0), max(end_hz, 20.0), num_blocks
    )

    zi = None
    for b_idx in range(num_blocks):
        s = b_idx * BLOCK
        e = min(s + BLOCK, n)
        chunk = samples[s:e].astype(np.float64)
        sos = _design_lowpass_biquad(cutoffs[b_idx], resonance)
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        filtered, zi = _sosfilt(sos, chunk, zi=zi)
        output[s:e] = filtered

    return output.astype(np.float32)


# ---------------------------------------------------------------------------
# Vibrato (LFO Pitch Modulation)
# ---------------------------------------------------------------------------

def generate_with_vibrato(
    freq: float,
    num_samples: int,
    waveform: str = "sine",
    vib_rate: float = 5.0,
    vib_depth: float = 0.3,
    duty: float = 0.5,
    wavetable: list[float] | None = None,
) -> np.ndarray:
    """
    Generate a waveform with vibrato (pitch wobble via LFO).

    Uses phase accumulation with frequency modulation, then applies the
    target waveform shape to the accumulated phase. This preserves the
    correct timbre for all waveform types.

    Args:
        freq: Base frequency in Hz.
        num_samples: Number of output samples.
        waveform: Waveform type string (sine, square, sawtooth, triangle, etc.).
        vib_rate: LFO frequency in Hz (typically 4-8).
        vib_depth: Pitch deviation in semitones (0.1 = subtle, 1.0 = wide).
        duty: Duty cycle for square waves.
        wavetable: Custom wavetable data for wavetable waveform.

    Returns:
        Float32 array with pitch modulation applied using the correct waveform.
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    # LFO modulates frequency by semitone deviation
    lfo = np.sin(2.0 * np.pi * vib_rate * t)
    freq_mod = freq * (2.0 ** (lfo * vib_depth / 12.0))

    # Phase accumulation with varying frequency
    phase = np.cumsum(freq_mod / SAMPLE_RATE)
    phase_frac = phase % 1.0

    # Apply the correct waveform shape to the accumulated phase
    if waveform == "square":
        return np.where(phase_frac < duty, 1.0, -1.0).astype(np.float32)
    elif waveform == "sawtooth":
        return (2.0 * phase_frac - 1.0).astype(np.float32)
    elif waveform == "triangle":
        return (2.0 * np.abs(2.0 * phase_frac - 1.0) - 1.0).astype(np.float32)
    elif waveform == "wavetable" and wavetable:
        wt = np.array(wavetable, dtype=np.float32)
        indices = (phase_frac * len(wt)).astype(np.int64) % len(wt)
        return wt[indices]
    elif waveform.startswith("additive_"):
        profile_name = waveform[9:]
        harmonics = HARMONIC_PROFILES.get(profile_name)
        if harmonics is None:
            harmonics = [0.7 ** i for i in range(12)]
        result = np.zeros(num_samples, dtype=np.float64)
        nyquist = SAMPLE_RATE / 2.0
        for i, amp in enumerate(harmonics):
            partial_freq = freq * (i + 1)
            if partial_freq >= nyquist or abs(amp) < 0.001:
                continue
            partial_phase = np.cumsum(freq_mod * (i + 1) / SAMPLE_RATE)
            result += amp * np.sin(2.0 * np.pi * partial_phase)
        peak = np.max(np.abs(result))
        if peak > 0:
            result /= peak
        return result.astype(np.float32)
    elif waveform == "fm" or waveform.startswith("fm_"):
        # FM synthesis with vibrato: apply pitch wobble to both carrier + modulator
        parts = waveform.split("_") if waveform.startswith("fm_") else []
        ratio = float(parts[1]) if len(parts) > 1 else 2.0
        index = float(parts[2]) if len(parts) > 2 else 5.0
        mod_freq = freq_mod * ratio
        mod_phase = np.cumsum(mod_freq / SAMPLE_RATE)
        modulator = index * np.sin(2.0 * np.pi * mod_phase)
        carrier_phase = np.cumsum(freq_mod / SAMPLE_RATE)
        return np.sin(2.0 * np.pi * carrier_phase + modulator).astype(np.float32)
    else:
        # Default: sine
        return np.sin(2.0 * np.pi * phase).astype(np.float32)


# ---------------------------------------------------------------------------
# Pitch Sweep (for kick drums, laser effects, etc.)
# ---------------------------------------------------------------------------

def generate_pitch_sweep(
    start_freq: float,
    end_freq: float,
    num_samples: int,
    waveform: str = "sine",
) -> np.ndarray:
    """
    Generate a waveform with pitch sweeping from start_freq to end_freq.

    Essential for punchy kick drums (sweep from ~200Hz down to ~40Hz).

    Args:
        start_freq: Starting frequency in Hz.
        end_freq: Ending frequency in Hz.
        num_samples: Number of output samples.
        waveform: Waveform type ("sine", "triangle", "square").

    Returns:
        Float32 array with pitch sweep.
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    # Exponential frequency sweep
    freq_curve = start_freq * ((end_freq / max(start_freq, 0.01)) ** (t / max(t[-1], 0.001)))
    # Phase accumulation
    phase = np.cumsum(freq_curve / SAMPLE_RATE) % 1.0

    if waveform == "sine":
        return np.sin(2.0 * np.pi * phase).astype(np.float32)
    elif waveform == "triangle":
        return (2.0 * np.abs(2.0 * phase - 1.0) - 1.0).astype(np.float32)
    elif waveform == "square":
        return np.where(phase < 0.5, 1.0, -1.0).astype(np.float32)
    else:
        return np.sin(2.0 * np.pi * phase).astype(np.float32)


# ---------------------------------------------------------------------------
# White Noise Generator
# ---------------------------------------------------------------------------

def generate_white_noise(num_samples: int) -> np.ndarray:
    """
    Generate white noise using numpy random.

    Unlike LFSR noise which has a periodic structure, this is true
    pseudo-random noise. Useful for cymbals, risers, and ambient textures.

    Args:
        num_samples: Number of output samples.

    Returns:
        Float32 array of random values in range [-1, 1].
    """
    rng = np.random.default_rng(42)
    return rng.uniform(-1.0, 1.0, num_samples).astype(np.float32)


# ---------------------------------------------------------------------------
# Supersaw Generator — Stacked Detuned Sawtooths
# ---------------------------------------------------------------------------

def generate_supersaw(
    freq: float,
    num_samples: int,
    voices: int = 7,
    detune_cents: float = 15.0,
) -> np.ndarray:
    """
    Generate a supersaw: multiple detuned sawtooth waves summed.

    The classic EDM/trance lead sound. Each voice is slightly offset in
    pitch, creating a thick, chorused texture.

    Args:
        freq: Center frequency in Hz.
        num_samples: Number of output samples.
        voices: Number of detuned voices (3-9 typical).
        detune_cents: Total detune spread in cents.

    Returns:
        Normalized float32 array in range [-1, 1].
    """
    result = np.zeros(num_samples, dtype=np.float64)
    half = voices // 2
    for v in range(voices):
        offset = (v - half) * detune_cents / max(half, 1)
        f = freq * (2.0 ** (offset / 1200.0))
        result += generate_sawtooth(f, num_samples).astype(np.float64)
    # Normalize and soft clip: 7+ voices summed can exceed [-1,1] at high velocity
    peak = np.max(np.abs(result))
    if peak > 0:
        result /= peak
        result = np.tanh(result * 1.2) / np.tanh(1.2)

    # Analog drift: real polysynth oscillators drift slightly in pitch,
    # giving that warm, alive quality vs sterile digital perfection
    result = apply_harmonic_drift(result.astype(np.float32),
                                  drift_cents=1.5, drift_rate=0.2)

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# FM Synthesis (Yamaha DX7 style)
# ---------------------------------------------------------------------------

def generate_fm(
    freq: float,
    num_samples: int,
    mod_ratio: float = 2.0,
    mod_index: float = 5.0,
    mod_index_decay: float = 0.0,
) -> np.ndarray:
    """
    Frequency Modulation synthesis — the Yamaha DX7 sound.

    A modulator oscillator modulates the frequency of a carrier. Creates
    metallic bells, electric pianos, sci-fi effects, and complex timbres
    impossible with additive or subtractive synthesis.

    Args:
        freq: Carrier frequency in Hz.
        num_samples: Number of output samples.
        mod_ratio: Modulator frequency as ratio of carrier (2.0 = octave above).
                   Integer ratios = harmonic, non-integer = inharmonic/metallic.
        mod_index: Modulation depth (0 = pure sine, 5 = bright, 20 = extreme).
        mod_index_decay: Exponential decay rate of mod index (0 = constant,
                        3.0 = mod index halves in ~0.3s). Creates plucked/bell sounds.

    Returns:
        Float32 array in range [-1, 1].
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE

    # Modulation index with optional decay (bell = high decay, organ = zero)
    if mod_index_decay > 0:
        mi = mod_index * np.exp(-mod_index_decay * t)
    else:
        mi = mod_index

    # Modulator signal
    mod_freq = freq * mod_ratio
    modulator = mi * np.sin(2.0 * np.pi * mod_freq * t)

    # Carrier with FM
    carrier = np.sin(2.0 * np.pi * freq * t + modulator)

    return carrier.astype(np.float32)


# ---------------------------------------------------------------------------
# Karplus-Strong String Synthesis (Physical Modeling)
# ---------------------------------------------------------------------------

def generate_karplus_strong(
    freq: float,
    num_samples: int,
    decay: float = 0.996,
    brightness: float = 0.5,
) -> np.ndarray:
    """
    Karplus-Strong plucked string synthesis — physical modeling.

    Simulates a plucked string: a short burst of noise is fed through a
    delay line with a low-pass filter. The delay length determines pitch,
    the filter determines brightness decay. Sounds like guitar, harp,
    harpsichord — organic and realistic.

    Uses **fractional delay** via linear interpolation between two integer
    delay positions, so pitch stays accurate at every frequency. The naive
    integer-only version was off by +6 cents at C5 and **+23 cents at E6**
    because 44100 / freq isn't an integer; the rounding pushes the actual
    pitch sharp. With linear interpolation the entire register is within
    a fraction of a cent of equal-temperament A440.

    Args:
        freq: Frequency in Hz (determines delay line length).
        num_samples: Number of output samples.
        decay: Feedback gain (0.99 = long sustain, 0.95 = quick decay).
        brightness: Low-pass blend (0.0 = dark/muted, 1.0 = bright/metallic).

    Returns:
        Float32 array in range [-1, 1].
    """
    # Karplus-Strong with fractional-delay tuning.
    #
    # The naive integer-only version was sharp by up to +23 cents in the
    # upper register because `int(SR/freq)` truncates toward zero, making
    # the loop period shorter than requested. Here we use a linear
    # interpolated read so the effective delay is exactly `SR / freq`,
    # giving cent-accurate pitch across the whole keyboard.
    #
    # Decay shaping is done by exponentiating the gain per loop iteration
    # AND by a separate output-stage low-pass (see the post-processing
    # step below). Keeping the low-pass OUT of the feedback path means it
    # contributes no group delay and the pitch stays exact regardless of
    # the brightness setting.
    target_period = SAMPLE_RATE / max(freq, 1.0)
    delay_int = max(2, int(target_period))
    delay_frac = max(0.0, target_period - delay_int)
    delay_max = delay_int + 1   # +1 for the second interpolation tap

    buf = np.zeros(num_samples, dtype=np.float64)

    # Initial excitation: noise burst with soft fade-in to suppress click
    rng = np.random.RandomState(int(freq * 100) % 2**31)
    excitation = rng.uniform(-1.0, 1.0, delay_max)
    fade_len = min(delay_max // 4, 30)
    if fade_len > 0:
        excitation[:fade_len] *= np.linspace(0.0, 1.0, fade_len)
    buf[:delay_max] = excitation

    one_minus_frac = 1.0 - delay_frac

    # Pure fractional-delay feedback loop. No filter inside the loop, so
    # period is exactly `delay_int + delay_frac` = `SR / freq`.
    for i in range(delay_max, num_samples):
        a = buf[i - delay_int]
        b = buf[i - delay_int - 1]
        buf[i] = decay * (one_minus_frac * a + delay_frac * b)

    # Output-stage darkening filter — applied AFTER the feedback loop so it
    # doesn't shift the pitch. brightness=1 leaves the metallic raw signal,
    # brightness=0 darkens it heavily by averaging adjacent samples.
    blend = max(0.0, min(brightness, 1.0))
    if blend < 1.0:
        # Repeated 2-tap moving average — each pass darkens by ~3 dB at
        # Nyquist. We do 1-3 passes depending on the brightness setting.
        n_passes = int(round((1.0 - blend) * 3))
        for _ in range(n_passes):
            shifted = np.empty_like(buf)
            shifted[0] = buf[0]
            shifted[1:] = buf[:-1]
            buf = 0.5 * (buf + shifted)

    # Normalize and soft clip to prevent harsh peaks
    peak = np.max(np.abs(buf))
    if peak > 0:
        buf /= peak
        buf = np.tanh(buf * 1.2) / np.tanh(1.2)

    return buf.astype(np.float32)


# ---------------------------------------------------------------------------
# Ring Modulation
# ---------------------------------------------------------------------------

def generate_ring_mod(
    freq: float,
    num_samples: int,
    mod_freq: float = 0.0,
    mod_ratio: float = 1.5,
) -> np.ndarray:
    """
    Ring modulation — multiply carrier × modulator.

    Creates metallic, bell-like, dissonant tones. When mod_ratio is integer,
    produces harmonic partials. Non-integer ratios create inharmonic, gamelan-like
    sounds.

    Args:
        freq: Carrier frequency in Hz.
        num_samples: Number of output samples.
        mod_freq: Modulator frequency in Hz (overrides mod_ratio if > 0).
        mod_ratio: Modulator as ratio of carrier (used if mod_freq == 0).

    Returns:
        Float32 array in range [-1, 1].
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    carrier = np.sin(2.0 * np.pi * freq * t)

    m_freq = mod_freq if mod_freq > 0 else freq * mod_ratio
    modulator = np.sin(2.0 * np.pi * m_freq * t)

    result = carrier * modulator
    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Granular Synthesis
# ---------------------------------------------------------------------------

def generate_granular(
    freq: float,
    num_samples: int,
    grain_size_ms: float = 50.0,
    grain_density: float = 8.0,
    scatter: float = 0.3,
    source: str = "sine",
) -> np.ndarray:
    """
    Granular synthesis — decompose and reconstruct audio from tiny grains.

    Cuts a source waveform into small overlapping grains (10-100ms),
    applies window functions, and scatters them in time. Creates textures
    impossible with traditional synthesis: shimmering pads, glitchy effects,
    time-stretched atmospheres.

    Args:
        freq: Base frequency for the source waveform.
        num_samples: Number of output samples.
        grain_size_ms: Size of each grain in milliseconds (10-100 typical).
        grain_density: Average grains per second (4 = sparse, 20 = dense cloud).
        scatter: Time randomization (0 = rigid grid, 1 = fully random).
        source: Source waveform ("sine", "saw", "noise", "square").

    Returns:
        Float32 array in range [-1, 1].
    """
    grain_samples = max(64, int(grain_size_ms * SAMPLE_RATE / 1000.0))
    result = np.zeros(num_samples, dtype=np.float64)

    # Generate source material (one cycle extended)
    source_len = max(grain_samples * 4, num_samples)
    if source == "saw":
        src = generate_sawtooth(freq, source_len).astype(np.float64)
    elif source == "noise":
        rng = np.random.RandomState(42)
        src = rng.uniform(-1.0, 1.0, source_len)
        # Pre-smooth noise source: removes micro-transients that cause harsh
        # grain edges when windowed (lesson from vocal formant work)
        kernel = np.array([0.25, 0.50, 0.25], dtype=np.float64)
        src = np.convolve(src, kernel, mode='same')
    elif source == "square":
        src = generate_square(freq, source_len).astype(np.float64)
    else:
        src = generate_sine(freq, source_len).astype(np.float64)

    # Grain window (Hann — wider crossfade reduces clicks at grain boundaries)
    window = np.hanning(grain_samples).astype(np.float64)

    # Place grains
    rng = np.random.RandomState(int(freq * 1000) % 2**31)
    total_grains = max(1, int(grain_density * num_samples / SAMPLE_RATE))
    base_spacing = num_samples / max(total_grains, 1)

    for g in range(total_grains):
        # Position with scatter
        base_pos = int(g * base_spacing)
        offset = int(rng.uniform(-scatter, scatter) * base_spacing)
        pos = max(0, min(base_pos + offset, num_samples - grain_samples))

        # Source position (cycle through source material)
        src_pos = (g * grain_samples) % max(1, source_len - grain_samples)

        # Extract, window, and place grain
        grain = src[src_pos:src_pos + grain_samples] * window
        end = min(pos + grain_samples, num_samples)
        actual = end - pos
        result[pos:end] += grain[:actual]

    # Normalize and soft clip: dense grain clouds can stack above [-1,1]
    peak = np.max(np.abs(result))
    if peak > 0:
        result /= peak
        result = np.tanh(result * 1.2) / np.tanh(1.2)

    # Subtle harmonic drift for organic shimmer (analog grain synthesizers drift)
    result = apply_harmonic_drift(result.astype(np.float32),
                                  drift_cents=2.5, drift_rate=0.3)

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Pulse Width Modulation (PWM)
# ---------------------------------------------------------------------------

def generate_pwm(
    freq: float,
    num_samples: int,
    pwm_rate: float = 2.0,
    pwm_depth: float = 0.3,
    base_duty: float = 0.5,
) -> np.ndarray:
    """
    Pulse Width Modulation — duty cycle sweeps over time via LFO.

    Creates the classic evolving synth lead texture. The timbre continuously
    changes as the duty cycle modulates, producing a chorus-like richness
    from a single oscillator.

    Args:
        freq: Frequency in Hz.
        num_samples: Number of output samples.
        pwm_rate: LFO rate for duty modulation (Hz).
        pwm_depth: LFO depth (0.0-0.4, how much duty varies).
        base_duty: Center duty cycle (0.5 = square).

    Returns:
        Float32 array in range [-1, 1].
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    phase = (freq * t) % 1.0
    dt = freq / SAMPLE_RATE

    # LFO modulates duty cycle
    lfo = np.sin(2.0 * np.pi * pwm_rate * t)
    duty = np.clip(base_duty + lfo * pwm_depth, 0.05, 0.95)

    # Variable-duty square wave with PolyBLEP
    naive = np.where(phase < duty, 1.0, -1.0).astype(np.float64)
    naive += _polyblep(phase, dt)
    for i in range(num_samples):
        edge_phase = (phase[i] + 1.0 - duty[i]) % 1.0
        if edge_phase < dt:
            t_val = edge_phase / dt
            naive[i] -= 2.0 * t_val - t_val * t_val - 1.0
        elif edge_phase > 1.0 - dt:
            t_val = (edge_phase - 1.0) / dt
            naive[i] -= t_val * t_val + 2.0 * t_val + 1.0

    return naive.astype(np.float32)


# ---------------------------------------------------------------------------
# Wavetable Morphing (smooth interpolation between wavetables)
# ---------------------------------------------------------------------------

def generate_wavetable_morph(
    wavetable_a: list[float],
    wavetable_b: list[float],
    freq: float,
    num_samples: int,
    morph_curve: float | np.ndarray = 0.5,
) -> np.ndarray:
    """
    Morph between two wavetables smoothly over time.

    Unlike abruptly switching wavetables, this interpolates sample-by-sample
    between two waveforms, creating smooth timbral transitions without clicks.

    Args:
        wavetable_a: Source wavetable (list of floats, typically 32 samples).
        wavetable_b: Target wavetable.
        freq: Playback frequency in Hz.
        num_samples: Number of output samples.
        morph_curve: Morph amount (0.0 = pure A, 1.0 = pure B) or per-sample array.

    Returns:
        Float32 array in range [-1, 1].
    """
    wt_a = np.array(wavetable_a, dtype=np.float32)
    wt_b = np.array(wavetable_b, dtype=np.float32)
    wt_len = min(len(wt_a), len(wt_b))

    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    # Fractional index into wavetable
    indices_f = (freq * t * wt_len) % wt_len
    idx_floor = indices_f.astype(np.int64) % wt_len
    idx_ceil = (idx_floor + 1) % wt_len
    frac = (indices_f - np.floor(indices_f)).astype(np.float32)

    # Linear interpolation within each wavetable
    sample_a = wt_a[idx_floor] * (1.0 - frac) + wt_a[idx_ceil] * frac
    sample_b = wt_b[idx_floor] * (1.0 - frac) + wt_b[idx_ceil] * frac

    # Morph between wavetables
    if isinstance(morph_curve, (int, float)):
        m = float(morph_curve)
        result = sample_a * (1.0 - m) + sample_b * m
    else:
        m = np.asarray(morph_curve, dtype=np.float32)[:num_samples]
        if len(m) < num_samples:
            m = np.pad(m, (0, num_samples - len(m)), constant_values=m[-1])
        result = sample_a * (1.0 - m) + sample_b * m

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Portamento (Pitch Glide Between Notes)
# ---------------------------------------------------------------------------

def apply_portamento(
    samples: np.ndarray,
    start_freq: float,
    end_freq: float,
    glide_time_sec: float = 0.05,
) -> np.ndarray:
    """
    Apply portamento — smooth pitch glide from one frequency to another.

    The pitch transitions logarithmically (constant rate in semitones/sec)
    over the glide time, then holds at the target frequency.

    Args:
        samples: Audio buffer to pitch-shift.
        start_freq: Starting frequency in Hz.
        end_freq: Target frequency in Hz.
        glide_time_sec: Duration of the glide (seconds).

    Returns:
        Float32 array with pitch glide applied.
    """
    n = len(samples)
    glide_samples = min(int(glide_time_sec * SAMPLE_RATE), n)

    if glide_samples <= 0 or abs(start_freq - end_freq) < 0.01:
        return samples

    # Logarithmic frequency curve during glide, then constant
    ratio = end_freq / max(start_freq, 0.01)
    t_glide = np.arange(glide_samples, dtype=np.float64) / glide_samples
    freq_curve = np.ones(n, dtype=np.float64)
    freq_curve[:glide_samples] = start_freq * (ratio ** t_glide)
    freq_curve[glide_samples:] = end_freq

    # Resample using the frequency curve (phase accumulation)
    phase = np.cumsum(freq_curve / end_freq) - 1.0  # normalize to target
    indices = np.clip(phase * n / max(phase[-1], 1.0), 0, n - 1.001)
    idx_floor = indices.astype(np.int64)
    idx_ceil = np.minimum(idx_floor + 1, n - 1)
    frac = (indices - idx_floor).astype(np.float32)

    result = samples[idx_floor] * (1.0 - frac) + samples[idx_ceil] * frac
    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Harmonic Drift (Organic Micro-Detuning)
# ---------------------------------------------------------------------------

def apply_harmonic_drift(
    samples: np.ndarray,
    drift_cents: float = 3.0,
    drift_rate: float = 0.5,
) -> np.ndarray:
    """
    Apply subtle frequency drift — simulates natural instrument instability.

    Real instruments (strings, brass, voice) don't hold perfectly steady pitch.
    This adds a slow random walk in pitch that makes digital synthesis sound
    more organic and alive.

    Args:
        samples: Audio buffer.
        drift_cents: Maximum pitch deviation in cents (1-5 typical).
        drift_rate: Speed of drift in Hz (0.2 = slow, 2.0 = fast wobble).

    Returns:
        Float32 array with micro-detuning applied.
    """
    n = len(samples)
    if n == 0 or drift_cents <= 0:
        return samples

    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE

    # Smooth random drift using multiple slow LFOs at irrational ratios
    drift = (
        np.sin(2.0 * np.pi * drift_rate * t) * 0.5 +
        np.sin(2.0 * np.pi * drift_rate * 1.618 * t) * 0.3 +  # golden ratio
        np.sin(2.0 * np.pi * drift_rate * 2.236 * t) * 0.2     # sqrt(5)
    )
    drift = drift / 1.0  # normalize to [-1, 1]

    # Convert cents to resampling ratio
    ratio = 2.0 ** (drift * drift_cents / 1200.0)

    # Phase-accumulation resampling
    phase = np.cumsum(ratio)
    phase = phase / phase[-1] * (n - 1)  # normalize to buffer length
    phase = np.clip(phase, 0, n - 1.001)

    idx_floor = phase.astype(np.int64)
    idx_ceil = np.minimum(idx_floor + 1, n - 1)
    frac = (phase - idx_floor).astype(np.float32)

    result = samples[idx_floor] * (1.0 - frac) + samples[idx_ceil] * frac
    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Metal Guitar Synthesis — Power Chords, Palm Mutes, Shred
# ---------------------------------------------------------------------------

def generate_power_chord(
    freq: float,
    num_samples: int,
    palm_mute: bool = False,
    chug: bool = False,
) -> np.ndarray:
    """
    Generate a power chord — root + fifth + octave stacked.

    The power chord is THE sound of rock and metal. Three strings vibrating
    together through distortion creates a wall of harmonic richness.

    Args:
        freq: Root note frequency in Hz (typically E2=82Hz to A3=220Hz).
        num_samples: Number of output samples.
        palm_mute: If True, simulate palm muting (short decay, dark, percussive).
        chug: If True, very tight palm mute (the "djent" sound).

    Returns:
        Float32 array — the raw power chord (apply amp_sim after).
    """
    if palm_mute or chug:
        decay = 0.980 if chug else 0.988
        bright = 0.15 if chug else 0.25
    else:
        decay = 0.998
        bright = 0.65

    # Stack root + perfect fifth + octave
    root = generate_karplus_strong(freq, num_samples, decay=decay, brightness=bright)
    fifth = generate_karplus_strong(freq * 1.5, num_samples, decay=decay, brightness=bright)
    octave = generate_karplus_strong(freq * 2.0, num_samples, decay=decay * 0.999,
                                     brightness=bright * 0.9)

    # Slight detune between strings (real guitars aren't perfectly in tune)
    detune_5th = generate_karplus_strong(freq * 1.5 * 1.001, num_samples,
                                          decay=decay, brightness=bright * 0.8)

    chord = (root + fifth * 0.85 + octave * 0.65 + detune_5th * 0.3) / 2.8

    # Soft clip: 4 stacked KS strings can exceed [-1,1] at onset
    chord = np.tanh(chord.astype(np.float64) * 1.1).astype(np.float32) / np.float32(np.tanh(1.1))

    # For palm mutes, apply quick exponential decay
    if palm_mute or chug:
        t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
        decay_rate = 15.0 if chug else 8.0
        envelope = np.exp(-decay_rate * t)
        chord = chord * envelope.astype(np.float32)

    # Subtle harmonic drift for organic feel (real guitars drift slightly)
    chord = apply_harmonic_drift(chord, drift_cents=2.0, drift_rate=0.3)

    return chord.astype(np.float32)


def generate_guitar_lead(
    freq: float,
    num_samples: int,
    sustain: float = 0.9,
    feedback: float = 0.3,
) -> np.ndarray:
    """
    Generate a lead guitar note with sustain and feedback.

    For solos and lead lines: bright, sustained, with harmonic feedback
    (the squealing overtones that happen at high gain). Uses KS with
    energy injection to maintain sustain.

    Args:
        freq: Note frequency in Hz.
        num_samples: Number of output samples.
        sustain: How long the note sustains (0.5 = quick, 0.95 = infinite).
        feedback: Harmonic feedback amount (0.0 = clean, 0.5 = squealing).

    Returns:
        Float32 array — raw lead guitar signal.
    """
    # High-brightness KS for lead tone
    note = generate_karplus_strong(freq, num_samples, decay=0.9985 + sustain * 0.001,
                                    brightness=0.75)

    # Add feedback harmonics (natural + octave harmonics)
    if feedback > 0:
        t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
        # Natural harmonic feedback builds over time
        fb_env = np.clip(t * 3.0, 0, 1) * feedback
        harmonic_2 = np.sin(2.0 * np.pi * freq * 2.0 * t) * fb_env * 0.15
        harmonic_3 = np.sin(2.0 * np.pi * freq * 3.0 * t) * fb_env * 0.08
        note = note + (harmonic_2 + harmonic_3).astype(np.float32)

    # Add subtle vibrato (guitarists bend strings)
    note = apply_harmonic_drift(note, drift_cents=8.0, drift_rate=5.5)

    return note.astype(np.float32)


def generate_guitar_trem(
    freq: float,
    num_samples: int,
    speed: float = 16.0,
) -> np.ndarray:
    """
    Generate tremolo-picked guitar — rapid alternate picking on one note.

    The foundation of thrash metal rhythm: rapid repeated attacks on a
    palm-muted string. Creates the "machine gun" chug.

    Args:
        freq: Note frequency.
        num_samples: Number of output samples.
        speed: Picks per second (8 = moderate, 16 = thrash, 24 = insane).

    Returns:
        Float32 array — tremolo-picked guitar.
    """
    pick_samples = max(64, int(SAMPLE_RATE / speed))
    result = np.zeros(num_samples, dtype=np.float64)

    # Generate individual pick attacks
    num_picks = num_samples // pick_samples + 1
    for p in range(num_picks):
        start = p * pick_samples
        if start >= num_samples:
            break
        end = min(start + pick_samples, num_samples)
        length = end - start

        # Each pick is a short KS burst (use higher octave if pick too short for delay line)
        pick_freq = freq
        while int(SAMPLE_RATE / pick_freq) > length - 2:
            pick_freq *= 2.0  # go up an octave if delay line doesn't fit
        pick = generate_karplus_strong(pick_freq, length, decay=0.985, brightness=0.3)

        # Attack envelope per pick
        attack = min(length, 20)
        env = np.ones(length, dtype=np.float32)
        env[:attack] = np.linspace(0, 1, attack)
        env[length // 2:] *= np.linspace(1, 0.3, length - length // 2)

        result[start:end] += (pick * env).astype(np.float64)

    peak = np.max(np.abs(result))
    if peak > 0:
        result /= peak

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Vocal Synthesis — Voices from Code
# ---------------------------------------------------------------------------

# Formant frequency table: (F1, F2, F3, F4, F5) in Hz
# Source: Peterson & Barney (1952), Hillenbrand et al. (1995)
VOWEL_FORMANTS: dict[str, tuple[float, ...]] = {
    "ah":  (730, 1090, 2440, 3400, 4500),    # /ɑ/ father — open, warm
    "ee":  (270, 2290, 3010, 3600, 4800),    # /i/ beat — bright, forward
    "eh":  (530, 1840, 2480, 3400, 4600),    # /ɛ/ bed — mid, open
    "oh":  (570, 840, 2410, 3400, 4500),     # /o/ boat — round, dark
    "oo":  (300, 870, 2240, 3200, 4500),     # /u/ boot — closed, deep
    "aa":  (660, 1720, 2410, 3400, 4600),    # /æ/ bat — bright, open
    "uh":  (520, 1190, 2390, 3400, 4500),    # /ʌ/ but — neutral, center
    "ih":  (390, 1990, 2550, 3400, 4700),    # /ɪ/ bit — short bright
}

# Formant bandwidths (Hz) — MUST be wide to prevent resonant ringing.
# Narrow bandpass filters excited by periodic pulses ring like plucked strings.
# Wider bands = lower Q = smooth vocal resonance instead of pluck artifacts.
# Widened significantly from original (80-200) to eliminate ringing.
FORMANT_BANDWIDTHS = (200, 220, 260, 300, 350)

# Formant gains (relative, dB) — how loud each formant is
# F1 carries fundamental weight, F2/F3 define vowel character (must be prominent)
# F2 boosted to -1dB for clearer vowel identity; F4/F5 more present for air/realism
FORMANT_GAINS_DB = (0, -1, -5, -9, -14)


def _design_formant_bandpass(center_hz: float, bandwidth_hz: float) -> np.ndarray:
    """
    Design a 2nd-order Butterworth bandpass filter centered on a vocal formant.

    Using a true bandpass (not a lowpass approximation) creates distinct spectral
    peaks at each formant frequency — which is what makes vowels recognizable.
    A lowpass at the formant edge (the previous approach) passes all low frequencies
    and produces muddy, whispy output with no vowel character.

    Args:
        center_hz: Formant center frequency in Hz.
        bandwidth_hz: -3dB bandwidth in Hz (typically 80-200 for voice).

    Returns:
        2nd-order SOS coefficients for scipy.signal.sosfilt.
    """
    from scipy.signal import butter
    nyq = SAMPLE_RATE / 2.0
    half_bw = max(bandwidth_hz, 30.0) / 2.0
    fl = max(center_hz - half_bw, 20.0)
    fh = min(center_hz + half_bw, nyq - 1.0)
    if fl >= fh:
        # Fallback: use 10% either side of center
        fl = max(center_hz * 0.90, 20.0)
        fh = min(center_hz * 1.10, nyq - 1.0)
    return butter(2, [fl / nyq, fh / nyq], btype='bandpass', output='sos')


def _snap_to_nearest_semitone(freq: float) -> float:
    """
    Autotune: snap a frequency to the nearest exact semitone (equal temperament).

    Converts freq to MIDI note number, rounds to nearest integer,
    then converts back to exact Hz. This produces pitch-perfect tuning.

    Args:
        freq: Input frequency in Hz.

    Returns:
        Frequency snapped to the nearest semitone.
    """
    if freq <= 0:
        return freq
    midi = 12.0 * math.log2(freq / 440.0) + 69.0
    midi_snapped = round(midi)
    return 440.0 * (2.0 ** ((midi_snapped - 69.0) / 12.0))


def generate_glottal_pulse(freq: float, num_samples: int, harmonics: int = 6) -> np.ndarray:
    """
    Generate a harmonically-rich glottal pulse waveform — the vocal cord excitation.

    Combines the Rosenberg glottal pulse model with additional harmonics
    from a band-limited sawtooth. This creates a richer, louder excitation
    source that cuts through mix and gives formant filters more energy to shape.

    Args:
        freq: Fundamental frequency (pitch) in Hz.
        num_samples: Number of output samples.
        harmonics: Number of additional saw harmonics to blend in (3-8 typical).

    Returns:
        Float32 array in [-1, 1].
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    phase = (freq * t) % 1.0

    # Smooth glottal pulse — asymmetric raised cosine + gentle taper.
    # MUST be smooth (no sharp edges!) because abrupt transitions excite
    # the narrow bandpass formant filters and cause plucked-string ringing.
    open_ratio = 0.42    # glottis open phase
    close_ratio = 0.18   # gradual close — longer = less ringing

    result = np.zeros(num_samples, dtype=np.float64)

    # Open phase: asymmetric raised cosine (richer spectrum than pure sine)
    mask_open = phase < open_ratio
    p_open = phase[mask_open] / open_ratio
    result[mask_open] = 0.5 * (1.0 - np.cos(2.0 * np.pi * p_open ** 0.9))

    # Close phase: smooth cosine taper (no sharp drop = no pluck artifacts)
    mask_close = (phase >= open_ratio) & (phase < open_ratio + close_ratio)
    p_close = (phase[mask_close] - open_ratio) / close_ratio
    result[mask_close] = 0.5 * (1.0 + np.cos(np.pi * p_close))

    return result.astype(np.float32)


def apply_formants(
    excitation: np.ndarray,
    vowel: str = "ah",
    vowel_end: str | None = None,
    breathiness: float = 0.0,
    formant_shift: float = 0.0,
    num_formants: int = 5,
) -> np.ndarray:
    """
    Apply formant filtering to an excitation source — creates vowel sounds.

    Passes the excitation through a bank of parallel resonant bandpass filters
    at formant frequencies. The result sounds like a human vocal tract shaping
    the raw vocal cord buzz into recognizable vowels.

    This is the core of vocal synthesis: excitation + formants = voice.

    Args:
        excitation: Raw excitation signal (glottal pulse, noise, or saw wave).
        vowel: Starting vowel ("ah", "ee", "eh", "oh", "oo", "aa", "uh", "ih").
        vowel_end: If set, morph from vowel → vowel_end over the duration.
        breathiness: Amount of noise mixed in (0.0 = clean, 0.5 = breathy, 1.0 = whisper).
        formant_shift: Shift all formants up/down (semitones). +12 = child, -12 = giant.
        num_formants: Number of formant filters to apply (3-5).

    Returns:
        Float32 array — the vocal sound.
    """
    n = len(excitation)
    if n == 0:
        return excitation

    formants_start = VOWEL_FORMANTS.get(vowel, VOWEL_FORMANTS["ah"])
    formants_end = VOWEL_FORMANTS.get(vowel_end, formants_start) if vowel_end else formants_start

    # Add breathiness (mix in filtered noise)
    if breathiness > 0:
        noise = np.random.RandomState(42).randn(n).astype(np.float32) * breathiness
        source = excitation * (1.0 - breathiness * 0.5) + noise * 0.3
    else:
        source = excitation.astype(np.float64)

    # Pre-smooth excitation: gentle 5-sample moving average removes micro-transients
    # that would excite bandpass filter ringing (plucked-string artifacts).
    # This is applied before the formant bank, not after, so vowel character is preserved.
    kernel = np.ones(5, dtype=np.float64) / 5.0
    source = np.convolve(source, kernel, mode='same')

    # Formant shift (transpose vocal tract — higher = child/female, lower = male/giant)
    shift_ratio = 2.0 ** (formant_shift / 12.0)

    # Apply each formant as a resonant bandpass filter
    num_f = min(num_formants, len(formants_start))
    result = np.zeros(n, dtype=np.float64)

    if not _HAS_SCIPY:
        # Fallback: just use the raw excitation
        return excitation

    for i in range(num_f):
        f_start = formants_start[i] * shift_ratio
        f_end = formants_end[i] * shift_ratio

        # Bandwidth and gain for this formant
        bw = FORMANT_BANDWIDTHS[min(i, len(FORMANT_BANDWIDTHS) - 1)]
        gain_db = FORMANT_GAINS_DB[min(i, len(FORMANT_GAINS_DB) - 1)]
        gain_linear = 10.0 ** (gain_db / 20.0)

        if vowel_end and abs(f_start - f_end) > 10:
            # Morph formant frequency over duration (chunked processing)
            # Each chunk uses a proper bandpass centered on the interpolated formant freq
            from scipy.signal import sosfilt as _sf

            BLOCK = 2048  # larger blocks = smoother transitions, fewer discontinuities
            num_blocks = (n + BLOCK - 1) // BLOCK
            freqs = np.geomspace(max(f_start, 30.0), max(f_end, 30.0), num_blocks)
            filtered = np.zeros(n, dtype=np.float64)
            zi = None

            for b in range(num_blocks):
                s = b * BLOCK
                e = min(s + BLOCK, n)
                chunk = source[s:e].astype(np.float64)
                center = freqs[b]
                sos = _design_formant_bandpass(center, bw)
                if zi is None:
                    zi = np.zeros((sos.shape[0], 2))
                out, zi = _sf(sos, chunk, zi=zi)
                filtered[s:e] = out

            result += filtered * gain_linear
        else:
            # Static formant — proper bandpass centered on the formant frequency
            # This creates a distinct spectral peak, giving the vowel its character
            from scipy.signal import sosfilt as _sf
            sos = _design_formant_bandpass(f_start, bw)
            filtered = _sf(sos, source.astype(np.float64))
            result += filtered * gain_linear

    # Scale output: bandpass filtering removes a lot of energy, so boost to
    # make vocals sit at proper level in the mix (not whispy/faint)
    peak = np.max(np.abs(result))
    if peak > 0:
        # Normalize then boost — compensate for energy lost in bandpass filtering
        # (1.5x, down from 1.8 — buzzier excitation carries more energy naturally)
        result = (result / peak) * 1.5
        # Gentle soft clip to prevent distortion artifacts
        result = np.tanh(result * 0.7) / np.tanh(0.7)

    return result.astype(np.float32)


def generate_vocal(
    freq: float,
    num_samples: int,
    vowel: str = "ah",
    vowel_end: str | None = None,
    breathiness: float = 0.0,
    vibrato_rate: float = 5.5,
    vibrato_depth: float = 0.25,
    formant_shift: float = 0.0,
) -> np.ndarray:
    """
    Generate a complete synthetic vocal sound — voice from pure code.

    Combines:
    1. Glottal pulse excitation (vocal cord model)
    2. Formant filtering (vocal tract model)
    3. Vibrato (natural pitch wobble)
    4. Breathiness (noise blend)
    5. Harmonic drift (organic micro-detuning)

    The result sounds like a human voice singing a sustained vowel —
    not a sample, not a recording, built entirely from mathematics.

    Args:
        freq: Pitch frequency in Hz (e.g., 440 = A4).
        num_samples: Number of output samples.
        vowel: Vowel sound ("ah", "ee", "oh", "oo", "eh", "uh", "ih", "aa").
        vowel_end: If set, vowel morphs from vowel → vowel_end.
        breathiness: Breath noise amount (0.0 = clean, 0.5 = breathy).
        vibrato_rate: Vibrato speed in Hz (4-6 = natural).
        vibrato_depth: Vibrato depth in semitones (0.15-0.35 = natural).
        formant_shift: Shift formants up/down in semitones.

    Returns:
        Float32 array in [-1, 1] — the voice.
    """
    # 0. Autotune: snap pitch to nearest semitone for clean harmonic alignment
    freq = _snap_to_nearest_semitone(freq)

    # 1. Generate harmonically-rich glottal pulse with vibrato
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE

    # Natural vibrato (slightly irregular — golden ratio modulation)
    # Tighter depth range to keep pitch correction effective
    lfo = (np.sin(2.0 * np.pi * vibrato_rate * t) * 0.7 +
           np.sin(2.0 * np.pi * vibrato_rate * 1.618 * t) * 0.2 +
           np.sin(2.0 * np.pi * vibrato_rate * 0.382 * t) * 0.1)
    vib_depth = min(vibrato_depth, 0.20)  # cap vibrato so autotune stays clean
    freq_mod = freq * (2.0 ** (lfo * vib_depth / 12.0))

    # Phase accumulation for pitch-modulated glottal pulse
    phase = np.cumsum(freq_mod / SAMPLE_RATE) % 1.0

    # Smooth glottal pulse — asymmetric raised cosine + gradual close.
    # Sharp transients (exponential drops, negative returns, derivatives) excite
    # the formant bandpass filters and cause plucked-string ringing artifacts.
    # Keeping the pulse smooth eliminates that while preserving vocal character.
    open_ratio = 0.42
    close_ratio = 0.18
    excitation = np.zeros(num_samples, dtype=np.float64)

    # Open phase: asymmetric raised cosine (richer than pure sine, still smooth)
    mask_open = phase < open_ratio
    p_open = phase[mask_open] / open_ratio
    excitation[mask_open] = 0.5 * (1.0 - np.cos(2.0 * np.pi * p_open ** 0.9))

    # Close phase: smooth cosine taper (no pluck-causing sharp edges)
    mask_close = (phase >= open_ratio) & (phase < open_ratio + close_ratio)
    p_close = (phase[mask_close] - open_ratio) / close_ratio
    excitation[mask_close] = 0.5 * (1.0 + np.cos(np.pi * p_close))

    # Amplitude shimmer: gentle LFO volume variation (no random noise —
    # random noise causes audible 'lines' / gritty texture over the voice)
    shimmer = 1.0 + 0.03 * np.sin(2.0 * np.pi * 3.7 * t) + \
              0.02 * np.sin(2.0 * np.pi * 7.3 * t)
    excitation = excitation * shimmer

    # Onset fade: prevent bandpass filter startup transient (clicks/blips)
    fade_len = min(200, num_samples)
    fade_in = np.linspace(0.0, 1.0, fade_len)
    excitation[:fade_len] *= fade_in

    # 2. Apply formant filtering
    voice = apply_formants(
        excitation.astype(np.float32),
        vowel=vowel,
        vowel_end=vowel_end,
        breathiness=breathiness,
        formant_shift=formant_shift,
    )

    # 3. Subtle chest warmth: very light low-frequency blend (10%)
    # Just enough body without closing down the sound
    if _HAS_SCIPY:
        from scipy.signal import butter, sosfilt
        nyq = SAMPLE_RATE / 2.0
        chest_sos = butter(1, 400.0 / nyq, btype='low', output='sos')
        chest = sosfilt(chest_sos, voice.astype(np.float64))
        voice = (voice.astype(np.float64) * 0.90 + chest * 0.10).astype(np.float32)

    # 4. Apply harmonic drift (organic micro-detuning)
    voice = apply_harmonic_drift(voice, drift_cents=2.0, drift_rate=0.25)

    return voice


def generate_vocal_choir(
    freq: float,
    num_samples: int,
    vowel: str = "ah",
    voices: int = 5,
    detune_cents: float = 12.0,
    breathiness: float = 0.05,
    formant_shift_range: float = 2.0,
) -> np.ndarray:
    """
    Generate a synthetic choir — multiple detuned vocal voices.

    Each voice has slightly different pitch, formant shift, and vibrato
    timing. The result is a rich, shimmering choir pad that sounds
    organic and alive — entirely from code.

    Args:
        freq: Base pitch in Hz.
        num_samples: Number of output samples.
        vowel: Vowel for the choir.
        voices: Number of choir voices (3-8 typical).
        detune_cents: Maximum detuning between voices.
        breathiness: Breath amount per voice.
        formant_shift_range: Random formant shift range (semitones).

    Returns:
        Float32 array — the choir.
    """
    result = np.zeros(num_samples, dtype=np.float64)
    rng = np.random.RandomState(42)

    for v in range(voices):
        # Each voice gets slightly different pitch, formant, vibrato
        detune = (rng.uniform(-1, 1) * detune_cents)
        voice_freq = freq * (2.0 ** (detune / 1200.0))
        fshift = rng.uniform(-formant_shift_range, formant_shift_range)
        vib_rate = 4.5 + rng.uniform(-1, 1) * 1.0  # 3.5-5.5 Hz
        vib_depth = 0.15 + rng.uniform(-0.03, 0.03)

        voice = generate_vocal(
            voice_freq, num_samples,
            vowel=vowel,
            breathiness=max(0.0, breathiness + rng.uniform(-0.02, 0.02)),
            vibrato_rate=vib_rate,
            vibrato_depth=vib_depth,
            formant_shift=fshift,
        )

        # Staggered onset: each voice enters at a slightly different time
        # (real choirs don't start at exactly the same sample — this adds
        # depth and prevents that "all voices are one voice" thinness)
        offset = int(rng.uniform(0, min(800, num_samples // 8)))
        if offset > 0 and offset < num_samples:
            delayed = np.zeros(num_samples, dtype=np.float64)
            delayed[offset:] = voice[:num_samples - offset].astype(np.float64)
            result += delayed
        else:
            result += voice.astype(np.float64)

    # Normalize and apply soft clip to preserve choir loudness
    peak = np.max(np.abs(result))
    if peak > 0:
        result = result / peak * 1.5  # boost choir (slightly more than before)
        result = np.tanh(result) * 0.95  # soft limit

    return result.astype(np.float32)


def generate_vocal_chop(
    freq: float,
    num_samples: int,
    vowel: str = "ah",
    chop_steps: int = 4,
) -> np.ndarray:
    """
    Generate a rhythmic vocal chop — the "hey! yeah! oh!" of EDM.

    Short vowel bursts with sharp attack and quick decay, designed to
    be sequenced as rhythmic elements.

    Args:
        freq: Pitch in Hz.
        num_samples: Number of output samples.
        vowel: Vowel sound for the chop.
        chop_steps: How many chops to fit in the duration.

    Returns:
        Float32 array — rhythmic vocal chops.
    """
    # Generate full vocal
    voice = generate_vocal(
        freq, num_samples,
        vowel=vowel,
        breathiness=0.1,
        vibrato_rate=0.0,   # no vibrato on chops — clean and tight
        vibrato_depth=0.0,
    )

    # Apply rhythmic gating
    chop_len = num_samples // max(chop_steps, 1)
    gate = np.zeros(num_samples, dtype=np.float32)
    for c in range(chop_steps):
        start = c * chop_len
        attack = min(chop_len // 8, 100)
        sustain = chop_len // 3
        release = min(chop_len // 4, 200)

        # Quick attack, short sustain, medium release
        if start + attack <= num_samples:
            gate[start:start + attack] = np.linspace(0, 1, attack)
        hold_end = min(start + attack + sustain, num_samples)
        gate[start + attack:hold_end] = 1.0
        rel_end = min(hold_end + release, num_samples)
        if rel_end > hold_end:
            gate[hold_end:rel_end] = np.linspace(1, 0, rel_end - hold_end)

    return (voice * gate).astype(np.float32)


# ---------------------------------------------------------------------------
# Distortion / Saturation
# ---------------------------------------------------------------------------

def apply_distortion(samples: np.ndarray, drive: float = 2.0) -> np.ndarray:
    """
    Apply soft-clipping distortion using tanh saturation.

    Adds harmonics and warmth. Low drive (1-2) = subtle warmth,
    high drive (4-8) = aggressive crunch.

    Args:
        samples: Float32 audio buffer.
        drive: Distortion amount (1.0 = mild, 8.0 = heavy).

    Returns:
        Distorted float32 array, normalized to [-1, 1].
    """
    return np.tanh(samples.astype(np.float64) * drive).astype(np.float32)


# ---------------------------------------------------------------------------
# High-Pass Filter
# ---------------------------------------------------------------------------

def _design_highpass_biquad(cutoff_hz: float, resonance: float) -> np.ndarray:
    """Design 2nd-order resonant highpass biquad (Audio EQ Cookbook)."""
    cutoff_hz = max(20.0, min(cutoff_hz, SAMPLE_RATE * 0.45))
    resonance = max(0.0, min(resonance, 0.95))
    w0 = 2.0 * math.pi * cutoff_hz / SAMPLE_RATE
    Q = 0.5 / max(1.0 - resonance * 0.99, 0.01)
    alpha = math.sin(w0) / (2.0 * Q)
    cos_w0 = math.cos(w0)
    b0 = (1.0 + cos_w0) / 2.0
    b1 = -(1.0 + cos_w0)
    b2 = (1.0 + cos_w0) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha
    return np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]])


def apply_highpass(samples: np.ndarray, cutoff_hz: float,
                   resonance: float = 0.0) -> np.ndarray:
    """
    Apply a 2-pole resonant high-pass filter.

    Removes low frequencies below the cutoff. Useful for thinning out
    sounds, cleaning up mud, or creating telephone/radio effects.

    Args:
        samples: Mono float32 audio buffer.
        cutoff_hz: Filter cutoff frequency in Hz.
        resonance: Resonance amount (0.0-0.95).

    Returns:
        Filtered float32 array.
    """
    if _HAS_SCIPY:
        sos = _design_highpass_biquad(cutoff_hz, resonance)
        return _sosfilt(sos, samples).astype(np.float32)
    # Python fallback: simple 1-pole highpass
    rc = 1.0 / (2.0 * math.pi * max(cutoff_hz, 20.0))
    dt_val = 1.0 / SAMPLE_RATE
    alpha_hp = rc / (rc + dt_val)
    out = np.empty_like(samples)
    prev_in = 0.0
    prev_out = 0.0
    for i in range(len(samples)):
        out[i] = alpha_hp * (prev_out + float(samples[i]) - prev_in)
        prev_in = float(samples[i])
        prev_out = float(out[i])
    return out.astype(np.float32)


# ---------------------------------------------------------------------------
# ADSR Envelope
# ---------------------------------------------------------------------------

@dataclass
class ADSR:
    """
    Attack-Decay-Sustain-Release amplitude envelope.

    All time values are in seconds. Sustain is a level (0.0–1.0).
    Supports both linear and exponential curves.

    Attributes:
        attack:  Ramp-up time from 0 to peak (seconds).
        decay:   Fall time from peak to sustain level (seconds).
        sustain: Steady-state amplitude (0.0–1.0).
        release: Fade-out time from sustain to 0 (seconds).
        curve: Exponent for envelope curves. 1.0 = linear, 2.0 = quadratic,
               0.5 = square root. Higher = snappier attack, smoother decay.
    """

    attack: float = 0.010
    decay: float = 0.050
    sustain: float = 0.70
    release: float = 0.100
    curve: float = 1.0  # 1.0 = linear (backwards compatible)

    def _shaped(self, start: float, end: float, n: int) -> np.ndarray:
        """Generate a shaped curve segment from start to end over n samples."""
        if n <= 0:
            return np.array([], dtype=np.float32)
        t = np.linspace(0.0, 1.0, n, dtype=np.float64)
        if self.curve != 1.0:
            if start < end:  # attack — use power curve for snappy rise
                t = t ** (1.0 / max(self.curve, 0.1))
            else:  # decay/release — use power curve for natural falloff
                t = t ** max(self.curve, 0.1)
        return (start + (end - start) * t).astype(np.float32)

    def apply(self, samples: np.ndarray) -> np.ndarray:
        """
        Apply this ADSR envelope to a sample buffer.

        If the buffer is shorter than A+D+R, all segments scale proportionally
        so the envelope always covers the full buffer.

        Args:
            samples: Float32 audio samples, shape (N,).

        Returns:
            Envelope-shaped float32 array, same shape as input.
        """
        n = len(samples)
        if n == 0:
            return samples

        a = int(self.attack * SAMPLE_RATE)
        d = int(self.decay * SAMPLE_RATE)
        r = int(self.release * SAMPLE_RATE)

        # If A + D + R exceeds buffer length, scale each segment proportionally
        if a + d + r > n:
            total = a + d + r
            a = int(a / total * n)
            d = int(d / total * n)
            r = n - a - d

        s = max(0, n - a - d - r)

        parts: list[np.ndarray] = []
        if a > 0:
            parts.append(self._shaped(0.0, 1.0, a))
        if d > 0:
            parts.append(self._shaped(1.0, self.sustain, d))
        if s > 0:
            parts.append(np.full(s, self.sustain, dtype=np.float32))
        if r > 0:
            parts.append(self._shaped(self.sustain, 0.0, r))

        if not parts:
            return samples

        env = np.concatenate(parts)

        # Handle floating-point rounding to guarantee exact length
        if len(env) < n:
            env = np.pad(env, (0, n - len(env)), constant_values=0.0)
        elif len(env) > n:
            env = env[:n]

        return (samples * env).astype(np.float32)


# ---------------------------------------------------------------------------
# MIDI / Frequency Utilities
# ---------------------------------------------------------------------------

def note_to_freq(midi_note: int, a4_hz: float = 440.0) -> float:
    """
    Convert a MIDI note number to frequency in Hz.

    Middle C = C4 = MIDI 60 = 261.63 Hz.

    Args:
        midi_note: MIDI note number (0–127).
        a4_hz: Tuning reference for A4 (default 440.0 Hz).

    Returns:
        Frequency in Hz as float.
    """
    return a4_hz * (2.0 ** ((midi_note - 69) / 12.0))


# ---------------------------------------------------------------------------
# Just Intonation — Pure Harmonic Ratios
# ---------------------------------------------------------------------------

# Just intonation ratios relative to the root of the current chord.
# These produce beatless, crystalline intervals impossible in equal temperament.
JUST_RATIOS: dict[int, float] = {
    0: 1.0,          # unison
    1: 16/15,        # minor second
    2: 9/8,          # major second
    3: 6/5,          # minor third
    4: 5/4,          # major third
    5: 4/3,          # perfect fourth
    6: 45/32,        # tritone (augmented fourth)
    7: 3/2,          # perfect fifth
    8: 8/5,          # minor sixth
    9: 5/3,          # major sixth
    10: 9/5,         # minor seventh
    11: 15/8,        # major seventh
}


def just_intonation_freq(midi_note: int, chord_root_midi: int = 60) -> float:
    """
    Compute frequency using just intonation relative to a chord root.

    Instead of equal temperament (every semitone = 2^(1/12)), uses pure
    harmonic ratios. Produces beatless, crystalline intervals.

    Args:
        midi_note: The MIDI note to tune.
        chord_root_midi: The MIDI note of the current chord root.

    Returns:
        Frequency in Hz, tuned to just intonation.
    """
    root_freq = note_to_freq(chord_root_midi)
    interval = (midi_note - chord_root_midi) % 12
    octave_offset = (midi_note - chord_root_midi) // 12
    ratio = JUST_RATIOS.get(interval, 2.0 ** (interval / 12.0))
    return root_freq * ratio * (2.0 ** octave_offset)


# ---------------------------------------------------------------------------
# Additive Synthesis — Build Timbres from Harmonic Partials
# ---------------------------------------------------------------------------

def generate_additive(
    freq: float,
    num_samples: int,
    harmonics: list[float] | None = None,
    harmonic_decay: float = 0.7,
    num_harmonics: int = 12,
) -> np.ndarray:
    """
    Additive synthesis: build a timbre from individual sine wave partials.

    Each harmonic is a sine wave at integer multiples of the fundamental.
    This creates timbres impossible with any single waveform — richer than
    saw, warmer than square, more controllable than either.

    Args:
        freq: Fundamental frequency in Hz.
        num_samples: Number of output samples.
        harmonics: Explicit amplitudes for each harmonic (1st, 2nd, 3rd...).
                   If None, uses exponential decay series.
        harmonic_decay: Decay factor per harmonic if harmonics is None.
                        0.5 = bright (slow decay), 0.9 = dark (fast decay).
        num_harmonics: Number of harmonics to generate if harmonics is None.

    Returns:
        Float32 array in range [-1, 1].
    """
    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE

    if harmonics is None:
        harmonics = [harmonic_decay ** i for i in range(num_harmonics)]

    result = np.zeros(num_samples, dtype=np.float64)
    nyquist = SAMPLE_RATE / 2.0

    for i, amp in enumerate(harmonics):
        partial_freq = freq * (i + 1)
        if partial_freq >= nyquist:
            break
        if abs(amp) < 0.001:
            continue
        result += amp * np.sin(2.0 * np.pi * partial_freq * t)

    # Normalize and soft clip: many harmonics summed can exceed [-1,1]
    peak = np.max(np.abs(result))
    if peak > 0:
        result = result / peak
        result = np.tanh(result * 1.2) / np.tanh(1.2)

    return result.astype(np.float32)


# Preset harmonic profiles for additive synthesis
HARMONIC_PROFILES: dict[str, list[float]] = {
    # Warm — strong fundamental, gentle odd harmonics (clarinet-like)
    "warm": [1.0, 0.0, 0.3, 0.0, 0.15, 0.0, 0.08, 0.0, 0.04, 0.0, 0.02, 0.0],
    # Bright — all harmonics present, slow decay (trumpet-like)
    "bright": [1.0, 0.8, 0.6, 0.5, 0.4, 0.32, 0.25, 0.2, 0.16, 0.12, 0.09, 0.07],
    # Hollow — only odd harmonics (square wave family, but smoother)
    "hollow": [1.0, 0.0, 0.33, 0.0, 0.2, 0.0, 0.14, 0.0, 0.11, 0.0, 0.09, 0.0],
    # Bell — inharmonic-ish: strong 1st, 3rd, 5th, 7th (metallic shimmer)
    "bell": [1.0, 0.1, 0.6, 0.05, 0.4, 0.03, 0.3, 0.02, 0.2, 0.01, 0.15, 0.01],
    # Organ — even and odd harmonics, church organ character
    "organ": [1.0, 0.5, 0.3, 0.25, 0.2, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.04],
    # Glass — sparse, high partials emphasized (ethereal)
    "glass": [0.3, 0.1, 0.5, 0.05, 0.8, 0.02, 0.4, 0.01, 1.0, 0.01, 0.3, 0.2],
    # String — even harmonics present but weaker (bowed string approximation)
    "string": [1.0, 0.6, 0.4, 0.35, 0.25, 0.2, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05],
    # Flute — pure fundamental with gentle harmonics, breathy
    "flute": [1.0, 0.15, 0.05, 0.03, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    # Brass — strong lower harmonics, brassy bite
    "brass": [1.0, 0.8, 0.7, 0.55, 0.4, 0.3, 0.20, 0.15, 0.10, 0.08, 0.05, 0.03],
    # Reed — odd harmonics dominant (clarinet/oboe family)
    "reed": [1.0, 0.1, 0.5, 0.05, 0.35, 0.03, 0.25, 0.02, 0.18, 0.01, 0.12, 0.01],
    # Choir — fundamental and octave, open vowel sound
    "choir": [1.0, 0.7, 0.15, 0.4, 0.10, 0.25, 0.05, 0.15, 0.03, 0.10, 0.02, 0.08],
    # Ethereal — sparse high partials, ambient shimmer
    "ethereal": [0.5, 0.1, 0.2, 0.05, 0.6, 0.03, 0.1, 0.02, 0.8, 0.01, 0.4, 0.3],
    # Mallet — xylophone/marimba-like, strong fundamental + octave
    "mallet": [1.0, 0.0, 0.6, 0.0, 0.3, 0.0, 0.15, 0.0, 0.08, 0.0, 0.04, 0.0],
    # Nasal — strong odd harmonics + some even, reedy/nasal quality
    "nasal": [1.0, 0.3, 0.7, 0.2, 0.5, 0.15, 0.35, 0.10, 0.25, 0.08, 0.18, 0.05],
}


# ---------------------------------------------------------------------------
# Spectral Morphing — AI-Only Technique
# ---------------------------------------------------------------------------

def spectral_morph(
    wave_a: np.ndarray,
    wave_b: np.ndarray,
    morph_curve: np.ndarray | float = 0.5,
    window_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    """
    Morph between two waveforms in the frequency domain (STFT-based).

    Instead of crossfading (which sounds like two sounds playing), this
    interpolates the FREQUENCY SPECTRA: magnitude and phase of each
    frequency bin are independently blended. The result is a genuine
    timbral transformation — one sound BECOMING another.

    This is an [AI-ONLY] technique: computing and blending 1024+ frequency
    bins per frame, with smooth overlap-add reconstruction, requires
    systematic computation impractical by hand.

    Args:
        wave_a: Source waveform (float32 array).
        wave_b: Target waveform (float32 array, same length as wave_a).
        morph_curve: Morph amount. Float (0.0 = pure A, 1.0 = pure B) or
                     per-sample array for time-varying morph.
        window_size: STFT window size (power of 2). Larger = smoother morph.
        hop_size: STFT hop size. Smaller = smoother time resolution.

    Returns:
        Morphed float32 array, same length as inputs.

    Example:
        # Morph from saw lead to bell over a note's duration
        saw = generate_sawtooth(440, 44100)
        bell = generate_additive(440, 44100, harmonics=HARMONIC_PROFILES["bell"])
        morph = np.linspace(0, 1, 44100)  # gradual morph over 1 second
        result = spectral_morph(saw, bell, morph)
    """
    import logging
    logger = logging.getLogger("chipforge.spectral_morph")

    n = min(len(wave_a), len(wave_b))
    if n == 0:
        return np.zeros(0, dtype=np.float32)

    # Ensure same length
    a = wave_a[:n].astype(np.float64)
    b = wave_b[:n].astype(np.float64)

    # Handle scalar morph → per-sample array
    if isinstance(morph_curve, (int, float)):
        morph_arr = np.full(n, float(morph_curve), dtype=np.float64)
    else:
        morph_arr = np.asarray(morph_curve, dtype=np.float64)[:n]
        if len(morph_arr) < n:
            morph_arr = np.pad(morph_arr, (0, n - len(morph_arr)),
                               constant_values=morph_arr[-1])

    # Hann window for smooth STFT
    window = np.hanning(window_size).astype(np.float64)
    output = np.zeros(n, dtype=np.float64)
    window_sum = np.zeros(n, dtype=np.float64)

    num_frames = max(1, (n - window_size) // hop_size + 1)
    logger.debug(f"Spectral morph: {num_frames} frames, window={window_size}, hop={hop_size}")

    for frame_idx in range(num_frames):
        start = frame_idx * hop_size
        end = start + window_size
        if end > n:
            break

        # Get morph value at frame center
        center = start + window_size // 2
        morph_val = float(morph_arr[min(center, n - 1)])

        # Windowed segments
        seg_a = a[start:end] * window
        seg_b = b[start:end] * window

        # FFT
        fft_a = np.fft.rfft(seg_a)
        fft_b = np.fft.rfft(seg_b)

        # Interpolate magnitude and phase independently
        mag_a = np.abs(fft_a)
        mag_b = np.abs(fft_b)
        phase_a = np.angle(fft_a)
        phase_b = np.angle(fft_b)

        # Magnitude: linear interpolation
        mag_morph = mag_a * (1.0 - morph_val) + mag_b * morph_val

        # Phase: circular interpolation (handle wrapping)
        phase_diff = phase_b - phase_a
        # Wrap to [-pi, pi]
        phase_diff = (phase_diff + np.pi) % (2 * np.pi) - np.pi
        phase_morph = phase_a + phase_diff * morph_val

        # Reconstruct
        fft_morph = mag_morph * np.exp(1j * phase_morph)
        frame_out = np.fft.irfft(fft_morph, n=window_size)

        # Overlap-add
        output[start:end] += frame_out * window
        window_sum[start:end] += window * window

    # Normalize by window sum (avoid division by zero)
    mask = window_sum > 1e-8
    output[mask] /= window_sum[mask]

    # Preserve original amplitude range
    peak = np.max(np.abs(output))
    if peak > 0:
        target_peak = max(np.max(np.abs(a)), np.max(np.abs(b)))
        output = output * (target_peak / peak)

    logger.debug(f"Spectral morph complete: peak={np.max(np.abs(output)):.4f}")
    return output.astype(np.float32)


# ---------------------------------------------------------------------------
# Per-Harmonic Envelope Shaping — AI-Only Technique
# ---------------------------------------------------------------------------

def generate_additive_shaped(
    freq: float,
    num_samples: int,
    harmonic_amplitudes: list[float] | None = None,
    harmonic_envelopes: list[ADSR] | None = None,
    num_harmonics: int = 12,
) -> np.ndarray:
    """
    Additive synthesis with independent ADSR envelope per harmonic partial.

    Unlike standard additive synthesis where all harmonics share one envelope,
    this gives each harmonic its OWN amplitude trajectory. This creates
    timbres that EVOLVE over every note's lifetime:
    - A bell: fundamental sustains, upper partials decay quickly
    - A brass: harmonics build up sequentially (low first, high later)
    - A vocal: formant-region harmonics sustain, others are transient

    This is [AI-ONLY]: 12 harmonics × 4 ADSR params = 48 parameters per
    instrument. Tuning by ear is infeasible; AI optimizes against target timbres.

    Args:
        freq: Fundamental frequency in Hz.
        num_samples: Number of output samples.
        harmonic_amplitudes: Peak amplitude for each harmonic (list of floats).
        harmonic_envelopes: Independent ADSR for each harmonic.
        num_harmonics: Number of harmonics if amplitudes not provided.

    Returns:
        Float32 array in [-1, 1].
    """
    import logging
    logger = logging.getLogger("chipforge.additive_shaped")

    t = np.arange(num_samples, dtype=np.float64) / SAMPLE_RATE
    nyquist = SAMPLE_RATE / 2.0

    if harmonic_amplitudes is None:
        harmonic_amplitudes = [0.7 ** i for i in range(num_harmonics)]

    if harmonic_envelopes is None:
        # Default: each higher harmonic decays faster (natural acoustic behavior)
        harmonic_envelopes = [
            ADSR(
                attack=0.005 + i * 0.002,
                decay=max(0.05, 0.4 - i * 0.03),
                sustain=max(0.0, 0.6 - i * 0.08),
                release=max(0.02, 0.2 - i * 0.015),
                curve=1.5,
            )
            for i in range(len(harmonic_amplitudes))
        ]

    result = np.zeros(num_samples, dtype=np.float64)
    active_harmonics = 0

    for i, amp in enumerate(harmonic_amplitudes):
        partial_freq = freq * (i + 1)
        if partial_freq >= nyquist:
            break
        if abs(amp) < 0.001:
            continue

        # Generate partial
        partial = amp * np.sin(2.0 * np.pi * partial_freq * t)

        # Apply this harmonic's own envelope
        if i < len(harmonic_envelopes):
            env = harmonic_envelopes[i]
            partial = env.apply(partial.astype(np.float32)).astype(np.float64)

        result += partial
        active_harmonics += 1

    # Normalize and soft clip: many shaped harmonics can stack above [-1,1]
    peak = np.max(np.abs(result))
    if peak > 0:
        result = result / peak
        result = np.tanh(result * 1.2) / np.tanh(1.2)

    logger.debug(f"Additive shaped: freq={freq:.1f}, harmonics={active_harmonics}, "
                 f"peak={np.max(np.abs(result)):.4f}")
    return result.astype(np.float32)


# Preset harmonic envelope profiles
SHAPED_PROFILES: dict[str, dict] = {
    "evolving_bell": {
        "amplitudes": [1.0, 0.1, 0.6, 0.05, 0.4, 0.03, 0.3, 0.02],
        "envelopes": [
            ADSR(0.002, 0.8, 0.15, 0.4),    # fundamental: long sustain
            ADSR(0.001, 0.05, 0.0, 0.02),    # 2nd: flash
            ADSR(0.003, 0.5, 0.08, 0.3),     # 3rd: medium ring
            ADSR(0.001, 0.03, 0.0, 0.01),    # 4th: flash
            ADSR(0.005, 0.3, 0.05, 0.2),     # 5th: shorter ring
            ADSR(0.001, 0.02, 0.0, 0.01),    # 6th: flash
            ADSR(0.008, 0.2, 0.03, 0.15),    # 7th: brief
            ADSR(0.001, 0.01, 0.0, 0.01),    # 8th: click
        ],
    },
    "brass_swell": {
        "amplitudes": [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.15],
        "envelopes": [
            ADSR(0.05, 0.1, 0.7, 0.15),     # fundamental: quick
            ADSR(0.08, 0.1, 0.65, 0.12),     # 2nd: slightly later
            ADSR(0.12, 0.1, 0.6, 0.10),      # 3rd: building
            ADSR(0.18, 0.1, 0.55, 0.08),     # 4th: later still
            ADSR(0.25, 0.1, 0.5, 0.06),      # 5th: last to arrive
            ADSR(0.30, 0.08, 0.4, 0.05),     # 6th: brief peak
            ADSR(0.35, 0.06, 0.3, 0.04),     # 7th: even later
            ADSR(0.40, 0.05, 0.2, 0.03),     # 8th: barely there
        ],
    },
    "plucked_decay": {
        "amplitudes": [1.0, 0.7, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1],
        "envelopes": [
            ADSR(0.001, 0.3, 0.1, 0.2, curve=2.5),   # fundamental: slow decay
            ADSR(0.001, 0.15, 0.0, 0.1, curve=3.0),   # 2nd: faster decay
            ADSR(0.001, 0.08, 0.0, 0.05, curve=3.5),  # 3rd: even faster
            ADSR(0.001, 0.05, 0.0, 0.03, curve=4.0),  # 4th: quick
            ADSR(0.001, 0.03, 0.0, 0.02, curve=4.0),  # 5th: very quick
            ADSR(0.001, 0.02, 0.0, 0.01, curve=4.0),  # 6th: flash
            ADSR(0.001, 0.015, 0.0, 0.01, curve=4.0), # 7th: click
            ADSR(0.001, 0.01, 0.0, 0.005, curve=4.0), # 8th: tick
        ],
    },
    "vocal_ah": {
        # Simulates "ah" vowel: strong 1st, 2nd, 3rd harmonics (700-2100 Hz region)
        "amplitudes": [1.0, 0.8, 0.6, 0.2, 0.15, 0.3, 0.1, 0.05],
        "envelopes": [
            ADSR(0.05, 0.1, 0.7, 0.2),      # fundamental: vocal onset
            ADSR(0.06, 0.1, 0.65, 0.18),     # 2nd: first formant region
            ADSR(0.07, 0.1, 0.5, 0.15),      # 3rd: second formant
            ADSR(0.08, 0.15, 0.15, 0.1),     # 4th: between formants (weak)
            ADSR(0.09, 0.15, 0.1, 0.08),     # 5th: weak
            ADSR(0.10, 0.1, 0.25, 0.1),      # 6th: third formant hint
            ADSR(0.12, 0.2, 0.05, 0.05),     # 7th: air
            ADSR(0.15, 0.2, 0.02, 0.03),     # 8th: breath
        ],
    },
}


# ---------------------------------------------------------------------------
# Main Synthesis Entry Point
# ---------------------------------------------------------------------------

# Maps waveform name strings to generator functions for non-parameterized cases
_WAVEFORM_MAP = {
    "sine": generate_sine,
    "sawtooth": generate_sawtooth,
    "triangle": generate_triangle,
}


def synthesize_note(
    midi_note: int,
    duration_sec: float,
    waveform: str = "square",
    duty: float = 0.25,
    adsr: Optional[ADSR] = None,
    volume: float = 0.8,
    wavetable: Optional[list[float]] = None,
    filter_cutoff: Optional[float] = None,
    filter_resonance: float = 0.0,
    vibrato_rate: float = 0.0,
    vibrato_depth: float = 0.0,
    pitch_start: Optional[float] = None,
    pitch_end: Optional[float] = None,
    distortion: float = 0.0,
    highpass_cutoff: Optional[float] = None,
    temperament: str = "equal",
    key_root_pc: int = 0,
    freq_override: Optional[float] = None,
) -> np.ndarray:
    """
    Synthesize a single note to a mono float32 buffer.

    Args:
        midi_note: MIDI note number. 0 = rest (silence).
        duration_sec: Duration of the output buffer in seconds.
        waveform: One of: sine, square, sawtooth, triangle, noise_lfsr_7,
                  noise_lfsr_15, white_noise, supersaw, wavetable,
                  additive_<profile>.
        duty: Duty cycle for square wave.
        adsr: ADSR envelope; uses default if None.
        volume: Output amplitude scalar (0.0-1.0).
        wavetable: Custom waveform samples for the 'wavetable' type.
        filter_cutoff: Low-pass filter cutoff in Hz (None = no filter).
        filter_resonance: Filter resonance (0.0-0.95).
        vibrato_rate: LFO rate in Hz for vibrato (0 = off).
        vibrato_depth: Vibrato depth in semitones.
        pitch_start: Override start frequency for pitch sweep (Hz).
        pitch_end: Override end frequency for pitch sweep (Hz).
        distortion: Soft-clip drive amount (0 = off, 1-8 typical).
        highpass_cutoff: High-pass filter cutoff in Hz (None = off).
        temperament: Tuning system — "equal" (default), "just", "pythagorean",
                     "meantone", "werckmeister", or "kirnberger".
        key_root_pc: Tonic pitch class (0=C ... 11=B) for non-equal tunings.

    Returns:
        Float32 numpy array, shape (num_samples,).
    """
    if adsr is None:
        adsr = ADSR()

    num_samples = int(duration_sec * SAMPLE_RATE)

    if midi_note == 0 or num_samples == 0:
        return np.zeros(num_samples, dtype=np.float32)

    if freq_override is not None:
        freq = freq_override
    elif temperament == "equal":
        freq = note_to_freq(midi_note)
    else:
        from .temperament import temper_freq
        freq = temper_freq(midi_note, temperament=temperament, key_root_pc=key_root_pc)

    # Waveforms that support phase-based vibrato
    _vibrato_ok = (
        waveform in ("sine", "square", "sawtooth", "triangle", "wavetable")
        or waveform.startswith("additive_")
        or waveform.startswith("fm_")
        or waveform == "fm"
    )

    # Pitch sweep mode (kick drums, lasers, risers)
    if pitch_start is not None and pitch_end is not None:
        raw = generate_pitch_sweep(pitch_start, pitch_end, num_samples, waveform)
    # Vibrato mode (only for waveforms that support it)
    elif vibrato_rate > 0 and vibrato_depth > 0 and _vibrato_ok:
        raw = generate_with_vibrato(
            freq, num_samples, waveform, vibrato_rate, vibrato_depth,
            duty=duty, wavetable=wavetable,
        )
    # Standard synthesis
    elif waveform == "square":
        raw = generate_square(freq, num_samples, duty)
    elif waveform == "noise_lfsr_7":
        raw = generate_lfsr_noise(num_samples, short_mode=True)
    elif waveform == "noise_lfsr_15":
        raw = generate_lfsr_noise(num_samples, short_mode=False)
    elif waveform == "white_noise":
        raw = generate_white_noise(num_samples)
    elif waveform == "supersaw":
        raw = generate_supersaw(freq, num_samples)
    elif waveform == "fm":
        raw = generate_fm(freq, num_samples)
    elif waveform.startswith("fm_"):
        # fm_<ratio>_<index> e.g. "fm_2_5" = ratio 2.0, index 5.0
        parts = waveform.split("_")
        ratio = float(parts[1]) if len(parts) > 1 else 2.0
        index = float(parts[2]) if len(parts) > 2 else 5.0
        raw = generate_fm(freq, num_samples, mod_ratio=ratio, mod_index=index)
    elif waveform == "karplus" or waveform == "string_pluck":
        raw = generate_karplus_strong(freq, num_samples)
    elif waveform.startswith("karplus_"):
        # karplus_<decay>_<brightness> e.g. "karplus_996_50"
        parts = waveform.split("_")
        decay = float(parts[1]) / 1000.0 if len(parts) > 1 else 0.996
        bright = float(parts[2]) / 100.0 if len(parts) > 2 else 0.5
        raw = generate_karplus_strong(freq, num_samples, decay=decay, brightness=bright)
    elif waveform == "ring_mod":
        raw = generate_ring_mod(freq, num_samples)
    elif waveform.startswith("ring_"):
        parts = waveform.split("_")
        ratio = float(parts[1]) if len(parts) > 1 else 1.5
        raw = generate_ring_mod(freq, num_samples, mod_ratio=ratio)
    elif waveform == "granular":
        raw = generate_granular(freq, num_samples)
    elif waveform.startswith("granular_"):
        src = waveform[9:]
        raw = generate_granular(freq, num_samples, source=src)
    elif waveform == "vocal" or waveform == "vocal_ah":
        raw = generate_vocal(freq, num_samples, vowel="ah")
    elif waveform.startswith("vocal_choir"):
        # vocal_choir or vocal_choir_<vowel>
        v = waveform[12:] if len(waveform) > 12 else "ah"
        raw = generate_vocal_choir(freq, num_samples, vowel=v or "ah")
    elif waveform.startswith("vocal_chop"):
        v = waveform[11:] if len(waveform) > 11 else "ah"
        raw = generate_vocal_chop(freq, num_samples, vowel=v or "ah")
    elif waveform.startswith("vocal_"):
        # vocal_<vowel> or vocal_<vowel>_<end_vowel>
        parts = waveform.split("_")
        vowel = parts[1] if len(parts) > 1 else "ah"
        vowel_end = parts[2] if len(parts) > 2 else None
        raw = generate_vocal(freq, num_samples, vowel=vowel, vowel_end=vowel_end)
    elif waveform == "power_chord":
        raw = generate_power_chord(freq, num_samples)
    elif waveform == "palm_mute":
        raw = generate_power_chord(freq, num_samples, palm_mute=True)
    elif waveform == "chug":
        raw = generate_power_chord(freq, num_samples, chug=True)
    elif waveform == "guitar_lead":
        raw = generate_guitar_lead(freq, num_samples)
    elif waveform == "guitar_trem":
        raw = generate_guitar_trem(freq, num_samples)
    elif waveform == "glottal":
        raw = generate_glottal_pulse(freq, num_samples)
    elif waveform == "pwm":
        raw = generate_pwm(freq, num_samples)
    elif waveform.startswith("pwm_"):
        # pwm_<rate>_<depth> e.g. "pwm_2_30" = 2Hz rate, 0.30 depth
        parts = waveform.split("_")
        rate = float(parts[1]) if len(parts) > 1 else 2.0
        depth = float(parts[2]) / 100.0 if len(parts) > 2 else 0.3
        raw = generate_pwm(freq, num_samples, pwm_rate=rate, pwm_depth=depth)
    elif waveform == "wavetable" and wavetable:
        raw = generate_wavetable(wavetable, freq, num_samples)
    elif waveform.startswith("shaped_"):
        profile_name = waveform[7:]  # e.g. "shaped_evolving_bell" → "evolving_bell"
        profile = SHAPED_PROFILES.get(profile_name, {})
        raw = generate_additive_shaped(
            freq, num_samples,
            harmonic_amplitudes=profile.get("amplitudes"),
            harmonic_envelopes=profile.get("envelopes"),
        )
    elif waveform.startswith("additive_"):
        profile_name = waveform[9:]  # e.g. "additive_warm" → "warm"
        harmonics = HARMONIC_PROFILES.get(profile_name)
        raw = generate_additive(freq, num_samples, harmonics=harmonics)
    elif waveform == "additive":
        raw = generate_additive(freq, num_samples)
    elif waveform in _WAVEFORM_MAP:
        raw = _WAVEFORM_MAP[waveform](freq, num_samples)
    else:
        raw = generate_square(freq, num_samples, 0.25)

    # Apply distortion (pre-filter for richer harmonics)
    if distortion > 0:
        raw = apply_distortion(raw, distortion)

    # Apply low-pass filter
    if filter_cutoff is not None:
        raw = apply_lowpass(raw, filter_cutoff, filter_resonance)

    # Apply high-pass filter
    if highpass_cutoff is not None:
        raw = apply_highpass(raw, highpass_cutoff)

    enveloped = adsr.apply(raw)
    return (enveloped * volume).astype(np.float32)
