# pdf_text_search.py

A command-line tool to search for text in PDF files and display sentences containing matches, with customizable color and style highlighting for the search term.

---

## Features

- **Searches for a text string** in one or more PDF files or folders.
- **Recursively searches subfolders** (optional).
- **Highlights matches** in color and/or style (bold, underline, or plain color).
- **Displays the sentence and approximate page number** for each match.
- **Supports multiple highlight colors** (`red`, `green`, `yellow`, `blue`, or `no-color`).

---

## Usage

```sh
python pdf_text_search.py SEARCH_TERM PATH [PATH ...] [options]
```

- `SEARCH_TERM`: The text to search for (case-insensitive).
- `PATH`: One or more PDF files or folders to search (space-separated).

### Options

- `-r`, `--recursive`  
  Search folders recursively (include subfolders).

- `-c COLOR`, `--color COLOR`  
  Highlight color for matches. Choices: `red`, `green`, `yellow`, `blue`, `no-color`. Default: `red`.

- `-s STYLE`, `--style STYLE`  
  Highlight style for matches. Choices: `color`, `bold`, `underline`. Default: `color`.

---

## Examples

**Search for "database" in all PDFs in the current folder:**
```sh
python pdf_text_search.py database .
```

**Search recursively in a folder and highlight in green and bold:**
```sh
python pdf_text_search.py user ./docs -r -c green -s bold
```

**Search in specific files:**
```sh
python pdf_text_search.py login file1.pdf file2.pdf
```

---

## Output

- For each match, prints the sentence containing the search term, with the term highlighted.
- Shows the (approximate) page number for each match.
- Groups results by file.

---

## Notes

- Hidden/system files are ignored.
- The tool uses [colorama](https://pypi.org/project/colorama/) for cross-platform color support.
- Page numbers are estimated based on text length and may not be exact.
- Only text-based PDFs are supported (scanned/image PDFs will not work unless OCR is used).

---

## Requirements

- Python 3.x
- [PyPDF2](https://pypi.org/project/PyPDF2/)
- [colorama](https://pypi.org/project/colorama/)

Install dependencies with:
```sh
pip install PyPDF2 colorama
```

---

## Example Output

```
Results for 'database':

In ./docs/guide.pdf:
Match 1 (approx. page 2): The application connects to the **database** using SQLAlchemy.
Match 2 (approx. page 5): Ensure your **database** credentials are correct.
```

---

**Author:**  
Your Name  
**License:**  
MIT (or your preferred license)
