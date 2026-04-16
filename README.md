# ChipForge

[![License](https://img.shields.io/badge/license-CONTENT--LICENSE-blue)](CONTENT-LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)](https://python.org)
[![Author](https://img.shields.io/badge/by-Joshua%20Ayson-black)](https://joshuaayson.com/projects/)

**AI-powered music synthesis engine — voices, guitars, and orchestras from pure mathematics.**

Built from scratch in Python/numpy. No samples, no recordings, no external audio libraries. Every sound is generated from code.

---

## What It Is

ChipForge started as a Game Boy APU emulator and evolved into a full synthesis engine with 146 instrument presets, 19 synthesis types, 20 effects, vocal synthesis, guitar amp simulation, and an AI composition pipeline. It generates audio waveforms sample-by-sample and exposes a REST API for AI agents to compose, sequence, and export music.

**140+ songs rendered** across EDM, soundtrack, rock, pop, classical, and stranger-things collections.

---

## Quick Start

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Render a song
./render.sh songs/edm/010_strobe_v5.py

# Run all tests (115 tests, ~2 seconds)
.venv/bin/python3 tests/test_engine_comprehensive.py

# Start the agent API
uvicorn api.main:app --reload --port 8765

# QA Dashboard — open in browser, drop WAV files to review
open tools/qa-dashboard.html
```

---

## Synthesis Types (19)

| Type | Description | Example Presets |
|------|-------------|-----------------|
| **Sine** | Pure tone | sine_pad, sine_bass |
| **Square** | GB pulse wave (4 duty cycles) | pulse_lead, chip_lead |
| **Sawtooth** | Bright, harmonically rich | saw_filtered, saw_dark |
| **Triangle** | Smooth, mellow | wave_melody, wave_bass |
| **Noise** | LFSR (7-bit metallic, 15-bit white) | noise_hat, noise_kick |
| **Wavetable** | Custom 32-sample cycle | gb_wavetable, gb_organ |
| **Additive** | Harmonic series control | additive_warm, additive_bright |
| **Supersaw** | Detuned saw stack (trance) | supersaw_3, supersaw_7 |
| **Shaped** | Per-harmonic ADSR envelopes | shaped_brass, shaped_bell |
| **FM** | Yamaha DX7-style frequency modulation | fm_bell, fm_epiano, fm_bass |
| **Karplus-Strong** | Physical modeling plucked string | ks_guitar, ks_harp, ks_bass |
| **Ring Mod** | Metallic/gamelan tones | ring_bell, ring_gamelan |
| **Granular** | Texture clouds from grain windows | grain_cloud, grain_shimmer |
| **PWM** | Pulse width modulation | pwm_lead, pwm_pad, pwm_bass |
| **Vocal** | Formant synthesis (8 vowels, choir, chops) | vocal_ah, vocal_choir |
| **Power Chord** | Stacked KS strings (root+fifth+oct) | metal_power |
| **Palm Mute** | Short-decay power chord | metal_palm, metal_chug |
| **Guitar Lead** | Sustained KS with harmonic feedback | metal_lead, metal_solo |
| **Guitar Trem** | Rapid alternate picking | metal_trem |

---

## Effects (20)

| Effect | Description |
|--------|-------------|
| Schroeder Reverb | 6 comb + 4 allpass (FFT convolution, LRU cached) |
| Feedback Delay | 5-tap echo with exponential decay |
| Chorus | Detuned voices with linear interpolation |
| Compressor | Dynamics control with attack/release |
| Sidechain | Ducking compression (kick pumping) |
| Multiband Compressor | 5-band frequency-selective dynamics |
| Parametric EQ | N-band peak/shelf/highpass/lowpass |
| Distortion | Soft clip, hard clip, foldback modes |
| Phaser | Cascaded allpass with LFO sweep |
| Flanger | Short modulated delay with feedback |
| Transient Shaper | Independent attack/sustain gain |
| Tape Saturation | Asymmetric clipping + flutter + HF rolloff |
| Noise Gate | Threshold-based silencing |
| Guitar Amp Sim | 3-stage cascaded distortion + cabinet EQ |
| Stereo Widener | Mid/side processing |
| Master Bus | Full mastering chain |
| Auto-Master | Genre-aware mastering (7 profiles) |
| Soft Limiter | tanh clipping at 0.85 threshold |
| Spectral Morph | STFT-based timbral interpolation |
| Mix Analysis | Peak, RMS, centroid, dynamic range, crest factor |

---

## AI-Only Techniques

Features that require systematic computation humans can't do by hand:

- **Spectral Morphing** — STFT interpolation between two timbres
- **Per-Harmonic Shaping** — Independent ADSR per harmonic partial
- **Auto-Counterpoint** — Generates harmonically correct counter-melodies (93% consonance rate)
- **Auto-Mastering** — Analyzes mix and computes optimal parameters per genre
- **Tension Analysis** — Compute harmonic tension per melody position from interval + chord context
- **Tension Curves** — 5 shapes: build_drop, verse_chorus, continuous_rise, arch, waves
- **Vocal Synthesis** — Glottal pulse + 5-formant filter bank = 8 vowels from mathematics

---

## QA Dashboard

Visual song review tool for rating songs and collecting timestamped feedback.

```bash
open tools/qa-dashboard.html
```

**Features:**
- Drag-and-drop WAV loading with song card grid
- Status tiers: ★ Favorite / Good / Needs Work / Broken / Untested
- Mini waveform preview per song (color-coded by status)
- Fixed player bar with quick feedback buttons (👍 🐛 🔧 🎸 🎚️)
- Live scrolling spectrogram (press S)
- Timestamped notes with type classification (bug/enhancement/instrument/mix/praise)
- JSON export with `action_items` array for agent processing
- Import previous feedback to continue across sessions
- All state auto-saved to localStorage

**Workflow:** Drop WAVs → listen → rate → add notes at timestamps → export JSON → feed to next agent session.

---

## Song Library (140+ files)

| Genre | Count | Highlights |
|-------|-------|------------|
| EDM | 53 | Strobe, Children, Nightcall, Sandstorm, Levels, Halcyon, Sad Machine |
| Soundtrack | 23 | Stranger Things, Zelda, Mario, Blade Runner, Ecstasy of Gold |
| Stranger Things | 19 | Running Up That Hill (4 versions), Master of Puppets, Heroes |
| Rock | 7 | Thunderstruck, Eruption, Enter Sandman, Eye of the Tiger |
| Classical | 6 | Bolero, Clair de Lune, Für Elise, Bach Toccata, Vivaldi |
| Pop | 3 | Ghostbusters, My Heart Will Go On, Don't You Forget |
| Other | 29+ | Laboratory experiments, originals, genre tests |

Many songs have v2-v5 versions showing the engine's evolution.

---

## Project Structure

```
chipforge/
├── src/
│   ├── synth.py           — 19 waveform generators, ADSR, filters, vocal, guitar
│   ├── instruments.py     — 146 instrument presets
│   ├── theory.py          — Scales, chords, melody, counterpoint, tension
│   ├── sequencer.py       — Pattern + Song data models
│   ├── mixer.py           — Multi-channel rendering, effects pipeline
│   ├── effects.py         — 20 audio effects + auto-mastering
│   ├── export.py          — WAV export + JSON song I/O
│   ├── catalog.py         — Song library indexing + search
│   └── web_compiler.py    — Song → JavaScript (Web Audio API)
├── api/
│   └── main.py            — FastAPI agent REST API
├── tools/
│   └── qa-dashboard.html  — Visual song review + feedback collection
├── tests/
│   ├── test_engine_comprehensive.py  — 85 regression tests (all modules)
│   └── test_ai_engine.py            — 30 AI engine tests
├── songs/                 — Song scripts by genre (140+ .py files)
├── output/                — Rendered WAV files (gitignored)
├── docs/
│   ├── ADR-003-composition-bible.md  — Composition guide + genre rules
│   ├── ADR-006-vocal-synthesis.md    — Vocal synthesis design
│   ├── AGENT-COMPOSITION-GUIDE.md    — Operational quick reference
│   ├── PROJECT-HISTORY.md            — Timeline + evolution narrative
│   └── LEGAL-NOTES.md               — Copyright analysis + Pixel Vault guidance
├── archive/               — Archived early-stage files
├── render.sh              — Background render helper
├── CLAUDE.md              — AI agent instructions + sound quality rules
└── README.md              — This file
```

---

## Legal Notes

All audio is generated from mathematical synthesis — no samples, no recordings. Song arrangements are original electronic interpretations. See `docs/LEGAL-NOTES.md` for copyright analysis and Pixel Vault integration guidance.

---

## Pixel Vault Integration

ChipForge songs can be compiled to self-contained JavaScript for use in Pixel Vault games:

```python
from src.web_compiler import compile_to_js
js_code = compile_to_js(song, minify=True)  # ~3-5 KB per song
```

The output uses Web Audio API oscillators — no audio files needed. See `new-142-chipforge.html` in the Pixel Vault repo for a working integration example.

---

**Version:** 0.4.1  
**Engine:** 146 presets · 19 synthesis types · 20 effects · 115 tests  
**Status:** Active development — 140+ songs, vocal synthesis, guitar amp sim  
**Maintainer:** Joshua Ayson / OA LLC

---

## License

Dual-licensed:

- **Engine** (`src/`, `api/`, `tests/`) — [GPL-3.0-or-later](LICENSE)
- **Original compositions** (`songs/`) — [CC BY-SA 4.0](CONTENT-LICENSE) *(covers and arrangements excluded)*

See [LICENSE](LICENSE) and [CONTENT-LICENSE](CONTENT-LICENSE) for details.
