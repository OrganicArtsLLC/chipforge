# ADR-005: AI-Amplified Engine — Strategic Vision for Recursive Enhancement

**Status:** Active
**Date:** March 29, 2026
**Author:** Joshua Ayson / OA LLC + Claude AI
**Purpose:** Map every engine component to its AI amplification potential. Identify the liminal spaces where AI transforms what's possible, not just what's faster.

---

## The Recursive Insight

This document was written by AI analyzing its own synthesis engine to identify where AI can enhance it further. Tomorrow, an AI can read this document, implement the changes, and write the NEXT version of this document identifying what's NOW possible that wasn't before. This is recursive self-improvement applied to creative tooling.

Each enhancement below is tagged:
- **[HUMAN]** — A human could do this with enough time
- **[AI-ASSISTED]** — AI makes this 10-100x faster
- **[AI-ONLY]** — Practically impossible without AI computation

---

## Part 1: Engine Audit Summary

### Current State (v0.4.0)

| Component | File | Lines | State | Key Issue |
|-----------|------|-------|-------|-----------|
| Synthesis | synth.py | 955 | Strong | 3 per-sample Python fallbacks when no scipy |
| Instruments | instruments.py | 1,020 | Excellent | 98 presets, comprehensive |
| Mixer | mixer.py | 506 | Good | IR caching works; chorus is basic |
| Effects | effects.py | 419 | Excellent | 100% vectorized, production-grade |
| Sequencer | sequencer.py | 282 | Solid | Clean data model |
| Export | export.py | 142 | Minimal | WAV only, no compressed formats |
| Theory | theory.py | 728 | Good | 12 scales, 11 chords, 7 grooves |
| Total | | 4,052 | | |

### Critical Findings

1. **SAMPLE_RATE defined in 3 places** (synth.py, effects.py, mixer.py) — must centralize
2. **effects.py not exported** from `__init__.py` — production DSP hidden from API
3. **3 per-sample Python loop fallbacks** — 100-1000x slower when scipy missing
4. **Filter envelopes split** between instrument definition and mixer application
5. **theory.py possible bug** — `rng.choice()` vs `rng.choices()` inconsistency

---

## Part 2: Component-by-Component AI Amplification Map

### 2.1 Synthesis (synth.py) — The Waveform DNA

**Current:** 8 waveform types (sine, square, saw, triangle, wavetable, noise, additive, supersaw)

**AI Amplifications:**

#### 2.1.1 Spectral Morphing Between Waveforms **[AI-ONLY]**
*Status: Not implemented. Impact: Very High. Complexity: Medium.*

Instead of switching between instruments discretely, morph the FREQUENCY SPECTRUM continuously between any two waveforms. AI computes FFT of both, interpolates magnitudes and phases of 50-100+ partials independently.

**Why AI-only:** Computing optimal morph curves for each partial requires evaluating spectral coherence across the full harmonic series. A human could tune one morph by hand in hours; AI can compute thousands per second.

```python
def spectral_morph(wave_a: np.ndarray, wave_b: np.ndarray,
                   morph: float, window_size: int = 2048) -> np.ndarray:
    """Morph between two waveforms in frequency domain."""
    # Chunk-based STFT for smooth morphing
    # AI computes optimal window overlap and morph curve per partial
```

**Implementation:** ~100 lines. Add as post-synthesis effect in mixer. Web-safe via AnalyserNode + custom processing.

#### 2.1.2 Per-Harmonic Envelope Shaping **[AI-ONLY]**
*Status: Additive synthesis exists but envelopes are static. Impact: High.*

Each harmonic partial gets its OWN ADSR envelope. A bell sound has: fundamental sustains, 3rd harmonic decays fast, 5th harmonic attacks late. This creates timbres that EVOLVE over every note's lifetime — impossible with subtractive synthesis.

**Why AI-only:** 12 harmonics × 4 envelope parameters = 48 parameters PER INSTRUMENT. Tuning these by ear is infeasible. AI can optimize them against target timbral profiles.

