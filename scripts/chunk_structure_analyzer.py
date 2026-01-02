#!/usr/bin/env python3
"""
Chunk Structure Analyzer - Parse the hierarchical chunk structure of ProjectData
Attempts to decode the full file structure including headers, chunks, and nested data.
"""

import struct
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ChunkType(Enum):
    """Known chunk types in Logic ProjectData."""
    TRACK = b'karT'
    AUDIO_REGION = b'gRuA'
    EVENT_SEQ = b'qSvE'
    MIDI_SEQ = b'qeSM'
    INSTRUMENT = b'tSnI'
    TEXT = b'tSxT'
    AUDIO_FILE = b'LFUA'
    AUDIO_FILE_ALT = b'lFuA'
    COMP = b'PMOC'
    TRANSFORM = b'snrT'
    CORE = b'MroC'
    UNKNOWN = b'????'


@dataclass
class Chunk:
    """Represents a chunk in the ProjectData file."""
    offset: int
    chunk_type: bytes
    size: Optional[int]
    data: bytes
    children: List['Chunk']
    metadata: Dict

    def __repr__(self):
        type_str = self.chunk_type.decode('latin-1', errors='ignore')
        return f"Chunk({type_str} @ 0x{self.offset:08x}, size={self.size}, children={len(self.children)})"


