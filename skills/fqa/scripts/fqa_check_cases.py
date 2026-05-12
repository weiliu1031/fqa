#!/usr/bin/env python3
"""Check FQA test plans and cases for actionable quality gates."""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys


WEAK_PATTERNS = [
    r"\bverify (the )?feature works\b",
    r"\btest error handling\b",
    r"\btest performance\b",
    r"\bcheck logs\b",
    r"\btest compatibility\b",
    r"\brun basic workflow\b",
    r"\bworks\b",
    r"\bis normal\b",
    r"\bacceptable\b",
    r"\bdoes not fail\b",
]

CASE_REQUIRED_PATTERNS = {
    "traceability section": r"^traceability:",
    "risk seed id": r"RS-(DESIGN|IMPL)-\d+",
    "source claims": r"source_claims:",
    "source files": r"source_files:",
    "oracle section": r"^oracle:",
    "oracle type": r"type:\s*(exact_response|data_invariant|state_invariant|compatibility|observability|resource)",
    "oracle expected": r"expected:\s*\S",
    "negative assertions": r"negative_assertions:",
    "diagnostics section": r"^diagnostics:",
    "failure triage": r"failure_triage:\s*\S",
    "evidence to collect": r"evidence_to_collect:",
    "flakiness controls": r"^flakiness_controls:",
    "timeout": r"timeout:\s*\S",
    "polling interval": r"polling_interval:\s*\S",
    "retry policy": r"retry_policy:\s*\S",
    "cleanup method": r"method:\s*\S",
}

PLAN_REQUIRED_PATTERNS = {
    "coverage matrix": r"^coverage_matrix:",
    "scenario matrix": r"^scenario_matrix:",
    "coverage status": r"status:\s*(covered|partial|missing)",
    "risk seed id": r"RS-(DESIGN|IMPL)-\d+",
    "scenario id": r"SCN-\d+",
    "scenario category": r"category:\s*(type_variant|operation_variant|validation|boundary|system_mode|compatibility|concurrency|other)",
    "decision status": r"decision_status:\s*(confirmed|needs_decision|not_applicable)",
}


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _has_nonempty_list_item(content: str, key: str) -> bool:
    pattern = rf"{re.escape(key)}:\n(?:\s+-\s+\S.*\n?)+"
    return re.search(pattern, content) is not None


def _check_required(path: str, content: str, requirements: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for description, pattern in requirements.items():
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"{path}: missing {description}")
    return errors


def _check_placeholders(path: str, content: str) -> list[str]:
    errors: list[str] = []
    for pattern in [r'""', r"<[^>]+>", r"\|\s*$"]:
        if re.search(pattern, content, re.MULTILINE):
            errors.append(f"{path}: unresolved placeholder matches {pattern!r}")
    return errors


def _check_weak_patterns(path: str, content: str) -> list[str]:
    errors: list[str] = []
    lowered = content.lower()
    for pattern in WEAK_PATTERNS:
        if re.search(pattern, lowered):
            errors.append(f"{path}: weak case wording matches {pattern!r}")
    return errors


def _check_case(path: str) -> list[str]:
    content = _read(path)
    errors = _check_required(path, content, CASE_REQUIRED_PATTERNS)
    errors.extend(_check_placeholders(path, content))
    errors.extend(_check_weak_patterns(path, content))

    for key in ["source_claims", "source_files", "assertions", "evidence_to_collect"]:
        if not _has_nonempty_list_item(content, key):
            errors.append(f"{path}: {key} must contain at least one non-empty item")

    observability_block = re.search(
        r"^observability:\n(?P<body>(?:\s+.*\n?)+?)(?:^[a-zA-Z_]+:|\Z)",
        content,
        re.MULTILINE,
    )
    if not observability_block or not re.search(r"-\s+\S", observability_block.group("body")):
        errors.append(f"{path}: observability must request logs, metrics, or traces")

    return errors


def _check_plan(path: str) -> list[str]:
    if not os.path.isfile(path):
        return [f"Missing test plan: {path}"]
    content = _read(path)
    errors = _check_required(path, content, PLAN_REQUIRED_PATTERNS)
    errors.extend(_check_placeholders(path, content))
    if "status: missing" in content and not re.search(r"gap:\s*\S", content):
        errors.append(f"{path}: missing coverage entries must explain gap")
    if "decision_status: needs_decision" in content:
        if "open_decisions:" not in content or not re.search(r"decision_id:\s*DEC-\d+", content):
            errors.append(f"{path}: scenarios needing decisions must have open_decisions entries")
    if re.search(r"scenario_id:\s*SCN-\d+", content) and not re.search(r"case_id:\s*FQA-\d+", content):
        errors.append(f"{path}: scenario rows must map to FQA case IDs unless explicitly blocked")
    return errors


def check(workspace: str) -> list[str]:
    planning_dir = os.path.join(workspace, "planning")
    errors = _check_plan(os.path.join(planning_dir, "test-plan.yaml"))

    case_paths = sorted(glob.glob(os.path.join(planning_dir, "cases", "FQA-*.yaml")))
    if not case_paths:
        errors.append(f"No FQA case files found under {os.path.join(planning_dir, 'cases')}")
        return errors

    for path in case_paths:
        errors.extend(_check_case(path))
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check FQA test plan and case quality.")
    parser.add_argument("workspace", help="Path to <fqa_base_dir>/features/<feature_id>")
    args = parser.parse_args(argv)

    errors = check(args.workspace)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"FQA test plan and cases look actionable: {args.workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
