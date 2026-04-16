# ADR-001: ChipForge Initial Architecture

**Status:** Accepted  
**Date:** March 29, 2026  
**Author:** Joshua Ayson / OA LLC

---

## Context

We need an agent-controllable music composition tool that:

1. Produces authentic, rich electronic sounds (not MIDI file writing or sample playback)
2. Follows tracker conventions (MOD/FastTracker heritage) since step grids map naturally to AI generation
3. Has a first-class REST API so any AI agent can control it without a GUI
4. Is built from the ground up in pure Python with no "magic box" audio libraries
5. Is designed to grow — MVP now, richer features (effects, live mode, MIDI export) later

**Inspiration:** Game Boy APU (DMG chip, 1989). Four discrete sound channels, each with a specific waveform type and hardware envelope. Despite extreme hardware limitations, produced musically compelling, distinctly "computer" yet melodic sounds. That aesthetic is the target.

---

## Options Considered

### Option A: Use an existing Python audio library (pydub, librosa, soundfile)

**Pros:** Less code, faster to prototype.  
**Cons:** Black boxes. Pydub wraps ffmpeg, librosa is for analysis, soundfile is for file I/O. None provide synthesis. We'd still need to write the oscillators ourselves.

**Rejected because:** We'd end up writing the synthesis layer anyway, plus carry the weight of opaque dependencies.

### Option B: Use pygame.mixer + sound objects

**Pros:** Simple playback, familiar to game devs.  
**Cons:** Pygame mixer expects pre-rendered sound buffers; synthesis still falls to us. Adds a substantial dependency for no synthesis help.

**Rejected because:** Same criticism as Option A — just provides playback scaffolding, not synthesis.

### Option C: Pure numpy synthesis + FastAPI REST API (chosen)

**Pros:**
- Full control: every sample value is ours
- Waveform characteristics are explicit and tunable (duty cycle, LFSR period, wavetable shape)
- numpy vectorized operations are fast enough for offline rendering
- No external dependencies beyond numpy + fastapi
- sounddevice is optional (only needed for live playback; WAV export works without it)
- REST API philosophy: language-agnostic, agent-agnostic

**Cons:**
- More code to write initially
- Real-time / streaming audio requires more work (deferred to future)

**Accepted.**

---

## Core Architecture Decisions

### 1. Sample Rate: 44100 Hz

Standard CD-quality. Game Boy hardware ran at ~32768 Hz but we target full quality. Easy to downsample if needed.

### 2. Waveform Engine (src/synth.py)

Five fundamental waveforms, all generated from first principles:

- **Sine** — `sin(2πft)` — pure tone, pads
- **Square with variable duty** — `sign(sin(2πft) - (2*duty - 1))` — authentic GB pulse channels
- **Sawtooth** — `2(ft mod 1) - 1` — bright, buzzy
- **Triangle** — `|2(ft mod 1) - 1| * 2 - 1` — smooth, mellow
- **LFSR Noise** — precomputed Linear Feedback Shift Register sequence — authentic GB CH4 noise

**LFSR noise is critical.** Random white noise does not sound like Game Boy CH4. The LFSR produces a periodic pseudo-random sequence with a characteristic timbre:
- 7-bit LFSR (period 127): metallic, hi-hat like
- 15-bit LFSR (period 32767): near-white, kick/snare use

Both sequences are precomputed at module load (127 and 32767 samples respectively) and tiled to any length. Zero overhead at render time.

**ADSR Envelope:** 4-phase amplitude shaping — Attack, Decay, Sustain, Release. Applied as a float32 multiplier envelope. If the note duration is shorter than A+D+R, segments scale proportionally.

### 3. Instrument Presets (src/instruments.py)

Fixed catalog of presets modeled after GB APU channel behavior:

