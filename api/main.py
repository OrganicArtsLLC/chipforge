"""
ChipForge Agent REST API
=========================
FastAPI application exposing ChipForge as an agent-controllable music engine.

Run with:
    uvicorn api.main:app --reload --port 8765

Interactive docs:
    http://localhost:8765/docs

Design principles:
  - All state is in-memory (songs dict keyed by UUID)
  - Every operation is a simple HTTP call with JSON in/out
  - Agents can compose songs step-by-step or in a single bulk call
  - The /render endpoint streams a WAV file directly
"""

from __future__ import annotations

import random
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
from pathlib import Path

# Ensure we can import src regardless of working directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    Song, Pattern, NoteEvent, PRESETS, SCALES, CHORD_TYPES, PROGRESSIONS,
    note_name_to_midi, get_scale_notes,
    generate_melody, generate_rhythm_pattern, generate_drum_pattern,
    render_song, render_pattern,
    audio_to_wav_bytes, save_song, song_to_dict,
)
from src.sequencer import DEFAULT_STEPS, DEFAULT_CHANNELS, DEFAULT_BPM


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ChipForge Agent API",
    description=(
        "Agent-controllable chip tune music engine. "
        "Build patterns, generate melodies, and render WAV audio via REST."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory song store: song_id (str UUID) → Song
_songs: dict[str, Song] = {}


def _get_song(song_id: str) -> Song:
    """Retrieve a song by ID or raise 404."""
    song = _songs.get(song_id)
    if song is None:
        raise HTTPException(status_code=404, detail=f"Song '{song_id}' not found.")
    return song


def _get_pattern(song_id: str, pattern_index: int) -> tuple[Song, Pattern]:
    """Retrieve a song and one of its patterns or raise 404."""
    song = _get_song(song_id)
    if not (0 <= pattern_index < len(song.patterns)):
        raise HTTPException(
            status_code=404,
            detail=f"Pattern index {pattern_index} out of range (song has {len(song.patterns)} patterns).",
        )
    return song, song.patterns[pattern_index]


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class SongInfo(BaseModel):
    song_id: str
    title: str
    bpm: float
    num_patterns: int
    sequence: list[int]
    duration_sec: float


class CreateSongRequest(BaseModel):
    title: str = "Untitled"
    bpm: float = Field(default=120.0, ge=20.0, le=400.0)
    author: str = "Agent"


class AddPatternRequest(BaseModel):
    name: str = "Pattern"
    num_steps: int = Field(default=DEFAULT_STEPS, ge=1, le=256)
    num_channels: int = Field(default=DEFAULT_CHANNELS, ge=1, le=16)
    bpm: Optional[float] = Field(default=None, ge=20.0, le=400.0)


class SetNoteRequest(BaseModel):
    channel: int = Field(ge=0)
    step: int = Field(ge=0)
    midi_note: int = Field(default=0, ge=0, le=127, description="0 = rest")
    velocity: float = Field(default=0.8, ge=0.0, le=1.0)
    duration_steps: int = Field(default=1, ge=1, le=64)
    instrument: str = "pulse_lead"


class BatchNoteItem(BaseModel):
    channel: int = Field(ge=0)
    step: int = Field(ge=0)
    midi_note: int = Field(default=0, ge=0, le=127)
    velocity: float = Field(default=0.8, ge=0.0, le=1.0)
    duration_steps: int = Field(default=1, ge=1, le=64)
    instrument: str = "pulse_lead"


class BatchNotesRequest(BaseModel):
    notes: list[BatchNoteItem]


class FillMelodyRequest(BaseModel):
    channel: int = Field(default=0, ge=0, description="Which channel to fill")
    root_note: str = Field(default="C", description="Root note name (C, F#, Bb, etc.)")
    octave: int = Field(default=5, ge=2, le=8)
    scale: str = Field(default="pentatonic_minor", description="Scale name")
    instrument: str = "pulse_lead"
    velocity: float = Field(default=0.8, ge=0.0, le=1.0)
    rest_probability: float = Field(default=0.15, ge=0.0, le=0.8)
    seed: Optional[int] = None


class FillRhythmRequest(BaseModel):
    kick_channel: int = Field(default=2, ge=0)
    snare_channel: Optional[int] = Field(default=3, ge=0)
    hat_channel: Optional[int] = Field(default=None, ge=0)
    kick_density: float = Field(default=0.35, ge=0.0, le=1.0)
    snare_density: float = Field(default=0.30, ge=0.0, le=1.0)
    hat_density: float = Field(default=0.50, ge=0.0, le=1.0)
    seed: Optional[int] = None


class AppendSequenceRequest(BaseModel):
    pattern_index: int = Field(ge=0)
    repeat: int = Field(default=1, ge=1, le=64)


class SetSequenceRequest(BaseModel):
    sequence: list[int]


class SaveSongRequest(BaseModel):
    filepath: str = ""  # if empty, saves to songs/{title}.chipforge.json


# For single-call song building
class ChannelData(BaseModel):
    instrument: str = "pulse_lead"
    notes: list[int] = Field(
        description="List of MIDI note numbers, length = num_steps. 0 = rest."
    )
    velocity: float = Field(default=0.8, ge=0.0, le=1.0)
    duration_steps: int = Field(default=1, ge=1, le=16)


class PatternData(BaseModel):
    name: str = "Pattern"
    num_steps: int = Field(default=DEFAULT_STEPS, ge=1, le=256)
    bpm: Optional[float] = None
    channels: list[ChannelData] = []


class BuildSongRequest(BaseModel):
    title: str = "Built Song"
    bpm: float = Field(default=120.0, ge=20.0, le=400.0)
    author: str = "Agent"
    patterns: list[PatternData] = []
    sequence: list[int] = []


class GenerateSongRequest(BaseModel):
    title: str = "Generated Song"
    bpm: float = Field(default=130.0, ge=20.0, le=400.0)
    key: str = Field(default="C", description="Root note of the key")
    key_octave: int = Field(default=5, ge=2, le=8)
    scale: str = Field(default="pentatonic_minor", description="Scale name")
    num_patterns: int = Field(default=2, ge=1, le=8)
    num_steps: int = Field(default=16, ge=4, le=64)
    num_melody_channels: int = Field(default=2, ge=1, le=4)
    include_drums: bool = True
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health():
    """Check if the API is running."""
    return {"status": "ok", "version": "0.1.0", "active_songs": len(_songs)}


# ---------------------------------------------------------------------------
# Reference Endpoints
# ---------------------------------------------------------------------------

@app.get("/instruments", tags=["Reference"])
def list_instruments():
    """List all available instrument presets."""
    return {
        key: {
            "name": inst.name,
            "waveform": inst.waveform,
            "duty": inst.duty,
            "volume": inst.volume,
            "adsr": {
                "attack": inst.adsr.attack,
                "decay": inst.adsr.decay,
                "sustain": inst.adsr.sustain,
                "release": inst.adsr.release,
            },
        }
        for key, inst in PRESETS.items()
    }


@app.get("/scales", tags=["Reference"])
def list_scales():
    """List all available scales with their interval patterns."""
    return {name: intervals for name, intervals in SCALES.items()}


@app.get("/chords", tags=["Reference"])
def list_chords():
    """List all available chord types with their interval patterns."""
    return CHORD_TYPES


# ---------------------------------------------------------------------------
# Song Management
# ---------------------------------------------------------------------------

@app.post("/songs", tags=["Songs"])
def create_song(req: CreateSongRequest) -> SongInfo:
    """Create a new empty song. Returns the song_id."""
    song_id = str(uuid.uuid4())
    song = Song(title=req.title, bpm=req.bpm, author=req.author)
    _songs[song_id] = song
    return SongInfo(
        song_id=song_id,
        title=song.title,
        bpm=song.bpm,
        num_patterns=0,
        sequence=[],
        duration_sec=0.0,
    )


@app.get("/songs/{song_id}", tags=["Songs"])
def get_song(song_id: str):
    """Get song metadata and pattern list."""
    song = _get_song(song_id)
    return {
        "song_id": song_id,
        "title": song.title,
        "author": song.author,
        "bpm": song.bpm,
        "num_patterns": len(song.patterns),
        "sequence": song.sequence,
        "duration_sec": song.total_duration_sec(),
        "patterns": [
            {
                "index": i,
                "name": p.name,
                "num_steps": p.num_steps,
                "num_channels": p.num_channels,
                "bpm": p.bpm,
                "duration_sec": p.total_duration_sec(),
            }
            for i, p in enumerate(song.patterns)
        ],
    }


@app.delete("/songs/{song_id}", tags=["Songs"])
def delete_song(song_id: str):
    """Delete a song from memory."""
    _get_song(song_id)  # raises 404 if not found
    del _songs[song_id]
    return {"deleted": song_id}


# ---------------------------------------------------------------------------
# Pattern Management
# ---------------------------------------------------------------------------

@app.post("/songs/{song_id}/patterns", tags=["Patterns"])
def add_pattern(song_id: str, req: AddPatternRequest):
    """Add a new empty pattern to the song. Returns the pattern index."""
    song = _get_song(song_id)
    bpm = req.bpm if req.bpm is not None else song.bpm
    pattern = Pattern(
        name=req.name,
        num_steps=req.num_steps,
        num_channels=req.num_channels,
        bpm=bpm,
    )
    idx = len(song.patterns)
    song.patterns.append(pattern)
    return {
        "pattern_index": idx,
        "name": pattern.name,
        "num_steps": pattern.num_steps,
        "num_channels": pattern.num_channels,
        "bpm": pattern.bpm,
    }


@app.get("/songs/{song_id}/patterns/{pattern_index}", tags=["Patterns"])
def get_pattern(song_id: str, pattern_index: int):
    """View a pattern's grid. Each row is a channel; each column is a step."""
    _, pattern = _get_pattern(song_id, pattern_index)
    return pattern.to_dict()


# ---------------------------------------------------------------------------
# Note Editing
# ---------------------------------------------------------------------------

@app.post("/songs/{song_id}/patterns/{pattern_index}/notes", tags=["Notes"])
def set_note(song_id: str, pattern_index: int, req: SetNoteRequest):
    """Set a single note in a pattern."""
    _, pattern = _get_pattern(song_id, pattern_index)

    if req.channel >= pattern.num_channels:
        raise HTTPException(
            status_code=400,
            detail=f"Channel {req.channel} out of range (pattern has {pattern.num_channels} channels).",
        )
    if req.step >= pattern.num_steps:
        raise HTTPException(
            status_code=400,
            detail=f"Step {req.step} out of range (pattern has {pattern.num_steps} steps).",
        )
    if req.instrument not in PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown instrument '{req.instrument}'. See GET /instruments.",
        )

    pattern.set_note(req.channel, req.step, NoteEvent(
        midi_note=req.midi_note,
        velocity=req.velocity,
        duration_steps=req.duration_steps,
        instrument=req.instrument,
    ))
    return {"ok": True, "channel": req.channel, "step": req.step, "midi_note": req.midi_note}


