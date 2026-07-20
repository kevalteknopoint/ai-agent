# bmad-security-scan

Zero-AI security scanning with deterministic CLI tools.

## When to Use

- "Security scan this repo"
- "Find vulnerabilities"
- "Run SAST/DAST"
- "Check for secrets"
- "Check for CVEs"

## Agent

Load `_bmad/agents/security-scan.md`

## Tools Used (zero LLM tokens)

| Tool | Purpose |
|---|---|
| semgrep | SAST pattern matching |
| gitleaks | Secret/credential detection |
| trivy | Container/dependency vulnerabilities |
| hadolint | Dockerfile best practices |
| checkov | IaC security |
| nuclei | DAST active probing |

## Steps

1. Collect: Git URL + branch (or local path), optional target URL, scan mode
2. Preflight: load `_bmad/checklists/security-preflight.md`
3. Check tools: `bash {ai_agent_repo}/scripts/security-scan/install_tools.sh --check-only`
4. Run: `bash {ai_agent_repo}/scripts/security-scan/run_scan.sh --git-url '{url}' --branch '{branch}' [--target-url '{url}'] [--quick]`
5. Display summary and point to report files

## Modes

| Mode | Includes |
|---|---|
| `full` (default) | All tools including DAST |
| `quick` | Skip DAST, shallow scans |
