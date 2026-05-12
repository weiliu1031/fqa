#!/usr/bin/env python3
"""Prepare a local Milvus worktree for FQA execution.

The helper defaults to a dry run. It locates an existing worktree for the target
branch or commit, or plans a new worktree under the requested root. It executes
git worktree creation, build, and service start only when --execute is set.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass
class Worktree:
    path: str
    head: str | None
    branch: str | None


def _run(cmd: list[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "fqa-feature"


def _repo_name(repo: str) -> str:
    base = repo.rstrip("/").split("/")[-1]
    if base.endswith(".git"):
        base = base[:-4]
    return _slug(base or "milvus")


def _is_git_repo(path: str) -> bool:
    try:
        result = _run(["git", "-C", path, "rev-parse", "--show-toplevel"], check=False)
    except FileNotFoundError:
        return False
    return result.returncode == 0


def _looks_like_milvus_repo(path: str) -> bool:
    if not _is_git_repo(path):
        return False
    if os.path.basename(os.path.realpath(path)) == "milvus":
        return True
    result = _run(["git", "-C", path, "remote", "-v"], check=False)
    return "milvus-io/milvus" in result.stdout or "milvus.git" in result.stdout


def _parse_worktrees(output: str) -> list[Worktree]:
    worktrees: list[Worktree] = []
    current: dict[str, str] = {}
    for line in output.splitlines():
        if not line:
            if current:
                worktrees.append(
                    Worktree(
                        path=current["worktree"],
                        head=current.get("HEAD"),
                        branch=current.get("branch"),
                    )
                )
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        worktrees.append(
            Worktree(
                path=current["worktree"],
                head=current.get("HEAD"),
                branch=current.get("branch"),
            )
        )
    return worktrees


def _worktrees(seed_repo: str) -> list[Worktree]:
    result = _run(["git", "-C", seed_repo, "worktree", "list", "--porcelain"])
    return _parse_worktrees(result.stdout)


def _branch_matches(worktree_branch: str | None, wanted: str | None) -> bool:
    if not wanted or not worktree_branch:
        return False
    branch = worktree_branch.removeprefix("refs/heads/")
    return branch == wanted or worktree_branch == wanted


def find_worktree(seed_repo: str, branch: str | None, commit: str | None) -> Worktree | None:
    for worktree in _worktrees(seed_repo):
        if commit and worktree.head and worktree.head.startswith(commit):
            return worktree
        if _branch_matches(worktree.branch, branch):
            return worktree
    return None


def _default_worktree_root(feature_id: str) -> str:
    return os.path.expanduser(os.path.join("~/Code", _slug(feature_id)))


def _shell_command(command: str, cwd: str) -> str:
    return f"cd {cwd} && {command}"


def _build_command() -> str:
    return "source ~/.profile && source scripts/setenv.sh && make milvus"


def _start_command() -> str:
    return "source ~/.profile && source scripts/setenv.sh && ./scripts/start_standalone.sh"


def _print_plan(
    *,
    selected: Worktree | None,
    planned_path: str,
    seed_repo: str | None,
    repo_url: str | None,
    branch: str | None,
    base_ref: str,
    execute: bool,
    build: bool,
    start: bool,
    skip_large: bool,
) -> None:
    target_path = selected.path if selected else planned_path
    print(f"Mode: {'execute' if execute else 'dry-run'}")
    print(f"Selected worktree: {target_path}")
    print(f"Existing worktree: {'yes' if selected else 'no'}")
    print(f"Skip large-data cases: {'yes' if skip_large else 'no'}")
    if not selected:
        source = seed_repo or repo_url
        print(f"Create worktree from: {source}")
        print(f"Base ref: {branch or base_ref}")
    if build:
        print(f"Build command: {_shell_command(_build_command(), target_path)}")
    if start:
        print(f"Start command: {_shell_command(_start_command(), target_path)}")


def _ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _execute_create_worktree(
    *,
    seed_repo: str | None,
    repo_url: str | None,
    target_path: str,
    branch: str | None,
    base_ref: str,
) -> None:
    _ensure_parent(target_path)
    if seed_repo:
        cmd = ["git", "-C", seed_repo, "worktree", "add", target_path, branch or base_ref]
        subprocess.run(cmd, check=True)
        return
    if not repo_url:
        raise RuntimeError("repo_url is required when seed_repo is not available")
    subprocess.run(["git", "clone", repo_url, target_path], check=True)
    if branch:
        subprocess.run(["git", "-C", target_path, "checkout", branch], check=True)
    elif base_ref:
        subprocess.run(["git", "-C", target_path, "checkout", base_ref], check=True)


def _execute_shell(command: str, cwd: str) -> None:
    subprocess.run(["bash", "-lc", command], cwd=cwd, check=True)


def _candidate_seed_repos(paths: Iterable[str]) -> list[str]:
    return [
        os.path.abspath(os.path.expanduser(path))
        for path in paths
        if path and _looks_like_milvus_repo(os.path.expanduser(path))
    ]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Prepare a local Milvus worktree for FQA execution.")
    parser.add_argument("--feature-id", required=True, help="FQA feature ID used for default worktree placement.")
    parser.add_argument("--repo-url", default="https://github.com/milvus-io/milvus.git", help="Milvus repository URL.")
    parser.add_argument("--seed-repo", action="append", default=[], help="Existing Milvus repo or worktree used to inspect git worktrees.")
    parser.add_argument("--branch", help="Target feature branch to locate or create.")
    parser.add_argument("--commit", help="Target commit prefix to locate.")
    parser.add_argument("--base-ref", default="master", help="Base ref used when creating a new worktree without --branch.")
    parser.add_argument("--worktree-root", help="Directory under which a new worktree should be created.")
    parser.add_argument("--execute", action="store_true", help="Create/build/start instead of printing a dry-run plan.")
    parser.add_argument("--no-build", action="store_true", help="Skip make milvus.")
    parser.add_argument("--no-start", action="store_true", help="Skip scripts/start_standalone.sh.")
    parser.add_argument("--include-large-data", action="store_true", help="Do not mark large-data cases skipped for local mode.")
    args = parser.parse_args(argv)

    default_seed_candidates = [
        os.getcwd(),
        os.path.expanduser("~/Code/milvus"),
        os.path.expanduser("~/code/milvus/master/milvus"),
        os.path.expanduser("~/Code/milvus/master/milvus"),
    ]
    seed_repos = _candidate_seed_repos([*args.seed_repo, *default_seed_candidates])
    seed_repo = seed_repos[0] if seed_repos else None

    selected = find_worktree(seed_repo, args.branch, args.commit) if seed_repo else None
    root = os.path.abspath(os.path.expanduser(args.worktree_root or _default_worktree_root(args.feature_id)))
    planned_path = os.path.join(root, _repo_name(args.repo_url))
    build = not args.no_build
    start = not args.no_start
    skip_large = not args.include_large_data

    _print_plan(
        selected=selected,
        planned_path=planned_path,
        seed_repo=seed_repo,
        repo_url=args.repo_url,
        branch=args.branch,
        base_ref=args.base_ref,
        execute=args.execute,
        build=build,
        start=start,
        skip_large=skip_large,
    )

    if not args.execute:
        return 0

    target_path = selected.path if selected else planned_path
    if selected is None:
        _execute_create_worktree(
            seed_repo=seed_repo,
            repo_url=args.repo_url,
            target_path=target_path,
            branch=args.branch,
            base_ref=args.base_ref,
        )
    if build:
        _execute_shell(_build_command(), target_path)
    if start:
        _execute_shell(_start_command(), target_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
