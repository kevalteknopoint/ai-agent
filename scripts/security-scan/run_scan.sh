#!/usr/bin/env bash
################################################################################
# run_scan.sh — Zero-AI Security Scanning Orchestrator
#
# No LLM tokens. No Claude. Pure CLI tools. Like ZAP + SonarQube + Trivy
# in one shell script.
#
# Clones a repo (or scans a local path), detects what's in it, runs every
# applicable security tool, and aggregates results into a unified report.
#
# Usage:
#   bash run_scan.sh --git-url <url> --branch <branch> [options]
#   bash run_scan.sh --path <local-dir> [options]
#
# Options:
#   --git-url <url>         GitHub/GitLab URL to clone
#   --branch <branch>       Branch to checkout
#   --path <dir>            Local directory to scan (instead of git clone)
#   --target-url <url>      Live URL for DAST probing (optional)
#   --output-dir <dir>      Where to write results (default: <repo>/security-analysis)
#   --quick                 Run only fast scans (skip DAST, skip deep trivy)
#   --skip-sast             Skip semgrep SAST scan
#   --skip-secrets          Skip gitleaks secrets scan
#   --skip-deps             Skip trivy dependency scan
#   --skip-config           Skip hadolint/checkov config audit
#   --skip-dast             Skip nuclei DAST scan
#   --severity <level>      Minimum severity to report: critical|high|medium|low|info
#   --format <fmt>          Output format: full|json-only|csv-only (default: full)
#
# Exit codes:
#   0 — scan completed (may have findings)
#   1 — usage error / missing args
#   2 — tool not installed (run install_tools.sh first)
#   3 — clone/checkout failed
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ─── Colors ───
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# ─── Defaults ───
GIT_URL="" ; BRANCH="" ; LOCAL_PATH="" ; TARGET_URL=""
OUTPUT_DIR="" ; QUICK=false ; MIN_SEVERITY="info" ; FORMAT="full"
SKIP_SAST=false ; SKIP_SECRETS=false ; SKIP_DEPS=false
SKIP_CONFIG=false ; SKIP_DAST=false
BASE_DIR="${TOOLKIT_ROOT}/repos"

# ─── Parse args ───
while [[ $# -gt 0 ]]; do
  case "$1" in
    --git-url)    GIT_URL="$2";     shift 2 ;;
    --branch)     BRANCH="$2";      shift 2 ;;
    --path)       LOCAL_PATH="$2";  shift 2 ;;
    --target-url) TARGET_URL="$2";  shift 2 ;;
    --output-dir) OUTPUT_DIR="$2";  shift 2 ;;
    --base-dir)   BASE_DIR="$2";    shift 2 ;;
    --quick)      QUICK=true;       shift   ;;
    --skip-sast)    SKIP_SAST=true;    shift ;;
    --skip-secrets) SKIP_SECRETS=true; shift ;;
    --skip-deps)    SKIP_DEPS=true;    shift ;;
    --skip-config)  SKIP_CONFIG=true;  shift ;;
    --skip-dast)    SKIP_DAST=true;    shift ;;
    --severity)   MIN_SEVERITY="$2"; shift 2 ;;
    --format)     FORMAT="$2";       shift 2 ;;
    -h|--help)
      head -35 "$0" | tail -30
      exit 0 ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
  esac
done

# ─── Validate inputs ───
if [[ -z "$GIT_URL" && -z "$LOCAL_PATH" ]]; then
  echo -e "${RED}Error: Provide --git-url <url> --branch <branch> OR --path <local-dir>${NC}"
  exit 1
fi
if [[ -n "$GIT_URL" && -z "$BRANCH" ]]; then
  echo -e "${RED}Error: --branch is required with --git-url${NC}"
  exit 1
fi

# ─── Quick mode: skip heavy scans ───
if $QUICK; then
  SKIP_DAST=true
  echo -e "${YELLOW}Quick mode: DAST disabled, shallow scans only${NC}"
fi

