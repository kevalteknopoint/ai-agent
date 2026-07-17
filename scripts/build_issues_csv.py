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
      "complexity": "Low|Med|High", "estHours": 1.5,

      // added by a rescan (scripts/apply_verdicts.py) — absent on a first scan
      "status": "Open|Fixed|Partially Fixed|Not Applicable|Unverifiable",
      "statusDetail": "...",
      "verifiedFile": "path/where/it/lives/now.ext", "verifiedLine": 78,
      "firstSeenCommit": "a1b2c3d", "lastVerifiedDate": "2026-07-17",
      "lastVerifiedCommit": "e4f5a6b", "fixedInCommit": "e4f5a6b"
    }, ...
  ]
}

Rows are written pre-sorted by status (open work first), then severity desc,
then file path asc, so the CSV reads in the same priority order as the
Markdown report without needing a spreadsheet tool's sort/filter UI. On a
first scan every issue is Open, so that ordering collapses to the original
severity-then-file order.
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
    ("Status", "status"),
    ("Status Detail", "statusDetail"),
    # "File"/"Line" stay as first reported; these two say where the issue lives
    # now. They differ when code moved under the finding — keeping both means a
    # rescan never erases the original pointer.
    ("Verified File", "verifiedFile"),
    ("Verified Line", "verifiedLine"),
    ("First Seen", "firstSeenCommit"),
    ("Last Verified", "lastVerifiedDate"),
    ("Last Verified Commit", "lastVerifiedCommit"),
    ("Fixed In Commit", "fixedInCommit"),
]

DEFAULT_STATUS = "Open"

# Canonical statuses, in the order a human wants to read them: what still
# needs work, then what needs a second look, then what's done.
STATUS_ORDER = {
    "Open": 0,
    "Partially Fixed": 1,
    "Unverifiable": 2,
    "Not Applicable": 3,
    "Fixed": 4,
}

# Statuses that mean "this issue needs no further looking at". Defined here,
# next to normalize_status, because every consumer must agree on the set — a
# rescan planner that thought "resolved" was non-terminal while the merger
# thought it was Fixed would re-verify the issue and then report a phantom
# regression when the verifier said Open.
TERMINAL_STATUSES = {"Fixed", "Not Applicable"}

# Verifier agents write their verdict files with the Write tool, so the status
# string is model-authored and can drift in case/phrasing. Normalize on read
# rather than trusting the enum to have held.
STATUS_ALIASES = {
    "open": "Open",
    "still open": "Open",
    "not fixed": "Open",
    "unfixed": "Open",
    "present": "Open",
    "regressed": "Open",
    "fixed": "Fixed",
    "resolved": "Fixed",
    "closed": "Fixed",
    "partially fixed": "Partially Fixed",
    "partial": "Partially Fixed",
    "partially-fixed": "Partially Fixed",
    "mitigated": "Partially Fixed",
    "not applicable": "Not Applicable",
    "not-applicable": "Not Applicable",
    "n/a": "Not Applicable",
    "na": "Not Applicable",
    "removed": "Not Applicable",
    "obsolete": "Not Applicable",
    "unverifiable": "Unverifiable",
    "unknown": "Unverifiable",
    "unclear": "Unverifiable",
}


def normalize_status(value):
    """Map a free-form status string onto the canonical vocabulary.

    A missing/empty status means "nobody has looked at this yet" → Open.
    Anything present but unrecognized becomes Unverifiable, never Fixed — a
    status we can't parse must not be able to silently close a security
    finding. Either way the answer is never Fixed, which is the property that
    matters.
    """
    if value is None or str(value).strip() == "":
        return DEFAULT_STATUS
    raw = str(value).strip()
    return STATUS_ALIASES.get(raw.lower(), "Unverifiable")


def issue_key(issue):
    """Canonical string ID for an issue.

    Shared so the rescan planner and the verdict merger agree on what an
    issue's ID *is*. They must produce byte-identical keys: the planner hands
    IDs to a verifier agent and the merger matches its verdicts back by string
    equality, so `str(None)` on one side and `""` on the other silently
    strands the issue as permanently unverifiable.

    Returns "" for an issue with no usable ID — callers treat that as
    unidentifiable rather than inventing a key.
    """
    return str(issue.get("id") or "").strip()


def sort_issues(issues):
    return sorted(
        issues,
        key=lambda i: (
            STATUS_ORDER.get(normalize_status(i.get("status")), 0),
            -int(i.get("severity") or 0),
            str(i.get("file") or ""),
        ),
    )


def write_csv(issues, output_path):
    """Write the tracker CSV. Importable so apply_verdicts.py can rebuild the
    tracker in the same call that updates the JSON — the two must never drift
    apart, and that is easier to guarantee here than in an agent's prompt."""
    rows = sort_issues(issues)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([label for label, _key in COLUMNS])
        for issue in rows:
            writer.writerow([
                normalize_status(issue.get("status")) if key == "status" else issue.get(key, "")
                for _label, key in COLUMNS
            ])
    return len(rows)


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: build_issues_csv.py <findings.json> <output.csv>\n")
        sys.exit(1)

    findings_path, output_path = sys.argv[1], sys.argv[2]
    with open(findings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    issues = data.get("issues", [])

    count = write_csv(issues, output_path)
    print(json.dumps({"written": output_path, "issueCount": count}))


if __name__ == "__main__":
    main()
