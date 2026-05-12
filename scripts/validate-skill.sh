#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$ROOT_DIR/skills/fqa"
VALIDATOR="${SKILL_CREATOR_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

PYTHONDONTWRITEBYTECODE=1 python3 "$VALIDATOR" "$SKILL_DIR"

version="$(awk '
  /^---$/ { fence++; next }
  fence == 1 && /^[[:space:]]*version:/ { print $2; exit }
' "$SKILL_DIR/SKILL.md")"

if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid or missing FQA skill version: $version" >&2
  exit 1
fi

required=(
  "$SKILL_DIR/SKILL.md"
  "$SKILL_DIR/agents/openai.yaml"
  "$SKILL_DIR/references/workflow.md"
  "$SKILL_DIR/references/artifact-schema.md"
  "$SKILL_DIR/references/intake-guidelines.md"
  "$SKILL_DIR/references/understanding-guidelines.md"
  "$SKILL_DIR/references/test-case-guidelines.md"
  "$SKILL_DIR/references/report-guidelines.md"
  "$SKILL_DIR/references/issue-guidelines.md"
  "$SKILL_DIR/assets/templates/design-understanding.md"
  "$SKILL_DIR/assets/templates/feature-intake.yaml"
  "$SKILL_DIR/assets/templates/implementation-understanding.md"
  "$SKILL_DIR/assets/templates/state.yaml"
  "$SKILL_DIR/assets/templates/test-plan.yaml"
  "$SKILL_DIR/assets/templates/test-case.yaml"
  "$SKILL_DIR/assets/templates/test-script-header.py"
  "$SKILL_DIR/assets/templates/test-run-result.yaml"
  "$SKILL_DIR/assets/templates/test-report.md"
  "$SKILL_DIR/assets/templates/issue-candidate.yaml"
  "$SKILL_DIR/scripts/fqa_status.py"
  "$SKILL_DIR/scripts/fqa_validate_workspace.py"
  "$SKILL_DIR/scripts/fqa_check_understanding.py"
  "$SKILL_DIR/scripts/fqa_check_cases.py"
)

for path in "${required[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
done

for script in \
  "$SKILL_DIR/scripts/fqa_status.py" \
  "$SKILL_DIR/scripts/fqa_validate_workspace.py" \
  "$SKILL_DIR/scripts/fqa_check_understanding.py" \
  "$SKILL_DIR/scripts/fqa_check_cases.py"; do
  if [[ ! -x "$script" ]]; then
    echo "Required script is not executable: $script" >&2
    exit 1
  fi
done

PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_status.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_validate_workspace.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_understanding.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_cases.py" --help >/dev/null

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
base_dir="$tmp_dir/fqa-base"
workspace="$base_dir/features/fqa-feature-YYYYMMDD-source"
mkdir -p "$workspace"/{intake,planning/understanding,planning/cases,execution/scripts,execution/runs,closure/reports,closure/issues}
cp "$SKILL_DIR/assets/templates/state.yaml" "$workspace/state.yaml"
cp "$SKILL_DIR/assets/templates/feature-intake.yaml" "$workspace/intake/feature-intake.yaml"
cat > "$workspace/planning/understanding/design-understanding.md" <<'EOF_DESIGN'
# Design Understanding

feature_id: fqa-feature-YYYYMMDD-source
state: Drafting

## Source Summary

### Documented Behavior

- Claim:
  - Evidence: test design source
  - Confidence: confirmed
  - QA impact: validates primary behavior

### Inferred Behavior

- Claim:
  - Evidence: test code source
  - Confidence: inferred
  - QA impact: validates inferred behavior

### Unknown or Ambiguous Behavior

- Question:
  - Why it matters: none for validation fixture
  - Evidence gap: none
  - Blocking: no

## Risk Seeds

- risk_seed_id: RS-DESIGN-001
  source_claim: validation fixture
  evidence: validation fixture
  risk_statement: Because validation behavior changes, users could hit a missed case, causing weak coverage.
  observable_assertion: generated cases reference this seed
  priority_hint: P1
  coverage_area: primary_workflow

## Quality Gate

- All major claims have evidence: yes
- Inferred behavior is separated from documented behavior: yes
- Unknowns that affect test design are listed: yes
- Compatibility expectations are covered or marked not applicable: yes
- Risk seeds are specific and observable: yes
EOF_DESIGN
cat > "$workspace/planning/understanding/implementation-understanding.md" <<'EOF_IMPL'
# Implementation Understanding

feature_id: fqa-feature-YYYYMMDD-source
state: Drafting

## Change Inventory

| File | Symbols | Change type | Responsibility | Evidence | Risk |
| --- | --- | --- | --- | --- | --- |
| validation | check | modify | fixture | validation fixture | low |

## Component Map

| Component | Files | Responsibility | Upstream callers | Downstream dependencies | Risk |
| --- | --- | --- | --- | --- | --- |
| validation | validation | fixture | test | none | low |

