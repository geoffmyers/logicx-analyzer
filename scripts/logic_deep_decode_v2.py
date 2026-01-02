import struct
import json
import re
import os

def read_variable_length(data, offset):
    """Logic uses a variable length int format in some places."""
    value = 0
    while True:
        if offset >= len(data): break
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
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[!] Error: File '{file_path}' not found.")
        return

    # Verify Magic (Logic LSO)
    if content[:4].hex() != "2347c0ab":
        print("[!] Warning: Magic bytes do not match standard Logic LSO (2347c0ab).")

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
        # Safety check for end of file
        if offset + 36 > len(content): break
        
        # Read Chunk Header
        chunk_header = content[offset:offset+36]
        
        # Decode descriptor (4 chars, reversed)
        try:
            desc = chunk_header[0:4][::-1].decode('ascii', errors='ignore')
        except:
            desc = "UNKN"
            
        data_len = struct.unpack('<Q', chunk_header[28:36])[0]
        chunk_data = content[offset+36 : offset+36+data_len]
        
        # --- PARSE 'Song' CHUNK (Global Globals) ---
        if desc == "Song":
            # Song chunk often contains global project settings
            pass

        # --- PARSE 'EvSq' CHUNK (Events: Markers, Tempo, Chords) ---
        elif desc == "EvSq":
            # Scan the chunk for event headers
            idx = 0
            while idx < len(chunk_data) - 16:
                # MARKER SIGNATURE CHECK
                # 0x12 (18) is often the event type for Markers/Meta events
                if chunk_data[idx] == 0x12 and chunk_data[idx+1:idx+4] == b'\x00\x00\x00':
                    
                    # Found a potential marker/event!
                    # Next 4 bytes are Ticks (Position)
                    try:
                        tick_bytes = chunk_data[idx+4:idx+8]
                        ticks = struct.unpack('<I', tick_bytes)[0]
                        
                        # Logic uses huge integers for muted/hidden events sometimes
                        # We filter reasonable song lengths (e.g., < 10,000 bars)
                        if ticks > project_info["duration_ticks"] and ticks < 3840000: 
                            project_info["duration_ticks"] = ticks
                        
                        position_str, raw_ticks = parse_ticks(ticks)
                        
                        # Store finding
                        project_info["markers"].append({
                            "type": "Marker/Event",
                            "position": position_str,
                            "raw_ticks": raw_ticks,
                            "offset_in_chunk": idx
                        })
                    except:
                        pass
                    
                    idx += 48 # Skip ahead (Marker structure is approx 48 bytes)
                else:
                    idx += 4 # Align search scan
        
        # --- PARSE 'TxSq' CHUNK (Text for Markers) ---
        elif desc == "TxSq":
            # This contains the actual text for the markers found in EvSq
            # Using raw string (r'') to avoid escape warning
            strings = re.findall(rb'[a-zA-Z0-9 \-_]{3,}', chunk_data)
            clean_strings = [s.decode('utf-8', errors='ignore') for s in strings]
            
            # Simple heuristic: if we found text here, associate it generally with the project
            # (Mapping specific text to specific marker IDs requires the m3 ID link)
            for s in clean_strings:
                # Filter out RTF formatting junk often found in Logic text chunks
                if "{" not in s and "}" not in s and "\\" not in s:
                    project_info["chords"].append(s) # Storing in chords/text dump for now

        offset += 36 + data_len

    # Finalize Calculations
    project_info["duration_bars"], _ = parse_ticks(project_info["duration_ticks"])
    
    # Sort markers by position
    project_info["markers"] = sorted(project_info["markers"], key=lambda x: x['raw_ticks'])
    
    # Dedup and clean text list
    project_info["chords"] = list(set(project_info["chords"]))

    # OUTPUT
    print(json.dumps(project_info, indent=4))
    
    # Save to file
    output_file = 'logic_project_deep_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(project_info, f, indent=4)
    print(f"[*] Analysis saved to {output_file}")

if __name__ == "__main__":
    # Ensure this matches your filename
    analyze_logic_binary('ProjectData')