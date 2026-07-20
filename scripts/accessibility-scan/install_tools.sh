#!/usr/bin/env bash
################################################################################
# install_tools.sh — Install accessibility scanning tools (idempotent)
#
# Zero AI. Installs open-source accessibility tools via npm/Homebrew.
# Safe to re-run — skips tools already installed.
#
# Tools installed:
#   @axe-core/cli     — Runtime WCAG scanning (axe-core engine)
#   pa11y             — Runtime accessibility testing (multiple runners)
#   lighthouse        — Google's accessibility audit (CLI mode)
#   html-validate     — HTML validity + accessibility rules
#   eslint            — Pluggable linter (with a11y plugins)
#   puppeteer         — Headless Chrome for runtime scanning
#
# Usage: bash install_tools.sh [--check-only]
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECK_ONLY=false
[[ "${1:-}" == "--check-only" ]] && CHECK_ONLY=true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Check Node.js ───
if ! command -v node &>/dev/null; then
  echo -e "${RED}Error: Node.js is required. Install via: brew install node${NC}"
  exit 2
fi

NODE_VERSION=$(node --version)
echo -e "${BLUE}Node.js: ${NODE_VERSION}${NC}"

# ─── Check npm global tools ───
NPM_TOOLS=(
  "@axe-core/cli:axe"
  "pa11y:pa11y"
  "lighthouse:lighthouse"
  "html-validate-cli:html-validate"
  "puppeteer:puppeteer"
)

MISSING=()
PRESENT=()

for entry in "${NPM_TOOLS[@]}"; do
  pkg="${entry%%:*}"
  cmd="${entry##*:}"
  
  # Check if command exists globally or in local node_modules
  if command -v "$cmd" &>/dev/null || npx --no-install "$cmd" --version &>/dev/null 2>&1; then
    ver=$("$cmd" --version 2>/dev/null || npx --no-install "$cmd" --version 2>/dev/null || echo "installed")
    PRESENT+=("$pkg ($ver)")
  else
    MISSING+=("$pkg")
  fi
done

# Also check for eslint with jsx-a11y plugin
if command -v eslint &>/dev/null; then
  PRESENT+=("eslint ($(eslint --version 2>/dev/null || echo 'installed'))")
else
  MISSING+=("eslint")
fi

echo -e "\n${BLUE}=== Accessibility Tools Status ===${NC}"
for p in "${PRESENT[@]}"; do
  echo -e "  ${GREEN}✓${NC} $p"
done
for m in "${MISSING[@]}"; do
  echo -e "  ${RED}✗${NC} $m — not installed"
done

if [[ ${#MISSING[@]} -eq 0 ]]; then
  echo -e "\n${GREEN}All accessibility tools installed.${NC}"
  exit 0
fi

if $CHECK_ONLY; then
  echo -e "\n${YELLOW}Missing ${#MISSING[@]} tool(s). Run without --check-only to install.${NC}"
  exit 1
fi

echo -e "\n${BLUE}Installing ${#MISSING[@]} missing tool(s)...${NC}\n"

# ─── Install via npm global ───
for m in "${MISSING[@]}"; do
  echo -e "${BLUE}Installing $m...${NC}"
  case "$m" in
    "@axe-core/cli")
      npm install -g @axe-core/cli
      ;;
    "pa11y")
      npm install -g pa11y pa11y-ci
      ;;
    "lighthouse")
      npm install -g lighthouse
      ;;
    "html-validate-cli")
      npm install -g html-validate html-validate-cli
      ;;
    "puppeteer")
      npm install -g puppeteer
      ;;
    "eslint")
      npm install -g eslint eslint-plugin-jsx-a11y
      ;;
    *)
      echo -e "${YELLOW}Unknown tool: $m — skipping${NC}"
      ;;
  esac
  
  if [[ $? -eq 0 ]]; then
    echo -e "  ${GREEN}✓ $m installed${NC}"
  else
    echo -e "  ${RED}✗ $m failed to install${NC}"
  fi
done

echo -e "\n${GREEN}Installation complete. Re-run with --check-only to verify.${NC}"
