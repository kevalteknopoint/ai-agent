#!/usr/bin/env python3
"""
aggregate_report.py — Merge raw security tool outputs into unified reports.

Zero AI. Reads JSON output from semgrep, gitleaks, trivy, hadolint, checkov,
nuclei and produces:
  - security-report.md      (human-readable executive summary)
  - security-findings.json   (machine-readable unified findings)
  - security-issues.csv      (tracker compatible with code-scan CSV format)
  - owasp-mapping.md         (findings mapped to OWASP Top 10 2021)

Usage:
  python3 aggregate_report.py --output-dir <dir> --repo-name <name> \
    --repo-path <path> --branch <branch> --timestamp <ts> --duration <sec> \
    [--min-severity info]
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ─── OWASP Top 10 2021 mapping ───
OWASP_MAP = {
    "A01": "Broken Access Control",
    "A02": "Cryptographic Failures",
    "A03": "Injection",
    "A04": "Insecure Design",
    "A05": "Security Misconfiguration",
    "A06": "Vulnerable and Outdated Components",
    "A07": "Identification and Authentication Failures",
    "A08": "Software and Data Integrity Failures",
    "A09": "Security Logging and Monitoring Failures",
    "A10": "Server-Side Request Forgery (SSRF)",
}

# CWE → OWASP category mapping (common CWEs)
CWE_TO_OWASP = {
    "CWE-22": "A01", "CWE-23": "A01", "CWE-35": "A01", "CWE-59": "A01",
    "CWE-200": "A01", "CWE-201": "A01", "CWE-219": "A01", "CWE-264": "A01",
    "CWE-275": "A01", "CWE-276": "A01", "CWE-284": "A01", "CWE-285": "A01",
    "CWE-352": "A01", "CWE-359": "A01", "CWE-377": "A01", "CWE-402": "A01",
    "CWE-425": "A01", "CWE-441": "A01", "CWE-497": "A01", "CWE-538": "A01",
    "CWE-540": "A01", "CWE-548": "A01", "CWE-552": "A01", "CWE-566": "A01",
    "CWE-601": "A01", "CWE-639": "A01", "CWE-651": "A01", "CWE-668": "A01",
    "CWE-706": "A01", "CWE-862": "A01", "CWE-863": "A01", "CWE-913": "A01",
    "CWE-922": "A01", "CWE-1275": "A01",
    "CWE-261": "A02", "CWE-296": "A02", "CWE-310": "A02", "CWE-319": "A02",
    "CWE-321": "A02", "CWE-322": "A02", "CWE-323": "A02", "CWE-324": "A02",
    "CWE-325": "A02", "CWE-326": "A02", "CWE-327": "A02", "CWE-328": "A02",
    "CWE-329": "A02", "CWE-330": "A02", "CWE-331": "A02", "CWE-335": "A02",
    "CWE-336": "A02", "CWE-337": "A02", "CWE-338": "A02", "CWE-340": "A02",
    "CWE-347": "A02", "CWE-523": "A02", "CWE-720": "A02", "CWE-757": "A02",
    "CWE-759": "A02", "CWE-760": "A02", "CWE-780": "A02", "CWE-818": "A02",
    "CWE-916": "A02",
    "CWE-20": "A03", "CWE-74": "A03", "CWE-75": "A03", "CWE-77": "A03",
    "CWE-78": "A03", "CWE-79": "A03", "CWE-80": "A03", "CWE-83": "A03",
    "CWE-87": "A03", "CWE-88": "A03", "CWE-89": "A03", "CWE-90": "A03",
    "CWE-91": "A03", "CWE-93": "A03", "CWE-94": "A03", "CWE-95": "A03",
    "CWE-96": "A03", "CWE-97": "A03", "CWE-98": "A03", "CWE-99": "A03",
    "CWE-100": "A03", "CWE-113": "A03", "CWE-116": "A03", "CWE-138": "A03",
    "CWE-184": "A03", "CWE-470": "A03", "CWE-471": "A03", "CWE-564": "A03",
    "CWE-610": "A03", "CWE-643": "A03", "CWE-644": "A03", "CWE-652": "A03",
    "CWE-917": "A03",
    "CWE-209": "A05", "CWE-215": "A05", "CWE-256": "A05", "CWE-257": "A05",
    "CWE-260": "A05", "CWE-312": "A05", "CWE-315": "A05", "CWE-316": "A05",
    "CWE-341": "A05", "CWE-434": "A05", "CWE-497": "A05", "CWE-611": "A05",
    "CWE-614": "A05", "CWE-756": "A05", "CWE-776": "A05", "CWE-942": "A05",
    "CWE-1004": "A05", "CWE-1032": "A05",
    "CWE-937": "A06", "CWE-1035": "A06", "CWE-1104": "A06",
    "CWE-255": "A07", "CWE-259": "A07", "CWE-287": "A07", "CWE-288": "A07",
    "CWE-290": "A07", "CWE-294": "A07", "CWE-295": "A07", "CWE-297": "A07",
    "CWE-300": "A07", "CWE-302": "A07", "CWE-304": "A07", "CWE-306": "A07",
    "CWE-307": "A07", "CWE-346": "A07", "CWE-384": "A07", "CWE-521": "A07",
    "CWE-613": "A07", "CWE-620": "A07", "CWE-640": "A07", "CWE-798": "A07",
    "CWE-940": "A07",
    "CWE-345": "A08", "CWE-353": "A08", "CWE-426": "A08", "CWE-427": "A08",
    "CWE-428": "A08", "CWE-502": "A08", "CWE-565": "A08", "CWE-784": "A08",
    "CWE-829": "A08", "CWE-830": "A08", "CWE-915": "A08",
    "CWE-117": "A09", "CWE-223": "A09", "CWE-532": "A09", "CWE-778": "A09",
    "CWE-918": "A10",
}

SEVERITY_ORDER = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}


def normalize_severity(sev):
    """Normalize severity string to one of: critical, high, medium, low, info."""
    s = str(sev).lower().strip()
    if s in SEVERITY_ORDER:
        return s
    if s in ("error", "err"):
        return "high"
    if s in ("warning", "warn"):
        return "medium"
    if s in ("note", "information", "style"):
        return "info"
    return "info"


def get_owasp_category(cwe_id=None, rule_id=None, tags=None):
    """Map a finding to OWASP Top 10 category."""
    if cwe_id and cwe_id in CWE_TO_OWASP:
        return CWE_TO_OWASP[cwe_id]
    if tags:
        for tag in tags:
            t = tag.upper()
            for code in OWASP_MAP:
                if code in t:
                    return code
    if rule_id:
        r = rule_id.lower()
        if any(w in r for w in ("injection", "sqli", "xss", "command-injection", "template-injection")):
            return "A03"
        if any(w in r for w in ("crypto", "tls", "ssl", "hash", "cipher", "random")):
            return "A02"
        if any(w in r for w in ("auth", "login", "password", "credential", "session", "jwt")):
            return "A07"
        if any(w in r for w in ("access", "permission", "idor", "traversal", "csrf")):
            return "A01"
        if any(w in r for w in ("config", "misconfiguration", "header", "cors", "csp")):
            return "A05"
        if any(w in r for w in ("deseriali", "integrity")):
            return "A08"
        if any(w in r for w in ("ssrf",)):
            return "A10"
        if any(w in r for w in ("log", "monitor")):
            return "A09"
    return "A05"  # default: misconfiguration


def parse_semgrep(filepath):
    """Parse semgrep JSON output into unified findings."""
    if not os.path.isfile(filepath):
        return []
    with open(filepath) as f:
        data = json.load(f)
    findings = []
    for r in data.get("results", []):
        cwe_ids = []
        tags = []
        meta = r.get("extra", {}).get("metadata", {})
        for cwe in meta.get("cwe", []):
            if isinstance(cwe, str):
                cwe_ids.append(cwe.split(":")[0] if ":" in cwe else cwe)
        tags = meta.get("owasp", []) + meta.get("references", [])
        sev = normalize_severity(r.get("extra", {}).get("severity", "info"))
        primary_cwe = cwe_ids[0] if cwe_ids else None
        findings.append({
            "id": f"SAST-{len(findings)+1:04d}",
            "tool": "semgrep",
            "domain": "SAST",
            "rule_id": r.get("check_id", "unknown"),
            "severity": sev,
            "severity_score": SEVERITY_ORDER.get(sev, 1),
            "file": r.get("path", ""),
            "line": r.get("start", {}).get("line", 0),
            "end_line": r.get("end", {}).get("line", 0),
            "message": r.get("extra", {}).get("message", ""),
            "snippet": r.get("extra", {}).get("lines", "").strip()[:200],
            "cwe": cwe_ids,
            "owasp": get_owasp_category(primary_cwe, r.get("check_id"), tags),
            "fix_suggestion": meta.get("fix", ""),
            "references": meta.get("references", [])[:3],
        })
    return findings


def parse_gitleaks(filepath):
    """Parse gitleaks JSON output into unified findings."""
    if not os.path.isfile(filepath):
        return []
    with open(filepath) as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    findings = []
    for r in data:
        findings.append({
            "id": f"SECRET-{len(findings)+1:04d}",
            "tool": "gitleaks",
            "domain": "Secrets",
            "rule_id": r.get("RuleID", "unknown"),
            "severity": "critical",
            "severity_score": 5,
            "file": r.get("File", ""),
            "line": r.get("StartLine", 0),
            "end_line": r.get("EndLine", 0),
            "message": f"Secret detected: {r.get('Description', r.get('RuleID', 'unknown'))}",
            "snippet": f"[REDACTED — {r.get('RuleID', 'secret')} pattern match]",
            "cwe": ["CWE-798"],
            "owasp": "A07",
            "fix_suggestion": "Move secret to environment variable or vault. Rotate the exposed credential immediately.",
            "references": [],
        })
    return findings


def parse_trivy(filepath):
    """Parse trivy JSON output into unified findings."""
    if not os.path.isfile(filepath):
        return []
    with open(filepath) as f:
        data = json.load(f)
    findings = []
    for result in data.get("Results", []):
        target = result.get("Target", "")
        for v in result.get("Vulnerabilities", []):
            sev = normalize_severity(v.get("Severity", "info"))
            findings.append({
                "id": f"DEP-{len(findings)+1:04d}",
                "tool": "trivy",
                "domain": "Dependencies",
                "rule_id": v.get("VulnerabilityID", "unknown"),
                "severity": sev,
                "severity_score": SEVERITY_ORDER.get(sev, 1),
                "file": target,
                "line": 0,
                "end_line": 0,
                "message": f"{v.get('PkgName', '?')} {v.get('InstalledVersion', '?')} — {v.get('Title', v.get('VulnerabilityID', ''))}",
                "snippet": f"Package: {v.get('PkgName', '?')}, Installed: {v.get('InstalledVersion', '?')}, Fixed: {v.get('FixedVersion', 'N/A')}",
                "cwe": [v.get("CweIDs", ["CWE-1104"])[0]] if v.get("CweIDs") else ["CWE-1104"],
                "owasp": "A06",
                "fix_suggestion": f"Upgrade {v.get('PkgName', '?')} to {v.get('FixedVersion', 'latest')}" if v.get("FixedVersion") else "No fix available yet — monitor for updates",
                "references": (v.get("References", []) or [])[:3],
            })
    return findings


def parse_checkov(filepath):
    """Parse checkov JSON output into unified findings."""
    if not os.path.isfile(filepath):
        return []
    with open(filepath) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    findings = []
    check_results = []
    if isinstance(data, list):
        for entry in data:
            check_results.extend(entry.get("results", {}).get("failed_checks", []))
    elif isinstance(data, dict):
        check_results = data.get("results", {}).get("failed_checks", [])

    for c in check_results:
        sev = normalize_severity(c.get("severity", "medium"))
        findings.append({
            "id": f"CFG-{len(findings)+1:04d}",
            "tool": "checkov",
            "domain": "Config",
            "rule_id": c.get("check_id", "unknown"),
            "severity": sev,
            "severity_score": SEVERITY_ORDER.get(sev, 1),
            "file": c.get("file_path", ""),
            "line": c.get("file_line_range", [0])[0],
            "end_line": c.get("file_line_range", [0, 0])[-1],
            "message": c.get("check_name", c.get("check_id", "")),
            "snippet": "",
            "cwe": [],
            "owasp": "A05",
            "fix_suggestion": c.get("guideline", ""),
            "references": [c.get("guideline", "")] if c.get("guideline") else [],
        })
    return findings


def parse_hadolint(filepath):
    """Parse hadolint raw output."""
    if not os.path.isfile(filepath):
        return []
    # hadolint output may have been pre-processed; try JSON
    with open(filepath) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    findings = []
    items = data if isinstance(data, list) else []
    for h in items:
        sev = normalize_severity(h.get("level", "info"))
        findings.append({
            "id": f"CFG-{len(findings)+1:04d}",
            "tool": "hadolint",
            "domain": "Config",
            "rule_id": h.get("code", "unknown"),
            "severity": sev,
            "severity_score": SEVERITY_ORDER.get(sev, 1),
            "file": h.get("file", "Dockerfile"),
            "line": h.get("line", 0),
            "end_line": h.get("line", 0),
            "message": h.get("message", ""),
            "snippet": "",
            "cwe": [],
            "owasp": "A05",
            "fix_suggestion": "",
            "references": [],
        })
    return findings


def parse_nuclei(filepath):
    """Parse nuclei JSONL output into unified findings."""
    if not os.path.isfile(filepath):
        return []
    findings = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            info = r.get("info", {})
            sev = normalize_severity(info.get("severity", "info"))
            cwe_list = []
            classification = info.get("classification", {})
            if classification.get("cwe-id"):
                cwe_list = [f"CWE-{c}" for c in classification["cwe-id"]]
            findings.append({
                "id": f"DAST-{len(findings)+1:04d}",
                "tool": "nuclei",
                "domain": "DAST",
                "rule_id": r.get("template-id", "unknown"),
                "severity": sev,
                "severity_score": SEVERITY_ORDER.get(sev, 1),
                "file": r.get("matched-at", r.get("host", "")),
                "line": 0,
                "end_line": 0,
                "message": info.get("name", r.get("template-id", "")),
                "snippet": r.get("matcher-name", ""),
                "cwe": cwe_list,
                "owasp": get_owasp_category(cwe_list[0] if cwe_list else None, r.get("template-id")),
                "fix_suggestion": info.get("remediation", ""),
                "references": (info.get("reference", []) or [])[:3],
            })
    return findings


def generate_report(findings, args):
    """Generate security-report.md."""
    by_severity = {}
    for f in findings:
        by_severity.setdefault(f["severity"], []).append(f)

    by_domain = {}
    for f in findings:
        by_domain.setdefault(f["domain"], []).append(f)

    by_owasp = {}
    for f in findings:
        by_owasp.setdefault(f["owasp"], []).append(f)

    lines = [
        f"# Security Scan Report",
        f"",
        f"**Repository:** {args.repo_name}  ",
        f"**Branch:** {args.branch}  ",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"**Duration:** {args.duration}s  ",
        f"**Path:** `{args.repo_path}`  ",
        f"",
        f"## Executive Summary",
        f"",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| Critical | {len(by_severity.get('critical', []))} |",
        f"| High     | {len(by_severity.get('high', []))} |",
        f"| Medium   | {len(by_severity.get('medium', []))} |",
        f"| Low      | {len(by_severity.get('low', []))} |",
        f"| Info     | {len(by_severity.get('info', []))} |",
        f"| **Total** | **{len(findings)}** |",
        f"",
        f"## Findings by Domain",
        f"",
        f"| Domain | Count | Critical | High | Medium |",
        f"|--------|-------|----------|------|--------|",
    ]
    for domain in ["SAST", "Secrets", "Dependencies", "Config", "DAST"]:
        items = by_domain.get(domain, [])
        if items:
            crit = sum(1 for i in items if i["severity"] == "critical")
            high = sum(1 for i in items if i["severity"] == "high")
            med = sum(1 for i in items if i["severity"] == "medium")
            lines.append(f"| {domain} | {len(items)} | {crit} | {high} | {med} |")

    lines += ["", "## OWASP Top 10 Mapping", ""]
    for code in sorted(OWASP_MAP.keys()):
        items = by_owasp.get(code, [])
        if items:
            lines.append(f"### {code}: {OWASP_MAP[code]} ({len(items)} findings)")
            lines.append("")
            for f in sorted(items, key=lambda x: -x["severity_score"])[:10]:
                lines.append(f"- **[{f['severity'].upper()}]** `{f['file']}:{f['line']}` — {f['message'][:120]}")
            if len(items) > 10:
                lines.append(f"- ... and {len(items) - 10} more")
            lines.append("")

    # Top findings (critical + high)
    critical_high = [f for f in findings if f["severity_score"] >= 4]
    if critical_high:
        lines += ["## Critical & High Priority Findings", ""]
        for f in sorted(critical_high, key=lambda x: -x["severity_score"])[:25]:
            lines.append(f"### {f['id']}: {f['message'][:100]}")
            lines.append(f"")
            lines.append(f"- **Severity:** {f['severity'].upper()}")
            lines.append(f"- **Tool:** {f['tool']}")
            lines.append(f"- **File:** `{f['file']}:{f['line']}`")
            lines.append(f"- **Rule:** `{f['rule_id']}`")
            if f.get("cwe"):
                lines.append(f"- **CWE:** {', '.join(f['cwe'])}")
            lines.append(f"- **OWASP:** {f['owasp']} — {OWASP_MAP.get(f['owasp'], 'Unknown')}")
            if f.get("fix_suggestion"):
                lines.append(f"- **Fix:** {f['fix_suggestion'][:200]}")
            if f.get("snippet"):
                lines.append(f"- **Context:** `{f['snippet'][:150]}`")
            lines.append("")

    lines += [
        "---",
        f"*Generated by ai-agent security-scan toolkit. Zero AI tokens used in this scan.*",
    ]
    return "\n".join(lines)


def generate_owasp_mapping(findings):
    """Generate owasp-mapping.md with detailed OWASP Top 10 breakdown."""
    by_owasp = {}
    for f in findings:
        by_owasp.setdefault(f["owasp"], []).append(f)

    lines = [
        "# OWASP Top 10 (2021) — Findings Mapping",
        "",
        "| # | Category | Findings | Critical | High | Medium | Low |",
        "|---|----------|----------|----------|------|--------|-----|",
    ]
    for code in sorted(OWASP_MAP.keys()):
        items = by_owasp.get(code, [])
        c = sum(1 for i in items if i["severity"] == "critical")
        h = sum(1 for i in items if i["severity"] == "high")
        m = sum(1 for i in items if i["severity"] == "medium")
        lo = sum(1 for i in items if i["severity"] == "low")
        status = "🔴" if c > 0 else "🟠" if h > 0 else "🟡" if m > 0 else "🟢"
        lines.append(f"| {status} {code} | {OWASP_MAP[code]} | {len(items)} | {c} | {h} | {m} | {lo} |")

    lines += ["", "---", "*Zero AI tokens used in this mapping.*"]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Aggregate security scan results")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--duration", default="0")
    parser.add_argument("--min-severity", default="info")
    args = parser.parse_args()

    out = Path(args.output_dir)
    min_sev = SEVERITY_ORDER.get(args.min_severity, 1)

    # Parse all raw tool outputs
    all_findings = []
    all_findings.extend(parse_semgrep(out / "sast-findings-raw.json"))
    all_findings.extend(parse_gitleaks(out / "secrets-findings-raw.json"))
    all_findings.extend(parse_trivy(out / "dependency-findings-raw.json"))
    all_findings.extend(parse_hadolint(out / "hadolint-raw.json"))
    all_findings.extend(parse_checkov(out / "checkov-raw.json"))
    all_findings.extend(parse_nuclei(out / "dast-findings-raw.jsonl"))

    # Re-number IDs globally
    for i, f in enumerate(all_findings, 1):
        f["id"] = f"{f['domain'][:4].upper()}-{i:04d}"

    # Filter by minimum severity
    filtered = [f for f in all_findings if f["severity_score"] >= min_sev]

    # Sort: critical first, then by domain
    filtered.sort(key=lambda x: (-x["severity_score"], x["domain"], x["file"], x["line"]))

    # 1. security-findings.json
    with open(out / "security-findings.json", "w") as f:
        json.dump({
            "meta": {
                "repo": args.repo_name,
                "branch": args.branch,
                "timestamp": args.timestamp,
                "duration_seconds": int(args.duration),
                "total_findings": len(filtered),
                "tools_used": list(set(f["tool"] for f in filtered)),
            },
            "findings": filtered,
        }, f, indent=2)

    # 2. security-issues.csv
    with open(out / "security-issues.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "domain", "severity", "owasp", "rule_id", "file", "line",
            "message", "tool", "cwe", "status",
        ])
        writer.writeheader()
        for finding in filtered:
            writer.writerow({
                "id": finding["id"],
                "domain": finding["domain"],
                "severity": finding["severity"],
                "owasp": finding["owasp"],
                "rule_id": finding["rule_id"],
                "file": finding["file"],
                "line": finding["line"],
                "message": finding["message"][:200],
                "tool": finding["tool"],
                "cwe": ",".join(finding.get("cwe", [])),
                "status": "Open",
            })

    # 3. security-report.md
    report = generate_report(filtered, args)
    with open(out / "security-report.md", "w") as f:
        f.write(report)

    # 4. owasp-mapping.md
    owasp = generate_owasp_mapping(filtered)
    with open(out / "owasp-mapping.md", "w") as f:
        f.write(owasp)

    print(f"Generated {len(filtered)} findings across {len(set(f['domain'] for f in filtered))} domain(s)")
    print(f"  security-report.md")
    print(f"  security-findings.json")
    print(f"  security-issues.csv")
    print(f"  owasp-mapping.md")


if __name__ == "__main__":
    main()
