import os
import argparse

def print_tree(start_path, prefix="", show_hidden=True):
    entries = sorted(os.listdir(start_path))
    if not show_hidden:
        entries = [e for e in entries if not e.startswith('.')]
    entries_count = len(entries)
    for idx, entry in enumerate(entries):
        path = os.path.join(start_path, entry)
        connector = "└── " if idx == entries_count - 1 else "├── "
        print(prefix + connector + entry)
        if os.path.isdir(path):
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