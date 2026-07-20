# Performance Test Preflight Checklist

## Before Running

- [ ] Target URL is accessible and authorized for load testing
- [ ] Test type selected (load/stress/soak/spike)
- [ ] VUs and duration are reasonable for target infrastructure
- [ ] Endpoints confirmed (default `/` if none specified)
- [ ] Thresholds set (p95 < 500ms, p99 < 1000ms, error < 1% defaults)

## Tool Requirements

| Tool | Required |
|---|---|
| k6 | Always |
| Node.js | For report generation |

## Safety Checks

- [ ] Not targeting production without explicit confirmation
- [ ] VU count won't overwhelm a development/staging environment
- [ ] Duration is bounded (no accidental infinite runs)
- [ ] Think time configured to prevent request flooding
- [ ] Authorization headers are valid (if required)

## Baseline Comparison

- [ ] Previous run JSON available for regression comparison? (optional)
- [ ] Same endpoint set as baseline for fair comparison? (if comparing)
