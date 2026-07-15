# AEM Development Automation Toolkit

AI-powered and rule-driven automation for Adobe AEM as a Cloud Service (AEMaaCS) projects: unit test generation, Spring Boot testing, rule-driven quality analysis, and multi-agent security-first code scanning.

## Available Workflows

### Code Scanning (Multi-Agent, Stack-Aware)

🔎 **Code Scan** (`code-scan`)
- Give it a GitHub URL and branch — it clones/updates, detects the tech stack, and dispatches only the analyzers that apply
- Five specialized reviewers: Java/Spring Boot, AEM Sightly (HTL), EDS blocks, JS/React, CSS/SCSS
- Each writes a severity-ranked Markdown report + Excel issue tracker to `./analysis/` in the scanned repo
- Model tier scales with blast radius: Opus for the Java/Spring Boot backend, Sonnet for AEM HTL/EDS/React, Haiku for CSS — plus zero-token deterministic clone/detect/xlsx-build steps
- Two entry points: the `code-scan` **skill** (interactive — asks for URL/branch) or the `code-scan` **workflow** (headless — pass `repoUrl`/`branch` as args)
- 👉 See [CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md) for the full pipeline and model-tiering rationale

### Testing & Code Generation (AI-Driven)

🏗️ **AEM Unit Test Cases** (`aem-unit-test-cases`)
- For Adobe AEM Sites backend projects
- Generates high-quality unit tests with 80%+ coverage
- AEM-specific testing patterns (Sling Models, Servlets, Services)
- Framework: JUnit, Mockito, AEM Mocks

🚀 **Spring Boot Unit Test Cases** (`spring-boot-unit-test-cases`)
- For Spring Boot applications
- Generates high-quality unit tests with 80%+ coverage  
- Spring Boot-specific testing patterns
- Framework: JUnit, Mockito, Spring Test

### Quality & Compliance (Rule-Driven, Zero AI for Scanning)

📊 **AEM Quality Gate** (`aem-quality-gate`)
- Rule-driven static analysis for AEMaaCS projects
- Enforces Java, Sling, HTL, JavaScript, CSS, and HTML best practices
- **Zero LLM tokens consumed for scanning** — uses deterministic rule engines
- Optional AI enhancement for rule tuning only
- Generates A-E quality ratings per dimension

## Overview

### Test Generation Agents

The **AEM Unit Test Cases** and **Spring Boot Unit Test Cases** are AI-driven workflows that:

✅ **Token Optimized** - 47% reduction in token usage
✅ **Safe by Default** - Explicit approval gates for setup, generation, and validation
✅ **Trusted Mode Ready** - Optional fast-track for power users (skip gates, keep validation)
✅ **Build-Validated** - Local Maven builds tested before pushing to remote
✅ **Centrally Organized** - Enforces strict repository location
✅ **Production-Ready** - Auto-push to feature branch when validation passes

### Quality Gate Workflow

The **AEM Quality Gate** is a rule-driven static analysis tool that:

✅ **Zero-Token Scanning** - All checks run locally via deterministic rule engines (PMD, Checkstyle, ESLint, Stylelint)
✅ **No AI Required for Scans** - Fastest, most cost-efficient scanning
✅ **AI-Enhanced Rule Tuning** - Optional: AI reads reports and proposes rule improvements (never re-analyzes code)
✅ **Comprehensive Coverage** - Java, Sling, HTL, JavaScript, CSS, HTML, Clientlibs
✅ **AEMaaCS-Optimized** - Built-in rules for ResourceResolver leaks, Sling Model issues, WCMUsePojo, etc.
✅ **SonarQube-Like Reporting** - A-E dimension ratings with severity-normalized findings

## Features

### 1. Token Optimization
- Concise prompts (50-100 words vs. 200+ previously)
- Structured output schemas at every stage
- ~47% token reduction per repository
- Efficient parallel processing

### 2. Multi-Stage Pipeline
- **Stage 1: Repository Setup** (permission gate)
  - Clone repos to centralized location
  - Create feature branches
  - Validate repo readiness

- **Stage 2: Test Generation** (permission gate)
  - AEM Test Case Creator analyzes codebase
  - Generates high-quality unit tests
  - Places tests in `src/test/java/`

- **Stage 3: Local Build Validation** (permission gate)
  - Runs `mvn clean test -pl core -am`
  - Validates all tests pass locally
  - Catches issues before pushing

- **Stage 4: Auto-Push** (NO permission gate)
  - Automatically pushes to `feature/ai-unit-test-cases`
  - No user intervention needed after validation passes

