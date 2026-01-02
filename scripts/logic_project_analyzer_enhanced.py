#!/usr/bin/env python3
"""
Enhanced Logic Pro Project Analyzer with Binary Format Reverse Engineering
Analyzes Logic Pro projects (*.logicx) including metadata and advanced ProjectData parsing.
Extracts plugins, presets, Session Players configurations, and track information.

Based on reverse engineering research of Logic Pro ProjectData binary format.
"""

import plistlib
import csv
import re
import json
import struct
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import statistics
from typing import Dict, List, Optional, Tuple, Set


# Constants
METADATA_PATH = "Alternatives/000/MetaData.plist"
PROJECT_INFO_PATH = "Resources/ProjectInformation.plist"
PROJECT_DATA_PATH = "Alternatives/000/ProjectData"

# Known binary markers (reversed FourCC codes)
CHUNK_MARKERS = {
    b'karT': 'Track',
    b'gRuA': 'AudioRegion',
    b'qSvE': 'EventSequence',
    b'qeSM': 'MIDISequence',
    b'tSnI': 'Instrument',
    b'tSxT': 'TextStyle',
    b'LFUA': 'AudioFile',
    b'lFuA': 'AudioFileAlt',
    b'PMOC': 'Comp',
    b'MroC': 'CoreMIDI',
    b'snrT': 'Transform'
}


def extract_strings_from_binary(file_path: Path, min_length: int = 4) -> List[str]:
    """Extract ASCII strings from a binary file."""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        pattern = b'[ -~]{' + str(min_length).encode() + b',}'
        strings_found = re.findall(pattern, data)
        return [s.decode('utf-8', errors='ignore') for s in strings_found]
    except Exception:
        return []


def extract_json_objects(data: bytes) -> List[Dict]:
    """Extract embedded JSON objects from binary data (Session Players presets)."""
    json_objects = []
    i = 0

    while i < len(data) - 10:
        if data[i:i+2] == b'{"':
            # Found potential JSON start
            brace_count = 0
            start = i
            in_string = False
            escape = False

            for j in range(i, min(i + 100000, len(data))):
                byte = data[j]

                if escape:
                    escape = False
                    continue

                if byte == ord('\\'):
                    escape = True
                    continue

                if byte == ord('"') and not escape:
                    in_string = not in_string

                if not in_string:
                    if byte == ord('{'):
                        brace_count += 1
                    elif byte == ord('}'):
                        brace_count -= 1
                        if brace_count == 0:
                            # Found complete JSON
                            json_str = data[start:j+1].decode('utf-8', errors='ignore')
                            try:
                                obj = json.loads(json_str)
                                json_objects.append({
                                    'offset': start,
                                    'size': j - start + 1,
                                    'data': obj
                                })
                            except json.JSONDecodeError:
                                pass
                            i = j
                            break
        i += 1

    return json_objects


