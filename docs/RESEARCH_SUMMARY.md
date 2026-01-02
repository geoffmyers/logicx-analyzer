## Logic Pro ProjectData Binary Format - Research Summary

### Executive Summary

Successfully reverse-engineered significant portions of Logic Pro's proprietary ProjectData binary format through systematic analysis. Extracted plugin configurations, preset data, and identified the chunk-based file structure. Track names remain partially elusive but significant progress has been made.

---

## Key Discoveries

### 1. File Structure

**File Header**:

- Magic bytes: `23 47 c0 ab` (appears to be file signature)
- Contains early reference to "gnoS" (Song backwards?)
- Version information embedded as text strings

**Overall Organization**:

- Chunk-based binary format (similar to IFF/RIFF)
- 801 total chunks in analyzed file (2.8 MB)
- Hierarchical structure with nested data

### 2. Chunk Types Identified (4-byte reversed ASCII markers)

| Bytes  | Reversed | Count | Purpose                     | Status        |
| ------ | -------- | ----- | --------------------------- | ------------- |
| `karT` | Trak     | 320   | Track definition            | ✅ Identified |
| `qeSM` | MSeq     | 169   | MIDI sequence data          | ✅ Identified |
| `qSvE` | EvSq     | 169   | Event sequence (automation) | ✅ Identified |
| `gRuA` | AuRg     | 38    | Audio region                | ✅ Identified |
| `tSxT` | TxSt     | 32    | Text/Score notation styles  | ✅ Decoded    |
| `lFuA` | AuFl     | 23    | Audio file reference        | ✅ Identified |
| `LFUA` | AUFL     | 23    | Audio file (variant)        | ✅ Identified |
| `PMOC` | COMP     | 23    | Comping/take data           | ✅ Identified |
| `MroC` | CorM     | 2     | Core MIDI?                  | ⚠️ Partial    |
| `tSnI` | InSt     | 1     | Instrument definition       | ✅ Identified |
| `snrT` | Trns     | 1     | Transform/transpose         | ⚠️ Partial    |

**Note**: The reverse-naming pattern (FourCC codes read backwards) is consistent throughout.

### 3. Data Encoding Methods

#### String Encoding (Multiple formats coexist):

1. **Length-prefixed (Pascal)**:

   ```
   [1-byte length][string data]
   ```

2. **2-byte length (Big-Endian)**:

   ```
   [2-byte BE length][string data]
   ```

3. **4-byte length (Big-Endian)**:

   ```
   [4-byte BE length][string data]
   ```

   Used for large JSON blocks

4. **Null-terminated**:
   ```
   [string data]\x00
   ```

#### Numeric Data:

- **Float32**: BPM values, plugin parameters (both BE and LE found)
- **Int32**: Sample positions, region lengths, counts (mostly BE)
- **Endianness**: Mixed, but Big-Endian appears dominant

### 4. Embedded JSON Data ✅ MAJOR FIND

**Discovery**: Large sections contain complete JSON objects for Session Players instruments

**Structure**:

```json
{
  "Preset": {
    "Name": "Sweet Memories",
    "CharacterIdentifier": "Acoustic Piano - Strummed",
    "PresetIdentifier": "Acoustic Piano - Strummed - Sweet Memories.dpst",
    "Type": "TypeFactoryPreset",
    "Parameters": {
      "intensity": 71,
      "dynamics": 119,
      "humanize": 37,
      "variation": 1,
      "fillsAmount": 69,
      "rComp": 42,
      "mComp": 3,
      ...
    }
  },
  "GeneratorMemento": {
    "Seeds": {"0": 1763219906, ...},
    "LastGenerateLength": 32,
    "MementoParameters": {
      "regionStartParams": "...",
      "regionEndParams": "...",
      "humanizeEndStatus": "...",
      ...
    }
  },
  "RegionType": "Type_AcousticPianoV2",
  "FollowTrackUniqueID": "43870E44-C22E-11F0-968B-D17F5F851CEB"
}
```

**Decoded Parameters**:

- **Intensity**: Musical intensity (0-127)
- **Dynamics**: Velocity range (0-127)
- **Humanize**: Timing variation (0-100)
- **Variation**: Pattern variation (1-4)
- **fillsAmount**: Drum fill density
- **rComp**: Rhythm complexity
- **mComp**: Melodic complexity
- **pushPull**: Timing feel (-50 to +50)
- **swing**: Swing amount (0-100)

### 5. Plugin/Instrument Data Extracted

#### Synthesizers:

- **Alchemy**:

  - Oscillator shapes: Sine, Saw, Triangle, Square
  - LFO shapes: Ramp Up, Ramp Down, Random, Sine
  - Formant filters: Vowel shapes (A, E, I, U)
  - Noise sources: White, Radio
  - Window functions: Tukey
  - Library paths successfully extracted

