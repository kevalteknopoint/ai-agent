#!/usr/bin/env python3
"""
analyze_results.py — Parse k6 test results and generate performance reports.

Zero AI. Reads k6 JSON summary output and produces:
  - perf-report.md         (human-readable report with SLA pass/fail)
  - perf-findings.json      (machine-readable performance findings)
  - perf-issues.csv         (tracker for SLA violations)
  - baseline-comparison.md  (delta vs previous run, if baseline exists)

Usage:
  python3 analyze_results.py --results <k6-summary.json> --output-dir <dir> \
    [--config <test-config.json>] [--baseline <prev-summary.json>]
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


# Default SLA thresholds
DEFAULT_THRESHOLDS = {
    "http_req_duration_p50": 200,
    "http_req_duration_p90": 400,
    "http_req_duration_p95": 500,
    "http_req_duration_p99": 1000,
    "error_rate_percent": 1.0,
    "min_throughput_rps": 0,
}


def parse_k6_summary(filepath):
    """Parse k6 --summary-export JSON or end-of-test JSON."""
    with open(filepath) as f:
        data = json.load(f)

    metrics = data.get("metrics", {})

    # Extract key metrics
    req_duration = metrics.get("http_req_duration", {}).get("values", {})
    req_failed = metrics.get("http_req_failed", {}).get("values", {})
    reqs = metrics.get("http_reqs", {}).get("values", {})
    iterations = metrics.get("iterations", {}).get("values", {})
    data_received = metrics.get("data_received", {}).get("values", {})
    data_sent = metrics.get("data_sent", {}).get("values", {})
    req_waiting = metrics.get("http_req_waiting", {}).get("values", {})
    req_connecting = metrics.get("http_req_connecting", {}).get("values", {})
    req_tls = metrics.get("http_req_tls_handshaking", {}).get("values", {})
    vus = metrics.get("vus", {}).get("values", {})
    vus_max = metrics.get("vus_max", {}).get("values", {})

    return {
        "response_time": {
            "avg": req_duration.get("avg", 0),
            "min": req_duration.get("min", 0),
            "max": req_duration.get("max", 0),
            "med": req_duration.get("med", 0),
            "p90": req_duration.get("p(90)", 0),
            "p95": req_duration.get("p(95)", 0),
            "p99": req_duration.get("p(99)", 0),
        },
        "error_rate": req_failed.get("rate", 0) * 100,  # Convert to percentage
        "throughput": {
            "rps": reqs.get("rate", 0),
            "total_requests": reqs.get("count", 0),
        },
        "iterations": {
            "rate": iterations.get("rate", 0),
            "count": iterations.get("count", 0),
        },
        "data_transfer": {
            "received_bytes": data_received.get("count", 0),
            "sent_bytes": data_sent.get("count", 0),
            "received_rate": data_received.get("rate", 0),
        },
        "connection": {
            "waiting_avg": req_waiting.get("avg", 0),
            "connecting_avg": req_connecting.get("avg", 0),
            "tls_avg": req_tls.get("avg", 0),
        },
        "vus": {
            "current": vus.get("value", 0),
            "max": vus_max.get("value", 0),
        },
        "raw_metrics": metrics,
    }


def check_sla(parsed, thresholds):
    """Check each SLA threshold and return pass/fail findings."""
    findings = []

    checks = [
        ("http_req_duration_p50", parsed["response_time"]["med"], "Response time p50"),
        ("http_req_duration_p90", parsed["response_time"]["p90"], "Response time p90"),
        ("http_req_duration_p95", parsed["response_time"]["p95"], "Response time p95"),
        ("http_req_duration_p99", parsed["response_time"]["p99"], "Response time p99"),
        ("error_rate_percent", parsed["error_rate"], "Error rate"),
    ]

    for key, actual, label in checks:
        threshold = thresholds.get(key, DEFAULT_THRESHOLDS.get(key))
        if threshold is None:
            continue
        passed = actual <= threshold
        severity = "info"
        if not passed:
            if "p99" in key or "error_rate" in key:
                severity = "high" if actual > threshold * 2 else "medium"
            elif "p95" in key:
                severity = "high" if actual > threshold * 1.5 else "medium"
            else:
                severity = "medium" if actual > threshold * 1.5 else "low"

        findings.append({
            "metric": key,
            "label": label,
            "actual": round(actual, 2),
            "threshold": threshold,
            "unit": "%" if "rate" in key else "ms",
            "passed": passed,
            "severity": severity,
            "delta_pct": round(((actual - threshold) / threshold) * 100, 1) if threshold > 0 else 0,
        })

    # Throughput check (minimum)
    min_rps = thresholds.get("min_throughput_rps", 0)
    if min_rps > 0:
        actual_rps = parsed["throughput"]["rps"]
        passed = actual_rps >= min_rps
        findings.append({
            "metric": "throughput_rps",
            "label": "Throughput",
            "actual": round(actual_rps, 2),
            "threshold": min_rps,
            "unit": "req/s",
            "passed": passed,
            "severity": "high" if not passed else "info",
            "delta_pct": round(((actual_rps - min_rps) / min_rps) * 100, 1) if min_rps > 0 else 0,
        })

    return findings


def compare_baseline(current, baseline_path):
    """Compare current results against a baseline run."""
    if not baseline_path or not os.path.isfile(baseline_path):
        return None

    baseline = parse_k6_summary(baseline_path)

    comparisons = []
    metrics = [
        ("Response time avg", current["response_time"]["avg"], baseline["response_time"]["avg"], "ms", "lower"),
        ("Response time p50", current["response_time"]["med"], baseline["response_time"]["med"], "ms", "lower"),
        ("Response time p95", current["response_time"]["p95"], baseline["response_time"]["p95"], "ms", "lower"),
        ("Response time p99", current["response_time"]["p99"], baseline["response_time"]["p99"], "ms", "lower"),
        ("Error rate", current["error_rate"], baseline["error_rate"], "%", "lower"),
        ("Throughput", current["throughput"]["rps"], baseline["throughput"]["rps"], "req/s", "higher"),
    ]

    for label, curr_val, base_val, unit, better_dir in metrics:
        if base_val == 0:
            delta_pct = 0
        else:
            delta_pct = ((curr_val - base_val) / base_val) * 100

        if better_dir == "lower":
            regression = delta_pct > 10  # 10% threshold for regression
        else:
            regression = delta_pct < -10

        comparisons.append({
            "metric": label,
            "current": round(curr_val, 2),
            "baseline": round(base_val, 2),
            "delta_pct": round(delta_pct, 1),
            "unit": unit,
            "regression": regression,
            "better_direction": better_dir,
        })

    return comparisons


def generate_report(parsed, findings, config, comparisons=None):
    """Generate perf-report.md."""
    test_type = config.get("testType", "load")
    target = config.get("targetUrl", "unknown")
    vus = config.get("vus", "?")
    duration = config.get("duration", "?")

    passed_count = sum(1 for f in findings if f["passed"])
    failed_count = sum(1 for f in findings if not f["passed"])
    overall = "PASS" if failed_count == 0 else "FAIL"
    overall_emoji = "✅" if overall == "PASS" else "❌"

    lines = [
        f"# Performance Test Report",
        f"",
        f"**Target:** {target}  ",
        f"**Test type:** {test_type}  ",
        f"**VUs:** {vus} | **Duration:** {duration}  ",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"",
        f"## Overall Result: {overall_emoji} {overall}",
        f"",
        f"SLA checks: **{passed_count} passed**, **{failed_count} failed**",
        f"",
        f"## Key Metrics",
        f"",
        f"| Metric | Value | Threshold | Status |",
        f"|--------|-------|-----------|--------|",
    ]

    for f in findings:
        status = "✅ Pass" if f["passed"] else f"❌ Fail (+{f['delta_pct']}%)"
        lines.append(
            f"| {f['label']} | {f['actual']}{f['unit']} | "
            f"<{f['threshold']}{f['unit']} | {status} |"
        )

    lines += [
        f"",
        f"## Response Time Distribution",
        f"",
        f"| Percentile | Time (ms) |",
        f"|------------|-----------|",
        f"| Min | {parsed['response_time']['min']:.0f} |",
        f"| p50 (Median) | {parsed['response_time']['med']:.0f} |",
        f"| p90 | {parsed['response_time']['p90']:.0f} |",
        f"| p95 | {parsed['response_time']['p95']:.0f} |",
        f"| p99 | {parsed['response_time']['p99']:.0f} |",
        f"| Max | {parsed['response_time']['max']:.0f} |",
        f"| Average | {parsed['response_time']['avg']:.0f} |",
        f"",
        f"## Throughput",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Requests/sec | {parsed['throughput']['rps']:.1f} |",
        f"| Total requests | {parsed['throughput']['total_requests']} |",
        f"| Iterations/sec | {parsed['iterations']['rate']:.1f} |",
        f"| Total iterations | {parsed['iterations']['count']} |",
        f"| Error rate | {parsed['error_rate']:.2f}% |",
        f"",
        f"## Data Transfer",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Data received | {parsed['data_transfer']['received_bytes'] / 1024 / 1024:.1f} MB |",
        f"| Data sent | {parsed['data_transfer']['sent_bytes'] / 1024 / 1024:.1f} MB |",
        f"| Receive rate | {parsed['data_transfer']['received_rate'] / 1024:.1f} KB/s |",
        f"",
        f"## Connection Timing",
        f"",
        f"| Phase | Avg (ms) |",
        f"|-------|----------|",
        f"| Connecting | {parsed['connection']['connecting_avg']:.1f} |",
        f"| TLS handshake | {parsed['connection']['tls_avg']:.1f} |",
        f"| Waiting (TTFB) | {parsed['connection']['waiting_avg']:.1f} |",
    ]

    # Baseline comparison
    if comparisons:
        lines += [
            f"",
            f"## Baseline Comparison",
            f"",
            f"| Metric | Current | Baseline | Delta | Status |",
            f"|--------|---------|----------|-------|--------|",
        ]
        for c in comparisons:
            arrow = "↑" if c["delta_pct"] > 0 else "↓" if c["delta_pct"] < 0 else "="
            status = "🔴 Regression" if c["regression"] else "🟢 OK"
            lines.append(
                f"| {c['metric']} | {c['current']}{c['unit']} | "
                f"{c['baseline']}{c['unit']} | {arrow} {c['delta_pct']}% | {status} |"
            )

    # SLA violations detail
    violations = [f for f in findings if not f["passed"]]
    if violations:
        lines += [
            f"",
            f"## SLA Violations",
            f"",
        ]
        for v in violations:
            lines.append(f"### {v['label']}")
            lines.append(f"")
            lines.append(f"- **Actual:** {v['actual']}{v['unit']}")
            lines.append(f"- **Threshold:** {v['threshold']}{v['unit']}")
            lines.append(f"- **Exceeded by:** {v['delta_pct']}%")
            lines.append(f"- **Severity:** {v['severity'].upper()}")
            lines.append(f"")

    lines += [
        "---",
        f"*Generated by ai-agent perf-test toolkit. Zero AI tokens used.*",
    ]
    return "\n".join(lines)


def generate_baseline_report(comparisons):
    """Generate baseline-comparison.md."""
    if not comparisons:
        return None

    regressions = [c for c in comparisons if c["regression"]]
    overall = "REGRESSION DETECTED" if regressions else "NO REGRESSION"
    emoji = "🔴" if regressions else "🟢"

    lines = [
        f"# Baseline Comparison: {emoji} {overall}",
        f"",
        f"| Metric | Current | Baseline | Delta | Status |",
        f"|--------|---------|----------|-------|--------|",
    ]
    for c in comparisons:
        arrow = "↑" if c["delta_pct"] > 0 else "↓" if c["delta_pct"] < 0 else "="
        status = "🔴 Regression" if c["regression"] else "🟢 OK"
        lines.append(
            f"| {c['metric']} | {c['current']}{c['unit']} | "
            f"{c['baseline']}{c['unit']} | {arrow} {c['delta_pct']}% | {status} |"
        )

    if regressions:
        lines += ["", "## Regressions Detected", ""]
        for r in regressions:
            lines.append(
                f"- **{r['metric']}**: {r['baseline']}{r['unit']} → {r['current']}{r['unit']} "
                f"({r['delta_pct']:+.1f}%) — wants {r['better_direction']}"
            )

    lines += ["", "---", "*Zero AI tokens used.*"]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze k6 performance test results")
    parser.add_argument("--results", required=True, help="k6 summary JSON file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--config", help="Test config JSON (for thresholds and metadata)")
    parser.add_argument("--baseline", help="Previous run summary JSON for comparison")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Parse results
    parsed = parse_k6_summary(args.results)

    # Load config for thresholds
    config = {}
    thresholds = dict(DEFAULT_THRESHOLDS)
    if args.config and os.path.isfile(args.config):
        with open(args.config) as f:
            config = json.load(f)
        if "thresholds" in config:
            thresholds.update(config["thresholds"])

    # Check SLAs
    findings = check_sla(parsed, thresholds)

    # Baseline comparison
    comparisons = compare_baseline(parsed, args.baseline)

    # 1. perf-findings.json
    with open(out / "perf-findings.json", "w") as f:
        json.dump({
            "meta": {
                "target": config.get("targetUrl", "unknown"),
                "test_type": config.get("testType", "unknown"),
                "vus": config.get("vus", "unknown"),
                "duration": config.get("duration", "unknown"),
                "timestamp": datetime.now().isoformat(),
            },
            "summary": parsed,
            "sla_checks": findings,
            "baseline_comparison": comparisons,
        }, f, indent=2)

    # 2. perf-issues.csv (SLA violations only)
    violations = [f for f in findings if not f["passed"]]
    with open(out / "perf-issues.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "metric", "label", "actual", "threshold", "unit",
            "delta_pct", "severity", "status",
        ])
        writer.writeheader()
        for i, v in enumerate(violations, 1):
            writer.writerow({
                "id": f"PERF-{i:04d}",
                "metric": v["metric"],
                "label": v["label"],
                "actual": v["actual"],
                "threshold": v["threshold"],
                "unit": v["unit"],
                "delta_pct": v["delta_pct"],
                "severity": v["severity"],
                "status": "Open",
            })

    # 3. perf-report.md
    report = generate_report(parsed, findings, config, comparisons)
    with open(out / "perf-report.md", "w") as f:
        f.write(report)

    # 4. baseline-comparison.md
    if comparisons:
        baseline_report = generate_baseline_report(comparisons)
        if baseline_report:
            with open(out / "baseline-comparison.md", "w") as f:
                f.write(baseline_report)

    # Print summary
    passed = sum(1 for f in findings if f["passed"])
    failed = sum(1 for f in findings if not f["passed"])
    overall = "PASS" if failed == 0 else "FAIL"
    print(f"\nResult: {overall} ({passed} passed, {failed} failed)")
    for f in findings:
        icon = "✓" if f["passed"] else "✗"
        print(f"  {icon} {f['label']}: {f['actual']}{f['unit']} (threshold: {f['threshold']}{f['unit']})")
    print(f"\nReports written to: {out}/")


if __name__ == "__main__":
    main()
