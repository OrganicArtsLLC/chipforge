"""
ChipForge Song Catalog
=======================
Lightweight JSON-based song index for browsing, filtering, and managing
a library of 2500+ songs. No database dependency — just a JSON file
that's rebuilt on demand from the songs/ directory.

The catalog stores metadata ABOUT songs, not the songs themselves.
Song code lives in .py files; the catalog is a fast lookup index.
"""

from __future__ import annotations

import json
import os
import re
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger("chipforge.catalog")

CATALOG_FILE = "songs/catalog.json"


@dataclass
class SongEntry:
    """Metadata for one song in the catalog."""
    id: str                      # e.g. "edm/010_strobe"
    title: str                   # e.g. "Strobe"
    artist: str                  # e.g. "Deadmau5"
    genre: str                   # e.g. "edm"
    subgenre: str = ""           # e.g. "progressive house"
    key: str = ""                # e.g. "F#m"
    bpm: int = 0                 # e.g. 128
    channels: int = 0            # e.g. 9
    duration_bars: int = 0       # e.g. 56
    version: str = "v1"          # e.g. "v4"
    file_path: str = ""          # e.g. "songs/edm/010_strobe.py"
    tags: list[str] = field(default_factory=list)  # e.g. ["progressive", "build", "emotional"]
    rating: Optional[str] = None # "favorite", "good", "not_good"
    ai_features: list[str] = field(default_factory=list)  # e.g. ["spectral_morph", "auto_counterpoint"]


@dataclass
class Catalog:
    """The full song catalog — serializable to/from JSON."""
    version: int = 1
    songs: list[SongEntry] = field(default_factory=list)

    def add(self, entry: SongEntry) -> None:
        # Replace existing entry with same id
        self.songs = [s for s in self.songs if s.id != entry.id]
        self.songs.append(entry)
        self.songs.sort(key=lambda s: s.id)

    def find(self, **kwargs) -> list[SongEntry]:
        """Filter songs by any field. E.g. find(genre="edm", bpm=128)."""
        results = self.songs
        for key, value in kwargs.items():
            if key == "bpm_min":
                results = [s for s in results if s.bpm >= value]
            elif key == "bpm_max":
                results = [s for s in results if s.bpm <= value]
            elif key == "tag":
                results = [s for s in results if value in s.tags]
            elif key == "search":
                pattern = value.lower()
                results = [s for s in results if pattern in s.title.lower()
                           or pattern in s.artist.lower()
                           or pattern in s.genre.lower()]
            elif hasattr(SongEntry, key):
                results = [s for s in results if getattr(s, key) == value]
        return results

    def stats(self) -> dict:
        """Summary statistics for the catalog."""
        genres = {}
        for s in self.songs:
            genres[s.genre] = genres.get(s.genre, 0) + 1
        return {
            "total_songs": len(self.songs),
            "genres": genres,
            "bpm_range": (
                min((s.bpm for s in self.songs if s.bpm > 0), default=0),
                max((s.bpm for s in self.songs if s.bpm > 0), default=0),
            ),
            "versions": {
                v: sum(1 for s in self.songs if s.version == v)
                for v in sorted(set(s.version for s in self.songs))
            },
        }

    def save(self, path: str = CATALOG_FILE) -> None:
        """Save catalog to JSON file."""
        data = {"version": self.version, "songs": [asdict(s) for s in self.songs]}
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Catalog saved: {len(self.songs)} songs → {path}")

    @classmethod
    def load(cls, path: str = CATALOG_FILE) -> "Catalog":
        """Load catalog from JSON file."""
        if not os.path.exists(path):
            logger.warning(f"No catalog at {path}, creating empty")
            return cls()
        with open(path) as f:
            data = json.load(f)
        catalog = cls(version=data.get("version", 1))
        for s in data.get("songs", []):
            catalog.songs.append(SongEntry(**s))
        logger.info(f"Catalog loaded: {len(catalog.songs)} songs from {path}")
        return catalog


def scan_songs_directory(root: str = "songs") -> Catalog:
    """
    Scan the songs/ directory and extract metadata from each .py file's docstring.

    Parses: title, key, BPM, channels, structure from the first docstring.
    This is the "rebuild catalog from source" operation.
    """
    catalog = Catalog()
    root_path = Path(root)

    for py_file in sorted(root_path.rglob("*.py")):
        if py_file.name.startswith("__"):
            continue

        rel_path = py_file.relative_to(root_path)
        genre = rel_path.parent.name if rel_path.parent.name != "." else "unknown"
        song_id = f"{genre}/{py_file.stem}"

        # Extract metadata from file header
        try:
            with open(py_file, "r") as f:
                content = f.read(3000)  # first 3KB for metadata
        except Exception:
            continue

        # Parse title from first line of docstring
        title = py_file.stem.replace("_", " ").title()
        # Remove leading number
        title = re.sub(r"^\d+\s*", "", title)

        # Parse key, BPM, channels from docstring
        key_match = re.search(r"Key:\s*(.+?)[\n,]", content)
        bpm_match = re.search(r"BPM:\s*(\d+)", content)
        ch_match = re.search(r"Channels?:\s*(\d+)", content)
        artist_match = re.search(r"[—–-]\s*(.+?)[\n\r]", content[:200])

        # Detect version
        version = "v1"
        if "_v4" in py_file.stem:
            version = "v4"
        elif "_v3" in py_file.stem:
            version = "v3"
        elif "_v2" in py_file.stem:
            version = "v2"

        # Detect AI features
        ai_features = []
        if "shaped_" in content:
            ai_features.append("shaped_instruments")
        if "spectral_morph" in content:
            ai_features.append("spectral_morph")
        if "generate_counterpoint" in content:
            ai_features.append("auto_counterpoint")
        if "auto_master" in content:
            ai_features.append("auto_mastering")
        if "analyze_mix" in content:
            ai_features.append("mix_analysis")

        entry = SongEntry(
            id=song_id,
            title=title,
            artist=artist_match.group(1).strip() if artist_match else "",
            genre=genre,
            key=key_match.group(1).strip() if key_match else "",
            bpm=int(bpm_match.group(1)) if bpm_match else 0,
            channels=int(ch_match.group(1)) if ch_match else 0,
            version=version,
            file_path=str(py_file),
            ai_features=ai_features,
        )
        catalog.add(entry)

    logger.info(f"Scanned {len(catalog.songs)} songs from {root}/")
    return catalog


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    catalog = scan_songs_directory()
    catalog.save()
    stats = catalog.stats()
    print(f"\nCatalog: {stats['total_songs']} songs")
    print(f"Genres: {stats['genres']}")
    print(f"BPM range: {stats['bpm_range']}")
    print(f"Versions: {stats['versions']}")
