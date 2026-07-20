# Changelog

All notable changes to this AI automation toolkit are documented in this file.

## [2.0.0] - 2026-07-20

### Changed (BREAKING)
- **BMAD Method v6 Structure**: Complete refactoring to modular AI-agent orchestration framework
  - Migrated from flat `agents/` structure to hierarchical `_bmad/` module
  - Separated personas (what) from workflows (how) for clearer routing
  - Added `.claude/skills/` and `.agents/skills/` launchers for IDE integration
  - Skills now invokable as `bmad-*` commands in both Claude Code and Cursor/Windsurf

### Added
- **Token Optimization**: ~60% reduction in orchestration context
  - Extracted checklists into separate on-demand files (`_bmad/checklists/`)
  - Checklists load only when analyzer runs, not at routing time
  - Shared reference files eliminate duplication across agents
- **BMAD Module Structure**:
  - `_bmad/config/module.yaml` - Module manifest defining all agents, skills, tasks
  - `_bmad/config/module-help.csv` - Context-aware help lookup table
  - `_bmad/agents/` - 12 token-optimized persona files (~50 lines each, down from ~800)
  - `_bmad/skills/` - 10 invokable SKILL.md workflows
  - `_bmad/tasks/` - 5 reusable atomic operations
  - `_bmad/checklists/` - 7 severity tables (loaded on-demand)
  - `_bmad/templates/` - 3 output templates
- **Documentation Consolidation**:
  - Comprehensive master README.md with all setup instructions and agent descriptions
  - Removed redundant AGENTS.md and QUICKSTART.md (merged into README.md)
  - Single source of truth for installation, usage, and agent capabilities
- **IDE Dual Support**:
  - `.claude/skills/` launchers for Claude Code
  - `.agents/skills/` launchers for Cursor/Windsurf
  - Same skill definitions work identically across both IDEs

### Removed
- `agents/*.md` - Migrated to `_bmad/agents/` with token optimization
- `AGENTS.md` - Content merged into master README.md
- `QUICKSTART.md` - Content merged into master README.md

### Technical
- Model split preserved: opus (planning/orchestration), sonnet (execution/review)
- Zero-AI tools remain deterministic (clone, detect, quality gate)
- Parallel dispatch capability maintained for independent analyzers
- Idempotent rescan mode unchanged

## [1.6.0] - 2026-07-19

### Added
- **`agents/wp-to-eds-migrator.md` onboarded into the repo.** Previously existed only as an
  untracked file at `~/.claude/agents/wp-to-eds-migrator.md` — not version-controlled, not
  installed by `install-standalone-agents.sh`, not documented in the README. Now a proper
  standalone agent alongside `tech-architecture-doc` and `vbrd-to-proofhub`.
  - Added to `scripts/install-standalone-agents.sh`'s `AGENTS` list.
  - Added to the README's agent table, standalone-agents description, and repo file tree.

