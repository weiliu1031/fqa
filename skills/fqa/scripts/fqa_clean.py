#!/usr/bin/env python3
"""Archive or delete one FQA feature workspace.

The helper defaults to a dry run. It only mutates files when --force is set.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from typing import Any

from fqa_status import default_base_dir, global_state_files, nested, parse_simple_yaml


ACTIVE_SESSION_STATUSES = {"active"}


def _quote(value: Any) -> str:
    if value is None or value == "-":
        return "null"
    return json.dumps(str(value))


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_feature_id(feature_id: str) -> str:
    if not feature_id or feature_id in {".", ".."}:
        raise ValueError("feature_id must not be empty")
    if "/" in feature_id or "\\" in feature_id:
        raise ValueError("feature_id must be a workspace name, not a path")
    return feature_id


def _workspace_for(base_dir: str, feature_id: str) -> str:
    base_real = os.path.realpath(os.path.abspath(os.path.expanduser(base_dir)))
    workspace = os.path.realpath(os.path.join(base_real, "features", feature_id))
    features_root = os.path.realpath(os.path.join(base_real, "features"))
    if os.path.commonpath([features_root, workspace]) != features_root:
        raise ValueError(f"workspace escapes FQA features directory: {workspace}")
    return workspace


def _load_state(workspace: str) -> dict[str, Any]:
    state_path = os.path.join(workspace, "state.yaml")
    if not os.path.isfile(state_path):
        raise FileNotFoundError(f"Missing state file: {state_path}")
    return parse_simple_yaml(state_path)


def _is_active(data: dict[str, Any]) -> bool:
    status = nested(data, "active_session", "status", default=None)
    return str(status) in ACTIVE_SESSION_STATUSES


def _next_archive_path(base_dir: str, feature_id: str) -> str:
    archive_root = os.path.join(base_dir, "archive")
    base_name = f"{feature_id}-{_timestamp()}"
    candidate = os.path.join(archive_root, base_name)
    suffix = 2
    while os.path.exists(candidate):
        candidate = os.path.join(archive_root, f"{base_name}-{suffix}")
        suffix += 1
    return candidate


def _registry_row(path: str) -> dict[str, Any]:
    data = parse_simple_yaml(path)
    return {
        "feature_id": nested(data, "feature_id"),
        "feature_name": nested(data, "feature_name"),
        "state": nested(data, "state"),
        "workspace": os.path.dirname(path),
        "source_repo": nested(data, "source", "repo", default=None),
        "source_repo_path": nested(data, "source", "repo_path", default=None),
        "source_worktree_path": nested(data, "source", "worktree_path", default=None),
        "branch": nested(data, "source", "branch", default=None),
        "commit": nested(data, "source", "commit", default=None),
        "updated_at": nested(data, "workspace", "updated_at", default=None),
    }


def rebuild_registry(base_dir: str) -> None:
    rows = sorted(
        (_registry_row(path) for path in global_state_files(base_dir)),
        key=lambda row: str(row["feature_id"]),
    )
    registry_path = os.path.join(base_dir, "registry.yaml")
    os.makedirs(base_dir, exist_ok=True)
    lines = [
        "version: 1",
        f"updated_at: {_quote(_iso_timestamp())}",
        "features:",
    ]
    if not rows:
        lines[-1] = "features: []"
    else:
        for row in rows:
            lines.extend(
                [
                    f"  - feature_id: {_quote(row['feature_id'])}",
                    f"    feature_name: {_quote(row['feature_name'])}",
                    f"    state: {_quote(row['state'])}",
                    f"    workspace: {_quote(row['workspace'])}",
                    f"    source_repo: {_quote(row['source_repo'])}",
                    f"    source_repo_path: {_quote(row['source_repo_path'])}",
                    f"    source_worktree_path: {_quote(row['source_worktree_path'])}",
                    f"    branch: {_quote(row['branch'])}",
                    f"    commit: {_quote(row['commit'])}",
                    f"    updated_at: {_quote(row['updated_at'])}",
                ]
            )
    with open(registry_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_archive_manifest(destination: str, workspace: str, feature_id: str) -> None:
    manifest_path = os.path.join(destination, "archive-manifest.yaml")
    lines = [
        "version: 1",
        f"feature_id: {_quote(feature_id)}",
        f"archived_at: {_quote(_iso_timestamp())}",
        f"original_workspace: {_quote(workspace)}",
        "reason: fqa_clean archive",
    ]
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def print_plan(
    *,
    action: str,
    workspace: str,
    destination: str | None,
    state: dict[str, Any],
    blocked: list[str],
    force: bool,
) -> None:
    print(f"Feature ID: {nested(state, 'feature_id')}")
    print(f"State: {nested(state, 'state')}")
    print(f"Session: {nested(state, 'active_session', 'status')}")
    print(f"Workspace: {workspace}")
    print(f"Action: {action}")
    if destination:
        print(f"Destination: {destination}")
    print(f"Mode: {'execute' if force else 'dry-run'}")
    if blocked:
        print("Blocked:")
        for reason in blocked:
            print(f"- {reason}")
    elif force:
        print("Result: ready to execute")
    else:
        print("Result: dry-run only; add --force to execute")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Archive or delete one FQA workflow.")
    parser.add_argument("feature_id", help="Feature workspace ID under <base>/features/")
    parser.add_argument(
        "--base",
        default=default_base_dir(),
        help="FQA base directory containing features/ (default: FQA_BASE_DIR, CODEX_HOME/fqa, or ~/.codex/fqa)",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--archive",
        action="store_true",
        help="Move the workspace to <base>/archive/<feature_id>-<timestamp>/ (default action).",
    )
    action.add_argument(
        "--delete",
        action="store_true",
        help="Permanently delete the workspace.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Execute the archive or delete action. Without this flag only a dry-run is printed.",
    )
    parser.add_argument(
        "--takeover",
        action="store_true",
        help="Allow cleanup when state.yaml or .lock indicates an active session.",
    )
    args = parser.parse_args(argv)

    try:
        feature_id = _safe_feature_id(args.feature_id)
        base_dir = os.path.abspath(os.path.expanduser(args.base))
        workspace = _workspace_for(base_dir, feature_id)
        if not os.path.isdir(workspace):
            print(f"No FQA workflow workspace found: {workspace}", file=sys.stderr)
            return 1
        state = _load_state(workspace)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    action_name = "delete" if args.delete else "archive"
    destination = None if action_name == "delete" else _next_archive_path(base_dir, feature_id)

    blocked: list[str] = []
    if _is_active(state):
        blocked.append("state.yaml records an active session; pass --takeover to override")
    if os.path.exists(os.path.join(workspace, ".lock")):
        blocked.append(".lock exists; pass --takeover to override")
    if blocked and args.takeover:
        blocked = []

    print_plan(
        action=action_name,
        workspace=workspace,
        destination=destination,
        state=state,
        blocked=blocked,
        force=args.force,
    )

    if blocked:
        return 2 if args.force else 0
    if not args.force:
        return 0

    if action_name == "delete":
        shutil.rmtree(workspace)
        print(f"Deleted: {workspace}")
    else:
        assert destination is not None
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.move(workspace, destination)
        write_archive_manifest(destination, workspace, feature_id)
        print(f"Archived: {destination}")

    rebuild_registry(base_dir)
    print(f"Registry rebuilt: {os.path.join(base_dir, 'registry.yaml')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
