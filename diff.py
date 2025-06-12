import argparse
import sys

def read_requirements(file_path):
    with open(file_path, 'r') as f:
        # Ignore empty lines and comments
        return set(line.strip() for line in f if line.strip() and not line.strip().startswith('#'))

def read_from_stdin():
    # Read lines from stdin, ignore empty lines and comments
    return set(line.strip() for line in sys.stdin if line.strip() and not line.strip().startswith('#'))

def main():
    parser = argparse.ArgumentParser(
        description="Find the difference between two requirements.txt files or between a file and stdin. "
                    "By default, outputs packages in file2 (or stdin) not in file1. "
                    "With --symmetric, outputs packages in either file but not both. "
                    "Use -o to write to a file (overwrites by default; use -a to append)."
    )
    parser.add_argument("file1", help="First requirements file (base)")
    parser.add_argument("file2", nargs='?', help="Second requirements file (to compare). If omitted, reads from stdin.")
    parser.add_argument("-o", "--output", help="Output file to write the difference", required=False)
    parser.add_argument("-s", "--symmetric", action="store_true", help="Compute symmetric difference (packages in either file but not both)")
    parser.add_argument("-a", "--append", action="store_true", help="Append to the output file instead of overwriting (requires -o)")
    args = parser.parse_args()

    reqs1 = read_requirements(args.file1)
    if args.file2:
        reqs2 = read_requirements(args.file2)
    else:
        reqs2 = read_from_stdin()

    # Compute difference based on symmetric flag
    if args.symmetric:
        diff = sorted(reqs1.symmetric_difference(reqs2))
    else:
        diff = sorted(reqs2 - reqs1)

    if args.output:
        # Use 'a' mode for append if --append is set, otherwise 'w' for overwrite
        mode = 'a' if args.append else 'w'
        with open(args.output, mode) as out:
            for pkg in diff:
                out.write(pkg + '\n')
        action = "appended to" if args.append else "written to"
        print(f"{'Symmetric difference' if args.symmetric else 'Difference'} {action} {args.output}")
    else:
        if args.append:
            print("Warning: --append ignored because no output file (-o) was specified.")
        for pkg in diff:
            print(pkg)

if __name__ == "__main__":
    main()