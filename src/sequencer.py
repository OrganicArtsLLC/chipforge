"""
ChipForge Sequencer
====================
Tracker-style pattern and song data models.

Inspired by MOD/FastTracker format:
  - Each Pattern is a 2D grid: grid[channel][step] = NoteEvent | None
  - A Song is a list of Patterns + an arrangement sequence
  - Rendering traverses the sequence and concatenates pattern audio buffers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REST: int = 0                   # MIDI note 0 = rest (silence)
DEFAULT_STEPS: int = 16         # One bar of 16th notes
DEFAULT_CHANNELS: int = 4       # Classic Game Boy style (4 channels)
DEFAULT_BPM: float = 120.0
DEFAULT_STEPS_PER_BEAT: int = 4  # 16th notes in 4/4


# ---------------------------------------------------------------------------
# Note Event
# ---------------------------------------------------------------------------

@dataclass
class NoteEvent:
    """
    A single note event at a pattern grid position.

    Attributes:
        midi_note: MIDI note number. 0 = rest/silence.
        velocity: Amplitude scalar (0.0–1.0).
        duration_steps: How many steps the note rings for (1 = one step).
        instrument: Instrument preset key string (e.g. "pulse_lead").
        articulation: Performance articulation:
            - "normal" — default ADSR, full duration
            - "staccato" — half duration, slight accent (detached)
            - "tenuto" — full duration, slight emphasis (held)
            - "legato" — extended into next note for slurred phrasing
            - "marcato" — strong accent (+15% velocity)
            - "accent" — light accent (+8% velocity)
            - "fermata" — held longer than written (~1.75x)
        glide_ms: Portamento glide time from the previous melodic note in
                  the same channel (0 = no glide). The first `glide_ms` of
                  the note ramps from the previous note's frequency to this
                  note's frequency, logarithmically (constant semitones/sec).
    """

    midi_note: int = REST
    velocity: float = 0.80
    duration_steps: int = 1
    instrument: str = "pulse_lead"
    articulation: str = "normal"
    glide_ms: float = 0.0

    def is_rest(self) -> bool:
        """Return True if this note event is a silence."""
        return self.midi_note == REST


# ---------------------------------------------------------------------------
# Pattern
# ---------------------------------------------------------------------------

@dataclass
class Pattern:
    """
    A fixed-length note grid: rows = steps, columns = channels.

    Like a single phrase or bar in a MOD tracker. Patterns are referenced
    by index from the Song and can repeat across the arrangement.

    Attributes:
        name: Display name for this pattern.
        num_steps: Total step count (16 = one 4/4 bar of 16th notes).
        num_channels: Number of simultaneous voices.
        bpm: Playback tempo in beats per minute.
        steps_per_beat: Rhythmic subdivision (4 = 16th notes, 2 = 8th notes).
        grid: 2D list — grid[channel][step] = NoteEvent or None.
    """

    name: str = "Pattern"
    num_steps: int = DEFAULT_STEPS
    num_channels: int = DEFAULT_CHANNELS
    bpm: float = DEFAULT_BPM
    steps_per_beat: int = DEFAULT_STEPS_PER_BEAT
    grid: list[list[Optional[NoteEvent]]] = field(default_factory=list)
    temperament: str = "equal"
    key_root_pc: int = 0  # 0 = C, 2 = D, 4 = E, 5 = F, 7 = G, 9 = A, 11 = B
    time_sig_num: int = 4    # numerator   — beats per bar (3 for waltz, 6 for jig)
    time_sig_den: int = 4    # denominator — beat unit (4 = quarter, 8 = eighth)

    def __post_init__(self) -> None:
        if not self.grid:
            self.grid = [[None] * self.num_steps for _ in range(self.num_channels)]

    def set_note(self, channel: int, step: int, note: NoteEvent) -> None:
        """
        Place a note event at the given channel and step.

        Args:
            channel: Channel index (0–num_channels-1).
            step: Step index (0–num_steps-1).
            note: NoteEvent to place.
        """
        if 0 <= channel < self.num_channels and 0 <= step < self.num_steps:
            self.grid[channel][step] = note

    def clear_note(self, channel: int, step: int) -> None:
        """Remove a note event from the given position (set to None = silence)."""
        if 0 <= channel < self.num_channels and 0 <= step < self.num_steps:
            self.grid[channel][step] = None

    def get_note(self, channel: int, step: int) -> Optional[NoteEvent]:
        """Return the NoteEvent at (channel, step), or None if empty."""
        if 0 <= channel < self.num_channels and 0 <= step < self.num_steps:
            return self.grid[channel][step]
        return None

    def clear_channel(self, channel: int) -> None:
        """Clear all notes from a channel."""
        if 0 <= channel < self.num_channels:
            self.grid[channel] = [None] * self.num_steps

    def clear_all(self) -> None:
        """Clear all notes from every channel."""
        self.grid = [[None] * self.num_steps for _ in range(self.num_channels)]

    def step_duration_sec(self) -> float:
        """Duration of one step in seconds based on BPM and subdivision."""
        beats_per_sec = self.bpm / 60.0
        return 1.0 / (beats_per_sec * self.steps_per_beat)

    def total_duration_sec(self) -> float:
        """Total duration of this pattern in seconds."""
        return self.num_steps * self.step_duration_sec()

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible plain dict."""
        grid_data: list[list] = []
        for channel in self.grid:
            ch: list = []
            for event in channel:
                if event is None:
                    ch.append(None)
                else:
                    ch.append({
                        "midi_note": event.midi_note,
                        "velocity": event.velocity,
                        "duration_steps": event.duration_steps,
                        "instrument": event.instrument,
                        "articulation": event.articulation,
                        "glide_ms": event.glide_ms,
                    })
            grid_data.append(ch)

        return {
            "name": self.name,
            "num_steps": self.num_steps,
            "num_channels": self.num_channels,
            "bpm": self.bpm,
            "steps_per_beat": self.steps_per_beat,
            "temperament": self.temperament,
            "key_root_pc": self.key_root_pc,
            "time_sig_num": self.time_sig_num,
            "time_sig_den": self.time_sig_den,
            "grid": grid_data,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        """Deserialize a Pattern from a plain dict."""
        raw_grid = data.get("grid", [])
        grid: list[list[Optional[NoteEvent]]] = []
        for ch_data in raw_grid:
            channel: list[Optional[NoteEvent]] = []
            for event_data in ch_data:
                if event_data is None:
                    channel.append(None)
                else:
                    channel.append(NoteEvent(
                        midi_note=event_data.get("midi_note", 0),
                        velocity=event_data.get("velocity", 0.8),
                        duration_steps=event_data.get("duration_steps", 1),
                        instrument=event_data.get("instrument", "pulse_lead"),
                        articulation=event_data.get("articulation", "normal"),
                        glide_ms=event_data.get("glide_ms", 0.0),
                    ))
            grid.append(channel)

        return cls(
            name=data.get("name", "Pattern"),
            num_steps=data.get("num_steps", DEFAULT_STEPS),
            num_channels=data.get("num_channels", DEFAULT_CHANNELS),
            bpm=data.get("bpm", DEFAULT_BPM),
            steps_per_beat=data.get("steps_per_beat", DEFAULT_STEPS_PER_BEAT),
            temperament=data.get("temperament", "equal"),
            key_root_pc=data.get("key_root_pc", 0),
            time_sig_num=data.get("time_sig_num", 4),
            time_sig_den=data.get("time_sig_den", 4),
            grid=grid,
        )


# ---------------------------------------------------------------------------
# Song
# ---------------------------------------------------------------------------

@dataclass
class Song:
    """
    A complete song: a collection of patterns and an arrangement sequence.

    The arrangement is defined by `sequence`, which is an ordered list of
    pattern indices. Patterns can repeat (e.g. [0, 0, 1, 0, 0] plays the
    first pattern twice, then the second once, then the first twice again).

    Attributes:
        title: Song title.
        author: Creator name.
        bpm: Global BPM (patterns inherit this unless overridden).
        patterns: List of Pattern objects.
        sequence: Ordered list of pattern indices (the arrangement).
    """

    title: str = "Untitled"
    author: str = "ChipForge"
    bpm: float = DEFAULT_BPM
    patterns: list[Pattern] = field(default_factory=list)
    sequence: list[int] = field(default_factory=list)
    panning: Optional[dict[int, float]] = field(default_factory=dict)
    channel_effects: Optional[dict[int, dict]] = field(default_factory=dict)
    master_reverb: float = 0.0
    master_delay: float = 0.0
    # Tempo curve: list of (beat_index, bpm) keyframes for accelerando /
    # ritardando. The mixer interpolates linearly between keyframes and
    # applies the resolved BPM to each pattern as the song unfolds.
    # Empty = constant tempo (use Song.bpm).
    tempo_curve: list[tuple[float, float]] = field(default_factory=list)
    # Dynamics curve: list of (beat_index, gain_db) keyframes that crescendo
    # or diminuendo across the song. The mixer interpolates linearly between
    # keyframes and scales every note's velocity by 10**(db/20) at its
    # beat position. Empty = no dynamic shaping (gain 0 dB everywhere).
    dynamics_curve: list[tuple[float, float]] = field(default_factory=list)

    def new_pattern(
        self,
        name: str = "Pattern",
        num_steps: int = DEFAULT_STEPS,
        num_channels: int = DEFAULT_CHANNELS,
    ) -> tuple[Pattern, int]:
        """
        Create a new empty pattern, add it to this song, and return it with its index.

        Args:
            name: Display name.
            num_steps: Step count.
            num_channels: Channel count.

        Returns:
            Tuple of (Pattern, index).
        """
        pattern = Pattern(
            name=name,
            num_steps=num_steps,
            num_channels=num_channels,
            bpm=self.bpm,
        )
        idx = len(self.patterns)
        self.patterns.append(pattern)
        return pattern, idx

    def append_to_sequence(self, pattern_index: int, repeat: int = 1) -> None:
        """
        Append a pattern to the arrangement sequence.

        Args:
            pattern_index: Index of the pattern in self.patterns.
            repeat: How many times to append it.
        """
        for _ in range(repeat):
            self.sequence.append(pattern_index)

    def total_duration_sec(self) -> float:
        """Total rendered duration in seconds."""
        return sum(
            self.patterns[i].total_duration_sec()
            for i in self.sequence
            if 0 <= i < len(self.patterns)
        )

    def gain_db_at_beat(self, beat: float) -> float:
        """
        Resolve the dynamics gain (in dB) at an absolute beat position.

        Linear interpolation between dynamics_curve keyframes; constant
        outside the curve range. Returns 0 dB if no curve is set.

        Args:
            beat: Absolute beat position from start of song.

        Returns:
            Gain in dB (0 dB = unity, +6 dB = ~2x amplitude).
        """
        if not self.dynamics_curve:
            return 0.0
        sorted_curve = sorted(self.dynamics_curve, key=lambda kv: kv[0])
        if beat <= sorted_curve[0][0]:
            return sorted_curve[0][1]
        if beat >= sorted_curve[-1][0]:
            return sorted_curve[-1][1]
        for (b0, db0), (b1, db1) in zip(sorted_curve, sorted_curve[1:]):
            if b0 <= beat <= b1:
                if b1 == b0:
                    return db1
                frac = (beat - b0) / (b1 - b0)
                return db0 + frac * (db1 - db0)
        return 0.0

    def gain_lin_at_beat(self, beat: float) -> float:
        """Resolve the dynamics gain at a beat as a linear amplitude scalar."""
        return 10.0 ** (self.gain_db_at_beat(beat) / 20.0)

    def tempo_at_beat(self, beat: float) -> float:
        """
        Resolve the BPM at an absolute beat position by interpolating the
        tempo_curve. Linear interpolation between keyframes; constant
        before the first and after the last keyframe. Falls back to
        self.bpm if no curve is set.

        Args:
            beat: Absolute beat position from start of song.

        Returns:
            BPM at that beat.
        """
        if not self.tempo_curve:
            return self.bpm
        sorted_curve = sorted(self.tempo_curve, key=lambda kv: kv[0])
        if beat <= sorted_curve[0][0]:
            return sorted_curve[0][1]
        if beat >= sorted_curve[-1][0]:
            return sorted_curve[-1][1]
        for (b0, t0), (b1, t1) in zip(sorted_curve, sorted_curve[1:]):
            if b0 <= beat <= b1:
                if b1 == b0:
                    return t1
                frac = (beat - b0) / (b1 - b0)
                return t0 + frac * (t1 - t0)
        return self.bpm

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible plain dict."""
        return {
            "title": self.title,
            "author": self.author,
            "bpm": self.bpm,
            "patterns": [p.to_dict() for p in self.patterns],
            "sequence": list(self.sequence),
            "panning": dict(self.panning) if self.panning else {},
            "channel_effects": (
                {str(k): v for k, v in self.channel_effects.items()}
                if self.channel_effects else {}
            ),
            "master_reverb": self.master_reverb,
            "master_delay": self.master_delay,
            "tempo_curve": [list(kv) for kv in self.tempo_curve],
            "dynamics_curve": [list(kv) for kv in self.dynamics_curve],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Song":
        """Deserialize a Song from a plain dict."""
        song = cls(
            title=data.get("title", "Untitled"),
            author=data.get("author", "ChipForge"),
            bpm=data.get("bpm", DEFAULT_BPM),
        )
        for p_data in data.get("patterns", []):
            song.patterns.append(Pattern.from_dict(p_data))
        song.sequence = data.get("sequence", [])
        # Panning keys may be JSON strings — coerce back to int.
        raw_pan = data.get("panning") or {}
        song.panning = {int(k): float(v) for k, v in raw_pan.items()}
        raw_fx = data.get("channel_effects") or {}
        song.channel_effects = {int(k): v for k, v in raw_fx.items()}
        song.master_reverb = float(data.get("master_reverb", 0.0))
        song.master_delay = float(data.get("master_delay", 0.0))
        song.tempo_curve = [tuple(kv) for kv in data.get("tempo_curve", [])]
        song.dynamics_curve = [tuple(kv) for kv in data.get("dynamics_curve", [])]
        return song
