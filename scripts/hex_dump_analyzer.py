#!/usr/bin/env python3
"""
Hex Dump Analyzer - Deep dive into specific sections of ProjectData
Creates annotated hex dumps around markers to understand data structures.
"""

import struct
from pathlib import Path
from typing import List, Dict, Tuple
import binascii


class HexDumpAnalyzer:
    """Analyzes binary data with annotated hex dumps."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        with open(file_path, 'rb') as f:
            self.data = f.read()
        self.size = len(self.data)

    def hex_dump(self, offset: int, size: int, bytes_per_line: int = 16) -> str:
        """Generate formatted hex dump with ASCII representation."""
        lines = []
        end = min(offset + size, self.size)

        for i in range(offset, end, bytes_per_line):
            chunk_size = min(bytes_per_line, end - i)
            chunk = self.data[i:i+chunk_size]

            # Offset
            line = f"{i:08x}  "

            # Hex bytes
            hex_parts = []
            for j in range(bytes_per_line):
                if j < chunk_size:
                    hex_parts.append(f"{chunk[j]:02x}")
                else:
                    hex_parts.append("  ")

                # Add extra space in the middle
                if j == 7:
                    hex_parts.append(" ")

            line += " ".join(hex_parts)
            line += "  |"

            # ASCII representation
            ascii_part = ""
            for j in range(chunk_size):
                byte = chunk[j]
                if 32 <= byte <= 126:
                    ascii_part += chr(byte)
                else:
                    ascii_part += "."

            line += ascii_part.ljust(bytes_per_line) + "|"
            lines.append(line)

        return "\n".join(lines)

    def analyze_marker_context(self, marker: bytes, max_samples: int = 5) -> List[Dict]:
        """Analyze data structure around each instance of a marker."""
        analyses = []

        offset = 0
        count = 0

        while count < max_samples:
            pos = self.data.find(marker, offset)
            if pos == -1:
                break

            # Analyze structure before marker
            before_size = 64
            after_size = 256

            start = max(0, pos - before_size)
            end = min(self.size, pos + len(marker) + after_size)

            analysis = {
                'offset': pos,
                'marker': marker.decode('latin-1', errors='ignore'),
                'hex_dump': self.hex_dump(start, end - start),
            }

            # Try to decode following data
            after_data = self.data[pos+len(marker):pos+len(marker)+128]

            # Try various string extraction methods
            analysis['string_attempts'] = []

            # Method 1: Null-terminated
            null_pos = after_data.find(b'\x00')
            if null_pos > 0 and null_pos < 100:
                try:
                    s = after_data[:null_pos].decode('utf-8', errors='ignore')
                    if self._is_printable(s):
                        analysis['string_attempts'].append({
                            'method': 'null-terminated',
                            'string': s,
                            'length': null_pos
                        })
                except:
                    pass

            # Method 2: Length-prefixed (1 byte)
            if len(after_data) > 1:
                length = after_data[0]
                if 1 <= length <= 100 and length + 1 <= len(after_data):
                    try:
                        s = after_data[1:1+length].decode('utf-8', errors='ignore')
                        if self._is_printable(s):
                            analysis['string_attempts'].append({
                                'method': '1-byte length prefix',
                                'string': s,
                                'length': length,
                                'prefix_byte': f"0x{length:02x}"
                            })
                    except:
                        pass

            # Method 3: Length-prefixed (2 bytes, big-endian)
            if len(after_data) > 2:
                length = struct.unpack('>H', after_data[0:2])[0]
                if 1 <= length <= 1000 and length + 2 <= len(after_data):
                    try:
                        s = after_data[2:2+length].decode('utf-8', errors='ignore')
                        if self._is_printable(s):
                            analysis['string_attempts'].append({
                                'method': '2-byte BE length prefix',
                                'string': s,
                                'length': length,
                                'prefix_bytes': f"0x{after_data[0]:02x}{after_data[1]:02x}"
                            })
                    except:
                        pass

            # Method 4: Skip N bytes then read
            for skip in [1, 2, 4, 8, 12, 16]:
                if skip < len(after_data):
                    remaining = after_data[skip:]
                    null_pos = remaining.find(b'\x00')
                    if null_pos > 3 and null_pos < 100:
                        try:
                            s = remaining[:null_pos].decode('utf-8', errors='ignore')
                            if self._is_printable(s) and len(s) >= 3:
                                analysis['string_attempts'].append({
                                    'method': f'skip {skip} bytes, null-terminated',
                                    'string': s,
                                    'length': null_pos,
                                    'skipped_bytes': binascii.hexlify(after_data[:skip]).decode()
                                })
                        except:
                            pass

            # Analyze potential numeric data
            if len(after_data) >= 8:
                analysis['numeric_data'] = []

                # Try int32 at various offsets
                for offset in [0, 4, 8]:
                    if offset + 4 <= len(after_data):
                        val_be = struct.unpack('>i', after_data[offset:offset+4])[0]
                        val_le = struct.unpack('<i', after_data[offset:offset+4])[0]
                        analysis['numeric_data'].append({
                            'offset': offset,
                            'int32_be': val_be,
                            'int32_le': val_le,
                        })

            analyses.append(analysis)
            count += 1
            offset = pos + 1

        return analyses

    def _is_printable(self, s: str) -> bool:
        """Check if string is mostly printable."""
        if len(s) < 3:
            return False
        printable = sum(1 for c in s if c.isprintable() or c in '\n\r\t')
        return printable / len(s) > 0.8

    def generate_marker_report(self, marker: bytes, sample_count: int = 5) -> str:
        """Generate detailed report for a specific marker."""
        analyses = self.analyze_marker_context(marker, sample_count)

        report = []
        report.append("=" * 80)
        report.append(f"Marker Analysis: {marker.decode('latin-1', errors='ignore')}")
        report.append(f"File: {self.file_path.name}")
        report.append("=" * 80)
        report.append("")

        for idx, analysis in enumerate(analyses, 1):
            report.append(f"Sample #{idx} - Offset: 0x{analysis['offset']:08x}")
            report.append("-" * 80)
            report.append("")

            # Hex dump
            report.append("HEX DUMP:")
            report.append(analysis['hex_dump'])
            report.append("")

            # String extraction attempts
            if analysis['string_attempts']:
                report.append("STRING EXTRACTION ATTEMPTS:")
                for attempt in analysis['string_attempts']:
                    report.append(f"  Method: {attempt['method']}")
                    report.append(f"  String: '{attempt['string']}'")
                    report.append(f"  Length: {attempt['length']}")
                    if 'prefix_byte' in attempt:
                        report.append(f"  Prefix: {attempt['prefix_byte']}")
                    if 'prefix_bytes' in attempt:
                        report.append(f"  Prefix: {attempt['prefix_bytes']}")
                    if 'skipped_bytes' in attempt:
                        report.append(f"  Skipped: {attempt['skipped_bytes']}")
                    report.append("")

            # Numeric data
            if 'numeric_data' in analysis and analysis['numeric_data']:
                report.append("NUMERIC DATA (first few int32 values):")
                for num_data in analysis['numeric_data'][:3]:
                    report.append(f"  Offset +{num_data['offset']:d}:")
                    report.append(f"    int32 BE: {num_data['int32_be']}")
                    report.append(f"    int32 LE: {num_data['int32_le']}")
                report.append("")

            report.append("=" * 80)
            report.append("")

        return "\n".join(report)


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

    print(f"\nAnalyzing: {file_path}\n")

    analyzer = HexDumpAnalyzer(file_path)

    # Analyze different markers
    markers = [
        b'karT',  # Track
        b'gRuA',  # Audio region
        b'tSnI',  # Instrument
        b'LFUA',  # Audio file
    ]

    for marker in markers:
        print(f"Analyzing marker: {marker.decode('latin-1')}")
        report = analyzer.generate_marker_report(marker, sample_count=3)

        # Save report
        marker_name = marker.decode('latin-1', errors='ignore')
        output_path = Path.cwd() / f"hex_analysis_{marker_name}_{file_path.parent.parent.parent.name}.txt"
        with open(output_path, 'w') as f:
            f.write(report)

        print(f"  Saved: {output_path.name}")

    print("\nHex dump analysis complete!")


if __name__ == "__main__":
    main()
