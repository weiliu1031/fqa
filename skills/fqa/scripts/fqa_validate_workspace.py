#!/usr/bin/env python3
"""Validate an FQA feature workspace."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from fqa_status import nested, parse_simple_yaml


VALID_STATES = {
    "Drafting",
    "CaseReview",
    "WaitingCluster",
    "ScriptReady",
    "Running",
    "ReportReview",
    "IssueReview",
    "IssueCreated",
    "WaitingFix",
    "Regression",
    "Closed",
}


def _join(workspace: str, value: Any) -> str | None:
    if value is None or value == "":
        return None
    path = str(value)
    if os.path.isabs(path):
        return path
    return os.path.join(workspace, path)


def validate(workspace: str) -> list[str]:
    errors: list[str] = []
    state_path = os.path.join(workspace, "state.yaml")
    if not os.path.isfile(state_path):
        return [f"Missing state file: {state_path}"]

    data = parse_simple_yaml(state_path)
    state = nested(data, "state", default=None)
    if state not in VALID_STATES:
        errors.append(f"Invalid state: {state}")

    for key in ["feature_id"]:
        if nested(data, key, default=None) is None:
            errors.append(f"Missing required state field: {key}")

    artifacts = data.get("artifacts", {})
    if not isinstance(artifacts, dict):
        errors.append("state.artifacts must be a mapping")
        return errors

    for key in ["cases_dir", "scripts_dir", "runs_dir", "reports_dir", "issues_dir"]:
        path = _join(workspace, artifacts.get(key))
        if path and not os.path.isdir(path):
            errors.append(f"Missing artifact directory {key}: {path}")

    for key in [
        "feature_intake",
        "design_understanding",
        "implementation_understanding",
        "test_plan",
    ]:
        path = _join(workspace, artifacts.get(key))
        if path and not os.path.isfile(path):
            errors.append(f"Missing artifact file {key}: {path}")

    latest_report = _join(workspace, nested(data, "latest", "report", default=None))
    if latest_report and not os.path.isfile(latest_report):
        errors.append(f"Missing latest report: {latest_report}")

    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate an FQA feature workspace.")
    parser.add_argument(
        "workspace",
        help="Path to <fqa_base_dir>/features/<feature_id> or legacy .fqa/features/<feature_id>",
    )
    args = parser.parse_args(argv)

    errors = validate(args.workspace)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"FQA workspace is valid: {args.workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
