# bmad-perf-test

Zero-AI performance/load testing with k6.

## When to Use

- "Load test this URL"
- "Run a performance test"
- "Stress test this API"
- "Benchmark this endpoint"

## Agent

Load `_bmad/agents/perf-test.md`

## Steps

1. Collect: target URL, test type, VUs, duration, endpoints, thresholds
2. Preflight: load `_bmad/checklists/perf-preflight.md`
3. Check k6: `bash {ai_agent_repo}/scripts/perf-test/install_tools.sh --check-only`
4. Run: `bash {ai_agent_repo}/scripts/perf-test/run_test.sh --url '{url}' --type '{type}' --vus {n} --duration '{dur}'`
5. Display SLA pass/fail summary

## Test Types

| Type | Pattern |
|---|---|
| `load` | Steady state at target VUs |
| `stress` | Ramp beyond capacity |
| `soak` | Extended duration |
| `spike` | Sudden burst |

## Defaults

| Parameter | Default |
|---|---|
| VUs | 10 |
| Duration | 1m |
| p95 threshold | 500ms |
| p99 threshold | 1000ms |
| Error threshold | 1% |
| Think time | 1s |
