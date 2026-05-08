# Report Guidelines

## Report Goals

The report must answer:

- What was tested?
- What risks were covered?
- What passed?
- What failed?
- What was blocked or skipped?
- What evidence supports the result?
- What issues should be created?
- What remains risky after this run?

## Failure Classification

Use one classification per failure:

- `product_bug`: Product behavior violates expected behavior.
- `test_bug`: Test script, assertion, or setup is wrong.
- `environment`: Cluster, dependency, quota, or access issue.
- `requirement_ambiguity`: Expected behavior cannot be determined.
- `blocked`: Required permission, data, or dependency is unavailable.

Do not report a run as successful when evidence is missing. Mark it blocked or
incomplete.

## Evidence

Prefer stable links or artifact paths over copied logs. Include enough raw
details to reproduce the failure, but do not include credentials or secrets.

## Release Signal

End with one of:

- `PASS`: Required cases passed and no release-blocking risk remains.
- `FAIL`: One or more P0/P1 product bugs remain.
- `BLOCKED`: Required coverage could not be executed.
- `PARTIAL`: Some non-blocking coverage remains incomplete.
