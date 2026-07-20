#!/usr/bin/env bash
# install-global.sh [target-dir]
#
# Installs the BMAD-structured AEM Toolkit skills into your IDE's global
# configuration directory, making all bmad-* skills available from any project.
#
# For Claude Code: Installs to ~/.claude/skills/ (or custom target)
# For Cursor/Windsurf: Also installs to ~/.agents/skills/
#
# This copies the skill launchers from .claude/skills/ and .agents/skills/
# in this repo to your global IDE configuration, making them discoverable
# from any workspace.
#
# Re-run this script after pulling updates to sync the latest versions.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Default to user's home directory if no target specified
# Users can override with: ./scripts/install-global.sh /custom/path
CLAUDE_TARGET="${1:-$HOME/.claude}"
AGENTS_TARGET="${1:-$HOME/.agents}"

echo "Installing AEM Toolkit BMAD skills..."
echo "Source: $SRC"
echo "Claude Code target: $CLAUDE_TARGET/skills/"
echo "Cursor/Windsurf target: $AGENTS_TARGET/skills/"
echo ""

# Install Claude Code skills
mkdir -p "$CLAUDE_TARGET/skills"
if [ -d "$SRC/.claude/skills" ]; then
  cp -r "$SRC/.claude/skills/"* "$CLAUDE_TARGET/skills/" 2>/dev/null || true
  echo "✓ Installed Claude Code skills (10 skills)"
else
  echo "⚠ Warning: .claude/skills not found in source"
fi

# Install Cursor/Windsurf skills
mkdir -p "$AGENTS_TARGET/skills"
if [ -d "$SRC/.agents/skills" ]; then
  cp -r "$SRC/.agents/skills/"* "$AGENTS_TARGET/skills/" 2>/dev/null || true
  echo "✓ Installed Cursor/Windsurf skills (10 skills)"
else
  echo "⚠ Warning: .agents/skills not found in source"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Available skills:"
echo "  - bmad-help               Context-aware guidance"
echo "  - bmad-code-scan          Multi-agent code scanning"
echo "  - bmad-security-scan      Zero-AI security scanning"
echo "  - bmad-perf-test          k6 performance testing"
echo "  - bmad-quality-gate       Rule-driven quality enforcement"
echo "  - bmad-tech-arch          Architecture documentation"
echo "  - bmad-wp-to-eds          WordPress to EDS migration"
echo "  - bmad-vbrd-to-proofhub   Visual BRD to ProofHub"
echo "  - bmad-unit-test-aem      AEM unit test generation"
echo "  - bmad-unit-test-spring   Spring Boot unit test generation"
echo ""
echo "Usage:"
echo "  Start a new IDE session and run: bmad-help"
echo ""
echo "To update: Re-run this script after pulling repo updates"
