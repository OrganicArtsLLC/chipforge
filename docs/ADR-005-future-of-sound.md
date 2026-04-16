# ADR-005: The Future of Sound — Engineering the Next Level

**Status:** Proposed  
**Date:** March 29, 2026  
**Author:** Joshua Ayson / OA LLC + Claude AI  
**Supersedes:** Portions of ADR-002 (quality/speed/web roadmap)  
**Companion:** ADR-004 (AI-only synthesis frontiers)

---

## Context

ChipForge has reached a strong foundation: 46 instrument presets, 6 waveform generators with PolyBLEP anti-aliasing, Schroeder reverb, feedback delay, chorus, 12 scales, 10 chord types, 7 drum groove templates, and a clean tracker-style sequencer. The engine renders full songs with rich stereo output. Quality is genuinely good.

But "good" is not the ceiling. This ADR maps the path from good to extraordinary across every dimension: mathematics, music theory, signal processing, software engineering, and performance. It answers:

1. **What DSP techniques are standard in professional production but missing here?**
2. **What effects do EDM artists and DJs rely on that can be built into code?**
3. **Where are the performance bottlenecks and how do we eliminate them?**
4. **How does post-processing work, and can we do it in-code before WAV export?**
5. **What does the architecture look like as this grows?**

### Current Technical Baseline

| Module | Lines | What It Does | Key Limitation |
|--------|-------|-------------|----------------|
| `synth.py` | ~665 | Waveform generation, ADSR, filters, vibrato | Filters are per-sample Python loops (slow) |
| `mixer.py` | ~410 | Channel rendering, reverb, delay, chorus, panning | Reverb is 80% of render time (per-sample loops) |
| `instruments.py` | ~600 | 46 presets, wavetables, ADSR configs | No runtime modulation, no layering |
| `sequencer.py` | ~280 | Pattern/Song dataclasses, tracker grid | No automation lanes, no tempo changes |
| `theory.py` | ~600 | Scales, chords, progressions, grooves | Limited chord voicings, no harmonic analysis |
| `export.py` | ~150 | WAV export, JSON persistence | Only 16-bit WAV, no compressed formats |

### The Post-Processing Question

> *"I'm guessing everything so far can be done directly in code and nothing is getting post-processed?"*

**Correct.** Everything happens in-memory as numpy float32 arrays before a single WAV byte is written. The full pipeline:

```
Note events → synthesize_note() → per-channel effects → stereo panning → 
channel summing → master effects → normalization → soft clip → WAV export
```

**This is actually an advantage.** Unlike a DAW where you record audio then process it, ChipForge has access to the entire audio buffer as a numpy array at every stage. We can apply any DSP operation — convolution, FFT analysis, multiband compression, spectral processing — before export. The buffer is just numbers.

**For web/gaming (Pixel Vault):** Real-time audio in browsers uses the Web Audio API, which has its own effect nodes (gain, delay, convolution, biquad filter, compressor, etc.). The rendering pipeline would need to be reimplemented in JavaScript/WebAssembly, but the _algorithms_ are identical. Songs could ship as:
- Pre-rendered compressed audio (OGG/MP3, ~1MB per 3-minute track)
- Procedural generation scripts (JS that builds audio in real-time, ~5-10KB)
- Hybrid (pre-rendered with real-time parameter variation)

This ADR focuses on what we build into the Python engine. Web/JS reimplementation is tracked separately.

---

## Decision

We will evolve ChipForge across five domains, prioritized by impact:

| Priority | Domain | Sections |
|----------|--------|----------|
| **P0** | Performance (render speed) | §1 |
| **P0** | Effects (production-grade DSP) | §2 |
| **P1** | Synthesis (sound generation) | §3 |
| **P1** | Sequencer (composition tools) | §4 |
| **P2** | Theory (musical intelligence) | §5 |
| **P2** | Export (formats & integration) | §6 |
| **P3** | Architecture (scaling & DevOps) | §7 |

---

## §1 — Performance: From Minutes to Seconds

### Problem

A 65-second song with 7 channels and full effects takes **65-290 seconds** to render. The bottleneck is clear:

| Component | Time | % of Total | Root Cause |
|-----------|------|-----------|------------|
| Schroeder reverb | 30-40s/channel | **~80%** | 6 comb + 4 allpass filters, each a Python `for` loop iterating over every sample |
| Low-pass filter | 3-8s/channel | **~10%** | State-variable filter requires per-sample feedback |
| Waveform synthesis | 1-3s total | **~3%** | Already vectorized |
| ADSR + panning | <1s total | **~1%** | Already vectorized |

### Solution 1.1: Vectorized Reverb via FFT Convolution (P0)

Replace the Schroeder reverb with **convolution reverb** using precomputed impulse responses:

```python
import numpy as np
from scipy.signal import fftconvolve

def generate_schroeder_ir(room_size: float, damping: float, 
                          duration_sec: float = 2.0) -> np.ndarray:
    """Generate Schroeder impulse response ONCE, reuse for all channels."""
    num_samples = int(SAMPLE_RATE * duration_sec)
    impulse = np.zeros(num_samples)
    impulse[0] = 1.0
    # Run the existing Schroeder algorithm on the impulse
    return apply_reverb_direct(impulse, room_size, damping, mix=1.0)

def apply_reverb_fft(audio: np.ndarray, ir: np.ndarray, mix: float) -> np.ndarray:
    """Apply reverb via FFT convolution — O(n log n) instead of O(n²)."""
    wet = fftconvolve(audio, ir, mode='full')[:len(audio)]
    return audio * (1 - mix) + wet * mix
```

**Speedup:** 50-100x for reverb. A 30-second reverb operation drops to 0.3-0.6 seconds. The impulse response is generated once and cached.

**Tradeoff:** Requires `scipy` as a dependency (already near-standard for scientific Python). Alternatively, `numpy.fft` can implement overlap-add convolution manually.

### Solution 1.2: Vectorized State-Variable Filter (P0)

The current SVF filter uses a Python `for` loop because it has per-sample state feedback. Two approaches:

**Option A: Block-based processing** — Process audio in blocks of 64-256 samples, running the feedback loop in C via `numpy` ufuncs or `numba.jit`:

```python
from numba import njit

@njit(cache=True)
def svf_filter_fast(samples, cutoff_hz, resonance, sample_rate):
    """JIT-compiled state-variable filter — near C speed."""
    n = len(samples)
    output = np.empty(n, dtype=np.float64)
    low = band = high = 0.0
    for i in range(n):
        f = 2.0 * np.sin(np.pi * cutoff_hz / sample_rate)
        q = 1.0 - resonance
        high = samples[i] - low - q * band
        band += f * high
        low += f * band
        output[i] = low
    return output.astype(np.float32)
```

**Speedup:** 20-50x via Numba JIT compilation (first call compiles, subsequent calls run at C speed).

**Option B: SciPy `sosfilt`** — Use the built-in second-order-section filter:

```python
from scipy.signal import butter, sosfilt

def apply_lowpass_scipy(samples, cutoff_hz, order=2):
    sos = butter(order, cutoff_hz, btype='low', fs=SAMPLE_RATE, output='sos')
    return sosfilt(sos, samples).astype(np.float32)
```

**Speedup:** 30-100x. No loop at all — runs in compiled C/Fortran. Supports any filter order (2-pole, 4-pole, etc.).

### Solution 1.3: Parallel Channel Rendering (P1)

Each channel is independent during pattern rendering. Use `multiprocessing`:

```python
from multiprocessing import Pool

def render_pattern_parallel(pattern, instruments, panning, channel_effects):
    channels = range(pattern.num_channels)
    with Pool(processes=min(len(channels), os.cpu_count())) as pool:
        channel_buffers = pool.starmap(render_single_channel, 
            [(pattern, ch, instruments, channel_effects) for ch in channels])
    # Sum to stereo
    return sum_channels_stereo(channel_buffers, panning)
```

**Speedup:** Near-linear with core count. On an 8-core M2: 7 channels in ~1/4 the time.

**Caveat:** Process startup has overhead (~200ms). Only beneficial for songs with 4+ channels where per-channel work exceeds 2-3 seconds.

### Solution 1.4: Draft Mode (P2)

Render at 22050 Hz (half sample rate) for quick previews:

```python
DRAFT_SAMPLE_RATE = 22050

def render_draft(song, **kwargs):
    """Render at half quality for instant feedback."""
    global SAMPLE_RATE
    original = SAMPLE_RATE
    SAMPLE_RATE = DRAFT_SAMPLE_RATE
    try:
        audio = render_song(song, **kwargs)
    finally:
        SAMPLE_RATE = original
    return audio
```

**Speedup:** 4x (half the samples, plus effects are cheaper on shorter buffers).

### Performance Roadmap

| Phase | Change | Expected Render Time (65s song, 7ch) | Speedup |
|-------|--------|--------------------------------------|---------|
| **Current** | Python loops | 90-290s | 1x |
| **Phase 1** | FFT reverb + scipy filter | 8-15s | 15-30x |
| **Phase 2** | + parallel channels | 3-6s | 40-80x |
| **Phase 3** | + draft mode (22050 Hz) | 1-2s | 100-200x |

---

## §2 — Effects: Production-Grade DSP

This is where professional sound is made. EDM producers use these effects on every track. All can be implemented as numpy operations on the audio buffer before WAV export.

### 2.1 Compressor / Limiter (P0)

**What it does:** Reduces dynamic range — loud parts get quieter, quiet parts get louder. Essential for making a mix "glue" together.

**Why we need it:** The current `soft_clip()` is a hard ceiling that prevents clipping but doesn't shape dynamics. A real compressor has controllable behavior.

```python
@dataclass
class CompressorConfig:
    threshold_db: float = -12.0   # when to start compressing
    ratio: float = 4.0            # 4:1 compression
    attack_ms: float = 5.0        # how fast to react (ms)
    release_ms: float = 50.0      # how fast to let go (ms)
    makeup_gain_db: float = 0.0   # boost after compression
    knee_db: float = 6.0          # soft knee width

def apply_compressor(audio: np.ndarray, config: CompressorConfig) -> np.ndarray:
    """RMS-based compressor with attack/release envelope following."""
    # Convert to dB domain
    # Compute gain reduction envelope
    # Apply attack/release smoothing
    # Apply gain + makeup gain
    ...
```

**Key variant — Sidechain Compression (the EDM pump):**

```python
def apply_sidechain(audio: np.ndarray, sidechain_signal: np.ndarray,
                    threshold_db: float = -20.0, ratio: float = 8.0,
                    attack_ms: float = 1.0, release_ms: float = 100.0) -> np.ndarray:
    """Duck audio based on another signal (usually kick drum).
    Creates the classic EDM pumping effect."""
    ...
```

In ChipForge, the sidechain signal would be the kick drum channel. Every time the kick hits, all other channels duck momentarily — creating that rhythmic breathing effect that defines EDM.

### 2.2 Parametric EQ (P0)

**What it does:** Boost or cut specific frequency ranges. Like a tone control but surgical.

**Current state:** Only a 2-pole low-pass filter. No high-pass, band-pass, shelf, or notch.

```python
@dataclass
class EQBand:
    freq_hz: float          # center frequency
    gain_db: float          # boost/cut (-12 to +12)
    q: float = 1.0          # width (0.5 = wide, 4.0 = narrow)
    band_type: str = 'peak' # 'peak', 'lowshelf', 'highshelf', 'highpass', 'lowpass', 'notch'

def apply_parametric_eq(audio: np.ndarray, bands: list[EQBand]) -> np.ndarray:
    """Multi-band parametric EQ using cascaded biquad filters."""
    from scipy.signal import sosfilt
    result = audio.copy()
    for band in bands:
        sos = design_biquad(band)
        result = sosfilt(sos, result).astype(np.float32)
    return result
```

**Common producer EQ moves:**
- High-pass at 30 Hz on everything except kick/bass (removes rumble)
- Low shelf cut at 200 Hz on pads (prevents muddiness)
- Presence boost at 3-5 kHz on leads (cuts through mix)
- Air shelf boost at 10-12 kHz on hats/cymbals (shimmer)
- Notch at 300-500 Hz on congested mixes (removes boxiness)

### 2.3 Distortion / Saturation (P0)

**What it does:** Adds harmonic content by clipping or shaping the waveform. From subtle warmth to screaming overdrive.

```python
def apply_distortion(audio: np.ndarray, drive: float = 0.5, 
                     mode: str = 'soft') -> np.ndarray:
    """
    Waveshaping distortion.
    
    Modes:
      'soft'    — tanh saturation (tube-like warmth)
      'hard'    — hard clip (aggressive, digital)
      'foldback' — wave folding (complex harmonics, Buchla-style)
      'bitcrush' — reduce bit depth (lo-fi, retro)
      'rectify' — half/full wave rectification (octave up effect)
    """
    if mode == 'soft':
        driven = audio * (1.0 + drive * 10.0)
        return np.tanh(driven) * 0.9
    elif mode == 'hard':
        driven = audio * (1.0 + drive * 10.0)
        return np.clip(driven, -1.0, 1.0)
    elif mode == 'foldback':
        driven = audio * (1.0 + drive * 5.0)
        # Fold back into [-1, 1] — creates odd harmonics
        return 4.0 * (np.abs(0.25 * driven + 0.25 - 
               np.round(0.25 * driven + 0.25)) - 0.25)
    elif mode == 'bitcrush':
        bits = max(2, int(16 - drive * 14))  # 16-bit down to 2-bit
        levels = 2 ** bits
        return np.round(audio * levels) / levels
    elif mode == 'rectify':
        return np.abs(audio)  # full-wave rectification
```

