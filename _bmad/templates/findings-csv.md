# Findings CSV Template

## Column Schema

```
id,file,line,severity,category,problem,currentCode,recommendedFix,status
```

## Field Definitions

| Column | Type | Description |
|---|---|---|
| id | string | Unique finding ID (e.g., `HTL-001`, `JAVA-042`) |
| file | string | Relative path from repo root |
| line | integer | Line number where issue occurs |
| severity | integer | 1-5 (1=Info, 5=Critical) |
| category | string | Check category (e.g., "XSS & context handling") |
| problem | string | One-line description |
| currentCode | string | The problematic code snippet |
| recommendedFix | string | Suggested remediation |
| status | string | `Open` / `Fixed` / `Partially Fixed` / `Not Applicable` / `Unverifiable` |

## Notes

- CSV uses RFC 4180 quoting (double-quote fields containing commas/newlines)
- Status defaults to `Open` on first scan
- Rescan updates status in-place (same file, same id)
- One CSV per analyzer domain (htl-issues.csv, java-issues.csv, etc.)
