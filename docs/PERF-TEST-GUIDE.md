# Performance Test Guide

Zero-AI load/performance testing: point it at a URL and it generates a k6
test script, runs it, and produces a report with SLA pass/fail. Like JMeter
from one command — no LLM tokens in actual testing.

## How it works

```
You provide: target URL + test parameters
                    ↓
    generate_k6_script.py — creates k6 JS from your params
                    ↓
    k6 run test.js — executes the load test (pure CLI)
                    ↓
    analyze_results.py — parses k6 metrics, checks SLAs
                    ↓
    Output: perf-results/ with reports + reusable k6 script
```

**Zero AI tokens in test execution.** k6 is an open-source CLI binary.

## Two entry points

| Entry point | Use when | Asks for input |
|---|---|---|
| **`perf-test` skill** (`skills/perf-test/SKILL.md`) | A human is driving | Asks for URL, test type, VUs, duration |
| **`perf-test` workflow** (`workflows/perf-test.js`) | CI / batch / scheduled | Takes args — no prompting |

## Quick start

### Interactive (skill)

```
> Run a load test

Target URL? https://staging.example.com
Test type? load / stress / soak / spike [load]
Virtual users? [10] 50
Duration? [1m] 5m
Endpoints? [just /] GET /api/products, GET /api/users, POST /api/login
```

### Headless (workflow)

```js
// Basic load test
{ url: "https://staging.example.com", type: "load", vus: 50, duration: "5m" }

// With specific endpoints
{
  url: "https://api.example.com",
  type: "stress",
  vus: 200,
  duration: "10m",
  endpoints: [
    { method: "GET", path: "/api/products", name: "Product list" },
    { method: "POST", path: "/api/search", name: "Search",
      body: { query: "test" } }
  ],
  headers: { "Authorization": "Bearer YOUR_TOKEN" }
}

// With baseline comparison
{
  url: "https://staging.example.com",
  type: "load",
  vus: 50,
  duration: "5m",
  baseline: "./perf-results/previous/k6-summary.json"
}

// Multiple tests
{
  tests: [
    { url: "https://api.example.com", type: "load", vus: 50, duration: "5m" },
    { url: "https://api.example.com", type: "stress", vus: 200, duration: "10m" }
  ]
}
```

### Direct CLI (no AI at all)

```bash
# Basic load test
bash scripts/perf-test/run_test.sh \
  --url 'https://staging.example.com' \
  --type load --vus 50 --duration 5m

# Stress test with endpoints
bash scripts/perf-test/run_test.sh \
  --url 'https://api.example.com' \
  --type stress --vus 200 --duration 10m \
  --endpoint 'GET /api/products Products' \
  --endpoint 'POST /api/login Login' \
  --header 'Authorization: Bearer TOKEN'

# With custom SLA thresholds
bash scripts/perf-test/run_test.sh \
  --url 'https://api.example.com' \
  --type load --vus 100 --duration 5m \
  --threshold-p95 200 --threshold-p99 500 --threshold-error 0.5

# Baseline comparison
bash scripts/perf-test/run_test.sh \
  --url 'https://staging.example.com' \
  --type load --vus 50 --duration 5m \
  --baseline './perf-results/previous/k6-summary.json'

# Generate script only (dry run)
bash scripts/perf-test/run_test.sh \
  --url 'https://staging.example.com' \
  --type load --vus 50 --duration 5m \
  --dry-run

# Soak test (1 hour)
bash scripts/perf-test/run_test.sh \
  --url 'https://app.example.com' \
  --type soak --vus 30 --duration 1h

# Spike test
bash scripts/perf-test/run_test.sh \
  --url 'https://app.example.com' \
  --type spike --vus 500 --duration 2m
```

## Test types

| Type | What it validates | When to use |
|------|-------------------|-------------|
| **load** | Normal traffic handling | Before every release |
| **stress** | Breaking point discovery | Capacity planning |
| **soak** | Memory leaks, connection exhaustion | Before major launches |
| **spike** | Sudden burst recovery | If you expect traffic spikes |

### Load test profile
```
     ↗ ramp-up ─── steady state ─── ramp-down ↘
VUs: 0 → 50        50 for 5m         50 → 0
```

### Stress test profile
```
     ↗ step 1 ─ step 2 ─ step 3 ─ step 4 ─ step 5 ↘
VUs: 0 → 50     100      150      200      250 → 0
```

### Soak test profile
```
     ↗ ramp ─── steady state (extended) ─── down ↘
VUs: 0 → 30     30 for 1–8 hours          30 → 0
```

### Spike test profile
```
                ┌─ spike ─┐
VUs: 5 ─ 5 ─ 5 → 500 → 500 → 5 ─ 5 ─ 5 → 0
```

## SLA thresholds (defaults)

| Metric | Default threshold | Configurable |
|--------|-------------------|--------------|
| Response time p50 | < 200ms | `--threshold-p50` |
| Response time p90 | < 400ms | `--threshold-p90` |
| Response time p95 | < 500ms | `--threshold-p95` |
| Response time p99 | < 1000ms | `--threshold-p99` |
| Error rate | < 1% | `--threshold-error` |
| Min throughput | N/A | `--min-rps` |

## Output

Reports go to `./perf-results/<domain>/<timestamp>/`:

| File | Content |
|------|---------|
| `perf-report.md` | Full report: SLA pass/fail, response times, throughput, recommendations |
| `perf-findings.json` | Machine-readable: all metrics + SLA check results |
| `perf-issues.csv` | SLA violation tracker |
| `baseline-comparison.md` | Delta vs previous run (when `--baseline` provided) |
| `k6-summary.json` | Raw k6 metrics (use as `--baseline` for next run) |
| `test.js` | Generated k6 script (**reusable** — run it directly with `k6 run`) |
| `test-config.json` | Test configuration |
| `k6-output.log` | Full k6 console output |

## Endpoints configuration

### Inline (CLI)
```bash
--endpoint 'GET /api/products Product List'
--endpoint 'POST /api/login Login'
--endpoint 'GET /api/users/:id User Detail'
```

### JSON file
```json
[
  {"method": "GET", "path": "/", "name": "Homepage"},
  {"method": "GET", "path": "/api/products", "name": "Product list"},
  {"method": "POST", "path": "/api/login", "name": "Login",
   "body": {"username": "test", "password": "test123"},
   "headers": {"Content-Type": "application/json"}},
  {"method": "GET", "path": "/api/products/1", "name": "Product detail"}
]
```

Pass via `--endpoints endpoints.json`

## Architecture

```
scripts/perf-test/
  install_tools.sh         ← Install k6 (idempotent)
  run_test.sh              ← Main orchestrator (zero AI)
  generate_k6_script.py    ← Generate k6 JS from config/params
  analyze_results.py       ← Parse k6 output → reports with SLA checks

agents/perf-test.md        ← Minimal agent (parameter collection only)
skills/perf-test/SKILL.md  ← Interactive entry point
workflows/perf-test.js     ← Headless/batch entry point
```

**Key principle:** The shell script does ALL the work. You can run `run_test.sh`
directly from the command line with zero AI involvement. The generated `test.js`
is a standard k6 script — reusable with `k6 run test.js` anywhere.