```python
HARMONIC_ENVELOPES = {
    "bell": [
        ADSR(0.001, 0.5, 0.0, 0.3),   # fundamental: sustains
        ADSR(0.001, 0.1, 0.0, 0.1),   # 2nd: quick decay
        ADSR(0.001, 0.3, 0.1, 0.2),   # 3rd: medium
        # ... 12 independent envelopes
    ]
}
```

#### 2.1.3 Formant Synthesis (Vocal Simulation) **[AI-ASSISTED]**
*Status: Not implemented. Impact: High for vocal-like leads.*

Model vowel sounds (ah, ee, oh, oo) as resonant filter peaks at specific frequencies. AI computes formant trajectories that sweep between vowels over a note's duration.

**Formant frequencies (Hz):** A (700, 1200, 2500), E (500, 1800, 2500), I (300, 2300, 3000), O (500, 1000, 2500), U (300, 900, 2200)

```python
def apply_formant(samples: np.ndarray, vowel_start: str, vowel_end: str) -> np.ndarray:
    """Sweep formant filters from one vowel to another."""
```

**Web-safe:** Yes — BiquadFilterNodes in series.

#### 2.1.4 Physically-Modeled Drums **[AI-ASSISTED]**
*Status: Current drums are pitched sweep + noise. Impact: Medium.*

Model drum membranes as coupled circular modes (Bessel functions). AI solves the wave equation for a circular membrane to generate drum sounds that respond to "strike position" and "tension" parameters.

More realistic than pitch sweep, but stays within the chip aesthetic.

---

### 2.2 Instruments (instruments.py) — The Palette

**Current:** 98 presets. Comprehensive but static.

**AI Amplifications:**

#### 2.2.1 AI-Designed Instrument Presets **[AI-ONLY]**
*Status: All 98 presets hand-designed. Impact: Very High.*

Given a text description ("warm 80s brass stab with slow attack and slight detune"), AI generates optimal instrument parameters: waveform, ADSR, filter cutoff, resonance, vibrato rate/depth, filter envelope, distortion drive.

This is the most immediate AI win: instead of manually tuning 14+ parameters, describe what you want and AI computes the preset.

```python
# Future: AI preset generator
def design_instrument(description: str) -> Instrument:
    """AI generates instrument parameters from natural language description."""
```

#### 2.2.2 Instrument Layering System **[AI-ASSISTED]**
*Status: Proposed in ADR-002 as P4. Not implemented.*

Stack 2-3 waveforms per instrument with independent envelopes and detuning. Creates much richer timbres without doubling channel count.

```python
@dataclass
class LayeredInstrument:
    layers: list[Instrument]  # 2-3 layers
    detune_cents: list[float]  # per-layer detune
    mix: list[float]  # per-layer volume
```

#### 2.2.3 Context-Aware Instrument Selection **[AI-ONLY]**
*Status: Not implemented. Impact: Medium.*

AI analyzes the current chord, key, register, and surrounding instruments to recommend the optimal preset for each musical moment. Different from static preset selection — this considers the full mix context.

---

### 2.3 Mixer (mixer.py) — The Sound Stage

**Current:** Pattern/song rendering, per-channel effects, stereo panning, master reverb/delay.

**AI Amplifications:**

#### 2.3.1 AI-Optimized Mix Levels **[AI-ONLY]**
*Status: Not implemented. Impact: Very High.*

Compute per-channel volume levels that maximize perceptual clarity using psychoacoustic masking models. AI analyzes the spectral content of all channels simultaneously and adjusts gains so no two instruments mask each other.

**Why AI-only:** Solving the psychoacoustic model (basilar membrane excitation, critical bandwidth, temporal masking) across 9 channels × 44100 samples/second requires computation that would take a human mastering engineer hours of careful listening.

```python
def auto_mix(channels: list[np.ndarray]) -> list[float]:
    """Compute optimal mix levels using psychoacoustic model."""
    # Compute spectral centroid and bandwidth per channel
    # Identify masking conflicts
    # Adjust gains to minimize masking while preserving balance
```

#### 2.3.2 Intelligent Reverb Allocation **[AI-ASSISTED]**
*Status: Currently manual per-channel reverb settings.*

AI determines optimal reverb parameters per channel based on the instrument's frequency range, the song's tempo, and the desired spatial image. Low frequencies get less reverb (tighter), high frequencies get more (wider).

