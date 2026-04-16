# Contributing to ChipForge

Thank you for your interest in contributing to ChipForge.

**Organization:** OA LLC  
**License:** See [LICENSE](LICENSE) and [CONTENT-LICENSE](CONTENT-LICENSE)

---

## Quick Start

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
.venv/bin/python3 tests/test_engine_comprehensive.py
.venv/bin/python3 tests/test_orchestral_presets.py

# Render a song (background — takes 60–290s)
./render.sh songs/edm/010_strobe_v5.py
```

## Development Guidelines

- **Python 3.11+** — use `list[T]`, `dict[K,V]`, `X | None`
- **No external audio libs** — numpy only (no pydub, librosa, pygame)
- **Type hints** on all function signatures
- **Max line length:** 100 characters
- See [CLAUDE.md](CLAUDE.md) for the full architecture and composition protocol

## Pre-commit Hook

The pre-commit hook is installed at `.githooks/pre-commit`. Activate it once:

```bash
git config core.hooksPath .githooks
```

It checks for hardcoded secrets and IP credential patterns before every commit.

## Commit Format

```
<type>: <subject>
```

Types: `feat:`, `fix:`, `docs:`, `perf:`, `refactor:`

## Reporting Issues

Open a GitHub Issue with:
- Python version (`python3 --version`)
- Error message (full traceback)
- Minimal reproduction case

## Security

Report security issues privately via GitHub Security Advisories — do **not** open a public issue.
