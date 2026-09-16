# Logic Pro ProjectData Binary Format Analysis

**Complete toolkit for reverse engineering Logic Pro's ProjectData binary format**

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Analysis Tools](#analysis-tools)
- [Generated Reports](#generated-reports)
- [Key Findings](#key-findings)
- [Usage Examples](#usage-examples)

---

## Overview

This directory contains a comprehensive suite of tools and documentation for analyzing Logic Pro's proprietary `.logicx` project file format, specifically the binary `ProjectData` file located at `Alternatives/000/ProjectData`.

**Achievement Level**: ~60% format decoded
- ✅ File structure and chunk system identified
- ✅ Plugin/instrument presets fully decoded (JSON format)
- ✅ Session Players parameters extracted
- ✅ Score notation styles documented
- ⚠️ Track names partially accessible
- ❌ Some chunk types remain unknown

---

## Quick Start

### Analyze a Single Project
```bash
python3 logic_project_analyzer_enhanced.py
```
Generates a comprehensive markdown report of all Logic projects in the current directory.

### Deep Binary Analysis
```bash
python3 binary_format_analyzer.py "path/to/ProjectData"
```
Analyzes binary structure, finds markers, extracts strings.

### Extract Plugin Data
```bash
python3 extract_plugin_data.py "path/to/ProjectData"
```
Extracts plugin names, presets, and configurations (outputs JSON).

### View Chunk Structure
```bash
python3 chunk_structure_analyzer.py "path/to/ProjectData"
```
Maps all chunks, shows hierarchy and types.

### Hex Dump Analysis
```bash
python3 hex_dump_analyzer.py "path/to/ProjectData"
```
Creates annotated hex dumps around key markers.

---

## Documentation

### 📘 Main Documents

1. **[RESEARCH_SUMMARY.md](RESEARCH_SUMMARY.md)** ⭐ START HERE
   - Complete research findings
   - Technical specifications
   - Decoded data structures
   - Sample outputs
   - Next steps

2. **[BINARY_FORMAT_FINDINGS.md](BINARY_FORMAT_FINDINGS.md)**
   - Detailed binary format specification
   - Chunk types and markers
   - String encoding methods
   - Data type documentation

### 📊 Generated Reports

#### Binary Analysis
- `binary_analysis_*.txt` - Full marker analysis with hex dumps
- `chunk_structure_*.txt` - Complete chunk map with metadata
- `hex_analysis_*.txt` - Annotated hex dumps for each marker type

#### Plugin Data
- `plugin_data_*.txt` - Human-readable plugin/preset list
- `plugin_data_*.json` - Machine-readable extraction results

#### Project Analysis
- `logic_projects_enhanced_*.md` - Complete project reports with metadata
- `logic_projects_enhanced_*.csv` - Spreadsheet-compatible data

---

## Analysis Tools

### 🔧 Core Tools

#### 1. **logic_project_analyzer_enhanced.py**
**Purpose**: Main analyzer combining metadata + binary analysis

**Features**:
- Reads MetaData.plist for project info
- Extracts track names from ProjectData (partial)
- Extracts region names
- Generates comprehensive markdown reports
- Creates CSV for spreadsheet analysis

**Output**:
- `logic_projects_enhanced_YYYYMMDD_HHMMSS.md`
- `logic_projects_enhanced_YYYYMMDD_HHMMSS.csv`

**Key Functions**:
```python
extract_track_names(project_path)      # Track/region name extraction
parse_project_data(metadata, proj_info) # Combine all data sources
generate_markdown_report(projects)      # Create final report
```

---

#### 2. **binary_format_analyzer.py**
**Purpose**: Low-level binary structure analysis

**Features**:
- Finds all magic markers (karT, gRuA, etc.)
- Extracts Pascal/length-prefixed strings
- Identifies numeric patterns (float32, int32)
- Analyzes data structures around markers
- Finds repeating chunk patterns

**Key Classes**:
```python
ProjectDataAnalyzer(file_path)
  .find_magic_markers()                  # Locate all 4-byte markers
  .extract_length_prefixed_strings()     # Multiple string formats
  .find_numeric_patterns()               # BPM, parameters
  .analyze_structure_around_marker()     # Context analysis
  .extract_track_data_advanced()         # Track extraction
```

---

#### 3. **extract_plugin_data.py**
**Purpose**: Plugin and instrument configuration extraction

**Features**:
- Extracts embedded JSON preset data
- Identifies plugin names (Alchemy, Sampler, etc.)
- Decodes Session Players presets
- Extracts audio file references
- Finds tempo/BPM data

**Key Classes**:
```python
PluginDataExtractor(file_path)
  .extract_json_objects()                # Find JSON in binary
  .extract_plugin_names()                # Identify plugins
  .extract_preset_names()                # Decode presets
  .extract_audio_file_references()       # Find audio paths
```

**Output**:
- JSON with full preset configurations
- Plugin parameters decoded
- Alchemy library references

---

#### 4. **hex_dump_analyzer.py**
**Purpose**: Detailed hex-level investigation

**Features**:
- Generates formatted hex dumps
- Analyzes context around markers
- Tries multiple string extraction methods
- Shows numeric data interpretations

**Key Classes**:
```python
HexDumpAnalyzer(file_path)
  .hex_dump(offset, size)                # Formatted hex view
  .analyze_marker_context(marker)        # Deep marker analysis
  .generate_marker_report(marker)        # Full report per marker
```

**Output**:
- Hex dumps with ASCII representation
- Multiple string extraction attempts
- Numeric data in different formats

---

#### 5. **chunk_structure_analyzer.py**
**Purpose**: Map hierarchical file structure

**Features**:
- Identifies all chunks in file
- Extracts chunk metadata
- Attempts to find track names
- Parses file header

**Key Classes**:
```python
ProjectDataParser(file_path)
  .parse_file_header()                   # File header analysis
  .find_all_chunks()                     # Locate every chunk
  .generate_chunk_map()                  # Visual structure map
  .analyze_track_name_candidates()       # Track name search
```

**Output**:
- Complete chunk listing
- Chunk type statistics
- Metadata extraction
- Track name candidates

---

## Key Findings

### ✅ Successfully Decoded

#### 1. File Structure
- **Format**: Chunk-based binary (similar to IFF/RIFF)
- **Magic**: `23 47 c0 ab` (file signature)
- **Chunks**: 801 in analyzed sample (2.8 MB file)
- **Endianness**: Primarily Big-Endian

#### 2. Chunk Types (Reversed FourCC codes)
```
karT (Trak) - 320 occurrences - Track definition
qeSM (MSeq) - 169 occurrences - MIDI sequences
qSvE (EvSq) - 169 occurrences - Event sequences
gRuA (AuRg) -  38 occurrences - Audio regions
tSxT (TxSt) -  32 occurrences - Text styles
LFUA (AUFL) -  23 occurrences - Audio files
PMOC (COMP) -  23 occurrences - Comping data
```

#### 3. Embedded JSON Presets
Complete parameter sets for Session Players:

**Acoustic Piano** (Type_AcousticPianoV2):
- Preset: "Sweet Memories"
- Parameters: intensity (71), dynamics (119), humanize (37)
- Voicing styles, arpeggiator, grace notes

**Electric Bass** (Type_ElectricBassV2):
- Preset: "Night Flight"
- Parameters: riffiness (3), slides (50), dead notes (72)
- Playing position, blues-yness, buzz trills

**Electronic Drummer** (Type_ElectronicDrummerV2):
- Preset: "Hit Factory"
- Kit piece complexity (a1-a3, b1-b3, c1-c3)
- Fill amounts, accent variation, phrase variation

#### 4. Alchemy Synthesizer Data
28+ library references extracted:
- Oscillator waveforms: Sine, Saw, Triangle, Square
- LFO shapes: Ramp Up/Down, Random, Sine
- Formant filters: Vowel A/E/I/U
- Noise: White, Radio

#### 5. Score Notation Styles
32 text style definitions:
- Plain Text, Page Number, Bar Number
- Instrument Name, Tuplet, Tempo Symbol
- Chord Root/Extensions, Tablature
- Guitar markings, Fingering

### ⚠️ Partially Decoded

#### Track Names
- Generic names found ("Audio 1", "Audio 2")
- Session Player region names in JSON
- Custom track names location still unknown
- Likely in separate index or using indirect references

### ❌ Not Yet Decoded

- AU/VST plugin states
- Mixer channel strip settings
- Smart Controls configuration
- Flex Time/Pitch editing data
- Complete automation curves

---

## Usage Examples

### Example 1: Basic Project Analysis
```bash
# Analyze all projects in current directory
python3 logic_project_analyzer_enhanced.py

# Output:
# - Markdown report with all project details
# - CSV with structured data
# - Track names (where found)
# - Plugin usage statistics
```

### Example 2: Extract Plugin Presets
```bash
# Extract from specific project
python3 extract_plugin_data.py \
  "My Project.logicx/Alternatives/000/ProjectData"

# Output: plugin_data_*.json
{
  "plugins": ["Alchemy", "Sampler", ...],
  "presets": [
    {
      "name": "Sweet Memories",
      "character": "Acoustic Piano - Strummed",
      "parameters": { "intensity": 71, ... }
    }
  ]
}
```

### Example 3: Deep Binary Investigation
```bash
# Full binary analysis
python3 binary_format_analyzer.py \
  "My Project.logicx/Alternatives/000/ProjectData"

# Shows:
# - All magic markers and positions
# - Extracted strings (multiple methods)
# - Numeric patterns (BPM, parameters)
# - Track analysis
```

### Example 4: Hex Dump Specific Markers
```bash
# Analyze karT (track) markers
python3 hex_dump_analyzer.py \
  "My Project.logicx/Alternatives/000/ProjectData"

# Creates hex dumps for:
# - karT (tracks)
# - gRuA (audio regions)
# - tSnI (instruments)
# - LFUA (audio files)
```

### Example 5: Map Entire File Structure
```bash
# Get complete chunk map
python3 chunk_structure_analyzer.py \
  "My Project.logicx/Alternatives/000/ProjectData"

# Output:
# - File header information
# - All 801 chunks listed
# - Chunk type statistics
# - Metadata extraction
# - Track name candidates
```

---

## Data Extraction Capabilities

### What Can Be Extracted

✅ **Project Metadata** (from MetaData.plist):
- Tempo (BPM)
- Key signature
- Time signature
- Sample rate
- Track count
- Audio file lists
- Logic Pro version

✅ **Session Players Data**:
- Preset names
- Full parameter sets
- Playing styles
- Humanization settings
- Pattern seeds
- Region automation

✅ **Plugin Information**:
- Plugin names (Alchemy, Sampler, etc.)
- Library references
- Synthesizer patch data

✅ **Score Notation**:
- Text style definitions
- Font settings
- Notation preferences

✅ **Audio References**:
- File paths (relative/absolute)
- Apple Loops used
- Sample library references

⚠️ **Partial Extraction**:
- Track names (generic only)
- MIDI sequence structure
- Automation structure

❌ **Cannot Extract** (yet):
- Custom track names reliably
- Full MIDI note data
- Complete automation curves
- Plugin parameter automation
- Mixer settings
- Smart Controls

---

## File Format Specification

### Magic Markers (Reversed FourCC)

| Bytes | ASCII | Reversed | Purpose |
|-------|-------|----------|---------|
| `6B 61 72 54` | karT | Trak | Track definition |
| `67 52 75 41` | gRuA | AuRg | Audio region |
| `71 53 76 45` | qSvE | EvSq | Event sequence |
| `71 65 53 4D` | qeSM | MSeq | MIDI sequence |
| `74 53 6E 49` | tSnI | InSt | Instrument |
| `74 53 78 54` | tSxT | TxSt | Text style |
| `4C 46 55 41` | LFUA | AUFL | Audio file |
| `6C 46 75 41` | lFuA | AuFl | Audio file alt |
| `50 4D 4F 43` | PMOC | COMP | Comping data |
| `4D 72 6F 43` | MroC | CorM | Core MIDI |
| `73 6E 72 54` | snrT | Trns | Transform |

### String Encoding Formats

**Method 1 - Length Prefix (1 byte)**:
```
0A 48 65 6C 6C 6F 20 57 6F 72 6C 64
^^ ^^-------string data-------^^
|  "Hello World"
Length = 10
```

**Method 2 - Length Prefix (2 bytes BE)**:
```
00 0A 48 65 6C 6C 6F 20 57 6F 72 6C 64
^^^^^  ^^-------string data-------^^
|      "Hello World"
Length = 10 (BE)
```

**Method 3 - Null Terminated**:
```
48 65 6C 6C 6F 00
^^-------^^    ^^
"Hello"       NULL
```

### Numeric Data

**Float32 (BPM)**:
```
42 A0 00 00  = 80.0 (BE)
00 00 A0 42  = 80.0 (LE)
```

**Int32 (counts, offsets)**:
```
00 00 01 40  = 320 (BE)
40 01 00 00  = 320 (LE)
```

---

## Advanced Topics

### Session Players JSON Structure

Full GeneratorMemento contains:
- **Seeds**: Random number generator seeds for pattern generation
- **LastGenerateLength**: Bar length of last generation
- **MementoParameters**: Automation parameter strings
  - `regionStartParams`: Parameters at region start
  - `regionEndParams`: Parameters at region end
  - `humanizeEndStatus`: Timing humanization state
  - `lastGenerateMappedEditorValues`: UI slider positions

### Parameter Encoding in JSON Strings

Format: `key=type,value`

Types:
- `n1,X` - 1-byte number (0-255)
- `n2,X` - 2-byte number (0-65535)
- `n3,X` - 3-byte number (0-16777215)
- `n5,X.Y` - Float
- `b4,true/false` - Boolean (4 bytes)
- `s0,` - String (empty)
- `tN,data` - Array/tuple

Example:
```
"swing=n1,0pushPull=n3,-16swingType=n1,1lowerPosition=n2,55"
```

Decoded:
- swing: 0 (1-byte)
- pushPull: -16 (3-byte, signed)
- swingType: 1 (1-byte)
- lowerPosition: 55 (2-byte)

---

## Troubleshooting

### "No ProjectData files found"
- Ensure you're in a directory with `.logicx` projects
- ProjectData is at: `Project.logicx/Alternatives/000/ProjectData`
- Use absolute path if needed

### "Permission denied"
- Logic must not be running with project open
- Check file permissions: `chmod +r ProjectData`

### Track names not appearing
- This is expected (format partially unknown)
- Generic names ("Audio 1") will appear
- Session Player region names work
- Custom track names still being researched

### JSON extraction fails
- Older Logic versions may use different format
- Some instruments don't use JSON (AU/VST plugins)
- Check Python version (requires 3.7+)

---

## Future Research Directions

### High Priority
1. **Track Name Location**
   - Analyze file header/footer
   - Look for offset tables
   - Compare multiple project versions

2. **Compression Detection**
   - Test zlib on PMOC chunks
   - Check for other algorithms

3. **AU/VST Plugin States**
   - Reverse engineer common plugins
   - Document state format

### Medium Priority
4. **Full Automation Curves**
   - Decode qSvE event data
   - Extract parameter values over time

5. **MIDI Note Data**
   - Parse qeSM sequence chunks
   - Extract note on/off, velocity, CC

6. **Mixer Configuration**
   - Channel strip settings
   - Routing/send configuration
   - Plugin chain order

### Long-term
7. **Complete Format Documentation**
   - Document all chunk types
   - Create formal specification
   - Enable third-party tools

---

## Contributing

If you discover new patterns or decode additional chunks:

1. Document findings in markdown
2. Add test cases to analyzers
3. Update [RESEARCH_SUMMARY.md](RESEARCH_SUMMARY.md)
4. Share sample ProjectData (anonymized)

---

## Technical Notes

### Python Requirements
```
Python 3.7+
Standard library only (no external dependencies)
```

### Tested On
- macOS 14.x (Sonoma)
- Logic Pro 11.x
- Python 3.14

### Performance
- Typical project (2-3 MB): ~1-2 seconds
- Large project (10+ MB): ~5-10 seconds
- Memory usage: ~100-200 MB

---

## File Inventory

### Python Tools (5)
- `logic_project_analyzer_enhanced.py` - Main analyzer
- `binary_format_analyzer.py` - Binary structure
- `extract_plugin_data.py` - Plugin extraction
- `hex_dump_analyzer.py` - Hex investigation
- `chunk_structure_analyzer.py` - Chunk mapping

### Documentation (2)
- `RESEARCH_SUMMARY.md` - Complete findings
- `BINARY_FORMAT_FINDINGS.md` - Technical spec

### Sample Reports (~10+)
- `binary_analysis_*.txt`
- `chunk_structure_*.txt`
- `hex_analysis_*.txt`
- `plugin_data_*.{txt,json}`
- `logic_projects_enhanced_*.{md,csv}`

---

## License & Disclaimer

**Educational/Research Use Only**

This research is for educational purposes and personal project analysis. The Logic Pro file format is proprietary to Apple Inc. This reverse engineering is conducted for interoperability and archival purposes only.

**No Warranty**: These tools are provided as-is. Always backup your projects before analysis.

**Not Affiliated**: Not affiliated with or endorsed by Apple Inc.

---

## Quick Reference

### Most Useful Commands

```bash
# Analyze everything
python3 logic_project_analyzer_enhanced.py

# Extract plugins only
python3 extract_plugin_data.py "path/to/ProjectData"

# Deep dive on specific project
python3 binary_format_analyzer.py "path/to/ProjectData"
python3 hex_dump_analyzer.py "path/to/ProjectData"
python3 chunk_structure_analyzer.py "path/to/ProjectData"
```

### File Paths
```
Project.logicx/
  ├── Alternatives/
  │   └── 000/
  │       ├── MetaData.plist          ← Project metadata
  │       └── ProjectData             ← Binary data (this!)
  ├── Resources/
  │   └── ProjectInformation.plist    ← Logic version
  └── Media/                          ← Audio files
```

---

**Last Updated**: December 5, 2025
**Version**: 1.0
**Status**: Active Research
