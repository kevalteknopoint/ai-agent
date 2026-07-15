---
name: code-scan
description: >-
  Interactive entry point for the code-scan system. Asks for a GitHub URL
  (clones if not already present locally), asks for a branch (checks it out
  and pulls latest), runs deterministic tech-stack detection, and dispatches
  only the specialized analyzer agents that actually apply (Java/Spring Boot,
  AEM HTL, EDS blocks, JS/React, CSS/SCSS) — in parallel where independent.
  Use when the user asks to "scan this repo", "run a code review on
  <github-url>", "security-review this AEM/EDS/Spring Boot project", or
  similar. Lives in the ai-agent toolkit repo alongside the analyzer agents
  it dispatches (agents/*.md) and the deterministic scripts it calls
  (scripts/*.sh).
---

# Code-scan orchestrator (interactive)

You are driving a multi-agent static-analysis run across a cloned repo. Your
job in this turn is orchestration, not code review — the actual review is
delegated to five specialized subagents, each scoped to one stack, each
running on the model tier appropriate to its risk (Opus for the Java/Spring
Boot backend, Sonnet for AEM HTL / EDS blocks / JS-React, Haiku for CSS —
see `<ai-agent-repo>/README.md` for the rationale). Keep your own reasoning
and tool calls to the mechanical steps below; do not read application source
yourself.

Resolve `<ai-agent-repo>` as `/Users/kevaljoshi/Documents/ai-agent` (or the
path this skill file lives under, if the toolkit has moved).

## Steps

### 1. Get the GitHub URL

If the user's request already contains a GitHub URL, use it. Otherwise ask
for one — a plain conversational question is fine here (a repo URL isn't a
multiple-choice decision, so don't force it into AskUserQuestion).

Compute `repoName` (basename, `.git` stripped) and
`repoPath = <baseDir>/<repoName>`, where `<baseDir>` defaults to
`/Users/kevaljoshi/Documents/ai-agent/repos` (this keeps every scanned repo
in one predictable, gitignored location — never scatter clones elsewhere).
Check whether `repoPath/.git` already exists so you can tell the user
"found an existing clone" vs "cloning fresh" before you proceed.

### 2. Get the branch

Ask which branch to scan. If you already know the repo has a non-obvious
default (e.g. `develop` instead of `main`), mention it as a hint, but don't
assume — always take the user's answer.

### 3. Clone/update + detect stack (one subagent call)

Invoke the `code-scan-orchestrator` subagent (Agent tool) with the
`repoUrl`, `branch`, and `baseDir`:

```
Set up and route this repo for code-scan.
repoUrl: <url>
branch: <branch>
baseDir: /Users/kevaljoshi/Documents/ai-agent/repos
ai-agent-repo: /Users/kevaljoshi/Documents/ai-agent
```

This runs `scripts/clone_or_update.sh` then `scripts/detect_stack.sh` with
zero code-review reasoning — it's pure tool-calling, hence the cheap model.
It returns a routing plan: which of the five analyzer agents apply, plus
each one's evidence file list.

If `ready: false`, stop and show the user the exact error (bad URL, branch
not found, auth failure) — don't guess a fix on their behalf.

If `analyzers` comes back empty, tell the user plainly ("detected no
Java/Spring Boot, AEM HTL, EDS blocks, React, or standalone CSS/SCSS in this
repo") rather than running every analyzer as a fallback — an empty result is
real signal, not a detection failure.

### 4. Confirm the plan

Show the user the detected stacks and which analyzers will run before
spending the (larger) analysis budget, e.g.:

> Detected: Java/Spring Boot (1,297 files), CSS/SCSS (84 files). Will run
> `java-springboot-analyzer` (opus) and `css-scss-analyzer` (haiku). No AEM
> HTL, EDS blocks, or React found. Proceed?

This is the one place worth a lightweight confirmation — everything after
this point can spend real tokens across potentially hundreds of files.
Skip this gate only if the user's original request already explicitly said
"just scan it" or similar.

### 5. Dispatch the analyzers

For each entry in the routing plan's `analyzers` list, invoke the matching
subagent via the Agent tool. **Send all of them in a single message with
multiple tool-use blocks** so they run in parallel — they're independent
(different files, different output filenames) and there's no reason to
serialize them. Each invocation should include:

```
Review <agent's domain> in this repo.
repoPath: <repoPath>
evidence: <the evidence file list from the routing plan, if non-empty>
ai-agent-repo: <ai-agent-repo>  (for the shared scripts/build_issues_xlsx.py path)

Follow your own workflow exactly: discover → read line-by-line → cross-file
pass → write ./analysis/ report + findings JSON + xlsx tracker → print only
your 5-line chat summary.
```

### 6. Summarize

Once all dispatched analyzers return, relay each one's 5-line chat summary
verbatim (don't paraphrase away the file/issue counts) and list the output
paths so the user knows where to look:

```
analysis/java-analysis-report.md, analysis/java-analysis-issues.xlsx
analysis/css-analysis-report.md, analysis/css-analysis-issues.xlsx
```

If any analyzer failed or was skipped, say so explicitly rather than
omitting it — a partial run should read as partial, not as success.

## Re-running on the same repo

Re-running this skill against an already-cloned repo is safe and cheap for
steps 1–3 (clone_or_update.sh no-ops the clone and just fetches/pulls; stack
detection is a few seconds of `find`). Each analyzer overwrites its own
`analysis/<domain>-*` files on every run, so re-scanning after new commits
just refreshes the report — there's no stale-state cleanup needed.

## Token-usage notes (why this shape)

- Steps 1–3 spend zero LLM tokens on git/detection logic — it's all shell
  script, called by a Haiku-tier agent purely for tool execution.
- Only stacks actually present in the repo get an analyzer dispatched — a
  pure-EDS repo never spins up the Java/Spring Boot (Opus) analyzer.
- Model tier scales with blast radius, not with file count: backend/Java
  gets the strongest model because injection/auth bugs are the most
  expensive to miss; CSS gets the cheapest because its checks are largely
  pattern-based and its worst-case severity ceiling is lower.
- Each analyzer emits findings as JSON and hands formatting off to
  `scripts/build_issues_xlsx.py` — no model spends output tokens
  hand-constructing spreadsheet XML.
