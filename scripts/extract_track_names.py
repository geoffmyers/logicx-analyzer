#!/usr/bin/env python3
"""
Extract Track Names from Logic Pro ProjectData Files
Attempts to parse binary ProjectData files to extract track names and region names.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple


def extract_strings_from_binary(file_path: Path, min_length: int = 4) -> List[str]:
    """
    Extract ASCII strings from a binary file.

    Args:
        file_path: Path to binary file
        min_length: Minimum string length to extract

    Returns:
        List of extracted strings
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        # Pattern to match printable ASCII strings
        pattern = b'[ -~]{' + str(min_length).encode() + b',}'
        strings_found = re.findall(pattern, data)

        # Decode to UTF-8
        return [s.decode('utf-8', errors='ignore') for s in strings_found]

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []


def extract_track_info(project_path: Path) -> Dict:
    """
    Extract track and region information from ProjectData file.

    Args:
        project_path: Path to .logicx project

    Returns:
        Dictionary with track and region information
    """
    project_data_path = project_path / "Alternatives" / "000" / "ProjectData"

    if not project_data_path.exists():
        return {
            'project_name': project_path.stem,
            'tracks': [],
            'regions': [],
            'audio_files': [],
            'error': 'ProjectData not found'
        }

    # Extract all strings
    all_strings = extract_strings_from_binary(project_data_path)

    # Look for track markers and extract track names
    tracks = []
    regions = []
    audio_files = []

    # Common patterns in Logic Pro ProjectData:
    # "karT" (reversed "Trak") appears before track names
    # "gRuA" (reversed "AuRg") appears before audio region names
    # "Audio 1", "Audio 2", etc. are common track names

    for i, string in enumerate(all_strings):
        # Look for track indicators
        if string == "karT" and i + 1 < len(all_strings):
            next_string = all_strings[i + 1]
            # Filter out known non-track strings
            if (next_string not in ['qSvE', 'qeSM', 'tSnI', 'tSxT'] and
                len(next_string) > 1 and
                not next_string.startswith('reserved')):
                if next_string not in tracks:
                    tracks.append(next_string)

        # Look for audio regions
        if string == "gRuA" and i + 1 < len(all_strings):
            next_string = all_strings[i + 1]
            if len(next_string) > 2 and next_string not in regions:
                regions.append(next_string)

        # Look for Audio track names pattern
        if re.match(r'^\s*Audio\s+\d+$', string):
            if string.strip() not in tracks:
                tracks.append(string.strip())

    # Also extract common audio file references
    for string in all_strings:
        if ('Audio Files' in string or
            '/Library/Audio' in string or
            '.caf' in string.lower() or
            '.wav' in string.lower() or
            '.aif' in string.lower()):
            if string not in audio_files and len(string) < 200:
                audio_files.append(string)

    return {
        'project_name': project_path.stem,
        'tracks': tracks,
        'regions': regions,
        'audio_files_found': len(audio_files),
        'error': None
    }


def analyze_all_projects(base_dir: Path) -> List[Dict]:
    """
    Analyze all Logic Pro projects in directory.

    Args:
        base_dir: Directory containing .logicx projects

    Returns:
        List of project analysis results
    """
    projects = []

    # Find all .logicx projects
    for project_path in sorted(base_dir.glob("*.logicx")):
        if project_path.is_dir():
            print(f"Processing: {project_path.name}...")
            info = extract_track_info(project_path)
            projects.append(info)

    return projects


def generate_report(projects: List[Dict], output_path: Path):
    """
    Generate a Markdown report of extracted track information.

    Args:
        projects: List of project analysis results
        output_path: Output file path
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Logic Pro Track Names Report\n\n")
        f.write("**Note:** This report attempts to extract track and region names from binary ProjectData files.\n")
        f.write("The extraction is heuristic-based and may not be 100% accurate.\n\n")

        f.write(f"**Total Projects Analyzed:** {len(projects)}\n\n")

        # Summary statistics
        total_tracks = sum(len(p['tracks']) for p in projects)
        total_regions = sum(len(p['regions']) for p in projects)

        f.write(f"**Total Tracks Found:** {total_tracks}\n")
        f.write(f"**Total Regions Found:** {total_regions}\n\n")

        f.write("---\n\n")

        # Project details
        for idx, project in enumerate(projects, 1):
            f.write(f"## {idx}. {project['project_name']}\n\n")

            if project['error']:
                f.write(f"**Error:** {project['error']}\n\n")
                continue

            # Tracks
            if project['tracks']:
                f.write(f"**Tracks ({len(project['tracks'])}):**\n")
                for track in project['tracks']:
                    f.write(f"- {track}\n")
                f.write("\n")
            else:
                f.write("**Tracks:** None found\n\n")

            # Regions
            if project['regions']:
                f.write(f"**Audio Regions ({len(project['regions'])}):**\n")
                for i, region in enumerate(project['regions'][:20], 1):  # Limit to first 20
                    f.write(f"- {region}\n")
                if len(project['regions']) > 20:
                    f.write(f"- *(... and {len(project['regions']) - 20} more)*\n")
                f.write("\n")

            f.write("---\n\n")


def main():
    """Main execution function."""
    print("\n" + "=" * 60)
    print("Logic Pro Track Name Extractor")
    print("=" * 60 + "\n")

    base_dir = Path.cwd()
    print(f"Analyzing projects in: {base_dir}\n")

    # Analyze all projects
    projects = analyze_all_projects(base_dir)

    if not projects:
        print("No Logic Pro projects found.")
        return

    print(f"\nAnalyzed {len(projects)} projects")

    # Generate report
    output_path = base_dir / "track_names_report.md"
    print(f"\nGenerating report: {output_path.name}")
    generate_report(projects, output_path)

    # Print summary
    print("\n" + "=" * 60)
    print("Extraction Complete!")
    print("=" * 60)

    total_tracks = sum(len(p['tracks']) for p in projects)
    total_regions = sum(len(p['regions']) for p in projects)

    print(f"\nTotal Tracks Found: {total_tracks}")
    print(f"Total Regions Found: {total_regions}")
    print(f"\nReport saved to: {output_path.name}\n")


if __name__ == "__main__":
    main()
