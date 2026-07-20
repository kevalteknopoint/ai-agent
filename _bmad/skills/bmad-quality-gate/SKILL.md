# bmad-quality-gate

Rule-driven AEM quality enforcement — zero AI, deterministic rules.

## When to Use

- "Run quality gate on this repo"
- "Check AEM best practices"
- "Enforce coding standards before PR"
- "Run lint rules"

## Steps

1. Confirm repository path and branch
2. Run task: `_bmad/tasks/clone-repo.md` (if remote)
3. Execute: `bash {ai_agent_repo}/quality-gate/runner/run-quality-gate.sh '{repoPath}'`
4. Display aggregated results with pass/fail per category

## Rule Categories

| Category | Manifest |
|---|---|
| Java | `quality-gate/rules/java/` |
| HTL | `quality-gate/rules/htl/` |
| Frontend | `quality-gate/rules/frontend/` |
| Custom | `quality-gate/rules/custom/` |
| OakPAL | `quality-gate/rules-manifest-oakpal.json` |

## Output

Aggregated report via `quality-gate/aggregator/aggregate-report.js`
