# AEM Development Automation Toolkit

AI-powered and rule-driven automation for Adobe AEM as a Cloud Service (AEMaaCS) and adjacent
stacks (Spring Boot, Edge Delivery Services, React): unit test generation, rule-driven quality
gating, and multi-agent security-first code scanning.

This README is the full catalog — every agent, workflow, and skill in this repo, what it does,
what model/tools it uses, and how to run it. If you're new to this repo (including "someone just
handed me this repo"), start at [Setup — using this repo](#setup--using-this-repo-fresh-clone-or-shared-copy).

## What's inside

### Agents (`agents/*.md`)

Standalone Claude Code subagent definitions. Each is invoked either directly (Task/Agent tool,
by its `name:` frontmatter) or as the `agentType` a workflow script dispatches to.

| Agent | Model | Tools | What it does |
|---|---|---|---|
| `code-scan-orchestrator` | Haiku | Read, Bash, Grep, Glob | Clones/updates a repo+branch and runs deterministic tech-stack detection; returns which analyzer agents apply. No code review. |
| `java-springboot-analyzer` | Opus | Read, Grep, Glob, Bash, Write | Backend security-first review: injection, auth, secrets, concurrency, N+1 queries, resource leaks. |
| `aem-htl-analyzer` | Sonnet | Read, Grep, Glob, Bash, Write | AEM Sightly/HTL templates: XSS context handling, Sling Model binding, authoring/edit-mode behavior. |
| `eds-blocks-analyzer` | Sonnet | Read, Grep, Glob, Bash, Write | Edge Delivery Services blocks: Core Web Vitals, DOM-first patterns, vanilla JS conventions. |
| `js-react-analyzer` | Sonnet | Read, Grep, Glob, Bash, Write | React/JS: correctness, XSS, hooks misuse, performance, architecture. |
| `css-scss-analyzer` | Haiku | Read, Grep, Glob, Bash, Write | CSS/SCSS: specificity, architecture, accessibility, performance. |
| `vbrd-to-proofhub` | inherit | Read, Write, Edit, Bash, Grep, Glob, WebFetch | Translates a Visual BRD Excel workbook into Jira-grade ProofHub tasklists/tasks (idempotent sync keyed on Component ID). |

The five analyzer agents (`java-springboot-analyzer` through `css-scss-analyzer`) are dispatched
by the `code-scan` skill/workflow below — you rarely invoke them standalone, though you can.

### Workflows (`workflows/*.js`)

Scripts for Claude Code's Workflow tool (multi-stage pipelines with permission gates). Each is
runnable as a slash command with a JSON `--args` payload.

| Workflow | Invocation | What it does |
|---|---|---|
| `code-scan` | `/code-scan --args '{...}'` | Clone/update → detect stack → dispatch only the matching analyzer agents, in parallel. Headless counterpart to the `code-scan` skill. |
| `aem-unit-test-cases` | `/aem-unit-test-cases --args '{...}'` | Clone → generate JUnit/Mockito/AEM-Mocks unit tests targeting 80%+ coverage → local Maven build validation → auto-push to a feature branch. |
| `spring-boot-unit-test-cases` | `/spring-boot-unit-test-cases --args '{...}'` | Same pipeline shape as above, tuned for Spring Boot (JUnit/Mockito/Spring Test). |
| `aem-quality-gate` | `/aem-quality-gate --args '{...}'` | Rule-driven static analysis — PMD, Checkstyle, ESLint, Stylelint, custom clientlib checks. **Zero LLM tokens for scanning**; optional AI pass only tunes rule thresholds afterward. |

### Skills (`skills/*/SKILL.md`)

Interactive entry points — loaded into the main conversation so they can ask follow-up questions,
unlike workflows/agents which run as a single dispatched task.

| Skill | What it does |
|---|---|
| `code-scan` | Asks for a GitHub URL (clones if not already present locally), asks for a branch (checks it out, pulls latest), shows the detected stack for confirmation, then dispatches only the applicable analyzer agents. |

