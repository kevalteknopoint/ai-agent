#!/usr/bin/env bash
################################################################################
# run_scan.sh — Zero-AI Accessibility Scanning Orchestrator
#
# No LLM tokens. Runs deterministic accessibility tools and produces
# consolidated reports. Like axe + pa11y + Lighthouse in one command.
#
# Supports:
#   - Static code analysis (HTML/JSX/HTL linting for a11y violations)
#   - Runtime analysis (headless browser scanning of live URLs)
#   - Both combined with cross-referencing
#
# Usage:
#   bash run_scan.sh --standard wcag2.1 --level aa --git-url <url> --branch <branch>
#   bash run_scan.sh --standard wcag2.2 --level aa --live-url <url>
#   bash run_scan.sh --mode code --standard wcag2.1 --level aa --path <dir>
#   bash run_scan.sh --mode rescan --path <dir> --baseline <report>
#
# Options:
#   --standard <std>        WCAG standard: wcag2.0|wcag2.1|wcag2.2|section508|en301549
#   --level <lvl>           Conformance level: a|aa|aaa (default: aa)
#   --mode <mode>           Scan mode: full|code|live|rescan (default: full)
#   --git-url <url>         GitHub/GitLab URL to clone
#   --branch <branch>       Branch to checkout
#   --path <dir>            Local directory to scan
#   --live-url <url>        Live website URL for runtime scanning
#   --pages <paths>         Comma-separated page paths to scan (default: /)
#   --viewport <vp>         Viewports: desktop|mobile|both (default: both)
#   --output-dir <dir>      Where to write results
#   --baseline <file>       Previous report for delta comparison (rescan mode)
#   --screenshots           Capture screenshots of violations
#   --max-pages <n>         Max pages to crawl for live scan (default: 20)
#   --timeout <ms>          Page load timeout in ms (default: 30000)
#
# Exit codes:
#   0 — scan completed (may have findings)
#   1 — usage error / missing args
#   2 — tool not installed
#   3 — clone/checkout failed
#   4 — live URL unreachable
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ─── Colors ───
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# ─── Defaults ───
STANDARD="wcag2.1"
LEVEL="aa"
MODE="full"
GIT_URL=""
BRANCH=""
LOCAL_PATH=""
LIVE_URL=""
PAGES="/"
VIEWPORT="both"
OUTPUT_DIR=""
BASELINE=""
SCREENSHOTS=false
MAX_PAGES=20
TIMEOUT=30000
BASE_DIR="${TOOLKIT_ROOT}/repos"

# ─── Parse args ───
while [[ $# -gt 0 ]]; do
  case "$1" in
    --standard)     STANDARD="$2";    shift 2 ;;
    --level)        LEVEL="$2";       shift 2 ;;
    --mode)         MODE="$2";        shift 2 ;;
    --git-url)      GIT_URL="$2";     shift 2 ;;
    --branch)       BRANCH="$2";      shift 2 ;;
    --path)         LOCAL_PATH="$2";  shift 2 ;;
    --live-url)     LIVE_URL="$2";    shift 2 ;;
    --pages)        PAGES="$2";       shift 2 ;;
    --viewport)     VIEWPORT="$2";    shift 2 ;;
    --output-dir)   OUTPUT_DIR="$2";  shift 2 ;;
    --baseline)     BASELINE="$2";    shift 2 ;;
    --base-dir)     BASE_DIR="$2";    shift 2 ;;
    --screenshots)  SCREENSHOTS=true; shift   ;;
    --max-pages)    MAX_PAGES="$2";   shift 2 ;;
    --timeout)      TIMEOUT="$2";     shift 2 ;;
    -h|--help)
      head -45 "$0" | tail -40
      exit 0 ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
  esac
done

# ─── Validate inputs ───
if [[ "$MODE" == "full" || "$MODE" == "code" ]]; then
  if [[ -z "$GIT_URL" && -z "$LOCAL_PATH" ]]; then
    echo -e "${RED}Error: Code scan requires --git-url + --branch OR --path${NC}"
    exit 1
  fi
  if [[ -n "$GIT_URL" && -z "$BRANCH" ]]; then
    echo -e "${RED}Error: --branch is required with --git-url${NC}"
    exit 1
  fi
