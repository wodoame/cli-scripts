#include <stdio.h>      // For printf, snprintf, fprintf, stderr
#include <stdlib.h>     // For atoi, EXIT_SUCCESS, EXIT_FAILURE
#include <string.h>     // For strcmp
#include <dirent.h>     // For opendir, readdir, closedir, struct dirent
#include <sys/stat.h>   // For lstat, struct stat, S_ISREG, S_ISDIR
#include <unistd.h>     // For getcwd
#include <limits.h>     // For PATH_MAX (max path length)

/**
 * @brief Recursively counts files in a directory up to a specified depth.
 *
 * @param base_path The path to the directory to scan.
 * @param current_depth The depth of the current call (1 for the start)#!/usr/bin/env python3
 * @param max_depth The maximum depth to recurse. 0 = unlimited.
 * @return The total count of regular files, or -1 on error.
 */
long long count_files(const char *base_path, int current_depth, int max_depth) {
    long long total_files = 0;
    DIR *dir;
    struct dirent *entry;
    struct stat st;

    // Try to open the directory
    dir = opendir(base_path);
    if (dir == NULL) {
        // Print error if we can't open it (e.g., permission denied)
        perror("Error opening directory");
        fprintf(stderr, "Path: %s\n", base_path);
        return -1; // Return -1 to signal an error
    }

    // Read directory entries one by one
    while ((entry = readdir(dir)) != NULL) {
        // Skip the special entries "." (current) and ".." (parent)
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue;
        }

        // --- Build the full path for the entry ---
        char full_path[PATH_MAX];
        // snprintf is a safe way to build paths, preventing buffer overflows
        int len = snprintf(full_path, sizeof(full_path), "%s/%s", base_path, entry->d_name);
        
        // Check if the path was truncated
        if (len >= sizeof(full_path)) {
            fprintf(stderr, "Error: Path too long: %s\n", full_path);
            continue; // Skip this entry
        }
        // --- End path building ---

        // Use lstat to get file info.
        // lstat does NOT follow symlinks, so a symlink to a dir is not S_ISDIR
        if (lstat(full_path, &st) == -1) {
            perror("Error getting file stats");
            fprintf(stderr, "Path: %s\n", full_path);
            continue; // Skip this entry
        }

        // Check if it's a regular file
        if (S_ISREG(st.st_mode)) {
            total_files++;
        } 
        // Check if it's a directory
        else if (S_ISDIR(st.st_mode)) {
            // --- Handle Recursion and Depth ---
            // If max_depth is 0 (unlimited) OR we are not yet at max_depth
            if (max_depth == 0 || current_depth < max_depth) {
                // Recurse into the subdirectory
                long long sub_count = count_files(full_path, current_depth + 1, max_depth);
                
                if (sub_count != -1) {
                    total_files += sub_count;
                }
            }
        }
    }

    closedir(dir);
    return total_files;
}

int main(int argc, char *argv[]) {
    printf("argc: %d\n", argc);

    // printf("Arguments:\n"); DEBUGGING
    for (int i = 0; i < argc; i++) {
        printf("  argv[%d]: %s\n", i, argv[i]);
    }
  

    // --- Default values ---
    char *directory = NULL;
    int max_depth = 1; // Default depth is 1
    char cwd_buffer[PATH_MAX];

    // --- Manual Argument Parsing ---
    for (int i = 1; i < argc; i++) {
        // Check for -d or --depth flag
        if (strcmp(argv[i], "-d") == 0 || strcmp(argv[i], "--depth") == 0) {
            if (i + 1 < argc) { // Make sure there is a value after the flag
                i++; // Move to the next argument (the number)
                max_depth = atoi(argv[i]); // Convert string number to int
                if (max_depth < 0) {
                    fprintf(stderr, "Error: Depth cannot be negative.\n");
                    return EXIT_FAILURE;
                }
            } else {
                fprintf(stderr, "Error: Missing value for %s\n", argv[i]);
                return EXIT_FAILURE;
            }
        } 
        // Check for -h or --help
        else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
             printf("Usage: %s [directory] [-d depth]\n", argv[0]);
             printf("Count files in a directory up to a specified depth.\n");
             printf("\nOptions:\n");
             printf("  directory    Directory to scan (default: current directory)\n");
             printf("  -d, --depth  Max depth to scan. 1=current dir only, 0=unlimited. (default: 1)\n");
             return EXIT_SUCCESS;
        }
        // Check for unknown options
        else if (argv[i][0] == '-') {
            fprintf(stderr, "Error: Unknown option: %s\n", argv[i]);
            return EXIT_FAILURE;
        } 
        // Assume it's the directory path
        else if (directory == NULL) {
            directory = argv[i];
        } 
        // If directory is already set, it's an error
        else {
            fprintf(stderr, "Error: Unexpected argument: %s\n", argv[i]);
            return EXIT_FAILURE;
        }
    }

    // If no directory was provided, use the current working directory
    if (directory == NULL) {
        if (getcwd(cwd_buffer, sizeof(cwd_buffer)) != NULL) {
            directory = cwd_buffer;
        } else {
            perror("Error getting current working directory");
            return EXIT_FAILURE;
        }
    }
    // --- End Argument Parsing ---

    // Call the recursive function, starting at depth 1
    long long count = count_files(directory, 1, max_depth);

    if (count != -1) {
        const char *depth_str = (max_depth == 0) ? "unlimited" : "";
        if (max_depth == 0) {
             printf("Number of files in '%s' (depth: unlimited): %lld\n", directory, count);
        } else {
             printf("Number of files in '%s' (depth: %d): %lld\n", directory, max_depth, count);
        }
    } else {
        // An error message was already printed by a perror call
        return EXIT_FAILURE; // Exit with an error code
    }

    return EXIT_SUCCESS;
}