### 3. Permission Gates (Safe Mode)
The workflow requests explicit permission before expensive operations:
- ✓ Repository Setup: User approves before cloning
- ✓ Test Generation: User approves before code creation
- ✓ Build Validation: User approves before Maven test
- ✗ Auto-Push: No permission needed (already validated)

**Optional Trusted Mode** (for power users):
- 🔓 Skip all permission gates
- ⚡ Faster execution (1-2 min vs 2-5 min)
- ✅ Build validation still runs
- Safe for CI/CD and batch operations

👉 See [Trusted Mode Guide](docs/TRUSTED-MODE-GUIDE.md)

### 4. Centralized Repository Location
All repositories are cloned to:
```
/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos
```

**Override Location:**
```bash
/aem-unit-test-cases --args '{
  "baseDir": "/your/custom/path",
  "testCases": [...]
}'
```

Benefits:
- Organized, predictable location
- Easy cleanup and management
- No scattered clones across filesystem
- Consistent across CI/CD pipelines
- Customizable via baseDir parameter

## Usage

### Prerequisites
- Claude Code or Claude API access
- Git installed and configured
- Maven installed (for build validation)
- Access to target repositories

### Basic Invocation

```bash
/aem-unit-test-cases
```

Or with explicit test cases (Safe Mode):

```bash
/aem-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/org/aem-core.git",
      "productionBranch": "main",
      "testCases": "ServiceImpl, UtilsClass, ModelClass"
    },
    {
      "repoUrl": "https://github.com/org/aem-models.git",
      "productionBranch": "develop",
      "testCases": "all high-priority"
    }
  ]
}'
```

Or with Trusted Mode (power users only):

```bash
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [
    {
      "repoUrl": "https://github.com/org/aem-core.git",
      "productionBranch": "main",
      "testCases": "ServiceImpl, UtilsClass, ModelClass"
    }
  ]
}'
```

### Workflow Parameters

```javascript
{
  "testCases": [
    {
      "repoUrl": string,           // GitHub repository URL
      "productionBranch": string,  // Main branch (e.g., "main", "develop")
      "testCases": string          // Classes to test or "all high-priority"
    }
  ]
}
```

## Execution Flow

```
START
  ↓
INPUT VALIDATION
  └─ Parse test cases
  └─ Enforce baseDir location
  └─ Log optimization details
  ↓
REPOSITORY SETUP (permission gate #1)
  └─ Ask user approval
  └─ Clone to ${baseDir}/${repoName}
  └─ Create feature/ai-unit-test-cases branch
  ↓
TEST GENERATION (permission gate #2)
  └─ Ask user approval
  └─ AEM Test Case Creator analyzes code
  └─ Creates tests in src/test/java/
  ↓
LOCAL BUILD VALIDATION (permission gate #3)
  └─ Ask user approval
  └─ Run: mvn clean test -pl core -am
  └─ Validate all tests pass
  └─ Fix issues if possible
  ↓
AUTO-PUSH (NO permission gate)
  └─ Auto-push to feature/ai-unit-test-cases
  └─ Commit: "feat: Add comprehensive AEM unit tests"
  └─ No user interaction needed
  ↓
SUMMARY
  └─ Report results
  └─ Show optimization metrics
  └─ List repository locations
```

## Results Output

The workflow returns a comprehensive result object:

```javascript
{
  totalProcessed: number,
  successful: number,        // Pushed successfully
  failed: number,            // Build/validation failed
  skipped: number,           // User denied permission
  baseDirectory: string,
  optimizations: {
    tokenReduction: string,
    permissionGates: string,
    strictLocation: string,
    buildValidation: string
  },
  results: [
    {
      repoName: string,
      repoUrl: string,
      repoPath: string,
      featureBranchPushed: boolean,
      testFilesCreated: string[],
      buildValidated: boolean,
      buildErrors?: string[],
      testsSummary?: string
    }
  ]
}
```

## Response Status Indicators

- **✓ PUSHED** - Successfully cloned, tested, validated, and pushed
- **⊘ SKIPPED** - User denied permission at some gate
- **✗ FAILED** - Error during setup, generation, or validation

## Choosing Your Workflow

### For Test Generation

**AEM Projects?** Use `aem-unit-test-cases`
```bash
/aem-unit-test-cases --args '{
  "testCases": [{
    "repoUrl": "https://github.com/org/aem-project.git",
    "productionBranch": "main",
    "testCases": "UserService, AuthController"
  }]
}'
```

