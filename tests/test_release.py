from __future__ import annotations

import datetime
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RELEASE_SCRIPT = ROOT / "scripts" / "release.sh"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def release(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(repo / "scripts" / "release.sh"), *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(RELEASE_SCRIPT, repo / "scripts" / "release.sh")
    (repo / "tool.sh").write_text('#!/usr/bin/env bash\nVERSION="1.0.0"\necho "$VERSION"\n')
    (repo / "tool.py").write_text('VERSION = "0.3.1"\nOTHER_VERSION = "9.9.9"\n')
    (repo / "plain.sh").write_text("#!/usr/bin/env bash\necho hi\n")
    (repo / "versions.tsv").write_text("tool.py\t0.3.1\ntool.sh\t1.0.0\n")
    changelogs = repo / "changelogs"
    changelogs.mkdir()
    (changelogs / "tool.sh.md").write_text(
        "# tool.sh\n\n## Unreleased\n\n### Added\n- A new flag.\n\n"
        "## 1.0.0 - 2026-01-01\n\nFirst release.\n"
    )
    (changelogs / "tool.py.md").write_text(
        "# tool.py\n\n## Unreleased\n- Fixed a crash.\n\n## 0.3.1 - 2026-01-01\n- Older.\n"
    )
    (changelogs / "plain.sh.md").write_text("# plain.sh\n\n## Unreleased\n\n- First release.\n")

    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "initial")
    return repo


def test_bump_keyword_updates_marker_manifest_commit_and_tag(repo: Path) -> None:
    result = release(repo, "--no-push", "tool.sh", "minor")

    assert result.returncode == 0, result.stderr
    assert 'VERSION="1.1.0"' in (repo / "tool.sh").read_text()
    assert (repo / "versions.tsv").read_text() == "tool.py\t0.3.1\ntool.sh\t1.1.0\n"
    assert git(repo, "log", "-1", "--format=%s") == "chore: release tool.sh 1.1.0"
    assert git(repo, "tag", "--points-at", "HEAD") == "tool.sh-1.1.0"
    assert git(repo, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("keyword", "expected"),
    [("patch", "0.3.2"), ("minor", "0.4.0"), ("major", "1.0.0")],
)
def test_bump_keywords(repo: Path, keyword: str, expected: str) -> None:
    result = release(repo, "--no-push", "tool.py", keyword)

    assert result.returncode == 0, result.stderr
    content = (repo / "tool.py").read_text()
    assert f'VERSION = "{expected}"' in content
    assert 'OTHER_VERSION = "9.9.9"' in content
    assert git(repo, "tag") == f"tool.py-{expected}"


def test_first_release_of_script_without_marker_adds_sorted_manifest_row(repo: Path) -> None:
    result = release(repo, "--no-push", "plain.sh", "1.0.0")

    assert result.returncode == 0, result.stderr
    assert (repo / "plain.sh").read_text() == "#!/usr/bin/env bash\necho hi\n"
    assert (
        (repo / "versions.tsv").read_text()
        == "plain.sh\t1.0.0\ntool.py\t0.3.1\ntool.sh\t1.0.0\n"
    )
    assert git(repo, "tag") == "plain.sh-1.0.0"


def test_bump_keyword_needs_an_existing_version(repo: Path) -> None:
    result = release(repo, "--no-push", "plain.sh", "patch")

    assert result.returncode == 1
    assert "no released version yet" in result.stderr


def test_dry_run_changes_nothing(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD")

    result = release(repo, "--dry-run", "--no-push", "tool.sh", "patch")

    assert result.returncode == 0, result.stderr
    assert "1.0.0 -> 1.0.1" in result.stdout
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "tag") == ""
    assert git(repo, "status", "--porcelain") == ""


def test_refuses_dirty_tree_existing_tag_and_bad_input(repo: Path) -> None:
    assert "not a version" in release(repo, "--no-push", "tool.sh", "banana").stderr
    assert "does not exist" in release(repo, "--no-push", "missing.sh", "patch").stderr
    assert "already released" in release(repo, "--no-push", "tool.sh", "1.0.0").stderr

    git(repo, "tag", "tool.sh-1.0.1")
    assert "already exists" in release(repo, "--no-push", "tool.sh", "patch").stderr

    (repo / "tool.py").write_text('VERSION = "0.3.1"\n# edited\n')
    result = release(repo, "--no-push", "tool.py", "patch")
    assert result.returncode == 1
    assert "uncommitted changes" in result.stderr


