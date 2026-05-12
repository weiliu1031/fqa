# Implementation Understanding

feature_id: `<feature_id>`
state: `Drafting`

## Source Inputs

- Repository:
- Worktree:
- Branch:
- Commit:
- PR:
- Diff:
- Code paths:

## Change Inventory

| File | Symbols | Change type | Responsibility | Evidence | Risk |
| --- | --- | --- | --- | --- | --- |
|  |  | add|modify|delete|config|test|docs |  |  |  |

## Component Map

| Component | Files | Responsibility | Upstream callers | Downstream dependencies | Risk |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Execution Paths

### Path 1

- Entry point:
  - Evidence:
- Call chain:
  - Step:
    - Function or method:
    - File:
    - Evidence:
- State mutation:
  - What changes:
  - Established by:
  - Consumed by:
  - Evidence:
- Persistence:
  - Storage or metadata touched:
  - Evidence:
- Async or background work:
  - Job or task:
  - Trigger:
  - Completion signal:
  - Evidence:
- User-visible result:
  - Evidence:
- QA impact:

## State and Invariants

- Invariant:
  - Established by:
  - Consumed by:
  - Violation impact:
  - Evidence:
  - Confidence: confirmed|inferred|unknown

## Failure Paths

- Failure:
  - Trigger:
  - Expected handling:
  - Evidence:
  - Observable signal:
  - QA impact:

## Compatibility and Migration Paths

- Scenario:
  - Old behavior:
  - New behavior:
  - Migration or fallback:
  - Evidence:
  - QA impact:

## Observability

- Logs:
  - Signal:
  - Evidence:
- Metrics:
  - Signal:
  - Evidence:
- Traces:
  - Signal:
  - Evidence:
- Error messages:
  - Signal:
  - Evidence:

## Implementation Assumptions

- Assumption:
  - Evidence:
  - Confidence: confirmed|inferred|unknown
  - What would falsify it:
  - QA impact:

## Risk Seeds

- risk_seed_id: RS-IMPL-001
  source_path:
  source_symbol:
  evidence:
  risk_statement: Because <implementation behavior or change>, users could hit <failure mode>, causing <impact>.
  observable_assertion:
  priority_hint: P0|P1|P2|P3
  coverage_area: data_flow|state_invariant|persistence|async_work|recovery|observability|compatibility|other

## Quality Gate

- All changed files are represented in Change Inventory: yes|no
- Main execution paths are traced from entry point to user-visible result: yes|no
- State mutations and invariants are identified: yes|no
- Failure paths include observable signals: yes|no
- Assumptions have confidence and falsification notes: yes|no
- Risk seeds are specific and observable: yes|no