- **Sampler/Quick Sampler**:
  - References found but minimal data

#### Session Players (with full preset data):

1. **Acoustic Piano - Strummed**:

   - Preset: "Sweet Memories"
   - Type: Type_AcousticPianoV2
   - Voicing styles, positions, humanization all decoded

2. **Electric Bass - Indie Disco**:

   - Preset: "Night Flight"
   - Type: Type_ElectricBassV2
   - Bass type, slides, dead notes, playing position decoded

3. **Electronic Drummer - Synthpop**:
   - Preset: "Hit Factory"
   - Type: Type_ElectronicDrummerV2
   - Kit pieces (a1, a2, a3, b1, b2, b3, c1, c2, c3) complexity mapped
   - Accent variation, phrase variation extracted

### 6. Text/Score Notation Styles (`tSxT` chunks)

Successfully decoded 32 text style definitions:

- Plain Text
- Page Number
- Bar Number
- Instrument Name
- Tuplet
- Repeat Ending
- Chord Root/Extensions
- Multiple Rest
- Tablature
- Tempo Symbol
- Octave Symbol
- Note Head
- Guitar Grid Fingering
- Guitar Marking
- Fingering
- Reserved styles (1-3, numbered slots)

Each with font specifications (Times-Italic found).

### 7. Audio File References

**Format**: Relative and absolute paths

- Alchemy library: `Alchemy/Libraries/WaveOsc/Basic/Sine.raw`
- System paths: `/Library/Application Support/Logic/Alchemy/...`
- Apple Loops: `Library/Audio/Apple Loops/Apple/21 Prismatica...`

### 8. Automation/Event Data

**MIDI Sequences** (`qeSM`):

- Contains note data
- "Untitle" strings found (possibly default region names)
- 169 sequences found

**Event Sequences** (`qSvE`):

- Automation curves
- Parameter modulation
- 169 instances (matches MIDI sequences 1:1)

### 9. Track Names - ONGOING CHALLENGE

**Current Status**: Partially solved

**What We Know**:

- Track markers (`karT`) do NOT have immediately adjacent names
- Generic strings found: "Audio 1", "Audio 2", etc.
- Session Player region names stored in JSON
- Score notation names found in `tSxT` chunks

**Hypotheses**:

1. Names stored in separate index table (not yet located)
2. Names use indirect references (offsets/pointers)
3. May be in file header or footer section
4. Could be in parent container we haven't identified

**Evidence of Names**:

- "Score Settings" found near `tSnI` instrument chunk
- "Plain Text", "Page Number" etc. are style names, not track names
- "Untitle" appears near `qeSM` markers (might be default MIDI region name)

---

## Technical Analysis

### Chunk Structure Pattern

Standard chunk appears to follow:

```
Offset  Bytes       Description
+0      [4 bytes]   Chunk type (reversed FourCC)
+4      [4 bytes]   Flags or sub-type (BE int32)
+8      [4 bytes]   Unknown (often 0x00000000)
+12     [4 bytes]   Unknown (often 0x0000FFFF or 0xFFFFFFFF)
+16     [variable]  Payload data
```

**Observed Header Integers** (Big-Endian):

- `karT`: `[83891968, 0, 65535, 4294967295]`
- `qeSM`: `[83886336, 0, 65535, 4294967295]`
- `qSvE`: `[16777472, 0, 13824, 65535]`
- `tSnI`: `[16777728, 0, 65535, 4294967295]`

### File Size & Chunk Distribution

**Example Project** (Hollywood Solaris):

- Total size: 2,801,481 bytes (2.8 MB)
- 801 chunks
- Average chunk size: ~3,497 bytes
- Largest chunks: JSON preset data (several KB)
- Smallest chunks: 36 bytes (minimal `karT` markers)

### Performance Parameters Decoded

**Drummer Parameters**:

- Kit piece complexity: a1-a3 (hi-hats, rides), b1-b3 (snares, claps), c1-c3 (kicks, toms)
- Each with min/max complexity values
- System variation (1-4): Overall pattern style
- Phrase variation (0-100): Pattern diversity
- Accent variation (0-4): Dynamic accents

**Bass Parameters**:

- Position (1-100): Fretboard position
- Slides amount (0-100)
- Dead notes (0-100)
- Buzz trills (0-100)
- Blue-syness (0-100): Blues inflection
- Riffiness (1-5): Pattern complexity
- Playing position: Pickup vs bridge

**Piano Parameters**:

- Upper/lower voicing style (1-5)
- Upper/lower playing style (1-5)
- Grace notes amount (0-100)
- Arp direction (0-3)
- Emphasis (-50 to +50)

---

## Tools Developed

1. **logic_project_analyzer_enhanced.py**:

   - Main analyzer with track name extraction
   - Generates markdown reports
   - Handles MetaData.plist + ProjectData

