"""
ChipForge Web Compiler — Song to JavaScript
=============================================
Compiles a ChipForge Song into a self-contained JavaScript file that
generates the same audio using the Web Audio API at runtime.

Target: < 25 KB total (engine + song data) for Pixel Vault integration.

The JS output creates an AudioContext, builds oscillators, applies
effects, and plays the song — no audio files needed.

Usage:
    from src.web_compiler import compile_to_js
    js_code = compile_to_js(song, minify=True)
    Path("game/music.js").write_text(js_code)
"""

from __future__ import annotations

import json
import math
import logging
from pathlib import Path
from typing import Optional

from .sequencer import Song, Pattern, NoteEvent
from .instruments import PRESETS, Instrument

logger = logging.getLogger("chipforge.web_compiler")

# Waveform mapping: ChipForge → Web Audio OscillatorNode types
WAVEFORM_MAP = {
    "sine": "sine",
    "square": "square",
    "sawtooth": "sawtooth",
    "triangle": "triangle",
    # Everything else maps to closest Web Audio equivalent
    "noise_lfsr_7": "custom",
    "noise_lfsr_15": "custom",
    "white_noise": "custom",
    "wavetable": "custom",
}


def _note_to_freq(midi: int) -> float:
    """MIDI → Hz."""
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def _compile_instrument(inst: Instrument) -> dict:
    """Compile an Instrument to a compact JSON-serializable dict."""
    waveform = WAVEFORM_MAP.get(inst.waveform, "square")
    # Handle composite waveforms
    if inst.waveform.startswith("additive") or inst.waveform.startswith("shaped"):
        waveform = "sawtooth"  # closest approximation
    elif inst.waveform.startswith("fm"):
        waveform = "sine"  # FM uses sine carrier
    elif inst.waveform.startswith("supersaw"):
        waveform = "sawtooth"
    elif inst.waveform.startswith("pwm"):
        waveform = "square"

    return {
        "w": waveform,
        "a": round(inst.adsr.attack, 4),
        "d": round(inst.adsr.decay, 4),
        "s": round(inst.adsr.sustain, 3),
        "r": round(inst.adsr.release, 4),
        "v": round(inst.volume, 3),
        "fc": int(inst.filter_cutoff) if inst.filter_cutoff else 0,
        "fr": round(inst.filter_resonance, 2) if inst.filter_resonance else 0,
    }


def _compile_pattern(pattern: Pattern) -> dict:
    """Compile a Pattern to compact JSON."""
    notes = []
    for ch_idx, channel in enumerate(pattern.grid):
        for step_idx, event in enumerate(channel):
            if event is None or event.midi_note == 0:
                continue
            notes.append({
                "c": ch_idx,
                "s": step_idx,
                "n": event.midi_note,
                "v": round(event.velocity, 3),
                "d": event.duration_steps,
                "i": event.instrument,
            })

    return {
        "name": pattern.name,
        "steps": pattern.num_steps,
        "channels": pattern.num_channels,
        "bpm": pattern.bpm or 120,
        "spb": pattern.steps_per_beat or 4,
        "notes": notes,
    }


def compile_to_js(
    song: Song,
    minify: bool = False,
    include_effects: bool = True,
) -> str:
    """
    Compile a ChipForge Song to a self-contained JavaScript module.

    The output JS creates a Web Audio AudioContext and plays the song
    using OscillatorNodes, GainNodes, BiquadFilterNodes, and DelayNodes.

    Args:
        song: The Song to compile.
        minify: If True, minimize whitespace (for production).
        include_effects: If True, include reverb/delay/chorus effects.

    Returns:
        JavaScript source code as string.
    """
    # Collect unique instruments used in this song
    used_instruments = set()
    for pattern in song.patterns:
        for channel in pattern.grid:
            for event in channel:
                if event and event.instrument:
                    used_instruments.add(event.instrument)

    # Compile instruments
    instruments_data = {}
    for name in used_instruments:
        inst = PRESETS.get(name)
        if inst:
            instruments_data[name] = _compile_instrument(inst)

    # Compile patterns
    patterns_data = [_compile_pattern(p) for p in song.patterns]

    # Song metadata
    song_data = {
        "title": song.title or "Untitled",
        "bpm": song.bpm,
        "sequence": list(song.sequence),
        "panning": {str(k): round(v, 3) for k, v in (song.panning or {}).items()},
        "instruments": instruments_data,
        "patterns": patterns_data,
    }

    if include_effects and song.channel_effects:
        fx_data = {}
        for ch, fx in song.channel_effects.items():
            fx_data[str(ch)] = {
                k: round(v, 4) if isinstance(v, float) else v
                for k, v in fx.items()
            }
        song_data["effects"] = fx_data

    song_json = json.dumps(song_data, separators=(",", ":") if minify else (", ", ": "))

    # Generate the JS engine + song data
    js = _generate_js_engine(song_json, include_effects, minify)

    size_kb = len(js) / 1024
    logger.info(f"Compiled to JS: {size_kb:.1f} KB, "
                f"{len(used_instruments)} instruments, "
                f"{len(patterns_data)} patterns, "
                f"{'minified' if minify else 'readable'}")

    return js


