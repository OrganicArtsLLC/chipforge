# ADR-002: Sound Quality, Render Speed, and Web Export

**Status:** Proposed  
**Date:** March 29, 2026  
**Author:** Joshua Ayson / OA LLC

---

## Context

After composing 9 songs with ChipForge, three improvement areas have emerged:

1. **Sound quality** — Early songs sounded thin and staccato. We discovered critical rules (duration, effects, velocity caps) but these are manual discipline. The engine itself could enforce better defaults and add richer DSP.

2. **Render speed** — A 65-second song with 7 channels and full effects takes ~290 seconds to render. The Schroeder reverb is the bottleneck (Python-level per-sample iteration). This limits creative iteration.

3. **Web export** — ChipForge currently outputs only 16-bit PCM WAV files (11-14 MB per song). For integration with Pixel Vault HTML5 games, we need size-efficient formats: either compressed audio files or self-contained JavaScript that generates audio at runtime.

---

## Problem 1: Sound Quality Gaps

### Current State

The synthesis engine is solid (PolyBLEP anti-aliasing, LFSR noise, filtered synth instruments, Schroeder reverb). But several features are missing that would elevate the sound from "retro chip tune" to "retro chip tune through a proper sound system":

### Proposed Improvements (Priority Order)

#### P0 — Filter Envelope (cutoff sweep per note)

**What:** Instead of static `cutoff_hz` on filtered instruments, sweep the cutoff over the note's lifetime (e.g., 4000 Hz → 800 Hz). This is the classic acid bass / TB-303 sound.

**Implementation:**
- Add `filter_attack`, `filter_decay`, `filter_sustain_cutoff` parameters to `Instrument`
- During note rendering in `synth.py`, calculate cutoff at each sample based on filter ADSR
- Apply existing `apply_lowpass()` with time-varying cutoff

**Impact:** Huge. Every filtered instrument would sound alive instead of static. Minimal code (the filter already exists).

#### P1 — LFO Modulation (vibrato, tremolo, filter wobble)

**What:** Low-frequency oscillator applied to pitch (vibrato), volume (tremolo), or filter cutoff (wobble/wah).

**Implementation:**
- `generate_with_vibrato()` already exists in `synth.py` but isn't used by any preset
- Add `lfo_target` (pitch/volume/filter), `lfo_rate` (Hz), `lfo_depth` to `Instrument`
- Apply during synthesis

**Impact:** High. Makes sustained notes shimmer and breathe instead of being flat tones.

#### P2 — Chorus Effect

**What:** Duplicate signal with slight pitch detune (±3-7 cents) and short delay (15-30ms). Creates width and thickness.

**Implementation:**
- New `apply_chorus()` function in mixer: duplicate buffer, pitch-shift by ±detune, delay by offset, blend
- Per-channel parameter: `{"chorus": 0.3, "chorus_detune": 5}`

**Impact:** Medium. Makes leads and pads sound significantly wider and more professional.

#### P3 — Sidechain Compression (kick ducking)

**What:** When the kick hits, briefly reduce volume of bass/pad channels. Classic EDM pumping effect.

**Implementation:**
- After rendering all channels, detect kick envelopes on channel 0
- Apply gain reduction curves to specified channels
- Parameters: `sidechain_source` (channel), `sidechain_amount`, `sidechain_release`

**Impact:** Medium. The pumping effect is the signature of EDM production.

#### P4 — Multi-layer Instruments (stacked waveforms)

**What:** A single instrument plays two waveforms simultaneously (e.g., sine sub + saw harmonics, or two detuned squares for thickness).

**Implementation:**
- Add optional `layer2_waveform`, `layer2_detune`, `layer2_volume` to `Instrument`
- Render both layers during note synthesis, sum with respective gains

**Impact:** Medium. Creates much richer timbres without doubling channel count.

#### P5 — Pitch Glide / Portamento

**What:** Smooth frequency transition between consecutive notes on the same channel. Creates the classic synth slide.

**Implementation:**
- Track previous MIDI note per channel
- When new note follows previous, sweep frequency logarithmically over `portamento_time` ms
- `generate_pitch_sweep()` already exists — extend to inter-note glides

