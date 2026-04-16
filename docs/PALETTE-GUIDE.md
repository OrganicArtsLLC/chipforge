# Instrument Palette Guide

**ChipForge Composition Reference**  
**Last Updated:** 2026-04-02

---

## The Core Problem

With 160+ presets, you can't use them all. You shouldn't try. Every great
chip tune track uses 5–8 instruments chosen to *fit together* — a palette
with a clear identity. Mixing palettes (a glottal buzz with a metal power
chord) is disorienting unless you understand why the contrast works.

This guide gives you named palettes: coherent groups that render well
together, with effect templates to match.

---

## Palette 1: Classic Game Boy
*The original 4-channel sound — pure, warm, constrained*

| Channel | Instrument | Role |
|---------|-----------|------|
| Lead | `pulse_lead` or `pulse_warm` | Melody |
| Bass | `wave_bass` or `pulse_bass` | Root movement |
| Harmony | `pulse_chime` or `gb_bell_wave` | Counter-melody / pads |
| Drums | `noise_kick` + `noise_snare` + `noise_hat` | Rhythm |

**Effects template:**
```python
channel_effects = {
    0: {"reverb": 0.06},                           # Kick: room
    1: {"reverb": 0.10},                           # Snare: presence
    2: {"delay": 0.14, "delay_feedback": 0.20},    # Hat: rhythmic echo
    3: {"reverb": 0.06},                           # Bass: tight
    4: {"reverb": 0.18, "delay": 0.16},            # Lead: space
    5: {"reverb": 0.30},                           # Harmony: halo
}
master_reverb = 0.10
```

**Palette rules:** BPM 100–140. No more than 2 harmony channels. Avoid
anything with `additive_`, `fm_`, or `karplus` — this is pure square-wave land.

**Songs using this palette:** most original work, `cascade_protocol.py`

---

## Palette 2: Synthwave / Rave
*Supersaw stacks, fat bass, big snare, lush pads — the main event*

| Channel | Instrument | Role |
|---------|-----------|------|
| Lead | `supersaw_lead` or `saw_filtered` | Melody |
| Bass | `bass_growl` or `bass_808` | Low end |
| Pad | `pad_lush` or `supersaw_pad` | Warmth |
| Keys | `fm_epiano` or `pwm_lead` | Mid fill |
| Kick | `kick_deep` or `kick_punchy` | Drive |
| Snare | `snare_fat` or `noise_clap` | Snap |
| Hat | `hat_crisp` + `hat_open_shimmer` | Groove |

**Effects template:**
```python
channel_effects = {
    0: {"reverb": 0.06},
    1: {"reverb": 0.14},
    2: {"delay": 0.20, "delay_feedback": 0.30, "reverb": 0.08},
    3: {"reverb": 0.08},
    4: {"reverb": 0.40},                           # Pad: deep hall
    5: {"reverb": 0.22, "delay": 0.18, "delay_feedback": 0.28},
    6: {"reverb": 0.30},
}
master_reverb = 0.15
```

**Palette rules:** BPM 128–145. Kick on 1 and 3. Pad should enter 2–4
bars before drums. Supersaw needs reverb 0.35+ to bloom.

**Songs using this palette:** `neural_cascade_v2.py`, `strobe.py`

---

## Palette 3: Ambient / Cinematic
*Slow evolving textures, no percussion, pure tone and space*

| Channel | Instrument | Role |
|---------|-----------|------|
| Foundation | `pad_lush` or `pad_warm_analog` | Drone base |
| Movement | `add_string` or `add_glass_pad` | Slow melody |
| Texture | `grain_shimmer` or `grain_cloud` | Shimmer |
| Accent | `ks_harp` or `fm_bell` | Sparse notes |
| Counter | `add_ethereal` or `pad_evolving` | Second voice |

**Effects template:**
```python
channel_effects = {
    0: {"reverb": 0.50},                           # Foundation: hall
    1: {"reverb": 0.45, "delay": 0.30, "delay_feedback": 0.40},
    2: {"reverb": 0.55},                           # Texture: wash
    3: {"reverb": 0.40, "delay": 0.40, "delay_feedback": 0.35},
    4: {"reverb": 0.50},
}
master_reverb = 0.25
```

