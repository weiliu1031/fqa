#!/usr/bin/env python3
"""Check FQA understanding artifacts for evidence-backed structure."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    pattern: str
    description: str


DESIGN_REQUIREMENTS = [
    Requirement(r"^## Source Summary$", "source summary"),
    Requirement(r"^### Documented Behavior$", "documented behavior"),
    Requirement(r"^### Inferred Behavior$", "inferred behavior"),
    Requirement(r"^### Unknown or Ambiguous Behavior$", "unknown or ambiguous behavior"),
    Requirement(r"^## Risk Seeds$", "risk seeds"),
    Requirement(r"risk_seed_id:\s*RS-DESIGN-", "design risk seed id"),
    Requirement(r"Evidence:", "evidence fields"),
    Requirement(r"Confidence:", "confidence fields"),
    Requirement(r"observable_assertion:", "observable assertion"),
    Requirement(r"^## Quality Gate$", "quality gate"),
]


IMPLEMENTATION_REQUIREMENTS = [
    Requirement(r"^## Change Inventory$", "change inventory"),
    Requirement(r"^## Component Map$", "component map"),
    Requirement(r"^## Execution Paths$", "execution paths"),
    Requirement(r"^## State and Invariants$", "state and invariants"),
    Requirement(r"^## Failure Paths$", "failure paths"),
    Requirement(r"^## Risk Seeds$", "risk seeds"),
    Requirement(r"risk_seed_id:\s*RS-IMPL-", "implementation risk seed id"),
    Requirement(r"Evidence:", "evidence fields"),
    Requirement(r"Confidence:", "confidence fields"),
    Requirement(r"observable_assertion:", "observable assertion"),
    Requirement(r"^## Quality Gate$", "quality gate"),
]


PLACEHOLDER_PATTERNS = [
    r"<feature_id>",
    r"Because <",
    r"causing <",
    r"^\s*-\s*$",
]


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _check_requirements(path: str, requirements: list[Requirement]) -> list[str]:
    errors: list[str] = []
    if not os.path.isfile(path):
        return [f"Missing understanding artifact: {path}"]

    content = _read(path)
    for requirement in requirements:
        if not re.search(requirement.pattern, content, re.MULTILINE):
            errors.append(f"{path}: missing {requirement.description}")

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, content, re.MULTILINE):
            errors.append(f"{path}: unresolved placeholder matches {pattern!r}")

    if "yes|no" in content:
        errors.append(f"{path}: unresolved quality gate value 'yes|no'")

    return errors


def check(workspace: str) -> list[str]:
    understanding_dir = os.path.join(workspace, "planning", "understanding")
    design_path = os.path.join(understanding_dir, "design-understanding.md")
    implementation_path = os.path.join(
        understanding_dir,
        "implementation-understanding.md",
    )
    errors: list[str] = []
    errors.extend(_check_requirements(design_path, DESIGN_REQUIREMENTS))
    errors.extend(_check_requirements(implementation_path, IMPLEMENTATION_REQUIREMENTS))
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Check FQA design and implementation understanding artifacts.",
    )
    parser.add_argument("workspace", help="Path to <fqa_base_dir>/features/<feature_id>")
    args = parser.parse_args(argv)

    errors = check(args.workspace)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"FQA understanding artifacts look complete: {args.workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
