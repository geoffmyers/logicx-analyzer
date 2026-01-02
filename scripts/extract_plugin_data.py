#!/usr/bin/env python3
"""
Extract Plugin and Instrument Configuration from ProjectData
Decodes plugin names, presets, and parameters embedded in the binary file.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict


class PluginDataExtractor:
    """Extracts plugin and instrument data from Logic ProjectData."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        with open(file_path, 'rb') as f:
            self.data = f.read()

    def extract_json_objects(self) -> List[Dict]:
        """Extract embedded JSON objects (often contain plugin presets)."""
        json_objects = []

        # Find patterns that look like JSON
        # Look for {"key":"value"...}
        i = 0
        while i < len(self.data) - 10:
            if self.data[i:i+2] == b'{"':
                # Found potential JSON start
                # Find the matching closing brace
                brace_count = 0
                start = i
                in_string = False
                escape = False

                for j in range(i, min(i + 1000000, len(self.data))):
                    byte = self.data[j]

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
                                # Found complete JSON object
                                json_str = self.data[start:j+1].decode('utf-8', errors='ignore')
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

    def extract_plugin_names(self) -> Set[str]:
        """Extract plugin/instrument names from the file."""
        plugins = set()

        # Common Logic plugin/instrument name patterns
        patterns = [
            rb'[A-Z][a-zA-Z0-9 ]{3,30}\.(component|vst|vst3|au)',
            rb'ES[ME][0-9]',  # ES1, ES2, ESM, ESE, etc.
            rb'Alchemy',
            rb'Sampler',
            rb'Ultrabeat',
            rb'Sculpture',
            rb'Retro Synth',
            rb'Vintage [A-Z][a-z]+',
        ]

        # Extract using regex
        for pattern in patterns:
            matches = re.findall(pattern, self.data)
            for match in matches:
                plugins.add(match.decode('utf-8', errors='ignore'))

        # Also look in extracted strings
        strings = self._extract_readable_strings(min_length=5, max_length=50)
        for s in strings:
            # Look for known plugin indicators
            if any(keyword in s for keyword in [
                'Alchemy', 'Sampler', 'Ultrabeat', 'EXS24',
                'Vintage', 'Sculpture', 'Retro Synth',
                '.component', '.vst', '.au'
            ]):
                plugins.add(s)

        return plugins

    def extract_preset_names(self) -> List[Dict]:
        """Extract preset names and their contexts."""
        presets = []

        # Look for JSON presets
        json_objects = self.extract_json_objects()

        for obj in json_objects:
            data = obj['data']
            preset_info = {
                'offset': obj['offset'],
                'type': None,
                'name': None,
                'character': None,
                'parameters': {}
            }

            # Check for preset structure
            if 'Preset' in data:
                preset = data['Preset']
                if 'Name' in preset:
                    preset_info['name'] = preset['Name']
                if 'CharacterIdentifier' in preset:
                    preset_info['character'] = preset['CharacterIdentifier']
                if 'Type' in preset:
                    preset_info['type'] = preset['Type']

                # Extract parameters
                if 'Parameters' in preset:
                    params = preset['Parameters']
                    # Get musical/interesting parameters
                    for key in ['intensity', 'dynamics', 'humanize', 'variation',
                               'fillsAmount', 'rComp', 'mComp']:
                        if key in params:
                            preset_info['parameters'][key] = params[key]

            # Also check top level
            if 'Name' in data:
                preset_info['name'] = data.get('Name')
            if 'CharacterIdentifier' in data:
                preset_info['character'] = data.get('CharacterIdentifier')
            if 'PresetUniqueIdentifier' in data:
                preset_info['preset_id'] = data.get('PresetUniqueIdentifier')
            if 'RegionType' in data:
                preset_info['region_type'] = data.get('RegionType')

            if preset_info['name'] or preset_info['character']:
                presets.append(preset_info)

        return presets

    def extract_audio_file_references(self) -> List[str]:
        """Extract audio file paths referenced in the project."""
        audio_files = []

        # Common audio file extensions
        patterns = [
            rb'[^\\x00]{3,200}\.(wav|aif|aiff|mp3|m4a|caf|raw)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, self.data, re.IGNORECASE)
            for match in matches:
                path = match.decode('utf-8', errors='ignore')
                if len(path) > 3 and '/' in path or '\\' in path:
                    audio_files.append(path)

        return list(set(audio_files))

    def extract_track_info_detailed(self) -> List[Dict]:
        """Extract detailed track information."""
        tracks = []

        # Find "karT" markers and analyze context
        offset = 0
        while True:
            pos = self.data.find(b'karT', offset)
            if pos == -1:
                break

            track_info = {
                'offset': pos,
                'marker': 'karT',
            }

            # Look for track name in next 200 bytes
            chunk = self.data[pos+4:pos+200]

            # Method 1: Find first reasonable string
            match = re.search(rb'[ -~]{4,}', chunk)
            if match:
                potential_name = match.group(0).decode('utf-8', errors='ignore')
                if self._is_valid_track_name(potential_name):
                    track_info['name'] = potential_name

            # Method 2: Look for specific byte patterns before string
            # Sometimes track names are prefixed with length or type bytes
            for skip in range(1, 20):
                if pos + 4 + skip < len(self.data):
                    byte_val = self.data[pos + 4 + skip]
                    # Check if this byte could be a length prefix
                    if 3 <= byte_val <= 100:
                        potential = self.data[pos + 5 + skip:pos + 5 + skip + byte_val]
                        if self._is_mostly_printable(potential):
                            name = potential.decode('utf-8', errors='ignore')
                            if self._is_valid_track_name(name):
                                track_info[f'name_method_{skip}'] = name

            tracks.append(track_info)
            offset = pos + 1

        return tracks

    def extract_tempo_changes(self) -> List[Dict]:
        """Extract tempo/BPM information from the file."""
        tempo_data = []

        # Look for float values in reasonable BPM range (40-240)
        import struct

        i = 0
        while i < len(self.data) - 8:
            # Try big-endian float
            try:
                val_be = struct.unpack('>f', self.data[i:i+4])[0]
                if 40.0 <= val_be <= 240.0:
                    tempo_data.append({
                        'offset': i,
                        'value': round(val_be, 2),
                        'endian': 'big',
                        'context': self._get_context_string(i)
                    })
            except:
                pass

            # Try little-endian float
            try:
                val_le = struct.unpack('<f', self.data[i:i+4])[0]
                if 40.0 <= val_le <= 240.0:
                    tempo_data.append({
                        'offset': i,
                        'value': round(val_le, 2),
                        'endian': 'little',
                        'context': self._get_context_string(i)
                    })
            except:
                pass

            i += 4

        return tempo_data

    def _extract_readable_strings(self, min_length: int = 4, max_length: int = 100) -> List[str]:
        """Extract human-readable strings."""
        pattern = rb'[ -~]{' + str(min_length).encode() + b',' + str(max_length).encode() + b'}'
        matches = re.findall(pattern, self.data)
        return [m.decode('utf-8', errors='ignore') for m in matches]

    def _is_mostly_printable(self, data: bytes, threshold: float = 0.8) -> bool:
        """Check if data is mostly printable."""
        if not data:
            return False
        printable_count = sum(1 for b in data if 32 <= b <= 126)
        return (printable_count / len(data)) >= threshold

    def _is_valid_track_name(self, name: str) -> bool:
        """Check if string is a valid track name."""
        if len(name) < 3 or len(name) > 100:
            return False

        # Must have some letters
        alpha_count = sum(1 for c in name if c.isalpha())
        if alpha_count < len(name) * 0.3:
            return False

        # Filter known garbage markers
        garbage = ['karT', 'gRuA', 'qSvE', 'qeSM', 'tSnI', 'LFUA']
        if name in garbage:
            return False

        return True

    def _get_context_string(self, offset: int, size: int = 20) -> str:
        """Get printable context around an offset."""
        start = max(0, offset - size)
        end = min(len(self.data), offset + size)
        chunk = self.data[start:end]

        result = []
        for b in chunk:
            if 32 <= b <= 126:
                result.append(chr(b))
            else:
                result.append('.')
        return ''.join(result)

    def generate_report(self) -> str:
        """Generate comprehensive extraction report."""
        report = []
        report.append("=" * 80)
        report.append(f"Plugin & Data Extraction: {self.file_path.name}")
        report.append("=" * 80)
        report.append("")

        # Plugin names
        report.append("PLUGINS/INSTRUMENTS DETECTED:")
        report.append("-" * 80)
        plugins = self.extract_plugin_names()
        for plugin in sorted(plugins):
            report.append(f"  - {plugin}")
        report.append(f"\nTotal: {len(plugins)} unique plugins")
        report.append("")

        # Presets
        report.append("PRESETS FOUND:")
        report.append("-" * 80)
        presets = self.extract_preset_names()
        preset_names = defaultdict(list)

        for preset in presets:
            if preset.get('name'):
                char = preset.get('character', 'Unknown')
                preset_names[char].append(preset['name'])

        for character, names in sorted(preset_names.items()):
            report.append(f"\n{character}:")
            for name in sorted(set(names)):
                report.append(f"  - {name}")

        report.append(f"\nTotal: {len(presets)} preset configurations")
        report.append("")

        # Audio files
        report.append("AUDIO FILE REFERENCES:")
        report.append("-" * 80)
        audio_files = self.extract_audio_file_references()
        for i, path in enumerate(sorted(set(audio_files))[:30], 1):
            report.append(f"  {i:3d}. {path}")
        if len(audio_files) > 30:
            report.append(f"  ... and {len(audio_files) - 30} more files")
        report.append(f"\nTotal: {len(set(audio_files))} unique audio files")
        report.append("")

        # Tempo data
        report.append("TEMPO/BPM DATA:")
        report.append("-" * 80)
        tempos = self.extract_tempo_changes()
        # Get unique tempo values
        unique_tempos = {}
        for t in tempos:
            val = t['value']
            if val not in unique_tempos:
                unique_tempos[val] = t

        for tempo_val in sorted(unique_tempos.keys())[:20]:
            t = unique_tempos[tempo_val]
            report.append(f"  {t['value']:7.2f} BPM at offset {t['offset']:08x} ({t['endian']})")

        report.append(f"\nTotal: {len(unique_tempos)} unique tempo values found")
        report.append("")

        report.append("=" * 80)

        return "\n".join(report)


def main():
    """Main execution."""
    import sys

    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Find first ProjectData in current directory
        project_data_files = list(Path.cwd().glob("**/*ProjectData"))
        if not project_data_files:
            project_data_files = list(Path.cwd().glob("**/ProjectData"))
        if not project_data_files:
            print("No ProjectData files found. Please specify a file path.")
            return
        file_path = project_data_files[0]

    print(f"\nExtracting plugin data from: {file_path}\n")

    extractor = PluginDataExtractor(file_path)
    report = extractor.generate_report()

    print(report)

    # Save detailed JSON output
    output_path = Path.cwd() / f"plugin_data_{file_path.parent.parent.parent.name}.txt"
    with open(output_path, 'w') as f:
        f.write(report)

    # Also save JSON data
    json_output = Path.cwd() / f"plugin_data_{file_path.parent.parent.parent.name}.json"
    detailed_data = {
        'plugins': list(extractor.extract_plugin_names()),
        'presets': extractor.extract_preset_names(),
        'audio_files': extractor.extract_audio_file_references(),
    }

    with open(json_output, 'w') as f:
        json.dump(detailed_data, f, indent=2)

    print(f"\nReports saved:")
    print(f"  - {output_path}")
    print(f"  - {json_output}")


if __name__ == "__main__":
    main()
