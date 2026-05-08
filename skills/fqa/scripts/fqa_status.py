#!/usr/bin/env python3
"""List FQA workflow status from .fqa feature workspaces.

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


def state_files(root: str) -> list[str]:
    return sorted(glob.glob(os.path.join(root, ".fqa", "features", "*", "state.yaml")))


def summarize(path: str) -> dict[str, Any]:
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
        "path": path,
        "raw": data,
    }


def print_table(rows: list[dict[str, Any]]) -> None:
    headers = ["Feature ID", "Feature", "State", "Session", "Updated", "Latest Run", "Next Gate"]
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
    print(f"State file: {row['path']}")
    print()
    print("Source:")
    for key in ["repo", "branch", "commit", "pr", "issue", "design_doc"]:
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
    parser.add_argument("--root", default=".", help="Repository root containing .fqa")
    args = parser.parse_args(argv)

    files = state_files(args.root)
    if not files:
        print("No FQA workflows found.")
        return 0

    rows = [summarize(path) for path in files]
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
