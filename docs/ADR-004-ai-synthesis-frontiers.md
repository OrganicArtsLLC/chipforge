# ADR-004: AI-Only Synthesis Techniques — Pushing the Frontiers

**Status:** Proposed
**Date:** March 29, 2026
**Author:** Joshua Ayson / OA LLC + Claude AI

---

## Context

ChipForge currently uses conventional synthesis: waveform generators, ADSR envelopes, static filters, Schroeder reverb. These are 1960s-1980s techniques. They sound good, but they're what any DAW does.

The question: **What can AI do that humans literally cannot?**

Not "AI helps write music faster" — that's table stakes. We mean: what synthesis and composition techniques are only practical when a machine can handle the mathematical complexity in real-time, across every sample, every note, every bar?

This ADR catalogs techniques from the known frontier through to the speculative unknown. Implementation priority is based on impact-to-complexity ratio and alignment with the web/Pixel Vault constraint (small bytecode, JS-generatable).

---

## Tier 1: Known But Impractical for Humans (Implement Now)

### 1.1 Spectral Morphing Between Instruments

**What:** Instead of crossfading two sounds (which sounds like two sounds playing), morph their FREQUENCY SPECTRA. Decompose each note into its harmonic partials (FFT), then interpolate between the partial amplitudes of instrument A and instrument B.

**Why AI-only:** Requires computing and blending 50-100+ harmonic partials per sample. A human can't tune this by hand. AI can compute the optimal morph curve for each partial independently.

**Sound:** A note that starts as a saw lead and BECOMES a bell — not a crossfade, but a genuine timbral transformation. Like a singer opening their mouth from "oo" to "ah."

**Implementation:**
```python
def spectral_morph(wave_a, wave_b, morph_curve):
    fft_a = np.fft.rfft(wave_a)
    fft_b = np.fft.rfft(wave_b)
    # Interpolate magnitude and phase independently
    mag = np.abs(fft_a) * (1-morph_curve) + np.abs(fft_b) * morph_curve
    phase = np.angle(fft_a) * (1-morph_curve) + np.angle(fft_b) * morph_curve
    return np.fft.irfft(mag * np.exp(1j * phase))
```

**Web-safe:** Yes — FFT is available in Web Audio API via AnalyserNode + custom processing.

### 1.2 Additive Synthesis with Harmonic DNA

