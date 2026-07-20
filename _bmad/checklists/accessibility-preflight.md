# Accessibility Scan Preflight Checklist

## Before Running

### Standard & Scope
- [ ] Accessibility standard confirmed (WCAG 2.0, 2.1, 2.2, Section 508, EN 301 549)
- [ ] Conformance level confirmed (A, AA, or AAA)
- [ ] Scan mode selected (full, code-only, live-only)

### Code Scan Prerequisites
- [ ] Git URL is valid and accessible (or local path exists)
- [ ] Branch name confirmed (don't guess `main` vs `master` vs `develop`)
- [ ] Tech stack known (determines which linters to run)

### Live Scan Prerequisites
- [ ] Live URL is accessible (not behind VPN/auth without credentials)
- [ ] Live URL is authorized for automated scanning
- [ ] Target pages identified (or confirm "all discoverable pages")
- [ ] Viewport(s) selected (desktop 1280px, mobile 375px, or both)

### Authorization Checks
- [ ] Confirm permission to scan live URL (not hitting unauthorized targets)
- [ ] Confirm scan rate won't overwhelm target server
- [ ] Results stay in designated output directory
- [ ] No personally identifiable information (PII) captured in screenshots

## Tool Requirements

| Tool | Purpose | Required For |
|---|---|---|
| @axe-core/cli | Runtime WCAG scanning | Live scans |
| pa11y | Runtime accessibility testing | Live scans |
| lighthouse (CLI) | Accessibility audit + scoring | Live scans |
| eslint-plugin-jsx-a11y | JSX/React static linting | React/JSX code |
| axe-linter | Static HTML linting | HTML/HTL code |
| html-validate | HTML validity + a11y rules | All HTML |
| puppeteer/chromium | Browser automation for runtime scans | Live scans |

## Conformance Level Quick Guide

| Level | Meaning | Typical Use |
|---|---|---|
| A | Minimum — removes absolute barriers | Rare as sole target |
| AA | Standard — recommended for most sites | Most common target |
| AAA | Maximum — highest accessibility | Specialized audiences |

## Common Pitfalls

- [ ] Don't scan staging URLs that return 403/auth walls — results will be misleading
- [ ] Don't test AAA contrast on brand-locked colors without discussing alternatives
- [ ] Don't assume SPA routes are separate pages — test client-side navigation
- [ ] Don't skip mobile viewport — many a11y issues are viewport-specific
- [ ] Don't forget to check dynamic content (modals, tooltips, accordions, tabs)
- [ ] Don't confuse "no violations found" with "fully accessible" — automated tools catch ~30-50% of issues
