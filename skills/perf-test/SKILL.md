---
name: perf-test
description: >-
  Interactive entry point for the zero-AI performance testing system. Asks for
  a website URL and load test parameters, then generates a k6 script, runs it,
  and produces a report with SLA pass/fail, response time percentiles,
  throughput, and optional baseline comparison. Zero LLM tokens in actual
  testing — all execution is k6 CLI. Use when the user asks to "load test",
  "performance test", "stress test", "benchmark", "check response times",
  or similar.
---

# Performance Test (Zero-AI Runtime)

You are the interactive entry point for the performance tester. Your job is
**parameter collection and script dispatch** — not load test execution. All
actual testing runs via k6 CLI with zero LLM tokens.

Resolve `<ai-agent-repo>` as the absolute path to this toolkit repository.
When invoked from a workflow, this is passed via `args.aiAgentRepo`.

## Steps

### 1. Get the target URL

If the user already provided a URL, use it. Otherwise ask:

> What URL should I load test?
> Example: `https://staging.example.com` or `https://api.example.com`

### 2. Get test parameters

Ask these in a natural conversational way, showing defaults:

> Configure your test:
>
> - **Test type**: `load` (normal traffic) / `stress` (find breaking point) /
>   `soak` (endurance, memory leaks) / `spike` (sudden burst) — default: `load`
> - **Virtual Users**: concurrent connections — default: `10`
> - **Duration**: how long to run — default: `1m` (e.g., `5m`, `30m`, `1h`)
> - **Endpoints**: specific paths to test? Default is just `/`
>   - Format: `GET /api/products ProductList`
>   - Format: `POST /api/login Login`
>   - Or provide an endpoints JSON file
>
> Any **custom headers** needed? (e.g., `Authorization: Bearer <token>`)

If the user provides all params upfront, skip the interactive questions.

### 3. Confirm and show plan

> Ready to run:
> - **Target:** {url}
> - **Type:** {type} test
> - **VUs:** {vus} concurrent users
> - **Duration:** {duration}
> - **Endpoints:** {count} endpoint(s)
> - **SLA thresholds:** p95 < 500ms, p99 < 1000ms, errors < 1%
>
> Proceed?

### 4. Check k6 installation

```bash
bash <ai-agent-repo>/scripts/perf-test/install_tools.sh --check-only
```

If missing, install:
```bash
bash <ai-agent-repo>/scripts/perf-test/install_tools.sh
```

### 5. Run the test

Build the command from collected parameters:

```bash
bash <ai-agent-repo>/scripts/perf-test/run_test.sh \
  --url '<url>' \
  --type '<type>' \
  --vus <vus> \
  --duration '<duration>' \
  [--endpoint 'METHOD /path Name'] \
  [--header 'Key: Value'] \
  [--threshold-p95 500] \
  [--threshold-p99 1000] \
  [--threshold-error 1]
```

**Note:** This script generates the k6 script, runs k6, and analyzes results
in one shot. It will print k6 output in real-time.

### 6. Show results

After completion, briefly show:
- Overall PASS/FAIL status
- Key metrics (p95, throughput, error rate)
- Point to the report files

Do NOT re-interpret the report. The script output contains everything.

## Rules

- **NEVER** generate k6 scripts yourself — the Python generator does this
- **NEVER** run k6 directly — always go through `run_test.sh`
- **NEVER** use LLM tokens for analysis — `analyze_results.py` does this
- The test scripts do ALL the work — you're just the dispatcher
