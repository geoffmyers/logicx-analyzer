# Multi-Format Output Guide

## Overview

The **Logic Project Analyzer Enhanced** now generates reports in **four different formats** simultaneously:
1. **Markdown** (.md) - Human-readable detailed report
2. **JSON** (.json) - Machine-readable complete data
3. **CSV Summary** (.csv) - Spreadsheet-compatible overview
4. **CSV Detailed** (_detailed.csv) - Plugin and preset listings

---

## Output Formats

### 📄 1. Markdown Report

**Filename:** `logic_projects_advanced_YYYYMMDD_HHMMSS.md`

**Purpose:** Comprehensive human-readable report with formatted tables and sections.

**Best For:**
- Reading and reviewing project details
- Sharing with collaborators
- Documentation
- Version control (Git-friendly)

**Contains:**
- Summary statistics with tables
- Plugin usage table
- Session Players characters
- Key distribution
- Per-project detailed sections:
  - Musical attributes
  - Binary structure
  - Plugin lists
  - Session Players presets with parameters
  - Alchemy library references
  - Track names
  - Region names
  - Audio resources

**Example Structure:**
```markdown
# Advanced Logicx Analyzer Report

## Summary Statistics
- Total Projects: 39
- Plugins Detected: 604
- Presets Found: 642

## Plugin Usage
| Plugin | Projects |
|--------|----------|
| Sampler | 11 |

## Project Details
### 1. My Project
**Musical Attributes:**
- Tempo: 120.0 BPM
- Key: C minor
```

---

### 📊 2. JSON Report

**Filename:** `logic_projects_advanced_YYYYMMDD_HHMMSS.json`

**Purpose:** Complete structured data for programmatic access.

**Best For:**
- Data processing and analysis
- Integration with other tools
- Database imports
- Web applications
- API endpoints
- Python/JavaScript parsing

**Contains:**
- Metadata (generation time, location, version)
- Complete summary statistics
- Full project data including:
  - All musical attributes
  - All technical specs
  - Complete plugin lists
  - Full preset configurations with all parameters
  - Binary structure data
  - Track and region information
  - Audio resource counts

**Structure:**
```json
{
  "metadata": {
    "generated": "2025-12-05T20:40:21.616180",
    "location": "/path/to/projects",
    "analyzer_version": "2.0",
    "total_projects": 39
  },
  "summary_statistics": {
    "total_projects": 39,
    "total_tracks": 588,
    "total_plugins_found": 604,
    "plugin_usage": { ... },
    "preset_usage": { ... }
  },
  "projects": [
    {
      "name": "My Project",
      "path": "/path/to/My Project.logicx",
      "musical": { ... },
      "technical": { ... },
      "plugin_data": { ... },
      "binary_data": { ... }
    }
  ]
}
```

**Usage Examples:**

**Python:**
```python
import json

with open('logic_projects_advanced_20251205_204021.json') as f:
    data = json.load(f)

# Get all projects with BPM > 120
fast_projects = [p for p in data['projects']
                 if p['musical']['bpm'] > 120]

# List all unique plugins
all_plugins = set()
for project in data['projects']:
    all_plugins.update(project['plugin_data']['plugins'])
```

**JavaScript:**
```javascript
fetch('logic_projects_advanced_20251205_204021.json')
  .then(response => response.json())
  .then(data => {
    // Get average BPM
    console.log(data.summary_statistics.avg_bpm);

    // Find projects in C minor
    const cMinorProjects = data.projects.filter(
      p => p.musical.key === 'C' && p.musical.mode === 'minor'
    );
  });
```

---

### 📈 3. CSV Summary Report

**Filename:** `logic_projects_advanced_YYYYMMDD_HHMMSS.csv`

**Purpose:** Spreadsheet-compatible project overview with one row per project.

**Best For:**
- Excel/Google Sheets analysis
- Quick data visualization
- Pivot tables
- Charts and graphs
- Database imports
- Data science workflows

**Columns:**
| Column | Description |
|--------|-------------|
| Project Name | Project filename |
| Tempo (BPM) | Beats per minute |
| Key | Musical key (e.g., "C minor") |
| Time Signature | Time signature (e.g., "4/4") |
| Tracks | Number of tracks |
| Sample Rate | Audio sample rate (Hz) |
| Logic Version | Logic Pro version used |
| Track Names Found | Count of track names extracted |
| Regions Found | Count of audio regions |
| Plugins Count | Number of plugins detected |
| Presets Count | Number of Session Players presets |
| Total Chunks | Binary file chunks count |
| Audio Files | Count of audio files |
| Total Samples | Total sample files used |
| Has ARA Plugins | Boolean for ARA plugin usage |
| Top Plugin | Most-used plugin in project |
| Top Preset Character | Most-used Session Players character |

**Example Usage:**

**Excel:**
1. Open CSV in Excel
2. Create pivot table: Plugins Count by Project
3. Chart: BPM distribution
4. Filter: Projects with ARA plugins

