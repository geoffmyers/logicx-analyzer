---
title: Architecture
description: How the Logic Pro project analyzer reads an undocumented binary format.
---

# Architecture

A set of Python analysis scripts for Logic Pro (`.logicx`) projects. There is no
published format specification, so the tooling is built around progressive
reverse engineering rather than a parser generated from a spec.

## Layout

| Path | What lives there |
|---|---|
| `scripts/logic_project_analyzer.py` | The main analyzer; `_enhanced` is the fuller pass. |
| `scripts/binary_format_analyzer.py`, `chunk_structure_analyzer.py`, `hex_dump_analyzer.py` | Format archaeology — chunk discovery and byte-level inspection. |
| `scripts/extract_track_names.py`, `extract_plugin_data.py` | Targeted extractors for the fields that are understood. |
| `scripts/experimental/` | Decoding attempts kept for reference. Not part of the supported path. |
| `docs/` | Notes on what has been decoded so far. |

## Notes

- A `.logicx` project is a **bundle** (a directory), not a single file.
- Findings are partial by nature: the extractors cover the structures that have
  been identified, and `experimental/` records the ones that have not.
