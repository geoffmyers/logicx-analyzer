#!/usr/bin/env python3
"""
Logic Pro Project Analyzer
Analyzes Logic Pro projects (*.logicx) and generates detailed reports
about their musical attributes, technical specifications, and audio resources.
"""

import csv
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
import statistics
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logic_project_common import (  # noqa: E402
    extract_metadata_plist as _extract_metadata_plist,
    extract_project_info,
    extract_common_metadata_fields,
    format_key_signature,
    format_time_signature,
    scan_directory,
)


def extract_metadata_plist(project_path: Path) -> Optional[Dict]:
    """
    Extract metadata from MetaData.plist file. Prints a message for read
    errors other than a missing or malformed plist (this script's original
    behaviour; see `logic_project_common.extract_metadata_plist`).

    Args:
        project_path: Path to .logicx project

    Returns:
        Dictionary of metadata or None if error
    """
    return _extract_metadata_plist(project_path, verbose_errors=True)


def extract_filenames(file_paths: List[str]) -> List[str]:
    """
    Extract just filenames from full file paths.

    Args:
        file_paths: List of full file paths

    Returns:
        List of filenames only
    """
    filenames = []
    for path in file_paths:
        try:
            filenames.append(Path(path).name)
        except Exception:
            filenames.append(path)

    return filenames


def parse_project_data(metadata: Dict, proj_info: Optional[Dict], project_path: Path) -> Dict:
    """
    Parse project data from metadata and project info plists.

    Args:
        metadata: MetaData.plist dictionary
        proj_info: ProjectInformation.plist dictionary (optional)
        project_path: Path to project

    Returns:
        Structured project data dictionary
    """
    f = extract_common_metadata_fields(metadata)

    # Extract project info
    logic_version = "Unknown"
    if proj_info:
        logic_version = proj_info.get('LastSavedFrom', 'Unknown')

    return {
        'name': project_path.stem,
        'path': project_path,
        'musical': {
            'bpm': f['bpm'],
            'key': f['key'],
            'mode': f['mode'],
            'time_signature': format_time_signature(f['time_sig_num'], f['time_sig_denom']),
            'signature_key': f['signature_key']
        },
        'technical': {
            'tracks': f['tracks'],
            'sample_rate': f['sample_rate'],
            'frame_rate_index': f['frame_rate_index'],
            'surround_format_index': f['surround_format_index'],
            'surround_mode_index': f['surround_mode_index'],
            'version': f['version'],
            'logic_version': logic_version,
            'has_ara_plugins': f['has_ara_plugins'],
            'has_grid': f['has_grid'],
            'is_timecode_based': f['is_timecode_based']
        },
        'audio_counts': {
            'audio_files': len(f['audio_files']),
            'sampler_instruments': len(f['sampler_instruments']),
            'quicksampler_files': len(f['quicksampler_files']),
            'impulse_responses': len(f['impulse_responses']),
            'alchemy_files': len(f['alchemy_files']),
            'ultrabeat_files': len(f['ultrabeat_files']),
            'playback_files': len(f['playback_files']),
            'unused_audio_files': len(f['unused_audio_files']),
            'total_samples': f['total_samples']
        },
        'file_lists': {
            'audio_files': f['audio_files'],
            'sampler_instruments': f['sampler_instruments'],
            'quicksampler_files': f['quicksampler_files'],
            'impulse_responses': f['impulse_responses'],
            'alchemy_files': f['alchemy_files'],
            'ultrabeat_files': f['ultrabeat_files'],
            'playback_files': f['playback_files'],
            'unused_audio_files': f['unused_audio_files']
        },
        'errors': f['errors']
    }