fi

if [[ "$MODE" == "full" || "$MODE" == "live" ]]; then
  if [[ -z "$LIVE_URL" && "$MODE" == "live" ]]; then
    echo -e "${RED}Error: Live scan requires --live-url${NC}"
    exit 1
  fi
fi

# ─── Map standard to tool flags ───
get_axe_tags() {
  case "${STANDARD}-${LEVEL}" in
    wcag2.0-a)       echo "wcag2a" ;;
    wcag2.0-aa)      echo "wcag2a,wcag2aa" ;;
    wcag2.0-aaa)     echo "wcag2a,wcag2aa,wcag2aaa" ;;
    wcag2.1-a)       echo "wcag2a,wcag21a" ;;
    wcag2.1-aa)      echo "wcag2a,wcag2aa,wcag21a,wcag21aa" ;;
    wcag2.1-aaa)     echo "wcag2a,wcag2aa,wcag2aaa,wcag21a,wcag21aa,wcag21aaa" ;;
    wcag2.2-a)       echo "wcag2a,wcag21a,wcag22aa" ;;
    wcag2.2-aa)      echo "wcag2a,wcag2aa,wcag21a,wcag21aa,wcag22aa" ;;
    wcag2.2-aaa)     echo "wcag2a,wcag2aa,wcag2aaa,wcag21a,wcag21aa,wcag21aaa,wcag22aa" ;;
    section508-*)    echo "wcag2a,wcag2aa,section508" ;;
    en301549-*)      echo "wcag2a,wcag2aa,wcag21a,wcag21aa" ;;
    *)               echo "wcag2a,wcag2aa,wcag21a,wcag21aa" ;;
  esac
}

get_pa11y_standard() {
  case "$STANDARD" in
    wcag2.0)    echo "WCAG2A" ;; # pa11y uses WCAG2A, WCAG2AA, WCAG2AAA
    wcag2.1)    echo "WCAG2AA" ;;
    wcag2.2)    echo "WCAG2AA" ;;
    section508) echo "Section508" ;;
    en301549)   echo "WCAG2AA" ;;
    *)          echo "WCAG2AA" ;;
  esac
}

AXE_TAGS=$(get_axe_tags)
PA11Y_STANDARD=$(get_pa11y_standard)

echo -e "${BOLD}${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          ACCESSIBILITY SCAN — Zero AI Tokens                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  Standard:    ${CYAN}${STANDARD} Level ${LEVEL^^}${NC}"
echo -e "  Mode:        ${CYAN}${MODE}${NC}"
[[ -n "$GIT_URL" ]]  && echo -e "  Repo:        ${CYAN}${GIT_URL} (${BRANCH})${NC}"
[[ -n "$LOCAL_PATH" ]] && echo -e "  Path:        ${CYAN}${LOCAL_PATH}${NC}"
[[ -n "$LIVE_URL" ]] && echo -e "  Live URL:    ${CYAN}${LIVE_URL}${NC}"
echo -e "  Viewport:    ${CYAN}${VIEWPORT}${NC}"
echo ""

# ─── Resolve repo path ───
REPO_PATH=""
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
  else
    if [[ -d "${REPO_PATH}/.git" ]]; then
      cd "$REPO_PATH" && git fetch origin && git checkout "$BRANCH" && git pull origin "$BRANCH"
    else
      mkdir -p "$BASE_DIR"
      git clone "$GIT_URL" "$REPO_PATH"
      cd "$REPO_PATH" && git checkout "$BRANCH"
    fi
    echo -e "${GREEN}✓ Repository ready${NC}"
  fi
elif [[ -n "$LOCAL_PATH" ]]; then
  REPO_PATH="$LOCAL_PATH"
  if [[ ! -d "$REPO_PATH" ]]; then
    echo -e "${RED}Error: Directory not found: $REPO_PATH${NC}"
    exit 1
  fi
fi

