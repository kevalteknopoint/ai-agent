#!/usr/bin/env bash
# install-standalone-agents.sh [target-dir]
#
# Installs standalone BMAD agents that can be invoked directly by name
# (not through the bmad-* skill system).
#
# These agents are installed to ~/.claude/agents by default, making them
# available from any project on the machine.
#
# Copies files from _bmad/agents/ to your global ~/.claude/agents/ directory.
# Re-run after pulling updates to sync the latest versions.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Default to user's home directory if no target specified
TARGET="${1:-$HOME/.claude}"

AGENTS=(
  tech-architecture-doc
  vbrd-to-proofhub
  wp-to-eds-migrator
  security-scan
  perf-test
)

echo "Installing standalone agents from BMAD structure..."
echo "Source: $SRC/_bmad/agents/"
echo "Target: $TARGET/agents/"
echo ""

mkdir -p "$TARGET/agents"

for a in "${AGENTS[@]}"; do
  if [ -f "$SRC/_bmad/agents/$a.md" ]; then
    cp "$SRC/_bmad/agents/$a.md" "$TARGET/agents/$a.md"
    echo "✓ Installed: $a"
  else
    echo "⚠ Warning: $SRC/_bmad/agents/$a.md not found"
  fi
done

echo ""
echo "Installation complete!"
echo ""
echo "Installed agents are now available in any Claude Code session."
echo "Source of truth: $SRC/_bmad/agents/"
echo ""
echo "Note: These agents may reference scripts in $SRC/scripts/"
echo "Keep this toolkit repo at a stable path for agents to work correctly."
