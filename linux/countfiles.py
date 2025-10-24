#!/usr/bin/env python3
import os
import argparse  # Use argparse for better argument handling

def count_files_in_directory(directory, max_depth=1):
    """
    Recursively counts files in a directory up to a specified depth.
    
    :param directory: The path to the directory to scan.
    :param max_depth: The maximum depth to recurse.
                      1 = only files in the start directory.
                      2 = files in start directory + immediate children.
                      0 = unlimited depth.
    """
    total_files = 0
    
    # Get the absolute starting path and its "level" (number of separators)
    # This is our baseline for calculating relative depth.
    try:
        start_path = os.path.abspath(directory)
    except FileNotFoundError:
        # Handle case where directory doesn't exist right away
        raise 
        
    start_level = start_path.count(os.sep)

    # os.walk(topdown=True) lets us modify the dirnames list
    # to control which subdirectories it recurses into.
    for dirpath, dirnames, filenames in os.walk(directory, topdown=True):
        
        # 1. Count files at the current level
        total_files += len(filenames)
        
        # 2. Check if we should stop going deeper
        
        # We check for max_depth > 0 to allow 0 to mean "unlimited"
        if max_depth > 0:
            # Calculate the current depth relative to the start
            current_level = os.path.abspath(dirpath).count(os.sep)
            current_depth = current_level - start_level + 1
            
            # If we are at the max_depth, prune the dirnames list
            if current_depth >= max_depth:
                # This in-place modification tells os.walk
                # NOT to visit any subdirectories from this point.
                del dirnames[:] 
                
    return total_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Count files in a directory up to a specified depth."
    )
    
    # Replaces sys.argv[1]
    parser.add_argument(
        "directory", 
        nargs="?",  # Makes the argument optional
        default=os.getcwd(),  # Default to current directory
        help="Directory to scan (default: current directory)"
    )
    
    # Your new depth argument
    parser.add_argument(
        "-d", "--depth", 
        type=int, 
        default=1,  # Default depth is 1
        help="Max depth to scan. 1=current dir only, 0=unlimited. (default: 1)"
    )
    
    args = parser.parse_args()
    
    try:
        # Pass the depth argument to the function
        count = count_files_in_directory(args.directory, max_depth=args.depth)
        
        # Make the output clearer for the "unlimited" case
        depth_str = "unlimited" if args.depth == 0 else str(args.depth)
        
        print(f"Number of files in '{args.directory}' (depth: {depth_str}): {count}")

    except FileNotFoundError:
        print(f"Error: Directory not found: {args.directory}")
    except NotADirectoryError:
        print(f"Error: Path is not a directory: {args.directory}")
    except PermissionError:
        print(f"Error: Permission denied for: {args.directory}")
