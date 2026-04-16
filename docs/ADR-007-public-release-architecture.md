# ADR-007: Public Release Architecture — History-Clean, Layered Privacy

**Status:** Accepted  
**Date:** 2026-04-12  
**Author:** Joshua Ayson / OA LLC

---

## Context

ChipForge contains two classes of content:

1. **Public content** — original song scripts with public-domain melodies, the synthesis engine, 36+ instrument presets, all source code, documentation, and tooling. These are the creative and technical contribution of this project — shareable under GPL-3.0.

2. **Private content** — song scripts that implement cover arrangements of copyrighted recordings (EDM tracks, pop songs, rock songs, soundtracks). Releasing these publicly would create IP liability even though the output is chip tune synthesis, not a recording.

The goal is to make ChipForge a public, forkable project while protecting all derivative compositions from public exposure.

---

## Decision

Adopt a **three-layer privacy architecture** and perform a one-time history clean.

### Layer 1: Working-Tree Privacy (`.gitignore`)

All derivative song scripts are gitignored. The `.gitignore` covers:

- `songs/edm/005_*` through `songs/edm/051_*` (cover arrangements)
- `songs/pop/`, `songs/rock/`, `songs/stranger_things/` (entire directories)
- `songs/soundtrack/002_*` and above (non-original soundtrack scripts)
- `CLAUDE.md`, `.github/copilot-instructions.md` (agent-private instructions)
- `docs/AGENT-COMPOSITION*.md`, `docs/ADR-003-composition*.md` (agent-private composition bible)
- `publish-public.sh` (operational tooling)

Files in these paths exist on disk for local development but **never enter git**.

### Layer 2: History Clean (`git filter-repo`)

On 2026-04-12, `git filter-repo --invert-paths --paths-from-file /tmp/chipforge-purge-paths.txt` was run to remove all 97 private paths from the **entire commit history**. This rewrote 103 commits and 71 remain in the public history.

The original commit hash `3a12728` (before filter-repo) became `942c674` (after). The repo's history now contains only engine code, original songs, and public documentation.

**To re-run history clean if needed (emergency rollback of an accidental commit):**
```bash
git log --all --name-only --format="" | sort -u | grep -E \
  '^songs/edm/0(0[5-9]|[1-9][0-9])|^songs/pop/|^songs/rock/|^songs/stranger_things/' \
  > /tmp/cf-purge.txt
git filter-repo --invert-paths --paths-from-file /tmp/cf-purge.txt --force
```

### Layer 3: Pre-Commit Hook (`.git/hooks/pre-commit`)

A pre-commit hook blocks any staged commit that includes private paths. It runs before every commit and exits 1 if private files are staged.

The hook was installed 2026-04-12 and is the **last line of defense** against accidental disclosure.

---

## What Is Public

| Category | Public | 
|----------|--------|
| `src/` — synthesis engine | ✅ |
| `api/` — FastAPI REST interface | ✅ |
| `tests/` — all test suites | ✅ |
| `docs/ADR-001`, `ADR-002`, `ADR-004` through `ADR-007` | ✅ |
| `songs/edm/001_` – `004_` (originals) | ✅ |
| `songs/edm/052_*` (originals) | ✅ |
| `songs/ambient/`, `songs/classical/`, `songs/electronic/` | ✅ |
| `songs/hiphop/`, `songs/jazz/`, `songs/laboratory/`, `songs/originals/` | ✅ |
| `songs/soundtrack/001_final_boss.py` | ✅ |
| `README.md`, `requirements.txt`, `render.sh`, `demo.py` | ✅ |

---

## What Remains Private (On-Disk Only)

| Category | Why Private |
|----------|-------------|
| `songs/edm/005_` – `051_*` | Cover arrangements of copyrighted recordings |
| `songs/pop/`, `songs/rock/`, `songs/stranger_things/` | Cover arrangements |
| `songs/soundtrack/002_*` and above | Some may reference licensed IP |
| `CLAUDE.md` | Agent composition system — internal tooling |
| `docs/ADR-003-composition-bible.md` | Agent composition guide — internal |
| `docs/AGENT-COMPOSITION-GUIDE.md` | Agent composition guide — internal |

---

## On-Demand Song Publishing

Individual songs can be published to the repo's `songs/published/` directory via the `tools/publish-song.sh` script (future — create as needed). The workflow:

1. Verify song is an original composition (no recognizable melody from a copyrighted work)
2. Run `tools/publish-song.sh songs/edm/052_my_original.py`
3. Script copies the file to `songs/published/`, adds git tracking entry, and commits

---

## Consequences

- ChipForge is now a public, forkable repository on GitHub
- All derivative cover songs remain private (local disk only)
- The engine, tooling, and original compositions are a genuine open-source contribution
- Pre-commit hook provides persistent safety; filter-repo is the one-time cleanup
- History has been rewritten; collaborators must `git clone` fresh (no existing collaborators)

---

## Related

- `ADR-001`: Initial synthesis architecture
- `ADR-002`: Quality, speed, web roadmap
- `ADR-004`: AI synthesis frontiers
- History-clean input file: `/tmp/chipforge-purge-paths.txt` (ephemeral, not in git)
