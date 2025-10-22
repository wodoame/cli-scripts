#!/usr/bin/env python3
import os
import argparse

def print_tree(start_path, prefix="", show_hidden=True):
    try:
        # Get all entries and sort them
        all_entries = os.listdir(start_path)
        
        # Filter hidden files if show_hidden is False
        if not show_hidden:
            entries = [e for e in all_entries if not e.startswith('.')]
        else:
            entries = all_entries
            
        entries = sorted(entries)

    except PermissionError:
        print(prefix + "└── [Permission Denied]")
        return # Stop recursing down this branch

    entries_count = len(entries)
    for idx, entry in enumerate(entries):
        # Get the full path for os.path checks
        path = os.path.join(start_path, entry)
        
        # Determine the connector
        connector = "└── " if idx == entries_count - 1 else "├── "
        
        display_name = entry
        is_dir = False # Flag to check if we need to recurse

        # Check entry type to add markers
        if os.path.islink(path):
            # Mark symlinks and show their target
            display_name += " -> " + os.readlink(path)
        elif os.path.isdir(path):
            # Mark directories with a /
            display_name += "/"
            is_dir = True

        # Print the entry
        print(prefix + connector + display_name)

        # If it's a directory, recurse
        if is_dir:
            # Calculate the prefix for the next level
            extension = "    " if idx == entries_count - 1 else "│   "
            print_tree(path, prefix + extension, show_hidden=show_hidden)

def main():
    parser = argparse.ArgumentParser(description="Print directory tree in Markdown-like style.")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to list (default: current directory)")
    parser.add_argument("--show-hidden", action="store_true", help="Include hidden files and folders")
    args = parser.parse_args()

    print(args.directory)
    print_tree(args.directory, show_hidden=args.show_hidden)

if __name__ == "__main__":
    main()
