from __future__ import annotations

import argparse
import os
import pwd
import runpy
from pathlib import Path

import pytest

# uv run --group dev pytest -q
ROOT = Path(__file__).resolve().parents[1]


def load_mys() -> dict[str, object]:
    return runpy.run_path(str(ROOT / "mys"))


def test_install_records_registry_entry(tmp_path: Path) -> None:
    mys = load_mys()
    registry_path = tmp_path / "registry.tsv"
    bin_dir = tmp_path / "bin"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        package="text_search.py",
        keep_extension=False,
        as_name=None,
        bin_dir=bin_dir,
        registry_path=registry_path,
    )

    mys["install_package"].__globals__["download_package"] = lambda repo, branch, package: (
        "mock",
        b"print('hello')\n",
    )

    exit_code = mys["install_package"](args)

    assert exit_code == 0
    assert (bin_dir / "text_search").exists()
    assert registry_path.read_text(encoding="utf-8").strip() == "\t".join(
        [
            "text_search",
            "text_search.py",
            "wodoame/cli-scripts",
            "main",
            str(bin_dir / "text_search"),
        ]
    )


def test_install_mjs_strips_extension_and_adds_node_shebang(tmp_path: Path) -> None:
    mys = load_mys()
    registry_path = tmp_path / "registry.tsv"
    bin_dir = tmp_path / "bin"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        package="schema.mjs",
        keep_extension=False,
        as_name=None,
        bin_dir=bin_dir,
        registry_path=registry_path,
    )

    mys["install_package"].__globals__["download_package"] = lambda repo, branch, package: (
        "mock",
        b"process.stdout.write('ok\\n');\n",
    )

    exit_code = mys["install_package"](args)

    assert exit_code == 0
    installed = bin_dir / "schema"
    assert installed.exists()
    assert installed.read_bytes().startswith(b"#!/usr/bin/env node\n")
    assert registry_path.read_text(encoding="utf-8").strip() == "\t".join(
        [
            "schema",
            "schema.mjs",
            "wodoame/cli-scripts",
            "main",
            str(installed),
        ]
    )


def test_parse_versions_manifest_skips_malformed_lines(capsys) -> None:
    mys = load_mys()
    parse_versions_manifest = mys["parse_versions_manifest"]

    versions = parse_versions_manifest("gh-ssh\t1.0.1\n\nbad-line\ntext_search.py\t2.0.0\n")
    captured = capsys.readouterr()

    assert versions == {"gh-ssh": "1.0.1", "text_search.py": "2.0.0"}
    assert "malformed versions.tsv entry" in captured.err


def test_resolve_branch_for_package_variants(capsys) -> None:
    mys = load_mys()
    resolve_branch_for_package = mys["resolve_branch_for_package"]

    assert resolve_branch_for_package("wodoame/cli-scripts", "main", "gh-ssh", None) == "main"
    assert (
        resolve_branch_for_package("wodoame/cli-scripts", "main", "gh-ssh", "1.0.0")
        == "gh-ssh-1.0.0"
    )

    mys["resolve_branch_for_package"].__globals__["resolve_latest_version"] = (
        lambda repo, branch, package: "1.0.1"
    )
    assert (
        resolve_branch_for_package("wodoame/cli-scripts", "main", "gh-ssh", "latest")
        == "gh-ssh-1.0.1"
    )

    mys["resolve_branch_for_package"].__globals__["resolve_latest_version"] = (
        lambda repo, branch, package: None
    )
    result = resolve_branch_for_package("wodoame/cli-scripts", "main", "unreleased.py", "latest")
    captured = capsys.readouterr()

    assert result is None
    assert "cannot resolve @latest" in captured.err


def test_install_resolves_latest_version(tmp_path: Path) -> None:
    mys = load_mys()
    registry_path = tmp_path / "registry.tsv"
    bin_dir = tmp_path / "bin"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        package="gh-ssh@latest",
        keep_extension=False,
        as_name=None,
        bin_dir=bin_dir,
        registry_path=registry_path,
    )

    def fake_download_package(repo: str, branch: str, package: str):
        if package == "versions.tsv":
            return "mock", b"gh-ssh\t1.0.1\n"
        return "mock", b"#!/usr/bin/env bash\necho hi\n"

    mys["install_package"].__globals__["download_package"] = fake_download_package

    exit_code = mys["install_package"](args)

    assert exit_code == 0
    assert registry_path.read_text(encoding="utf-8").strip() == "\t".join(
        [
            "gh-ssh",
            "gh-ssh",
            "wodoame/cli-scripts",
            "gh-ssh-1.0.1",
            str(bin_dir / "gh-ssh"),
        ]
    )


def test_install_latest_without_manifest_entry_fails(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        package="unreleased.py@latest",
        keep_extension=False,
        as_name=None,
        bin_dir=tmp_path / "bin",
        registry_path=tmp_path / "registry.tsv",
    )

    mys["install_package"].__globals__["download_package"] = lambda repo, branch, package: (
        "mock",
        b"",
    )

    exit_code = mys["install_package"](args)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "cannot resolve @latest" in captured.err


