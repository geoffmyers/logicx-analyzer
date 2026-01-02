# Contributing to LogicX Analyzer

Thank you for your interest in contributing to the LogicX Analyzer project! This document provides guidelines for contributing to the reverse engineering effort of Logic Pro's binary format.

## 🎯 Project Goals

- Decode Logic Pro's proprietary ProjectData binary format
- Extract metadata, plugins, presets, and project structure
- Create tools for musicians and researchers to analyze Logic projects
- Document findings for educational and archival purposes

## 🔬 Current Status

- **~60% format decoded** - significant progress but still incomplete
- **High priority**: Track name extraction (custom names location unknown)
- See [docs/RESEARCH_SUMMARY.md](docs/RESEARCH_SUMMARY.md) for detailed status

## 🤝 How to Contribute

### 1. Format Research & Discovery

**Found a new chunk type or data structure?**

1. Document your findings in markdown format
2. Include hex dumps showing the pattern
3. Provide sample data (anonymize file paths)
4. Explain how to reproduce the discovery
5. Update [docs/RESEARCH_SUMMARY.md](docs/RESEARCH_SUMMARY.md)

**Example format:**
```markdown
## New Chunk Discovery: `XyZw` marker

**Purpose**: Appears to control [functionality]
**Location**: Found at offset [X] in ProjectData
**Frequency**: [N] occurrences per project
**Structure**:
- Bytes 0-3: `XyZw` marker
- Bytes 4-7: Length (Big-Endian int32)
- Bytes 8+: Data payload

**Hex dump example**:
\`\`\`
00001234: 58 79 5a 77 00 00 00 10  ...
\`\`\`
```

### 2. Code Contributions

**Adding new analyzers or improving existing ones:**

1. **Follow existing patterns**:
   - Use classes like `ProjectDataAnalyzer`, `PluginDataExtractor`
   - Include docstrings for all functions
   - Use type hints where possible
   - Follow PEP 8 style guidelines

2. **Test with multiple projects**:
   - Test on at least 3-5 different Logic projects
   - Include different Logic Pro versions (10.x, 11.x)
   - Test various project sizes and complexities

3. **Update documentation**:
   - Add usage examples to README.md
   - Document new findings in appropriate docs/ files
   - Update CLAUDE.md if architecture changes

4. **Submit clean commits**:
   ```bash
   git add <files>
   git commit -m "Add: Brief description of what you added"
   ```

### 3. Bug Reports

**Found an issue?**

Include:
- Python version
- macOS version
- Logic Pro version
- Sample error output
- Steps to reproduce

### 4. Feature Requests

**Have an idea for improvement?**

1. Check existing documentation first
2. Open an issue describing the feature
3. Explain the use case
4. Suggest implementation approach (if you have ideas)

## 📁 Code Organization

### Production Scripts (scripts/)
- `logic_project_analyzer_enhanced.py` - Main analyzer (add general features here)
- `binary_format_analyzer.py` - Low-level binary analysis
- `chunk_structure_analyzer.py` - File structure mapping
- `extract_plugin_data.py` - Plugin/preset extraction
- `hex_dump_analyzer.py` - Hex-level investigation
- `extract_track_names.py` - Track name extraction (needs improvement!)

### Experimental Scripts (scripts/experimental/)
- Archive for research prototypes
- Not for production use
- See [scripts/experimental/README.md](scripts/experimental/README.md)

### Documentation (docs/)
- `RESEARCH_SUMMARY.md` - Complete findings
- `BINARY_FORMAT_FINDINGS.md` - Technical specification
- `README_BINARY_ANALYSIS.md` - Analysis guide
- `QUICK_REFERENCE.md` - Command reference

## 🧪 Testing Guidelines

### Manual Testing
```bash
# Test main analyzer
python3 scripts/logic_project_analyzer_enhanced.py

# Test on specific project
python3 scripts/binary_format_analyzer.py "path/to/ProjectData"

# Compare results across Logic versions
python3 scripts/chunk_structure_analyzer.py "path/to/Project_v10.logicx/Alternatives/000/ProjectData"
python3 scripts/chunk_structure_analyzer.py "path/to/Project_v11.logicx/Alternatives/000/ProjectData"
```