**EDM applications:**
- Soft saturation on bass (adds harmonics audible on small speakers)
- Bitcrushing on drums (lo-fi texture)
- Foldback distortion on leads (metallic, aggressive)
- Subtle drive on the master bus (analog warmth simulation)

### 2.4 Flanger (P1)

**What it does:** Sweeps a short delay (0.1-10ms) with LFO modulation, creating a "jet plane" sweeping effect. Classic on guitars and synths.

```python
def apply_flanger(audio: np.ndarray, rate: float = 0.25, 
                  depth: float = 0.7, feedback: float = 0.5,
                  min_delay_ms: float = 0.1, max_delay_ms: float = 7.0,
                  mix: float = 0.5) -> np.ndarray:
    """
    Flanger effect via LFO-modulated delay line.
    
    rate: LFO speed in Hz (0.05-2.0)
    depth: LFO amount (0-1)
    feedback: delayed signal fed back (creates resonance)
    """
    n = len(audio)
    t = np.arange(n) / SAMPLE_RATE
    lfo = 0.5 * (1.0 + np.sin(2.0 * np.pi * rate * t))  # 0 to 1
    delay_samples = ((min_delay_ms + depth * lfo * (max_delay_ms - min_delay_ms)) 
                     * SAMPLE_RATE / 1000.0)
    # Fractional delay via linear interpolation
    output = np.zeros_like(audio)
    for i in range(n):
        d = delay_samples[i]
        idx = i - d
        if idx >= 1:
            frac = idx - int(idx)
            output[i] = audio[i] + mix * (
                audio[int(idx)] * (1 - frac) + audio[int(idx) - 1] * frac
            )
        else:
            output[i] = audio[i]
    # Note: this loop should be @njit compiled for performance
    return output
```

### 2.5 Phaser (P1)

**What it does:** Passes audio through a series of all-pass filters whose frequencies sweep via LFO, creating notches that move through the spectrum. Subtler than flanger, "swirling" quality.

```python
def apply_phaser(audio: np.ndarray, rate: float = 0.3,
                 depth: float = 0.7, stages: int = 4,
                 feedback: float = 0.3, mix: float = 0.5) -> np.ndarray:
    """
    Phaser effect using cascaded all-pass filters with LFO modulation.
    
    stages: number of all-pass filter stages (2, 4, 6, 8 typical)
    More stages = more pronounced notches
    """
    ...
```

### 2.6 Stereo Widener / Haas Effect (P1)

**What it does:** Makes a mono source sound wider in stereo by introducing tiny timing or EQ differences between left and right.

```python
def apply_stereo_widener(audio_stereo: np.ndarray, width: float = 1.5,
                         method: str = 'mid_side') -> np.ndarray:
    """
    Stereo width control.
    
    width: 0.0 = mono, 1.0 = unchanged, 2.0 = extra wide
    
    Methods:
      'mid_side' — boost side signal relative to mid (musical, mono-compatible)
      'haas'     — delay one channel by 10-30ms (wide but can cause phase issues)
      'eq_diff'  — apply different EQ to L and R (subtle widening)
    """
    mid = (audio_stereo[:, 0] + audio_stereo[:, 1]) * 0.5
    side = (audio_stereo[:, 0] - audio_stereo[:, 1]) * 0.5
    side *= width
    return np.column_stack([mid + side, mid - side])
```

### 2.7 Filter Effects — Auto-Wah, Envelope Filter (P1)

**What it does:** The filter cutoff responds to the amplitude of the input signal. Loud notes open the filter (bright), quiet notes close it (dark). Classic funk/electronic sound.

```python
def apply_envelope_filter(audio: np.ndarray, sensitivity: float = 1.0,
                          min_cutoff: float = 200.0, max_cutoff: float = 8000.0,
                          resonance: float = 0.4, attack_ms: float = 5.0,
                          release_ms: float = 50.0) -> np.ndarray:
    """Amplitude-following filter (auto-wah / envelope filter)."""
    ...
```

### 2.8 Tape Delay / Ping-Pong Delay (P1)

**Current state:** Simple feedback delay with echo taps. Upgrades:

```python
def apply_ping_pong_delay(audio_stereo: np.ndarray, 
                          delay_time_l: float = 0.375,
                          delay_time_r: float = 0.250,
                          feedback: float = 0.4,
                          filter_cutoff: float = 3000.0,
                          mix: float = 0.3) -> np.ndarray:
    """
    Ping-pong delay: echoes alternate between left and right channels.
    
    Each tap passes through a low-pass filter (simulates tape degradation).
    Different delay times for L/R create spatial movement.
    """
    ...

def apply_tape_delay(audio: np.ndarray, delay_sec: float = 0.3,
                     feedback: float = 0.5, wow_flutter: float = 0.02,
                     saturation: float = 0.3, filter_cutoff: float = 4000.0,
                     mix: float = 0.35) -> np.ndarray:
    """
    Tape-style delay with analog character.
    
    wow_flutter: pitch modulation from tape speed variation
    saturation: soft clipping on feedback path (tape compression)
    filter_cutoff: LP filter on each tap (darker echoes over time)
    """
    ...
```

### 2.9 Granular Delay / Stutter (P2)

**What it does:** Chops audio into tiny grains (10-100ms) and replays/rearranges them. Creates glitchy, stuttering, or timestretching effects popular in modern EDM.

```python
def apply_stutter(audio: np.ndarray, stutter_rate: float = 8.0,
                  grain_size_ms: float = 50.0, repeat: int = 4,
                  pitch_shift: float = 0.0) -> np.ndarray:
    """
    Rhythmic stutter/gate effect.
    
    stutter_rate: repetitions per beat
    grain_size_ms: size of each repeated grain
    repeat: how many times to repeat each grain
    pitch_shift: semitones to shift repeated grains
    """
    ...
```

### 2.10 Convolution Reverb (P2)

**What it does:** Instead of algorithmic reverb (which approximates a room), convolution reverb captures the actual acoustic signature of a real space and applies it mathematically.

```python
# Precomputed impulse responses for different spaces
REVERB_PRESETS = {
    'small_room': generate_ir(room_size=0.2, rt60=0.3),
    'large_hall': generate_ir(room_size=0.8, rt60=2.5),
    'cathedral': generate_ir(room_size=0.95, rt60=4.0),
    'plate': generate_plate_ir(decay=1.5),           # classic studio plate
    'spring': generate_spring_ir(tension=0.7),         # guitar amp spring reverb
    'shimmer': generate_shimmer_ir(pitch_shift=12),    # octave-up reverb tail
    'reverse': generate_reverse_ir(rt60=1.5),          # reversed reverb (pre-echo)
    'gated': generate_gated_ir(threshold=-30, rt60=0.5), # 80s gated snare
}
```

### 2.11 Master Bus Processing Chain (P1)

Professional producers always apply effects to the final stereo mix. We should build a configurable master chain:

