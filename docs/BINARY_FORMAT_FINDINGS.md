# Logic Pro ProjectData Binary Format - Reverse Engineering Findings

## Overview

This document summarizes findings from reverse engineering the binary format of Logic Pro's `ProjectData` files located at `Alternatives/000/ProjectData` within `.logicx` project bundles.

## File Structure

### Magic Markers (4-byte identifiers)

The format uses reversed 4-character codes (fourCC) as markers:

| Marker | Decoded | Frequency | Purpose                           |
| ------ | ------- | --------- | --------------------------------- |
| `karT` | Track   | ~320      | Track/channel definition          |
| `qSvE` | EvSq    | ~169      | Event Sequence (MIDI/automation?) |
| `qeSM` | MSeq    | ~169      | MIDI Sequence                     |
| `gRuA` | AuRg    | ~38       | Audio Region                      |
| `tSxT` | TxSt    | ~32       | Text data                         |
| `LFUA` | AUFL    | ~23       | Audio File reference              |
| `lFuA` | AuFl    | ~23       | Audio File variant                |
| `PMOC` | COMP    | ~23       | Compression/Comping data          |
| `tSnI` | InSt    | 1         | Instrument definition             |
| `snrT` | Trns    | 1         | Transpose/transformation          |
| `MroC` | CorM    | ?         | Core MIDI?                        |

**Pattern**: Markers appear to be reversed ASCII strings (e.g., "karT" = "Trak" backwards)

### Data Layout Around Markers

#### Track Marker (`karT`)

```
Offset   Bytes                              Description
-------- ---------------------------------- -----------
-16      [variable]                         Padding/previous structure
+0       6b 61 72 54                        "karT" marker
+4       05 00 17 00                        Unknown (possibly flags/size)
+8       00 00 00 00 00 00 ff ff           Unknown
+16      ff ff ff ff ff 7f                 Unknown
+22      02 00 00 00 02 00 00 00           Unknown
...      [followed by other markers]
```

**Observations**:

- Track markers do NOT appear to have immediately following track names
- Track names are likely stored elsewhere with references/indices
- Following the `karT` marker, other markers appear (qSvE, tSnI, etc.)

#### Audio Region Marker (`gRuA`)

```
Offset   Example Bytes                      Notes
-------- ---------------------------------- -----------
+0       67 52 75 41                        "gRuA" marker
+4-8     [variable length data]             Region properties
```

**Observations**:

- Audio regions contain references to audio files
- May contain position, length, fade information

## Data Types Discovered

### 1. JSON-Embedded Configuration

**Location**: Large sections contain complete JSON objects
**Content**: Plugin/Instrument presets with full parameter sets

Example structure:

```json
{
  "Preset": {
    "Name": "Sweet Memories",
    "CharacterIdentifier": "Acoustic Piano - Strummed",
    "Parameters": {
      "intensity": 71,
      "dynamics": 119,
      "humanize": 37,
      "variation": 1,
      "fillsAmount": 69,
      "rComp": 42,
      "mComp": 3
    },
    "Type": "TypeFactoryPreset",
    "PresetIdentifier": "Acoustic Piano - Strummed - Sweet Memories.dpst"
  },
  "RegionType": "Type_AcousticPianoV2",
  "GeneratorMemento": { ... }
}
```

**Instruments Found**:

- Acoustic Piano (Session Players)
- Electric Bass (Session Players)
- Electronic Drummer (Session Players)

### 2. Alchemy Synth Data

**Embedded Paths** to Alchemy library files:

- `Alchemy/Libraries/WaveOsc/Basic/Sine.raw`
- `Alchemy/Libraries/WaveOsc/Basic/Saw.raw`
- `Alchemy/Libraries/WaveLfo/Basic/*.raw`
- `Alchemy/Libraries/Formant/Vowel1 [AEIOU].csv`
- `Alchemy/Libraries/OscillatorPitch/Unison.csv`
- `Alchemy/Libraries/OscillatorAmp/*.csv`
- `Alchemy/Libraries/Window/Tukey.csv`
- `Alchemy/Libraries/WaveNoise/White.wav`
- `Alchemy/Libraries/WaveNoise/Radio.wav`

### 3. String Encoding Methods

Multiple string encoding methods observed:

#### Method A: Null-Terminated Strings

```
[string bytes] 00
```

