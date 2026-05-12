# Test Design Patterns

Use this file before writing `planning/test-plan.yaml`. It captures patterns
from concrete feature test designs and prevents FQA from collapsing detailed
coverage into overly broad risk cases.

## Risk Spine Plus Scenario Matrix

Start with a small risk spine, then expand each risk into a scenario matrix.
The risk spine explains why the area matters; the scenario matrix explains
exactly what must be executed.

Use a scenario matrix when the feature includes any of these dimensions:

- Type variants: element types, scalar types, vector types, nullable vs
  non-nullable, old schema vs new schema.
- Operation variants: append, remove, update, delete, replace, retry, cancel,
  load, release, flush, query, search.
- Validation branches: invalid field, invalid type, missing payload, unknown
  parameter, unsupported target, permission failure.
- Boundary values: empty, single element, duplicate, no match, exact capacity,
  overflow, max length, null payload, null stored value.
- System modes: standalone, distributed, old client, mixed version, restart,
  recovery, index path, filter path, concurrent requests.

## Scenario Matrix Shape

Add `scenario_matrix` to `planning/test-plan.yaml`:

```yaml
scenario_matrix:
  - scenario_id: SCN-001
    risk_id: RISK-001
    risk_seed_ids:
      - RS-DESIGN-001
    case_id: FQA-001
    priority: P0
    category: type_variant|operation_variant|validation|boundary|system_mode|compatibility|concurrency
    parameters:
      element_type: Bool|Int8|Int16|Int32|Int64|Float|Double|VarChar|null
      operation: append|remove|null
      boundary: empty|single|duplicate|no_match|exact_capacity|overflow|null_payload|null_stored|null
    setup: string
    action: string
    expected: string
    decision_status: confirmed|needs_decision|not_applicable
    notes: string
```

Keep scenario IDs stable. A single executable case may cover multiple
scenarios only when it can report each scenario independently, for example via
pytest parametrization.

## Open Decisions

When expected behavior is not explicit, do not invent it. Add an
`open_decisions` entry:

```yaml
open_decisions:
  - decision_id: DEC-001
    scenario_ids:
      - SCN-003
    question: string
    options:
      - string
    impact: string
    owner: string|null
    status: needs_decision
```

Cases that depend on unresolved behavior should be proposed as blocked or
pending-decision scenarios, not as confirmed pass/fail expectations.

## Learned Pattern: Array Partial Update

For Array partial update style features, preserve both levels:

- Risk spine: append/remove correctness, validation, capacity, multi-field
  mapping, persistence/recovery, compatibility, concurrency.
- Scenario matrix:
  - Append type variants: Bool, Int8, Int16, Int32, Int64, Float, Double,
    VarChar.
  - Remove type variants: Bool, Int8, Int16, Int32, Int64, Float, Double,
    VarChar when the requirement says all element types.
  - Validation: non-array field, primary key field, unknown field, element type
    mismatch, missing field data, automatic partial update behavior.
  - Boundaries: empty array, remove all, no-match remove, duplicate remove,
    single element append/remove, nullable payload row, append to stored null,
    exact capacity, overflow by type, VarChar max length.
  - System modes: multi-field same request, flush/reload/filter path,
    compatibility boundary, concurrent same-primary-key upserts.

If a document says "all element types" but lists only a subset, mark the
missing types as `partial` or `missing` in the coverage matrix.

Also include a `dimension_coverage` row:

```yaml
dimension_coverage:
  - dimension: array_partial_update
    applies_when: ARRAY_APPEND or ARRAY_REMOVE changes Array field behavior
    status: covered|partial|missing
    required:
      operations: [append, remove]
      element_types: [Bool, Int8, Int16, Int32, Int64, Float, Double, VarChar]
      boundaries: [empty_base, single_element, duplicate, no_match, remove_all, exact_capacity, overflow, varchar_max_length]
      system_modes: [multi_field, mixed_insert_update, flush_reload_filter, compatibility, concurrency, sdk]
    covered:
      append_element_types: []
      remove_element_types: []
      boundaries: []
      system_modes: []
    scenario_ids: []
    gaps: []
```

For Array partial update, a `covered` dimension row must include every required
operation, append/remove element type, boundary, and system mode above. If an
environment is unavailable, a product decision is pending, or a type is omitted,
the row must be `partial` or `missing`. Nullable behavior should be isolated in
an `open_decisions` scenario or a blocked case, not mixed into a confirmed
multi-risk case.

## Quality Rules

- Do not replace a concrete matrix with one abstract case.
- Do not mark a matrix dimension covered unless a case or parameter row names
  it explicitly.
- Do not treat unresolved semantics as confirmed expected behavior.
- Do not mark a coverage or dimension row `covered` if its gap mentions missing
  environment, pending decisions, skipped execution, or follow-up work.
- Do not mix `decision_status: needs_decision` and confirmed assertions in the
  same diagnostic case unless the pending scenario is explicitly blocked.
- Prefer parameterized cases for repetitive type/boundary rows, but keep
  validation branches separate when failure diagnosis differs.
- Every `P0` scenario must either have a case or an explicit open decision.
