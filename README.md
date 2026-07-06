# Unit Test Cases Workflow Agents

Comprehensive AI workflow agents for orchestrating unit test case creation across multiple repositories with advanced optimization, permission gates, and local build validation.

## Available Agents

🏗️ **AEM Unit Test Cases** (`aem-unit-test-cases`)
- For Adobe AEM Sites backend projects
- AEM-specific testing patterns
- JUnit, Mockito, AEM Mocks

🚀 **Spring Boot Unit Test Cases** (`spring-boot-unit-test-cases`)
- For Spring Boot applications
- Spring Boot testing patterns  
- JUnit, Mockito, Spring Test

Both agents share identical architecture with technology-specific optimizations.

## Overview

The **AEM Unit Test Cases** agent is a multi-stage workflow that:

✅ **Token Optimized** - 47% reduction in token usage vs. previous version
✅ **Safe by Default** - Explicit approval gates for setup, generation, and validation
✅ **Trusted Mode Ready** - Optional fast-track for power users (skip gates, keep validation)
✅ **Build-Validated** - Local Maven builds tested before pushing to remote
✅ **Centrally Organized** - Enforces strict repository location
✅ **Production-Ready** - Auto-push when validation passes

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

## Choosing Your Agent

### AEM Projects? Use `aem-unit-test-cases`
```bash
/aem-unit-test-cases --args '{"testCases": [...]}'
```

### Spring Boot Projects? Use `spring-boot-unit-test-cases`
```bash
/spring-boot-unit-test-cases --args '{"testCases": [...]}'
```

👉 See [WORKFLOWS-COMPARISON.md](docs/WORKFLOWS-COMPARISON.md) for detailed comparison

## Documentation

- **[WORKFLOWS-COMPARISON.md](docs/WORKFLOWS-COMPARISON.md)** - Compare AEM vs Spring Boot agents
- **[TRUSTED-MODE-GUIDE.md](docs/TRUSTED-MODE-GUIDE.md)** - Safe Mode vs Trusted Mode, use cases, and best practices
- **[SPRING-BOOT-WORKFLOW-GUIDE.md](docs/SPRING-BOOT-WORKFLOW-GUIDE.md)** - Spring Boot agent guide
- **[AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md](docs/AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md)** - AEM agent technical guide
- **[AEM-UNIT-TEST-CASES-BEFORE-AFTER.md](docs/AEM-UNIT-TEST-CASES-BEFORE-AFTER.md)** - AEM before/after comparison

## File Structure

```
ai-agent/
├── README.md                                          # This file
├── workflows/
│   └── aem-unit-test-cases.js                         # Main workflow agent
├── docs/
│   ├── AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md           # Technical documentation
│   └── AEM-UNIT-TEST-CASES-BEFORE-AFTER.md            # Comparison guide
└── examples/
    └── (Sample test cases and configurations)
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
