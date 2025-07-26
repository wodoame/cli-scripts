import os
import sys

def count_files_in_directory(directory):
    return sum([len(files) for _, _, files in os.walk(directory)])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dir_path = sys.argv[1]
    else:
        dir_path = os.getcwd()
    count = count_files_in_directory(dir_path)
    print(f"Number of files in '{dir_path}': {count}")
