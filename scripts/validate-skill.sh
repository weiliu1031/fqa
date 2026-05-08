#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$ROOT_DIR/skills/fqa"
VALIDATOR="${SKILL_CREATOR_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

python3 "$VALIDATOR" "$SKILL_DIR"

required=(
  "$SKILL_DIR/SKILL.md"
  "$SKILL_DIR/agents/openai.yaml"
  "$SKILL_DIR/references/workflow.md"
  "$SKILL_DIR/references/artifact-schema.md"
  "$SKILL_DIR/references/test-case-guidelines.md"
  "$SKILL_DIR/references/report-guidelines.md"
  "$SKILL_DIR/references/issue-guidelines.md"
  "$SKILL_DIR/assets/templates/design-understanding.md"
  "$SKILL_DIR/assets/templates/implementation-understanding.md"
  "$SKILL_DIR/assets/templates/state.yaml"
  "$SKILL_DIR/assets/templates/test-plan.yaml"
  "$SKILL_DIR/assets/templates/test-case.yaml"
  "$SKILL_DIR/assets/templates/test-script-header.py"
  "$SKILL_DIR/assets/templates/test-run-result.yaml"
  "$SKILL_DIR/assets/templates/test-report.md"
  "$SKILL_DIR/assets/templates/issue-candidate.yaml"
)

for path in "${required[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
done

echo "FQA skill resources validated"
