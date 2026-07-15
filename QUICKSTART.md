# Quick Start Guide

This toolkit has four workflows and a code-scan skill — see [README.md](README.md) for the full
catalog. This guide covers the fastest path for each; the detailed walkthrough below (permission
gates, examples, troubleshooting) is written for `aem-unit-test-cases` specifically but the same
shape applies to `spring-boot-unit-test-cases`.

## Code Scan — 2-Minute Start (most common ask: "review this repo")

**One-time setup** so it's available from any project directory, not just from inside this repo:
```bash
./scripts/install-global.sh
```
(See [README.md → Wiring it into Claude Code](README.md#2-wiring-it-into-claude-code--making-it-invokable-from-anywhere)
for what this does and how to target a different `.claude/` location.) Start a fresh Claude Code
session after running it.

Then, from anywhere:

Interactive — just tell Claude Code what to scan, no JSON needed:
```
Use the code-scan skill on https://github.com/org/aem-project.git
```
It asks which branch, shows you the detected stack (Java/Spring Boot, AEM HTL, EDS blocks,
React, CSS/SCSS — whichever apply), confirms the plan, then runs only the matching reviewer
agents in parallel. Reports land in `analysis/` at the root of the cloned repo.

Headless (no prompts — for CI or scripted runs):
```bash
/code-scan --args '{"repoUrl": "https://github.com/org/aem-project.git", "branch": "main"}'
```

Beyond that one-time install, no dependency to install — cloning, stack detection, and the CSV
tracker are all zero-dependency shell/Python (stdlib only).
👉 [CODE-SCAN-GUIDE.md](docs/CODE-SCAN-GUIDE.md) for the full pipeline.

## Quality Gate — Zero-AI Lint Pass

```bash
/aem-quality-gate --args '{"repositories":[{"repoUrl":"https://github.com/org/aem-project.git","repoName":"my-app","branch":"main"}]}'
```
Needs `cd quality-gate && npm install` once (pulls in ESLint/Stylelint). No LLM tokens spent
scanning. 👉 [AEM-QUALITY-GATE-GUIDE.md](docs/AEM-QUALITY-GATE-GUIDE.md)

## Unit Test Generation — 5-Minute Setup

### 1. Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

Or use the web app at https://claude.ai/code

### 2. Load the Workflow
The workflow is already configured in your Claude Code environment:
```bash
/aem-unit-test-cases
```

### 3. Prepare Your Test Cases
Create a file with your repository information:

```json
{
  "testCases": [
    {
      "repoUrl": "https://github.com/your-org/aem-core.git",
      "productionBranch": "main",
      "testCases": "ServiceImpl, UtilsClass"
    }
  ]
}
```

**Optional Parameters:**
```json
{
  "baseDir": "/custom/repo/location",
  "trustedMode": false,
  "testCases": [...]
}
```

### 4. Run the Workflow
```bash
/aem-unit-test-cases --args '{"testCases": [...]}'
```

### 5. Follow the Prompts
The workflow will ask for permission at 3 stages:
- ✓ Repository Setup
- ✓ Test Generation
- ✓ Build Validation
- ✗ Auto-Push (automatic, no prompt)

## Example 1: Single Repository

```bash
/aem-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/company/aem-core.git",
      "productionBranch": "main",
      "testCases": "UserService, AuthUtil"
    }
  ]
}'
```

## Example 2: Multiple Repositories

```bash
/aem-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/company/aem-core.git",
      "productionBranch": "main",
      "testCases": "ServiceImpl, UtilsClass"
    },
    {
      "repoUrl": "https://github.com/company/aem-models.git",
      "productionBranch": "develop",
      "testCases": "all high-priority"
    },
    {
      "repoUrl": "https://github.com/company/aem-api.git",
      "productionBranch": "main",
      "testCases": "RestController, RequestHandler"
    }
  ]
}'
```

## Example 3: Trusted Mode (Power Users Only)

Skip all permission gates for faster execution:

```bash
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [
    {
      "repoUrl": "https://github.com/company/aem-core.git",
      "productionBranch": "main",
      "testCases": "ServiceImpl, UtilsClass"
    },
    {
      "repoUrl": "https://github.com/company/aem-models.git",
      "productionBranch": "develop",
      "testCases": "all high-priority"
    }
  ]
}'
```

**Trusted Mode Features:**
- 🔓 Skips all permission gates
- ⚡ Faster execution (1-2 min vs 2-5 min)
- ✅ Build validation still runs
- ⚠️ Opt-in only, disabled by default

**When to Use:**
- CI/CD pipelines
- Batch testing operations
- Power users who reviewed the workflow
- Trusted environments

👉 **See [TRUSTED-MODE-GUIDE.md](docs/TRUSTED-MODE-GUIDE.md) for detailed documentation**

## What Happens During Execution

### Stage 1: Repository Setup
- The workflow asks: "Approve cloning this repository?"
- Shows: Repo name, URL, target location, branch
- You: Approve or Deny
- Result: Repo cloned to `project-unit-test cases/repo/{repo-name}`

### Stage 2: Test Generation
- The workflow asks: "Approve test generation?"
- Shows: Repo, target classes, location
- You: Approve or Deny
- Result: Test files created in `src/test/java/`

### Stage 3: Build Validation
- The workflow asks: "Approve local build validation?"
- Shows: Repo, build command, expected duration
- You: Approve or Deny
- Result: `mvn clean test -pl core -am` runs locally

### Stage 4: Auto-Push
- NO permission asked
- Automatically pushes to `feature/ai-unit-test-cases`
- Creates commit: "feat: Add comprehensive AEM unit tests"
- Pushes to origin

## Understanding Results

After execution, you'll see:

```
Completed: 2 pushed, 0 failed, 0 skipped out of 2 total

Optimizations Applied:
  - Token usage reduced: Concise prompts + structured schemas
  - Permission gates: Requested before setup, generation, validation
  - Auto-push: No permission needed after build validation passes
  - Strict location: All repos cloned to /path/.../repo

Repository locations:
  1. [✓ PUSHED] aem-core → /path/project-unit-test cases/repo/aem-core
  2. [✓ PUSHED] aem-models → /path/project-unit-test cases/repo/aem-models
```

**Status Meanings:**
- ✓ PUSHED = Successfully cloned, tested, validated, and pushed
- ⊘ SKIPPED = User denied permission at some gate
- ✗ FAILED = Error during setup, generation, or validation

## Common Workflows

### Workflow A: Generate Tests for Single Service
```bash
/aem-unit-test-cases --args '{
  "testCases": [{
    "repoUrl": "https://github.com/acme/auth-service.git",
    "productionBranch": "main",
    "testCases": "AuthService, TokenValidator"
  }]
}'
```

### Workflow B: Batch Test Multiple Modules
```bash
/aem-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/acme/core-module.git",
      "productionBranch": "develop",
      "testCases": "all high-priority"
    },
    {
      "repoUrl": "https://github.com/acme/utils-module.git",
      "productionBranch": "develop",
      "testCases": "all high-priority"
    },
    {
      "repoUrl": "https://github.com/acme/models-module.git",
      "productionBranch": "main",
      "testCases": "ModelClass, EntityClass"
    }
  ]
}'
```

### Workflow C: Review Tests Before Pushing
If you want to review tests before auto-push:
1. Approve Setup & Generation & Validation
2. The tests are now in `project-unit-test cases/repo/{repo}/src/test/java/`
3. Review the test files
4. The auto-push happens automatically (you can cancel before validation if needed)

## Troubleshooting

### "Permission denied" error
Check you have permission to clone the repository:
```bash
git clone https://github.com/your-org/repo.git
```

### "Build validation failed"
Check Maven is installed:
```bash
mvn --version
```

And the repository has a `pom.xml`:
```bash
cd project-unit-test\ cases/repo/{repo-name}
ls pom.xml
```

### "Cannot push to branch"
Check you have write access:
```bash
git clone https://github.com/your-org/repo.git
git checkout -b feature/ai-unit-test-cases
git push -u origin feature/ai-unit-test-cases
```

## Next Steps

1. **Review Documentation**: Read [README.md](README.md) for full details
2. **Check Optimizations**: See [docs/AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md](docs/AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md)
3. **Compare Versions**: Check [docs/AEM-UNIT-TEST-CASES-BEFORE-AFTER.md](docs/AEM-UNIT-TEST-CASES-BEFORE-AFTER.md)
4. **Run Your First Test**: Execute `/aem-unit-test-cases` with your repo data

## Support

For issues or questions:
1. Check the [README.md](README.md) troubleshooting section
2. Review the [full documentation](docs/)
3. Check Claude Code logs: `~/.claude/logs/`

---

Happy testing! 🚀
