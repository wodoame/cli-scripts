#ifndef ARG_PARSER_H
#define ARG_PARSER_H

#include <stdbool.h> // For bool type

/*
 * @brief Defines the type of an argument.
 */
typedef enum {
  ARG_FLAG,      // A simple flag, e.g., --verbose
  ARG_STRING,    // An option that takes a string, e.g., --file <name>
  ARG_INT,       // An option that takes an integer, e.g., --count <num>
  ARG_POSITIONAL // A positional argument, e.g., <input_file>
} ArgType;

/*
 * @brief Defines a single expected argument.
 */
typedef struct {
  char short_opt;          // 'v' (use 0 for positional)
  const char *long_opt;    // "verbose" (use name like "input" for positional)
  ArgType type;            // The type of argument
  void *value_ptr;         // A pointer to the variable this arg should update
  const char *description; // A description for the help message
} ArgDefinition;

/**
 * @brief Parses the command-line arguments.
 *
 * @param argc The argument count from main().
 * @param argv The argument vector from main().
 * @param defs An array of argument definitions.
 * @param def_count The number of items in the defs array.
 * @return 0 on success, -1 on failure (e.g., unknown option).
 */
int parse_arguments(int argc, char *argv[], ArgDefinition defs[],
                    int def_count);

/**
 * @brief A helper to print a formatted help message.
 */
void print_help(const char *program_name, ArgDefinition defs[], int def_count);

#endif // ARG_PARSER_H
