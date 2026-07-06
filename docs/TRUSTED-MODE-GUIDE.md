# Trusted Mode Guide

## Overview

**Trusted Mode** is an optional, opt-in feature for power users who have reviewed the workflow and want to skip permission gates for faster execution. By default, the workflow runs in **Safe Mode** which requires explicit approval at each major operation.

## Modes Explained

### 🔒 Safe Mode (Default)

**Who**: Everyone by default, especially new users
**Permission Gates**: 3 gates required
1. Repository Setup - Approve before cloning
2. Test Generation - Approve before code creation  
3. Build Validation - Approve before Maven test
4. Auto-Push - No gate, automatic

**Workflow Duration**: ~2-5 minutes (with user approvals)

```
START → Setup Gate? (user decides) → Gen Gate? → Validate Gate? → Auto-Push → END
         (prompt)                    (prompt)     (prompt)        (automatic)
```

### 🔓 Trusted Mode (Opt-In)

**Who**: Power users, CI/CD pipelines, trusted environments
**Permission Gates**: 0 gates - All skipped
1. Repository Setup - Auto-proceed
2. Test Generation - Auto-proceed
3. Build Validation - Auto-proceed
4. Auto-Push - Auto-proceed (as always)

**Workflow Duration**: ~1-2 minutes (no user interaction)

```
START → Setup (auto) → Gen (auto) → Validate (auto) → Auto-Push (auto) → END
```

## Enabling Trusted Mode

### Method 1: Workflow Parameters

```bash
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [
    {
      "repoUrl": "https://github.com/your-org/aem-core.git",
      "productionBranch": "main",
      "testCases": "ServiceImpl, UtilsClass"
    }
  ]
}'
```

### Method 2: Environment Variable (Future)

```bash
export CLAUDE_TRUSTED_MODE=true
/aem-unit-test-cases --args '{"testCases": [...]}'
```

### Method 3: Configuration File (Future)

```json
{
  "trustedMode": true,
  "testCases": [...]
}
```

## Safety Guarantees

Even in Trusted Mode, the workflow maintains critical safety features:

✅ **Build Validation Still Runs**
- Local Maven builds are ALWAYS executed
- Failed tests still prevent push
- Issues are caught before remote push

✅ **Single Repo Location**
- All repos cloned to same `project-unit-test cases/repo` folder
- No scattered clones across filesystem

✅ **Feature Branches Only**
- Changes pushed to `feature/ai-unit-test-cases` (not main/develop)
- Safe for review before merge

✅ **No Credential Handling**
- Workflow doesn't handle passwords or tokens
- Uses existing git configuration

## Use Cases for Trusted Mode

### 1. CI/CD Pipelines
```bash
# In CI/CD script
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [...]
}'
```

### 2. Batch Operations
```bash
# Generate tests for 10+ repos without clicking 30+ times
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [repo1, repo2, repo3, ...]
}'
```

### 3. Automated Testing Pipelines
```bash
# Nightly job that tests all AEM modules
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [all-high-priority-classes]
}'
```

### 4. Experienced Users
```bash
# Power user who has used workflow 100+ times
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [...]
}'
```

## Comparison: Safe vs Trusted Mode

| Feature | Safe Mode | Trusted Mode |
|---------|-----------|--------------|
| Default | ✅ Yes | ❌ No (opt-in) |
| Permission Gates | 3 gates | 0 gates |
| User Interaction Required | Yes (3x) | No |
| Build Validation | ✅ Always | ✅ Always |
| Auto-Push | ✅ Yes | ✅ Yes |
| Recommended For | New users, Reviews | Power users, CI/CD |
| Duration | 2-5 min | 1-2 min |
| Token Overhead | ~2,850 tokens (3 repos) | ~2,550 tokens (3 repos) |

## Example: Safe Mode Workflow

```
$ /aem-unit-test-cases --args '{...}'

Processing 2 repository(ies)
🔒 SAFE MODE - Permission gates required before each major operation

[Repository Setup]
Requesting permission to clone/setup: aem-core
? Approve repository setup? (Y/n)
  → aem-core (user approved)
  ✓ Cloned to project-unit-test cases/repo/aem-core

[Test Generation]  
Requesting permission to generate tests for: aem-core
? Approve test generation? (Y/n)
  → aem-core (user approved)
  ✓ Created 3 test files

[Local Build Validation]
Requesting permission to validate build locally for: aem-core
? Approve build validation? (Y/n)
  → aem-core (user approved)
  ✓ mvn clean test: PASSED (12 tests)

[Auto-Push]
Auto-pushing aem-core - no permission needed
  → Pushed feature/ai-unit-test-cases
  ✓ SUCCESS

Total execution time: 3 minutes 45 seconds
```

## Example: Trusted Mode Workflow