**Palette rules:** BPM 60–90 (or free time). Duration >= 8 bars before
any notes. All notes duration >= 8 steps. Velocity max 0.70.

---

## Palette 4: Organic / Vocal
*The new frontier — voices as melody, choir as pad, KS as bass*

| Channel | Instrument | Role |
|---------|-----------|------|
| Melody | `vocal_lead_ah` or `vocal_lead_ee` | Sung melody line |
| Pad | `vocal_ensemble` or `vocal_pad_warm` | Vocal pad |
| Bass | `vocal_bass_oo` or `ks_bass` | Root |
| Choir | `vocal_choir` or `vocal_choir_ee` | Harmony |
| Texture | `grain_shimmer` or `add_ethereal` | Air |
| Percussion | `vocal_chop` | Rhythmic hits |

**Effects template:**
```python
channel_effects = {
    0: {"reverb": 0.35},                           # Melody: room + tail
    1: {"reverb": 0.45},                           # Pad: hall
    2: {"reverb": 0.12},                           # Bass: tight
    3: {"reverb": 0.50, "delay": 0.20},            # Choir: cathedral
    4: {"reverb": 0.40},                           # Texture: diffuse
    5: {"delay": 0.14, "delay_feedback": 0.20, "reverb": 0.10},  # Chop: bounce
}
master_reverb = 0.20
```

**Palette rules:** BPM 80–110. Melody notes duration >= 4 steps. Choir
should enter at least 4 bars in. Vocal chop velocity max 0.75 — they hit hard.
All vocal instruments need `duration_steps >= 3` for the formants to ring.

**Key insight:** `vocal_lead_ah` over `pad_lush` is a combination no pure
chip tune engine has ever produced. The contrast between mathematical voice
synthesis and subtractive pad creates something genuinely new.

**Untried combinations to explore:**
- `vocal_stab` as rhythmic pulse under a `supersaw_lead` melody
- `glottal_buzz` as bass with `vocal_choir` harmony (very Gregorian)
- `vocal_morph_ah_ee` as lead over `fm_pad` — formants moving against FM modulation
- `vocal_chop` rhythmically sequenced against `kick_808` + `hat_crisp` (EDM vocal chop)
- `vocal_pad_warm` as a drone under `ks_harp` plucks — organic, not chip

---

## Palette 5: Metal / Heavy
*Power chords, djent chug, shred lead — maximum aggression*

| Channel | Instrument | Role |
|---------|-----------|------|
| Rhythm | `metal_power` or `metal_palm` | Riff |
| Chug | `metal_chug` | Djent gate |
| Lead | `metal_lead` or `metal_solo` | Solo |
| Bass | `bass_dirty` or `bass_808` | Low end |
| Drums | `kick_distorted` + `snare_808` + `hat_tight` | Blast |

**Effects template:**
```python
channel_effects = {
    0: {"reverb": 0.08},                           # Rhythm: tight room
    1: {"reverb": 0.05},                           # Chug: very dry
    2: {"reverb": 0.20, "delay": 0.10},            # Lead: slight tail
    3: {"reverb": 0.08},
    4: {"reverb": 0.06},
    5: {"reverb": 0.10},
    6: {"reverb": 0.06},
}
master_reverb = 0.06
```

**Palette rules:** Metal should be DRY. Avoid reverb > 0.25 on anything.
BPM 140–200. Kick on every beat (or double-kick pattern). The `metal_chug`
needs `duration_steps=1` to stay tight.

---

## Palette 6: FM / Jazz Electronic
*Complex timbres, unpredictable harmonics, organic warmth*

| Channel | Instrument | Role |
|---------|-----------|------|
| Lead | `fm_organ` or `lead_expressive` | Melody |
| Keys | `fm_epiano` | Chords / comping |
| Bass | `fm_bass` or `ks_bass` | Root |
| Strings | `add_string` or `ks_guitar` | Texture |
| Percussion | `perc_click` + `shaker` + `ride` | Groove |

