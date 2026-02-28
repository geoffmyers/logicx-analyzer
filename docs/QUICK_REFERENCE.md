---
title: Logicx Analyzer - Quick Reference Card
created: 2026-02-04
modified: 2026-02-04
description: "``bash cd \"/path/to/logic/projects\" python3 \"logicx-analyzer/Scripts/logic_project_analyzer_enhanced.py\" ``"
tags: [music]
---

# Logicx Analyzer - Quick Reference Card

## 🚀 Most Common Commands

### Analyze All Projects (Most Used)

```bash
cd "/path/to/logic/projects"
python3 "logicx-analyzer/Scripts/logic_project_analyzer_enhanced.py"
```

**Output:** `logic_projects_advanced_YYYYMMDD_HHMMSS.md`

---

## 📂 Directory Quick Reference

| Path       | Purpose                      |
| ---------- | ---------------------------- |
| `scripts/` | Main analyzers ⭐ START HERE |
| `docs/`    | All documentation            |

---

## 🔧 Script Reference

### Main Scripts

| Script                                    | Command                                              | Output                         | Use When                              |
| ----------------------------------------- | ---------------------------------------------------- | ------------------------------ | ------------------------------------- |
| **logic_project_analyzer_enhanced.py** ⭐ | `python3 scripts/logic_project_analyzer_enhanced.py` | `logic_projects_advanced_*.md` | **You want everything** (recommended) |
| logic_project_analyzer.py                 | `python3 scripts/logic_project_analyzer.py`          | `logic_projects_report_*.md`   | You only need metadata                |
| extract_track_names.py                    | `python3 scripts/extract_track_names.py`             | `track_names_report.md`        | You only need track names             |

### Binary Analysis Tools

| Tool                        | Command                                                   | Output                     | Use When                  |
| --------------------------- | --------------------------------------------------------- | -------------------------- | ------------------------- |
| binary_format_analyzer.py   | `python3 scripts/binary_format_analyzer.py ProjectData`   | `binary_analysis_*.txt`    | Research format structure |
| chunk_structure_analyzer.py | `python3 scripts/chunk_structure_analyzer.py ProjectData` | `chunk_structure_*.txt`    | Map file chunks           |
| extract_plugin_data.py      | `python3 scripts/extract_plugin_data.py ProjectData`      | `plugin_data_*.{txt,json}` | Extract plugins only      |
| hex_dump_analyzer.py        | `python3 scripts/hex_dump_analyzer.py ProjectData`        | `hex_analysis_*.txt`       | Hex-level investigation   |

---

## 📊 What Gets Analyzed

### ✅ Extracted Data

| Category      | Data Points                        |
| ------------- | ---------------------------------- |
| **Musical**   | BPM, Key, Time Signature           |
| **Technical** | Tracks, Sample Rate, Logic Version |
| **Plugins**   | Names, Counts, Usage Statistics    |
| **Presets**   | Session Players configurations     |
| **Binary**    | Chunk counts, Structure complexity |
| **Tracks**    | Names (partial), Region names      |
| **Audio**     | File counts, Sample usage          |

### 📈 Report Sections

1. Summary Statistics (projects, tracks, plugins)
2. Plugin Usage Table
3. Session Players Characters
4. Key Distribution
5. Per-Project Details:
   - Musical Attributes
   - Binary Structure
   - Plugin List
   - Session Players Presets
   - Alchemy References
   - Track Names
   - Region Names
   - Audio Resources

---

## 📚 Documentation Quick Links

| Document                      | What's Inside                | Read When            |
| ----------------------------- | ---------------------------- | -------------------- |
| **README.md**                 | Overview, quick start        | First time using     |
| **README_BINARY_ANALYSIS.md** | Complete usage guide         | Want all details     |
| **RESEARCH_SUMMARY.md**       | Reverse engineering findings | Curious about format |
| **BINARY_FORMAT_FINDINGS.md** | Technical specification      | Need format details  |
| **QUICK_REFERENCE.md**        | This cheat sheet             | Need quick answer    |

---

## 🎯 Common Workflows

### 1️⃣ Analyze a Single Project

```bash
cd "/Users/you/Music/Logic"
python3 "logicx-analyzer/scripts/logic_project_analyzer_enhanced.py"
```

### 2️⃣ Analyze All Projects in Folder

Same command - automatically finds all `.logicx` files in current directory

### 3️⃣ Deep Dive on Specific Project

```bash
PROJECT="My Project.logicx/Alternatives/000/ProjectData"

# Full binary analysis
python3 "scripts/binary_format_analyzer.py" "$PROJECT"

# Chunk structure
python3 "scripts/chunk_structure_analyzer.py" "$PROJECT"

# Plugin extraction
python3 "scripts/extract_plugin_data.py" "$PROJECT"

# Hex dumps
python3 "scripts/hex_dump_analyzer.py" "$PROJECT"
```

