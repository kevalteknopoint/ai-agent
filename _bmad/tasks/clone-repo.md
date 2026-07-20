# Task: Clone Repository

## Purpose

Clone a Git repository (or update an existing clone) to the standardized local location.

## Command

```bash
bash {ai_agent_repo}/scripts/clone_or_update.sh '{repoUrl}' '{branch}' '{baseDir}'
```

## Inputs

| Parameter | Required | Default |
|---|---|---|
| repoUrl | yes | — |
| branch | yes | — |
| baseDir | no | `{ai_agent_repo}/repos` |

## Output (JSON)

```json
{
  "ready": true,
  "repoPath": "/path/to/repos/repo-name",
  "sha": "abc123...",
  "branch": "main"
}
```

## Error Handling

- If `ready: false` → surface the `error` field verbatim, do NOT retry
- Never guess branch names — require explicit input
- Safe to call repeatedly (idempotent: fetches + checks out + pulls)

## Notes

- All repos clone to `{baseDir}/{repoName}` (basename, `.git` stripped)
- The `repos/` directory is git-ignored — never commit client code
