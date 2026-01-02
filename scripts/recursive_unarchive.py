import gzip
import plistlib

def recursive_unarchive(obj, objects):
    """
    Recursively resolves UIDs in an NSKeyedArchiver structure 
    to reconstruct the original object graph.
    """
    if isinstance(obj, plistlib.UID):
        # The magic happens here: UID(123) -> objects[123]
        idx = obj.data
        if 0 <= idx < len(objects):
            return recursive_unarchive(objects[idx], objects)
        return f"<Invalid UID {idx}>"
    
    elif isinstance(obj, dict):
        # If it has a $class key, it's a serialized Logic object
        if '$class' in obj:
            # We treat the object as a dictionary of its properties
            new_obj = {}
            for k, v in obj.items():
                if k != '$class':
                    new_obj[k] = recursive_unarchive(v, objects)
            # Optional: Add class name for context
            # class_uid = obj['$class']
            # new_obj['_class_info'] = objects[class_uid.data]
            return new_obj
        else:
            return {k: recursive_unarchive(v, objects) for k, v in obj.items()}
            
    elif isinstance(obj, list):
        return [recursive_unarchive(x, objects) for x in obj]
    
    else:
        return obj

file_path = 'ProjectData'

try:
    # 1. Read & Decompress
    with open(file_path, 'rb') as f:
        file_content = f.read()
        
    # Check for GZIP signature (1f 8b)
    if file_content.startswith(b'\x1f\x8b'):
        print("Detected GZIP compression. Decompressing...")
        file_content = gzip.decompress(file_content)

    # 2. Parse Binary Plist
    if file_content.startswith(b'bplist'):
        print("Detected Binary Plist. Decoding...")
        plist_root = plistlib.loads(file_content)
        
        # 3. Unarchive NSKeyedArchiver
        if '$objects' in plist_root:
            print("Detected NSKeyedArchiver structure. Reconstructing Object Graph...")
            objects = plist_root['$objects']
            root_uid = plist_root['$top']['root']
            
            # Reconstruct the project data
            project_data = recursive_unarchive(root_uid, objects)
            
            print("\n--- DECODED SUCCESS ---")
            print("Root Object Keys:", list(project_data.keys()))
            # print(project_data) # Uncomment to dump the full project structure
        else:
            print("Standard Plist structure found.")
            print(plist_root)
    else:
        print("Unknown file format. Magic bytes:", file_content[:10].hex())

except Exception as e:
    print(f"Analysis failed: {e}")