@app.post("/songs/{song_id}/patterns/{pattern_index}/notes/batch", tags=["Notes"])
def set_notes_batch(song_id: str, pattern_index: int, req: BatchNotesRequest):
    """
    Set many notes at once. Ideal for agents that build a full channel in one call.
    Invalid positions are skipped (not raised as errors).
    """
    _, pattern = _get_pattern(song_id, pattern_index)
    placed = 0
    skipped = 0
    for item in req.notes:
        if (0 <= item.channel < pattern.num_channels
                and 0 <= item.step < pattern.num_steps
                and item.instrument in PRESETS):
            pattern.set_note(item.channel, item.step, NoteEvent(
                midi_note=item.midi_note,
                velocity=item.velocity,
                duration_steps=item.duration_steps,
                instrument=item.instrument,
            ))
            placed += 1
        else:
            skipped += 1
    return {"placed": placed, "skipped": skipped}


@app.delete("/songs/{song_id}/patterns/{pattern_index}/notes/{channel}/{step}", tags=["Notes"])
def clear_note(song_id: str, pattern_index: int, channel: int, step: int):
    """Clear a single note from a pattern step."""
    _, pattern = _get_pattern(song_id, pattern_index)
    pattern.clear_note(channel, step)
    return {"ok": True, "channel": channel, "step": step}


