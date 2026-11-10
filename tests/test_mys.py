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

    # No version: latest release, unless the branch was chosen explicitly.
    mys["resolve_branch_for_package"].__globals__["resolve_latest_version"] = (
        lambda repo, branch, package, quiet=False: "1.0.1"
    )
    assert (
        resolve_branch_for_package("wodoame/cli-scripts", "main", "gh-ssh", None)
        == "gh-ssh-1.0.1"
    )
    assert (
        resolve_branch_for_package("wodoame/cli-scripts", "dev", "gh-ssh", None, False) == "dev"
    )

    # No version and no release: fall back to the branch HEAD without complaining.
    mys["resolve_branch_for_package"].__globals__["resolve_latest_version"] = (
        lambda repo, branch, package, quiet=False: None
    )
    assert (
        resolve_branch_for_package("wodoame/cli-scripts", "main", "unreleased.py", None) == "main"
    )
    assert capsys.readouterr().err == ""

    assert (
        resolve_branch_for_package("wodoame/cli-scripts", "main", "gh-ssh", "1.0.0")
        == "gh-ssh-1.0.0"
    )

    mys["resolve_branch_for_package"].__globals__["resolve_latest_version"] = (
        lambda repo, branch, package, quiet=False: "1.0.1"
    )
    assert (
        resolve_branch_for_package("wodoame/cli-scripts", "main", "gh-ssh", "latest")
        == "gh-ssh-1.0.1"
    )

    mys["resolve_branch_for_package"].__globals__["resolve_latest_version"] = (
        lambda repo, branch, package, quiet=False: None
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


def test_install_without_version_resolves_latest_version(tmp_path: Path) -> None:
    mys = load_mys()
    registry_path = tmp_path / "registry.tsv"
    bin_dir = tmp_path / "bin"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        package="gh-ssh",
        keep_extension=False,
        as_name=None,
        bin_dir=bin_dir,
        registry_path=registry_path,
    )

    def fake_download_package(repo: str, branch: str, package: str):
        if package == "versions.tsv":
            return "mock", b"gh-ssh\t1.0.1\n"
        assert branch == "gh-ssh-1.0.1"
        return "mock", b"#!/usr/bin/env bash\necho hi\n"

    mys["install_package"].__globals__["download_package"] = fake_download_package

    assert mys["install_package"](args) == 0
    assert registry_path.read_text(encoding="utf-8").split("\t")[3] == "gh-ssh-1.0.1"


def test_install_with_explicit_branch_skips_latest_version(tmp_path: Path) -> None:
    mys = load_mys()
    registry_path = tmp_path / "registry.tsv"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="dev",
        branch_explicit=True,
        package="gh-ssh",
        keep_extension=False,
        as_name=None,
        bin_dir=tmp_path / "bin",
        registry_path=registry_path,
    )

    def fake_download_package(repo: str, branch: str, package: str):
        assert package != "versions.tsv"
        assert branch == "dev"
        return "mock", b"#!/usr/bin/env bash\necho hi\n"

    mys["install_package"].__globals__["download_package"] = fake_download_package

    assert mys["install_package"](args) == 0
    assert registry_path.read_text(encoding="utf-8").split("\t")[3] == "dev"


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


def test_self_update_without_version_resolves_latest_version(tmp_path: Path) -> None:
    mys = load_mys()
    bin_dir = tmp_path / "bin"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        bin_dir=bin_dir,
        version=None,
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


def test_self_update_with_explicit_branch_uses_that_branch(tmp_path: Path) -> None:
    mys = load_mys()
    bin_dir = tmp_path / "bin"
    args = argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        branch_explicit=True,
        bin_dir=bin_dir,
        version=None,
    )

    def fake_download_package(repo: str, branch: str, package: str):
        assert package != "versions.tsv"
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


# --- dependencies ("mys-requires:" headers) ---------------------------------


def make_repo_download(files: dict[str, bytes], calls: list[tuple[str, str]] | None = None):
    """Fake download_package serving files from a dict keyed by package path."""

    def fake_download_package(repo: str, branch: str, package: str):
        if calls is not None:
            calls.append((branch, package))
        if package not in files:
            return None
        return "mock", files[package]

    return fake_download_package


