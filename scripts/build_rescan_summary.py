#!/usr/bin/env python3
"""build_rescan_summary.py <repoPath> [--output analysis/rescan-summary.md]

Deterministic cross-domain rescan summary. Reads every
`analysis/*-analysis-findings.json` after a rescan has written statuses back
and renders one Markdown page answering the question a rescan exists to
answer: what got fixed, what's still open, and what regressed.

Written by a script rather than a model because every number here is already
in the JSON — paying an agent to retype them would risk the counts in the
summary disagreeing with the counts in the tracker.

Prints a JSON summary on stdout.
"""
import argparse
import datetime
import glob
import json
import os

from build_issues_csv import normalize_status

STATUSES = ["Open", "Partially Fixed", "Unverifiable", "Not Applicable", "Fixed"]
OPEN_STATUSES = {"Open", "Partially Fixed"}
SEVERITY_LABELS = {5: "Critical", 4: "High", 3: "Medium", 2: "Low", 1: "Info"}
MAX_LISTED_OPEN = 25


def latest_run(data):
    history = data.get("scanHistory") or []
    return history[-1] if history else {}


def collect(analysis_dir):
    domains = []
    for path in sorted(glob.glob(os.path.join(analysis_dir, "*-analysis-findings.json"))):
        domain = os.path.basename(path)[: -len("-analysis-findings.json")]
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        issues = data.get("issues", [])
        counts = {s: 0 for s in STATUSES}
        for issue in issues:
            counts[normalize_status(issue.get("status"))] += 1
        domains.append({
            "domain": domain,
            "issues": issues,
            "counts": counts,
            "total": len(issues),
            "run": latest_run(data),
            "csv": f"analysis/{domain}-analysis-issues.csv",
        })
    return domains


def location(issue):
    """Where the issue is *now*, falling back to where it was first found.

    A rescan that watched code move under a finding records verifiedFile /
    verifiedLine; pointing a reader at the stale original path would send them
    to code that no longer has the bug.
    """
    path = issue.get("verifiedFile") or issue.get("file") or "?"
    line = issue.get("verifiedLine") or issue.get("line") or "?"
    moved = bool(issue.get("verifiedFile")) and issue.get("verifiedFile") != issue.get("file")
    return f"{path}:{line}", moved


def issue_line(domain, issue):
    severity = int(issue.get("severity") or 0)
    label = issue.get("severityLabel") or SEVERITY_LABELS.get(severity, "?")
    where, moved = location(issue)
    status = normalize_status(issue.get("status"))
    detail = str(issue.get("statusDetail") or "").strip()
    tags = []
    if status == "Partially Fixed":
        tags.append("partially fixed")
    if moved:
        tags.append(f"moved from {issue.get('file')}")
    tag = f" _({'; '.join(tags)})_" if tags else ""
    suffix = f" — {detail}" if detail and status == "Partially Fixed" else ""
    return (
        f"- **{label}** · `{issue.get('id')}` · {domain} · "
        f"`{where}` — {issue.get('problem')}{tag}{suffix}"
    )


