# Design Understanding

feature_id: `<feature_id>`
state: `Drafting`

## Source Summary

| Source | Path or URL | Status | Notes |
| --- | --- | --- | --- |
| Design doc |  | provided|missing|inferred |  |
| PR or diff |  | provided|missing|inferred |  |
| Issue or request |  | provided|missing|inferred |  |

## Behavior Model

### Documented Behavior

- Claim:
  - Evidence:
  - Confidence: confirmed|inferred|unknown
  - QA impact:

### Inferred Behavior

- Claim:
  - Evidence:
  - Confidence: inferred|unknown
  - QA impact:

### Changed Behavior

- Before:
  - Evidence:
- After:
  - Evidence:
- Compatibility impact:
- QA impact:

### Unknown or Ambiguous Behavior

- Question:
  - Why it matters:
  - Evidence gap:
  - Blocking: yes|no

## Goals

- Goal:
  - Evidence:
  - Confidence: confirmed|inferred|unknown

## Non-Goals

- Non-goal:
  - Evidence:
  - Confidence: confirmed|inferred|unknown

## User Workflows

1. Workflow:
   - Actor:
   - Inputs:
   - Actions:
   - Expected outputs:
   - Evidence:
   - QA impact:

## External Contracts

| Contract | Expected behavior | Evidence | Compatibility impact | QA impact |
| --- | --- | --- | --- | --- |
| API |  |  |  |  |
| Config |  |  |  |  |
| CLI |  |  |  |  |
| Storage |  |  |  |  |
| Metrics |  |  |  |  |
| Logs or errors |  |  |  |  |

## Compatibility Expectations

- Upgrade:
  - Expected behavior:
  - Evidence:
  - Risk:
- Rollback:
  - Expected behavior:
  - Evidence:
  - Risk:
- Existing data:
  - Expected behavior:
  - Evidence:
  - Risk:
- Existing clients:
  - Expected behavior:
  - Evidence:
  - Risk:

## Risk Seeds

- risk_seed_id: RS-DESIGN-001
  source_claim:
  evidence:
  risk_statement: Because <source behavior or change>, users could hit <failure mode>, causing <impact>.
  observable_assertion:
  priority_hint: P0|P1|P2|P3
  coverage_area: primary_workflow|api_contract|compatibility|recovery|observability|security|other

## Quality Gate

- All major claims have evidence: yes|no
- Inferred behavior is separated from documented behavior: yes|no
- Unknowns that affect test design are listed: yes|no
- Compatibility expectations are covered or marked not applicable: yes|no
- Risk seeds are specific and observable: yes|no
