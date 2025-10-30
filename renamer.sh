#!/bin/bash

# --- 1. Initialize Variables ---
DRY_RUN=false
TARGET_DIR=""
# Declare arrays to hold our lists of rules
declare -a prefixes_to_remove=()
declare -a suffixes_to_remove=()
declare -a strings_to_remove=()

# --- 2. Help Function ---
show_help() {
  echo "Usage: $0 [OPTIONS] [DIRECTORY]"
  echo "Flexibly renames files in a directory based on a set of rules."
  echo
  echo "If [DIRECTORY] is not provided, it defaults to the current directory."
  echo
  echo "Options:"
  echo "  -d, --dry-run      Show what would be renamed without doing it."
  echo "  -h, --help         Show this help message."
  echo
  echo "Removal Rules (can be used multiple times):"
  echo "  --prefix 'STRING'  Add a string to remove from the *beginning* of filenames."
  echo "  --suffix 'STRING'  Add a string to remove from the *end* of filenames."
  echo "  --remove 'STRING'  Add a string to remove from *anywhere* in the filename"
  echo "                     (removes all occurrences)."
  echo
  echo "Default Cleanup Rules (always applied *after* removals):"
  echo "  1. Replaces all underscores (_) with dashes (-)."
  echo "  2. Squashes multiple dashes (--) into a single dash (-)."
  echo
  echo "Example:"
  echo "  # Dry run in '~/books' to remove a prefix and a common suffix"
  echo "  $0 -d --prefix '_oceanpdf.com_' --suffix '.epub' ~/books"
}

# --- 3. Parse Arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
  -h | --help)
    show_help
    exit 0
    ;;
  -d | --dry-run)
    DRY_RUN=true
    shift # Remove the flag
    ;;
  --prefix)
    if [ -z "$2" ]; then
      echo "Error: --prefix requires a string argument." >&2
      exit 1
    fi
    prefixes_to_remove+=("$2") # Add to prefix array
    shift 2                    # Remove the flag and its argument
    ;;
  --suffix)
    if [ -z "$2" ]; then
      echo "Error: --suffix requires a string argument." >&2
      exit 1
    fi
    suffixes_to_remove+=("$2") # Add to suffix array
    shift 2
    ;;
  --remove)
    if [ -z "$2" ]; then
      echo "Error: --remove requires a string argument." >&2
      exit 1
    fi
    strings_to_remove+=("$2") # Add to global remove array
    shift 2
    ;;
  *)
    # If it's not a flag, assume it's the target directory.
    if [ -z "$TARGET_DIR" ]; then
      TARGET_DIR="$1"
    fi
    shift # Remove the argument
    ;;
  esac
done

# --- 4. Set and Validate Directory ---
if [ -z "$TARGET_DIR" ]; then
  TARGET_DIR="."
fi

if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory '$TARGET_DIR' not found."
  exit 1
fi

if [ "$DRY_RUN" = true ]; then
  echo "--- DRY RUN MODE --- (No files will be renamed)"
fi
echo "Scanning for files in '$TARGET_DIR'..."

# --- 5. Find and Loop ---
find "$TARGET_DIR" -maxdepth 1 -type f | while read -r f; do

  base_name=$(basename "$f")
  # Start with the original name and modify it step-by-step
  new_name="$base_name"

  # --- Rule 1: Apply prefix removals ---
  for prefix in "${prefixes_to_remove[@]}"; do
    # ${var#pattern} removes 'pattern' from the start of $var
    new_name="${new_name#$prefix}"
  done

  # --- Rule 2: Apply suffix removals ---
  for suffix in "${suffixes_to_remove[@]}"; do
    # ${var%pattern} removes 'pattern' from the end of $var
    new_name="${new_name%$suffix}"
  done

  # --- Rule 3: Apply global (all occurrences) removals ---
  for str in "${strings_to_remove[@]}"; do
    # ${var//pattern/replace} replaces all 'pattern' with 'replace'
    # We replace with an empty string to remove it.
    new_name="${new_name//$str/}"
  done

  # --- Rule 4: Replace underscores with dashes (Cleanup) ---
  name_step1="${new_name//_/-}"

  # --- Rule 5: Squash multiple dashes (Cleanup) ---
  final_name=$(echo "$name_step1" | tr -s '-')
  # NEW: Remove a single dash if it's at the very end
  final_name="${final_name%-}"
  # NEW: Remove a single dash if it's at the very beginning
  final_name="${final_name#-}"

  # --- Safety Check ---
  if [ "$base_name" != "$final_name" ]; then

    dir_name=$(dirname "$f")
    new_full_path="$dir_name/$final_name"

    if [ -e "$new_full_path" ]; then
      echo "⚠️  WARNING: Could not rename '$f'. Target '$new_full_path' already exists."
    else
      # --- 6. Execute or Dry Run ---
      if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Renaming: '$f'  ->  '$new_full_path'"
      else
        echo "Renaming: '$f'  ->  '$new_full_path'"
        mv "$f" "$new_full_path"
      fi
    fi
  fi
done

echo "Renaming complete."
