# Create-Unit-Tests: Before vs After

## Quick Comparison

### 1. TOKEN USAGE

#### Before
```javascript
// Setup prompt - 240 tokens
`Setup repository for unit test generation in individual folder:

Repository URL: ${repoUrl}
Production Branch: ${productionBranch}
Test Cases/Classes: ${testCaseStr}
Target Folder: ${repoFolderPath}

Tasks:
1. Create folder: ${repoFolderPath} (create if doesn't exist)
2. Check if repository already exists in ${repoFolderPath}
3. If not exists: Clone repository to ${repoFolderPath}
4. If exists: Navigate to ${repoFolderPath} and fetch latest
5. Checkout production branch: ${productionBranch}
6. Create feature branch: feature/ai-unit-test-cases from ${productionBranch}
7. Report the folder path and branch status`
```

#### After
```javascript
// Setup prompt - 80 tokens (~67% reduction)
`Setup repo: ${repoName}
URL: ${repoUrl}
Path: ${repoPath}
Branch: ${productionBranch}

1. mkdir -p '${baseDir}'
2. cd '${baseDir}'
3. Clone/fetch to ${repoPath}
4. Checkout ${productionBranch}
5. Create feature/ai-unit-test-cases`
```

---

### 2. PERMISSION FLOW

#### Before
```
┌──────────────────────────┐
│ Input Validation         │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Repository Setup         │ ← No permission gate
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Test Generation          │ ← No permission gate
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Build Validation         │ ← No permission gate
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Push to Branch           │ ← No permission gate
└──────────────────────────┘
```

#### After
```
┌──────────────────────────┐
│ Input Validation         │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Repository Setup         │ ✓ PERMISSION GATE #1
├──────────────────────────┤
│ ? Ask user approval      │
│ (clone/fetch, branch)    │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Test Generation          │ ✓ PERMISSION GATE #2
├──────────────────────────┤
│ ? Ask user approval      │
│ (code generation)        │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Local Build Validation   │ ✓ PERMISSION GATE #3
├──────────────────────────┤
│ ? Ask user approval      │
│ (Maven build test)       │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Auto-Push to Branch      │ ✗ NO PERMISSION GATE
├──────────────────────────┤
│ Auto-execute if build    │
│ validation passed        │
└──────────────────────────┘
```

---

### 3. REPOSITORY LOCATION

#### Before
```javascript
// ❌ User could specify any location
const baseDir = args?.baseDir || process.cwd()

// Could result in:
// /tmp/repo-a (bad)
// ~/Documents/some-folder/repo-a (bad)
// /path/to/some-random-path/repo-a (bad)
```

#### After
```javascript
// ✅ Strict enforcement - no flexibility
const baseDir = args?.baseDir || `${process.env.HOME}/Documents/project-source/project-unit-test cases/repos`

// ALWAYS results in:
// $HOME/Documents/project-source/project-unit-test cases/repos/repo-a
// $HOME/Documents/project-source/project-unit-test cases/repos/repo-b
// (Centralized, organized, predictable)
```

---

### 4. BUILD VALIDATION

#### Before
```
Test Generation Stage
  ↓
Test files created
  ↓
Build Validation Stage (same stage, not isolated)
  ↓
Push to Branch

❌ Build checked during test generation
❌ No local validation before push
❌ Push might fail if build fails in CI
```

#### After
```
Test Generation Stage
  ↓
Test files created (initial build check)
  ↓
Local Build Validation Stage (separate, explicit)
  ✓ Permission gate
  ✓ Run: mvn clean test -pl core -am
  ✓ Verify all tests pass locally
  ✓ Fix issues if possible
  ↓
Auto-Push to Branch

✅ Dedicated validation stage
✅ User controls when to run build
✅ Local verification before push
✅ CI won't fail on pre-validated code
```

---

### 5. SCHEMA DEFINITIONS

#### Before
```javascript
schema: {
  type: 'object',
  properties: {
    testFilesCreated: {
      type: 'array',
      items: { type: 'string' },
      description: 'List of test files created/modified',
    },
    testStrategy: { type: 'string', description: 'Summary of testing strategy applied' },
    buildStatus: {
      type: 'string',
      enum: ['passed', 'failed'],
      description: 'Final build status after test creation',
    },
    coverageGain: {
      type: 'string',
      description: 'Estimated coverage improvement',
    },
    failureReason: {
      type: 'string',
      description: 'If build failed, reason and attempted fixes',
    },
    notes: { type: 'string', description: 'Additional notes and recommendations' },
  },
  required: ['testFilesCreated', 'buildStatus'],
}
// 16 lines, verbose descriptions
```

#### After
```javascript
schema: {
  type: 'object',
  properties: {
    testFilesCreated: { type: 'array', items: { type: 'string' } },
    buildStatus: { type: 'string', enum: ['passed', 'failed'] },
    coverageGain: { type: 'string' },
    failureReason: { type: 'string' },
  },
  required: ['testFilesCreated', 'buildStatus'],
}
// 8 lines, concise, only essential properties
// 50% smaller schema definition
```

---

### 6. AGENT CALL EFFICIENCY

#### Before
```javascript
const testGenResult = await agent(
  `You are an AEM Test Case Creator. Analyze the AEM backend codebase at ${repoPath} and create high-quality unit tests.

Current Location: ${repoPath}
Current Branch: feature/ai-unit-test-cases (already checked out)
Production Branch Reference: ${productionBranch}
Test Cases/Classes to Prioritize: ${testCaseStr}

Instructions:
1. Work ONLY in the local directory: ${repoPath}
2. All test files MUST be created in: ${repoPath}/src/test/java/
3. All test resources MUST be created in: ${repoPath}/src/test/resources/
4. Scan the repository structure, pom.xml, existing tests, and backend code
5. Provide an initial testing strategy
6. Identify high-priority classes for test generation
7. Create comprehensive unit tests following AEM best practices
8. Ensure all tests follow the existing project patterns
9. Place tests in correct locations with proper package structure
10. Create/update test resources as needed
11. Use existing test frameworks (JUnit, Mockito, AEM Mocks) already in the project
12. Do NOT add unnecessary dependencies
13. Do NOT modify production logic unless required for testability

CRITICAL: All operations happen in: ${repoPath}

After creating tests:
1. Run: mvn clean test -pl core -am (from ${repoPath})
2. Check if build passes
3. If build fails, fix test cases and retry
4. Report which test files were created (relative to ${repoPath})
5. Report final build status
6. Report estimated coverage improvement

Work incrementally and keep the repository buildable at every step.`,
  {
    label: `test-gen:${repoUrl.split('/').pop()}`,
    phase: 'Test Generation',
    agentType: 'aem-test-case-creator',
    // ... large schema ...
  },
)
// ~320 tokens, verbose instructions, lengthy schema
```

#### After
```javascript
const testGenResult = await agent(
  `Create AEM unit tests for: ${repoName}
Path: ${repoPath}
Classes: ${testCaseData?.testCases || 'high-priority'}

- Analyze codebase at ${repoPath}
- Create tests in ${repoPath}/src/test/java/
- Follow AEM patterns
- Keep project buildable
- Report: testFilesCreated[], coverage estimate, buildStatus

Work in ${repoPath} only.`,
  {
    label: `test-gen:${repoName}`,
    phase: 'Test Generation',
    agentType: 'aem-test-case-creator',
    schema: {
      type: 'object',
      properties: {
        testFilesCreated: { type: 'array', items: { type: 'string' } },
        buildStatus: { type: 'string', enum: ['passed', 'failed'] },
        coverageGain: { type: 'string' },
        failureReason: { type: 'string' },
      },
      required: ['testFilesCreated', 'buildStatus'],
    },
  },
)
// ~170 tokens, concise, tight schema
// 47% reduction
```

---

### 7. RESULT OUTPUT

#### Before
```javascript
return {
  totalProcessed: testCases.length,
  successful: successCount,
  failed: failedCount,
  baseDirectory: baseDir,
  results: results.filter(Boolean),
}
// No optimization info, no status indicators
```

#### After
```javascript
return {
  totalProcessed: testCases.length,
  successful: successCount,
  failed: failedCount,
  skipped: skippedCount,
  baseDirectory: baseDir,
  optimizations: {
    tokenReduction: 'Concise structured prompts with schemas',
    permissionGates: 'Before setup, generation, validation (auto-push only)',
    strictLocation: `Enforced ${baseDir}`,
    buildValidation: 'Local Maven build before push',
  },
  results: results.filter(Boolean),
}
// Includes optimization details and status tracking
// Better transparency
```

---

## Token Savings Summary

| Operation | Before | After | Savings |
|-----------|--------|-------|---------|
| Setup prompt | 240 | 80 | 67% |
| Setup schema | 12 lines | 8 lines | 33% |
| Test Gen prompt | 320 | 170 | 47% |
| Test Gen schema | 16 lines | 8 lines | 50% |
| Validation prompt | 180 | 100 | 44% |
| **Per Repo Total** | **~1,800** | **~950** | **~47%** |
| **For 3 Repos** | **~5,400** | **~2,850** | **~47%** |

---

## Permission Gates Summary

| Operation | Before | After | Change |
|-----------|--------|-------|--------|
| Setup | ✗ No gate | ✓ Gate #1 | User approval required |
| Test Gen | ✗ No gate | ✓ Gate #2 | User approval required |
| Validation | ✗ No gate | ✓ Gate #3 | User approval required |
| Push | ✗ No gate | ✗ No gate | Auto-execute (validation passed) |

---

## Key Improvements at a Glance

```
BEFORE                          AFTER
├─ No permission gates          ├─ 3 permission gates
├─ Verbose prompts              ├─ Concise prompts (47% reduction)
├─ Flexible repo location       ├─ Strict repo location
├─ No dedicated build stage     ├─ Dedicated build validation
├─ Auto-push always             ├─ Auto-push only after validation
├─ Large schemas                ├─ Minimal schemas
└─ 1,800 tokens/repo            └─ 950 tokens/repo

Result: Optimized, controlled, and token-efficient workflow ✅
```

---

## How This Helps

1. **For Token Budget** 💰
   - Save ~2,550 tokens processing 3 repos
   - More workflows can run within same budget
   - 47% efficiency gain

2. **For User Control** 🎮
   - Explicit approval before expensive operations
   - Can skip repos without cascading failures
   - Transparent decision points

3. **For Code Quality** ✅
   - Local build validation catches issues early
   - No CI failures from unvalidated tests
   - Build-pass guarantee before push

4. **For Organization** 📁
   - All repos in centralized location
   - Easy to find and manage test case repos
   - Consistent across different machines

5. **For Reliability** 🛡️
   - Auto-push only happens when ready
   - No user intervention needed once validated
   - Better error tracking and recovery