**Effects template:**
```python
channel_effects = {
    0: {"reverb": 0.25},
    1: {"reverb": 0.20, "delay": 0.15, "delay_feedback": 0.25},
    2: {"reverb": 0.12},
    3: {"reverb": 0.30},
    4: {"reverb": 0.08},
    5: {"reverb": 0.06},
}
master_reverb = 0.12
```

---

## Palette 7: Lo-Fi / Vintage
*Degraded, warm, imperfect — the sound of worn tape*

| Channel | Instrument | Role |
|---------|-----------|------|
| Lead | `lead_soft` or `pluck_mellow` | Melody |
| Keys | `organ_warm` or `fm_epiano` | Chords |
| Bass | `bass_smooth` | Root |
| Sample texture | `grain_texture` or `grain_cloud` | Vinyl crackle |
| Drums | `snare_lo_fi` + `hat_lo_fi` + `kick_short` | Dusty kit |

**Effects template:**
```python
channel_effects = {
    0: {"reverb": 0.20},
    1: {"reverb": 0.25, "delay": 0.20, "delay_feedback": 0.30},
    2: {"reverb": 0.15},
    3: {"reverb": 0.40},                           # Texture: washed
    4: {"reverb": 0.18},
    5: {"reverb": 0.12},
}
master_reverb = 0.18
```

**Palette rules:** BPM 70–90. Velocity max 0.75 on everything. The lo-fi
aesthetic is compressed amplitude. Nothing should be loud.

---

## Cross-Palette Experiments

These combinations violate palette boundaries intentionally — high-risk,
high-reward if the contrast is controlled:

| Combination | Concept | Notes |
|-------------|---------|-------|
| `vocal_choir` + `supersaw_lead` | Human vs machine | Choir as pad, supersaw cuts over |
| `metal_power` + `vocal_stab` | Aggression meets breath | Stab on the 1, power chord fills |
| `ks_harp` + `pad_lush` | Organic pluck in a synthetic ocean | Sparse harp over deep pad |
| `glottal_buzz` + `fm_organ` | Two voice models side by side | Both are vocal-adjacent, very eerie |
| `grain_shimmer` + `vocal_ensemble` | Synthetic texture + synthetic voice | Ambient, no clear instrument |
| `vocal_morph_ah_ee` + `pwm_lead` | Formant movement vs PWM sweep | Two different mod sources, same energy |
| `ks_guitar` + `vocal_choir_ee` | String body + choir halo | The choir blooms behind the pluck |
| `add_brass` + `metal_trem` | Orchestral aggression | Brass stabs under tremolo guitar |

---

## Palette Assembly Checklist

Before finalizing a song's instrument mix:

- [ ] **Is the bass represented?** — at least one instrument below 200 Hz
- [ ] **Is the mid covered?** — 200–2000 Hz, the presence zone
- [ ] **Is the high end adding air?** — shimmer, hat, overtones in 5–12 kHz
- [ ] **No two leads fighting?** — max one melody-range instrument at a time
- [ ] **Drum palette consistent?** — don't mix GB drums with metal drums
- [ ] **Effects match the palette** — metal = dry, ambient = wet, rave = mid
- [ ] **Velocity budget** — 7+ channels all at 0.85 will clip; scale down
- [ ] **Duration budget** — pads need `dur >= 8`, leads `dur >= 2`, perc `dur = 1–2`

---

## New Vocal Presets (Added 2026-04-02)

After fixing the formant filter engine (bandpass, not lowpass), these
new presets are specifically designed for palette use:

| Preset | Character | Best with |
|--------|-----------|-----------|
| `vocal_lead_ah` | Clean sung melody | Palette 4: Organic |
| `vocal_lead_ee` | Bright high lead | Low pad backgrounds |
| `vocal_bass_oo` | Deep vowel bass | Choir harmony above |
| `vocal_ensemble` | Slow swell choir | Sparse melody on top |
| `vocal_stab` | Percussive hit | Rave/EDM palette |
| `vocal_pad_warm` | Long drone | Harp or glass pluck above |
| `vocal_whisper` | Soft air texture | Ambient / background |
