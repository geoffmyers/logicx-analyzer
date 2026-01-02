#!/usr/bin/env python3
"""
Deep Binary Format Analyzer for Logic Pro ProjectData Files
Reverse engineers the binary structure to identify and decode additional data.
"""

import struct
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import binascii


class BinaryChunk:
    """Represents a chunk of data in the binary file."""
    def __init__(self, offset: int, size: int, chunk_type: str, data: bytes):
        self.offset = offset
        self.size = size
        self.chunk_type = chunk_type
        self.data = data


class ProjectDataAnalyzer:
    """Analyzes Logic Pro ProjectData binary format."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        with open(file_path, 'rb') as f:
            self.data = f.read()
        self.size = len(self.data)

    def find_magic_markers(self) -> Dict[str, List[int]]:
        """Find all occurrences of potential magic markers (4-byte sequences)."""
        markers = defaultdict(list)

        # Common 4-byte markers seen in Logic files
        known_markers = [
            b'karT',  # Track marker (reverse "Trak")
            b'gRuA',  # Audio region (reverse "AuRg")
            b'LFUA',  # Audio File
            b'lFuA',  # Audio file variant
            b'EVAW',  # WAVE
            b'PMOC',  # COMP
            b'tSnI',  # Instrument
            b'tSxT',  # Text
            b'qSvE',  # EvSq (Event Sequence?)
            b'qeSM',  # MSeq (MIDI Sequence?)
            b'snrT',  # Trans (Transpose?)
            b'dddd',  # Unknown repeating pattern
            b'TFEL',  # LEFT
            b'THGR',  # RIGHT
            b'RTSM',  # MSTR (Master?)
        ]

        for marker in known_markers:
            offset = 0
            while True:
                pos = self.data.find(marker, offset)
                if pos == -1:
                    break
                markers[marker.decode('latin-1')].append(pos)
                offset = pos + 1

        return dict(markers)

    def extract_pascal_strings(self) -> List[Tuple[int, str]]:
        """
        Extract Pascal-style strings (length-prefixed strings).
        Format: [1-byte length][string data]
        """
        strings = []
        i = 0

        while i < self.size - 1:
            length = self.data[i]

            # Reasonable string length (1-255)
            if 1 <= length <= 255 and i + length + 1 <= self.size:
                try:
                    string_data = self.data[i+1:i+1+length]
                    # Check if it's mostly printable ASCII
                    if self._is_mostly_printable(string_data):
                        decoded = string_data.decode('utf-8', errors='ignore')
                        if len(decoded) >= 3:  # Minimum useful string
                            strings.append((i, decoded))
                except (UnicodeDecodeError, ValueError):
                    pass
            i += 1

        return strings

    def extract_length_prefixed_strings(self) -> List[Tuple[int, str, str]]:
        """
        Extract strings with various length-prefix formats.
        Returns: [(offset, string, format_type)]
        """
        strings = []
        i = 0

        while i < self.size - 4:
            # Try 1-byte length prefix (Pascal style)
            len1 = self.data[i]
            if 3 <= len1 <= 100 and i + len1 + 1 <= self.size:
                chunk = self.data[i+1:i+1+len1]
                if self._is_mostly_printable(chunk):
                    try:
                        decoded = chunk.decode('utf-8', errors='ignore')
                        if self._is_valid_string(decoded):
                            strings.append((i, decoded, "pascal-1byte"))
                    except:
                        pass

            # Try 2-byte big-endian length prefix
            len2 = struct.unpack('>H', self.data[i:i+2])[0]
            if 3 <= len2 <= 1000 and i + len2 + 2 <= self.size:
                chunk = self.data[i+2:i+2+len2]
                if self._is_mostly_printable(chunk):
                    try:
                        decoded = chunk.decode('utf-8', errors='ignore')
                        if self._is_valid_string(decoded):
                            strings.append((i, decoded, "2byte-be"))
                    except:
                        pass

            # Try 4-byte big-endian length prefix
            if i + 4 <= self.size:
                len4 = struct.unpack('>I', self.data[i:i+4])[0]
                if 3 <= len4 <= 10000 and i + len4 + 4 <= self.size:
                    chunk = self.data[i+4:i+4+len4]
                    if self._is_mostly_printable(chunk):
                        try:
                            decoded = chunk.decode('utf-8', errors='ignore')
                            if self._is_valid_string(decoded):
                                strings.append((i, decoded, "4byte-be"))
                        except:
                            pass

            i += 1

        return strings

    def find_numeric_patterns(self) -> Dict[str, List[Tuple[int, float]]]:
        """Find numeric data patterns (floats, ints, etc)."""
        patterns = {
            'float32': [],
            'float64': [],
            'int32': [],
            'int16': [],
        }

        i = 0
        while i < self.size - 8:
            # Try float32
            if i + 4 <= self.size:
                try:
                    val = struct.unpack('>f', self.data[i:i+4])[0]
                    # Look for reasonable BPM, time, or musical values
                    if 0 < val < 1000 and val != float('inf') and val == val:  # not NaN
                        patterns['float32'].append((i, val))
                except:
                    pass

            # Try int32 (could be sample positions, frame counts)
            if i + 4 <= self.size:
                try:
                    val = struct.unpack('>i', self.data[i:i+4])[0]
                    if 0 < val < 1000000000:  # Reasonable range
                        patterns['int32'].append((i, val))
                except:
                    pass

            i += 4

        return patterns

    def analyze_structure_around_marker(self, marker: str, offset: int,
                                        context_before: int = 32,
                                        context_after: int = 128) -> Dict:
        """Analyze the binary structure around a known marker."""
        start = max(0, offset - context_before)
        end = min(self.size, offset + len(marker) + context_after)

        chunk = self.data[start:end]

        analysis = {
            'offset': offset,
            'marker': marker,
            'hex_before': binascii.hexlify(self.data[max(0, offset-16):offset]).decode(),
            'hex_after': binascii.hexlify(self.data[offset+len(marker):min(self.size, offset+len(marker)+32)]).decode(),
            'ascii_before': self._safe_ascii(self.data[max(0, offset-16):offset]),
            'ascii_after': self._safe_ascii(self.data[offset+len(marker):min(self.size, offset+len(marker)+64)]),
        }

        # Try to extract following string
        after_marker = offset + len(marker)

        # Try various string extraction methods
        if after_marker < self.size:
            # Method 1: Null-terminated string
            null_pos = self.data.find(b'\x00', after_marker, after_marker + 128)
            if null_pos != -1:
                potential = self.data[after_marker:null_pos]
                if self._is_mostly_printable(potential):
                    analysis['null_terminated_string'] = potential.decode('utf-8', errors='ignore')

            # Method 2: Length-prefixed (1 byte)
            str_len = self.data[after_marker]
            if 0 < str_len < 128 and after_marker + str_len + 1 <= self.size:
                potential = self.data[after_marker+1:after_marker+1+str_len]
                if self._is_mostly_printable(potential):
                    analysis['length_prefixed_string'] = potential.decode('utf-8', errors='ignore')

            # Method 3: Fixed-offset string (skip N bytes then read)
            for skip in [1, 2, 4, 8]:
                if after_marker + skip < self.size:
                    next_bytes = self.data[after_marker+skip:after_marker+skip+64]
                    # Find first printable sequence
                    match = re.search(b'[ -~]{4,}', next_bytes)
                    if match:
                        analysis[f'string_at_offset_{skip}'] = match.group(0).decode('utf-8', errors='ignore')

        return analysis

    def find_repeating_structures(self, min_size: int = 8, max_size: int = 256) -> List[Dict]:
        """Identify repeating binary structures that might indicate records/chunks."""
        patterns = []

        # Look for patterns like: [4-byte type][4-byte size][data]
        i = 0
        while i < self.size - 8:
            # Try to find chunk-like structures
            potential_type = self.data[i:i+4]

            # Check if it looks like a 4CC code (four-character code)
            if self._is_mostly_printable(potential_type):
                # Next 4 bytes might be size
                if i + 8 <= self.size:
                    size_be = struct.unpack('>I', self.data[i+4:i+8])[0]
                    size_le = struct.unpack('<I', self.data[i+4:i+8])[0]

                    # Check if size makes sense (not too big, not too small)
                    for size, endian in [(size_be, 'big'), (size_le, 'little')]:
                        if 8 <= size <= 100000 and i + 8 + size <= self.size:
                            patterns.append({
                                'offset': i,
                                'type': potential_type.decode('latin-1'),
                                'size': size,
                                'endian': endian,
                                'data_preview': binascii.hexlify(self.data[i+8:i+16]).decode()
                            })

            i += 1

        return patterns

    def extract_track_data_advanced(self) -> List[Dict]:
        """Advanced track data extraction using pattern analysis."""
        tracks = []

        # Find all "karT" markers
        markers = self.find_magic_markers()

        if 'karT' in markers:
            for offset in markers['karT']:
                analysis = self.analyze_structure_around_marker('karT', offset)

                # Extract any found strings
                track_info = {
                    'offset': offset,
                    'marker': 'karT',
                }

                # Try to find track name from various methods
                for key in ['null_terminated_string', 'length_prefixed_string',
                           'string_at_offset_1', 'string_at_offset_2',
                           'string_at_offset_4', 'string_at_offset_8']:
                    if key in analysis and analysis[key]:
                        track_info['possible_name'] = analysis[key]
                        break

                # Add hex context for manual inspection
                track_info['hex_context'] = analysis.get('hex_after', '')

                tracks.append(track_info)

        return tracks

    def _is_mostly_printable(self, data: bytes, threshold: float = 0.8) -> bool:
        """Check if data is mostly printable ASCII/UTF-8."""
        if not data:
            return False

        printable_count = sum(1 for b in data if 32 <= b <= 126 or b in (9, 10, 13))
        return (printable_count / len(data)) >= threshold

    def _is_valid_string(self, s: str) -> bool:
        """Check if string looks like valid text (not binary garbage)."""
        if len(s) < 3:
            return False

        # Must have some letters
        alpha_count = sum(1 for c in s if c.isalpha())
        if alpha_count < len(s) * 0.3:
            return False

        # Check for reasonable character distribution
        printable = sum(1 for c in s if c.isprintable())
        if printable < len(s) * 0.9:
            return False

        return True

    def _safe_ascii(self, data: bytes) -> str:
        """Convert bytes to ASCII, replacing non-printable with dots."""
        return ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)

    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        report = []
        report.append("=" * 80)
        report.append(f"Binary Format Analysis: {self.file_path.name}")
        report.append("=" * 80)
        report.append(f"File size: {self.size:,} bytes")
        report.append("")

        # Magic markers
        report.append("MAGIC MARKERS FOUND:")
        report.append("-" * 80)
        markers = self.find_magic_markers()
        for marker, positions in sorted(markers.items(), key=lambda x: len(x[1]), reverse=True):
            report.append(f"  {marker:8s} : {len(positions):4d} occurrences")
            if len(positions) <= 5:
                report.append(f"             Positions: {positions}")
        report.append("")

        # Pascal strings
        report.append("LENGTH-PREFIXED STRINGS:")
        report.append("-" * 80)
        strings = self.extract_length_prefixed_strings()

        # Group by format type
        by_format = defaultdict(list)
        for offset, string, fmt in strings:
            by_format[fmt].append((offset, string))

        for fmt, items in by_format.items():
            report.append(f"\n{fmt.upper()} format ({len(items)} found):")
            # Show unique strings
            unique = list(set(s for _, s in items))[:20]
            for s in sorted(unique):
                report.append(f"  - {s}")

        report.append("")

        # Track data analysis
        report.append("TRACK DATA ANALYSIS:")
        report.append("-" * 80)
        tracks = self.extract_track_data_advanced()
        for i, track in enumerate(tracks[:10], 1):
            report.append(f"\nTrack #{i} at offset {track['offset']}:")
            if 'possible_name' in track:
                report.append(f"  Name: {track['possible_name']}")
            report.append(f"  Hex: {track['hex_context'][:64]}")

        if len(tracks) > 10:
            report.append(f"\n  ... and {len(tracks) - 10} more tracks")

        report.append("")

        # Repeating structures
        report.append("CHUNK-LIKE STRUCTURES:")
        report.append("-" * 80)
        structures = self.find_repeating_structures()

        # Group by type
        by_type = defaultdict(list)
        for s in structures:
            by_type[s['type']].append(s)

        for chunk_type, chunks in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            report.append(f"\n{chunk_type} ({len(chunks)} occurrences):")
            for chunk in chunks[:3]:
                report.append(f"  Offset: {chunk['offset']:08x}, Size: {chunk['size']}, "
                            f"Endian: {chunk['endian']}, Data: {chunk['data_preview']}")

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
            print("No ProjectData files found. Please specify a file path.")
            return
        file_path = project_data_files[0]

    print(f"\nAnalyzing: {file_path}\n")

    analyzer = ProjectDataAnalyzer(file_path)
    report = analyzer.generate_report()

    print(report)

    # Save report
    output_path = Path.cwd() / f"binary_analysis_{file_path.parent.parent.parent.name}.txt"
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
