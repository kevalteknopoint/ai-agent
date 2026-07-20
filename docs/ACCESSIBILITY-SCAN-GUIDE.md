# Accessibility Scan Guide

## Overview

The `bmad-accessibility-scan` module provides multi-standard accessibility auditing
with **zero AI tokens for scanning** — all analysis is performed by deterministic
CLI tools (axe-core, pa11y, Lighthouse, eslint-plugin-jsx-a11y, html-validate).

LLM tokens are used **only** in the fix phase for interpreting findings and generating
context-aware remediation code.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              accessibility-scan-orchestrator                  │
│            (opus — parameter collection + routing)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Static Code  │  │ Live Runtime │  │   Aggregator     │  │
│  │   Analysis   │  │   Analysis   │  │  (Python script) │  │
│  │              │  │              │  │                   │  │
│  │ • html-valid │  │ • axe-core   │  │ • Deduplicate    │  │
│  │ • eslint-a11y│  │ • pa11y      │  │ • Cross-ref      │  │
│  │ • patterns   │  │ • lighthouse │  │ • Categorize     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│              accessibility-code-fixer                         │
│          (sonnet — applies fixes WITH user confirmation)     │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Tools

```bash
bash scripts/accessibility-scan/install_tools.sh
```

### 2. Run a Scan

**Full scan (code + live):**
```bash
bash scripts/accessibility-scan/run_scan.sh \
  --standard wcag2.1 \
  --level aa \
  --git-url 'https://github.com/org/repo.git' \
  --branch main \
  --live-url 'https://example.com' \
  --viewport both
```

**Code-only scan:**
```bash
bash scripts/accessibility-scan/run_scan.sh \
  --mode code \
  --standard wcag2.2 \
  --level aa \
  --path ./my-project
```

**Live-only scan:**
```bash
bash scripts/accessibility-scan/run_scan.sh \
  --mode live \
  --standard wcag2.1 \
  --level aa \
  --live-url 'https://example.com' \
  --pages '/,/about,/contact'
```

### 3. Using the Agent

In VS Code with the agent loaded, say:

> "Accessibility scan https://github.com/org/repo.git branch main against WCAG 2.1 AA.
> Live URL: https://example.com"

The agent will:
1. Ask for any missing inputs
2. Check tool installation
3. Run the scan
4. Present findings
5. Offer to fix (with confirmation per edit)

## Supported Standards

| Standard | Flag | Description |
|----------|------|-------------|
| WCAG 2.0 | `wcag2.0` | W3C 2008 baseline |
| WCAG 2.1 | `wcag2.1` | W3C 2018 — adds mobile + cognitive (recommended default) |
| WCAG 2.2 | `wcag2.2` | W3C 2023 — adds focus, auth, help criteria |
| Section 508 | `section508` | US Federal requirement (maps to WCAG 2.0 AA) |
| EN 301 549 | `en301549` | EU accessibility standard (maps to WCAG 2.1 AA) |

## Conformance Levels

| Level | Description | Typical Use |
|-------|-------------|-------------|
| A | Minimum barrier removal | Rare as sole target |
| AA | Standard — recommended for most | Default for legal compliance |
| AAA | Maximum accessibility | Specialized audiences, government |

## Scanning Tools

### Static Code Analysis (Zero AI)

| Tool | What It Checks |
|------|---------------|
| `html-validate` | HTML validity, landmark roles, form labels, heading structure |
| `eslint-plugin-jsx-a11y` | React-specific: alt text, roles, keyboard, ARIA |
| Pattern scanner (grep) | Images without alt, missing lang, empty links, outline:none, etc. |

### Live Runtime Analysis (Zero AI)

| Tool | What It Checks |
|------|---------------|
| `axe-core` | Full WCAG rule engine against rendered DOM |
| `pa11y` | HTML CodeSniffer rules against live pages |
| `Lighthouse` | Google's accessibility audit with scoring (0-100) |

## Fix Workflow

The fix phase is **interactive** — the agent NEVER edits code without permission:

```
For each violation:
  1. Agent presents: "WCAG 2.4.7 Focus Visible — the .btn class removes 
     outline without replacement. This makes keyboard navigation invisible 
     for all keyboard-only users."
  
  2. Agent proposes: "Add :focus-visible outline with 3:1 contrast ratio"
     Shows diff:
       - .btn { outline: none; }
       + .btn { outline: none; }
       + .btn:focus-visible { outline: 2px solid #1a73e8; outline-offset: 2px; }
  
  3. User responds: "yes" / "skip" / "modify" / "stop"
  
  4. If "yes" → agent applies the fix
  5. Move to next violation
```

After all fixes: automatic re-scan to verify resolution.

## Output Files

All results go to `{repo}/accessibility-analysis/` (or `{output}/accessibility-analysis/`):

| File | Content |
|------|---------|
| `report.md` | Human-readable findings grouped by WCAG principle |
| `summary.json` | Machine-readable summary (counts, score, tools) |
| `findings.json` | All findings with full metadata |
| `axe-results/*.json` | Raw axe-core output per page/viewport |
| `pa11y-results/*.json` | Raw pa11y output per page/viewport |
| `lighthouse-results/*.json` | Raw Lighthouse output per page |
| `pattern-findings.txt` | Grep-based pattern scan results |
| `screenshots/` | Element screenshots of violations (if enabled) |

## Severity Scale

| Level | Impact | Description | axe-core Mapping |
|-------|--------|-------------|-----------------|
| 5 | Critical | Blocks access entirely for some users | critical |
| 4 | Serious | Significantly difficult for some users | serious |
| 3 | Moderate | Somewhat difficult for some users | moderate |
| 2 | Minor | Annoying but not blocking | minor |

## WCAG Principles (POUR)

| Principle | Code | Question It Answers |
|-----------|------|-------------------|
| Perceivable | P | Can users perceive the content? (alt text, contrast, captions) |
| Operable | O | Can users operate the interface? (keyboard, timing, seizures) |
| Understandable | U | Can users understand the content? (language, predictability, errors) |
| Robust | R | Can assistive tech interpret the content? (valid HTML, ARIA, name/role/value) |

## Limitations

1. **Automated tools catch 30-50% of issues** — manual testing essential
2. **Cannot test complex interactions** — multi-step flows need human judgment
3. **Cannot verify content quality** — alt text *exists* ≠ alt text is *good*
4. **ARIA is complex** — some ARIA patterns need assistive tech testing to verify
5. **Dynamic content** — SPAs with client-side routing need special handling
6. **Third-party content** — embedded widgets may have their own issues

## Recommended Manual Tests (Post-Scan)

After automated scanning, recommend these manual checks:

1. **Screen reader** — Navigate full page flow with VoiceOver/NVDA/JAWS
2. **Keyboard only** — Tab through all interactive elements, verify focus visible
3. **Zoom 200%** — Check nothing is clipped or overlapping
4. **High contrast mode** — Windows High Contrast / forced-colors media query
5. **Reduced motion** — Check prefers-reduced-motion is respected
6. **Form flows** — Complete forms with errors, verify error messaging
7. **Mobile** — Test touch targets, zoom, orientation changes

## Integration with Other BMAD Modules

- **Code Scan** → accessibility issues surface in code quality findings
- **EDS Blocks** → block-specific a11y patterns (decorate, createOptimizedPicture)
- **Quality Gate** → can block deployment if critical a11y violations exist
- **Code Fix** → accessibility fixer can be routed from the general code-fix orchestrator
