# ChipForge Song Production Workflow

## Folder Structure

```
songs/
  classical/     — Bach, Beethoven, Mozart, Chopin, Vivaldi, Debussy...
  edm/           — Trance, house, techno, drum & bass, dubstep...
  hiphop/        — G-funk, trap, boom bap, lo-fi...
  jazz/          — Bebop, fusion, smooth, cool jazz...
  ambient/       — Chill, downtempo, new age, drone...
  rock/          — Classic rock, metal, punk, prog...
  pop/           — Pop, synth-pop, disco, funk...
  electronic/    — Synthwave, IDM, electronica, experimental...
  world/         — Latin, African, Middle Eastern, Asian...
  soundtrack/    — Film scores, video game OSTs, anime...
```

All song .py files go in their genre folder. Output WAVs always render to `output/`.

## File Naming Convention

```
songs/<genre>/<number>_<short_title>.py
```

- `<number>`: 3-digit zero-padded (001, 002, ...)
- `<short_title>`: lowercase, underscores, descriptive

Examples:
```
songs/classical/001_moonlight_sonata.py
songs/classical/002_bach_invention_13.py
songs/edm/001_euphoric_trance.py
songs/hiphop/001_west_coast_bounce.py
songs/jazz/001_blue_monk.py
```

The number is per-genre (each genre has its own sequence).

## Output Naming Convention

```
output/<genre>_<number>_<short_title>.wav
```

Examples:
```
output/classical_001_moonlight_sonata.wav
output/edm_001_euphoric_trance.wav
```

## Git Workflow

### For Small Batches (1-3 songs)

Work directly on main. Commit after each song is verified:

```bash
git add songs/<genre>/NNN_title.py
git commit -m "feat: add <song title> (<genre>)"
```

### For Larger Batches (4+ songs)

Create a feature branch:

```bash
git checkout -b songs/<genre>-batch-N
# or for mixed genres:
git checkout -b songs/batch-NNN-NNN
```

PR format:
```
Title: feat: add songs NNN-NNN (<genre> batch)
Body: List of songs with brief descriptions
```

Merge to main when the batch is reviewed and approved.

### Parallel Work

Multiple branches can exist simultaneously for different genres:
```
main
├── songs/classical-batch-1    (songs 001-010)
├── songs/edm-batch-1          (songs 001-010)
└── songs/jazz-batch-1         (songs 001-005)
```

These branches won't conflict since they touch different files.

## Quality Tiers

Songs move through quality tiers based on review:

| Tier | Meaning | Action |
|------|---------|--------|
| Draft | Rendered, not reviewed | Needs listening |
| Reviewed | Listened to, feedback given | May need revision |
| Approved | Meets quality bar | Ready for library |
| Featured | Exceptional quality | Showcase piece |

Track tier in commit messages or a future catalog file.

## Scaling Protocol

```
Round 1: 1 song   → full critique → calibrate quality bar
Round 2: 3 songs  → batch review  → refine approach
Round 3: 10 songs → spot check    → verify consistency
Round 4: 50 songs → statistical   → review highlights + any flagged
Round 5: 100+     → automated     → quality checklist + spot check
```
