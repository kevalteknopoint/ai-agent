#!/usr/bin/env bash
# detect_stack.sh <repoPath>
#
# Deterministic tech-stack detector for the code-scan orchestrator. Runs with
# zero LLM tokens so the routing decision ("which analyzer agents apply") is
# never guessed by a model. Emits one JSON object on stdout:
#
# {
#   "javaSpringBoot": {"detected":bool,"fileCount":n,"evidence":[...]},
#   "aemHtl":         {"detected":bool,"fileCount":n,"evidence":[...]},
#   "edsBlocks":      {"detected":bool,"fileCount":n,"evidence":[...]},
#   "jsReact":        {"detected":bool,"fileCount":n,"evidence":[...]},
#   "cssScss":        {"detected":bool,"fileCount":n,"evidence":[...]}
# }
#
# "evidence" is capped at 5 paths — enough for a calling agent to scope its
# review without dumping the whole repo tree into context.

set -uo pipefail

REPO_PATH="${1:-}"
[ -z "$REPO_PATH" ] && { echo '{"error":"repoPath is required"}'; exit 1; }
cd "$REPO_PATH" || { echo '{"error":"repoPath not found"}'; exit 1; }

# Exclusion pipeline (grep -v) instead of a `find -prune` expression: keeps
# wildcard patterns out of shell variable expansion entirely, so nothing gets
# globbed against the filesystem before `find`/`grep` ever sees it.
EXCLUDE_RE='/(node_modules|target|build|dist|\.git|\.next|out)/'

evidence_json() {
  local first=1
  local out="["
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    if [ $first -eq 0 ]; then out="$out,"; fi
    p="${p//\\/\\\\}"; p="${p//\"/\\\"}"
    out="$out\"$p\""
    first=0
  done
  out="$out]"
  printf '%s' "$out"
}

block() {
  # $1=key $2=detected(true/false) $3=count $4=evidence-list(newline sep)
  local ev
  ev=$(printf '%s' "$4" | evidence_json)
  printf '"%s":{"detected":%s,"fileCount":%s,"evidence":%s}' "$1" "$2" "$3" "$ev"
}

# --- Java / Spring Boot (also covers plain AEM backend Java) ---
JAVA_FILES=$(find . -type f -name '*.java' -path '*/src/main/java/*' 2>/dev/null | grep -Ev "$EXCLUDE_RE")
JAVA_COUNT=$(printf '%s\n' "$JAVA_FILES" | grep -c . || true)
JAVA_DETECTED="false"; [ "$JAVA_COUNT" -gt 0 ] && JAVA_DETECTED="true"
JAVA_EVIDENCE=$(printf '%s\n' "$JAVA_FILES" | head -5)

# --- AEM Sightly / HTL ---
HTL_FILES=$(find . -type f -name '*.html' -path '*jcr_root/apps/*' 2>/dev/null | grep -Ev "$EXCLUDE_RE")
HTL_COUNT=$(printf '%s\n' "$HTL_FILES" | grep -c . || true)
HTL_DETECTED="false"; [ "$HTL_COUNT" -gt 0 ] && HTL_DETECTED="true"
HTL_EVIDENCE=$(printf '%s\n' "$HTL_FILES" | head -5)

# --- EDS blocks (boilerplate signature: blocks/ + scripts/aem.js|scripts.js|lib-franklin.js) ---
EDS_SIGNATURE=$(find . -type f \( -name 'aem.js' -o -name 'scripts.js' -o -name 'lib-franklin.js' \) -path '*/scripts/*' 2>/dev/null | grep -Ev "$EXCLUDE_RE" | head -1)
EDS_JS_FILES=$(find . -type f -name '*.js' -path '*/blocks/*' 2>/dev/null | grep -Ev "$EXCLUDE_RE")
EDS_JS_COUNT=$(printf '%s\n' "$EDS_JS_FILES" | grep -c . || true)
EDS_DETECTED="false"
[ -n "$EDS_SIGNATURE" ] && [ "$EDS_JS_COUNT" -gt 0 ] && EDS_DETECTED="true"
EDS_EVIDENCE=$(printf '%s\n' "$EDS_JS_FILES" | head -5)

# --- JS/React ---
REACT_PKG_FILES=$(find . -type f -name 'package.json' 2>/dev/null | grep -Ev "$EXCLUDE_RE" | xargs -I{} grep -l '"react"' {} 2>/dev/null)
REACT_COUNT=$(printf '%s\n' "$REACT_PKG_FILES" | grep -c . || true)
REACT_DETECTED="false"; [ "$REACT_COUNT" -gt 0 ] && REACT_DETECTED="true"
REACT_EVIDENCE=$(printf '%s\n' "$REACT_PKG_FILES" | head -5)

# --- CSS/SCSS (excluding files already inside an EDS blocks/ tree, which the EDS analyzer owns) ---
CSS_FILES=$(find . -type f \( -name '*.css' -o -name '*.scss' -o -name '*.sass' \) 2>/dev/null | grep -Ev "$EXCLUDE_RE" | grep -v '/blocks/' | grep -v '\.min\.css$')
CSS_COUNT=$(printf '%s\n' "$CSS_FILES" | grep -c . || true)
CSS_DETECTED="false"; [ "$CSS_COUNT" -gt 0 ] && CSS_DETECTED="true"
CSS_EVIDENCE=$(printf '%s\n' "$CSS_FILES" | head -5)

printf '{'
block javaSpringBoot "$JAVA_DETECTED" "$JAVA_COUNT" "$JAVA_EVIDENCE"; printf ','
block aemHtl "$HTL_DETECTED" "$HTL_COUNT" "$HTL_EVIDENCE"; printf ','
block edsBlocks "$EDS_DETECTED" "$EDS_JS_COUNT" "$EDS_EVIDENCE"; printf ','
block jsReact "$REACT_DETECTED" "$REACT_COUNT" "$REACT_EVIDENCE"; printf ','
block cssScss "$CSS_DETECTED" "$CSS_COUNT" "$CSS_EVIDENCE"
printf '}\n'