#### Method B: Length-Prefixed (Pascal-style)

```
[1-byte length] [string bytes]
```

Example: `0A 50 6C` = 10 bytes, "Pl..."

#### Method C: 2-Byte Length Prefix (Big-Endian)

```
[2-byte length BE] [string bytes]
```

#### Method D: 4-Byte Length Prefix (Big-Endian)

```
[4-byte length BE] [string bytes]
```

Common for larger JSON blocks

### 4. Numeric Data

#### Float32 (BPM, Parameters)

- **Range observed**: 40.0 - 240.0 BPM
- **Encoding**: Both big-endian and little-endian found
- **Context**: Musical tempo, plugin parameters

#### Int32 (Sample positions, counts)

- **Encoding**: Big-endian appears more common
- **Usage**: Sample offsets, region lengths, frame counts

## Plugin/Instrument Detection

### Successfully Extracted:

1. **Plugin Names**:

   - Alchemy (synth)
   - Sampler
   - Q-Sampler (Quick Sampler)

2. **Session Players Presets**:

   - Acoustic Piano - "Sweet Memories"
   - Electric Bass - "Night Flight"
   - Electronic Drummer - "Hit Factory"

3. **Preset Parameters** (decoded from JSON):
   - Intensity (0-127)
   - Dynamics (0-127)
   - Humanize (0-100)
   - Variation (1-4)
   - Fill amounts
   - Rhythm complexity (rComp, mComp)

### Parameter Details

Session Players (Drummer/Bass/Keys) store:

- **Generator Seeds**: Random seeds for pattern generation
- **Region Start/End Params**: Parameters at region boundaries for automation
- **Controller Values**: MIDI CC values (sustain, pitch bend, vibrato, pressure)
- **Humanization State**: Timing shifts, directional variations
- **Follow Track**: UUID of tracked track for chord following
- **Manual Mode**: Pattern step data for user-created patterns

## Chunk-Like Structures

Evidence of chunk-based format:

```
[4-byte type ID] [4-byte size] [data...]
```

Similar to RIFF/IFF formats but with Logic-specific markers.

## Automation Data

Format appears to store:

- **Event Sequences** (`qSvE`): Automation events
- **MIDI Sequences** (`qeSM`): Note data, CC automation
- **Parameter Interpolation**: Start/end values for smooth transitions

## Track Names - Current Status

**Challenge**: Track names are not immediately adjacent to `karT` markers.

**Hypotheses**:

1. Track names may be in a separate index/table
2. Names might use an indirect reference (offset pointer)
3. Could be stored in a different section of the file
4. May require parsing parent structure to locate

**Evidence**:

- Strings like "Audio 1", "Audio 2" found via regex but not reliably associated with tracks
- Region names for Session Players found in JSON (not custom track names)

## File References

Audio files and samples are referenced by:

- **Relative paths** within Alchemy library
- **Absolute paths** for user audio: `/Library/Application Support/Logic/Alchemy/...`
- **Embedded in JSON** for Session Players regions

## Next Steps for Further Research

1. **Track Name Location**:

   - Analyze file header/footer sections
   - Look for offset tables/indices
   - Compare multiple project versions to find name differences

2. **Chunk Hierarchy**:

   - Map parent-child relationships between chunks
   - Determine if there's a container structure

3. **Numeric Fields**:

   - Decode the unknown bytes around markers
   - Identify flags, version numbers, indices

4. **Compression**:

   - Check if any sections use compression (zlib, etc.)
   - The `PMOC` (COMP) marker suggests possible compression

5. **Version Detection**:
   - File format may vary by Logic Pro version
   - Header should contain version identifier

## Tools Created

1. **binary_format_analyzer.py**: Identifies markers, extracts strings, analyzes patterns
2. **extract_plugin_data.py**: Extracts JSON presets, plugin names, audio references
3. **hex_dump_analyzer.py**: Creates annotated hex dumps around markers
4. **logic_project_analyzer_enhanced.py**: Main analyzer integrating all findings

## References

- Logic Pro version: ~11.x (based on embedded version strings)
- File format appears proprietary, no public documentation
- Similar to other DAW project formats (chunk-based binary with embedded data)

---

**Last Updated**: 2025-12-05
**Analyzed File**: `Example Project.logicx/Alternatives/000/ProjectData`
**File Size**: 2,801,481 bytes