**Impact:** Low-medium. Beautiful for bass lines and leads but narrow use case.

---

## Problem 2: Render Speed

### Current State

The render pipeline is: for each pattern, for each channel, for each step with a note, synthesize waveform + ADSR + filter → apply per-channel effects (reverb, delay) → sum channels → apply master effects → normalize → export.

**Measured performance** (MacBook Pro M-series):

| Component | Time per channel | Notes |
|-----------|-----------------|-------|
| Waveform + ADSR | ~2-5s | numpy vectorized, fast |
| Low-pass filter | ~3-8s | Per-sample state variable, slow |
| Schroeder reverb | ~30-40s | Per-sample Python loop, VERY slow |
| Delay | ~1-2s | Array shift + sum, fast |
| Normalization | <1s | Vectorized, trivial |

**The reverb is 80%+ of total render time.** A 7-channel song with reverb on all channels: 7 × 35s = 245s of reverb alone.

### Proposed Improvements (Priority Order)

#### P0 — Vectorized Reverb (numpy batch processing)

**What:** Replace the per-sample Python `for` loop in comb/allpass filters with numpy array operations.

**Implementation strategy:**
- Comb filter: precompute the full delay line as a numpy roll, apply feedback gain as array multiply, accumulate
- Allpass filter: similar vectorization using shifted arrays
- Process in chunks of 4096 samples instead of sample-by-sample

**Target:** 10-20x speedup on reverb. A 290s render should drop to ~40-60s.

**Risk:** Comb filters with feedback are inherently recursive (output[n] depends on output[n-delay]). Pure vectorization isn't possible. But chunk-based processing with feedback carry reduces Python loop iterations by 4096x.

#### P1 — Parallel Channel Rendering (multiprocessing)

**What:** Render each channel independently in a separate process, then sum the results.

**Implementation:**
- Channels are independent until the final mix stage
- Use `multiprocessing.Pool` with `map()` to render channels in parallel
- Collect numpy arrays, sum for final mix

**Target:** Near-linear scaling with CPU cores. 7 channels on 8-core machine → ~7x wall-clock speedup.

**Risk:** Inter-process numpy array transfer has overhead (shared memory or serialization). Need to benchmark real speedup vs overhead.

#### P2 — Cached Reverb Impulse Response

**What:** Instead of running the Schroeder algorithm on every note, precompute an impulse response (IR) for each reverb configuration and convolve via FFT.

**Implementation:**
- Generate IR by running a single impulse sample through the Schroeder chain
- Cache IR per unique `(room_size, damping, mix)` tuple
- Apply reverb via `scipy.signal.fftconvolve(audio, ir)` — highly optimized

**Target:** ~50x speedup on reverb (FFT convolution is O(n log n) vs O(n × m) for direct processing).

**Dependency:** Requires scipy (new dependency) or custom FFT convolution with numpy.

#### P3 — Optional Draft Sample Rate (22050 Hz)

**What:** Allow rendering at half sample rate for quick previews. Sounds slightly muffled but perfectly fine for composition iteration.

**Implementation:**
- Parameterize `SAMPLE_RATE` in render pipeline (not global constant)
- Half sample rate = half the samples = ~2x speedup across all stages
- Final production render at 44100 Hz

**Target:** 2x speedup on everything, stackable with other improvements.

#### P4 — Cython / C Extension for Hot Loops

**What:** Compile the comb filter and allpass filter inner loops to C via Cython.

**Implementation:**
- Extract `_apply_comb_filter()` and `_apply_allpass_filter()` to a `.pyx` file
- Compile with Cython — Python calling convention, C speed inner loop
- Fallback to pure Python if Cython not available

**Target:** 50-100x speedup on reverb inner loops. Combined with parallel rendering, total render time under 10s for most songs.

**Risk:** Adds build complexity (Cython compilation step, platform-specific binaries). Could use `cffi` or `ctypes` as alternatives.

#### Combined Speed Target

