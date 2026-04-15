from __future__ import annotations

import argparse
import os
import pwd
import runpy
from pathlib import Path

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