#### 2.3.3 Cross-Channel Ducking **[AI-ONLY]**
*Status: Sidechain exists in effects.py but only kick→bass. Impact: High.*

AI computes spectral conflicts between ALL channel pairs and applies frequency-selective ducking. When the lead melody plays a note at 2kHz, the arp channel is ducked specifically at 1.5-2.5kHz — not globally, just in the conflicting band.

```python
def spectral_ducking(channels: list[np.ndarray],
                     priority: list[int]) -> list[np.ndarray]:
    """Frequency-selective cross-channel ducking."""
```

---

### 2.4 Effects (effects.py) — The Polish

**Current:** Compressor, sidechain, distortion (5 modes), parametric EQ, stereo widener, master bus. 100% vectorized.

**AI Amplifications:**

#### 2.4.1 AI-Mastered Output **[AI-ONLY]**
*Status: Manual MasterBusConfig per song. Impact: Very High.*

AI analyzes the rendered mix and computes optimal mastering parameters: EQ curve, compression threshold/ratio, stereo width, saturation amount, limiter ceiling. Different for each song based on its genre, dynamics, and spectral content.

**Why AI-only:** Professional mastering engineers charge $50-200/song and take 30-60 minutes. AI can analyze spectral balance, dynamic range, stereo correlation, and loudness curves in milliseconds.

```python
def auto_master(audio: np.ndarray, genre: str = "edm") -> np.ndarray:
    """AI-computed mastering chain optimized for the specific mix."""
    # Analyze: spectral balance, dynamic range, stereo width
    # Compute: optimal EQ, compression, limiting, width
    # Apply: full mastering chain with computed parameters
```

#### 2.4.2 Convolution Reverb with Computed IRs **[AI-ASSISTED]**
*Status: Schroeder reverb with IR caching. Impact: Medium.*

Instead of the Schroeder algorithm, compute impulse responses that model specific acoustic spaces (concert hall, cathedral, studio, outdoor). AI can design IR profiles for arbitrary spaces described in natural language.

#### 2.4.3 Multiband Compression **[HUMAN]**
*Status: Not implemented. Impact: Medium.*

Split audio into frequency bands (sub, low, mid, high, air), compress each independently. Standard mastering technique, well-understood.

```python
def multiband_compress(audio: np.ndarray,
                       crossovers: list[float] = [80, 250, 2000, 8000],
                       settings: list[dict] = ...) -> np.ndarray:
```

---

### 2.5 Theory (theory.py) — The Musical Brain

**Current:** 12 scales, 11 chords, 8 progressions, 7 grooves, phrase-aware melody generation.

**AI Amplifications:**

#### 2.5.1 Style-Conditioned Melody Generation **[AI-ONLY]**
*Status: Current melody generation is weighted random walk. Impact: Very High.*

Train Markov chains on analyzed melodies from different genres/composers. Generate melodies that are statistically similar to Bach, Beethoven, Deadmau5, or Daft Punk without copying any specific piece.

**Why AI-only:** Building transition probability matrices across pitch, duration, velocity, and position dimensions from hundreds of analyzed pieces requires systematic computation no human can perform.

```python
class StyleMarkov:
    """Markov chain melody generator conditioned on musical style."""
    def __init__(self, style: str):
        self.transitions = STYLE_MATRICES[style]  # pre-computed

    def generate(self, length: int, key: str, chord: str) -> list[int]:
        """Generate melody notes conditioned on harmony."""
```

#### 2.5.2 Counterpoint Engine **[AI-ONLY]**
*Status: Counter-melodies are hand-written per song. Impact: Very High.*

Given a melody, algorithmically generate a harmonically correct counter-melody following species counterpoint rules: consonance on strong beats, stepwise motion, contrary motion, no parallel fifths.

**Why AI-only:** Evaluating all possible counter-melody candidates against 6+ simultaneous rules at each beat position creates a combinatorial search space. AI can prune this efficiently; humans do it intuitively but slowly.

```python
def generate_counterpoint(melody: list[int], key: str,
                          species: int = 1) -> list[int]:
    """Generate counterpoint voice following classical rules."""
```