def install_args(tmp_path: Path, package: str, **overrides) -> argparse.Namespace:
    values = dict(
        repo="wodoame/cli-scripts",
        branch="main",
        package=package,
        keep_extension=False,
        as_name=None,
        bin_dir=tmp_path / "bin",
        registry_path=tmp_path / "registry.tsv",
    )
    values.update(overrides)
    return argparse.Namespace(**values)


def registry_rows(registry_path: Path) -> dict[str, list[str]]:
    rows = [line.split("\t") for line in registry_path.read_text(encoding="utf-8").splitlines()]
    return {row[0]: row for row in rows}


def test_parse_requires_reads_header_comments() -> None:
    parse_requires = load_mys()["parse_requires"]

    assert parse_requires(b"#!/usr/bin/env bash\n# mys-requires: gh-ssh, dirtree.py@1.0.0\n") == [
        "gh-ssh",
        "dirtree.py@1.0.0",
    ]
    assert parse_requires(b"// mys-requires: a.mjs b.mjs\n#mys-requires: a.mjs, c.sh\n") == [
        "a.mjs",
        "b.mjs",
        "c.sh",
    ]
    assert parse_requires(b"echo '# mys-requires: nope'\nx = 1\n") == []
    assert parse_requires(b"\n" * 40 + b"# mys-requires: too-late\n") == []
    assert parse_requires(b"# mys-requires:\n") == []


