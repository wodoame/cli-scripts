# cli-scripts

This repo contains small personal CLI utilities and setup scripts.

## Tools

- `gh-ssh`: Generate GitHub SSH keys and add/update a matching SSH alias in `~/.ssh/config`. See [docs/gh-ssh.md](docs/gh-ssh.md).
- `mys`: Install and update one script at a time from GitHub into `/usr/local/bin`. See [#mys](#mys) below.
- `diff.py`: Compare package requirements files. See [docs/diff.md](docs/diff.md).
- `dirtree.py`: Print a directory tree. See [docs/dirtree.md](docs/dirtree.md).

## mys

`mys` is a small personal package manager for this repo. It installs and updates one script at a time from GitHub into `/usr/local/bin`, and tracks its installs in a local TSV registry that acts as the source of truth.

## Installation

> **Note:** `mys` relies on standard library features and requires **Python 3.8+** to be installed on your system.

To install `mys` itself directly from GitHub natively on **Unix/Linux**:

```bash
sudo curl -fsSL https://raw.githubusercontent.com/wodoame/cli-scripts/main/mys -o /usr/local/bin/mys
sudo chmod +x /usr/local/bin/mys
```

If you are using **Windows (Git Bash)**, you can safely install it into your user profile without elevated privileges. You'll also want to update the shebang to use `py`, as that is the standard Python launcher executable on Windows:

```bash
mkdir -p ~/bin
curl -fsSL https://raw.githubusercontent.com/wodoame/cli-scripts/main/mys -o ~/bin/mys
sed -i '1s|.*|#!/usr/bin/env py|' ~/bin/mys
```

After installing, you can update `mys` natively with:

```bash
mys self-update
```

## Why Python

Python is the best fit for the first version because it can:

- make HTTP requests with the standard library
- handle file permissions cleanly
- work well with `.py` and `.sh` scripts in this repo
- stay dependency-free

## Package Naming

The package name is the relative file path in the GitHub repo:

- `mys install gh-ssh`
- `mys install renamer.sh`
- `mys install diff.py`
- `mys install dirtree.py`

By default, `mys` removes `.py` and `.sh` from the installed command name:

- `mys install diff.py` installs `/usr/local/bin/diff`
- `mys install renamer.sh` installs `/usr/local/bin/renamer`
- `mys install dirtree.py` installs `/usr/local/bin/dirtree`

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
mys install gh-ssh
mys update gh-ssh
mys install dirtree.py --as dirtree-cli
mys deps gh-ssh
mys changelog gh-ssh
mys list
mys export mys-registry.tsv
mys import mys-registry.tsv
mys sync
mys self-update
mys remove text_search
mys config
```

## Versioning

Installing with no `@` suffix installs the latest released version:

```bash
mys install gh-ssh
```

`mys` resolves it by downloading `versions.tsv` from the repo root (on the default branch) and
looking up the package's current released version there. The resolved version is then pinned
in the registry as the git tag `{package_path}-{version}` (e.g. `gh-ssh-1.0.1`) — it does not
keep tracking future releases, so re-run `mys update gh-ssh` to pick up a newer release later.
`gh-ssh@latest` is still accepted and means the same thing, except that it fails if the script
has no release.

If the script has no row in `versions.tsv` (or the repo has no `versions.tsv`), `mys` falls
back to the default branch HEAD.

Pin an install to a specific tagged version by appending `@version` to the package path:

```bash
mys install gh-ssh@1.0.1
mys url gh-ssh@1.0.1
```

To install straight off a branch HEAD instead, which may be ahead of the latest tagged
release, pass `--branch` explicitly:

```bash
mys --branch main install gh-ssh
```

`versions.tsv` is a two-column TSV mapping package path to its latest released version, e.g.:

```
gh-ssh	1.0.1
mys	1.1.0
```

### Changelogs

Each script has its own changelog at `changelogs/{package_path}.md`, newest version first,
with an `## Unreleased` section at the top:

```markdown
# gh-ssh

## Unreleased

### Added
- `gh-ssh rotate` replaces an existing key.

## 1.0.1 - 2026-06-27

### Added
- `--version` flag.
```

When you change a script, add a line under `## Unreleased` in the same commit. Group lines
under `### Added`, `### Changed`, `### Fixed` or `### Removed` when that helps.

Read a script's changelog from the terminal with `mys changelog`. It downloads the file from
the default branch, leaves out `## Unreleased`, and marks the version you have installed:

```bash
mys changelog gh-ssh          # every released version, newest first
mys changelog gh-ssh@1.0.1    # one release
mys changelog gh-ssh@latest   # the newest release
mys changelog gh-ssh --new    # only releases newer than the installed one
```

### Cutting a release

Commit the script's changes and its changelog notes first, then run `scripts/release.sh` with
the package path and either an explicit version or `major`, `minor` or `patch`:

```bash
scripts/release.sh gh-ssh patch
scripts/release.sh mys 1.2.0
```

It bumps the script's `VERSION` marker (if it has one), updates the package's row in
`versions.tsv`, and moves the notes under `## Unreleased` to a new
`## {version} - {date}` section, leaving `## Unreleased` empty for next time. It commits
those as `chore: release {package_path} {version}`, tags that commit as
`{package_path}-{version}`, then pushes the commit and tag together.

It refuses to run with uncommitted changes, an existing tag, a branch that is behind its
remote, or nothing under `## Unreleased`.

Use `--dry-run` to see what a release would do, `--no-push` to commit and tag locally without
pushing, or `--no-changelog` to release without changelog notes.

`mys` itself is versioned the same way. Check the installed version with:

```bash
mys --version
```

`mys self-update` updates to the latest released version. Pass a version to pin the update to
a specific release, or `--branch` to update from a branch HEAD:

```bash
mys self-update
mys self-update 1.0.0
mys --branch main self-update
```

## Dependencies

A script declares the other scripts it needs in a header comment, within its first 30 lines:

```bash
#!/usr/bin/env bash
# mys-requires: gh-ssh, dirtree.py@1.0.0
```

Each entry is a package path, as you would pass to `mys install`. A bare path means the latest
released version and `@version` pins one. Entries are separated by commas or spaces, and the
line can be repeated. Use `//` instead of `#` in `.mjs` scripts. Dependencies come from the
same repo as the script that declares them.

`mys install` reads the header after downloading a script and installs every dependency that
is not installed yet, following the dependencies of dependencies too:

```bash
mys install app.sh
# Installed lib.sh as /usr/local/bin/lib (required by app.sh)
# Installed app.sh as /usr/local/bin/app
```

- Everything is downloaded before anything is written, so if one dependency cannot be fetched
  nothing is installed.
- A dependency that is already installed is left alone, even if the header asks for a
  different version; `mys` prints a note in that case.
- Dependencies are installed under their default command name, into the same directory as
  the script that needs them, and are tracked in the registry like any other install.
- `mys update` and `mys sync` also install dependencies that are missing, but never update
  ones that are already there.
- `mys remove` refuses to remove a command that another installed script requires. Pass
  `--force` to remove it anyway. Removing a script does not remove its dependencies.

Print the dependency tree of a package, with the ref each one resolves to:

```bash
mys deps app.sh
# app.sh (app.sh-1.0.0)
#   lib.sh (lib.sh-2.0.0) [installed]
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

## Shell Completion

A bash completion script is included at `completions/mys.bash`. It completes commands, flags, and — for `mys remove` — dynamically reads installed command names from the registry.

Install it for your user (no `.bashrc` edit needed; bash-completion 2.x sources this directory automatically):

```bash
mkdir -p ~/.local/share/bash-completion/completions
curl -fsSL https://raw.githubusercontent.com/wodoame/cli-scripts/main/completions/mys.bash \
     -o ~/.local/share/bash-completion/completions/mys
```

Open a new shell and tab completion is active.