#### 2.5.3 Harmonic Analysis and Reharmonization **[AI-ONLY]**
*Status: Not implemented. Impact: High.*

Given a melody, AI determines the optimal chord progression by analyzing scale degree function, voice leading options, and genre conventions. Can reharmonize existing melodies in different styles (jazz reharmonization of a pop melody, etc.).

#### 2.5.4 Entropy-Controlled Composition **[AI-ONLY]**
*Status: Not implemented. Impact: High.*

Use Shannon entropy to control musical "surprise." Compute information content of each musical moment. Target specific entropy curves: verse = moderate surprise (2.5 bits/note), chorus = low surprise (1.5 bits = catchy/predictable), bridge = high surprise (4.0 bits = keeps interest).

```python
def entropy_at(melody: list[int], position: int,
               markov: StyleMarkov) -> float:
    """Compute information content (surprise) at a melody position."""
```

---

### 2.6 Sequencer (sequencer.py) — The Grid

**Current:** Clean tracker-style grid. Well-designed.

**AI Amplifications:**

#### 2.6.1 AI Song Structure Generator **[AI-ONLY]**
*Status: Song structures are manually defined per song.*

Given genre and duration, AI generates an optimal song structure: number of sections, section types (intro/verse/chorus/bridge/drop/outro), section lengths, energy arc, key modulation plan.

```python
def generate_structure(genre: str, duration_sec: float,
                       energy_curve: str = "build-drop-resolve") -> list[Section]:
    """AI-generated song structure optimized for genre and duration."""
```

#### 2.6.2 Automatic Arrangement **[AI-ONLY]**
*Status: Manual channel assignment per section.*

AI decides which instruments play in each section, how many channels are active, when elements enter/exit. Creates the professional arrangement decisions (bass enters bar 8, drums drop in breakdown, counter-melody only in final chorus).

---

### 2.7 Export (export.py) — The Output

**Current:** WAV only (16-bit PCM stereo).

**AI Amplifications:**

#### 2.7.1 ChipForge.js Compiler **[AI-ASSISTED]**
*Status: Proposed in ADR-002 Strategy B. Not implemented. Impact: CRITICAL for Pixel Vault.*

Compile a ChipForge Song to a compact JavaScript file that generates the same audio using Web Audio API at runtime. Target: 8-23 KB total (engine + song data).

This is the #1 strategic priority for Pixel Vault integration.

#### 2.7.2 Adaptive Quality Export **[AI-ASSISTED]**
*Status: Not implemented.*

Export at different quality levels: draft (22050 Hz, mono, 8-bit = small), standard (44100 Hz, stereo, 16-bit = current), high (44100 Hz, stereo, 24-bit = future).

---

## Part 3: Quick Wins — Implement Now

### Priority 0 (Do Today)

| # | Enhancement | Type | Impact | Lines | Why |
|---|---|---|---|---|---|
| 1 | Centralize SAMPLE_RATE | [HUMAN] | Code health | ~10 | Defined in 3 places |
| 2 | Export effects.py from __init__.py | [HUMAN] | API completeness | ~15 | Production DSP hidden |
| 3 | Fix theory.py rng.choice() bug | [HUMAN] | Correctness | ~2 | Potential runtime error |
| 4 | Require scipy (warn if missing) | [HUMAN] | Performance guarantee | ~5 | Fallbacks are 100-1000x slower |

### Priority 1 (This Week)

| # | Enhancement | Type | Impact | Lines |
|---|---|---|---|---|
| 5 | Spectral morph function | [AI-ONLY] | New timbral possibilities | ~80 |
| 6 | Per-harmonic envelopes in additive synth | [AI-ONLY] | Living instrument timbres | ~60 |
| 7 | Counterpoint generator | [AI-ONLY] | Auto counter-melodies | ~120 |
| 8 | Auto-mastering from genre analysis | [AI-ONLY] | Consistent quality | ~100 |
| 9 | Multiband compression | [HUMAN] | Better mixes | ~80 |
| 10 | Instrument layering | [AI-ASSISTED] | Richer timbres | ~50 |

### Priority 2 (This Month)

