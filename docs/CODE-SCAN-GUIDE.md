# Code-Scan Guide

Multi-agent static analysis: point it at a GitHub repo and branch, and it
clones/updates the repo, figures out what stack it actually contains, and
runs only the specialized reviewers that apply — each writing a
severity-ranked Markdown report and a CSV issue tracker to an `analysis/`
folder created **at the root of the cloned repo** (`<repoPath>/analysis/`,
not inside this toolkit).

## Why this exists

The five domains (Java/Spring Boot, AEM HTL, EDS blocks, JS/React,
CSS/SCSS) need genuinely different expertise — an XSS context bug in HTL and
an N+1 query in a Spring repository aren't caught by the same checklist. But
running all five against every repo wastes tokens on domains that don't
exist in it (a pure-EDS storefront has no Java to review; a Spring Boot API
has no HTL). So the system detects the stack first, deterministically, and
only pays for the analyzers that apply.

## Two entry points

| Entry point | Use when | Asks for input |
|---|---|---|
| **`code-scan` skill** (`skills/code-scan/SKILL.md`) | A human is driving the session | Conversational — asks for the GitHub URL, then the branch, confirms the routing plan before spending the analysis budget |
| **`code-scan` workflow** (`workflows/code-scan.js`) | CI, scheduled runs, multi-repo sweeps | Takes `repoUrl`/`branch` (or a `repos[]` list) as arguments — no prompting |

Both funnel into the same building blocks: `scripts/clone_or_update.sh`,
`scripts/detect_stack.sh`, the `code-scan-orchestrator` agent, and the five
analyzer agents.

## Pipeline

```
1. Get repoUrl                 (skill: ask user · workflow: args.repoUrl)
2. Get branch                  (skill: ask user · workflow: args.branch)
3. code-scan-orchestrator agent
     └─ scripts/clone_or_update.sh   (clone if absent, else fetch+checkout+pull)
     └─ scripts/detect_stack.sh      (find-based, zero LLM tokens)
     └─ returns: which of the 5 analyzers apply + evidence file lists
4. Confirm the plan with the user (skill only — workflow has a permission gate instead)
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

## Model policy (token-usage optimization)

The single biggest cost lever in a multi-agent system like this is keeping
planning centralized and execution scoped, rather than running heavyweight
reasoning across irrelevant files. This system uses a fixed model policy:
**Opus for planning/orchestration** and **Sonnet for execution/review**.

| Step | Model | Why |
|---|---|---|
| Repo clone/checkout/pull | *(shell script, no model)* | Purely deterministic — a model adds cost and a chance of mis-executing git commands for zero benefit |
| Stack detection | *(shell script, no model)* | `find`/`grep` pattern matching; a model would spend tokens re-deriving what a glob already answers exactly |
| `code-scan-orchestrator` (the agent that *calls* the two scripts above) | **Opus** | Planning/orchestration stage: deterministic setup + routing, strict schema output |
| `java-springboot-analyzer` | **Sonnet** | Execution-stage backend review with strict scope and file-level evidence |
| `aem-htl-analyzer` | **Sonnet** | Still security-relevant (XSS context handling) but scoped to templating layer; Sonnet handles context-based pattern matching reliably |
| `eds-blocks-analyzer` | **Sonnet** | Core Web Vitals + DOM-first correctness judgment calls that benefit from a stronger model, without backend-level stakes |
| `js-react-analyzer` | **Sonnet** | General correctness/security review, comparable complexity to the EDS analyzer |
| `css-scss-analyzer` | **Sonnet** | Execution-stage stylesheet review remains scoped and schema-driven for consistent output quality |
| Findings → csv tracker | *(stdlib Python script via `scripts/build_issues_csv.py`)* | Every analyzer emits findings as JSON; formatting into a pre-sorted CSV is 100% mechanical — no model should spend output tokens hand-building the tracker, and stdlib-only means no dependency to install on a fresh clone |

Net effect: Opus is used only for planning/routing; Sonnet is used only for
execution analyzers that are actually needed for the detected stack; and
clone/detect/tracker generation still spend zero LLM tokens.

## Output layout (inside the scanned repo, not this toolkit)

```
<scanned-repo>/                              ← repoPath, e.g. ai-agent/repos/<repoName>
└── analysis/                                ← created at the repo root
    ├── java-analysis-report.md / -findings.json / -issues.csv
    ├── aem-htl-analysis-report.md / -findings.json / -issues.csv
    ├── eds-blocks-analysis-report.md / -findings.json / -issues.csv
    ├── js-react-analysis-report.md / -findings.json / -issues.csv
    └── css-analysis-report.md / -findings.json / -issues.csv
```

Only the files for detected/dispatched analyzers are written — no empty
placeholder reports for stacks that aren't present. `analysis/` is a plain
folder inside the scanned repo (not gitignored by this toolkit — if you
don't want it committed to the scanned repo's own history, add
`analysis/` to *that* repo's `.gitignore`).

## Extending

To add a sixth domain (e.g. GraphQL schemas, Terraform):
1. Add a detection block to `scripts/detect_stack.sh` (new JSON key).
2. Add a new `agents/<domain>-analyzer.md` following the existing five as a
   template — keep the Input contract, Workflow, Severity table, and the
   "emit JSON → call `build_issues_csv.py`" Outputs pattern.
3. Add the new key → agent name mapping to
   `agents/code-scan-orchestrator.md` step 4.
4. Keep the same model policy: Opus for planning/orchestration updates,
   Sonnet for execution analyzer updates.
