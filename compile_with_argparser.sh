#!/bin/bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 path/to/program.c" >&2
    exit 1
fi

source_path=$1

if [[ ! -f "$source_path" ]]; then
    echo "Error: Source file '$source_path' not found." >&2
    exit 1
fi

if [[ "${source_path##*.}" != "c" ]]; then
    echo "Error: '$source_path' is not a .c source file." >&2
    exit 1
fi

source_dir=$(dirname -- "$source_path")
source_base=$(basename -- "$source_path")
output_name=${source_base%.c}

object_file="$source_dir/$output_name.o"
executable="$source_dir/$output_name"

# Compile the requested source and link it with the shared argparser module.
gcc -c "$source_path" -o "$object_file"
gcc -c parser/argparser.c -o parser/argparser.o
gcc -o "$executable" "$object_file" parser/argparser.o
