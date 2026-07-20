# AEM Development Automation Toolkit

> AI-powered automation for Adobe AEM development with multi-agent code scanning, quality enforcement, performance testing, and intelligent code generation.

A BMAD Method-based toolkit providing 12 specialized AI agents for AEM as a Cloud Service (AEMaaCS), Edge Delivery Services (EDS), Spring Boot, and adjacent stacks. Features token-optimized orchestration, zero-AI security scanning, and deterministic quality gates.

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Available Agents](#available-agents)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Advanced Topics](#advanced-topics)

---

## Quick Start

**Get up and running in 3 steps:**

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/ai-agent.git
cd ai-agent

# 2. Run installation script
./scripts/install-global.sh

# 3. Start using agents (in Claude Code or Cursor)
bmad-help
```

That's it! The installation script sets up all agents for both Claude Code and Cursor/Windsurf IDEs.

---

## Prerequisites

### Required
- **Node.js** 20+ (for quality-gate dependencies)
- **Git** (for repository operations)
- **IDE**: Claude Code *or* Cursor/Windsurf

### Optional (for specific features)
- **Docker** (for security scanning with trivy/hadolint)
- **k6** (for performance testing)
- **Python 3** (for verification scripts)

---

## Installation

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/<your-org>/ai-agent.git
cd ai-agent

# Install quality gate dependencies (one-time)
cd quality-gate && npm install && cd ..

# Install all agents into your IDE
./scripts/install-global.sh
```

> **Note:** If you encounter npm dependency conflicts, delete `quality-gate/node_modules` and `quality-gate/package-lock.json`, then run `npm install` again.

The installation script:
- Copies agent definitions to `_bmad/`
- Registers skills in `.claude/skills/` (for Claude Code)
- Registers skills in `.agents/skills/` (for Cursor/Windsurf)
- Makes all `bmad-*` commands available globally

### 2. Verify Installation

Start a new chat session in your IDE and run:

```
bmad-help
```

You should see context-aware guidance and a list of available skills.

### 3. IDE-Specific Setup

**Claude Code:**
- Skills are automatically discovered from `.claude/skills/`
- Invoke with natural language or `/bmad-*` commands

**Cursor/Windsurf:**
- Skills are automatically discovered from `.agents/skills/`
- Invoke with `@bmad-*` or natural language

---

## Available Agents

### 🔍 Analysis & Discovery

#### **Code Scan Orchestrator** (`bmad-code-scan`)
Multi-agent code scanning with intelligent tech stack detection.

**What it does:**
- Clones repository and detects tech stack (Java, HTL, EDS, JS/CSS, React)
- Dispatches specialized analyzer agents in parallel
- Produces severity-ranked findings (Blocker/Critical/Major/Minor)
- Supports full scan and rescan modes (rescan verifies fixes without new analysis)

**When to use:**
- Initial code review for new repositories
- Pre-merge quality checks
- Post-fix verification (rescan mode)
- Architecture discovery

**Model:** opus (orchestration), sonnet (analyzers)

**Example:**
```
Use bmad-code-scan on https://github.com/org/aem-project.git branch main
```

**Output:** `analysis/findings.json`, `analysis/findings.csv`, `analysis/report.md`

---

#### **Security Scanner** (`bmad-security-scan`)
Zero-AI security scanning with industry-standard tools.

**What it does:**
- Runs semgrep (SAST), gitleaks (secrets), trivy (container), hadolint (Dockerfile), checkov (IaC), nuclei (DAST)
- Generates consolidated security report
- No token usage (deterministic tools only)

**When to use:**
- Pre-deployment security gate
- CI/CD pipeline integration
- Compliance audits
- Secrets detection

**Model:** sonnet (orchestration only, tools are deterministic)

**Example:**
```
Run bmad-security-scan on the current project
```

---

#### **Architecture Documentarian** (`bmad-tech-arch`)
Multi-repository architecture discovery with C4 diagrams.

**What it does:**
- Scans multiple repositories to reconstruct end-to-end architecture
- Generates C4 context, container, and component diagrams
- Documents system integration, API contracts, data flows
- Produces technical architecture document with evidence-based findings

**When to use:**
- Documenting legacy systems
- Client handoff documentation
- Migration planning
- Onboarding new team members

**Model:** opus

**Example:**
```
Generate tech architecture doc for:
- https://github.com/org/frontend.git
- https://github.com/org/backend.git
- https://github.com/org/infrastructure.git
```

---

### ⚡ Quality & Performance

#### **Quality Gate** (`bmad-quality-gate`)
Rule-driven AEM quality enforcement (zero AI).

**What it does:**
- Validates AEM code against 200+ deterministic rules
- Checks HTL, Java, frontend, and OakPAL policies
- Generates pass/fail report with actionable feedback
- No token usage (pure rule engine)

**When to use:**
- PR checks before code review
- CI/CD quality gates
- Policy enforcement
- Onboarding validation

**Model:** None (deterministic rules only)

**Example:**
```bash
cd quality-gate
node runner/run-quality-gate.sh ../repos/my-aem-project
```

---

#### **Performance Tester** (`bmad-perf-test`)
k6-based load and performance testing.

**What it does:**
- Generates k6 test scripts from API specs or manual definitions
- Runs load tests with configurable VUs (virtual users) and duration
- Reports SLA pass/fail against thresholds (p95, error rate)
- Produces performance metrics and recommendations

**When to use:**
- Pre-production load testing
- API performance validation
- Capacity planning
- SLA verification

**Model:** sonnet

**Example:**
```
Run bmad-perf-test on https://api.example.com/products with 50 VUs for 2 minutes
```

---

### 🧪 Testing & Code Generation

#### **AEM Unit Test Generator** (`bmad-unit-test-aem`)
Generates AEM unit tests for Sling Models, servlets, and OSGi components.

**What it does:**
- Scans AEM Java codebase for testable components
- Generates JUnit 5 + Mockito tests with AEM Mocks
- Creates test branch and pushes to remote
- Covers Sling Models, servlets, schedulers, OSGi services

**When to use:**
- Increasing test coverage for AEM projects
- Retroactive test generation for legacy code
- CI/CD test automation

**Model:** sonnet

**Example:**
```
Generate AEM unit tests for repos/dtin-indiafirstlife-commons on branch feature/tests
```

---

#### **Spring Boot Unit Test Generator** (`bmad-unit-test-spring`)
Generates Spring Boot unit and integration tests.

**What it does:**
- Scans Spring Boot codebase for controllers, services, repositories
- Generates JUnit 5 + Mockito + Spring Boot Test tests
- Creates test branch and pushes to remote
- Includes integration tests with @SpringBootTest

**When to use:**
- Increasing test coverage for Spring Boot projects
- Retroactive test generation
- TDD workflow acceleration

**Model:** sonnet

**Example:**
```
Generate Spring Boot tests for repos/backend-apis on branch feature/spring-tests
```

---

### 🔄 Migration & Transformation

#### **WordPress to EDS Migrator** (`bmad-wp-to-eds`)
Migrates WordPress components to AEM Edge Delivery Services.

**What it does:**
- Converts WordPress blocks (Gutenberg/ACF), shortcodes, and template partials
- Generates EDS blocks compatible with Universal Editor (XWalk)
- Produces ESLint/Stylelint-clean, accessible, variant-driven code
- Consolidates similar WP blocks into minimal reusable EDS blocks

**When to use:**
- WordPress to AEM EDS migration
- Content platform modernization
- Universal Editor adoption

**Model:** sonnet

**Example:**
```
Migrate WordPress theme from /wordpress-theme to EDS blocks in /blocks
```

---

#### **VBRD to ProofHub Translator** (`bmad-vbrd-to-proofhub`)
Converts Visual BRD Excel workbooks to ProofHub developer tasks.

**What it does:**
- Parses VBRD Excel (one sheet per section)
- Creates ProofHub tasklists and tasks with Jira-grade tickets
- Generates user stories, requirements, acceptance criteria
- Idempotent sync (updates existing tasks on re-run)

**When to use:**
- Design handoff to development
- Project setup from requirements docs
- ProofHub project automation

**Model:** sonnet

**Example:**
```
Convert /docs/visual-brd.xlsx to ProofHub project "AEM Implementation"
```

---

### 🤖 Specialized Analyzers

These agents are invoked automatically by `bmad-code-scan` based on detected tech stack:

#### **AEM HTL Analyzer**
Reviews HTL templates for AEM-specific issues, component patterns, and accessibility.

#### **Java/Spring Boot Analyzer**
Reviews Java backend code for Spring Boot best practices, security, and performance.

#### **JS/React Analyzer**
Reviews JavaScript and React code for modern patterns, hooks usage, and performance.

#### **CSS/SCSS Analyzer**
Reviews stylesheets for BEM conventions, responsive design, and accessibility.

#### **EDS Blocks Analyzer**
Reviews Edge Delivery Services blocks for decoration patterns and Universal Editor compatibility.

#### **Code Scan Verifier**
Re-checks previously identified findings to determine fix status (Fixed/Open/Partially Fixed).

---

### 📚 Utilities

#### **Help Agent** (`bmad-help`)
Context-aware guidance for the AEM Toolkit.

**What it does:**
- Analyzes current project context
- Recommends next steps based on repo state
- Lists available skills with usage examples
- Provides troubleshooting guidance

**Example:**
```
bmad-help
```

---

## Usage Examples

### Example 1: Full Code Review

```
Use bmad-code-scan on https://github.com/org/aem-project.git branch develop
```

**What happens:**
1. Clones repository to `repos/aem-project/`
2. Detects tech stack: Java + HTL + CSS
3. Dispatches Java, HTL, and CSS analyzers in parallel
4. Generates `analysis/findings.json`, `analysis/findings.csv`, `analysis/report.md`

---

### Example 2: Fix Verification (Rescan)

After fixing issues from a previous scan:

```
Rescan https://github.com/org/aem-project.git to verify fixes
```

**What happens:**
1. Reads existing `analysis/findings.json`
2. Re-checks only files with known findings
3. Updates status: Fixed/Open/Partially Fixed
4. Generates `analysis/rescan-summary.md`

---

### Example 3: Multi-Repo Architecture Documentation

```
Run bmad-tech-arch for:
- https://github.com/org/frontend.git branch main
- https://github.com/org/backend.git branch main
- https://github.com/org/infrastructure.git branch main
```

**What happens:**
1. Clones all three repositories
2. Analyzes dependencies, APIs, and integration points
3. Generates C4 diagrams (context, container, component)
4. Produces technical architecture document in `output/tech-architecture/`

---

### Example 4: Pre-Deployment Security Scan

```
Run bmad-security-scan on repos/aem-project before deployment
```

**What happens:**
1. Runs semgrep (SAST), gitleaks (secrets), trivy (containers)
2. Generates consolidated security report
3. Returns pass/fail verdict with remediation steps

---

### Example 5: Load Testing

```
Run bmad-perf-test on https://api.example.com:
- Endpoint: /api/products
- 100 VUs
- 5 minutes
- Threshold: p95 < 500ms, error rate < 1%
```

**What happens:**
1. Generates k6 test script
2. Runs load test with 100 virtual users for 5 minutes
3. Reports SLA pass/fail
4. Provides performance recommendations

---

## Project Structure

```
ai-agent/
├── _bmad/                      # BMAD Method structure (runtime)
│   ├── config/
│   │   ├── module.yaml         # Module manifest
│   │   └── module-help.csv     # Help lookup table
│   ├── agents/                 # Agent persona files (12 agents)
│   ├── skills/                 # Invokable workflows (10 skills)
│   ├── tasks/                  # Reusable operations (5 tasks)
│   ├── checklists/             # Severity tables (loaded on-demand)
│   └── templates/              # Output templates
│
├── .claude/skills/             # Claude Code launchers
├── .agents/skills/             # Cursor/Windsurf launchers
│
├── scripts/                    # Installation & utility scripts
│   ├── install-global.sh       # Main installer
│   ├── clone_or_update.sh      # Repo cloning
│   ├── detect_stack.sh         # Tech stack detection
│   ├── security-scan/          # Security tool wrappers
│   └── perf-test/              # k6 test runners
│
├── quality-gate/               # AEM quality gate rules
│   ├── rules/                  # Rule definitions
│   │   ├── htl/
│   │   ├── java/
│   │   ├── frontend/
│   │   └── custom/
│   ├── runner/
│   │   └── run-quality-gate.sh
│   └── aggregator/
│       └── aggregate-report.js
│
├── docs/                       # Detailed guides
│   ├── CODE-SCAN-GUIDE.md
│   ├── SECURITY-SCAN-GUIDE.md
│   ├── PERF-TEST-GUIDE.md
│   ├── AEM-QUALITY-GATE-GUIDE.md
│   └── SPRING-BOOT-WORKFLOW-GUIDE.md
│
├── examples/                   # Usage examples & sample outputs
├── repos/                      # Cloned repositories (gitignored)
├── output/                     # Generated artifacts
│
└── README.md                   # This file
```

### Key Directories

**`_bmad/`** - Core agent runtime
- `agents/`: Token-optimized persona files (~50 lines each)
- `skills/`: Invokable SKILL.md workflows
- `checklists/`: On-demand loaded severity tables (60% token savings)

**`.claude/skills/` & `.agents/skills/`** - IDE integrations
- Launcher files that reference `_bmad/skills/`
- Enable `bmad-*` command discovery

**`scripts/`** - Zero-dependency automation
- Shell scripts for deterministic operations (clone, detect, install)
- No AI tokens used for these operations

**`quality-gate/`** - Deterministic rule engine
- 200+ AEM-specific rules (HTL, Java, frontend, OakPAL)
- Pure JavaScript rule evaluation (no AI)

---

## Advanced Topics

### Token Optimization

The BMAD Method structure achieves ~60% token reduction at orchestration time:

1. **Checklists loaded on-demand**: Severity tables only loaded when analyzer runs
2. **Persona separation**: Small persona files for routing, detailed checklists for execution
3. **Model split**: opus for planning, sonnet for execution
4. **Deterministic tools**: Clone, detect, quality gate use zero tokens

### IDE Compatibility

**Both Claude Code and Cursor/Windsurf supported:**

```bash
# Installation creates launchers for both IDEs
./scripts/install-global.sh

# Claude Code: .claude/skills/
# Cursor/Windsurf: .agents/skills/
```

Skills work identically across both IDEs.

### Rescan Mode

After fixing code issues, use rescan mode to verify fixes without full re-analysis:

```
Rescan https://github.com/org/repo.git
```

**Benefits:**
- 10x faster than full scan (only checks files with known findings)
- Updates finding status in same JSON/CSV (no duplicates)
- Generates comparison report (Fixed/Open/Partially Fixed)

### Custom Rules

Add custom quality gate rules:

```bash
# Create custom rule
cat > quality-gate/rules/custom/my-rule.js << 'EOF'
module.exports = {
  name: 'no-hardcoded-author',
  severity: 'major',
  check: (content, filepath) => {
    if (/author\./.test(content)) {
      return { fail: true, message: 'Avoid hardcoded author references' };
    }
    return { fail: false };
  }
};
EOF

# Run quality gate
node quality-gate/runner/run-quality-gate.sh repos/my-project
```

### CI/CD Integration

Run agents in CI pipelines:

```yaml
# .github/workflows/quality-check.yml
name: Quality Check
on: [pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Quality Gate
        run: |
          cd quality-gate && npm install
          node runner/run-quality-gate.sh ..
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: quality-report
          path: quality-gate/report.json
```

### Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Support

- **Issues**: [GitHub Issues](https://github.com/org/ai-agent/issues)
- **Docs**: See `docs/` folder for detailed guides
- **Examples**: See `examples/` folder for sample outputs

---

## License

[Your License Here]

---

## Credits

Built with the BMAD Method for modular AI-agent orchestration.

- **Token Optimization**: On-demand checklist loading
- **Model Strategy**: opus (planning) + sonnet (execution)  
- **Zero-AI Tools**: Deterministic clone/detect/quality-gate operations
- **IDE Agnostic**: Claude Code + Cursor/Windsurf support

### Agents (`agents/*.md`)

Standalone Claude Code subagent definitions. Each is invoked either directly (Task/Agent tool,
by its `name:` frontmatter) or as the `agentType` a workflow script dispatches to.

| Agent | Model | Tools | What it does |
|---|---|---|---|
| `code-scan-orchestrator` | Opus | Read, Bash, Grep, Glob | Clones/updates a repo+branch, runs deterministic tech-stack detection, and checks for a prior `analysis/` folder; returns which analyzer agents apply and whether a cheap rescan is possible. No code review. |
| `code-scan-verifier` | Sonnet | Read, Grep, Glob, Bash, Write | Rescan only: re-checks a batch of findings from a previous scan against the current code and returns Fixed/Open/Partially Fixed/Not Applicable/Unverifiable per issue. Doesn't hunt for new issues. |
| `java-springboot-analyzer` | Sonnet | Read, Grep, Glob, Bash, Write | Backend security-first review: injection, auth, secrets, concurrency, N+1 queries, resource leaks. |
| `aem-htl-analyzer` | Sonnet | Read, Grep, Glob, Bash, Write | AEM Sightly/HTL templates: XSS context handling, Sling Model binding, authoring/edit-mode behavior. |
| `eds-blocks-analyzer` | Sonnet | Read, Grep, Glob, Bash, Write | Edge Delivery Services blocks: Core Web Vitals, DOM-first patterns, vanilla JS conventions. |
| `js-react-analyzer` | Sonnet | Read, Grep, Glob, Bash, Write | React/JS: correctness, XSS, hooks misuse, performance, architecture. |
| `css-scss-analyzer` | Sonnet | Read, Grep, Glob, Bash, Write | CSS/SCSS: specificity, architecture, accessibility, performance. |
| `vbrd-to-proofhub` | Sonnet | Read, Write, Edit, Bash, Grep, Glob, WebFetch | Translates a Visual BRD Excel workbook into Jira-grade ProofHub tasklists/tasks (idempotent sync keyed on Component ID). |
| `tech-architecture-doc` | Opus | Read, Write, Edit, Bash, Grep, Glob, WebFetch | Asks which repos + branches make up a client platform, then reconstructs the **cross-repo** architecture from source and writes an evidence-based Technical Architecture Document (C4 context/container/component, integration, sequence, deployment, security, data-flow, column-level database schema (ER), CI/CD diagrams + risks + target state). Database schema is extracted from actual DDL/migrations when present, or ORM entity mappings (JPA/Hibernate, Django, SQLAlchemy, TypeORM, EF Core, GORM, etc.) otherwise — technology-agnostic, never a generic template. Stack is discovered, never assumed. |
| `wp-to-eds-migrator` | Sonnet | Read, Write, Edit, Bash, Grep, Glob, WebFetch | Migrates WordPress theme components (Gutenberg/ACF blocks, shortcodes, template partials) into AEM Edge Delivery Services blocks authorable in Universal Editor (XWalk model-driven authoring). Consolidates similar WP blocks into a minimal, variant-driven set — never mechanical 1:1 copies. |

The five analyzer agents (`java-springboot-analyzer` through `css-scss-analyzer`) plus
`code-scan-verifier` are dispatched by the `code-scan` skill/workflow below — you rarely invoke
them standalone, though you can.

`vbrd-to-proofhub`, `tech-architecture-doc`, and `wp-to-eds-migrator` are **standalone** —
invoked directly by name, not dispatched by any workflow. They install to `~/.claude` (see
[install-standalone-agents.sh](#2-wiring-it-into-claude-code--making-it-invokable-from-anywhere))
so they work from any directory, not just repos nested under `project-source/`.

**`tech-architecture-doc` vs `code-scan`:** `code-scan` reviews ONE repo for code defects and
writes findings into that repo's `analysis/`. `tech-architecture-doc` reviews the **joins
between several repos** (which consumer calls which gateway route which service which table)
and writes a document. Different question, different output — they compose well: scan for
defects, document for architecture.

### Model policy (global)

- Planning/orchestration uses Opus.
- Execution/review/generation uses Sonnet.
- Token optimization is achieved through strict scope control, deterministic pre-processing scripts, and schema-constrained outputs (not by downgrading execution model quality).

### Workflows (`workflows/*.js`)

Scripts for Claude Code's Workflow tool (multi-stage pipelines with permission gates). Each is
runnable as a slash command with a JSON `--args` payload.

| Workflow | Invocation | What it does |
|---|---|---|
| `code-scan` | `/code-scan --args '{...}'` | Clone/update → detect stack → dispatch only the matching analyzer agents, in parallel. If the repo already has an `analysis/` folder, rescans instead: re-verifies the known findings and writes fix status back to the same JSON/CSV (`mode`: `auto`\|`full`\|`rescan`). Headless counterpart to the `code-scan` skill. |
| `aem-unit-test-cases` | `/aem-unit-test-cases --args '{...}'` | Clone → generate JUnit/Mockito/AEM-Mocks unit tests targeting 80%+ coverage → local Maven build validation → auto-push to a feature branch. |
| `spring-boot-unit-test-cases` | `/spring-boot-unit-test-cases --args '{...}'` | Same pipeline shape as above, tuned for Spring Boot (JUnit/Mockito/Spring Test). |
| `aem-quality-gate` | `/aem-quality-gate --args '{...}'` | Rule-driven static analysis — PMD, Checkstyle, ESLint, Stylelint, custom clientlib checks. **Zero LLM tokens for scanning**; optional AI pass only tunes rule thresholds afterward. |

### Skills (`skills/*/SKILL.md`)

Interactive entry points — loaded into the main conversation so they can ask follow-up questions,
unlike workflows/agents which run as a single dispatched task.

| Skill | What it does |
|---|---|
| `code-scan` | Asks for a GitHub URL (clones if not already present locally), asks for a branch (checks it out, pulls latest), shows the detected stack for confirmation, then dispatches only the applicable analyzer agents. On a repo that's been scanned before, offers a rescan instead — re-check the known findings and update their fix status in the same tracker. |

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
| `python3` | `code-scan`'s CSV tracker, rescan planning + status merge | preinstalled on macOS/Linux — **stdlib only, nothing to `pip install`** |
| `mvn` (Maven) | `aem-unit-test-cases`, `spring-boot-unit-test-cases` build validation | required only if you use those two workflows |
| `node` + `npm` | `aem-quality-gate` | run `cd quality-gate && npm install` once |
| ProofHub API access | `vbrd-to-proofhub` only | set `PROOFHUB_BASE_URL`, `PROOFHUB_API_KEY`, `PROOFHUB_USER_AGENT` in your environment or a local `.env` — never hardcode these in a prompt or commit them |

Nothing here needs a database, a server, or network services beyond git/GitHub and (for
`vbrd-to-proofhub`) the ProofHub API.

### 2. Wiring it into Claude Code — making it invokable from anywhere

Claude Code discovers agents/workflows/skills by walking **up** from your current directory
looking for `.claude/agents`, `.claude/workflows`, `.claude/skills` (merged with whatever's in
`~/.claude`, which is truly global). This repo keeps its source of truth at the **repo root**
(`agents/`, `workflows/`, `skills/`) so the toolkit is easy to browse/diff/version as one unit —
but that root isn't itself on Claude Code's discovery path, so it needs to be installed into a
`.claude/` directory that *is*.

**Recommended: install into the nearest shared parent directory of your projects.** If you keep
client/project repos under a common folder (e.g. `~/Documents/project-source/projects/<repo>`),
put a `.claude/` at that shared parent (`~/Documents/project-source/.claude/`) — every repo
nested under it then sees the same agents/workflows/skills with zero per-project setup. This is
exactly how every other custom agent in this environment already works (`aem-test-case-creator`,
`eds-block-creator`, `spring-boot-test-creator`, … all live in that shared `.claude/`, not inside
any single project).

Run the installer, which copies the code-scan pieces there (default target shown; pass a
different path as `$1` to install elsewhere, e.g. `~/.claude` for truly machine-wide):

```bash
./scripts/install-global.sh
# or: ./scripts/install-global.sh /path/to/shared/.claude
```

It copies (not symlinks — matching this environment's existing convention) the 5 analyzer agents,
the `code-scan-orchestrator` router agent, `workflows/code-scan.js`, and `skills/code-scan/`.
**Re-run it after editing anything under `agents/`, `workflows/`, or `skills/`** — installed
copies don't auto-update. A new Claude Code session started from any nested directory then has
`code-scan` available immediately (existing sessions pick up new skills without a restart in most
builds; agents/workflows are read at session start, so start a fresh session to see those).

The five analyzer agents shell out to `<ai-agent-repo>/scripts/*.sh` and `build_issues_csv.py` via
an explicit path passed at invocation time (see each agent's "Input contract" / the
`ai-agent-repo` argument) — so the installed copies keep working correctly no matter where the
*scanned* repo lives, as long as this toolkit repo itself stays at a stable path.

**Standalone agents install machine-wide instead.** `vbrd-to-proofhub`, `tech-architecture-doc`,
and `wp-to-eds-migrator` aren't part of the code-scan system and are used from repos that don't
live under `project-source/` (e.g. `ai-initiative/presales`, client repos in arbitrary
locations). `project-source/.claude` wouldn't cover those, so they go to `~/.claude` — the one
directory Claude Code merges in regardless of cwd:

```bash
./scripts/install-standalone-agents.sh
# or: ./scripts/install-standalone-agents.sh /path/to/some/.claude
```

Same rules as above: it copies, and installed copies don't auto-update — **re-run it after
editing `agents/tech-architecture-doc.md`, `agents/vbrd-to-proofhub.md`, or
`agents/wp-to-eds-migrator.md`** — then start a fresh session (agents are read at session start).
`tech-architecture-doc` takes the same `aiAgentRepo` argument as the analyzers so its installed
copy can find `scripts/clone_or_update.sh` and `scripts/detect_stack.sh`.

If you'd rather work from inside this repo directly instead of installing anywhere: `cd ai-agent
&& claude`, then invoke by name (`/code-scan`, or ask for the skill in conversation) — no install
needed, but only works from this directory.

### 3. Where things get cloned

Every workflow here clones target repos to a predictable, git-ignored location instead of
scattering them across the filesystem:

| Workflow | Default clone location | Override |
|---|---|---|
| `aem-unit-test-cases`, `spring-boot-unit-test-cases`, `aem-quality-gate` | `/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos` | `args.baseDir` |
| `code-scan` (skill or workflow) | `<this-repo>/repos` | `args.baseDir` (workflow) or say a different location when the skill asks |
| `tech-architecture-doc` (agent) | `<this-repo>/repos` — reuses `clone_or_update.sh`, so several client repos land side by side | `baseDir` input, or point it at existing local clones |

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

  A **rescan** (the default on a repo that already has `analysis/`) writes no new report. It
  updates `-findings.json` and `-issues.csv` **in place**, adding a `Status` column
  (Open/Fixed/Partially Fixed/Not Applicable/Unverifiable) plus the evidence and commit
  provenance behind each verdict, and adds:
  ```
  <repoPath>/analysis/
    rescan-summary.md    # cross-domain status table, regressions, still-open list
    .verify/             # batch plan + per-batch verdicts (audit trail)
  ```
- **Tech Architecture Doc** (`tech-architecture-doc`): spans several repos, so its output can't
  live inside any one of them. Defaults to `<this-repo>/output/tech-architecture/<client-slug>/`
  (**git-ignored** — these are client-confidential deliverables; never commit them here).
  Override via the `outDir` input — presales engagements usually point it at
  `~/Documents/Projects/ai-initiative/presales-doc/tech-architecture/<client-slug>/`, matching
  that repo's convention for generated artefacts. Contents:
  ```
  <outDir>/
    technical-architecture.md   # the document (diagrams embedded)
    evidence-register.csv       # every finding → repo, commit, file path, confidence
    unresolved.md               # references that never resolved (usually external systems)
    inventory/                  # repos · endpoints · consumer-calls · integrations · tables (.tsv)
    diagrams/                   # *.mmd sources + rendered *.svg
  ```
  `evidence-register.csv` is the source of truth: every arrow on every diagram is a row in it.

## Choosing which one to run

**Want unit tests written for an AEM or Spring Boot backend?** → `aem-unit-test-cases` /
`spring-boot-unit-test-cases` (below)

**Want a fast, zero-AI lint/quality gate on an AEMaaCS repo?** → `aem-quality-gate`

**Want a deep, security-first code review (Java/Spring Boot, AEM HTL, EDS, React, or CSS —
whichever the repo actually contains)?** → `code-scan`

**Need an evidence-based technical architecture document across multiple repos?** →
`tech-architecture-doc` (invoke the agent directly; it reconstructs cross-repo integrations,
diagrams, and deployment/integration flows)

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
- Point it at the same repo later and it **rescans** instead: re-checks the findings already on
  record against the current code and writes each one's fix status back into the same JSON/CSV.
- Model policy is fixed: Opus for planning/routing, Sonnet for execution analyzers — plus
  zero-token deterministic clone/detect/plan/tracker/summary steps.
- Two entry points: the `code-scan` **skill** (interactive — asks for URL/branch) or the
  `code-scan` **workflow** (headless — pass `repoUrl`/`branch` as args).

### Two modes

| | Full scan | Rescan |
|---|---|---|
| Answers | "What's wrong with this code?" | "Which known issues are fixed?" |
| Runs when | No `analysis/` folder yet, or `mode:"full"` | `analysis/` already there (the default then) |
| Reads | Every in-scope file | Only files carrying a known finding — much cheaper |
| Finds new issues | Yes | **No** — that's the trade |
| Writes | Report + findings JSON + CSV | Status into the *same* JSON + CSV, in place |

`mode` defaults to `auto` and picks for you. Force `mode:"full"` after a release or a big merge,
where a rescan would faithfully verify the old findings while missing everything the new code
introduced.

### Usage

Interactive (a human is present to answer "which repo / which branch"):
```
Use the code-scan skill on https://github.com/org/aem-project.git
```
It will ask for the branch, show you the detected stack and which analyzers it plans to run, and
wait for confirmation before spending the analysis budget. On a repo it has scanned before, it
offers the rescan instead — and tells you how many findings are pending.

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
Rescan a repo you've already scanned — re-check the known findings and update their status in the
same tracker:
```bash
/code-scan --args '{
  "mode": "rescan",
  "repoUrl": "https://github.com/org/aem-project.git",
  "branch": "main"
}'
```

See [examples/code-scan-examples.json](examples/code-scan-examples.json) for more, including
`trustedMode` (skip confirmation gates), `recheckFixed` (re-verify already-fixed issues to catch
regressions), `batchSize`, and a custom `baseDir`.

Unlike Quality Gate (rule-engine linting, zero AI), `code-scan` runs up to five domain-expert LLM
reviewers — but only the ones whose stack is actually detected in the repo, and each on the model
tier its blast radius warrants.

👉 See [CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md) for the full pipeline, stack-detection rules,
rescan statuses and design constraints, and the complete model-tiering rationale.

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
- **[CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md)** — Full pipeline, stack-detection rules, and model policy rationale

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
│   ├── tech-architecture-doc.md                       # Multi-repo architecture doc + diagrams (opus)
│   ├── vbrd-to-proofhub.md                            # VBRD → ProofHub translation
│   ├── code-scan-orchestrator.md                      # Clone/branch/detect router (opus planning)
│   ├── java-springboot-analyzer.md                    # Backend security review (sonnet execution)
│   ├── aem-htl-analyzer.md                            # HTL/Sightly XSS + authoring review (sonnet)
│   ├── eds-blocks-analyzer.md                         # EDS blocks CWV + DOM review (sonnet)
│   ├── js-react-analyzer.md                           # React correctness/security review (sonnet)
│   ├── css-scss-analyzer.md                           # CSS/SCSS architecture review (sonnet)
│   └── wp-to-eds-migrator.md                          # WordPress → AEM EDS block migration (sonnet)
├── skills/
│   └── code-scan/
│       └── SKILL.md                                   # Interactive code-scan entry point
├── scripts/
│   ├── clone_or_update.sh                             # Deterministic clone/checkout/pull
│   ├── detect_stack.sh                                # Deterministic tech-stack detector
│   ├── build_issues_csv.py                            # JSON findings → csv tracker (stdlib only)
│   ├── install-global.sh                              # Installs code-scan into a shared .claude/ dir
│   └── install-standalone-agents.sh                   # Installs standalone agents into ~/.claude
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
│   └── CODE-SCAN-GUIDE.md                             # Code-scan pipeline + model policy
├── examples/
│   ├── sample-config.json                             # AEM test generation examples
│   ├── spring-boot-examples.json                      # Spring Boot test examples
│   ├── quality-gate-examples.json                     # Quality Gate examples
│   └── code-scan-examples.json                        # Code-scan examples
├── repos/                                              # Git-ignored — where scanned/tested repos get cloned
└── output/                                             # Git-ignored — tech-architecture-doc deliverables
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
- Model policy is deterministic: Opus for planning/orchestration, Sonnet for execution/review.

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
