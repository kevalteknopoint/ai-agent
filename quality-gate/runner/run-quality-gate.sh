#!/bin/bash

################################################################################
# AEM Quality Gate - Rule-Based Static Analysis Runner
#
# Zero AI, zero Claude involvement. Runs all quality checks offline.
# Usage: ./run-quality-gate.sh <targetRepoPath> [outputDir]
################################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Resolve script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOOLKIT_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET_REPO="${1:-.}"
OUTPUT_DIR="${2:-.}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}=== AEM Quality Gate Scanner ===${NC}"
echo "Toolkit: $TOOLKIT_ROOT"
echo "Target:  $TARGET_REPO"
echo "Output:  $OUTPUT_DIR"
echo ""

# Track results
declare -A results
results[java_pmd]=0
results[java_checkstyle]=0
results[htl]=0
results[eslint]=0
results[stylelint]=0
results[custom]=0

################################################################################
# 1. PMD - AEM/Sling Anti-Patterns
################################################################################
echo -e "${BLUE}[1/6] PMD - AEM/Sling Anti-Patterns${NC}"

if [ -f "$TARGET_REPO/core/pom.xml" ]; then
  RULESETS="$TOOLKIT_ROOT/rules/java/pmd-ruleset-aem-sling.xml,$TOOLKIT_ROOT/rules/java/pmd-ruleset-java-general.xml"

  if mvn org.apache.maven.plugins:maven-pmd-plugin:3.21.2:pmd \
      -Dpmd.rulesets="$RULESETS" \
      -Dformat=json \
      -f "$TARGET_REPO/core/pom.xml" \
      -q 2>/dev/null || true; then

    # Look for PMD report
    if [ -f "$TARGET_REPO/core/target/pmd.json" ]; then
      cp "$TARGET_REPO/core/target/pmd.json" "$OUTPUT_DIR/pmd-report.json"
      results[java_pmd]=1
      echo -e "${GREEN}✓ PMD scan completed${NC}"
    else
      echo -e "${YELLOW}⚠ PMD report not generated${NC}"
    fi
  else
    echo -e "${YELLOW}⚠ PMD execution failed (check project structure)${NC}"
  fi
else
  echo -e "${YELLOW}⚠ No core/pom.xml found${NC}"
fi

################################################################################
# 2. Checkstyle - Java Style
################################################################################
echo -e "${BLUE}[2/6] Checkstyle - Java Style Rules${NC}"

if [ -f "$TARGET_REPO/core/pom.xml" ]; then
  if mvn org.apache.maven.plugins:maven-checkstyle-plugin:3.3.1:check \
      -Dcheckstyle.config.location="$TOOLKIT_ROOT/rules/java/checkstyle-aem.xml" \
      -f "$TARGET_REPO/core/pom.xml" \
      -q 2>/dev/null || true; then

    if [ -f "$TARGET_REPO/core/target/checkstyle-result.xml" ]; then
      cp "$TARGET_REPO/core/target/checkstyle-result.xml" "$OUTPUT_DIR/checkstyle-report.xml"
      results[java_checkstyle]=1
      echo -e "${GREEN}✓ Checkstyle scan completed${NC}"
    else
      echo -e "${YELLOW}⚠ Checkstyle report not generated${NC}"
    fi
  else
    echo -e "${YELLOW}⚠ Checkstyle execution failed${NC}"
  fi
else
  echo -e "${YELLOW}⚠ No core/pom.xml found${NC}"
fi

################################################################################
# 3. HTL Validation
################################################################################
echo -e "${BLUE}[3/6] HTL Validation${NC}"

if [ -f "$TARGET_REPO/ui.apps/pom.xml" ]; then
  if mvn org.apache.sling:htl-maven-plugin:3.2.0:validate \
      -f "$TARGET_REPO/ui.apps/pom.xml" \
      -q 2>&1 | tee "$OUTPUT_DIR/htl-report.log" || true; then
    results[htl]=1
    echo -e "${GREEN}✓ HTL validation completed${NC}"
  else
    echo -e "${YELLOW}⚠ HTL validation failed or issues found${NC}"
  fi
