# striplines.py

A simple CLI tool to remove leading and trailing whitespace from each line of a file or from standard input (stdin).

## Features

- Strips whitespace from the beginning and end of every line.
- Can process a file or read from another command’s output via stdin.
- Optionally writes the cleaned lines to an output file.

## Usage

```sh
python striplines.py [input_file] [-o OUTPUT]
```

- `input_file` (optional): The file to process. If omitted, reads from stdin.
- `-o OUTPUT`, `--output OUTPUT`: Write the result to this file. If omitted, prints to stdout.

## Examples

**Strip lines in a file and print to terminal:**
```sh
python striplines.py file1.txt
```

**Strip lines in a file and write to a new file:**
```sh
python striplines.py file1.txt -o cleaned.txt
```

**Strip lines from the output of another command (using a pipe):**
```sh
type file1.txt | python striplines.py
```

**Strip lines from piped input and write to a file:**
```sh
type file1.txt | python striplines.py -o cleaned.txt
```

## Notes

- Works with both files and piped input.
- Each line is stripped of leading and trailing whitespace before output.
- If an output file is specified, the result is written there; otherwise, it is printed to the terminal.