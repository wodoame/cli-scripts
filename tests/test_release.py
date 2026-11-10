from __future__ import annotations

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
