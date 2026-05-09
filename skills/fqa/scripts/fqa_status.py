#!/usr/bin/env python3
"""List FQA workflow status from global and legacy feature workspaces.

This helper intentionally parses only the simple YAML shape used by FQA
state.yaml files so it does not add runtime dependencies.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Any


NEXT_GATE = {
    "Drafting": "finish feature understanding and generate cases",
    "CaseReview": "approve, reject, or edit test cases",
    "WaitingCluster": "provide cluster access and execution permission",
    "ScriptReady": "approve execution on the target cluster",
    "Running": "wait for run completion and evidence collection",
    "ReportReview": "accept report or request corrections",
    "IssueReview": "approve, reject, merge, or edit issue candidates",
    "IssueCreated": "provide or track fix references",
    "WaitingFix": "provide fix PR, commit, image, or build",
    "Regression": "accept regression results or request rerun",
    "Closed": "no action required",
}


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value in {"", "null", "None", "~"}:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "[]":
        return []
    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        return value[1:-1]
    return value


def parse_simple_yaml(path: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.lstrip().startswith("- "):
                continue
            indent = len(line) - len(line.lstrip(" "))
            if ":" not in line:
                continue
            key, raw_value = line.strip().split(":", 1)
            while stack and indent <= stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]
            if raw_value.strip() == "":
                child: dict[str, Any] = {}
                parent[key] = child
                stack.append((indent, child))
            else:
                parent[key] = _parse_scalar(raw_value)
    return root


def nested(data: dict[str, Any], *keys: str, default: Any = "-") -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    if cur is None or cur == "":
        return default
    return cur


def default_base_dir() -> str:
    if os.environ.get("FQA_BASE_DIR"):
        return os.path.expanduser(os.environ["FQA_BASE_DIR"])
    if os.environ.get("CODEX_HOME"):
        return os.path.join(os.path.expanduser(os.environ["CODEX_HOME"]), "fqa")
    return os.path.expanduser("~/.codex/fqa")


def _realpath(path: str | None) -> str | None:
    if not path or path == "-":
        return None
    return os.path.realpath(os.path.expanduser(path))


def _state_files_under(pattern_root: str, relative_pattern: str) -> list[str]:
    pattern = os.path.join(pattern_root, relative_pattern)
    return sorted(glob.glob(pattern))


def global_state_files(base_dir: str) -> list[str]:
    return _state_files_under(base_dir, os.path.join("features", "*", "state.yaml"))


def legacy_state_files(root: str) -> list[str]:
    return _state_files_under(root, os.path.join(".fqa", "features", "*", "state.yaml"))


def _repo_matches(data: dict[str, Any], root: str) -> bool:
    wanted = _realpath(root)
    if wanted is None:
        return True
    candidates = [
        nested(data, "source", "repo", default=None),
        nested(data, "source", "repo_path", default=None),
        nested(data, "source", "worktree_path", default=None),
    ]
    for candidate in candidates:
        resolved = _realpath(candidate)
        if resolved == wanted:
            return True
    return False


def summarize(path: str, storage: str) -> dict[str, Any]:
    data = parse_simple_yaml(path)
    state = str(nested(data, "state", default="unknown"))
    return {
        "feature_id": nested(data, "feature_id"),
        "feature": nested(data, "feature_name"),
        "state": state,
        "session": nested(data, "active_session", "status"),
        "updated": nested(data, "workspace", "updated_at"),
        "latest_run": nested(data, "latest", "run_id"),
        "next_gate": NEXT_GATE.get(state, "inspect state.yaml"),
        "storage": storage,
        "repo": nested(data, "source", "repo", default="-"),
        "worktree": nested(data, "source", "worktree_path", default="-"),
        "path": path,
        "raw": data,
    }


def print_table(rows: list[dict[str, Any]]) -> None:
    headers = [
        "Feature ID",
        "Feature",
        "State",
        "Session",
        "Updated",
        "Latest Run",
        "Storage",
        "Next Gate",
    ]
    print(" | ".join(headers))
    for row in rows:
        print(
            " | ".join(
                str(row[key])
                for key in [
                    "feature_id",
                    "feature",
                    "state",
                    "session",
                    "updated",
                    "latest_run",
                    "storage",
                    "next_gate",
                ]
            )
        )


def print_detail(row: dict[str, Any]) -> None:
    data = row["raw"]
    print(f"Feature ID: {row['feature_id']}")
    print(f"Feature: {row['feature']}")
    print(f"State: {row['state']}")
    print(f"Next gate: {row['next_gate']}")
    print(f"Storage: {row['storage']}")
    print(f"State file: {row['path']}")
    print()
    print("Source:")
    for key in [
        "repo",
        "repo_path",
        "worktree_path",
        "branch",
        "commit",
        "pr",
        "issue",
        "design_doc",
    ]:
        print(f"- {key}: {nested(data, 'source', key)}")
    print()
    print("Session:")
    for key in ["session_id", "owner", "status", "started_at", "updated_at"]:
        print(f"- {key}: {nested(data, 'active_session', key)}")
    print()
    print("Artifacts:")
    artifacts = data.get("artifacts", {})
    if isinstance(artifacts, dict):
        for key, value in artifacts.items():
            print(f"- {key}: {value if value not in (None, '') else '-'}")
    print()
    print("Latest:")
    print(f"- run_id: {nested(data, 'latest', 'run_id')}")
    print(f"- report: {nested(data, 'latest', 'report')}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Show FQA workflow status.")
    parser.add_argument("feature_id", nargs="?", help="Optional feature_id to show")
    parser.add_argument(
        "--base",
        default=default_base_dir(),
        help="FQA base directory containing features/ (default: FQA_BASE_DIR, CODEX_HOME/fqa, or ~/.codex/fqa)",
    )
    parser.add_argument(
        "--root",
        help="Repository root used to filter global workflows and scan legacy .fqa",
    )
    parser.add_argument(
        "--legacy-only",
        action="store_true",
        help="Scan only legacy <root>/.fqa/features workspaces",
    )
    args = parser.parse_args(argv)

    if args.legacy_only and not args.root:
        print("--legacy-only requires --root", file=sys.stderr)
        return 2

    rows: list[dict[str, Any]] = []
    base_dir = os.path.abspath(os.path.expanduser(args.base))

    if not args.legacy_only:
        for path in global_state_files(base_dir):
            row = summarize(path, "global")
            if args.root and not _repo_matches(row["raw"], args.root):
                continue
            rows.append(row)

    if args.root:
        root = os.path.abspath(os.path.expanduser(args.root))
        rows.extend(summarize(path, "repo_local_legacy") for path in legacy_state_files(root))

    if not rows:
        print("No FQA workflows found.")
        return 0

    rows = sorted(rows, key=lambda row: (str(row["feature_id"]), str(row["path"])))
    if args.feature_id:
        matches = [row for row in rows if row["feature_id"] == args.feature_id]
        if not matches:
            print(f"No FQA workflow found for feature_id: {args.feature_id}", file=sys.stderr)
            print_table(rows)
            return 1
        print_detail(matches[0])
        return 0

    print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