class ProjectDataParser:
    """Parses Logic ProjectData binary file."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        with open(file_path, 'rb') as f:
            self.data = f.read()
        self.size = len(self.data)
        self.offset = 0

    def parse_file_header(self) -> Dict:
        """Parse the file header."""
        if self.size < 256:
            return {'error': 'File too small'}

        header = {
            'magic': self.data[0:4].hex(),
            'header_bytes': self.data[0:64].hex(),
            'first_100_ascii': self._to_ascii(self.data[0:100])
        }

        # Look for version strings
        version_match = self.data[0:1000].find(b'Logic Pro')
        if version_match != -1:
            version_end = self.data[version_match:version_match+50].find(b'\x00')
            if version_end != -1:
                header['logic_version'] = self.data[version_match:version_match+version_end].decode('utf-8', errors='ignore')

        return header

    def find_all_chunks(self) -> List[Chunk]:
        """Find all top-level chunks in the file."""
        chunks = []

        # Known markers
        markers = [
            b'karT', b'gRuA', b'qSvE', b'qeSM', b'tSnI',
            b'tSxT', b'LFUA', b'lFuA', b'PMOC', b'snrT', b'MroC'
        ]

        # Find all marker positions
        marker_positions = []
        for marker in markers:
            offset = 0
            while True:
                pos = self.data.find(marker, offset)
                if pos == -1:
                    break
                marker_positions.append((pos, marker))
                offset = pos + 1

        # Sort by position
        marker_positions.sort()

        # Create chunks
        for i, (pos, marker) in enumerate(marker_positions):
            # Determine chunk size (distance to next marker or end of file)
            if i + 1 < len(marker_positions):
                next_pos = marker_positions[i + 1][0]
                chunk_size = next_pos - pos
            else:
                chunk_size = self.size - pos

            # Limit chunk size to reasonable value
            chunk_size = min(chunk_size, 100000)

            chunk_data = self.data[pos:pos+chunk_size]

            chunk = Chunk(
                offset=pos,
                chunk_type=marker,
                size=chunk_size,
                data=chunk_data,
                children=[],
                metadata={}
            )

            # Try to extract metadata
            chunk.metadata = self._analyze_chunk_data(chunk)

            chunks.append(chunk)

        return chunks

    def _analyze_chunk_data(self, chunk: Chunk) -> Dict:
        """Analyze chunk data to extract metadata."""
        metadata = {}
        data = chunk.data

        if len(data) < 4:
            return metadata

        # Skip the marker itself
        payload = data[4:]

        # Try to extract strings
        strings = []
        i = 0
        while i < min(len(payload), 512):
            # Look for length-prefixed strings
            if i + 1 < len(payload):
                length = payload[i]
                if 3 <= length <= 100 and i + 1 + length <= len(payload):
                    try:
                        s = payload[i+1:i+1+length].decode('utf-8', errors='ignore')
                        if self._is_printable_string(s):
                            strings.append({
                                'offset': i,
                                'string': s,
                                'method': 'length-prefix-1'
                            })
                    except:
                        pass
            i += 1

        if strings:
            metadata['strings'] = strings[:5]  # Keep first 5

        # Try to find numeric patterns
        if len(payload) >= 16:
            # Extract first few 32-bit values
            nums = []
            for offset in [0, 4, 8, 12]:
                if offset + 4 <= len(payload):
                    val_be = struct.unpack('>I', payload[offset:offset+4])[0]
                    nums.append(val_be)
            metadata['header_ints_be'] = nums

        # Look for JSON
        json_start = payload.find(b'{"')
        if json_start != -1 and json_start < 100:
            # Try to extract JSON
            try:
                # Find closing brace (simplified)
                json_end = payload.find(b'}\x00', json_start)
                if json_end != -1:
                    json_str = payload[json_start:json_end+1].decode('utf-8', errors='ignore')
                    try:
                        json_obj = json.loads(json_str)
                        if 'Preset' in json_obj:
                            metadata['preset_name'] = json_obj['Preset'].get('Name', 'Unknown')
                        elif 'Name' in json_obj:
                            metadata['name'] = json_obj.get('Name')
                    except:
                        metadata['has_json'] = True
            except:
                pass

        return metadata

    def _is_printable_string(self, s: str) -> bool:
        """Check if string is printable."""
        if len(s) < 3:
            return False
        printable = sum(1 for c in s if c.isprintable())
        alpha = sum(1 for c in s if c.isalpha())
        return printable / len(s) > 0.8 and alpha >= 2

    def _to_ascii(self, data: bytes) -> str:
        """Convert bytes to ASCII with dots for non-printable."""
        return ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)

    def generate_chunk_map(self) -> str:
        """Generate a visual map of chunks in the file."""
        chunks = self.find_all_chunks()

        # Group by type
        from collections import defaultdict
        by_type = defaultdict(list)
        for chunk in chunks:
            type_str = chunk.chunk_type.decode('latin-1', errors='ignore')
            by_type[type_str].append(chunk)

        report = []
        report.append("=" * 80)
        report.append(f"Chunk Structure Map: {self.file_path.name}")
        report.append("=" * 80)
        report.append(f"File size: {self.size:,} bytes")
        report.append(f"Total chunks found: {len(chunks)}")
        report.append("")

        # Summary by type
        report.append("CHUNK TYPE SUMMARY:")
        report.append("-" * 80)
        for chunk_type, chunk_list in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            report.append(f"  {chunk_type:8s} : {len(chunk_list):4d} chunks")
        report.append("")

        # Detailed chunk listing (first 50)
        report.append("CHUNK DETAILS (first 50):")
        report.append("-" * 80)

        for i, chunk in enumerate(chunks[:50]):
            type_str = chunk.chunk_type.decode('latin-1', errors='ignore')
            report.append(f"\n#{i+1:3d}. {type_str} @ offset 0x{chunk.offset:08x} (size: {chunk.size:,} bytes)")

            # Show metadata
            if chunk.metadata:
                if 'preset_name' in chunk.metadata:
                    report.append(f"     Preset: {chunk.metadata['preset_name']}")
                if 'name' in chunk.metadata:
                    report.append(f"     Name: {chunk.metadata['name']}")
                if 'strings' in chunk.metadata:
                    for s in chunk.metadata['strings'][:2]:
                        report.append(f"     String: '{s['string']}'")
                if 'header_ints_be' in chunk.metadata:
                    ints = chunk.metadata['header_ints_be']
                    report.append(f"     Header ints: {ints}")

        if len(chunks) > 50:
            report.append(f"\n... and {len(chunks) - 50} more chunks")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def analyze_track_name_candidates(self) -> List[Dict]:
        """Special analysis to find track names."""
        candidates = []

        # Find all karT markers
        chunks = [c for c in self.find_all_chunks() if c.chunk_type == b'karT']

        for chunk in chunks:
            # Analyze data around this track
            start = max(0, chunk.offset - 256)
            end = min(self.size, chunk.offset + 512)
            context = self.data[start:end]

            # Look for strings in context
            strings = self._extract_strings_from_bytes(context)

            # Filter likely track names
            likely_names = []
            for s in strings:
                if self._looks_like_track_name(s):
                    likely_names.append(s)

            if likely_names:
                candidates.append({
                    'track_offset': chunk.offset,
                    'possible_names': likely_names,
                    'context_start': start,
                    'context_end': end
                })

        return candidates

    def _extract_strings_from_bytes(self, data: bytes) -> List[str]:
        """Extract all printable strings from bytes."""
        import re
        strings = []
        pattern = rb'[ -~]{4,}'
        matches = re.findall(pattern, data)
        for match in matches:
            try:
                s = match.decode('utf-8', errors='ignore')
                strings.append(s)
            except:
                pass
        return strings

    def _looks_like_track_name(self, s: str) -> bool:
        """Check if string looks like a track name."""
        # Track names typically:
        # - Are 3-50 characters
        # - Start with letter or number
        # - Have reasonable character distribution

        if len(s) < 3 or len(s) > 50:
            return False

        if not (s[0].isalnum() or s[0].isspace()):
            return False

        # Filter out known garbage
        garbage = ['karT', 'gRuA', 'qSvE', 'qeSM', 'tSnI', 'LFUA', 'PMOC']
        if s in garbage:
            return False

        # Must have some letters
        alpha_count = sum(1 for c in s if c.isalpha())
        if alpha_count < len(s) * 0.3:
            return False

        return True


def main():
    """Main execution."""
    import sys

    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Find first ProjectData
        project_data_files = list(Path.cwd().glob("**/ProjectData"))
        if not project_data_files:
            print("No ProjectData files found.")
            return
        file_path = project_data_files[0]

    print(f"\nAnalyzing chunk structure: {file_path}\n")

    parser = ProjectDataParser(file_path)

    # Parse header
    print("Parsing file header...")
    header = parser.parse_file_header()
    print(f"Header: {json.dumps(header, indent=2)}\n")

    # Generate chunk map
    print("Generating chunk map...")
    chunk_map = parser.generate_chunk_map()
    print(chunk_map)

    # Save report
    output_path = Path.cwd() / f"chunk_structure_{file_path.parent.parent.parent.name}.txt"
    with open(output_path, 'w') as f:
        f.write("FILE HEADER:\n")
        f.write(json.dumps(header, indent=2))
        f.write("\n\n")
        f.write(chunk_map)

    print(f"\nReport saved: {output_path}")

    # Track name analysis
    print("\nAnalyzing track name candidates...")
    candidates = parser.analyze_track_name_candidates()
    if candidates:
        print(f"\nFound {len(candidates)} tracks with possible names:")
        for i, cand in enumerate(candidates[:10], 1):
            print(f"\nTrack #{i} at 0x{cand['track_offset']:08x}:")
            for name in cand['possible_names'][:3]:
                print(f"  - {name}")


if __name__ == "__main__":
    main()