def extract_plugin_data(project_path: Path) -> Dict:
    """Extract plugin names, presets, and configurations from ProjectData."""
    project_data_path = project_path / PROJECT_DATA_PATH

    if not project_data_path.exists():
        return {
            'plugins': [],
            'presets': [],
            'alchemy_references': []
        }

    with open(project_data_path, 'rb') as f:
        data = f.read()

    plugins = set()
    alchemy_refs = set()

    # Extract plugin names
    strings = extract_strings_from_binary(project_data_path, min_length=5)

    for s in strings:
        # Alchemy library references
        if 'Alchemy/Libraries' in s:
            alchemy_refs.add(s)

        # Plugin identifiers
        if any(keyword in s for keyword in ['Alchemy', 'Sampler', 'Q-Sampler',
                                              'Ultrabeat', 'Sculpture', 'Retro Synth',
                                              'Vintage', 'ES1', 'ES2', 'ESM', 'ESE']):
            if len(s) < 100:  # Avoid long paths
                plugins.add(s)

    # Extract JSON presets (Session Players)
    json_objects = extract_json_objects(data)
    presets = []

    for obj in json_objects:
        preset_info = {
            'offset': obj['offset'],
            'type': None,
            'name': None,
            'character': None,
            'region_type': None,
            'parameters': {}
        }

        data_obj = obj['data']

        # Extract preset information
        if 'Preset' in data_obj:
            preset = data_obj['Preset']
            preset_info['name'] = preset.get('Name')
            preset_info['character'] = preset.get('CharacterIdentifier')
            preset_info['type'] = preset.get('Type')

            # Extract key parameters
            if 'Parameters' in preset:
                params = preset['Parameters']
                for key in ['intensity', 'dynamics', 'humanize', 'variation',
                           'fillsAmount', 'rComp', 'mComp', 'pushPull', 'swing',
                           'bassType', 'slidesAmount', 'riffiness', 'bluesyness',
                           'phraseVariation', 'accentVariation']:
                    if key in params:
                        preset_info['parameters'][key] = params[key]

        # Top-level data
        if 'CharacterIdentifier' in data_obj:
            preset_info['character'] = data_obj.get('CharacterIdentifier')
        if 'RegionType' in data_obj:
            preset_info['region_type'] = data_obj.get('RegionType')
        if 'PresetUniqueIdentifier' in data_obj:
            preset_info['preset_id'] = data_obj.get('PresetUniqueIdentifier')

        # Only add if we found meaningful data
        if preset_info['name'] or preset_info['character']:
            presets.append(preset_info)

    return {
        'plugins': list(plugins),
        'presets': presets,
        'alchemy_references': list(alchemy_refs)
    }


def count_chunk_markers(project_path: Path) -> Dict[str, int]:
    """Count occurrences of each chunk marker type."""
    project_data_path = project_path / PROJECT_DATA_PATH

    if not project_data_path.exists():
        return {}

    with open(project_data_path, 'rb') as f:
        data = f.read()

    counts = {}
    for marker_bytes, marker_name in CHUNK_MARKERS.items():
        count = data.count(marker_bytes)
        if count > 0:
            counts[marker_name] = count

    return counts


def extract_tempo_data(project_path: Path) -> List[float]:
    """Extract potential BPM values from binary data."""
    project_data_path = project_path / PROJECT_DATA_PATH

    if not project_data_path.exists():
        return []

    with open(project_data_path, 'rb') as f:
        data = f.read()

    tempos = set()
    i = 0

    while i < len(data) - 4:
        try:
            # Try big-endian float
            val = struct.unpack('>f', data[i:i+4])[0]
            if 40.0 <= val <= 240.0:
                tempos.add(round(val, 2))
        except:
            pass
        i += 4

    return sorted(list(tempos))[:10]  # Return top 10


def is_valid_name(name: str) -> bool:
    """
    Check if a string is likely a valid track/region name.
    Filters out binary garbage and invalid strings.
    """
    if len(name) < 3:
        return False

    # Filter out known garbage patterns and chunk markers
    garbage_patterns = [
        'karT', 'qSvE', 'qeSM', 'tSnI', 'tSxT', 'gRuA',
        'LFUA', 'lFuA', 'EVAW', 'PMOC', 'ffac', 'snrT', 'MroC'
    ]

    if name in garbage_patterns or name.startswith('reserved'):
        return False

    # Must start with alphanumeric or space
    if not (name[0].isalnum() or name[0].isspace()):
        return False

    # Check for valid character distribution
    alpha_count = sum(1 for c in name if c.isalpha())
    alpha_ratio = alpha_count / len(name)

    # At least 40% should be letters
    if alpha_ratio < 0.4:
        return False

    # Check for excessive special characters
    special_char_count = sum(1 for c in name if not (c.isalnum() or c.isspace() or c in '-_.,()[]#\'"/'))
    special_char_ratio = special_char_count / len(name)

    if special_char_ratio > 0.25:
        return False

    # Filter strings with weird patterns
    if len(name) >= 4 and len(name) <= 8:
        vowel_count = sum(1 for c in name.lower() if c in 'aeiou')
        if vowel_count == 0:
            return False

    # Filter encoding artifacts
    if len(name) >= 4:
        suffix = name[-3:].lower()
        if suffix in ['qoa', 'psa', 'ksa', 'iba', 'jba', 'uoa', 'poa', 'koa']:
            return False

    return True


