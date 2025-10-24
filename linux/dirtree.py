#!/usr/bin/env python3
import os
import argparse

def print_tree(start_path, prefix="", show_hidden=True, dirs_only=False):
    try:
        # Get all entries and sort them
        entries = os.listdir(start_path)
        
        # Filter hidden files if show_hidden is False
        if not show_hidden:
            entries = [e for e in entries if not e.startswith('.')] 
        entries = sorted(entries)

    except PermissionError:
        print(prefix + "└── [Permission Denied]")
        return # Stop recursing down this branch
    entries_count = len(entries)
    for idx, entry in enumerate(entries):
        # Get the full path for os.path checks
        path = os.path.join(start_path, entry)
        
        # Check types
        is_link = os.path.islink(path)
        # os.path.isdir follows symlinks, which is what we want for display
        is_directory_type = os.path.isdir(path)
        
        # This flag is for recursion, and the original script
        # only recursed on *non-symlink* directories.
        is_recursive_dir = (not is_link) and is_directory_type

        # Check if we should skip this entry
        if dirs_only and not is_directory_type:
            continue # Skip files if dirs_only is True
            
        # Determine the connector
        connector = "└── " if idx == entries_count - 1 else "├── "
        
        display_name = entry
        
        # Check entry type to add markers
        if is_link:
            # Mark symlinks and show their target
            display_name += " -> " + os.readlink(path)
        elif is_recursive_dir:
            # Mark directories with a /
            display_name += "/"
        
        # Print the entry
        print(prefix + connector + display_name)

        # If it's a directory, recurse
        if is_recursive_dir:
            # Calculate the prefix for the next level
            extension = "    " if idx == entries_count - 1 else "│   "
            print_tree(path, prefix + extension, show_hidden=show_hidden, dirs_only=dirs_only)

def main():
    parser = argparse.ArgumentParser(description="Print directory tree in Markdown-like style.")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to list (default: current directory)")
    parser.add_argument("-a", "--show-hidden", action="store_true", help="Include hidden files and folders")
    parser.add_argument("-d", "--dirs-only", action="store_true", help="List directories only")
    args = parser.parse_args()
    print(args.directory)
    # Pass the arguments to the function
    print_tree(args.directory, show_hidden=args.show_hidden, dirs_only=args.dirs_only)

if __name__ == "__main__":
    main()
