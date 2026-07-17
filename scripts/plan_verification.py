#!/usr/bin/env python3
"""plan_verification.py <repoPath> [--batch-size N] [--recheck-fixed]

Deterministic rescan planner for the code-scan system. Detects whether a repo
already carries an ./analysis/ folder from a prior scan and, if so, turns the
existing findings JSON into a batched verification plan — which issues to
re-check, grouped so one verifier agent reads one slice of the codebase.

Runs with zero LLM tokens: deciding "has this repo been scanned before" and
"which issues still need checking" is a filesystem + JSON question, never a
judgment call.

Writes `<repoPath>/analysis/.verify/plan.json` (the full plan, read by the
verifier agents directly off disk so no model has to retype it) and prints a
compact summary on stdout for the orchestrator to return.

Stale verdict files from an earlier interrupted run are purged here, at plan
time — that is the only safe moment to do it, since the merge step globs the
whole `.verify/` directory and would otherwise fold a previous run's verdicts
into this one's results.

Summary shape (stdout):
{
  "present": true,
  "repoPath": "/abs/path",
  "analysisDir": "/abs/path/analysis",
  "planPath": "/abs/path/analysis/.verify/plan.json",
  "batchSize": 12,
  "recheckFixed": false,
  "domains": [
    {"domain":"java","findingsPath":"analysis/java-analysis-findings.json",
     "totalIssues":42,"toVerify":40,"skippedFixed":2,"duplicateIds":[],
     "unidentified":0,"batchIds":["java-b1","java-b2"]}
  ],
  "totals": {"domains":1,"totalIssues":42,"toVerify":40,"skippedFixed":2,
             "excluded":0,"batches":2}
}

`present:false` means no prior analysis — the caller should run a full scan.

Issues excluded from verification are counted, never dropped quietly:
`skippedFixed` (terminal — pass --recheck-fixed to include them),
`duplicateIds` (same ID on two issues: a verdict can't be routed back
unambiguously), `unidentified` (no ID at all), and `errors` (a findings file
that wouldn't parse). A caller that reports "all clear" while `excluded` is
non-zero is lying to someone.
"""
import argparse
import glob
import json
import os
import shutil
import sys

from build_issues_csv import TERMINAL_STATUSES, issue_key, normalize_status

FINDINGS_SUFFIX = "-analysis-findings.json"


def domain_paths(analysis_dir, domain):
    return {
        "findingsPath": os.path.join(analysis_dir, f"{domain}{FINDINGS_SUFFIX}"),
        "csvPath": os.path.join(analysis_dir, f"{domain}-analysis-issues.csv"),
        "reportPath": os.path.join(analysis_dir, f"{domain}-analysis-report.md"),
    }


def batch_issues(issues, batch_size):
    """Group issues by file, then pack file-groups into batches.

    Grouping by file first means a verifier agent that opens UserController.java
    checks every finding in it while it has the file in context, instead of
    three agents each re-reading the same file. A single file with more issues
    than batch_size overflows its batch rather than being split — keeping one
    file's findings together is worth more than an even batch size.
    """
    by_file = {}
    for issue in issues:
        by_file.setdefault(str(issue.get("file") or "(unknown)"), []).append(issue)

    batches = []
    current = {"issueIds": [], "files": []}
    for path in sorted(by_file):
        group = by_file[path]
        if current["issueIds"] and len(current["issueIds"]) + len(group) > batch_size:
            batches.append(current)
            current = {"issueIds": [], "files": []}
        current["issueIds"].extend(issue_key(i) for i in group)
        current["files"].append(path)
    if current["issueIds"]:
        batches.append(current)
    return batches