# ---------------------------------------------------------------------------
# AI Generation
# ---------------------------------------------------------------------------

@app.post("/songs/{song_id}/patterns/{pattern_index}/fill-melody", tags=["Generate"])
def fill_melody(song_id: str, pattern_index: int, req: FillMelodyRequest):
    """
    Auto-generate a melody and fill a channel using weighted scale walking.
    Overwrites any existing notes in the target channel.
    """
    _, pattern = _get_pattern(song_id, pattern_index)

    if req.channel >= pattern.num_channels:
        raise HTTPException(status_code=400, detail=f"Channel {req.channel} out of range.")
    if req.scale not in SCALES:
        raise HTTPException(status_code=400, detail=f"Unknown scale '{req.scale}'. See GET /scales.")
    if req.instrument not in PRESETS:
        raise HTTPException(status_code=400, detail=f"Unknown instrument '{req.instrument}'.")

    root_midi = note_name_to_midi(req.root_note, req.octave)
    rng = random.Random(req.seed)
    melody = generate_melody(
        root_midi=root_midi,
        scale_name=req.scale,
        num_steps=pattern.num_steps,
        rest_probability=req.rest_probability,
        rng=rng,
    )

    pattern.clear_channel(req.channel)
    for step, midi_note in enumerate(melody):
        if midi_note > 0:
            pattern.set_note(req.channel, step, NoteEvent(
                midi_note=midi_note,
                velocity=req.velocity,
                duration_steps=1,
                instrument=req.instrument,
            ))

    return {
        "channel": req.channel,
        "root": req.root_note,
        "octave": req.octave,
        "scale": req.scale,
        "generated": melody,
    }


