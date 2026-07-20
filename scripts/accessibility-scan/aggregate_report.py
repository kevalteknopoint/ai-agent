#!/usr/bin/env python3
"""
aggregate_report.py — Accessibility Findings Aggregator

Reads raw output from axe-core, pa11y, Lighthouse, html-validate, and eslint,
then produces a consolidated report with:
  - Unified severity mapping
  - WCAG Success Criterion references
  - Deduplication across tools
  - Categorization by WCAG principle (P/O/U/R)
  - Prioritized fix recommendations

Zero AI tokens — pure data transformation.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ─── Severity Mapping ───
IMPACT_TO_SEVERITY = {
    "critical": 5,
    "serious": 4,
    "moderate": 3,
    "minor": 2,
    "info": 1,
}

# ─── WCAG Principle from SC number ───
def get_principle(sc: str) -> str:
    """Map WCAG SC number to principle."""
    if not sc:
        return "Unknown"
    try:
        first_digit = int(sc.split(".")[0])
        return {1: "Perceivable", 2: "Operable", 3: "Understandable", 4: "Robust"}.get(
            first_digit, "Unknown"
        )
    except (ValueError, IndexError):
        return "Unknown"


def parse_axe_results(output_dir: Path) -> list:
    """Parse axe-core JSON results."""
    findings = []
    axe_dir = output_dir / "axe-results"
    if not axe_dir.exists():
        return findings

    for json_file in axe_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)

            # axe-core output can be array of results or single object
            results = data if isinstance(data, list) else [data]

            for result in results:
                violations = result.get("violations", [])
                for violation in violations:
                    for node in violation.get("nodes", []):
                        finding = {
                            "tool": "axe-core",
                            "rule_id": violation.get("id", ""),
                            "description": violation.get("description", ""),
                            "help": violation.get("help", ""),
                            "help_url": violation.get("helpUrl", ""),
                            "impact": violation.get("impact", "moderate"),
                            "severity": IMPACT_TO_SEVERITY.get(
                                violation.get("impact", "moderate"), 3
                            ),
                            "wcag_tags": [
                                t
                                for t in violation.get("tags", [])
                                if t.startswith("wcag")
                            ],
                            "element": node.get("html", ""),
                            "selector": ", ".join(node.get("target", [])),
                            "page": result.get("url", json_file.stem),
                            "source_file": str(json_file),
                            "failure_summary": node.get("failureSummary", ""),
                        }
                        findings.append(finding)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Warning: Could not parse {json_file}: {e}", file=sys.stderr)

    return findings


def parse_pa11y_results(output_dir: Path) -> list:
    """Parse pa11y JSON results."""
    findings = []
    pa11y_dir = output_dir / "pa11y-results"
    if not pa11y_dir.exists():
        return findings

    for json_file in pa11y_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)

            issues = data if isinstance(data, list) else data.get("issues", [])

            for issue in issues:
                type_map = {"error": 4, "warning": 3, "notice": 2}
                finding = {
                    "tool": "pa11y",
                    "rule_id": issue.get("code", ""),
                    "description": issue.get("message", ""),
                    "impact": issue.get("type", "warning"),
                    "severity": type_map.get(issue.get("type", "warning"), 3),
                    "element": issue.get("context", ""),
                    "selector": issue.get("selector", ""),
                    "page": json_file.stem,
                    "source_file": str(json_file),
                    "wcag_tags": extract_wcag_from_code(issue.get("code", "")),
                }
                findings.append(finding)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Warning: Could not parse {json_file}: {e}", file=sys.stderr)

    return findings


def parse_lighthouse_results(output_dir: Path) -> list:
    """Parse Lighthouse accessibility audit results."""
    findings = []
    lh_dir = output_dir / "lighthouse-results"
    if not lh_dir.exists():
        return findings

    for json_file in lh_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)

            audits = data.get("audits", {})
            categories = data.get("categories", {})

            # Get accessibility score
            a11y_score = categories.get("accessibility", {}).get("score", None)

            for audit_id, audit in audits.items():
                if audit.get("score") == 0:  # Failed audits
                    details = audit.get("details", {})
                    items = details.get("items", [])

                    for item in items:
                        finding = {
                            "tool": "lighthouse",
                            "rule_id": audit_id,
                            "description": audit.get("description", ""),
                            "help": audit.get("title", ""),
                            "impact": "serious" if audit.get("weight", 0) > 3 else "moderate",
                            "severity": 4 if audit.get("weight", 0) > 3 else 3,
                            "element": item.get("node", {}).get("snippet", ""),
                            "selector": item.get("node", {}).get("selector", ""),
                            "page": json_file.stem,
                            "source_file": str(json_file),
                            "wcag_tags": [],
                            "lighthouse_score": a11y_score,
                        }
                        findings.append(finding)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Warning: Could not parse {json_file}: {e}", file=sys.stderr)

    return findings


def parse_pattern_findings(output_dir: Path) -> list:
    """Parse pattern-based grep findings."""
    findings = []
    pattern_file = output_dir / "pattern-findings.txt"
    if not pattern_file.exists():
        return findings

    current_category = ""
    with open(pattern_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                current_category = line[3:]
            elif line and not line.startswith("#"):
                # Parse grep output: file:line:content
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    finding = {
                        "tool": "pattern-scan",
                        "rule_id": current_category.lower().replace(" ", "-"),
                        "description": current_category,
                        "impact": "moderate",
                        "severity": 3,
                        "element": parts[2].strip()[:200],
                        "file": parts[0],
                        "line": parts[1],
                        "page": "code",
                        "source_file": str(pattern_file),
                        "wcag_tags": category_to_wcag(current_category),
                    }
                    findings.append(finding)

    return findings


def extract_wcag_from_code(code: str) -> list:
    """Extract WCAG SC references from pa11y rule codes."""
    import re
    matches = re.findall(r"WCAG2[A]+\.Principle(\d)\.Guideline(\d+_\d+)\.(\d+_\d+_\d+)", code)
    tags = []
    for match in matches:
        sc = f"{match[0]}.{match[1].replace('_', '.')}.{match[2].replace('_', '.')}"
        tags.append(f"wcag{sc}")
    return tags


def category_to_wcag(category: str) -> list:
    """Map pattern category to likely WCAG SC."""
    mapping = {
        "images without alt attribute": ["wcag1.1.1"],
        "html without lang attribute": ["wcag3.1.1"],
        "potentially empty links": ["wcag2.4.4"],
        "inputs potentially missing labels": ["wcag1.3.1", "wcag3.3.2"],
        "positive tabindex": ["wcag2.4.3"],
        "autoplay media": ["wcag1.4.2"],
        "buttons without type attribute": ["wcag4.1.2"],
        "click handlers potentially missing keyboard support": ["wcag2.1.1"],
        "css outline removal": ["wcag2.4.7"],
    }
    return mapping.get(category.lower(), [])


def deduplicate_findings(findings: list) -> list:
    """Remove duplicate findings across tools (same element + same violation)."""
    seen = set()
    unique = []

    for f in findings:
        # Create a dedup key from element + rule category
        key = (
            f.get("selector", f.get("element", ""))[:100],
            f.get("rule_id", ""),
            f.get("page", ""),
        )
        if key not in seen:
            seen.add(key)
            unique.append(f)
        else:
            # If we've seen this before, increase confidence
            for existing in unique:
                existing_key = (
                    existing.get("selector", existing.get("element", ""))[:100],
                    existing.get("rule_id", ""),
                    existing.get("page", ""),
                )
                if existing_key == key:
                    existing["confirmed_by_multiple_tools"] = True
                    break

    return unique


def generate_report(findings: list, output_dir: Path, standard: str, level: str, timestamp: str):
    """Generate the consolidated markdown report."""
    
    # Sort by severity (desc), then by principle
    findings.sort(key=lambda f: (-f.get("severity", 3), f.get("rule_id", "")))

    # Group by principle
    by_principle = defaultdict(list)
    for f in findings:
        wcag_tags = f.get("wcag_tags", [])
        principle = "Unknown"
        for tag in wcag_tags:
            # Extract first digit from wcag tag
            import re
            match = re.search(r"(\d)", tag)
            if match:
                principle = get_principle(match.group(1))
                break
        by_principle[principle].append(f)

    # Count by severity
    severity_counts = defaultdict(int)
    for f in findings:
        sev = f.get("severity", 3)
        severity_counts[sev] += 1

    # Get Lighthouse score if available
    lh_score = None
    for f in findings:
        if "lighthouse_score" in f:
            lh_score = f["lighthouse_score"]
            break

    # ─── Write Summary JSON ───
    summary = {
        "timestamp": timestamp,
        "standard": standard,
        "level": level,
        "total_findings": len(findings),
        "by_severity": {
            "critical": severity_counts.get(5, 0),
            "serious": severity_counts.get(4, 0),
            "moderate": severity_counts.get(3, 0),
            "minor": severity_counts.get(2, 0),
        },
        "by_principle": {k: len(v) for k, v in by_principle.items()},
        "lighthouse_score": lh_score,
        "tools_used": list(set(f.get("tool", "") for f in findings)),
        "multi_tool_confirmed": sum(
            1 for f in findings if f.get("confirmed_by_multiple_tools")
        ),
    }

    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # ─── Write Findings JSON ───
    with open(output_dir / "findings.json", "w") as f:
        json.dump(findings, f, indent=2, default=str)

    # ─── Write Markdown Report ───
    report_lines = [
        f"# Accessibility Scan Report",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Standard:** {standard.upper()} Level {level.upper()}",
        f"**Total Violations:** {len(findings)}",
        f"",
    ]

    if lh_score is not None:
        score_pct = int(lh_score * 100)
        report_lines.append(f"**Lighthouse Accessibility Score:** {score_pct}/100")
        report_lines.append("")

    # Severity summary
    report_lines.extend([
        "## Summary",
        "",
        "| Severity | Count | Action |",
        "|----------|-------|--------|",
        f"| Critical (5) | {severity_counts.get(5, 0)} | Fix immediately — blocks access |",
        f"| Serious (4) | {severity_counts.get(4, 0)} | Fix soon — significant barriers |",
        f"| Moderate (3) | {severity_counts.get(3, 0)} | Fix planned — causes difficulty |",
        f"| Minor (2) | {severity_counts.get(2, 0)} | Fix when possible — annoying |",
        "",
    ])

    # By principle
    for principle in ["Perceivable", "Operable", "Understandable", "Robust", "Unknown"]:
        issues = by_principle.get(principle, [])
        if not issues:
            continue

        report_lines.extend([
            f"## {principle}",
            "",
            f"*{len(issues)} violation(s)*",
            "",
        ])

        for i, issue in enumerate(issues[:20], 1):  # Cap at 20 per principle
            sev_label = {5: "CRITICAL", 4: "SERIOUS", 3: "MODERATE", 2: "MINOR"}.get(
                issue.get("severity", 3), "MODERATE"
            )
            report_lines.extend([
                f"### {i}. [{sev_label}] {issue.get('help', issue.get('description', 'Unknown'))}",
                "",
                f"- **Rule:** `{issue.get('rule_id', 'N/A')}`",
                f"- **Tool:** {issue.get('tool', 'N/A')}",
                f"- **WCAG:** {', '.join(issue.get('wcag_tags', ['N/A']))}",
                f"- **Element:** `{issue.get('element', 'N/A')[:120]}`",
                f"- **Selector:** `{issue.get('selector', 'N/A')}`",
                f"- **Page:** {issue.get('page', 'N/A')}",
            ])

            if issue.get("confirmed_by_multiple_tools"):
                report_lines.append("- **Confidence:** HIGH (confirmed by multiple tools)")

            if issue.get("help_url"):
                report_lines.append(f"- **Reference:** {issue['help_url']}")

            report_lines.append("")

        if len(issues) > 20:
            report_lines.append(f"*... and {len(issues) - 20} more {principle} violations*\n")

    # Footer
    report_lines.extend([
        "---",
        "",
        "## Important Notes",
        "",
        "1. Automated tools typically catch 30-50% of accessibility issues",
        "2. Manual testing with assistive technologies is essential",
        "3. Issues confirmed by multiple tools have higher confidence",
        "4. Some findings may be false positives — review in context",
        "",
        "*Generated by bmad-accessibility-scan (deterministic CLI tools)*",
    ])

    with open(output_dir / "report.md", "w") as f:
        f.write("\n".join(report_lines))

    print(f"  ✓ Report: {output_dir / 'report.md'}")
    print(f"  ✓ Summary: {output_dir / 'summary.json'}")
    print(f"  ✓ Findings: {output_dir / 'findings.json'}")


def main():
    parser = argparse.ArgumentParser(description="Aggregate accessibility scan results")
    parser.add_argument("--output-dir", required=True, help="Directory with scan results")
    parser.add_argument("--standard", default="wcag2.1", help="WCAG standard used")
    parser.add_argument("--level", default="aa", help="Conformance level")
    parser.add_argument("--timestamp", default=datetime.now().strftime("%Y%m%d_%H%M%S"))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"  Aggregating results from: {output_dir}")

    # Collect findings from all tools
    all_findings = []
    all_findings.extend(parse_axe_results(output_dir))
    all_findings.extend(parse_pa11y_results(output_dir))
    all_findings.extend(parse_lighthouse_results(output_dir))
    all_findings.extend(parse_pattern_findings(output_dir))

    print(f"  Raw findings: {len(all_findings)}")

    # Deduplicate
    unique_findings = deduplicate_findings(all_findings)
    print(f"  After dedup: {len(unique_findings)}")

    # Generate report
    generate_report(unique_findings, output_dir, args.standard, args.level, args.timestamp)


if __name__ == "__main__":
    main()
