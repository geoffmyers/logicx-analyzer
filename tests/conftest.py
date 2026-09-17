"""
Shared pytest fixtures for the logicx-analyzer test suite.

The scripts under `scripts/` are standalone CLI tools, not an installed
package: each adds its own directory to `sys.path[0]` when run directly
(`python3 scripts/foo.py`). Tests import them the same way, so this file
adds `scripts/` to `sys.path` once for the whole run.

Every fixture below builds a small SYNTHETIC `.logicx` bundle from scratch
(binary plists via `plistlib`, a hand-built `ProjectData` byte string) —
never a real Logic Pro project. Nothing here reads or depends on any of
the owner's own project files.
"""

from __future__ import annotations

import json
import plistlib
import struct
import sys
from pathlib import Path
from typing import Optional

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

METADATA_PATH = "Alternatives/000/MetaData.plist"
PROJECT_INFO_PATH = "Resources/ProjectInformation.plist"
PROJECT_DATA_PATH = "Alternatives/000/ProjectData"


def write_logicx_bundle(
    base_dir: Path,
    name: str = "SyntheticSong.logicx",
    metadata: Optional[dict] = None,
    proj_info: Optional[dict] = None,
    project_data: Optional[bytes] = None,
) -> Path:
    """
    Build one synthetic `.logicx` bundle under `base_dir` and return its path.

    Any of `metadata` / `proj_info` / `project_data` left as None is skipped
    entirely (so tests can exercise the "file not found" paths too).
    """
    bundle = base_dir / name
    (bundle / "Alternatives" / "000").mkdir(parents=True, exist_ok=True)
    (bundle / "Resources").mkdir(parents=True, exist_ok=True)

    if metadata is not None:
        with open(bundle / METADATA_PATH, "wb") as f:
            plistlib.dump(metadata, f, fmt=plistlib.FMT_BINARY)

    if proj_info is not None:
        with open(bundle / PROJECT_INFO_PATH, "wb") as f:
            plistlib.dump(proj_info, f, fmt=plistlib.FMT_BINARY)

    if project_data is not None:
        with open(bundle / PROJECT_DATA_PATH, "wb") as f:
            f.write(project_data)

    return bundle


DEFAULT_METADATA = {
    "BeatsPerMinute": 120.5,
    "SongKey": "C",
    "SongGenderKey": "major",
    "SongSignatureNumerator": 4,
    "SongSignatureDenominator": 4,
    "SignatureKey": 7,
    "NumberOfTracks": 3,
    "SampleRate": 48000,
    "FrameRateIndex": 2,
    "SurroundFormatIndex": 0,
    "SurroundModeIndex": 0,
    "Version": 1050,
    "HasARAPlugins": False,
    "HasGrid": True,
    "isTimeCodeBased": False,
    "AudioFiles": ["Media/kick.wav", "Media/snare.wav"],
    "SamplerInstrumentsFiles": [],
    "QuicksamplerFiles": [],
    "ImpulsResponsesFiles": [],
    "AlchemyFiles": ["Alchemy/Libraries/Pad.alp"],
    "UltrabeatFiles": [],
    "PlaybackFiles": [],
    "UnusedAudioFiles": ["Media/unused.wav"],
}

DEFAULT_PROJECT_INFO = {"LastSavedFrom": "11.1.0"}


def build_project_data_bytes() -> bytes:
    """
    A synthetic `ProjectData` binary blob carrying: the file's magic bytes,
    a `karT` (Track) marker followed by a plausible track name, a `gRuA`
    (AudioRegion) marker followed by a region name, an `Audio 2` generic
    track name, a big-endian float in the accepted tempo range (40-240),
    and an embedded Session Players preset as JSON — one instance of every
    "Decoded" shape the README's feature table and CLAUDE.md's chunk-marker
    table document.

    Two alignment rules the byte layout has to satisfy, or the parsers this
    fixture exists to exercise silently find nothing:

    - `extract_strings_from_binary()` extracts *runs* of printable ASCII
      (regex `[ -~]{4,}`), so a marker with no non-printable byte before its
      following name merges into one string ("karTLead Vocal") instead of
      two list entries — and `extract_track_names()` matches on an exact
      `string == "karT"` list entry followed by the next entry. Every
      marker/name/field below is separated by a NUL byte so each survives
      as its own extracted string.
    - `extract_tempo_data()` reads a big-endian float from every 4-byte-
      aligned offset counting from byte 0 of the file (non-overlapping
      `struct.unpack('>f', data[i:i+4])` at `i = 0, 4, 8, …`), not a sliding
      byte-by-byte scan. The embedded tempo candidate is padded to start on
      a multiple of 4 or it is never read at all.
    """
    preset_json = json.dumps(
        {
            "Preset": {
                "Name": "Sweet Memories",
                "CharacterIdentifier": "Acoustic Piano - Strummed",
                "Parameters": {"intensity": 5, "dynamics": 3},
            },
            "RegionType": "Type_AcousticPianoV2",
        }
    ).encode("utf-8")

    prefix = b"".join(
        [
            b"\x23\x47\xc0\xab",  # magic bytes
            b"\x00",
            b"karT",
            b"\x00",
            b"Lead Vocal",
            b"\x00",
            b"gRuA",
            b"\x00",
            b"Verse 1 Region",
            b"\x00",
            b"karT",
            b"\x00",
            b"Audio 2",
            b"\x00",
        ]
    )
    # Pad to a 4-byte boundary so the tempo float below lands on an offset
    # `extract_tempo_data()` actually reads (see docstring).
    prefix += b"\x00" * ((-len(prefix)) % 4)

    return b"".join(
        [
            prefix,
            struct.pack(">f", 120.5),  # tempo candidate in [40, 240]
            b"\x00",
            preset_json,
            b"\x00",
            b"Alchemy/Libraries/EPiano.alp Sampler Ultrabeat",
            b"\x00" * 8,
        ]
    )


@pytest.fixture
def synthetic_bundle(tmp_path: Path) -> Path:
    """A complete synthetic .logicx bundle: metadata, project info and
    binary ProjectData, all built in this fixture — never a real project."""
    return write_logicx_bundle(
        tmp_path,
        metadata=DEFAULT_METADATA,
        proj_info=DEFAULT_PROJECT_INFO,
        project_data=build_project_data_bytes(),
    )


@pytest.fixture
def synthetic_project_dir(tmp_path: Path) -> Path:
    """The directory containing `synthetic_bundle` (what `scan_directory`
    and the scripts' `main()` are pointed at)."""
    write_logicx_bundle(
        tmp_path,
        metadata=DEFAULT_METADATA,
        proj_info=DEFAULT_PROJECT_INFO,
        project_data=build_project_data_bytes(),
    )
    return tmp_path
