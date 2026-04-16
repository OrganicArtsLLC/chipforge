"""
Underground Pulse v2 — Deep House Groove, 2AM Underground
==========================================================
Complete rewrite. Previous version had wrong snare (noise_rim), was too short,
and shared a channel between sub reinforcement and lead.

Key: G Dorian (G A Bb C D E♮ F) — raised 6th (E natural) for sophistication
BPM: 122 — patient, hypnotic, room to breathe
~22 seconds (12 bars), 7 dedicated channels

FIXES FROM v1:
  - Snare: noise_clap (NOT noise_rim) — body, not click
  - Lead: lead_expressive (filter envelope + vibrato) on dedicated ch4
  - Bass: bass_growl on dedicated ch3 — no channel sharing
  - Pad: pad_evolving (filter slowly opens) with chorus for width
  - Arp: pluck_mellow (warm pluck), quarter-note stabs dur=4

Channels:
  0 - Kick     (kick_deep) — four-on-floor with swing velocity pattern
  1 - Snare    (noise_clap) — beats 2+4, vel=0.55, dur=3
  2 - Hats     (hat_crisp + hat_open_shimmer) — swung 8ths, opens on &2 &4
  3 - Bass     (bass_growl) — root beat 1, chromatic approach to fifth beat 3
  4 - Lead     (lead_expressive) — sparse soulful Dorian, 2-3 notes/bar, dur=4-6
  5 - Pad      (pad_evolving) — sustained Dorian 7th chords, chorus 0.30
  6 - Arp      (pluck_mellow) — quarter-note chord stabs, dur=4

Structure:
  [0-4s]    INTRO   2 bars — kick + bass only, establishing the pocket
  [4-8s]    BUILD   4 bars — hats + snare + pad + arp layers arrive
  [8-20s]   FULL    6 bars — lead melody enters, peak groove, E natural featured
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sequencer import Song, Pattern, NoteEvent
from src.mixer import render_song
from src.export import export_wav
from pathlib import Path

BPM = 122
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

def note(inst: str, midi: int, vel: float = 0.80, dur: int = 2) -> NoteEvent:
    """Create a note. Default dur=2 (no staccato). Vel capped at 0.85."""
    return NoteEvent(midi_note=midi, velocity=min(vel, 0.85),
                     duration_steps=max(dur, 2), instrument=inst)

def new_grid(steps: int) -> list:
    return [[None] * steps for _ in range(NUM_CH)]

# ── Instrument Assignments ──────────────────────────────────────────────
KICK    = 'kick_deep'
SNARE   = 'noise_clap'          # Body, NOT noise_rim click
HAT_CL  = 'hat_crisp'
HAT_OP  = 'hat_open_shimmer'
BASS    = 'bass_growl'           # Groove engine
LEAD    = 'lead_expressive'      # Filter envelope + vibrato
PAD     = 'pad_evolving'         # Filter slowly opens
ARP     = 'pluck_mellow'         # Warm pluck, quarter stabs

# ── G Dorian note constants (MIDI) ─────────────────────────────────────
# G Dorian: G A Bb C D E♮ F — raised 6th = E natural
G2 = 43; A2 = 45; Bb2 = 46; C3 = 48; D3 = 50; E3 = 52; F3 = 53
G3 = 55; A3 = 57; Bb3 = 58; C4 = 60; D4 = 62; E4 = 64; F4 = 65
G4 = 67; A4 = 69; Bb4 = 70; C5 = 72; D5 = 74; E5 = 76; F5 = 77
G5 = 79; Eb3 = 51; Eb4 = 63; Fs4 = 66

# Chord voicings — Dorian 7th chords
# Gm7 = G-Bb-D-F, Cm7 = C-Eb-G-Bb, Am7b5 = A-C-Eb-G, D7 = D-F#-A-C
CHORDS = [
    (G3, Bb3, D4, F4),     # Gm7  — home
    (C4, Eb4, G4, Bb4),    # Cm7  — subdominant
    (A3, C4, Eb4, G4),     # Am7b5 — the spice
    (D4, Fs4, A4, C5),     # D7   — dominant pull back to i
]

BASS_ROOTS = [G2, C3, A2, D3]

# ── Swing kick velocity pattern ───────────────────────────────────────
KICK_VELS = [0.80, 0.75, 0.82, 0.73]  # per spec: swing feel

def swung_kick(g: list, bar: int, energy: float = 1.0) -> None:
    """Four-on-floor with velocity swing. The pocket lives here."""
    bs = bar * BAR
    for beat in range(4):
        vel = KICK_VELS[beat] * energy
        g[0][bs + beat * 4] = note(KICK, 36, vel, 2)

def clap_snare(g: list, bar: int, vel: float = 0.55) -> None:
    """noise_clap on beats 2 and 4. dur=3 for body."""
    bs = bar * BAR
    g[1][bs + 4] = note(SNARE, 40, vel, 3)
    g[1][bs + 12] = note(SNARE, 40, vel * 0.95, 3)

def swung_hats(g: list, bar: int, vel: float = 0.50) -> None:
    """Swung 8th-note hats. Open hat on 'and' of 2 and 4."""
    bs = bar * BAR
    for step in range(0, BAR, 2):  # 8th notes
        if step % 4 == 0:
            # On-beat: closed, louder
            g[2][bs + step] = note(HAT_CL, 42, vel, 2)
        else:
            # Off-beat: closed, softer (the swing)
            g[2][bs + step] = note(HAT_CL, 42, vel * 0.70, 2)

    # Open hat accents on 'and' of 2 and 'and' of 4 (steps 6 and 14)
    g[2][bs + 6] = note(HAT_OP, 46, vel * 0.85, 3)
    g[2][bs + 14] = note(HAT_OP, 46, vel * 0.80, 3)

def groove_bass(g: list, bar: int, root: int, vel: float = 0.78) -> None:
    """Bass IS the song. Root on beat 1 (dur=4), chromatic approach to fifth."""
    bs = bar * BAR
    fifth = root + 7
    # Beat 1: root, sustained (dur=4 per spec — not 6, tighter pocket)
    g[3][bs] = note(BASS, root, vel, 4)
    # Beat 2.5: chromatic approach (half-step below fifth)
    g[3][bs + 6] = note(BASS, fifth - 1, vel * 0.58, 2)
    # Beat 3: fifth arrives
    g[3][bs + 8] = note(BASS, fifth, vel * 0.70, 4)
    # Beat 4: root octave bounce
    g[3][bs + 12] = note(BASS, root + 12, vel * 0.52, 3)

def evolving_pad(g: list, bar: int, chord: tuple, vel: float = 0.40) -> None:
    """Sustained Dorian 7th chord. pad_evolving filter slowly opens."""
    bs = bar * BAR
    # Two voices: 3rd and 7th for richness
    g[5][bs] = note(PAD, chord[1], vel, BAR)
    if len(chord) > 3:
        g[5][bs + 2] = note(PAD, chord[3], vel * 0.72, BAR - 2)

def quarter_stabs(g: list, bar: int, chord: tuple, vel: float = 0.42) -> None:
    """Quarter-note chord stabs with pluck_mellow. dur=4. NOT 16ths."""
    bs = bar * BAR
    tones = [chord[0], chord[2], chord[1], chord[2]]  # root-5th-3rd-5th
    for beat in range(4):
        g[6][bs + beat * 4] = note(ARP, tones[beat], vel, 4)


# ── Lead melodies — sparse, soulful, E natural featured ──────────────
# 2-3 notes per bar, dur=4-6. The Dorian raised 6th (E) is the star.

# Phrase A (2 bars): opening statement — G up through E natural
MELODY_A = [
    # Bar 0: sparse — D holds, then E natural (the character note)
    (0,  D5,  0.72, 6),       # long D, soulful entrance
    (8,  E5,  0.78, 5),       # E NATURAL — Dorian signature, prominent
    # Bar 1: resolve downward, breathing
    (16, G5,  0.74, 4),       # peak to high root
    (22, F5,  0.68, 5),       # gentle descent
    (28, D5,  0.65, 4),       # settle on 5th
]

# Phrase B (2 bars): deeper, more chromatic, E natural again
MELODY_B = [
    # Bar 0: start low, climb through the mode
    (0,  A4,  0.70, 5),       # start on 2nd degree
    (6,  Bb4, 0.72, 4),       # minor 3rd color
    (12, D5,  0.76, 4),       # leap to 5th
    # Bar 1: the E natural phrase — lingering, soulful
    (17, E5,  0.80, 6),       # E NATURAL — let it ring, the whole point
    (24, D5,  0.68, 4),       # step down
    (29, C5,  0.64, 4),       # resolve to 4th
]

# Phrase C (2 bars): peak expression — wider intervals, more E natural
MELODY_C = [
    # Bar 0: big leap, emotional
    (0,  G4,  0.72, 4),       # start from root
    (5,  E5,  0.82, 6),       # LEAP to E natural — the moment
    (12, F5,  0.74, 4),       # step up from E
    # Bar 1: descend with grace
    (18, E5,  0.78, 5),       # E natural AGAIN — can't get enough
    (24, C5,  0.70, 4),       # drop to 4th
    (30, Bb4, 0.65, 4),       # Dorian minor 3rd, warm close
]

def place_melody(g: list, bar_offset: int, melody: list,
                 vel_scale: float = 1.0) -> None:
    """Place a 2-bar melody phrase on ch4 starting at bar_offset."""
    bs = bar_offset * BAR
    for step, midi, vel, dur in melody:
        s = bs + step
        if s < len(g[4]):
            g[4][s] = note(LEAD, midi, vel * vel_scale, dur)


# ── PATTERN BUILDERS ───────────────────────────────────────────────────

def make_intro() -> Pattern:
    """2 bars: Kick + bass ONLY. Establishing the pocket.
    The groove must make you move from bar 1."""
    steps = BAR * 2
    g = new_grid(steps)

    for bar in range(2):
        root = BASS_ROOTS[bar % 4]

        # Kick: four-on-floor with swing from the start
        swung_kick(g, bar, energy=0.95)

        # Bass: the groove engine, slightly restrained
        groove_bass(g, bar, root, vel=0.72)

    return Pattern(name='intro', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_build() -> Pattern:
    """4 bars: Layers arrive gradually — deep house patience.
    Hats + snare enter bar 0. Pad fades in. Arp enters bar 2."""
    steps = BAR * 4
    g = new_grid(steps)

    for bar in range(4):
        chord_idx = (bar + 2) % 4  # Continue from where intro left off
        chord = CHORDS[chord_idx]
        root = BASS_ROOTS[chord_idx]

        # Kick: full swing
        swung_kick(g, bar)

        # Snare: enters, builds confidence
        clap_snare(g, bar, vel=0.48 + bar * 0.02)

        # Hats: swung 8ths, gradually louder
        swung_hats(g, bar, vel=0.40 + bar * 0.03)

        # Bass: bounce continues, building
        groove_bass(g, bar, root, vel=0.74 + bar * 0.01)

        # Pad: fading in from nothing — filter slowly opens
        pad_vel = 0.20 + bar * 0.06
        evolving_pad(g, bar, chord, pad_vel)

        # Arp: enters in bar 2 (patience!)
        if bar >= 2:
            arp_vel = 0.32 + (bar - 2) * 0.05
            quarter_stabs(g, bar, chord, arp_vel)

    return Pattern(name='build', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


def make_full() -> Pattern:
    """6 bars: THE GROOVE. Lead melody enters. All 7 channels.
    This is where you feel it. E natural featured prominently."""
    steps = BAR * 6
    g = new_grid(steps)

    for bar in range(6):
        chord_idx = bar % 4
        chord = CHORDS[chord_idx]
        root = BASS_ROOTS[chord_idx]

        # Energy curve: builds across the 6 bars
        energy = 0.92 + bar * 0.013  # 0.92 → 0.99

        # Kick: full swing, peak energy
        swung_kick(g, bar, energy=energy)

        # Snare: full confidence
        clap_snare(g, bar, vel=0.55)

        # Hats: full groove with swing
        swung_hats(g, bar, vel=0.52)

        # Bass: full groove engine
        groove_bass(g, bar, root, vel=0.80)

        # Pad: full warmth, sustained
        evolving_pad(g, bar, chord, vel=0.42)

        # Arp: quarter stabs, the sophistication
        quarter_stabs(g, bar, chord, vel=0.45)

    # Lead melody: sparse, soulful, E natural is the star
    # Melody enters — 3 phrases across 6 bars
    place_melody(g, 0, MELODY_A, vel_scale=0.90)   # bars 0-1: opening
    place_melody(g, 2, MELODY_B, vel_scale=0.95)   # bars 2-3: deeper
    place_melody(g, 4, MELODY_C, vel_scale=1.0)    # bars 4-5: peak expression

    # Extra hat ghost notes in bars 3 and 5 for momentum
    for bar in [3, 5]:
        bs = bar * BAR
        for step in [1, 5, 9, 13]:
            if g[2][bs + step] is None:
                g[2][bs + step] = note(HAT_CL, 42, 0.22, 2)

    # Final bar: snare fill leading to the (implied) loop point
    bs = 5 * BAR
    g[1][bs + 10] = note(SNARE, 40, 0.45, 2)
    g[1][bs + 14] = note(SNARE, 40, 0.50, 2)

    return Pattern(name='full', num_steps=steps, num_channels=NUM_CH,
                   steps_per_beat=SPB, bpm=BPM, grid=g)


# ── SONG ASSEMBLY ─────────────────────────────────────────────────────

def build_song() -> Song:
    patterns = [
        make_intro(),    # 0 — 2 bars
        make_build(),    # 1 — 4 bars
        make_full(),     # 2 — 6 bars
    ]
    # Total: 12 bars at 122 BPM = ~23.6 seconds

    # PANNING: wide stereo — deep house spatial awareness
    panning = {
        0:  0.00,    # kick: dead center
        1:  0.05,    # snare: nearly center
        2:  0.28,    # hats: right (creates space)
        3: -0.08,    # bass: nearly center (sub integrity)
        4:  0.12,    # lead: slight right
        5: -0.22,    # pad: left (balances hats + arp width)
        6: -0.30,    # arp: left (wide stereo with hats)
    }

    # EFFECTS: every channel treated. Deep house = space and warmth.
    channel_effects = {
        0: {  # Kick: subtle room
            'reverb': 0.08, 'reverb_mix': 0.04,
        },
        1: {  # Snare/Clap: medium room for body
            'reverb': 0.22, 'reverb_mix': 0.14,
        },
        2: {  # Hats: rhythmic delay + room shimmer
            'delay': 0.122, 'delay_feedback': 0.22, 'delay_mix': 0.14,
            'reverb': 0.25, 'reverb_mix': 0.12,
        },
        3: {  # Bass: tight room (keeps low end focused)
            'reverb': 0.08, 'reverb_mix': 0.04,
        },
        4: {  # Lead: rich reverb + slapback — the space around the melody
            'reverb': 0.50, 'reverb_mix': 0.28,
            'delay': 0.245, 'delay_feedback': 0.28, 'delay_mix': 0.18,
        },
        5: {  # Pad: DEEP hall reverb + chorus for width (0.50 reverb per spec)
            'reverb': 0.85, 'reverb_mix': 0.50,
            'chorus': 0.30,
        },
        6: {  # Arp: spacious delay + medium room
            'delay': 0.184, 'delay_feedback': 0.32, 'delay_mix': 0.22,
            'reverb': 0.35, 'reverb_mix': 0.18,
        },
    }

    return Song(
        title='Underground Pulse v2 — Deep House Groove',
        author='ChipForge / Joshua Ayson (OA LLC)',
        bpm=BPM,
        patterns=patterns,
        sequence=[0, 1, 2],
        panning=panning,
        channel_effects=channel_effects,
        master_reverb=0.12,     # Per spec: room coherence
        master_delay=0.06,
    )


# ── MAIN ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Underground Pulse v2 — Deep House Groove")
    print("=" * 42)
    print(f"  Key: G Dorian (E natural = raised 6th) | BPM: {BPM}")
    print("  Structure: intro (2 bars) -> build (4 bars) -> full (6 bars)")
    print("  Rendering...", flush=True)

    song = build_song()
    audio = render_song(
        song,
        panning=song.panning,
        channel_effects=song.channel_effects,
        master_reverb=song.master_reverb,
        master_delay=song.master_delay,
    )

    out = Path('output/edm_004_underground_pulse.wav')
    out.parent.mkdir(exist_ok=True)
    export_wav(audio, out)

    duration = len(audio) / 44100.0
    size_mb = out.stat().st_size / 1_048_576
    print(f"  Duration: {duration:.1f}s | Size: {size_mb:.1f} MB")
    print(f"  File:     {out}")
    print()
    print("  2AM. Underground. The groove moves you.")
