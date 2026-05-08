# FQA Workflow

## Purpose

FQA turns a feature change into a reviewed, executable, evidence-backed QA
cycle. It is designed for product features that require cluster validation,
cross-component behavior checks, or release confidence beyond unit tests.

## Phases

### Drafting

Collect feature inputs:

- Feature name and short description.
- Design document path or URL.
- Repository path.
- PR, branch, commit, or diff.
- Relevant code paths.
- Release target and compatibility target.
- Forbidden operations, such as destructive cleanup or component restarts.

Create or resume the feature workspace before writing artifacts:

```text
.fqa/features/<feature_id>/
├── state.yaml
├── design-understanding.md
├── implementation-understanding.md
├── test-plan.yaml
├── cases/
├── scripts/
├── runs/
├── reports/
└── issues/
```

`feature_id` must be stable and collision-resistant:
`fqa-<short-name>-<YYYYMMDD>-<source-id>`. Prefer a PR number, issue number,
branch slug, or short commit as `source-id`. If none exists, add a short
session suffix.

`state.yaml` is the source of truth for the active state, current session,
artifact paths, approvals, and latest run/report pointers. Use paths relative to
the feature workspace.

If the design document is missing, inspect code and generate a design
understanding from observed behavior. Make uncertainty explicit.

### CaseReview

Generate test cases from risks. Stop and ask for review. The user may approve,
remove, edit, or add cases. Do not generate scripts before approval.

### WaitingCluster

Ask for:

- Endpoint and protocol.
- Authentication method.
- Namespace, database, tenant, or project.
- Collection or resource name prefix.
- Cleanup permission.
- Resource budget.
- Whether component restart, fault injection, or chaos operations are allowed.
- Log, metric, trace, and dashboard access.

Treat secrets as sensitive. Do not print credentials in reports.

### ScriptReady

Generate one script or script entry point per approved case. Scripts must be
idempotent where possible, must clean up resources when permitted, and must
emit structured results.

### Running

Record evidence:

- Feature version, commit, image, or build.
- Cluster topology and version.
- Test input and generated resource names.
- Commands executed.
- Assertions and raw results.
- Logs, metrics, traces, or query outputs used as evidence.
- Cleanup status.

Every execution creates a new append-only run directory:

```text
runs/RUN-YYYYMMDD-HHMMSS-<session-id>/
```

Do not overwrite prior run results. If a case is rerun, write a new result file
and update `state.yaml` pointers to the latest run.

### ReportReview

Write a report that is useful for release decisions. Include coverage,
failures, blocked areas, risks not tested, and evidence links.

### IssueReview

Create issue candidates only for failures classified as product bugs or
requirement ambiguities that need product/engineering decisions. Stop for human
approval.

### IssueCreated

After approval, create issues and link each issue to cases, runs, failures, and
evidence. If issue creation tooling is unavailable, prepare issue text and ask
the user to create it.

### WaitingFix

Track issue status and fix PRs or commits. Do not mark resolved based only on
issue status. Regression evidence is required.

### Regression

Rerun failed cases plus adjacent-risk cases. Adjacent-risk cases are cases
sharing the same component, state machine, API, storage path, compatibility
surface, or failure mode.

### Closed

Close only after the user accepts the final report. Record unresolved risks and
skipped cases.

## Resume Behavior

When resuming:

1. Locate `.fqa/features/<feature_id>/state.yaml`. If the feature is unknown,
   list candidate feature workspaces and ask the user to choose.
2. Identify current state from `state.yaml`.
3. Verify referenced files exist.
4. Continue from the next incomplete gate.
5. Do not regenerate earlier artifacts unless the user requests it or inputs
   changed.

## Concurrent Sessions

Different features may be tested at the same time because each feature has its
own workspace.

For the same feature:

- If `state.yaml.active_session.status` is `active` and belongs to another
  session, stop before writing and ask whether to take over, wait, or open a
  separate run-only session.
- A takeover must update `active_session` with the new session ID, owner,
  timestamp, and takeover note.
- Never mark another session's approval as granted. Approval fields must record
  who approved and when.
- Runs are append-only and may coexist. State transitions, approvals, reports,
  and issue candidates are single-writer updates through `state.yaml`.
- If a session is clearly stale, explain the evidence before taking over.
