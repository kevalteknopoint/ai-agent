# Task: Install Security Tools

## Purpose

Check (and optionally install) the CLI tools required for zero-AI security scanning.

## Check Command

```bash
bash {ai_agent_repo}/scripts/security-scan/install_tools.sh --check-only
```

## Install Command

```bash
bash {ai_agent_repo}/scripts/security-scan/install_tools.sh
```

## Required Tools

| Tool | Check | Install |
|---|---|---|
| semgrep | `which semgrep` | `pip install semgrep` |
| gitleaks | `which gitleaks` | `brew install gitleaks` |
| trivy | `which trivy` | `brew install trivy` |
| hadolint | `which hadolint` | `brew install hadolint` |
| checkov | `which checkov` | `pip install checkov` |
| nuclei | `which nuclei` | `go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |

## Notes

- Always run check-only first, report missing tools to user
- Offer to install only after user confirms
- Some tools require specific runtimes (Python, Go, Homebrew)