**Spring Boot Projects?** Use `spring-boot-unit-test-cases`
```bash
/spring-boot-unit-test-cases --args '{
  "testCases": [{
    "repoUrl": "https://github.com/org/spring-app.git",
    "productionBranch": "main",
    "testCases": "UserService, OrderController"
  }]
}'
```

👉 See [WORKFLOWS-COMPARISON.md](docs/WORKFLOWS-COMPARISON.md) for detailed comparison

### For Quality Analysis

**Any AEMaaCS Project?** Use `aem-quality-gate`
```bash
/aem-quality-gate --args '{
  "repositories": [{
    "repoUrl": "https://github.com/org/aem-project.git",
    "repoName": "my-aem-app",
    "branch": "main"
  }]
}'
```

✨ Zero AI tokens consumed for scanning — rule engines run locally

👉 See [AEM-QUALITY-GATE-GUIDE.md](docs/AEM-QUALITY-GATE-GUIDE.md) for detailed guide

### For Deep, Stack-Aware Code Review

**Any AEM/EDS/Spring Boot/React repo?** Use `code-scan`

Interactive (asks for the URL and branch):
```
Use the code-scan skill on https://github.com/org/aem-project.git
```

Headless/batch:
```bash
/code-scan --args '{
  "repoUrl": "https://github.com/org/aem-project.git",
  "branch": "main"
}'
```

Unlike Quality Gate (rule-engine linting, zero AI), `code-scan` runs five
domain-expert LLM reviewers — but only the ones whose stack is actually
detected in the repo, and each on the model tier its blast radius warrants.

👉 See [CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md) for detailed guide

## Documentation

### Test Generation
- **[WORKFLOWS-COMPARISON.md](docs/WORKFLOWS-COMPARISON.md)** - Compare AEM vs Spring Boot agents
- **[TRUSTED-MODE-GUIDE.md](docs/TRUSTED-MODE-GUIDE.md)** - Safe Mode vs Trusted Mode, use cases, and best practices
- **[SPRING-BOOT-WORKFLOW-GUIDE.md](docs/SPRING-BOOT-WORKFLOW-GUIDE.md)** - Spring Boot agent guide
- **[AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md](docs/AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md)** - AEM agent technical guide
- **[AEM-UNIT-TEST-CASES-BEFORE-AFTER.md](docs/AEM-UNIT-TEST-CASES-BEFORE-AFTER.md)** - AEM before/after comparison

### Quality Analysis
- **[AEM-QUALITY-GATE-GUIDE.md](docs/AEM-QUALITY-GATE-GUIDE.md)** - Complete Quality Gate guide, usage, rules, and CI/CD integration
- **[README.md](quality-gate/)** - Quality Gate toolkit directory with rule definitions

### Code Scanning
- **[CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md)** - Full pipeline, stack-detection rules, and model-tiering rationale

## File Structure

