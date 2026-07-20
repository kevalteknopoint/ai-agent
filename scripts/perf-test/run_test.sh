#!/usr/bin/env bash
################################################################################
# run_test.sh — Zero-AI Performance Testing Orchestrator
#
# No LLM tokens. No Claude. Pure k6 CLI. Like JMeter from one command.
#
# Generates a k6 test script from parameters, runs it, parses results,
# and generates a human-readable report with SLA pass/fail.
#
# Usage:
#   bash run_test.sh --url <target-url> [options]
#
# Options:
#   --url <url>              Target URL to test (required)
#   --type <type>            Test type: load|stress|soak|spike (default: load)
#   --vus <n>                Virtual users / concurrent connections (default: 10)
#   --duration <dur>         Test duration: e.g., 1m, 5m, 1h (default: 1m)
#   --endpoints <file>       JSON file with endpoint definitions
#   --endpoint <spec>        Inline endpoint: "METHOD /path Name" (repeatable)
#   --header <h>             Default header: "Key: Value" (repeatable)
#   --config <file>          Full JSON config (overrides other params)
#   --output-dir <dir>       Where to write results (default: ./perf-results/<timestamp>)
#   --threshold-p95 <ms>     p95 response time SLA in ms (default: 500)
#   --threshold-p99 <ms>     p99 response time SLA in ms (default: 1000)
#   --threshold-error <pct>  Max error rate % (default: 1)
#   --baseline <file>        Previous k6 summary JSON for comparison
#   --ramp-up <dur>          Ramp-up duration (default: auto)
#   --think-time <sec>       Think time between requests in sec (default: 1)
#   --k6-args <args>         Additional k6 CLI args (passed through)
#   --dry-run                Generate script only, don't execute
#
# Exit codes:
#   0 — test completed, all SLAs passed
#   1 — usage error / missing args
#   2 — k6 not installed
#   3 — target not reachable
#   4 — test completed but SLAs failed
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ─── Colors ───
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# ─── Defaults ───
TARGET_URL=""; TEST_TYPE="load"; VUS=10; DURATION="1m"
ENDPOINTS_FILE=""; CONFIG_FILE=""; OUTPUT_DIR=""
THRESHOLD_P95=500; THRESHOLD_P99=1000; THRESHOLD_ERROR=1
BASELINE=""; RAMP_UP=""; THINK_TIME=1; K6_EXTRA_ARGS=""
DRY_RUN=false
INLINE_ENDPOINTS=()
INLINE_HEADERS=()

# ─── Parse args ───
while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)             TARGET_URL="$2";       shift 2 ;;
    --type)            TEST_TYPE="$2";        shift 2 ;;
    --vus)             VUS="$2";              shift 2 ;;
    --duration)        DURATION="$2";         shift 2 ;;
    --endpoints)       ENDPOINTS_FILE="$2";   shift 2 ;;
    --endpoint)        INLINE_ENDPOINTS+=("$2"); shift 2 ;;
    --header)          INLINE_HEADERS+=("$2"); shift 2 ;;
    --config)          CONFIG_FILE="$2";      shift 2 ;;
    --output-dir)      OUTPUT_DIR="$2";       shift 2 ;;
    --threshold-p95)   THRESHOLD_P95="$2";    shift 2 ;;
    --threshold-p99)   THRESHOLD_P99="$2";    shift 2 ;;
    --threshold-error) THRESHOLD_ERROR="$2";  shift 2 ;;
    --baseline)        BASELINE="$2";         shift 2 ;;
    --ramp-up)         RAMP_UP="$2";          shift 2 ;;
    --think-time)      THINK_TIME="$2";       shift 2 ;;
    --k6-args)         K6_EXTRA_ARGS="$2";    shift 2 ;;
    --dry-run)         DRY_RUN=true;          shift ;;
    -h|--help)
      head -38 "$0" | tail -34
      exit 0 ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
  esac
done

# ─── Validate ───
if [[ -z "$TARGET_URL" && -z "$CONFIG_FILE" ]]; then
  echo -e "${RED}Error: --url <target-url> is required (or --config <file>)${NC}"
  exit 1
