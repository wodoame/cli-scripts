# mys

## Unreleased

## 1.3.0 - 2026-11-10

### Added
- `mys changelog <package>` prints what changed in each released version, marking the
  installed one. Append `@version` for a single release, or pass `--new` for only the
  releases newer than the installed version.

## 1.2.0 - 2026-11-10

### Added
- Scripts can declare the scripts they need with a `# mys-requires:` header. `install`,
  `update` and `sync` install any that are missing.
- `mys deps <package>` prints a package's dependency tree.
- `mys remove --force` removes a command even if another installed script requires it.

### Changed
- `mys remove` refuses to remove a command that another installed script requires.

## 1.1.0 - 2026-11-10

### Changed
- A package with no `@version` now installs its latest released version instead of the
  default branch HEAD. Scripts with no release still install from the branch HEAD.
- `mys self-update` with no version updates to the latest released version.
- Passing `--branch` explicitly installs that branch's HEAD.

## 1.0.0 - 2026-07-14

First versioned release.

### Added
- `mys --version`.
- `@version` suffix to pin a release, and `@latest` to resolve the newest one from
  `versions.tsv`.
- `mys self-update <version>`.
