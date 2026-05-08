# Test Case Guidelines

## Goal

High-quality FQA cases are risk-first, source-derived, executable,
observable, isolated, and evidence-backed. They are not a broad checklist of
feature behaviors. A case is useful only if it can reveal a meaningful product
risk and produce enough evidence for another engineer to diagnose the result.

Use this file before writing `test-plan.yaml` and `cases/FQA-*.yaml`.

## Source-to-Risk Derivation

Derive cases from verified source signals. Prefer concrete design text, code
paths, API contracts, migration logic, config defaults, and previous incident
patterns over generic QA categories.

For each feature, inspect these signals when available:

- Public API shape: new parameters, defaults, validation, error messages, and
  backward-compatible behavior.
- State transitions: create, update, delete, load, release, retry, timeout,
  cancellation, restart, and recovery.
- Data correctness contract: persisted fields, ordering, idempotency,
  consistency, isolation, and exact result expectations.
- Cross-component path: request owner, downstream services, metadata writes,
  storage writes, background tasks, cache invalidation, and async completion.
- Compatibility surface: old client to new server, new client to old server,
  rolling upgrade, downgrade, saved data, and changed defaults.
- Failure modes: dependency outage, partial write, leader change, component
  restart, network timeout, retry exhaustion, and cleanup failure.
- Resource behavior: high cardinality, large payloads, concurrent users,
  memory pressure, disk growth, long-running operations, and rate limits.
- Observability contract: logs, metrics, traces, audit records, and user-facing
  error text needed to diagnose failures.

Convert each source signal into a risk statement before writing cases:

```text
Because <source behavior or change>, users could hit <failure mode>, causing
<impact>. We can detect it by <observable assertion>.
```

Only keep the case if the risk and observable assertion are both specific.

## Coverage Areas

Generate cases across these areas when applicable:

- Primary user workflow.
- API validation and user-visible errors.
- Cross-component data flow.
- Persistence, restart, and recovery.
- Upgrade, downgrade, and rollback compatibility.
- Configuration flags and default behavior.
- Concurrency and consistency.
- Large data volume and resource pressure.
- Failure injection and retry behavior.
- Observability: logs, metrics, traces, and error messages.
- Security, permissions, tenant isolation, and destructive operations.

## Case Quality Bar

Each case must be executable by a different engineer without extra context.

Every case needs:

- A specific risk.
- A stable content hash once proposed or approved. Use SHA-256 of the case
  artifact content after review edits.
- Concrete setup.
- Exact user or system actions.
- Observable assertions.
- Required cluster capability.
- Cleanup plan.
- Priority.

Avoid vague cases like "test performance" or "verify error handling". Replace
them with measurable assertions.

Before proposing a case, check all quality gates:

- Risk: names one concrete failure mode and user or release impact.
- Source traceability: points back to a design claim, code path, API contract,
  config, compatibility promise, or observed implementation behavior.
- Minimal scope: exercises one diagnostic risk, not several unrelated risks.
- Deterministic setup: resource names, data shape, topology, config, and
  permissions are explicit.
- Exact action: user or system steps are ordered and reproducible.
- Strong oracle: assertions compare against exact data, state, status, error
  text, metric, log pattern, or trace attribute.
- Negative evidence: when applicable, asserts what must not happen, such as
  no partial data, no duplicate task, no leaked resource, or no silent retry
  loop.
- Diagnostics: failure output tells an engineer where to look next.
- Isolation: resources are unique to the case and safe for parallel workflows.
- Cleanup: cleanup is explicit, and failure to clean up is reported.
- Regression metadata: components, code paths, risk tags, and related cases
  are filled when they are known.

Reject or rewrite a case if it fails any of these checks.

## Test Oracle Design

The assertion is the most important part of the case. Do not use "works",
"succeeds", or "is normal" as an oracle.

Prefer these oracle types:

- Exact response: status code, error code, message fragment, returned field,
  and stable ordering when ordering is required.
- Data invariant: row count, vector count, entity identity, timestamp ordering,
  idempotency, consistency, or absence of partial writes.
- State invariant: component state, metadata state, task state, persisted
  checkpoint, or recovery marker.
- Compatibility invariant: old data remains readable, old clients keep the
  same behavior, or downgrade rejects new-only state with a clear error.
- Observability invariant: expected metric labels and values, log message with
  request or resource identity, trace span status, or audit event.
- Resource invariant: bounded memory, disk, goroutine/task count, retry count,
  or cleanup completion within a stated threshold.

