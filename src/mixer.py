"""
ChipForge Mixer
================
Renders Patterns and Songs to float32 stereo audio buffers.

Features:
  - Per-channel stereo panning
  - Delay/echo effect (tempo-synced)
  - Algorithmic reverb (Schroeder style)
  - Soft-knee compressor/limiter
  - Multi-channel accumulation with headroom management
"""

from __future__ import annotations

from typing import Optional

import numpy as np

import math

from .synth import synthesize_note, SAMPLE_RATE
from .instruments import PRESETS, Instrument
from .sequencer import Pattern, Song

try:
    from scipy.signal import fftconvolve as _fftconvolve
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------

def apply_delay(
    audio: np.ndarray,
    delay_sec: float = 0.25,
    feedback: float = 0.35,
    mix: float = 0.3,
) -> np.ndarray:
    """
    Apply a feedback delay effect.

    Args:
        audio: Mono float32 audio buffer.
        delay_sec: Delay time in seconds.
        feedback: Feedback amount (0.0–0.8). Higher = more repeats.
        mix: Wet/dry mix (0.0 = dry, 1.0 = full wet).

    Returns:
        Float32 array with delay applied.
    """
    delay_samples = int(delay_sec * SAMPLE_RATE)
    if delay_samples == 0:
        return audio
    feedback = min(feedback, 0.8)

    buf = np.copy(audio).astype(np.float64)
    out = np.copy(audio).astype(np.float64)

    for tap in range(1, 6):  # up to 5 echo taps
        offset = delay_samples * tap
        if offset >= len(buf):
            break
        gain = feedback ** tap
        if gain < 0.01:
            break
        out[offset:] += buf[:len(buf) - offset] * gain

    return (audio * (1.0 - mix) + out.astype(np.float32) * mix).astype(np.float32)


# ---------------------------------------------------------------------------
# Impulse Response cache for FFT convolution reverb
# ---------------------------------------------------------------------------
from functools import lru_cache
from threading import Lock

_IR_CACHE_LOCK = Lock()


@lru_cache(maxsize=256)
def _generate_schroeder_ir(room_size: float, damping: float) -> np.ndarray:
    """Generate a Schroeder reverb impulse response (LRU cached, thread-safe).

    Runs the same comb+allpass algorithm on a unit impulse to produce the IR,
    then caches it via LRU (max 256 entries, ~128MB worst case).
    Subsequent calls with the same (room_size, damping) return instantly.
    """
    room_size = round(room_size, 4)
    damping = round(damping, 4)

    comb_delays = [int(d * (0.5 + room_size))
                   for d in [1557, 1617, 1491, 1422, 1277, 1356]]
    comb_feedback = 0.7 + room_size * 0.15

    # Compute RT60 to determine IR length
    max_delay_sec = max(comb_delays) / SAMPLE_RATE
    rt60 = -3.0 * max_delay_sec / math.log10(max(comb_feedback, 0.01))
    ir_length = min(int(rt60 * 2.0 * SAMPLE_RATE), SAMPLE_RATE * 5)
    ir_length = max(ir_length, SAMPLE_RATE)  # At least 1 second

    # Unit impulse
    impulse = np.zeros(ir_length, dtype=np.float64)
    impulse[0] = 1.0

    wet = np.zeros(ir_length, dtype=np.float64)

    for delay in comb_delays:
        buf = np.zeros(ir_length, dtype=np.float64)
        filt = 0.0
        for i in range(ir_length):
            read_idx = i - delay
            delayed = buf[read_idx] if read_idx >= 0 else 0.0
            filt = delayed * (1.0 - damping) + filt * damping
            buf[i] = impulse[i] + filt * comb_feedback
            wet[i] += delayed

    wet /= len(comb_delays)

    allpass_delays = [225, 556, 441, 341]
    for delay in allpass_delays:
        buf_in = wet.copy()
        for i in range(ir_length):
            read_idx = i - delay
            delayed = buf_in[read_idx] if read_idx >= 0 else 0.0
            wet[i] = -buf_in[i] + delayed + buf_in[i] * 0.5

    return wet.astype(np.float32)