# ─── Resolve repo path ───
REPO_PATH=""
REPO_NAME=""
if [[ -n "$GIT_URL" ]]; then
  REPO_NAME=$(basename "$GIT_URL" .git)
  REPO_PATH="${BASE_DIR}/${REPO_NAME}"

  echo -e "${BLUE}=== Repository Setup ===${NC}"
  if [[ -f "${TOOLKIT_ROOT}/scripts/clone_or_update.sh" ]]; then
    CLONE_RESULT=$(bash "${TOOLKIT_ROOT}/scripts/clone_or_update.sh" "$GIT_URL" "$BRANCH" "$BASE_DIR" 2>&1) || {
      echo -e "${RED}Clone/update failed:${NC}"
      echo "$CLONE_RESULT"
      exit 3
    }
    echo -e "${GREEN}✓ Repository ready: ${REPO_PATH}${NC}"
    echo -e "  Branch: ${BRANCH}"
  else
    # Fallback: manual clone
    if [[ -d "${REPO_PATH}/.git" ]]; then
      echo "Updating existing clone..."
      cd "$REPO_PATH"
      git fetch origin
      git checkout "$BRANCH"
      git pull origin "$BRANCH"
    else
      echo "Cloning fresh..."
      mkdir -p "$BASE_DIR"
      git clone "$GIT_URL" "$REPO_PATH"
      cd "$REPO_PATH"
      git checkout "$BRANCH"
    fi
    echo -e "${GREEN}✓ Repository ready${NC}"
  fi
else
  REPO_PATH="$LOCAL_PATH"
  REPO_NAME=$(basename "$REPO_PATH")
  if [[ ! -d "$REPO_PATH" ]]; then
    echo -e "${RED}Error: Directory not found: $REPO_PATH${NC}"
    exit 1
  fi
  echo -e "${BLUE}Scanning local path: ${REPO_PATH}${NC}"
fi

# ─── Output directory ───
[[ -z "$OUTPUT_DIR" ]] && OUTPUT_DIR="${REPO_PATH}/security-analysis"
mkdir -p "$OUTPUT_DIR"
SCAN_LOG="${OUTPUT_DIR}/scan-${TIMESTAMP}.log"
echo -e "Output: ${OUTPUT_DIR}\n"

# ─── Check required tools ───
check_tool() {
  if ! command -v "$1" &>/dev/null; then
    echo -e "${RED}✗ $1 not installed. Run: bash ${SCRIPT_DIR}/install_tools.sh${NC}"
    return 1
  fi
  return 0
}

TOOLS_OK=true
$SKIP_SAST    || check_tool semgrep  || TOOLS_OK=false
$SKIP_SECRETS || check_tool gitleaks || TOOLS_OK=false
$SKIP_DEPS    || check_tool trivy    || TOOLS_OK=false
$SKIP_CONFIG  || { check_tool hadolint 2>/dev/null || true; check_tool checkov 2>/dev/null || true; }
$SKIP_DAST    || check_tool nuclei   || { echo -e "${YELLOW}⚠ nuclei not installed — DAST will be skipped${NC}"; SKIP_DAST=true; }

if ! $TOOLS_OK; then
  echo -e "\n${RED}Missing required tools. Install first:${NC}"
  echo "  bash ${SCRIPT_DIR}/install_tools.sh"
  exit 2
fi

# ─── Surface detection (zero-token) ───
echo -e "${BLUE}=== Detecting Security Surface ===${NC}"

HAS_JAVA=false; HAS_NODE=false; HAS_PYTHON=false; HAS_GO=false; HAS_RUBY=false
HAS_DOCKER=false; HAS_K8S=false; HAS_TERRAFORM=false; HAS_CF=false
HAS_DOTENV=false; HAS_CICD=false; HAS_OPENAPI=false

cd "$REPO_PATH"

# Language / framework detection
[[ -n "$(find . -name '*.java' -not -path '*/node_modules/*' -not -path '*/target/*' 2>/dev/null | head -1)" ]] && HAS_JAVA=true
[[ -f "package.json" || -f "package-lock.json" || -f "yarn.lock" || -f "pnpm-lock.yaml" ]] && HAS_NODE=true
[[ -f "requirements.txt" || -f "Pipfile" || -f "pyproject.toml" || -f "setup.py" ]] && HAS_PYTHON=true
[[ -f "go.mod" || -f "go.sum" ]] && HAS_GO=true
[[ -f "Gemfile" || -f "Gemfile.lock" ]] && HAS_RUBY=true

