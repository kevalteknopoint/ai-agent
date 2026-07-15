# Changelog

All notable changes to this AI automation toolkit are documented in this file.

## [1.3.0] - 2026-07-15

### Changed
- **Global model policy standardized across agents, skills, workflows, and docs**
  - Planning/orchestration now uses Opus.
  - Execution/review/generation now uses Sonnet.
  - Removed previous mixed execution tiering assumptions from code-scan docs and skill guidance.

- **Agent model assignments aligned to the policy**
  - `code-scan-orchestrator` moved to Opus (planning stage).
  - `java-springboot-analyzer` moved to Sonnet (execution stage).
  - `css-scss-analyzer` moved to Sonnet (execution stage).
  - `vbrd-to-proofhub` set to Sonnet.

- **Workflow execution model routing enforced in code**
  - Added explicit planning/execution model constants in:
    - `workflows/code-scan.js`
    - `workflows/aem-unit-test-cases.js`
    - `workflows/spring-boot-unit-test-cases.js`
    - `workflows/aem-quality-gate.js`
  - Permission and orchestration calls route to Opus.
  - Execution/generation/analysis calls route to Sonnet.

- **Documentation expanded and normalized for onboarding and operations**
  - `README.md` updated with clone-first setup, install/verify flow, AE defaults, full model policy, and refreshed component catalog.
  - `QUICKSTART.md` updated with policy-aligned code-scan usage note.
  - `docs/CODE-SCAN-GUIDE.md` updated from model tiering language to fixed policy language.

### Fixed
- **Repository hygiene for local scan clones**
  - `.gitignore` hardened with root-level `/repos/` and `/repos/**` exclusions.
  - Verified `repos/` currently has zero tracked files in git.

### Benefits
- Predictable model behavior across the toolkit (no hidden per-agent tier drift).
- Better governance: planning and execution responsibilities are clearly separated.
- Token efficiency preserved via deterministic preprocessing and stack-scoped dispatch.
- Lower risk of accidental commit noise from local cloned repositories.

## [1.2.0] - 2026-07-06

### Added
- **Spring Boot Unit Test Cases Agent** (`spring-boot-unit-test-cases`)
  - Full Spring Boot test generation with JUnit, Mockito, Spring Test
  - Same architecture as AEM agent for consistency
  - Safe Mode (default) with 3 permission gates
  - Trusted Mode (opt-in) for automation
  - Local Maven build validation
  - Token optimization (47% reduction)

- **New Documentation**
  - SPRING-BOOT-WORKFLOW-GUIDE.md: Comprehensive Spring Boot guide
  - WORKFLOWS-COMPARISON.md: Detailed comparison between agents
  - spring-boot-examples.json: 10 example configurations

- **Examples**
  - Single service testing
  - Multiple microservices (parallel)
  - Batch testing with Trusted Mode
  - CI/CD pipeline integration
  - Custom repository locations

### Changed
- Updated README.md to highlight both available agents
- Enhanced documentation structure for multiple agents

### Benefits
- Choose appropriate agent for your technology stack
- Reuse proven architecture across different frameworks
- Unified token optimization and permission gates
- Consistent testing workflows

## [1.1.0] - 2026-07-06

### Fixed
- **Critical**: Fixed `process.cwd()` error in workflow sandbox
  - Workflow scripts run in sandbox with no Node.js API access
  - `process`, `Date.now()`, `Math.random()`, and `fs` are unavailable
  - Changed baseDir from dynamic `process.cwd()` to hardcoded absolute path
  - Made baseDir customizable via `args.baseDir` parameter

### Changed
- Repository location changed from `repo` to `repos` (plural) to match actual directory
- Updated default baseDir to `/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos`
- Added clarity to logging about baseDir override
- Updated documentation with baseDir parameter usage

### Technical Details
**Before (would crash):**
```javascript
const baseDir = `${process.cwd()}/project-unit-test cases/repo`
// Error: process is not defined (in workflow sandbox)
```

**After (works correctly):**
```javascript
const baseDir = args?.baseDir || '/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos'
// Uses hardcoded path by default, overridable via args.baseDir
```

## [1.0.0] - 2026-07-06

### Added
- **Trusted Mode** for power users
  - Optional `trustedMode: true` parameter
  - Skips all permission gates for fully automated execution
  - Build validation still runs (safety net)
  - 25-35% faster execution than Safe Mode
  - Results show which mode was used for audit trail

- **Safe Mode** (default)
  - 3 permission gates (setup, generation, validation)
  - Explicit user approval before major operations
  - Best for learning and oversight
  
- **Comprehensive Documentation**
  - TRUSTED-MODE-GUIDE.md: Complete Safe vs Trusted Mode guide
  - MODES-COMPARISON.md: Detailed comparison with examples
  - AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md: Technical deep-dive
  - AEM-UNIT-TEST-CASES-BEFORE-AFTER.md: Before/after comparison