def _apply_reverb_python(
    audio: np.ndarray,
    room_size: float = 0.5,
    damping: float = 0.5,
    mix: float = 0.2,
) -> np.ndarray:
    """Python fallback: per-sample Schroeder reverb."""
    n = len(audio)
    comb_delays = [int(d * (0.5 + room_size))
                   for d in [1557, 1617, 1491, 1422, 1277, 1356]]
    comb_feedback = 0.7 + room_size * 0.15

    wet = np.zeros(n, dtype=np.float64)

    for delay in comb_delays:
        buf = np.zeros(n, dtype=np.float64)
        filt = 0.0
        for i in range(n):
            read_idx = i - delay
            delayed = buf[read_idx] if read_idx >= 0 else 0.0
            filt = delayed * (1.0 - damping) + filt * damping
            buf[i] = float(audio[i]) + filt * comb_feedback
            wet[i] += delayed

    wet /= len(comb_delays)

    allpass_delays = [225, 556, 441, 341]
    for delay in allpass_delays:
        buf_in = wet.copy()
        for i in range(n):
            read_idx = i - delay
            delayed = buf_in[read_idx] if read_idx >= 0 else 0.0
            wet[i] = -buf_in[i] + delayed + buf_in[i] * 0.5

    return (audio * (1.0 - mix) + wet.astype(np.float32) * mix).astype(np.float32)


def apply_reverb(
    audio: np.ndarray,
    room_size: float = 0.5,
    damping: float = 0.5,
    mix: float = 0.2,
) -> np.ndarray:
    """
    Apply Schroeder reverb.

    With scipy: generates IR once (cached), then uses FFT convolution
    (O(N log N) in C). Typically 30-120x faster than per-sample Python.

    Without scipy: falls back to per-sample Python loops.

    Args:
        audio: Mono float32 audio buffer.
        room_size: Room size factor (0.0-1.0). Larger = longer decay.
        damping: High-frequency damping (0.0-1.0).
        mix: Wet/dry mix (0.0 = dry, 1.0 = full wet).

    Returns:
        Float32 array with reverb applied.
    """
    if not _HAS_SCIPY:
        return _apply_reverb_python(audio, room_size, damping, mix)

    ir = _generate_schroeder_ir(room_size, damping)
    n = len(audio)
    wet = _fftconvolve(audio.astype(np.float64), ir.astype(np.float64),
                       mode='full')[:n]
    return (audio * (1.0 - mix) + wet.astype(np.float32) * mix).astype(np.float32)


def apply_chorus(
    audio: np.ndarray,
    detune_cents: float = 7.0,
    delay_ms: float = 20.0,
    mix: float = 0.3,
) -> np.ndarray:
    """
    Apply a chorus effect — slight pitch detune + short delay creates width and thickness.

    Uses linear interpolation for smooth pitch shifting (avoids aliasing artifacts
    from naive integer-index resampling). Two detuned voices are blended with
    the original at different delay offsets for stereo width.

    Args:
        audio: Mono float32 audio buffer.
        detune_cents: Pitch deviation in cents (3-10 typical). 7 = subtle warmth.
        delay_ms: Base delay offset in milliseconds (15-30 typical).
        mix: Wet/dry mix (0.0 = dry, 1.0 = full wet).

    Returns:
        Float32 array with chorus applied.
    """
    n = len(audio)
    if n == 0:
        return audio
    delay_samples = int(delay_ms * SAMPLE_RATE / 1000.0)
    detune_cents = max(0.0, min(detune_cents, 50.0))
    mix = max(0.0, min(mix, 1.0))

    # Detune factor: cents to ratio
    detune_ratio = 2.0 ** (detune_cents / 1200.0)
    audio_f64 = audio.astype(np.float64)

    # Linear interpolation resampling (avoids aliasing from integer indexing)
    def resample_lerp(src: np.ndarray, ratio: float) -> np.ndarray:
        """Resample using linear interpolation for clean pitch shift."""
        indices = np.arange(n, dtype=np.float64) * ratio
        indices = np.clip(indices, 0, n - 1.001)
        idx_floor = indices.astype(np.int64)
        idx_ceil = np.minimum(idx_floor + 1, n - 1)
        frac = indices - idx_floor
        return src[idx_floor] * (1.0 - frac) + src[idx_ceil] * frac

    # Voice 1: slightly sharp, Voice 2: slightly flat
    voice_up = resample_lerp(audio_f64, detune_ratio)
    voice_dn = resample_lerp(audio_f64, 1.0 / detune_ratio)

    # Apply delay offsets (different for each voice → stereo width)
    delayed_up = np.zeros(n, dtype=np.float64)
    delayed_dn = np.zeros(n, dtype=np.float64)
    delay_2 = delay_samples + delay_samples // 3
    if delay_samples < n:
        delayed_up[delay_samples:] = voice_up[:n - delay_samples]
    if delay_2 < n:
        delayed_dn[delay_2:] = voice_dn[:n - delay_2]

    wet = (delayed_up + delayed_dn) * 0.5
    return (audio * (1.0 - mix) + wet.astype(np.float32) * mix).astype(np.float32)