def extract_track_names(project_path: Path) -> Tuple[List[str], List[str]]:
    """
    Extract track and region names from ProjectData binary file.
    Returns: Tuple of (track_names, region_names)
    """
    project_data_path = project_path / PROJECT_DATA_PATH

    if not project_data_path.exists():
        return ([], [])

    all_strings = extract_strings_from_binary(project_data_path)

    tracks = []
    regions = []

    # Extract track names (look for "karT" marker)
    for i, string in enumerate(all_strings):
        if string == "karT" and i + 1 < len(all_strings):
            next_string = all_strings[i + 1]
            if is_valid_name(next_string) and next_string not in tracks:
                tracks.append(next_string)

        # Extract region names (look for "gRuA" marker)
        if string == "gRuA" and i + 1 < len(all_strings):
            next_string = all_strings[i + 1]
            if is_valid_name(next_string) and next_string not in regions:
                regions.append(next_string)

        # Look for "Audio N" pattern
        if re.match(r'^\s*Audio\s+\d+$', string):
            track_name = string.strip()
            if track_name not in tracks:
                tracks.append(track_name)

    return (tracks, regions)


def scan_directory(base_path: Path) -> List[Path]:
    """Scan directory for Logic Pro projects."""
    logicx_projects = []
    try:
        for item in base_path.glob("*.logicx"):
            if item.is_dir():
                logicx_projects.append(item)
    except PermissionError as e:
        print(f"Warning: Permission denied accessing directory: {e}")
    return sorted(logicx_projects, key=lambda p: p.name)


def extract_metadata_plist(project_path: Path) -> Optional[Dict]:
    """Extract metadata from MetaData.plist file."""
    plist_path = project_path / METADATA_PATH
    try:
        with open(plist_path, 'rb') as f:
            return plistlib.load(f)
    except (FileNotFoundError, plistlib.InvalidFileException, Exception):
        return None


def extract_project_info(project_path: Path) -> Optional[Dict]:
    """Extract project information from ProjectInformation.plist."""
    plist_path = project_path / PROJECT_INFO_PATH
    try:
        with open(plist_path, 'rb') as f:
            return plistlib.load(f)
    except (FileNotFoundError, plistlib.InvalidFileException, Exception):
        return None


def format_key_signature(key: str, mode: str) -> str:
    """Format key signature combining key and mode."""
    if key == "Unknown" or mode == "Unknown":
        return "Unknown"
    return f"{key} {mode}"


def format_time_signature(numerator: int, denominator: int) -> str:
    """Format time signature."""
    if numerator == 0 or denominator == 0:
        return "Unknown"
    return f"{numerator}/{denominator}"


