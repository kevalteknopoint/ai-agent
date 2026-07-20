---
name: code-scan
description: >-
  Interactive entry point for the code-scan system. Asks for a GitHub URL
  (clones if not already present locally), asks for a branch (checks it out
  and pulls latest), runs deterministic tech-stack detection, and dispatches
  only the specialized analyzer agents that actually apply (Java/Spring Boot,
  AEM HTL, EDS blocks, JS/React, CSS/SCSS) — in parallel where independent.
  If the repo already carries an ./analysis/ folder from a previous scan, it
  offers a rescan instead: re-verify the findings already on record against
  the current code and write each one's fix status back into the same findings
  JSON and CSV tracker. Use when the user asks to "scan this repo", "run a
  code review on <github-url>", "security-review this AEM/EDS/Spring Boot
  project", "recheck what's been fixed", "update the scan status", or similar.
  Lives in the ai-agent toolkit repo alongside the analyzer agents it
  dispatches (agents/*.md) and the deterministic scripts it calls
  (scripts/*).
---

# Code-scan orchestrator (interactive)

You are driving a multi-agent static-analysis run across a cloned repo. Your
job in this turn is orchestration, not code review — the actual review is
delegated to five specialized subagents, each scoped to one stack, each
running on Sonnet for execution. Planning/orchestration stays on Opus
(including repository setup + routing). Keep your own reasoning and tool
calls to the mechanical steps below; do not read application source yourself.

Resolve `<ai-agent-repo>` as the absolute path to this toolkit repository.
When invoked from a workflow, this is passed via `args.aiAgentRepo`.

## Two runs, one skill

A repo that has never been scanned needs a **full scan**: read everything,
find issues, write the report + findings JSON + CSV tracker.

A repo that already has an `analysis/` folder usually doesn't. The question
the second time is almost always *"which of these did we actually fix?"* — so
the default there is a **rescan**: take the findings already on record, check
each one against the current code, and write its status back into the same
JSON and the same CSV. It reads only the files carrying a known finding, so
it costs a fraction of a full scan.

The trade is explicit: **a rescan finds no new issues.** It answers "is this
fixed", not "what's wrong now". Say so when you offer it, and offer the full
scan alongside — after a big feature merge, a full re-scan is the right call
even though `analysis/` exists.

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

### 3. Clone/update + detect stack + check for prior analysis (one subagent call)

Invoke the `code-scan-orchestrator` subagent (Agent tool) with the
`repoUrl`, `branch`, and `baseDir`:

```
Set up and route this repo for code-scan.
repoUrl: <url>
branch: <branch>
baseDir: <ai-agent-repo>/repos
ai-agent-repo: <absolute-path-to-toolkit>
mode: auto
```

This runs `scripts/clone_or_update.sh`, `scripts/detect_stack.sh`, then
`scripts/plan_verification.py` with zero code-review reasoning, and returns:
a routing plan (which of the five analyzer agents apply, plus each one's
evidence file list) and `priorAnalysis` (whether an `analysis/` folder is
already there, and how many findings are pending verification).

If `ready: false`, stop and show the user the exact error (bad URL, branch
not found, auth failure) — don't guess a fix on their behalf.

If `analyzers` comes back empty, tell the user plainly ("detected no
Java/Spring Boot, AEM HTL, EDS blocks, React, or standalone CSS/SCSS in this
repo") rather than running every analyzer as a fallback — an empty result is
real signal, not a detection failure.

### 4. Confirm the plan

Everything past this point can spend real tokens across hundreds of files, so
this is the one gate worth a confirmation. What you offer depends on
`priorAnalysis`.

**`priorAnalysis.present: false`** — only a full scan is possible. Show the
detected stacks and go:

> Detected: Java/Spring Boot (1,297 files), CSS/SCSS (84 files). Will run
> `java-springboot-analyzer` (sonnet) and `css-scss-analyzer` (sonnet). No AEM
> HTL, EDS blocks, or React found. Proceed?

**`priorAnalysis.present: true`** — both are possible, and the choice is the
user's. This is a genuine fork worth an `AskUserQuestion`, since the two
answer different questions and cost very different amounts:

> Found a previous scan: 42 findings across java (40 pending) and css (2).
>
> - **Rescan (recommended)** — re-check those 42 against the current code and
>   update their status in the same CSV/JSON. Won't find new issues.
> - **Full re-scan** — review the whole codebase again from scratch. Finds new
>   issues, and rewrites the reports.

Recommend the rescan by default, but steer toward the full scan when the user
says the code has changed substantially since the last scan (a release, a big
merge, a refactor) — a rescan there would faithfully verify 42 old findings
while missing everything the new code introduced.

Skip this gate only if the user's original request already picked a lane
("just scan it", "check what's been fixed").

Then go to **step 5** for a full scan, or **step 5b** for a rescan.

### 5. Dispatch the analyzers (full scan)

For each entry in the routing plan's `analyzers` list, invoke the matching
subagent via the Agent tool. **Send all of them in a single message with
multiple tool-use blocks** so they run in parallel — they're independent
(different files, different output filenames) and there's no reason to
serialize them. Each invocation should include:

```
Review <agent's domain> in this repo.
repoPath: <repoPath>
evidence: <the evidence file list from the routing plan, if non-empty>
ai-agent-repo: <ai-agent-repo>  (for the shared scripts/build_issues_csv.py path)

Follow your own workflow exactly: discover → read line-by-line → cross-file
pass → write ./analysis/ report + findings JSON + csv tracker → print only
your 5-line chat summary.
```

### 5b. Dispatch the verifiers (rescan)

`plan_verification.py` already wrote the batch plan to
`<repoPath>/analysis/.verify/plan.json` and `priorAnalysis.domains[].batchIds`
names each batch. For every batch ID across every domain, invoke the
`code-scan-verifier` subagent — **all of them in a single message with
multiple tool-use blocks** so they run in parallel. They're independent: each
writes its own verdict file.

```
Verify a batch of prior code-scan findings against the current code.
repoPath: <repoPath>
planPath: <priorAnalysis.planPath>
batchId: <batchId>
domain: <domain>

Follow your own workflow exactly: read the plan → pull your batch's issue
records from the findings JSON → re-read the current code (search for the
pattern; do not trust the recorded line number) → write one verdict per issue
ID to your batch's verdictPath → print only your 3-line chat summary.
```

Once **all batches for a domain** have returned, merge that domain (Bash):

```
cd <repoPath> && python3 <ai-agent-repo>/scripts/apply_verdicts.py \
  analysis/<domain>-analysis-findings.json \
  analysis/.verify/<domain>-b[0-9]*-verdicts.json \
  --csv analysis/<domain>-analysis-issues.csv --mode rescan
```

This is the only thing that writes status back — it updates the findings JSON
and rebuilds the CSV from the same issue list, so the two can't drift. **Never
hand-edit either file**; a model rewriting a 300-row tracker is how rows go
missing. Wait for a domain's batches before merging it: the script globs all
of that domain's verdicts at once. Keep the `[0-9]` in the glob — a bare
`<domain>-b*` would let a domain whose name prefixes another's cross-merge
(`eds-b*` matches `eds-blocks-b1-verdicts.json`).

Then render the cross-domain summary (Bash, once):

```
cd <repoPath> && python3 <ai-agent-repo>/scripts/build_rescan_summary.py <repoPath>
```

### 6. Summarize

**After a full scan** — relay each analyzer's 5-line chat summary verbatim
(don't paraphrase away the file/issue counts) and list the output paths so the
user knows where to look. Everything lands in `analysis/` at the root of the
cloned repo (`<repoPath>/analysis/`, not inside this toolkit):

```
analysis/java-analysis-report.md, analysis/java-analysis-issues.csv
analysis/css-analysis-report.md, analysis/css-analysis-issues.csv
```

**After a rescan** — lead with the number the user came for: how many of the
known findings are now fixed, and what's left.

> Rescanned 42 findings against `a1b2c3d`: **18 fixed**, 21 still open, 2 no
> longer applicable, 1 needs a human look. Status written back to
> `analysis/java-analysis-issues.csv` and `analysis/css-analysis-issues.csv`.
> Summary: `analysis/rescan-summary.md`.

Call out two things explicitly whenever they appear, because they're the ones
a status table makes easy to miss:

- **Regressions** (`regressed` in the merge output) — an issue that was Fixed
  and is now Open again. That's a real event, not a row in a table.
- **Unverifiable** issues — nobody knows if these are fixed. Name them so they
  land on a human rather than dissolving into a count.

Also report anything the merge flagged: `notVerified` (a batch failed, so
those issues kept their old status), `unknownVerdictIds`, `badVerdictFiles`.

If any analyzer or verifier failed or was skipped, say so explicitly rather
than omitting it — a partial run should read as partial, not as success.

## Re-running on the same repo

Steps 1–3 are safe and cheap to repeat (`clone_or_update.sh` no-ops the clone
and just fetches/pulls; stack detection is a few seconds of `find`).

What changes on a re-run is what's worth doing next:

- **Full scan** — each analyzer overwrites its own `analysis/<domain>-*` files,
  so a re-scan refreshes the report wholesale. No stale-state cleanup needed.
  It also **discards the fix statuses** a rescan recorded, since the findings
  are regenerated from scratch with new IDs. Mention that if the user has been
  tracking progress in the CSV.
- **Rescan** — updates statuses in place and preserves history: each issue
  keeps `firstSeenCommit`, and `scanHistory` in the findings JSON grows one
  entry per run, so the trend across runs stays readable.

Issues already marked `Fixed` / `Not Applicable` are skipped on later rescans —
re-reading a deleted file every run is cost with no signal. To re-check them
for regressions, pass `--recheck-fixed` to `plan_verification.py`.

## Token-usage notes (why this shape)

- Steps 1–3 spend zero LLM tokens on git/detection/planning logic — it's all
  shell and stdlib Python, executed by the planning/orchestrator layer.
- Only stacks actually present in the repo get an analyzer dispatched — a
  pure-EDS repo never spins up the Java/Spring Boot analyzer.
- Planning stays on Opus while execution runs on Sonnet, so token usage is
  optimized by keeping orchestration centralized and execution scoped by
  deterministic stack detection.
- Each analyzer emits findings as JSON and hands formatting off to
  `scripts/build_issues_csv.py` (stdlib-only, no dependency to install) —
  no model spends output tokens hand-constructing the tracker file.
- A rescan reads only the files carrying a known finding, not the codebase —
  which is the whole reason it exists. Verifier batches are grouped by file, so
  a file with six findings is opened once, not six times.
- The batch plan lives on disk (`analysis/.verify/plan.json`) and the verifiers
  read it directly. No model ever retypes a 300-issue list to pass it along.
