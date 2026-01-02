import struct
import json
import re

def read_variable_length(data, offset):
    """Logic uses a variable length int format in some places."""
    value = 0
    while True:
        byte = data[offset]
        value = (value << 7) | (byte & 0x7F)
        offset += 1
        if not (byte & 0x80):
            break
    return value, offset

def parse_ticks(ticks):
    """Converts Logic ticks (960 PPQ) to Bars.Beats.Division.Ticks"""
    # Logic defaults to 960 ticks per beat (quarter note)
    # 4/4 Time Signature assumed for calculation (can be adjusted)
    ticks_per_beat = 960
    beats_per_bar = 4
    ticks_per_bar = ticks_per_beat * beats_per_bar
    
    bar = (ticks // ticks_per_bar) + 1
    remaining = ticks % ticks_per_bar
    beat = (remaining // ticks_per_beat) + 1
    remaining = remaining % ticks_per_beat
    division = (remaining // 240) + 1
    tick = remaining % 240
    
    return f"{bar}.{beat}.{division}.{tick}", ticks

def analyze_logic_binary(file_path):
    print(f"[*] Analyzing binary: {file_path}")
    
    with open(file_path, 'rb') as f:
        content = f.read()

    # Verify Magic (Logic LSO)
    if content[:4].hex() != "2347c0ab":
        print("[!] Warning: Magic bytes do not match standard Logic LSO.")

    # Data Containers
    project_info = {
        "tempo": "Unknown",
        "time_signature": "4/4 (Assumed)",
        "markers": [],
        "chords": [],
        "duration_ticks": 0,
        "duration_bars": "0.0.0.0"
    }

    offset = 24 # Skip file header
    
    while offset < len(content):
        if offset + 36 > len(content): break
        
        # Read Chunk Header
        chunk_header = content[offset:offset+36]
        desc = chunk_header[0:4][::-1].decode('ascii', errors='ignore')
        data_len = struct.unpack('<Q', chunk_header[28:36])[0]
        chunk_data = content[offset+36 : offset+36+data_len]
        
        # --- PARSE 'Song' CHUNK (Global Globals) ---
        if desc == "Song":
            # Heuristic: Tempo often lives around offset 0x30 or 0x34 as a large int
            # or standard 120.0000 bpm might be encoded.
            # Logic tempo is often fixed point or integer * 10000
            pass

        # --- PARSE 'EvSq' CHUNK (Events: Markers, Tempo, Chords) ---
        elif desc == "EvSq":
            # We look for the Marker Signature described in documentation
            # Signature: 12 00 00 00 [4 bytes ticks]
            
            # Scan the chunk for event headers
            idx = 0
            while idx < len(chunk_data) - 16:
                # MARKER SIGNATURE CHECK
                # 0x12 (18) is often the event type for Markers in Logic's internal CMap
                if chunk_data[idx] == 0x12 and chunk_data[idx+1:idx+4] == b'\x00\x00\x00':
                    
                    # Found a potential marker!
                    # Next 4 bytes are Ticks (Position)
                    tick_bytes = chunk_data[idx+4:idx+8]
                    ticks = struct.unpack('<I', tick_bytes)[0]
                    
                    # Update global song length if this is the latest event
                    if ticks > project_info["duration_ticks"] and ticks < 10000000: # Sanity check
                        project_info["duration_ticks"] = ticks
                    
                    # Try to find the Text Link (m3 ID)
                    # The doc says it's 8 bytes after ticks?
                    # Let's verify with the string extraction we did earlier
                    
                    position_str, raw_ticks = parse_ticks(ticks)
                    
                    # Store finding
                    project_info["markers"].append({
                        "type": "Marker/Event",
                        "position": position_str,
                        "raw_ticks": raw_ticks,
                        "offset_in_chunk": idx
                    })
                    
                    idx += 48 # Skip ahead (Marker structure is ~48 bytes)
                else:
                    idx += 4 # Align search
        
        # --- PARSE 'TxSq' CHUNK (Text for Markers) ---
        elif desc == "TxSq":
            # This contains the actual text for the markers found in EvSq
            # We assume sequential ordering for this basic script
            strings = re.findall(b'[a-zA-Z0-9\ \-\_]{3,}', chunk_data)
            clean_strings = [s.decode('utf-8') for s in strings]
            if clean_strings:
                # Append to the last found marker if possible, or store generally
                pass

        offset += 36 + data_len

    # Finalize Calculations
    project_info["duration_bars"], _ = parse_ticks(project_info["duration_ticks"])
    
    # Sort markers by position
    project_info["markers"] = sorted(project_info["markers"], key=lambda x: x['raw_ticks'])
    
    # OUTPUT
    print(json.dumps(project_info, indent=4))
    
    # Save to file
    with open('logic_project_deep_analysis.json', 'w') as f:
        json.dump(project_info, f, indent=4)

if __name__ == "__main__":
    analyze_logic_project('ProjectData')