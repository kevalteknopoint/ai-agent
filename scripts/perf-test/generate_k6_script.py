#!/usr/bin/env python3
"""
generate_k6_script.py — Generate k6 load test scripts from a JSON config.

Zero AI. Reads a test configuration and produces a ready-to-run k6 JavaScript
test script with proper scenarios, thresholds, checks, and data parameterization.

Usage:
  python3 generate_k6_script.py --config <config.json> --output <test.js>
  python3 generate_k6_script.py --url <url> --type <load|stress|soak|spike> \
    --vus <n> --duration <dur> [--endpoints <file>] --output <test.js>

Config JSON format:
  {
    "targetUrl": "https://example.com",
    "testType": "load",
    "vus": 50,
    "duration": "5m",
    "endpoints": [
      {"method": "GET", "path": "/", "name": "Homepage"},
      {"method": "GET", "path": "/api/products", "name": "Product list"},
      {"method": "POST", "path": "/api/login", "name": "Login",
       "body": {"username": "test", "password": "test123"},
       "headers": {"Content-Type": "application/json"}}
    ],
    "thresholds": {
      "http_req_duration_p95": 500,
      "http_req_duration_p99": 1000,
      "error_rate": 1
    },
    "headers": {"Authorization": "Bearer TOKEN"},
    "tags": {"env": "staging"}
  }
"""

import argparse
import json
import os
import sys
from pathlib import Path


def build_config(args):
    """Build config from either JSON file or CLI args."""
    if args.config:
        with open(args.config) as f:
            return json.load(f)

    config = {
        "targetUrl": args.url,
        "testType": args.type or "load",
        "vus": int(args.vus or 10),
        "duration": args.duration or "1m",
        "endpoints": [],
        "thresholds": {
            "http_req_duration_p95": int(args.threshold_p95 or 500),
            "http_req_duration_p99": int(args.threshold_p99 or 1000),
            "error_rate": float(args.threshold_error or 1),
        },
    }

    # Parse endpoints from file or generate default
    if args.endpoints:
        with open(args.endpoints) as f:
            eps = json.load(f)
            config["endpoints"] = eps if isinstance(eps, list) else eps.get("endpoints", [])
    elif args.endpoint:
        # --endpoint can be passed multiple times: "GET /path name"
        for ep_str in args.endpoint:
            parts = ep_str.split(None, 2)
            method = parts[0].upper() if len(parts) > 0 else "GET"
            path = parts[1] if len(parts) > 1 else "/"
            name = parts[2] if len(parts) > 2 else path
            config["endpoints"].append({"method": method, "path": path, "name": name})

    if not config["endpoints"]:
        config["endpoints"] = [{"method": "GET", "path": "/", "name": "Homepage"}]

    if args.header:
        config["headers"] = {}
        for h in args.header:
            key, _, val = h.partition(":")
            config["headers"][key.strip()] = val.strip()

    if args.ramp_up:
        config["rampUp"] = args.ramp_up

    return config