def soft_clip(audio: np.ndarray, threshold: float = 0.85) -> np.ndarray:
    """
    Soft-knee clipping / limiter. Prevents harsh digital clipping.

    Args:
        audio: Float32 audio buffer (mono or stereo).
        threshold: Level above which soft clipping engages.

    Returns:
        Soft-clipped float32 array.
    """
    out = audio.copy()
    mask = np.abs(out) > threshold
    out[mask] = np.sign(out[mask]) * (threshold + (1.0 - threshold) * np.tanh(
        (np.abs(out[mask]) - threshold) / (1.0 - threshold)
    ))
    return out.astype(np.float32)


# ---------------------------------------------------------------------------
# Pattern Renderer
# ---------------------------------------------------------------------------

def render_pattern(
    pattern: Pattern,
    instruments: Optional[dict[str, Instrument]] = None,
    panning: Optional[dict[int, float]] = None,
    channel_effects: Optional[dict[int, dict]] = None,
    start_beat: float = 0.0,
    dynamics_fn=None,
) -> np.ndarray:
    """
    Render a single Pattern to a stereo float32 audio buffer.

    Each channel is synthesized independently and placed in the stereo field
    according to per-channel panning. Optional per-channel effects (delay,
    reverb, filter) can be applied.

    Args:
        pattern: The pattern to render.
        instruments: Instrument preset dict. Defaults to built-in PRESETS.
        panning: Dict mapping channel index to pan position (-1.0=left, 0.0=center, 1.0=right).
        channel_effects: Dict mapping channel index to effects config, e.g.:
            {0: {"delay": 0.25, "delay_feedback": 0.3, "reverb": 0.2}}

    Returns:
        Float32 numpy array, shape (num_samples, 2), values in range [-1, 1].
    """
    if instruments is None:
        instruments = PRESETS
    if panning is None:
        panning = {}
    if channel_effects is None:
        channel_effects = {}

    step_dur = pattern.step_duration_sec()
    total_samples = max(1, int(pattern.total_duration_sec() * SAMPLE_RATE))
    # Stereo mix buffer
    mix_l = np.zeros(total_samples, dtype=np.float32)
    mix_r = np.zeros(total_samples, dtype=np.float32)

    # Articulation modifiers — multipliers for (duration, velocity)
    _ARTIC = {
        "normal":   (1.00, 1.00),
        "staccato": (0.50, 1.05),
        "tenuto":   (1.00, 1.05),
        "legato":   (1.10, 1.00),  # bleeds slightly into next note
        "marcato":  (1.00, 1.15),
        "accent":   (1.00, 1.08),
        "fermata":  (1.75, 1.00),
    }

    for ch_idx, channel in enumerate(pattern.grid):
        # Render this channel to mono first
        ch_buf = np.zeros(total_samples, dtype=np.float32)
        # Track previous note's frequency for portamento glide.
        prev_freq: float | None = None

        for step_idx, event in enumerate(channel):
            if event is None:
                # Empty grid cell — the previous note is still ringing,
                # so leave prev_freq alone for the next note's glide.
                continue
            if event.is_rest():
                # Explicit rest — break the glide chain so the next note
                # starts at its own frequency without a portamento bend.
                prev_freq = None
                continue

            inst = instruments.get(event.instrument) or instruments.get("pulse_lead")
            if inst is None:
                continue

            # Articulation: scale duration and velocity
            artic = getattr(event, "articulation", "normal")
            dur_mult, vel_mult = _ARTIC.get(artic, (1.0, 1.0))

            start_sample = int(step_idx * step_dur * SAMPLE_RATE)
            max_duration = (total_samples - start_sample) / SAMPLE_RATE
            base_duration = step_dur * event.duration_steps * dur_mult
            note_duration = min(base_duration, max_duration)

            if note_duration <= 0:
                continue

            # Velocity respects the soft-clip ceiling so accents stay clean
            effective_velocity = min(event.velocity * vel_mult, 0.95)

            # Song-level dynamics curve (crescendo/diminuendo). The note's
            # absolute beat position is start_beat + step_idx / steps_per_beat.
            if dynamics_fn is not None:
                note_beat = start_beat + step_idx / pattern.steps_per_beat
                effective_velocity = min(
                    effective_velocity * float(dynamics_fn(note_beat)),
                    0.99,
                )

            # Pass instrument filter/effect params if available
            synth_kwargs: dict = {
                "midi_note": event.midi_note,
                "duration_sec": note_duration,
                "waveform": inst.waveform,
                "duty": inst.duty,
                "adsr": inst.adsr,
                "volume": effective_velocity * inst.volume,
                "wavetable": inst.wavetable,
                "temperament": getattr(pattern, "temperament", "equal"),
                "key_root_pc": getattr(pattern, "key_root_pc", 0),
            }
            # Forward filter params from instrument
            if hasattr(inst, "filter_cutoff") and inst.filter_cutoff is not None:
                synth_kwargs["filter_cutoff"] = inst.filter_cutoff
                synth_kwargs["filter_resonance"] = getattr(inst, "filter_resonance", 0.0)
            # Forward pitch sweep params
            if hasattr(inst, "pitch_start") and inst.pitch_start is not None:
                synth_kwargs["pitch_start"] = inst.pitch_start
                synth_kwargs["pitch_end"] = getattr(inst, "pitch_end", 40.0)
            # Forward vibrato params
            vib_rate = getattr(inst, "vibrato_rate", 0.0)
            vib_depth = getattr(inst, "vibrato_depth", 0.0)
            if vib_rate > 0 and vib_depth > 0:
                synth_kwargs["vibrato_rate"] = vib_rate
                synth_kwargs["vibrato_depth"] = vib_depth
            # Forward distortion
            dist = getattr(inst, "distortion", 0.0)
            if dist > 0:
                synth_kwargs["distortion"] = dist
            # Forward highpass filter
            hp = getattr(inst, "highpass_cutoff", None)
            if hp is not None:
                synth_kwargs["highpass_cutoff"] = hp

            note_samples = synthesize_note(**synth_kwargs)

            # Resolve this note's effective frequency under the active tuning
            # so we can track prev_freq for the next note's glide.
            from .synth import note_to_freq as _ntf
            from .temperament import temper_freq as _tf
            _temp = synth_kwargs.get("temperament", "equal")
            if _temp == "equal":
                this_freq = _ntf(event.midi_note)
            else:
                this_freq = _tf(event.midi_note, _temp,
                                synth_kwargs.get("key_root_pc", 0))

            # Portamento — glide from previous note's frequency
            glide_ms = getattr(event, "glide_ms", 0.0)
            if glide_ms > 0 and prev_freq is not None and prev_freq != this_freq:
                from .synth import apply_portamento
                note_samples = apply_portamento(
                    note_samples,
                    start_freq=prev_freq,
                    end_freq=this_freq,
                    glide_time_sec=glide_ms / 1000.0,
                )

            # Stacked voice layers (multi-waveform timbres)
            extra_layers = getattr(inst, "layers", None)
            if extra_layers:
                from .synth import synthesize_note as _syn, note_to_freq
                from .temperament import temper_freq as _temper
                base_note = synth_kwargs["midi_note"]
                base_velocity = event.velocity * inst.volume
                pat_temperament = synth_kwargs.get("temperament", "equal")
                pat_key_root = synth_kwargs.get("key_root_pc", 0)
                # Resolve the primary's tempered frequency for detune offsets
                if pat_temperament == "equal":
                    base_freq = note_to_freq(base_note)
                else:
                    base_freq = _temper(base_note, pat_temperament, pat_key_root)
                for layer in extra_layers:
                    layer_kwargs = dict(synth_kwargs)
                    layer_kwargs["waveform"] = layer.waveform
                    layer_kwargs["duty"] = layer.duty
                    layer_kwargs["wavetable"] = layer.wavetable
                    if layer.adsr is not None:
                        layer_kwargs["adsr"] = layer.adsr
                    layer_kwargs["volume"] = base_velocity * layer.gain
                    # Detune in cents → frequency multiplier on top of base
                    layer_kwargs["freq_override"] = base_freq * (
                        2.0 ** (layer.detune_cents / 1200.0)
                    )
                    layer_buf = _syn(**layer_kwargs)
                    if len(layer_buf) < len(note_samples):
                        layer_buf = np.pad(layer_buf, (0, len(note_samples) - len(layer_buf)))
                    elif len(layer_buf) > len(note_samples):
                        layer_buf = layer_buf[: len(note_samples)]
                    note_samples = note_samples + layer_buf
                # Soft-clip the summed layers to avoid runaway peaks
                peak = float(np.max(np.abs(note_samples))) if len(note_samples) else 0.0
                if peak > 0.95:
                    note_samples = (np.tanh(note_samples * 0.85) / 0.85).astype(np.float32)

            # Apply filter envelope (ADSR-shaped) — preferred over linear sweep
            fenv = getattr(inst, "filter_env", None)
            if fenv is not None:
                from .synth import apply_filter_envelope
                note_samples = apply_filter_envelope(note_samples, fenv)
            else:
                # Legacy linear sweep (filter_env_start → filter_env_end)
                fenv_start = getattr(inst, "filter_env_start", None)
                fenv_end = getattr(inst, "filter_env_end", None)
                if fenv_start is not None and fenv_end is not None:
                    from .synth import apply_filter_sweep
                    note_samples = apply_filter_sweep(
                        note_samples, fenv_start, fenv_end,
                        resonance=getattr(inst, "filter_resonance", 0.3),
                    )

            n = len(note_samples)
            end = min(start_sample + n, total_samples)
            actually_placed = end - start_sample
            ch_buf[start_sample:end] += note_samples[:actually_placed]

            # Remember this note's frequency so the NEXT note in this
            # channel can glide from it.
            prev_freq = this_freq

        # Apply per-channel effects
        fx = channel_effects.get(ch_idx, {})
        if "delay" in fx:
            ch_buf = apply_delay(
                ch_buf,
                delay_sec=fx.get("delay", 0.25),
                feedback=fx.get("delay_feedback", 0.3),
                mix=fx.get("delay_mix", 0.25),
            )
        if "morph_target" in fx:
            # Spectral morph: blend this channel's waveform toward a target
            from .synth import spectral_morph, generate_additive, HARMONIC_PROFILES
            target_profile = fx.get("morph_target", "bell")
            morph_amount = fx.get("morph_amount", 0.5)
            # Generate target waveform at reference pitch
            target_harmonics = HARMONIC_PROFILES.get(target_profile)
            if target_harmonics:
                target_wave = generate_additive(220.0, len(ch_buf),
                                                harmonics=target_harmonics)
                # Scale target to match channel energy
                ch_energy = np.sqrt(np.mean(ch_buf ** 2))
                tgt_energy = np.sqrt(np.mean(target_wave ** 2))
                if tgt_energy > 0:
                    target_wave = target_wave * (ch_energy / tgt_energy)
                ch_buf = spectral_morph(ch_buf, target_wave, morph_amount)
        if "chorus" in fx:
            ch_buf = apply_chorus(
                ch_buf,
                detune_cents=fx.get("chorus_detune", 7.0),
                delay_ms=fx.get("chorus_delay", 20.0),
                mix=fx.get("chorus", 0.3),
            )
        if "phaser" in fx:
            from .effects import apply_phaser
            ch_buf = apply_phaser(
                ch_buf,
                rate_hz=fx.get("phaser_rate", 0.5),
                depth=fx.get("phaser_depth", 0.7),
                stages=fx.get("phaser_stages", 4),
                mix=fx.get("phaser", 0.5),
            )
        if "flanger" in fx:
            from .effects import apply_flanger
            ch_buf = apply_flanger(
                ch_buf,
                rate_hz=fx.get("flanger_rate", 0.3),
                depth_ms=fx.get("flanger_depth", 3.0),
                feedback=fx.get("flanger_feedback", 0.5),
                mix=fx.get("flanger", 0.5),
            )
        if "reverb" in fx:
            ch_buf = apply_reverb(
                ch_buf,
                room_size=fx.get("reverb", 0.5),
                damping=fx.get("reverb_damping", 0.5),
                mix=fx.get("reverb_mix", 0.2),
            )

        # Stereo panning (constant-power)
        pan = panning.get(ch_idx, 0.0)  # -1.0 left, 0.0 center, 1.0 right
        pan_norm = (pan + 1.0) / 2.0  # 0.0–1.0
        gain_l = np.float32(np.cos(pan_norm * np.pi / 2.0))
        gain_r = np.float32(np.sin(pan_norm * np.pi / 2.0))

        mix_l += ch_buf * gain_l
        mix_r += ch_buf * gain_r

    stereo = np.stack([mix_l, mix_r], axis=1)
    return stereo