def calculate_statistics(projects: List[Dict]) -> Dict:
    """
    Calculate summary statistics across all projects.

    Args:
        projects: List of project data dictionaries

    Returns:
        Dictionary of statistics
    """
    if not projects:
        return {
            'total_projects': 0,
            'total_tracks': 0,
            'avg_tracks': 0,
            'avg_bpm': 0,
            'bpm_range': (0, 0),
            'key_distribution': {},
            'mode_distribution': {},
            'time_signatures': {},
            'sample_rates': {},
            'total_audio_files': 0,
            'total_samples_used': 0,
            'projects_with_alchemy': 0,
            'projects_with_ara': 0,
            'projects_with_grid': 0,
            'errors_encountered': 0
        }

    # Collect data
    tracks_list = [p['technical']['tracks'] for p in projects]
    bpms = [p['musical']['bpm'] for p in projects if p['musical']['bpm'] > 0]

    keys = []
    for p in projects:
        key = format_key_signature(p['musical']['key'], p['musical']['mode'])
        if key != "Unknown":
            keys.append(key)

    modes = [p['musical']['mode'] for p in projects if p['musical']['mode'] != 'Unknown']
    time_sigs = [p['musical']['time_signature'] for p in projects if p['musical']['time_signature'] != 'Unknown']
    sample_rates = [p['technical']['sample_rate'] for p in projects if p['technical']['sample_rate'] > 0]

    # Calculate statistics
    total_tracks = sum(tracks_list)
    total_audio = sum(p['audio_counts']['audio_files'] for p in projects)
    total_samples = sum(p['audio_counts']['total_samples'] for p in projects)

    projects_with_alchemy = sum(1 for p in projects if p['audio_counts']['alchemy_files'] > 0)
    projects_with_ara = sum(1 for p in projects if p['technical']['has_ara_plugins'])
    projects_with_grid = sum(1 for p in projects if p['technical']['has_grid'])

    errors = sum(len(p['errors']) for p in projects)

    return {
        'total_projects': len(projects),
        'total_tracks': total_tracks,
        'avg_tracks': round(statistics.mean(tracks_list), 2) if tracks_list else 0,
        'avg_bpm': round(statistics.mean(bpms), 2) if bpms else 0,
        'bpm_range': (min(bpms), max(bpms)) if bpms else (0, 0),
        'key_distribution': dict(Counter(keys)),
        'mode_distribution': dict(Counter(modes)),
        'time_signatures': dict(Counter(time_sigs)),
        'sample_rates': dict(Counter(sample_rates)),
        'total_audio_files': total_audio,
        'total_samples_used': total_samples,
        'projects_with_alchemy': projects_with_alchemy,
        'projects_with_ara': projects_with_ara,
        'projects_with_grid': projects_with_grid,
        'errors_encountered': errors
    }