```
ai-agent/
├── README.md                                          # This file
├── QUICKSTART.md                                      # 5-minute setup guide
├── CHANGELOG.md                                       # Version history
├── workflows/
│   ├── aem-unit-test-cases.js                         # AEM test generation
│   ├── spring-boot-unit-test-cases.js                 # Spring Boot test generation
│   ├── aem-quality-gate.js                            # Quality analysis
│   └── code-scan.js                                   # Multi-agent code scan, headless/batch (NEW)
├── agents/
│   ├── vbrd-to-proofhub.md                            # VBRD → ProofHub translation
│   ├── code-scan-orchestrator.md                      # Clone/branch/detect router (haiku) (NEW)
│   ├── java-springboot-analyzer.md                    # Backend security review (opus) (NEW)
│   ├── aem-htl-analyzer.md                            # HTL/Sightly XSS + authoring review (sonnet) (NEW)
│   ├── eds-blocks-analyzer.md                         # EDS blocks CWV + DOM review (sonnet) (NEW)
│   ├── js-react-analyzer.md                           # React correctness/security review (sonnet) (NEW)
│   └── css-scss-analyzer.md                           # CSS/SCSS architecture review (haiku) (NEW)
├── skills/
│   └── code-scan/
│       └── SKILL.md                                   # Interactive code-scan entry point (NEW)
├── scripts/
│   ├── clone_or_update.sh                             # Deterministic clone/checkout/pull (NEW)
│   ├── detect_stack.sh                                # Deterministic tech-stack detector (NEW)
│   └── build_issues_xlsx.py                           # JSON findings → xlsx tracker (NEW)
├── quality-gate/                                      # Quality Gate Toolkit
│   ├── package.json                                   # Frontend tools (ESLint, Stylelint)
│   ├── rules-manifest.json                            # Master rule catalog
│   ├── rules/
│   │   ├── java/                                      # PMD + Checkstyle configs
│   │   ├── frontend/                                  # ESLint, Stylelint, HTMLHint configs
│   │   ├── htl/                                       # HTL validator config
│   │   └── custom/                                    # Custom clientlib checker
│   ├── runner/
│   │   └── run-quality-gate.sh                        # Orchestrates all engines
│   └── aggregator/
│       └── aggregate-report.js                        # Parses outputs into unified report
├── docs/
│   ├── WORKFLOWS-COMPARISON.md                        # AEM vs Spring Boot
│   ├── TRUSTED-MODE-GUIDE.md                          # Safe vs Trusted Mode
│   ├── SPRING-BOOT-WORKFLOW-GUIDE.md                  # Spring Boot guide
│   ├── AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md           # AEM technical deep-dive
│   ├── AEM-UNIT-TEST-CASES-BEFORE-AFTER.md            # AEM before/after
│   ├── AEM-QUALITY-GATE-GUIDE.md                      # Quality Gate complete guide
│   └── CODE-SCAN-GUIDE.md                             # Code-scan pipeline + model tiering (NEW)
└── examples/
    ├── sample-config.json                             # AEM test generation examples
    ├── spring-boot-examples.json                      # Spring Boot test examples
    ├── quality-gate-examples.json                     # Quality Gate examples
    └── code-scan-examples.json                        # Code-scan examples (NEW)
```

## Key Optimizations

### Token Usage
| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Setup prompt | 240 tokens | 80 tokens | 67% |
| Test gen prompt | 320 tokens | 170 tokens | 47% |
| Validation prompt | 180 tokens | 100 tokens | 44% |
| **Per repo total** | **~1,800** | **~950** | **~47%** |

### Schema Definitions
- Reduced from 16 lines to 8 lines
- Removed verbose descriptions
- Only essential properties defined
- 50% smaller schema footprint

### Permission Gates
- User controls expensive operations
- Skip-friendly (marked as skipped, not failed)
- Auto-push when validation passes
- Better user experience and confidence

## Performance Benefits

- **Concurrency**: Multiple repos processed in parallel across pipeline stages
- **Efficiency**: Pipeline model allows repos in different stages simultaneously
- **Speed**: No sequential barriers or unnecessary waits
- **Cost**: 47% token reduction = significant cost savings at scale

## Security Considerations

- ✅ No sensitive data in prompts
- ✅ Permission gates prevent uncontrolled operations
- ✅ Build validation catches malicious code issues
- ✅ Local build test before remote push
- ✅ Feature branches (not main/develop)

## Troubleshooting

### Permission Denied at Setup
**Cause**: User denied cloning repository
**Solution**: Re-run workflow and approve at permission gate

### Permission Denied at Generation
**Cause**: User denied test creation
**Solution**: Review test classes and retry, or deny intentionally to skip

### Permission Denied at Validation
**Cause**: User denied local build test
**Solution**: Test build locally first, fix issues, then retry

### Build Validation Failed
**Cause**: Maven build did not pass
**Solution**: Review buildErrors, fix test cases, retry workflow

### Auto-Push Failed
**Cause**: Network, auth, or remote changes
**Solution**: Check git logs, resolve push errors manually

## Future Enhancements

Possible improvements:
- Batch permission for all remaining repos after first approval
- Dry-run mode to preview without changes
- Auto-retry logic for failed builds
- Coverage reporting via JaCoCo integration
- Automatic PR creation instead of branch push
- Slack/email notifications for progress updates

## Contributing

To contribute improvements to this workflow:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request with detailed description

## Support

For issues, questions, or feature requests:
- Check the [Documentation](docs/)
- Review the [Troubleshooting](#troubleshooting) section
- Contact the maintainers

## License

[Specify your license here]

## Changelog

### v1.0.0 (2026-07-06)
- Initial release
- Token optimization: 47% reduction
- Multi-stage pipeline with permission gates
- Local build validation before push
- Centralized repository location enforcement
- Comprehensive documentation

---

**Built with ❤️ using Claude Code and Claude API**

For more information about Claude Code, visit: https://github.com/anthropics/claude-code

For Claude API documentation, visit: https://docs.anthropic.com