# ---------------------------------------------------------------------------
# Song Renderer
# ---------------------------------------------------------------------------

def render_song(
    song: Song,
    instruments: Optional[dict[str, Instrument]] = None,
    normalize: bool = True,
    panning: Optional[dict[int, float]] = None,
    channel_effects: Optional[dict[int, dict]] = None,
    master_reverb: float = 0.0,
    master_delay: float = 0.0,
) -> np.ndarray:
    """
    Render a full Song arrangement to a stereo float32 audio buffer.

    Args:
        song: The Song to render.
        instruments: Instrument preset dict. Defaults to built-in PRESETS.
        normalize: If True, normalize peak amplitude to 0.92.
        panning: Per-channel pan positions passed to render_pattern.
        channel_effects: Per-channel effects passed to render_pattern.
        master_reverb: Master reverb mix (0.0 = off, 0.3 = subtle).
        master_delay: Master delay time in seconds (0.0 = off).

    Returns:
        Float32 numpy array, shape (num_samples, 2), values in range [-1, 1].
    """
    if not song.sequence:
        return np.zeros((0, 2), dtype=np.float32)

    has_curve = bool(getattr(song, "tempo_curve", None))
    has_dyn = bool(getattr(song, "dynamics_curve", None))
    dyn_fn = song.gain_lin_at_beat if has_dyn else None

    buffers: list[np.ndarray] = []
    cursor_beat = 0.0
    for pattern_idx in song.sequence:
        if not (0 <= pattern_idx < len(song.patterns)):
            continue
        pat = song.patterns[pattern_idx]

        # If a tempo curve exists, override this pattern's BPM with the
        # curve's value at the pattern's starting beat. We restore afterward
        # so the song object isn't mutated for the caller.
        original_bpm = pat.bpm
        if has_curve:
            pat.bpm = song.tempo_at_beat(cursor_beat)

        buf = render_pattern(
            pat, instruments, panning, channel_effects,
            start_beat=cursor_beat, dynamics_fn=dyn_fn,
        )
        buffers.append(buf)

        # Advance the beat cursor by the pattern's musical length (in beats),
        # NOT by its real-time length, so the curve indexing stays musically
        # meaningful regardless of tempo.
        cursor_beat += pat.num_steps / pat.steps_per_beat
        if has_curve:
            pat.bpm = original_bpm

    if not buffers:
        return np.zeros((0, 2), dtype=np.float32)

    mixed = np.concatenate(buffers, axis=0)

    # Master effects (applied to each channel independently)
    if master_reverb > 0:
        mixed[:, 0] = apply_reverb(mixed[:, 0], room_size=0.6, mix=master_reverb)
        mixed[:, 1] = apply_reverb(mixed[:, 1], room_size=0.6, mix=master_reverb)

    if master_delay > 0:
        mixed[:, 0] = apply_delay(mixed[:, 0], delay_sec=master_delay, feedback=0.3, mix=0.15)
        mixed[:, 1] = apply_delay(mixed[:, 1], delay_sec=master_delay * 1.07, feedback=0.3, mix=0.15)

    if normalize:
        peak = float(np.max(np.abs(mixed)))
        if peak > 0:
            mixed = mixed * (0.92 / peak)

    # Soft clip for safety
    mixed = soft_clip(mixed, threshold=0.95)

    return mixed.astype(np.float32)


# ---------------------------------------------------------------------------
# Optional Real-Time Playback
# ---------------------------------------------------------------------------

def play_audio(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    """
    Play an audio buffer through the system speakers.

    Requires the `sounddevice` package. If it is not installed, this function
    logs a message and returns without error — export to WAV instead.

    Args:
        audio: Float32 array, shape (num_samples, 2) or (num_samples,).
        sample_rate: Sample rate in Hz.
    """
    try:
        import sounddevice as sd  # type: ignore[import-untyped]
        sd.play(audio, samplerate=sample_rate)
        sd.wait()
    except ImportError:
        print(
            "[ChipForge] sounddevice is not installed. "
            "Run `pip install sounddevice` for realtime playback, "
            "or use export_wav() to save to a file."
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ChipForge] Playback error: {exc}")