```python
@dataclass
class MasterBusConfig:
    # EQ
    highpass_hz: float = 30.0          # remove sub-rumble
    low_shelf_hz: float = 80.0         # bass warmth control
    low_shelf_db: float = 0.0
    presence_hz: float = 4000.0        # vocal/lead presence
    presence_db: float = 0.0
    air_shelf_hz: float = 12000.0      # high-end sparkle
    air_shelf_db: float = 0.0
    # Compression
    comp_threshold_db: float = -8.0
    comp_ratio: float = 2.0
    comp_attack_ms: float = 10.0
    comp_release_ms: float = 100.0
    # Stereo
    stereo_width: float = 1.0          # 0=mono, 1=natural, 2=wide
    # Limiting
    limiter_ceiling_db: float = -0.3   # final ceiling (prevents clipping)
    # Saturation
    analog_warmth: float = 0.0         # 0=clean, 1=warm tape color

def apply_master_bus(audio_stereo: np.ndarray, 
                     config: MasterBusConfig) -> np.ndarray:
    """Full mastering chain applied to final stereo mix."""
    audio = audio_stereo.copy()
    # 1. High-pass filter (remove rumble)
    audio = apply_highpass(audio, config.highpass_hz)
    # 2. Parametric EQ (shape tonality)
    audio = apply_master_eq(audio, config)
    # 3. Compression (glue the mix)
    audio = apply_compressor(audio, config.comp_threshold_db, config.comp_ratio,
                             config.comp_attack_ms, config.comp_release_ms)
    # 4. Stereo widening
    audio = apply_stereo_widener(audio, config.stereo_width)
    # 5. Analog warmth (subtle saturation)
    if config.analog_warmth > 0:
        audio = apply_distortion(audio, drive=config.analog_warmth * 0.15, mode='soft')
    # 6. Final limiter (brick wall at ceiling)
    audio = apply_limiter(audio, config.limiter_ceiling_db)
    return audio
```

### Effects Summary Table

| Effect | Priority | Complexity | EDM Essential? | Impact |
|--------|----------|-----------|----------------|--------|
| Compressor / Sidechain | P0 | Medium | **YES** — defines the genre | Massive |
| Parametric EQ | P0 | Medium (via scipy) | **YES** | Large |
| Distortion / Saturation | P0 | Easy | Yes | Large |
| Master Bus Chain | P1 | Medium | **YES** | Massive |
| Ping-Pong Delay | P1 | Easy | Yes | Medium |
| Tape Delay | P1 | Medium | Yes | Medium |
| Flanger | P1 | Medium | Sometimes | Medium |
| Phaser | P1 | Medium | Sometimes | Medium |
| Stereo Widener | P1 | Easy | Yes | Large |
| Envelope Filter | P1 | Medium | Sometimes | Medium |
| Convolution Reverb | P2 | Medium (FFT) | Nice to have | Large |
| Granular Stutter | P2 | Medium | Yes (modern EDM) | Medium |
| Gated Reverb | P2 | Easy (variant of reverb) | Sometimes | Small |
| Shimmer Reverb | P2 | Medium | Yes (ambient, synthwave) | Medium |
| Vocoder | P3 | Hard | Niche | Small |

---

## §3 — Synthesis: The Sound Itself

### 3.1 Multi-Oscillator Instruments / Layering (P0)

**What it does:** Stack multiple waveforms per note, each with independent pitch, volume, and filtering. This is how every modern synth works (Serum, Massive, Vital all have 2-3 oscillators plus sub-oscillator).

```python
@dataclass
class OscillatorLayer:
    waveform: str = 'sawtooth'
    detune_cents: float = 0.0        # pitch offset in cents (100 = 1 semitone)
    octave_offset: int = 0           # +1 = one octave up
    volume: float = 1.0              # relative volume
    duty: float = 0.25               # for square waves
    filter_cutoff: float | None = None
    filter_resonance: float = 0.0

@dataclass
class MultiOscInstrument:
    name: str
    oscillators: list[OscillatorLayer]
    adsr: ADSR
    volume: float = 0.80
    # ... existing fields ...
```

**Example — "Supersaw" lead (Trance/EDM staple):**
```python
'supersaw': MultiOscInstrument(
    name='supersaw',
    oscillators=[
        OscillatorLayer('sawtooth', detune_cents=0),     # center
        OscillatorLayer('sawtooth', detune_cents=+7),     # sharp
        OscillatorLayer('sawtooth', detune_cents=-7),     # flat
        OscillatorLayer('sawtooth', detune_cents=+15),    # wider sharp
        OscillatorLayer('sawtooth', detune_cents=-15),    # wider flat
        OscillatorLayer('sawtooth', detune_cents=+25, volume=0.5),
        OscillatorLayer('sawtooth', detune_cents=-25, volume=0.5),
    ],
    adsr=ADSR(attack=0.01, decay=0.1, sustain=0.7, release=0.2),
    volume=0.55,  # lower because 7 voices sum hot
)
```

### 3.2 Unison & Detune (P0)

Closely related to multi-oscillator but as a simple parameter:

```python
@dataclass
class Instrument:
    # ... existing fields ...
    unison_voices: int = 1           # 1 = mono, 3-7 = thick
    unison_detune: float = 0.0       # spread in cents (7-25 typical)
    unison_stereo_spread: float = 0.0  # 0 = center, 1 = full L/R spread
```

### 3.3 FM Synthesis (P1)

**What it does:** One oscillator (modulator) modulates the frequency of another (carrier), creating complex harmonic spectra impossible with subtractive synthesis. This is how the Yamaha DX7 worked. Basis of electric piano, bell, and metallic sounds.

```python
def generate_fm(carrier_freq: float, mod_freq: float, mod_index: float,
                num_samples: int) -> np.ndarray:
    """
    2-operator FM synthesis.
    
    carrier_freq: fundamental frequency
    mod_freq: modulator frequency (ratio to carrier defines timbre)
    mod_index: modulation depth (0 = sine, 1-3 = harmonics, 5+ = metallic)
    
    Classic ratios:
      1:1 — sawtooth-like
      1:2 — clarinet-like (odd harmonics)
      1:3 — bell-like
      1:√2 — inharmonic, metallic
    """
    t = np.arange(num_samples) / SAMPLE_RATE
    modulator = mod_index * np.sin(2.0 * np.pi * mod_freq * t)
    carrier = np.sin(2.0 * np.pi * carrier_freq * t + modulator)
    return carrier.astype(np.float32)
```

Can extend to 4-operator or 6-operator (like the DX7) for enormous timbral variety — each operator can modulate others in different algorithms (series, parallel, branching).

### 3.4 Wavetable Morphing (P1)

**Current state:** Fixed 32-sample wavetables from Game Boy CH3. 

**Upgrade:** Support interpolation between multiple wavetable frames over the duration of a note:

```python
def generate_wavetable_morph(wavetables: list[np.ndarray], freq: float,
                              num_samples: int, 
                              morph_curve: np.ndarray) -> np.ndarray:
    """
    Morph between wavetable frames over time.
    
    wavetables: list of waveform arrays (e.g., sine → saw → square)
    morph_curve: 0.0-1.0 array controlling which frame(s) are active
    
    This is how Serum and Vital work — the wavetable position sweeps
    through different waveform shapes, creating evolving timbres.
    """
    ...
```

### 3.5 Physical Modeling (P2)

**What it does:** Simulates the physics of real instruments using digital waveguide synthesis. A string is modeled as a delay line with damping. A tube (flute/clarinet) is modeled as a bidirectional delay line with reflection.

**Application:** More realistic plucked strings, blown tubes, struck surfaces than any preset can achieve.

```python
def karplus_strong(freq: float, num_samples: int, 
                   damping: float = 0.5, 
                   brightness: float = 0.5) -> np.ndarray:
    """
    Karplus-Strong plucked string synthesis.
    
    1. Fill a delay buffer (length = sample_rate / freq) with noise
    2. Each sample = average of delay[i] and delay[i+1] (low-pass)
    3. Feed back into delay buffer
    
    Naturally creates plucked string sound. Near zero CPU cost.
    """
    period = int(SAMPLE_RATE / freq)
    buf = np.random.uniform(-1, 1, period).astype(np.float32)
    output = np.zeros(num_samples, dtype=np.float32)
    for i in range(num_samples):
        output[i] = buf[i % period]
        buf[i % period] = (damping * buf[i % period] + 
                          (1 - damping) * buf[(i + 1) % period]) * brightness
    return output
```

### 3.6 Noise Types Beyond LFSR (P2)

| Type | Character | Use |
|------|-----------|-----|
| White noise | Equal energy per frequency | Snares, risers |
| Pink noise | Equal energy per octave (natural) | Pads, ambience, ocean |
| Brown noise | -6 dB/octave (bass-heavy) | Rumble, sub-bass texture |
| Blue noise | +3 dB/octave (treble-heavy) | Hi-hats, shimmer |
| Velvet noise | Sparse impulse noise | Vintage drum machines |

```python
def generate_pink_noise(num_samples: int) -> np.ndarray:
    """Pink noise via Voss-McCartney algorithm."""
    ...

def generate_brown_noise(num_samples: int) -> np.ndarray:
    """Brownian noise (integrated white noise with drift limiting)."""
    white = np.random.randn(num_samples)
    brown = np.cumsum(white)
    brown = brown / np.max(np.abs(brown))  # normalize
    return brown.astype(np.float32)
```

### 3.7 Advanced ADSR: Multi-Stage Envelopes (P2)

Real synthesizers go beyond ADSR. Multi-stage envelopes allow arbitrary shapes:

```python
@dataclass
class EnvelopeStage:
    duration_sec: float
    target_level: float
    curve: float = 1.0  # 1.0=linear, >1=exponential, <1=logarithmic

@dataclass
class MultiStageEnvelope:
    stages: list[EnvelopeStage]
    loop_start: int | None = None   # loop between stages for sustain
    loop_end: int | None = None
    
    # Example: AHDSR (Attack-Hold-Decay-Sustain-Release)
    # stages = [
    #   (0.01, 1.0, 2.0),   # attack to peak
    #   (0.05, 1.0, 1.0),   # hold at peak
    #   (0.1,  0.6, 1.5),   # decay to sustain
    #   (0.0,  0.6, 1.0),   # sustain (zero duration = wait for note-off)
    #   (0.2,  0.0, 0.8),   # release to silence
    # ]
```

### Synthesis Summary

| Feature | Priority | Impact | Opens Up |
|---------|----------|--------|----------|
| Multi-oscillator / Unison | P0 | Massive | Supersaws, detuned leads, thick pads |
| FM Synthesis | P1 | Large | Electric pianos, bells, metallic timbres |
| Wavetable morphing | P1 | Large | Evolving timbres, modern synth sounds |
| Physical modeling | P2 | Medium | Realistic strings, plucks, mallets |
| Colored noise | P2 | Medium | Better drums, ambience, textures |
| Multi-stage envelopes | P2 | Medium | Complex dynamics, looping sounds |

---

## §4 — Sequencer: Composition Architecture

### 4.1 Automation Lanes (P1)

**What it does:** Control any parameter (filter cutoff, volume, panning, effect wet/dry) over time, per step.

**Current state:** Parameters are static per note. A filter cutoff is set once and stays. No way to sweep a filter over a 4-bar phrase.

```python
@dataclass
class AutomationPoint:
    step: int
    value: float
    curve: str = 'linear'  # 'linear', 'exponential', 'step', 'smooth'

@dataclass
class AutomationLane:
    target: str              # e.g., 'filter_cutoff', 'volume', 'pan', 'reverb_mix'
    channel: int
    points: list[AutomationPoint]
    
    def value_at_step(self, step: float) -> float:
        """Interpolate between automation points."""
        ...

@dataclass
class Pattern:
    # ... existing fields ...
    automation: list[AutomationLane] = field(default_factory=list)
```

**Use cases:**
- Filter sweep building over 8 bars (rising energy)
- Volume swell at start of verse
- Panning movement (auto-pan on hi-hats)
- Reverb mix increase during breakdown, decrease at drop
- Delay feedback ramp for psychedelic builds

### 4.2 Tempo Changes & Time Signatures (P1)

**Current state:** BPM is fixed per song. Only 4/4 time.

```python
@dataclass
class TempoEvent:
    bar: int
    bpm: float
    transition: str = 'instant'  # 'instant', 'linear', 'exponential'
    transition_bars: int = 0      # how many bars to transition

@dataclass
class TimeSignature:
    numerator: int = 4    # beats per bar
    denominator: int = 4  # beat unit (4 = quarter note)

@dataclass
class Song:
    # ... existing fields ...
    tempo_map: list[TempoEvent] = field(default_factory=list)
    time_signature: TimeSignature = field(default_factory=TimeSignature)
```

### 4.3 Swing / Groove Quantization (P1)

**What it does:** Offsets the timing of alternate 16th notes to create a shuffle/swing feel. Straight quantized music sounds robotic.

```python
def apply_swing(grid: list, swing_amount: float = 0.6) -> list:
    """
    Shift every other 16th note forward in time.
    
    swing_amount:
      0.5 = straight (no swing)
      0.6 = subtle swing (house)
      0.667 = triplet swing (jazz)
      0.75 = extreme swing (hip-hop)
    """
    # Implemented by adjusting the sample offset of odd-numbered steps
    ...
```

### 4.4 Micro-Timing / Humanization (P2)

Beyond swing — add random timing and velocity variation to emulate human playing:

