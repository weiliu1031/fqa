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
    "execution modes": r"execution_modes:",
    "local mode support": r"local:\n\s+supported:\s*(true|false)",
    "remote mode support": r"remote:\n\s+supported:\s*(true|false)",
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
    "dimension coverage": r"^dimension_coverage:",
    "scenario matrix": r"^scenario_matrix:",
    "coverage status": r"status:\s*(covered|partial|missing)",
    "risk seed id": r"RS-(DESIGN|IMPL)-\d+",
    "scenario id": r"SCN-\d+",
    "scenario category": r"category:\s*(type_variant|operation_variant|validation|boundary|system_mode|compatibility|concurrency|other)",
    "decision status": r"decision_status:\s*(confirmed|needs_decision|not_applicable)",
}

BLOCKED_GAP_PATTERNS = [
    r"\brequires?\b",
    r"\bdepends on\b",
    r"\bcan be skipped\b",
    r"\bif no\b",
    r"\bneeds? decision\b",
    r"\bpending\b",
    r"\bnot available\b",
    r"\bafter .*approval\b",
]

ARRAY_REQUIRED_APPEND_TYPES = {
    "Bool",
    "Int8",
    "Int16",
    "Int32",
    "Int64",
    "Float",
    "Double",
    "VarChar",
}
ARRAY_REQUIRED_REMOVE_TYPES = ARRAY_REQUIRED_APPEND_TYPES
ARRAY_REQUIRED_BOUNDARIES = {
    "empty_base",
    "single_element",
    "duplicate",
    "no_match",
    "remove_all",
    "exact_capacity",
    "overflow",
    "varchar_max_length",
}
ARRAY_REQUIRED_SYSTEM_MODES = {
    "multi_field",
    "mixed_insert_update",
    "flush_reload_filter",
    "compatibility",
    "concurrency",
    "sdk",
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


def _split_top_level_blocks(content: str, key: str) -> list[str]:
    match = re.search(rf"^{re.escape(key)}:\n", content, re.MULTILINE)
    if not match:
        return []
    start = match.end()
    next_top = re.search(r"^[a-zA-Z_]+:\n", content[start:], re.MULTILINE)
    section = content[start:] if not next_top else content[start : start + next_top.start()]
    starts = list(re.finditer(r"^  - ", section, re.MULTILINE))
    if not starts:
        return []
    blocks: list[str] = []
    for index, item in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(section)
        blocks.append(section[item.start() : end])
    return blocks


def _extract_inline_list(block: str, key: str) -> set[str]:
    match = re.search(rf"{re.escape(key)}:\s*\[(?P<items>[^\]]*)\]", block)
    if not match:
        return set()
    return {
        item.strip().strip("'\"")
        for item in match.group("items").split(",")
        if item.strip()
    }


def _extract_block_list(block: str, key: str) -> set[str]:
    lines = block.splitlines()
    values: set[str] = set()
    for index, line in enumerate(lines):
        if not re.match(rf"\s*{re.escape(key)}:\s*$", line):
            continue
        base_indent = len(line) - len(line.lstrip(" "))
        for child in lines[index + 1 :]:
            if not child.strip():
                continue
            indent = len(child) - len(child.lstrip(" "))
            if indent <= base_indent:
                break
            item = re.match(r"\s*-\s+(.+?)\s*$", child)
            if item:
                values.add(item.group(1).strip().strip("'\""))
    return values


def _extract_list(block: str, key: str) -> set[str]:
    return _extract_inline_list(block, key) or _extract_block_list(block, key)


def _extract_mapping_section(block: str, key: str) -> str:
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if not re.match(rf"\s*{re.escape(key)}:\s*$", line):
            continue
        base_indent = len(line) - len(line.lstrip(" "))
        section: list[str] = []
        for child in lines[index + 1 :]:
            if not child.strip():
                section.append(child)
                continue
            indent = len(child) - len(child.lstrip(" "))
            if indent <= base_indent:
                break
            section.append(child)
        return "\n".join(section)
    return ""


def _has_array_partial_update(content: str) -> bool:
    return re.search(r"ARRAY_(APPEND|REMOVE)|array_partial_update", content, re.IGNORECASE) is not None


def _check_covered_gaps(path: str, content: str) -> list[str]:
    errors: list[str] = []
    for section_name in ["coverage_matrix", "dimension_coverage"]:
        for block in _split_top_level_blocks(content, section_name):
            if not re.search(r"status:\s*covered\b", block):
                continue
            gap_match = re.search(r"gaps?:\s*(?P<gap>.*)", block)
            gap_text = gap_match.group("gap") if gap_match else ""
            if not gap_text.strip() or gap_text.strip() in {"[]", "none", "null"}:
                continue
            lowered = gap_text.lower()
            for pattern in BLOCKED_GAP_PATTERNS:
                if re.search(pattern, lowered):
                    errors.append(
                        f"{path}: {section_name} uses status covered with unresolved gap matching {pattern!r}"
                    )
                    break
    return errors


def _check_decision_case_mixing(path: str, content: str) -> list[str]:
    errors: list[str] = []
    decision_scenarios: set[str] = set()
    for scenario in _split_top_level_blocks(content, "scenario_matrix"):
        if "decision_status: needs_decision" not in scenario:
            continue
        scenario_id = re.search(r"scenario_id:\s*(SCN-\d+)", scenario)
        case_id = re.search(r"case_id:\s*(FQA-\d+)", scenario)
        if scenario_id:
            decision_scenarios.add(scenario_id.group(1))
        if case_id and "blocked" not in scenario.lower() and "pending" not in scenario.lower():
            errors.append(
                f"{path}: needs_decision scenario maps to {case_id.group(1)} without blocked or pending wording"
            )

    if decision_scenarios and "open_decisions:" not in content:
        errors.append(f"{path}: needs_decision scenarios must have open_decisions")

    case_status: dict[str, set[str]] = {}
    for scenario in _split_top_level_blocks(content, "scenario_matrix"):
        case_id = re.search(r"case_id:\s*(FQA-\d+)", scenario)
        decision_status = re.search(r"decision_status:\s*(confirmed|needs_decision|not_applicable)", scenario)
        if case_id and decision_status:
            case_status.setdefault(case_id.group(1), set()).add(decision_status.group(1))
    for case_id, statuses in case_status.items():
        if "needs_decision" in statuses and "confirmed" in statuses:
            errors.append(
                f"{path}: {case_id} mixes confirmed and needs_decision scenarios; split the pending decision"
            )
    return errors


def _check_array_dimension_coverage(path: str, content: str) -> list[str]:
    if not _has_array_partial_update(content):
        return []

    blocks = [
        block
        for block in _split_top_level_blocks(content, "dimension_coverage")
        if re.search(r"dimension:\s*array_partial_update\b", block)
    ]
    if not blocks:
        return [f"{path}: Array partial update plans must include dimension_coverage for array_partial_update"]

    errors: list[str] = []
    for block in blocks:
        status_match = re.search(r"status:\s*(covered|partial|missing|not_applicable)", block)
        status = status_match.group(1) if status_match else "unknown"
        covered_block = _extract_mapping_section(block, "covered")
        append_types = _extract_list(covered_block, "append_element_types")
        remove_types = _extract_list(covered_block, "remove_element_types")
        boundaries = _extract_list(covered_block, "boundaries")
        system_modes = _extract_list(covered_block, "system_modes")

        missing: list[str] = []
        for label, covered, required in [
            ("append element types", append_types, ARRAY_REQUIRED_APPEND_TYPES),
            ("remove element types", remove_types, ARRAY_REQUIRED_REMOVE_TYPES),
            ("boundaries", boundaries, ARRAY_REQUIRED_BOUNDARIES),
            ("system modes", system_modes, ARRAY_REQUIRED_SYSTEM_MODES),
        ]:
            gap = sorted(required - covered)
            if gap:
                missing.append(f"{label}: {', '.join(gap)}")

        if status == "covered" and missing:
            errors.append(
                f"{path}: array_partial_update dimension is covered but misses {'; '.join(missing)}"
            )
        elif status in {"partial", "missing"} and not re.search(r"gaps:\n\s+-\s+\S|gaps:\s*\[[^\]]+\]", block):
            errors.append(f"{path}: array_partial_update {status} dimension must list gaps")
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
    errors.extend(_check_covered_gaps(path, content))
    errors.extend(_check_decision_case_mixing(path, content))
    errors.extend(_check_array_dimension_coverage(path, content))
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