def parse_project_data(metadata: Dict, proj_info: Optional[Dict], project_path: Path) -> Dict:
    """Parse project data from metadata, project info plists, and binary ProjectData."""
    errors = []

    # Extract musical attributes
    bpm = metadata.get('BeatsPerMinute', 0)
    if isinstance(bpm, (int, float)):
        bpm = round(float(bpm), 2)
    else:
        bpm = 0
        errors.append('Invalid BPM format')

    key = metadata.get('SongKey', 'Unknown')
    mode = metadata.get('SongGenderKey', 'Unknown')
    time_sig_num = metadata.get('SongSignatureNumerator', 0)
    time_sig_denom = metadata.get('SongSignatureDenominator', 0)

    # Extract technical specs
    tracks = metadata.get('NumberOfTracks', 0)
    sample_rate = metadata.get('SampleRate', 0)
    frame_rate_index = metadata.get('FrameRateIndex', 0)
    version = metadata.get('Version', 0)
    has_ara = metadata.get('HasARAPlugins', False)
    has_grid = metadata.get('HasGrid', False)
    is_timecode = metadata.get('isTimeCodeBased', False)

    # Extract audio file lists
    audio_files = metadata.get('AudioFiles', [])
    sampler_instruments = metadata.get('SamplerInstrumentsFiles', [])
    quicksampler_files = metadata.get('QuicksamplerFiles', [])
    impulse_responses = metadata.get('ImpulsResponsesFiles', [])
    alchemy_files = metadata.get('AlchemyFiles', [])
    ultrabeat_files = metadata.get('UltrabeatFiles', [])
    playback_files = metadata.get('PlaybackFiles', [])
    unused_audio = metadata.get('UnusedAudioFiles', [])

    total_samples = (
        len(audio_files) + len(sampler_instruments) + len(quicksampler_files) +
        len(impulse_responses) + len(alchemy_files) + len(ultrabeat_files) +
        len(playback_files)
    )

    # NEW: Extract advanced binary data
    track_names, region_names = extract_track_names(project_path)
    plugin_data = extract_plugin_data(project_path)
    chunk_counts = count_chunk_markers(project_path)
    tempo_candidates = extract_tempo_data(project_path)

    # Extract project info
    logic_version = "Unknown"
    if proj_info:
        logic_version = proj_info.get('LastSavedFrom', 'Unknown')

    return {
        'name': project_path.stem,
        'path': project_path,
        'musical': {
            'bpm': bpm,
            'key': key,
            'mode': mode,
            'time_signature': format_time_signature(time_sig_num, time_sig_denom),
            'signature_key': metadata.get('SignatureKey', 0),
            'tempo_candidates': tempo_candidates  # NEW
        },
        'technical': {
            'tracks': tracks,
            'sample_rate': sample_rate,
            'frame_rate_index': frame_rate_index,
            'version': version,
            'logic_version': logic_version,
            'has_ara_plugins': has_ara,
            'has_grid': has_grid,
            'is_timecode_based': is_timecode
        },
        'audio_counts': {
            'audio_files': len(audio_files),
            'sampler_instruments': len(sampler_instruments),
            'quicksampler_files': len(quicksampler_files),
            'impulse_responses': len(impulse_responses),
            'alchemy_files': len(alchemy_files),
            'ultrabeat_files': len(ultrabeat_files),
            'playback_files': len(playback_files),
            'unused_audio_files': len(unused_audio),
            'total_samples': total_samples
        },
        'track_info': {
            'track_names': track_names,
            'track_count_found': len(track_names),
            'region_names': region_names,
            'region_count_found': len(region_names)
        },
        # NEW: Plugin and preset data
        'plugin_data': {
            'plugins': plugin_data['plugins'],
            'plugin_count': len(plugin_data['plugins']),
            'presets': plugin_data['presets'],
            'preset_count': len(plugin_data['presets']),
            'alchemy_references': plugin_data['alchemy_references'],
            'alchemy_ref_count': len(plugin_data['alchemy_references'])
        },
        # NEW: Binary structure data
        'binary_data': {
            'chunk_counts': chunk_counts,
            'total_chunks': sum(chunk_counts.values()) if chunk_counts else 0
        },
        'file_lists': {
            'audio_files': audio_files,
            'sampler_instruments': sampler_instruments,
            'quicksampler_files': quicksampler_files,
            'impulse_responses': impulse_responses
        },
        'errors': errors
    }