```python
@dataclass
class HumanizeConfig:
    timing_ms: float = 5.0       # random timing offset (±ms)
    velocity_range: float = 0.05 # random velocity variation (±)
    chance_to_skip: float = 0.0  # probability of omitting a note (ghost feel)
    
def humanize_pattern(pattern: Pattern, config: HumanizeConfig) -> Pattern:
    """Add subtle timing and velocity randomization."""
    ...
```

### 4.5 Fill / Transition Generator (P2)

Automatic generation of drum fills for transitions:

```python
def generate_fill(fill_type: str, bars: int = 1, 
                  instrument: str = 'snare_tight') -> Pattern:
    """
    Generate transition fills.
    
    Types:
      'buildup'   — accelerating hits (8th → 16th → 32nd)
      'breakdown'  — strip layers, add riser noise
      'roll'      — snare roll (even hits, increasing velocity)
      'stutter'   — rhythmic gate (half bar repetition)
      'drop'      — silence → impact (one bar silence + kick hit)
      'sweep'     — noise sweep rising to climax
    """
    ...
```

---

## §5 — Theory: Musical Intelligence

### 5.1 Voice Leading & Chord Inversions (P1)

**Current state:** Chords are always in root position. C major = C3-E3-G3.

**Reality:** Good voice leading minimizes the distance between consecutive chord notes. C major → F major shouldn't jump C3-E3-G3 → F3-A3-C4. Instead: C3-E3-G3 → C3-F3-A3 (one note moves, two are close).

```python
def voice_lead(chord_a: list[int], chord_b: list[int]) -> list[int]:
    """
    Revoice chord_b to minimize total movement from chord_a.
    
    Uses minimal-distance algorithm:
    1. Generate all inversions/octave placements of chord_b
    2. Score each by sum of absolute semitone movement from chord_a
    3. Return the voicing with minimum total movement
    """
    ...
```

### 5.2 Tension / Resolution Mapping (P1)

Model harmonic tension numerically so the engine can generate progressions that build and release:

```python
TENSION_TABLE = {
    'I':   0.0,   # home, resolved
    'ii':  0.3,   # mild tension
    'iii': 0.2,   # relative minor, gentle
    'IV':  0.3,   # subdominant, mild away
    'V':   0.6,   # dominant, wants to resolve
    'V7':  0.8,   # strong pull to I
    'vi':  0.2,   # deceptive, melancholic
    'vii°': 0.9,  # maximum tension (diminished)
    '#IV': 0.7,   # Lydian tension
    'bVII': 0.5,  # modal, floating
}

def generate_tension_curve(shape: str, bars: int) -> list[float]:
    """
    Generate a target tension curve for a section.
    
    Shapes:
      'build'     — 0.2 → 0.8 (steadily increasing)
      'release'   — 0.8 → 0.2 (resolving)
      'verse'     — low, stable (0.2-0.4)
      'chorus'    — medium-high (0.5-0.7)
      'climax'    — peak then resolve (0.3 → 0.9 → 0.1)
      'breakdown' — strip to nothing (0.5 → 0.0)
    """
    ...
```

### 5.3 Scale Modulation & Key Changes (P2)

**Current state:** Songs stay in one key throughout.

```python
def modulate_key(current_root: int, current_scale: str,
                 target_root: int, target_scale: str,
                 method: str = 'pivot') -> list[tuple[int, str]]:
    """
    Generate a smooth key change using a pivot chord.
    
    Methods:
      'pivot'    — find a chord common to both keys, use as bridge
      'chromatic' — chromatic ascent/descent to new key
      'parallel' — switch modes (C major → C minor)
      'relative' — relative major/minor (C major → A minor)
      'tritone'  — tritone substitution (C → F#, dramatic)
    """
    ...
```

### 5.4 Modes & Extended Scales (P2)

Add scales beyond the 12 currently defined:

| Scale | Intervals | Character |
|-------|-----------|-----------|
| Melodic minor | 0,2,3,5,7,9,11 | Jazz standard |
| Hungarian minor | 0,2,3,6,7,8,11 | Dark, exotic |
| Japanese (In) | 0,1,5,7,8 | Traditional Japanese |
| Arabic (Hijaz) | 0,1,4,5,7,8,11 | Middle Eastern |
| Prometheus | 0,2,4,6,9,10 | Scriabin, impressionist |
| Enigmatic | 0,1,4,6,8,10,11 | Verdi, deliberately unsettled |
| Acoustic | 0,2,4,6,7,9,10 | Overtone series, Bartók |
| Bhairav | 0,1,4,5,7,8,11 | Hindustani morning raga |

### 5.5 Chord Extensions & Voicings (P2)

Beyond basic triads and 7ths:

| Type | Intervals | Sound |
|------|-----------|-------|
| 9th | 0,4,7,10,14 | Rich, soulful |
| 11th | 0,4,7,10,14,17 | Suspended, spacious |
| 13th | 0,4,7,10,14,17,21 | Full, orchestral |
| add9 | 0,4,7,14 | Open, clean |
| 6/9 | 0,4,7,9,14 | Jazz fusion |
| min(maj7) | 0,3,7,11 | Film noir, mysterious |
| 7#9 | 0,4,7,10,15 | "Hendrix chord", aggressive |
| slash chords | C/G, Am/E | Inversions with bass note |

---

## §6 — Export: Formats & Integration

### 6.1 Compressed Audio Export (P1)

**Current state:** Only 16-bit PCM WAV. A 3-minute song = ~30 MB.

```python
# OGG Vorbis via oggenc (system tool)
def export_ogg(audio: np.ndarray, filepath: Path, quality: float = 0.5) -> Path:
    """Export as OGG Vorbis. Requires oggenc installed."""
    wav_path = export_wav(audio, filepath.with_suffix('.wav'))
    subprocess.run(['oggenc', '-q', str(quality), str(wav_path), '-o', str(filepath)])
    wav_path.unlink()  # remove temp WAV
    return filepath

# MP3 via lame (system tool)
def export_mp3(audio: np.ndarray, filepath: Path, bitrate: int = 192) -> Path:
    """Export as MP3. Requires lame installed."""
    ...

# FLAC (lossless compression)
def export_flac(audio: np.ndarray, filepath: Path) -> Path:
    """Export as FLAC (lossless). Requires flac installed."""
    ...
```

**Size comparison (3-minute stereo song):**

| Format | Size | Quality Loss |
|--------|------|-------------|
| WAV 16-bit | ~30 MB | None |
| FLAC | ~15 MB | None (lossless) |
| OGG q5 | ~1.5 MB | Imperceptible |
| MP3 192k | ~2.7 MB | Minimal |
| OGG q2 | ~0.8 MB | Slight, acceptable for games |

### 6.2 Multi-Bit-Depth WAV (P2)

```python
def export_wav(audio, filepath, bit_depth: int = 16):
    """
    bit_depth options:
      8  — retro/chiptune character (lo-fi)
      16 — CD quality (current default)
      24 — studio quality (for mastering)
      32 — float (for further processing in a DAW)
    """
    ...
```