### Rule-driven toolkit (`quality-gate/`)

Not an agent or a workflow — a standalone, zero-AI static-analysis engine (`quality-gate/runner/run-quality-gate.sh`
orchestrates PMD/Checkstyle/ESLint/Stylelint/HTMLHint per `quality-gate/rules-manifest.json`,
`quality-gate/aggregator/aggregate-report.js` merges results into one report). The `aem-quality-gate`
workflow above is the thin wrapper that clones a repo and calls this toolkit.

## Setup — using this repo (fresh clone or shared copy)

### 1. Prerequisites

| Need | Required for | Install |
|---|---|---|
| Claude Code CLI | everything | `npm install -g @anthropic-ai/claude-code` (or use claude.ai/code) |
| `git` | everything | usually preinstalled |
| `python3` | `code-scan`'s CSV tracker | preinstalled on macOS/Linux — **stdlib only, nothing to `pip install`** |
| `mvn` (Maven) | `aem-unit-test-cases`, `spring-boot-unit-test-cases` build validation | required only if you use those two workflows |
| `node` + `npm` | `aem-quality-gate` | run `cd quality-gate && npm install` once |
| ProofHub API access | `vbrd-to-proofhub` only | set `PROOFHUB_BASE_URL`, `PROOFHUB_API_KEY`, `PROOFHUB_USER_AGENT` in your environment or a local `.env` — never hardcode these in a prompt or commit them |

Nothing here needs a database, a server, or network services beyond git/GitHub and (for
`vbrd-to-proofhub`) the ProofHub API.

### 2. Wiring it into Claude Code

Claude Code auto-discovers agents/skills/workflows from a project's `.claude/` directory. This
repo keeps its source of truth at the **repo root** (`agents/`, `workflows/`, `skills/`) instead,
so the whole toolkit is easy to browse, diff, and version as one unit. Two ways to use it:

**Option A — work from inside this repo.** `cd ai-agent && claude`, then invoke workflows/skills
by name (e.g. `/code-scan`, or ask for the `code-scan` skill in conversation). This is the
simplest path if you're scanning/testing repos that live alongside this toolkit (e.g. under
`ai-agent/repos/`, which is git-ignored).

**Option B — wire it into another project.** Symlink (or copy) the pieces you need into that
project's `.claude/` directory:

```bash
TOOLKIT=/path/to/ai-agent   # wherever you cloned this repo
mkdir -p .claude/agents .claude/skills .claude/workflows
ln -s "$TOOLKIT"/agents/*.md .claude/agents/
ln -s "$TOOLKIT"/skills/* .claude/skills/
ln -s "$TOOLKIT"/workflows/*.js .claude/workflows/
```

Symlinks (not copies) mean `git pull` inside `$TOOLKIT` updates every project you've wired it
into. The five code-scan analyzer agents also shell out to `$TOOLKIT/scripts/*.sh` and
`build_issues_csv.py` — those paths are passed explicitly at invocation time (see each agent's
"Input contract" / the `ai-agent-repo` argument), so Option B works even though the scripts
themselves aren't symlinked into `.claude/`.

### 3. Where things get cloned

Every workflow here clones target repos to a predictable, git-ignored location instead of
scattering them across the filesystem:

| Workflow | Default clone location | Override |
|---|---|---|
| `aem-unit-test-cases`, `spring-boot-unit-test-cases`, `aem-quality-gate` | `/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos` | `args.baseDir` |
| `code-scan` (skill or workflow) | `<this-repo>/repos` | `args.baseDir` (workflow) or say a different location when the skill asks |

