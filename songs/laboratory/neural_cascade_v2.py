"""
Neural Cascade v2 — Deep Rave Edition
=======================================
A reimagining of Neural Cascade as a warm, rich EDM/rave piece.

PHILOSOPHY: Every note has SUSTAIN. Every channel has EFFECTS.
No staccato chirps. No dry signals. Think 3AM warehouse rave
with a proper sound system — everything smooth, everything wide.

SOUND DESIGN IMPROVEMENTS OVER v1:
  - ALL melodic notes get duration_steps >= 2 (no 1-step chirps)
  - ALL channels get reverb or delay (nothing dry)
  - Velocities capped at 0.85 max (prevents digital clipping)
  - Warmer instruments: saw_filtered, pulse_warm, saw_dark
  - Snare = noise_clap (more body) + longer decay via duration
  - Bass = bass_growl (richer harmonics than bass_sub)
  - Pad layer present in EVERY section (warmth floor)
  - Master reverb 0.15 + master delay 0.08 (room coherence)

Key: D minor (i → bVI → bVII → i) — same DNA as v1
BPM: 140 (slightly slower = more groove, less frantic)
Channels: 7
  0 - Kick (kick_deep)
  1 - Snare/Clap (noise_clap — fatter than snare_tight)
  2 - Hi-hat (hat_crisp + hat_open_shimmer — alternating)
  3 - Bass (bass_growl — richer harmonics)
  4 - Lead (saw_filtered — warm and present)
  5 - Chords/Pad (pad_lush — sustained warmth)
  6 - Arp (pulse_warm — smooth, not plucky)

Structure (~66 seconds):
  [0-7s]    ATMOSPHERE  4 bars  — Pad wash + filtered arp + soft hats
  [7-14s]   RISE        4 bars  — Kick enters, bass slides in, snare roll
  [14-28s]  DROP 1      8 bars  — Full groove, the hook, everything vibing
  [28-35s]  BREATHE     4 bars  — Strip to pad + arp + soft kick
  [35-49s]  DROP 2      8 bars  — Everything back + counter-melody, peak
  [49-55s]  CRESCENDO   4 bars  — Final build, velocity swell
  [55-66s]  RESOLVE     6 bars  — Gentle decay, return to atmosphere
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 140
SPB = 4
BAR = 16
NUM_CH = 7

# ── Helpers ──────────────────────────────────────────────────────────────

def hz(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12.0))

def freq_to_midi(freq: float) -> int:
    if freq <= 0:
        return 0
    return round(12 * math.log2(freq / 440.0) + 69)

def note(inst: str, midi: int, vel: float = 0.70, dur: int = 2) -> NoteEvent:
    """Create a note. DEFAULT duration = 2 steps (smooth, not staccato)."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 1), instrument=inst)

def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]

# ── Instrument Assignments (warm palette) ────────────────────────────────
KICK    = 'kick_deep'
SNARE   = 'noise_clap'       # Fatter than snare_tight
HAT_CL  = 'hat_crisp'
HAT_OP  = 'hat_open_shimmer'
BASS    = 'bass_growl'        # Rich harmonics
LEAD    = 'saw_filtered'      # Warm, filtered, smooth
PAD     = 'pad_lush'          # Sustained warmth
ARP     = 'pulse_warm'        # Smooth pulse, not plucky
LEAD_B  = 'saw_dark'          # Counter-melody: dark and moody

# ── D minor note constants ──────────────────────────────────────────────
# D minor scale: D E F G A Bb C
D2=38; F2=41; G2=43; A2=45; Bb2=46; C3=48; D3=50; E3=52; F3=53
G3=55; A3=57; Bb3=58; C4=60; D4=62; E4=64; F4=65; G4=67; A4=69
Bb4=70; C5=72; D5=74; E5=76; F5=77; G5=79; A5=81; Bb5=82; D6=86

# Chord voicings: Dm → Bb → C → Dm (i → bVI → bVII → i)
CHORDS = [
    (D4, F4, A4),      # Dm
    (Bb3, D4, F4),     # Bb
    (C4, E4, G4),      # C
    (D4, F4, A4),      # Dm
]

