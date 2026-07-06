# Safe Mode vs Trusted Mode - Quick Comparison

## At a Glance

| Aspect | Safe Mode | Trusted Mode |
|--------|-----------|--------------|
| **Default** | ✅ Yes | ❌ No (opt-in) |
| **Permission Gates** | 3 gates | 0 gates |
| **Build Validation** | ✅ Always | ✅ Always |
| **Auto-Push** | ✅ Yes | ✅ Yes |
| **Duration (3 repos)** | 3-5 min | 1-2 min |
| **User Interaction** | 3 approvals | 0 approvals |
| **Recommended For** | All users (default) | Power users, CI/CD |
| **Safety Level** | High | High (validation) |

## Detailed Comparison

### Safe Mode (Default)

```
🔒 SAFE MODE - Permission gates required before each major operation

START
  ↓
Input Validation (auto)
  ↓
Repository Setup
  → 🤔 User approval required
  ↓ (if approved)
  ✓ Clone repo
  ↓
Test Generation
  → 🤔 User approval required
  ↓ (if approved)
  ✓ Create tests
  ↓
Build Validation
  → 🤔 User approval required
  ↓ (if approved)
  ✓ Run Maven build
  ↓
Auto-Push
  ✓ Push to remote (no approval)
  ↓
END
```

**Timeline**: 3-5 minutes (with user thinking time)

**User Interaction**:
- Gate 1: "Approve cloning aem-core?" → Approve/Deny
- Gate 2: "Approve test generation?" → Approve/Deny
- Gate 3: "Approve build validation?" → Approve/Deny

### Trusted Mode (Opt-In)

```
🔓 TRUSTED MODE ENABLED - Skipping all permission gates

START
  ↓
Input Validation (auto)
  ↓
Repository Setup
  ✓ Auto-approved
  ✓ Clone repo
  ↓
Test Generation
  ✓ Auto-approved
  ✓ Create tests
  ↓
Build Validation
  ✓ Auto-approved
  ✓ Run Maven build
  ↓
Auto-Push
  ✓ Push to remote
  ↓
END
```

**Timeline**: 1-2 minutes (fully automated)

**User Interaction**: None (fully automated)

## Side-by-Side Execution Example

### Safe Mode Output
```
Processing 1 repository(ies)
🔒 SAFE MODE - Permission gates required before each major operation

[Repository Setup]
Requesting permission to clone/setup: aem-core

? User approval required...
→ aem-core (approved)
✓ Cloned to project-unit-test cases/repo/aem-core

[Test Generation]
Requesting permission to generate tests for: aem-core

? User approval required...
→ aem-core (approved)
✓ Created 3 test files

[Local Build Validation]
Requesting permission to validate build locally for: aem-core

? User approval required...
→ aem-core (approved)
✓ mvn clean test -pl core -am: PASSED

[Auto-Push]
Auto-pushing aem-core - no permission needed
✓ Pushed feature/ai-unit-test-cases

Completed: 1 pushed, 0 failed, 0 skipped
```

### Trusted Mode Output
```
Processing 1 repository(ies)
🔓 TRUSTED MODE ENABLED - Skipping all permission gates

[Repository Setup]
  → Auto-approved: setup for aem-core
✓ Cloned to project-unit-test cases/repo/aem-core

[Test Generation]
  → Auto-approved: generation for aem-core
✓ Created 3 test files

[Local Build Validation]
  → Auto-approved: validation for aem-core
✓ mvn clean test -pl core -am: PASSED

[Auto-Push]
Auto-pushing aem-core - no permission needed
✓ Pushed feature/ai-unit-test-cases

Completed: 1 pushed, 0 failed, 0 skipped
```

## Decision Matrix

### Use Safe Mode If:

✅ First time using this workflow
✅ Testing unfamiliar repositories
✅ Want to review process step-by-step
✅ Part of learning/onboarding
✅ Multiple approvers needed
✅ No time pressure
✅ Default choice (no parameter needed)

### Use Trusted Mode If:

✅ Familiar with workflow (used 5+ times)
✅ Running in CI/CD pipeline
✅ Testing known, trusted repos
✅ Batch operations (10+ repos)
✅ Single operator in controlled environment
✅ Time-sensitive operations
✅ Power user who reviewed code

## Execution Time Comparison

### Safe Mode: 3 Repositories

```
Repo 1: Clone (30s) + Gen (45s) + Validate (90s) + Approve (60s) = 225s
Repo 2: Clone (30s) + Gen (45s) + Validate (90s) + Approve (60s) = 225s
Repo 3: Clone (30s) + Gen (45s) + Validate (90s) + Approve (60s) = 225s

Total: ~11 minutes (parallel processing)
+ User approval time: ~3-5 minutes (thinking between gates)
= 14-16 minutes total
```

### Trusted Mode: 3 Repositories