@app.post("/songs/{song_id}/patterns/{pattern_index}/fill-rhythm", tags=["Generate"])
def fill_rhythm(song_id: str, pattern_index: int, req: FillRhythmRequest):
    """
    Auto-generate a drum pattern and fill kick/snare/hat channels.
    Uses Game Boy LFSR noise instruments.
    """
    _, pattern = _get_pattern(song_id, pattern_index)

    rng = random.Random(req.seed)
    drums = generate_drum_pattern(
        num_steps=pattern.num_steps,
        kick_density=req.kick_density,
        snare_density=req.snare_density,
        hat_density=req.hat_density,
        rng=rng,
    )

    def fill_channel(channel_idx: Optional[int], hits: list[bool], instrument: str) -> int:
        if channel_idx is None or channel_idx >= pattern.num_channels:
            return 0
        pattern.clear_channel(channel_idx)
        placed = 0
        for step, hit in enumerate(hits):
            if hit:
                pattern.set_note(channel_idx, step, NoteEvent(
                    midi_note=60,  # pitch doesn't matter for noise
                    velocity=0.8,
                    duration_steps=1,
                    instrument=instrument,
                ))
                placed += 1
        return placed

    kick_placed = fill_channel(req.kick_channel, drums["kick"], "noise_kick")
    snare_placed = fill_channel(req.snare_channel, drums["snare"], "noise_snare")
    hat_placed = fill_channel(req.hat_channel, drums["hat"], "noise_hat")

    return {
        "kick_channel": req.kick_channel,
        "snare_channel": req.snare_channel,
        "hat_channel": req.hat_channel,
        "kick_hits": kick_placed,
        "snare_hits": snare_placed,
        "hat_hits": hat_placed,
    }


# ---------------------------------------------------------------------------
# Arrangement / Sequence
# ---------------------------------------------------------------------------

@app.post("/songs/{song_id}/sequence/append", tags=["Sequence"])
def append_to_sequence(song_id: str, req: AppendSequenceRequest):
    """Append a pattern index to the song arrangement sequence."""
    song = _get_song(song_id)
    if not (0 <= req.pattern_index < len(song.patterns)):
        raise HTTPException(
            status_code=400,
            detail=f"Pattern index {req.pattern_index} out of range.",
        )
    song.append_to_sequence(req.pattern_index, req.repeat)
    return {"sequence": song.sequence, "duration_sec": song.total_duration_sec()}


@app.put("/songs/{song_id}/sequence", tags=["Sequence"])
def set_sequence(song_id: str, req: SetSequenceRequest):
    """Replace the arrangement sequence entirely."""
    song = _get_song(song_id)
    for idx in req.sequence:
        if not (0 <= idx < len(song.patterns)):
            raise HTTPException(
                status_code=400,
                detail=f"Pattern index {idx} is out of range (song has {len(song.patterns)} patterns).",
            )
    song.sequence = req.sequence
    return {"sequence": song.sequence, "duration_sec": song.total_duration_sec()}


