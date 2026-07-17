#!/usr/bin/env python3
"""apply_verdicts.py <findings.json> <verdicts.json> [<verdicts.json> ...]
                     [--csv <tracker.csv>] [--commit X] [--branch B] [--date YYYY-MM-DD]

Deterministic status merger for a code-scan rescan. Verifier agents decide
*whether* each prior finding is fixed; this script owns *writing that decision
back* — into the same findings JSON and the same CSV tracker the original scan
produced. Keeping the write here rather than in an agent prompt means no model
ever rewrites a findings file by hand, so a 300-issue tracker cannot lose rows
to a truncated generation.

verdicts.json shape (written by the code-scan-verifier agent):
{
  "verdicts": [
    {"id":"001","status":"Fixed","statusDetail":"binds :email via setParameter",
     "verifiedFile":"src/main/java/UserController.java","verifiedLine":78}
  ]
}

Merge rules:
- An issue keeps every field it already had; only status/provenance fields move.
- First scan to touch an issue stamps firstSeenCommit/firstSeenDate.
- Fixed → non-Fixed clears fixedInCommit: a regression must not keep claiming
  the commit that once fixed it.
- An issue with no verdict this run keeps its prior status untouched and is
  reported as `notVerified` — silence is never read as "fixed".
- A status that's present but unparseable normalizes to Unverifiable, and a
  missing one to Open (see build_issues_csv.normalize_status) — either way, a
  malformed verdict can never close a finding.
- A duplicated issue ID is left untouched and reported: one verdict cannot be
  routed to two issues without closing one of them on the other's evidence.
- A malformed verdict file is reported in `badVerdictFiles` and skipped, never
  fatal — one bad batch must not discard every other batch's good verdicts.

Prints a JSON summary on stdout.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys

from build_issues_csv import issue_key, normalize_status, write_csv


def git_commit(path):
    try:
        out = subprocess.run(
            ["git", "-C", path, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10, check=True,
        )
        return out.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def git_branch(path):
    try:
        out = subprocess.run(
            ["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=10, check=True,
        )
        return out.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def load_verdicts(paths):
    """Collect verdicts from every batch file, tolerating malformed ones.

    Verdict files are model-authored, so this parses defensively: one bad file
    must not take down the merge, or a single malformed batch would discard
    every other batch's good verdicts along with it.
    """
    verdicts, bad_files = {}, []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            bad_files.append({"file": path, "error": str(exc)})
            continue

        # Accept {"verdicts": [...]} (the documented shape) or a bare [...].
        if isinstance(data, dict):
            entries = data.get("verdicts", [])
        elif isinstance(data, list):
            entries = data
        else:
            entries = None
        if not isinstance(entries, list):
            bad_files.append({"file": path, "error": "expected {'verdicts': [...]} or a list of verdicts"})
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                bad_files.append({"file": path, "error": f"verdict is not an object: {entry!r}"})
                continue
            issue_id = issue_key(entry)
            if issue_id:
                verdicts[issue_id] = entry
    return verdicts, bad_files


def main():
    parser = argparse.ArgumentParser(description="Merge rescan verdicts into a findings JSON + CSV tracker")
    parser.add_argument("findings")
    parser.add_argument("verdicts", nargs="+")
    parser.add_argument("--csv", dest="csv_path", default=None)
    parser.add_argument("--commit", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--mode", default="rescan")
    args = parser.parse_args()

    findings_path = os.path.abspath(args.findings)
    if not os.path.isfile(findings_path):
        print(json.dumps({"error": f"findings file not found: {findings_path}"}))
        sys.exit(1)

    repo_dir = os.path.dirname(os.path.dirname(findings_path))  # <repo>/analysis/x.json -> <repo>
    commit = args.commit or git_commit(repo_dir)
    branch = args.branch or git_branch(repo_dir)
    date = args.date or datetime.date.today().isoformat()

    with open(findings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    issues = data.get("issues", [])

    verdicts, bad_files = load_verdicts(args.verdicts)

    counts = {"Open": 0, "Fixed": 0, "Partially Fixed": 0, "Not Applicable": 0, "Unverifiable": 0}
    newly_fixed, regressed, not_verified = [], [], []
    seen_ids = set()

    # A duplicated ID is ambiguous: one verdict can't be routed to two issues,
    # and applying it to both would close a live finding on another issue's
    # evidence. Left untouched and reported. plan_verification.py excludes
    # these from verification for the same reason, so normally no verdict
    # arrives for them at all — this is the backstop for a hand-run merge.
    id_counts = {}
    for issue in issues:
        key = issue_key(issue)
        id_counts[key] = id_counts.get(key, 0) + 1
    duplicate_ids = sorted(k for k, n in id_counts.items() if k and n > 1)

    for issue in issues:
        issue_id = issue_key(issue)
        seen_ids.add(issue_id)
        previous = normalize_status(issue.get("status"))
        verdict = None if issue_id in duplicate_ids else verdicts.get(issue_id)

        if verdict is None:
            counts[previous] = counts.get(previous, 0) + 1
            not_verified.append(issue_id)
            issue.setdefault("status", previous)
            continue

        status = normalize_status(verdict.get("status"))
        issue["status"] = status
        issue["statusDetail"] = str(verdict.get("statusDetail") or "").strip()

        # Where the issue lives now. Recorded separately from file/line so a
        # refactor that moved the code can't erase the original pointer.
        # Cleared when this verdict doesn't supply them: these describe the
        # current verdict, and carrying a previous run's location forward would
        # render as "moved from X" against a finding this run never located.
        verified_file = verdict.get("verifiedFile")
        if verified_file not in (None, ""):
            issue["verifiedFile"] = str(verified_file)
        else:
            issue.pop("verifiedFile", None)
        verified_line = verdict.get("verifiedLine")
        if verified_line not in (None, "", 0):
            issue["verifiedLine"] = verified_line
        else:
            issue.pop("verifiedLine", None)

        if not issue.get("firstSeenCommit"):
            history = data.get("scanHistory") or []
            issue["firstSeenCommit"] = (history[0].get("commit") if history else "") or commit
            issue["firstSeenDate"] = (history[0].get("date") if history else "") or date

        issue["lastVerifiedCommit"] = commit
        issue["lastVerifiedDate"] = date

        if status == "Fixed":
            if previous != "Fixed":
                newly_fixed.append(issue_id)
                issue["fixedInCommit"] = commit
                issue["fixedDate"] = date
            issue.setdefault("fixedInCommit", commit)
            issue.setdefault("fixedDate", date)
        else:
            if previous == "Fixed":
                regressed.append(issue_id)
            issue.pop("fixedInCommit", None)
            issue.pop("fixedDate", None)

        counts[status] = counts.get(status, 0) + 1

    unknown_ids = sorted(set(verdicts) - seen_ids)

    entry = {
        "commit": commit,
        "branch": branch,
        "date": date,
        "mode": args.mode,
        "issuesTotal": len(issues),
        "verified": len(issues) - len(not_verified),
        "counts": dict(counts),
        "newlyFixed": newly_fixed,
        "regressed": regressed,
        "duplicateIds": duplicate_ids,
    }
    data.setdefault("scanHistory", []).append(entry)
    data["issues"] = issues

    with open(findings_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    csv_path = args.csv_path
    if csv_path is None:
        csv_path = findings_path.replace("-analysis-findings.json", "-analysis-issues.csv")
    csv_written = None
    if csv_path:
        write_csv(issues, csv_path)
        csv_written = csv_path

    print(json.dumps({
        "findings": findings_path,
        "csv": csv_written,
        "commit": commit,
        "branch": branch,
        "date": date,
        "total": len(issues),
        "verified": len(issues) - len(not_verified),
        "counts": counts,
        "newlyFixed": newly_fixed,
        "regressed": regressed,
        "notVerified": not_verified,
        "duplicateIds": duplicate_ids,
        "unknownVerdictIds": unknown_ids,
        "badVerdictFiles": bad_files,
    }))


if __name__ == "__main__":
    main()
