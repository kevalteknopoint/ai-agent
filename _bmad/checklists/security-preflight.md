# Security Scan Preflight Checklist

## Before Running

- [ ] Git URL is valid and accessible (or local path exists)
- [ ] Branch name confirmed (don't guess `main` vs `master` vs `develop`)
- [ ] Target URL (if DAST) is authorized for testing
- [ ] Scan mode selected (`full` or `quick`)

## Tool Requirements

| Tool | Purpose | Required For |
|---|---|---|
| semgrep | SAST pattern matching | All scans |
| gitleaks | Secret detection | All scans |
| trivy | CVE scanning | All scans |
| hadolint | Dockerfile lint | When Dockerfiles present |
| checkov | IaC security | When IaC files present |
| nuclei | DAST probing | Full mode + target URL |

## Authorization Checks

- [ ] Confirm permission to scan (not scanning unauthorized targets)
- [ ] DAST target URL is owned/authorized by requestor
- [ ] No credentials will be printed in output
- [ ] Results stay in designated output directory
