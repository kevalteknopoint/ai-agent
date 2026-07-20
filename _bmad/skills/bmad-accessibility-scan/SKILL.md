# bmad-accessibility-scan

Multi-standard accessibility auditing with deterministic CLI tools + LLM-driven fix orchestration.

## When to Use

- "Accessibility scan this site"
- "Check WCAG compliance"
- "Run a11y audit"
- "Scan for accessibility issues"
- "Fix accessibility violations"
- "Check Section 508 compliance"
- "WCAG 2.2 audit"
- "Check if this site is accessible"

## Agent

Load `_bmad/agents/accessibility-scan-orchestrator.md`

## Tools Used

| Tool | Purpose | LLM Tokens? |
|---|---|---|
| axe-core (via @axe-core/cli) | Runtime WCAG scanning of live pages | Zero |
| pa11y | Runtime accessibility testing with multiple standards | Zero |
| Lighthouse (CI mode) | Accessibility audit with scoring | Zero |
| eslint-plugin-jsx-a11y | Static JSX/React accessibility linting | Zero |
| axe-linter (CLI) | Static HTML accessibility linting | Zero |
| html-validate | HTML validity + a11y rules | Zero |
| color-contrast-checker | Programmatic contrast ratio calculation | Zero |
| LLM (findings analysis) | Interpret findings, plan fixes, generate remediation code | Yes (fix phase only) |

## Steps

1. **Collect inputs** — standard, conformance level, repo/path, live URL, scope
2. **Preflight** — load `_bmad/checklists/accessibility-preflight.md`
3. **Check tools** — `bash {ai_agent_repo}/scripts/accessibility-scan/install_tools.sh --check-only`
4. **Run scan** — `bash {ai_agent_repo}/scripts/accessibility-scan/run_scan.sh [options]`
5. **Display findings** — categorized by WCAG principle, sorted by severity
6. **(Optional) Fix** — ask user, then dispatch `accessibility-code-fixer` with confirmation flow

## Modes

| Mode | Includes |
|---|---|
| `full` (default) | Code analysis + live runtime scan |
| `code-only` | Static analysis of repo files only |
| `live-only` | Runtime scan of live URL only |

## Standards Supported

| Standard | Flag | Maps To |
|---|---|---|
| WCAG 2.0 | `--standard wcag2.0` | W3C 2008 |
| WCAG 2.1 | `--standard wcag2.1` | W3C 2018 (default) |
| WCAG 2.2 | `--standard wcag2.2` | W3C 2023 |
| Section 508 | `--standard section508` | US Federal (WCAG 2.0 AA) |
| EN 301 549 | `--standard en301549` | EU (WCAG 2.1 AA) |

## Output

Reports written to `{output}/accessibility-analysis/`:
- `summary.json` — machine-readable consolidated findings
- `report.md` — human-readable report with WCAG SC references
- `code-findings.json` — static code analysis results
- `live-findings.json` — runtime scan results
- `fix-plan.json` — prioritized fix plan (if fix mode activated)
- `screenshots/` — element screenshots of violations (if enabled)
