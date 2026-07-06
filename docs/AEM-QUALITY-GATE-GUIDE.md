# AEM Quality Gate — Rule-Driven Static Analysis

## Overview

**AEM Quality Gate** is a rule-driven static analysis toolkit for AEMaaCS projects that enforces Java, Sling, HTL, JavaScript, CSS, and HTML best practices. Unlike AI-driven tools, quality checking runs **100% offline via deterministic rule engines** (PMD, Checkstyle, ESLint, Stylelint, HTMLHint, custom scripts) with **zero LLM tokens consumed for scanning**. AI is available only as an optional enhancement to tune rule definitions, never to analyze code.

### Why This Matters

Real AEMaaCS projects in production have:
- ✗ Zero enforced Java quality gates (no PMD, Checkstyle, SpotBugs)
- ✗ ESLint/Stylelint configs that exist but are disconnected from any build
- ✗ No checks for Sling anti-patterns (ResourceResolver leaks, WCMUsePojo, JCR session misuse)
- ✗ Zero clientlib convention validation

**Quality Gate fills all these gaps.** It's also:
- 💰 **Cost-efficient**: scanning costs zero tokens (no AI required)
- 🚀 **Fast**: local rule engines are milliseconds vs. AI reasoning minutes
- 📊 **Accurate**: rule-based checks have zero false negatives vs. AI which can miss things
- 🔒 **Transparent**: every rule is human-readable and AI-tunable (not a black box)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Claude Workflow (Optional Orchestration)                        │
│  - Repository Setup (permission gate)                           │
│  - Local Quality Scan (no gate — deterministic)                │
│  - Report Aggregation (no gate — pure parsing)                 │
│  - [Optional] AI Rule Curation (read report only)              │
│  - Save Reports                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Quality Gate Toolkit (Standalone, Zero AI)                      │
│  - PMD (Sling/AEM anti-patterns, general Java)                 │
│  - Checkstyle (Java style)                                     │
│  - HTL Maven Plugin (HTL syntax validation)                    │
│  - ESLint (JavaScript quality)                                  │
│  - Stylelint (CSS/SCSS quality)                                │
│  - HTMLHint (HTML best practices)                              │
│  - Custom Clientlib Validator (AEM-specific)                   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Rules by Dimension

### 1. Sling/AEM (Highest Priority)
- **ResourceResolver must be closed** (blocker) — use try-with-resources
- **JCR Session logout required** (blocker) — prevent login-session leaks
- **No getAdministrativeResourceResolver()** (critical) — use service-user login
- **WCMUsePojo deprecated** (major) — migrate to Sling Models
- **adaptTo() without null-check** (major) — prevents NullPointerException
- **Sling Model missing @Optional/@Default** (major) — on nullable fields

### 2. Java General
- Null pointer dereference (critical)
- Cyclomatic complexity threshold (major) — max 10
- God class detection (major) — too many methods/fields
- Error-prone patterns (major) — empty catch blocks, etc.
- Best practices (minor) — unused variables, unclosed resources

### 3. HTL (Sightly)
- Syntax validation (blocker) — invalid HTL expressions
- No inline `<script>`/`<style>` (major) — use clientlibs
- No WCMUsePojo in `data-sly-use` (major)
- Missing `data-sly-test` guard (major) — on risky includes

### 4. JavaScript
- TypeScript type safety (@typescript-eslint/recommended)
- No unused variables
- Curly braces required (consistency)
- Max line length 120 characters

### 5. CSS/SCSS
- No duplicate selectors
- No excessive `!important` (indicates design problem)
- stylelint-config-standard baseline

### 6. HTML/Clientlibs
- Clientlib category naming (e.g., `com.client.app.grid`)
- js.txt/css.txt file references must exist
- Embed vs. dependencies correct usage
- allowProxy flag correctness

## Installation & Setup

### Prerequisites
- Git installed and configured
- Maven installed (for Java/HTL analysis)
- Node.js 18+ and npm 9+ (for frontend analysis)

### One-Time Setup
```bash
# Clone the ai-agent repo (if not already)
git clone https://github.com/kevalteknopoint/ai-agent.git
cd ai-agent/quality-gate

# Install frontend tool dependencies
npm install
```

### Manual Scanning (Standalone, No Claude)
```bash
# Run quality gate against any AEM project
cd quality-gate
bash runner/run-quality-gate.sh /path/to/aem-project /output-dir

# Example:
bash runner/run-quality-gate.sh ~/projects/my-aem-app ~/quality-reports
```

