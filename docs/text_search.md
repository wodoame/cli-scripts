# text_search

A Python script that searches for text patterns in `.txt` files with colored highlighting and various formatting options.

## Usage

```bash
python text_search.py pattern [target] [options]
```

### Arguments

- `pattern` (required): Text pattern to search for (supports regular expressions)
- `target` (optional): Directory, single file, or comma-separated list of files to search. Defaults to current working directory.

### Options

- `-c, --color COLOR`: Highlight color for matches (default: yellow)
  - Available colors: black, red, green, yellow, blue, magenta, cyan, white
- `-r, --recursive`: Search recursively in subdirectories
- `-s, --style STYLE`: Highlight style for matches
  - Options: `bold`, `underline`, `none` (default: none)
- `-h, --help`: Show help message

## Examples

### Basic Usage

Search for "error" in all .txt files in the current directory:

```bash
python text_search.py error
```

Search in a specific directory:

```bash
python text_search.py "function" C:\Users\username\Documents
```

### Advanced Usage

Search recursively with red bold highlighting:

```bash
python text_search.py "TODO" . -r -c red -s bold
```

Search in specific files:

```bash
python text_search.py "import" file1.txt,file2.txt,file3.txt
```

Search with underline style:

```bash
python text_search.py "class" -s underline -c blue
```

## Features

- **Pattern matching**: Supports case-insensitive regular expression patterns
- **Flexible input**: Can search in directories, single files, or comma-separated file lists
- **Recursive search**: Optional recursive directory traversal
- **Colored output**: Customizable highlight colors using colorama
- **Multiple styles**: Bold, underline, or plain highlighting
- **Line numbers**: Shows line numbers for each match
- **UTF-8 support**: Handles various text encodings gracefully

## Output Format

The script displays results in the following format:

```text
filename.txt:
  5: This line contains the search pattern
  12: Another line with the pattern highlighted
  
another_file.txt:
  3: Found pattern here too
```

Matches are highlighted in the specified color and style within the output.

## Supported File Types

The script specifically searches for files with `.txt` extension (case-insensitive). Files with other extensions are ignored.

## Requirements

- Python 3.x
- `colorama` library for colored terminal output

Install colorama if not already available:

```bash
pip install colorama
```

## Implementation Details

- Uses `re.search()` for pattern matching with case-insensitive flag
- Employs `os.walk()` for recursive directory traversal
- Handles file encoding errors gracefully with `errors='ignore'`
- Utilizes colorama for cross-platform colored terminal output
- Supports ANSI escape codes for underline formatting

## Error Handling

The script handles various error conditions:

- Non-existent directories or files
- Permission denied errors
- File encoding issues
- Invalid regular expression patterns

## Pattern Syntax

Since the script uses regular expressions, you can use advanced pattern matching:

- `.` - matches any character
- `*` - matches zero or more of the preceding character
- `+` - matches one or more of the preceding character
- `^` - matches start of line
- `$` - matches end of line
- `[abc]` - matches any character in brackets
- `\d` - matches any digit
- `\w` - matches any word character

### Pattern Examples

```bash
# Find lines starting with "Error"
python text_search.py "^Error"

# Find email addresses
python text_search.py "\w+@\w+\.\w+"

# Find dates in MM/DD/YYYY format
python text_search.py "\d{2}/\d{2}/\d{4}"

# Find words ending with "ing"
python text_search.py "\w+ing\b"
```
