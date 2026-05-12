# Artifact Schema

Use these fields when creating FQA artifacts. Markdown artifacts may contain
human-readable text, but structured blocks should preserve these keys.

## State Manifest

`state.yaml` is the source of truth for a feature workspace. Store artifact
paths relative to `<fqa_base_dir>/features/<feature_id>/` unless an absolute
path is required for an external source. The canonical base directory resolves
from `FQA_BASE_DIR`, then `$CODEX_HOME/fqa`, then `~/.codex/fqa`.

```yaml
feature_id: string
feature_name: string
state: Drafting|CaseReview|WaitingCluster|ScriptReady|Running|ReportReview|IssueReview|IssueCreated|WaitingFix|Regression|Closed
workspace:
  root: string
  base_dir: string
  storage: global|repo_local_legacy
  legacy_root: string|null
  created_at: string
  updated_at: string
active_session:
  session_id: string
  owner: string|null
  status: active|released|stale|closed
  started_at: string
  updated_at: string
  takeover_note: string|null
source:
  design_doc: string|null
  repo: string|null
  repo_path: string|null
  worktree_path: string|null
  branch: string|null
  commit: string|null
  pr: string|null
  issue: string|null
artifacts:
  feature_intake: string|null
  design_understanding: string|null
  implementation_understanding: string|null
  test_plan: string|null
  cases_dir: string
  scripts_dir: string
  runs_dir: string
  reports_dir: string
  issues_dir: string
latest:
  run_id: string|null
  report: string|null
approvals:
  test_cases:
    approved: boolean
    approved_cases:
      - case_id: string
        content_hash: string
    approved_by: string|null
    approved_at: string|null
  cluster_execution:
    approved: boolean
    approved_by: string|null
    approved_at: string|null
  issue_creation:
    approved_candidates:
      - string
    approved_by: string|null
    approved_at: string|null
  closeout:
    accepted: boolean
    accepted_by: string|null
    accepted_at: string|null
notes:
  - string
```

Use the phase directories consistently:

| Artifact | Default path |
| --- | --- |
| Intake | `intake/feature-intake.yaml` |
| Design understanding | `planning/understanding/design-understanding.md` |
| Implementation understanding | `planning/understanding/implementation-understanding.md` |
| Test plan | `planning/test-plan.yaml` |
| Test cases | `planning/cases/` |
| Test scripts | `execution/scripts/` |
| Run evidence | `execution/runs/` |
| Reports | `closure/reports/` |
| Issue candidates | `closure/issues/` |

## Registry

`registry.yaml` is a best-effort index under `<fqa_base_dir>/registry.yaml`.
Update it after creating a workspace or changing a workflow state. It is used
for global status discovery only; reconstruct it from state files if it is
missing or stale.

```yaml
version: 1
updated_at: string
features:
  - feature_id: string
    feature_name: string
    state: Drafting|CaseReview|WaitingCluster|ScriptReady|Running|ReportReview|IssueReview|IssueCreated|WaitingFix|Regression|Closed
    workspace: string
    source_repo: string|null
    source_repo_path: string|null
    source_worktree_path: string|null
    branch: string|null
    commit: string|null
    updated_at: string
```

After cleanup, rebuild the registry from remaining active
`features/*/state.yaml` files. Archived workspaces are stored under
`<fqa_base_dir>/archive/` and are intentionally excluded from active status
listing.

## Feature Intake

`intake/feature-intake.yaml` records what the user provided, what the agent
inferred, and what is still missing. Use it to avoid repeatedly asking the same
intake questions and to keep assumptions visible.

Every intake item should preserve this shape:

```yaml
value: string|boolean|array|null
source: provided|inferred|missing|not_applicable
confidence: confirmed|inferred|unknown
notes: string
```

Top-level structure:

