#include "../parser/argparser.h"
#include <dirent.h>   // For opendir, readdir, closedir, struct dirent
#include <limits.h>   // For PATH_MAX (max path length)
#include <stdio.h>    // For printf, snprintf, fprintf, stderr
#include <stdlib.h>   // For atoi, EXIT_SUCCESS, EXIT_FAILURE
#include <string.h>   // For strcmp
#include <sys/stat.h> // For lstat, struct stat, S_ISREG, S_ISDIR
#include <unistd.h>   // For getcwd
/**
 * @brief Recursively counts files in a directory up to a specified depth.
 *
 * @param base_path The path to the directory to scan.
 * @param current_depth The depth of the current call (1 for the
 * start)#!/usr/bin/env python3
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
    int len = snprintf(full_path, sizeof(full_path), "%s/%s", base_path,
                       entry->d_name);

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
        long long sub_count =
            count_files(full_path, current_depth + 1, max_depth);

        if (sub_count != -1) {
          total_files += sub_count;
        }
      }
    }
  }

  closedir(dir);
  return total_files;
}

typedef struct {
  char *directory;
  int depth;
} AppConfig;

static void debug(int argc, char *argv[], int def_count, AppConfig config) {
  // printf("result: %d\n", result);
  printf("argc: %d\n", argc);

  // printf("Arguments:\n"); DEBUGGING
  for (int i = 0; i < argc; i++) {
    printf("argv[%d]: %s\n", i, argv[i]);
  }

  printf("Configured directory: %s\n", config.directory); // DEBUGGING
  printf("Configured depth: %d\n", config.depth);         // DEBUGGING
}

int main(int argc, char *argv[]) {
  // Task: Replace the manual argument parsing with the argparser library
  AppConfig config = {.directory = ".", .depth = 1};
  ArgDefinition defs[] = {
      {'d', "depth", ARG_INT, &config.depth,
       "  -d, --depth  Max depth to scan. 1=current dir "
       "only, 0=unlimited. (default: 1)\n"},
      {0, "directory", ARG_POSITIONAL, &config.directory,
       "Directory to scan (default: current directory)\n"},
  };
  int defs_count = sizeof(defs) / sizeof(defs[0]);
  int result = parse_arguments(argc, argv, defs, defs_count);
  if (result != 0) {
    // Parsing failed, error message already printed
    return EXIT_FAILURE;
  }

  // --- Default values ---
  char *directory = config.directory;
  int max_depth = config.depth; // Default depth is 1
  char cwd_buffer[PATH_MAX];

  // debug(argc, argv, defs_count, config); // DEBUGGING

  long long count = count_files(directory, 1, max_depth);
  if (count != -1) {
    const char *depth_str = (max_depth == 0) ? "unlimited" : "";
    if (max_depth == 0) {
      printf("Number of files in '%s' (depth: unlimited): %lld\n", directory,
             count);
    } else {
      printf("Number of files in '%s' (depth: %d): %lld\n", directory,
             max_depth, count);
    }
  } else {
    // An error message was already printed by a perror call
    return EXIT_FAILURE; // Exit with an error code
  }

  return EXIT_SUCCESS;
}