def test_pushes_commit_and_tag(repo: Path, tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-q", "-u", "origin", "main")

    result = release(repo, "tool.sh", "patch")

    assert result.returncode == 0, result.stderr
    assert git(remote, "rev-parse", "main") == git(repo, "rev-parse", "HEAD")
    assert git(remote, "tag") == "tool.sh-1.0.1"


def test_release_moves_unreleased_notes_under_the_new_version(repo: Path) -> None:
    result = release(repo, "--no-push", "tool.sh", "minor")

    assert result.returncode == 0, result.stderr
    today = datetime.date.today().isoformat()
    assert (repo / "changelogs" / "tool.sh.md").read_text() == (
        "# tool.sh\n\n## Unreleased\n\n"
        f"## 1.1.0 - {today}\n\n### Added\n- A new flag.\n\n"
        "## 1.0.0 - 2026-01-01\n\nFirst release.\n"
    )
    assert "- A new flag." in result.stdout
    committed = git(repo, "show", "--name-only", "--format=", "HEAD").splitlines()
    assert sorted(committed) == ["changelogs/tool.sh.md", "tool.sh", "versions.tsv"]


def test_release_refuses_without_changelog_notes(repo: Path) -> None:
    changelog = repo / "changelogs" / "tool.sh.md"
    changelog.write_text("# tool.sh\n\n## Unreleased\n\n## 1.0.0 - 2026-01-01\n\nFirst release.\n")
    git(repo, "commit", "-q", "-am", "empty unreleased")

    result = release(repo, "--no-push", "tool.sh", "patch")
    assert result.returncode == 1
    assert "nothing under '## Unreleased'" in result.stderr

    changelog.write_text("# tool.sh\n\n## 1.0.0 - 2026-01-01\n\nFirst release.\n")
    git(repo, "commit", "-q", "-am", "no unreleased")
    result = release(repo, "--no-push", "tool.sh", "patch")
    assert result.returncode == 1
    assert "has no '## Unreleased' section" in result.stderr

    git(repo, "rm", "-q", "changelogs/tool.sh.md")
    git(repo, "commit", "-q", "-m", "no changelog")
    result = release(repo, "--no-push", "tool.sh", "patch")
    assert result.returncode == 1
    assert "does not exist" in result.stderr
    assert git(repo, "tag") == ""


def test_no_changelog_flag_releases_without_touching_the_changelog(repo: Path) -> None:
    git(repo, "rm", "-q", "changelogs/tool.sh.md")
    git(repo, "commit", "-q", "-m", "no changelog")

    result = release(repo, "--no-push", "--no-changelog", "tool.sh", "patch")

    assert result.returncode == 0, result.stderr
    assert git(repo, "tag") == "tool.sh-1.0.1"
    assert not (repo / "changelogs" / "tool.sh.md").exists()


def test_message_flag_sets_the_release_commit_message(repo: Path) -> None:
    result = release(repo, "--no-push", "-m", "release: tool.sh 1.0.1", "tool.sh", "patch")

    assert result.returncode == 0, result.stderr
    assert "commit: release: tool.sh 1.0.1" in result.stdout
    assert git(repo, "log", "-1", "--format=%s") == "release: tool.sh 1.0.1"
    assert git(repo, "tag", "--points-at", "HEAD") == "tool.sh-1.0.1"

    result = release(repo, "--no-push", "--message=Cut tool.py\n\nWith a body.", "tool.py", "patch")

    assert result.returncode == 0, result.stderr
    assert git(repo, "log", "-1", "--format=%B") == "Cut tool.py\n\nWith a body."


def test_message_flag_needs_a_value(repo: Path) -> None:
    for args in (["tool.sh", "patch", "-m"], ["-m", "  ", "tool.sh", "patch"]):
        result = release(repo, "--no-push", *args)
        assert result.returncode == 1
        assert "commit message" in result.stderr
    assert git(repo, "tag") == ""
