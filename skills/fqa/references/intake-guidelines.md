# Feature Intake Guidelines

Use this file when a user asks to start FQA for a feature, PR, branch, issue,
design document, commit, or implementation. Intake turns the user's first
request into a traceable `intake/feature-intake.yaml` artifact without asking for
execution credentials too early.

## Core Principle

Use progressive intake. Ask only for the information needed for the current
state.

- During `Drafting`, collect enough information to understand the feature and
  generate reviewable test cases.
- Do not ask for cluster credentials, secrets, endpoint details, or execution
  permission before test cases are approved.
- After case approval, collect cluster access and execution constraints in
  `WaitingCluster`.
- Treat every inferred value as unconfirmed until it is shown to the user or
  recorded with `confidence: inferred`.

## Intake Artifact

Create `intake/feature-intake.yaml` in the feature workspace before writing
feature understanding, test plans, or cases.

Record each item with:

- `value`: the supplied or inferred value.
- `source`: `provided`, `inferred`, `missing`, or `not_applicable`.
- `confidence`: `confirmed`, `inferred`, or `unknown`.
- `notes`: short explanation, evidence path, or open question.

Do not store secrets in `intake/feature-intake.yaml`. Store only an auth method,
credential alias, or instruction such as "provided out of band".

## Minimum Drafting Inputs

To generate test cases, FQA needs at least one feature source plus enough scope
to know where to inspect.

Required before case generation:

- Feature source: PR, issue, branch, commit, diff, design document, or a clear
  feature description.
- Repository path or repository URL.
- Test scope: entire feature, selected components, or selected code paths.
- Release target when compatibility matters. If unknown, record `missing` and
  generate compatibility risks as assumptions.
- Forbidden operations known at planning time, such as destructive cleanup,
  component restarts, fault injection, load testing, or data mutation.

If a required value is missing but the agent can continue safely, record it as
missing and make the assumption explicit in the next user-facing update. Do not
block on optional details.

## Optional Drafting Context

Ask for these only when they materially improve test quality:

- Design document, requirement doc, or product note.
- Must-test user workflows.
- Must-not-test areas.
- Compatibility target: old client, old server, rolling upgrade, downgrade, or
  persisted data compatibility.
- Known incidents, previous regressions, or customer-impacting paths.
- Expected observability signals: logs, metrics, traces, dashboards, or audit
  records.
- Resource budget for planned scale tests, if the feature obviously needs
  scale or performance validation.

## First Response Pattern

When the user asks to start testing a feature and has not provided enough
context, respond with a compact intake request:

```text
State: Drafting

I can start once I know the feature source and test scope.

Please provide one of:
- PR URL or number
- branch / commit / diff
- issue or design document
- local repo path and changed files

Optional but useful:
- release target
- compatibility target
- must-test scenarios
- forbidden operations

I will not ask for cluster credentials until test cases are approved.
```

If the user provides a PR, branch, commit, design document, or repo path, inspect
what is available before asking more questions. Then summarize known, inferred,
and missing items:

```text
State: Drafting

I found:
- source: <provided or inferred source>
- repo: <repo path or URL>
- changed areas: <components or code paths>
- design doc: <found path, provided URL, or missing>
- release target: <value or missing>
- forbidden operations: <value or missing>

I can generate cases from the available source now.
Please confirm any missing release or operation constraints if they matter.
```

Ask at most one follow-up question when the missing information blocks safe case
generation. Prefer continuing with explicit assumptions over asking a long
questionnaire.

## Inference Rules

Prefer verified source signals in this order:

1. User-provided PR, design document, issue, branch, commit, or diff.
2. Local repository status, current branch, staged diff, and changed files.
3. Source code, tests, proto/API definitions, config, and migration logic.
4. README or implementation notes.
5. Prior workflow artifacts for the same feature.

When inferring:

- Record where the inference came from.
- Use conservative wording in user updates.
- Do not infer permission for destructive operations.
- Do not infer cluster access or execution approval.
- Do not infer acceptance of generated cases.

## Missing Information Policy

Block only when proceeding would create low-quality or unsafe artifacts.

Block in `Drafting` when:

- There is no feature source and no clear feature description.
- There is no repository path or inspectable source.
- The scope is too ambiguous to produce meaningful risks.

Continue with explicit assumptions when:

- Release target is unknown, but compatibility cases can be marked as
  assumptions.
- Design document is missing, but code or diff can be inspected.
- Forbidden operations are unknown; default them to not allowed.
- Observability access is unknown; generate observability expectations without
  requiring execution access.

## Cluster Intake After Case Approval

Only after test cases are approved, move to `WaitingCluster` and ask for:

- Endpoint alias or endpoint and protocol.
- Authentication method or credential alias.
- Namespace, database, tenant, project, or resource group.
- Resource name prefix.
- Cleanup permission.
- Resource budget.
- Whether component restart, fault injection, or chaos operations are allowed.
- Log, metric, trace, and dashboard access.
- Execution approval for the target cluster.

Separate credentials from reports and artifacts. If the user sends a secret,
do not repeat it back.

## User Interaction Rules

- Keep each user-facing update short.
- Always state the current state and next gate.
- Separate required inputs from optional inputs.
- Ask for secrets only when execution is approved and only as aliases when
  possible.
- Never request cluster details before case approval.
- Never advance past an approval gate based on inferred information.
- When blocked, state the smallest missing item that unblocks progress.

## Resume Behavior

When resuming a workflow:

1. Read `state.yaml`.
2. Read `intake/feature-intake.yaml` if present.
3. Report known, inferred, and missing intake items only if they affect the
   next gate.
4. Do not re-ask questions that already have confirmed answers.
5. If intake is missing for an older workflow, create it from existing
   artifacts and mark inferred values as `inferred`.
