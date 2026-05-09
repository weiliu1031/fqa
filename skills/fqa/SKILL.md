---
name: fqa
description: Use when planning, generating, executing, reporting, or regressing feature-level QA for a product change, PR, design document, branch, issue, or implementation. Use for system tests, cluster tests, end-to-end validation, compatibility checks, failure recovery, observability verification, issue candidate review, and regression workflows; not for unit-test generation.
metadata:
  version: 0.4.0
---

# FQA

FQA drives a feature-level QA workflow with explicit human gates. Treat every
artifact as part of a traceable chain from feature understanding to test cases,
test runs, issues, fixes, regression, and final report.

## Core Rule

Do not execute an irreversible or externally visible step without explicit
approval in the current conversation.

Required gates:

1. Stop after generating test cases. Ask for test case approval.
2. Stop before execution. Ask for cluster connection details and execution
   permission.
3. Stop after generating issue candidates. Ask which issues to create.
4. Stop before closing the workflow. Ask whether regression results are
   accepted.

## State Machine

Use exactly one active state:

```text
Drafting
-> CaseReview
-> WaitingCluster
-> ScriptReady
-> Running
-> ReportReview
-> IssueReview
-> IssueCreated
-> WaitingFix
-> Regression
-> Closed
```

If the user resumes a workflow, identify the current state from artifacts and
continue from there. Do not restart unless requested.

## Workspace and State

Before creating any workflow artifact, choose or create the canonical FQA base
directory:

```text
${FQA_BASE_DIR:-${CODEX_HOME:-~/.codex}/fqa}
```

Use this base directory for all new workflow artifacts, even when the tested
feature lives in a Git worktree. The canonical feature workspace is:

```text
<fqa_base_dir>/features/<feature_id>/
```

Each feature workspace owns exactly one active `state.yaml`. Use
`assets/templates/state.yaml` when creating it. Store all artifacts for that
feature under the same canonical workspace so parallel sessions and different
worktrees do not collide. Record the tested repository and worktree path in
`state.yaml.source`.

Maintain `<fqa_base_dir>/registry.yaml` as a best-effort index of feature IDs,
workspace paths, source repositories, source worktrees, and states. The
registry is an index only; `state.yaml` remains the source of truth. A
repo-local `.fqa/` directory may contain compatibility pointers, but do not
create new canonical artifacts there unless the user explicitly requests
repo-local storage.

When resuming, start from `<feature_workspace>/state.yaml`. If another active
session is recorded for the same feature, do not overwrite its state unless the
user confirms takeover or the recorded session is clearly stale. Runs are always
append-only under `runs/<run_id>/`.

If only an older repo-local `.fqa/features/<feature_id>/state.yaml` exists,
report it as a legacy workspace and ask before migrating or continuing in
place.

## Status and Resume

Support these user intents:

- `status`, `list`, or `show workflows`: scan
  `<fqa_base_dir>/features/*/state.yaml` and summarize all workflows. Include
  legacy repo-local `.fqa/features/*/state.yaml` only when a repo root is in
  scope.
- `status <feature_id>`: show one workflow's state, approvals, latest run,
  latest report, and next required human decision.
- `resume <feature_id>`: read that workflow's `state.yaml`, verify referenced
  artifacts exist, and continue from the next incomplete gate.

If a feature ID is missing or ambiguous, list candidate workflows and ask the
user to choose. Read `references/workflow.md` for the required status fields and
resume behavior.

Bundled helper scripts:

- `scripts/fqa_status.py`: summarize global workflows, repo-filtered workflows,
  or one workflow. It defaults to `$FQA_BASE_DIR`, falling back to
  `$CODEX_HOME/fqa` or `~/.codex/fqa`.
- `scripts/fqa_validate_workspace.py`: validate a feature workspace before
  resume, report, issue creation, or closeout.

## Workflow

