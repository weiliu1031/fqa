# FQA

FQA is a Codex skill for feature-level QA orchestration.

It guides an agent through a gated workflow:

1. Understand the feature from design documents and source code.
2. Generate design and implementation understanding when documents are missing.
3. Build a risk model and feature-level test cases.
4. Wait for human approval and test-cluster connection details.
5. Generate executable test scripts for approved cases.
6. Execute scripts and collect evidence.
7. Produce a test report and issue candidates.
8. Wait for human approval before creating issues.
9. Track fixes, rerun regression tests, and update the report.

FQA is intentionally not a unit-test generator. It is for feature QA across
systems, clusters, workflows, compatibility, failure handling, observability,
and regression verification.

## Install

Install the skill into the default Codex skills directory:

```bash
./scripts/install-skill.sh
```

Or install to a custom directory:

```bash
./scripts/install-skill.sh /path/to/skills
```

After installation, invoke it as:

```text
Use $fqa to generate feature-level test cases for this PR.
Use $fqa to execute the approved test plan on this cluster.
Use $fqa to regress the issues fixed by these PRs.
```

## Project Layout

```text
skills/fqa/                 Codex skill package
skills/fqa/SKILL.md         Core workflow and guardrails
skills/fqa/references/      Detailed workflow, schemas, and guidelines
skills/fqa/assets/templates Reusable artifact templates
scripts/install-skill.sh    Copy the skill into a Codex skills directory
scripts/validate-skill.sh   Validate skill metadata and required resources
examples/                   Example task inputs and expected artifact shape
```

## Human Gates

FQA must stop at these gates:

- Test case review before generating test scripts.
- Cluster access review before executing tests.
- Issue candidate review before creating issues.

The skill should not bypass those gates unless the user explicitly provides
approval in the current conversation.

## License

MIT
