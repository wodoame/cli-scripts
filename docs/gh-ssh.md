# gh-ssh

`gh-ssh` is a Bash CLI that generates a new GitHub SSH key pair and adds a matching SSH alias to your `~/.ssh/config`.

## Features

- Creates a new SSH key pair with `ssh-keygen`.
- Avoids file collisions by renaming new keys with numeric suffixes like `github-1`.
- Adds or updates a tool-managed `Host` alias block in `~/.ssh/config`.
- Can print the SSH config file so you can inspect existing aliases quickly.
- Supports both flags and interactive prompts for missing values.

## Usage

```bash
gh-ssh [--email EMAIL] [--alias ALIAS] [--key-name NAME] [--show-config] [--ssh-dir DIR] [--config-path PATH] [--type TYPE]
```

## Arguments

- `-e, --email EMAIL`: Email/comment to embed in the SSH key. If omitted, `gh-ssh` prompts for it.
- `-a, --alias ALIAS`: SSH alias to use for GitHub, for example `github-work`. If omitted, `gh-ssh` prompts for it.
- `-k, --key-name NAME`: Base key filename inside the SSH directory. Defaults to `github`.
- `--show-config`: Print the SSH config file and exit without creating a key.
- `--ssh-dir DIR`: SSH directory to use. Defaults to `~/.ssh`.
- `--config-path PATH`: SSH config path to update. Defaults to `~/.ssh/config`.
- `-t, --type TYPE`: SSH key type. Defaults to `ed25519`.
- `-h, --help`: Show the built-in help message.

## Behavior

- New keys are written to `~/.ssh/github` by default.
- If `github` or `github.pub` already exists, the tool tries `github-1`, then `github-2`, and so on.
- The SSH config entry is stored in a managed block so rerunning the tool for the same alias updates only that block.
- If the alias already exists in an unmanaged `Host` block, the tool stops instead of guessing how to merge the config.
- Passphrase entry is handled directly by `ssh-keygen`.

Example managed block:

```sshconfig
# >>> gh-ssh alias: github-work >>>
Host github-work
  HostName github.com
  User git
  IdentityFile /home/you/.ssh/github
  IdentitiesOnly yes
# <<< gh-ssh alias: github-work <<<
```

## Examples

Create a key and alias with prompts:

```bash
gh-ssh
```

Create a work account key non-interactively:

```bash
gh-ssh --email you@work.com --alias github-work
```

Choose a custom base name:

```bash
gh-ssh --email you@work.com --alias github-work --key-name work-github
```

Print the current SSH config:

```bash
gh-ssh --show-config
```

## After Running

`gh-ssh` prints the final private key path, public key path, alias, and the Git SSH URL format to use:

```bash
git@github-work:OWNER/REPO.git
```

You can verify the setup with:

```bash
ssh -T git@github-work
```
