#!/usr/bin/env bash
# clone_or_update.sh <repoUrl> <branch> <baseDir>
#
# Deterministic repo setup for the code-scan orchestrator. Runs with zero LLM
# tokens: clone-if-absent, fetch, checkout the requested branch, pull latest.
# Emits a single-line JSON result on stdout so a calling agent can parse it
# without needing to reason about git output.

set -uo pipefail

REPO_URL="${1:-}"
BRANCH="${2:-}"
BASE_DIR="${3:-}"

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  printf '%s' "$s"
}

fail() {
  local msg
  msg=$(json_escape "$1")
  printf '{"ready":false,"error":"%s"}\n' "$msg"
  exit 1
}

[ -z "$REPO_URL" ] && fail "repoUrl is required"
[ -z "$BRANCH" ] && fail "branch is required"
[ -z "$BASE_DIR" ] && fail "baseDir is required"

REPO_NAME=$(basename "$REPO_URL" .git)
REPO_PATH="$BASE_DIR/$REPO_NAME"

mkdir -p "$BASE_DIR" || fail "could not create baseDir $BASE_DIR"

if [ -d "$REPO_PATH/.git" ]; then
  CLONED="false"
else
  git clone --quiet "$REPO_URL" "$REPO_PATH" 2>/tmp/clone_or_update.err || \
    fail "git clone failed: $(cat /tmp/clone_or_update.err 2>/dev/null | tail -c 300)"
  CLONED="true"
fi

cd "$REPO_PATH" || fail "repoPath missing after clone"

git fetch --quiet origin 2>/tmp/clone_or_update.err || \
  fail "git fetch failed: $(cat /tmp/clone_or_update.err 2>/dev/null | tail -c 300)"

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout --quiet "$BRANCH" 2>/tmp/clone_or_update.err || \
    fail "git checkout failed: $(cat /tmp/clone_or_update.err 2>/dev/null | tail -c 300)"
else
  git checkout --quiet -b "$BRANCH" "origin/$BRANCH" 2>/tmp/clone_or_update.err || \
    fail "branch '$BRANCH' not found on origin: $(cat /tmp/clone_or_update.err 2>/dev/null | tail -c 300)"
fi

git pull --quiet origin "$BRANCH" 2>/tmp/clone_or_update.err || \
  fail "git pull failed: $(cat /tmp/clone_or_update.err 2>/dev/null | tail -c 300)"

COMMIT=$(git rev-parse --short HEAD)
COMMIT_MSG=$(json_escape "$(git log -1 --pretty=%s)")

printf '{"ready":true,"cloned":%s,"repoName":"%s","repoPath":"%s","branch":"%s","commit":"%s","commitMessage":"%s"}\n' \
  "$CLONED" "$(json_escape "$REPO_NAME")" "$(json_escape "$REPO_PATH")" "$(json_escape "$BRANCH")" "$COMMIT" "$COMMIT_MSG"