Raw reports are written to the output directory:
- `pmd-report.json` — PMD violations
- `checkstyle-report.xml` — Checkstyle violations
- `eslint-report.json` — ESLint violations
- `stylelint-report.json` — Stylelint violations
- `clientlib-report.json` — Clientlib validation
- `htl-report.log` — HTL validation log

Then aggregate:
```bash
node aggregator/aggregate-report.js /output-dir
```

Returns unified JSON with dimension ratings (A-E) and normalized findings.

## Claude Code Workflow Usage

### Safe Mode (Default) — Explicit Approval Gates

```bash
/aem-quality-gate --args '{
  "repositories": [
    {
      "repoUrl": "https://github.com/your-org/aem-project.git",
      "repoName": "my-aem-app",
      "branch": "main"
    }
  ]
}'
```

Workflow prompts you to approve:
1. **Repository Setup** — "Clone this repo?" (yes/no)
2. **Quality Scan** — Runs automatically (no approval needed)
3. **Report Aggregation** — Runs automatically (no approval needed)
4. **Save Reports** — Saves to `<baseDir>/<repoName>/quality-reports/`

**No git push.** This is a report-only tool.

### Trusted Mode — Fully Automated

```bash
/aem-quality-gate --args '{
  "trustedMode": true,
  "repositories": [
    {
      "repoUrl": "https://github.com/your-org/aem-project.git",
      "repoName": "my-aem-app",
      "branch": "main"
    },
    {
      "repoUrl": "https://github.com/your-org/aem-services.git",
      "repoName": "aem-services",
      "branch": "develop"
    }
  ]
}'
```

- ✓ Repository setup auto-approved
- ✓ Scanning runs silently
- ✓ Reports saved automatically
- ✓ Perfect for batch runs and CI/CD

### With AI Rule Curation (Optional)

```bash
/aem-quality-gate --args '{
  "repositories": [{...}],
  "aiCuration": true
}'
```

Adds a phase:
1. Scanning (as above)
2. **AI Curator reads the report** and proposes rule tuning (no code analysis)
3. You review proposals and approve/deny
4. If approved, updates `rules-manifest.json` for future scans

Example curator proposals:
- "ESLint max-len rule fires 47 times, mostly in generated code → demote to warning"
- "New pattern detected: hardcoded servlet paths → add XPath rule"
- "Suppress Java cyclomatic-complexity in test files → reduce false positives"

### Custom Repository Location

```bash
/aem-quality-gate --args '{
  "baseDir": "/ci/test-repos",
  "repositories": [{...}]
}'
```

Default location: `/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos`

## Results Output

After a scan, reports are written to:
```
<baseDir>/<repoName>/quality-reports/<timestamp>/
├── pmd-report.json
├── checkstyle-report.xml
├── eslint-report.json
├── stylelint-report.json
├── clientlib-report.json
├── htl-report.log
└── aggregated-report.json  (unified)
```

### Aggregated Report Structure
```json
{
  "summary": {
    "totalFindings": 42,
    "overallRating": "C",
    "severityCounts": {
      "blocker": 0,
      "critical": 3,
      "major": 20,
      "minor": 19,
      "info": 0
    }
  },
  "dimensionRatings": {
    "Java": { "rating": "C", "findings": 20, ... },
    "Sling/AEM": { "rating": "D", "findings": 15, ... },
    "HTL": { "rating": "B", "findings": 2, ... },
    "JavaScript": { "rating": "B", "findings": 3, ... },
    "CSS": { "rating": "A", "findings": 0, ... },
    "HTML": { "rating": "A", "findings": 2, ... }
  },
  "findings": [
    {
      "engine": "pmd",
      "file": "core/src/main/java/com/client/app/core/models/UserModel.java",
      "line": 42,
      "severity": "critical",
      "ruleId": "aem-resource-resolver-leak",
      "message": "ResourceResolver must be closed via try-with-resources",
      "dimension": "Sling/AEM"
    },
    ...
  ]
}
```

### Rating Scale
| Rating | Description | Meaning |
|--------|-------------|---------|
| **A** | Excellent | 0-5 total quality debt |
| **B** | Good | 5-15 findings |
| **C** | Fair | 15-30 findings |
| **D** | Poor | 30-50 findings |
| **E** | Critical | 50+ findings or blockers present |

Per-dimension ratings are weighted by impact. Java and Sling/AEM carry highest weight (35%+) since they affect runtime correctness.

## Rule Customization

### Viewing All Rules
```bash
cat ai-agent/quality-gate/rules-manifest.json | jq '.rules'
```

Each rule has: id, engine, dimension, category, severity, rationale, enabled flag.

### Adjusting Severity
Edit `rules-manifest.json`:
```json
{
  "id": "eslint-line-length",
  "severity": "warn",        // change from "error" to "warn"
  ...
}
```