fi

# ─── Check k6 ───
if ! command -v k6 &>/dev/null; then
  echo -e "${RED}Error: k6 is not installed.${NC}"
  echo "Install with: bash ${SCRIPT_DIR}/install_tools.sh"
  exit 2
fi
K6_VER=$(k6 version 2>/dev/null | head -1)
echo -e "${BLUE}k6 version: ${K6_VER}${NC}"

# ─── Check target reachability ───
if [[ -n "$TARGET_URL" ]]; then
  echo -e "${BLUE}Checking target: ${TARGET_URL}${NC}"
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$TARGET_URL" 2>/dev/null || echo "000")
  if [[ "$HTTP_CODE" == "000" ]]; then
    echo -e "${RED}Error: Target ${TARGET_URL} is not reachable${NC}"
    exit 3
  fi
  echo -e "${GREEN}✓ Target reachable (HTTP ${HTTP_CODE})${NC}"
fi

# ─── Output directory ───
DOMAIN=$(echo "$TARGET_URL" | sed 's|https\?://||' | sed 's|/.*||' | sed 's|:.*||')
[[ -z "$OUTPUT_DIR" ]] && OUTPUT_DIR="./perf-results/${DOMAIN:-test}/${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo -e "\n${BOLD}${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BOLD}  Performance Test Configuration${NC}"
echo -e "${BOLD}${BLUE}══════════════════════════════════════════${NC}"
echo -e "  Target:     ${TARGET_URL}"
echo -e "  Test type:  ${TEST_TYPE}"
echo -e "  VUs:        ${VUS}"
echo -e "  Duration:   ${DURATION}"
echo -e "  Thresholds: p95<${THRESHOLD_P95}ms, p99<${THRESHOLD_P99}ms, error<${THRESHOLD_ERROR}%"
echo -e "  Output:     ${OUTPUT_DIR}"
echo -e "${BOLD}${BLUE}══════════════════════════════════════════${NC}\n"

# ─── Generate k6 script ───
echo -e "${BLUE}[1/3] Generating k6 test script...${NC}"

K6_SCRIPT="${OUTPUT_DIR}/test.js"
TEST_CONFIG="${OUTPUT_DIR}/test-config.json"

# Build generator command
GEN_CMD="python3 ${SCRIPT_DIR}/generate_k6_script.py --output '${K6_SCRIPT}'"

if [[ -n "$CONFIG_FILE" ]]; then
  GEN_CMD="$GEN_CMD --config '${CONFIG_FILE}'"
  # Copy config for report reference
  cp "$CONFIG_FILE" "$TEST_CONFIG"
else
  GEN_CMD="$GEN_CMD --url '${TARGET_URL}' --type '${TEST_TYPE}' --vus ${VUS} --duration '${DURATION}'"
  GEN_CMD="$GEN_CMD --threshold-p95 ${THRESHOLD_P95} --threshold-p99 ${THRESHOLD_P99} --threshold-error ${THRESHOLD_ERROR}"

  if [[ -n "$ENDPOINTS_FILE" ]]; then
    GEN_CMD="$GEN_CMD --endpoints '${ENDPOINTS_FILE}'"
  fi
  for ep in "${INLINE_ENDPOINTS[@]}"; do
    GEN_CMD="$GEN_CMD --endpoint '${ep}'"
  done
  for hdr in "${INLINE_HEADERS[@]}"; do
    GEN_CMD="$GEN_CMD --header '${hdr}'"
  done
  if [[ -n "$RAMP_UP" ]]; then
    GEN_CMD="$GEN_CMD --ramp-up '${RAMP_UP}'"
  fi

  # Write config JSON for analyze_results.py
  python3 -c "
import json
config = {
    'targetUrl': '${TARGET_URL}',
    'testType': '${TEST_TYPE}',
    'vus': ${VUS},
    'duration': '${DURATION}',
    'thresholds': {
        'http_req_duration_p95': ${THRESHOLD_P95},
        'http_req_duration_p99': ${THRESHOLD_P99},
        'error_rate_percent': ${THRESHOLD_ERROR}
    }
}
json.dump(config, open('${TEST_CONFIG}', 'w'), indent=2)
"
fi

