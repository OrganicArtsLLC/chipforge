"""
ChipForge Version Tracking
===========================
Build ID and version metadata for tracking engine changes across renders.
"""

from __future__ import annotations

import os
import subprocess

__version__ = "0.4.0"

# Changelog:
# 0.1.0 — Initial engine (Game Boy APU synth, basic mixer)
# 0.2.0 — 36 instrument presets, Schroeder reverb, delay, chorus
# 0.3.0 — Enhanced drums, filtered synth, additive synthesis, vibrato, pitch sweep
# 0.4.0 — FFT convolution reverb, scipy filters, effects module, test suite


def get_build_id() -> str:
    """Get short git hash as build identifier."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_version_string() -> str:
    """Full version string for display and metadata."""
    return f"ChipForge v{__version__} ({get_build_id()})"


def get_version_dict() -> dict:
    """Version metadata as dict (for JSON serialization)."""
    return {
        "engine": "ChipForge",
        "version": __version__,
        "build": get_build_id(),
    }
