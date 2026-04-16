"""
ChipForge Instrument Presets
=============================
Instrument definitions inspired by the Game Boy DMG APU sound channels.

Each instrument pairs a waveform with an ADSR envelope and optional parameters.
Agents reference instruments by their string key (e.g. "pulse_lead").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .synth import ADSR, FilterEnvelope


# ---------------------------------------------------------------------------
# Voice Layer (for multi-layer / stacked instruments)
# ---------------------------------------------------------------------------

@dataclass
class VoiceLayer:
    """
    A single waveform layer in a multi-layer instrument.

    Real instruments are spectrally rich because multiple sound sources
    contribute simultaneously: a piano has the hammer strike + the string
    body + sympathetic resonance; a violin has the bowed body + the wood +
    the room. Layering 2-4 detuned waveforms gives us the same depth.

    Each layer has its own waveform, ADSR, gain, and small detune offset
    so they don't phase-cancel into a single thin tone.

    Attributes:
        waveform: Waveform key passed to synthesize_note (e.g. "sawtooth").
        gain: Linear amplitude scalar (0.0-1.0). Total of all layers should
              stay around 1.0 to avoid clipping the sum.
        detune_cents: Pitch offset in cents (negative = flat, positive = sharp).
                      ±5 to ±15 is typical for natural ensemble width.
        adsr: Optional per-layer ADSR. If None, uses the parent instrument's.
        duty: Duty cycle for square layers.
        wavetable: Custom wavetable data for "wavetable" layers.
    """

    waveform: str
    gain: float = 1.0
    detune_cents: float = 0.0
    adsr: Optional[ADSR] = None
    duty: float = 0.25
    wavetable: Optional[list[float]] = None


# ---------------------------------------------------------------------------
# Default Wavetable Shapes (Game Boy CH3 style — 32 4-bit samples quantized)
# ---------------------------------------------------------------------------

def _gb_quantize(signal: np.ndarray, steps: int = 16) -> list[float]:
    """Quantize a float array to N steps, mimicking Game Boy 4-bit wave channel."""
    quantized = np.round(signal * (steps / 2 - 0.5)) / (steps / 2 - 0.5)
    return quantized.clip(-1.0, 1.0).tolist()


_t32 = np.linspace(0, 1, 32, endpoint=False)

WAVETABLES: dict[str, list[float]] = {
    # Smooth sine quantized to 4 bits — warm, hollow tone
    "gb_smooth": _gb_quantize(np.sin(2.0 * np.pi * _t32)),
    # Rising sawtooth — buzzy, classic synth
    "gb_sawtooth": _gb_quantize(2.0 * _t32 - 1.0),
    # Descending ramp — reversed saw
    "gb_ramp_down": _gb_quantize(1.0 - 2.0 * _t32),
    # Organ-like double sine
    "gb_organ": _gb_quantize(np.sin(2.0 * np.pi * _t32) + 0.5 * np.sin(4.0 * np.pi * _t32)),
    # Bell-like — fast attack harmonics
    "gb_bell": _gb_quantize(
        np.sin(2.0 * np.pi * _t32)
        + 0.3 * np.sin(6.0 * np.pi * _t32)
        + 0.1 * np.sin(10.0 * np.pi * _t32)
    ),
}


# ---------------------------------------------------------------------------
# Instrument Dataclass
# ---------------------------------------------------------------------------

@dataclass
class Instrument:
    """
    An instrument definition: waveform type + ADSR envelope + optional parameters.

    Attributes:
        name: Human-readable display name.
        waveform: Waveform type key (see synth.py).
        adsr: ADSR envelope parameters.
        duty: Duty cycle for square waveforms (0.125, 0.25, 0.5, 0.75).
        volume: Master volume scalar (0.0–1.0).
        wavetable: Custom wavetable data for 'wavetable' waveform.
        filter_cutoff: Low-pass filter cutoff in Hz (None = bypass).
        filter_resonance: Filter resonance (0.0–0.95).
        pitch_start: Starting frequency for pitch sweep (None = disabled).
        pitch_end: Ending frequency for pitch sweep.
    """

    name: str
    waveform: str
    adsr: ADSR = field(default_factory=ADSR)
    duty: float = 0.25
    volume: float = 0.80
    wavetable: Optional[list[float]] = None
    filter_cutoff: Optional[float] = None
    filter_resonance: float = 0.0
    pitch_start: Optional[float] = None
    pitch_end: Optional[float] = None
    vibrato_rate: float = 0.0
    vibrato_depth: float = 0.0
    filter_env_start: Optional[float] = None
    filter_env_end: Optional[float] = None
    filter_env: Optional[FilterEnvelope] = None  # ADSR-shaped cutoff envelope
    distortion: float = 0.0
    highpass_cutoff: Optional[float] = None
    layers: Optional[list[VoiceLayer]] = None  # extra waveform layers stacked under the main voice


# ---------------------------------------------------------------------------
# Instrument Presets — Game Boy APU Inspired
# ---------------------------------------------------------------------------

PRESETS: dict[str, Instrument] = {

    # -----------------------------------------------------------------------
    # Pulse Channel (GB CH1 / CH2) — Square waves with duty cycle variation
    # -----------------------------------------------------------------------

    "pulse_lead": Instrument(
        name="Pulse Lead",
        waveform="square",
        adsr=ADSR(attack=0.004, decay=0.08, sustain=0.60, release=0.05),
        duty=0.25,          # signature GB quarter-pulse tone
        volume=0.80,
    ),
    "pulse_bass": Instrument(
        name="Pulse Bass",
        waveform="square",
        adsr=ADSR(attack=0.008, decay=0.10, sustain=0.55, release=0.12),
        duty=0.50,          # full square — rounder, fuller bass
        volume=0.85,
    ),
    "pulse_chime": Instrument(
        name="Pulse Chime",
        waveform="square",
        adsr=ADSR(attack=0.002, decay=0.25, sustain=0.00, release=0.15),
        duty=0.125,         # 1/8 duty — very sharp, bell-like ping
        volume=0.70,
    ),
    "pulse_wide": Instrument(
        name="Pulse Wide",
        waveform="square",
        adsr=ADSR(attack=0.005, decay=0.06, sustain=0.65, release=0.08),
        duty=0.75,          # 3/4 duty — inverted pulse, nasal sound
        volume=0.75,
    ),
    "chip_lead": Instrument(
        name="Chip Lead",
        waveform="square",
        adsr=ADSR(attack=0.003, decay=0.12, sustain=0.45, release=0.07),
        duty=0.50,
        volume=0.78,
    ),
    "pulse_arp": Instrument(
        name="Pulse Arpeggio",
        waveform="square",
        adsr=ADSR(attack=0.001, decay=0.04, sustain=0.30, release=0.02),
        duty=0.25,
        volume=0.72,
    ),

    # -----------------------------------------------------------------------
    # Wave / Triangle Channel (GB CH3 analog) — Smooth tones
    # -----------------------------------------------------------------------

    "wave_melody": Instrument(
        name="Wave Melody",
        waveform="triangle",
        adsr=ADSR(attack=0.010, decay=0.05, sustain=0.70, release=0.12),
        volume=0.72,
    ),
    "wave_bass": Instrument(
        name="Wave Bass",
        waveform="triangle",
        adsr=ADSR(attack=0.005, decay=0.08, sustain=0.60, release=0.15),
        volume=0.80,
    ),
    "gb_wavetable": Instrument(
        name="GB Wave Channel",
        waveform="wavetable",
        adsr=ADSR(attack=0.005, decay=0.04, sustain=0.75, release=0.10),
        volume=0.72,
        wavetable=WAVETABLES["gb_smooth"],
    ),
    "gb_organ": Instrument(
        name="GB Organ",
        waveform="wavetable",
        adsr=ADSR(attack=0.015, decay=0.05, sustain=0.80, release=0.20),
        volume=0.65,
        wavetable=WAVETABLES["gb_organ"],
    ),
    "gb_bell_wave": Instrument(
        name="GB Bell Wave",
        waveform="wavetable",
        adsr=ADSR(attack=0.002, decay=0.35, sustain=0.00, release=0.20),
        volume=0.70,
        wavetable=WAVETABLES["gb_bell"],
    ),

    # -----------------------------------------------------------------------
    # Sine / Saw — Classical and modern chip leads
    # -----------------------------------------------------------------------

    "sine_pad": Instrument(
        name="Sine Pad",
        waveform="sine",
        adsr=ADSR(attack=0.200, decay=0.10, sustain=0.60, release=0.40),
        volume=0.55,
    ),
    "sine_bass": Instrument(
        name="Sine Bass",
        waveform="sine",
        adsr=ADSR(attack=0.005, decay=0.15, sustain=0.40, release=0.20),
        volume=0.80,
    ),
    "saw_lead": Instrument(
        name="Sawtooth Lead",
        waveform="sawtooth",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.55, release=0.08),
        volume=0.68,
    ),
    "saw_bass": Instrument(
        name="Sawtooth Bass",
        waveform="sawtooth",
        adsr=ADSR(attack=0.008, decay=0.12, sustain=0.50, release=0.15),
        volume=0.75,
    ),

    # -----------------------------------------------------------------------
    # Noise Channel (GB CH4) — Percussion using LFSR
    # 7-bit LFSR (short mode) = metallic, periodic — hat / click
    # 15-bit LFSR (long mode) = near-white noise — snare / kick
    # -----------------------------------------------------------------------

    "noise_hat": Instrument(
        name="Hi-Hat",
        waveform="noise_lfsr_7",      # 7-bit LFSR = metallic
        adsr=ADSR(attack=0.001, decay=0.035, sustain=0.00, release=0.010),
        volume=0.38,
    ),
    "noise_hat_open": Instrument(
        name="Open Hi-Hat",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.12, sustain=0.00, release=0.05),
        volume=0.42,
    ),
    "noise_snare": Instrument(
        name="Snare",
        waveform="noise_lfsr_15",     # 15-bit LFSR = wide noise
        adsr=ADSR(attack=0.001, decay=0.110, sustain=0.00, release=0.040),
        volume=0.58,
    ),
    "noise_kick": Instrument(
        name="Kick",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.001, decay=0.180, sustain=0.00, release=0.080),
        volume=0.78,
    ),
    "noise_rim": Instrument(
        name="Rimshot",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.055, sustain=0.00, release=0.015),
        volume=0.50,
    ),
    "noise_clap": Instrument(
        name="Clap",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.002, decay=0.080, sustain=0.00, release=0.030),
        volume=0.60,
    ),

    # -----------------------------------------------------------------------
    # Enhanced Drums — pitch sweep + filtered percussion
    # -----------------------------------------------------------------------

    "kick_deep": Instrument(
        name="Deep Kick",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.200, sustain=0.00, release=0.060, curve=2.5),
        volume=0.90,
        pitch_start=180.0,
        pitch_end=38.0,
    ),
    "kick_punchy": Instrument(
        name="Punchy Kick",
        waveform="triangle",
        adsr=ADSR(attack=0.001, decay=0.140, sustain=0.00, release=0.040, curve=3.0),
        volume=0.92,
        pitch_start=250.0,
        pitch_end=45.0,
    ),
    "snare_tight": Instrument(
        name="Tight Snare",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.001, decay=0.090, sustain=0.00, release=0.025, curve=2.0),
        volume=0.65,
        filter_cutoff=6000.0,
        filter_resonance=0.15,
    ),
    "hat_crisp": Instrument(
        name="Crisp Hi-Hat",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.030, sustain=0.00, release=0.008, curve=2.0),
        volume=0.40,
        filter_cutoff=9000.0,
    ),
    "hat_open_shimmer": Instrument(
        name="Shimmer Open Hat",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.180, sustain=0.05, release=0.060, curve=1.5),
        volume=0.38,
        filter_cutoff=7000.0,
        filter_resonance=0.2,
    ),
    "tom_high": Instrument(
        name="High Tom",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.150, sustain=0.00, release=0.040, curve=2.0),
        volume=0.70,
        pitch_start=300.0,
        pitch_end=180.0,
    ),
    "tom_low": Instrument(
        name="Low Tom",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.200, sustain=0.00, release=0.060, curve=2.0),
        volume=0.75,
        pitch_start=200.0,
        pitch_end=80.0,
    ),

    # -----------------------------------------------------------------------
    # Filtered Synth Voices — richer textures
    # -----------------------------------------------------------------------

    "saw_filtered": Instrument(
        name="Filtered Saw",
        waveform="sawtooth",
        adsr=ADSR(attack=0.010, decay=0.15, sustain=0.50, release=0.12, curve=1.5),
        volume=0.65,
        filter_cutoff=3000.0,
        filter_resonance=0.30,
    ),
    "saw_dark": Instrument(
        name="Dark Saw",
        waveform="sawtooth",
        adsr=ADSR(attack=0.015, decay=0.10, sustain=0.55, release=0.15, curve=1.5),
        volume=0.60,
        filter_cutoff=1200.0,
        filter_resonance=0.40,
    ),
    "pulse_warm": Instrument(
        name="Warm Pulse",
        waveform="square",
        adsr=ADSR(attack=0.008, decay=0.12, sustain=0.55, release=0.10, curve=1.5),
        duty=0.50,
        volume=0.70,
        filter_cutoff=2500.0,
        filter_resonance=0.20,
    ),
    "pad_lush": Instrument(
        name="Lush Pad",
        waveform="sawtooth",
        adsr=ADSR(attack=0.300, decay=0.15, sustain=0.55, release=0.50, curve=1.5),
        volume=0.45,
        filter_cutoff=2000.0,
        filter_resonance=0.35,
    ),
    "bass_sub": Instrument(
        name="Sub Bass",
        waveform="sine",
        adsr=ADSR(attack=0.005, decay=0.08, sustain=0.70, release=0.10, curve=1.5),
        volume=0.85,
    ),
    "bass_growl": Instrument(
        name="Growl Bass",
        waveform="sawtooth",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.55, release=0.10, curve=2.0),
        volume=0.80,
        filter_cutoff=800.0,
        filter_resonance=0.50,
    ),
    "lead_bright": Instrument(
        name="Bright Lead",
        waveform="sawtooth",
        adsr=ADSR(attack=0.003, decay=0.08, sustain=0.50, release=0.06, curve=1.5),
        volume=0.72,
        filter_cutoff=5000.0,
        filter_resonance=0.25,
    ),
    "pluck_short": Instrument(
        name="Short Pluck",
        waveform="sawtooth",
        adsr=ADSR(attack=0.001, decay=0.06, sustain=0.00, release=0.03, curve=2.5),
        volume=0.70,
        filter_cutoff=4000.0,
        filter_resonance=0.30,
    ),

    # -----------------------------------------------------------------------
    # Enhanced Synth Voices — using filter envelopes, vibrato, and chorus
    # -----------------------------------------------------------------------

    "lead_vibrato": Instrument(
        name="Vibrato Lead",
        waveform="sawtooth",
        adsr=ADSR(attack=0.008, decay=0.10, sustain=0.55, release=0.12, curve=1.5),
        volume=0.68,
        filter_cutoff=3500.0,
        filter_resonance=0.25,
        vibrato_rate=5.5,
        vibrato_depth=0.25,
    ),
    "lead_expressive": Instrument(
        name="Expressive Lead",
        waveform="sawtooth",
        adsr=ADSR(attack=0.012, decay=0.12, sustain=0.50, release=0.15, curve=1.5),
        volume=0.65,
        filter_env_start=4500.0,
        filter_env_end=1500.0,
        filter_resonance=0.35,
        vibrato_rate=4.0,
        vibrato_depth=0.15,
    ),
    "acid_bass": Instrument(
        name="Acid Bass",
        waveform="sawtooth",
        adsr=ADSR(attack=0.003, decay=0.12, sustain=0.45, release=0.08, curve=2.0),
        volume=0.78,
        filter_env_start=3500.0,
        filter_env_end=400.0,
        filter_resonance=0.65,
    ),
    "bass_smooth": Instrument(
        name="Smooth Bass",
        waveform="sawtooth",
        adsr=ADSR(attack=0.008, decay=0.10, sustain=0.60, release=0.12, curve=1.5),
        volume=0.78,
        filter_cutoff=1200.0,
        filter_resonance=0.30,
        vibrato_rate=3.0,
        vibrato_depth=0.08,
    ),
    "pad_evolving": Instrument(
        name="Evolving Pad",
        waveform="sawtooth",
        adsr=ADSR(attack=0.400, decay=0.20, sustain=0.50, release=0.60, curve=1.5),
        volume=0.42,
        filter_env_start=800.0,
        filter_env_end=3000.0,
        filter_resonance=0.40,
    ),
    "pad_glass": Instrument(
        name="Glass Pad",
        waveform="sawtooth",
        adsr=ADSR(attack=0.250, decay=0.15, sustain=0.55, release=0.45, curve=1.5),
        volume=0.40,
        filter_cutoff=4000.0,
        filter_resonance=0.20,
        vibrato_rate=2.5,
        vibrato_depth=0.10,
    ),
    "shimmer_bell": Instrument(
        name="Shimmer Bell",
        waveform="wavetable",
        adsr=ADSR(attack=0.003, decay=0.40, sustain=0.10, release=0.30, curve=1.5),
        volume=0.55,
        wavetable=WAVETABLES["gb_bell"],
        filter_cutoff=6000.0,
        vibrato_rate=6.0,
        vibrato_depth=0.20,
    ),
    "string_ensemble": Instrument(
        name="String Ensemble",
        waveform="sawtooth",
        adsr=ADSR(attack=0.150, decay=0.10, sustain=0.65, release=0.30, curve=1.5),
        volume=0.50,
        filter_cutoff=2800.0,
        filter_resonance=0.15,
        vibrato_rate=5.0,
        vibrato_depth=0.18,
    ),
    "pluck_mellow": Instrument(
        name="Mellow Pluck",
        waveform="sawtooth",
        adsr=ADSR(attack=0.002, decay=0.15, sustain=0.10, release=0.10, curve=2.0),
        volume=0.65,
        filter_env_start=5000.0,
        filter_env_end=800.0,
        filter_resonance=0.25,
    ),
    # -----------------------------------------------------------------------
    # Additive Synthesis Voices — built from individual harmonics
    # Richer timbres than any single waveform. AI-computed harmonic profiles.
    # -----------------------------------------------------------------------

    "add_warm_lead": Instrument(
        name="Additive Warm Lead",
        waveform="additive_warm",
        adsr=ADSR(attack=0.010, decay=0.12, sustain=0.55, release=0.12, curve=1.5),
        volume=0.65,
        vibrato_rate=5.0,
        vibrato_depth=0.20,
    ),
    "add_bell": Instrument(
        name="Additive Bell",
        waveform="additive_bell",
        adsr=ADSR(attack=0.002, decay=0.40, sustain=0.08, release=0.25, curve=2.0),
        volume=0.55,
    ),
    "add_string": Instrument(
        name="Additive String",
        waveform="additive_string",
        adsr=ADSR(attack=0.120, decay=0.10, sustain=0.60, release=0.25, curve=1.5),
        volume=0.50,
        vibrato_rate=5.5,
        vibrato_depth=0.15,
    ),
    "add_organ": Instrument(
        name="Additive Organ",
        waveform="additive_organ",
        adsr=ADSR(attack=0.008, decay=0.05, sustain=0.75, release=0.15, curve=1.0),
        volume=0.55,
    ),
    "add_glass_pad": Instrument(
        name="Additive Glass Pad",
        waveform="additive_glass",
        adsr=ADSR(attack=0.350, decay=0.20, sustain=0.45, release=0.50, curve=1.5),
        volume=0.40,
        vibrato_rate=2.0,
        vibrato_depth=0.10,
    ),
    "add_bright_lead": Instrument(
        name="Additive Bright Lead",
        waveform="additive_bright",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.50, release=0.08, curve=1.5),
        volume=0.62,
        filter_cutoff=4500.0,
        filter_resonance=0.20,
    ),
    "add_hollow_pad": Instrument(
        name="Additive Hollow Pad",
        waveform="additive_hollow",
        adsr=ADSR(attack=0.300, decay=0.15, sustain=0.55, release=0.40, curve=1.5),
        volume=0.42,
        filter_cutoff=2500.0,
        filter_resonance=0.30,
    ),

    "arp_shimmer": Instrument(
        name="Shimmer Arp",
        waveform="square",
        adsr=ADSR(attack=0.003, decay=0.08, sustain=0.40, release=0.06, curve=1.5),
        duty=0.25,
        volume=0.62,
        filter_cutoff=3500.0,
        filter_resonance=0.20,
        vibrato_rate=4.0,
        vibrato_depth=0.12,
    ),

    # -----------------------------------------------------------------------
    # Extended Drum Kit — wider variety of electronic percussion
    # -----------------------------------------------------------------------

    "kick_808": Instrument(
        name="808 Kick",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.350, sustain=0.00, release=0.100, curve=2.0),
        volume=0.88,
        pitch_start=160.0,
        pitch_end=32.0,
    ),
    "kick_short": Instrument(
        name="Short Kick",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.080, sustain=0.00, release=0.020, curve=3.0),
        volume=0.90,
        pitch_start=220.0,
        pitch_end=50.0,
    ),
    "kick_distorted": Instrument(
        name="Distorted Kick",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.180, sustain=0.00, release=0.050, curve=2.5),
        volume=0.85,
        pitch_start=200.0,
        pitch_end=40.0,
        distortion=3.0,
    ),
    "snare_fat": Instrument(
        name="Fat Snare",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.001, decay=0.200, sustain=0.05, release=0.080, curve=1.5),
        volume=0.65,
        filter_cutoff=3500.0,
        filter_resonance=0.25,
    ),
    "snare_snap": Instrument(
        name="Snap Snare",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.001, decay=0.050, sustain=0.00, release=0.015, curve=3.0),
        volume=0.70,
        filter_cutoff=8000.0,
        filter_resonance=0.10,
    ),
    "snare_lo_fi": Instrument(
        name="Lo-Fi Snare",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.002, decay=0.160, sustain=0.08, release=0.060, curve=1.5),
        volume=0.55,
        filter_cutoff=1800.0,
        filter_resonance=0.45,
    ),
    "snare_808": Instrument(
        name="808 Snare",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.001, decay=0.180, sustain=0.00, release=0.060, curve=2.0),
        volume=0.68,
        filter_cutoff=5000.0,
        filter_resonance=0.20,
        highpass_cutoff=200.0,
    ),
    "clap_big": Instrument(
        name="Big Clap",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.003, decay=0.150, sustain=0.05, release=0.060, curve=1.5),
        volume=0.62,
        filter_cutoff=4000.0,
        filter_resonance=0.30,
    ),
    "clap_tight": Instrument(
        name="Tight Clap",
        waveform="noise_lfsr_15",
        adsr=ADSR(attack=0.001, decay=0.060, sustain=0.00, release=0.020, curve=2.5),
        volume=0.58,
        filter_cutoff=6000.0,
        filter_resonance=0.15,
        highpass_cutoff=400.0,
    ),
    "hat_tight": Instrument(
        name="Tight Hat",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.015, sustain=0.00, release=0.005, curve=2.5),
        volume=0.35,
        filter_cutoff=10000.0,
    ),
    "hat_lo_fi": Instrument(
        name="Lo-Fi Hat",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.040, sustain=0.00, release=0.012, curve=2.0),
        volume=0.35,
        filter_cutoff=4000.0,
        filter_resonance=0.35,
    ),
    "hat_808": Instrument(
        name="808 Hat",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.045, sustain=0.00, release=0.010, curve=2.0),
        volume=0.38,
        filter_cutoff=8000.0,
        highpass_cutoff=5000.0,
    ),
    "crash": Instrument(
        name="Crash Cymbal",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.002, decay=0.600, sustain=0.10, release=0.200, curve=1.5),
        volume=0.35,
        filter_cutoff=8000.0,
        filter_resonance=0.15,
    ),
    "ride": Instrument(
        name="Ride Cymbal",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.300, sustain=0.15, release=0.100, curve=1.5),
        volume=0.32,
        filter_cutoff=6500.0,
        filter_resonance=0.20,
    ),
    "ride_bell": Instrument(
        name="Ride Bell",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.200, sustain=0.10, release=0.080, curve=2.0),
        volume=0.38,
        filter_cutoff=9000.0,
        filter_resonance=0.30,
        highpass_cutoff=3000.0,
    ),
    "cowbell": Instrument(
        name="Cowbell",
        waveform="triangle",
        adsr=ADSR(attack=0.001, decay=0.120, sustain=0.00, release=0.030, curve=2.5),
        volume=0.60,
        filter_cutoff=5000.0,
        pitch_start=800.0,
        pitch_end=540.0,
    ),
    "shaker": Instrument(
        name="Shaker",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.003, decay=0.050, sustain=0.00, release=0.020, curve=1.5),
        volume=0.28,
        filter_cutoff=7000.0,
        highpass_cutoff=3000.0,
    ),
    "tambourine": Instrument(
        name="Tambourine",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.080, sustain=0.05, release=0.040, curve=1.5),
        volume=0.30,
        filter_cutoff=9000.0,
        highpass_cutoff=4000.0,
    ),
    "perc_click": Instrument(
        name="Click",
        waveform="noise_lfsr_7",
        adsr=ADSR(attack=0.001, decay=0.008, sustain=0.00, release=0.003, curve=3.0),
        volume=0.50,
        filter_cutoff=12000.0,
    ),
    "tom_mid": Instrument(
        name="Mid Tom",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.170, sustain=0.00, release=0.050, curve=2.0),
        volume=0.72,
        pitch_start=250.0,
        pitch_end=130.0,
    ),
    "tom_floor": Instrument(
        name="Floor Tom",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.250, sustain=0.00, release=0.080, curve=2.0),
        volume=0.78,
        pitch_start=160.0,
        pitch_end=60.0,
    ),

    # -----------------------------------------------------------------------
    # Supersaw Voices — stacked detuned sawtooths for EDM/trance
    # -----------------------------------------------------------------------

    "supersaw_lead": Instrument(
        name="Supersaw Lead",
        waveform="supersaw",
        adsr=ADSR(attack=0.008, decay=0.12, sustain=0.55, release=0.10, curve=1.5),
        volume=0.58,
        filter_cutoff=4000.0,
        filter_resonance=0.25,
    ),
    "supersaw_pad": Instrument(
        name="Supersaw Pad",
        waveform="supersaw",
        adsr=ADSR(attack=0.300, decay=0.15, sustain=0.50, release=0.45, curve=1.5),
        volume=0.40,
        filter_cutoff=2500.0,
        filter_resonance=0.30,
    ),
    "supersaw_bass": Instrument(
        name="Supersaw Bass",
        waveform="supersaw",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.50, release=0.08, curve=2.0),
        volume=0.72,
        filter_cutoff=1200.0,
        filter_resonance=0.40,
    ),

    # -----------------------------------------------------------------------
    # Extended Bass Voices
    # -----------------------------------------------------------------------

    "bass_808": Instrument(
        name="808 Bass",
        waveform="sine",
        adsr=ADSR(attack=0.003, decay=0.15, sustain=0.65, release=0.15, curve=1.5),
        volume=0.82,
        distortion=1.5,
    ),
    "bass_dirty": Instrument(
        name="Dirty Bass",
        waveform="sawtooth",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.55, release=0.08, curve=2.0),
        volume=0.75,
        filter_cutoff=900.0,
        filter_resonance=0.45,
        distortion=2.5,
    ),
    "bass_pluck": Instrument(
        name="Pluck Bass",
        waveform="sawtooth",
        adsr=ADSR(attack=0.002, decay=0.08, sustain=0.15, release=0.05, curve=2.5),
        volume=0.78,
        filter_env_start=3000.0,
        filter_env_end=500.0,
        filter_resonance=0.35,
    ),
    "bass_wobble": Instrument(
        name="Wobble Bass",
        waveform="sawtooth",
        adsr=ADSR(attack=0.005, decay=0.12, sustain=0.55, release=0.10, curve=1.5),
        volume=0.75,
        filter_cutoff=1500.0,
        filter_resonance=0.55,
        vibrato_rate=3.0,
        vibrato_depth=0.20,
    ),

    # -----------------------------------------------------------------------
    # Extended Lead Voices
    # -----------------------------------------------------------------------

    "lead_thick": Instrument(
        name="Thick Lead",
        waveform="square",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.60, release=0.08, curve=1.5),
        duty=0.50,
        volume=0.68,
        filter_cutoff=3000.0,
        filter_resonance=0.30,
        vibrato_rate=5.0,
        vibrato_depth=0.15,
    ),
    "lead_crystal": Instrument(
        name="Crystal Lead",
        waveform="additive_bright",
        adsr=ADSR(attack=0.003, decay=0.08, sustain=0.50, release=0.10, curve=1.5),
        volume=0.60,
        filter_cutoff=5000.0,
        vibrato_rate=4.5,
        vibrato_depth=0.12,
    ),
    "lead_distorted": Instrument(
        name="Distorted Lead",
        waveform="sawtooth",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.55, release=0.08, curve=1.5),
        volume=0.62,
        filter_cutoff=3500.0,
        filter_resonance=0.25,
        distortion=3.0,
    ),
    "lead_soft": Instrument(
        name="Soft Lead",
        waveform="triangle",
        adsr=ADSR(attack=0.015, decay=0.08, sustain=0.60, release=0.12, curve=1.5),
        volume=0.65,
        filter_cutoff=3000.0,
        vibrato_rate=4.0,
        vibrato_depth=0.10,
    ),

    # -----------------------------------------------------------------------
    # Extended Pad & Atmosphere Voices
    # -----------------------------------------------------------------------

    "pad_dark": Instrument(
        name="Dark Pad",
        waveform="sawtooth",
        adsr=ADSR(attack=0.350, decay=0.20, sustain=0.50, release=0.55, curve=1.5),
        volume=0.38,
        filter_cutoff=800.0,
        filter_resonance=0.40,
    ),
    "pad_choir": Instrument(
        name="Choir Pad",
        waveform="additive_choir",
        adsr=ADSR(attack=0.300, decay=0.15, sustain=0.55, release=0.50, curve=1.5),
        volume=0.42,
        filter_cutoff=3000.0,
        vibrato_rate=3.5,
        vibrato_depth=0.12,
    ),
    "pad_shimmer": Instrument(
        name="Shimmer Pad",
        waveform="additive_ethereal",
        adsr=ADSR(attack=0.350, decay=0.20, sustain=0.45, release=0.55, curve=1.5),
        volume=0.38,
        vibrato_rate=2.0,
        vibrato_depth=0.08,
    ),
    "pad_warm_analog": Instrument(
        name="Warm Analog Pad",
        waveform="square",
        adsr=ADSR(attack=0.250, decay=0.15, sustain=0.55, release=0.40, curve=1.5),
        duty=0.50,
        volume=0.42,
        filter_cutoff=1800.0,
        filter_resonance=0.30,
        vibrato_rate=3.0,
        vibrato_depth=0.10,
    ),

    # -----------------------------------------------------------------------
    # Additive Synthesis — new harmonic profiles
    # -----------------------------------------------------------------------

    "add_flute": Instrument(
        name="Additive Flute",
        waveform="additive_flute",
        adsr=ADSR(attack=0.030, decay=0.08, sustain=0.55, release=0.15, curve=1.5),
        volume=0.58,
        vibrato_rate=5.0,
        vibrato_depth=0.15,
    ),
    "add_brass": Instrument(
        name="Additive Brass",
        waveform="additive_brass",
        adsr=ADSR(attack=0.015, decay=0.08, sustain=0.60, release=0.10, curve=1.5),
        volume=0.60,
        filter_cutoff=4000.0,
        filter_resonance=0.20,
    ),
    "add_reed": Instrument(
        name="Additive Reed",
        waveform="additive_reed",
        adsr=ADSR(attack=0.010, decay=0.10, sustain=0.55, release=0.12, curve=1.5),
        volume=0.55,
        vibrato_rate=5.5,
        vibrato_depth=0.18,
    ),
    "add_mallet": Instrument(
        name="Additive Mallet",
        waveform="additive_mallet",
        adsr=ADSR(attack=0.002, decay=0.25, sustain=0.05, release=0.15, curve=2.0),
        volume=0.60,
    ),
    "add_nasal": Instrument(
        name="Additive Nasal",
        waveform="additive_nasal",
        adsr=ADSR(attack=0.008, decay=0.10, sustain=0.50, release=0.08, curve=1.5),
        volume=0.55,
        filter_cutoff=3500.0,
        filter_resonance=0.30,
    ),
    "add_choir": Instrument(
        name="Additive Choir",
        waveform="additive_choir",
        adsr=ADSR(attack=0.200, decay=0.15, sustain=0.55, release=0.35, curve=1.5),
        volume=0.45,
        vibrato_rate=4.0,
        vibrato_depth=0.12,
    ),
    "add_ethereal": Instrument(
        name="Additive Ethereal",
        waveform="additive_ethereal",
        adsr=ADSR(attack=0.400, decay=0.20, sustain=0.40, release=0.50, curve=1.5),
        volume=0.38,
        vibrato_rate=2.5,
        vibrato_depth=0.08,
    ),

    # -----------------------------------------------------------------------
    # Utility / FX Voices
    # -----------------------------------------------------------------------

    "brass_stab": Instrument(
        name="Brass Stab",
        waveform="additive_brass",
        adsr=ADSR(attack=0.003, decay=0.06, sustain=0.20, release=0.04, curve=2.0),
        volume=0.68,
        filter_cutoff=4500.0,
        filter_resonance=0.20,
    ),
    "organ_warm": Instrument(
        name="Warm Organ",
        waveform="additive_organ",
        adsr=ADSR(attack=0.010, decay=0.05, sustain=0.70, release=0.15, curve=1.0),
        volume=0.55,
        filter_cutoff=2500.0,
        filter_resonance=0.15,
        vibrato_rate=5.5,
        vibrato_depth=0.10,
    ),
    "organ_electric": Instrument(
        name="Electric Organ",
        waveform="additive_organ",
        adsr=ADSR(attack=0.005, decay=0.08, sustain=0.65, release=0.10, curve=1.5),
        volume=0.58,
        filter_cutoff=3500.0,
        distortion=1.5,
    ),
    "pluck_soft": Instrument(
        name="Soft Pluck",
        waveform="triangle",
        adsr=ADSR(attack=0.002, decay=0.12, sustain=0.08, release=0.08, curve=2.0),
        volume=0.62,
        filter_cutoff=3000.0,
    ),
    "pluck_bright": Instrument(
        name="Bright Pluck",
        waveform="sawtooth",
        adsr=ADSR(attack=0.001, decay=0.08, sustain=0.05, release=0.05, curve=2.5),
        volume=0.65,
        filter_env_start=6000.0,
        filter_env_end=1000.0,
        filter_resonance=0.30,
    ),
    "arp_clean": Instrument(
        name="Clean Arp",
        waveform="square",
        adsr=ADSR(attack=0.002, decay=0.06, sustain=0.45, release=0.04, curve=1.5),
        duty=0.25,
        volume=0.60,
        filter_cutoff=3000.0,
    ),
    "arp_acid": Instrument(
        name="Acid Arp",
        waveform="sawtooth",
        adsr=ADSR(attack=0.002, decay=0.10, sustain=0.35, release=0.06, curve=2.0),
        volume=0.65,
        filter_env_start=4000.0,
        filter_env_end=600.0,
        filter_resonance=0.60,
    ),
    "fx_riser": Instrument(
        name="Riser FX",
        waveform="sawtooth",
        adsr=ADSR(attack=0.500, decay=0.10, sustain=0.50, release=0.20, curve=0.5),
        volume=0.45,
        filter_env_start=200.0,
        filter_env_end=6000.0,
        filter_resonance=0.35,
    ),
    "fx_drop": Instrument(
        name="Drop FX",
        waveform="sine",
        adsr=ADSR(attack=0.001, decay=0.400, sustain=0.00, release=0.100, curve=2.0),
        volume=0.70,
        pitch_start=800.0,
        pitch_end=30.0,
    ),
    "noise_texture": Instrument(
        name="Noise Texture",
        waveform="white_noise",
        adsr=ADSR(attack=0.100, decay=0.15, sustain=0.30, release=0.20, curve=1.5),
        volume=0.25,
        filter_cutoff=3000.0,
        filter_resonance=0.20,
    ),

    # -----------------------------------------------------------------------
    # Shaped Additive — Per-harmonic envelope instruments (AI-Only technique)
    # Each harmonic has its own ADSR creating evolving timbres
    # -----------------------------------------------------------------------

    "shaped_bell": Instrument(
        name="Evolving Bell (Shaped)",
        waveform="shaped_evolving_bell",
        adsr=ADSR(attack=0.002, decay=0.6, sustain=0.10, release=0.4, curve=1.5),
        volume=0.55,
    ),
    "shaped_brass": Instrument(
        name="Brass Swell (Shaped)",
        waveform="shaped_brass_swell",
        adsr=ADSR(attack=0.05, decay=0.15, sustain=0.65, release=0.15, curve=1.5),
        volume=0.60,
        filter_cutoff=4000.0,
        filter_resonance=0.20,
    ),
    "shaped_pluck": Instrument(
        name="Natural Pluck (Shaped)",
        waveform="shaped_plucked_decay",
        adsr=ADSR(attack=0.001, decay=0.3, sustain=0.05, release=0.15, curve=2.0),
        volume=0.65,
    ),
    "shaped_vocal": Instrument(
        name="Vocal Ah (Shaped)",
        waveform="shaped_vocal_ah",
        adsr=ADSR(attack=0.05, decay=0.12, sustain=0.60, release=0.20, curve=1.5),
        volume=0.55,
        vibrato_rate=5.5,
        vibrato_depth=0.20,
    ),

    # -----------------------------------------------------------------------
    # FM Synthesis — Yamaha DX7-style metallic/bell/electric piano sounds
    # -----------------------------------------------------------------------

    "fm_bell": Instrument(
        name="FM Bell",
        waveform="fm_3.5_8",  # inharmonic ratio = metallic bell
        adsr=ADSR(attack=0.002, decay=0.6, sustain=0.05, release=0.4, curve=2.0),
        volume=0.55,
    ),
    "fm_epiano": Instrument(
        name="FM Electric Piano",
        waveform="fm_2_3",  # harmonic ratio, moderate index = Rhodes-like
        adsr=ADSR(attack=0.003, decay=0.3, sustain=0.20, release=0.25, curve=2.0),
        volume=0.65,
    ),
    "fm_bass": Instrument(
        name="FM Bass",
        waveform="fm_1_6",  # unison ratio, high index = punchy bass
        adsr=ADSR(attack=0.002, decay=0.15, sustain=0.40, release=0.10, curve=2.5),
        volume=0.75,
    ),
    "fm_metallic": Instrument(
        name="FM Metallic",
        waveform="fm_7_12",  # high ratio + high index = extreme metallic
        adsr=ADSR(attack=0.001, decay=0.4, sustain=0.0, release=0.2, curve=2.5),
        volume=0.50,
    ),
    "fm_pad": Instrument(
        name="FM Pad",
        waveform="fm_2_2",  # gentle FM, warm evolving pad
        adsr=ADSR(attack=0.300, decay=0.15, sustain=0.55, release=0.40, curve=1.5),
        volume=0.45,
    ),
    "fm_organ": Instrument(
        name="FM Organ",
        waveform="fm_1_1",  # subtle FM, organ-like
        adsr=ADSR(attack=0.008, decay=0.05, sustain=0.75, release=0.12, curve=1.0),
        volume=0.60,
    ),

    # -----------------------------------------------------------------------
    # Egyptian / Middle-Eastern twang — sitar-like, Phrygian resonance
    # -----------------------------------------------------------------------
    # Uses FM at non-integer ratio (1.5 = between octave and fifth) which
    # produces the characteristic inharmonic metallic ring. High resonance
    # filter at 2800 Hz gives the nasal "twang." Fast decay + low sustain
    # reads as plucked oud/sitar. Vibrato at 6 Hz adds the pitch bend.

    # -----------------------------------------------------------------------
    # Harpsichord — Karplus-Strong with bright attack, short decay
    # -----------------------------------------------------------------------
    # Classic Baroque continuo instrument. Bright pluck, rapid decay, no
    # sustain — reads as harpsichord at any tempo. High filter cutoff + KS
    # brightness parameter makes it "jangly" not "warm guitar."

    "harpsichord": Instrument(
        name="Harpsichord",
        waveform="karplus_990_70",     # short sustain, bright
        adsr=ADSR(attack=0.001, decay=0.18, sustain=0.05, release=0.10, curve=3.0),
        volume=0.58,
        filter_cutoff=6000.0,          # bright, jangly
        filter_resonance=0.30,
    ),

    "harpsichord_soft": Instrument(
        name="Harpsichord (Soft)",
        waveform="karplus_994_50",     # longer sustain, softer brightness
        adsr=ADSR(attack=0.002, decay=0.28, sustain=0.08, release=0.15, curve=2.5),
        volume=0.50,
        filter_cutoff=4500.0,
        filter_resonance=0.22,
    ),

    # -----------------------------------------------------------------------
    # Piano — pulse + FM hybrid with hammer-like attack
    # -----------------------------------------------------------------------
    # Not a sampled piano — a chiptune approximation. FM at ratio 1:1 (warm)
    # with quick attack and medium decay. Reads as "piano-ish" against other
    # chip instruments. The low distortion adds harmonic richness.

    "piano_chip": Instrument(
        name="Chip Piano",
        waveform="fm_1_2",            # warm FM (same as accordion base, different ADSR)
        adsr=ADSR(attack=0.003, decay=0.30, sustain=0.20, release=0.18, curve=2.0),
        volume=0.60,
        filter_cutoff=4000.0,
        filter_resonance=0.20,
        distortion=0.4,               # slight warmth
    ),

    "piano_bright": Instrument(
        name="Chip Piano (Bright)",
        waveform="fm_1_3",
        adsr=ADSR(attack=0.002, decay=0.25, sustain=0.15, release=0.15, curve=2.5),
        volume=0.55,
        filter_cutoff=5500.0,
        filter_resonance=0.28,
    ),

    # -----------------------------------------------------------------------
    # Egyptian / Middle-Eastern twang — sitar-like, Phrygian resonance
    # -----------------------------------------------------------------------

    "egyptian_twang": Instrument(
        name="Egyptian Twang",
        waveform="fm_1.5_6",       # non-integer ratio = metallic/bell-like
        adsr=ADSR(attack=0.003, decay=0.35, sustain=0.12, release=0.20, curve=2.5),
        volume=0.62,
        vibrato_rate=6.0,           # fast pitch bend ornament
        vibrato_depth=0.35,         # wide — microtonal Middle-Eastern feel
        filter_cutoff=2800.0,       # nasal twang peak
        filter_resonance=0.55,      # high resonance = the "twang"
        distortion=0.8,             # slight grit
    ),

    "egyptian_twang_deep": Instrument(
        name="Egyptian Twang (Deep)",
        waveform="fm_1.5_4",       # less modulation — warmer, darker
        adsr=ADSR(attack=0.005, decay=0.45, sustain=0.15, release=0.25, curve=2.0),
        volume=0.58,
        vibrato_rate=5.2,
        vibrato_depth=0.28,
        filter_cutoff=2200.0,
        filter_resonance=0.48,
        distortion=0.5,
    ),

    # -----------------------------------------------------------------------
    # Accordion / Concertina — FM reed + bellows tremolo
    # -----------------------------------------------------------------------
    # Reed-like FM at ratio 1:1 (like fm_organ but with vibrato for bellows
    # wobble). The vibrato at 5.5 Hz / 0.18 semitones creates the classic
    # accordion "breathing" feel. Filter at 3500 Hz warms the reed tone.
    # Fast attack for responsiveness. Good for polka, Irish, folk, waltz.

    "accordion": Instrument(
        name="Accordion (Gritty)",
        waveform="fm_1_4",          # ratio 1:1, index 4 — buzzy reed, overtones
        adsr=ADSR(attack=0.010, decay=0.06, sustain=0.78, release=0.08, curve=1.0),
        volume=0.65,
        vibrato_rate=5.8,           # bellows tremolo
        vibrato_depth=0.22,         # wider wobble — rougher
        filter_cutoff=4200.0,       # brighter so the grit reads
        filter_resonance=0.35,      # resonant peak adds edge
        distortion=1.8,             # soft-clip crunch — the grit
    ),

    "accordion_bright": Instrument(
        name="Accordion (Bright/Dirty)",
        waveform="fm_1_5",          # high FM index = aggressive buzz
        adsr=ADSR(attack=0.008, decay=0.04, sustain=0.80, release=0.06, curve=0.8),
        volume=0.60,
        vibrato_rate=6.5,
        vibrato_depth=0.28,         # wide bellows shake
        filter_cutoff=5500.0,       # opens up the dirt
        filter_resonance=0.40,      # nasty resonant peak
        distortion=2.5,             # more aggressive
    ),

    "concertina": Instrument(
        name="Concertina",
        waveform="fm_1_3",          # moderate FM — still has character
        adsr=ADSR(attack=0.018, decay=0.08, sustain=0.70, release=0.12, curve=1.2),
        volume=0.58,
        vibrato_rate=5.0,
        vibrato_depth=0.18,
        filter_cutoff=3800.0,
        filter_resonance=0.28,
        distortion=1.2,
    ),

    # -----------------------------------------------------------------------
    # Karplus-Strong — Physical modeling plucked strings
    # -----------------------------------------------------------------------

    "ks_guitar": Instrument(
        name="KS Acoustic Guitar",
        waveform="karplus_996_30",  # long sustain, softened brightness
        adsr=ADSR(attack=0.003, decay=0.5, sustain=0.10, release=0.3, curve=2.0),
        volume=0.65,
        filter_cutoff=3500.0,  # tame high-end twang
    ),
    "ks_harp": Instrument(
        name="KS Harp",
        waveform="karplus_994_40",  # medium sustain, moderate brightness
        adsr=ADSR(attack=0.003, decay=0.4, sustain=0.05, release=0.25, curve=2.5),
        volume=0.60,
        filter_cutoff=4000.0,
    ),
    "ks_muted": Instrument(
        name="KS Muted String",
        waveform="karplus_990_15",  # quick decay, dark
        adsr=ADSR(attack=0.002, decay=0.2, sustain=0.0, release=0.1, curve=3.0),
        volume=0.65,
        filter_cutoff=2500.0,
    ),
    "ks_bass": Instrument(
        name="KS Bass Guitar",
        waveform="karplus_997_18",  # long sustain, very dark = smooth bass
        adsr=ADSR(attack=0.005, decay=0.6, sustain=0.15, release=0.3, curve=2.0),
        volume=0.75,
        filter_cutoff=1800.0,  # strongly tame twang for bass
    ),

    # -----------------------------------------------------------------------
    # Ring Modulation — Metallic, gamelan, dissonant textures
    # -----------------------------------------------------------------------

    "ring_bell": Instrument(
        name="Ring Mod Bell",
        waveform="ring_2.5",  # non-integer ratio = inharmonic bell
        adsr=ADSR(attack=0.002, decay=0.5, sustain=0.05, release=0.3, curve=2.0),
        volume=0.55,
    ),
    "ring_gamelan": Instrument(
        name="Ring Mod Gamelan",
        waveform="ring_1.414",  # sqrt(2) ratio = Javanese gamelan-like
        adsr=ADSR(attack=0.003, decay=0.6, sustain=0.08, release=0.35, curve=1.5),
        volume=0.50,
    ),
    "ring_dark": Instrument(
        name="Ring Mod Dark",
        waveform="ring_0.5",  # sub-harmonic modulation = ominous
        adsr=ADSR(attack=0.010, decay=0.3, sustain=0.30, release=0.20, curve=1.5),
        volume=0.55,
        filter_cutoff=2000.0,
        filter_resonance=0.30,
    ),

    # -----------------------------------------------------------------------
    # Granular Synthesis — Textures, clouds, glitch
    # -----------------------------------------------------------------------

    "grain_cloud": Instrument(
        name="Granular Cloud",
        waveform="granular",  # sine grains = ethereal cloud
        adsr=ADSR(attack=0.200, decay=0.15, sustain=0.50, release=0.40, curve=1.5),
        volume=0.45,
    ),
    "grain_texture": Instrument(
        name="Granular Noise Texture",
        waveform="granular_noise",  # noise grains = textural wash
        adsr=ADSR(attack=0.150, decay=0.20, sustain=0.40, release=0.30, curve=1.5),
        volume=0.40,
        filter_cutoff=3000.0,
        filter_resonance=0.25,
    ),
    "grain_shimmer": Instrument(
        name="Granular Shimmer",
        waveform="granular_saw",  # saw grains = shimmering texture
        adsr=ADSR(attack=0.100, decay=0.12, sustain=0.55, release=0.25, curve=1.5),
        volume=0.45,
    ),

    # -----------------------------------------------------------------------
    # PWM (Pulse Width Modulation) — evolving synth leads
    # -----------------------------------------------------------------------

    "pwm_lead": Instrument(
        name="PWM Lead",
        waveform="pwm_2_30",  # 2Hz rate, 30% depth
        adsr=ADSR(attack=0.008, decay=0.12, sustain=0.55, release=0.12, curve=1.5),
        volume=0.65,
        filter_cutoff=3500.0,
        filter_resonance=0.25,
    ),
    "pwm_pad": Instrument(
        name="PWM Pad",
        waveform="pwm_1_25",  # slow 1Hz, gentle 25% depth
        adsr=ADSR(attack=0.300, decay=0.15, sustain=0.55, release=0.40, curve=1.5),
        volume=0.45,
        filter_cutoff=2500.0,
        filter_resonance=0.30,
    ),
    "pwm_bass": Instrument(
        name="PWM Bass",
        waveform="pwm_3_35",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.50, release=0.10, curve=2.0),
        volume=0.75,
        filter_cutoff=1200.0,
        filter_resonance=0.40,
    ),

    # -----------------------------------------------------------------------
    # Vocal Synthesis — Voices from Pure Code (ADR-006)
    # -----------------------------------------------------------------------

    "vocal_ah": Instrument(
        name="Vocal Ah (Open)",
        waveform="vocal_ah",
        adsr=ADSR(attack=0.030, decay=0.10, sustain=0.80, release=0.18, curve=1.5),
        volume=0.82,
    ),
    "vocal_ee": Instrument(
        name="Vocal Ee (Bright)",
        waveform="vocal_ee",
        adsr=ADSR(attack=0.030, decay=0.10, sustain=0.80, release=0.18, curve=1.5),
        volume=0.80,
    ),
    "vocal_oh": Instrument(
        name="Vocal Oh (Round)",
        waveform="vocal_oh",
        adsr=ADSR(attack=0.035, decay=0.12, sustain=0.78, release=0.22, curve=1.5),
        volume=0.82,
    ),
    "vocal_oo": Instrument(
        name="Vocal Oo (Deep)",
        waveform="vocal_oo",
        adsr=ADSR(attack=0.035, decay=0.12, sustain=0.78, release=0.22, curve=1.5),
        volume=0.80,
    ),
    "vocal_morph_ah_ee": Instrument(
        name="Vocal Morph Ah\u2192Ee",
        waveform="vocal_ah_ee",
        adsr=ADSR(attack=0.030, decay=0.08, sustain=0.80, release=0.18, curve=1.5),
        volume=0.80,
    ),
    "vocal_morph_oh_ah": Instrument(
        name="Vocal Morph Oh\u2192Ah",
        waveform="vocal_oh_ah",
        adsr=ADSR(attack=0.035, decay=0.10, sustain=0.78, release=0.20, curve=1.5),
        volume=0.80,
    ),
    "vocal_choir": Instrument(
        name="Vocal Choir",
        waveform="vocal_choir",
        adsr=ADSR(attack=0.150, decay=0.12, sustain=0.78, release=0.35, curve=1.5),
        volume=0.82,
    ),
    "vocal_choir_ee": Instrument(
        name="Vocal Choir Ee",
        waveform="vocal_choir_ee",
        adsr=ADSR(attack=0.150, decay=0.12, sustain=0.78, release=0.35, curve=1.5),
        volume=0.80,
    ),
    "vocal_chop": Instrument(
        name="Vocal Chop",
        waveform="vocal_chop",
        adsr=ADSR(attack=0.003, decay=0.06, sustain=0.30, release=0.04, curve=2.0),
        volume=0.82,
    ),
    "vocal_breathy": Instrument(
        name="Vocal Breathy Pad",
        waveform="vocal_ah",
        adsr=ADSR(attack=0.250, decay=0.18, sustain=0.65, release=0.35, curve=1.5),
        volume=0.74,
    ),
    "glottal_buzz": Instrument(
        name="Glottal Buzz",
        waveform="glottal",
        adsr=ADSR(attack=0.005, decay=0.10, sustain=0.70, release=0.10, curve=1.5),
        volume=0.80,
        filter_cutoff=2200.0,
        filter_resonance=0.25,
    ),

    # -----------------------------------------------------------------------
    # Metal Guitar — Power chords, palm mutes, leads, shred
    # Run through apply_amp_sim() in post_process for full metal tone
    # -----------------------------------------------------------------------

    "metal_power": Instrument(
        name="Metal Power Chord",
        waveform="power_chord",
        adsr=ADSR(attack=0.002, decay=0.15, sustain=0.70, release=0.10, curve=1.5),
        volume=0.75,
        distortion=0.6,
    ),
    "metal_palm": Instrument(
        name="Metal Palm Mute",
        waveform="palm_mute",
        adsr=ADSR(attack=0.001, decay=0.08, sustain=0.15, release=0.05, curve=2.5),
        volume=0.78,
        distortion=0.7,
    ),
    "metal_chug": Instrument(
        name="Metal Chug (Djent)",
        waveform="chug",
        adsr=ADSR(attack=0.001, decay=0.04, sustain=0.05, release=0.03, curve=3.0),
        volume=0.80,
        distortion=0.8,
    ),
    "metal_lead": Instrument(
        name="Metal Lead Guitar",
        waveform="guitar_lead",
        adsr=ADSR(attack=0.003, decay=0.20, sustain=0.65, release=0.15, curve=1.5),
        volume=0.70,
        distortion=0.5,
        vibrato_rate=6.0,
        vibrato_depth=0.30,
    ),
    "metal_trem": Instrument(
        name="Metal Tremolo Pick",
        waveform="guitar_trem",
        adsr=ADSR(attack=0.001, decay=0.10, sustain=0.55, release=0.08, curve=2.0),
        volume=0.75,
        distortion=0.7,
    ),
    "metal_solo": Instrument(
        name="Metal Solo (High Gain)",
        waveform="guitar_lead",
        adsr=ADSR(attack=0.002, decay=0.25, sustain=0.75, release=0.20, curve=1.5),
        volume=0.68,
        distortion=0.8,
        vibrato_rate=5.5,
        vibrato_depth=0.40,
    ),

    # -----------------------------------------------------------------------
    # Extended Vocal Presets — combinations and character variants
    # Use these for melodic lines, pads, and experimental palette blending
    # -----------------------------------------------------------------------

    "vocal_lead_ah": Instrument(
        name="Vocal Lead Ah (Clean Melody)",
        waveform="vocal_ah",
        adsr=ADSR(attack=0.020, decay=0.06, sustain=0.85, release=0.12, curve=1.3),
        volume=0.85,
        filter_cutoff=5000.0,    # keep vocal presence + air
        filter_resonance=0.08,
    ),
    "vocal_lead_ee": Instrument(
        name="Vocal Lead Ee (Bright Melody)",
        waveform="vocal_ee",
        adsr=ADSR(attack=0.015, decay=0.05, sustain=0.85, release=0.10, curve=1.3),
        volume=0.82,
        filter_cutoff=5500.0,
        filter_resonance=0.10,
    ),
    "vocal_bass_oo": Instrument(
        name="Vocal Bass Oo (Deep Low)",
        waveform="vocal_oo",
        adsr=ADSR(attack=0.050, decay=0.15, sustain=0.80, release=0.25, curve=1.5),
        volume=0.82,
    ),
    "vocal_ensemble": Instrument(
        name="Vocal Ensemble (Choir + Slow Swell)",
        waveform="vocal_choir",
        adsr=ADSR(attack=0.350, decay=0.18, sustain=0.78, release=0.55, curve=1.2),
        volume=0.85,
    ),
    "vocal_stab": Instrument(
        name="Vocal Stab (Percussive Hit)",
        waveform="vocal_ah",
        adsr=ADSR(attack=0.004, decay=0.12, sustain=0.12, release=0.06, curve=2.5),
        volume=0.85,
        filter_cutoff=3500.0,
        filter_resonance=0.18,
    ),
    "vocal_pad_warm": Instrument(
        name="Vocal Pad Warm (Oo Drone)",
        waveform="vocal_oo",
        adsr=ADSR(attack=0.400, decay=0.25, sustain=0.72, release=0.70, curve=1.1),
        volume=0.80,
    ),
    "vocal_whisper": Instrument(
        name="Vocal Whisper (Breathy Air)",
        waveform="vocal_ah",
        adsr=ADSR(attack=0.180, decay=0.20, sustain=0.58, release=0.45, curve=1.5),
        volume=0.66,
        filter_cutoff=2200.0,
        filter_resonance=0.05,
    ),

    # -----------------------------------------------------------------------
    # Orchestral Presets — piano, strings, winds, brass
    #
    # These presets exist for classical and chamber writing. They use the
    # multi-layer voice system to stack a primary timbre with detuned body
    # resonance, optional filter envelopes for swells, and ADSR shapes
    # tuned to each instrument family. They pair well with the new
    # historical temperaments (Werckmeister for keyboard, just intonation
    # for strings, etc.).
    #
    # Tone tip: every orchestral preset wants reverb 0.20-0.40 in the
    # channel effects to feel like it's in a real space.
    # -----------------------------------------------------------------------

    # Acoustic grand piano. Hammer transient + Karplus body + warm sub +
    # bright bell harmonic for sparkle. With the Karplus tuning fix in
    # place, the body now stays in tune across the full register, so the
    # sine sub-octave layer no longer beats audibly against it.
    #
    # Generous sustain and a long decay tail mean the note rings instead
    # of dying instantly, which is what you actually hear from a grand
    # piano with the pedal up.
    "piano_grand": Instrument(
        name="Acoustic Grand Piano",
        waveform="karplus",
        adsr=ADSR(attack=0.002, decay=2.80, sustain=0.18,
                  release=0.60, curve=2.0),
        volume=0.80,
        layers=[
            # Bright additive hammer transient
            VoiceLayer(
                waveform="additive_warm", gain=0.30, detune_cents=0.0,
                adsr=ADSR(attack=0.001, decay=0.40, sustain=0.0,
                          release=0.12, curve=3.0),
            ),
            # Sub-octave sine for warmth and body
            VoiceLayer(
                waveform="sine", gain=0.22, detune_cents=-1200.0,
                adsr=ADSR(attack=0.005, decay=2.40, sustain=0.20,
                          release=0.50, curve=2.0),
            ),
            # 5th-harmonic bell for sparkle and dynamic content
            VoiceLayer(
                waveform="sine", gain=0.10, detune_cents=1900.0,
                adsr=ADSR(attack=0.001, decay=0.25, sustain=0.0,
                          release=0.10, curve=3.5),
            ),
        ],
    ),

    # Upright piano — slightly thinner top, more wood/clack.
    "piano_upright": Instrument(
        name="Upright Piano",
        waveform="karplus",
        adsr=ADSR(attack=0.003, decay=2.00, sustain=0.12,
                  release=0.45, curve=2.0),
        volume=0.74,
        layers=[
            VoiceLayer(
                waveform="additive_bright", gain=0.25, detune_cents=0.0,
                adsr=ADSR(attack=0.001, decay=0.22, sustain=0.0,
                          release=0.08, curve=3.0),
            ),
            VoiceLayer(
                waveform="sine", gain=0.16, detune_cents=-1200.0,
                adsr=ADSR(attack=0.005, decay=1.80, sustain=0.15,
                          release=0.40, curve=2.0),
            ),
        ],
    ),

    # NEW — Concert grand. Bigger, more layered than piano_grand. Use this
    # for solo piano showpieces (Chopin, Debussy, Liszt). Adds a 4'
    # octave-up layer and a wider stereo image via two slightly detuned
    # body voices, for an aural depth that piano_grand can't reach alone.
    "piano_concert": Instrument(
        name="Concert Grand Piano",
        waveform="karplus",
        adsr=ADSR(attack=0.002, decay=3.20, sustain=0.22,
                  release=0.80, curve=2.0),
        volume=0.82,
        layers=[
            # Hammer transient
            VoiceLayer(
                waveform="additive_warm", gain=0.32, detune_cents=0.0,
                adsr=ADSR(attack=0.001, decay=0.50, sustain=0.0,
                          release=0.15, curve=3.0),
            ),
            # Twin Karplus bodies, one slightly +cent / one -cent. Tiny
            # detune (±2¢) gives spatial width without smearing pitch.
            VoiceLayer(
                waveform="karplus", gain=0.28, detune_cents=-2.0,
                adsr=ADSR(attack=0.002, decay=2.80, sustain=0.20,
                          release=0.60, curve=2.0),
            ),
            VoiceLayer(
                waveform="karplus", gain=0.28, detune_cents=+2.0,
                adsr=ADSR(attack=0.002, decay=2.80, sustain=0.20,
                          release=0.60, curve=2.0),
            ),
            # Sub-octave for body
            VoiceLayer(
                waveform="sine", gain=0.20, detune_cents=-1200.0,
                adsr=ADSR(attack=0.005, decay=3.20, sustain=0.25,
                          release=0.70, curve=2.0),
            ),
            # Octave-up sparkle
            VoiceLayer(
                waveform="sine", gain=0.10, detune_cents=+1200.0,
                adsr=ADSR(attack=0.001, decay=1.20, sustain=0.05,
                          release=0.30, curve=2.5),
            ),
        ],
    ),

    # Harpsichord — Bach's instrument. Plucked, bright, no dynamic range.
    # Pair with Werckmeister III temperament for authenticity. Detunes
    # tightened to ±1¢ so the temperament's character isn't smeared by
    # internal chorusing.
    "harpsichord": Instrument(
        name="Harpsichord",
        waveform="karplus",
        adsr=ADSR(attack=0.001, decay=1.00, sustain=0.0,
                  release=0.12, curve=3.0),
        volume=0.78,
        layers=[
            # Bright pluck top — drives the plucked-quill character
            VoiceLayer(
                waveform="additive_bright", gain=0.36, detune_cents=0.0,
                adsr=ADSR(attack=0.001, decay=0.55, sustain=0.0,
                          release=0.08, curve=3.5),
            ),
            # Octave-up second register (typical 4' stop on Baroque harpsichords)
            VoiceLayer(
                waveform="karplus", gain=0.18, detune_cents=+1200.0,
                adsr=ADSR(attack=0.001, decay=0.40, sustain=0.0,
                          release=0.06, curve=3.0),
            ),
            # Tiny sub for body
            VoiceLayer(
                waveform="sawtooth", gain=0.08, detune_cents=-1.0,
                adsr=ADSR(attack=0.001, decay=0.30, sustain=0.0,
                          release=0.05, curve=3.0),
            ),
        ],
    ),

    # Pipe organ — long sustain (no decay), foundational + 5th + octave
    # stops layered together. Slow release simulates room reverb tail.
    "pipe_organ": Instrument(
        name="Pipe Organ (Diapason)",
        waveform="additive_organ",
        adsr=ADSR(attack=0.030, decay=0.05, sustain=0.95,
                  release=0.40, curve=1.2),
        volume=0.62,
        layers=[
            # Octave stop (4' rank)
            VoiceLayer(
                waveform="sine", gain=0.22, detune_cents=1200.0,
                adsr=ADSR(attack=0.030, decay=0.05, sustain=0.95,
                          release=0.40, curve=1.2),
            ),
            # Quint stop (5th)
            VoiceLayer(
                waveform="sine", gain=0.14, detune_cents=702.0,
                adsr=ADSR(attack=0.030, decay=0.05, sustain=0.95,
                          release=0.40, curve=1.2),
            ),
        ],
    ),

    # Violin — bowed sawtooth + body filter envelope swell. Detune
    # tightened to ±2¢ so the violin doesn't fight pure-tuning intervals
    # in just / Pythagorean / meantone temperaments. Brighter top end
    # via a higher filter peak. Adds an octave-up overtone layer for
    # the spectral shimmer real strings have.
    "violin": Instrument(
        name="Violin (Solo)",
        waveform="sawtooth",
        adsr=ADSR(attack=0.050, decay=0.08, sustain=0.88,
                  release=0.18, curve=1.5),
        volume=0.66,
        vibrato_rate=5.8,
        vibrato_depth=0.22,
        filter_env=FilterEnvelope(
            base_hz=2200.0, peak_hz=6500.0, sustain_hz=3200.0,
            attack_sec=0.08, decay_sec=0.18, release_sec=0.16,
            resonance=0.22,
        ),
        layers=[
            # Tight chorus for ensemble width without smearing intonation
            VoiceLayer(
                waveform="sawtooth", gain=0.20, detune_cents=-2.0,
                adsr=ADSR(attack=0.050, decay=0.08, sustain=0.88,
                          release=0.18, curve=1.5),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.20, detune_cents=+2.0,
                adsr=ADSR(attack=0.050, decay=0.08, sustain=0.88,
                          release=0.18, curve=1.5),
            ),
            # Octave-up overtone for the bowed-string shimmer
            VoiceLayer(
                waveform="triangle", gain=0.10, detune_cents=+1200.0,
                adsr=ADSR(attack=0.060, decay=0.08, sustain=0.85,
                          release=0.16, curve=1.5),
            ),
        ],
    ),

    # Viola — slightly darker than violin, same architecture.
    "viola": Instrument(
        name="Viola (Solo)",
        waveform="sawtooth",
        adsr=ADSR(attack=0.070, decay=0.08, sustain=0.88,
                  release=0.20, curve=1.5),
        volume=0.66,
        vibrato_rate=5.2,
        vibrato_depth=0.20,
        filter_env=FilterEnvelope(
            base_hz=1500.0, peak_hz=4500.0, sustain_hz=2200.0,
            attack_sec=0.10, decay_sec=0.20, release_sec=0.16,
            resonance=0.22,
        ),
        layers=[
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-2.0,
                adsr=ADSR(attack=0.070, decay=0.08, sustain=0.88,
                          release=0.20, curve=1.5),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+2.0,
                adsr=ADSR(attack=0.070, decay=0.08, sustain=0.88,
                          release=0.20, curve=1.5),
            ),
            VoiceLayer(
                waveform="triangle", gain=0.10, detune_cents=+1200.0,
                adsr=ADSR(attack=0.080, decay=0.08, sustain=0.85,
                          release=0.18, curve=1.5),
            ),
        ],
    ),

    # Cello — rich, dark, slow attack with sub-octave body. Tightened
    # detunes; added 5th-overtone for warmth.
    "cello": Instrument(
        name="Cello (Solo)",
        waveform="sawtooth",
        adsr=ADSR(attack=0.090, decay=0.10, sustain=0.90,
                  release=0.28, curve=1.4),
        volume=0.70,
        vibrato_rate=4.8,
        vibrato_depth=0.16,
        filter_env=FilterEnvelope(
            base_hz=900.0, peak_hz=3500.0, sustain_hz=1600.0,
            attack_sec=0.10, decay_sec=0.22, release_sec=0.18,
            resonance=0.20,
        ),
        layers=[
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-3.0,
                adsr=ADSR(attack=0.090, decay=0.10, sustain=0.90,
                          release=0.28, curve=1.4),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+3.0,
                adsr=ADSR(attack=0.090, decay=0.10, sustain=0.90,
                          release=0.28, curve=1.4),
            ),
            # Sub-octave body
            VoiceLayer(
                waveform="sine", gain=0.18, detune_cents=-1200.0,
                adsr=ADSR(attack=0.070, decay=0.08, sustain=0.92,
                          release=0.25, curve=1.4),
            ),
            # 5th overtone for the rich cello midrange
            VoiceLayer(
                waveform="triangle", gain=0.10, detune_cents=702.0,
                adsr=ADSR(attack=0.090, decay=0.10, sustain=0.85,
                          release=0.20, curve=1.5),
            ),
        ],
    ),

    # Contrabass — very low, slow attack. Sub octave gives the gut-string
    # foundation. Tightened detune.
    "contrabass": Instrument(
        name="Contrabass (Arco)",
        waveform="sawtooth",
        adsr=ADSR(attack=0.120, decay=0.12, sustain=0.88,
                  release=0.32, curve=1.4),
        volume=0.74,
        vibrato_rate=4.2,
        vibrato_depth=0.13,
        filter_env=FilterEnvelope(
            base_hz=500.0, peak_hz=1900.0, sustain_hz=900.0,
            attack_sec=0.16, decay_sec=0.28, release_sec=0.20,
            resonance=0.20,
        ),
        layers=[
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-3.0,
                adsr=ADSR(attack=0.120, decay=0.12, sustain=0.88,
                          release=0.32, curve=1.4),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+3.0,
                adsr=ADSR(attack=0.120, decay=0.12, sustain=0.88,
                          release=0.32, curve=1.4),
            ),
            VoiceLayer(
                waveform="sine", gain=0.20, detune_cents=-1200.0,
                adsr=ADSR(attack=0.100, decay=0.10, sustain=0.92,
                          release=0.30, curve=1.4),
            ),
        ],
    ),

    # NEW — Pizzicato cello. Plucked rather than bowed. Karplus-based
    # for that wood-on-string snap.
    "cello_pizz": Instrument(
        name="Cello Pizzicato",
        waveform="karplus",
        adsr=ADSR(attack=0.001, decay=0.50, sustain=0.0,
                  release=0.15, curve=3.0),
        volume=0.72,
        layers=[
            VoiceLayer(
                waveform="sine", gain=0.22, detune_cents=-1200.0,
                adsr=ADSR(attack=0.001, decay=0.40, sustain=0.0,
                          release=0.12, curve=3.0),
            ),
        ],
    ),

    # Flute — pure tone + 5th harmonic + breath noise. Brighter top end
    # and more prominent breath component.
    "flute": Instrument(
        name="Flute",
        waveform="sine",
        adsr=ADSR(attack=0.060, decay=0.05, sustain=0.94,
                  release=0.16, curve=1.3),
        volume=0.70,
        vibrato_rate=5.0,
        vibrato_depth=0.18,
        layers=[
            # Octave-up overtone for the silvery top
            VoiceLayer(
                waveform="sine", gain=0.18, detune_cents=+1200.0,
                adsr=ADSR(attack=0.060, decay=0.05, sustain=0.92,
                          release=0.16, curve=1.3),
            ),
            # 5th harmonic (12th interval) for body
            VoiceLayer(
                waveform="sine", gain=0.10, detune_cents=+1902.0,
                adsr=ADSR(attack=0.060, decay=0.05, sustain=0.85,
                          release=0.14, curve=1.3),
            ),
            # Breath/air component — heavily filtered noise
            VoiceLayer(
                waveform="white_noise", gain=0.06, detune_cents=0.0,
                adsr=ADSR(attack=0.040, decay=0.08, sustain=0.60,
                          release=0.18, curve=1.3),
            ),
        ],
    ),

    # Oboe — reedy double-reed. Brighter, more distinctive nasal character
    # via stronger harmonics and a higher resonant filter peak.
    "oboe": Instrument(
        name="Oboe",
        waveform="additive_warm",
        adsr=ADSR(attack=0.030, decay=0.06, sustain=0.88,
                  release=0.14, curve=1.4),
        volume=0.66,
        vibrato_rate=5.5,
        vibrato_depth=0.20,
        filter_cutoff=4500.0,
        filter_resonance=0.22,
        layers=[
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-2.0,
                adsr=ADSR(attack=0.030, decay=0.06, sustain=0.88,
                          release=0.14, curve=1.4),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+2.0,
                adsr=ADSR(attack=0.030, decay=0.06, sustain=0.88,
                          release=0.14, curve=1.4),
            ),
            # Octave overtone — defining oboe brightness
            VoiceLayer(
                waveform="triangle", gain=0.15, detune_cents=+1200.0,
                adsr=ADSR(attack=0.030, decay=0.06, sustain=0.85,
                          release=0.12, curve=1.4),
            ),
        ],
    ),

    # Clarinet — hollow square (odd harmonics), warm filter. Add a 12th
    # (3rd harmonic) for the characteristic clarinet "second register"
    # color, which is what makes it sound clarinet-y vs generic square.
    "clarinet": Instrument(
        name="Clarinet",
        waveform="square",
        duty=0.50,
        adsr=ADSR(attack=0.045, decay=0.06, sustain=0.92,
                  release=0.18, curve=1.3),
        volume=0.66,
        vibrato_rate=4.8,
        vibrato_depth=0.12,
        filter_cutoff=2800.0,
        filter_resonance=0.14,
        layers=[
            # 12th = 3rd harmonic = pure 5th + octave. Defines clarinet color.
            VoiceLayer(
                waveform="sine", gain=0.16, detune_cents=1902.0,
                adsr=ADSR(attack=0.045, decay=0.06, sustain=0.90,
                          release=0.18, curve=1.3),
            ),
            # 5th harmonic for top sparkle
            VoiceLayer(
                waveform="sine", gain=0.08, detune_cents=2786.0,
                adsr=ADSR(attack=0.045, decay=0.06, sustain=0.85,
                          release=0.16, curve=1.3),
            ),
        ],
    ),

    # Bassoon — low double-reed. Beefed up with a sub octave for body.
    "bassoon": Instrument(
        name="Bassoon",
        waveform="additive_warm",
        adsr=ADSR(attack=0.050, decay=0.08, sustain=0.88,
                  release=0.22, curve=1.4),
        volume=0.70,
        vibrato_rate=4.4,
        vibrato_depth=0.16,
        filter_cutoff=2400.0,
        filter_resonance=0.20,
        layers=[
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-2.0,
                adsr=ADSR(attack=0.050, decay=0.08, sustain=0.88,
                          release=0.22, curve=1.4),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+2.0,
                adsr=ADSR(attack=0.050, decay=0.08, sustain=0.88,
                          release=0.22, curve=1.4),
            ),
            # Sub octave for the bassoon's deep body
            VoiceLayer(
                waveform="sine", gain=0.18, detune_cents=-1200.0,
                adsr=ADSR(attack=0.050, decay=0.08, sustain=0.90,
                          release=0.20, curve=1.4),
            ),
        ],
    ),

    # Trumpet — bright brass blat. Faster filter swell, brighter top.
    "trumpet": Instrument(
        name="Trumpet",
        waveform="sawtooth",
        adsr=ADSR(attack=0.015, decay=0.06, sustain=0.88,
                  release=0.12, curve=1.4),
        volume=0.72,
        vibrato_rate=5.8,
        vibrato_depth=0.18,
        filter_env=FilterEnvelope(
            base_hz=1000.0, peak_hz=6500.0, sustain_hz=3600.0,
            attack_sec=0.03, decay_sec=0.12, release_sec=0.08,
            resonance=0.28,
        ),
        layers=[
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-2.0,
                adsr=ADSR(attack=0.015, decay=0.06, sustain=0.88,
                          release=0.12, curve=1.4),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+2.0,
                adsr=ADSR(attack=0.015, decay=0.06, sustain=0.88,
                          release=0.12, curve=1.4),
            ),
            # Octave overtone for the bell-bright top
            VoiceLayer(
                waveform="triangle", gain=0.12, detune_cents=+1200.0,
                adsr=ADSR(attack=0.015, decay=0.06, sustain=0.85,
                          release=0.12, curve=1.4),
            ),
        ],
    ),

    # French horn — warm, mellow brass. Slower attack, darker filter.
    "french_horn": Instrument(
        name="French Horn",
        waveform="sawtooth",
        adsr=ADSR(attack=0.040, decay=0.08, sustain=0.90,
                  release=0.24, curve=1.4),
        volume=0.74,
        vibrato_rate=4.8,
        vibrato_depth=0.14,
        filter_env=FilterEnvelope(
            base_hz=800.0, peak_hz=3400.0, sustain_hz=1700.0,
            attack_sec=0.06, decay_sec=0.20, release_sec=0.18,
            resonance=0.22,
        ),
        layers=[
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-2.0,
                adsr=ADSR(attack=0.040, decay=0.08, sustain=0.90,
                          release=0.24, curve=1.4),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+2.0,
                adsr=ADSR(attack=0.040, decay=0.08, sustain=0.90,
                          release=0.24, curve=1.4),
            ),
            # Sub-octave gives the rich horn body
            VoiceLayer(
                waveform="sine", gain=0.18, detune_cents=-1200.0,
                adsr=ADSR(attack=0.040, decay=0.08, sustain=0.92,
                          release=0.22, curve=1.4),
            ),
        ],
    ),

    # Trombone — sliding brass, medium attack, mid-bright filter.
    "trombone": Instrument(
        name="Trombone",
        waveform="sawtooth",
        adsr=ADSR(attack=0.035, decay=0.08, sustain=0.88,
                  release=0.20, curve=1.4),
        volume=0.72,
        vibrato_rate=4.8,
        vibrato_depth=0.15,
        filter_env=FilterEnvelope(
            base_hz=700.0, peak_hz=3800.0, sustain_hz=1900.0,
            attack_sec=0.05, decay_sec=0.18, release_sec=0.14,
            resonance=0.24,
        ),
        layers=[
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-2.0,
                adsr=ADSR(attack=0.035, decay=0.08, sustain=0.88,
                          release=0.20, curve=1.4),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+2.0,
                adsr=ADSR(attack=0.035, decay=0.08, sustain=0.88,
                          release=0.20, curve=1.4),
            ),
            VoiceLayer(
                waveform="sine", gain=0.16, detune_cents=-1200.0,
                adsr=ADSR(attack=0.035, decay=0.08, sustain=0.90,
                          release=0.20, curve=1.4),
            ),
        ],
    ),

    # NEW — Symphonic string section. Bigger than solo violin/viola/cello,
    # designed to be ONE channel that fills a string section's role.
    # Great for cinematic backgrounds and chord pads.
    "strings_ensemble": Instrument(
        name="Strings Ensemble (Section)",
        waveform="sawtooth",
        adsr=ADSR(attack=0.080, decay=0.10, sustain=0.92,
                  release=0.40, curve=1.3),
        volume=0.68,
        vibrato_rate=5.0,
        vibrato_depth=0.16,
        filter_env=FilterEnvelope(
            base_hz=1500.0, peak_hz=4500.0, sustain_hz=2400.0,
            attack_sec=0.10, decay_sec=0.20, release_sec=0.30,
            resonance=0.18,
        ),
        layers=[
            # Stacked octaves for body
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=-4.0,
                adsr=ADSR(attack=0.080, decay=0.10, sustain=0.92,
                          release=0.40, curve=1.3),
            ),
            VoiceLayer(
                waveform="sawtooth", gain=0.22, detune_cents=+4.0,
                adsr=ADSR(attack=0.080, decay=0.10, sustain=0.92,
                          release=0.40, curve=1.3),
            ),
            VoiceLayer(
                waveform="sine", gain=0.16, detune_cents=-1200.0,
                adsr=ADSR(attack=0.080, decay=0.10, sustain=0.92,
                          release=0.40, curve=1.3),
            ),
            VoiceLayer(
                waveform="triangle", gain=0.12, detune_cents=+1200.0,
                adsr=ADSR(attack=0.090, decay=0.10, sustain=0.88,
                          release=0.35, curve=1.4),
            ),
        ],
    ),

    # NEW — Concert harp. Plucked, with long ringing decay.
    "harp": Instrument(
        name="Concert Harp",
        waveform="karplus",
        adsr=ADSR(attack=0.001, decay=2.50, sustain=0.10,
                  release=0.50, curve=2.5),
        volume=0.74,
        layers=[
            # Bell-like overtone for the harp shimmer
            VoiceLayer(
                waveform="sine", gain=0.18, detune_cents=+1200.0,
                adsr=ADSR(attack=0.001, decay=1.80, sustain=0.05,
                          release=0.30, curve=2.5),
            ),
            VoiceLayer(
                waveform="sine", gain=0.10, detune_cents=+1902.0,
                adsr=ADSR(attack=0.001, decay=1.20, sustain=0.0,
                          release=0.20, curve=3.0),
            ),
            VoiceLayer(
                waveform="sine", gain=0.16, detune_cents=-1200.0,
                adsr=ADSR(attack=0.001, decay=2.20, sustain=0.10,
                          release=0.40, curve=2.5),
            ),
        ],
    ),
}
