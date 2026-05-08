# Issue Guidelines

## When to Create an Issue Candidate

Create an issue candidate for:

- Product bugs.
- Requirement ambiguities that require a decision.
- Reproducible compatibility or recovery failures.

Do not create issue candidates for:

- Test script bugs.
- Temporary environment failures.
- Missing credentials or permissions.
- Duplicate failures with the same root cause.

## Candidate Requirements

Each issue candidate must include:

- Clear title.
- Severity.
- Component.
- Affected case IDs and run IDs.
- Expected behavior.
- Actual behavior.
- Reproduction steps.
- Evidence links or artifact paths.
- Suspected root cause, if supported by evidence.

## Approval Rule

Never create issues automatically. Present candidates and wait for the user to
approve, reject, merge, or edit them.

## Linkage

After creating an issue, update the report and structured artifacts with:

- Issue URL.
- Related case IDs.
- Related run IDs.
- Related failure IDs.
- Fix PR or commit once available.
