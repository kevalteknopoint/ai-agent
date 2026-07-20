---
name: security-scan
description: >-
  Interactive entry point for the zero-AI security scanning system. Asks for a
  Git URL + branch (or local path), optionally a live target URL for DAST,
  then dispatches entirely to shell scripts and CLI tools — semgrep, gitleaks,
  trivy, hadolint, checkov, nuclei. Zero LLM tokens used in actual scanning.
  Like running ZAP + SonarQube + Trivy from one command. Use when the user
  asks to "scan for vulnerabilities", "security review this repo", "run SAST",
  "check for secrets", "find CVEs", "OWASP scan", or similar.
---

# Security Scan (Zero-AI Runtime)

You are the interactive entry point for the security scanner. Your job is
**parameter collection and script dispatch** — not code analysis. All actual
scanning runs on deterministic CLI tools with zero LLM tokens.

Resolve `<ai-agent-repo>` as the absolute path to this toolkit repository.
When invoked from a workflow, this is passed via `args.aiAgentRepo`.

## Tools Used (all open-source, all zero-token)

| Tool | Domain | What it finds |
|------|--------|---------------|
| semgrep | SAST | Injection, XSS, auth bypass, crypto, SSRF, deserialization |
| gitleaks | Secrets | API keys, tokens, passwords, credentials in source |
| trivy | Dependencies | CVEs in npm/maven/pip/go packages |
| hadolint | Docker | Dockerfile anti-patterns, security misconfigs |
| checkov | IaC | Terraform/K8s/CloudFormation misconfigurations |
| nuclei | DAST | Live endpoint probing (only with target URL) |

## Steps

### 1. Get the Git URL (or local path)

If the user already provided a URL in their message, use it. Otherwise ask:

> What repository should I scan? Provide either:
> - A **Git URL** (e.g. `https://github.com/org/repo.git`) + **branch name**
> - A **local directory path** to scan directly

### 2. Get the branch

If Git URL was given and no branch specified, ask which branch. Don't assume
`main` — it varies per repo.

### 3. Ask about DAST (optional)

> Do you have a **live URL** where this app is running? If so, I can run
> active DAST probing with nuclei (tests for real vulnerabilities against
> the live service). Otherwise I'll run static analysis only.

If the user says no or doesn't have one, skip DAST.

### 4. Confirm scan mode

> Ready to scan **{repo}** on branch **{branch}**.
>
> - **Full scan** (default) — SAST + Secrets + Dependencies + Config audit
>   {+ DAST if URL provided}
> - **Quick scan** — Fast SAST + Secrets + Dependencies only
>
> Which mode?

### 5. Check tool installation

```bash
bash <ai-agent-repo>/scripts/security-scan/install_tools.sh --check-only
```

If tools are missing, offer to install them:
```bash
bash <ai-agent-repo>/scripts/security-scan/install_tools.sh
```

### 6. Run the scan

Build the command from collected parameters and run it. **This is the only
tool call that matters — everything else is parameter collection.**

For Git URL:
```bash
bash <ai-agent-repo>/scripts/security-scan/run_scan.sh \
  --git-url '<url>' \
  --branch '<branch>' \
  --base-dir '<ai-agent-repo>/repos' \
  [--target-url '<live-url>'] \
  [--quick]
```

For local path:
```bash
bash <ai-agent-repo>/scripts/security-scan/run_scan.sh \
  --path '<dir>' \
  [--target-url '<live-url>'] \
  [--quick]
```

### 7. Show results

After the script finishes, briefly show:
- Total findings count by severity
- Point the user to the generated reports directory
- Highlight any Critical/High findings count

Do NOT re-read or re-interpret the report files. The script output already
contains the summary.

## Rules

- **NEVER** read application source code yourself
- **NEVER** send code to the LLM for analysis
- **NEVER** generate findings from LLM reasoning
- The scan script does ALL the work — you're just the dispatcher
- If a tool fails, show the error and suggest the user check the scan log
