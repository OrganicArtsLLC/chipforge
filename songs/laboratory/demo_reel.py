#!/usr/bin/env python3
"""
ChipForge Demo Reel
====================
Five short tracks showcasing the engine's range — different moods, scales,
instruments, and tempos.  Exports each track individually + a single
concatenated reel WAV.

Run:
    python demo_reel.py

Output:
    output/reel-1-midnight-chase.wav
    output/reel-2-crystal-waltz.wav
    output/reel-3-neon-drift.wav
    output/reel-4-iron-march.wav
    output/reel-5-ghost-signal.wav
    output/demo-reel-full.wav          ← all five back-to-back
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from src import (
    Song, Pattern, NoteEvent,
    render_song, export_wav, save_song,
)
from src.synth import SAMPLE_RATE

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

R = 0  # rest


# ═══════════════════════════════════════════════════════════════════════════
# Track 1: Midnight Chase — fast, dark, blues scale in E
# ═══════════════════════════════════════════════════════════════════════════

def track_midnight_chase() -> Song:
    """Aggressive 160 BPM blues chase — pulse leads + heavy kick."""
    BPM = 160
    song = Song(title="Midnight Chase", bpm=BPM, author="ChipForge")

    # E blues: E G A Bb B D
    # E4=64, G4=67, A4=69, Bb4=70, B4=71, D5=74, E5=76

    # ── Pattern A: opening riff ───────────────────────────────────────────
    pa = Pattern(name="Chase A", num_steps=16, num_channels=5, bpm=BPM)

    lead = [76, R,  74, 71, R,  70, 69, R,  67, R,  64, R,  67, 69, 70, R ]
    for s, n in enumerate(lead):
        if n: pa.set_note(0, s, NoteEvent(n, 0.85, 1, "pulse_lead"))

    bass = [52, R,  R,  R,  52, R,  R,  R,  55, R,  R,  R,  57, R,  R,  R ]
    for s, n in enumerate(bass):
        if n: pa.set_note(1, s, NoteEvent(n, 0.90, 2, "pulse_bass"))

    for s in range(0, 16, 2):
        pa.set_note(2, s, NoteEvent(60, 0.50, 1, "noise_hat"))

    for s in [0, 4, 8, 10, 12]:
        pa.set_note(3, s, NoteEvent(60, 0.92, 1, "noise_kick"))

    for s in [4, 12]:
        pa.set_note(4, s, NoteEvent(60, 0.78, 1, "noise_snare"))

    # ── Pattern B: call-and-response ──────────────────────────────────────
    pb = Pattern(name="Chase B", num_steps=16, num_channels=5, bpm=BPM)

    lead2 = [64, 67, 69, 70, 71, R,  74, 76, R,  R,  76, 74, 71, 70, 69, 67]
    for s, n in enumerate(lead2):
        if n: pb.set_note(0, s, NoteEvent(n, 0.82, 1, "chip_lead"))

    bass2 = [52, R,  R,  52, R,  R,  55, R,  R,  57, R,  R,  55, R,  52, R ]
    for s, n in enumerate(bass2):
        if n: pb.set_note(1, s, NoteEvent(n, 0.88, 2, "wave_bass"))

    for s in range(16):
        pb.set_note(2, s, NoteEvent(60, 0.40 if s % 2 else 0.55, 1, "noise_hat"))

    for s in [0, 6, 8, 14]:
        pb.set_note(3, s, NoteEvent(60, 0.90, 1, "noise_kick"))
    for s in [4, 12]:
        pb.set_note(4, s, NoteEvent(60, 0.75, 1, "noise_snare"))

    song.patterns = [pa, pb]
    song.sequence = [0, 0, 1, 0, 1, 0]
    return song


# ═══════════════════════════════════════════════════════════════════════════
# Track 2: Crystal Waltz — gentle, lydian mode in F, slower
# ═══════════════════════════════════════════════════════════════════════════

def track_crystal_waltz() -> Song:
    """Dreamy 90 BPM lydian melody — wavetable chimes + soft triangle bass."""
    BPM = 90
    song = Song(title="Crystal Waltz", bpm=BPM, author="ChipForge")

    # F lydian: F G A B C D E
    # F5=77, G5=79, A5=81, B5=83, C6=84, D6=86, E6=88

    # ── Pattern A: twinkle melody ─────────────────────────────────────────
    pa = Pattern(name="Crystal A", num_steps=16, num_channels=4, bpm=BPM)

    mel = [77, R,  81, R,  84, R,  83, R,  81, R,  79, R,  77, R,  R,  R ]
    for s, n in enumerate(mel):
        if n: pa.set_note(0, s, NoteEvent(n, 0.68, 2, "pulse_chime"))

    bass = [53, R,  R,  R,  R,  R,  R,  R,  57, R,  R,  R,  R,  R,  R,  R ]
    for s, n in enumerate(bass):
        if n: pa.set_note(1, s, NoteEvent(n, 0.75, 4, "wave_bass"))

    # gentle hat on every beat (every 4 steps)
    for s in range(0, 16, 4):
        pa.set_note(2, s, NoteEvent(60, 0.30, 1, "noise_hat"))

    # soft kick on beat 1
    pa.set_note(3, 0, NoteEvent(60, 0.60, 1, "noise_kick"))
    pa.set_note(3, 8, NoteEvent(60, 0.55, 1, "noise_kick"))

    # ── Pattern B: rising arpeggios ───────────────────────────────────────
    pb = Pattern(name="Crystal B", num_steps=16, num_channels=4, bpm=BPM)

    arp = [77, 81, 84, 88, 84, 81, 77, R,  79, 83, 86, R,  84, 81, 79, 77]
    for s, n in enumerate(arp):
        if n: pb.set_note(0, s, NoteEvent(n, 0.60, 1, "gb_bell_wave"))

    bass2 = [53, R,  R,  R,  55, R,  R,  R,  57, R,  R,  R,  53, R,  R,  R ]
    for s, n in enumerate(bass2):
        if n: pb.set_note(1, s, NoteEvent(n, 0.72, 3, "sine_bass"))

    for s in range(0, 16, 4):
        pb.set_note(2, s, NoteEvent(60, 0.28, 1, "noise_hat"))
    pb.set_note(3, 0, NoteEvent(60, 0.55, 1, "noise_kick"))

    song.patterns = [pa, pb]
    song.sequence = [0, 0, 1, 0, 1, 1]
    return song


# ═══════════════════════════════════════════════════════════════════════════
# Track 3: Neon Drift — chill synthwave, dorian in A, mid-tempo
# ═══════════════════════════════════════════════════════════════════════════

def track_neon_drift() -> Song:
    """Smooth 110 BPM dorian groove — sine pad + saw lead, riding bass."""
    BPM = 110
    song = Song(title="Neon Drift", bpm=BPM, author="ChipForge")

    # A dorian: A B C D E F# G
    # A4=69, B4=71, C5=72, D5=74, E5=76, F#5=78, G5=79, A5=81

    # ── Pattern A: pad + melody ───────────────────────────────────────────
    pa = Pattern(name="Drift A", num_steps=16, num_channels=5, bpm=BPM)

    mel = [76, R,  78, 79, R,  78, 76, R,  74, R,  72, R,  74, 76, R,  R ]
    for s, n in enumerate(mel):
        if n: pa.set_note(0, s, NoteEvent(n, 0.75, 1, "saw_lead"))

    # warm pad chord tones (held long)
    pad = [69, R,  R,  R,  R,  R,  R,  R,  72, R,  R,  R,  R,  R,  R,  R ]
    for s, n in enumerate(pad):
        if n: pa.set_note(1, s, NoteEvent(n, 0.55, 8, "sine_pad"))

    bass = [57, R,  R,  57, R,  R,  60, R,  R,  R,  62, R,  R,  60, R,  R ]
    for s, n in enumerate(bass):
        if n: pa.set_note(2, s, NoteEvent(n, 0.85, 2, "pulse_bass"))

    for s in range(0, 16, 2):
        pa.set_note(3, s, NoteEvent(60, 0.42, 1, "noise_hat"))
    for s in [0, 8]:
        pa.set_note(4, s, NoteEvent(60, 0.80, 1, "noise_kick"))
    for s in [4, 12]:
        pa.set_note(4, s, NoteEvent(60, 0.65, 1, "noise_snare"))

    # ── Pattern B: breakdown — just bass + hats ──────────────────────────
    pb = Pattern(name="Drift B", num_steps=16, num_channels=5, bpm=BPM)

    bass2 = [57, R,  57, R,  60, R,  R,  62, R,  R,  60, R,  57, R,  R,  R ]
    for s, n in enumerate(bass2):
        if n: pb.set_note(2, s, NoteEvent(n, 0.80, 2, "wave_bass"))

    for s in range(16):
        pb.set_note(3, s, NoteEvent(60, 0.35 if s % 2 else 0.50, 1, "noise_hat"))
    pb.set_note(4, 0, NoteEvent(60, 0.75, 1, "noise_kick"))
    pb.set_note(4, 12, NoteEvent(60, 0.60, 1, "noise_snare"))

    # ── Pattern C: return with arpeggiated lead ──────────────────────────
    pc = Pattern(name="Drift C", num_steps=16, num_channels=5, bpm=BPM)

    arp = [69, 72, 76, 72, 69, 74, 78, 74, 69, 72, 76, 79, 81, 79, 76, 72]
    for s, n in enumerate(arp):
        if n: pc.set_note(0, s, NoteEvent(n, 0.68, 1, "pulse_arp"))

    for s, n in enumerate(bass):
        if n: pc.set_note(2, s, NoteEvent(n, 0.82, 2, "pulse_bass"))
    for s in range(0, 16, 2):
        pc.set_note(3, s, NoteEvent(60, 0.45, 1, "noise_hat"))
    for s in [0, 8]:
        pc.set_note(4, s, NoteEvent(60, 0.80, 1, "noise_kick"))
    for s in [4, 12]:
        pc.set_note(4, s, NoteEvent(60, 0.65, 1, "noise_snare"))

    song.patterns = [pa, pb, pc]
    song.sequence = [0, 0, 1, 2, 0, 2]
    return song


# ═══════════════════════════════════════════════════════════════════════════
# Track 4: Iron March — heavy, phrygian in E, march tempo
# ═══════════════════════════════════════════════════════════════════════════

def track_iron_march() -> Song:
    """Stomping 130 BPM phrygian war march — wide pulse + heavy drums."""
    BPM = 130
    song = Song(title="Iron March", bpm=BPM, author="ChipForge")

    # E phrygian: E F G A B C D
    # E4=64, F4=65, G4=67, A4=69, B4=71, C5=72, D5=74, E5=76

    # ── Pattern A: militant riff ──────────────────────────────────────────
    pa = Pattern(name="March A", num_steps=16, num_channels=5, bpm=BPM)

    mel = [76, 76, R,  74, 72, R,  71, R,  69, 67, R,  65, 64, R,  64, R ]
    for s, n in enumerate(mel):
        if n: pa.set_note(0, s, NoteEvent(n, 0.88, 1, "pulse_wide"))

    bass = [52, R,  52, R,  R,  R,  53, R,  52, R,  R,  R,  52, 52, R,  R ]
    for s, n in enumerate(bass):
        if n: pa.set_note(1, s, NoteEvent(n, 0.92, 2, "saw_bass"))

    # march beat: heavy kick + rim
    for s in [0, 2, 4, 8, 10, 12]:
        pa.set_note(3, s, NoteEvent(60, 0.95, 1, "noise_kick"))
    for s in [6, 14]:
        pa.set_note(4, s, NoteEvent(60, 0.80, 1, "noise_snare"))
    # hats
    for s in range(16):
        pa.set_note(2, s, NoteEvent(60, 0.38, 1, "noise_hat"))

    # ── Pattern B: power chord stabs ─────────────────────────────────────
    pb = Pattern(name="March B", num_steps=16, num_channels=5, bpm=BPM)

    # E power chord + F power chord stabs
    stab = [64, R,  R,  R,  64, 64, R,  R,  65, R,  R,  R,  65, 65, R,  R ]
    for s, n in enumerate(stab):
        if n: pb.set_note(0, s, NoteEvent(n, 0.90, 2, "chip_lead"))
    # fifth above
    stab5 = [71, R,  R,  R,  71, 71, R,  R,  72, R,  R,  R,  72, 72, R,  R ]
    for s, n in enumerate(stab5):
        if n: pb.set_note(1, s, NoteEvent(n, 0.82, 2, "pulse_lead"))

    for s in [0, 4, 5, 8, 12, 13]:
        pb.set_note(3, s, NoteEvent(60, 0.95, 1, "noise_kick"))
    for s in [6, 14]:
        pb.set_note(4, s, NoteEvent(60, 0.82, 1, "noise_snare"))
    for s in range(16):
        pb.set_note(2, s, NoteEvent(60, 0.40, 1, "noise_hat"))

    song.patterns = [pa, pb]
    song.sequence = [0, 0, 1, 0, 1, 1]
    return song


# ═══════════════════════════════════════════════════════════════════════════
# Track 5: Ghost Signal — eerie, whole-tone scale, sparse, slow
# ═══════════════════════════════════════════════════════════════════════════

def track_ghost_signal() -> Song:
    """Haunting 75 BPM whole-tone ambience — GB organ + sine + space."""
    BPM = 75
    song = Song(title="Ghost Signal", bpm=BPM, author="ChipForge")

    # C whole tone: C D E F# G# A#
    # C5=72, D5=74, E5=76, F#5=78, G#5=80, A#5=82, C6=84

    # ── Pattern A: drifting tones ─────────────────────────────────────────
    pa = Pattern(name="Ghost A", num_steps=16, num_channels=4, bpm=BPM)

    # sparse melody, lots of space
    mel = [72, R,  R,  R,  76, R,  R,  80, R,  R,  R,  82, R,  R,  R,  R ]
    for s, n in enumerate(mel):
        if n: pa.set_note(0, s, NoteEvent(n, 0.55, 3, "gb_organ"))

    low = [60, R,  R,  R,  R,  R,  R,  R,  64, R,  R,  R,  R,  R,  R,  R ]
    for s, n in enumerate(low):
        if n: pa.set_note(1, s, NoteEvent(n, 0.50, 6, "sine_pad"))

    # almost no drums — just ghost taps
    for s in [0, 12]:
        pa.set_note(2, s, NoteEvent(60, 0.25, 1, "noise_hat"))
    pa.set_note(3, 8, NoteEvent(60, 0.40, 1, "noise_rim"))

    # ── Pattern B: descending unease ──────────────────────────────────────
    pb = Pattern(name="Ghost B", num_steps=16, num_channels=4, bpm=BPM)

    mel2 = [84, R,  R,  82, R,  R,  80, R,  R,  78, R,  R,  76, R,  74, 72]
    for s, n in enumerate(mel2):
        if n: pb.set_note(0, s, NoteEvent(n, 0.50, 2, "gb_bell_wave"))

    low2 = [66, R,  R,  R,  R,  R,  R,  R,  R,  R,  R,  R,  60, R,  R,  R ]
    for s, n in enumerate(low2):
        if n: pb.set_note(1, s, NoteEvent(n, 0.45, 8, "sine_bass"))

    for s in [4, 10]:
        pb.set_note(2, s, NoteEvent(60, 0.22, 1, "noise_hat"))

    # ── Pattern C: signal pulse ───────────────────────────────────────────
    pc = Pattern(name="Ghost C", num_steps=16, num_channels=4, bpm=BPM)

    pulse = [72, R,  72, R,  R,  R,  76, R,  R,  R,  R,  R,  R,  R,  R,  R ]
    for s, n in enumerate(pulse):
        if n: pc.set_note(0, s, NoteEvent(n, 0.62, 1, "pulse_chime"))

    low3 = [60, R,  R,  R,  R,  R,  R,  R,  R,  R,  R,  R,  R,  R,  R,  R ]
    for s, n in enumerate(low3):
        if n: pc.set_note(1, s, NoteEvent(n, 0.48, 8, "sine_pad"))

    for s in [0, 2]:
        pc.set_note(2, s, NoteEvent(60, 0.30, 1, "noise_hat"))

    song.patterns = [pa, pb, pc]
    song.sequence = [0, 0, 1, 2, 0, 1]
    return song


# ═══════════════════════════════════════════════════════════════════════════
# Main — build all tracks, export individually + concatenated reel
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("╔══════════════════════════════════════╗")
    print("║       ChipForge  Demo  Reel          ║")
    print("╚══════════════════════════════════════╝")
    print()

    tracks = [
        ("reel-1-midnight-chase",  track_midnight_chase),
        ("reel-2-crystal-waltz",   track_crystal_waltz),
        ("reel-3-neon-drift",      track_neon_drift),
        ("reel-4-iron-march",      track_iron_march),
        ("reel-5-ghost-signal",    track_ghost_signal),
    ]

    all_audio = []
    # Silence gap between tracks (1.2 seconds)
    gap = np.zeros((int(SAMPLE_RATE * 1.2), 2), dtype=np.float32)

    for filename, builder in tracks:
        song = builder()
        dur = song.total_duration_sec()
        print(f"  ♪  {song.title:<22s}  {song.bpm:>5.0f} BPM   {dur:>5.1f}s")

        audio = render_song(song)
        wav_path = OUTPUT / f"{filename}.wav"
        export_wav(audio, wav_path)
        print(f"     → {wav_path}")

        all_audio.append(audio)
        all_audio.append(gap)

    # ── Concatenated reel ─────────────────────────────────────────────────
    print()
    full = np.concatenate(all_audio, axis=0)

    # Normalize the full reel
    peak = np.max(np.abs(full))
    if peak > 0:
        full = full * (0.92 / peak)

    reel_path = OUTPUT / "demo-reel-full.wav"
    export_wav(full, reel_path)
    total_dur = len(full) / SAMPLE_RATE
    print(f"  ★  Full reel: {reel_path}  ({total_dur:.1f}s)")

    # ── Playback ──────────────────────────────────────────────────────────
    print()
    try:
        from src.mixer import play_audio
        print("Playing full reel … ", end="", flush=True)
        play_audio(full, SAMPLE_RATE)
        print("done.")
    except Exception as exc:
        print(f"Playback skipped ({exc}).")
        print(f"  Open the WAV directly: {reel_path.resolve()}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