| # | Enhancement | Type | Impact | Lines |
|---|---|---|---|---|
| 11 | Style-conditioned Markov melody | [AI-ONLY] | Original melodies | ~200 |
| 12 | Formant synthesis | [AI-ASSISTED] | Vocal-like instruments | ~100 |
| 13 | Entropy-controlled composition | [AI-ONLY] | Optimal surprise curves | ~150 |
| 14 | Cross-channel spectral ducking | [AI-ONLY] | Perfect mixes | ~100 |
| 15 | ChipForge.js compiler (Pixel Vault) | [AI-ASSISTED] | Web deployment | ~500 |

---

## Part 4: The Liminal Spaces — Where New Possibilities Emerge

These are the edges where the lines blur between "tool" and "artist."

### 4.1 Self-Evaluating Compositions

AI renders a song, analyzes the output (spectral balance, dynamic range, stereo width, harmonic content), identifies weaknesses, and automatically adjusts parameters to fix them. Render → analyze → adjust → re-render. This loop can iterate 3-5 times in the time a human takes to listen once.

### 4.2 Cross-Pollination Between Songs

AI analyzes the favorites folder to extract what makes those songs good (specific frequency balances, velocity distributions, effects settings, structural patterns). Then applies those learned preferences to new compositions automatically.

### 4.3 Musical DNA Transfer

Take the "DNA" of one song (its harmonic rhythm, melodic contour, rhythmic density, timbral evolution) and apply it to a different melody in a different key at a different tempo. The DNA transfers the FEEL without copying the NOTES.

### 4.4 Generative Variation Engine

Instead of hand-writing verse 1 and verse 2 variations, AI generates them by applying controlled mutations: swap two melody notes, shift a phrase by one beat, add a chromatic approach, invert a contour. Each mutation is validated against harmonic rules before acceptance.

### 4.5 Collaborative Evolution

User rates songs 1-10. AI analyzes what rated high vs low. AI generates songs 11-20 biased toward what worked. User rates those. AI refines. By generation 5-10, the AI has learned the user's taste with statistical precision — without any explicit rules, just from the signal of "liked" vs "didn't like."

---

## Part 5: Architecture Principles for AI-Amplified Code

1. **Every function must be deterministic** — given the same inputs, produce the same output. This enables: testing, caching, comparison, and recursive refinement.

2. **Every parameter must be numeric** — no magic strings for AI to guess. Numeric parameters enable: gradient-based optimization, interpolation, and automated tuning.

3. **Every effect must be composable** — any effect can be applied to any audio buffer. This enables: arbitrary effect chains, A/B testing, and automated experimentation.

4. **Every decision must be overridable** — defaults are smart, but everything can be explicitly set. This enables: AI to override any decision while humans can still control everything.

5. **Fast feedback loops** — rendering must be fast enough to iterate. With scipy FFT reverb, we're at 60-90 seconds per 3-minute song. Target: under 30 seconds.

6. **Measure everything** — peak levels, spectral balance, dynamic range, render time. What gets measured gets optimized.

---

## Appendix: Immediate Code Fixes

### Fix 1: Centralize SAMPLE_RATE

```python
# In synth.py (the canonical source):
SAMPLE_RATE: int = 44100

# In effects.py, REPLACE line 18:
from .synth import SAMPLE_RATE

# In mixer.py (already imports from synth — verify no local definition)
```

### Fix 2: Export effects.py

```python
# In __init__.py, ADD:
from .effects import (
    apply_compressor, apply_sidechain, apply_distortion,
    apply_parametric_eq, apply_stereo_widener, apply_master_bus,
    EQBand, MasterBusConfig,
)
```

### Fix 3: Fix theory.py rng bug

Verify `rng.choice()` vs `rng.choices()` at line 532. If using `random.Random` instance, method is `.choice()` (singular, picks one). If list result expected, use `.choices()`.

---

**This document is itself an artifact of AI-amplified development. It was produced by an AI analyzing its own codebase, identifying its own limitations, and proposing its own enhancements. The next iteration will be written by an AI that has already implemented some of these enhancements, operating from a higher baseline.**

**Last Updated:** March 29, 2026
**Version:** 1.0.0