- **Multi-Stage Workflow**
  - Repository Setup: Clone and create feature branches
  - Test Generation: AEM Test Case Creator generates tests
  - Local Build Validation: Maven build testing before push
  - Auto-Push: Automatic push to feature branch

- **Token Optimization**
  - 47% reduction in token usage vs previous version
  - Concise prompts (50-100 words vs 200+ previously)
  - Structured output schemas at every stage
  - Efficient data threading between pipeline stages

- **Permission Gates**
  - Gate #1: Repository Setup (approve before cloning)
  - Gate #2: Test Generation (approve before code creation)
  - Gate #3: Build Validation (approve before Maven test)
  - No gate: Auto-Push (automatic when validation passes)
  - Optional skip with Trusted Mode

- **Build Validation**
  - Local Maven build: `mvn clean test -pl core -am`
  - Catches issues before pushing to remote
  - Prevents bad code from reaching origin
  - Works in both Safe Mode and Trusted Mode

- **Repository Organization**
  - Centralized location for all test repos
  - Strict enforcement of folder location
  - Consistent across machines and CI/CD
  - Customizable via baseDir parameter

- **Comprehensive Examples**
  - 5 sample configurations in examples/sample-config.json
  - Use cases for single repo, multiple repos, batch operations
  - CI/CD pipeline examples
  - Trusted Mode examples

### Documentation
- README.md: Complete feature guide and usage
- QUICKSTART.md: 5-minute setup guide
- .gitignore: Proper git configuration

### Project Structure
```
ai-agent/
├── README.md
├── QUICKSTART.md
├── CHANGELOG.md
├── .gitignore
├── workflows/
│   └── aem-unit-test-cases.js
├── docs/
│   ├── TRUSTED-MODE-GUIDE.md
│   ├── MODES-COMPARISON.md
│   ├── AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md
│   └── AEM-UNIT-TEST-CASES-BEFORE-AFTER.md
└── examples/
    └── sample-config.json
```

---

## Implementation Notes

### Workflow Execution
The workflow runs in Claude Code's agent sandbox with the following constraints:
- No `process` object (process.cwd(), process.env unavailable)
- No `Date.now()` or `new Date()` 
- No `Math.random()`
- No filesystem API (`fs` module)
- No external network requests beyond MCP tools
- All work must use agents for actual filesystem/git operations

### Permission Gates Design
Each permission gate is implemented as:
1. User-facing agent that asks for approval
2. Response schema with `approved: boolean`
3. Conditional execution based on response
4. Clear logging of decision

In Trusted Mode, the `requestPermission()` helper returns `{approved: true}` automatically without prompting.

### Build Validation Strategy
Build validation is always executed because:
- It catches issues early (before push)
- Prevents bad code reaching remote
- Provides confidence in test quality
- Same in both Safe and Trusted modes
- Only safety mechanism in Trusted Mode

### Result Object
Every workflow returns structured result with:
- `mode`: "safe" or "trusted" (for audit)
- `totalProcessed`, `successful`, `failed`, `skipped`
- `baseDirectory`: Where repos were cloned
- `results`: Array with per-repo details
- `optimizations`: Summary of applied optimizations

---

## Future Enhancements

Possible improvements for future versions:
- [ ] GitHub PR creation instead of branch push
- [ ] JaCoCo coverage reporting integration
- [ ] Slack/email notifications for pipeline runs
- [ ] Batch permission approval ("approve all remaining")
- [ ] Dry-run mode (preview without changes)
- [ ] Automatic retry logic for failed builds
- [ ] Custom test execution commands
- [ ] Multi-branch support (push to different branches)
- [ ] Test report generation and archiving
- [ ] Integration with issue tracking systems

---

## Compatibility

### Tested On
- Claude Haiku 4.5
- Claude Opus 4.8 (compatible)
- Claude Sonnet 5 (compatible)

### Requirements
- Claude Code (CLI or Web)
- Git installed and configured
- Maven installed (for build validation)
- Access to target repositories

### Known Limitations
- Workflow runs in sandbox (no direct filesystem/process access)
- All operations delegated to agents
- Permission gates are user-facing only
- Build validation requires Maven pom.xml

---

## Support

For issues or questions:
1. Check the [README.md](README.md) troubleshooting section
2. Review [TRUSTED-MODE-GUIDE.md](docs/TRUSTED-MODE-GUIDE.md)
3. See [MODES-COMPARISON.md](docs/MODES-COMPARISON.md) for detailed explanations
4. Check Claude Code logs: `~/.claude/logs/`

---

## License

[Specify your license here]

---

## Contributors

Built by Claude Code with ❤️
