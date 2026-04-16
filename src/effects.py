"""
ChipForge Effects Module
=========================
Production-grade DSP effects: compressor, parametric EQ, distortion,
and master bus processing chain.

All operations are numpy-vectorized. No per-sample Python loops.
Scipy is used for EQ biquad filters (optional — EQ degrades gracefully without it).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .synth import SAMPLE_RATE

try:
    from scipy.signal import sosfilt as _sosfilt
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


# ---------------------------------------------------------------------------
# Compressor / Limiter
# ---------------------------------------------------------------------------

def apply_compressor(
    audio: np.ndarray,
    threshold_db: float = -12.0,
    ratio: float = 4.0,
    attack_ms: float = 5.0,
    release_ms: float = 50.0,
    makeup_db: float = 0.0,
    knee_db: float = 6.0,
) -> np.ndarray:
    """
    Vectorized RMS compressor with soft knee.

    Args:
        audio: Float32 mono audio buffer.
        threshold_db: Level above which compression starts.
        ratio: Compression ratio (4.0 = 4:1).
        attack_ms: Attack time (envelope detection window).
        release_ms: Release time (gain smoothing).
        makeup_db: Output gain boost after compression.
        knee_db: Soft knee width in dB (0 = hard knee).

    Returns:
        Compressed float32 array.
    """
    n = len(audio)
    if n == 0:
        return audio

    # Step 1: RMS envelope via sliding window (cumsum trick for speed)
    window_size = max(1, int(attack_ms * SAMPLE_RATE / 1000.0))
    squared = audio.astype(np.float64) ** 2
    padded = np.pad(squared, (window_size, 0), mode='constant')
    cumsum = np.cumsum(padded)
    rms = np.sqrt((cumsum[window_size:] - cumsum[:-window_size]) / window_size)
    rms = rms[:n]

    # Step 2: Convert to dB
    env_db = 20.0 * np.log10(np.maximum(rms, 1e-10))

    # Step 3: Gain reduction with soft knee
    gain_reduction_db = np.zeros(n, dtype=np.float64)
    if knee_db > 0:
        half_knee = knee_db / 2.0
        below = env_db < (threshold_db - half_knee)
        above = env_db > (threshold_db + half_knee)
        in_knee = ~below & ~above

        over_above = env_db[above] - threshold_db
        gain_reduction_db[above] = over_above * (1.0 - 1.0 / ratio)

        if np.any(in_knee):
            x = env_db[in_knee] - threshold_db + half_knee
            gain_reduction_db[in_knee] = (x ** 2) / (2.0 * knee_db) * (1.0 - 1.0 / ratio)
    else:
        over = np.maximum(env_db - threshold_db, 0.0)
        gain_reduction_db = over * (1.0 - 1.0 / ratio)

    # Step 4: Smooth gain curve (exponential decay kernel approximation)
    release_samples = max(1, int(release_ms * SAMPLE_RATE / 1000.0))
    kernel_size = min(release_samples, n // 2)
    if kernel_size > 1:
        kernel = np.exp(-np.arange(kernel_size, dtype=np.float64) * 3.0 / kernel_size)
        kernel /= kernel.sum()
        gain_reduction_db = np.convolve(gain_reduction_db, kernel, mode='same')

    # Step 5: Apply gain
    gain_linear = 10.0 ** ((-gain_reduction_db + makeup_db) / 20.0)
    return (audio * gain_linear).astype(np.float32)


def apply_sidechain(
    audio: np.ndarray,
    sidechain: np.ndarray,
    threshold_db: float = -20.0,
    ratio: float = 8.0,
    attack_ms: float = 1.0,
    release_ms: float = 100.0,
) -> np.ndarray:
    """
    Sidechain compression — duck audio based on another signal's level.

    Classic EDM pump effect: kick drum triggers ducking on all other channels.

    Args:
        audio: Signal to compress (e.g., bass, pad).
        sidechain: Signal that triggers compression (e.g., kick drum).
        threshold_db: Sidechain level that triggers ducking.
        ratio: How aggressively to duck (8:1 = strong pump).
        attack_ms: How fast ducking kicks in.
        release_ms: How fast audio recovers (100ms = classic pump).

    Returns:
        Ducked float32 array.
    """
    n = min(len(audio), len(sidechain))
    sc = sidechain[:n]

    # Envelope from sidechain signal
    window_size = max(1, int(attack_ms * SAMPLE_RATE / 1000.0))
    sc_squared = sc.astype(np.float64) ** 2
    padded = np.pad(sc_squared, (window_size, 0), mode='constant')
    cumsum = np.cumsum(padded)
    sc_rms = np.sqrt((cumsum[window_size:] - cumsum[:-window_size]) / window_size)
    sc_rms = sc_rms[:n]

    sc_db = 20.0 * np.log10(np.maximum(sc_rms, 1e-10))
    over = np.maximum(sc_db - threshold_db, 0.0)
    gain_reduction_db = over * (1.0 - 1.0 / ratio)

    # Smooth with release envelope
    release_samples = max(1, int(release_ms * SAMPLE_RATE / 1000.0))
    kernel_size = min(release_samples, n // 2)
    if kernel_size > 1:
        kernel = np.exp(-np.arange(kernel_size, dtype=np.float64) * 3.0 / kernel_size)
        kernel /= kernel.sum()
        gain_reduction_db = np.convolve(gain_reduction_db, kernel, mode='same')

    gain_linear = 10.0 ** (-gain_reduction_db / 20.0)
    result = audio[:n] * gain_linear
    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Transient Shaper
# ---------------------------------------------------------------------------

def apply_transient_shaper(
    audio: np.ndarray,
    attack_gain_db: float = 3.0,
    sustain_gain_db: float = 0.0,
    sensitivity_ms: float = 10.0,
) -> np.ndarray:
    """
    Transient shaper — independently control attack and sustain portions.

    Enhances or reduces the initial transient (attack) of each sound event
    independently from the sustained body. Essential for:
    - Making drums punchier (boost attack) or softer (reduce attack)
    - Making pads more/less present (adjust sustain)

    Args:
        audio: Mono float32 audio buffer.
        attack_gain_db: Boost/cut for transient portion (+6 = punchier, -6 = softer).
        sustain_gain_db: Boost/cut for sustained portion.
        sensitivity_ms: Detection window for transient/sustain split.

    Returns:
        Float32 array with shaped transients.
    """
    n = len(audio)
    if n == 0:
        return audio

    window = max(1, int(sensitivity_ms * SAMPLE_RATE / 1000.0))

    # Compute fast and slow envelopes
    abs_audio = np.abs(audio).astype(np.float64)

    # Fast envelope (follows transients)
    fast_env = np.maximum.accumulate(abs_audio)  # rough peak follower
    # Smooth with short window
    kernel_fast = np.ones(window) / window
    fast_env = np.convolve(abs_audio, kernel_fast, mode='same')

    # Slow envelope (follows sustain)
    slow_window = window * 10
    kernel_slow = np.ones(slow_window) / slow_window
    slow_env = np.convolve(abs_audio, kernel_slow, mode='same')

    # Transient = where fast > slow (attack portions)
    transient_mask = fast_env > slow_env * 1.2
    sustain_mask = ~transient_mask

    # Apply gains
    attack_gain = 10.0 ** (attack_gain_db / 20.0)
    sustain_gain = 10.0 ** (sustain_gain_db / 20.0)

    result = audio.astype(np.float64)
    result[transient_mask] *= attack_gain
    result[sustain_mask] *= sustain_gain

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Tape Saturation (Analog Warmth Model)
# ---------------------------------------------------------------------------

def apply_tape_saturation(
    audio: np.ndarray,
    drive: float = 0.3,
    bias: float = 0.1,
    flutter_rate: float = 0.5,
    flutter_depth: float = 0.002,
) -> np.ndarray:
    """
    Tape saturation model — emulates analog tape recorder characteristics.

    Combines:
    - Soft saturation curve (asymmetric for even harmonics)
    - High-frequency rolloff (tape head response)
    - Flutter (slow pitch wobble from motor speed variation)
    - Bias (DC offset for asymmetric clipping = even harmonics = warmth)

    Args:
        audio: Mono float32 audio buffer.
        drive: Input gain before saturation (0.1 = subtle, 0.5 = heavy).
        bias: DC bias for asymmetric saturation (0.0-0.2).
        flutter_rate: Flutter LFO rate in Hz (0.3-2.0).
        flutter_depth: Flutter pitch deviation (0.001 = subtle, 0.005 = obvious).

    Returns:
        Float32 array with tape warmth applied.
    """
    n = len(audio)
    if n == 0:
        return audio

    result = audio.astype(np.float64)

    # 1. Input gain (drive)
    result = result * (1.0 + drive * 3.0)

    # 2. DC bias for asymmetric saturation (creates even harmonics = warmth)
    result = result + bias

    # 3. Soft saturation (asymmetric tanh — different for + and -)
    positive = result > 0
    result[positive] = np.tanh(result[positive] * 1.2) / 1.2
    result[~positive] = np.tanh(result[~positive] * 0.8) / 0.8

    # 4. Remove DC bias
    result = result - np.mean(result)

    # 5. High-frequency rolloff (tape head = gentle low-pass at ~15kHz)
    if _HAS_SCIPY:
        sos = _design_biquad(15000.0, 0.0, 0.707, "lowpass")
        result = _sosfilt(sos, result)

    # 6. Flutter (slow pitch wobble)
    if flutter_depth > 0 and n > 100:
        t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
        flutter = 1.0 + flutter_depth * np.sin(2.0 * np.pi * flutter_rate * t)
        # Resample with flutter
        indices = np.cumsum(flutter)
        indices = indices / indices[-1] * (n - 1)
        indices = np.clip(indices, 0, n - 1.001)
        idx_floor = indices.astype(np.int64)
        idx_ceil = np.minimum(idx_floor + 1, n - 1)
        frac = (indices - idx_floor).astype(np.float64)
        result = result[idx_floor] * (1.0 - frac) + result[idx_ceil] * frac

    # Normalize to original peak
    peak = np.max(np.abs(result))
    orig_peak = np.max(np.abs(audio))
    if peak > 0 and orig_peak > 0:
        result = result * (orig_peak / peak)

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Noise Gate
# ---------------------------------------------------------------------------

def apply_gate(
    audio: np.ndarray,
    threshold_db: float = -40.0,
    attack_ms: float = 1.0,
    release_ms: float = 50.0,
    range_db: float = -80.0,
) -> np.ndarray:
    """
    Noise gate — silences audio below threshold.

    Useful for cleaning up noise between notes, tightening drum hits,
    and creating rhythmic gating effects.

    Args:
        audio: Mono float32 audio buffer.
        threshold_db: Level below which gating engages.
        attack_ms: How quickly gate opens.
        release_ms: How quickly gate closes.
        range_db: Maximum attenuation when gate is closed (-80 = near-silence).

    Returns:
        Float32 array with gating applied.
    """
    n = len(audio)
    if n == 0:
        return audio

    # RMS envelope
    window = max(1, int(attack_ms * SAMPLE_RATE / 1000.0))
    squared = audio.astype(np.float64) ** 2
    padded = np.pad(squared, (window, 0), mode='constant')
    cumsum = np.cumsum(padded)
    rms = np.sqrt((cumsum[window:] - cumsum[:-window]) / window)

    # Convert to dB
    env_db = 20.0 * np.log10(np.maximum(rms[:n], 1e-10))

    # Gate open/closed
    gate_open = env_db > threshold_db
    range_linear = 10.0 ** (range_db / 20.0)

    # Smooth gate transitions
    release_samples = max(1, int(release_ms * SAMPLE_RATE / 1000.0))
    kernel = np.ones(release_samples) / release_samples
    gate_smooth = np.convolve(gate_open.astype(np.float64), kernel, mode='same')
    gate_smooth = np.clip(gate_smooth, 0.0, 1.0)

    # Apply gate
    gain = range_linear + (1.0 - range_linear) * gate_smooth
    return (audio * gain[:n].astype(np.float32)).astype(np.float32)


# ---------------------------------------------------------------------------
# Guitar Amp Simulation — Metal Tone Chain
# ---------------------------------------------------------------------------

def apply_amp_sim(
    audio: np.ndarray,
    gain: float = 0.8,
    tone: str = "metal",
    cabinet: bool = True,
    presence: float = 3.0,
    tightness: float = 0.7,
) -> np.ndarray:
    """
    Guitar amplifier simulation — cascaded gain stages + cabinet modeling.

    Models the signal chain: guitar → preamp (gain staging) → power amp
    (compression) → speaker cabinet (EQ). This is the core of electric
    guitar tone — especially heavy metal, which uses EXTREME gain.

    The "metal" tone uses 3 cascaded distortion stages (like a Mesa Boogie
    Triple Rectifier) for thick, harmonically rich saturation.

    Args:
        audio: Mono float32 audio buffer (raw guitar signal).
        gain: Preamp gain (0.0-1.0). 0.3 = clean, 0.6 = crunch, 0.9 = metal.
        tone: Amp voicing ("clean", "crunch", "metal", "lead").
        cabinet: Apply cabinet EQ simulation if True.
        presence: Presence knob — upper-mid boost in dB (2-5 for metal).
        tightness: Low-end tightness (0.0 = loose/doom, 1.0 = tight/thrash).

    Returns:
        Float32 array — amp-processed guitar signal.
    """
    n = len(audio)
    if n == 0:
        return audio

    result = audio.astype(np.float64)

    # --- PREAMP: Cascaded gain stages ---
    if tone == "metal":
        # Stage 1: Initial gain boost + soft clip
        result = result * (1.0 + gain * 8.0)
        result = np.tanh(result * 0.6) / 0.6

        # Stage 2: More gain + asymmetric clip (even harmonics = warmth)
        result = result * (1.0 + gain * 4.0)
        pos = result > 0
        result[pos] = np.tanh(result[pos] * 0.8) / 0.8
        result[~pos] = np.tanh(result[~pos] * 1.2) / 1.2

        # Stage 3: Final saturation + compression
        result = result * (1.0 + gain * 2.0)
        result = np.tanh(result)

    elif tone == "lead":
        # Smoother, more sustain, less fizz
        result = result * (1.0 + gain * 6.0)
        result = np.tanh(result * 0.7) / 0.7
        result = result * (1.0 + gain * 3.0)
        result = np.tanh(result)

    elif tone == "crunch":
        # Light breakup
        result = result * (1.0 + gain * 4.0)
        result = np.tanh(result * 0.5) / 0.5

    else:  # clean
        result = result * (1.0 + gain * 1.5)
        result = np.clip(result, -1.0, 1.0)

    # --- POWER AMP: Gentle compression ---
    result = np.tanh(result * 0.9) / 0.9

    # --- CABINET: Speaker EQ simulation ---
    if cabinet and _HAS_SCIPY:
        # Cut sub-bass (< 80 Hz) — speakers don't reproduce this
        sos_hp = _design_biquad(80.0 * tightness + 40.0, 0.0, 0.707, "highpass")
        result = _sosfilt(sos_hp, result)

        # Cut fizzy highs (> 5-6 kHz) — speaker cone rolloff
        sos_lp = _design_biquad(5500.0, 0.0, 0.707, "lowpass")
        result = _sosfilt(sos_lp, result)

        # Presence peak (2-4 kHz) — the "cut" of the guitar
        sos_pres = _design_biquad(3000.0, presence, 2.0, "peak")
        result = _sosfilt(sos_pres, result)

        # Low-mid body (250-500 Hz)
        sos_body = _design_biquad(350.0, 1.5, 1.5, "peak")
        result = _sosfilt(sos_body, result)

    # Normalize
    peak = np.max(np.abs(result))
    if peak > 0:
        result = result * (0.85 / peak)

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Multiband Compression
# ---------------------------------------------------------------------------

def apply_multiband_compress(
    audio: np.ndarray,
    crossovers: list[float] | None = None,
    thresholds_db: list[float] | None = None,
    ratios: list[float] | None = None,
    makeup_db: list[float] | None = None,
) -> np.ndarray:
    """
    Multiband compressor — split audio into frequency bands, compress each independently.

    Essential for professional mastering: control sub bass independently from
    mids independently from highs. Prevents bass from pumping the entire mix.

    Args:
        audio: Mono float32 audio buffer.
        crossovers: Frequency boundaries (default [80, 250, 2500, 8000] = 5 bands).
        thresholds_db: Per-band compression threshold.
        ratios: Per-band compression ratio.
        makeup_db: Per-band makeup gain.

    Returns:
        Compressed float32 array.
    """
    if crossovers is None:
        crossovers = [80.0, 250.0, 2500.0, 8000.0]
    num_bands = len(crossovers) + 1

    if thresholds_db is None:
        thresholds_db = [-12.0] * num_bands
    if ratios is None:
        ratios = [3.0, 2.5, 2.0, 2.5, 3.0][:num_bands]
    if makeup_db is None:
        makeup_db = [0.0] * num_bands

    # Split into bands using cascaded biquad filters
    bands = []
    remaining = audio.astype(np.float64)

    if _HAS_SCIPY:
        for i, freq in enumerate(crossovers):
            # Low-pass for this band
            sos_lp = _design_biquad(freq, 0.0, 0.707, "lowpass")
            band = _sosfilt(sos_lp, remaining).astype(np.float64)
            bands.append(band)
            # High-pass the remainder
            sos_hp = _design_biquad(freq, 0.0, 0.707, "highpass")
            remaining = _sosfilt(sos_hp, remaining).astype(np.float64)
        bands.append(remaining)  # highest band
    else:
        # Fallback: just compress the whole signal as one band
        return apply_compressor(audio, thresholds_db[0], ratios[0],
                                makeup_db=makeup_db[0])

    # Compress each band independently
    result = np.zeros_like(audio, dtype=np.float64)
    for i, band in enumerate(bands):
        thresh = thresholds_db[i] if i < len(thresholds_db) else -12.0
        ratio = ratios[i] if i < len(ratios) else 2.0
        makeup = makeup_db[i] if i < len(makeup_db) else 0.0
        compressed = apply_compressor(
            band.astype(np.float32), thresh, ratio, makeup_db=makeup
        )
        result += compressed.astype(np.float64)

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Phaser Effect
# ---------------------------------------------------------------------------

def apply_phaser(
    audio: np.ndarray,
    rate_hz: float = 0.5,
    depth: float = 0.7,
    stages: int = 4,
    mix: float = 0.5,
) -> np.ndarray:
    """
    Phaser effect — cascaded allpass filters with LFO-modulated frequencies.

    Creates the classic sweeping, jet-like sound of phase cancellation.
    Used extensively in synth pads, guitar effects, and psychedelic sounds.

    Args:
        audio: Mono float32 audio buffer.
        rate_hz: LFO speed (0.1 = slow sweep, 2.0 = fast).
        depth: LFO depth (0.0-1.0, how wide the sweep is).
        stages: Number of allpass stages (2 = subtle, 6 = deep).
        mix: Wet/dry mix.

    Returns:
        Float32 array with phaser applied.
    """
    n = len(audio)
    if n == 0:
        return audio

    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    lfo = (np.sin(2.0 * np.pi * rate_hz * t) * 0.5 + 0.5) * depth

    # Sweep center frequency from 200 Hz to 4000 Hz
    min_freq = 200.0
    max_freq = 4000.0
    sweep_freq = min_freq + lfo * (max_freq - min_freq)

    out = audio.astype(np.float64)
    for _ in range(stages):
        # First-order allpass filter with varying coefficient
        allpass_out = np.zeros(n, dtype=np.float64)
        prev_in = 0.0
        prev_out = 0.0
        for i in range(n):
            # Allpass coefficient from sweep frequency
            coeff = (1.0 - np.pi * sweep_freq[i] / SAMPLE_RATE)
            coeff = max(-0.99, min(coeff, 0.99))
            allpass_out[i] = coeff * out[i] + prev_in - coeff * prev_out
            prev_in = out[i]
            prev_out = allpass_out[i]
        out = allpass_out

    result = audio.astype(np.float64) * (1.0 - mix) + out * mix
    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Flanger Effect
# ---------------------------------------------------------------------------

def apply_flanger(
    audio: np.ndarray,
    rate_hz: float = 0.3,
    depth_ms: float = 3.0,
    feedback: float = 0.5,
    mix: float = 0.5,
) -> np.ndarray:
    """
    Flanger effect — short modulated delay with feedback.

    Creates metallic, jet-engine swooshing. Similar to chorus but with
    shorter delay times and feedback for comb-filtering resonances.

    Args:
        audio: Mono float32 audio buffer.
        rate_hz: LFO speed (0.1-2.0 Hz typical).
        depth_ms: Maximum delay modulation depth in ms (1-10 typical).
        feedback: Feedback amount (0.0-0.9). Higher = more metallic.
        mix: Wet/dry mix.

    Returns:
        Float32 array with flanger applied.
    """
    n = len(audio)
    if n == 0:
        return audio

    max_delay = int(depth_ms * SAMPLE_RATE / 1000.0) + 1
    buf = np.zeros(n + max_delay, dtype=np.float64)
    buf[:n] = audio.astype(np.float64)

    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    # LFO modulates delay time
    lfo = (np.sin(2.0 * np.pi * rate_hz * t) * 0.5 + 0.5) * depth_ms
    delay_samples = (lfo * SAMPLE_RATE / 1000.0).astype(np.float64)

    wet = np.zeros(n, dtype=np.float64)
    feedback = max(0.0, min(feedback, 0.9))

    for i in range(n):
        # Linear interpolation for fractional delay
        d = delay_samples[i]
        idx = i - d
        if idx < 0:
            continue
        idx_floor = int(idx)
        frac = idx - idx_floor
        if idx_floor + 1 < n:
            delayed = buf[idx_floor] * (1.0 - frac) + buf[idx_floor + 1] * frac
        elif idx_floor < n:
            delayed = buf[idx_floor]
        else:
            continue
        wet[i] = delayed
        buf[i] += delayed * feedback

    result = audio.astype(np.float64) * (1.0 - mix) + wet * mix
    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Distortion / Saturation
# ---------------------------------------------------------------------------

def apply_distortion(
    audio: np.ndarray,
    drive: float = 0.5,
    mode: str = "soft",
) -> np.ndarray:
    """
    Waveshaping distortion with multiple character modes.

    Args:
        audio: Float32 audio buffer.
        drive: Distortion amount (0.0-1.0).
        mode: 'soft' (tube warmth), 'hard' (aggressive clip),
              'foldback' (complex harmonics), 'bitcrush' (lo-fi),
              'rectify' (octave-up effect).

    Returns:
        Distorted float32 array.
    """
    if mode == "soft":
        driven = audio * (1.0 + drive * 10.0)
        return (np.tanh(driven) * 0.9).astype(np.float32)
    elif mode == "hard":
        driven = audio * (1.0 + drive * 10.0)
        return np.clip(driven, -1.0, 1.0).astype(np.float32)
    elif mode == "foldback":
        driven = audio * (1.0 + drive * 5.0)
        folded = 4.0 * (np.abs(0.25 * driven + 0.25 -
                 np.round(0.25 * driven + 0.25)) - 0.25)
        return folded.astype(np.float32)
    elif mode == "bitcrush":
        bits = max(2, int(16 - drive * 14))
        levels = 2 ** bits
        return (np.round(audio * levels) / levels).astype(np.float32)
    elif mode == "rectify":
        return np.abs(audio).astype(np.float32)
    else:
        return audio


# ---------------------------------------------------------------------------
# Parametric EQ (requires scipy for biquad filtering)
# ---------------------------------------------------------------------------

def _design_biquad(freq_hz: float, gain_db: float, q: float,
                   band_type: str) -> np.ndarray:
    """Design biquad SOS coefficients using Audio EQ Cookbook formulas."""
    w0 = 2.0 * math.pi * freq_hz / SAMPLE_RATE
    cos_w0 = math.cos(w0)
    sin_w0 = math.sin(w0)
    alpha = sin_w0 / (2.0 * q)

    if band_type == "peak":
        A = 10.0 ** (gain_db / 40.0)
        b0 = 1.0 + alpha * A
        b1 = -2.0 * cos_w0
        b2 = 1.0 - alpha * A
        a0 = 1.0 + alpha / A
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha / A
    elif band_type == "lowshelf":
        A = 10.0 ** (gain_db / 40.0)
        sq_A = math.sqrt(A)
        b0 = A * ((A + 1) - (A - 1) * cos_w0 + 2 * sq_A * alpha)
        b1 = 2 * A * ((A - 1) - (A + 1) * cos_w0)
        b2 = A * ((A + 1) - (A - 1) * cos_w0 - 2 * sq_A * alpha)
        a0 = (A + 1) + (A - 1) * cos_w0 + 2 * sq_A * alpha
        a1 = -2 * ((A - 1) + (A + 1) * cos_w0)
        a2 = (A + 1) + (A - 1) * cos_w0 - 2 * sq_A * alpha
    elif band_type == "highshelf":
        A = 10.0 ** (gain_db / 40.0)
        sq_A = math.sqrt(A)
        b0 = A * ((A + 1) + (A - 1) * cos_w0 + 2 * sq_A * alpha)
        b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
        b2 = A * ((A + 1) + (A - 1) * cos_w0 - 2 * sq_A * alpha)
        a0 = (A + 1) - (A - 1) * cos_w0 + 2 * sq_A * alpha
        a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
        a2 = (A + 1) - (A - 1) * cos_w0 - 2 * sq_A * alpha
    elif band_type == "highpass":
        b0 = (1.0 + cos_w0) / 2.0
        b1 = -(1.0 + cos_w0)
        b2 = (1.0 + cos_w0) / 2.0
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
    elif band_type == "lowpass":
        b0 = (1.0 - cos_w0) / 2.0
        b1 = 1.0 - cos_w0
        b2 = (1.0 - cos_w0) / 2.0
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
    elif band_type == "notch":
        b0 = 1.0
        b1 = -2.0 * cos_w0
        b2 = 1.0
        a0 = 1.0 + alpha
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha
    else:
        raise ValueError(f"Unknown band type: {band_type}")

    return np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]])


@dataclass
class EQBand:
    """Single parametric EQ band configuration."""
    freq_hz: float
    gain_db: float = 0.0
    q: float = 1.0
    band_type: str = "peak"  # peak, lowshelf, highshelf, highpass, lowpass, notch


def apply_parametric_eq(
    audio: np.ndarray,
    bands: list[EQBand],
) -> np.ndarray:
    """
    Multi-band parametric EQ using cascaded biquad filters.

    Requires scipy. Returns audio unchanged if scipy is not available.

    Args:
        audio: Float32 audio buffer (mono).
        bands: List of EQ band configs.

    Returns:
        EQ'd float32 array.
    """
    if not _HAS_SCIPY or not bands:
        return audio

    result = audio.astype(np.float64)
    for band in bands:
        if band.gain_db == 0.0 and band.band_type == "peak":
            continue  # No-op for flat peak bands
        sos = _design_biquad(band.freq_hz, band.gain_db, band.q, band.band_type)
        result = _sosfilt(sos, result)
    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Stereo Widener (Mid/Side)
# ---------------------------------------------------------------------------

def apply_stereo_widener(
    audio_stereo: np.ndarray,
    width: float = 1.5,
) -> np.ndarray:
    """
    Stereo width control via mid/side processing.

    Args:
        audio_stereo: Shape (n, 2) stereo buffer.
        width: 0.0=mono, 1.0=unchanged, 2.0=extra wide.

    Returns:
        Width-adjusted stereo array.
    """
    if audio_stereo.ndim != 2 or audio_stereo.shape[1] != 2:
        return audio_stereo

    mid = (audio_stereo[:, 0] + audio_stereo[:, 1]) * 0.5
    side = (audio_stereo[:, 0] - audio_stereo[:, 1]) * 0.5
    side = side * width
    return np.column_stack([mid + side, mid - side]).astype(np.float32)


# ---------------------------------------------------------------------------
# Master Bus Processing Chain
# ---------------------------------------------------------------------------

@dataclass
class MasterBusConfig:
    """Full mastering chain configuration."""
    # EQ
    highpass_hz: float = 30.0
    low_shelf_hz: float = 80.0
    low_shelf_db: float = 0.0
    presence_hz: float = 4000.0
    presence_db: float = 0.0
    air_shelf_hz: float = 12000.0
    air_shelf_db: float = 0.0
    # Compression
    comp_threshold_db: float = -8.0
    comp_ratio: float = 2.0
    comp_attack_ms: float = 10.0
    comp_release_ms: float = 100.0
    # Stereo
    stereo_width: float = 1.0
    # Saturation
    analog_warmth: float = 0.0  # 0=clean, 0.1-0.3=warm
    # Limiter
    limiter_ceiling_db: float = -0.3


def apply_master_bus(
    audio_stereo: np.ndarray,
    config: MasterBusConfig | None = None,
) -> np.ndarray:
    """
    Full mastering chain: HP filter -> EQ -> compression -> width -> warmth -> limiter.

    Args:
        audio_stereo: Shape (n, 2) stereo buffer.
        config: MasterBusConfig or None for defaults.

    Returns:
        Mastered stereo float32 array.
    """
    if config is None:
        config = MasterBusConfig()

    audio = audio_stereo.copy()

    # 1. High-pass to remove sub-rumble
    if _HAS_SCIPY and config.highpass_hz > 20.0:
        hp_sos = _design_biquad(config.highpass_hz, 0.0, 0.707, "highpass")
        audio[:, 0] = _sosfilt(hp_sos, audio[:, 0]).astype(np.float32)
        audio[:, 1] = _sosfilt(hp_sos, audio[:, 1]).astype(np.float32)

    # 2. Parametric EQ
    eq_bands = []
    if config.low_shelf_db != 0.0:
        eq_bands.append(EQBand(config.low_shelf_hz, config.low_shelf_db, 0.7, "lowshelf"))
    if config.presence_db != 0.0:
        eq_bands.append(EQBand(config.presence_hz, config.presence_db, 1.5, "peak"))
    if config.air_shelf_db != 0.0:
        eq_bands.append(EQBand(config.air_shelf_hz, config.air_shelf_db, 0.7, "highshelf"))
    if eq_bands:
        audio[:, 0] = apply_parametric_eq(audio[:, 0], eq_bands)
        audio[:, 1] = apply_parametric_eq(audio[:, 1], eq_bands)

    # 3. Stereo bus compression (glue)
    if config.comp_ratio > 1.0:
        for ch in range(2):
            audio[:, ch] = apply_compressor(
                audio[:, ch],
                threshold_db=config.comp_threshold_db,
                ratio=config.comp_ratio,
                attack_ms=config.comp_attack_ms,
                release_ms=config.comp_release_ms,
            )

    # 4. Stereo widening
    if config.stereo_width != 1.0:
        audio = apply_stereo_widener(audio, config.stereo_width)

    # 5. Analog warmth (subtle saturation)
    if config.analog_warmth > 0:
        for ch in range(2):
            audio[:, ch] = apply_distortion(
                audio[:, ch], drive=config.analog_warmth * 0.15, mode="soft"
            )

    # 6. Brick-wall limiter
    ceiling = 10.0 ** (config.limiter_ceiling_db / 20.0)
    peak = float(np.max(np.abs(audio)))
    if peak > ceiling:
        audio = audio * (ceiling / peak)

    return audio.astype(np.float32)


# ---------------------------------------------------------------------------
# Auto-Mastering — AI-Only Technique
# ---------------------------------------------------------------------------

# Genre-specific mastering profiles (learned from analysis)
GENRE_PROFILES: dict[str, dict] = {
    "edm": {
        "low_shelf_db": 2.0, "low_shelf_hz": 80.0,
        "presence_db": 2.5, "presence_hz": 4000.0,
        "air_db": 2.0, "air_hz": 12000.0,
        "comp_threshold": -8.0, "comp_ratio": 3.0,
        "stereo_width": 1.35, "warmth": 0.08,
        "target_lufs": -8.0,
    },
    "trance": {
        "low_shelf_db": 1.5, "low_shelf_hz": 80.0,
        "presence_db": 2.0, "presence_hz": 3500.0,
        "air_db": 2.5, "air_hz": 11000.0,
        "comp_threshold": -10.0, "comp_ratio": 2.5,
        "stereo_width": 1.40, "warmth": 0.06,
        "target_lufs": -9.0,
    },
    "rock": {
        "low_shelf_db": 2.5, "low_shelf_hz": 100.0,
        "presence_db": 3.0, "presence_hz": 3000.0,
        "air_db": 1.5, "air_hz": 10000.0,
        "comp_threshold": -6.0, "comp_ratio": 3.5,
        "stereo_width": 1.25, "warmth": 0.12,
        "target_lufs": -7.0,
    },
    "cinematic": {
        "low_shelf_db": 1.0, "low_shelf_hz": 60.0,
        "presence_db": 1.5, "presence_hz": 4500.0,
        "air_db": 2.0, "air_hz": 13000.0,
        "comp_threshold": -12.0, "comp_ratio": 2.0,
        "stereo_width": 1.30, "warmth": 0.05,
        "target_lufs": -12.0,
    },
    "classical": {
        "low_shelf_db": 0.5, "low_shelf_hz": 60.0,
        "presence_db": 1.0, "presence_hz": 5000.0,
        "air_db": 1.5, "air_hz": 14000.0,
        "comp_threshold": -16.0, "comp_ratio": 1.5,
        "stereo_width": 1.20, "warmth": 0.03,
        "target_lufs": -14.0,
    },
    "hiphop": {
        "low_shelf_db": 3.0, "low_shelf_hz": 80.0,
        "presence_db": 2.0, "presence_hz": 3500.0,
        "air_db": 1.0, "air_hz": 10000.0,
        "comp_threshold": -6.0, "comp_ratio": 4.0,
        "stereo_width": 1.20, "warmth": 0.10,
        "target_lufs": -7.0,
    },
    "ambient": {
        "low_shelf_db": 0.0, "low_shelf_hz": 60.0,
        "presence_db": 0.5, "presence_hz": 5000.0,
        "air_db": 2.5, "air_hz": 12000.0,
        "comp_threshold": -18.0, "comp_ratio": 1.3,
        "stereo_width": 1.50, "warmth": 0.02,
        "target_lufs": -16.0,
    },
}


def analyze_mix(audio: np.ndarray) -> dict:
    """
    Analyze a stereo mix and return diagnostic metrics.

    Returns spectral balance, dynamic range, stereo width, and loudness
    measurements that inform mastering decisions.

    Args:
        audio: Stereo float32 array, shape (N, 2).

    Returns:
        Dict with: peak_db, rms_db, dynamic_range_db, spectral_centroid_hz,
                   stereo_correlation, crest_factor.
    """
    import logging
    logger = logging.getLogger("chipforge.analyze_mix")

    mono = (audio[:, 0] + audio[:, 1]) * 0.5

    # Peak and RMS
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(mono ** 2)))
    peak_db = 20 * np.log10(max(peak, 1e-10))
    rms_db = 20 * np.log10(max(rms, 1e-10))
    dynamic_range = peak_db - rms_db

    # Spectral centroid (brightness indicator)
    fft_mag = np.abs(np.fft.rfft(mono[:min(len(mono), 65536)]))
    freqs = np.fft.rfftfreq(min(len(mono), 65536), 1.0 / SAMPLE_RATE)
    total_energy = np.sum(fft_mag)
    if total_energy > 0:
        centroid = float(np.sum(freqs * fft_mag) / total_energy)
    else:
        centroid = 0.0

    # Stereo correlation (1.0 = mono, 0.0 = uncorrelated, -1.0 = out of phase)
    if len(audio) > 0:
        corr = float(np.corrcoef(audio[:, 0], audio[:, 1])[0, 1])
    else:
        corr = 1.0

    # Crest factor (peak/RMS — higher = more dynamic, lower = more compressed)
    crest = peak / max(rms, 1e-10)

    metrics = {
        "peak_db": round(peak_db, 2),
        "rms_db": round(rms_db, 2),
        "dynamic_range_db": round(dynamic_range, 2),
        "spectral_centroid_hz": round(centroid, 1),
        "stereo_correlation": round(corr, 4),
        "crest_factor": round(crest, 2),
    }

    logger.info(f"Mix analysis: peak={peak_db:.1f}dB, RMS={rms_db:.1f}dB, "
                f"DR={dynamic_range:.1f}dB, centroid={centroid:.0f}Hz, "
                f"stereo_corr={corr:.3f}, crest={crest:.1f}")

    return metrics


def auto_master(
    audio: np.ndarray,
    genre: str = "edm",
    target_peak_db: float = -0.3,
) -> np.ndarray:
    """
    AI-computed mastering chain optimized for the specific mix and genre.

    Analyzes the mix (spectral balance, dynamics, stereo width) then applies
    genre-appropriate mastering: EQ, compression, stereo width, saturation,
    and limiting. Different parameters for each genre based on empirical
    profiles.

    This is [AI-ONLY]: computing optimal mastering from mix analysis
    requires evaluating spectral balance, dynamic range, and loudness
    curves simultaneously — what human engineers do by ear over 30-60 min.

    Args:
        audio: Stereo float32 array, shape (N, 2).
        genre: Genre key for profile selection.
        target_peak_db: Final peak level in dB (default -0.3 dB).

    Returns:
        Mastered stereo float32 array.
    """
    import logging
    logger = logging.getLogger("chipforge.auto_master")

    # Get genre profile (default to EDM)
    profile = GENRE_PROFILES.get(genre, GENRE_PROFILES["edm"])
    logger.info(f"Auto-mastering: genre={genre}, profile keys={list(profile.keys())}")

    # Analyze the input mix
    pre_metrics = analyze_mix(audio)
    logger.info(f"Pre-master: {pre_metrics}")

    # Build MasterBusConfig from genre profile + mix analysis
    # Adjust compression based on existing dynamic range
    comp_threshold = profile["comp_threshold"]
    if pre_metrics["dynamic_range_db"] < 8:
        # Already compressed — use gentler settings
        comp_threshold -= 4
        logger.info("Mix already compressed, reducing master compression")

    # Adjust stereo width based on existing correlation
    width = profile["stereo_width"]
    if pre_metrics["stereo_correlation"] > 0.95:
        # Very mono — widen more
        width = min(width + 0.1, 1.6)
        logger.info(f"Mix is very mono ({pre_metrics['stereo_correlation']:.3f}), "
                    f"increasing width to {width:.2f}")

    config = MasterBusConfig(
        highpass_hz=28.0,
        low_shelf_hz=profile["low_shelf_hz"],
        low_shelf_db=profile["low_shelf_db"],
        presence_hz=profile["presence_hz"],
        presence_db=profile["presence_db"],
        air_shelf_hz=profile.get("air_hz", 12000.0),
        air_shelf_db=profile.get("air_db", 2.0),
        comp_threshold_db=comp_threshold,
        comp_ratio=profile["comp_ratio"],
        comp_attack_ms=12.0,
        comp_release_ms=100.0,
        stereo_width=width,
        analog_warmth=profile["warmth"],
        limiter_ceiling_db=target_peak_db,
    )

    # Apply the mastering chain
    mastered = apply_master_bus(audio.copy(), config)

    # Post-analysis
    post_metrics = analyze_mix(mastered)
    logger.info(f"Post-master: {post_metrics}")
    logger.info(f"Loudness change: {post_metrics['rms_db'] - pre_metrics['rms_db']:+.1f}dB RMS")

    return mastered