def calculate_statistics(projects: List[Dict]) -> Dict:
    """Calculate summary statistics across all projects."""
    if not projects:
        return {
            'total_projects': 0,
            'total_tracks': 0,
            'total_track_names_found': 0,
            'total_regions_found': 0,
            'total_plugins_found': 0,
            'total_presets_found': 0,
            'avg_tracks': 0,
            'avg_bpm': 0,
            'bpm_range': (0, 0),
            'key_distribution': {},
            'mode_distribution': {},
            'time_signatures': {},
            'sample_rates': {},
            'plugin_usage': {},
            'preset_usage': {}
        }

    tracks_list = [p['technical']['tracks'] for p in projects]
    bpms = [p['musical']['bpm'] for p in projects if p['musical']['bpm'] > 0]

    keys = []
    for p in projects:
        key = format_key_signature(p['musical']['key'], p['musical']['mode'])
        if key != "Unknown":
            keys.append(key)

    modes = [p['musical']['mode'] for p in projects if p['musical']['mode'] != 'Unknown']
    time_sigs = [p['musical']['time_signature'] for p in projects if p['musical']['time_signature'] != 'Unknown']
    sample_rates = [p['technical']['sample_rate'] for p in projects if p['technical']['sample_rate'] > 0]

    total_track_names = sum(p['track_info']['track_count_found'] for p in projects)
    total_regions = sum(p['track_info']['region_count_found'] for p in projects)

    # NEW: Plugin statistics
    all_plugins = []
    all_presets = []

    for p in projects:
        all_plugins.extend(p['plugin_data']['plugins'])
        for preset in p['plugin_data']['presets']:
            if preset.get('character'):
                all_presets.append(preset['character'])

    return {
        'total_projects': len(projects),
        'total_tracks': sum(tracks_list),
        'total_track_names_found': total_track_names,
        'total_regions_found': total_regions,
        'total_plugins_found': len(all_plugins),
        'total_presets_found': len(all_presets),
        'avg_tracks': round(statistics.mean(tracks_list), 2) if tracks_list else 0,
        'avg_bpm': round(statistics.mean(bpms), 2) if bpms else 0,
        'bpm_range': (min(bpms), max(bpms)) if bpms else (0, 0),
        'key_distribution': dict(Counter(keys)),
        'mode_distribution': dict(Counter(modes)),
        'time_signatures': dict(Counter(time_sigs)),
        'sample_rates': dict(Counter(sample_rates)),
        'plugin_usage': dict(Counter(all_plugins)),
        'preset_usage': dict(Counter(all_presets))
    }