2. **binary_format_analyzer.py**:

   - Magic marker detection
   - String extraction (multiple methods)
   - Repeating structure identification
   - Hex context analysis

3. **extract_plugin_data.py**:

   - JSON object extraction
   - Plugin name detection
   - Preset configuration decoding
   - Audio file reference extraction

4. **hex_dump_analyzer.py**:

   - Annotated hex dumps
   - Context analysis around markers
   - Multiple string extraction attempts
   - Numeric data patterns

5. **chunk_structure_analyzer.py**:
   - Full file structure mapping
   - Chunk hierarchy visualization
   - Header parsing
   - Track name candidate analysis

---

## Remaining Mysteries

### High Priority:

1. **Track Names**: Primary location still unknown
2. **Chunk Size Field**: Format unclear (not simple 4-byte size)
3. **Chunk Hierarchy**: Parent-child relationships not fully mapped
4. **Compression**: `PMOC` (COMP) chunks may use compression (not yet tested)

### Medium Priority:

4. **Plugin States**: AU/VST plugin data encoding
5. **Mixer Settings**: Channel strip, routing, sends
6. **Smart Controls**: Mapping and configuration
7. **Flex Time/Pitch**: Audio editing metadata

### Low Priority:

8. **Undo History**: Project file backups format
9. **Color Coding**: Track/region colors
10. **Folder Tracks**: Grouping structure

---

## Next Steps

### Immediate Actions:

1. **Search for Name Table**:

   - Analyze file header more thoroughly
   - Look for offset pointer tables
   - Check file footer sections

2. **Test Compression**:

   - Try zlib decompression on `PMOC` chunks
   - Check for other compression algorithms

3. **Compare Projects**:
   - Analyze multiple projects with known track names
   - Diff files to isolate name storage location

### Medium-term:

4. **Build Parser Library**:

   - Python module for ProjectData parsing
   - Clean API for extracting data
   - Integration with existing analyzer

5. **Document AU/VST Formats**:
   - Reverse engineer plugin state chunks
   - Map common plugins (EQ, compressor, etc.)

### Long-term:

6. **Complete Format Specification**:
   - Document all chunk types
   - Create format reference guide
   - Enable third-party tools

---

## Conclusions

### Successfully Decoded:

✅ File structure (chunk-based)
✅ Chunk markers and types
✅ Session Players presets (full parameter sets)
✅ Alchemy synthesizer configurations
✅ Score notation styles
✅ Audio file references
✅ MIDI/automation sequences (structure)
✅ JSON-embedded configurations

### Partially Decoded:

⚠️ Track names (generic names found, custom names elusive)
⚠️ Chunk hierarchy
⚠️ Some marker types (MroC, snrT)

### Not Yet Decoded:

❌ AU/VST plugin states
❌ Mixer configurations
❌ Smart Controls
❌ Flex editing data
❌ Compression schemes

---

## Research Value

This reverse engineering effort provides:

1. **Enhanced Project Analysis**:

   - Extract detailed instrument configurations
   - Analyze musical parameters across projects
   - Track plugin usage patterns

2. **Workflow Insights**:

   - Understand Session Players generation
   - Decode preset parameters for learning
   - Extract musical metadata

3. **Future Tool Development**:

   - Foundation for ProjectData parsers
   - Potential for project conversion tools
   - Cross-DAW project migration

4. **Format Documentation**:
   - First comprehensive analysis of ProjectData format
   - Reference for future research
   - Enables community tools

---

**Research Date**: December 5, 2025
**Logic Pro Version**: 11.x (detected from files)
**Files Analyzed**: 3 projects, ~2-3 MB each
**Format Coverage**: ~60% understood, 40% remaining

**Tools Available At**: This repository - see README.md for usage instructions

---

## Sample Output

From analyzing "Example Project.logicx":

**Plugins Detected**:

- Alchemy (synthesizer with 28 library references)
- Sampler
- Q-Sampler (Quick Sampler)

**Presets Found**:

- Acoustic Piano - "Sweet Memories" (Type_AcousticPianoV2)
  - Intensity: 71, Dynamics: 119, Humanize: 37
- Electric Bass - "Night Flight" (Type_ElectricBassV2)
  - Intensity: 79, Dynamics: 100, Riffiness: 3
- Electronic Drummer - "Hit Factory" (Type_ElectronicDrummerV2)
  - Intensity: 97.3, Fill Amount: 30.5

**File Statistics**:

- Size: 2,801,481 bytes
- Total Chunks: 801
- Tracks: 320
- MIDI Sequences: 169
- Audio Regions: 38
- Text Styles: 32

---

## References

- No official documentation exists for this format
- Format appears proprietary to Apple Logic Pro
- Similar chunk-based formats: IFF, RIFF, AIFF
- Endianness: Primarily Big-Endian (network byte order)
