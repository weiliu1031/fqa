#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$ROOT_DIR/skills/fqa"
VALIDATOR="${SKILL_CREATOR_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

PYTHONDONTWRITEBYTECODE=1 python3 "$VALIDATOR" "$SKILL_DIR"

version="$(awk '
  /^---$/ { fence++; next }
  fence == 1 && /^[[:space:]]*version:/ { print $2; exit }
' "$SKILL_DIR/SKILL.md")"

if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid or missing FQA skill version: $version" >&2
  exit 1
fi

required=(
  "$SKILL_DIR/SKILL.md"
  "$SKILL_DIR/agents/openai.yaml"
  "$SKILL_DIR/references/workflow.md"
  "$SKILL_DIR/references/artifact-schema.md"
  "$SKILL_DIR/references/intake-guidelines.md"
  "$SKILL_DIR/references/test-case-guidelines.md"
  "$SKILL_DIR/references/report-guidelines.md"
  "$SKILL_DIR/references/issue-guidelines.md"
  "$SKILL_DIR/assets/templates/design-understanding.md"
  "$SKILL_DIR/assets/templates/feature-intake.yaml"
  "$SKILL_DIR/assets/templates/implementation-understanding.md"
  "$SKILL_DIR/assets/templates/state.yaml"
  "$SKILL_DIR/assets/templates/test-plan.yaml"
  "$SKILL_DIR/assets/templates/test-case.yaml"
  "$SKILL_DIR/assets/templates/test-script-header.py"
  "$SKILL_DIR/assets/templates/test-run-result.yaml"
  "$SKILL_DIR/assets/templates/test-report.md"
  "$SKILL_DIR/assets/templates/issue-candidate.yaml"
  "$SKILL_DIR/scripts/fqa_status.py"
  "$SKILL_DIR/scripts/fqa_validate_workspace.py"
)

for path in "${required[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: $path" >&2
    exit 1
  fi
done

for script in "$SKILL_DIR/scripts/fqa_status.py" "$SKILL_DIR/scripts/fqa_validate_workspace.py"; do
  if [[ ! -x "$script" ]]; then
    echo "Required script is not executable: $script" >&2
    exit 1
  fi
done

PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_status.py" --help >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_validate_workspace.py" --help >/dev/null

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
base_dir="$tmp_dir/fqa-base"
workspace="$base_dir/features/fqa-feature-YYYYMMDD-source"
mkdir -p "$workspace"/{intake,planning/understanding,planning/cases,execution/scripts,execution/runs,closure/reports,closure/issues}
cp "$SKILL_DIR/assets/templates/state.yaml" "$workspace/state.yaml"
cp "$SKILL_DIR/assets/templates/feature-intake.yaml" "$workspace/intake/feature-intake.yaml"
FQA_BASE_DIR="$base_dir" PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_status.py" >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_validate_workspace.py" "$workspace" >/dev/null

legacy_workspace="$tmp_dir/repo/.fqa/features/fqa-feature-legacy-YYYYMMDD-source"
mkdir -p "$legacy_workspace"/{cases,scripts,runs,reports,issues}
cp "$SKILL_DIR/assets/templates/state.yaml" "$legacy_workspace/state.yaml"
cp "$SKILL_DIR/assets/templates/feature-intake.yaml" "$legacy_workspace/feature-intake.yaml"
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/fqa_status.py" --root "$tmp_dir/repo" --legacy-only >/dev/null

echo "FQA skill resources validated"
