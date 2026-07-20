# Security Scan Guide

Zero-AI security scanning: point it at a Git repo (or local directory) and it
runs real security tools — semgrep, gitleaks, trivy, hadolint, checkov,
nuclei — with zero LLM tokens. Like running ZAP + SonarQube + Trivy from one
command.

## How it works

```
You provide: Git URL + branch (or local path)
                    ↓
    clone_or_update.sh — get the code
                    ↓
    detect security surface — languages, frameworks, infra files
                    ↓
    run tools in parallel:
      semgrep (SAST) → injection, XSS, auth, crypto, SSRF
      gitleaks       → hardcoded secrets, API keys, tokens
      trivy          → CVEs in dependencies (npm, maven, pip, go)
      hadolint       → Dockerfile security anti-patterns
      checkov        → Terraform/K8s/CloudFormation misconfigs
      nuclei (DAST)  → live endpoint probing (only with target URL)
                    ↓
    aggregate_report.py — merge all outputs
                    ↓
    Output: security-analysis/ folder with reports
```

**Zero AI tokens in the actual scan.** The tools are open-source CLI binaries.

## Two entry points

| Entry point | Use when | Asks for input |
|---|---|---|
| **`security-scan` skill** (`skills/security-scan/SKILL.md`) | A human is driving | Conversational — asks for URL, branch, DAST target, scan mode |
| **`security-scan` workflow** (`workflows/security-scan.js`) | CI / batch / scheduled | Takes args — no prompting |

## Quick start

### Interactive (skill)

```
> Run a security scan

I'll need a few details:
1. Git URL: https://github.com/org/repo.git
2. Branch: main
3. Live URL for DAST? (optional): https://app.example.com
4. Mode: full / quick
```

### Headless (workflow)

```js
// Single repo
{ gitUrl: "https://github.com/org/repo.git", branch: "main" }

// With DAST
{ gitUrl: "https://github.com/org/repo.git", branch: "main", targetUrl: "https://app.example.com" }

// Multiple repos
{ repos: [
    { gitUrl: "https://github.com/org/backend.git", branch: "main" },
    { gitUrl: "https://github.com/org/frontend.git", branch: "develop" }
  ]
}

// Quick mode (fast scans only)
{ gitUrl: "https://github.com/org/repo.git", branch: "main", quick: true }
```

### Direct CLI (no AI at all)

```bash
# Full scan
bash scripts/security-scan/run_scan.sh \
  --git-url 'https://github.com/org/repo.git' \
  --branch 'main'

# With DAST
bash scripts/security-scan/run_scan.sh \
  --git-url 'https://github.com/org/repo.git' \
  --branch 'main' \
  --target-url 'https://app.example.com'

# Local directory
bash scripts/security-scan/run_scan.sh \
  --path '/path/to/project'

# Quick mode
bash scripts/security-scan/run_scan.sh \
  --git-url 'https://github.com/org/repo.git' \
  --branch 'main' \
  --quick
```

## Tools

### Prerequisites

```bash
bash scripts/security-scan/install_tools.sh
```

This installs all 6 tools via Homebrew (macOS) or direct binary download.
Run `--check-only` to verify without installing.

| Tool | Version | What it scans | Detection |
|------|---------|---------------|-----------|
| [semgrep](https://semgrep.dev/) | latest | SAST — pattern-based code analysis | Any source code |
| [gitleaks](https://github.com/gitleaks/gitleaks) | latest | Secrets — keys, tokens, passwords | Any repo |
| [trivy](https://trivy.dev/) | latest | Dependencies — CVE database | package.json, pom.xml, requirements.txt, go.mod, Gemfile |
| [hadolint](https://github.com/hadolint/hadolint) | latest | Dockerfiles — security & best practices | Dockerfile* |
| [checkov](https://www.checkov.io/) | latest | IaC — Terraform, K8s, CloudFormation, Helm | *.tf, K8s YAML, CF templates |
| [nuclei](https://nuclei.projectdiscovery.io/) | latest | DAST — active endpoint probing | Only when --target-url provided |

## Output

All reports go to `<repo-path>/security-analysis/`:

| File | Content |
|------|---------|
| `security-report.md` | Executive summary, severity counts, OWASP mapping, top findings |
| `security-findings.json` | Machine-readable unified findings (all tools merged) |
| `security-issues.csv` | Issue tracker (same format as code-scan CSV) |
| `owasp-mapping.md` | Findings mapped to OWASP Top 10 (2021) with counts per category |
| `sast-findings-raw.json` | Raw semgrep output |
| `secrets-findings-raw.json` | Raw gitleaks output |
| `dependency-findings-raw.json` | Raw trivy output |
| `checkov-raw.json` | Raw checkov output |
| `dast-findings-raw.jsonl` | Raw nuclei output (JSONL) |
| `scan-*.log` | Scan execution log |

## Severity model

| Level | Label | CVSS Range | Examples |
|-------|-------|------------|---------|
| 5 | Critical | 9.0–10.0 | Hardcoded secrets, RCE-capable injection, unauthenticated admin |
| 4 | High | 7.0–8.9 | SQL injection, SSRF, broken access control, known CVE with exploit |
| 3 | Medium | 4.0–6.9 | XSS, CSRF, missing rate limiting, verbose errors |
| 2 | Low | 0.1–3.9 | Missing security headers, cookie flags, weak TLS |
| 1 | Info | 0.0 | Best practices, style, informational |

## OWASP Top 10 mapping

Every finding is mapped to an OWASP Top 10 (2021) category via CWE ID
or rule pattern matching:

| Category | What it covers |
|----------|----------------|
| A01: Broken Access Control | Path traversal, IDOR, CSRF, missing auth checks |
| A02: Cryptographic Failures | Weak crypto, hardcoded keys, missing TLS |
| A03: Injection | SQLi, XSS, command injection, SSTI, LDAP injection |
| A04: Insecure Design | Design-level flaws |
| A05: Security Misconfiguration | Missing headers, debug endpoints, default creds |
| A06: Vulnerable Components | Known CVEs in dependencies |
| A07: Auth Failures | Hardcoded creds, weak passwords, session issues |
| A08: Data Integrity Failures | Insecure deserialization, CI/CD integrity |
| A09: Logging Failures | Log injection, missing audit trail |
| A10: SSRF | Server-side request forgery |

## Architecture

```
scripts/security-scan/
  install_tools.sh       ← Install all 6 tools (idempotent)
  run_scan.sh            ← Main orchestrator (zero AI)
  aggregate_report.py    ← Merge tool outputs into unified reports

agents/security-scan.md  ← Minimal agent (parameter collection only)
skills/security-scan/SKILL.md  ← Interactive entry point
workflows/security-scan.js     ← Headless/batch entry point
```

**Key principle:** The shell script does ALL the work. The agent/skill/workflow
are just parameter collectors. You can run `run_scan.sh` directly from the
command line with zero AI involvement.