```
$ /aem-unit-test-cases --args '{"trustedMode": true, ...}'

Processing 2 repository(ies)
🔓 TRUSTED MODE ENABLED - Skipping all permission gates

[Repository Setup]
  → Auto-approved: setup for aem-core
  ✓ Cloned to project-unit-test cases/repo/aem-core

[Test Generation]  
  → Auto-approved: generation for aem-core
  ✓ Created 3 test files

[Local Build Validation]
  → Auto-approved: validation for aem-core
  ✓ mvn clean test: PASSED (12 tests)

[Auto-Push]
Auto-pushing aem-core - no permission needed
  → Pushed feature/ai-unit-test-cases
  ✓ SUCCESS

Total execution time: 1 minute 20 seconds
```

## Security Considerations

### ✅ Safe to Use in Trusted Mode When:
- Running in your own CI/CD pipeline
- Testing known, trusted repositories
- Running on your own machine
- With your own GitHub credentials
- In controlled environments

### ⚠️ NOT Recommended for Trusted Mode When:
- Receiving workflows from untrusted sources
- Running community-contributed test cases
- With shared credentials or accounts
- In open-source communities
- In multi-tenant environments

### 🔒 Always Safe (Even in Trusted Mode):
- Local build validation still runs
- Failed tests prevent push
- Only feature branches touched (not main)
- No sensitive data in prompts

## Reversing Trusted Mode

If you enable Trusted Mode but want to revert to Safe Mode:

Simply don't include `trustedMode: true` in args:

```bash
# This runs in Safe Mode (default)
/aem-unit-test-cases --args '{
  "testCases": [...]
}'

# This runs in Trusted Mode (explicit opt-in)
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [...]
}'
```

## Audit Trail

Even in Trusted Mode, the workflow logs show which mode was used:

```
🔓 TRUSTED MODE ENABLED - Skipping all permission gates
  → Auto-approved: setup for aem-core
  → Auto-approved: generation for aem-core
  → Auto-approved: validation for aem-core
```

vs

```
🔒 SAFE MODE - Permission gates required before each major operation
  ? User approval required for setup
  ? User approval required for generation
  ? User approval required for validation
```

## Logging and Monitoring

The result object includes the mode used:

```javascript
{
  mode: "trusted",  // or "safe"
  totalProcessed: 3,
  successful: 3,
  failed: 0,
  skipped: 0,
  optimizations: {
    permissionGates: "DISABLED (trusted mode)"  // Shows mode in results
  }
}
```

## FAQ

**Q: Is Trusted Mode safe to use?**
A: Yes, if you're in a controlled environment. Build validation still runs, preventing bad code from pushing.

**Q: Can Trusted Mode push bad code?**
A: No. If Maven build fails, the push is blocked.

**Q: Should I use Trusted Mode by default?**
A: No. Use Safe Mode by default. Enable Trusted Mode only after you've reviewed the workflow and understand what it does.

**Q: Can I use Trusted Mode in production?**
A: Yes, but only in trusted CI/CD environments with proper access controls.

**Q: What's the token difference?**
A: Trusted Mode saves permission prompts, but build validation still runs. Typical savings: ~300-400 tokens per 3-repo batch.

**Q: Can I mix Safe and Trusted Mode?**
A: No, the mode applies to the entire workflow run. All repos get same mode.

**Q: How do I audit who used Trusted Mode?**
A: Check the result object's `mode` field and logs showing "TRUSTED MODE ENABLED".

## Best Practices

1. **Start with Safe Mode**
   - Use default Safe Mode for first runs
   - Review workflow behavior
   - Build confidence

2. **Graduate to Trusted Mode**
   - Once familiar with workflow
   - Only in appropriate environments
   - For batch/CI operations

3. **Document Your Decision**
   - If using Trusted Mode, document why
   - In CI/CD scripts, add comments explaining opt-in
   - In team policies, clarify when Trusted Mode is allowed

4. **Monitor Results**
   - Always review the summary output
   - Check build validation results
   - Verify correct repos were pushed

5. **Keep Build Validation On**
   - Never disable build validation
   - It's your safety net in Trusted Mode
   - Let it run, don't try to bypass it

## Examples for Your Team

### Example 1: New Team Member (Safe Mode)
```bash
# First time - use Safe Mode to learn
/aem-unit-test-cases --args '{"testCases": [...]}'
# Approve at each gate to understand what happens
```

### Example 2: Regular User (Safe Mode)
```bash
# Recurring testing - Safe Mode for oversight
/aem-unit-test-cases --args '{"testCases": [...]}'
# Quick approvals become second nature
```

### Example 3: CI/CD Job (Trusted Mode)
```bash
# Nightly automation - Trusted Mode for speed
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [...]
}'
# No user interaction needed
```

### Example 4: Batch Operations (Trusted Mode)
```bash
# Testing 20+ repos - Trusted Mode to avoid 60 prompts
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [large-list-of-repos]
}'
# Complete in 20-30 minutes instead of hours
```

---

**Remember**: Default is Safe Mode. Trusted Mode is opt-in. Both are secure due to build validation and feature branch usage.

Use Safe Mode for control. Use Trusted Mode for speed when you know what you're doing.
