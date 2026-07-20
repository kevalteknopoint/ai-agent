#!/usr/bin/env python3
"""build_fix_plan.py <repoPath> [--mode all|critical|domain] [--domain java|htl|eds|jsReact|css]
                     [--min-severity N] [--max-batch N] [--dry-run]

Reads all analysis/*-findings.json files from a scanned repository, filters to
open issues, groups them into dependency-safe batches, and writes a structured
fix execution plan.

The plan is consumed by the code-fix-orchestrator agent which dispatches
domain-specific fixer agents in the correct order.

Output: analysis/fix-plan.json
"""
import argparse
import datetime
import json
import os
import sys
from collections import defaultdict


# Domain detection from findings filename
DOMAIN_MAP = {
    "java": "java",
    "htl": "htl",
    "eds": "eds",
    "js-react": "jsReact",
    "css": "css",
}

# Fix layer ordering (lower = fix first)
LAYER_ORDER = {
    "config": 0,
    "model": 1,
    "service": 2,
    "controller": 3,
    "template": 4,
    "style": 5,
}

# Map categories to layers for ordering
CATEGORY_TO_LAYER = {
    # Java/Spring
    "Security": "config",
    "Spring Framework": "config",
    "Concurrency": "service",
    "Performance": "service",
    "Correctness": "model",
    # HTL
    "XSS & context handling": "template",
    "Sling Model integration": "model",
    # EDS
    "CWV — LCP": "template",
    "CWV — CLS": "style",
    "CWV — INP": "template",
    "DOM-first Patterns": "template",
    "Image & Media": "template",
    # JS/React
    "React Specific": "template",
    "Error Handling": "service",
    "Architecture": "service",
    # CSS
    "Specificity & Cascade": "style",
    "Responsive": "style",
    "Accessibility": "style",
    "Maintainability": "style",
}


def detect_domain(filename):
    """Detect domain from findings filename."""
    basename = os.path.basename(filename).lower()
    for key, domain in DOMAIN_MAP.items():
        if key in basename:
            return domain
    return "unknown"


def get_layer(issue):
    """Determine the fix layer for ordering."""
    category = issue.get("category", "")
    for cat_prefix, layer in CATEGORY_TO_LAYER.items():
        if cat_prefix.lower() in category.lower():
            return LAYER_ORDER.get(layer, 3)
    return 3  # default to controller layer


