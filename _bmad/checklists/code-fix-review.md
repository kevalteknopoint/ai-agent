# Code Fix Review Checklist

## Purpose

Quality gate for every fix applied by a fixer agent. Each fix must pass ALL applicable checks before being committed.

## Fix Quality Criteria

### Correctness
- [ ] Fix resolves the EXACT finding described (not a similar-looking issue)
- [ ] Fix does not introduce new issues of equal or higher severity
- [ ] Fix preserves existing functionality (no behavioral regression)
- [ ] Fix compiles/parses without errors
- [ ] Fix does not break existing tests

### Minimality
- [ ] Change is the smallest possible to resolve the finding
- [ ] No "while I'm here" refactoring included
- [ ] No unrelated formatting changes
- [ ] No new abstractions for a single-use fix
- [ ] Method signatures unchanged unless fix requires it

### Security (for security fixes)
- [ ] Fix follows OWASP remediation guidance
- [ ] Fix does not introduce a different vulnerability class
- [ ] Input validation is at the correct boundary (not too deep, not too shallow)
- [ ] No secrets or credentials in the fix
- [ ] Fix handles edge cases (empty input, max-length, unicode)

### Idiomatic Code
- [ ] Fix matches the project's existing code style
- [ ] Fix uses project's existing patterns (not introducing foreign idioms)
- [ ] Fix respects naming conventions already in use
- [ ] Fix uses framework features correctly (not fighting the framework)

### Dependencies
- [ ] No new dependencies added without explicit justification
- [ ] If dependency added: no known CVEs, actively maintained, license compatible
- [ ] Fix does not conflict with other fixes in the same batch
- [ ] Fix considers downstream callers of modified code

### Documentation
- [ ] Fix is self-explanatory (no comment needed for obvious changes)
- [ ] If complex: brief inline comment explaining WHY (not WHAT)
- [ ] Fix log entry captures the before/after delta

## Fix Validation Steps

### Pre-Apply
1. Read the finding's `currentCode` and `recommendedFix` fields
2. Read ±50 lines of surrounding context in the target file
3. Identify all callers/dependents of the code being changed
4. Confirm the recommendedFix is appropriate for THIS codebase (not generic)

### Post-Apply
1. Syntax validation (compile/parse check)
2. Verify the finding's pattern no longer appears at the location
3. Grep for the same anti-pattern elsewhere in the file (don't create inconsistency)
4. If tests exist: run them

## Severity-Specific Gates

### Critical (Sev 5) Fixes
- [ ] Fix addresses the root cause, not a symptom
- [ ] Fix covers all code paths (not just the reported line)
- [ ] No bypass possible (attacker cannot circumvent the fix)

### High (Sev 4) Fixes
- [ ] Fix handles edge cases properly
- [ ] Performance impact acceptable (fix doesn't trade correctness for speed)

### Medium (Sev 3) Fixes
- [ ] Fix improves the code measurably (not just different)
- [ ] Architectural consistency maintained

### Low/Info (Sev 1–2) Fixes
- [ ] Fix is clearly an improvement, not a style preference
- [ ] Won't conflict with planned refactoring

## Rollback Criteria

A fix MUST be rolled back if:
- Compilation/parse fails after applying
- Existing tests break
- The fix introduces a higher-severity issue
- The fix changes observable behavior in an untested path
- The rescan shows the finding is still Open after the fix
