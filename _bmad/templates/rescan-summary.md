# Rescan Summary Template

## Header

```
# Rescan Summary
Date: {YYYY-MM-DD}
Repository: {repoName}
Branch: {branch} @ {sha}
Prior scan: {prior-date}
```

## Verdict Distribution

| Status | Count | % |
|---|---|---|
| Fixed | {n} | {pct} |
| Open | {n} | {pct} |
| Partially Fixed | {n} | {pct} |
| Not Applicable | {n} | {pct} |
| Unverifiable | {n} | {pct} |
| **Total** | **{total}** | 100% |

## Progress by Severity

| Severity | Total | Fixed | Open | Fix Rate |
|---|---|---|---|---|
| Critical (5) | {n} | {n} | {n} | {pct} |
| High (4) | {n} | {n} | {n} | {pct} |
| Medium (3) | {n} | {n} | {n} | {pct} |
| Low (2) | {n} | {n} | {n} | {pct} |

## Still Open (Action Required)

### [{id}] {title}
- **File**: `{file}:{verifiedLine}`
- **Severity**: {level}
- **Status**: Open (code unchanged)

## Recently Fixed

### [{id}] {title}
- **File**: `{file}` — code remediated
- **Verdict**: Fixed