@app.delete("/songs/{song_id}/sequence", tags=["Sequence"])
def clear_sequence(song_id: str):
    """Clear the arrangement sequence."""
    song = _get_song(song_id)
    song.sequence = []
    return {"sequence": [], "duration_sec": 0.0}


# ---------------------------------------------------------------------------
# Render + Export
# ---------------------------------------------------------------------------

@app.get("/songs/{song_id}/render", tags=["Export"])
def render_song_to_wav(song_id: str):
    """
    Render the song and return a downloadable 16-bit stereo WAV file.
    Longer songs may take a moment — rendering is synchronous.
    """
    song = _get_song(song_id)
    if not song.sequence:
        raise HTTPException(status_code=400, detail="Song has no sequence. Add patterns to the sequence first.")

    audio = render_song(song)
    wav_bytes = audio_to_wav_bytes(audio)
    safe_title = "".join(c for c in song.title if c.isalnum() or c in " _-").strip() or "song"

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.wav"'},
    )


@app.post("/songs/{song_id}/save", tags=["Export"])
def save_song_to_file(song_id: str, req: SaveSongRequest):
    """Save the song as a JSON file. Defaults to songs/{title}.chipforge.json."""
    song = _get_song(song_id)
    if req.filepath:
        filepath = req.filepath
    else:
        safe_title = "".join(c for c in song.title if c.isalnum() or c in " _-").strip() or "song"
        filepath = f"songs/{safe_title}.chipforge.json"

    saved_path = save_song(song, filepath)
    return {"saved_to": str(saved_path)}


# ---------------------------------------------------------------------------
# Power Endpoints — bulk song construction for agents
# ---------------------------------------------------------------------------

@app.post("/songs/build", tags=["Power"])
def build_song(req: BuildSongRequest) -> dict:
    """
    Build a complete song in a single API call.

    Accepts a full song description: patterns with channel note arrays,
    and an arrangement sequence. Returns the song_id.

    Example body:
    ```json
    {
      "title": "My Tune",
      "bpm": 140,
      "patterns": [
        {
          "name": "Loop A",
          "num_steps": 16,
          "channels": [
            {"instrument": "pulse_lead", "notes": [72,0,75,0,77,0,75,0,72,0,0,0,70,0,0,0]},
            {"instrument": "pulse_bass", "notes": [48,0,0,0,48,0,0,0,51,0,0,0,53,0,0,0]},
            {"instrument": "noise_kick", "notes": [60,0,0,0,0,0,0,0,60,0,0,0,0,0,0,0]},
            {"instrument": "noise_snare","notes": [0,0,0,0,60,0,0,0,0,0,0,0,60,0,0,0]}
          ]
        }
      ],
      "sequence": [0, 0, 0, 0]
    }
    ```
    """
    song_id = str(uuid.uuid4())
    song = Song(title=req.title, bpm=req.bpm, author=req.author)

    for p_data in req.patterns:
        num_channels = max(len(p_data.channels), DEFAULT_CHANNELS)
        num_steps = p_data.num_steps
        bpm = p_data.bpm if p_data.bpm is not None else req.bpm

        pattern = Pattern(
            name=p_data.name,
            num_steps=num_steps,
            num_channels=num_channels,
            bpm=bpm,
        )

        for ch_idx, ch_data in enumerate(p_data.channels):
            for step_idx, midi_note in enumerate(ch_data.notes[:num_steps]):
                if midi_note > 0:
                    pattern.set_note(ch_idx, step_idx, NoteEvent(
                        midi_note=midi_note,
                        velocity=ch_data.velocity,
                        duration_steps=ch_data.duration_steps,
                        instrument=ch_data.instrument,
                    ))

        song.patterns.append(pattern)

    song.sequence = req.sequence or list(range(len(song.patterns)))
    _songs[song_id] = song

    return {
        "song_id": song_id,
        "title": song.title,
        "bpm": song.bpm,
        "num_patterns": len(song.patterns),
        "sequence": song.sequence,
        "duration_sec": song.total_duration_sec(),
        "render_url": f"/songs/{song_id}/render",
    }