```yaml
feature_id: string
feature_name:
  value: string
  source: provided|inferred|missing|not_applicable
  confidence: confirmed|inferred|unknown
  notes: string
source:
  pr: intake_item
  issue: intake_item
  branch: intake_item
  commit: intake_item
  diff: intake_item
  design_doc: intake_item
repository:
  repo: intake_item
  code_paths:
    - intake_item
scope:
  test_scope: intake_item
  release_target: intake_item
  compatibility_target: intake_item
constraints:
  forbidden_operations:
    - intake_item
  must_test:
    - intake_item
  must_not_test:
    - intake_item
cluster:
  requested_before_case_approval: boolean
  endpoint_alias: intake_item
  auth_method: intake_item
  namespace: intake_item
  resource_prefix: intake_item
  cleanup_allowed: intake_item
  restart_allowed: intake_item
  fault_injection_allowed: intake_item
  resource_budget: intake_item
observability:
  logs: intake_item
  metrics: intake_item
  traces: intake_item
questions:
  blocking:
    - string
  optional:
    - string
assumptions:
  - string
status: drafting|case_review|waiting_cluster|script_ready|running|report_review|issue_review|issue_created|waiting_fix|regression|closed
```

Do not store credentials or raw secrets in this artifact. Store credential
aliases or auth methods only.

## Test Plan

```yaml
feature_id: string
feature_name: string
state: Drafting|CaseReview|WaitingCluster|ScriptReady|Running|ReportReview|IssueReview|IssueCreated|WaitingFix|Regression|Closed
source:
  design_doc: string|null
  repo: string|null
  branch: string|null
  commit: string|null
  pr: string|null
  issue: string|null
risk_model:
  - risk_id: string
    risk_seed_ids:
      - string
    area: string
    description: string
    severity: P0|P1|P2|P3
    covered_by:
      - case_id
coverage_matrix:
  - area: string
    risk_seed_ids:
      - string
    case_ids:
      - string
    status: covered|partial|missing
    gap: string|null
scenario_matrix:
  - scenario_id: string
    risk_id: string
    risk_seed_ids:
      - string
    case_id: string|null
    priority: P0|P1|P2|P3
    category: type_variant|operation_variant|validation|boundary|system_mode|compatibility|concurrency|other
    parameters:
      element_type: string|null
      operation: string|null
      boundary: string|null
    setup: string
    action: string
    expected: string
    decision_status: confirmed|needs_decision|not_applicable
    notes: string|null
open_decisions:
  - decision_id: string
    scenario_ids:
      - string
    question: string
    options:
      - string
    impact: string
    owner: string|null
    status: needs_decision|resolved|not_applicable
cases:
  - case_id: string
    title: string
    risk_seed_ids:
      - string
    content_hash: string
```

## Test Case

```yaml
case_id: string
case_version: integer
content_hash: string
title: string
priority: P0|P1|P2|P3
traceability:
  risk_seed_ids:
    - string
  source_claims:
    - string
  source_files:
    - string
risk:
  risk_id: string
  risk_seed_ids:
    - string
  area: string
  description: string
preconditions:
  - string
cluster_requirement:
  topology: string
  permissions:
    cleanup: boolean
    restart_components: boolean
    fault_injection: boolean
data_requirement:
  datasets:
    - string
  scale: string
regression:
  components:
    - string
  code_paths:
    - string
  risk_tags:
    - string
  related_cases:
    - string
steps:
  - step: integer
    action: string
    expected: string
assertions:
  - string
oracle:
  type: exact_response|data_invariant|state_invariant|compatibility|observability|resource
  expected: string
  negative_assertions:
    - string
observability:
  logs:
    - string
  metrics:
    - string
  traces:
    - string
diagnostics:
  failure_triage: string
  evidence_to_collect:
    - string
flakiness_controls:
  timeout: string
  polling_interval: string
  retry_policy: string
cleanup:
  required: boolean
  method: string
status: proposed|approved|rejected|scripted|passed|failed|blocked|skipped
```

## Test Run Result

```yaml
run_id: string
case_id: string
status: passed|failed|blocked|skipped
started_at: string
ended_at: string
environment:
  endpoint_alias: string
  version: string
  commit: string|null
  topology: string
evidence:
  logs:
    - string
  metrics:
    - string
  traces:
    - string
  artifacts:
    - string
  redactions:
    - string
failure:
  failure_id: string|null
  classification: product_bug|test_bug|environment|requirement_ambiguity|blocked|null
  summary: string|null
cleanup:
  attempted: boolean
  status: success|failed|not_allowed|not_needed
```

## Issue Candidate

```yaml
issue_candidate_id: string
title: string
severity: P0|P1|P2|P3
component: string
case_ids:
  - string
run_ids:
  - string
failure_ids:
  - string
expected: string
actual: string
reproduction:
  - string
evidence:
  - string
suspected_root_cause: string|null
labels:
  - string
approved: false
created_issue: string|null
```