Changes apply to the next scan.

### Disabling Rules
```json
{
  "id": "eslint-line-length",
  "enabled": false,          // disable this rule entirely
  ...
}
```

### Using AI to Propose Tuning
Set `aiCuration: true` in the workflow. The AI reads the aggregated report (not the source code) and suggests:
- Which rules are too noisy
- Which severities are misaligned
- Which new rules would catch recurring patterns

All proposals are advisory and require your approval before applying.

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run AEM Quality Gate
  run: |
    /aem-quality-gate --args '{
      "trustedMode": true,
      "baseDir": "/runner/quality-reports",
      "repositories": [
        {
          "repoUrl": "${{ github.repository }}",
          "repoName": "pr-branch",
          "branch": "${{ github.head_ref }}"
        }
      ]
    }'

- name: Upload Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: quality-reports
    path: /runner/quality-reports/*/quality-reports/
```

### Jenkins Pipeline
```groovy
stage('Quality Gate') {
  steps {
    sh '''
      /aem-quality-gate --args '{
        "trustedMode": true,
        "repositories": [{
          "repoUrl": "https://github.com/your-org/aem-project.git",
          "repoName": "aem-project",
          "branch": "main"
        }]
      }'
    '''
    
    archiveArtifacts artifacts: '**/quality-reports/**'
  }
}
```

## Best Practices

### 1. Start with Safe Mode
```bash
# First run — review the rules and findings
/aem-quality-gate --args '{
  "repositories": [{"repoUrl": "...", ...}]
  # No trustedMode — you'll see each gate
}'
```

### 2. Review Reports Before Merging
The quality reports are **informational only** — they don't block merges. But:
- Blocker/critical findings should be fixed immediately
- Major findings should be fixed in the current sprint
- Minor findings can be addressed when convenient

### 3. Use AI Curation Sparingly
AI rule tuning is useful for:
- ✓ Finding noisy rules to suppress
- ✓ Identifying coverage gaps
- ✗ NOT for re-analyzing code (that's the rule engines' job)

Run with `aiCuration: true` quarterly, not on every scan.

### 4. Exclude Vendor/Generated Code
Add suppressions to `rules-manifest.json` for:
- `node_modules/` directory
- Generated code (e.g., proto-generated Java classes)
- Third-party libraries

Example:
```json
{
  "ruleId": "java-errorprone",
  "pattern": "vendor/**/*",
  "reason": "Third-party code out of scope"
}
```

### 5. Monitor Trends
Keep historical reports to track progress:
- Are dimensions improving (A vs. E ratings)?
- Are blockers/critical findings decreasing?
- Are new developers introducing more violations than before?

## Troubleshooting

### "No core/pom.xml found"
AEM project must have a Maven structure with `core/`, `ui.apps/`, `ui.frontend/` modules.

### "PMD execution failed"
- Ensure Maven is installed: `mvn --version`
- Check that the target repo has a valid pom.xml

### "ESLint/Stylelint: command not found"
- Run `npm install` in `quality-gate/` directory
- Or use `npx --prefix quality-gate eslint ...`

### "Clientlib script failed"
- Ensure Node 18+ is installed: `node --version`
- Check that `ui.apps` directory has `.content.xml` files for clientlibs

### "Too many findings — report is overwhelming"
- Use AI curation to identify noisy rules: `aiCuration: true`
- Disable rules that are generating false positives
- Focus on blocker/critical findings first

## Comparison: This vs. SonarQube

| Feature | Quality Gate | SonarQube |
|---------|-------------|-----------|
| **Cost** | Free (no LLM tokens) | Paid per lines of code |
| **Setup** | 5 minutes | Hours to configure |
| **Speed** | Milliseconds | Minutes |
| **Rule Transparency** | JSON/XML — fully human-editable | Black box |
| **AI Enhancement** | Optional, reads reports only | N/A |
| **Works Offline** | Yes (standalone toolkit) | No (cloud) |
| **AEM-Specific** | Yes (built-in rules) | No (generic Java) |

## Next Steps

1. **Try standalone**: `bash quality-gate/runner/run-quality-gate.sh /path/to/aem-project /tmp/reports`
2. **Review raw reports**: Check the generated JSON/XML files
3. **Run via Claude**: `/aem-quality-gate --args '{...}'` to see the orchestration
4. **Review findings**: Focus on Sling/AEM dimension first (highest risk)
5. **Integrate into CI/CD**: Add the GitHub Actions / Jenkins example to your pipeline

---

**Built with ❤️ by Claude Code — Rule-Driven Quality, AI-Enhanced**
