# argparser

A small ANSI C helper for parsing command-line options, intended for the utilities in this repository. It supports short and long options, combined short flags (e.g. `-abc`), string and integer values, and positional arguments.

## Quick start

```c
#include "parser/argparser.h"

int main(int argc, char *argv[]) {
    bool verbose = false;
    const char *output = NULL;
    int repeat = 1;
    const char *input_path = NULL;

    ArgDefinition defs[] = {
        {.short_opt = 'v', .long_opt = "verbose", .type = ARG_FLAG, .value_ptr = &verbose,
         .description = "Turn on verbose logging"},
        {.short_opt = 'o', .long_opt = "output", .type = ARG_STRING, .value_ptr = &output,
         .description = "Write results to this file"},
        {.short_opt = 'r', .long_opt = "repeat", .type = ARG_INT, .value_ptr = &repeat,
         .description = "Repeat count"},
        {.short_opt = 0, .long_opt = "input", .type = ARG_POSITIONAL, .value_ptr = &input_path,
         .description = "Input file"},
    };

    if (parse_arguments(argc, argv, defs, sizeof(defs) / sizeof(defs[0])) != 0) {
        return 1; // parse_arguments already prints the error message
    }

    /* Use parsed values here */
    return 0;
}
```

Compile the code together with `parser/argparser.c` and include `parser/argparser.h` in the translation unit that defines your `ArgDefinition` array.

## Defining arguments

Each entry in the `ArgDefinition` array describes a single expected argument:

- `short_opt`: Single-character short option (e.g. `'v'`). Use `0` for positional arguments.
- `long_opt`: Long option name without the leading dashes (e.g. `"verbose"`). For positional arguments, use a friendly name such as `"input"`.
- `type`: One of `ARG_FLAG`, `ARG_STRING`, `ARG_INT`, or `ARG_POSITIONAL`.
- `value_ptr`: Pointer to the variable that should receive the parsed value. Provide addresses of the right type:
  - `bool*` for `ARG_FLAG`
  - `const char**` for `ARG_STRING` and `ARG_POSITIONAL`
  - `int*` for `ARG_INT`
- `description`: Short help string shown by `print_help()` and when the user requests `--help` or `-h`.

## Parsing behaviour

- `parse_arguments()` iterates the command line and updates the variables you supplied via `value_ptr`.
- Flag options (`ARG_FLAG`) become `true` when present.
- String and integer options consume the next argument. Missing values cause an error message and a `-1` return code.
- Positional arguments are matched in the order they appear in the `defs` array. Extra positional tokens trigger an error.
- Combined short flags (e.g. `-xzv`) are supported as long as every member of the bundle is declared as `ARG_FLAG`.
- Unknown options print an error message and return `-1`.
- If the user passes `-h` or `--help`, `parse_arguments()` prints the help text and exits the program with status `0`.

Always check the return value of `parse_arguments()` before using the parsed data. Treat a non-zero result as a fatal condition for your tool.

## Help output

Call `print_help(argv[0], defs, def_count)` when you want to show usage information explicitly. The helper constructs a usage line, lists options, and then positional arguments using the descriptions you provided.

Example output:

```text
Usage: mytool [options] <input>

Options:
  -v, --verbose       Turn on verbose logging
  -o, --output        Write results to this file
  -r, --repeat        Repeat count

Arguments:
  input               Input file
```

## Error handling and exit codes

- `parse_arguments()` prints context-aware error messages to `stderr` for unknown options, missing values, and unexpected positionals.
- On error the function returns `-1`; leave the exit logic to your caller so the tool can decide the final status code.
- The function does not allocate memory, so there is nothing to clean up on failure.

## Notes and limitations

- The parser does not support short options that take attached values (`-ofile`) or long options with inline equals (`--output=path`). Supply values as separate tokens (`-o file`, `--output file`).
- Combined short option groups must contain only `ARG_FLAG` definitions.
- Positional arguments are assigned in the order defined and cannot be optional; if you need optional positionals, add custom validation after parsing.

With these conventions in place you can reuse `argparser.c` across the C-based utilities in this repository.

## Full example

```c
#include <stdbool.h>
#include <stdio.h>
#include "parser/argparser.h"

typedef struct {
  bool verbose;
  bool force;
  bool create;
  const char *output_file;
} AppConfig;

int main(int argc, char *argv[]) {
  AppConfig config = {
    .verbose = false,
    .force = false,
    .create = false,
    .output_file = NULL,
  };

  ArgDefinition definitions[] = {
    {'v', "verbose", ARG_FLAG, &config.verbose, "Enable verbose output"},
    {'f', "force", ARG_FLAG, &config.force, "Force operation"},
    {'c', "create", ARG_FLAG, &config.create, "Create new file"},
    {'o', "output", ARG_STRING, &config.output_file, "Specify output file"},
  };

  int def_count = sizeof(definitions) / sizeof(definitions[0]);

  if (parse_arguments(argc, argv, definitions, def_count) != 0) {
    fprintf(stderr, "Try '%s --help' for more information.\n", argv[0]);
    return 1;
  }

  printf("Parsing complete! Here's the config:\n");
  printf("  Verbose:     %s\n", config.verbose ? "true" : "false");
  printf("  Force:       %s\n", config.force ? "true" : "false");
  printf("  Create:      %s\n", config.create ? "true" : "false");
  printf("  Output File: %s\n",
       config.output_file ? config.output_file : "(not set)");

  return 0;
}
```

## Building

- Place your source file alongside the repository or update the include path so the compiler sees `parser/argparser.h`.
- Compile both your source file and `parser/argparser.c`. A minimal command using GCC and the repo's layout looks like this:

  ```bash
  gcc -std=c99 -I. example.c parser/argparser.c -o example
  ```

- Adjust include flags (`-I`) and library paths to match your project structure. Link the resulting binary as usual for your build system.
