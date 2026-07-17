#!/usr/bin/env bash
# install-standalone-agents.sh [target-claude-dir]
#
# Installs the STANDALONE agents — the ones invoked directly by name rather
# than dispatched by the code-scan workflow — into a Claude Code directory
# that's on the discovery path.
#
# Why a separate script from install-global.sh:
#   install-global.sh installs the *code-scan system* (router + 5 analyzers +
#   workflow + skill) and defaults to project-source/.claude, which only
#   covers repos nested under project-source/. The agents here are used from
#   anywhere on the machine (e.g. ai-initiative/presales, client repos in
#   arbitrary locations), so they default to `~/.claude` — the only directory
#   Claude Code merges in regardless of cwd.
#
# Copies, not symlinks — matching this environment's existing convention.
# Re-run after editing anything under agents/; installed copies don't
# auto-update. Agents are read at session start, so start a fresh Claude Code
# session to pick up changes.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$HOME/.claude}"

AGENTS=(
  tech-architecture-doc
  vbrd-to-proofhub
)

mkdir -p "$TARGET/agents"

for a in "${AGENTS[@]}"; do
  cp "$SRC/agents/$a.md" "$TARGET/agents/$a.md"
done

echo "Installed into $TARGET/agents:"
for a in "${AGENTS[@]}"; do
  echo "  - $a"
done
echo ""
echo "Source of truth stays at $SRC/agents/ — re-run this script after editing."
echo "tech-architecture-doc shells out to $SRC/scripts/{clone_or_update,detect_stack}.sh"
echo "via the aiAgentRepo input, so the installed copy works from any directory"
echo "as long as this toolkit repo stays at a stable path."
