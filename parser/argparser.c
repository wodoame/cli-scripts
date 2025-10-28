#include "argparser.h"
#include <stdio.h>  // For printf, fprintf, stderr
#include <stdlib.h> // For atoi, exit
#include <string.h> // For strcmp, strncmp

// A private helper function to find an option definition by name
static ArgDefinition *find_def(const char *arg, ArgDefinition defs[],
                               int def_count) {
  for (int i = 0; i < def_count; i++) {
    // Skip positional definitions
    if (defs[i].type == ARG_POSITIONAL)
      continue;

    // Check for long option, e.g., --verbose
    if (strncmp(arg, "--", 2) == 0) {
      if (defs[i].long_opt && strcmp(arg + 2, defs[i].long_opt) == 0) {
        return &defs[i];
      }
    }
    // Check for short option, e.g., -v
    else if (strncmp(arg, "-", 1) == 0) {
      if (defs[i].short_opt && arg[1] == defs[i].short_opt && arg[2] == '\0') {
        return &defs[i];
      }
    }
  }
  return NULL; // Not found
}

// The main parsing function
int parse_arguments(int argc, char *argv[], ArgDefinition defs[],
                    int def_count) {

  // Track how many positional args we've found so far
  int positional_count = 0;

  // Start at 1 to skip the program name (argv[0])
  for (int i = 1; i < argc; i++) {
    const char *arg = argv[i];

    // --- Handle Help ---
    if (strcmp(arg, "--help") == 0 || strcmp(arg, "-h") == 0) {
      print_help(argv[0], defs, def_count);
      exit(0); // Exit after printing help
    }

    // --- Find the matching definition ---
    ArgDefinition *def = find_def(arg, defs, def_count);

    if (def) {
      // --- Case 1: It's an OPTION (e.g., -f or --file) ---
      switch (def->type) {
      case ARG_FLAG:
        // It's a flag, just set the bool to true
        *(bool *)(def->value_ptr) = true;
        break;

      case ARG_STRING:
      case ARG_INT:
        // These types need a value, so check for the next argument
        if (i + 1 >= argc) {
          fprintf(stderr, "Error: Option '%s' requires a value.\n", arg);
          return -1;
        }

        // Move to the next argument (the value)
        i++;
        const char *value_str = argv[i];

        if (def->type == ARG_STRING) {
          // Store the pointer to the string
          *(const char **)(def->value_ptr) = value_str;
        } else {
          // Convert to int and store
          *(int *)(def->value_ptr) = atoi(value_str);
        }
        break;
      case ARG_POSITIONAL:
        // This case is handled by find_def, should not be reached
        break;
      }
    } else if (arg[0] == '-') {
      // --- Case 2: It starts with '-' but wasn't found ---
      fprintf(stderr, "Error: Unknown option '%s'\n", arg);
      return -1;
    } else {
      // --- Case 3: It's a POSITIONAL ARGUMENT ---

      // Find the *next* available positional definition
      ArgDefinition *positional_def = NULL;
      int current_pos_idx = 0;
      for (int j = 0; j < def_count; j++) {
        if (defs[j].type == ARG_POSITIONAL) {
          if (current_pos_idx == positional_count) {
            positional_def = &defs[j];
            break;
          }
          current_pos_idx++;
        }
      }

      if (positional_def) {
        // We found the Nth positional arg definition.
        // We'll assume positional args are always strings for simplicity.
        *(const char **)(positional_def->value_ptr) = arg;
        positional_count++;
      } else {
        // User provided more positional args than we expected
        fprintf(stderr, "Error: Unexpected positional argument '%s'\n", arg);
        return -1;
      }
    }
  }
  return 0; // Success
}

// Implementation for the help printer
void print_help(const char *program_name, ArgDefinition defs[], int def_count) {
  // --- Build the Usage line ---
  printf("Usage: %s [options]", program_name);
  for (int i = 0; i < def_count; i++) {
    if (defs[i].type == ARG_POSITIONAL) {
      // Use long_opt as the placeholder name, e.g., <input>
      printf(" <%s>", defs[i].long_opt ? defs[i].long_opt : "arg");
    }
  }
  printf("\n\n");

  // --- Print Options ---
  printf("Options:\n");
  for (int i = 0; i < def_count; i++) {
    // Skip positional args, we'll print them later
    if (defs[i].type == ARG_POSITIONAL)
      continue;

    char opt_buf[64];
    snprintf(opt_buf, sizeof(opt_buf), "  -%c, --%s",
             defs[i].short_opt ? defs[i].short_opt : ' ',
             defs[i].long_opt ? defs[i].long_opt : "");

    printf("%-20s %s\n", opt_buf, defs[i].description);
  }

  // --- Print Positional Arguments ---
  printf("\nArguments:\n");
  for (int i = 0; i < def_count; i++) {
    if (defs[i].type == ARG_POSITIONAL) {
      // Use long_opt as the name
      const char *name = defs[i].long_opt ? defs[i].long_opt : "arg";
      printf("  %-18s %s\n", name, defs[i].description);
    }
  }
}
