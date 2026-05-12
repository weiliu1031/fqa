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
  "$SKILL_DIR/references/test-design-patterns.md"
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
  "$SKILL_DIR/scripts/fqa_clean.py"
  "$SKILL_DIR/scripts/fqa_local_milvus.py"
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
  "$SKILL_DIR/scripts/fqa_check_cases.py" \
  "$SKILL_DIR/scripts/fqa_clean.py" \
  "$SKILL_DIR/scripts/fqa_local_milvus.py"; do
  if [[ ! -x "$script" ]]; then
    echo "Required script is not executable: $script" >&2
    exit 1
  fi
done

PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_status.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_validate_workspace.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_understanding.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_cases.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_clean.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_local_milvus.py" --help >/dev/null

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
dimension_coverage:
  - dimension: validation_fixture
    applies_when: local validation fixture
    status: not_applicable
    required:
      operations: []
      element_types: []
      boundaries: []
      system_modes: []
    covered:
      append_element_types: []
      remove_element_types: []
      boundaries: []
      system_modes: []
    scenario_ids:
      - SCN-001
    gaps: []
scenario_matrix:
  - scenario_id: SCN-001
    risk_id: RISK-001
    risk_seed_ids:
      - RS-DESIGN-001
      - RS-IMPL-001
    case_id: FQA-001
    priority: P1
    category: validation
    parameters:
      element_type: null
      operation: validate
      boundary: null
    setup: validation workspace contains a complete case file
    action: run the FQA case checker
    expected: checker exits zero for complete case artifacts
    decision_status: confirmed
    notes: validation fixture
open_decisions:
  - decision_id: DEC-001
    scenario_ids:
      - SCN-001
    question: none
    options:
      - already confirmed
    impact: none
    owner: null
    status: not_applicable
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
  execution_modes:
    local:
      supported: true
      skip_reason: null
    remote:
      supported: true
      skip_reason: null
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
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_local_milvus.py" \
  --feature-id fqa-feature-YYYYMMDD-source \
  --repo-url https://github.com/milvus-io/milvus.git \
  --worktree-root "$tmp_dir/worktrees" \
  --no-build \
  --no-start >/dev/null

negative_dir="$tmp_dir/negative"
mkdir -p "$negative_dir"/{missing-array-dim,covered-gap,decision-mixing}/planning/cases
cp "$workspace/planning/cases/FQA-001.yaml" "$negative_dir/missing-array-dim/planning/cases/FQA-001.yaml"
cp "$workspace/planning/cases/FQA-001.yaml" "$negative_dir/covered-gap/planning/cases/FQA-001.yaml"
cp "$workspace/planning/cases/FQA-001.yaml" "$negative_dir/decision-mixing/planning/cases/FQA-001.yaml"
cat > "$negative_dir/missing-array-dim/planning/test-plan.yaml" <<'EOF_NEG_ARRAY'
feature_id: fqa-negative-array
feature_name: ARRAY_APPEND / ARRAY_REMOVE negative fixture
state: CaseReview
risk_model:
  - risk_id: RISK-001
    risk_seed_ids: [RS-DESIGN-001]
    area: primary_workflow
    description: array partial update fixture
    severity: P0
    covered_by: [FQA-001]
coverage_matrix:
  - area: primary_workflow
    risk_seed_ids: [RS-DESIGN-001]
    case_ids: [FQA-001]
    status: covered
    gap: none
dimension_coverage:
  - dimension: array_partial_update
    applies_when: ARRAY_APPEND and ARRAY_REMOVE change Array field behavior
    status: covered
    required:
      operations: [append, remove]
      element_types: [Bool, Int8, Int16, Int32, Int64, Float, Double, VarChar]
      boundaries: [empty_base, single_element, duplicate, no_match, remove_all, exact_capacity, overflow, varchar_max_length]
      system_modes: [multi_field, mixed_insert_update, flush_reload_filter, compatibility, concurrency, sdk]
    covered:
      append_element_types: [Bool, Int8, Int16, Int32, Int64, Float, Double, VarChar]
      remove_element_types: [Bool, Float, Double, VarChar]
      boundaries: [duplicate, no_match, exact_capacity, overflow]
      system_modes: [multi_field, flush_reload_filter]
    scenario_ids: [SCN-001]
    gaps: []
