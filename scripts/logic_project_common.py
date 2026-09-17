#!/usr/bin/env python3
"""
Shared helpers for the Logic Pro project analyzer scripts.

`logic_project_analyzer.py`, `logic_project_analyzer_enhanced.py` and
`extract_track_names.py` each carried their own near-identical copies of
directory scanning, plist reading, and key/time-signature formatting. This
module is the one place those now live; each script keeps its own CLI
behaviour, report shape and output — only these building blocks are shared.

Not a package: each script adds its own directory (`scripts/`) to
`sys.path[0]` automatically when run directly (`python3 scripts/foo.py`),
so `from logic_project_common import ...` resolves without an `__init__.py`.
"""

import plistlib
import re
from pathlib import Path
from typing import Dict, List, Optional

# Relative paths of the two plist files inside a .logicx bundle.
METADATA_PATH = "Alternatives/000/MetaData.plist"
PROJECT_INFO_PATH = "Resources/ProjectInformation.plist"


def scan_directory(base_path: Path) -> List[Path]:
    """
    Scan a directory for Logic Pro projects (*.logicx packages).

    Args:
        base_path: Directory to scan

    Returns:
        Sorted list of .logicx project paths
    """
    logicx_projects = []

    try:
        for item in base_path.glob("*.logicx"):
            if item.is_dir():
                logicx_projects.append(item)
    except PermissionError as e:
        print(f"Warning: Permission denied accessing directory: {e}")

    return sorted(logicx_projects, key=lambda p: p.name)


def extract_metadata_plist(project_path: Path, verbose_errors: bool = False) -> Optional[Dict]:
    """
    Extract metadata from MetaData.plist.

    Args:
        project_path: Path to .logicx project
        verbose_errors: Print a message for errors other than a missing or
            malformed plist (matches `logic_project_analyzer.py`'s original
            behaviour). The enhanced analyzer passes the default, False.

    Returns:
        Dictionary of metadata or None if error
    """
    plist_path = project_path / METADATA_PATH

    try:
        with open(plist_path, 'rb') as f:
            return plistlib.load(f)
    except FileNotFoundError:
        return None
    except plistlib.InvalidFileException:
        return None
    except Exception as e:
        if verbose_errors:
            print(f"Error reading {plist_path}: {e}")
        return None


def extract_project_info(project_path: Path) -> Optional[Dict]:
    """
    Extract project information from ProjectInformation.plist.

    Args:
        project_path: Path to .logicx project

    Returns:
        Dictionary of project info or None if error
    """
    plist_path = project_path / PROJECT_INFO_PATH

    try:
        with open(plist_path, 'rb') as f:
            return plistlib.load(f)
    except (FileNotFoundError, plistlib.InvalidFileException):
        return None
    except Exception:
        return None


def format_key_signature(key: str, mode: str) -> str:
    """
    Format key signature combining key and mode.

    Args:
        key: Musical key (e.g., "F#", "C")
        mode: Major or minor

    Returns:
        Formatted key signature (e.g., "F# minor")
    """
    if key == "Unknown" or mode == "Unknown":
        return "Unknown"
    return f"{key} {mode}"


def format_time_signature(numerator: int, denominator: int) -> str:
    """
    Format time signature.

    Args:
        numerator: Top number
        denominator: Bottom number

    Returns:
        Formatted time signature (e.g., "4/4")
    """
    if numerator == 0 or denominator == 0:
        return "Unknown"
    return f"{numerator}/{denominator}"


def extract_strings_from_binary(
    file_path: Path, min_length: int = 4, verbose_errors: bool = False
) -> List[str]:
    """
    Extract ASCII strings from a binary file.

    Args:
        file_path: Path to binary file
        min_length: Minimum string length to extract
        verbose_errors: Print a message on read failure (matches
            `extract_track_names.py`'s original behaviour). The analyzer
            scripts pass the default, False.

    Returns:
        List of extracted strings
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        pattern = b'[ -~]{' + str(min_length).encode() + b',}'
        strings_found = re.findall(pattern, data)

        return [s.decode('utf-8', errors='ignore') for s in strings_found]
    except Exception as e:
        if verbose_errors:
            print(f"Error reading {file_path}: {e}")
        return []


def extract_common_metadata_fields(metadata: Dict) -> Dict:
    """
    Pull the fields both `parse_project_data()` implementations read out of
    a MetaData.plist dictionary, before each script shapes its own return
    structure. `logic_project_analyzer.py` includes the surround-sound
    fields and every file list; `logic_project_analyzer_enhanced.py` adds
    binary-parsed track/plugin/chunk data on top and narrows `file_lists`
    to the four it reports — this only covers what both need in common.

    Args:
        metadata: MetaData.plist dictionary

    Returns:
        Dictionary of raw fields and file lists, plus an `errors` list
    """
    errors = []

    bpm = metadata.get('BeatsPerMinute', 0)
    if isinstance(bpm, (int, float)):
        bpm = round(float(bpm), 2)
    else:
        bpm = 0
        errors.append('Invalid BPM format')

    audio_files = metadata.get('AudioFiles', [])
    sampler_instruments = metadata.get('SamplerInstrumentsFiles', [])
    quicksampler_files = metadata.get('QuicksamplerFiles', [])
    impulse_responses = metadata.get('ImpulsResponsesFiles', [])
    alchemy_files = metadata.get('AlchemyFiles', [])
    ultrabeat_files = metadata.get('UltrabeatFiles', [])
    playback_files = metadata.get('PlaybackFiles', [])
    unused_audio = metadata.get('UnusedAudioFiles', [])

    total_samples = (
        len(audio_files) +
        len(sampler_instruments) +
        len(quicksampler_files) +
        len(impulse_responses) +
        len(alchemy_files) +
        len(ultrabeat_files) +
        len(playback_files)
    )

    return {
        'bpm': bpm,
        'key': metadata.get('SongKey', 'Unknown'),
        'mode': metadata.get('SongGenderKey', 'Unknown'),
        'time_sig_num': metadata.get('SongSignatureNumerator', 0),
        'time_sig_denom': metadata.get('SongSignatureDenominator', 0),
        'signature_key': metadata.get('SignatureKey', 0),
        'tracks': metadata.get('NumberOfTracks', 0),
        'sample_rate': metadata.get('SampleRate', 0),
        'frame_rate_index': metadata.get('FrameRateIndex', 0),
        'surround_format_index': metadata.get('SurroundFormatIndex', 0),
        'surround_mode_index': metadata.get('SurroundModeIndex', 0),
        'version': metadata.get('Version', 0),
        'has_ara_plugins': metadata.get('HasARAPlugins', False),
        'has_grid': metadata.get('HasGrid', False),
        'is_timecode_based': metadata.get('isTimeCodeBased', False),
        'audio_files': audio_files,
        'sampler_instruments': sampler_instruments,
        'quicksampler_files': quicksampler_files,
        'impulse_responses': impulse_responses,
        'alchemy_files': alchemy_files,
        'ultrabeat_files': ultrabeat_files,
        'playback_files': playback_files,
        'unused_audio_files': unused_audio,
        'total_samples': total_samples,
        'errors': errors,
    }