### 6.3 MIDI Export (P2)

Export songs as MIDI files for use in other DAWs or hardware synths:

```python
def export_midi(song: Song, filepath: Path) -> Path:
    """Export pattern grid as Standard MIDI File (Type 1)."""
    # Requires midiutil or custom SMF writer
    ...
```

### 6.4 Stem Export (P2)

Export each channel as a separate WAV file for mixing in other tools:

```python
def export_stems(song: Song, output_dir: Path) -> list[Path]:
    """Export individual channel stems (one WAV per channel)."""
    ...
```

### 6.5 Web Audio Integration (P3)

For Pixel Vault and browser-based games:

**Option A: Pre-rendered (simple, reliable)**
- Render to OGG/MP3 at ~1-2 MB per track
- Load with `<audio>` element or `AudioContext.decodeAudioData()`
- Ship as static assets

**Option B: ChipForge.js (advanced, tiny)**
- Port synthesis engine to JavaScript/WebAssembly
- Song data as JSON (~2-5 KB per song)
- Real-time synthesis in browser via Web Audio API
- `AudioWorklet` for custom DSP (filter, reverb)
- `OfflineAudioContext` for pre-rendering

**Option C: Hybrid**
- Pre-render most of the song
- Add real-time parameter variation (filter sweeps, tempo changes)
- React to game events (intensity up during boss fights)

---

## §7 — Architecture: Scaling the Engine

### 7.1 Dependency Strategy

**Current:** numpy only (plus stdlib `wave`).

**Proposed tiered dependencies:**

| Tier | Package | What It Adds | When |
|------|---------|-------------|------|
| **Core** | numpy | Everything today | Always |
| **Performance** | scipy | FFT convolution, biquad filters (100x speedup) | P0 |
| **Performance** | numba | JIT compilation for remaining Python loops | P0 |
| **Export** | — | Shell out to `oggenc`, `lame`, `flac` (system tools) | P1 |
| **MIDI** | midiutil | MIDI file export | P2 |
| **Future** | — | No new Python deps planned beyond scipy/numba | — |

**Design principle:** scipy and numba are the _only_ new Python dependencies needed. Everything else uses system tools or custom code. No audio frameworks (no pydub, librosa, sounddevice, pygame).

### 7.2 Module Evolution

```
src/
├── synth.py           # Waveform generation, ADSR, filters (existing)
├── oscillators.py     # NEW: Multi-oscillator, FM, wavetable morphing, physical modeling
├── effects.py         # NEW: Compressor, EQ, distortion, flanger, phaser, stereo
├── mixer.py           # Channel rendering, master bus (existing, refactored)
├── instruments.py     # Preset library (existing, extended)
├── sequencer.py       # Pattern/Song models (existing, extended with automation)
├── theory.py          # Music theory (existing, extended)
├── master.py          # NEW: Master bus processing chain
├── export.py          # WAV + OGG + MP3 + FLAC + MIDI + stems (existing, extended)
├── performance.py     # NEW: FFT convolution, parallel rendering, draft mode
└── presets/           # NEW: directory of preset banks (instead of one dict)
    ├── classic.py     # GB-era sounds
    ├── edm.py         # Modern EDM sounds
    ├── cinematic.py   # Film score sounds
    ├── experimental.py # Unusual timbres
    └── drums.py       # All percussion presets
```

### 7.3 Configuration-Driven Effects

Move from hardcoded effect params to configurable chains:

```python
@dataclass
class EffectChain:
    """Ordered list of effects applied to a channel or master bus."""
    effects: list[dict]  # [{"type": "eq", "bands": [...]}, {"type": "comp", ...}]
    
    def apply(self, audio: np.ndarray) -> np.ndarray:
        for fx in self.effects:
            audio = EFFECT_REGISTRY[fx['type']](audio, **fx)
        return audio
```

### 7.4 Plugin Architecture (P3)

Eventually, effects and oscillators should be discoverable and pluggable:

```python
# Register new effect types
EFFECT_REGISTRY = {
    'reverb': apply_reverb,
    'delay': apply_delay,
    'chorus': apply_chorus,
    'compressor': apply_compressor,
    'eq': apply_parametric_eq,
    'distortion': apply_distortion,
    'flanger': apply_flanger,
    'phaser': apply_phaser,
    'widener': apply_stereo_widener,
    'sidechain': apply_sidechain,
    'stutter': apply_stutter,
    'gate': apply_noise_gate,
}

# New effects auto-register
def register_effect(name: str, fn: Callable):
    EFFECT_REGISTRY[name] = fn
```

### 7.5 Testing Strategy

| Level | What | Tool | When |
|-------|------|------|------|
| Unit | Each DSP function (FFT, filter, envelope) | pytest | Every PR |
| Audio regression | Compare output to reference WAV (byte-level) | Custom fixture | Release |
| Performance benchmark | Track render time per operation | pytest-benchmark | Weekly |
| Integration | Full song render, verify non-silence / non-clipping | pytest | Every PR |

```python
# Example audio regression test
def test_saw_filter_matches_reference():
    """Ensure saw_filtered preset produces consistent output."""
    audio = synthesize_note(60, 1.0, waveform='sawtooth', 
                            filter_cutoff=3000.0, filter_resonance=0.3)
    reference = np.load('tests/fixtures/saw_filtered_c4.npy')
    np.testing.assert_allclose(audio, reference, atol=1e-5)
```

### 7.6 DevOps & CI/CD

```yaml
# .github/workflows/ci.yml
name: ChipForge CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short
      
  benchmark:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - run: pytest tests/benchmarks/ --benchmark-json=benchmark.json
      - uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'pytest'
          output-file-path: benchmark.json
```

---

## §8 — Implementation Phases

### Phase 1: Foundation (P0) — "Make It Fast, Make It Loud"

Focus: Performance + essential effects. Every song sounds better immediately.

| # | Task | Module | Est. Effort |
|---|------|--------|-------------|
| 1.1 | Add scipy dependency, FFT convolution reverb | `mixer.py` | 4h |
| 1.2 | Replace Python SVF filter with scipy `sosfilt` | `synth.py` | 2h |
| 1.3 | Compressor/limiter with sidechain | `effects.py` (new) | 6h |
| 1.4 | Parametric EQ (biquad cascade) | `effects.py` | 4h |
| 1.5 | Distortion (5 modes) | `effects.py` | 3h |
| 1.6 | Master bus processing chain | `master.py` (new) | 4h |
| 1.7 | Multi-oscillator instruments | `instruments.py` | 6h |
| 1.8 | Parallel channel rendering | `mixer.py` | 4h |

**Expected outcome:** Render times drop from 60-290s to 5-15s. Songs gain compression, EQ, distortion, and multi-oscillator thickness.

### Phase 2: Expression (P1) — "Make It Move"

Focus: Modulation, time-varying parameters, spatial effects. Music comes alive.

