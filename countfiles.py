#!/usr/bin/env python3
import os
import argparse
import stat 

def count_files_in_directory(directory, max_depth=1):
    total_files = 0
    try:
        start_path = os.path.abspath(directory)
    except FileNotFoundError:
        raise
        
    start_level = start_path.count(os.sep)

    for dirpath, dirnames, filenames in os.walk(directory, topdown=True):
        
        # --- MODIFIED SECTION ---
        # Instead of just counting the list, check each file.
        for f in filenames:
            path = os.path.join(dirpath, f)
            try:
                # Use lstat to get stats of the file *without* following symlinks
                st = os.lstat(path)
                
                # Check if it's a REGULAR file (like S_ISREG in C)
                if stat.S_ISREG(st.st_mode):
                    total_files += 1
            except (FileNotFoundError, PermissionError):
                # Skip files that vanish or we can't read
                continue
        # --- END MODIFIED SECTION ---
        
        if max_depth > 0:
            current_level = os.path.abspath(dirpath).count(os.sep)
            current_depth = current_level - start_level + 1
            
            if current_depth >= max_depth:
                del dirnames[:] 
                
    return total_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Count files in a directory up to a specified depth."
    )
    
    parser.add_argument(
        "directory", 
        nargs="?",
        default=os.getcwd(),
        help="Directory to scan (default: current directory)"
    )
    
    parser.add_argument(
        "-d", "--depth", 
        type=int, 
        default=1,
        help="Max depth to scan. 1=current dir only, 0=unlimited. (default: 1)"
    )
    
    args = parser.parse_args()
    
    try:
        count = count_files_in_directory(args.directory, max_depth=args.depth)
        depth_str = "unlimited" if args.depth == 0 else str(args.depth)
        
        print(f"Number of files in '{args.directory}' (depth: {depth_str}): {count}")

    except FileNotFoundError:
        print(f"Error: Directory not found: {args.directory}")
    except NotADirectoryError:
        print(f"Error: Path is not a directory: {args.directory}")
    except PermissionError:
        print(f"Error: Permission denied for: {args.directory}")
