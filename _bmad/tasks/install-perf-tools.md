# Task: Install Performance Tools

## Purpose

Check (and optionally install) k6 for performance/load testing.

## Check Command

```bash
bash {ai_agent_repo}/scripts/perf-test/install_tools.sh --check-only
```

## Install Command

```bash
bash {ai_agent_repo}/scripts/perf-test/install_tools.sh
```

## Required Tools

| Tool | Check | Install |
|---|---|---|
| k6 | `which k6` | `brew install k6` |

## Notes

- k6 is the only runtime dependency for performance testing
- All test script generation happens via the shell script
- Report results don't require additional tooling