### What to Test For
- ✅ Correct tempo extraction
- ✅ Plugin names properly decoded
- ✅ JSON presets parse without errors
- ✅ Chunk counts match expected values
- ✅ No crashes on malformed data
- ✅ Handles missing files gracefully

## 🎨 Code Style

### Python Style
- **PEP 8** compliance
- **Type hints** for function signatures
- **Docstrings** for all public functions
- **4 spaces** for indentation (no tabs)

### Example Function
```python
def extract_chunk_data(data: bytes, offset: int, marker: bytes) -> Optional[Dict[str, Any]]:
    """
    Extract data from a chunk starting at the given offset.

    Args:
        data: Complete binary file data
        offset: Position where chunk begins
        marker: 4-byte chunk marker to look for

    Returns:
        Dictionary with chunk info, or None if invalid
    """
    if data[offset:offset+4] != marker:
        return None

    # Implementation...
    return chunk_info
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `ProjectDataAnalyzer`)
- **Functions**: `snake_case` (e.g., `extract_json_objects`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `CHUNK_MARKERS`)
- **Private**: `_leading_underscore` (e.g., `_parse_header`)

## 🔍 Research Best Practices

### When Analyzing Binary Data

1. **Always use hex editors** alongside Python scripts
   - HexFiend (macOS), 010 Editor, or ImHex recommended

2. **Document byte offsets** in your findings
   - Makes it reproducible for others

3. **Look for patterns** across multiple files
   - Don't assume one project is representative

4. **Test edge cases**:
   - Empty projects
   - Maximum track count
   - Different time signatures
   - Non-standard sample rates

### Research Priorities (Help Wanted!)

1. **Track Name Location** 🔥 **HIGH PRIORITY**
   - Custom track names location still unknown
   - Generic names work ("Audio 1") but custom names elusive
   - Likely in offset table or index structure

2. **Compression Detection**
   - Some chunks may be compressed (zlib, gzip)
   - PMOC chunks are candidates

3. **AU/VST Plugin States**
   - Native plugins work (Alchemy, Sampler)
   - Third-party plugin state format unknown

4. **Complete Automation Curves**
   - qSvE chunks identified but not fully decoded
   - Parameter automation over time

5. **Full MIDI Note Data**
   - qeSM chunks contain MIDI data
   - Note on/off, velocity, CC extraction

## 📜 Legal & Ethical Guidelines

### Research Scope
✅ **Allowed**:
- Analyzing your own Logic Pro projects
- Educational reverse engineering
- Interoperability research
- Personal archival purposes
- Publishing findings and tools

❌ **Not Allowed**:
- Circumventing copy protection
- Enabling piracy
- Violating Logic Pro EULA
- Redistributing Apple's binaries
- Commercial use without proper licensing

### Attribution
- Logic Pro is © Apple Inc.
- This project is not affiliated with or endorsed by Apple
- Always include disclaimer in derivative works

## 🚀 Submitting Contributions

### Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/your-feature-name`
3. **Make changes** following guidelines above
4. **Test thoroughly** with multiple projects
5. **Commit** with clear messages
6. **Push** to your fork
7. **Open a Pull Request** with description of changes

### PR Description Template
```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Research findings
- [ ] Documentation update
- [ ] Code refactoring

## Testing
Describe testing performed:
- Logic Pro version:
- Number of projects tested:
- Test results:

## New Findings (if applicable)
Document any new chunk types, markers, or format discoveries

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tested on multiple projects
- [ ] No personal file paths in code/output
```

## 💬 Communication

### Questions?
- Check [docs/](docs/) folder first
- Review [RESEARCH_SUMMARY.md](docs/RESEARCH_SUMMARY.md)
- Open a GitHub Issue for discussion

### Sharing Discoveries
When sharing discoveries, please:
- Anonymize file paths
- Remove personal project names
- Include only relevant hex dumps (not entire files)

## 🙏 Recognition

Contributors will be recognized in project documentation. Significant research contributions may be highlighted in RESEARCH_SUMMARY.md.

Thank you for helping decode Logic Pro's format! 🎵

---

**Last Updated**: January 2, 2026