scenario_matrix:
  - scenario_id: SCN-001
    risk_id: RISK-001
    risk_seed_ids: [RS-DESIGN-001]
    case_id: FQA-001
    priority: P0
    category: type_variant
    parameters: {element_type: Bool|Float|Double|VarChar, operation: remove, boundary: duplicate}
    setup: array fixture
    action: run array partial update
    expected: exact result
    decision_status: confirmed
    notes: negative fixture
cases:
  - case_id: FQA-001
    title: negative fixture
    risk_seed_ids: [RS-DESIGN-001]
    content_hash: validationhash
EOF_NEG_ARRAY
if PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_cases.py" \
  "$negative_dir/missing-array-dim" >/dev/null 2>&1; then
  echo "fqa_check_cases accepted missing array dimension coverage" >&2
  exit 1
fi

cat > "$negative_dir/covered-gap/planning/test-plan.yaml" <<'EOF_NEG_GAP'
feature_id: fqa-negative-covered-gap
feature_name: covered gap negative fixture
state: CaseReview
risk_model:
  - risk_id: RISK-001
    risk_seed_ids: [RS-DESIGN-001]
    area: compatibility
    description: compatibility fixture
    severity: P1
    covered_by: [FQA-001]
coverage_matrix:
  - area: compatibility
    risk_seed_ids: [RS-DESIGN-001]
    case_ids: [FQA-001]
    status: covered
    gap: Requires old-version cluster after approval.
dimension_coverage:
  - dimension: compatibility_fixture
    applies_when: compatibility environment exists
    status: not_applicable
    required:
      operations: []
      element_types: []
      boundaries: []
      system_modes: []
    covered:
      append_element_types: []
      remove_element_types: []
      boundaries: []
      system_modes: []
    scenario_ids: [SCN-001]
    gaps: []
scenario_matrix:
  - scenario_id: SCN-001
    risk_id: RISK-001
    risk_seed_ids: [RS-DESIGN-001]
    case_id: FQA-001
    priority: P1
    category: compatibility
    parameters: {element_type: null, operation: null, boundary: null}
    setup: compatibility fixture
    action: compare versions
    expected: exact compatibility result
    decision_status: confirmed
    notes: negative fixture
cases:
  - case_id: FQA-001
    title: negative fixture
    risk_seed_ids: [RS-DESIGN-001]
    content_hash: validationhash
EOF_NEG_GAP
if PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_cases.py" \
  "$negative_dir/covered-gap" >/dev/null 2>&1; then
  echo "fqa_check_cases accepted covered coverage row with unresolved gap" >&2
  exit 1
fi

cat > "$negative_dir/decision-mixing/planning/test-plan.yaml" <<'EOF_NEG_DECISION'
feature_id: fqa-negative-decision-mixing
feature_name: decision mixing negative fixture
state: CaseReview
risk_model:
  - risk_id: RISK-001
    risk_seed_ids: [RS-DESIGN-001]
    area: boundary
    description: decision mixing fixture
    severity: P1
    covered_by: [FQA-001]
coverage_matrix:
  - area: boundary
    risk_seed_ids: [RS-DESIGN-001]
    case_ids: [FQA-001]
    status: partial
    gap: pending product decision
dimension_coverage:
  - dimension: decision_fixture
    applies_when: pending semantics exist
    status: partial
    required:
      operations: [append]
      element_types: []
      boundaries: [null_payload]
      system_modes: []
    covered:
      append_element_types: []
      remove_element_types: []
      boundaries: []
      system_modes: []
    scenario_ids: [SCN-001, SCN-002]
    gaps:
      - null payload decision is pending
