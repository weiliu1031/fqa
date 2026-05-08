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

1. Locate the latest report or state artifact.
2. Identify current state.
3. Verify referenced files exist.
4. Continue from the next incomplete gate.
5. Do not regenerate earlier artifacts unless the user requests it or inputs
   changed.
