# Making a repo compatible with mys

`mys` can install scripts from any GitHub repo, not only `wodoame/cli-scripts`. This guide
lists what a repo has to provide for that to work.

Only the first section is required. Versions, dependencies and changelogs are opt-in: a repo
that skips them still installs, it just installs from the branch HEAD with no extras.

| Feature | What the repo provides | Needed for |
| --- | --- | --- |
| [Installable scripts](#1-installable-scripts-required) | Public GitHub repo with single-file scripts | `mys install`, `update`, `sync`, `url` |
| [Versions](#2-versions-optional) | `versions.tsv` and a git tag per release | Latest-release installs, `@version`, `@latest` |
| [Dependencies](#3-dependencies-optional) | A `mys-requires:` header in the script | Automatic install of required scripts, `mys deps` |
| [Changelogs](#4-changelogs-optional) | `changelogs/{package_path}.md` | `mys changelog` |

Throughout this guide, a **package path** is the script's path relative to the repo root, for
example `gh-ssh` or `linux/dirtree.py`. It is what users pass to `mys install`.

## 1. Installable scripts (required)

### The repo

- **Hosted on GitHub and public.** `mys` downloads each file from
  `https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{package_path}` without
  authentication, so private repos and other hosts do not work.
- **Default branch named `main`.** `mys` looks on `main` unless the user has configured
  another branch. If your default branch has a different name, tell your users to run
  `mys config --branch <name>` (see [Pointing mys at the repo](#pointing-mys-at-the-repo)).

### Each script

- **One self-contained file.** `mys` downloads exactly one file per package and nothing else
  from the repo. A script cannot import a sibling module or read a data file that sits next
  to it. If it needs another script, declare it as a [dependency](#3-dependencies-optional)
  and call it as a command.
- **No third-party packages are installed.** `mys` does not run `pip`, `npm` or anything
  similar. Stick to the standard library, or document what the user must install.
- **A known extension, or its own shebang.** `mys` handles the shebang for these extensions:

  | Extension | Interpreter | Shebang handling |
  | --- | --- | --- |
  | `.py` | `python3` (or `python` / `py`) | Added if missing; an existing Python shebang is rewritten to the interpreter found on the user's machine |
  | `.sh` | `bash` | Added if missing |
  | `.mjs` | `node` | Added if missing |
  | anything else, or none | — | Left untouched, so the file must start with its own `#!` line |

- **A sensible file name.** The installed command is the file name with a `.py`, `.sh` or
  `.mjs` extension removed: `tools/text_search.py` installs as `text_search`. Two scripts
  that reduce to the same command name collide, so keep names unique across the repo.
- **No `@` in the path.** `mys` treats everything after `@` as a version.

`mys` marks the installed file executable, so the file mode in the repo does not matter.

### Pointing mys at the repo

Users choose the repo per command or persist it:

```bash
mys --repo owner/name install tool.sh
```

```bash
mys config --repo owner/name
```

The registry records the repo for every installed command, so `mys sync` and `mys list` keep
working when commands come from several repos.

If the default branch is not `main`, users should persist it with `mys config --branch <name>`
(or the `MYS_BRANCH` environment variable). Passing `--branch` on the command line is
different: it means "install this branch's HEAD" and skips the latest-release lookup.

## 2. Versions (optional)

Without this section, `mys install tool.sh` installs the file from the default branch HEAD.
With it, the same command installs the latest release, and users can pin one with
`tool.sh@1.2.0`.

### A git tag per release

Each release of a script is a git tag named `{package_path}-{version}`, pointing at the
commit that holds that version of the file:

| Package path | Version | Tag |
| --- | --- | --- |
| `gh-ssh` | `1.0.1` | `gh-ssh-1.0.1` |
| `linux/dirtree.py` | `1.0.0` | `linux/dirtree.py-1.0.0` |

Scripts are versioned independently, so a repo has one series of tags per script. The tag
must be pushed; a local tag is invisible to `mys`.

`mys` does not interpret the version string, so any format works as long as the tag matches.
`X.Y.Z` is recommended. Do not use `latest` as a version: `mys` reserves it.

A tag alone is enough for `mys install tool.sh@1.2.0`.

### `versions.tsv`

To make a bare `mys install tool.sh` (and `@latest`) resolve to the newest release, add a
`versions.tsv` file at the repo root, on the default branch:

```
gh-ssh	1.0.1
linux/dirtree.py	1.0.0
```

- One line per released script: package path, a **tab**, the latest released version.
- Exactly two columns. `mys` ignores any line with a different number of columns, and that
  script is then treated as unreleased.
- No header line.
- Every version listed must have a matching pushed tag, or installs of that script fail.

A script with no line in `versions.tsv` installs from the default branch HEAD.

### Releasing

A release is three things that must agree: the file contents at the tagged commit, the tag,
and the line in `versions.tsv`. Do them in one commit and push the commit and tag together:

1. Update the script's line in `versions.tsv` (and any version string inside the script).
2. Commit.
3. Tag that commit `{package_path}-{version}`.
4. Push the branch and the tag.

`scripts/release.sh` in `wodoame/cli-scripts` automates these steps and can be copied into
another repo. It expects the in-script version to be a top-level `VERSION="1.2.3"` (bash) or
`VERSION = "1.2.3"` (Python) line. That marker is a convention of the release script only;
`mys` never reads it.

GitHub caches raw files for a few minutes, so a new line in `versions.tsv` can take up to
about five minutes to be seen by `mys`.

## 3. Dependencies (optional)

A script declares the other scripts it needs in a comment within its first 30 lines:

```bash
#!/usr/bin/env bash
# mys-requires: setup-react.sh, gh-ssh@1.0.1
```

- **Syntax:** `# mys-requires:` followed by package paths separated by commas or spaces. Use
  `// mys-requires:` in `.mjs` files. The line may be repeated.
- **Versions:** a bare path means the latest release; `@version` pins one.
- **Same repo only.** Dependencies are fetched from the repo the script itself came from.
- **Default command names.** A dependency is installed under its default command name
  (extension removed), so call it by that name in the script, e.g. `setup-react`.
- **Lines after the 30th are not scanned**, so keep the header near the top.

`mys install` then installs every missing dependency, including dependencies of
dependencies, before the script itself. One that is already installed is left as it is.

Dependencies are read from the file being installed. For a versioned script that is the
tagged file, so adding a `mys-requires:` line only takes effect once you cut a new release.

## 4. Changelogs (optional)

`mys changelog tool.sh` prints a script's release notes. To support it, add one Markdown file
per script at `changelogs/{package_path}.md` on the default branch, for example
`changelogs/gh-ssh.md` or `changelogs/linux/dirtree.py.md`:

```markdown
# gh-ssh

## Unreleased

### Added
- `gh-ssh rotate` replaces an existing key.

## 1.0.1 - 2026-06-27

### Added
- `--version` flag.

## 1.0.0 - 2026-06-27

First versioned release.
```

- **One `## ` heading per release, newest first.** The first word of the heading is the
  version and must equal the version in the tag and in `versions.tsv`. Anything after it,
  such as a date, is shown as written. A leading `v` or surrounding `[ ]` is ignored.
- **`## Unreleased` is never shown**, so use it to collect notes for the next release.
- **Text above the first `## ` heading is ignored.**
- The body of a section is printed as it is, so any Markdown works.

`mys` matches the installed version against these headings to mark it `[installed]` and to
work out what `mys changelog --new` should print.

## Checklist

Required:

- [ ] The repo is public and on GitHub.
- [ ] The default branch is `main`, or users are told to run `mys config --branch <name>`.
- [ ] Each script is a single file that runs on its own.
- [ ] Each script ends in `.py`, `.sh` or `.mjs`, or starts with its own `#!` line.
- [ ] No two scripts reduce to the same command name.

For versions:

- [ ] Each release has a pushed tag named `{package_path}-{version}`.
- [ ] `versions.tsv` at the repo root lists `package path<TAB>latest version`, two columns.

For dependencies:

- [ ] `# mys-requires:` appears in the first 30 lines and names scripts in the same repo.
- [ ] A release was cut after the header was added.

For changelogs:

- [ ] `changelogs/{package_path}.md` exists, with a `## {version}` heading per release.

## Checking your repo

These commands change nothing on your machine, apart from the install into a scratch
directory at the end. Replace `owner/name` and `tool.sh` with your own.

Confirm `mys` resolves the ref you expect (the release tag, or the branch if unreleased):

```bash
mys --repo owner/name url tool.sh
```

Confirm the dependency tree:

```bash
mys --repo owner/name deps tool.sh
```

Confirm the changelog is found and parsed:

```bash
mys --repo owner/name changelog tool.sh
```

Do a real install into a throwaway directory, without touching `/usr/local/bin` or your
registry:

```bash
mys --repo owner/name --bin-dir /tmp/mys-check/bin --registry-path /tmp/mys-check/registry.tsv install tool.sh
```

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `failed to download ... HTTP Error 404` on a bare install | The repo is private, the path is wrong, the default branch is not `main`, or `versions.tsv` names a version whose tag was never pushed |
| A bare install gets the branch HEAD, not the release | No line for the script in `versions.tsv`, the line does not have exactly two tab-separated columns, or GitHub's cache has not refreshed yet |
| `no released version found ...; cannot resolve @latest` | `versions.tsv` is missing or has no line for the script |
| `ignoring malformed versions.tsv entry` | A line uses spaces, not a tab, or has extra columns |
| A dependency is not installed | The header is below line 30, uses the wrong comment marker, or the released tag predates the header |
| `no changelog found` | The file is not at `changelogs/{package_path}.md` on the default branch |
| The installed command fails with "command not found" or an exec error | The file has an unknown extension and no `#!` line |
