# Test Case Guidelines

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
- Concrete setup.
- Exact user or system actions.
- Observable assertions.
- Required cluster capability.
- Cleanup plan.
- Priority.

Avoid vague cases like "test performance" or "verify error handling". Replace
them with measurable assertions.

## Prioritization

- `P0`: Release-blocking safety, data correctness, crash, security, or severe
  compatibility risk.
- `P1`: Core feature behavior or common failure path.
- `P2`: Important edge case, scale case, or less common compatibility path.
- `P3`: Nice-to-have coverage, exploratory validation, or low-risk variation.

## Deduplication

Merge cases if they exercise the same risk, setup, action, and assertion.
Keep cases separate when failure diagnosis would differ materially.
