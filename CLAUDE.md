# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

LogicX Analyzer is a Python-based reverse engineering toolkit for analyzing Logic Pro project files (.logicx). The project has successfully decoded ~60% of Logic Pro's proprietary binary ProjectData format, extracting plugin configurations, Session Players presets, and file structure.

**License**: GPL 2.0 (see [LICENSE.md](LICENSE.md))
**Status**: Production ready, active research
**Python**: 3.7+ required, standard library only (no dependencies)

## Commands

### Analysis Commands

```bash
# Main analyzer - comprehensive project analysis with binary parsing
python3 scripts/logic_project_analyzer_enhanced.py

# Original analyzer - metadata only (MetaData.plist)
python3 scripts/logic_project_analyzer.py

# Extract track names only
python3 scripts/extract_track_names.py
```

### Binary Analysis Tools

```bash
# Deep binary structure analysis - finds markers, strings, numeric patterns
python3 scripts/binary_format_analyzer.py "path/to/ProjectData"

# Complete file structure mapping - identifies all chunks
python3 scripts/chunk_structure_analyzer.py "path/to/ProjectData"

# Plugin and preset extraction - outputs JSON
python3 scripts/extract_plugin_data.py "path/to/ProjectData"

# Hex-level investigation - creates annotated hex dumps
python3 scripts/hex_dump_analyzer.py "path/to/ProjectData"
```

### Requirements

- Python 3.7+
- Standard library only (no external dependencies)
- macOS (tested on Sonoma 14.x)

## Architecture

### File Structure of .logicx Projects

```
Project.logicx/
├── Alternatives/000/
│   ├── MetaData.plist     # Standard metadata (BPM, key, time signature)
│   └── ProjectData        # Binary data (main reverse engineering target)
├── Resources/
│   └── ProjectInformation.plist  # Logic Pro version info
└── Media/                 # Audio files
```

### Binary Format Architecture

**ProjectData** uses a chunk-based binary format similar to IFF/RIFF:

- **Magic bytes**: `23 47 c0 ab` (file signature)
- **Chunk markers**: 4-byte reversed FourCC codes (e.g., `karT` = "Trak" backwards)
- **Endianness**: Mixed, primarily Big-Endian
- **String encoding**: Multiple methods coexist (length-prefixed, null-terminated)
- **Embedded JSON**: Session Players presets stored as complete JSON objects

### Key Chunk Types

| Marker | Reversed | Purpose | Frequency |
|--------|----------|---------|-----------|
| `karT` | Trak | Track definition | ~320 |
| `qeSM` | MSeq | MIDI sequences | ~169 |
| `qSvE` | EvSq | Event sequences (automation) | ~169 |
| `gRuA` | AuRg | Audio regions | ~38 |
| `tSxT` | TxSt | Text/notation styles | ~32 |
| `LFUA`/`lFuA` | AUFL/AuFl | Audio file references | ~23 |
| `PMOC` | COMP | Comping/take data | ~23 |
| `tSnI` | InSt | Instrument definition | ~1 |

### Code Organization

**Production Scripts** (`scripts/`):

- `logic_project_analyzer_enhanced.py` - Primary tool combining metadata + binary analysis
- `logic_project_analyzer.py` - Original metadata-only analyzer
- `binary_format_analyzer.py` - Low-level binary structure analysis
- `chunk_structure_analyzer.py` - File structure mapping
- `extract_plugin_data.py` - Plugin/preset extraction
- `extract_track_names.py` - Track name extraction
- `hex_dump_analyzer.py` - Hex-level investigation

**Experimental Scripts** (`scripts/experimental/`):

- Archived research prototypes (NOT for production use)
- `decode_logic.py`, `decode_logic_v2.py` - Early string extraction experiments
- `logic_deep_decode.py`, `logic_deep_decode_v2.py` - Variable-length int parsing
- `recursive_unarchive.py` - NSKeyedArchiver exploration (incorrect hypothesis)
- See `scripts/experimental/README.md` for details

**Binary Analysis Classes** (found across multiple scripts):

- `ProjectDataAnalyzer` - Low-level binary structure analysis
- `PluginDataExtractor` - JSON preset extraction
- `HexDumpAnalyzer` - Hex-level investigation
- `ProjectDataParser` - Chunk mapping

**Key Functions**:
- `extract_strings_from_binary()` - Regex-based ASCII string extraction
- `extract_json_objects()` - Parses embedded JSON from binary data
- `find_magic_markers()` - Locates all chunk markers
- `extract_length_prefixed_strings()` - Multiple string encoding methods

### Data Extraction Pipeline

1. **MetaData.plist parsing** → Musical attributes (BPM, key, time signature)
2. **ProjectData binary analysis** → Chunk structure mapping
3. **String extraction** → Track names, region names (partial)
4. **JSON parsing** → Session Players presets with full parameters
5. **Plugin detection** → Alchemy, Sampler, Retro Synth identification
6. **Report generation** → Markdown + CSV output

### String Encoding Methods

The binary format uses 4 different string encoding patterns:

```python
# Method 1: 1-byte length prefix (Pascal)
[1-byte length][string data]

# Method 2: 2-byte Big-Endian length
[2-byte BE length][string data]

# Method 3: 4-byte Big-Endian length (JSON blocks)
[4-byte BE length][string data]

# Method 4: Null-terminated
[string data]\x00
```

### JSON Preset Structure

Session Players use embedded JSON with this structure:

```json
{
  "Preset": {
    "Name": "Sweet Memories",
    "CharacterIdentifier": "Acoustic Piano - Strummed",
    "Parameters": { /* intensity, dynamics, humanize, etc. */ }
  },
  "RegionType": "Type_AcousticPianoV2",
  "GeneratorMemento": {
    "Seeds": [/* RNG seeds */],
    "MementoParameters": {
      "regionStartParams": "key=type,value...",
      "regionEndParams": "...",
      "lastGenerateMappedEditorValues": "..."
    }
  }
}
```

Parameter encoding in strings: `key=n1,value` where:
- `n1,X` = 1-byte number (0-255)
- `n2,X` = 2-byte number
- `n3,X` = 3-byte number (signed)
- `n5,X.Y` = Float
- `b4,true/false` = Boolean
- `tN,data` = Array/tuple

## What Has Been Decoded (Current Status)

### ✅ Successfully Decoded
- File structure and chunk system
- Plugin names (Alchemy, Sampler, Retro Synth, etc.)
- Session Players presets with complete parameter sets
- Score notation text styles (32 types)
- Alchemy synthesizer library references (28+ types)
- Audio file references and paths
- Binary structure complexity metrics
- Tempo candidates from binary data

### ⚠️ Partially Decoded
- Track names (generic names like "Audio 1" work, custom names still elusive)
- MIDI sequence structure
- Automation structure

### ❌ Not Yet Decoded
- Custom track name reliable extraction
- Full MIDI note data
- Complete automation curves
- AU/VST plugin parameter states
- Mixer channel strip settings
- Smart Controls configuration
- Flex Time/Pitch editing data

## Development Notes

### Common Patterns

When analyzing binary data, scripts consistently use:
1. Regex pattern matching for ASCII strings: `b'[ -~]{4,}'`
2. Struct unpacking for numeric data: `struct.unpack('>f', bytes)` (Big-Endian)
3. JSON parsing with error handling for malformed data
4. Offset tracking for correlation with hex editors

### Output Formats

All analyzers generate timestamped reports:
- **Markdown**: `logic_projects_enhanced_YYYYMMDD_HHMMSS.md`
- **CSV**: `logic_projects_enhanced_YYYYMMDD_HHMMSS.csv`
- **JSON**: `plugin_data_YYYYMMDD_HHMMSS.json`
- **Text**: `binary_analysis_YYYYMMDD_HHMMSS.txt`

### Performance Characteristics

- Typical project (2-3 MB): 1-2 seconds
- Large project (10+ MB): 5-10 seconds
- Memory usage: 100-200 MB

### Research Limitations

- Logic Pro must not be running with project open
- Format is proprietary (educational/research use only)
- Some data structures use compression (not yet identified)
- Track name location remains unknown (high priority research item)

## Key Implementation Details

### Track Name Extraction Challenge

Track names are the primary unsolved problem. Current approaches:
- Search around `karT` markers (unsuccessful - names not adjacent)
- Look for length-prefixed strings (finds generic names only)
- Parse JSON (works for Session Players regions only)
- Theory: Names stored in separate index/offset table (not yet located)

### Marker Detection Pattern

All analysis tools use similar marker finding:

```python
known_markers = [b'karT', b'gRuA', b'qeSM', ...]
for i in range(len(data) - 4):
    marker = data[i:i+4]
    if marker in known_markers:
        positions[marker].append(i)
```

### JSON Extraction State Machine

The JSON extractor uses brace counting with string state tracking to handle nested objects and escaped quotes within the binary stream.

## Documentation

**Root Documentation**:

- [README.md](README.md) - User-facing documentation and quick start
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines and research priorities
- [LICENSE.md](LICENSE.md) - GPL 2.0 license with educational use disclaimer
- [CLAUDE.md](CLAUDE.md) - This file (AI assistant context)

**Technical Documentation** (`docs/`):

- [docs/README_BINARY_ANALYSIS.md](docs/README_BINARY_ANALYSIS.md) - Complete binary analysis guide
- [docs/RESEARCH_SUMMARY.md](docs/RESEARCH_SUMMARY.md) - Research findings and discoveries
- [docs/BINARY_FORMAT_FINDINGS.md](docs/BINARY_FORMAT_FINDINGS.md) - Technical format specification
- [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Command quick reference
- [docs/MULTI_FORMAT_OUTPUT.md](docs/MULTI_FORMAT_OUTPUT.md) - Output format examples

**Experimental Archive**:

- [scripts/experimental/README.md](scripts/experimental/README.md) - Archived research scripts documentation

## Contributing

When making changes to this repository:

1. **Follow existing patterns** - Scripts use consistent structure and naming
2. **Update documentation** - Modify relevant docs when changing functionality
3. **Test with multiple projects** - Ensure compatibility across Logic versions
4. **See CONTRIBUTING.md** - Full guidelines for research contributions
5. **Track name extraction** is the #1 research priority (currently unsolved)

## Important Notes for AI Assistants

- **Do NOT use experimental scripts** for production analysis - they are archived research only
- **Output files are gitignored** - Analysis reports should not be committed
- **GPL 2.0 licensed** - Derivative works must maintain GPL 2.0 license
- **Educational use only** - Logic Pro format is proprietary to Apple Inc.
- **No external dependencies** - All scripts use Python standard library only
- **macOS focused** - Developed and tested on macOS (Sonoma 14.x)