| Optimization | Speedup Factor | Cumulative |
|-------------|---------------|------------|
| Baseline (current) | 1x | 290s |
| Vectorized reverb (P0) | ~10x on reverb | ~60s |
| Parallel channels (P1) | ~4x wall-clock | ~15s |
| Cached IR (P2) | Replaces P0 if used | ~10s |
| Draft sample rate (P3) | ~2x additional | ~5s |
| Cython hot loops (P4) | Replaces P0 if used | ~3-5s |

**Realistic near-term target:** P0 + P1 → renders under 30 seconds. That's fast enough for real iteration.

---

## Problem 3: Web Export (Pixel Vault Integration)

### Current State

ChipForge outputs 16-bit PCM stereo WAV at 44100 Hz. A 60-second song is ~10 MB. This is far too large for embedding in Pixel Vault games (hard limit: 50 KB per game file, zero external dependencies).

### Three Export Strategies

#### Strategy A — Compressed Audio File (OGG/MP3)

**What:** Export to OGG Vorbis or MP3 instead of WAV. Include as base64-encoded data URI in HTML.

**Size math:**
- 60s WAV: ~10 MB
- 60s OGG @ 64 kbps: ~480 KB
- 60s OGG @ 32 kbps: ~240 KB
- 60s MP3 @ 48 kbps: ~360 KB
- Base64 overhead: +33%
- **Result: 320-640 KB** (still too large for Pixel Vault 50 KB limit, but fine for standalone HTML players)

**Implementation:**
- Add `export_ogg()` using `pydub` or direct `ffmpeg` subprocess
- Or pure-Python OGG encoder (complex, probably not worth it)
- Web playback: `new Audio('data:audio/ogg;base64,...')`

**Best for:** Standalone HTML music players, web demos, portfolio pieces. NOT for Pixel Vault games due to size.

**Dependency:** ffmpeg (system) or pydub (Python).

#### Strategy B — Inline JavaScript Audio Generation (Pixel Vault native)

**What:** Instead of exporting audio, export a JavaScript file that generates the same audio using the Web Audio API at runtime. The JS code mirrors ChipForge's synthesis but runs in the browser.

**Size math:**
- JS synthesis engine: ~5-8 KB (minified)
- Song data (note grids, instruments, effects): ~3-15 KB depending on complexity
- **Total: 8-23 KB** — fits within Pixel Vault's 50 KB budget

**Implementation (the big one):**

1. **ChipForge.js** — Minimal JS synthesis engine:
   - Oscillator node (square, sawtooth, triangle, sine) via Web Audio API
   - LFSR noise via AudioWorklet or ScriptProcessorNode
   - ADSR envelope via GainNode + linearRampToValueAtTime
   - Low-pass filter via BiquadFilterNode
   - Reverb via ConvolverNode with programmatic IR
   - Delay via DelayNode + GainNode feedback loop

2. **Song Compiler** — Python script that converts a ChipForge Song to a compact JSON or binary format:
   - Compress note grids (run-length encoding for sparse patterns)
   - Map instrument presets to Web Audio parameters
   - Encode effects chain as parameter objects
   - Output: `song.js` file that creates an AudioContext and plays the song

3. **Integration pattern for Pixel Vault:**
   ```html
   <script>
   // ChipForge.js engine (minified, ~6KB)
   const CF={...};
   // Song data (compressed, ~5KB)
   const SONG={bpm:140,patterns:[...],sequence:[0,1,2]};
   // Play
   CF.play(SONG);
   </script>
   ```

**Best for:** Pixel Vault games. Tiny size, zero latency (generates audio on-the-fly), no file downloads.

**Risk:** Web Audio API differences between browsers. Not all ChipForge effects translate 1:1 (Schroeder reverb → ConvolverNode is close but not identical). Sound won't be byte-for-byte identical to WAV output, but should be audibly equivalent.

#### Strategy C — Adjustable Bit Depth + Sample Rate Export

**What:** Export WAV at reduced quality for smaller files. 8-bit mono at 22050 Hz is the authentic Game Boy sound.

