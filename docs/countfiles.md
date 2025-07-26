# countfiles

A Python script that counts the total number of files in a directory and its subdirectories.

## Usage

```bash
python countfiles.py [directory_path]
```

### Arguments

- `directory_path` (optional): Path to the directory to count files in. If not provided, uses the current working directory.

### Examples

Count files in the current directory:
```bash
python countfiles.py
```

Count files in a specific directory:
```bash
python countfiles.py C:\Users\username\Documents
```

Count files in a relative path:
```bash
python countfiles.py ../projects
```

## Features

- **Recursive counting**: Counts all files in the specified directory and all its subdirectories
- **Simple output**: Displays the total count with the directory path
- **Default behavior**: Uses current working directory if no path is provided
- **Cross-platform**: Works on Windows, macOS, and Linux

## Output

The script outputs a single line showing the total number of files and the directory path:

```
Number of files in 'C:\Users\username\Documents': 342
```

## Implementation Details

The script uses Python's `os.walk()` function to traverse the directory tree recursively and counts all files (not directories) found. It handles the directory traversal efficiently by using a generator expression with `sum()`.

## Requirements

- Python 3.x
- No external dependencies (uses only standard library modules)

## Error Handling

The script will fail gracefully if:
- The specified directory doesn't exist
- Permission is denied to access certain directories
- Invalid path is provided

In such cases, Python will raise appropriate exceptions with descriptive error messages.