```
Repo 1: Clone (30s) + Gen (45s) + Validate (90s) = 165s
Repo 2: Clone (30s) + Gen (45s) + Validate (90s) = 165s
Repo 3: Clone (30s) + Gen (45s) + Validate (90s) = 165s

Total: ~11 minutes (parallel processing)
+ User approval time: 0 seconds
= 11 minutes total
```

**Time Savings**: 3-5 minutes per batch (25-35% faster)

## Use Cases

### Case 1: First-Time User
**Scenario**: John is using this workflow for the first time
**Mode**: Safe Mode (default)
**Reason**: 
- Wants to understand what's happening
- First repo should be familiar
- Build validation will educate on test quality
**Workflow**: Safe Mode → Approve 3 gates → Success

### Case 2: Regular Developer
**Scenario**: Jane uses this monthly for routine testing
**Mode**: Safe Mode (mostly, occasional Trusted for rush)
**Reason**:
- Knows the workflow well
- Quick approvals become automatic
- Maintains oversight
**Workflow**: Safe Mode → Quick approvals → Success

### Case 3: CI/CD Pipeline
**Scenario**: Nightly job tests 20 AEM modules
**Mode**: Trusted Mode
**Reason**:
- Automated, no human interaction needed
- Builds must pass validation anyway
- Speed important for overnight runs
**Workflow**: Trusted Mode → Full auto → Success or build failure

### Case 4: Batch Testing
**Scenario**: Release manager testing 15 repos before release
**Mode**: Trusted Mode
**Reason**:
- Time critical (pre-release)
- All repos already reviewed
- Same person manages entire operation
**Workflow**: Trusted Mode → All 15 repos → Success

## Security Comparison

### Safe Mode Security

✅ **Approval Gates**: User explicitly approves each major operation
✅ **Prevents Surprise Changes**: User sees what will happen
✅ **Perfect for Review**: Others can observe what's being tested
✅ **Audit Trail**: Three deliberate approval points
❌ **Slower**: Requires user interaction

### Trusted Mode Security

✅ **Build Validation**: Always runs, catches bad code
✅ **Feature Branches**: Never touches main/develop
✅ **Audit Trail**: Result shows mode used + auto-approvals
✅ **Fast**: Fully automated
❌ **Fewer Checkpoints**: Less manual oversight
⚠️ **Operator Responsibility**: Trusts the person running it

### Both Modes Guarantee

✅ Build validation always runs
✅ Failed tests prevent push
✅ Only feature branches touched
✅ No credential handling
✅ Consistent repo location
✅ Clear result logging

## Migration Guide

### Safe Mode → Trusted Mode

When you're ready to upgrade:

1. **Understand the workflow**
   - Use Safe Mode several times
   - Read the documentation
   - Understand what each stage does

2. **Start with single repo**
   ```bash
   /aem-unit-test-cases --args '{
     "trustedMode": true,
     "testCases": [{single-repo}]
   }'
   ```

3. **Review the results**
   - Confirm mode was used correctly
   - Verify all repos pushed successfully
   - Check build validation results

4. **Expand to batch operations**
   ```bash
   /aem-unit-test-cases --args '{
     "trustedMode": true,
     "testCases": [{multiple-repos}]
   }'
   ```

5. **Document your decision**
   - If using Trusted Mode in CI/CD, add comments
   - Explain why Trusted Mode is appropriate
   - Link to this documentation

### Trusted Mode → Safe Mode (Reverting)

If you want to go back:

Simply remove `trustedMode: true` parameter:

```bash
# This reverts to Safe Mode
/aem-unit-test-cases --args '{"testCases": [...]}'
```

## Results Output Difference

### Safe Mode Result
```javascript
{
  mode: "safe",
  successful: 3,
  failed: 0,
  skipped: 0,
  optimizations: {
    permissionGates: "Before setup, generation, validation"
  }
}
```

### Trusted Mode Result
```javascript
{
  mode: "trusted",
  successful: 3,
  failed: 0,
  skipped: 0,
  optimizations: {
    permissionGates: "DISABLED (trusted mode)"
  }
}
```

Both show which mode was used for auditing.

## FAQ

**Q: Which mode is safer?**
A: Both are safe due to build validation. Safe Mode has more oversight; Trusted Mode is faster.

**Q: Can I switch modes mid-batch?**
A: No, the mode applies to entire workflow run.

**Q: Will Trusted Mode push bad code?**
A: No, build validation prevents it.

**Q: Should my team use Trusted Mode?**
A: Start with Safe Mode. Use Trusted Mode only in appropriate contexts (CI/CD, power users).

**Q: Is there a GUI to switch modes?**
A: No, it's a parameter: `trustedMode: true`

**Q: Can I use Trusted Mode in production?**
A: Yes, but only in properly controlled environments with appropriate access.

**Q: What if build fails in Trusted Mode?**
A: Push is blocked, same as Safe Mode. No bad code goes to remote.

**Q: How do I know which mode was used?**
A: Check result object's `mode` field and logs showing "TRUSTED MODE" or "SAFE MODE".

---

**Remember**: Default is Safe Mode. Trusted Mode is opt-in. Both keep your code safe through build validation.