def plan_domain(analysis_dir, rel_analysis, domain, batch_size, recheck_fixed):
    paths = domain_paths(analysis_dir, domain)
    with open(paths["findingsPath"], "r", encoding="utf-8") as f:
        data = json.load(f)

    issues = data.get("issues", [])

    # An ID that appears twice can't be verified: the verifier gets one key for
    # two issues and the merger would apply the single verdict it gets back to
    # both — closing one finding on another's evidence. Excluded here and
    # reported, rather than handed downstream as an ambiguous key.
    counts = {}
    for issue in issues:
        key = issue_key(issue)
        counts[key] = counts.get(key, 0) + 1
    duplicate_ids = sorted(k for k, n in counts.items() if k and n > 1)

    to_verify, skipped_fixed, unidentified = [], 0, 0
    for issue in issues:
        key = issue_key(issue)
        if not key:
            # No ID means no way to route a verdict back to this issue.
            unidentified += 1
            continue
        if key in duplicate_ids:
            continue
        # Normalize before the terminal check: the merger normalizes too, and
        # if the two disagree (raw "resolved" is not "fixed", but normalizes to
        # Fixed) this issue gets re-verified and then reported as a phantom
        # regression the moment the verifier says Open.
        if normalize_status(issue.get("status")) in TERMINAL_STATUSES and not recheck_fixed:
            skipped_fixed += 1
            continue
        to_verify.append(issue)

    batches = []
    for index, batch in enumerate(batch_issues(to_verify, batch_size), start=1):
        batch_id = f"{domain}-b{index}"
        batches.append({
            "batchId": batch_id,
            "domain": domain,
            "findingsPath": os.path.join(rel_analysis, f"{domain}{FINDINGS_SUFFIX}"),
            "verdictPath": os.path.join(rel_analysis, ".verify", f"{batch_id}-verdicts.json"),
            "issueCount": len(batch["issueIds"]),
            "issueIds": batch["issueIds"],
            "files": batch["files"],
        })

    return {
        "domain": domain,
        "findingsPath": os.path.join(rel_analysis, f"{domain}{FINDINGS_SUFFIX}"),
        "csvPath": os.path.join(rel_analysis, f"{domain}-analysis-issues.csv"),
        "reportPath": os.path.join(rel_analysis, f"{domain}-analysis-report.md"),
        "totalIssues": len(issues),
        "toVerify": len(to_verify),
        "skippedFixed": skipped_fixed,
        "duplicateIds": duplicate_ids,
        "unidentified": unidentified,
        "batches": batches,
    }


def main():
    parser = argparse.ArgumentParser(description="Plan a code-scan rescan from prior analysis output")
    parser.add_argument("repoPath")
    parser.add_argument("--batch-size", type=int, default=12,
                        help="max issues per verifier agent (default 12)")
    parser.add_argument("--recheck-fixed", action="store_true",
                        help="also re-verify issues already marked Fixed/Not Applicable (regression check)")
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repoPath)
    if not os.path.isdir(repo_path):
        print(json.dumps({"present": False, "error": f"repoPath not found: {repo_path}"}))
        sys.exit(1)

    analysis_dir = os.path.join(repo_path, "analysis")
    findings_files = sorted(glob.glob(os.path.join(analysis_dir, f"*{FINDINGS_SUFFIX}")))
    if not findings_files:
        print(json.dumps({
            "present": False,
            "repoPath": repo_path,
            "reason": "no analysis/*-analysis-findings.json found — this repo has not been scanned yet",
        }))
        return

    verify_dir = os.path.join(analysis_dir, ".verify")
    shutil.rmtree(verify_dir, ignore_errors=True)
    os.makedirs(verify_dir, exist_ok=True)

    domains, errors = [], []
    for path in findings_files:
        domain = os.path.basename(path)[: -len(FINDINGS_SUFFIX)]
        try:
            domains.append(plan_domain(analysis_dir, "analysis", domain, args.batch_size, args.recheck_fixed))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append({"domain": domain, "error": str(exc)})

    domains = [d for d in domains if d["batches"]] + [d for d in domains if not d["batches"]]

    plan = {
        "present": True,
        "repoPath": repo_path,
        "analysisDir": analysis_dir,
        "batchSize": args.batch_size,
        "recheckFixed": args.recheck_fixed,
        "domains": domains,
        "errors": errors,
    }
    plan_path = os.path.join(verify_dir, "plan.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    # stdout stays compact: the orchestrator agent echoes this back to the
    # workflow, so it must not carry the per-issue ID lists that live in
    # plan.json — the verifier agents read those straight off disk.
    summary = {
        "present": True,
        "repoPath": repo_path,
        "analysisDir": analysis_dir,
        "planPath": plan_path,
        "batchSize": args.batch_size,
        "recheckFixed": args.recheck_fixed,
        "domains": [{
            "domain": d["domain"],
            "findingsPath": d["findingsPath"],
            "csvPath": d["csvPath"],
            "totalIssues": d["totalIssues"],
            "toVerify": d["toVerify"],
            "skippedFixed": d["skippedFixed"],
            "duplicateIds": d["duplicateIds"],
            "unidentified": d["unidentified"],
            "batchIds": [b["batchId"] for b in d["batches"]],
        } for d in domains],
        "totals": {
            "domains": len(domains),
            "totalIssues": sum(d["totalIssues"] for d in domains),
            "toVerify": sum(d["toVerify"] for d in domains),
            "skippedFixed": sum(d["skippedFixed"] for d in domains),
            "excluded": sum(len(d["duplicateIds"]) + d["unidentified"] for d in domains),
            "batches": sum(len(d["batches"]) for d in domains),
        },
        "errors": errors,
    }
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