def test_version_flag_prints_name_and_version(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    defaults = {
        "repo": "wodoame/cli-scripts",
        "branch": "main",
        "bin_dir": str(tmp_path / "bin"),
        "registry_path": str(tmp_path / "registry.tsv"),
    }
    parser = mys["build_parser"](defaults, tmp_path / "config.tsv")

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--version"])
    captured = capsys.readouterr()

    assert excinfo.value.code == 0
    assert captured.out.strip() == f"{mys['SCRIPT_NAME']} {mys['VERSION']}"


def test_self_update_resolves_latest_version(tmp_path: Path) -> None:
    mys = load_mys()
    bin_dir = tmp_path / "bin"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        bin_dir=bin_dir,
        version="latest",
    )

    def fake_download_package(repo: str, branch: str, package: str):
        if package == "versions.tsv":
            return "mock", b"mys\t1.0.0\n"
        assert branch == "mys-1.0.0"
        return "mock", b"#!/usr/bin/env python3\nprint('hi')\n"

    mys["self_update"].__globals__["download_package"] = fake_download_package

    exit_code = mys["self_update"](args)

    assert exit_code == 0
    assert (bin_dir / "mys").exists()


def test_self_update_without_version_uses_default_branch(tmp_path: Path) -> None:
    mys = load_mys()
    bin_dir = tmp_path / "bin"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        bin_dir=bin_dir,
        version=None,
    )

    def fake_download_package(repo: str, branch: str, package: str):
        assert branch == "main"
        return "mock", b"#!/usr/bin/env python3\nprint('hi')\n"

    mys["self_update"].__globals__["download_package"] = fake_download_package

    exit_code = mys["self_update"](args)

    assert exit_code == 0
    assert (bin_dir / "mys").exists()


def test_remove_refuses_unregistered_command(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "tool").write_text("content\n", encoding="utf-8")
    args = argparse.Namespace(
        name="tool",
        bin_dir=bin_dir,
        registry_path=tmp_path / "registry.tsv",
    )

    exit_code = mys["remove_package"](args)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "refusing to delete it" in captured.err
    assert (bin_dir / "tool").exists()


def test_import_merges_by_command_name(tmp_path: Path) -> None:
    mys = load_mys()
    registry_path = tmp_path / "registry.tsv"
    import_path = tmp_path / "import.tsv"
    registry_path.write_text(
        "alpha\ttext_search.py\twodoame/cli-scripts\tmain\t/tmp/alpha\n",
        encoding="utf-8",
    )
    import_path.write_text(
        (
            "beta\tlinux/dirtree.py\twodoame/cli-scripts\tmain\t/tmp/beta\n"
            "alpha\tcountfiles.py\twodoame/cli-scripts\tmain\t/tmp/alpha\n"
        ),
        encoding="utf-8",
    )
    args = argparse.Namespace(
        input=str(import_path),
        replace=False,
        registry_path=registry_path,
    )

    exit_code = mys["import_registry"](args)

    assert exit_code == 0
    assert registry_path.read_text(encoding="utf-8") == (
        "alpha\tcountfiles.py\twodoame/cli-scripts\tmain\t/tmp/alpha\n"
        "beta\tlinux/dirtree.py\twodoame/cli-scripts\tmain\t/tmp/beta\n"
    )


def test_config_persistence_and_environment_precedence(tmp_path: Path) -> None:
    mys = load_mys()
    config_path = tmp_path / "config.tsv"
    save_config = mys["save_config"]
    build_effective_config = mys["build_effective_config"]
    apply_environment_overrides = mys["apply_environment_overrides"]

    save_config(
        config_path,
        {
            "repo": "saved/repo",
            "branch": "saved-branch",
            "bin_dir": str(tmp_path / "saved-bin"),
            "registry_path": str(tmp_path / "saved-registry.tsv"),
        },
    )

    effective = build_effective_config(config_path)
    assert effective["repo"] == "saved/repo"
    assert effective["branch"] == "saved-branch"

    old_env = os.environ.copy()
    try:
        os.environ["MYS_REPO"] = "env/repo"
        os.environ["MYS_BRANCH"] = "env-branch"
        overridden = apply_environment_overrides(effective)
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    assert overridden["repo"] == "env/repo"
    assert overridden["branch"] == "env-branch"
    assert overridden["bin_dir"] == str(tmp_path / "saved-bin")


def test_sudo_uses_invoking_users_home_for_defaults() -> None:
    current_user = pwd.getpwuid(os.getuid())
    expected_home = Path(current_user.pw_dir)

    old_env = os.environ.copy()
    try:
        os.environ["SUDO_USER"] = current_user.pw_name
        mys = load_mys()
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    old_env = os.environ.copy()
    try:
        os.environ["SUDO_USER"] = current_user.pw_name
        assert mys["get_default_home"]() == expected_home
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    assert mys["DEFAULT_REGISTRY_PATH"] == expected_home / ".local" / "share" / "mys" / "registry.tsv"
    assert mys["DEFAULT_CONFIG_PATH"] == expected_home / ".config" / "mys" / "config.tsv"


def test_install_permission_error_is_friendly(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        package="text_search.py",
        keep_extension=False,
        as_name=None,
        bin_dir=tmp_path / "bin",
        registry_path=tmp_path / "registry.tsv",
    )

    mys["install_package"].__globals__["download_package"] = lambda repo, branch, package: (
        "mock",
        b"print('hello')\n",
    )
    mys["install_package"].__globals__["write_installed_file"] = (
        lambda bin_dir, package_path, command_name, content: (_ for _ in ()).throw(PermissionError())
    )

    exit_code = mys["install_package"](args)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "permission denied while writing" in captured.err
    assert "traceback" not in captured.err.lower()
