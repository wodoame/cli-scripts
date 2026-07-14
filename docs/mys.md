# mys

`mys` is a small personal package manager for this repo. It installs and updates one script at a time from GitHub into `/usr/local/bin`, and tracks its installs in a local TSV registry that acts as the source of truth.

## Why Python

Python is the best fit for the first version because it can:

- make HTTP requests with the standard library
- handle file permissions cleanly
- work well with `.py`, `.sh`, and `.mjs` scripts in this repo
- stay dependency-free

## Package Naming

The package name is the relative file path in the GitHub repo:

- `mys install text_search.py`
- `mys install compile_with_argparser.sh`
- `mys install linux/dirtree.py`
- `mys install schema.mjs`

By default, `mys` removes `.py`, `.sh`, and `.mjs` from the installed command name:

- `mys install text_search.py` installs `/usr/local/bin/text_search`
- `mys install compile_with_argparser.sh` installs `/usr/local/bin/compile_with_argparser`
- `mys install schema.mjs` installs `/usr/local/bin/schema`

Use `--keep-extension` if you want the original file name preserved.

## Install Flow

`mys` currently:

1. builds a raw GitHub URL from `owner/repo`, branch, and package path
2. downloads only that file
3. prepends a shebang for `.py`, `.sh`, and `.mjs` if the file does not already have one
4. marks the installed file executable
5. writes it into `/usr/local/bin`
6. records the install in `~/.local/share/mys/registry.tsv`

`mys update <package>` follows the same flow, but it requires the destination command to already exist.

`mys remove <command>` only removes commands that are present in the registry, which prevents accidentally deleting unrelated files from `/usr/local/bin`.

`mys sync` uses the registry to reinstall or refresh every tracked command at its recorded install path.

## Configuration

`mys` can persist its defaults in `~/.config/mys/config.tsv`.

Defaults:

- repo: `wodoame/cli-scripts`
- branch: `main`
- bin dir: `/usr/local/bin`
- registry path: `~/.local/share/mys/registry.tsv`
- config path: `~/.config/mys/config.tsv`

Runtime precedence is:

1. built-in defaults
2. config file
3. environment variables
4. CLI flags

You can override config values with environment variables:

- `MYS_REPO`
- `MYS_BRANCH`
- `MYS_BIN_DIR`
- `MYS_REGISTRY_PATH`
- `MYS_CONFIG_PATH`

If `/usr/local/bin` is not writable for your user, run `mys` with `sudo` or override `--bin-dir`.

To persist new defaults for later runs:

```bash
mys config --repo wodoame/cli-scripts --branch main
mys config --bin-dir ~/bin --registry-path ~/.local/share/mys/registry.tsv
```

Running `mys config` without extra flags prints the active values.

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

## Versioning

Pin an install to a specific tagged version by appending `@version` to the package path:

```bash
mys install gh-ssh@1.0.1
mys url gh-ssh@1.0.1
```

This resolves to the git tag `{package_path}-{version}` (e.g. `gh-ssh-1.0.1`) and downloads
the file from that ref instead of the default branch.

Append `@latest` to install the newest released version without knowing its exact number:

```bash
mys install gh-ssh@latest
```

`mys` resolves `@latest` by downloading `versions.tsv` from the repo root (on the default
branch) and looking up the package's current released version there. The resolved version is
then pinned in the registry exactly like an explicit `@version` — it does not keep tracking
future releases, so re-run `mys update gh-ssh@latest` to pick up a newer release later.

Installing with no `@` suffix at all (e.g. `mys install gh-ssh`) keeps installing straight off
the default branch HEAD, which may be ahead of the latest tagged release.

`versions.tsv` is a two-column TSV mapping package path to its latest released version, e.g.:

```
gh-ssh	1.0.1
```

When cutting a release for a script: bump any in-script version marker, commit, tag the commit
as `{package_path}-{version}`, update that package's row in `versions.tsv` in the same commit,
then push the commit and tag.

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

## Shell Completion

A bash completion script is included at `completions/mys.bash`. It completes commands, flags, and — for `mys remove` — dynamically reads installed command names from the registry.

Install it for your user (no `.bashrc` edit needed; bash-completion 2.x sources this directory automatically):

```bash
mkdir -p ~/.local/share/bash-completion/completions
curl -fsSL https://raw.githubusercontent.com/wodoame/cli-scripts/main/completions/mys.bash \
     -o ~/.local/share/bash-completion/completions/mys
```

Open a new shell and tab completion is active.

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