BASS_ROOTS = [D2, Bb2, C3, D2]

# THE HOOK — same contour as v1 but placed with proper durations
# Format: (beat_offset, midi_note, velocity, duration_steps)
HOOK = [
    # Call: ascending D→F→G→A
    (0,  D5,  0.78, 3),
    (3,  F5,  0.70, 2),
    (5,  G5,  0.74, 2),
    (7,  A5,  0.82, 3),
    # Response: descending, breathing
    (10, A5,  0.68, 2),
    (12, G5,  0.72, 2),
    (14, F5,  0.65, 3),
    # Repeat with Bb tension
    (17, D5,  0.78, 3),
    (20, F5,  0.70, 2),
    (22, G5,  0.74, 2),
    (24, A5,  0.82, 2),
    # Peak: Bb → A → resolve to D
    (26, Bb5, 0.80, 3),
    (29, A5,  0.72, 2),
    (31, D5,  0.75, 4),
]

# Counter-melody for Drop 2 — weaves around the hook
COUNTER = [
    (1,  A4,  0.55, 3),
    (4,  G4,  0.52, 2),
    (7,  F4,  0.58, 3),
    (11, E4,  0.50, 2),
    (14, D4,  0.55, 4),
    (18, F4,  0.52, 2),
    (21, G4,  0.55, 3),
    (25, A4,  0.58, 2),
    (28, Bb4, 0.55, 3),
    (31, A4,  0.52, 4),
]


# ── Groove Patterns ──────────────────────────────────────────────────────

def four_on_floor(g: list, bar: int, vel: float = 0.78) -> None:
    """Standard EDM kick: beats 1, 2, 3, 4."""
    bs = bar * BAR
    for beat in range(4):
        g[0][bs + beat * 4] = note(KICK, 36, vel, 2)


def rave_hats(g: list, bar: int, vel: float = 0.45, swing: bool = False) -> None:
    """Smooth hat pattern: 8ths with open hat on offbeats.
    Alternating closed/open creates width and groove."""
    bs = bar * BAR
    for step in range(0, BAR, 2):  # 8th notes
        if step % 4 == 0:
            # On-beat: closed hat, softer
            g[2][bs + step] = note(HAT_CL, 42, vel * 0.85, 2)
        else:
            # Off-beat: open hat, slightly louder (the groove)
            g[2][bs + step] = note(HAT_OP, 46, vel, 3)


def fat_snare(g: list, bar: int, vel: float = 0.72) -> None:
    """Snare/clap on beats 2 and 4. Using noise_clap for body.
    Duration = 3 steps for sustained transient (not a click)."""
    bs = bar * BAR
    g[1][bs + 4] = note(SNARE, 40, vel, 3)       # beat 2
    g[1][bs + 12] = note(SNARE, 40, vel * 0.95, 3)  # beat 4 (slightly softer)


def smooth_bass(g: list, bar: int, root: int, vel: float = 0.75) -> None:
    """Bass with sustained notes — no staccato pops.
    Root on beat 1 (long), fifth on beat 3 (medium)."""
    bs = bar * BAR
    g[3][bs] = note(BASS, root, vel, 6)          # root: sustained
    g[3][bs + 8] = note(BASS, root + 7, vel * 0.65, 4)  # fifth up: medium


def warm_pad(g: list, bar: int, chord: tuple, vel: float = 0.40) -> None:
    """Sustained pad chord — the warmth floor. Full bar duration."""
    bs = bar * BAR
    # Use the middle note of the chord for the pad (smoothest)
    g[5][bs] = note(PAD, chord[1], vel, BAR)