**Python (Pandas):**
```python
import pandas as pd

df = pd.read_csv('logic_projects_advanced_20251205_204021.csv')

# Average BPM
print(df['Tempo (BPM)'].mean())

# Projects by key
print(df['Key'].value_counts())

# Top 10 projects by plugin count
top_projects = df.nlargest(10, 'Plugins Count')
```

---

### 📋 4. CSV Detailed Report

**Filename:** `logic_projects_advanced_YYYYMMDD_HHMMSS_detailed.csv`

**Purpose:** Row-per-item listing of plugins and presets across all projects.

**Best For:**
- Plugin inventory
- Preset cataloging
- Database imports
- Detailed analysis
- Filtering and searching
- Cross-project comparisons

**Columns:**
| Column | Description |
|--------|-------------|
| Project | Project name |
| Type | "Plugin" or "Preset" |
| Name | Plugin/preset name |
| Category | Plugin category or preset character |
| Parameters | Key parameters (for presets) |

**Example Rows:**
```csv
Project,Type,Name,Category,Parameters
My Project,Plugin,Alchemy,Plugin,
My Project,Preset,Sweet Memories,Acoustic Piano - Strummed,"intensity=71, dynamics=119, humanize=37"
My Project,Plugin,Sampler,Plugin,
```

**Usage Examples:**

**Find all Alchemy usage:**
```python
import pandas as pd

df = pd.read_csv('logic_projects_advanced_20251205_204021_detailed.csv')

# All projects using Alchemy
alchemy_projects = df[df['Name'].str.contains('Alchemy', na=False)]
print(alchemy_projects['Project'].unique())
```

**Count presets per character:**
```python
presets = df[df['Type'] == 'Preset']
print(presets['Category'].value_counts())
```

---

## File Sizes

Typical file sizes for 39 projects:

| Format | Size | Compression |
|--------|------|-------------|
| Markdown | ~69 KB | Human-readable |
| JSON | ~620 KB | Complete data |
| CSV Summary | ~6 KB | Compact overview |
| CSV Detailed | ~137 KB | Full inventory |

---

## Usage Patterns

### Pattern 1: Quick Overview
**Use:** CSV Summary
**Open in:** Excel, Google Sheets
**Purpose:** See all projects at a glance

### Pattern 2: Detailed Review
**Use:** Markdown
**Open in:** Text editor, VS Code, Browser
**Purpose:** Read comprehensive report

### Pattern 3: Data Analysis
**Use:** JSON
**Open in:** Python, JavaScript, jq
**Purpose:** Programmatic processing

### Pattern 4: Plugin Inventory
**Use:** CSV Detailed
**Open in:** Excel, Database
**Purpose:** Catalog all plugins/presets

---

## Integration Examples

### Example 1: Import to Database

**PostgreSQL:**
```sql
CREATE TABLE projects (
    project_name TEXT,
    tempo FLOAT,
    key TEXT,
    time_signature TEXT,
    tracks INTEGER,
    plugins_count INTEGER,
    presets_count INTEGER
);

COPY projects FROM 'logic_projects_advanced_20251205_204021.csv'
WITH (FORMAT CSV, HEADER TRUE);
```

### Example 2: Web Dashboard

**Python Flask:**
```python
from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route('/api/projects')
def get_projects():
    with open('logic_projects_advanced_20251205_204021.json') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/api/stats')
def get_stats():
    with open('logic_projects_advanced_20251205_204021.json') as f:
        data = json.load(f)
    return jsonify(data['summary_statistics'])
```

### Example 3: Data Visualization

**Python Matplotlib:**
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('logic_projects_advanced_20251205_204021.csv')

# BPM distribution
plt.figure(figsize=(10, 6))
plt.hist(df['Tempo (BPM)'], bins=20)
plt.xlabel('BPM')
plt.ylabel('Count')
plt.title('Project BPM Distribution')
plt.show()

# Plugins per project
top_10 = df.nlargest(10, 'Plugins Count')
plt.barh(top_10['Project Name'], top_10['Plugins Count'])
plt.xlabel('Plugin Count')
plt.title('Top 10 Projects by Plugin Usage')
plt.tight_layout()
plt.show()
```

### Example 4: Plugin Usage Report

**Python:**
```python
import pandas as pd

# Load detailed CSV
detailed = pd.read_csv('logic_projects_advanced_20251205_204021_detailed.csv')

# Count plugin usage across all projects
plugin_counts = detailed[detailed['Type'] == 'Plugin']['Name'].value_counts()

print("Top 10 Most Used Plugins:")
print(plugin_counts.head(10))

# Preset usage by character
presets = detailed[detailed['Type'] == 'Preset']
preset_chars = presets['Category'].value_counts()