@app.post("/songs/generate", tags=["Power"])
def generate_song(req: GenerateSongRequest) -> dict:
    """
    Generate a complete song algorithmically from high-level parameters.

    Creates melodic patterns using scale walks and LFSR drum patterns.
    Returns the song_id — then call GET /songs/{id}/render for the WAV.
    """
    song_id = str(uuid.uuid4())
    song = Song(title=req.title, bpm=req.bpm, author="ChipForge Generator")

    root_midi = note_name_to_midi(req.key, req.key_octave)
    rng = random.Random(req.seed)

    # Melody instruments for rotation
    melody_instruments = ["pulse_lead", "wave_melody", "pulse_chime", "saw_lead"]
    bass_instruments = ["pulse_bass", "wave_bass", "sine_bass"]

    for pattern_num in range(req.num_patterns):
        num_channels = req.num_melody_channels + (2 if req.include_drums else 0) + 1  # +1 bass
        pattern = Pattern(
            name=f"Pattern {pattern_num + 1}",
            num_steps=req.num_steps,
            num_channels=num_channels,
            bpm=req.bpm,
        )

        # Channel 0: Bass line (one octave below root)
        bass_root = root_midi - 12
        bass_melody = generate_melody(
            root_midi=bass_root,
            scale_name=req.scale,
            num_steps=req.num_steps,
            octave_range=1,
            rest_probability=0.3,
            rng=rng,
        )
        bass_inst = bass_instruments[pattern_num % len(bass_instruments)]
        for step, note in enumerate(bass_melody):
            if note > 0:
                pattern.set_note(0, step, NoteEvent(
                    midi_note=note, velocity=0.85,
                    duration_steps=2, instrument=bass_inst,
                ))

        # Channels 1..N: Melody lines
        for mel_idx in range(req.num_melody_channels):
            channel = mel_idx + 1
            mel_inst = melody_instruments[(pattern_num + mel_idx) % len(melody_instruments)]
            # Higher melody channels play slightly higher
            octave_offset = mel_idx * 12
            melody = generate_melody(
                root_midi=root_midi + octave_offset,
                scale_name=req.scale,
                num_steps=req.num_steps,
                octave_range=2,
                rest_probability=0.15 + mel_idx * 0.1,
                rng=rng,
            )
            for step, note in enumerate(melody):
                if note > 0:
                    pattern.set_note(channel, step, NoteEvent(
                        midi_note=note, velocity=0.8 - mel_idx * 0.1,
                        duration_steps=1, instrument=mel_inst,
                    ))

        # Drum channels
        if req.include_drums:
            drum_base_channel = req.num_melody_channels + 1
            drums = generate_drum_pattern(
                num_steps=req.num_steps,
                kick_density=0.30,
                snare_density=0.25,
                hat_density=0.45,
                rng=rng,
            )
            for step, hit in enumerate(drums["kick"]):
                if hit and drum_base_channel < num_channels:
                    pattern.set_note(drum_base_channel, step, NoteEvent(
                        midi_note=60, velocity=0.80, duration_steps=1, instrument="noise_kick",
                    ))
            snare_chan = drum_base_channel + 1
            for step, hit in enumerate(drums["snare"]):
                if hit and snare_chan < num_channels:
                    pattern.set_note(snare_chan, step, NoteEvent(
                        midi_note=60, velocity=0.65, duration_steps=1, instrument="noise_snare",
                    ))

        song.patterns.append(pattern)

    # Arrangement: play all patterns in order, first one repeats at end
    if req.num_patterns == 1:
        song.sequence = [0, 0, 0, 0]
    elif req.num_patterns == 2:
        song.sequence = [0, 0, 1, 0, 0]
    else:
        # A A B A C A ... loop back to A at end
        seq = []
        for i in range(req.num_patterns):
            seq.extend([0, i] if i > 0 else [0, 0])
        seq.append(0)
        song.sequence = seq

    _songs[song_id] = song

    return {
        "song_id": song_id,
        "title": song.title,
        "bpm": song.bpm,
        "key": req.key,
        "scale": req.scale,
        "num_patterns": len(song.patterns),
        "sequence": song.sequence,
        "duration_sec": song.total_duration_sec(),
        "render_url": f"/songs/{song_id}/render",
    }