# Infrastructure detection
[[ -n "$(find . -maxdepth 3 -name 'Dockerfile*' 2>/dev/null | head -1)" ]] && HAS_DOCKER=true
[[ -n "$(find . -maxdepth 3 \( -name '*.yaml' -o -name '*.yml' \) -exec grep -l 'kind:\s*\(Deployment\|Service\|Pod\|StatefulSet\)' {} + 2>/dev/null | head -1)" ]] && HAS_K8S=true
[[ -n "$(find . -maxdepth 3 -name '*.tf' 2>/dev/null | head -1)" ]] && HAS_TERRAFORM=true
[[ -n "$(find . -maxdepth 3 -name '*.template' -exec grep -l 'AWSTemplateFormatVersion' {} + 2>/dev/null | head -1)" ]] && HAS_CF=true

# Secrets surface
[[ -n "$(find . -maxdepth 3 -name '.env*' -not -name '.env.example' -not -name '.env.sample' 2>/dev/null | head -1)" ]] && HAS_DOTENV=true

# CI/CD detection
[[ -d ".github/workflows" || -f ".gitlab-ci.yml" || -f "Jenkinsfile" || -f "azure-pipelines.yml" || -d ".circleci" ]] && HAS_CICD=true

# OpenAPI / Swagger
[[ -n "$(find . -maxdepth 3 \( -name 'openapi*' -o -name 'swagger*' \) \( -name '*.json' -o -name '*.yaml' -o -name '*.yml' \) 2>/dev/null | head -1)" ]] && HAS_OPENAPI=true

echo "  Languages:"
$HAS_JAVA   && echo -e "    ${GREEN}✓${NC} Java"
$HAS_NODE   && echo -e "    ${GREEN}✓${NC} Node.js"
$HAS_PYTHON && echo -e "    ${GREEN}✓${NC} Python"
$HAS_GO     && echo -e "    ${GREEN}✓${NC} Go"
$HAS_RUBY   && echo -e "    ${GREEN}✓${NC} Ruby"
echo "  Infrastructure:"
$HAS_DOCKER    && echo -e "    ${GREEN}✓${NC} Dockerfiles"
$HAS_K8S       && echo -e "    ${GREEN}✓${NC} Kubernetes manifests"
$HAS_TERRAFORM && echo -e "    ${GREEN}✓${NC} Terraform"
$HAS_CF        && echo -e "    ${GREEN}✓${NC} CloudFormation"
echo "  Other:"
$HAS_DOTENV  && echo -e "    ${YELLOW}!${NC} .env files found"
$HAS_CICD    && echo -e "    ${GREEN}✓${NC} CI/CD configs"
$HAS_OPENAPI && echo -e "    ${GREEN}✓${NC} OpenAPI/Swagger specs"
echo ""

# ─── Track results ───
SCAN_RESULTS=()
TOTAL_FINDINGS=0
SCAN_START=$(date +%s)

