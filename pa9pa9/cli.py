from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
API_VERSION = "2022-11-28"
APP_DIR = Path.home() / ".config" / "pa9pa9"
TOKEN_FILE = APP_DIR / "credentials.json"
STATE_FILE = Path(".pa9pa9/state.json")
CONFIG_FILE = Path(".pa9pa9/config.json")
SKILL_NAME = "pa9pa9-review"


class Pa9Error(Exception):
    pass


def run(args: list[str], *, cwd: Path | None = None, check: bool = True,
        capture: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            input=input_text,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            check=False,
        )
    except FileNotFoundError as exc:
        raise Pa9Error(f"Required command not found: {args[0]}") from exc
    if check and result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        raise Pa9Error(f"Command failed ({' '.join(args[:3])}): {detail}")
    return result


def repo_root() -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip()).resolve()


def remote_repo(root: Path) -> tuple[str, str]:
    remotes = run(["git", "remote", "-v"], cwd=root).stdout.splitlines()
    urls = [line.split()[1] for line in remotes if line.split()[0] == "origin"]
    if not urls:
        raise Pa9Error("No 'origin' remote found. Add a GitHub origin and rerun setup.")
    url = urls[0]
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
    if not match:
        raise Pa9Error(f"Origin is not a recognized GitHub URL: {url}")
    return match.group(1), match.group(2)