**What:** Instead of subtractive synthesis (start with harmonics-rich waveform, filter out what you don't want), BUILD the exact harmonic series you want from individual sine waves. Each harmonic has its own amplitude envelope, creating timbres impossible with any single waveform.

**Why AI-only:** A 12-harmonic instrument requires 12 independent amplitude curves per note. Across 7 channels × 16 steps × 12 harmonics = 1,344 parameters per bar. AI can compute these; humans cannot.

**Sound:** Instruments that evolve their timbre over every note's lifetime — a bass that starts with 3 harmonics (warm) and gains 8 more (growly) then loses them (warm again). Naturally, organically.

**Implementation:**
```python
def additive_note(freq, harmonics, envelopes, num_samples):
    """Each harmonic has its own envelope curve."""
    result = np.zeros(num_samples)
    for i, (amp, env) in enumerate(zip(harmonics, envelopes)):
        partial = amp * np.sin(2*np.pi * freq * (i+1) * t)
        result += partial * env  # env is per-sample amplitude curve
    return result
```

**Web-safe:** Yes — multiple OscillatorNodes summed. Actually more efficient than subtractive in Web Audio.

### 1.3 Microtonality and Just Intonation

**What:** Standard Western music uses equal temperament — every note is slightly out of tune with the natural harmonic series. Just intonation uses mathematically pure ratios (3/2 for a fifth, 5/4 for a major third). AI can compose in just intonation, retuning every note based on its harmonic context.

**Why AI-only:** In just intonation, the "same" note has different tunings depending on what chord it's in. D in a G chord (3/2 above G) is different from D in a Bb chord (5/4 below F#). AI can track and compute these relationships across all voices simultaneously.

**Sound:** Chords that ring with crystalline purity. The "beats" (interference patterns) that equal temperament creates disappear. Sounds noticeably more beautiful, especially on sustained chords.

**Implementation:** Replace `440 * 2^((midi-69)/12)` with context-aware frequency calculation based on the current chord root and the note's function within that chord.

**Web-safe:** Yes — frequency is just a number. No extra cost.

---

## Tier 2: Cutting Edge (Implement Soon)

### 2.1 Fractal Self-Similar Composition

**What:** Generate musical structures that are self-similar at multiple time scales. The rhythm of a 4-bar phrase mirrors the rhythm of each individual bar, which mirrors each beat's subdivision. Like a coastline — zoom in and the pattern recurs.

**Why AI-only:** Computing L-system or IFS fractal expansions across melody, rhythm, and harmony simultaneously, then verifying musical coherence at each level, requires systematic mathematical generation that humans approximate intuitively but AI can compute exactly.

**Sound:** Music that feels "deep" — the more you listen, the more patterns you discover at different time scales. The chorus rhythm mirrors the verse melody contour. The bass line's note choices mirror the song's key structure.

### 2.2 Stochastic Process Composition (Controlled Randomness)

**What:** Use Markov chains trained on analyzed musical styles to generate melodies that are statistically similar to a genre but never repeat. Each note's probability depends on the previous 2-3 notes, the current chord, the position in the phrase, and the overall energy arc.

**Why AI-only:** Computing transition probability matrices across multiple dimensions (pitch, duration, velocity, position) and sampling from them in real-time while maintaining musical coherence.

**Sound:** Melodies that sound "composed" but are genuinely new every time. Each rendering of the same song could produce slightly different melodies that all fit perfectly.

### 2.3 Psychoacoustic Optimization

**What:** Use mathematical models of human hearing to optimize the mix. Compute masking curves (which frequencies hide which other frequencies), critical bandwidth, and loudness perception to ensure every instrument is maximally audible with minimum energy.

**Why AI-only:** Computing the basilar membrane excitation pattern for a full mix at every moment requires solving the psychoacoustic model for 44,100 samples per second. This is what mastering engineers approximate by ear over hours.

**Sound:** Mixes that sound "loud" and "clear" at low volumes. Every instrument occupies its own perceptual space. No two instruments fight for the same auditory attention.

### 2.4 Evolving Wavetables (Per-Sample Waveshaping)

**What:** Instead of cycling through a fixed 32-sample wavetable, compute a DIFFERENT wavetable for every few samples. The waveform itself evolves continuously — not just the filter or amplitude, but the actual wave shape.

**Why AI-only:** At 44100 Hz with a 32-sample wavetable updating every 128 samples, that's 345 unique wavetables per second, each needing mathematical coherence with the previous one to avoid clicks.

**Sound:** Instruments that have continuously evolving timbre — like a physical instrument where every bow stroke, breath, or pick is slightly different.

---

## Tier 3: Speculative / Unknown Territory (Research)

### 3.1 Topology-Based Harmony

**What:** Use mathematical topology to navigate harmonic spaces. Chords exist as points in a high-dimensional manifold. Chord progressions become paths through this space. "Smooth" progressions follow geodesics (shortest paths on the manifold). "Surprising" progressions jump between distant regions.

**Why novel:** This was proposed by Dmitri Tymoczko (Princeton) in "A Geometry of Music" (2011) but has never been applied to generative synthesis. AI can compute geodesics in chord-space manifolds and generate progressions that are mathematically optimal for smoothness or surprise.

**Sound:** Chord progressions that feel inevitable yet unexpected — the harmonic equivalent of a perfectly designed rollercoaster.

### 3.2 Neural Waveform Synthesis (Learned Timbres)

**What:** Train a tiny neural network (< 5KB weights) to generate waveforms that match a target timbre. The network takes frequency + time as input and outputs sample values. The "instrument" IS the neural network.

**Why frontier:** This combines generative AI with traditional synthesis. The neural network learns timbral features that are impossible to describe with simple waveform equations. Could fit in Pixel Vault's JS budget as a tiny inference engine.

**Feasibility for web:** Marginal — depends on network size. A 2-layer network with 32 hidden units = ~2KB of weights. Could run at audio rate in WebAssembly.

### 3.3 Entropic Composition (Information-Theoretic Music)

**What:** Use information theory (Shannon entropy) to control musical surprise. Compute the entropy of each musical moment — how "surprising" is this note given everything before it? Then shape the entropy curve over the song: low entropy = predictable = comfortable, high entropy = surprising = exciting.

**Why novel:** Composers do this intuitively, but AI can compute exact entropy values and target specific entropy curves. A "verse" might target 2.5 bits/note, while a "drop" targets 1.2 bits/note (very predictable = catchy hook), and a "bridge" targets 4.0 bits/note (surprising = keeps interest).

**Sound:** Music that is optimally interesting — scientifically calibrated to maximize listener engagement without fatigue.

### 3.4 Resonance Network Synthesis

**What:** Model an instrument as a network of coupled resonators (like a piano body, a guitar string, a drum head). Each resonator has a frequency, damping, and coupling strength to its neighbors. Pluck one resonator and the energy propagates through the network, creating rich, evolving timbres.

**Why AI-only:** Solving a system of N coupled differential equations per sample. Even N=8 resonators creates richer timbres than any traditional synthesis method. N=32 approaches physical modeling of real instruments.

**Sound:** Instruments that respond to being "played" — the timbre changes based on how hard you hit it, what notes came before, and the current state of the resonance network. Genuinely organic-sounding digital instruments.

---

## Implementation Priority (Impact / Complexity / Web-Safety)

| Technique | Impact | Complexity | Web-Safe | Priority |
|-----------|--------|------------|----------|----------|
| Just intonation | High | Low | Yes | **P0** |
| Additive synthesis | Very High | Medium | Yes | **P0** |
| Spectral morphing | Very High | Medium | Partial | **P1** |
| Fractal composition | High | Medium | Yes | **P1** |
| Stochastic Markov melody | High | Medium | Yes | **P1** |
| Psychoacoustic optimization | High | High | Yes | **P2** |
| Evolving wavetables | Medium | Medium | Yes | **P2** |
| Topology harmony | Medium | High | Yes | **P3** |
| Entropic composition | Medium | Medium | Yes | **P3** |
| Neural waveform | High | Very High | Marginal | **P4** |
| Resonance networks | Very High | Very High | No (too slow) | **P4** |

---

## Architecture Principles

All additions must be:

1. **Antifragile** — new features don't break existing ones. Every technique is optional and additive.
2. **Fast** — numpy vectorized where possible. No per-sample Python loops for new features (we already have that problem with reverb).
3. **Web-portable** — if it can't eventually be expressed in <10KB of JS, it needs a compelling reason.
4. **Composable** — techniques stack. Additive synthesis + just intonation + spectral morphing = instruments impossible in any DAW.
5. **Measurable** — every technique should produce audibly different results on A/B comparison.

---

## Next Steps

1. Implement just intonation mode (P0) — a flag on Song that recomputes all frequencies based on chord context
2. Implement additive synthesis engine (P0) — new waveform type "additive" with harmonic series + per-harmonic envelopes
3. Build spectral morph function (P1) — numpy FFT-based, operates on rendered note buffers
4. Add fractal rhythm generator (P1) — replaces Euclidean as the mathematical rhythm engine
5. Profile and optimize — the reverb bottleneck must be solved before adding more features

---

**Last Updated:** March 29, 2026
**Version:** 1.0.0
