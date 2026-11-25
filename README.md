# Fast PR

Fast PR is a local command-line tool that asks your signed-in Codex CLI to review GitHub pull requests, then posts actionable suggestions as a comment-only PR review. It does not edit branches or create commits. This version runs manually; scheduling is out of scope.

## Requirements

- Python 3.10 or newer
- Git
- Codex CLI installed and signed in (`codex login`)
- A GitHub fine-grained personal access token scoped to this repository, with **Pull requests: read and write**. GitHub's Metadata read permission is granted automatically.

The token is saved per repository in `~/.config/fast-pr/credentials.json` with owner-only file permissions. It is never passed to Codex. You can instead provide `FAST_PR_GITHUB_TOKEN` in the environment for a single run.

## Install and configure

From the project clone:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
fast-pr setup
```

Setup detects the repository from its `origin` GitHub remote, checks that Codex is installed and signed in, installs the generic review skill and rules file if they are missing, and prompts for the GitHub token without echoing it. Existing skill and rules files are preserved. The selected repository and local review state are ignored by Git.

Edit these files to customize reviews:

- `.agents/skills/fast-pr-review/SKILL.md` — Codex review procedure and output requirements.
- `.fast-pr/rules.md` — project review and severity rules.

## Review pull requests

```sh
fast-pr review
```

The CLI checks open PRs. A PR is reviewed when its head commit or base commit differs from the last successfully posted review. Rebase-generated head SHA changes trigger a review. `fast-pr review --force` reviews all open PRs again.

Reviews run in a temporary detached worktree at the PR head, so uncommitted changes in the user's checkout are not included or altered. Codex runs with a read-only sandbox. Before publishing, Fast PR checks that the PR head and base SHAs have not changed during analysis. Findings are posted as an ordinary `COMMENT` review, which does not request changes or block merging.

Local state is kept in `.fast-pr/state.json` and ignored by Git. The state is updated only after the GitHub review is accepted. The GitHub API needs Pull requests read/write access to list PRs and create reviews with inline comments.