eval "$GEN_CMD"
echo -e "${GREEN}✓ Script generated: ${K6_SCRIPT}${NC}"

# ─── Dry run? ───
if $DRY_RUN; then
  echo -e "\n${YELLOW}Dry run — script generated but not executed.${NC}"
  echo -e "Run manually: k6 run ${K6_SCRIPT}"
  exit 0
fi

# ─── Run k6 ───
echo -e "\n${BLUE}[2/3] Running k6 ${TEST_TYPE} test...${NC}"
echo -e "${CYAN}  This may take a while depending on duration and VU count.${NC}\n"

K6_SUMMARY="${OUTPUT_DIR}/k6-summary.json"
K6_LOG="${OUTPUT_DIR}/k6-output.log"

# Allow TARGET_URL override via environment variable
K6_RUN_CMD="k6 run --summary-export '${K6_SUMMARY}' ${K6_EXTRA_ARGS} '${K6_SCRIPT}'"

TEST_START=$(date +%s)

# Run k6 — capture output but also display it
if eval "$K6_RUN_CMD" 2>&1 | tee "$K6_LOG"; then
  K6_EXIT=0
else
  K6_EXIT=$?
fi

TEST_END=$(date +%s)
TEST_DURATION=$((TEST_END - TEST_START))

echo -e "\n${GREEN}✓ k6 completed in ${TEST_DURATION}s (exit code: ${K6_EXIT})${NC}"

# ─── Analyze results ───
echo -e "\n${BLUE}[3/3] Analyzing results...${NC}"

if [[ ! -f "$K6_SUMMARY" ]]; then
  echo -e "${RED}Error: k6 summary not generated. Check ${K6_LOG}${NC}"
  exit 4
fi

ANALYZE_CMD="python3 ${SCRIPT_DIR}/analyze_results.py --results '${K6_SUMMARY}' --output-dir '${OUTPUT_DIR}' --config '${TEST_CONFIG}'"
if [[ -n "$BASELINE" ]]; then
  ANALYZE_CMD="$ANALYZE_CMD --baseline '${BASELINE}'"
fi

eval "$ANALYZE_CMD"

# ─── Summary ───
echo -e "\n${BOLD}${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BOLD}  Performance Test Complete${NC}"
echo -e "${BOLD}${BLUE}══════════════════════════════════════════${NC}"
echo -e "  Target:      ${TARGET_URL}"
echo -e "  Test type:   ${TEST_TYPE}"
echo -e "  Duration:    ${TEST_DURATION}s"
echo -e "  k6 exit:     ${K6_EXIT}"
echo ""
echo -e "  Reports: ${OUTPUT_DIR}/"
echo -e "    perf-report.md       — Full report with SLA results"
echo -e "    perf-findings.json   — Machine-readable results"
echo -e "    perf-issues.csv      — SLA violation tracker"
if [[ -n "$BASELINE" ]]; then
  echo -e "    baseline-comparison.md — Delta vs baseline"
fi
echo -e "    k6-summary.json      — Raw k6 metrics"
echo -e "    test.js              — Generated k6 script (reusable)"
echo -e "    test-config.json     — Test configuration"
echo -e "${BOLD}${BLUE}══════════════════════════════════════════${NC}"

# Exit with SLA status
if [[ -f "${OUTPUT_DIR}/perf-issues.csv" ]]; then
  VIOLATIONS=$(tail -n +2 "${OUTPUT_DIR}/perf-issues.csv" | wc -l | tr -d ' ')
  if [[ "$VIOLATIONS" -gt 0 ]]; then
    echo -e "\n${RED}⚠ ${VIOLATIONS} SLA violation(s) detected — see perf-issues.csv${NC}"
    exit 4
  fi
fi

echo -e "\n${GREEN}✓ All SLA checks passed${NC}"
exit 0