# ─── Output directory ───
if [[ -z "$OUTPUT_DIR" ]]; then
  if [[ -n "$REPO_PATH" ]]; then
    OUTPUT_DIR="${REPO_PATH}/accessibility-analysis"
  else
    OUTPUT_DIR="${TOOLKIT_ROOT}/output/accessibility-analysis"
  fi
fi
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/screenshots" 2>/dev/null || true

SCAN_LOG="${OUTPUT_DIR}/scan-${TIMESTAMP}.log"
CODE_FINDINGS="${OUTPUT_DIR}/code-findings.json"
LIVE_FINDINGS="${OUTPUT_DIR}/live-findings.json"
SUMMARY="${OUTPUT_DIR}/summary.json"
REPORT="${OUTPUT_DIR}/report.md"

echo -e "  Output:      ${CYAN}${OUTPUT_DIR}${NC}\n"

# ─── Check required tools ───
echo -e "${BLUE}=== Checking Tools ===${NC}"
TOOLS_OK=true

check_tool() {
  local tool="$1"
  local required="$2"
  if command -v "$tool" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} $tool"
    return 0
  elif npx --no-install "$tool" --version &>/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} $tool (via npx)"
    return 0
  else
    if [[ "$required" == "true" ]]; then
      echo -e "  ${RED}✗${NC} $tool — REQUIRED"
      TOOLS_OK=false
    else
      echo -e "  ${YELLOW}○${NC} $tool — optional, skipping"
    fi
    return 1
  fi
}

if [[ "$MODE" == "full" || "$MODE" == "live" ]]; then
  check_tool "axe" "true" || true
  check_tool "pa11y" "true" || true
  check_tool "lighthouse" "false" || true
fi

if [[ "$MODE" == "full" || "$MODE" == "code" ]]; then
  check_tool "html-validate" "false" || true
  check_tool "eslint" "false" || true
fi

if [[ "$TOOLS_OK" == "false" ]]; then
  echo -e "\n${RED}Required tools missing. Run: bash ${SCRIPT_DIR}/install_tools.sh${NC}"
  exit 2
fi
echo ""

# ═══════════════════════════════════════════════════════════════════
# PHASE 1: Static Code Analysis
# ═══════════════════════════════════════════════════════════════════

