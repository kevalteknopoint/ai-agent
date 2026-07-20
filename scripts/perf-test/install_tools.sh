#!/usr/bin/env bash
################################################################################
# install_tools.sh — Install performance testing tools (idempotent)
#
# Zero AI. Installs k6 (primary load testing tool) and optional JMeter.
# Safe to re-run — skips tools already installed.
#
# Usage: bash install_tools.sh [--check-only] [--with-jmeter]
################################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECK_ONLY=false
WITH_JMETER=false

for arg in "$@"; do
  case "$arg" in
    --check-only)   CHECK_ONLY=true  ;;
    --with-jmeter)  WITH_JMETER=true ;;
  esac
done

TOOLS=(k6)
$WITH_JMETER && TOOLS+=(jmeter)

# Also check python3 for report generation
TOOLS+=(python3)

MISSING=()
PRESENT=()

for tool in "${TOOLS[@]}"; do
  if command -v "$tool" &>/dev/null; then
    ver=$("$tool" version 2>/dev/null || "$tool" --version 2>/dev/null | head -1 || echo "unknown")
    PRESENT+=("$tool ($ver)")
  else
    MISSING+=("$tool")
  fi
done

echo -e "${BLUE}=== Performance Testing Tools Status ===${NC}"
for p in "${PRESENT[@]}"; do
  echo -e "  ${GREEN}✓${NC} $p"
done
for m in "${MISSING[@]}"; do
  echo -e "  ${RED}✗${NC} $m — not installed"
done

if [[ ${#MISSING[@]} -eq 0 ]]; then
  echo -e "\n${GREEN}All tools installed.${NC}"
  exit 0
fi

if $CHECK_ONLY; then
  echo -e "\n${YELLOW}Missing ${#MISSING[@]} tool(s). Run without --check-only to install.${NC}"
  exit 1
fi

echo -e "\n${BLUE}Installing ${#MISSING[@]} missing tool(s)...${NC}\n"

HAS_BREW=false
command -v brew &>/dev/null && HAS_BREW=true

FAILED=()

for tool in "${MISSING[@]}"; do
  echo -e "${BLUE}Installing $tool...${NC}"
  case "$tool" in
    k6)
      if $HAS_BREW; then
        brew install k6
      else
        # Direct binary (Linux)
        local os arch
        os=$(uname -s | tr '[:upper:]' '[:lower:]')
        arch=$(uname -m)
        [[ "$arch" == "x86_64" ]] && arch="amd64"
        [[ "$arch" == "aarch64" || "$arch" == "arm64" ]] && arch="arm64"
        curl -sSL "https://github.com/grafana/k6/releases/latest/download/k6-v0.48.0-${os}-${arch}.tar.gz" | tar xz
        mv k6-*/k6 /usr/local/bin/
        rm -rf k6-*/
      fi
      ;;
    jmeter)
      if $HAS_BREW; then
        brew install jmeter
      else
        echo -e "${YELLOW}JMeter requires manual install: https://jmeter.apache.org/download_jmeter.cgi${NC}"
        FAILED+=("jmeter")
        continue
      fi
      ;;
    python3)
      echo -e "${RED}Python 3 is required but not installed.${NC}"
      echo "Install via: brew install python3 (macOS) or apt install python3 (Linux)"
      FAILED+=("python3")
      continue
      ;;
  esac

  if command -v "$tool" &>/dev/null; then
    echo -e "${GREEN}✓ $tool installed${NC}"
  else
    echo -e "${RED}✗ $tool installation failed${NC}"
    FAILED+=("$tool")
  fi
done

echo ""
if [[ ${#FAILED[@]} -eq 0 ]]; then
  echo -e "${GREEN}All tools installed successfully.${NC}"
else
  echo -e "${RED}Failed to install: ${FAILED[*]}${NC}"
  exit 1
fi
