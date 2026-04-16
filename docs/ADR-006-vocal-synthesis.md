# ADR-006: Vocal Synthesis — Voices from Code, Not Samples

**Status:** Active
**Date:** March 30, 2026
**Author:** Joshua Ayson / OA LLC + Claude AI
**Purpose:** Create human vocal-like sounds purely from synthesis — no samples, no recordings, no WAV files. Shape voices from the dust of code.

---

## The Challenge

Every EDM track that makes a crowd move has one thing in common: **the human element**. Whether it's a chopped vocal, a "yeah!", a breathy pad, or a full vocal melody — the human voice is the most emotionally resonant instrument in existence. Our brains are hardwired to respond to it.

But sampling is off the table. ChipForge generates everything from math. So how do we create voices from code?

## The Science of Voice

The human voice is three things:

### 1. Excitation Source (The Vocal Cords)
- A pulse train (like a square wave) at the fundamental frequency (85-255 Hz male, 165-500 Hz female)
- NOT a pure tone — rich in harmonics (buzz-like)
- Frequency varies with pitch (vibrato, portamento)

### 2. Formant Filter (The Vocal Tract)
- The mouth/throat/nasal cavity creates resonant peaks called **formants**
- F1 (250-900 Hz) — jaw openness (high F1 = open mouth "ah")
- F2 (700-2500 Hz) — tongue position (high F2 = front tongue "ee")
- F3 (2500-3500 Hz) — lip rounding and nasal quality
- Different vowels = different formant frequencies

### 3. Articulation (Consonants, Breath, Noise)
- Fricatives (s, f, sh) = filtered noise bursts
- Plosives (p, t, k) = silence → burst
- Nasals (m, n) = formants shift to nasal resonances

## Formant Frequencies (Hz) — The Vowel Map

| Vowel | F1 | F2 | F3 | Sound |
|---|---|---|---|---|
| /a/ (father) | 730 | 1090 | 2440 | Open, warm |
| /e/ (bed) | 530 | 1840 | 2480 | Mid-front |
| /i/ (beat) | 270 | 2290 | 3010 | Closed, bright |
| /o/ (boat) | 570 | 840 | 2410 | Rounded, dark |
| /u/ (boot) | 300 | 870 | 2240 | Closed, round |
| /æ/ (bat) | 660 | 1720 | 2410 | Open-front |
| /ɔ/ (caught) | 590 | 880 | 2540 | Open-back |

## The AI Approach — What Only Code Can Do

### Technique 1: Formant Synthesis (Classical Approach, Enhanced)

Stack 3-5 resonant bandpass filters (formants) over a harmonics-rich excitation source. AI computes optimal Q factors and gains for each formant to maximize naturalness.

**The AI advantage:** A human tuning 5 filters × 3 parameters (freq, Q, gain) = 15 knobs simultaneously is torture. AI computes the optimal formant configuration for any vowel or vowel transition in milliseconds.

### Technique 2: Vocal Tract Physical Model

Model the vocal tract as a series of connected tube segments with varying diameters. Each segment is a waveguide delay with reflections. AI computes the tube diameters that produce each vowel.

### Technique 3: Vowel Morphing via Spectral Envelope

Use the spectral morph engine (already built!) to morph between different vowel timbres. A note that starts as "oo" and ends as "ah" — continuously, not switching.

### Technique 4: The "Vocal Chop" Synthesizer

EDM vocal chops aren't full words — they're rhythmic fragments. Generate short vowel bursts with pitch-controlled formants, then sequence them as rhythmic elements. The "hey!", "yeah!", "oh!" that drive dance music.

### Technique 5: Breathy Pad (Noise + Formants)

Mix filtered noise (breath) with formant-filtered harmonics. The result sounds like a choir or breathy vocal pad — organic, warm, alive. This is the "angel choir" sound in trance music.

## Implementation Plan

### Phase 1: Formant Filter Bank
- Add `apply_formants()` to synth.py
- 3-5 parallel bandpass filters at formant frequencies
- Vowel parameter as input (selects formant freqs)
- Vowel morphing over note duration

### Phase 2: Vocal Excitation Sources
- Glottal pulse waveform (asymmetric, more natural than square)
- Breathy noise blend (noise mixed with pulse for breathiness)
- Vibrato with natural irregularity (harmonic drift)

### Phase 3: Vocal Instrument Presets
- `vocal_ah`, `vocal_ee`, `vocal_oh`, `vocal_oo`
- `vocal_morph_ah_ee` (morphing vowels)
- `vocal_choir` (multi-voice, detuned, breathy)
- `vocal_chop` (short rhythmic burst)
- `vocal_breathy_pad` (noise + formants)

### Phase 4: Integration
- Wire formants into the mixer pipeline
- Instrument presets with formant parameters
- Demo songs showcasing vocal synthesis

---

## Design Decisions

### Why Not Just Use Samples?
1. **File size** — Pixel Vault has a 50 KB budget. A single vocal sample is 500 KB+.
2. **Flexibility** — Synthesized vocals can be any pitch, any vowel, any duration.
3. **Originality** — Every sound is generated, never copied. This is creation, not curation.
4. **Novelty** — No synth engine does this well from pure code. This is new territory.

### Why Formant Synthesis?
- Scientifically grounded (vowel acoustics are well-understood)
- Computationally cheap (3-5 biquad filters per voice)
- Web Audio compatible (BiquadFilterNode cascade)
- Can be vectorized with numpy/scipy

### What About Consonants?
Phase 1 focuses on vowels (the sustained, melodic part of voice). Consonants (plosives, fricatives) are Phase 2 — they're filtered noise bursts and can be synthesized as percussion events.

---

**This ADR is about creating something genuinely new. Not emulating a sample library. Not copying a recording. Building a voice from mathematics — shaping sound into something that touches the soul.**

**Last Updated:** March 30, 2026
**Version:** 1.0.0