def generate_scenario(config):
    """Generate k6 scenario/stages based on test type."""
    test_type = config.get("testType", "load")
    vus = config.get("vus", 10)
    duration = config.get("duration", "1m")

    # Parse duration to seconds for stage calculations
    dur_sec = parse_duration(duration)

    if test_type == "load":
        ramp_up = config.get("rampUp", f"{max(dur_sec // 5, 10)}s")
        return {
            "stages": [
                {"duration": ramp_up, "target": vus},
                {"duration": duration, "target": vus},
                {"duration": f"{max(dur_sec // 10, 5)}s", "target": 0},
            ],
            "description": f"Load test: ramp to {vus} VUs, hold for {duration}, ramp down",
        }
    elif test_type == "stress":
        step = max(vus // 4, 1)
        step_dur = f"{max(dur_sec // 5, 30)}s"
        return {
            "stages": [
                {"duration": step_dur, "target": step},
                {"duration": step_dur, "target": step * 2},
                {"duration": step_dur, "target": step * 3},
                {"duration": step_dur, "target": vus},
                {"duration": step_dur, "target": vus + step},
                {"duration": f"{max(dur_sec // 10, 10)}s", "target": 0},
            ],
            "description": f"Stress test: incremental ramp to {vus}+ VUs to find breaking point",
        }
    elif test_type == "soak":
        ramp_up = config.get("rampUp", f"{max(dur_sec // 10, 30)}s")
        return {
            "stages": [
                {"duration": ramp_up, "target": vus},
                {"duration": duration, "target": vus},
                {"duration": f"{max(dur_sec // 10, 10)}s", "target": 0},
            ],
            "description": f"Soak test: {vus} VUs for {duration} to find memory leaks and degradation",
        }
    elif test_type == "spike":
        spike_dur = f"{max(dur_sec // 5, 10)}s"
        return {
            "stages": [
                {"duration": "10s", "target": max(vus // 10, 1)},
                {"duration": "5s", "target": vus},
                {"duration": spike_dur, "target": vus},
                {"duration": "5s", "target": max(vus // 10, 1)},
                {"duration": "30s", "target": max(vus // 10, 1)},
                {"duration": "5s", "target": 0},
            ],
            "description": f"Spike test: sudden burst to {vus} VUs, drop, measure recovery",
        }
    else:
        return {
            "stages": [{"duration": duration, "target": vus}],
            "description": f"Custom test: {vus} VUs for {duration}",
        }


def parse_duration(dur_str):
    """Parse duration string like '5m', '1h', '30s' to seconds."""
    dur_str = str(dur_str).strip()
    if dur_str.endswith("h"):
        return int(dur_str[:-1]) * 3600
    elif dur_str.endswith("m"):
        return int(dur_str[:-1]) * 60
    elif dur_str.endswith("s"):
        return int(dur_str[:-1])
    else:
        return int(dur_str)


def generate_k6_script(config):
    """Generate the full k6 JavaScript test script."""
    target_url = config["targetUrl"].rstrip("/")
    endpoints = config.get("endpoints", [{"method": "GET", "path": "/", "name": "Homepage"}])
    thresholds = config.get("thresholds", {})
    headers = config.get("headers", {})
    scenario = generate_scenario(config)

    # Build thresholds block
    threshold_lines = []
    p95 = thresholds.get("http_req_duration_p95", 500)
    p99 = thresholds.get("http_req_duration_p99", 1000)
    error_rate = thresholds.get("error_rate", 1)
    threshold_lines.append(f"    http_req_duration: ['p(95)<{p95}', 'p(99)<{p99}'],")
    threshold_lines.append(f"    http_req_failed: ['rate<{error_rate / 100}'],")
    threshold_lines.append(f"    http_reqs: ['rate>0'],")

    # Add per-endpoint thresholds
    for ep in endpoints:
        name = ep.get("name", ep["path"]).replace("'", "\\'")
        tag = name.replace(" ", "_").lower()
        threshold_lines.append(f"    'http_req_duration{{name:{tag}}}': ['p(95)<{p95}'],")

    # Build stages block
    stages_lines = []
    for stage in scenario["stages"]:
        stages_lines.append(
            f"      {{ duration: '{stage['duration']}', target: {stage['target']} }},"
        )

    # Build default headers
    header_lines = []
    for k, v in headers.items():
        header_lines.append(f"    '{k}': '{v}',")

    # Build endpoint request functions
    endpoint_funcs = []
    for i, ep in enumerate(endpoints):
        method = ep.get("method", "GET").upper()
        path = ep.get("path", "/")
        name = ep.get("name", path)
        tag = name.replace(" ", "_").lower()
        body = ep.get("body")
        ep_headers = ep.get("headers", {})

        if method == "GET":
            func = f"""  // {name}
  {{
    const res = http.get(`${{BASE_URL}}{path}`, {{
      tags: {{ name: '{tag}' }},
      headers: Object.assign({{}}, DEFAULT_HEADERS, {json.dumps(ep_headers)}),
    }});
    check(res, {{
      '{name} status 2xx': (r) => r.status >= 200 && r.status < 300,
      '{name} response time < {p95}ms': (r) => r.timings.duration < {p95},
    }});
  }}"""
        else:
            body_str = json.dumps(body) if body else "{}"
            func = f"""  // {name}
  {{
    const res = http.{method.lower()}(`${{BASE_URL}}{path}`, JSON.stringify({body_str}), {{
      tags: {{ name: '{tag}' }},
      headers: Object.assign({{}}, DEFAULT_HEADERS, {{'Content-Type': 'application/json'}}, {json.dumps(ep_headers)}),
    }});
    check(res, {{
      '{name} status 2xx': (r) => r.status >= 200 && r.status < 300,
      '{name} response time < {p95}ms': (r) => r.timings.duration < {p95},
    }});
  }}"""

        endpoint_funcs.append(func)

    # Think time between requests
    sleep_time = config.get("thinkTime", 1)

    script = f"""// ══════════════════════════════════════════════════════════════════
// k6 Load Test — Auto-generated by ai-agent perf-test toolkit
// {scenario['description']}
// Target: {target_url}
// Generated: {{date}}
//
// Run: k6 run {config.get('outputFile', 'test.js')}
// Run with JSON output: k6 run --out json=results.json {config.get('outputFile', 'test.js')}
// ══════════════════════════════════════════════════════════════════

import http from 'k6/http';
import {{ check, sleep }} from 'k6';
import {{ Rate, Trend }} from 'k6/metrics';

// ─── Custom metrics ───
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');

// ─── Configuration ───
const BASE_URL = __ENV.TARGET_URL || '{target_url}';

const DEFAULT_HEADERS = {{
{chr(10).join(header_lines) if header_lines else "    // No default headers"}
}};

// ─── Test options ───
export const options = {{
  stages: [
{chr(10).join(stages_lines)}
  ],
  thresholds: {{
{chr(10).join(threshold_lines)}
  }},
  // Graceful stop: allow in-flight requests to complete
  gracefulStop: '10s',
  // Don't throw on HTTP errors — we check them explicitly
  noConnectionReuse: false,
  userAgent: 'k6-perf-test/1.0',
}};

// ─── Setup (runs once before test) ───
export function setup() {{
  // Verify target is reachable
  const res = http.get(`${{BASE_URL}}/`);
  if (res.status === 0) {{
    throw new Error(`Target ${{BASE_URL}} is not reachable`);
  }}
  console.log(`Target ${{BASE_URL}} is reachable (status: ${{res.status}})`);
  return {{ startTime: new Date().toISOString() }};
}}

// ─── Main test function (runs per VU iteration) ───
export default function (data) {{
{(chr(10) + chr(10) + f"  sleep({sleep_time});" + chr(10)).join(endpoint_funcs)}

  sleep({sleep_time});
}}

// ─── Teardown (runs once after test) ───
export function teardown(data) {{
  console.log(`Test started at: ${{data.startTime}}`);
  console.log(`Test ended at: ${{new Date().toISOString()}}`);
}}
"""

    # Replace {date} placeholder
    from datetime import datetime
    script = script.replace("{date}", datetime.now().strftime("%Y-%m-%d %H:%M"))

    return script


def main():
    parser = argparse.ArgumentParser(description="Generate k6 load test script")
    parser.add_argument("--config", help="JSON config file path")
    parser.add_argument("--url", help="Target URL")
    parser.add_argument("--type", choices=["load", "stress", "soak", "spike"], default="load")
    parser.add_argument("--vus", type=int, default=10, help="Virtual users")
    parser.add_argument("--duration", default="1m", help="Test duration (e.g., 5m, 1h)")
    parser.add_argument("--endpoints", help="JSON file with endpoint definitions")
    parser.add_argument("--endpoint", action="append", help="Endpoint: 'METHOD /path name'")
    parser.add_argument("--header", action="append", help="Default header: 'Key: Value'")
    parser.add_argument("--threshold-p95", type=int, default=500)
    parser.add_argument("--threshold-p99", type=int, default=1000)
    parser.add_argument("--threshold-error", type=float, default=1)
    parser.add_argument("--ramp-up", help="Ramp-up duration (e.g., 30s)")
    parser.add_argument("--output", required=True, help="Output k6 script path")
    args = parser.parse_args()

    if not args.config and not args.url:
        parser.error("Provide --config <file.json> OR --url <target-url>")

    config = build_config(args)
    config["outputFile"] = os.path.basename(args.output)
    script = generate_k6_script(config)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write(script)

    print(f"Generated k6 script: {args.output}")
    print(f"  Type: {config['testType']}")
    print(f"  Target: {config['targetUrl']}")
    print(f"  VUs: {config['vus']}")
    print(f"  Duration: {config['duration']}")
    print(f"  Endpoints: {len(config.get('endpoints', []))}")


if __name__ == "__main__":
    main()