`code-scan` additionally writes its output **inside the scanned repo itself** — see
[Output locations](#output-locations) below, not into this toolkit.

## Output locations

- **Test generation** (`aem-unit-test-cases`, `spring-boot-unit-test-cases`): test files land in
  `<clonedRepo>/src/test/java/...`, and on success the workflow pushes a `feature/ai-unit-test-cases`
  branch to the repo's own remote.
- **Quality Gate** (`aem-quality-gate`): reports land wherever `quality-gate/runner/run-quality-gate.sh`
  is configured to write (see [AEM-QUALITY-GATE-GUIDE.md](docs/AEM-QUALITY-GATE-GUIDE.md)).
- **Code Scan** (`code-scan`): each dispatched analyzer creates an `analysis/` folder **at the
  root of the cloned repo** (`<repoPath>/analysis/`, i.e. a sibling of that repo's `pom.xml`/
  `package.json`) and writes three files per domain:
  ```
  <repoPath>/analysis/
    java-analysis-report.md / -findings.json / -issues.csv
    aem-htl-analysis-report.md / -findings.json / -issues.csv
    eds-blocks-analysis-report.md / -findings.json / -issues.csv
    js-react-analysis-report.md / -findings.json / -issues.csv
    css-analysis-report.md / -findings.json / -issues.csv
  ```
  Only the domains actually detected in that repo get written. `-report.md` is the narrative
  writeup, `-findings.json` is the structured source of truth, `-issues.csv` is the sortable
  tracker (opens directly in Excel/Numbers/Sheets — no dependency to install). `analysis/` is a
  plain folder in the scanned repo, not gitignored by this toolkit — add it to *that* repo's own
  `.gitignore` if you don't want it committed there.

## Choosing which one to run

**Want unit tests written for an AEM or Spring Boot backend?** → `aem-unit-test-cases` /
`spring-boot-unit-test-cases` (below)

**Want a fast, zero-AI lint/quality gate on an AEMaaCS repo?** → `aem-quality-gate`

**Want a deep, security-first code review (Java/Spring Boot, AEM HTL, EDS, React, or CSS —
whichever the repo actually contains)?** → `code-scan`

**Need to turn a Visual BRD spreadsheet into ProofHub tasks?** → `vbrd-to-proofhub` (invoke the
agent directly; it's not part of a workflow)

---

## Code Scan (multi-agent, stack-aware)

🔎 **`code-scan`** — the newest and most involved workflow here, detailed in full below.

- Give it a GitHub URL and branch — it clones/updates, detects the tech stack, and dispatches
  only the analyzers that apply.
- Five specialized reviewers: Java/Spring Boot, AEM Sightly (HTL), EDS blocks, JS/React, CSS/SCSS.
- Each writes a severity-ranked Markdown report + CSV issue tracker to `analysis/` **inside the
  scanned repo**.
- Model tier scales with blast radius: Opus for the Java/Spring Boot backend, Sonnet for AEM
  HTL/EDS/React, Haiku for CSS — plus zero-token deterministic clone/detect/tracker-build steps.
- Two entry points: the `code-scan` **skill** (interactive — asks for URL/branch) or the
  `code-scan` **workflow** (headless — pass `repoUrl`/`branch` as args).

### Usage

Interactive (a human is present to answer "which repo / which branch"):
```
Use the code-scan skill on https://github.com/org/aem-project.git
```
It will ask for the branch, show you the detected stack and which analyzers it plans to run, and
wait for confirmation before spending the analysis budget.

Headless/batch (CI, scheduled runs, scripted sweeps):
```bash
/code-scan --args '{
  "repoUrl": "https://github.com/org/aem-project.git",
  "branch": "main"
}'
```
Or multiple repos in one run:
```bash
/code-scan --args '{
  "repos": [
    { "repoUrl": "https://github.com/org/aem-backend.git", "branch": "main" },
    { "repoUrl": "https://github.com/org/eds-storefront.git", "branch": "main" }
  ]
}'
```
See [examples/code-scan-examples.json](examples/code-scan-examples.json) for more, including
`trustedMode` (skip confirmation gates) and a custom `baseDir`.

Unlike Quality Gate (rule-engine linting, zero AI), `code-scan` runs up to five domain-expert LLM
reviewers — but only the ones whose stack is actually detected in the repo, and each on the model
tier its blast radius warrants.

👉 See [CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md) for the full pipeline, stack-detection rules,
and the complete model-tiering rationale.

---

## Testing & Code Generation (AI-Driven)

🏗️ **AEM Unit Test Cases** (`aem-unit-test-cases`)
- For Adobe AEM Sites backend projects
- Generates high-quality unit tests with 80%+ coverage
- AEM-specific testing patterns (Sling Models, Servlets, Services)
- Framework: JUnit, Mockito, AEM Mocks

🚀 **Spring Boot Unit Test Cases** (`spring-boot-unit-test-cases`)
- For Spring Boot applications
- Generates high-quality unit tests with 80%+ coverage
- Spring Boot-specific testing patterns
- Framework: JUnit, Mockito, Spring Test

The **AEM Unit Test Cases** and **Spring Boot Unit Test Cases** are AI-driven workflows that:

✅ **Token Optimized** - 47% reduction in token usage
✅ **Safe by Default** - Explicit approval gates for setup, generation, and validation
✅ **Trusted Mode Ready** - Optional fast-track for power users (skip gates, keep validation)
✅ **Build-Validated** - Local Maven builds tested before pushing to remote
✅ **Centrally Organized** - Enforces strict repository location
✅ **Production-Ready** - Auto-push to feature branch when validation passes

### Multi-Stage Pipeline
- **Stage 1: Repository Setup** (permission gate) — clone repos to centralized location, create feature branches, validate repo readiness
- **Stage 2: Test Generation** (permission gate) — AEM/Spring Boot Test Case Creator analyzes codebase, generates high-quality unit tests, places tests in `src/test/java/`
- **Stage 3: Local Build Validation** (permission gate) — runs `mvn clean test -pl core -am`, validates all tests pass locally, catches issues before pushing
- **Stage 4: Auto-Push** (NO permission gate) — automatically pushes to `feature/ai-unit-test-cases`, no user intervention needed after validation passes

**Optional Trusted Mode** (for power users): skip all permission gates, faster execution
(1-2 min vs 2-5 min), build validation still runs. Safe for CI/CD and batch operations.
👉 See [Trusted Mode Guide](docs/TRUSTED-MODE-GUIDE.md)

### Basic Invocation

```bash
/aem-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/org/aem-core.git",
      "productionBranch": "main",
      "testCases": "ServiceImpl, UtilsClass, ModelClass"
    }
  ]
}'
```

```bash
/spring-boot-unit-test-cases --args '{
  "testCases": [{
    "repoUrl": "https://github.com/org/spring-app.git",
    "productionBranch": "main",
    "testCases": "UserService, OrderController"
  }]
}'
```

With Trusted Mode:
```bash
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [{
    "repoUrl": "https://github.com/org/aem-core.git",
    "productionBranch": "main",
    "testCases": "ServiceImpl, UtilsClass, ModelClass"
  }]
}'
```

👉 See [WORKFLOWS-COMPARISON.md](docs/WORKFLOWS-COMPARISON.md), [QUICKSTART.md](QUICKSTART.md)

---

## Quality & Compliance (Rule-Driven, Zero AI for Scanning)

📊 **AEM Quality Gate** (`aem-quality-gate`)
- Rule-driven static analysis for AEMaaCS projects
- Enforces Java, Sling, HTL, JavaScript, CSS, and HTML best practices
- **Zero LLM tokens consumed for scanning** — uses deterministic rule engines (PMD, Checkstyle, ESLint, Stylelint)
- Optional AI enhancement for rule tuning only (never re-analyzes code)
- Generates A-E quality ratings per dimension, SonarQube-style

```bash
/aem-quality-gate --args '{
  "repositories": [{
    "repoUrl": "https://github.com/org/aem-project.git",
    "repoName": "my-aem-app",
    "branch": "main"
  }]
}'
```

👉 See [AEM-QUALITY-GATE-GUIDE.md](docs/AEM-QUALITY-GATE-GUIDE.md)

---

## Documentation index

### Code Scanning
- **[CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md)** — Full pipeline, stack-detection rules, and model-tiering rationale

### Test Generation
- **[WORKFLOWS-COMPARISON.md](docs/WORKFLOWS-COMPARISON.md)** — Compare AEM vs Spring Boot agents
- **[TRUSTED-MODE-GUIDE.md](docs/TRUSTED-MODE-GUIDE.md)** — Safe Mode vs Trusted Mode, use cases, and best practices
- **[SPRING-BOOT-WORKFLOW-GUIDE.md](docs/SPRING-BOOT-WORKFLOW-GUIDE.md)** — Spring Boot agent guide
- **[AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md](docs/AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md)** — AEM agent technical guide
- **[AEM-UNIT-TEST-CASES-BEFORE-AFTER.md](docs/AEM-UNIT-TEST-CASES-BEFORE-AFTER.md)** — AEM before/after comparison

### Quality Analysis
- **[AEM-QUALITY-GATE-GUIDE.md](docs/AEM-QUALITY-GATE-GUIDE.md)** — Complete Quality Gate guide, usage, rules, and CI/CD integration
- **[quality-gate/](quality-gate/)** — Quality Gate toolkit directory with rule definitions

### General
- **[QUICKSTART.md](QUICKSTART.md)** — 5-minute walkthrough (currently focused on the test-generation workflows)
- **[CHANGELOG.md](CHANGELOG.md)** — Version history

## File Structure

```
ai-agent/
├── README.md                                          # This file
├── QUICKSTART.md                                      # 5-minute setup guide
├── CHANGELOG.md                                       # Version history
├── workflows/
│   ├── aem-unit-test-cases.js                         # AEM test generation
│   ├── spring-boot-unit-test-cases.js                 # Spring Boot test generation
│   ├── aem-quality-gate.js                            # Quality analysis
│   └── code-scan.js                                   # Multi-agent code scan, headless/batch
├── agents/
│   ├── vbrd-to-proofhub.md                            # VBRD → ProofHub translation
│   ├── code-scan-orchestrator.md                      # Clone/branch/detect router (haiku)
│   ├── java-springboot-analyzer.md                    # Backend security review (opus)
│   ├── aem-htl-analyzer.md                            # HTL/Sightly XSS + authoring review (sonnet)
│   ├── eds-blocks-analyzer.md                         # EDS blocks CWV + DOM review (sonnet)
│   ├── js-react-analyzer.md                           # React correctness/security review (sonnet)
│   └── css-scss-analyzer.md                           # CSS/SCSS architecture review (haiku)
├── skills/
│   └── code-scan/
│       └── SKILL.md                                   # Interactive code-scan entry point
├── scripts/
│   ├── clone_or_update.sh                             # Deterministic clone/checkout/pull
│   ├── detect_stack.sh                                # Deterministic tech-stack detector
│   └── build_issues_csv.py                            # JSON findings → csv tracker (stdlib only)
├── quality-gate/                                      # Quality Gate Toolkit
│   ├── package.json                                   # Frontend tools (ESLint, Stylelint)
│   ├── rules-manifest.json                            # Master rule catalog
│   ├── rules/
│   │   ├── java/                                      # PMD + Checkstyle configs
│   │   ├── frontend/                                  # ESLint, Stylelint, HTMLHint configs
│   │   ├── htl/                                       # HTL validator config
│   │   └── custom/                                    # Custom clientlib checker
│   ├── runner/
│   │   └── run-quality-gate.sh                        # Orchestrates all engines
│   └── aggregator/
│       └── aggregate-report.js                        # Parses outputs into unified report
├── docs/
│   ├── WORKFLOWS-COMPARISON.md                        # AEM vs Spring Boot
│   ├── TRUSTED-MODE-GUIDE.md                          # Safe vs Trusted Mode
│   ├── SPRING-BOOT-WORKFLOW-GUIDE.md                  # Spring Boot guide
│   ├── AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md           # AEM technical deep-dive
│   ├── AEM-UNIT-TEST-CASES-BEFORE-AFTER.md            # AEM before/after
│   ├── AEM-QUALITY-GATE-GUIDE.md                      # Quality Gate complete guide
│   └── CODE-SCAN-GUIDE.md                             # Code-scan pipeline + model tiering
├── examples/
│   ├── sample-config.json                             # AEM test generation examples
│   ├── spring-boot-examples.json                      # Spring Boot test examples
│   ├── quality-gate-examples.json                     # Quality Gate examples
│   └── code-scan-examples.json                        # Code-scan examples
└── repos/                                              # Git-ignored — where scanned/tested repos get cloned
```

## Key Optimizations

### Token Usage (test-generation workflows)
| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Setup prompt | 240 tokens | 80 tokens | 67% |
| Test gen prompt | 320 tokens | 170 tokens | 47% |
| Validation prompt | 180 tokens | 100 tokens | 44% |
| **Per repo total** | **~1,800** | **~950** | **~47%** |

### Token usage (code-scan)
- Clone, branch checkout, stack detection, and CSV tracker generation spend **zero LLM tokens**
  (pure shell/Python, see [CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md)).
- A repo only pays for the analyzer agents whose stack is actually detected in it.
- Model tier scales with blast radius, not file count: Opus only for the backend, Haiku for the
  cheapest-checklist/lowest-severity-ceiling domain (CSS).

### Permission Gates
- User controls expensive operations
- Skip-friendly (marked as skipped, not failed)
- Auto-push when validation passes (test-generation workflows only — `code-scan` never writes to
  the scanned repo's git history, only to its working tree)

## Security Considerations

- ✅ No sensitive data in prompts
- ✅ Permission gates prevent uncontrolled operations (except in explicit Trusted Mode)
- ✅ Build validation catches malicious code issues before push (test-generation workflows)
- ✅ `code-scan` agents never edit application code, create branches, commit, or push — read/report only
- ✅ Feature branches (not main/develop) for any workflow that does push
- ✅ Credentials (ProofHub, etc.) read from environment/`.env`, never hardcoded or logged

## Troubleshooting

### "Permission denied" cloning a repo
Check you have access: `git clone https://github.com/your-org/repo.git`

### `aem-unit-test-cases`/`spring-boot-unit-test-cases`: "Build validation failed"
Check Maven is installed (`mvn --version`) and the repo has a `pom.xml`.

### `aem-quality-gate`: engine not found
Run `cd quality-gate && npm install` once to pull in ESLint/Stylelint/etc.

### `code-scan`: "ready: false" from the orchestrator
The error field names the exact cause (bad URL, branch not found on origin, auth failure) — fix
that specifically rather than retrying blindly.

### `code-scan`: "no applicable stack detected"
This is a real result, not a bug — `scripts/detect_stack.sh` found none of the five known
signatures (Java under `src/main/java`, HTL under `jcr_root/apps`, EDS `blocks/` + boilerplate
signature, `package.json` with `react`, or standalone CSS/SCSS). If you believe it should have
matched, check the repo structure against the rules in
[CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md#stack-detection-rules-scriptsdetect_stacksh).

### "Cannot push to branch"
Check write access: `git push -u origin feature/ai-unit-test-cases`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (for code-scan: `bash -n` the scripts, `python3 -m py_compile` the Python, and
   run `scripts/detect_stack.sh` against a real local checkout before wiring up a new domain)
5. Submit a pull request with a detailed description

## Support

For issues, questions, or feature requests:
- Check the [Documentation index](#documentation-index) above
- Review the [Troubleshooting](#troubleshooting) section
- Check Claude Code logs: `~/.claude/logs/`

## License

[Specify your license here]

---

**Built with ❤️ using Claude Code and Claude API**

For more information about Claude Code, visit: https://github.com/anthropics/claude-code

For Claude API documentation, visit: https://docs.anthropic.com