| # | Task | Module | Est. Effort |
|---|------|--------|-------------|
| 2.1 | Automation lanes (per-step parameter control) | `sequencer.py` | 8h |
| 2.2 | FM synthesis (2-operator and 4-operator) | `oscillators.py` (new) | 6h |
| 2.3 | Wavetable morphing | `oscillators.py` | 6h |
| 2.4 | Flanger + phaser effects | `effects.py` | 6h |
| 2.5 | Ping-pong delay + tape delay | `effects.py` | 4h |
| 2.6 | Stereo widener (mid/side) | `effects.py` | 2h |
| 2.7 | Envelope filter (auto-wah) | `effects.py` | 4h |
| 2.8 | Compressed audio export (OGG/MP3/FLAC) | `export.py` | 3h |
| 2.9 | Swing / groove quantization | `sequencer.py` | 3h |
| 2.10 | Voice leading + chord inversions | `theory.py` | 4h |
| 2.11 | Tempo changes + mixed time signatures | `sequencer.py` | 6h |

### Phase 3: Intelligence (P2) — "Make It Think"

Focus: Musical intelligence, compositional depth, expanded timbral palette.

| # | Task | Module | Est. Effort |
|---|------|--------|-------------|
| 3.1 | Tension/resolution mapping | `theory.py` | 4h |
| 3.2 | Key modulation (pivot chords) | `theory.py` | 4h |
| 3.3 | Extended scales (20+ total) | `theory.py` | 2h |
| 3.4 | Chord extensions (9th, 11th, 13th, slash) | `theory.py` | 3h |
| 3.5 | Physical modeling synthesis (Karplus-Strong) | `oscillators.py` | 4h |
| 3.6 | Colored noise types (pink, brown, blue) | `synth.py` | 2h |
| 3.7 | Multi-stage envelopes | `synth.py` | 4h |
| 3.8 | Convolution reverb presets | `effects.py` | 4h |
| 3.9 | Granular stutter/glitch | `effects.py` | 6h |
| 3.10 | Fill/transition generator | `theory.py` | 6h |
| 3.11 | Stem export | `export.py` | 3h |
| 3.12 | MIDI export | `export.py` | 4h |

### Phase 4: Platform (P3) — "Make It Everywhere"

Focus: Web/game integration, plugin architecture, community.

| # | Task | Est. Effort |
|---|------|-------------|
| 4.1 | ChipForge.js core (Web Audio API port) | 40h |
| 4.2 | Plugin architecture (effect/oscillator registry) | 8h |
| 4.3 | Preset bank system (directory-based, loadable) | 4h |
| 4.4 | CI/CD pipeline with audio regression tests | 6h |
| 4.5 | Performance benchmark tracking | 4h |
| 4.6 | Visual waveform/spectrogram PNG export | 6h |
| 4.7 | WebSocket streaming for live agent control | 8h |
| 4.8 | Real-time MIDI input support | 8h |

---

## §9 — The Harmonic Frontier: Sound as Mathematics

This section is for the reader who wants to understand _why_ these techniques work, not just what they are.

### Fourier's Gift

Every sound is a sum of sine waves. A sawtooth wave at 440 Hz is actually: 440 Hz + 880 Hz + 1320 Hz + 1760 Hz + ... (all integer multiples, each at decreasing amplitude). This is the **harmonic series**. A filter removes some of these harmonics. Distortion adds new ones. Reverb smears them across time. EQ reshapes their relative levels.

Every effect in this ADR is, at its mathematical core, a transformation of the harmonic spectrum.

### The Three Dimensions of Sound

1. **Frequency** (pitch) — controlled by oscillators, FM, pitch sweep
2. **Amplitude** (volume) — controlled by ADSR, compressor, limiter, tremolo
3. **Time** (when/how long) — controlled by sequencer, delay, reverb, gates

Professional production manipulates all three simultaneously. A sidechain compressor modifies amplitude in response to another signal's timing. A phaser shifts frequency in a pattern over time. A tape delay degrades both amplitude and frequency content with each echo.

### Psychoacoustics: How Humans Hear

| Phenomenon | What It Means | Engineering Application |
|------------|--------------|----------------------|
| Fletcher-Munson curves | Humans hear midrange (1-4 kHz) louder than bass or treble at the same energy | EQ should boost lows and highs when listening at low volumes |
| Haas effect | A delayed copy (5-35ms) is perceived as spaciousness, not echo | Stereo widening works by introducing tiny L/R timing differences |
| Masking | Loud frequencies hide nearby quiet frequencies | EQ should carve space for each instrument in a different frequency band |
| Missing fundamental | Humans perceive a pitch even if the fundamental is absent (harmonics imply it) | Bass can be "heard" on small speakers by adding harmonics at 2x, 3x, 4x |
| Temporal masking | A loud sound masks what comes just before (pre-masking) and after (post-masking) it | Compressor attack/release must account for perceptual timing |

### The Mathematics of Warmth

"Warmth" in audio is not subjective hand-waving. It has measurable properties:

1. **Even harmonics** (2x, 4x, 6x fundamental) — perceived as musical, pleasant
2. **Odd harmonics** (3x, 5x, 7x) — perceived as hollow, sometimes harsh
3. **Soft saturation** (tanh, tube emulation) adds predominantly even harmonics
4. **Hard clipping** adds predominantly odd harmonics
5. **Tape saturation** adds even harmonics + gentle high-frequency rolloff + subtle pitch modulation (wow/flutter)

This is why `tanh` soft clipping sounds warm and hard clipping sounds harsh — it's the mathematical relationship between the transfer function and the Fourier series it generates.

---

## Consequences

### Positive
- Render times drop by 15-200x (from minutes to seconds)
- Sound quality approaches professional DAW output
- Timbral palette expands from 46 static presets to virtually unlimited
- Composition tools enable more complex, nuanced arrangements
- Master bus processing makes every song sound polished
- Web integration path is clear and achievable
- Architecture supports growth without rewrites

### Negative
- Two new dependencies (scipy, numba) increase install complexity
- More effects = more parameters for song scripts to manage
- Parallel rendering adds process management complexity
- Testing audio is inherently harder than testing logic (regression tests needed)

### Risks
- Scope creep: this ADR describes years of work. Phase 1 alone delivers enormous value
- Over-engineering: not every song needs every effect. Keep defaults sensible
- Performance regression: new features must not slow down songs that don't use them

### Mitigations
- Phase-gated implementation: complete one phase before starting next
- Optional effects: every new feature defaults to "off" unless explicitly enabled
- Benchmark tests: render time tracked per commit, regressions block merge
- scipy/numba are mature, widely used, pip-installable — minimal risk

---

## Status

**Proposed.** Awaiting review from Joshua Ayson.

Implementation begins with Phase 1 (Performance + Essential Effects) as the highest-impact work.

---

**Last Updated:** March 29, 2026  
**Version:** 1.0.0  
**Maintained by:** Joshua Ayson / OA LLC