def github(token: str, method: str, endpoint: str, body: dict[str, Any] | None = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        API + endpoint,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "pa9pa9/0.1",
            **({"Content-Type": "application/json"} if data else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()
            return json.loads(content) if content else None
    except urllib.error.HTTPError as exc:
        reason = exc.read().decode(errors="replace")
        if exc.code == 401:
            raise Pa9Error("GitHub rejected the token. Re-run 'pa9pa9 setup' with a valid token.") from exc
        if exc.code == 403:
            raise Pa9Error("GitHub denied access. Check that the fine-grained token is approved and has Pull requests read/write access.") from exc
        raise Pa9Error(f"GitHub API returned HTTP {exc.code}: {reason}") from exc
    except urllib.error.URLError as exc:
        raise Pa9Error(f"Could not reach GitHub: {exc.reason}") from exc


def read_token(root: Path) -> str:
    env_token = os.environ.get("PA9PA9_GITHUB_TOKEN")
    if env_token:
        return env_token.strip()
    try:
        config = load_config(root)
        credentials = json.loads(TOKEN_FILE.read_text())
        if "token" in credentials:  # Upgrade credentials written by early versions.
            return str(credentials["token"])
        return str(credentials[f"{config['owner']}/{config['repo']}"])
    except (OSError, ValueError, KeyError) as exc:
        raise Pa9Error("GitHub token is not configured. Run 'pa9pa9 setup'.") from exc


def configure_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    lines = path.read_text().splitlines() if path.exists() else []
    required = [".pa9pa9/config.json", ".pa9pa9/state.json"]
    additions = [line for line in required if line not in lines]
    if additions:
        with path.open("a") as file:
            if path.exists() and path.stat().st_size:
                file.write("\n")
            file.write("\n".join(additions) + "\n")


def setup(_: argparse.Namespace) -> None:
    root = repo_root()
    owner, repo = remote_repo(root)
    if not shutil.which("codex"):
        raise Pa9Error("Codex CLI was not found on PATH. Install and sign in to Codex, then rerun setup.")
    # Verify the user-authenticated Codex CLI is ready without invoking a model.
    auth = run(["codex", "login", "status"], check=False)
    if auth.returncode:
        raise Pa9Error("Codex CLI is not signed in. Run 'codex login' and rerun setup.")

    skill_dest = root / ".agents" / "skills" / SKILL_NAME / "SKILL.md"
    rules_dest = root / ".pa9pa9" / "rules.md"
    skill_dest.parent.mkdir(parents=True, exist_ok=True)
    rules_dest.parent.mkdir(parents=True, exist_ok=True)
    templates = Path(__file__).parent / "templates"
    if not skill_dest.exists():
        shutil.copyfile(templates / "skill" / "SKILL.md", skill_dest)
        print(f"Created {skill_dest.relative_to(root)}")
    else:
        print(f"Keeping existing {skill_dest.relative_to(root)}")
    if not rules_dest.exists():
        shutil.copyfile(templates / "rules.md", rules_dest)
        print(f"Created {rules_dest.relative_to(root)}")
    else:
        print(f"Keeping existing {rules_dest.relative_to(root)}")

    config = {"owner": owner, "repo": repo}
    (root / CONFIG_FILE).write_text(json.dumps(config, indent=2) + "\n")
    os.chmod(root / CONFIG_FILE, 0o600)
    configure_gitignore(root)

    token = getpass.getpass("Fine-grained GitHub token (input hidden): ").strip()
    if not token:
        raise Pa9Error("No token entered. Setup files are ready; rerun setup to add credentials.")
    github(token, "GET", f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}")
    APP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        credentials = json.loads(TOKEN_FILE.read_text())
    except (OSError, ValueError):
        credentials = {}
    if "token" in credentials:
        credentials = {}
    credentials[f"{owner}/{repo}"] = token
    TOKEN_FILE.write_text(json.dumps(credentials, indent=2) + "\n")
    os.chmod(TOKEN_FILE, 0o600)
    print(f"Connected to {owner}/{repo}. Token saved in {TOKEN_FILE} with owner-only permissions.")
    print("Setup complete. Run 'pa9pa9 review' to review open pull requests.")


def load_config(root: Path) -> dict[str, str]:
    try:
        config = json.loads((root / CONFIG_FILE).read_text())
        return {"owner": config["owner"], "repo": config["repo"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise Pa9Error("Project is not configured. Run 'pa9pa9 setup'.") from exc


def load_state(root: Path) -> dict[str, Any]:
    path = root / STATE_FILE
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except (ValueError, OSError) as exc:
        raise Pa9Error(f"Could not read state file {path}: {exc}") from exc


def save_state(root: Path, state: dict[str, Any]) -> None:
    path = root / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def codex_review(root: Path, pull: dict[str, Any], base_sha: str) -> dict[str, Any]:
    head_sha = pull["head"]["sha"]
    number = pull["number"]
    head_ref = f"refs/pa9pa9/pr-{number}"
    base_ref = f"refs/pa9pa9/base-{number}"
    run([
        "git", "fetch", "--quiet", "origin",
        f"+refs/pull/{number}/head:{head_ref}",
        f"+refs/heads/{pull['base']['ref']}:{base_ref}",
    ], cwd=root)
    fetched_head = run(["git", "rev-parse", head_ref], cwd=root).stdout.strip()
    fetched_base = run(["git", "rev-parse", base_ref], cwd=root).stdout.strip()
    if fetched_head != head_sha or fetched_base != base_sha:
        raise Pa9Error(f"PR #{number} changed while fetching revisions. Run review again.")
    temp_dir = Path(tempfile.mkdtemp(prefix="pa9pa9-review-"))
    added_worktree = False
    try:
        run(["git", "worktree", "add", "--quiet", "--detach", str(temp_dir), head_sha], cwd=root)
        added_worktree = True
        # The setup files may be local and not committed. Copy the active policy into this isolated checkout.
        skill_src = root / ".agents" / "skills" / SKILL_NAME
        rules_src = root / ".pa9pa9" / "rules.md"
        skill_target = temp_dir / ".agents" / "skills" / SKILL_NAME
        skill_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_src, skill_target, dirs_exist_ok=True)
        rules_target = temp_dir / ".pa9pa9" / "rules.md"
        rules_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rules_src, rules_target)

        diff = run(["git", "diff", "--no-ext-diff", "--unified=5", f"{base_sha}...{head_sha}"], cwd=root).stdout
        prompt = (
            f"Review GitHub pull request #{pull['number']}: {pull.get('title', '')}\n"
            f"Author: {pull.get('user', {}).get('login', 'unknown')}\n"
            f"Base commit: {base_sha}\nHead commit: {head_sha}\n\n"
            f"PR description:\n{pull.get('body') or '(none)'}\n\n"
            "Use the $pa9pa9-review skill and follow .pa9pa9/rules.md. The checkout contains the PR head. "
            "Compare it to the base using git diff BASE...HEAD as needed. Return exactly the JSON object required by the skill.\n\n"
            f"Initial diff:\n```diff\n{diff[:120000]}\n```"
        )
        schema = Path(__file__).parent / "templates" / "output-schema.json"
        output_file = temp_dir / ".pa9pa9-review-output.json"
        result = run([
            "codex", "exec", "--cd", str(temp_dir), "--sandbox", "read-only", "--ephemeral",
            "--output-schema", str(schema), "--output-last-message", str(output_file), prompt,
        ], check=False, capture=True)
        if result.returncode:
            raise Pa9Error(f"Codex review failed for PR #{pull['number']}: {(result.stderr or result.stdout).strip()}")
        try:
            data = json.loads(output_file.read_text())
        except (ValueError, OSError) as exc:
            raise Pa9Error(f"Codex did not write valid structured output for PR #{pull['number']}.") from exc
        validate_review(data, pull)
        return data
    finally:
        if added_worktree:
            run(["git", "worktree", "remove", "--force", str(temp_dir)], cwd=root, check=False)
        shutil.rmtree(temp_dir, ignore_errors=True)
        run(["git", "update-ref", "-d", head_ref], cwd=root, check=False)
        run(["git", "update-ref", "-d", base_ref], cwd=root, check=False)


def validate_review(review: Any, pull: dict[str, Any]) -> None:
    if not isinstance(review, dict) or not isinstance(review.get("summary"), str) or not isinstance(review.get("findings"), list):
        raise Pa9Error(f"Codex returned an invalid review object for PR #{pull['number']}.")
    for finding in review["findings"]:
        if not isinstance(finding, dict) or not all(isinstance(finding.get(key), str) and finding[key] for key in ("title", "body", "path")):
            raise Pa9Error(f"Codex returned a malformed finding for PR #{pull['number']}.")
        if finding.get("severity") not in {"critical", "high", "medium", "low"}:
            raise Pa9Error(f"Codex returned an unknown finding severity for PR #{pull['number']}.")
        if not isinstance(finding.get("start_line"), int) or not isinstance(finding.get("end_line"), int):
            raise Pa9Error(f"Codex finding is missing line numbers for PR #{pull['number']}.")


def post_review(token: str, owner: str, repo: str, pull: dict[str, Any], review: dict[str, Any]) -> None:
    comments = []
    for finding in review["findings"]:
        comment: dict[str, Any] = {
            "path": finding["path"],
            "line": finding["end_line"],
            "side": "RIGHT",
            "body": f"**{finding['title']}**\n\n{finding['body']}",
        }
        if finding["start_line"] != finding["end_line"]:
            comment["start_line"] = finding["start_line"]
            comment["start_side"] = "RIGHT"
        comments.append(comment)
    payload = {
        "commit_id": pull["head"]["sha"],
        "body": review["summary"],
        "event": "REQUEST_CHANGES",
        "comments": comments,
    }
    github(token, "POST", f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/pulls/{pull['number']}/reviews", payload)


def review_command(args: argparse.Namespace) -> None:
    root = repo_root()
    config = load_config(root)
    token = read_token(root)
    owner, repo = config["owner"], config["repo"]
    pulls = []
    page = 1
    while True:
        batch = github(token, "GET", f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/pulls?state=open&per_page=100&page={page}")
        pulls.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    state = load_state(root)
    changed = False
    for pull in pulls:
        number = str(pull["number"])
        head_sha, base_sha = pull["head"]["sha"], pull["base"]["sha"]
        previous = state.get(number, {})
        if not args.force and previous.get("head_sha") == head_sha and previous.get("base_sha") == base_sha:
            print(f"PR #{number}: unchanged; skipped")
            continue
        print(f"PR #{number}: reviewing {head_sha[:8]} against base {base_sha[:8]}...")
        result = codex_review(root, pull, base_sha)
        # The PR may advance during analysis; never publish stale line comments.
        latest = github(token, "GET", f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/pulls/{number}")
        if latest["head"]["sha"] != head_sha or latest["base"]["sha"] != base_sha:
            print(f"PR #{number}: changed during review; skipped posting. Run again.")
            continue
        post_review(token, owner, repo, pull, result)
        state[number] = {"head_sha": head_sha, "base_sha": base_sha}
        save_state(root, state)
        changed = True
        print(f"PR #{number}: posted {len(result['findings'])} finding(s).")
    if not pulls:
        print("No open pull requests found.")
    elif not changed:
        print("Nothing to review.")


def main() -> int:
    parser = argparse.ArgumentParser(prog="pa9pa9", description="Review GitHub pull requests with Codex.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    setup_parser = subparsers.add_parser("setup", help="configure this clone and save GitHub credentials")
    setup_parser.set_defaults(func=setup)
    review_parser = subparsers.add_parser("review", help="review changed open pull requests")
    review_parser.add_argument("--force", action="store_true", help="review all open pull requests, even unchanged ones")
    review_parser.set_defaults(func=review_command)
    try:
        args = parser.parse_args()
        args.func(args)
        return 0
    except Pa9Error as exc:
        print(f"pa9pa9: error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\npa9pa9: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