---

## 💡 Pro Tips

### Tip 1: Always Run from Project Directory

```bash
# ✅ GOOD
cd "/path/to/your/projects"
python3 "scripts/logic_project_analyzer_enhanced.py"

# ❌ BAD (won't find projects)
python3 "scripts/logic_project_analyzer_enhanced.py" /some/other/path
```

### Tip 2: Use Absolute Paths for Binary Tools

```bash
# ✅ GOOD - absolute path to ProjectData
python3 binary_format_analyzer.py "/full/path/to/Project.logicx/Alternatives/000/ProjectData"

# ⚠️ OK - relative path (if you're in the right directory)
python3 binary_format_analyzer.py "Project.logicx/Alternatives/000/ProjectData"
```

---

## 🔍 Troubleshooting

### Problem: "No Logic Pro projects found"

**Solution:** Make sure you're in a directory with `.logicx` files

```bash
ls *.logicx  # Should list projects
```

### Problem: "Permission denied"

**Solution:** Logic might have project open - close it first

### Problem: Track names not showing

**Expected:** Custom track names are hard to find (format limitation)

- Generic names ("Audio 1") work fine
- Session Player regions work fine

### Problem: Script takes long time

**Normal:** Large projects (10+ MB) take 5-10 seconds
**Solution:** Be patient or analyze fewer projects

---

## 📈 Example Output

### Console Output

```
======================================================================
Advanced Logic Pro Project Analyzer
with Binary Format Reverse Engineering
======================================================================

Scanning directory: /Users/you/Music/Logic
Found 39 Logic Pro project(s)

Processing projects:
[1/39] My Project.logicx... ✓
...

Total Projects: 39
Total Tracks: 588
Plugins Detected: 604
Presets Found: 642
Average Tempo: 99.74 BPM

Report Generated:
- logic_projects_advanced_20251205_195021.md
```

### Report Sample

```markdown
## Summary Statistics

- Total Projects: 39
- Total Tracks: 588
- Plugins Detected: 604
- Presets Found: 642
- Average Tempo: 99.74 BPM

## Plugin Usage

| Plugin      | Projects |
| ----------- | -------- |
| Sampler     | 11       |
| Q-Sampler   | 10       |
| Retro Synth | 9        |

## Session Players Characters

| Character                  | Usage |
| -------------------------- | ----- |
| Electric Bass - Modern R&B | 183   |
| Acoustic Piano - Strummed  | 120   |
```

---

## ⚙️ Requirements

- **Python:** 3.7+
- **OS:** macOS (tested on Sonoma 14.x)
- **Logic:** 10.x - 11.x
- **Dependencies:** None (stdlib only)

---

## 🎓 Learning Path

1. **First Use:** Run `scripts/logic_project_analyzer_enhanced.py` on your projects
2. **Explore Results:** Open generated markdown report
3. **Learn More:** Read `docs/README.md`
4. **Deep Dive:** Check `docs/RESEARCH_SUMMARY.md`
5. **Advanced:** Try binary analysis tools
6. **Expert:** Read `docs/BINARY_FORMAT_FINDINGS.md`

---

## 📞 Quick Help

**Don't know which script to use?**
→ Use `scripts/logic_project_analyzer_enhanced.py` (the main one)

**Need technical details?**
→ Read `docs/RESEARCH_SUMMARY.md`

**Want step-by-step guide?**
→ Read `docs/README_BINARY_ANALYSIS.md`

---

## 🏆 Best Practices

1. ✅ Always backup projects before analysis
2. ✅ Close Logic Pro before analyzing
3. ✅ Run from project directory
4. ✅ Check sample output first
5. ✅ Read README.md for first use
6. ✅ Keep projects in one folder for batch analysis

---

## 🔗 File Locations Cheat Sheet

```
ProjectData Location:
  Project.logicx/Alternatives/000/ProjectData

MetaData Location:
  Project.logicx/Alternatives/000/MetaData.plist

Project Info:
  Project.logicx/Resources/ProjectInformation.plist

Audio Files:
  Project.logicx/Media/
```

---

## ⏱️ Performance Reference

| Projects    | Size    | Time    | Memory |
| ----------- | ------- | ------- | ------ |
| 1 project   | 2-3 MB  | 1-2 sec | 100 MB |
| 10 projects | ~30 MB  | ~5 sec  | 150 MB |
| 39 projects | ~100 MB | ~10 sec | 250 MB |

---

## 🎨 Output Formats

| Format   | Extension | Use For                            |
| -------- | --------- | ---------------------------------- |
| Markdown | `.md`     | Reports (human-readable)           |
| JSON     | `.json`   | Data processing (machine-readable) |
| Text     | `.txt`    | Binary analysis (debugging)        |

---

**Last Updated:** January 2, 2026
**Version:** 2.0
**Quick Reference:** For detailed info, see docs/README.md
