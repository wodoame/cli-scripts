# mys

`mys` is a small personal package manager for this repo. It installs one script at a time from GitHub into `~/.local/bin`.

## Why Python

Python is the best fit for the first version because it can:

- make HTTP requests with the standard library
- handle file permissions cleanly
- work well with both `.py` and `.sh` scripts in this repo
- stay dependency-free

## Package Naming

The package name is the relative file path in the GitHub repo:

- `mys install text_search.py`
- `mys install compile_with_argparser.sh`
- `mys install linux/dirtree.py`

By default, `mys` removes `.py` and `.sh` from the installed command name:

- `mys install text_search.py` installs `~/.local/bin/text_search`
- `mys install compile_with_argparser.sh` installs `~/.local/bin/compile_with_argparser`

Use `--keep-extension` if you want the original file name preserved.

## Install Flow

`mys` currently:

1. builds a raw GitHub URL from `owner/repo`, branch, and package path
2. downloads only that file
3. prepends a shebang for `.py` and `.sh` if the file does not already have one
4. marks the installed file executable
5. writes it into `~/.local/bin`

## Configuration

Defaults:

- repo: `wodoame/cli-scripts`
- branch: `main`
- bin dir: `~/.local/bin`

You can override repo and branch with environment variables:

- `MYS_REPO`
- `MYS_BRANCH`

Examples:

```bash
mys install text_search.py
mys install linux/dirtree.py --as dirtree-linux
mys remove text_search
mys config
```

## Bootstrapping

To install `mys` itself:

```bash
install -Dm755 ./mys ~/.local/bin/mys
```