1. **Collect inputs**
   - Read `references/intake-guidelines.md`.
   - Choose, create, or resume the feature workspace.
   - Create `feature-intake.yaml` from `assets/templates/feature-intake.yaml`
     in the feature workspace.
   - Collect or infer only the information needed for `Drafting`: feature
     source, repository, scope, release target, compatibility target, and known
     forbidden operations.
   - Mark each intake value as provided, inferred, missing, or not applicable.
   - Do not request cluster credentials, secrets, endpoint details, or
     execution permission before test cases are approved.
   - Update `state.yaml`.
   - Update `<fqa_base_dir>/registry.yaml` after creating or changing the
     workspace.

2. **Understand the feature**
   - If a design document exists, summarize it.
   - If no design document exists, inspect source code and generate:
     - `design-understanding.md`
     - `implementation-understanding.md`
   - Read `references/workflow.md` for the full artifact flow.

3. **Model risk**
   - Cover user workflows, cross-component behavior, persistence, recovery,
     compatibility, concurrency, configuration, performance, observability,
     security, and rollback.
   - Read `references/test-case-guidelines.md` before generating cases.

4. **Generate test plan and test cases**
   - Use `assets/templates/test-plan.yaml`.
   - Use one `assets/templates/test-case.yaml` shape per case.
   - Set state to `CaseReview`.
   - Update `state.yaml` with produced artifact paths and approval status.
   - Record case content hashes when cases are approved.
   - Ask the user to approve, reject, or edit cases.

5. **Ask for cluster access**
   - After case approval, request endpoint, auth method, namespace, resource
     limits, cleanup permission, and fault-injection permission.
   - Update `feature-intake.yaml` with cluster details, using aliases for
     credentials and never storing secrets.
   - Set state to `WaitingCluster` until provided.

6. **Generate scripts**
   - Generate scripts only for approved cases.
   - Use `assets/templates/test-script-header.py` as the script contract.
   - Each script must emit a `test-run-result.yaml` compatible result.
   - Set state to `ScriptReady`.

7. **Execute and collect evidence**
   - Execute only after cluster permission.
   - Record code version, cluster version, config, raw output, logs, metrics,
     and cleanup status.
   - Write each execution to a new `runs/<run_id>/` directory.
   - Set state to `Running`, then `ReportReview`.

8. **Report and classify failures**
   - Use `assets/templates/test-report.md`.
   - Classify each failure as product bug, test bug, environment issue,
     requirement ambiguity, or blocked.
   - Generate issue candidates using `assets/templates/issue-candidate.yaml`.
   - Read `references/report-guidelines.md` and `references/issue-guidelines.md`.
   - Set state to `IssueReview`.

9. **Create issues only after approval**
   - Create only approved issues.
   - Link issue IDs back to case IDs and run IDs.
   - Set state to `IssueCreated` or `WaitingFix`.

10. **Regression**
    - When fixes are available, rerun failed cases and adjacent-risk cases.
    - Update the report with fix versions and regression outcomes.
    - Set state to `Regression`, then `Closed` after user acceptance.

## Artifact IDs

Use stable IDs:

- `feature_id`: `fqa-<short-name>-YYYYMMDD-<source-id>`
- `case_id`: `FQA-<NNN>`
- `run_id`: `RUN-YYYYMMDD-HHMMSS-<session-id>`
- `failure_id`: `FAIL-<case_id>-<NN>`
- `issue_candidate_id`: `ISSUE-CAND-<NN>`
- `regression_id`: `REG-YYYYMMDD-HHMMSS`

## Reference Files

- Read `references/workflow.md` for phase details and resume behavior.
- Read `references/artifact-schema.md` when writing structured artifacts.
- Read `references/intake-guidelines.md` before asking startup or cluster
  intake questions.
- Read `references/test-case-guidelines.md` before generating test cases.
- Read `references/report-guidelines.md` before writing reports.
- Read `references/issue-guidelines.md` before creating issue candidates.

## Output Discipline

Keep user-facing updates concise. Always state:

- Current state.
- Artifact path changed or produced.
- Required next human decision, if blocked.

Never hide failed cleanup, missing evidence, skipped checks, or environment
problems behind a passing summary.