| Preset | Waveform | Duty | Archetype |
|--------|----------|------|-----------|
| pulse_lead | square | 25% | GB CH1 melody |
| pulse_bass | square | 50% | GB CH2 bass |
| pulse_chime | square | 12.5% | GB bell tone |
| wave_melody | triangle | — | GB CH3 smooth |
| sine_pad | sine | — | atmospheric |
| saw_lead | sawtooth | — | synth lead |
| noise_hat | lfsr_7 | — | GB CH4 short |
| noise_snare | lfsr_15 | — | GB CH4 long |
| noise_kick | lfsr_15 | — | GB CH4 long + longer decay |
| chip_lead | square | 50% | punchy chip solo |

Instruments are plain dataclasses: waveform + ADSR + duty + volume. Agents can reference these by string key.

### 4. Music Theory (src/theory.py)

Pure functions, no state. Provides:

- Note name ↔ MIDI number conversion (C4 = 60)
- Scale definitions (11 scales)
- Chord type definitions (9 types)
- Classical chord progressions
- `generate_melody()`: weighted random walk along scale notes with stepwise bias
- `generate_rhythm_pattern()`: density-based hit pattern with downbeat emphasis

These are intentionally simple for MVP. The goal is musically sensible output, not academic perfection.

### 5. Sequencer (src/sequencer.py)

Tracker-style data model:

```
Song
  └── patterns: list[Pattern]
  └── sequence: list[int]       ← indices into patterns list (arrangement)

Pattern
  └── grid: list[list[NoteEvent | None]]
             ↑ channel          ↑ step

NoteEvent
  └── midi_note: int            ← 0 = rest
  └── velocity: float
  └── duration_steps: int
  └── instrument: str
```

A song is rendered by iterating `sequence`, rendering each referenced `Pattern`, and concatenating the audio buffers.

### 6. Mixer (src/mixer.py)

`render_pattern()`:
1. Allocates a zero float32 buffer sized to pattern duration
2. For each channel, for each step with a NoteEvent, synthesizes the note
3. Accumulates all channels into the mix
4. Converts mono mix to stereo (both channels identical for now — panning is future work)

`render_song()`:
1. Renders each pattern in `song.sequence`
2. Concatenates pattern buffers
3. Normalizes peak to ≤ 0.90 to prevent clipping

Peak normalization preserves musical dynamics while preventing hard clipping.

### 7. Export (src/export.py)

**WAV:** 16-bit PCM stereo, written using stdlib `wave` module. No external dependency.

**JSON:** Song serialized to plain dict with `json.dump`. Human-readable, version-controllable.

**In-memory to bytes:** `audio_to_wav_bytes()` renders WAV to `io.BytesIO` for the API render endpoint (no temp files).

### 8. Agent REST API (api/main.py)

Built with FastAPI. Design principles:

- **In-memory state:** `songs: dict[str, Song]` — UUID-keyed. Survives server restart... it doesn't. Sufficient for MVP. SQLite persistence is planned.
- **One-call song building:** `POST /songs/build` accepts a complete song description. Agents can build a full song in a single API call.
- **Algorithmic generation:** `POST /songs/generate` accepts high-level parameters (key, scale, BPM, num_patterns) and generates a complete song algorithmically.
- **Step-by-step editing:** Individual note endpoints allow fine-grained control.
- **WAV streaming:** `GET /songs/{id}/render` returns raw WAV bytes directly.

---

## Consequences

**Positive:**
- Complete waveform control — can implement any GB-era or classic chip sound
- No licensing issues — nothing proprietary
- Runs offline, no cloud dependency
- REST API is agent-framework agnostic (Claude, GPT, LangChain, etc.)
- Easy to add effects (reverb, distortion, filter) as numpy DSP later

**Negative / Accepted trade-offs:**
- Rendering is CPU-bound and synchronous — a 3-minute song may take 2–3 seconds to render. Acceptable for MVP. Streaming/incremental render is future work.
- No real-time playback without sounddevice. WAV file workflow is primary.
- In-memory state is lost on server restart. File-based or SQLite persistence is the next architectural step.

---

## Future ADRs Expected

- ADR-002: Song persistence strategy (SQLite vs flat files vs PostgreSQL)
- ADR-003: Real-time streaming audio (WebSocket or chunked render)
- ADR-004: Effects chain architecture (filter, reverb, distortion)
- ADR-005: MIDI import/export support
