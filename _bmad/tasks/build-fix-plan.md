# Task: Build Fix Plan

## Purpose

Parse scan findings, filter to open issues, and generate a structured fix execution plan.

## Command

```bash
python3 {ai_agent_repo}/scripts/build_fix_plan.py '{repoPath}' --mode '{mode}' --max-batch {batchSize}
```

### With domain filter:
```bash
python3 {ai_agent_repo}/scripts/build_fix_plan.py '{repoPath}' --mode domain --domain '{domain}'
```

### Critical-only:
```bash
python3 {ai_agent_repo}/scripts/build_fix_plan.py '{repoPath}' --mode critical
```

### Dry-run (plan only, no dispatch):
```bash
python3 {ai_agent_repo}/scripts/build_fix_plan.py '{repoPath}' --mode '{mode}' --dry-run
```

## Inputs

| Parameter | Required | Default |
|---|---|---|
| repoPath | yes | — |
| mode | no | `all` |
| domain | no | — (required if mode=domain) |
| batchSize | no | `8` |

## Output (JSON)

```json
{
  "planPath": "/path/to/repos/repo-name/analysis/fix-plan.json",
  "totalIssues": 42,
  "totalBatches": 6,
  "dryRun": false
}
```

## Error Handling

- If no `analysis/` folder → error: run bmad-code-scan first
- If no open findings match filters → `status: no_issues`, zero batches
- Malformed findings files are skipped with a warning, never fatal

## Notes

- Plan is written to `{repoPath}/analysis/fix-plan.json`
- The orchestrator reads this plan to dispatch fixer agents
- Re-running overwrites the prior plan (idempotent)
