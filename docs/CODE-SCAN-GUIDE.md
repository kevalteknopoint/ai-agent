# Code-Scan Guide

Multi-agent static analysis: point it at a GitHub repo and branch, and it
clones/updates the repo, figures out what stack it actually contains, and
runs only the specialized reviewers that apply — each writing a
severity-ranked Markdown report and a CSV issue tracker to an `analysis/`
folder created **at the root of the cloned repo** (`<repoPath>/analysis/`,
not inside this toolkit).

Point it at the *same* repo later and it does something different: instead of
re-reviewing the codebase, it re-checks the findings already on record and
writes each one's fix status back into the same JSON and CSV. See
[Rescan mode](#rescan-mode-has-this-been-fixed-yet).

## Why this exists

The five domains (Java/Spring Boot, AEM HTL, EDS blocks, JS/React,
CSS/SCSS) need genuinely different expertise — an XSS context bug in HTL and
an N+1 query in a Spring repository aren't caught by the same checklist. But
running all five against every repo wastes tokens on domains that don't
exist in it (a pure-EDS storefront has no Java to review; a Spring Boot API
has no HTL). So the system detects the stack first, deterministically, and
only pays for the analyzers that apply.

The same logic drove rescan mode. Once a repo has been scanned, the recurring
question isn't "what's wrong with this code" — it's "which of these 42 did we
actually fix?" Re-running the full analysis to answer that re-reads every file
in the repo to re-derive findings you already have, and hands back fresh issue
IDs that no longer line up with the tracker anyone's been working from. A
rescan reads only the files carrying a known finding and updates the tracker in
place.

## Two entry points

| Entry point | Use when | Asks for input |
|---|---|---|
| **`code-scan` skill** (`skills/code-scan/SKILL.md`) | A human is driving the session | Conversational — asks for the GitHub URL, then the branch, offers full-scan vs rescan when prior analysis exists, confirms before spending the analysis budget |
| **`code-scan` workflow** (`workflows/code-scan.js`) | CI, scheduled runs, multi-repo sweeps | Takes `repoUrl`/`branch` (or a `repos[]` list) plus an optional `mode` as arguments — no prompting |

Both funnel into the same building blocks: the scripts in `scripts/`, the
`code-scan-orchestrator` router, the five analyzer agents, and the
`code-scan-verifier`.

## Two modes

| | Full scan | Rescan |
|---|---|---|
| **Answers** | "What's wrong with this code?" | "Which known issues are fixed?" |
| **Runs when** | No `analysis/` folder yet, or forced with `mode:"full"` | `analysis/` already present (the default then) |
| **Reads** | Every in-scope file | Only files carrying a known finding |
| **Finds new issues** | Yes | **No** — that's the trade |
| **Writes** | Report + findings JSON + CSV, overwritten wholesale | Status back into the *same* findings JSON + CSV, in place |
| **Agents** | The detected analyzers | `code-scan-verifier`, one per batch |

`mode` (workflow) defaults to `auto`: rescan when there's prior analysis with
pending findings, full scan otherwise. `mode:"rescan"` with no prior analysis
fails loudly rather than silently spending a full-scan budget nobody asked for.

**When to force a full scan anyway:** after a release, a big merge, or a
refactor. A rescan there would faithfully verify 42 old findings while missing
everything the new code introduced. Note that a full re-scan regenerates
findings from scratch with new IDs, discarding recorded fix statuses.

## Pipeline

```
1. Get repoUrl                 (skill: ask user · workflow: args.repoUrl)
2. Get branch                  (skill: ask user · workflow: args.branch)
3. code-scan-orchestrator agent
     └─ scripts/clone_or_update.sh   (clone if absent, else fetch+checkout+pull)
     └─ scripts/detect_stack.sh      (find-based, zero LLM tokens)
     └─ scripts/plan_verification.py (is there prior analysis? what needs re-checking?)
     └─ returns: which of the 5 analyzers apply + evidence file lists + priorAnalysis
4. Confirm the plan with the user (skill only — workflow has a permission gate instead)

   ── FULL SCAN ────────────────────────────────────────────────────────────
5. Dispatch only the detected analyzers, IN PARALLEL:
     java-springboot-analyzer   (sonnet)
     aem-htl-analyzer           (sonnet)
     eds-blocks-analyzer        (sonnet)
     js-react-analyzer          (sonnet)
     css-scss-analyzer          (sonnet)
6. Each analyzer writes, into <repoPath>/analysis/ (created at the repo root):
     analysis/<domain>-analysis-report.md      — narrative findings, LLM-authored
     analysis/<domain>-analysis-findings.json  — structured findings, LLM-authored
     analysis/<domain>-analysis-issues.csv     — generated deterministically by
                                                  scripts/build_issues_csv.py from the JSON

   ── RESCAN ───────────────────────────────────────────────────────────────
5b. Dispatch one code-scan-verifier (sonnet) per batch, IN PARALLEL.
      Each reads its batch from analysis/.verify/plan.json, re-reads the current
      code at each finding, and writes analysis/.verify/<batchId>-verdicts.json
6b. Per domain, once its batches land:
      scripts/apply_verdicts.py  → merges verdicts into the SAME findings JSON
                                    and rebuilds the SAME CSV (zero LLM tokens)
    Then once per repo:
      scripts/build_rescan_summary.py → analysis/rescan-summary.md

7. Summary relayed to the user / returned by the workflow
```

## Stack detection rules (`scripts/detect_stack.sh`)

| Analyzer | Trigger |
|---|---|
| `java-springboot-analyzer` | any `*.java` under `src/main/java/` (covers Spring Boot apps and plain AEM backend Java — the Spring-specific checks just yield fewer findings on non-Spring code) |
| `aem-htl-analyzer` | any `*.html` under `jcr_root/apps/` (HTL/Sightly templates) |
| `eds-blocks-analyzer` | `blocks/*.js` **and** an EDS boilerplate signature (`scripts/aem.js`, `scripts/scripts.js`, or `scripts/lib-franklin.js`) |
| `js-react-analyzer` | a `package.json` with a `"react"` dependency |
| `css-scss-analyzer` | `*.css`/`*.scss`/`*.sass` outside any `blocks/` tree (EDS block CSS is owned by `eds-blocks-analyzer`, so it's excluded here to avoid double-reviewing the same files) |

A repo can trigger multiple analyzers (e.g. a classic AEM project: Java +
HTL + CSS) or exactly one (an EDS-only storefront: just `eds-blocks-analyzer`).
Detection is pure `find`/`grep` — no model ever guesses the stack.

## Rescan mode ("has this been fixed yet?")

Rescan detection is the same kind of question as stack detection, so it gets
the same kind of answer: `scripts/plan_verification.py` globs
`analysis/*-analysis-findings.json`. Findings on disk → rescan is possible. No
model opinion involved.

### Statuses

Each issue in the findings JSON gains a `status`:

| Status | Meaning |
|---|---|
| `Open` | Still present — here, or somewhere else after a refactor. The default. |
| `Fixed` | Genuinely gone, with a pointer to the fix. |
| `Partially Fixed` | Real mitigation landed but the issue survives on some path — one of three call sites fixed, escaping added but not for attribute context. |
| `Not Applicable` | The code carrying it no longer exists. It didn't get fixed; it left. |
| `Unverifiable` | The verifier couldn't tell. Routed to a human — never silently closed. |

Alongside the status, each issue carries its own provenance: `statusDetail`
(the evidence for the verdict), `verifiedFile`/`verifiedLine` (where it lives
*now*, kept separate from the original `file`/`line` so a rescan never erases
the original pointer), `firstSeenCommit`, `lastVerifiedCommit`/`Date`, and
`fixedInCommit`. The findings JSON also grows a `scanHistory` entry per run, so
the trend across runs stays readable.

### Design constraints (why it's shaped this way)

A rescan writes to the artifact a team is actively tracking work in, so the
failure modes are worse than a full scan's — a full scan that gets something
wrong produces a bad report, but a rescan that gets something wrong *silently
closes a live security finding*. That drove four decisions:

- **Models judge; scripts write.** Verifiers only ever emit small verdict JSONs.
  `apply_verdicts.py` merges them into the findings JSON and rebuilds the CSV
  from the same in-memory issue list, so the two can't drift and a 300-row
  tracker can't lose rows to a truncated generation.
- **Ambiguity resolves toward Open, never Fixed.** The verifier is told to pick
  `Unverifiable` over a guessed `Fixed`, and `normalize_status()` maps any
  unrecognized status string to `Unverifiable` — so a malformed verdict cannot
  close a finding. Silence does the same: an issue with no verdict (a crashed
  batch) keeps its previous status and is reported as `notVerified`.
- **Line numbers are treated as rotten.** Someone adds an import and every
  finding in the file shifts. The verifier is told to search for the pattern,
  not trust the recorded line, and to record where the issue moved to —
  including into a different file.
- **Regressions are first-class.** A `Fixed` issue found present again clears
  its `fixedInCommit` and lands in the summary under its own heading, because a
  reverted fix is an event, not a row in a table.

### Cost

Terminal issues (`Fixed`, `Not Applicable`) are skipped on later rescans —
re-reading a deleted file every run is cost with no signal. `--recheck-fixed`
(`recheckFixed: true`) re-verifies them to catch regressions; it's worth
running before a release, not every sprint.

Verifier batches are grouped by file, so a file with six findings is opened
once, not six times. `--batch-size` (default 12) caps issues per verifier. The
batch plan lives on disk at `analysis/.verify/plan.json` and the verifiers read
it directly — no model ever retypes a 300-issue list to pass it along.

`analysis/.verify/` is purged and rewritten at the start of every rescan.
That's deliberate and it's the only safe moment: the merge step globs the whole
directory, so a previous run's stragglers would otherwise be folded into this
run's results.

## Model policy (token-usage optimization)

The single biggest cost lever in a multi-agent system like this is keeping
planning centralized and execution scoped, rather than running heavyweight
reasoning across irrelevant files. This system uses a fixed model policy:
**Opus for planning/orchestration** and **Sonnet for execution/review**.

| Step | Model | Why |
|---|---|---|
| Repo clone/checkout/pull | *(shell script, no model)* | Purely deterministic — a model adds cost and a chance of mis-executing git commands for zero benefit |
| Stack detection | *(shell script, no model)* | `find`/`grep` pattern matching; a model would spend tokens re-deriving what a glob already answers exactly |
| Rescan planning (is there prior analysis? what needs re-checking? how to batch it?) | *(stdlib Python via `scripts/plan_verification.py`)* | A glob and a status filter — a model would spend tokens re-deriving what the filesystem answers exactly |
| `code-scan-orchestrator` (the agent that *calls* the three scripts above) | **Opus** | Planning/orchestration stage: deterministic setup + routing, strict schema output |
| `code-scan-verifier` (rescan) | **Sonnet** | Execution-stage judgment, but a narrow one: does this specific known issue still exist? Scoped to one batch of findings, with the original problem + recommended fix already in hand |
| `java-springboot-analyzer` | **Sonnet** | Execution-stage backend review with strict scope and file-level evidence |
| `aem-htl-analyzer` | **Sonnet** | Still security-relevant (XSS context handling) but scoped to templating layer; Sonnet handles context-based pattern matching reliably |
| `eds-blocks-analyzer` | **Sonnet** | Core Web Vitals + DOM-first correctness judgment calls that benefit from a stronger model, without backend-level stakes |
| `js-react-analyzer` | **Sonnet** | General correctness/security review, comparable complexity to the EDS analyzer |
| `css-scss-analyzer` | **Sonnet** | Execution-stage stylesheet review remains scoped and schema-driven for consistent output quality |
| Findings → csv tracker | *(stdlib Python script via `scripts/build_issues_csv.py`)* | Every analyzer emits findings as JSON; formatting into a pre-sorted CSV is 100% mechanical — no model should spend output tokens hand-building the tracker, and stdlib-only means no dependency to install on a fresh clone |
| Verdicts → status in the JSON + CSV | *(stdlib Python via `scripts/apply_verdicts.py`)* | Merging verdicts and rebuilding the tracker is mechanical, and doing it in one script is what keeps the JSON and CSV from drifting apart |
| Cross-domain rescan summary | *(stdlib Python via `scripts/build_rescan_summary.py`)* | Every number is already in the JSON; paying a model to retype them risks a summary that disagrees with the tracker |

Net effect: Opus is used only for planning/routing; Sonnet is used only for
execution analyzers that are actually needed for the detected stack, and for
the narrow rescan verdicts; and clone/detect/plan/tracker/summary generation
still spend zero LLM tokens.

## Output layout (inside the scanned repo, not this toolkit)

```
<scanned-repo>/                              ← repoPath, e.g. ai-agent/repos/<repoName>
└── analysis/                                ← created at the repo root
    ├── java-analysis-report.md / -findings.json / -issues.csv
    ├── aem-htl-analysis-report.md / -findings.json / -issues.csv
    ├── eds-blocks-analysis-report.md / -findings.json / -issues.csv
    ├── js-react-analysis-report.md / -findings.json / -issues.csv
    ├── css-analysis-report.md / -findings.json / -issues.csv
    │
    ├── rescan-summary.md                    ← rescan only: cross-domain status,
    │                                          regressions, still-open list
    └── .verify/                             ← rescan scratch + audit trail
        ├── plan.json                          (batch plan, read by the verifiers)
        └── <batchId>-verdicts.json            (one per verifier batch)
```

Only the files for detected/dispatched analyzers are written — no empty
placeholder reports for stacks that aren't present. `analysis/` is a plain
folder inside the scanned repo (not gitignored by this toolkit — if you
don't want it committed to the scanned repo's own history, add
`analysis/` to *that* repo's `.gitignore`).

A rescan does not touch `<domain>-analysis-report.md`: the narrative report is
a point-in-time artifact of the scan that produced it. Current status lives in
the CSV/JSON, and `rescan-summary.md` is the readable view of it.

## Extending

To add a sixth domain (e.g. GraphQL schemas, Terraform):
1. Add a detection block to `scripts/detect_stack.sh` (new JSON key).
2. Add a new `agents/<domain>-analyzer.md` following the existing five as a
   template — keep the Input contract, Workflow, Severity table, and the
   "emit JSON → call `build_issues_csv.py`" Outputs pattern.
3. Add the new key → agent name mapping to
   `agents/code-scan-orchestrator.md` step 5.
4. Keep the same model policy: Opus for planning/orchestration updates,
   Sonnet for execution analyzer updates.

Rescan needs no work here: `plan_verification.py` discovers domains by globbing
`analysis/*-analysis-findings.json` and derives the CSV/report paths from the
filename, so a new analyzer that follows the naming convention is picked up
automatically. `code-scan-verifier` is stack-agnostic by design — it verifies
whatever the finding describes, whatever language it's in.
