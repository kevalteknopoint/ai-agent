#!/usr/bin/env python3
"""build_issues_csv.py <findings.json> <output.csv>

Deterministic tracker builder shared by every code-scan analyzer agent.
Analyzer agents emit findings as plain JSON (cheap, no formatting tokens
spent); this script turns that JSON into the standard per-analyzer CSV
tracker. Stdlib only — no dependency to install, so a freshly cloned copy
of this toolkit works with zero setup.

findings.json shape:
{
  "issues": [
    {
      "id": "001", "severity": 5, "severityLabel": "Critical",
      "file": "path/to/file.ext", "line": 24, "category": "XSS & context handling",
      "problem": "...", "impact": "...",
      "currentCode": "...", "recommendedFix": "...", "optimizedExample": "...",
      "complexity": "Low|Med|High", "estHours": 1.5
    }, ...
  ]
}

Rows are written pre-sorted by severity desc, then file path asc, so the
CSV reads in the same priority order as the Markdown report without needing
a spreadsheet tool's sort/filter UI.
"""
import csv
import json
import sys

COLUMNS = [
    ("Issue ID", "id"),
    ("Severity", "severity"),
    ("Severity Label", "severityLabel"),
    ("File", "file"),
    ("Line", "line"),
    ("Category", "category"),
    ("Problem", "problem"),
    ("Impact", "impact"),
    ("Current Code", "currentCode"),
    ("Recommended Fix", "recommendedFix"),
    ("Optimized Example", "optimizedExample"),
    ("Complexity", "complexity"),
    ("Est. Hours", "estHours"),
]


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: build_issues_csv.py <findings.json> <output.csv>\n")
        sys.exit(1)

    findings_path, output_path = sys.argv[1], sys.argv[2]
    with open(findings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    issues = data.get("issues", [])

    issues.sort(key=lambda i: (-int(i.get("severity") or 0), str(i.get("file") or "")))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([label for label, _key in COLUMNS])
        for issue in issues:
            writer.writerow([issue.get(key, "") for _label, key in COLUMNS])

    print(json.dumps({"written": output_path, "issueCount": len(issues)}))


if __name__ == "__main__":
    main()