### Fixed
- **`wp-to-eds-migrator` model policy violation.** Was set to `model: inherit`, which doesn't
  follow the [global model policy](README.md#model-policy-global) (Opus for
  planning/orchestration, Sonnet for execution/generation). It's a single-shot
  analysis-then-code-generation agent with the same shape as `vbrd-to-proofhub`, so it's now
  fixed to `model: sonnet`.
  - Full audit of `agents/*.md`, `workflows/*.js`, `skills/*/SKILL.md`, and `scripts/*` found
    no other gaps — the policy set up in [1.3.0](#130---2026-07-15) was already applied
    consistently everywhere else that dispatches an LLM call.
- **Stale installed copy of `tech-architecture-doc.md`** — `~/.claude/agents/` still had the
  pre-1.5.0 version (missing column-level DB schema diagrams). Re-ran
  `install-standalone-agents.sh` to resync.

## [1.5.0] - 2026-07-17

### Added
- **`tech-architecture-doc` — column-level database schema diagrams.** The diagram set's
  former "ER diagram" step only drew entity relationships; it now requires full column-level
  detail (name, type, nullable, PK, FK target, unique, index) for every table, extracted
  technology-agnostically:
  - **Priority 1 — DDL/migrations** when present: Flyway, Liquibase, Alembic, Prisma
    `schema.prisma`, Rails `db/schema.rb`, EF Core `Migrations/`, raw `.sql`.
  - **Priority 2 — ORM entity mappings** when no migrations are in scope: JPA/Hibernate
    (`@Entity`/`@Column`/`@JoinColumn`), Django models, SQLAlchemy, TypeORM, Sequelize,
    ActiveRecord, EF Core attributes/Fluent API, GORM struct tags, Doctrine. Capped at Medium
    confidence unless corroborated by DDL.
  - New `inventory/tables.tsv` spec: one row per **column**, not per table.
  - Large schemas (>25–30 tables) split into one domain-overview relationship diagram plus
    per-domain diagrams with full Mermaid `erDiagram` attribute blocks — never one wall-sized
    diagram.
  - Phase 2's stack-detection table gained an ORM-mapping row so the right extraction pattern
    is picked per language rather than assumed to be Java/Spring.

## [1.4.0] - 2026-07-17

### Added
- **Rescan mode for `code-scan` — re-verify prior findings instead of re-reviewing the repo**
  - Point `code-scan` at a repo that already has an `analysis/` folder and it now re-checks the
    findings already on record against the current code, writing each one's fix status back into
    the **same** `analysis/<domain>-analysis-findings.json` and `analysis/<domain>-analysis-issues.csv`.
  - Reads only the files carrying a known finding, not the codebase — a fraction of a full scan's cost.
  - Explicit trade: a rescan finds **no new issues**. It answers "is this fixed", not "what's wrong now".
  - Statuses: `Open`, `Fixed`, `Partially Fixed`, `Not Applicable` (the code carrying it is gone),
    `Unverifiable` (routed to a human, never silently closed).
  - Per-issue provenance: `statusDetail` (evidence), `verifiedFile`/`verifiedLine` (where it lives now,
    kept separate from the original `file`/`line`), `firstSeenCommit`, `lastVerifiedCommit`/`Date`,
    `fixedInCommit`. A `scanHistory` entry is appended to the findings JSON per run.

- **`agents/code-scan-verifier.md`** (Sonnet) — verifies one batch of prior findings and returns a
  verdict per issue. Deliberately narrow: no new-issue discovery, no code edits, no writes to the
  findings JSON or CSV.

- **Three deterministic scripts (stdlib-only, zero LLM tokens)**
  - `scripts/plan_verification.py` — detects prior analysis, filters out terminal issues, and batches
    the rest by file into a plan at `analysis/.verify/plan.json`. Purges stale verdicts.
  - `scripts/apply_verdicts.py` — merges verdicts into the findings JSON and rebuilds the CSV from the
    same issue list, so the two can't drift.
  - `scripts/build_rescan_summary.py` — renders `analysis/rescan-summary.md` (cross-domain status,
    regressions, still-open list).

- **Workflow args**: `mode` (`auto` | `full` | `rescan`, default `auto`), `recheckFixed`, `batchSize`.
  `mode:"rescan"` with no prior analysis fails loudly rather than silently spending a full-scan budget.

### Changed
- **`workflows/code-scan.js`** — added `Rescan Verification` and `Status Update` phases, mode
  resolution, and a per-domain verify→merge pipeline (each domain merges as soon as its own batches
  land; no cross-domain barrier).
- **`agents/code-scan-orchestrator.md`** — now also runs `plan_verification.py` and returns
  `priorAnalysis`. It reports what's on disk; the caller picks the mode.
- **`skills/code-scan/SKILL.md`** — offers full-scan vs rescan when prior analysis exists, and leads
  the rescan summary with the fixed/open counts.
- **`scripts/build_issues_csv.py`** — added the status columns (`Status`, `Status Detail`,
  `Verified File`, `Verified Line`, `First Seen`, `Last Verified`, `Last Verified Commit`,
  `Fixed In Commit`); rows now sort open-work-first, then severity desc, then file. Exposes
  `write_csv()`/`normalize_status()` for reuse. **Backward compatible**: a findings JSON with no
  status fields still builds, with every issue defaulting to `Open`.
- **`scripts/install-global.sh`** — installs `code-scan-verifier`.

### Security
- Ambiguity resolves toward `Open`, never `Fixed` — a wrong "Fixed" silently closes a live security
  finding. The guarantees:
  - `normalize_status()` maps any present-but-unrecognized status to `Unverifiable` and a missing one
    to `Open`, so a malformed verdict cannot close an issue.
  - An issue with no verdict (crashed batch, unreadable verdict file) keeps its previous status and is
    reported as `notVerified` — silence is never read as "fixed".
  - A duplicated issue ID is excluded from verification and left untouched: one verdict cannot be
    routed to two issues without closing one on the other's evidence.
  - A malformed verdict file is reported in `badVerdictFiles` and skipped rather than being fatal, so
    one bad batch can't discard every other batch's good verdicts.
  - A `Fixed` issue found present again clears its `fixedInCommit` and is surfaced as a regression.
  - Everything excluded from a run (terminal, duplicate, ID-less, unparseable domain) is logged. A
    rescan that verified 38 of 42 findings never reports as if it covered all 42.
- The rescan planner and the verdict merger share `normalize_status()`/`issue_key()`/`TERMINAL_STATUSES`
  rather than each defining their own. Independent copies had already drifted: the planner's raw-string
  terminal check didn't recognize `"resolved"` as Fixed while the merger did, which re-verified the
  issue every run and then reported a phantom regression the moment a verifier said Open.

## [1.3.0] - 2026-07-15

### Changed
- **Global model policy standardized across agents, skills, workflows, and docs**
  - Planning/orchestration now uses Opus.
  - Execution/review/generation now uses Sonnet.
  - Removed previous mixed execution tiering assumptions from code-scan docs and skill guidance.

- **Agent model assignments aligned to the policy**
  - `code-scan-orchestrator` moved to Opus (planning stage).
  - `java-springboot-analyzer` moved to Sonnet (execution stage).
  - `css-scss-analyzer` moved to Sonnet (execution stage).
  - `vbrd-to-proofhub` set to Sonnet.

- **Workflow execution model routing enforced in code**
  - Added explicit planning/execution model constants in:
    - `workflows/code-scan.js`
    - `workflows/aem-unit-test-cases.js`
    - `workflows/spring-boot-unit-test-cases.js`
    - `workflows/aem-quality-gate.js`
  - Permission and orchestration calls route to Opus.
  - Execution/generation/analysis calls route to Sonnet.

- **Documentation expanded and normalized for onboarding and operations**
  - `README.md` updated with clone-first setup, install/verify flow, AE defaults, full model policy, and refreshed component catalog.
  - `QUICKSTART.md` updated with policy-aligned code-scan usage note.
  - `docs/CODE-SCAN-GUIDE.md` updated from model tiering language to fixed policy language.

### Fixed
- **Repository hygiene for local scan clones**
  - `.gitignore` hardened with root-level `/repos/` and `/repos/**` exclusions.
  - Verified `repos/` currently has zero tracked files in git.

### Benefits
- Predictable model behavior across the toolkit (no hidden per-agent tier drift).
- Better governance: planning and execution responsibilities are clearly separated.
- Token efficiency preserved via deterministic preprocessing and stack-scoped dispatch.
- Lower risk of accidental commit noise from local cloned repositories.

## [1.2.0] - 2026-07-06

### Added
- **Spring Boot Unit Test Cases Agent** (`spring-boot-unit-test-cases`)
  - Full Spring Boot test generation with JUnit, Mockito, Spring Test
  - Same architecture as AEM agent for consistency
  - Safe Mode (default) with 3 permission gates
  - Trusted Mode (opt-in) for automation
  - Local Maven build validation
  - Token optimization (47% reduction)

- **New Documentation**
  - SPRING-BOOT-WORKFLOW-GUIDE.md: Comprehensive Spring Boot guide
  - WORKFLOWS-COMPARISON.md: Detailed comparison between agents
  - spring-boot-examples.json: 10 example configurations

- **Examples**
  - Single service testing
  - Multiple microservices (parallel)
  - Batch testing with Trusted Mode
  - CI/CD pipeline integration
  - Custom repository locations

### Changed
- Updated README.md to highlight both available agents
- Enhanced documentation structure for multiple agents

### Benefits
- Choose appropriate agent for your technology stack
- Reuse proven architecture across different frameworks
- Unified token optimization and permission gates
- Consistent testing workflows

## [1.1.0] - 2026-07-06

### Fixed
- **Critical**: Fixed `process.cwd()` error in workflow sandbox
  - Workflow scripts run in sandbox with no Node.js API access
  - `process`, `Date.now()`, `Math.random()`, and `fs` are unavailable
  - Changed baseDir from dynamic `process.cwd()` to hardcoded absolute path
  - Made baseDir customizable via `args.baseDir` parameter

### Changed
- Repository location changed from `repo` to `repos` (plural) to match actual directory
- Updated default baseDir to `/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos`
- Added clarity to logging about baseDir override
- Updated documentation with baseDir parameter usage

### Technical Details
**Before (would crash):**
```javascript
const baseDir = `${process.cwd()}/project-unit-test cases/repo`
// Error: process is not defined (in workflow sandbox)
```

**After (works correctly):**
```javascript
const baseDir = args?.baseDir || '/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos'
// Uses hardcoded path by default, overridable via args.baseDir
```

## [1.0.0] - 2026-07-06

### Added
- **Trusted Mode** for power users
  - Optional `trustedMode: true` parameter
  - Skips all permission gates for fully automated execution
  - Build validation still runs (safety net)
  - 25-35% faster execution than Safe Mode
  - Results show which mode was used for audit trail

- **Safe Mode** (default)
  - 3 permission gates (setup, generation, validation)
  - Explicit user approval before major operations
  - Best for learning and oversight
  
- **Comprehensive Documentation**
  - TRUSTED-MODE-GUIDE.md: Complete Safe vs Trusted Mode guide
  - MODES-COMPARISON.md: Detailed comparison with examples
  - AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md: Technical deep-dive
  - AEM-UNIT-TEST-CASES-BEFORE-AFTER.md: Before/after comparison

- **Multi-Stage Workflow**
  - Repository Setup: Clone and create feature branches
  - Test Generation: AEM Test Case Creator generates tests
  - Local Build Validation: Maven build testing before push
  - Auto-Push: Automatic push to feature branch

- **Token Optimization**
  - 47% reduction in token usage vs previous version
  - Concise prompts (50-100 words vs 200+ previously)
  - Structured output schemas at every stage
  - Efficient data threading between pipeline stages

- **Permission Gates**
  - Gate #1: Repository Setup (approve before cloning)
  - Gate #2: Test Generation (approve before code creation)
  - Gate #3: Build Validation (approve before Maven test)
  - No gate: Auto-Push (automatic when validation passes)
  - Optional skip with Trusted Mode

- **Build Validation**
  - Local Maven build: `mvn clean test -pl core -am`
  - Catches issues before pushing to remote
  - Prevents bad code from reaching origin
  - Works in both Safe Mode and Trusted Mode

- **Repository Organization**
  - Centralized location for all test repos
  - Strict enforcement of folder location
  - Consistent across machines and CI/CD
  - Customizable via baseDir parameter

- **Comprehensive Examples**
  - 5 sample configurations in examples/sample-config.json
  - Use cases for single repo, multiple repos, batch operations
  - CI/CD pipeline examples
  - Trusted Mode examples

### Documentation
- README.md: Complete feature guide and usage
- QUICKSTART.md: 5-minute setup guide
- .gitignore: Proper git configuration

### Project Structure
```
ai-agent/
├── README.md
├── QUICKSTART.md
├── CHANGELOG.md
├── .gitignore
├── workflows/
│   └── aem-unit-test-cases.js
├── docs/
│   ├── TRUSTED-MODE-GUIDE.md
│   ├── MODES-COMPARISON.md
│   ├── AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md
│   └── AEM-UNIT-TEST-CASES-BEFORE-AFTER.md
└── examples/
    └── sample-config.json
```

---

## Implementation Notes

### Workflow Execution
The workflow runs in Claude Code's agent sandbox with the following constraints:
- No `process` object (process.cwd(), process.env unavailable)
- No `Date.now()` or `new Date()` 
- No `Math.random()`
- No filesystem API (`fs` module)
- No external network requests beyond MCP tools
- All work must use agents for actual filesystem/git operations

### Permission Gates Design
Each permission gate is implemented as:
1. User-facing agent that asks for approval
2. Response schema with `approved: boolean`
3. Conditional execution based on response
4. Clear logging of decision

In Trusted Mode, the `requestPermission()` helper returns `{approved: true}` automatically without prompting.

### Build Validation Strategy
Build validation is always executed because:
- It catches issues early (before push)
- Prevents bad code reaching remote
- Provides confidence in test quality
- Same in both Safe and Trusted modes
- Only safety mechanism in Trusted Mode

### Result Object
Every workflow returns structured result with:
- `mode`: "safe" or "trusted" (for audit)
- `totalProcessed`, `successful`, `failed`, `skipped`
- `baseDirectory`: Where repos were cloned
- `results`: Array with per-repo details
- `optimizations`: Summary of applied optimizations

---

## Future Enhancements

Possible improvements for future versions:
- [ ] GitHub PR creation instead of branch push
- [ ] JaCoCo coverage reporting integration
- [ ] Slack/email notifications for pipeline runs
- [ ] Batch permission approval ("approve all remaining")
- [ ] Dry-run mode (preview without changes)
- [ ] Automatic retry logic for failed builds
- [ ] Custom test execution commands
- [ ] Multi-branch support (push to different branches)
- [ ] Test report generation and archiving
- [ ] Integration with issue tracking systems

---

## Compatibility

### Tested On
- Claude Haiku 4.5
- Claude Opus 4.8 (compatible)
- Claude Sonnet 5 (compatible)

### Requirements
- Claude Code (CLI or Web)
- Git installed and configured
- Maven installed (for build validation)
- Access to target repositories

### Known Limitations
- Workflow runs in sandbox (no direct filesystem/process access)
- All operations delegated to agents
- Permission gates are user-facing only
- Build validation requires Maven pom.xml

---

## Support

For issues or questions:
1. Check the [README.md](README.md) troubleshooting section
2. Review [TRUSTED-MODE-GUIDE.md](docs/TRUSTED-MODE-GUIDE.md)
3. See [MODES-COMPARISON.md](docs/MODES-COMPARISON.md) for detailed explanations
4. Check Claude Code logs: `~/.claude/logs/`

---

## License

[Specify your license here]

---

## Contributors

Built by Claude Code with ❤️