run_code_scan() {
  echo -e "${BLUE}=== Phase 1: Static Code Analysis ===${NC}"
  
  local findings_count=0
  local code_results="[]"
  
  cd "$REPO_PATH"
  
  # ─── Detect file types ───
  HTML_FILES=$(find . -name "*.html" -o -name "*.htm" -o -name "*.htl" | head -200)
  JSX_FILES=$(find . -name "*.jsx" -o -name "*.tsx" | head -200)
  VUE_FILES=$(find . -name "*.vue" | head -200)
  CSS_FILES=$(find . -name "*.css" -o -name "*.scss" | head -200)
  
  HTML_COUNT=$(echo "$HTML_FILES" | grep -c "." || echo 0)
  JSX_COUNT=$(echo "$JSX_FILES" | grep -c "." || echo 0)
  VUE_COUNT=$(echo "$VUE_FILES" | grep -c "." || echo 0)
  
  echo -e "  Found: ${HTML_COUNT} HTML/HTL, ${JSX_COUNT} JSX/TSX, ${VUE_COUNT} Vue files"
  
  # ─── html-validate for HTML files ───
  if command -v html-validate &>/dev/null && [[ $HTML_COUNT -gt 0 ]]; then
    echo -e "\n  ${CYAN}Running html-validate...${NC}"
    
    # Create a11y-focused config
    cat > "$OUTPUT_DIR/.htmlvalidate.json" <<'EOF'
{
  "extends": ["html-validate:recommended"],
  "rules": {
    "wcag/h30": "error",
    "wcag/h32": "error",
    "wcag/h36": "error",
    "wcag/h37": "error",
    "wcag/h67": "error",
    "wcag/h71": "error",
    "no-missing-references": "error",
    "input-missing-label": "error",
    "empty-heading": "error",
    "no-autoplay": "error",
    "aria-label-misuse": "error"
  }
}
EOF
    
    echo "$HTML_FILES" | while read -r f; do
      [[ -z "$f" ]] && continue
      html-validate --formatter json "$f" 2>/dev/null >> "$OUTPUT_DIR/html-validate-raw.json" || true
    done
    
    echo -e "  ${GREEN}✓ html-validate complete${NC}"
  fi
  
  # ─── ESLint with jsx-a11y for React ───
  if command -v eslint &>/dev/null && [[ $JSX_COUNT -gt 0 ]]; then
    echo -e "\n  ${CYAN}Running eslint-plugin-jsx-a11y...${NC}"
    
    # Create a11y eslint config
    cat > "$OUTPUT_DIR/.eslintrc.a11y.json" <<'EOF'
{
  "plugins": ["jsx-a11y"],
  "extends": ["plugin:jsx-a11y/recommended"],
  "parserOptions": {
    "ecmaFeatures": { "jsx": true },
    "ecmaVersion": 2021,
    "sourceType": "module"
  },
  "rules": {
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/anchor-has-content": "error",
    "jsx-a11y/anchor-is-valid": "error",
    "jsx-a11y/aria-activedescendant-has-tabindex": "error",
    "jsx-a11y/aria-props": "error",
    "jsx-a11y/aria-proptypes": "error",
    "jsx-a11y/aria-role": "error",
    "jsx-a11y/aria-unsupported-elements": "error",
    "jsx-a11y/click-events-have-key-events": "error",
    "jsx-a11y/heading-has-content": "error",
    "jsx-a11y/html-has-lang": "error",
    "jsx-a11y/iframe-has-title": "error",
    "jsx-a11y/img-redundant-alt": "error",
    "jsx-a11y/interactive-supports-focus": "error",
    "jsx-a11y/label-has-associated-control": "error",
    "jsx-a11y/media-has-caption": "error",
    "jsx-a11y/mouse-events-have-key-events": "error",
    "jsx-a11y/no-access-key": "error",
    "jsx-a11y/no-autofocus": "error",
    "jsx-a11y/no-distracting-elements": "error",
    "jsx-a11y/no-interactive-element-to-noninteractive-role": "error",
    "jsx-a11y/no-noninteractive-element-interactions": "error",
    "jsx-a11y/no-noninteractive-element-to-interactive-role": "error",
    "jsx-a11y/no-noninteractive-tabindex": "error",
    "jsx-a11y/no-redundant-roles": "error",
    "jsx-a11y/no-static-element-interactions": "error",
    "jsx-a11y/role-has-required-aria-props": "error",
    "jsx-a11y/role-supports-aria-props": "error",
    "jsx-a11y/scope": "error",
    "jsx-a11y/tabindex-no-positive": "error"
  }
}
EOF
    
    eslint --config "$OUTPUT_DIR/.eslintrc.a11y.json" \
      --format json \
      --no-eslintrc \
      $(echo "$JSX_FILES" | tr '\n' ' ') \
      > "$OUTPUT_DIR/eslint-a11y-raw.json" 2>/dev/null || true
    
    echo -e "  ${GREEN}✓ eslint jsx-a11y complete${NC}"
  fi
  
  # ─── Manual pattern scanning (zero-dependency) ───
  echo -e "\n  ${CYAN}Running pattern-based a11y checks...${NC}"
  
  PATTERN_FINDINGS="$OUTPUT_DIR/pattern-findings.txt"
  > "$PATTERN_FINDINGS"
  
  # Check for images without alt
  if [[ $HTML_COUNT -gt 0 ]]; then
    echo "## Images without alt attribute" >> "$PATTERN_FINDINGS"
    grep -rn '<img[^>]*>' . --include="*.html" --include="*.htm" --include="*.htl" --include="*.jsx" --include="*.tsx" 2>/dev/null | \
      grep -v 'alt=' >> "$PATTERN_FINDINGS" 2>/dev/null || true
    echo "" >> "$PATTERN_FINDINGS"
  fi
  
  # Check for missing lang attribute
  echo "## HTML without lang attribute" >> "$PATTERN_FINDINGS"
  grep -rn '<html' . --include="*.html" --include="*.htm" 2>/dev/null | \
    grep -v 'lang=' >> "$PATTERN_FINDINGS" 2>/dev/null || true
  echo "" >> "$PATTERN_FINDINGS"
  
  # Check for empty links/buttons
  echo "## Potentially empty links" >> "$PATTERN_FINDINGS"
  grep -rn '<a[^>]*>\s*</a>' . --include="*.html" --include="*.htm" --include="*.jsx" --include="*.tsx" 2>/dev/null >> "$PATTERN_FINDINGS" || true
  echo "" >> "$PATTERN_FINDINGS"
  
  # Check for missing form labels
  echo "## Inputs potentially missing labels" >> "$PATTERN_FINDINGS"
  grep -rn '<input' . --include="*.html" --include="*.htm" --include="*.jsx" --include="*.tsx" 2>/dev/null | \
    grep -v 'aria-label\|aria-labelledby\|id=.*label\|type="hidden"\|type="submit"\|type="button"' >> "$PATTERN_FINDINGS" 2>/dev/null || true
  echo "" >> "$PATTERN_FINDINGS"
  
  # Check for positive tabindex
  echo "## Positive tabindex (anti-pattern)" >> "$PATTERN_FINDINGS"
  grep -rn 'tabindex="[1-9]' . --include="*.html" --include="*.htm" --include="*.jsx" --include="*.tsx" 2>/dev/null >> "$PATTERN_FINDINGS" || true
  echo "" >> "$PATTERN_FINDINGS"
  
  # Check for autoplaying media
  echo "## Autoplay media" >> "$PATTERN_FINDINGS"
  grep -rn 'autoplay' . --include="*.html" --include="*.htm" --include="*.jsx" --include="*.tsx" 2>/dev/null >> "$PATTERN_FINDINGS" || true
  echo "" >> "$PATTERN_FINDINGS"
  
  # Check for missing button type
  echo "## Buttons without type attribute" >> "$PATTERN_FINDINGS"
  grep -rn '<button' . --include="*.html" --include="*.htm" --include="*.jsx" --include="*.tsx" 2>/dev/null | \
    grep -v 'type=' >> "$PATTERN_FINDINGS" 2>/dev/null || true
  echo "" >> "$PATTERN_FINDINGS"
  
  # Check click handlers without keyboard equivalents
  echo "## Click handlers potentially missing keyboard support" >> "$PATTERN_FINDINGS"
  grep -rn 'onclick\|onClick' . --include="*.html" --include="*.htm" --include="*.jsx" --include="*.tsx" --include="*.js" 2>/dev/null | \
    grep -v 'onkeydown\|onKeyDown\|onkeyup\|onKeyUp\|onkeypress\|onKeyPress\|<button\|<a ' >> "$PATTERN_FINDINGS" 2>/dev/null || true
  echo "" >> "$PATTERN_FINDINGS"
  
  # CSS: Check for outline:none/0 without replacement
  echo "## CSS outline removal (potential focus indicator issue)" >> "$PATTERN_FINDINGS"
  grep -rn 'outline:\s*none\|outline:\s*0\|outline:\s*0px' . --include="*.css" --include="*.scss" 2>/dev/null | \
    grep -v ':focus-visible\|focus-within' >> "$PATTERN_FINDINGS" 2>/dev/null || true
  echo "" >> "$PATTERN_FINDINGS"
  
  findings_count=$(grep -c "^[^#]" "$PATTERN_FINDINGS" 2>/dev/null || echo 0)
  echo -e "  ${GREEN}✓ Pattern scan: ${findings_count} potential issues found${NC}"
  
  echo -e "\n${GREEN}=== Code Analysis Complete ===${NC}"
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 2: Live Runtime Analysis
# ═══════════════════════════════════════════════════════════════════

run_live_scan() {
  echo -e "\n${BLUE}=== Phase 2: Live Runtime Analysis ===${NC}"
  echo -e "  Target: ${CYAN}${LIVE_URL}${NC}"
  
  # ─── Verify URL is reachable ───
  echo -e "\n  ${CYAN}Checking URL accessibility...${NC}"
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$LIVE_URL" 2>/dev/null || echo "000")
  
  if [[ "$HTTP_STATUS" == "000" ]]; then
    echo -e "  ${RED}✗ URL unreachable: ${LIVE_URL}${NC}"
    echo -e "  ${YELLOW}Check: VPN required? DNS resolution? Firewall?${NC}"
    exit 4
  elif [[ "$HTTP_STATUS" -ge 400 ]]; then
    echo -e "  ${YELLOW}⚠ URL returned HTTP ${HTTP_STATUS} — scan may have limited results${NC}"
  else
    echo -e "  ${GREEN}✓ URL reachable (HTTP ${HTTP_STATUS})${NC}"
  fi
  
  # ─── Build page list ───
  IFS=',' read -ra PAGE_LIST <<< "$PAGES"
  FULL_URLS=()
  for page in "${PAGE_LIST[@]}"; do
    page=$(echo "$page" | xargs) # trim whitespace
    if [[ "$page" == /* ]]; then
      FULL_URLS+=("${LIVE_URL%/}${page}")
    else
      FULL_URLS+=("${LIVE_URL%/}/${page}")
    fi
  done
  
  echo -e "  Pages to scan: ${#FULL_URLS[@]}"
  for url in "${FULL_URLS[@]}"; do
    echo -e "    - ${url}"
  done
  
  # ─── Viewport configurations ───
  VIEWPORTS=()
  case "$VIEWPORT" in
    desktop) VIEWPORTS=("1280x720") ;;
    mobile)  VIEWPORTS=("375x812") ;;
    both)    VIEWPORTS=("1280x720" "375x812") ;;
  esac
  
  # ─── axe-core scan ───
  if command -v axe &>/dev/null; then
    echo -e "\n  ${CYAN}Running axe-core...${NC}"
    echo -e "  Tags: ${AXE_TAGS}"
    
    AXE_RESULTS="$OUTPUT_DIR/axe-results"
    mkdir -p "$AXE_RESULTS"
    
    for url in "${FULL_URLS[@]}"; do
      page_name=$(echo "$url" | sed 's|.*/||; s|^$|index|')
      
      for vp in "${VIEWPORTS[@]}"; do
        vp_name="${vp//x/_}"
        output_file="${AXE_RESULTS}/${page_name}_${vp_name}.json"
        
        echo -e "    Scanning: ${url} @ ${vp}"
        axe "$url" \
          --tags "$AXE_TAGS" \
          --save "$output_file" \
          --timeout "$TIMEOUT" \
          2>/dev/null || echo -e "    ${YELLOW}⚠ axe scan had issues for ${url}${NC}"
      done
    done
    
    echo -e "  ${GREEN}✓ axe-core complete${NC}"
  fi
  
  # ─── pa11y scan ───
  if command -v pa11y &>/dev/null; then
    echo -e "\n  ${CYAN}Running pa11y...${NC}"
    echo -e "  Standard: ${PA11Y_STANDARD}"
    
    PA11Y_RESULTS="$OUTPUT_DIR/pa11y-results"
    mkdir -p "$PA11Y_RESULTS"
    
    for url in "${FULL_URLS[@]}"; do
      page_name=$(echo "$url" | sed 's|.*/||; s|^$|index|')
      
      for vp in "${VIEWPORTS[@]}"; do
        vp_name="${vp//x/_}"
        width="${vp%%x*}"
        height="${vp##*x}"
        output_file="${PA11Y_RESULTS}/${page_name}_${vp_name}.json"
        
        echo -e "    Scanning: ${url} @ ${vp}"
        pa11y "$url" \
          --standard "$PA11Y_STANDARD" \
          --reporter json \
          --timeout "$TIMEOUT" \
          --viewport.width "$width" \
          --viewport.height "$height" \
          > "$output_file" 2>/dev/null || echo -e "    ${YELLOW}⚠ pa11y had issues for ${url}${NC}"
      done
    done
    
    echo -e "  ${GREEN}✓ pa11y complete${NC}"
  fi
  
  # ─── Lighthouse accessibility audit ───
  if command -v lighthouse &>/dev/null; then
    echo -e "\n  ${CYAN}Running Lighthouse accessibility audit...${NC}"
    
    LH_RESULTS="$OUTPUT_DIR/lighthouse-results"
    mkdir -p "$LH_RESULTS"
    
    for url in "${FULL_URLS[@]}"; do
      page_name=$(echo "$url" | sed 's|.*/||; s|^$|index|')
      output_file="${LH_RESULTS}/${page_name}.json"
      
      echo -e "    Auditing: ${url}"
      lighthouse "$url" \
        --only-categories=accessibility \
        --output=json \
        --output-path="$output_file" \
        --chrome-flags="--headless --no-sandbox --disable-gpu" \
        --quiet \
        2>/dev/null || echo -e "    ${YELLOW}⚠ Lighthouse had issues for ${url}${NC}"
    done
    
    echo -e "  ${GREEN}✓ Lighthouse complete${NC}"
  fi
  
  echo -e "\n${GREEN}=== Live Analysis Complete ===${NC}"
}

# ═══════════════════════════════════════════════════════════════════
# PHASE 3: Aggregate Results
# ═══════════════════════════════════════════════════════════════════

aggregate_results() {
  echo -e "\n${BLUE}=== Aggregating Results ===${NC}"
  
  # Run the Python aggregator if available
  if command -v python3 &>/dev/null && [[ -f "${SCRIPT_DIR}/aggregate_report.py" ]]; then
    python3 "${SCRIPT_DIR}/aggregate_report.py" \
      --output-dir "$OUTPUT_DIR" \
      --standard "$STANDARD" \
      --level "$LEVEL" \
      --timestamp "$TIMESTAMP"
    echo -e "  ${GREEN}✓ Aggregation complete${NC}"
  else
    # Fallback: simple summary
    echo -e "  ${YELLOW}Python3 or aggregator not available — generating basic summary${NC}"
    
    cat > "$REPORT" <<EOF
# Accessibility Scan Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Standard:** ${STANDARD} Level ${LEVEL^^}
**Mode:** ${MODE}

## Scan Targets
$([ -n "$REPO_PATH" ] && echo "- **Code:** ${REPO_PATH}")
$([ -n "$LIVE_URL" ] && echo "- **Live URL:** ${LIVE_URL}")

## Results Location

All raw findings are in: \`${OUTPUT_DIR}/\`

### Files Generated
$(ls -1 "$OUTPUT_DIR"/*.json 2>/dev/null | sed 's/^/- /' || echo "- No JSON results")
$(ls -1 "$OUTPUT_DIR"/*.txt 2>/dev/null | sed 's/^/- /' || echo "")

## Next Steps

1. Review findings in the output directory
2. Use the accessibility-code-fixer agent to remediate issues
3. Re-scan after fixes to verify resolution

---
*Generated by bmad-accessibility-scan (zero-AI scanning)*
EOF
    echo -e "  ${GREEN}✓ Basic report generated${NC}"
  fi
}

# ═══════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════

case "$MODE" in
  full)
    [[ -n "$REPO_PATH" ]] && run_code_scan
    [[ -n "$LIVE_URL" ]] && run_live_scan
    aggregate_results
    ;;
  code)
    run_code_scan
    aggregate_results
    ;;
  live)
    run_live_scan
    aggregate_results
    ;;
  rescan)
    echo -e "${BLUE}=== Rescan Mode (delta comparison) ===${NC}"
    if [[ -z "$BASELINE" ]]; then
      echo -e "${YELLOW}No baseline provided — running fresh scan${NC}"
    fi
    [[ -n "$REPO_PATH" ]] && run_code_scan
    [[ -n "$LIVE_URL" ]] && run_live_scan
    aggregate_results
    # TODO: compute delta against baseline
    ;;
esac

# ─── Final Summary ───
echo -e "\n${BOLD}${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    SCAN COMPLETE                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  Report:     ${CYAN}${REPORT}${NC}"
echo -e "  Output dir: ${CYAN}${OUTPUT_DIR}${NC}"
echo -e "  Standard:   ${CYAN}${STANDARD} ${LEVEL^^}${NC}"
echo ""
echo -e "  ${YELLOW}Tip: Automated tools catch ~30-50% of accessibility issues.${NC}"
echo -e "  ${YELLOW}Manual testing with screen readers is still recommended.${NC}"
echo ""
