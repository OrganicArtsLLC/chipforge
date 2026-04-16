# ChipForge Project History & Timeline

A record of how this project evolved from a Game Boy sound emulator to a full AI-powered synthesis engine in 48 hours.

---

## Timeline (from git log)

### Day 1 — March 29, 2026: The Foundation

**Morning: Birth**
- `chip forge initial commit` — The spark. Pure numpy synthesis, Game Boy APU inspiration. 4 waveforms (sine, square, saw, triangle), LFSR noise, basic ADSR. 36 instrument presets.
- `more songs` / `few more songs and ADR for the future` — First compositions: Cascade Protocol, Neural Cascade, Golden Cascade, Pac-Man Drizzle, Moonlight Sonata. These became the "laboratory" — the reference for what good sounds like.
- `docs: add copilot instructions` — Sound quality rules learned the hard way: every melodic note needs dur>=2, every channel needs reverb, velocities capped at 0.85.

**Afternoon: The Composition Bible**
- `docs on creating songs for chipforge` — ADR-003 (Composition Bible), ADR-004 (AI Synthesis Frontiers), AGENT-COMPOSITION-GUIDE, WORKFLOW docs created. The strategic vision: 100s of songs across all genres, 3-5 minute standard duration, mathematical composition techniques.

**Evening: Mass Production Begins**
- `feat: batch 001-010 songs` — First 10 songs across 7 genres. User rates them: some favorites, some not good. The Favorites Formula emerges empirically.
- `feat: add 31 songs + engine upgrades` — Engine gets additive synthesis, chorus effect, filter envelopes, vibrato on presets, just intonation. 53 presets. Songs: Mario, Zelda, Sonic, Mega Man, Chrono Trigger, Blade Runner, Inception, Imperial March, and more.

**Night: The EDM Sprint**
- 50+ EDM songs produced in rapid batches of 5: Born Slippy, Sandstorm, Children, Strobe, Blue Monday, Insomnia, Levels, Nightcall, Firestarter, Language, Ghosts n Stuff, Opus, D.A.N.C.E., Teardrop, Right Here Right Now, Windowlicker, Enjoy the Silence, Turbo Killer, Scary Monsters, Porcelain, Block Rockin' Beats, 9PM, Café del Mar, Halcyon, Exploration of Space, Flaming June, Xpander, The Robots, Promises, Icarus, Don't You Worry Child, Genesis, Pursuit, A Moment Apart, Satellite, Computer Love, Roads, Oxygène, Sad Machine, Chase, and more.
- `expanded instrument palette` — User expands the instrument library, adds new drum kit, supersaw, 808 bass, choir pad.

### Day 2 — March 30, 2026: The AI Revolution

**Morning: AI-Only Techniques**
- `feat: ADR-005 AI-amplified engine vision` — Strategic document mapping every component to its AI amplification potential. P0 fixes: centralize SAMPLE_RATE, export effects.py.
- `feat: spectral morphing + per-harmonic envelope shaping` — The first AI-only synthesis techniques. STFT-based spectral interpolation. Independent ADSR per harmonic partial. 30/30 tests.
- `feat: counterpoint generator + auto-mastering` — AI generates harmonically correct counter-melodies (93% consonance rate). Auto-mastering analyzes mix and computes optimal parameters per genre.

**Midday: v4 Showcase**
- `feat: 6 v4 showcase songs` — Running Up That Hill v4, Heroes v4, Strobe v4, Wily Stage v4, Café del Mar v4, Bolero v4. Each uses all AI-only features. The Bolero v4 discovery: spectral morphing implements Ravel's orchestration changes as continuous mathematical transformation.
- `feat: engine hardening` — LRU IR cache (memory safety), chorus linear interpolation fix, song catalog system (122 songs indexed, search/filter).

**Afternoon: Full Monte**
- `feat: FM synthesis, Karplus-Strong, ring mod, granular, multiband comp, phaser, flanger` — 4 new synthesis types, 3 new effects. 126 presets.
- `feat: full monte` — PWM, portamento, harmonic drift, tape saturation, transient shaper, noise gate, tension curves, ChipForge.js web compiler. 129 presets.

**Evening: Voices from Code**
- `feat: vocal synthesis — voices from pure code (ADR-006)` — Glottal pulse excitation, 5-formant filter bank, 8 vowels, vowel morphing, 5-voice choir, vocal chops. 140 presets. Voices synthesized from mathematics — no samples, no recordings.
- `feat: "Voices from Code"` — Demo song showcasing all vocal types.
- `feat: 10 masterpiece v4 revamps` — Ground-up rewrites: Stranger Things Theme, Master of Puppets, Time After Time, Children, Nightcall, Enjoy the Silence, Porcelain, Halcyon, Sad Machine, Ecstasy of Gold.

**Night: Metal & The Climax**
- `feat: metal guitar synthesis — amp sim, power chords, palm mutes, shred` — Guitar amp simulator (3-stage cascaded distortion + cabinet EQ). Power chords, palm mutes, tremolo picking. Master of Puppets v5, Thunderstruck, Eruption, Enter Sandman. 146 presets.
- `feat: Strobe v5 + Café del Mar v5` — Comparison pair: v4 vs full engine.
- `feat: Deal with God — The Vecna Climax` — The culmination. Kate Bush's vocal as synthesized soprano. 5-act emotional arc from darkness to transcendence. Every engine feature in one piece.

---

## Engine Evolution

| Milestone | Presets | Synth Types | Effects | Lines |
|-----------|---------|-------------|---------|-------|
| Initial commit | 36 | 5 | 3 | ~2,000 |
| Post-EDM sprint | 53 | 8 | 6 | ~3,500 |
| AI techniques | 102 | 10 | 10 | ~5,000 |
| Full monte | 129 | 14 | 17 | ~6,500 |
| Vocal + metal | 146 | 19 | 20 | ~7,500 |

## Song Count Evolution

| Milestone | Songs |
|-----------|-------|
| Initial (laboratory) | 9 |
| First batch | 13 |
| EDM sprint | 65 |
| v4 showcases | 71 |
| Masterpiece revamps | 83 |
| Metal + vocal | 90 |
| Total with all versions | 140+ files |

---

## Key Discoveries

1. **The Favorites Formula** — Hand-crafted hooks + wet everything + noise_clap + bass_growl + dur>=2 + structural silence = favorite quality. Empirically derived from user ratings.

2. **Spectral Morphing for Orchestration** — Ravel's Bolero orchestration changes (flute→clarinet→brass) can be implemented as continuous mathematical spectral interpolation. A genuinely novel application.

3. **Vocal Synthesis from Formants** — Glottal pulse + 5 resonant filters = recognizable vowels. No samples needed. The voice is mathematics.

4. **Guitar Amp as Cascaded Distortion** — 3 stages of asymmetric tanh saturation + cabinet EQ = convincing metal guitar tone from Karplus-Strong string model.

5. **Auto-Mastering from Genre Analysis** — AI can compute optimal mastering parameters (EQ, compression, width, saturation) by analyzing spectral balance and dynamic range, then applying genre-specific profiles.

---

**This project went from zero to 146 instruments, 19 synthesis types, 20 effects, 140+ songs, vocal synthesis, guitar amp simulation, auto-mastering, and a web compiler in 48 hours. Every sound is generated from mathematics. No samples. No recordings. Code shaped into music.**
