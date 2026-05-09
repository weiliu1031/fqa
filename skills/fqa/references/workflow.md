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

Use progressive intake. Read `references/intake-guidelines.md` before asking
questions. During `Drafting`, ask only for enough information to understand the
feature and generate reviewable cases. Do not request cluster credentials,
secrets, endpoint details, or execution approval before test cases are
approved.

Minimum inputs before case generation:

- One feature source: PR, issue, branch, commit, diff, design document, or
  clear feature description.
- Repository path or repository URL.
- Test scope: entire feature, selected components, or selected code paths.
- Release or compatibility target when it materially affects test design.
- Forbidden operations known at planning time.

When values are unknown but safe defaults exist, continue with explicit
assumptions. Default destructive cleanup, component restart, fault injection,
and load testing to not allowed until the user explicitly approves them.

Create or resume the feature workspace before writing artifacts. Resolve the
canonical FQA base directory first:

1. Use `FQA_BASE_DIR` when it is set.
2. Otherwise use `$CODEX_HOME/fqa` when `CODEX_HOME` is set.
3. Otherwise use `~/.codex/fqa`.

New workflow artifacts belong under the canonical base directory, not under an
individual Git worktree:

```text
<fqa_base_dir>/
├── registry.yaml
└── features/
    └── <feature_id>/
        ├── .lock
        ├── state.yaml
        ├── feature-intake.yaml
        ├── design-understanding.md
        ├── implementation-understanding.md
        ├── test-plan.yaml
        ├── cases/
        ├── scripts/
        ├── runs/
        ├── reports/
        └── issues/
```

Repo-local `.fqa/` directories are compatibility locations only:

```text
<repo>/.fqa/
├── .lock
├── index.yaml
└── features/<feature_id>.ref
```

Do not create new canonical artifacts in a repo-local `.fqa/features/`
directory unless the user explicitly requests local storage. If an older
repo-local `.fqa/features/<feature_id>/state.yaml` is the only existing state,
report it as legacy and ask before migrating it to the canonical base or
continuing in place.

Create `feature-intake.yaml` from `assets/templates/feature-intake.yaml` after
the feature workspace exists. Record each intake value as `provided`,
`inferred`, `missing`, or `not_applicable`. If the user provides a PR, branch,
commit, design document, or repo path, inspect available source before asking
follow-up questions. Show the user a compact summary of known, inferred, and
missing items when a missing item affects the next gate.

`feature_id` must be stable and collision-resistant:
`fqa-<short-name>-<YYYYMMDD>-<source-id>`. Prefer a PR number, issue number,
branch slug, or short commit as `source-id`. If none exists, add a short
session suffix.

`state.yaml` is the source of truth for the active state, current session,
artifact paths, approvals, and latest run/report pointers. Use paths relative to
the feature workspace. Record `workspace.root`, `workspace.base_dir`,
`workspace.storage`, and the tested `source.repo` / `source.worktree_path`.
`source.repo` should identify the repository; `source.worktree_path` should
identify the concrete local checkout used for inspection or execution.

Maintain `<fqa_base_dir>/registry.yaml` after creating or updating a workflow.
The registry is a best-effort index for status listing across repositories and
worktrees. It may be reconstructed from `features/*/state.yaml`; never treat it
as more authoritative than a feature workspace's `state.yaml`.

Generated workflow artifacts should stay out of source control unless they are
sanitized examples. In a repository, ignore `.fqa/` by default because
repo-local files are pointers or legacy artifacts, not release content.

If the design document is missing, inspect code and generate a design
understanding from observed behavior. Make uncertainty explicit.

### CaseReview

Generate test cases from risks. Stop and ask for review. The user may approve,
remove, edit, or add cases. Do not generate scripts before approval.
When cases are approved, record the approved case IDs and content hashes in
`state.yaml` so later edits cannot silently reuse stale approval.
Use a SHA-256 hash of the case artifact content after review edits. If a case
changes after approval, clear its approval until the user approves the new hash.

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
Update `feature-intake.yaml` with cluster details after case approval. Store
credential aliases or auth methods, not secrets.

### ScriptReady

