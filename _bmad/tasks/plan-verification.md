# Task: Plan Verification (Prior Analysis Check)

## Purpose

Check whether a repository already has findings from a prior scan and prepare a batch plan for rescan verification.

## Command

```bash
python3 {ai_agent_repo}/scripts/plan_verification.py '{repoPath}' [--batch-size N] [--recheck-fixed]
```

## Inputs

| Parameter | Required | Default |
|---|---|---|
| repoPath | yes | — |
| --batch-size | no | 12 |
| --recheck-fixed | no | false (skip Fixed/NA findings) |

## Output (JSON)

```json
{
  "present": true,
  "findingsCount": 47,
  "batches": [
    { "batchId": "java-b1", "findingsPath": "...", "verdictPath": "...", "issueIds": [...] },
    { "batchId": "htl-b1", "findingsPath": "...", "verdictPath": "...", "issueIds": [...] }
  ]
}
```

## Behavior

- `present: true` → repo has prior findings; caller can choose rescan
- `present: false` → no prior scan; full scan required
- Purges stale `.verify/` verdicts
- Writes fresh batch plan to `analysis/.verify/plan.json`
- Groups findings by analyzer domain and splits into sized batches

## Notes

- Does NOT choose the scan mode — reports state for caller to decide
- Pass `--recheck-fixed` to hunt for regressions on previously-fixed items