def render(repo_path, domains, date):
    totals = {s: 0 for s in STATUSES}
    for d in domains:
        for s in STATUSES:
            totals[s] += d["counts"][s]
    grand = sum(totals.values())

    run = next((d["run"] for d in domains if d.get("run")), {})
    commit = run.get("commit", "")
    branch = run.get("branch", "")

    resolved = totals["Fixed"] + totals["Not Applicable"]
    fix_rate = (resolved / grand * 100) if grand else 0.0
    still_open = totals["Open"] + totals["Partially Fixed"]

    newly_fixed = [(d["domain"], i) for d in domains for i in d["run"].get("newlyFixed", [])]
    regressed = [(d["domain"], i) for d in domains for i in d["run"].get("regressed", [])]

    out = []
    out.append("# Code-scan Rescan Summary")
    out.append("")
    out.append(f"Repo: `{os.path.basename(repo_path)}`  ")
    out.append(f"Branch: `{branch or 'unknown'}` · Commit: `{commit or 'unknown'}`  ")
    out.append(f"Date: {date}")
    out.append("")
    out.append("This run re-verified findings from the previous scan against the current")
    out.append("code. It did not search for new issues — run a full scan for that.")
    out.append("")
    out.append("## Status")
    out.append("")
    out.append("| Domain | Total | Open | Partially Fixed | Fixed | N/A | Unverifiable |")
    out.append("|---|---|---|---|---|---|---|")
    for d in domains:
        c = d["counts"]
        out.append(
            f"| {d['domain']} | {d['total']} | {c['Open']} | {c['Partially Fixed']} | "
            f"{c['Fixed']} | {c['Not Applicable']} | {c['Unverifiable']} |"
        )
    out.append(
        f"| **Total** | **{grand}** | **{totals['Open']}** | **{totals['Partially Fixed']}** | "
        f"**{totals['Fixed']}** | **{totals['Not Applicable']}** | **{totals['Unverifiable']}** |"
    )
    out.append("")
    out.append(f"**Resolved: {resolved}/{grand} ({fix_rate:.0f}%)** · Still open: {still_open}")
    out.append("")

    if regressed:
        out.append("## ⚠️ Regressions")
        out.append("")
        out.append("Previously marked Fixed, found present again:")
        out.append("")
        for domain, issue_id in regressed:
            out.append(f"- `{issue_id}` · {domain}")
        out.append("")

    if newly_fixed:
        out.append("## Fixed since last scan")
        out.append("")
        for domain, issue_id in newly_fixed:
            out.append(f"- `{issue_id}` · {domain}")
        out.append("")

    open_issues = [
        (d["domain"], i) for d in domains for i in d["issues"]
        if normalize_status(i.get("status")) in OPEN_STATUSES
    ]
    open_issues.sort(key=lambda t: (-int(t[1].get("severity") or 0), t[0], str(t[1].get("file") or "")))

    out.append("## Still open")
    out.append("")
    if not open_issues:
        out.append("Nothing open — every prior finding is fixed or no longer applicable. 🎉")
    else:
        for domain, issue in open_issues[:MAX_LISTED_OPEN]:
            out.append(issue_line(domain, issue))
        if len(open_issues) > MAX_LISTED_OPEN:
            out.append("")
            out.append(
                f"_…and {len(open_issues) - MAX_LISTED_OPEN} more. Full list in the per-domain CSV trackers._"
            )
    out.append("")

    unverifiable = [
        (d["domain"], i) for d in domains for i in d["issues"]
        if normalize_status(i.get("status")) == "Unverifiable"
    ]
    if unverifiable:
        out.append("## Needs a human look")
        out.append("")
        out.append("The verifier could not reach a confident verdict on these:")
        out.append("")
        for domain, issue in unverifiable:
            detail = str(issue.get("statusDetail") or "no detail given").strip()
            where, _moved = location(issue)
            out.append(f"- `{issue.get('id')}` · {domain} · `{where}` — {detail}")
        out.append("")

    out.append("## Trackers")
    out.append("")
    for d in domains:
        out.append(f"- `{d['csv']}`")
    out.append("")

    return "\n".join(out), {
        "total": grand,
        "counts": totals,
        "resolved": resolved,
        "stillOpen": still_open,
        "fixRate": round(fix_rate, 1),
        "newlyFixed": len(newly_fixed),
        "regressed": len(regressed),
    }


def main():
    parser = argparse.ArgumentParser(description="Render a cross-domain rescan summary")
    parser.add_argument("repoPath")
    parser.add_argument("--output", default=None)
    parser.add_argument("--date", default=None)
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repoPath)
    analysis_dir = os.path.join(repo_path, "analysis")
    date = args.date or datetime.date.today().isoformat()

    domains = collect(analysis_dir)
    if not domains:
        print(json.dumps({"error": f"no findings JSON in {analysis_dir}"}))
        return

    markdown, stats = render(repo_path, domains, date)
    output = args.output or os.path.join(analysis_dir, "rescan-summary.md")
    with open(output, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(json.dumps({"written": output, "domains": [d["domain"] for d in domains], **stats}))


if __name__ == "__main__":
    main()