Generate one script or script entry point per approved case. Scripts must be
idempotent where possible, must clean up resources when permitted, and must
emit structured results.
Scripts must not require third-party packages unless the generated script also
documents the dependency. Prefer the standard-library contract in
`assets/templates/test-script-header.py`.

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
Store raw evidence in files when possible and reference artifact paths from
results. Redact secrets before writing error traces, command output, or config
snippets to artifacts.

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

1. Locate `<fqa_base_dir>/features/<feature_id>/state.yaml`. If a repo root is
   in scope, also check legacy `<repo>/.fqa/features/<feature_id>/state.yaml`.
   If the feature is unknown, list candidate feature workspaces and ask the
   user to choose.
2. Identify current state from `state.yaml`.
3. Read `feature-intake.yaml` if it exists. If it is missing for an older
   workflow, reconstruct it from existing artifacts and mark reconstructed
   values as `inferred`.
4. Verify referenced files exist.
5. Run `scripts/fqa_validate_workspace.py <workspace>` when available before
   resuming report, issue, regression, or closeout work.
6. Continue from the next incomplete gate.
7. Do not regenerate earlier artifacts unless the user requests it or inputs
   changed.

For common resume points:

- `CaseReview`: summarize proposed cases and ask for approval, rejection, or
  edits.
- `WaitingCluster`: ask for missing endpoint, auth method, namespace, resource
  budget, cleanup permission, and fault-injection permission.
- `ReportReview`: summarize release signal, failures, blocked coverage, and
  ask for report acceptance or corrections.
- `IssueReview`: summarize issue candidates and ask which candidates to create.
- `WaitingFix`: ask for fix PR, commit, image, or build before regression.
- `Regression`: rerun failed and adjacent-risk cases, then ask whether results
  are accepted before closing.

## Status Listing

When the user asks for FQA status, list workflows by reading every existing
`<fqa_base_dir>/features/*/state.yaml`. If a repo root is in scope, filter
global workflows to states whose `source.repo`, `source.repo_path`, or
`source.worktree_path` matches the repo root, and include legacy
`<repo>/.fqa/features/*/state.yaml`. If no state files exist, report that no
FQA workflows were found.
Use `scripts/fqa_status.py` when available for deterministic output.

Show one row per workflow:

```text
Feature ID | Feature | State | Session | Updated | Latest Run | Next Gate
```

Derive `Next Gate` from `state`:

| State | Next Gate |
| --- | --- |
| Drafting | finish feature understanding and generate cases |
| CaseReview | approve, reject, or edit test cases |
| WaitingCluster | provide cluster access and execution permission |
| ScriptReady | approve execution on the target cluster |
| Running | wait for run completion and evidence collection |
| ReportReview | accept report or request corrections |
| IssueReview | approve, reject, merge, or edit issue candidates |
| IssueCreated | provide or track fix references |
| WaitingFix | provide fix PR, commit, image, or build |
| Regression | accept regression results or request rerun |
| Closed | no action required |

For `status <feature_id>`, show:

- Feature ID, feature name, and current state.
- Source repo, branch, commit, PR, issue, and design doc if present.
- Active session ID, owner, status, and last update time.
- Approval status for test cases, cluster execution, issue creation, and
  closeout.
- Artifact paths from `state.yaml`.
- Latest run ID, latest report, and next gate.
- Any notes.

## Concurrent Sessions

Different features may be tested at the same time because each feature has its
own canonical workspace, independent of the Git worktree used to inspect or run
the feature.

For the same feature:

- Use `.lock` as the feature workspace single-writer marker when writing
  `state.yaml`, reports, issue candidates, or approval updates. The lock should
  record session ID, owner, started time, and last update time.
- If `state.yaml.active_session.status` is `active` and belongs to another
  session, stop before writing and ask whether to take over, wait, or open a
  separate run-only session.
- A takeover must update `active_session` with the new session ID, owner,
  timestamp, takeover note, and `.lock`.
- Never mark another session's approval as granted. Approval fields must record
  who approved and when.
- Runs are append-only and may coexist. State transitions, approvals, reports,
  and issue candidates are single-writer updates through `state.yaml`.
- If a session is clearly stale, explain the evidence before taking over.