# ─── 1. SAST — semgrep ───
if ! $SKIP_SAST; then
  echo -e "${BLUE}[1/5] SAST — semgrep${NC}"
  SAST_OUT="${OUTPUT_DIR}/sast-findings-raw.json"

  SEMGREP_CONFIGS="--config auto"
  # Add OWASP-specific rules if available
  SEMGREP_CONFIGS="$SEMGREP_CONFIGS --config p/owasp-top-ten 2>/dev/null || true"

  # Build exclude list
  SEMGREP_EXCLUDES="--exclude node_modules --exclude target --exclude build --exclude dist --exclude .git --exclude vendor --exclude __pycache__"

  if semgrep scan --json --config auto \
    --exclude node_modules --exclude target --exclude build \
    --exclude dist --exclude .git --exclude vendor --exclude __pycache__ \
    --exclude '*.min.js' --exclude '*.min.css' \
    --severity INFO \
    --max-target-bytes 1000000 \
    "$REPO_PATH" > "$SAST_OUT" 2>>"$SCAN_LOG"; then
    SAST_COUNT=$(python3 -c "
import json, sys
try:
    data = json.load(open('$SAST_OUT'))
    results = data.get('results', [])
    print(len(results))
except:
    print(0)
" 2>/dev/null || echo "0")
    TOTAL_FINDINGS=$((TOTAL_FINDINGS + SAST_COUNT))
    SCAN_RESULTS+=("SAST:${SAST_COUNT}")
    echo -e "  ${GREEN}✓${NC} semgrep found ${BOLD}${SAST_COUNT}${NC} finding(s)"
  else
    echo -e "  ${YELLOW}⚠${NC} semgrep scan completed with warnings (check ${SCAN_LOG})"
    # semgrep returns non-zero when findings exist — results file is still valid
    if [[ -f "$SAST_OUT" ]]; then
      SAST_COUNT=$(python3 -c "
import json, sys
try:
    data = json.load(open('$SAST_OUT'))
    results = data.get('results', [])
    print(len(results))
except:
    print(0)
" 2>/dev/null || echo "0")
      TOTAL_FINDINGS=$((TOTAL_FINDINGS + SAST_COUNT))
      SCAN_RESULTS+=("SAST:${SAST_COUNT}")
      echo -e "  ${GREEN}✓${NC} semgrep found ${BOLD}${SAST_COUNT}${NC} finding(s)"
    fi
  fi
else
  echo -e "${YELLOW}[1/5] SAST — skipped${NC}"
fi

# ─── 2. Secrets — gitleaks ───
if ! $SKIP_SECRETS; then
  echo -e "${BLUE}[2/5] Secrets — gitleaks${NC}"
  SECRETS_OUT="${OUTPUT_DIR}/secrets-findings-raw.json"

  # gitleaks returns exit code 1 when secrets found — that's expected
  if gitleaks detect --source "$REPO_PATH" --report-format json \
    --report-path "$SECRETS_OUT" --no-banner 2>>"$SCAN_LOG"; then
    echo -e "  ${GREEN}✓${NC} No secrets detected"
    SCAN_RESULTS+=("Secrets:0")
  else
    if [[ -f "$SECRETS_OUT" ]]; then
      SECRETS_COUNT=$(python3 -c "
import json
data = json.load(open('$SECRETS_OUT'))
print(len(data) if isinstance(data, list) else 0)
" 2>/dev/null || echo "0")
      TOTAL_FINDINGS=$((TOTAL_FINDINGS + SECRETS_COUNT))
      SCAN_RESULTS+=("Secrets:${SECRETS_COUNT}")
      echo -e "  ${RED}!${NC} gitleaks found ${BOLD}${SECRETS_COUNT}${NC} secret(s)"
    else
      echo -e "  ${YELLOW}⚠${NC} gitleaks failed (check ${SCAN_LOG})"
      SCAN_RESULTS+=("Secrets:error")
    fi
  fi
else
  echo -e "${YELLOW}[2/5] Secrets — skipped${NC}"
fi

# ─── 3. Dependency Vulnerabilities — trivy ───
if ! $SKIP_DEPS; then
  echo -e "${BLUE}[3/5] Dependencies — trivy${NC}"
  DEPS_OUT="${OUTPUT_DIR}/dependency-findings-raw.json"

  TRIVY_ARGS="fs --format json --output $DEPS_OUT"
  $QUICK && TRIVY_ARGS="$TRIVY_ARGS --severity CRITICAL,HIGH"

  if trivy fs --format json --output "$DEPS_OUT" \
    --scanners vuln \
    "$REPO_PATH" 2>>"$SCAN_LOG"; then
    DEPS_COUNT=$(python3 -c "
import json
data = json.load(open('$DEPS_OUT'))
total = 0
for result in data.get('Results', []):
    for vuln in result.get('Vulnerabilities', []):
        total += 1
print(total)
" 2>/dev/null || echo "0")
    TOTAL_FINDINGS=$((TOTAL_FINDINGS + DEPS_COUNT))
    SCAN_RESULTS+=("Dependencies:${DEPS_COUNT}")
    echo -e "  ${GREEN}✓${NC} trivy found ${BOLD}${DEPS_COUNT}${NC} vulnerability(ies)"
  else
    echo -e "  ${YELLOW}⚠${NC} trivy scan failed (check ${SCAN_LOG})"
    SCAN_RESULTS+=("Dependencies:error")
  fi
else
  echo -e "${YELLOW}[3/5] Dependencies — skipped${NC}"
fi

# ─── 4. Config Audit — hadolint + checkov ───
if ! $SKIP_CONFIG; then
  echo -e "${BLUE}[4/5] Config Audit — hadolint + checkov${NC}"
  CONFIG_COUNT=0
  CONFIG_OUT="${OUTPUT_DIR}/config-findings-raw.json"
  echo '{"hadolint":[],"checkov":[]}' > "$CONFIG_OUT"

  # 4a. Hadolint — Dockerfiles
  if $HAS_DOCKER && command -v hadolint &>/dev/null; then
    DOCKERFILES=$(find "$REPO_PATH" -maxdepth 3 -name 'Dockerfile*' 2>/dev/null)
    HADOLINT_OUT="${OUTPUT_DIR}/hadolint-raw.json"
    HADOLINT_RESULTS="[]"
    while IFS= read -r df; do
      [[ -z "$df" ]] && continue
      if RESULT=$(hadolint --format json "$df" 2>>"$SCAN_LOG"); then
        true  # clean Dockerfile
      fi
      # hadolint outputs JSON array even on non-zero exit
      SINGLE=$(echo "$RESULT" | python3 -c "
import json, sys
try:
    items = json.load(sys.stdin)
    for item in items:
        item['file'] = '$df'
    json.dump(items, sys.stdout)
except:
    print('[]')
" 2>/dev/null || echo "[]")
      HADOLINT_RESULTS=$(python3 -c "
import json
a = json.loads('$HADOLINT_RESULTS')
b = json.loads('''$SINGLE''')
json.dump(a + b, __import__('sys').stdout)
" 2>/dev/null || echo "$HADOLINT_RESULTS")
    done <<< "$DOCKERFILES"

    H_COUNT=$(python3 -c "import json; print(len(json.loads('$HADOLINT_RESULTS')))" 2>/dev/null || echo "0")
    CONFIG_COUNT=$((CONFIG_COUNT + H_COUNT))
    echo -e "  hadolint: ${BOLD}${H_COUNT}${NC} finding(s)"
  fi

  # 4b. Checkov — IaC
  if command -v checkov &>/dev/null; then
    HAS_IAC=false
    $HAS_K8S && HAS_IAC=true
    $HAS_TERRAFORM && HAS_IAC=true
    $HAS_CF && HAS_IAC=true
    $HAS_DOCKER && HAS_IAC=true

    if $HAS_IAC; then
      CHECKOV_OUT="${OUTPUT_DIR}/checkov-raw.json"
      if checkov --directory "$REPO_PATH" --output json --quiet \
        --skip-path node_modules --skip-path target --skip-path build \
        --skip-path dist --skip-path .git \
        > "$CHECKOV_OUT" 2>>"$SCAN_LOG"; then
        true
      fi
      if [[ -f "$CHECKOV_OUT" ]]; then
        C_COUNT=$(python3 -c "
import json
data = json.load(open('$CHECKOV_OUT'))
total = 0
if isinstance(data, list):
    for check in data:
        total += len(check.get('results', {}).get('failed_checks', []))
elif isinstance(data, dict):
    total = len(data.get('results', {}).get('failed_checks', []))
print(total)
" 2>/dev/null || echo "0")
        CONFIG_COUNT=$((CONFIG_COUNT + C_COUNT))
        echo -e "  checkov: ${BOLD}${C_COUNT}${NC} finding(s)"
      fi
    else
      echo -e "  checkov: no IaC files detected, skipping"
    fi
  fi

  TOTAL_FINDINGS=$((TOTAL_FINDINGS + CONFIG_COUNT))
  SCAN_RESULTS+=("Config:${CONFIG_COUNT}")
  echo -e "  ${GREEN}✓${NC} Config audit: ${BOLD}${CONFIG_COUNT}${NC} total finding(s)"
else
  echo -e "${YELLOW}[4/5] Config Audit — skipped${NC}"
fi

# ─── 5. DAST — nuclei ───
if ! $SKIP_DAST && [[ -n "$TARGET_URL" ]]; then
  echo -e "${BLUE}[5/5] DAST — nuclei${NC}"
  DAST_OUT="${OUTPUT_DIR}/dast-findings-raw.jsonl"

  NUCLEI_TEMPLATES="-automatic-scan"
  $QUICK && NUCLEI_TEMPLATES="-t http/misconfiguration/ -t http/exposures/"

  if nuclei -u "$TARGET_URL" -jsonl -output "$DAST_OUT" \
    -severity info,low,medium,high,critical \
    -silent -automatic-scan \
    2>>"$SCAN_LOG"; then
    if [[ -f "$DAST_OUT" ]]; then
      DAST_COUNT=$(wc -l < "$DAST_OUT" | tr -d ' ')
      TOTAL_FINDINGS=$((TOTAL_FINDINGS + DAST_COUNT))
      SCAN_RESULTS+=("DAST:${DAST_COUNT}")
      echo -e "  ${GREEN}✓${NC} nuclei found ${BOLD}${DAST_COUNT}${NC} finding(s)"
    else
      SCAN_RESULTS+=("DAST:0")
      echo -e "  ${GREEN}✓${NC} No DAST findings"
    fi
  else
    echo -e "  ${YELLOW}⚠${NC} nuclei scan failed (check ${SCAN_LOG})"
    SCAN_RESULTS+=("DAST:error")
  fi
elif ! $SKIP_DAST && [[ -z "$TARGET_URL" ]]; then
  echo -e "${YELLOW}[5/5] DAST — skipped (no --target-url provided)${NC}"
else
  echo -e "${YELLOW}[5/5] DAST — skipped${NC}"
fi

# ─── Aggregate results ───
echo -e "\n${BLUE}=== Aggregating Results ===${NC}"
SCAN_END=$(date +%s)
DURATION=$((SCAN_END - SCAN_START))

if python3 "${SCRIPT_DIR}/aggregate_report.py" \
  --output-dir "$OUTPUT_DIR" \
  --repo-name "$REPO_NAME" \
  --repo-path "$REPO_PATH" \
  --branch "${BRANCH:-local}" \
  --timestamp "$TIMESTAMP" \
  --duration "$DURATION" \
  --min-severity "$MIN_SEVERITY" \
  2>>"$SCAN_LOG"; then
  echo -e "${GREEN}✓ Reports generated${NC}"
else
  echo -e "${RED}✗ Report aggregation failed (raw findings still in ${OUTPUT_DIR})${NC}"
fi

# ─── Summary ───
echo -e "\n${BOLD}${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BOLD}  Security Scan Complete${NC}"
echo -e "${BOLD}${BLUE}══════════════════════════════════════════${NC}"
echo -e "  Repository: ${REPO_NAME} (${BRANCH:-local})"
echo -e "  Duration:   ${DURATION}s"
echo -e "  Total:      ${BOLD}${TOTAL_FINDINGS}${NC} finding(s)"
echo ""
for result in "${SCAN_RESULTS[@]}"; do
  IFS=':' read -r domain count <<< "$result"
  if [[ "$count" == "error" ]]; then
    echo -e "    ${RED}✗${NC} ${domain}: error"
  elif [[ "$count" -gt 0 ]]; then
    echo -e "    ${YELLOW}!${NC} ${domain}: ${count}"
  else
    echo -e "    ${GREEN}✓${NC} ${domain}: 0"
  fi
done
echo ""
echo -e "  Reports: ${OUTPUT_DIR}/"
echo -e "    security-report.md"
echo -e "    security-findings.json"
echo -e "    security-issues.csv"
echo -e "    owasp-mapping.md"
echo -e "${BOLD}${BLUE}══════════════════════════════════════════${NC}"
