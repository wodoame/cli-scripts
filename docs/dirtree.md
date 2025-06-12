# dirtree.py

A simple CLI tool to print the directory structure in a graphical, Markdown-like tree format.

## Features

- Lists all files and subdirectories in a tree view.
- Optionally includes or excludes hidden files and folders (those starting with a dot).
- Output is similar to directory trees often seen in Markdown documentation.

## Usage

```sh
python dirtree.py [directory] [--show-hidden]
```

- `directory` (optional): The root directory to display. Defaults to the current directory (`.`) if not specified.
- `--show-hidden`: If provided, hidden files and folders (starting with `.`) will be included in the output.

## Examples

**List the current directory tree (excluding hidden files/folders):**
```sh
python dirtree.py
```

**List a specific directory:**
```sh
python dirtree.py path/to/your/folder
```

**Include hidden files and folders:**
```sh
python dirtree.py path/to/your/folder --show-hidden
```

## Sample Output

```
myfolder
├── file1.txt
├── file2.py
└── subdir
    └── file3.md
```

## How it works

- The script recursively traverses the specified directory.
- For each directory, it prints the contents in a tree structure using `├──`, `└──`, and indentation.
- By default, hidden files and folders are excluded unless `--show-hidden` is specified.

---

**Tip:**  
You can create a batch file (e.g., `dirtree.bat`) to make it easier to run on Windows:

```bat
@echo off
python C:\path\to\dirtree.py %*
```

Now you can run `dirtree.bat` from the command line.