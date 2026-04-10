# mys

`mys` is a small personal package manager for this repo. It installs and updates one script at a time from GitHub into `/usr/local/bin`, and tracks its installs in a local TSV registry that acts as the source of truth.

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

- `mys install text_search.py` installs `/usr/local/bin/text_search`
- `mys install compile_with_argparser.sh` installs `/usr/local/bin/compile_with_argparser`

Use `--keep-extension` if you want the original file name preserved.

## Install Flow

`mys` currently:

1. builds a raw GitHub URL from `owner/repo`, branch, and package path
2. downloads only that file
3. prepends a shebang for `.py` and `.sh` if the file does not already have one
4. marks the installed file executable
5. writes it into `/usr/local/bin`
6. records the install in `~/.local/share/mys/registry.tsv`

`mys update <package>` follows the same flow, but it requires the destination command to already exist.

`mys remove <command>` only removes commands that are present in the registry, which prevents accidentally deleting unrelated files from `/usr/local/bin`.

`mys sync` uses the registry to reinstall or refresh every tracked command at its recorded install path.

## Configuration

Defaults:

- repo: `wodoame/cli-scripts`
- branch: `main`
- bin dir: `/usr/local/bin`
- registry path: `~/.local/share/mys/registry.tsv`

You can override repo and branch with environment variables:

- `MYS_REPO`
- `MYS_BRANCH`

If `/usr/local/bin` is not writable for your user, run `mys` with `sudo` or override `--bin-dir`.

Examples:

```bash
mys install text_search.py
mys update text_search.py
mys install linux/dirtree.py --as dirtree-linux
mys list
mys export mys-registry.tsv
mys import mys-registry.tsv
mys sync
mys self-update
mys remove text_search
mys config
```

## Registry Format

The registry is a tab-separated file with these columns:

1. command name
2. package path
3. repo
4. branch
5. installed path

## Moving To Another Machine

On the current machine:

```bash
mys export mys-registry.tsv
```

On the new machine:

```bash
mys import mys-registry.tsv
mys sync
```

`mys import` merges entries by command name by default. Use `mys import --replace ...` if you want the imported registry to fully replace the local one.

## Bootstrapping

To install `mys` itself directly from GitHub:

```bash
sudo curl -fsSL https://raw.githubusercontent.com/wodoame/cli-scripts/main/mys -o /usr/local/bin/mys
sudo chmod +x /usr/local/bin/mys
```

After bootstrapping, update `mys` itself with:

```bash
mys self-update
```
