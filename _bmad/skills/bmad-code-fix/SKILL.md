# bmad-code-fix

Parse code-scan findings, apply actual code fixes to source files, and present changes for human review.

## What This Does

**This agent EDITS YOUR SOURCE CODE.** It reads the findings from `bmad-code-scan`, understands the issues, and writes corrected code directly into the source files. All changes are made on a dedicated git branch — the human reviews the diff and decides whether to commit or discard.

## When to Use

- "Fix the scan findings"
- "Apply fixes from the code review"
- "Fix all critical issues in the analysis"
- "Auto-remediate the security findings"
- "Fix the Java/HTL/EDS/JS/CSS issues found by the scan"
- "Dry-run fix plan for review"

## Agent

Load `_bmad/agents/code-fix-orchestrator.md` for routing.

## Three Modes

| Mode | When | Scope |
|---|---|---|
| **all** | Fix everything open | All domains, severity 1–5 |
| **critical** | Only urgent fixes | Severity 4–5 (Critical + High) |
| **domain** | Single-stack focus | One domain (java/htl/eds/jsReact/css) |

## Steps

1. Get repo path from user (or infer from prior `bmad-code-scan` run)
2. Validate `analysis/` folder exists with `*-findings.json` files
3. Load all findings, filter to `status=Open` (or absent status = first scan)
4. If `mode=critical`: filter to severity ≥ 4
5. If `mode=domain`: filter to specified domain only
6. Build fix execution plan (priority-ordered, dependency-safe batches)
7. If `dryRun=true`: write plan to `analysis/fix-plan.json` and stop
8. Create git branch `fix/code-scan-{YYYY-MM-DD}`
9. Dispatch domain-specific fixer agents with batches
10. **Fixer agents EDIT the actual source files** (the real code, not copies)
11. Collect fix results from all fixer agents
12. Validate fixes (compile/lint check per domain)
13. Run `git diff --stat` to show what changed
14. **Present diff to human for review**
15. **Human decides:** commit, amend individual files, or `git checkout .` to discard

> **No auto-commit. No auto-push.** The human always has final say.

## Dispatch Rules

Only dispatch fixers for domains that have open findings:

| Domain | Fixer Agent | Checklist |
|---|---|---|
| `java` | java-code-fixer | `_bmad/checklists/code-fix-review.md` |
| `htl` | htl-code-fixer | `_bmad/checklists/code-fix-review.md` |
| `eds` | eds-code-fixer | `_bmad/checklists/code-fix-review.md` |
| `jsReact` | js-react-code-fixer | `_bmad/checklists/code-fix-review.md` |
| `css` | css-code-fixer | `_bmad/checklists/code-fix-review.md` |

## Fix Ordering Protocol

Fixes are applied in a safe order to avoid cascading conflicts:

1. **Configuration/Infrastructure** — security config, application.yml, build files
2. **Models/Entities** — data layer changes that other layers depend on
3. **Services/Business Logic** — core logic fixes
4. **Controllers/Endpoints** — API layer
5. **Templates/Views** — HTL, frontend components
6. **Styles** — CSS/SCSS last (least dependency impact)

Within each layer, severity 5 (Critical) fixes go first.

## Safety Rails

- Always creates a new git branch (never fixes on main/develop)
- Each fixer agent validates syntax after applying fixes
- If compilation/syntax check fails, fix is rolled back for that file
- **NEVER auto-commits** — human reviews `git diff` and decides
- **NEVER auto-pushes** — human pushes when ready
- A failed fix is reverted in-place (`git checkout -- <file>`) and logged as `FixFailed`
- Maximum 3 retries per issue before marking `FixFailed` and moving on
- Human can discard ALL changes with `git checkout .` or cherry-pick individual files

## Model Policy

- Orchestration/routing: **opus**
- Fixer agents (code editing): **sonnet**

## Output

| File | Purpose |
|---|---|
| `analysis/fix-plan.json` | Execution plan (written before fixes start) |
| `analysis/fix-report.md` | Human-readable summary |
| `analysis/fix-results.json` | Machine-parseable outcomes per issue |
| `analysis/fix-log.md` | Chronological change log |
| `analysis/.fix/*-results.json` | Per-batch intermediate results |
