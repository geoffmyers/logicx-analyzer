#!/usr/bin/env python3
"""
Early experimental script for Logic Pro ProjectData string extraction.
DEPRECATED: Use logic_project_analyzer_enhanced.py instead.
"""

import struct
import re
import json
import os

def extract_strings(data, min_length=4):
    """
    Extracts contiguous ASCII and UTF-8 strings from binary data.
    Filters out common binary noise.
    """
    results = []
    # Regex to find sequences of printable characters
    # We include common path characters like / and _ and space
    # 4 chars is a safe minimum to avoid random 3-byte noise
    pattern = re.compile(b'[ -~]{4,}')
    
    for match in pattern.finditer(data):
        try:
            s_str = match.group().decode('utf-8')
            # Heuristic filter: reject strings that look like random noise
            # (e.g., mostly symbols, or pure numbers)
            if len(s_str.strip()) >= min_length and not re.match(r'^[0-9]+$', s_str):
                results.append(s_str)
        except:
            continue
    return results

def analyze_logic_project(file_path, output_json):
    print(f"[*] Reading binary file: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[!] Error: File '{file_path}' not found.")
        return

    # 1. Verify Magic Header
    header = content[:4]
    magic_hex = header.hex()
    
    # Logic LSO Magic: 23 47 C0 AB
    if magic_hex != "2347c0ab":
        print(f"[!] Warning: File signature {magic_hex} does not match known Logic LSO header (2347c0ab).")
        print("    Proceeding anyway with string analysis...")
    else:
        print(f"[*] Verified Logic Pro LSO binary format.")

    # 2. Extract All Strings
    print("[*] Extracting string data...")
    raw_strings = extract_strings(content)
    print(f"    - Found {len(raw_strings)} candidate strings.")

    # 3. Classify Data
    # We use sets to avoid duplicates
    data_map = {
        "metadata": {
            "file_size_bytes": len(content),
            "magic_signature": magic_hex
        },
        "plugins": set(),
        "presets": set(),
        "tracks_and_regions": set(),
        "file_paths": set(),
        "potential_names": set()
    }

    # Knowledge base for classification
    known_plugins = [
        "Alchemy", "Retro Synth", "Sampler", "Q-Sampler", "Quick Sampler",
        "Space Designer", "Channel EQ", "Compressor", "ChromaVerb",
        "Vintage B3", "Vintage Clav", "Vintage Electric Piano", "Sculpture",
        "Phat FX", "Step FX", "Delay Designer", "Logic", "Audio"
    ]
    
    file_extensions = ['.exs', '.pst', '.cst', '.aif', '.wav', '.caf', '.mid', '.aaz', '.acp']

    print("[*] Classifying data...")
    
    for s in raw_strings:
        s_clean = s.strip()
        
        # A. File Paths
        if '/' in s_clean and (s_clean.startswith('/') or s_clean.startswith('Users/') or s_clean.startswith('Volumes/')):
            data_map["file_paths"].add(s_clean)
            continue

        # B. Files with Extensions (Presets/Samples)
        if any(ext in s_clean.lower() for ext in file_extensions):
            data_map["presets"].add(s_clean)
            continue

        # C. Known Plugins
        # Check if the string matches a known plugin exactly or contains it
        is_plugin = False
        for kp in known_plugins:
            if kp in s_clean:
                data_map["plugins"].add(s_clean)
                is_plugin = True
                break
        if is_plugin:
            continue

        # D. Tracks / Regions / Custom Names
        # This is heuristic. Logic region names often look like "Chorus", "Verse", "Audio 1"
        # We filter out short technical strings
        if len(s_clean) > 3 and len(s_clean) < 50:
            # Heuristic: starts with capital letter, contains letters
            if s_clean[0].isupper() and any(c.isalpha() for c in s_clean):
                data_map["tracks_and_regions"].add(s_clean)
            else:
                data_map["potential_names"].add(s_clean)

    # 4. Convert sets to lists for JSON serialization
    final_output = {
        "metadata": data_map["metadata"],
        "plugins_detected": sorted(list(data_map["plugins"])),
        "presets_and_assets": sorted(list(data_map["presets"])),
        "tracks_regions_candidates": sorted(list(data_map["tracks_and_regions"])),
        "file_paths": sorted(list(data_map["file_paths"])),
        # "raw_strings_dump": raw_strings # Uncomment if you want the massive full dump
    }

    # 5. Save to JSON
    with open(output_json, 'w') as f:
        json.dump(final_output, f, indent=4)
    
    print(f"[*] Analysis complete. Saved to: {output_json}")
    print(f"    - Plugins found: {len(final_output['plugins_detected'])}")
    print(f"    - Presets/Assets found: {len(final_output['presets_and_assets'])}")
    print(f"    - Track/Region names: {len(final_output['tracks_regions_candidates'])}")

# --- Execution ---
if __name__ == "__main__":
    # Create a dummy file for demonstration if it doesn't exist
    # (In your environment, you would just point this to 'ProjectData')
    target_file = 'ProjectData'
    output_file = 'project_data_decoded.json'
    
    analyze_logic_project(target_file, output_file)