def generate_markdown_report(projects: List[Dict], stats: Dict, output_path: Path):
    """Generate comprehensive Markdown report with all extracted data."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Advanced Logicx Analyzer Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Location:** {Path.cwd()}\n\n")

        f.write("**Note:** This report includes advanced binary analysis of ProjectData files.\n")
        f.write("Extracts plugins, presets, Session Players configurations, and chunk structure.\n")
        f.write("Based on reverse engineering research of Logic Pro binary format.\n\n")

        # Summary Statistics
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Projects:** {stats['total_projects']}\n")
        f.write(f"- **Total Tracks:** {stats['total_tracks']}\n")
        f.write(f"- **Track Names Extracted:** {stats['total_track_names_found']}\n")
        f.write(f"- **Audio Regions Extracted:** {stats['total_regions_found']}\n")
        f.write(f"- **Plugins Detected:** {stats['total_plugins_found']}\n")
        f.write(f"- **Presets Found:** {stats['total_presets_found']}\n")
        f.write(f"- **Average Tracks per Project:** {stats['avg_tracks']}\n")
        f.write(f"- **Average Tempo:** {stats['avg_bpm']} BPM\n")

        if stats['bpm_range'][0] > 0:
            f.write(f"- **Tempo Range:** {stats['bpm_range'][0]} - {stats['bpm_range'][1]} BPM\n")

        f.write("\n")

        # Plugin Usage
        if stats['plugin_usage']:
            f.write("## Plugin Usage\n\n")
            f.write("| Plugin | Projects |\n|--------|----------|\n")
            for plugin, count in sorted(stats['plugin_usage'].items(), key=lambda x: x[1], reverse=True)[:20]:
                # Truncate long plugin names
                plugin_display = plugin[:50] + '...' if len(plugin) > 50 else plugin
                f.write(f"| {plugin_display} | {count} |\n")
            f.write("\n")

        # Preset Usage (Session Players)
        if stats['preset_usage']:
            f.write("## Session Players Characters\n\n")
            f.write("| Character | Usage |\n|-----------|-------|\n")
            for preset, count in sorted(stats['preset_usage'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {preset} | {count} |\n")
            f.write("\n")

        # Key Distribution
        if stats['key_distribution']:
            f.write("## Key Distribution\n\n")
            f.write("| Key | Count |\n|-----|-------|\n")
            for key, count in sorted(stats['key_distribution'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {key} | {count} |\n")
            f.write("\n")

        # Project Details
        f.write("## Project Details\n\n")

        for idx, project in enumerate(projects, 1):
            f.write(f"### {idx}. {project['name']}\n\n")

            # Musical Attributes
            f.write("**Musical Attributes:**\n")
            f.write(f"- **Tempo:** {project['musical']['bpm']} BPM\n")
            f.write(f"- **Key:** {format_key_signature(project['musical']['key'], project['musical']['mode'])}\n")
            f.write(f"- **Time Signature:** {project['musical']['time_signature']}\n")
            f.write(f"- **Tracks:** {project['technical']['tracks']}\n")

            # Show tempo candidates if found
            if project['musical']['tempo_candidates']:
                tempos_str = ', '.join(str(t) for t in project['musical']['tempo_candidates'][:5])
                f.write(f"- **Tempo Candidates (from binary):** {tempos_str}\n")

            f.write("\n")

            # Binary Structure
            if project['binary_data']['chunk_counts']:
                f.write("**Binary Structure:**\n")
                f.write(f"- **Total Chunks:** {project['binary_data']['total_chunks']}\n")
                for chunk_type, count in sorted(project['binary_data']['chunk_counts'].items(),
                                               key=lambda x: x[1], reverse=True):
                    f.write(f"- **{chunk_type}:** {count}\n")
                f.write("\n")

            # Plugin Information
            if project['plugin_data']['plugins']:
                f.write(f"**Plugins ({project['plugin_data']['plugin_count']}):**\n")
                for plugin in sorted(set(project['plugin_data']['plugins']))[:10]:
                    plugin_display = plugin[:60] + '...' if len(plugin) > 60 else plugin
                    f.write(f"- {plugin_display}\n")
                if project['plugin_data']['plugin_count'] > 10:
                    f.write(f"- *(... and {project['plugin_data']['plugin_count'] - 10} more)*\n")
                f.write("\n")

            # Session Players Presets
            if project['plugin_data']['presets']:
                f.write(f"**Session Players Presets ({project['plugin_data']['preset_count']}):**\n")

                # Group by character
                presets_by_char = defaultdict(list)
                for preset in project['plugin_data']['presets']:
                    char = preset.get('character', 'Unknown')
                    presets_by_char[char].append(preset)

                for character, presets in sorted(presets_by_char.items()):
                    f.write(f"\n*{character}:*\n")
                    for preset in presets[:3]:  # Limit to 3 per character
                        if preset.get('name'):
                            f.write(f"- **{preset['name']}**")
                            if preset.get('region_type'):
                                f.write(f" ({preset['region_type']})")
                            f.write("\n")

                            # Show key parameters
                            if preset['parameters']:
                                params_str = ', '.join(f"{k}: {v}" for k, v in
                                                      list(preset['parameters'].items())[:5])
                                f.write(f"  - {params_str}\n")

                f.write("\n")

            # Alchemy References
            if project['plugin_data']['alchemy_references']:
                f.write(f"**Alchemy Library References ({project['plugin_data']['alchemy_ref_count']}):**\n")
                for ref in sorted(set(project['plugin_data']['alchemy_references']))[:10]:
                    f.write(f"- {ref}\n")
                if project['plugin_data']['alchemy_ref_count'] > 10:
                    f.write(f"- *(... and {project['plugin_data']['alchemy_ref_count'] - 10} more)*\n")
                f.write("\n")

            # Track Names
            if project['track_info']['track_names']:
                clean_tracks = project['track_info']['track_names']
                f.write(f"**Track Names ({len(clean_tracks)}):**\n")
                for track in clean_tracks[:20]:
                    f.write(f"- {track}\n")
                if len(clean_tracks) > 20:
                    f.write(f"- *(... and {len(clean_tracks) - 20} more)*\n")
                f.write("\n")

            # Region Names
            if project['track_info']['region_names']:
                clean_regions = project['track_info']['region_names']
                f.write(f"**Audio Regions ({len(clean_regions)}):**\n")
                for region in clean_regions[:10]:
                    f.write(f"- {region}\n")
                if len(clean_regions) > 10:
                    f.write(f"- *(... and {len(clean_regions) - 10} more)*\n")
                f.write("\n")

            # Audio Resources
            f.write("**Audio Resources:**\n")
            f.write(f"- **Audio Files:** {project['audio_counts']['audio_files']}\n")
            f.write(f"- **Sampler Instruments:** {project['audio_counts']['sampler_instruments']}\n")
            f.write(f"- **Quick Sampler:** {project['audio_counts']['quicksampler_files']}\n")
            f.write(f"- **Alchemy:** {project['audio_counts']['alchemy_files']}\n")
            f.write(f"- **Total Samples:** {project['audio_counts']['total_samples']}\n")
            f.write("\n")

            f.write("---\n\n")


def generate_json_report(projects: List[Dict], stats: Dict, output_path: Path):
    """Generate comprehensive JSON report with all data."""

    # Prepare data for JSON serialization
    json_data = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'location': str(Path.cwd()),
            'analyzer_version': '2.0',
            'total_projects': len(projects)
        },
        'summary_statistics': stats,
        'projects': []
    }

    # Add project data
    for project in projects:
        # Convert Path objects to strings for JSON serialization
        project_data = {
            'name': project['name'],
            'path': str(project['path']),
            'musical': project['musical'],
            'technical': project['technical'],
            'audio_counts': project['audio_counts'],
            'track_info': project['track_info'],
            'plugin_data': project['plugin_data'],
            'binary_data': project['binary_data'],
            'errors': project['errors']
        }

        json_data['projects'].append(project_data)

    # Write JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


def generate_csv_report(projects: List[Dict], stats: Dict, output_path: Path):
    """Generate CSV report with project summary data."""

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        # Define columns
        fieldnames = [
            'Project Name',
            'Tempo (BPM)',
            'Key',
            'Time Signature',
            'Tracks',
            'Sample Rate',
            'Logic Version',
            'Track Names Found',
            'Regions Found',
            'Plugins Count',
            'Presets Count',
            'Total Chunks',
            'Audio Files',
            'Total Samples',
            'Has ARA Plugins',
            'Top Plugin',
            'Top Preset Character'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for project in projects:
            # Find top plugin
            top_plugin = 'None'
            if project['plugin_data']['plugins']:
                top_plugin = project['plugin_data']['plugins'][0][:50]

            # Find top preset character
            top_preset = 'None'
            if project['plugin_data']['presets']:
                preset_chars = [p.get('character', '') for p in project['plugin_data']['presets']]
                if preset_chars:
                    char_counts = Counter(preset_chars)
                    if char_counts:
                        top_preset = char_counts.most_common(1)[0][0]

            row = {
                'Project Name': project['name'],
                'Tempo (BPM)': project['musical']['bpm'],
                'Key': format_key_signature(project['musical']['key'], project['musical']['mode']),
                'Time Signature': project['musical']['time_signature'],
                'Tracks': project['technical']['tracks'],
                'Sample Rate': project['technical']['sample_rate'],
                'Logic Version': project['technical']['logic_version'],
                'Track Names Found': project['track_info']['track_count_found'],
                'Regions Found': project['track_info']['region_count_found'],
                'Plugins Count': project['plugin_data']['plugin_count'],
                'Presets Count': project['plugin_data']['preset_count'],
                'Total Chunks': project['binary_data']['total_chunks'],
                'Audio Files': project['audio_counts']['audio_files'],
                'Total Samples': project['audio_counts']['total_samples'],
                'Has ARA Plugins': project['technical']['has_ara_plugins'],
                'Top Plugin': top_plugin,
                'Top Preset Character': top_preset
            }

            writer.writerow(row)


def generate_detailed_csv_report(projects: List[Dict], output_path: Path):
    """Generate detailed CSV with plugin and preset information."""

    rows = []

    for project in projects:
        # One row per plugin
        for plugin in project['plugin_data']['plugins'][:50]:  # Limit to 50 plugins
            rows.append({
                'Project': project['name'],
                'Type': 'Plugin',
                'Name': plugin[:100],
                'Category': 'Plugin',
                'Parameters': ''
            })

        # One row per preset
        for preset in project['plugin_data']['presets']:
            params_str = ', '.join(f"{k}={v}" for k, v in list(preset.get('parameters', {}).items())[:5])
            rows.append({
                'Project': project['name'],
                'Type': 'Preset',
                'Name': preset.get('name', 'Unknown'),
                'Category': preset.get('character', 'Unknown'),
                'Parameters': params_str
            })

    if rows:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Project', 'Type', 'Name', 'Category', 'Parameters']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def main():
    """Main execution function."""
    print("\n" + "=" * 70)
    print("Advanced Logic Pro Project Analyzer")
    print("with Binary Format Reverse Engineering")
    print("=" * 70 + "\n")

    base_dir = Path.cwd()
    print(f"Scanning directory: {base_dir}\n")

    project_paths = scan_directory(base_dir)

    if not project_paths:
        print("No Logic Pro projects found in current directory.")
        return

    print(f"Found {len(project_paths)} Logic Pro project(s)\n")

    # Process projects
    print("Processing projects:")
    projects = []

    for idx, project_path in enumerate(project_paths, 1):
        print(f"[{idx}/{len(project_paths)}] {project_path.name}...", end=' ')

        metadata = extract_metadata_plist(project_path)

        if metadata is None:
            print("✗ (MetaData.plist not found)")
            continue

        proj_info = extract_project_info(project_path)
        project_data = parse_project_data(metadata, proj_info, project_path)
        projects.append(project_data)

        print("✓")

    if not projects:
        print("\nNo valid projects found to analyze.")
        return

    print(f"\nSuccessfully processed {len(projects)} project(s)")

    # Calculate statistics
    print("\nCalculating statistics...")
    stats = calculate_statistics(projects)

    # Generate reports in all formats
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"logic_projects_advanced_{timestamp}"

    markdown_output = base_dir / f"{base_filename}.md"
    json_output = base_dir / f"{base_filename}.json"
    csv_output = base_dir / f"{base_filename}.csv"
    csv_detailed_output = base_dir / f"{base_filename}_detailed.csv"

    print("\nGenerating reports in multiple formats...")

    print("  - Markdown report...")
    generate_markdown_report(projects, stats, markdown_output)

    print("  - JSON report...")
    generate_json_report(projects, stats, json_output)

    print("  - CSV summary report...")
    generate_csv_report(projects, stats, csv_output)

    print("  - CSV detailed report...")
    generate_detailed_csv_report(projects, csv_detailed_output)

    # Summary
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print(f"\nTotal Projects: {len(projects)}")
    print(f"Total Tracks: {stats['total_tracks']}")
    print(f"Track Names Found: {stats['total_track_names_found']}")
    print(f"Audio Regions Found: {stats['total_regions_found']}")
    print(f"Plugins Detected: {stats['total_plugins_found']}")
    print(f"Presets Found: {stats['total_presets_found']}")
    print(f"Average Tempo: {stats['avg_bpm']} BPM")
    print(f"\nReports Generated:")
    print(f"  📄 Markdown: {markdown_output.name}")
    print(f"  📊 JSON:     {json_output.name}")
    print(f"  📈 CSV:      {csv_output.name}")
    print(f"  📋 CSV Det:  {csv_detailed_output.name}")
    print()


if __name__ == "__main__":
    main()
