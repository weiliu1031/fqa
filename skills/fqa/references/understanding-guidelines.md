# Understanding Guidelines

Use this file before writing `planning/understanding/design-understanding.md`
and `planning/understanding/implementation-understanding.md`.

## Goal

Understanding artifacts must convert feature source into evidence-backed
claims and risk seeds. They are not summaries. They are the traceable bridge
between source inspection and feature-level QA cases.

## Evidence Rules

Every major claim needs evidence. Prefer evidence in this order:

1. Design document section, issue requirement, PR description, or user-provided
   requirement.
2. Diff hunk, changed file, function, method, config, schema, or migration.
3. Existing tests, examples, docs, or operational notes.
4. Inference from code paths, marked as `Confidence: inferred`.

If evidence is missing, keep the claim only when it affects test design and
mark `Confidence: unknown`.

## Design Understanding Process

Separate design facts from inferred behavior:

- `Documented Behavior`: behavior explicitly stated in a design, issue, PR, or
  user request.
- `Inferred Behavior`: behavior inferred from code or surrounding contracts.
- `Changed Behavior`: before/after behavior that users or operators can
  observe.
- `Unknown or Ambiguous Behavior`: missing decisions that affect test design.

Do not state inferred behavior as fact. If the design document is missing,
say so and build the behavior model from code evidence.

## Implementation Understanding Process

Trace implementation from source to observable behavior:

1. List changed files and changed symbols.
2. Group files by component and responsibility.
3. Trace each important execution path:
   entry point -> call chain -> state mutation -> persistence -> async work ->
   user-visible result.
4. Identify invariants established or consumed by the change.
5. Identify failure paths and their observable signals.
6. Identify compatibility or migration behavior.

Do not stop at changed files. Follow downstream code until the user-visible or
system-visible effect is clear enough to test.

## Risk Seeds

Each understanding artifact must produce risk seeds. Use this shape:

```text
- risk_seed_id: RS-DESIGN-001 or RS-IMPL-001
  source_claim:
  source_path:
  source_symbol:
  evidence:
  risk_statement: Because <source behavior or change>, users could hit <failure mode>, causing <impact>.
  observable_assertion:
  priority_hint: P0|P1|P2|P3
  coverage_area:
```

Good risk seeds are specific enough to become one or more test cases. Reject or
rewrite risk seeds whose assertion is "works", "succeeds", or "is normal".

## Quality Gate

Before generating test cases, verify:

- Major claims include evidence.
- Design facts and inferred behavior are separated.
- Unknowns that affect case generation are listed.
- Changed files and important unchanged downstream files are represented.
- Main execution paths are traced to user-visible or system-visible effects.
- State mutations, invariants, persistence, async work, and failure paths are
  covered when applicable.
- Risk seeds have concrete failure modes and observable assertions.

Run `scripts/fqa_check_understanding.py <feature_workspace>` when available.
Fix reported errors before moving to `CaseReview`, unless the missing
information is explicitly marked unknown and carried into test risk.
