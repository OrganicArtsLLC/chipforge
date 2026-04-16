# ChipForge Song Catalog

**Version:** 1.0.0  
**Last Updated:** April 2026  
**License:** See [CONTENT-LICENSE](../CONTENT-LICENSE) for full terms

This catalog documents all song scripts in ChipForge: original compositions, classical
arrangements, and named exclusions. All CC BY-SA 4.0 content is indicated. Files that
are mechanical arrangements of copyrighted works are explicitly excluded from CC licensing.

---

## License Legend

| Symbol | Meaning |
|--------|---------|
| ✅ CC BY-SA 4.0 | Original composition — share and adapt with attribution + same license |
| 🎓 PD Arrangement | Arrangement of public domain source — CC BY-SA 4.0 on the arrangement |
| ⛔ COVER — EXCLUDED | Mechanical arrangement of copyrighted song — NOT covered by CC BY-SA. Personal use only. |
| ⚠️ VERIFY | Name shared with copyrighted work — confirm original vs. arrangement before distribution |

---

## Root-Level Scripts (Song Files)

These files live in the project root and predate the `songs/` directory organization.

| File | Title | Type | License | Notes |
|------|-------|------|---------|-------|
| `aqualung.py` | Aqualung | Original composition | ⚠️ VERIFY | Name shared with Jethro Tull (1971). If this is an original composition with no melodic borrowing, it is CC BY-SA 4.0. Confirm before publishing. |
| `axel_f.py` | Axel F | Cover | ⛔ COVER — EXCLUDED | Mechanical arrangement of Harold Faltermeyer's "Axel F" (1984, Beverley Hills Cop). Not CC. Personal use only. |
| `clocks.py` | Clocks | Cover | ⛔ COVER — EXCLUDED | Mechanical arrangement of Coldplay's "Clocks" (2002). Not CC. Personal use only. |
| `core_fable_melody.py` | Core Fable — Melody | Original | ✅ CC BY-SA 4.0 | Film score for Core Fable project (primary version) |
| `core_fable_melody_v3.py` | Core Fable — Melody v3 | Original | ✅ CC BY-SA 4.0 | Version 3 iteration |
| `core_fable_melody_v4.py` | Core Fable — Melody v4 | Original | ✅ CC BY-SA 4.0 | Version 4 iteration |
| `core_fable_score.py` | Core Fable — Full Score | Original | ✅ CC BY-SA 4.0 | Complete film score with all channels |
| `demo_effects.py` | Demo Effects | Original | ✅ CC BY-SA 4.0 | DSP and effects demonstration |
| `moonlight_waltz.py` | Moonlight Waltz | Original | ✅ CC BY-SA 4.0 | Original waltz in moonlight mood. Not a chip tune arrangement of Beethoven's Moonlight Sonata. |
| `the_mapmaker_score.py` | The Mapmaker — Score | Original | ✅ CC BY-SA 4.0 | Original film score |
| `the_mapmaker_score_v2.py` | The Mapmaker — Score v2 | Original | ✅ CC BY-SA 4.0 | Version 2 iteration |
| `voices_from_the_grid.py` | Voices from the Grid | Original | ✅ CC BY-SA 4.0 | Atmospheric original |

---

## songs/ambient/

| File | Title | License | Notes |
|------|-------|---------|-------|
| `stellar_drift.py` | Stellar Drift | ✅ CC BY-SA 4.0 | Original ambient composition |

---

## songs/classical/

All songs in this folder are arrangements of works whose **source compositions are in the public domain** (published before 1926 in the US). The ChipForge arrangement is original and licensed CC BY-SA 4.0.

| File | Source Work | Composer | Source Published | License |
|------|------------|---------|-----------------|---------|
| `001_clair_de_lune.py` | Clair de Lune | Debussy | 1905 | 🎓 PD Arrangement |
| `002_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `003_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `004_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `005_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `006_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `007_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `008_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `009_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `010_*.py` | TBD | TBD | Pre-1926 | 🎓 PD Arrangement |
| `011_satie_gymnopedie_1.py` | Gymnopédie No. 1 | Erik Satie | 1888 | 🎓 PD Arrangement |

> **Note:** Fill in rows 002-010 as songs are confirmed. Do not guess at source works —
> verify the exact composition and its publication date before marking PD.

---

## songs/edm/

52+ original EDM compositions. All are original works.

| Range | Count | License |
|-------|-------|---------|
| `001_neon_trance.py` → `052_voices_from_code.py` | 52+ | ✅ CC BY-SA 4.0 (all originals) |

For detailed track listings, see the individual files. All EDM tracks were composed from scratch
using ChipForge's numpy synthesis engine. None are arrangements of existing works.

---

## songs/electronic/

| File | Title | License | Notes |
|------|-------|---------|-------|
| `neon_rider.py` | Neon Rider | ✅ CC BY-SA 4.0 | Original electronic composition |

---

## songs/hiphop/

| File | License | Notes |
|------|---------|-------|
| `001_*.py` | ✅ CC BY-SA 4.0 | Original hip-hop composition |
| `002_*.py` | ✅ CC BY-SA 4.0 | Original hip-hop composition |

---

## songs/jazz/

| File | Title | License | Notes |
|------|-------|---------|-------|
| `midnight_blues.py` | Midnight Blues | ✅ CC BY-SA 4.0 | Original jazz composition. Generic genre title, no specific song referenced. |

---

## songs/laboratory/

| File | Title | License | Notes |
|------|-------|---------|-------|
| `cascade_protocol.py` | Cascade Protocol | ✅ CC BY-SA 4.0 | Original experimental composition |

---

## songs/originals/, songs/pop/, songs/rock/, songs/soundtrack/, songs/stranger-things/, songs/world/

All subdirectories contain original compositions or are under development. Update this catalog
as songs are added. Do not add a track without classifying its license.

---

## Excluded Covers: Full List

These files are **never** to be distributed under CC BY-SA 4.0. They are included in the
repository for personal use and reference only.

| File | Source Song | Original Artist | Year | Why Excluded |
|------|------------|-----------------|------|-------------|
| `axel_f.py` | Axel F | Harold Faltermeyer | 1984 | Mechanical arrangement, copyright held |
| `clocks.py` | Clocks | Coldplay | 2002 | Mechanical arrangement, copyright held |

These exclusions are documented in `CONTENT-LICENSE` under "Explicit Exclusions."

---

## Verification Checklist

Before distributing or publishing any song file:

- [ ] File is in this catalog
- [ ] License status is confirmed (not ⚠️ VERIFY)
- [ ] If 🎓 PD Arrangement: source work's publication year is documented and confirmed pre-1926
- [ ] If ✅ CC BY-SA 4.0: no melodic/harmonic borrowing from copyrighted works
- [ ] Attribution line is available for anyone who uses the work

---

## Updating This Catalog

When adding a new song:

1. Add an entry to the appropriate table in this file
2. Research the source: is it original? an arrangement of an existing song?
3. If arrangement: is the source published before 1926? If not, it is a cover → exclude from CC
4. Commit the catalog update in the same commit as the song file

When uncertain, mark as ⚠️ VERIFY and add a note. Do not assume CC coverage.
