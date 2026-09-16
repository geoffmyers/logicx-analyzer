# Experimental Scripts

This directory contains early research prototypes and experimental scripts that explored different approaches to decoding Logic Pro's binary ProjectData format. These scripts are preserved for historical reference and educational purposes but have been **superseded by the main production analyzers**.

## ⚠️ Status: Archived

**DO NOT USE** these scripts for production analysis. They represent early experimental work and contain incomplete or incorrect implementations.

## Current Production Tools

Use these instead:
- **[logic_project_analyzer_enhanced.py](../logic_project_analyzer_enhanced.py)** - Complete analyzer with all features
- **[binary_format_analyzer.py](../binary_format_analyzer.py)** - Deep binary structure analysis
- **[extract_plugin_data.py](../extract_plugin_data.py)** - Plugin/preset extraction
- **[chunk_structure_analyzer.py](../chunk_structure_analyzer.py)** - File structure mapping

## Scripts in This Directory

### decode_logic.py & decode_logic_v2.py
**Purpose**: Early string extraction experiments
**Approach**: Regex-based ASCII string extraction from binary data
**Findings**: Demonstrated that strings can be extracted, but without context they're not useful
**Superseded by**: String extraction methods in `logic_project_analyzer_enhanced.py`

### logic_deep_decode.py & logic_deep_decode_v2.py
**Purpose**: Variable-length integer parsing experiments
**Approach**: Attempted to decode Logic's tick-based timing system (960 PPQ)
**Findings**: Variable-length encoding exists but is not the primary data format
**Status**: Incomplete - tick parsing works but doesn't unlock track names or major structures

### recursive_unarchive.py
**Purpose**: NSKeyedArchiver exploration
**Approach**: Attempted to treat ProjectData as an NSKeyedArchive (macOS serialization format)
**Findings**: **ProjectData is NOT an NSKeyedArchive** - it uses a custom chunk-based binary format
**Status**: Dead end - incorrect hypothesis about file format

## What We Learned

These experiments contributed to the current understanding:

1. **String Extraction Works**: Regex patterns can find ASCII strings, but context is needed
2. **Not NSKeyedArchive**: ProjectData uses a custom binary format, not standard macOS serialization
3. **Multiple Encodings**: File uses multiple string encoding methods (length-prefixed, null-terminated)
4. **Chunk-Based Structure**: File uses FourCC markers (reversed) to identify data chunks
5. **JSON Embedded**: Session Players data is stored as JSON within binary stream

## Research Timeline

- **Early December 2025**: Initial exploration with these experimental scripts
- **Mid December 2025**: Chunk-based structure identified, JSON extraction working
- **Late December 2025**: Production analyzers developed
- **January 2026**: Scripts archived to `experimental/` directory

## For Researchers

If you're conducting your own research:
1. Start by reading [docs/RESEARCH_SUMMARY.md](../../docs/RESEARCH_SUMMARY.md)
2. Review the production analyzers to see current best practices
3. Use these experimental scripts as cautionary examples of approaches that didn't work
4. The hex dump tools are more effective than trying to parse as structured data

## Historical Value

These scripts are kept because they:
- Document the research process
- Show what approaches were tried and why they failed
- Provide examples of Python binary data manipulation techniques
- May contain useful utility functions for future experiments

---

**Last Updated**: January 2, 2026
**Status**: Archived - Historical Reference Only
