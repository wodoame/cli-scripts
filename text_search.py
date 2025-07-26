
import os
import sys
import argparse
import re
from colorama import init, Fore, Style

def highlight(text, match, color, style):
    color_code = getattr(Fore, color.upper(), Fore.YELLOW)
    style_code = ''
    if style == 'bold':
        style_code = Style.BRIGHT
    elif style == 'underline':
        style_code = '\033[4m'  # ANSI underline
    else:
        style_code = ''
    reset_code = Style.RESET_ALL
    # For underline, need to reset manually
    if style == 'underline':
        reset_code += '\033[24m'
    return re.sub(re.escape(match), f"{color_code}{style_code}{match}{reset_code}", text, flags=re.IGNORECASE)

def search_in_file(filepath, pattern, color, style):
    matches = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for lineno, line in enumerate(f, 1):
            if re.search(pattern, line, re.IGNORECASE):
                highlighted = highlight(line.rstrip(), pattern, color, style)
                matches.append((lineno, highlighted))
    return matches

def find_txt_files(target, recursive):
    # If target is a file or comma-separated list of files, return those
    if os.path.isfile(target):
        return [target]
    if ',' in target:
        files = [f.strip() for f in target.split(',') if f.strip()]
        return [f for f in files if os.path.isfile(f)]
    # Otherwise treat as directory
    txt_files = []
    if os.path.isdir(target):
        if recursive:
            for root, _, files in os.walk(target):
                for file in files:
                    if file.lower().endswith('.txt'):
                        txt_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(target):
                if file.lower().endswith('.txt'):
                    txt_files.append(os.path.join(target, file))
    return txt_files

def main():
    init(autoreset=True)
    parser = argparse.ArgumentParser(description='Search for text in .txt files in a directory.')
    parser.add_argument('pattern', help='Text pattern to search for')
    parser.add_argument('target', nargs='?', default=os.getcwd(), help='Directory, file, or comma-separated list of files to search')
    parser.add_argument('-c', '--color', default='yellow', help='Highlight color (default: yellow)')
    parser.add_argument('-r', '--recursive', action='store_true', help='Search recursively in subdirectories')
    parser.add_argument('-s', '--style', choices=['bold', 'underline', 'none'], default='none', help='Highlight style: bold, underline, or none (default: none)')
    args = parser.parse_args()

    style = args.style if args.style != 'none' else ''
    txt_files = find_txt_files(args.target, args.recursive)
    if not txt_files:
        print(f"No .txt files found in {args.target}")
        sys.exit(0)

    found = False
    for file in txt_files:
        matches = search_in_file(file, args.pattern, args.color, style)
        if matches:
            found = True
            print(f"\n{file}:")
            for lineno, line in matches:
                print(f"  {lineno}: {line}")
    if not found:
        print(f"No matches for '{args.pattern}' found in .txt files.")

if __name__ == "__main__":
    main()