def generate_markdown_report(projects: List[Dict], stats: Dict, output_path: Path):
    """
    Generate comprehensive Markdown report.

    Args:
        projects: List of project data
        stats: Statistics dictionary
        output_path: Output file path
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("# Logicx Analyzer Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Location:** {Path.cwd()}\n\n")

        # Summary Statistics
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Projects:** {stats['total_projects']}\n")
        f.write(f"- **Total Tracks:** {stats['total_tracks']}\n")
        f.write(f"- **Average Tracks per Project:** {stats['avg_tracks']}\n")
        f.write(f"- **Average Tempo:** {stats['avg_bpm']} BPM\n")

        if stats['bpm_range'][0] > 0:
            f.write(f"- **Tempo Range:** {stats['bpm_range'][0]} - {stats['bpm_range'][1]} BPM\n")

        f.write(f"- **Total Audio Files Used:** {stats['total_audio_files']}\n")
        f.write(f"- **Total Sample Files:** {stats['total_samples_used']}\n")
        f.write(f"- **Projects with Alchemy:** {stats['projects_with_alchemy']}\n")
        f.write(f"- **Projects with ARA Plugins:** {stats['projects_with_ara']}\n")
        f.write(f"- **Projects with Grid:** {stats['projects_with_grid']}\n")

        if stats['errors_encountered'] > 0:
            f.write(f"- **Errors Encountered:** {stats['errors_encountered']}\n")

        # Key Distribution
        if stats['key_distribution']:
            f.write("\n## Key Distribution\n\n")
            f.write("| Key | Count |\n")
            f.write("|-----|-------|\n")
            for key, count in sorted(stats['key_distribution'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {key} | {count} |\n")

        # Mode Distribution
        if stats['mode_distribution']:
            f.write("\n## Mode Distribution\n\n")
            f.write("| Mode | Count |\n")
            f.write("|------|-------|\n")
            for mode, count in sorted(stats['mode_distribution'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {mode} | {count} |\n")

        # Time Signature Distribution
        if stats['time_signatures']:
            f.write("\n## Time Signature Distribution\n\n")
            f.write("| Time Signature | Count |\n")
            f.write("|----------------|-------|\n")
            for sig, count in sorted(stats['time_signatures'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {sig} | {count} |\n")

        # Sample Rate Distribution
        if stats['sample_rates']:
            f.write("\n## Sample Rate Distribution\n\n")
            f.write("| Sample Rate (Hz) | Count |\n")
            f.write("|------------------|-------|\n")
            for rate, count in sorted(stats['sample_rates'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"| {rate} | {count} |\n")

        # Project Details
        f.write("\n## Project Details\n\n")

        for idx, project in enumerate(projects, 1):
            f.write(f"### {idx}. {project['name']}\n\n")

            # Musical Attributes
            f.write("**Musical Attributes:**\n")
            f.write(f"- **Tempo:** {project['musical']['bpm']} BPM\n")
            f.write(f"- **Key:** {format_key_signature(project['musical']['key'], project['musical']['mode'])}\n")
            f.write(f"- **Time Signature:** {project['musical']['time_signature']}\n")
            f.write(f"- **Tracks:** {project['technical']['tracks']}\n")
            f.write("\n")

            # Technical Specs
            f.write("**Technical Specifications:**\n")
            f.write(f"- **Sample Rate:** {project['technical']['sample_rate']} Hz\n")
            f.write(f"- **Logic Version:** {project['technical']['logic_version']}\n")
            f.write(f"- **Frame Rate Index:** {project['technical']['frame_rate_index']}\n")
            f.write(f"- **Has ARA Plugins:** {'Yes' if project['technical']['has_ara_plugins'] else 'No'}\n")
            f.write(f"- **Has Grid:** {'Yes' if project['technical']['has_grid'] else 'No'}\n")
            f.write(f"- **TimeCode Based:** {'Yes' if project['technical']['is_timecode_based'] else 'No'}\n")
            f.write("\n")

            # Audio Resources
            f.write("**Audio Resources:**\n")
            f.write(f"- **Audio Files:** {project['audio_counts']['audio_files']}\n")
            f.write(f"- **Sampler Instruments:** {project['audio_counts']['sampler_instruments']}\n")
            f.write(f"- **Quick Sampler Files:** {project['audio_counts']['quicksampler_files']}\n")
            f.write(f"- **Impulse Responses:** {project['audio_counts']['impulse_responses']}\n")
            f.write(f"- **Alchemy Files:** {project['audio_counts']['alchemy_files']}\n")
            f.write(f"- **Ultrabeat Files:** {project['audio_counts']['ultrabeat_files']}\n")
            f.write(f"- **Playback Files:** {project['audio_counts']['playback_files']}\n")
            f.write(f"- **Unused Audio Files:** {project['audio_counts']['unused_audio_files']}\n")
            f.write(f"- **Total Samples:** {project['audio_counts']['total_samples']}\n")
            f.write("\n")

            # Sample Files (if any)
            has_samples = any([
                project['file_lists']['audio_files'],
                project['file_lists']['sampler_instruments'],
                project['file_lists']['quicksampler_files'],
                project['file_lists']['impulse_responses'],
                project['file_lists']['alchemy_files'],
                project['file_lists']['ultrabeat_files']
            ])

            if has_samples:
                f.write("**Sample Files:**\n\n")

                if project['file_lists']['audio_files']:
                    f.write("*Audio Files:*\n")
                    for file_path in project['file_lists']['audio_files']:
                        f.write(f"- {file_path}\n")
                    f.write("\n")

                if project['file_lists']['sampler_instruments']:
                    f.write("*Sampler Instruments:*\n")
                    for file_path in project['file_lists']['sampler_instruments']:
                        f.write(f"- {file_path}\n")
                    f.write("\n")

                if project['file_lists']['quicksampler_files']:
                    f.write("*Quick Sampler Files:*\n")
                    for file_path in project['file_lists']['quicksampler_files']:
                        f.write(f"- {file_path}\n")
                    f.write("\n")

                if project['file_lists']['impulse_responses']:
                    f.write("*Impulse Responses:*\n")
                    for file_path in project['file_lists']['impulse_responses']:
                        f.write(f"- {file_path}\n")
                    f.write("\n")

                if project['file_lists']['alchemy_files']:
                    f.write("*Alchemy Files:*\n")
                    for file_path in project['file_lists']['alchemy_files']:
                        f.write(f"- {file_path}\n")
                    f.write("\n")

                if project['file_lists']['ultrabeat_files']:
                    f.write("*Ultrabeat Files:*\n")
                    for file_path in project['file_lists']['ultrabeat_files']:
                        f.write(f"- {file_path}\n")
                    f.write("\n")

            # Errors (if any)
            if project['errors']:
                f.write("**Errors:**\n")
                for error in project['errors']:
                    f.write(f"- {error}\n")
                f.write("\n")

            f.write("---\n\n")


def generate_csv_report(projects: List[Dict], output_path: Path):
    """
    Generate CSV report with project data.

    Args:
        projects: List of project data
        output_path: Output file path
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Project Name', 'Tempo (BPM)', 'Key', 'Mode', 'Time Signature',
            'Tracks', 'Sample Rate', 'Logic Version', 'Frame Rate Index',
            'Audio Files', 'Sampler Instruments', 'Quick Sampler',
            'Impulse Responses', 'Alchemy', 'Ultrabeat', 'Playback Files',
            'Unused Audio', 'Total Samples', 'Has ARA', 'Has Grid',
            'TimeCode Based', 'Errors'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for project in projects:
            row = {
                'Project Name': project['name'],
                'Tempo (BPM)': project['musical']['bpm'],
                'Key': project['musical']['key'],
                'Mode': project['musical']['mode'],
                'Time Signature': project['musical']['time_signature'],
                'Tracks': project['technical']['tracks'],
                'Sample Rate': project['technical']['sample_rate'],
                'Logic Version': project['technical']['logic_version'],
                'Frame Rate Index': project['technical']['frame_rate_index'],
                'Audio Files': project['audio_counts']['audio_files'],
                'Sampler Instruments': project['audio_counts']['sampler_instruments'],
                'Quick Sampler': project['audio_counts']['quicksampler_files'],
                'Impulse Responses': project['audio_counts']['impulse_responses'],
                'Alchemy': project['audio_counts']['alchemy_files'],
                'Ultrabeat': project['audio_counts']['ultrabeat_files'],
                'Playback Files': project['audio_counts']['playback_files'],
                'Unused Audio': project['audio_counts']['unused_audio_files'],
                'Total Samples': project['audio_counts']['total_samples'],
                'Has ARA': 'Yes' if project['technical']['has_ara_plugins'] else 'No',
                'Has Grid': 'Yes' if project['technical']['has_grid'] else 'No',
                'TimeCode Based': 'Yes' if project['technical']['is_timecode_based'] else 'No',
                'Errors': '; '.join(project['errors']) if project['errors'] else ''
            }

            writer.writerow(row)