scenario_matrix:
  - scenario_id: SCN-001
    risk_id: RISK-001
    risk_seed_ids: [RS-DESIGN-001]
    case_id: FQA-001
    priority: P1
    category: boundary
    parameters: {element_type: Int64, operation: append, boundary: single_element}
    setup: decision fixture
    action: append value
    expected: exact result
    decision_status: confirmed
    notes: confirmed scenario
  - scenario_id: SCN-002
    risk_id: RISK-001
    risk_seed_ids: [RS-DESIGN-001]
    case_id: FQA-001
    priority: P1
    category: boundary
    parameters: {element_type: Int64, operation: append, boundary: null_payload}
    setup: decision fixture
    action: append null payload
    expected: pending decision
    decision_status: needs_decision
    notes: unresolved scenario
open_decisions:
  - decision_id: DEC-001
    scenario_ids: [SCN-002]
    question: decide null payload behavior
    options:
      - reject null payload
    impact: pass criteria
    owner: product
    status: needs_decision
cases:
  - case_id: FQA-001
    title: negative fixture
    risk_seed_ids: [RS-DESIGN-001]
    content_hash: validationhash
EOF_NEG_DECISION
if PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_check_cases.py" \
  "$negative_dir/decision-mixing" >/dev/null 2>&1; then
  echo "fqa_check_cases accepted confirmed and needs_decision scenarios in one case" >&2
  exit 1
fi

cat > "$base_dir/registry.yaml" <<EOF_REGISTRY
version: 1
updated_at: "validation"
features:
  - feature_id: "fqa-feature-YYYYMMDD-source"
    feature_name: "validation fixture"
    state: "CaseReview"
    workspace: "$workspace"
    source_repo: "validation"
    source_repo_path: null
    source_worktree_path: null
    branch: "main"
    commit: "validation"
    updated_at: null
EOF_REGISTRY
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_clean.py" \
  fqa-feature-YYYYMMDD-source --base "$base_dir" >/dev/null
if [[ ! -d "$workspace" ]]; then
  echo "fqa_clean dry-run mutated workspace" >&2
  exit 1
fi
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_clean.py" \
  fqa-feature-YYYYMMDD-source --base "$base_dir" --force --takeover >/dev/null
if [[ -d "$workspace" ]]; then
  echo "fqa_clean archive did not move workspace" >&2
  exit 1
fi
if ! find "$base_dir/archive" -name archive-manifest.yaml -print -quit | grep -q archive-manifest.yaml; then
  echo "fqa_clean archive did not write archive manifest" >&2
  exit 1
fi
if grep -q "fqa-feature-YYYYMMDD-source" "$base_dir/registry.yaml"; then
  echo "fqa_clean archive did not rebuild registry" >&2
  exit 1
fi

delete_workspace="$base_dir/features/fqa-delete-YYYYMMDD-source"
mkdir -p "$delete_workspace"
cp "$SKILL_DIR/assets/templates/state.yaml" "$delete_workspace/state.yaml"
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_clean.py" \
  fqa-delete-YYYYMMDD-source --base "$base_dir" --delete --force --takeover >/dev/null
if [[ -d "$delete_workspace" ]]; then
  echo "fqa_clean delete did not remove workspace" >&2
  exit 1
fi

legacy_workspace="$tmp_dir/repo/.fqa/features/fqa-feature-legacy-YYYYMMDD-source"
mkdir -p "$legacy_workspace"/{cases,scripts,runs,reports,issues}
cp "$SKILL_DIR/assets/templates/state.yaml" "$legacy_workspace/state.yaml"
cp "$SKILL_DIR/assets/templates/feature-intake.yaml" "$legacy_workspace/feature-intake.yaml"
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_status.py" --root "$tmp_dir/repo" --legacy-only >/dev/null

echo "FQA skill resources validated"
