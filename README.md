# LogicX Analyzer

<!-- BADGES:START -->
![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python)
[![Licence GPL--2.0](https://img.shields.io/badge/licence-GPL--2.0-blue?style=flat-square)](LICENSE.md)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)
<!-- BADGES:END -->

## Description




Complete toolkit for analyzing Logic Pro projects (.logicx) with advanced binary format reverse engineering.

## Screenshot

<p align="center">
  <img src="docs/terminal-analyzer.svg" width="100%" alt="The analyzer's entry point, run against a Logic Pro project bundle.">
</p>

<p align="center"><em>The analyzer's entry point, run against a Logic Pro project bundle.</em></p>

## 📁 Directory Structure

```
logicx-analyzer/
├── scripts/                                  # Production analysis tools
│   ├── logic_project_analyzer_enhanced.py    # ⭐ Main analyzer (use this!)
│   ├── binary_format_analyzer.py             # Low-level binary structure analysis
│   ├── chunk_structure_analyzer.py           # File structure mapping
│   ├── extract_plugin_data.py                # Plugin/preset extraction
│   ├── extract_track_names.py                # Standalone track name extractor
│   ├── hex_dump_analyzer.py                  # Hex dump investigation
│   ├── logic_project_analyzer.py             # Original basic analyzer
│   └── experimental/                         # Archived research scripts
│       └── README.md                         # See experimental/README.md
├── docs/                                     # Complete documentation
│   ├── BINARY_FORMAT_FINDINGS.md             # Technical format specification
│   ├── MULTI_FORMAT_OUTPUT.md                # Output format examples
│   ├── QUICK_REFERENCE.md                    # Command quick reference
│   ├── README_BINARY_ANALYSIS.md             # Binary analysis guide
│   └── RESEARCH_SUMMARY.md                   # Complete research findings
├── CLAUDE.md                                 # AI assistant context
├── CONTRIBUTING.md                           # Contribution guidelines
├── LICENSE.md                                # GPL 2.0 license
└── README.md                                 # This file
```

## 🚀 Quick Start

### Analyze All Projects in Current Directory

```bash
cd "/path/to/your/logic/projects"
python3 "/path/to/logicx-analyzer/scripts/logic_project_analyzer_enhanced.py"
```

### Output

- Comprehensive markdown report with:
  - Musical attributes (BPM, key, time signature)
  - Binary structure analysis
  - Plugin usage and presets
  - Session Players configurations
  - Track and region names
  - Audio resource counts
  - Alchemy library references

## 📊 What Gets Analyzed

### From MetaData.plist (Standard)

- ✅ Tempo (BPM)
- ✅ Key signature
- ✅ Time signature
- ✅ Track count
- ✅ Sample rate
- ✅ Audio file lists
- ✅ Logic Pro version

### From ProjectData Binary (Advanced) ⭐ NEW

- ✅ **Plugins detected** (Alchemy, Sampler, Retro Synth, etc.)
- ✅ **Session Players presets** with full parameters
  - Preset names ("Sweet Memories", "Night Flight", etc.)
  - Character types (Electric Bass, Acoustic Piano, Drummer)
  - All parameters (intensity, dynamics, humanize, variation)
- ✅ **Binary structure**
  - Chunk counts (Track, MIDI, Audio Region, etc.)
  - File complexity metrics
- ✅ **Alchemy synthesizer data**
  - Library references (oscillators, LFOs, formants)
  - Synthesis complexity
- ✅ **Track names** (partial - generic names work)
- ✅ **Region names**
- ✅ **Tempo candidates** from binary data

## 🔧 Main Scripts

### 1. logic_project_analyzer_enhanced.py ⭐ RECOMMENDED

**The complete analyzer with all features.**

```bash
python3 scripts/logic_project_analyzer_enhanced.py
```

**Features:**

- Complete metadata extraction
- Advanced binary format parsing
- Plugin and preset detection
- Session Players analysis
- Binary structure mapping
- Comprehensive reports

**Output:**

- `logic_projects_advanced_YYYYMMDD_HHMMSS.md`

**Use Cases:**

- Full project analysis
- Plugin usage tracking
- Session Players preset documentation
- Project complexity assessment
- Binary format research

---

### 2. logic_project_analyzer.py

**Original basic analyzer (metadata only).**

```bash
python3 scripts/logic_project_analyzer.py
```

**Features:**

- MetaData.plist parsing
- Basic statistics
- Simple reports

**Output:**

- `logic_projects_report_YYYYMMDD_HHMMSS.md`

**Use Cases:**

- Quick metadata check
- When binary analysis isn't needed
- Baseline compatibility testing

---

### 3. extract_track_names.py

**Standalone track name extractor.**

```bash
python3 scripts/extract_track_names.py
```

**Features:**

- Extracts track names from ProjectData
- Generates simple report

**Output:**

- `track_names_report.md`

**Use Cases:**

- Quick track name check
- Testing track name extraction
- Minimal analysis needed

## 🔬 Binary Analysis Tools

Located in `scripts/` - these are advanced tools for format research.

### binary_format_analyzer.py

Deep binary structure analysis.

```bash
python3 "scripts/binary_format_analyzer.py" "path/to/ProjectData"
```

**Capabilities:**

- Finds all magic markers (karT, gRuA, qeSM, etc.)
- Extracts strings with multiple methods
- Identifies numeric patterns
- Analyzes data structures

**Output:**

- `binary_analysis_*.txt`

---

### chunk_structure_analyzer.py

Complete file structure mapping.

```bash
python3 "scripts/chunk_structure_analyzer.py" "path/to/ProjectData"
```

**Capabilities:**

- Maps all chunks in file
- Counts chunk types
- Extracts metadata
- Finds track name candidates

**Output:**

- `chunk_structure_*.txt`

---

### extract_plugin_data.py

Plugin and preset extraction.

```bash
python3 "scripts/extract_plugin_data.py" "path/to/ProjectData"
```

**Capabilities:**

- Extracts JSON presets
- Identifies plugins
- Finds Alchemy references
- Analyzes audio file paths

**Output:**

- `plugin_data_*.txt`
- `plugin_data_*.json`

---

### hex_dump_analyzer.py

Hex-level investigation.

```bash
python3 "scripts/hex_dump_analyzer.py" "path/to/ProjectData"
```

**Capabilities:**

- Creates annotated hex dumps
- Analyzes marker contexts
- Multiple string extraction attempts
- Numeric data interpretation

**Output:**

- `hex_analysis_karT_*.txt` (Track markers)
- `hex_analysis_gRuA_*.txt` (Audio regions)
- `hex_analysis_tSnI_*.txt` (Instruments)
- `hex_analysis_LFUA_*.txt` (Audio files)

## 📚 Documentation

### README_BINARY_ANALYSIS.md

Complete guide to binary format analysis.

**Contents:**

- Binary format overview
- Tool usage examples
- Data extraction capabilities
- Format specification
- Quick reference

---

### RESEARCH_SUMMARY.md

Complete reverse engineering findings.

**Contents:**

- Executive summary
- Key discoveries
- Data types decoded
- Chunk specifications
- Session Players parameters
- Next research steps

---

### BINARY_FORMAT_FINDINGS.md

Technical format specification.

**Contents:**

- File structure
- Magic markers
- Data encoding methods
- String formats
- Numeric types
- Plugin data structures

---

### UPGRADE_SUMMARY.md

Recent enhancement details.

**Contents:**

- Version 2.0 changes
- New features added
- Test results
- Before/after comparisons
- Performance metrics

## 📈 Example Output

### Summary Statistics

```
Total Projects: 39
Total Tracks: 588
Track Names Extracted: 394
Audio Regions Extracted: 1,066
Plugins Detected: 604
Presets Found: 642
Average Tempo: 99.74 BPM
```

### Plugin Usage

```
| Plugin              | Projects |
|--------------------|----------|
| Sampler            | 11       |
| Q-Sampler          | 10       |
| Retro Synth        | 9        |
| Alchemy            | 7        |
```

### Session Players Characters

```
| Character                        | Usage |
|----------------------------------|-------|
| Electric Bass - Modern R&B       | 183   |
| Acoustic Piano - Strummed        | 120   |
| Keyboard - Supporting Pad        | 66    |
| Acoustic Drummer - Neo Soul      | 63    |
```

### Per-Project Details

```
### Example Project

**Musical Attributes:**
- Tempo: 120.0 BPM
- Key: C minor
- Time Signature: 4/4
- Tracks: 15

**Binary Structure:**
- Total Chunks: 801
- Track: 320
- MIDISequence: 169
- EventSequence: 169
- AudioRegion: 38

**Session Players Presets:**
*Electric Bass - Modern R&B:*
- **Steady Rolling** (Type_ElectricBassV2)
  - intensity: 79, dynamics: 100, riffiness: 3
```

## 🎯 Use Cases

### For Musicians/Producers

- Track plugin usage across projects
- Identify most-used Session Players presets
- Analyze musical patterns (key, tempo, time signatures)
- Document project complexity
- Archive project metadata

### For Researchers

- Reverse engineer Logic Pro format
- Document binary structures
- Extract embedded configurations
- Study plugin architectures
- Develop third-party tools

### For Project Management

- Inventory audio resources
- Track sample usage
- Document project settings
- Generate project reports
- Analyze workflow patterns

## ⚙️ Requirements

- **Python:** 3.7 or higher
- **Dependencies:** None (standard library only)
- **Platform:** macOS (tested on Sonoma 14.x)
- **Logic Pro:** 10.x - 11.x

## 🔍 Technical Details

### Binary Format

- Chunk-based structure (similar to IFF/RIFF)
- Reversed FourCC markers (e.g., `karT` = "Trak" backwards)
- Mixed endianness (primarily Big-Endian)
- Multiple string encoding methods
- JSON-embedded configurations

### File Locations

```
Project.logicx/
├── Alternatives/000/
│   ├── MetaData.plist          # Metadata (analyzed)
│   └── ProjectData             # Binary data (analyzed)
├── Resources/
│   └── ProjectInformation.plist # Version info
└── Media/                       # Audio files
```

### Performance

- Typical project (2-3 MB): 1-2 seconds
- Large project (10+ MB): 5-10 seconds
- Memory usage: 100-200 MB

## 📝 Version History

### Version 2.0 (December 2025) - Current

- ✅ Advanced binary format parsing
- ✅ Plugin detection and analysis
- ✅ Session Players preset extraction
- ✅ Binary structure mapping
- ✅ Alchemy library reference extraction
- ✅ Tempo extraction from binary data
- ✅ Enhanced reporting with 6 new sections

### Version 1.0 (November 2025)

- ✅ Basic metadata extraction
- ✅ Track name extraction (partial)
- ✅ Audio resource counting
- ✅ Musical attribute analysis
- ✅ CSV export

## 🤝 Contributing

If you discover new patterns or decode additional chunks:

1. Document findings in markdown
2. Add test cases to analyzers
3. Update RESEARCH_SUMMARY.md
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## 📜 License

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE.md](LICENSE.md) file for details.

**Educational/Research Use Only**

This research is for educational purposes and personal project analysis. The Logic Pro file format is proprietary to Apple Inc. This reverse engineering is conducted for interoperability and archival purposes only.

**No Warranty:** Tools provided as-is. Always backup projects before analysis.

**Not Affiliated:** Not affiliated with or endorsed by Apple Inc.

## 📧 Support

For issues or questions:

- Check docs/ folder
- Refer to docs/RESEARCH_SUMMARY.md for technical details

## 🔗 Quick Links

- **Main Analyzer:** [scripts/logic_project_analyzer_enhanced.py](scripts/logic_project_analyzer_enhanced.py)
- **Complete Guide:** [docs/README_BINARY_ANALYSIS.md](docs/README_BINARY_ANALYSIS.md)
- **Research Findings:** [docs/RESEARCH_SUMMARY.md](docs/RESEARCH_SUMMARY.md)
- **Format Spec:** [docs/BINARY_FORMAT_FINDINGS.md](docs/BINARY_FORMAT_FINDINGS.md)

---

**Last Updated:** January 2, 2026
**Version:** 2.0 (Advanced Binary Analysis)
**Status:** ✅ Production Ready

## Credits

Logic Pro and Logic Pro X are trademarks of Apple Inc. This project reads
project files produced by Logic Pro and is not affiliated with or endorsed by
Apple.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the project fits together.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the project fits together — the
layout, the data flow, and the constraints worth knowing before changing it.

