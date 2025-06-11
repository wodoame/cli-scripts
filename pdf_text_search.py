import PyPDF2
import os
import re
import argparse
from typing import List, Tuple
import colorama

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + " "
            return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def find_sentences_with_text(text: str, search_term: str) -> List[Tuple[str, int]]:
    """
    Find sentences containing the search term and their page numbers.
    Returns list of (sentence, page_number) tuples.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    matches = []
    total_length = len(text)
    page_count = estimate_page_count(text)
    
    for sentence in sentences:
        if search_term.lower() in sentence.lower():
            position = text.lower().find(sentence.lower())
            if position != -1 and total_length > 0:
                page_num = int((position / total_length) * page_count) + 1
                matches.append((sentence.strip(), page_num))
    
    return matches

def estimate_page_count(text: str) -> int:
    """Estimate number of pages based on text length (rough approximation)."""
    chars_per_page = 2000
    return max(1, len(text) // chars_per_page + 1)

def search_pdfs(pdf_paths: List[str], search_term: str) -> dict:
    """Search multiple PDF files for the search term."""
    results = {}
    
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            continue
            
        if not pdf_path.lower().endswith('.pdf'):
            print(f"Skipping non-PDF file: {pdf_path}")
            continue
            
        print(f"Searching in: {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        if not text:
            continue
            
        matches = find_sentences_with_text(text, search_term)
        if matches:
            results[pdf_path] = matches
            
    return results

def get_pdf_files_from_folder(folder_path: str, recursive: bool) -> List[str]:
    """Get all PDF files from a folder, optionally searching subfolders."""
    pdf_files = []
    try:
        if recursive:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(folder_path):
                full_path = os.path.join(folder_path, file)
                if os.path.isfile(full_path) and file.lower().endswith('.pdf'):
                    pdf_files.append(full_path)
    except Exception as e:
        print(f"Error accessing folder {folder_path}: {e}")
    return pdf_files

def highlight_text(sentence: str, search_term: str, color: str, style: str) -> str:
    """Highlight the search term in the sentence using colorama color and style codes."""
    # Initialize colorama (safe to call multiple times)
    colorama.init(autoreset=True)

    # Colorama color codes
    color_codes = {
        'no-color': '',
        'red': colorama.Fore.RED,
        'green': colorama.Fore.GREEN,
        'yellow': colorama.Fore.YELLOW,
        'blue': colorama.Fore.BLUE
    }
    # Colorama style codes
    style_codes = {
        'color': '',
        'bold': colorama.Style.BRIGHT,
        'underline': '\033[4m'  # ANSI code for underline
    }
    color_code = color_codes.get(color.lower(), colorama.Fore.RED)
    style_code = style_codes.get(style.lower(), '')
    reset_code = colorama.Style.RESET_ALL

    def repl(match):
        return f"{style_code}{color_code}{match.group(0)}{reset_code}"

    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    return pattern.sub(repl, sentence)

def main():
    parser = argparse.ArgumentParser(description="Search for text in PDF files and display sentences containing matches.")
    parser.add_argument("search_term", help="Text to search for in the PDFs")
    parser.add_argument("paths", nargs='+', help="PDF files or folders to search (space-separated)")
    parser.add_argument("-r", "--recursive", action="store_true", 
                       help="Search folders recursively (include subfolders)")
    parser.add_argument("-c", "--color", default="red", 
                       choices=['red', 'green', 'yellow', 'blue', 'no-color'],
                       help="Color for highlighting matches (default: red)")
    parser.add_argument("-s", "--style", default="color", 
                       choices=['color', 'bold', 'underline'],
                       help="Style for highlighting matches (default: color)")
    
    args = parser.parse_args()
    search_term = args.search_term.strip()
    paths = args.paths
    recursive = args.recursive
    color = args.color
    style = args.style
    
    if not search_term:
        print("Search term cannot be empty.")
        return
    
    pdf_files = []
    for path in paths:
        if os.path.isdir(path):
            pdf_files.extend(get_pdf_files_from_folder(path, recursive))
        elif os.path.isfile(path):
            pdf_files.append(path)
        else:
            print(f"Invalid path: {path}")
    
    if not pdf_files:
        print("No valid PDF files found.")
        return
    
    pdf_files = list(dict.fromkeys(pdf_files))  # Remove duplicates
    
    results = search_pdfs(pdf_files, search_term)
    
    if not results:
        print(f"No matches found for '{search_term}'.")
        return
        
    print(f"\nResults for '{search_term}':")
    for pdf_path, matches in results.items():
        print(f"\nIn {pdf_path}:")
        for i, (sentence, page_num) in enumerate(matches, 1):
            highlighted_sentence = highlight_text(sentence, search_term, color, style)
            print(f"Match {i} (approx. page {page_num}): {highlighted_sentence}")

if __name__ == "__main__":
    main()