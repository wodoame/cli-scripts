#!/usr/bin/env bash
#
# Cut a release of one script in this repo:
#   1. bump the script's VERSION marker (if it has one)
#   2. update its row in versions.tsv
#   3. commit both as "chore: release <package> <version>"
#   4. tag the commit as <package>-<version>
#   5. push the commit and the tag
#
# This is a repo maintenance tool, not a package to install with mys.

set -euo pipefail

SCRIPT_NAME="release.sh"
MANIFEST="versions.tsv"
REMOTE="origin"

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [options] <package> <version|major|minor|patch>

Release one script: bump its VERSION marker, update $MANIFEST, commit,
tag the commit as <package>-<version>, then push the commit and tag.

Arguments:
  package            Path of the script relative to the repo root, e.g. gh-ssh
  version            Explicit version (1.2.3), or major, minor or patch to bump
                     the version currently recorded in $MANIFEST

Options:
  -n, --dry-run      Show what would happen without changing anything
      --no-push      Commit and tag locally, but do not push
  -h, --help         Show this help and exit

Examples:
  $SCRIPT_NAME gh-ssh patch
  $SCRIPT_NAME mys 1.2.0
  $SCRIPT_NAME --dry-run dirtree.py minor
EOF
}

die() {
  echo "$SCRIPT_NAME: $*" >&2
  exit 1
}

dry_run=false
push=true
positional=()

while [[ $# -gt 0 ]]; do
  case "$1" in
  -n | --dry-run) dry_run=true ;;
  --no-push) push=false ;;
  -h | --help)
    usage
    exit 0
    ;;
  -*) die "unknown option: $1 (see --help)" ;;
  *) positional+=("$1") ;;
  esac
  shift
done

if [[ ${#positional[@]} -ne 2 ]]; then
  usage >&2
  exit 2
fi

package="${positional[0]}"
requested="${positional[1]}"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside a git repository"
cd "$repo_root"

# --- Validate the package -----------------------------------------------------

[[ "$package" != "$MANIFEST" ]] || die "$MANIFEST is the manifest, not a package"
[[ -f "$package" ]] || die "$package does not exist in $repo_root"
git ls-files --error-unmatch -- "$package" >/dev/null 2>&1 || die "$package is not tracked by git"

# --- Work out the current and new version -------------------------------------

manifest_version=""
if [[ -f "$MANIFEST" ]]; then
  manifest_version="$(awk -F'\t' -v pkg="$package" '$1 == pkg { print $2; exit }' "$MANIFEST")"
fi

# The in-script marker: a top-level VERSION="1.2.3" (bash) or VERSION = "1.2.3" (python).
marker_pattern='^VERSION[[:space:]]*=[[:space:]]*"[^"]*"'
marker_version="$(grep -m1 -E "$marker_pattern" "$package" | sed -E 's/^[^"]*"([^"]*)".*/\1/' || true)"

current_version="${manifest_version:-$marker_version}"

semver_pattern='^[0-9]+\.[0-9]+\.[0-9]+$'

case "$requested" in
major | minor | patch)
  [[ -n "$current_version" ]] ||
    die "$package has no released version yet; pass an explicit version, e.g. 1.0.0"
  [[ "$current_version" =~ $semver_pattern ]] ||
    die "cannot bump '$current_version'; pass an explicit version instead"
  IFS=. read -r major minor patch <<<"$current_version"
  case "$requested" in
  major) new_version="$((major + 1)).0.0" ;;
  minor) new_version="$major.$((minor + 1)).0" ;;
  patch) new_version="$major.$minor.$((patch + 1))" ;;
  esac
  ;;
*)
  new_version="${requested#v}"
  [[ "$new_version" =~ $semver_pattern ]] ||
    die "'$requested' is not a version (expected X.Y.Z, major, minor or patch)"
  ;;
esac

tag="$package-$new_version"

# --- Validate the repo state --------------------------------------------------

[[ "$new_version" != "$manifest_version" ]] || die "$package is already released at $new_version"

if git rev-parse --verify --quiet "refs/tags/$tag" >/dev/null; then
  die "tag $tag already exists"
fi

branch="$(git symbolic-ref --quiet --short HEAD)" || die "HEAD is detached; check out a branch first"

if ! git diff --quiet || ! git diff --cached --quiet; then
  die "the working tree has uncommitted changes; commit or stash them first"
fi

if $push; then
  git remote get-url "$REMOTE" >/dev/null 2>&1 || die "no '$REMOTE' remote; use --no-push"
  if ! $dry_run; then
    git fetch --quiet --tags "$REMOTE" || die "could not fetch from $REMOTE; use --no-push to release offline"
    if git rev-parse --verify --quiet "refs/tags/$tag" >/dev/null; then
      die "tag $tag already exists on $REMOTE"
    fi
    if git rev-parse --verify --quiet "refs/remotes/$REMOTE/$branch" >/dev/null &&
      [[ -n "$(git rev-list "HEAD..$REMOTE/$branch")" ]]; then
      die "$branch is behind $REMOTE/$branch; pull first"
    fi
  fi
fi

# --- Report the plan ----------------------------------------------------------

echo "Releasing $package ${current_version:-(unreleased)} -> $new_version"
if [[ -n "$marker_version" ]]; then
  echo "  bump VERSION marker in $package ($marker_version -> $new_version)"
else
  echo "  $package has no VERSION marker; only $MANIFEST will change"
fi
echo "  update $MANIFEST"
echo "  commit: chore: release $package $new_version"
echo "  tag:    $tag"
if $push; then
  echo "  push:   $branch and $tag to $REMOTE"
else
  echo "  push:   skipped (--no-push)"
fi

if $dry_run; then
  echo "Dry run: nothing was changed."
  exit 0
fi

# --- Apply --------------------------------------------------------------------

rewrite() {
  # rewrite <file> <awk args...>: run awk over the file and replace it in place,
  # keeping its permissions.
  local file="$1" tmp
  shift
  tmp="$(mktemp)"
  if [[ -f "$file" ]]; then
    awk "$@" "$file" >"$tmp"
  else
    awk "$@" /dev/null >"$tmp"
  fi
  cat "$tmp" >"$file"
  rm -f "$tmp"
}

if [[ -n "$marker_version" ]]; then
  rewrite "$package" -v version="$new_version" '
    !done && /^VERSION[[:space:]]*=[[:space:]]*"[^"]*"/ {
      sub(/"[^"]*"/, "\"" version "\"")
      done = 1
    }
    { print }
  '
fi

# Replace the package row (or add it), keeping the manifest sorted by package path.
rewrite "$MANIFEST" -F'\t' -v pkg="$package" -v version="$new_version" '
  NF && $1 != pkg { print }
  END { print pkg "\t" version }
'
LC_ALL=C sort -o "$MANIFEST" "$MANIFEST"

git add -- "$package" "$MANIFEST"
git commit --quiet -m "chore: release $package $new_version"
git tag "$tag"
echo "Committed and tagged $tag"

if $push; then
  if git push --atomic "$REMOTE" "$branch" "$tag"; then
    echo "Pushed $branch and $tag to $REMOTE"
  else
    die "push failed; the commit and tag exist locally. Retry with: git push --atomic $REMOTE $branch $tag"
  fi
else
  echo "Not pushed. When ready: git push --atomic $REMOTE $branch $tag"
fi

echo "Released $package $new_version"