def main():
    """Main execution function."""
    print("\n" + "=" * 60)
    print("Logic Pro Project Analyzer")
    print("=" * 60 + "\n")

    # Scan for projects
    base_dir = Path.cwd()
    print(f"Scanning directory: {base_dir}\n")

    project_paths = scan_directory(base_dir)

    if not project_paths:
        print("No Logic Pro projects found in current directory.")
        return

    print(f"Found {len(project_paths)} Logic Pro project(s)\n")

    # Process projects
    print("Processing projects:")
    projects = []

    for idx, project_path in enumerate(project_paths, 1):
        print(f"[{idx}/{len(project_paths)}] {project_path.name}...", end=' ')

        metadata = extract_metadata_plist(project_path)

        if metadata is None:
            print("✗ (MetaData.plist not found or corrupt)")
            continue

        proj_info = extract_project_info(project_path)
        project_data = parse_project_data(metadata, proj_info, project_path)
        projects.append(project_data)

        print("✓")

    if not projects:
        print("\nNo valid projects found to analyze.")
        return

    print(f"\nSuccessfully processed {len(projects)} project(s)")

    # Calculate statistics
    print("\nCalculating statistics...")
    stats = calculate_statistics(projects)

    # Generate reports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    markdown_output = base_dir / f"logic_projects_report_{timestamp}.md"
    csv_output = base_dir / f"logic_projects_report_{timestamp}.csv"

    print("Generating Markdown report...")
    generate_markdown_report(projects, stats, markdown_output)

    print("Generating CSV report...")
    generate_csv_report(projects, csv_output)

    # Summary
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print(f"\nTotal Projects Analyzed: {len(projects)}")
    print(f"Total Tracks: {stats['total_tracks']}")
    print(f"Average Tempo: {stats['avg_bpm']} BPM")
    print(f"\nReports Generated:")
    print(f"- Markdown: {markdown_output.name}")
    print(f"- CSV: {csv_output.name}")
    print()


if __name__ == "__main__":
    main()