print("\nSession Players Usage:")
print(preset_chars)
```

---

## Format Selection Guide

| Need | Format | Tool |
|------|--------|------|
| Read report | Markdown | Text editor |
| Share findings | Markdown | Email, GitHub |
| Spreadsheet analysis | CSV Summary | Excel |
| Plugin inventory | CSV Detailed | Database |
| Data processing | JSON | Python, JS |
| Web integration | JSON | API |
| Charts/graphs | CSV Summary | Excel, Python |
| Search presets | CSV Detailed | Grep, Database |
| Version control | Markdown, JSON | Git |
| Quick stats | CSV Summary | Spreadsheet |

---

## Output Location

All files are saved in the same directory where the analyzer is run:

```
/path/to/your/projects/
├── logic_projects_advanced_20251205_204021.md
├── logic_projects_advanced_20251205_204021.json
├── logic_projects_advanced_20251205_204021.csv
└── logic_projects_advanced_20251205_204021_detailed.csv
```

**Tip:** Run analyzer from a dedicated "Reports" folder to keep outputs organized.

---

## Command Line Output

When running the analyzer, you'll see:

```
Generating reports in multiple formats...
  - Markdown report...
  - JSON report...
  - CSV summary report...
  - CSV detailed report...

Analysis Complete!

Reports Generated:
  📄 Markdown: logic_projects_advanced_20251205_204021.md
  📊 JSON:     logic_projects_advanced_20251205_204021.json
  📈 CSV:      logic_projects_advanced_20251205_204021.csv
  📋 CSV Det:  logic_projects_advanced_20251205_204021_detailed.csv
```

---

## Best Practices

### 1. Choose Right Format
- **Reading:** Markdown
- **Analyzing:** CSV or JSON
- **Sharing:** Markdown or CSV
- **Archiving:** All formats

### 2. File Management
- Keep all 4 files together (same timestamp)
- Move to dedicated Reports folder
- Version control Markdown + JSON
- Gitignore large CSVs (optional)

### 3. Automation
- Use JSON for automated workflows
- Parse CSV for spreadsheet updates
- Generate charts from CSV
- Archive Markdown for documentation

### 4. Integration
- Import CSV to databases
- Use JSON with web apps
- Share Markdown on wikis
- Process CSV with pandas

---

## Troubleshooting

### Large File Sizes

**JSON files are large:**
- Expected for comprehensive data
- Compress with gzip: `gzip *.json`
- Filter data if needed

**CSV detailed is large:**
- Normal with many plugins/presets
- Import to database for querying
- Use Excel filtering

### Character Encoding

**Non-ASCII characters:**
- All formats use UTF-8
- Open CSV with UTF-8 encoding in Excel
- JSON preserves Unicode perfectly

### File Locations

**Can't find files:**
- Check current working directory
- Look for timestamp in filename
- Use `find` command:
  ```bash
  find . -name "logic_projects_advanced_*.md"
  ```

---

## Examples by Use Case

### Use Case 1: Project Portfolio Review
**Format:** Markdown
**Workflow:**
1. Run analyzer
2. Open `.md` file in VS Code
3. Review summary statistics
4. Check plugin usage table
5. Review individual projects

### Use Case 2: Plugin Usage Analysis
**Format:** CSV Detailed
**Workflow:**
1. Open `_detailed.csv` in Excel
2. Filter by Type = "Plugin"
3. Create pivot table: Plugin Name × Count
4. Generate bar chart
5. Identify most-used plugins

### Use Case 3: Database Integration
**Format:** CSV Summary
**Workflow:**
1. Import `.csv` to PostgreSQL
2. Create indexes on key columns
3. Query for insights:
   ```sql
   SELECT key, AVG(tempo) FROM projects GROUP BY key;
   ```

### Use Case 4: Web Dashboard
**Format:** JSON
**Workflow:**
1. Load `.json` in web app
2. Display summary stats
3. Create interactive charts
4. Enable project filtering
5. Show preset parameters

---

## Format Specifications

### JSON Schema

```json
{
  "metadata": {
    "generated": "ISO 8601 timestamp",
    "location": "absolute path",
    "analyzer_version": "version string",
    "total_projects": "integer"
  },
  "summary_statistics": {
    "total_projects": "int",
    "total_tracks": "int",
    "avg_bpm": "float",
    "key_distribution": "object",
    "plugin_usage": "object",
    "preset_usage": "object"
  },
  "projects": [
    {
      "name": "string",
      "path": "string",
      "musical": "object",
      "technical": "object",
      "plugin_data": "object",
      "binary_data": "object"
    }
  ]
}
```

### CSV Column Data Types

**Summary CSV:**
- Project Name: String
- Tempo (BPM): Float
- Tracks: Integer
- Plugins Count: Integer
- Has ARA Plugins: Boolean

**Detailed CSV:**
- Project: String
- Type: Enum ("Plugin", "Preset")
- Name: String
- Category: String
- Parameters: String (comma-separated)

---

## Version History

### Version 2.1 (December 2025)
- ✅ Added JSON export
- ✅ Added CSV summary export
- ✅ Added CSV detailed export
- ✅ Simultaneous multi-format generation

### Version 2.0 (December 2025)
- Markdown reports with binary analysis

### Version 1.0 (November 2025)
- Basic Markdown reports

---

**Last Updated:** December 5, 2025
**Feature Version:** 2.1
**Documentation:** Multi-Format Output Guide
