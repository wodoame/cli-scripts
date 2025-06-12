# diff.py Documentation

## Overview

`diff.py` is a Python command-line tool that compares two sets of Python package requirements (from `requirements.txt` files or standard input) and outputs the differences. By default, it lists packages present in the second input but not in the first (set difference). With the `--symmetric` (or `-s`) flag, it computes the symmetric difference, listing packages that are in either input but not in both. The output can be printed to the console or written to a file.

## Requirements

- Python 3.x
- No external dependencies (uses standard library modules `argparse` and `sys`).

## Usage

Run the script from the command line with the following syntax:

```bash
python diff.py file1 [file2] [-o output_file] [-s | --symmetric]
```

### Arguments

- **`file1`** (required): Path to the first requirements file (base file). This file contains package names, one per line, with optional version specifiers (e.g., `requests==2.28.1`). Empty lines and lines starting with `#` are ignored.
- **`file2`** (optional): Path to the second requirements file to compare against `file1`. If omitted, the script reads from standard input (`stdin`).
- **`-o`, `--output`** (optional): Path to an output file where the difference will be written. If not provided, the difference is printed to the console.
- **`-s`, `--symmetric`** (optional): If specified, computes the symmetric difference (packages in either `file1` or `file2`/`stdin` but not in both) instead of the default one-way difference (packages in `file2`/`stdin` not in `file1`).

### Behavior

- **Default Mode**: Computes the set difference (`file2 - file1`), outputting packages that are in `file2` (or `stdin`) but not in `file1`. The order of inputs matters in this mode.
- **Symmetric Mode**: With `-s` or `--symmetric`, computes the symmetric difference (`file1 XOR file2`), outputting packages that are in either input but not both. The order of inputs does not affect the result in this mode.
- Lines in input files that are empty or start with `#` are ignored.
- The output is sorted alphabetically for consistency.
- If an output file is specified via `-o`, the result is written to that file, and a confirmation message is printed to the console. Otherwise, the result is printed directly to the console.

## Examples

### Example 1: Default Difference
Suppose `reqs1.txt` contains:
```
requests
numpy
```

And `reqs2.txt` contains:
```
requests
pandas
```

Run:
```bash
python diff.py reqs1.txt reqs2.txt
```

**Output** (packages in `reqs2.txt` not in `reqs1.txt`):
```
pandas
```

### Example 2: Symmetric Difference
Using the same files, run:
```bash
python diff.py reqs1.txt reqs2.txt -s
```

**Output** (packages in either file but not both):
```
numpy
pandas
```

### Example 3: Output to File
Run:
```bash
python diff.py reqs1.txt reqs2.txt -o diff.txt
```

**Result**: The package `pandas` is written to `diff.txt`, and the console shows:
```
Difference written to diff.txt
```

### Example 4: Using Standard Input
Run:
```bash
echo -e "requests\npandas" | python diff.py reqs1.txt
```

**Output** (packages in `stdin` not in `reqs1.txt`):
```
pandas
```

### Example 5: Symmetric Difference with Standard Input
Run:
```bash
echo -e "requests\npandas" | python diff.py reqs1.txt -s
```

**Output** (packages in either `reqs1.txt` or `stdin` but not both):
```
numpy
pandas
```

## Notes

- The script assumes that input files are text files with one package per line, following the `requirements.txt` format. Invalid file paths or unreadable files will raise an error.
- When using standard input, ensure the input is properly formatted (one package per line, no trailing whitespace).
- The symmetric difference mode (`-s` or `--symmetric`) is useful when you want to identify all unique packages across both inputs, regardless of their order.
- The output preserves the package names as they appear in the input files, including any version specifiers (e.g., `requests==2.28.1`).

## Error Handling

- If `file1` does not exist or is not readable, the script will raise a `FileNotFoundError` or `PermissionError`.
- If `file2` is provided but does not exist or is not readable, the same errors apply.
- If the output file path (`-o`) cannot be written to (e.g., due to permissions or invalid path), a corresponding error will be raised.

## Source Code

The script uses Python's `set` operations:
- Default mode: `set(file2) - set(file1)`
- Symmetric mode: `set(file1).symmetric_difference(set(file2))`

It leverages `argparse` for command-line argument parsing and `sys` for handling standard input.