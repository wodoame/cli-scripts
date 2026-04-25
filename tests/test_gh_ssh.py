from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "gh-ssh"


def run_gh_ssh(
    tmp_path: Path,
    *,
    extra_args: list[str] | None = None,
    stdin: str = "",
    stub_body: str | None = None,
    include_default_paths: bool = True,
    home_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    ssh_keygen = bin_dir / "ssh-keygen"
    ssh_keygen.write_text(
        stub_body
        or """#!/usr/bin/env bash
set -euo pipefail
output=""
comment=""
type=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f)
      output="$2"
      shift 2
      ;;
    -C)
      comment="$2"
      shift 2
      ;;
    -t)
      type="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
mkdir -p "$(dirname "$output")"
printf 'private:%s:%s\\n' "$type" "$comment" > "$output"
printf 'public:%s:%s\\n' "$type" "$comment" > "${output}.pub"
""",
        encoding="utf-8",
    )
    os.chmod(ssh_keygen, stat.S_IRWXU)

    ssh_dir = tmp_path / "ssh"
    args = [str(SCRIPT)]
    if include_default_paths:
        args.extend(
            [
                "--ssh-dir",
                str(ssh_dir),
                "--config-path",
                str(ssh_dir / "config"),
            ]
        )
    if extra_args:
        args.extend(extra_args)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    if home_dir is not None:
        env["HOME"] = str(home_dir)

    return subprocess.run(
        args,
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_creates_default_key_and_config_block(tmp_path: Path) -> None:
    result = run_gh_ssh(
        tmp_path,
        extra_args=["--email", "me@example.com", "--alias", "github-work"],
    )

    assert result.returncode == 0, result.stderr
    ssh_dir = tmp_path / "ssh"
    assert (ssh_dir / "github").read_text(encoding="utf-8") == "private:ed25519:me@example.com\n"
    assert (ssh_dir / "github.pub").read_text(encoding="utf-8") == "public:ed25519:me@example.com\n"

    config = (ssh_dir / "config").read_text(encoding="utf-8")
    assert "# >>> gh-ssh alias: github-work >>>" in config
    assert "Host github-work" in config
    assert f"IdentityFile {ssh_dir / 'github'}" in config


def test_uses_numeric_suffix_when_default_name_exists(tmp_path: Path) -> None:
    ssh_dir = tmp_path / "ssh"
    ssh_dir.mkdir()
    (ssh_dir / "github").write_text("existing\n", encoding="utf-8")
    (ssh_dir / "github.pub").write_text("existing\n", encoding="utf-8")

    result = run_gh_ssh(
        tmp_path,
        extra_args=["--email", "me@example.com", "--alias", "github-work"],
    )

    assert result.returncode == 0, result.stderr
    assert (ssh_dir / "github-1").exists()
    assert (ssh_dir / "github-1.pub").exists()
    assert "Private key: " + str(ssh_dir / "github-1") in result.stdout


def test_replaces_existing_managed_alias_block(tmp_path: Path) -> None:
    ssh_dir = tmp_path / "ssh"
    ssh_dir.mkdir()
    config_path = ssh_dir / "config"
    config_path.write_text(
        "\n".join(
            [
                "# >>> gh-ssh alias: github-work >>>",
                "Host github-work",
                "  HostName github.com",
                "  User git",
                "  IdentityFile /tmp/old-key",
                "  IdentitiesOnly yes",
                "# <<< gh-ssh alias: github-work <<<",
                "",
                "Host another-host",
                "  HostName example.com",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_gh_ssh(
        tmp_path,
        extra_args=["--email", "me@example.com", "--alias", "github-work"],
    )

    assert result.returncode == 0, result.stderr
    config = config_path.read_text(encoding="utf-8")
    assert "IdentityFile /tmp/old-key" not in config
    assert config.count("Host github-work") == 1
    assert "Host another-host" in config


def test_errors_on_unmanaged_alias_conflict(tmp_path: Path) -> None:
    ssh_dir = tmp_path / "ssh"
    ssh_dir.mkdir()
    config_path = ssh_dir / "config"
    config_path.write_text(
        "Host github-work\n  HostName github.com\n",
        encoding="utf-8",
    )

    result = run_gh_ssh(
        tmp_path,
        extra_args=["--email", "me@example.com", "--alias", "github-work"],
    )

    assert result.returncode == 1
    assert "already exists" in result.stderr


def test_prompts_fill_missing_flags(tmp_path: Path) -> None:
    result = run_gh_ssh(tmp_path, stdin="me@example.com\ngithub-personal\n")

    assert result.returncode == 0, result.stderr
    assert "Alias: github-personal" in result.stdout


def test_allows_custom_key_type_and_name(tmp_path: Path) -> None:
    result = run_gh_ssh(
        tmp_path,
        extra_args=[
            "--email",
            "me@example.com",
            "--alias",
            "github-work",
            "--key-name",
            "work-key",
            "--type",
            "rsa",
        ],
    )

    assert result.returncode == 0, result.stderr
    ssh_dir = tmp_path / "ssh"
    assert (ssh_dir / "work-key").read_text(encoding="utf-8") == "private:rsa:me@example.com\n"
    assert (ssh_dir / "work-key.pub").read_text(encoding="utf-8") == "public:rsa:me@example.com\n"


def test_show_config_prints_existing_config_without_ssh_keygen(tmp_path: Path) -> None:
    ssh_dir = tmp_path / "ssh"
    ssh_dir.mkdir()
    config_path = ssh_dir / "config"
    config_path.write_text(
        "Host github-work\n  HostName github.com\n",
        encoding="utf-8",
    )

    result = run_gh_ssh(
        tmp_path,
        extra_args=["--show-config"],
        stub_body="""#!/usr/bin/env bash
set -euo pipefail
echo "ssh-keygen should not run" >&2
exit 99
""",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Host github-work\n  HostName github.com\n"


def test_show_config_errors_when_config_is_missing(tmp_path: Path) -> None:
    result = run_gh_ssh(
        tmp_path,
        extra_args=["--show-config"],
        stub_body="""#!/usr/bin/env bash
set -euo pipefail
echo "ssh-keygen should not run" >&2
exit 99
""",
    )

    assert result.returncode == 1
    assert "SSH config not found" in result.stderr


def test_show_config_uses_default_home_ssh_config_path(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    ssh_dir = home_dir / ".ssh"
    ssh_dir.mkdir(parents=True)
    (ssh_dir / "config").write_text(
        "Host github-personal\n  HostName github.com\n",
        encoding="utf-8",
    )

    result = run_gh_ssh(
        tmp_path,
        extra_args=["--show-config"],
        include_default_paths=False,
        home_dir=home_dir,
        stub_body="""#!/usr/bin/env bash
set -euo pipefail
echo "ssh-keygen should not run" >&2
exit 99
""",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Host github-personal\n  HostName github.com\n"