If the oracle depends on timing, state the timeout and polling condition. Avoid
sleep-only checks.

## Prioritization

- `P0`: Release-blocking safety, data correctness, crash, security, or severe
  compatibility risk.
- `P1`: Core feature behavior or common failure path.
- `P2`: Important edge case, scale case, or less common compatibility path.
- `P3`: Nice-to-have coverage, exploratory validation, or low-risk variation.

Assign priority from impact first, then likelihood. Do not promote a case only
because it is easy to run.

## Case Shape

Use one case for one diagnostic risk. If a case fails, the report should be
able to classify the failure without rerunning unrelated steps.

Good case titles include the condition and expected behavior:

- `FQA-003 rejects stale checkpoint after rolling restart`
- `FQA-006 preserves old client search result shape with new server`
- `FQA-009 reports retry exhaustion with resource identity in metrics`

Weak case titles hide the risk:

- `Test checkpoint`
- `Compatibility test`
- `Verify metrics`

## Deduplication

Merge cases if they exercise the same risk, setup, action, and assertion.
Keep cases separate when failure diagnosis would differ materially.

Use these split/merge rules:

- Split API validation from persistence or recovery checks.
- Split happy path from destructive or fault-injection checks.
- Split compatibility cases by upgrade direction when diagnosis differs.
- Merge parameter variations when they share the same implementation branch
  and assertion.
- Keep scale cases separate from functional correctness cases unless scale is
  the risk being tested.

## Example: Low-Quality Case

```yaml
case_id: FQA-001
title: "Test import performance"
priority: P1
risk:
  risk_id: RISK-001
  area: large_data_volume
  description: "Performance may be bad."
preconditions:
  - "Cluster is running."
steps:
  - step: 1
    action: "Import a large file."
    expected: "Import succeeds."
assertions:
  - "Performance is acceptable."
cleanup:
  required: true
  method: "Delete data."
```

Why this is low quality:

- The risk does not name a concrete failure mode or impact.
- "Large" and "acceptable" are not measurable.
- Dataset, topology, timeout, and resource budget are missing.
- The assertion cannot diagnose whether a failure is product, environment, or
  test script related.
- No logs, metrics, or cleanup evidence are requested.

## Example: High-Quality Case

```yaml
case_id: FQA-001
title: "Bulk import completes 10M-row JSON file without partial collection state"
priority: P1
risk:
  risk_id: RISK-001
  area: large_data_volume
  description: >
    Bulk import writes metadata and segment files asynchronously. A timeout or
    partial failure could leave the collection visible with missing segments,
    causing incorrect search results after import.
preconditions:
  - "Standalone or distributed cluster has at least 8 CPU cores and 32 GiB memory."
  - "Object storage is reachable and import source file exists at s3://bucket/import/10m.json."
  - "Test collection name uses the FQA run ID prefix."
cluster_requirement:
  topology: "standalone or distributed"
  permissions:
    cleanup: true
    restart_components: false
    fault_injection: false
data_requirement:
  datasets:
    - "10M rows, dim=128, primary key range [0, 9999999], one scalar filter field."
  scale: "10M rows; import must finish within 45 minutes."
steps:
  - step: 1
    action: "Create the collection and start the bulk import task."
    expected: "Import API returns a task ID and does not create queryable partial data."
  - step: 2
    action: "Poll task state every 30 seconds until completed or 45 minutes elapse."
    expected: "Task reaches completed state before timeout."
  - step: 3
    action: "Load the collection and query count plus three deterministic primary keys."
    expected: "Count is 10000000 and all selected primary keys return exactly one entity."
assertions:
  - "Import task status is completed within 45 minutes."
  - "Collection row count equals 10000000 after load."
  - "Primary keys 0, 5000000, and 9999999 are searchable and scalar fields match source data."
  - "No query succeeds against the collection before the import task reaches completed."
observability:
  logs:
    - "Import task ID, collection name, and failure reason if any task state is failed."
  metrics:
    - "Import task duration and failed task count for the test collection."
  traces:
    - "Import request trace or task ID correlation if tracing is enabled."
cleanup:
  required: true
  method: "Drop the test collection and remove temporary import artifacts if cleanup is allowed."
status: proposed
```

Why this is high quality:

- The risk explains a concrete async metadata/segment consistency failure.
- Setup, data scale, topology, and permission requirements are explicit.
- Actions are ordered and reproducible.
- Assertions include positive and negative evidence.
- Failure evidence includes task ID, collection name, logs, and metrics.
- Cleanup is tied to the exact resources created by the case.