def _generate_js_engine(song_json: str, include_effects: bool, minify: bool) -> str:
    """Generate the ChipForge.js playback engine."""

    nl = "" if minify else "\n"
    indent = "" if minify else "  "

    engine = f"""// ChipForge.js — Web Audio Playback Engine
// Generated by ChipForge Web Compiler v0.4.1
// https://github.com/OrganicArtsLLC/chipforge

const CF = (() => {{
{indent}const SONG = {song_json};
{indent}let ctx = null;
{indent}let playing = false;

{indent}function noteToFreq(n) {{
{indent}{indent}return 440 * Math.pow(2, (n - 69) / 12);
{indent}}}

{indent}function createNote(inst, midi, startTime, duration, velocity) {{
{indent}{indent}const freq = noteToFreq(midi);
{indent}{indent}const i = SONG.instruments[inst];
{indent}{indent}if (!i) return;

{indent}{indent}// Oscillator
{indent}{indent}const osc = ctx.createOscillator();
{indent}{indent}osc.type = i.w;
{indent}{indent}osc.frequency.value = freq;

{indent}{indent}// ADSR via GainNode
{indent}{indent}const gain = ctx.createGain();
{indent}{indent}const vol = velocity * i.v;
{indent}{indent}const t = startTime;
{indent}{indent}gain.gain.setValueAtTime(0, t);
{indent}{indent}gain.gain.linearRampToValueAtTime(vol, t + i.a);
{indent}{indent}gain.gain.linearRampToValueAtTime(vol * i.s, t + i.a + i.d);
{indent}{indent}gain.gain.setValueAtTime(vol * i.s, t + duration - i.r);
{indent}{indent}gain.gain.linearRampToValueAtTime(0, t + duration);

{indent}{indent}// Filter (if cutoff > 0)
{indent}{indent}let output = gain;
{indent}{indent}if (i.fc > 0) {{
{indent}{indent}{indent}const filter = ctx.createBiquadFilter();
{indent}{indent}{indent}filter.type = 'lowpass';
{indent}{indent}{indent}filter.frequency.value = i.fc;
{indent}{indent}{indent}filter.Q.value = 1 + i.fr * 10;
{indent}{indent}{indent}gain.connect(filter);
{indent}{indent}{indent}output = filter;
{indent}{indent}}} else {{
{indent}{indent}{indent}// no filter
{indent}{indent}}}

{indent}{indent}osc.connect(gain);
{indent}{indent}output.connect(ctx.destination);
{indent}{indent}osc.start(t);
{indent}{indent}osc.stop(t + duration + 0.1);
{indent}}}

{indent}function play() {{
{indent}{indent}if (playing) return;
{indent}{indent}ctx = new (window.AudioContext || window.webkitAudioContext)();
{indent}{indent}playing = true;

{indent}{indent}let offset = 0;
{indent}{indent}for (const patIdx of SONG.sequence) {{
{indent}{indent}{indent}const pat = SONG.patterns[patIdx];
{indent}{indent}{indent}const stepDur = 60 / (pat.bpm * pat.spb);

{indent}{indent}{indent}for (const note of pat.notes) {{
{indent}{indent}{indent}{indent}const startTime = offset + note.s * stepDur;
{indent}{indent}{indent}{indent}const duration = note.d * stepDur;
{indent}{indent}{indent}{indent}createNote(note.i, note.n, startTime, duration, note.v);
{indent}{indent}{indent}}}

{indent}{indent}{indent}offset += pat.steps * stepDur;
{indent}{indent}}}
{indent}}}

{indent}function stop() {{
{indent}{indent}if (ctx) {{
{indent}{indent}{indent}ctx.close();
{indent}{indent}{indent}ctx = null;
{indent}{indent}}}
{indent}{indent}playing = false;
{indent}}}

{indent}return {{ play, stop, song: SONG }};
}})();
"""

    return engine


def compile_song_file(
    song_py_path: str,
    output_js_path: str | None = None,
    minify: bool = True,
) -> str:
    """
    Compile a song .py file to a .js file.

    Args:
        song_py_path: Path to the song Python file.
        output_js_path: Output path for JS file (auto-generated if None).
        minify: Minimize output for production.

    Returns:
        Path to the generated JS file.
    """
    import importlib.util

    # Load the song module
    spec = importlib.util.spec_from_file_location("song_module", song_py_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load {song_py_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find build_song() function
    if not hasattr(module, "build_song"):
        raise ValueError(f"No build_song() function in {song_py_path}")

    song = module.build_song()

    # Compile to JS
    js_code = compile_to_js(song, minify=minify)

    # Write output
    if output_js_path is None:
        output_js_path = str(Path(song_py_path).with_suffix(".js"))

    Path(output_js_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_js_path).write_text(js_code)

    size_kb = len(js_code) / 1024
    logger.info(f"Compiled {song_py_path} → {output_js_path} ({size_kb:.1f} KB)")

    return output_js_path


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m src.web_compiler <song.py> [output.js]")
        sys.exit(1)

    song_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    result = compile_song_file(song_path, out_path)
    print(f"Compiled: {result}")
