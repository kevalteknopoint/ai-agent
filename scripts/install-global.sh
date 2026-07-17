#!/usr/bin/env bash
# install-global.sh [target-claude-dir]
#
# Installs the code-scan system (5 analyzer agents + the router agent + the
# rescan verifier + the workflow + the skill) into a Claude Code project-scope
# `.claude/` directory so it's invokable from ANY project nested under it —
# not just from inside this toolkit repo.
#
# Why this location and not this repo's own agents/workflows/skills dirs:
# Claude Code discovers agents/workflows/skills by walking UP from the
# current directory looking for `.claude/agents`, `.claude/workflows`,
# `.claude/skills` (merged with the ones in `~/.claude`). Every other
# custom agent in this environment (aem-test-case-creator, eds-block-
# creator, spring-boot-test-creator, ...) already lives in
# project-source/.claude/ for exactly this reason — placing code-scan
# there means it works from any client repo under project-source/projects/
# without per-project setup.
#
# Re-run this script after editing anything under agents/, workflows/, or
# skills/ in this repo to re-sync the installed copies.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-/Users/kevaljoshi/Documents/project-source/.claude}"

mkdir -p "$TARGET/agents" "$TARGET/workflows" "$TARGET/skills/code-scan"

cp "$SRC/agents/code-scan-orchestrator.md" "$TARGET/agents/"
cp "$SRC/agents/code-scan-verifier.md" "$TARGET/agents/"
cp "$SRC/agents/java-springboot-analyzer.md" "$TARGET/agents/"
cp "$SRC/agents/aem-htl-analyzer.md" "$TARGET/agents/"
cp "$SRC/agents/eds-blocks-analyzer.md" "$TARGET/agents/"
cp "$SRC/agents/js-react-analyzer.md" "$TARGET/agents/"
cp "$SRC/agents/css-scss-analyzer.md" "$TARGET/agents/"
cp "$SRC/workflows/code-scan.js" "$TARGET/workflows/"
cp "$SRC/skills/code-scan/SKILL.md" "$TARGET/skills/code-scan/"

echo "Installed into $TARGET:"
echo "  agents:    code-scan-orchestrator, code-scan-verifier, java-springboot-analyzer,"
echo "             aem-htl-analyzer, eds-blocks-analyzer, js-react-analyzer, css-scss-analyzer"
echo "  workflow:  code-scan.js"
echo "  skill:     code-scan"
echo ""
echo "New Claude Code sessions started from anywhere under $(dirname "$TARGET") will now see these."
echo "This toolkit repo's absolute path ($SRC) is what the agents use to find the shared"
echo "scripts/ (build_issues_csv.py, plan_verification.py, apply_verdicts.py,"
echo "build_rescan_summary.py) — that still works regardless of where the scan target lives."