def load_findings(repo_path):
    """Load all findings from analysis/ folder."""
    analysis_dir = os.path.join(repo_path, "analysis")
    if not os.path.isdir(analysis_dir):
        print(f"ERROR: No analysis/ folder found at {analysis_dir}", file=sys.stderr)
        sys.exit(1)

    all_findings = []
    for fname in os.listdir(analysis_dir):
        if fname.endswith("-findings.json"):
            fpath = os.path.join(analysis_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                domain = detect_domain(fname)
                for issue in data.get("issues", []):
                    issue["_domain"] = domain
                    issue["_source"] = fname
                    all_findings.append(issue)
            except (json.JSONDecodeError, OSError) as e:
                print(f"WARNING: Skipping {fname}: {e}", file=sys.stderr)

    return all_findings


def filter_open(findings):
    """Filter to only open (unfixed) issues."""
    return [
        f for f in findings
        if f.get("status", "Open") in ("Open", "Partially Fixed", "")
    ]


def filter_severity(findings, min_severity=1):
    """Filter to issues at or above minimum severity."""
    return [f for f in findings if f.get("severity", 1) >= min_severity]


def filter_domain(findings, domain):
    """Filter to a specific domain."""
    return [f for f in findings if f.get("_domain") == domain]


def build_batches(findings, max_batch=8):
    """Group findings into execution batches.

    Strategy:
    1. Group by domain
    2. Within domain, sort by layer (fix-order), then severity desc
    3. Within same file, keep together (avoids merge conflicts)
    4. Chunk into batches of max_batch size
    """
    # Group by domain
    by_domain = defaultdict(list)
    for f in findings:
        by_domain[f["_domain"]].append(f)

    batches = []
    for domain, issues in by_domain.items():
        # Sort: layer asc, severity desc, file asc
        issues.sort(key=lambda x: (get_layer(x), -x.get("severity", 1), x.get("file", "")))

        # Group by file proximity
        file_groups = defaultdict(list)
        for issue in issues:
            file_groups[issue.get("file", "unknown")].append(issue)

        # Build batches respecting file grouping
        current_batch = []
        for file_path in sorted(file_groups.keys()):
            file_issues = file_groups[file_path]
            if len(current_batch) + len(file_issues) > max_batch and current_batch:
                batches.append({
                    "batchId": f"{domain}-fix-b{len(batches) + 1}",
                    "domain": domain,
                    "agent": f"{domain.replace('jsReact', 'js-react')}-code-fixer",
                    "issues": current_batch,
                    "issueCount": len(current_batch),
                })
                current_batch = []
            current_batch.extend(file_issues)

        if current_batch:
            batches.append({
                "batchId": f"{domain}-fix-b{len(batches) + 1}",
                "domain": domain,
                "agent": f"{domain.replace('jsReact', 'js-react')}-code-fixer",
                "issues": current_batch,
                "issueCount": len(current_batch),
            })

    # Sort batches by layer order (config-level fixes first)
    batches.sort(key=lambda b: min(get_layer(i) for i in b["issues"]))

    return batches


def main():
    parser = argparse.ArgumentParser(description="Build fix execution plan from scan findings")
    parser.add_argument("repoPath", help="Path to the scanned repository")
    parser.add_argument("--mode", choices=["all", "critical", "domain"], default="all")
    parser.add_argument("--domain", choices=["java", "htl", "eds", "jsReact", "css"])
    parser.add_argument("--min-severity", type=int, default=1)
    parser.add_argument("--max-batch", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.mode == "domain" and not args.domain:
        print("ERROR: --domain required when mode=domain", file=sys.stderr)
        sys.exit(1)

    # Load and filter
    findings = load_findings(args.repoPath)
    findings = filter_open(findings)

    if args.mode == "critical":
        findings = filter_severity(findings, min_severity=4)
    elif args.min_severity > 1:
        findings = filter_severity(findings, args.min_severity)

    if args.mode == "domain":
        findings = filter_domain(findings, args.domain)

    if not findings:
        print("No open findings match the filter criteria.")
        plan = {"status": "no_issues", "batches": [], "totalIssues": 0}
    else:
        batches = build_batches(findings, args.max_batch)
        plan = {
            "status": "ready",
            "generatedAt": datetime.datetime.now().isoformat(),
            "mode": args.mode,
            "domain": args.domain,
            "minSeverity": args.min_severity if args.mode != "critical" else 4,
            "totalIssues": len(findings),
            "totalBatches": len(batches),
            "severityBreakdown": {
                "critical": len([f for f in findings if f.get("severity") == 5]),
                "high": len([f for f in findings if f.get("severity") == 4]),
                "medium": len([f for f in findings if f.get("severity") == 3]),
                "low": len([f for f in findings if f.get("severity") == 2]),
                "info": len([f for f in findings if f.get("severity") == 1]),
            },
            "domainBreakdown": dict(
                (d, len([f for f in findings if f.get("_domain") == d]))
                for d in set(f.get("_domain") for f in findings)
            ),
            "batches": batches,
        }

    # Write plan
    output_dir = os.path.join(args.repoPath, "analysis")
    os.makedirs(output_dir, exist_ok=True)
    plan_path = os.path.join(output_dir, "fix-plan.json")

    # Strip internal fields from output
    for batch in plan.get("batches", []):
        for issue in batch.get("issues", []):
            issue.pop("_domain", None)
            issue.pop("_source", None)

    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(json.dumps({
        "planPath": plan_path,
        "totalIssues": plan.get("totalIssues", 0),
        "totalBatches": plan.get("totalBatches", 0),
        "dryRun": args.dry_run,
    }, indent=2))


if __name__ == "__main__":
    main()
