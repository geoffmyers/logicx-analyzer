#!/usr/bin/env python3
"""
Experimental script v2 for Logic Pro ProjectData string extraction.
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

def parse_chunk_header(chunk_data):
    """
    Parses the 36-byte chunk header based on the provided documentation.
    """
    if len(chunk_data) < 36:
        return None

    header = {}
    
    # 0x00 - 0x03: Descriptor (4 chars, backwards)
    try:
        descriptor_bytes = chunk_data[0:4]
        # Reverse the bytes to get the descriptor
        descriptor = descriptor_bytes[::-1].decode('ascii')
        header['descriptor'] = descriptor
    except:
        header['descriptor'] = 'UNKNOWN'

    # 0x04 - 0x05: m1 (16-bit int)
    header['m1'] = struct.unpack('<H', chunk_data[4:6])[0]

    # 0x06 - 0x09: m2 (32-bit int)
    header['m2'] = struct.unpack('<I', chunk_data[6:10])[0]

    # 0x0A - 0x0D: m3/OID (32-bit int)
    header['m3'] = struct.unpack('<I', chunk_data[10:14])[0]

    # 0x0E - 0x11: m4 (32-bit int)
    header['m4'] = struct.unpack('<I', chunk_data[14:18])[0]

    # 0x12 - 0x15: m5 (32-bit int)
    header['m5'] = struct.unpack('<I', chunk_data[18:22])[0]

    # 0x16 - 0x1B: stati (6 bytes, usually 02 00 00 00 01 00)
    header['stati'] = chunk_data[22:28].hex()

    # 0x1C - 0x23: len (64-bit int length of chunk data)
    header['data_len'] = struct.unpack('<Q', chunk_data[28:36])[0]

    return header

def analyze_logic_project_v2(file_path, output_json):
    print(f"[*] Reading binary file: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[!] Error: File '{file_path}' not found.")
        return

    # 1. Verify Magic Header (24 bytes)
    header_bytes = content[:24]
    magic, version_le, unknown_flags = struct.unpack('<I H 18s', header_bytes)
    
    metadata = {
        "file_size_bytes": len(content),
        "magic_signature": hex(magic),
        "version_hex": hex(version_le)
    }
    
    # Logic LSO Magic: 23 47 C0 AB (0xabc04723 in LE)
    if magic != 0xabc04723:
        print(f"[!] Warning: File signature {hex(magic)} does not match known Logic LSO header (0xabc04723).")
    else:
        print(f"[*] Verified Logic Pro LSO binary format.")

    # 2. Iterate through chunks
    chunks = []
    offset = 24 # Start after file header
    
    while offset < len(content):
        # Ensure we have enough bytes for a chunk header
        if offset + 36 > len(content):
            break
            
        chunk_header_data = content[offset:offset+36]
        header_info = parse_chunk_header(chunk_header_data)
        
        if not header_info:
            break
            
        # Extract data based on length
        data_len = header_info['data_len']
        data_start = offset + 36
        data_end = data_start + data_len
        
        if data_end > len(content):
            print(f"[!] Warning: Chunk data length exceeds file size. Truncating.")
            data_end = len(content)
            
        chunk_data = content[data_start:data_end]
        
        # Analyze chunk data based on type
        chunk_analysis = {
            "header": header_info,
            "strings": extract_strings(chunk_data)
        }
        
        # Add to list
        chunks.append(chunk_analysis)
        
        # Move to next chunk
        offset = data_end

    print(f"[*] Parsed {len(chunks)} chunks.")

    # 3. Consolidate Data for JSON
    
    # Group chunks by type
    chunks_by_type = {}
    for c in chunks:
        desc = c['header']['descriptor']
        if desc not in chunks_by_type:
            chunks_by_type[desc] = []
        chunks_by_type[desc].append(c)
        
    final_output = {
        "metadata": metadata,
        "chunk_summary": {k: len(v) for k, v in chunks_by_type.items()},
        "chunks": chunks_by_type
    }

    # 4. Save to JSON
    with open(output_json, 'w') as f:
        json.dump(final_output, f, indent=4)
    
    print(f"[*] Analysis complete. Saved to: {output_json}")

# --- Execution ---
if __name__ == "__main__":
    target_file = 'ProjectData'
    output_file = 'project_data_decoded_v2.json'
    
    analyze_logic_project_v2(target_file, output_file)