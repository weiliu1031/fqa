#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="${1:-${CODEX_HOME:-$HOME/.codex}/skills}"
TARGET_DIR="$TARGET_ROOT/fqa"

mkdir -p "$TARGET_ROOT"
rm -rf "$TARGET_DIR"
cp -R "$ROOT_DIR/skills/fqa" "$TARGET_DIR"

version="$(awk '
  /^---$/ { fence++; next }
  fence == 1 && /^[[:space:]]*version:/ { print $2; exit }
' "$TARGET_DIR/SKILL.md")"

echo "Installed fqa skill $version to $TARGET_DIR"