else
  echo -e "${YELLOW}⚠ No ui.apps/pom.xml found${NC}"
fi

################################################################################
# 4. ESLint - JavaScript
################################################################################
echo -e "${BLUE}[4/6] ESLint - JavaScript Quality${NC}"

if [ -d "$TARGET_REPO/ui.frontend/src" ]; then
  if npm --prefix "$TOOLKIT_ROOT" install >/dev/null 2>&1; then
    if npx --prefix "$TOOLKIT_ROOT" eslint \
        --config "$TOOLKIT_ROOT/rules/frontend/eslint.config.aem.mjs" \
        --format json \
        "$TARGET_REPO/ui.frontend/src" \
        > "$OUTPUT_DIR/eslint-report.json" 2>&1 || true; then
      results[eslint]=1
      echo -e "${GREEN}✓ ESLint scan completed${NC}"
    else
      echo -e "${YELLOW}⚠ ESLint execution failed${NC}"
    fi
  else
    echo -e "${YELLOW}⚠ npm install failed${NC}"
  fi
else
  echo -e "${YELLOW}⚠ No ui.frontend/src directory found${NC}"
fi

################################################################################
# 5. Stylelint - CSS/SCSS
################################################################################
echo -e "${BLUE}[5/6] Stylelint - CSS/SCSS Quality${NC}"

if [ -d "$TARGET_REPO/ui.frontend/src" ]; then
  if npm --prefix "$TOOLKIT_ROOT" install >/dev/null 2>&1; then
    if npx --prefix "$TOOLKIT_ROOT" stylelint \
        --config "$TOOLKIT_ROOT/rules/frontend/stylelint.aem.json" \
        --formatter json \
        "$TARGET_REPO/ui.frontend/src/**/*.{less,scss,css}" \
        > "$OUTPUT_DIR/stylelint-report.json" 2>&1 || true; then
      results[stylelint]=1
      echo -e "${GREEN}✓ Stylelint scan completed${NC}"
    else
      echo -e "${YELLOW}⚠ Stylelint execution failed${NC}"
    fi
  else
    echo -e "${YELLOW}⚠ npm install failed${NC}"
  fi
else
  echo -e "${YELLOW}⚠ No ui.frontend/src directory found${NC}"
fi

################################################################################
# 6. Custom Clientlib Conventions
################################################################################
echo -e "${BLUE}[6/6] Custom - Clientlib Conventions${NC}"

if [ -d "$TARGET_REPO/ui.apps" ]; then
  if node "$TOOLKIT_ROOT/rules/custom/clientlib-conventions.js" \
      "$TARGET_REPO/ui.apps" \
      > "$OUTPUT_DIR/clientlib-report.json" 2>&1; then
    results[custom]=1
    echo -e "${GREEN}✓ Clientlib conventions check completed${NC}"
  else
    echo -e "${YELLOW}⚠ Clientlib check failed${NC}"
  fi
else
  echo -e "${YELLOW}⚠ No ui.apps directory found${NC}"
fi

################################################################################
# Summary
################################################################################
echo ""
echo -e "${BLUE}=== Summary ===${NC}"
echo "Java/PMD:      $([ ${results[java_pmd]} -eq 1 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⊘${NC}")"
echo "Java/Checkstyle: $([ ${results[java_checkstyle]} -eq 1 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⊘${NC}")"
echo "HTL:           $([ ${results[htl]} -eq 1 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⊘${NC}")"
echo "ESLint:        $([ ${results[eslint]} -eq 1 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⊘${NC}")"
echo "Stylelint:     $([ ${results[stylelint]} -eq 1 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⊘${NC}")"
echo "Clientlibs:    $([ ${results[custom]} -eq 1 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⊘${NC}")"
echo ""
echo "Raw reports written to: $OUTPUT_DIR"
echo ""