def smooth_arp(g: list, bar: int, chord: tuple, vel: float = 0.45) -> None:
    """Arpeggiate chord tones as smooth 8th notes with long sustain.
    Duration = 3 steps per note (notes overlap slightly = legato)."""
    bs = bar * BAR
    tones = list(chord) + [chord[0] + 12]  # add octave for 4 tones
    for step in range(0, BAR, 2):  # 8th note pulse
        tone = tones[step // 2 % len(tones)]
        g[6][bs + step] = note(ARP, tone, vel, 3)  # sustain through next note


def place_hook(g: list, bar_offset: int, hook_data: list, inst: str,
               vel_scale: float = 1.0, channel: int = 4) -> None:
    """Place melody hook at bar_offset with proper sustain."""
    bs = bar_offset * BAR
    for step, midi, vel, dur in hook_data:
        s = bs + step
        if s < len(g[channel]):
            g[channel][s] = note(inst, midi, vel * vel_scale, dur)


# ── PATTERN BUILDERS ─────────────────────────────────────────────────────

def make_atmosphere() -> Pattern:
    """4 bars: Pad wash establishing the key. Soft filtered arp.
    Very gentle hats. No kick, no bass. Pure warmth."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        chord = CHORDS[bar % 4]

        # Pad: full sustained warmth, gradually louder
        vel = 0.30 + bar * 0.04
        warm_pad(g, bar, chord, vel)

        # Arp: quiet, filtered, legato — establishing the vibe
        arp_vel = 0.28 + bar * 0.04
        smooth_arp(g, bar, chord, arp_vel)

        # Hats: very soft shimmer, every 4 steps
        bs = bar * BAR
        for step in range(0, BAR, 4):
            g[2][bs + step] = note(HAT_OP, 46, 0.20 + bar * 0.02, 3)

        # Melody tease: first 4 notes of hook in bars 2-3 only
        if bar == 2:
            for i, (step, midi, vel_h, dur) in enumerate(HOOK[:4]):
                g[4][bs + step] = note(LEAD, midi, vel_h * 0.45, dur + 1)

    return Pattern(name='atmosphere', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_rise() -> Pattern:
    """4 bars: Kick fades in. Bass slides in. Snare roll in bar 4.
    Building tension toward the drop."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        chord = CHORDS[bar % 4]
        root = BASS_ROOTS[bar % 4]

        # Pad: always present (warmth floor)
        warm_pad(g, bar, chord, 0.38)

        # Arp: getting more present
        smooth_arp(g, bar, chord, 0.38 + bar * 0.04)

        # Kick: enters bar 1, builds
        if bar >= 1:
            kick_vel = 0.55 + (bar - 1) * 0.08
            four_on_floor(g, bar, kick_vel)

        # Bass: enters bar 2, sustained
        if bar >= 2:
            bass_vel = 0.55 + (bar - 2) * 0.10
            smooth_bass(g, bar, root, bass_vel)

        # Hats: building from atmosphere to full groove
        hat_vel = 0.30 + bar * 0.05
        rave_hats(g, bar, hat_vel)

        # Bar 4: snare roll (building tension toward drop)
        if bar == 3:
            bs = bar * BAR
            for step in range(0, BAR, 2):
                roll_vel = 0.40 + step * 0.025  # crescendo roll
                g[1][bs + step] = note(SNARE, 40, min(roll_vel, 0.78), 2)

            # THE GAP: silence on last 2 steps (anticipation)
            g[0][bs + 14] = None
            g[0][bs + 15] = None

    return Pattern(name='rise', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_drop1() -> Pattern:
    """8 bars: THE DROP. Full groove. The hook plays twice.
    Everything smooth, everything hitting, everything warm."""
    steps = BAR * 8
    g = new_grid(steps)

    for bar in range(8):
        chord = CHORDS[bar % 4]
        root = BASS_ROOTS[bar % 4]

        # Drums: full groove
        four_on_floor(g, bar, 0.80)
        fat_snare(g, bar, 0.75)
        rave_hats(g, bar, 0.50)

        # Bass: driving but smooth
        smooth_bass(g, bar, root, 0.78)

        # Pad: sustained chord warmth (slightly lower in mix — drums take over)
        warm_pad(g, bar, chord, 0.32)

        # Arp: full groove, adds width
        smooth_arp(g, bar, chord, 0.48)

    # Hook: plays in bars 0-1 and 4-5 (call and response across the drop)
    place_hook(g, 0, HOOK, LEAD, 0.95)
    place_hook(g, 4, HOOK, LEAD, 1.0)  # second time slightly louder

    # Fill: extra snare hits at bar transitions for groove
    for bar in [3, 7]:
        bs = bar * BAR
        g[1][bs + 14] = note(SNARE, 40, 0.55, 2)  # ghost snare before downbeat

    return Pattern(name='drop1', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_breathe() -> Pattern:
    """4 bars: Breakdown. Strip to pad + arp + soft kick.
    The room exhales. Counter-melody teases."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        chord = CHORDS[bar % 4]
        root = BASS_ROOTS[bar % 4]

        # Pad: front and center now (louder than in drop)
        warm_pad(g, bar, chord, 0.48)

        # Arp: dreamy, slower feel (quarter notes instead of 8ths)
        bs = bar * BAR
        tones = list(chord)
        for beat in range(4):
            tone = tones[beat % len(tones)]
            g[6][bs + beat * 4] = note(ARP, tone, 0.38, 4)  # long quarter notes

        # Kick: half-time (beats 1 and 3 only), soft
        g[0][bs] = note(KICK, 36, 0.55, 2)
        g[0][bs + 8] = note(KICK, 36, 0.48, 2)

        # Hats: sparse shimmer
        g[2][bs + 4] = note(HAT_OP, 46, 0.25, 3)
        g[2][bs + 12] = note(HAT_OP, 46, 0.22, 3)

        # Bass: gentle root only
        g[3][bs] = note(BASS, root, 0.50, 8)

        # Counter-melody tease (bars 2-3)
        if bar >= 2:
            for step, midi, vel, dur in COUNTER[:5]:
                s = bs + step
                if s < steps:
                    g[4][s] = note(LEAD_B, midi, vel * 0.7, dur + 1)

    return Pattern(name='breathe', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_drop2() -> Pattern:
    """8 bars: Everything returns + counter-melody weaving around hook.
    This is the emotional peak. Slightly higher velocities, richer texture."""
    steps = BAR * 8
    g = new_grid(steps)

    for bar in range(8):
        chord = CHORDS[bar % 4]
        root = BASS_ROOTS[bar % 4]

        # Full groove with slightly more energy
        four_on_floor(g, bar, 0.82)
        fat_snare(g, bar, 0.78)
        rave_hats(g, bar, 0.52)

        # Bass: more aggressive — root + octave bounce
        bs = bar * BAR
        g[3][bs] = note(BASS, root, 0.80, 4)
        g[3][bs + 4] = note(BASS, root + 12, 0.62, 3)  # octave up
        g[3][bs + 8] = note(BASS, root + 7, 0.68, 4)   # fifth
        g[3][bs + 12] = note(BASS, root, 0.72, 4)       # back to root

        # Pad: sustained warmth
        warm_pad(g, bar, chord, 0.35)

        # Arp: full groove
        smooth_arp(g, bar, chord, 0.50)

    # Hook: bars 0-1 and 4-5
    place_hook(g, 0, HOOK, LEAD, 1.0)
    place_hook(g, 4, HOOK, LEAD, 1.0)

    # Counter-melody: weaves around hook in bars 2-3 and 6-7
    place_hook(g, 2, COUNTER, LEAD_B, 0.85)
    place_hook(g, 6, COUNTER, LEAD_B, 0.90)

    # Extra hat variation: open hat accents on odd bars
    for bar in [1, 3, 5, 7]:
        bs = bar * BAR
        g[2][bs + 6] = note(HAT_OP, 46, 0.55, 3)
        g[2][bs + 14] = note(HAT_OP, 46, 0.50, 3)

    return Pattern(name='drop2', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_crescendo() -> Pattern:
    """4 bars: Final build. Velocity swell across all channels.
    Snare roll returns. Bass octave walk. Maximum energy."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        chord = CHORDS[bar % 4]
        root = BASS_ROOTS[bar % 4]
        # Energy multiplier: 0.85 → 0.98 across 4 bars
        energy = 0.82 + bar * 0.045

        # Kick: pounding
        four_on_floor(g, bar, min(energy, 0.85))

        # Hats: full groove
        rave_hats(g, bar, energy * 0.60)

        # Bass: octave walk — ascending energy
        bs = bar * BAR
        g[3][bs] = note(BASS, root, energy * 0.90, 4)
        g[3][bs + 4] = note(BASS, root + 5, energy * 0.72, 3)  # fourth
        g[3][bs + 8] = note(BASS, root + 7, energy * 0.78, 3)  # fifth
        g[3][bs + 12] = note(BASS, root + 12, energy * 0.82, 4)  # octave

        # Pad: building
        warm_pad(g, bar, chord, energy * 0.45)

        # Arp: faster in final bars (16th notes bars 2-3)
        if bar < 2:
            smooth_arp(g, bar, chord, energy * 0.52)
        else:
            # 16th note arp for building urgency
            tones = list(chord) + [chord[0] + 12]
            for step in range(BAR):
                tone = tones[step % len(tones)]
                g[6][bs + step] = note(ARP, tone, energy * 0.42, 2)

        # Snare: roll builds across all 4 bars
        if bar < 2:
            fat_snare(g, bar, energy * 0.82)
        else:
            # Snare roll: 8th notes → 16th notes
            interval = 2 if bar == 3 else 4
            for step in range(0, BAR, interval):
                roll_vel = energy * (0.55 + step * 0.015)
                g[1][bs + step] = note(SNARE, 40, min(roll_vel, 0.85), 2)

    # Hook: one final time, bars 0-1, peak velocity
    place_hook(g, 0, HOOK, LEAD, 1.0)

    return Pattern(name='crescendo', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_resolve() -> Pattern:
    """6 bars: Gentle decay back to atmosphere. The afterglow.
    Elements drop out one by one. Pad sustains to the end."""
    steps = BAR * 6
    g = new_grid(steps)

    for bar in range(6):
        chord = CHORDS[bar % 4]
        root = BASS_ROOTS[bar % 4]

        # Pad: always present, slowly fading
        pad_vel = 0.45 - bar * 0.05
        warm_pad(g, bar, chord, max(pad_vel, 0.18))

        # Arp: quarter notes, fading
        if bar < 4:
            bs = bar * BAR
            tones = list(chord)
            arp_vel = 0.40 - bar * 0.06
            for beat in range(4):
                tone = tones[beat % len(tones)]
                g[6][bs + beat * 4] = note(ARP, tone, max(arp_vel, 0.15), 5)

        # Kick: drops out after bar 2
        if bar < 3:
            kick_vel = 0.65 - bar * 0.12
            bs = bar * BAR
            g[0][bs] = note(KICK, 36, max(kick_vel, 0.35), 2)
            if bar < 2:
                g[0][bs + 8] = note(KICK, 36, max(kick_vel * 0.80, 0.30), 2)

        # Hats: sparse, fading
        if bar < 4:
            bs = bar * BAR
            hat_vel = 0.30 - bar * 0.05
            g[2][bs + 4] = note(HAT_OP, 46, max(hat_vel, 0.12), 3)
            g[2][bs + 12] = note(HAT_OP, 46, max(hat_vel * 0.8, 0.10), 3)

        # Bass: bar 0-1 only
        if bar < 2:
            g[3][bar * BAR] = note(BASS, root, 0.50 - bar * 0.12, 8)

        # Lead: final hook fragment (bars 0-1), very soft
        if bar == 0:
            bs = bar * BAR
            for step, midi, vel, dur in HOOK[:4]:
                g[4][bs + step] = note(LEAD, midi, vel * 0.40, dur + 2)

    # Final note: low D pad, sustained to the end
    g[5][4 * BAR] = note(PAD, D3, 0.25, BAR * 2)

    return Pattern(name='resolve', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── SONG ASSEMBLY ─────────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_atmosphere(),  # 0 — 4 bars
        make_rise(),        # 1 — 4 bars
        make_drop1(),       # 2 — 8 bars
        make_breathe(),     # 3 — 4 bars
        make_drop2(),       # 4 — 8 bars
        make_crescendo(),   # 5 — 4 bars
        make_resolve(),     # 6 — 6 bars
    ]
    # Total: 38 bars ≈ 65.1 seconds at 140 BPM

    # PANNING: wide stereo field — every element has a place
    panning = {
        0:  0.00,    # kick: dead center
        1:  0.00,    # snare: dead center
        2:  0.28,    # hats: right (creates space)
        3:  0.00,    # bass: center (mono is correct for sub)
        4:  0.12,    # lead: slight right
        5: -0.20,    # pad: slight left (balances hats)
        6: -0.30,    # arp: left (wide stereo with hats)
    }

    # EFFECTS: THE KEY TO SMOOTH SOUND — every channel gets treatment
    channel_effects = {
        0: {  # Kick: subtle room, keeps it present but not dry
            'reverb': 0.18, 'reverb_mix': 0.08,
        },
        1: {  # Snare/Clap: medium room for body
            'reverb': 0.35, 'reverb_mix': 0.18,
        },
        2: {  # Hats: ping-pong delay feel + room
            'delay': 0.107, 'delay_feedback': 0.25, 'delay_mix': 0.15,
            'reverb': 0.30, 'reverb_mix': 0.15,
        },
        3: {  # Bass: very subtle room (keeps it tight but not dead)
            'reverb': 0.12, 'reverb_mix': 0.05,
        },
        4: {  # Lead: rich reverb + slapback delay
            'reverb': 0.55, 'reverb_mix': 0.28,
            'delay': 0.214, 'delay_feedback': 0.30, 'delay_mix': 0.20,
        },
        5: {  # Pad: deep hall reverb (the room itself)
            'reverb': 0.85, 'reverb_mix': 0.50,
        },
        6: {  # Arp: spacious delay + medium room
            'delay': 0.161, 'delay_feedback': 0.35, 'delay_mix': 0.25,
            'reverb': 0.45, 'reverb_mix': 0.22,
        },
    }

    return Song(
        title='Neural Cascade v2 — Deep Rave Edition',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2, 3, 4, 5, 6],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.15,     # Global room cohesion
        master_delay=0.08,      # Global depth
    )


# ── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("╔════════════════════════════════════════════════════╗")
    print("║  NEURAL CASCADE v2 — Deep Rave Edition            ║")
    print("║  Smooth · Rich · Warm · No Staccato Chirps        ║")
    print("╚════════════════════════════════════════════════════╝")
    print()
    print("  Sound design philosophy:")
    print("    ♫  Every note has sustain (min 2 steps)")
    print("    ♫  Every channel has reverb or delay")
    print("    ♫  Velocities capped at 0.85 (no clipping)")
    print("    ♫  Warm instruments: saw_filtered, pulse_warm")
    print("    ♫  Fat snare: noise_clap (3-step sustain)")
    print("    ♫  Rich bass: bass_growl (harmonics)")
    print("    ♫  Pad floor in every section")
    print()
    print(f"  Key: D minor (i→bVI→bVII→i)")
    print(f"  BPM: {BPM}")
    print()
    print("  [0-7s]    Atmosphere — Pad wash + filtered arp")
    print("  [7-14s]   Rise       — Kick enters, bass slides in")
    print("  [14-28s]  Drop 1     — Full groove, the hook")
    print("  [28-35s]  Breathe    — Strip to pad + arp")
    print("  [35-49s]  Drop 2     — Counter-melody weaves in")
    print("  [49-55s]  Crescendo  — Final build, snare roll")
    print("  [55-66s]  Resolve    — Gentle decay to silence")
    print()
    print("  Rendering...", flush=True)

    song = build_song()
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    out = Path('output/neural_cascade_v2.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  3AM. Warehouse. Proper sound system.")
    print("  Everything smooth. Everything wide.")
