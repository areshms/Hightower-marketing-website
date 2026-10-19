"""blog_pipeline/deploy.py — git commit + Netlify deploy hook."""
from __future__ import annotations
import subprocess, os, urllib.request
from pathlib import Path
from typing import List

from blog_pipeline.config import REPO_ROOT, NETLIFY_DEPLOY_HOOK


def run_git(args: List[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def commit_and_push(
    files: List[Path],
    message: str,
    repo_root: Path = REPO_ROOT,
) -> bool:
    """Stage, commit, and push the listed files."""
    for f in files:
        run_git(["add", str(f)], cwd=repo_root)
    result = run_git(["commit", "-m", message], cwd=repo_root)
    if result.returncode != 0 and "nothing to commit" not in result.stdout:
        raise RuntimeError(f"git commit failed: {result.stderr}")
    push = run_git(["push", "origin", "main"], cwd=repo_root)
    return push.returncode == 0


def deploy_netlify(deploy_hook: str | None = None, timeout: int = 30) -> bool:
    """Hit the Netlify build hook URL; returns True on HTTP 200."""
    hook = deploy_hook or NETLIFY_DEPLOY_HOOK or os.environ.get("NETLIFY_DEPLOY_HOOK")
    if not hook:
        print("No Netlify deploy hook configured; skipping.")
        return False
    req = urllib.request.Request(hook, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Netlify deploy hook failed: {e}")
        return False
