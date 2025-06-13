import argparse
import sys

def strip_lines_from_iter(lines, output_file=None):
    stripped = [line.strip() for line in lines]
    if output_file:
        with open(output_file, 'w') as out:
            for line in stripped:
                out.write(line + '\n')
    else:
        for line in stripped:
            print(line)

def main():
    parser = argparse.ArgumentParser(description="Remove leading and trailing whitespace from each line of a file or stdin.")
    parser.add_argument("input_file", nargs="?", help="Input file to process (if omitted, reads from stdin)")
    parser.add_argument("-o", "--output", help="Output file (if omitted, prints to stdout)")
    args = parser.parse_args()

    if args.input_file:
        with open(args.input_file, 'r') as f:
            strip_lines_from_iter(f, args.output)
    else:
        strip_lines_from_iter(sys.stdin, args.output)

if __name__ == "__main__":
    main()