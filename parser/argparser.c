#include "argparser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// This helper function is UNCHANGED.
// It finds single options like -f, --file, but fails on -vcf
static ArgDefinition *find_def(const char *arg, ArgDefinition defs[],
                               int def_count) {
  for (int i = 0; i < def_count; i++) {
    if (defs[i].type == ARG_POSITIONAL)
      continue;
    if (strncmp(arg, "--", 2) == 0) {
      if (defs[i].long_opt && strcmp(arg + 2, defs[i].long_opt) == 0) {
        return &defs[i];
      }
    } else if (strncmp(arg, "-", 1) == 0) {
      // This arg[2] == '\0' check is what makes it fail for "-vcf"
      if (defs[i].short_opt && arg[1] == defs[i].short_opt && arg[2] == '\0') {
        return &defs[i];
      }
    }
  }
  return NULL;
}

// The main parsing function
int parse_arguments(int argc, char *argv[], ArgDefinition defs[],
                    int def_count) {

  int positional_count = 0;

  for (int i = 1; i < argc; i++) {
    const char *arg = argv[i];

    if (strcmp(arg, "--help") == 0 || strcmp(arg, "-h") == 0) {
      print_help(argv[0], defs, def_count);
      exit(0);
    }

    ArgDefinition *def = find_def(arg, defs, def_count);

    if (def) {
      // --- Case 1: It's a KNOWN single option (e.g., -f, --file, -v) ---
      switch (def->type) {
      case ARG_FLAG:
        *(bool *)(def->value_ptr) = true;
        break;
      case ARG_STRING:
      case ARG_INT:
        if (i + 1 >= argc) {
          fprintf(stderr, "Error: Option '%s' requires a value.\n", arg);
          return -1;
        }
        i++;
        const char *value_str = argv[i];
        if (def->type == ARG_STRING) {
          *(const char **)(def->value_ptr) = value_str;
        } else {
          *(int *)(def->value_ptr) = atoi(value_str);
        }
        break;
      case ARG_POSITIONAL:
        break; // Should not be reached
      }
    }
    // --- NEW LOGIC FOR COMBINED FLAGS ---
    else if (arg[0] == '-' && arg[1] != '-' && arg[2] != '\0') {
      // --- Case 2: It's a combined short flag group (e.g., -vcf) ---
      // arg[1] != '-' ensures it's not a long option
      // arg[2] != '\0' ensures it has multiple characters

      for (int j = 1; arg[j] != '\0'; j++) {
        char opt_char = arg[j];
        ArgDefinition *char_def = NULL;

        // Find the definition for this single character
        for (int k = 0; k < def_count; k++) {
          if (defs[k].short_opt == opt_char) {
            char_def = &defs[k];
            break;
          }
        }

        if (!char_def) {
          fprintf(stderr, "Error: Unknown short option '-%c' in group '%s'\n",
                  opt_char, arg);
          return -1;
        }

        // For this simple parser, combined flags *must* be ARG_FLAG
        if (char_def->type == ARG_FLAG) {
          *(bool *)(char_def->value_ptr) = true;
        } else {
          // e.g., User wrote -vcf but 'f' needs a value.
          fprintf(stderr,
                  "Error: Option '-%c' in group '%s' requires a value and "
                  "cannot be combined.\n",
                  opt_char, arg);
          return -1;
        }
      }
    }
    // --- END NEW LOGIC ---
    else if (arg[0] == '-') {
      // --- Case 3: It's an unknown single option (e.g., -z) or long option
      fprintf(stderr, "Error: Unknown option '%s'\n", arg);
      return -1;
    } else {
      // --- Case 4: It's a POSITIONAL ARGUMENT ---
      (void)positional_count; // This line is just to use the variable

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
        *(const char **)(positional_def->value_ptr) = arg;
        positional_count++;
      } else {
        fprintf(stderr, "Error: Unexpected positional argument '%s'\n", arg);
        return -1;
      }
    }
  }
  return 0; // Success
}

// This function is UNCHANGED
void print_help(const char *program_name, ArgDefinition defs[], int def_count) {
  // --- Build the Usage line ---
  printf("Usage: %s [options]", program_name);
  for (int i = 0; i < def_count; i++) {
    if (defs[i].type == ARG_POSITIONAL) {
      printf(" <%s>", defs[i].long_opt ? defs[i].long_opt : "arg");
    }
  }
  printf("\n\n");

  // --- Print Options ---
  printf("Options:\n");
  for (int i = 0; i < def_count; i++) {
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
      const char *name = defs[i].long_opt ? defs[i].long_opt : "arg";
      printf("  %-18s %s\n", name, defs[i].description);
    }
  }
}
