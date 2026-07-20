#!/usr/bin/env bash
################################################################################
# install_tools.sh — Install security scanning tools (idempotent)
#
# Zero AI. Installs open-source security tools via Homebrew (macOS) or direct
# binary download. Safe to re-run — skips tools already installed.
#
# Tools installed:
#   semgrep      — SAST (pattern-based static analysis, OWASP rules)
#   gitleaks     — Secrets detection (pattern + entropy)
#   trivy        — Dependency vulnerability scanner + IaC audit
#   hadolint     — Dockerfile linter
#   checkov      — IaC scanner (Terraform, K8s, CloudFormation, Helm)
#   nuclei       — DAST (template-based active probing)
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

TOOLS=(semgrep gitleaks trivy hadolint checkov nuclei)
MISSING=()
PRESENT=()

for tool in "${TOOLS[@]}"; do
  if command -v "$tool" &>/dev/null; then
    ver=$("$tool" --version 2>/dev/null | head -1 || echo "unknown")
    PRESENT+=("$tool ($ver)")
  else
    MISSING+=("$tool")
  fi
done

echo -e "${BLUE}=== Security Tools Status ===${NC}"
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

# Detect package manager
HAS_BREW=false
HAS_PIP=false
command -v brew &>/dev/null && HAS_BREW=true
command -v pip3 &>/dev/null && HAS_PIP=true

install_tool() {
  local tool="$1"
  echo -e "${BLUE}Installing $tool...${NC}"
  case "$tool" in
    semgrep)
      if $HAS_PIP; then
        pip3 install semgrep
      elif $HAS_BREW; then
        brew install semgrep
      else
        echo -e "${RED}Need pip3 or brew to install semgrep${NC}" && return 1
      fi
      ;;
    gitleaks)
      if $HAS_BREW; then
        brew install gitleaks
      else
        # Direct binary download (Linux/macOS)
        local os arch url
        os=$(uname -s | tr '[:upper:]' '[:lower:]')
        arch=$(uname -m)
        [[ "$arch" == "x86_64" ]] && arch="x64"
        [[ "$arch" == "aarch64" || "$arch" == "arm64" ]] && arch="arm64"
        url="https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_${os}_${arch}.tar.gz"
        curl -sSL "$url" | tar xz -C /usr/local/bin gitleaks
      fi
      ;;
    trivy)
      if $HAS_BREW; then
        brew install trivy
      else
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
      fi
      ;;
    hadolint)
      if $HAS_BREW; then
        brew install hadolint
      else
        local os arch
        os=$(uname -s)
        arch=$(uname -m)
        curl -sSL "https://github.com/hadolint/hadolint/releases/latest/download/hadolint-${os}-${arch}" -o /usr/local/bin/hadolint
        chmod +x /usr/local/bin/hadolint
      fi
      ;;
    checkov)
      if $HAS_PIP; then
        pip3 install checkov
      elif $HAS_BREW; then
        brew install checkov
      else
        echo -e "${RED}Need pip3 or brew to install checkov${NC}" && return 1
      fi
      ;;
    nuclei)
      if $HAS_BREW; then
        brew install nuclei
      else
        curl -sSL https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_$(uname -s)_$(uname -m).zip -o /tmp/nuclei.zip
        unzip -o /tmp/nuclei.zip -d /usr/local/bin nuclei
        rm /tmp/nuclei.zip
      fi
      ;;
  esac

  if command -v "$tool" &>/dev/null; then
    echo -e "${GREEN}✓ $tool installed${NC}"
  else
    echo -e "${RED}✗ $tool installation failed${NC}"
    return 1
  fi
}

FAILED=()
for tool in "${MISSING[@]}"; do
  install_tool "$tool" || FAILED+=("$tool")
done

echo ""
if [[ ${#FAILED[@]} -eq 0 ]]; then
  echo -e "${GREEN}All tools installed successfully.${NC}"
else
  echo -e "${RED}Failed to install: ${FAILED[*]}${NC}"
  echo "Install these manually and re-run with --check-only to verify."
  exit 1
fi
