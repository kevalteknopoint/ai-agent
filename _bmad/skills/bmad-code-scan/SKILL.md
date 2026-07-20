# bmad-code-scan

Clone a repo, detect its tech stack, and dispatch the applicable analyzer agents.

## When to Use

- "Scan this repo"
- "Run a code review on <github-url>"
- "Security-review this AEM/EDS/Spring Boot project"
- "Recheck what's been fixed"
- "Update the scan status"

## Agent

Load `_bmad/agents/code-scan-orchestrator.md` for routing.

## Two Modes

| Mode | When | Cost |
|---|---|---|
| **Full scan** | No `analysis/` folder exists | Every in-scope file read |
| **Rescan** | `analysis/` already present | Only files carrying known findings |

A rescan finds NO new issues — it answers "is this fixed?" not "what's wrong now?"

## Steps

1. Get GitHub URL (or local path) + branch from user
2. Run task: `_bmad/tasks/clone-repo.md`
3. Run task: `_bmad/tasks/detect-stack.md`
4. If `mode=auto`: run task `_bmad/tasks/plan-verification.md` to check for prior analysis
5. **Full scan path**: dispatch detected-stack analyzers in parallel
6. **Rescan path**: dispatch `code-scan-verifier` with batch plan, then `python3 {ai_agent_repo}/scripts/apply_verdicts.py`

## Dispatch Rules

Only dispatch agents whose stack was detected:

| Flag | Agent | Checklist |
|---|---|---|
| `javaSpringBoot` | java-springboot-analyzer | `_bmad/checklists/java-review.md` |
| `aemHtl` | aem-htl-analyzer | `_bmad/checklists/htl-review.md` |
| `edsBlocks` | eds-blocks-analyzer | `_bmad/checklists/eds-blocks-review.md` |
| `jsReact` | js-react-analyzer | `_bmad/checklists/js-react-review.md` |
| `cssScss` | css-scss-analyzer | `_bmad/checklists/css-review.md` |

## Model Policy

- Orchestration/routing: **opus**
- Execution/review agents: **sonnet**

## Output

Reports, findings JSON, and CSV tracker written to `{repoPath}/analysis/`.