**Size math:**
- 60s 16-bit stereo 44100 Hz: ~10.1 MB
- 60s 16-bit mono 44100 Hz: ~5.0 MB
- 60s 8-bit stereo 22050 Hz: ~2.6 MB
- 60s 8-bit mono 22050 Hz: ~1.3 MB
- 60s 8-bit mono 11025 Hz: ~0.65 MB

**Implementation:**
- Add `bit_depth` (8, 16, 24) and `mono` (bool) parameters to `export_wav()`
- Add optional `target_sample_rate` for downsampling via decimation
- 8-bit uses unsigned PCM (0-255 center at 128)

**Best for:** Retro-authentic exports, size-constrained WAV delivery. Not small enough for Pixel Vault inline but good for web download.

### Recommended Approach

**Phase 1:** Strategy C (adjustable bit depth) — trivial to implement, immediately useful.
**Phase 2:** Strategy B (JS audio generation) — highest value for Pixel Vault integration.
**Phase 3:** Strategy A (OGG/MP3) — for web players and portfolio.

---

## Implementation Phases

### Phase 1: Quick Wins (Next Session)

| Item | Effort | Impact |
|------|--------|--------|
| Filter envelope (P0 Quality) | 2-3 hours | Huge: brings instruments alive |
| Adjustable bit depth export (Strategy C) | 1 hour | Medium: smaller WAV files |
| Vectorized reverb chunks (P0 Speed) | 3-4 hours | Huge: 10x reverb speedup |

### Phase 2: Serious Upgrades

| Item | Effort | Impact |
|------|--------|--------|
| LFO modulation (P1 Quality) | 2 hours | High: vibrato/tremolo |
| Parallel channel rendering (P1 Speed) | 2-3 hours | High: 4x wall-clock |
| Chorus effect (P2 Quality) | 2 hours | Medium: width/thickness |
| ChipForge.js engine (Strategy B) | 8-12 hours | Huge: Pixel Vault integration |

### Phase 3: Polish

| Item | Effort | Impact |
|------|--------|--------|
| Sidechain compression (P3 Quality) | 3 hours | Medium: EDM pumping |
| Multi-layer instruments (P4 Quality) | 2 hours | Medium: richer timbre |
| OGG/MP3 export (Strategy A) | 2 hours | Medium: web delivery |
| Song visualization (waveform PNG) | 3 hours | Low: visual debugging |
| Cached reverb IR (P2 Speed) | 3 hours | High if P0 isn't enough |

### Phase 4: Advanced

| Item | Effort | Impact |
|------|--------|--------|
| Cython hot loops (P4 Speed) | 4-6 hours | Very high: near-real-time rendering |
| MIDI export | 3 hours | Medium: interop with DAWs |
| WebSocket live agent control | 5-8 hours | High: real-time composition |
| SQLite song persistence | 2-3 hours | Medium: replace in-memory state |

---

## Decision

**Accepted approach:** Implement improvements in priority order across sessions. Phase 1 items (filter envelope, adjustable bit depth, vectorized reverb) are the next concrete tasks.

**Key principle:** Always measure before and after. Render the same song before/after each change to verify improvement and catch regressions.

**Web export target:** Strategy B (inline JS generation) is the North Star for Pixel Vault integration. Phase 1 and 2 quality/speed improvements make the WAV output better, and Strategy B makes it deployable in the browser at minimal size.

---

## Consequences

### Positive
- Faster iteration means more songs, better songs
- Web export unlocks Pixel Vault soundtrack integration
- Sound quality improvements compound (each song benefits from every new feature)
- Reduced render time removes the biggest friction point in the creative workflow

### Negative
- More code to maintain in synthesis engine
- Cython dependency adds build complexity (if pursued)
- ChipForge.js requires maintaining two synthesis engines (Python + JS)
- Web Audio API differences mean sound won't be identical to WAV

### Mitigations
- Keep Cython optional (pure Python fallback always works)
- ChipForge.js targets "close enough" not "identical" — the aesthetic is chip tune, not audiophile
- Automated regression tests: render reference songs, compare output (future)

---

**Last Updated:** March 29, 2026  
**Version:** 1.0.0
