# Task: Collect Fix Results

## Purpose

After all fixer agents complete, merge batch results into final report artifacts.

## Command

```bash
python3 {ai_agent_repo}/scripts/collect_fix_results.py '{repoPath}'
```

## Inputs

| Parameter | Required | Default |
|---|---|---|
| repoPath | yes | — |

## Prerequisites

- Fixer agents have written results to `{repoPath}/analysis/.fix/*-results.json`

## Output (JSON)

```json
{
  "totalFixed": 28,
  "totalFailed": 3,
  "totalSkipped": 2,
  "reportPath": "/path/to/repos/repo-name/analysis/fix-report.md"
}
```

## Artifacts Written

| File | Purpose |
|---|---|
| `analysis/fix-results.json` | All batch results merged |
| `analysis/fix-report.md` | Human-readable summary |
| `analysis/fix-log.md` | Chronological change log |

## Error Handling

- If no `.fix/` folder → error: no fixer agents have run
- Malformed batch result files are skipped with warning
- Empty results → exits cleanly with zero counts