def test_install_installs_transitive_dependencies(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    args = install_args(tmp_path, "app.sh")
    files = {
        "versions.tsv": b"lib.sh\t2.0.0\n",
        "app.sh": b"#!/usr/bin/env bash\n# mys-requires: lib.sh, helper.py@1.2.0\necho app\n",
        "lib.sh": b"#!/usr/bin/env bash\n# mys-requires: base.sh\necho lib\n",
        "helper.py": b"print('helper')\n",
        # A cycle back to the root must not loop forever.
        "base.sh": b"#!/usr/bin/env bash\n# mys-requires: app.sh\necho base\n",
    }
    mys["install_package"].__globals__["download_package"] = make_repo_download(files)

    exit_code = mys["install_package"](args)
    captured = capsys.readouterr()

    assert exit_code == 0
    rows = registry_rows(args.registry_path)
    assert {name: row[3] for name, row in rows.items()} == {
        "app": "main",
        "lib": "lib.sh-2.0.0",
        "helper": "helper.py-1.2.0",
        "base": "main",
    }
    for name in rows:
        assert (args.bin_dir / name).exists()
    assert "(required by app.sh)" in captured.out
    assert "(required by lib.sh)" in captured.out


def test_install_leaves_installed_dependency_alone(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    calls: list[tuple[str, str]] = []
    files = {
        "app.sh": b"# mys-requires: lib.sh@2.0.0\necho app\n",
        "lib.sh": b"echo lib\n",
    }
    mys["install_package"].__globals__["download_package"] = make_repo_download(files, calls)

    assert mys["install_package"](install_args(tmp_path, "lib.sh@1.0.0")) == 0
    calls.clear()
    assert mys["install_package"](install_args(tmp_path, "app.sh")) == 0
    captured = capsys.readouterr()

    assert registry_rows(tmp_path / "registry.tsv")["lib"][3] == "lib.sh-1.0.0"
    assert all(package != "lib.sh" for _, package in calls)
    assert "already installed from lib.sh-1.0.0" in captured.err


def test_install_writes_nothing_when_a_dependency_is_missing(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    args = install_args(tmp_path, "app.sh")
    files = {
        "app.sh": b"# mys-requires: lib.sh, missing.sh\necho app\n",
        "lib.sh": b"echo lib\n",
    }
    mys["install_package"].__globals__["download_package"] = make_repo_download(files)

    exit_code = mys["install_package"](args)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "could not fetch missing.sh, required by app.sh" in captured.err
    assert not args.registry_path.exists()
    assert not (args.bin_dir / "app").exists()
    assert not (args.bin_dir / "lib").exists()


def test_install_refuses_dependency_whose_command_name_is_taken(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    files = {
        "tools/lib.py": b"print('other lib')\n",
        "app.sh": b"# mys-requires: lib.sh\necho app\n",
        "lib.sh": b"echo lib\n",
    }
    mys["install_package"].__globals__["download_package"] = make_repo_download(files)

    assert mys["install_package"](install_args(tmp_path, "tools/lib.py")) == 0
    exit_code = mys["install_package"](install_args(tmp_path, "app.sh"))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "'lib' is already used by tools/lib.py" in captured.err
    assert not (tmp_path / "bin" / "app").exists()


def test_update_installs_newly_declared_dependencies(tmp_path: Path) -> None:
    mys = load_mys()
    args = install_args(tmp_path, "app.sh")
    files = {"app.sh": b"echo app\n", "lib.sh": b"echo lib\n"}
    mys["install_package"].__globals__["download_package"] = make_repo_download(files)
    assert mys["install_package"](args) == 0
    assert set(registry_rows(args.registry_path)) == {"app"}

    files["app.sh"] = b"# mys-requires: lib.sh\necho app v2\n"
    assert mys["update_package"](args) == 0

    assert set(registry_rows(args.registry_path)) == {"app", "lib"}
    assert (args.bin_dir / "lib").exists()


def test_sync_installs_dependencies_missing_from_registry(tmp_path: Path) -> None:
    mys = load_mys()
    bin_dir = tmp_path / "bin"
    registry_path = tmp_path / "registry.tsv"
    registry_path.write_text(
        "\t".join(["app", "app.sh", "wodoame/cli-scripts", "main", str(bin_dir / "app")]) + "\n",
        encoding="utf-8",
    )
    files = {
        "app.sh": b"# mys-requires: lib.sh\necho app\n",
        "lib.sh": b"echo lib\n",
    }
    mys["sync_registry"].__globals__["download_package"] = make_repo_download(files)

    exit_code = mys["sync_registry"](
        argparse.Namespace(branch="main", registry_path=registry_path)
    )

    assert exit_code == 0
    assert set(registry_rows(registry_path)) == {"app", "lib"}
    assert (bin_dir / "lib").exists()


def test_remove_refuses_required_command_unless_forced(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    args = install_args(tmp_path, "app.sh")
    files = {
        "app.sh": b"# mys-requires: lib.sh\necho app\n",
        "lib.sh": b"echo lib\n",
    }
    mys["install_package"].__globals__["download_package"] = make_repo_download(files)
    assert mys["install_package"](args) == 0

    remove_args = argparse.Namespace(
        name="lib", bin_dir=args.bin_dir, registry_path=args.registry_path, force=False
    )
    assert mys["remove_package"](remove_args) == 1
    assert "lib is required by app" in capsys.readouterr().err
    assert (args.bin_dir / "lib").exists()

    remove_args.force = True
    assert mys["remove_package"](remove_args) == 0
    assert not (args.bin_dir / "lib").exists()
    assert set(registry_rows(args.registry_path)) == {"app"}


def test_deps_prints_resolved_tree(tmp_path: Path, capsys) -> None:
    mys = load_mys()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "helper").write_text("print('helper')\n", encoding="utf-8")
    registry_path = tmp_path / "registry.tsv"
    registry_path.write_text(
        "\t".join(
            ["helper", "helper.py", "wodoame/cli-scripts", "main", str(bin_dir / "helper")]
        )
        + "\n",
        encoding="utf-8",
    )
    files = {
        "versions.tsv": b"app.sh\t1.0.0\nlib.sh\t2.0.0\n",
        "app.sh": b"# mys-requires: lib.sh, helper.py\necho app\n",
        "lib.sh": b"# mys-requires: app.sh\necho lib\n",
        "helper.py": b"print('helper')\n",
    }
    mys["print_dependencies"].__globals__["download_package"] = make_repo_download(files)

    exit_code = mys["print_dependencies"](
        argparse.Namespace(
            repo="wodoame/cli-scripts",
            branch="main",
            package="app.sh",
            registry_path=registry_path,
        )
    )

    assert exit_code == 0
    assert capsys.readouterr().out.splitlines() == [
        "app.sh (app.sh-1.0.0)",
        "  lib.sh (lib.sh-2.0.0)",
        "    app.sh (dependency cycle)",
        "  helper.py (main) [installed]",
    ]


# --- changelog ---------------------------------------------------------------

CHANGELOG = b"""# gh-ssh

Intro text that is not part of any version.

## Unreleased

- Not out yet.

## 1.1.0 - 2026-11-10

### Added
- Rotate keys.

## 1.0.1 - 2026-06-27

### Added
- `--version` flag.

## 1.0.0 - 2026-06-27

First versioned release.
"""


def changelog_args(tmp_path: Path, package: str, new: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        repo="wodoame/cli-scripts",
        branch="main",
        package=package,
        new=new,
        registry_path=tmp_path / "registry.tsv",
    )


def write_registry_row(tmp_path: Path, branch: str) -> None:
    (tmp_path / "registry.tsv").write_text(
        "\t".join(["gh-ssh", "gh-ssh", "wodoame/cli-scripts", branch, "/usr/local/bin/gh-ssh"])
        + "\n",
        encoding="utf-8",
    )


def load_mys_with_changelog(calls: list[tuple[str, str]] | None = None) -> dict[str, object]:
    mys = load_mys()
    mys["print_changelog"].__globals__["download_package"] = make_repo_download(
        {"changelogs/gh-ssh.md": CHANGELOG}, calls
    )
    return mys


def test_parse_changelog_drops_unreleased_and_preamble() -> None:
    sections = load_mys()["parse_changelog"](CHANGELOG.decode())

    assert [section["version"] for section in sections] == ["1.1.0", "1.0.1", "1.0.0"]
    assert sections[0]["heading"] == "1.1.0 - 2026-11-10"
    assert sections[0]["body"] == "### Added\n- Rotate keys."
    assert sections[2]["body"] == "First versioned release."


def test_changelog_prints_released_versions_and_marks_installed(tmp_path: Path, capsys) -> None:
    calls: list[tuple[str, str]] = []
    mys = load_mys_with_changelog(calls)
    write_registry_row(tmp_path, "gh-ssh-1.0.1")

    exit_code = mys["print_changelog"](changelog_args(tmp_path, "gh-ssh"))
    out = capsys.readouterr().out

    assert exit_code == 0
    assert calls == [("main", "changelogs/gh-ssh.md")]
    assert out.startswith("# gh-ssh\n\n## 1.1.0 - 2026-11-10\n\n### Added\n- Rotate keys.\n\n")
    assert "## 1.0.1 - 2026-06-27 [installed]" in out
    assert "## 1.0.0 - 2026-06-27\n\nFirst versioned release.\n" in out
    assert "Not out yet" not in out
    assert "Intro text" not in out


def test_changelog_single_version_and_latest(tmp_path: Path, capsys) -> None:
    mys = load_mys_with_changelog()

    assert mys["print_changelog"](changelog_args(tmp_path, "gh-ssh@1.0.1")) == 0
    assert capsys.readouterr().out == (
        "# gh-ssh\n\n## 1.0.1 - 2026-06-27\n\n### Added\n- `--version` flag.\n"
    )

    assert mys["print_changelog"](changelog_args(tmp_path, "gh-ssh@latest")) == 0
    out = capsys.readouterr().out
    assert "## 1.1.0" in out and "## 1.0.1" not in out

    assert mys["print_changelog"](changelog_args(tmp_path, "gh-ssh@9.9.9")) == 1
    assert "no changelog entry for gh-ssh 9.9.9" in capsys.readouterr().err


def test_changelog_new_prints_only_newer_releases(tmp_path: Path, capsys) -> None:
    mys = load_mys_with_changelog()

    assert mys["print_changelog"](changelog_args(tmp_path, "gh-ssh", new=True)) == 1
    assert "is not installed" in capsys.readouterr().err

    write_registry_row(tmp_path, "main")
    assert mys["print_changelog"](changelog_args(tmp_path, "gh-ssh", new=True)) == 1
    assert "installed from a branch" in capsys.readouterr().err

    write_registry_row(tmp_path, "gh-ssh-1.0.0")
    assert mys["print_changelog"](changelog_args(tmp_path, "gh-ssh", new=True)) == 0
    out = capsys.readouterr().out
    assert "## 1.1.0" in out and "## 1.0.1" in out and "## 1.0.0" not in out

    write_registry_row(tmp_path, "gh-ssh-1.1.0")
    assert mys["print_changelog"](changelog_args(tmp_path, "gh-ssh", new=True)) == 0
    assert capsys.readouterr().out == "gh-ssh 1.1.0 is the latest release.\n"


def test_changelog_missing_file_is_a_short_error(tmp_path: Path, capsys) -> None:
    mys = load_mys_with_changelog()

    exit_code = mys["print_changelog"](changelog_args(tmp_path, "nope.sh"))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.err == "mys: no changelog found for nope.sh in wodoame/cli-scripts\n"