## Execution Paths

### Path 1

- Entry point:
  - Evidence: validation fixture

## State and Invariants

- Invariant:
  - Established by: validation fixture
  - Consumed by: validation fixture
  - Violation impact: weak validation
  - Evidence: validation fixture
  - Confidence: confirmed

## Failure Paths

- Failure:
  - Trigger: missing section
  - Expected handling: checker fails
  - Evidence: validation fixture
  - Observable signal: non-zero exit
  - QA impact: catches incomplete understanding

## Risk Seeds

- risk_seed_id: RS-IMPL-001
  source_path: validation
  source_symbol: check
  evidence: validation fixture
  risk_statement: Because validation behavior changes, users could miss incomplete understanding, causing weak test cases.
  observable_assertion: checker exits non-zero for incomplete artifacts
  priority_hint: P1
  coverage_area: observability

## Quality Gate

- All changed files are represented in Change Inventory: yes
- Main execution paths are traced from entry point to user-visible result: yes
- State mutations and invariants are identified: yes
- Failure paths include observable signals: yes
- Assumptions have confidence and falsification notes: yes
- Risk seeds are specific and observable: yes
EOF_IMPL
FQA_BASE_DIR="$base_dir" PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_status.py" >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_validate_workspace.py" "$workspace" >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_understanding.py" "$workspace" >/dev/null
cat > "$workspace/planning/test-plan.yaml" <<'EOF_PLAN'
feature_id: fqa-feature-YYYYMMDD-source
feature_name: validation fixture
state: CaseReview
source:
  design_doc: null
  repo: validation
  branch: main
  commit: validation
  pr: null
  issue: null
risk_model:
  - risk_id: RISK-001
    risk_seed_ids:
      - RS-DESIGN-001
      - RS-IMPL-001
    area: primary_workflow
    description: validation risk with observable assertion
    severity: P1
    covered_by:
      - FQA-001
coverage_matrix:
  - area: primary_workflow
    risk_seed_ids:
      - RS-DESIGN-001
      - RS-IMPL-001
    case_ids:
      - FQA-001
    status: covered
    gap: none
cases:
  - case_id: FQA-001
    title: rejects incomplete validation fixture with actionable diagnostics
    risk_seed_ids:
      - RS-DESIGN-001
      - RS-IMPL-001
    content_hash: validationhash
EOF_PLAN
cat > "$workspace/planning/cases/FQA-001.yaml" <<'EOF_CASE'
case_id: FQA-001
case_version: 1
content_hash: validationhash
title: rejects incomplete validation fixture with actionable diagnostics
priority: P1
traceability:
  risk_seed_ids:
    - RS-DESIGN-001
    - RS-IMPL-001
  source_claims:
    - validation fixture claim requires actionable diagnostics
  source_files:
    - skills/fqa/scripts/fqa_check_cases.py
risk:
  risk_id: RISK-001
  risk_seed_ids:
    - RS-DESIGN-001
    - RS-IMPL-001
  area: primary_workflow
  description: incomplete case artifacts could pass review without actionable diagnostics
preconditions:
  - validation workspace contains a generated case file
cluster_requirement:
  topology: local validation
  permissions:
    cleanup: false
    restart_components: false
    fault_injection: false
data_requirement:
  datasets:
    - validation fixture
  scale: one case file
regression:
  components:
    - fqa case checker
  code_paths:
    - skills/fqa/scripts/fqa_check_cases.py
  risk_tags:
    - case_quality
  related_cases: []
steps:
  - step: 1
    action: run the FQA case checker against the validation workspace
    expected: checker exits zero for complete case artifacts
assertions:
  - checker output contains actionable validation success for the workspace
oracle:
  type: exact_response
  expected: checker exits zero and prints actionable validation success
  negative_assertions:
    - checker must not accept empty oracle fields
observability:
  logs:
    - checker stdout and stderr
  metrics:
    - validation exit code
  traces:
    - validation command line
diagnostics:
  failure_triage: inspect checker stderr for missing field names
  evidence_to_collect:
    - checker stderr
flakiness_controls:
  timeout: 30s
  polling_interval: not applicable
  retry_policy: no retry
cleanup:
  required: true
  method: remove temporary validation workspace
status: proposed
EOF_CASE
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_cases.py" "$workspace" >/dev/null

legacy_workspace="$tmp_dir/repo/.fqa/features/fqa-feature-legacy-YYYYMMDD-source"
mkdir -p "$legacy_workspace"/{cases,scripts,runs,reports,issues}
cp "$SKILL_DIR/assets/templates/state.yaml" "$legacy_workspace/state.yaml"
cp "$SKILL_DIR/assets/templates/feature-intake.yaml" "$legacy_workspace/feature-intake.yaml"
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_status.py" --root "$tmp_dir/repo" --legacy-only >/dev/null

echo "FQA skill resources validated"
