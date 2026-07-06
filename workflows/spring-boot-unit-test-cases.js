export const meta = {
  name: 'spring-boot-unit-test-cases',
  description: 'Orchestrates Spring Boot unit test case creation with optional trusted mode for power users',
  phases: [
    { title: 'Input Validation', detail: 'Validate test case inputs and enforce repo location' },
    { title: 'Repository Setup', detail: 'Clone/fetch repos (with optional permission gate)' },
    { title: 'Test Generation', detail: 'Generate unit tests (with optional permission gate)' },
    { title: 'Local Build Validation', detail: 'Build projects locally to verify tests' },
    { title: 'Push to Branch', detail: 'Auto-push without permission when build passes' },
  ],
}

// Main orchestration
phase('Input Validation')

const testCases = args?.testCases || []
const trustedMode = args?.trustedMode === true
// ENFORCE strict location: project-unit-test cases/repos
// Note: process.cwd() doesn't work in workflow sandbox, use hardcoded path or override via args.baseDir
const baseDir = args?.baseDir || '/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos'

if (!Array.isArray(testCases) || testCases.length === 0) {
  throw new Error('No test cases provided. Pass: [{repoUrl, productionBranch, testCases}, ...]')
}

log(`Processing ${testCases.length} Spring Boot repository(ies)`)
log(`Repository location: ${baseDir}`)
log(`Override with: args.baseDir = '/your/custom/path'`)
log(`Token optimization: Reduced prompt verbosity and enabled caching`)

if (trustedMode) {
  log(`🔓 TRUSTED MODE ENABLED - Skipping all permission gates`)
} else {
  log(`🔒 SAFE MODE - Permission gates required before each major operation`)
}

// Helper function to conditionally request permission based on mode
const requestPermission = async (operationName, operationDetails, repoName) => {
  if (trustedMode) {
    log(`  → Auto-approved: ${operationName} for ${repoName}`)
    return { approved: true, trusted: true }
  }

  return await agent(
    `Ask user to confirm ${operationName}:
${operationDetails}

Confirm before proceeding.`,
    {
      label: `perm:${operationName}:${repoName}`,
      phase: `${operationName} (Permission)`,
      schema: {
        type: 'object',
        properties: {
          approved: { type: 'boolean' },
          reason: { type: 'string' },
        },
        required: ['approved'],
      },
    },
  )
}

const results = await pipeline(
  testCases,

  // Stage 1: Repository Setup (with optional permission gate)
  async (testCase) => {
    phase('Repository Setup')

    const { repoUrl, productionBranch } = testCase
    const repoName = repoUrl.split('/').pop().replace(/\.git$/, '')
    const repoPath = `${baseDir}/${repoName}`

    // REQUEST PERMISSION before setup (unless trusted mode)
    const setupPermission = await requestPermission(
      'setup',
      `Repo: ${repoName}
URL: ${repoUrl}
Location: ${repoPath}
Branch: ${productionBranch}`,
      repoName,
    )

    if (!setupPermission?.approved) {
      return {
        repoUrl,
        repoName,
        repoPath,
        status: 'skipped',
        reason: trustedMode ? 'Denied in trusted mode' : 'User did not approve repository setup',
      }
    }

    // Setup repo (no permission needed after this point in this stage)
    const setupResult = await agent(
      `Setup repo: ${repoName}
URL: ${repoUrl}
Path: ${repoPath}
Branch: ${productionBranch}

1. mkdir -p '${baseDir}'
2. cd '${baseDir}'
3. Clone/fetch to ${repoPath}
4. Checkout ${productionBranch}
5. Create feature/ai-unit-test-cases

Return: {repoPath, featureBranch: 'feature/ai-unit-test-cases', ready: true/false}`,
      {
        label: `setup:${repoName}`,
        phase: 'Repository Setup',
        agentType: 'general-purpose',
        schema: {
          type: 'object',
          properties: {
            repoPath: { type: 'string' },
            featureBranch: { type: 'string' },
            ready: { type: 'boolean' },
            error: { type: 'string' },
          },
          required: ['ready'],
        },
      },
    )

    return {
      repoUrl,
      repoName,
      repoPath,
      ...setupResult,
    }
  },

  // Stage 2: Test Generation (with optional permission gate)
  async (repoSetup) => {
    phase('Test Generation')

    if (!repoSetup?.ready) {
      return {
        ...repoSetup,
        status: 'failed',
        reason: 'Repository not ready',
      }
    }

    const { repoPath, repoName, repoUrl } = repoSetup
    const testCaseData = testCases.find(tc => tc.repoUrl === repoUrl)

    // REQUEST PERMISSION before test generation (unless trusted mode)
    const genPermission = await requestPermission(
      'generation',
      `Repo: ${repoName}
Target: ${testCaseData?.testCases || 'all high-priority classes'}
Location: ${repoPath}`,
      repoName,
    )

    if (!genPermission?.approved) {
      return {
        ...repoSetup,
        status: 'skipped',
        reason: trustedMode ? 'Denied in trusted mode' : 'User did not approve test generation',
      }
    }

    // Generate tests
    const testGenResult = await agent(
      `Create Spring Boot unit tests for: ${repoName}
Path: ${repoPath}
Classes: ${testCaseData?.testCases || 'high-priority'}

- Analyze Spring Boot codebase at ${repoPath}
- Check pom.xml for test frameworks (JUnit, Mockito, TestRestTemplate)
- Create tests in ${repoPath}/src/test/java/
- Follow Spring Boot testing patterns and best practices
- Keep project buildable at every step
- Report: testFilesCreated[], coverage estimate, buildStatus

Work in ${repoPath} only.`,
      {
        label: `test-gen:${repoName}`,
        phase: 'Test Generation',
        agentType: 'spring-boot-test-creator',
        schema: {
          type: 'object',
          properties: {
            testFilesCreated: {
              type: 'array',
              items: { type: 'string' },
            },
            buildStatus: {
              type: 'string',
              enum: ['passed', 'failed'],
            },
            coverageGain: { type: 'string' },
            failureReason: { type: 'string' },
          },
          required: ['testFilesCreated', 'buildStatus'],
        },
      },
    )

    return {
      ...repoSetup,
      ...testGenResult,
      status: testGenResult?.buildStatus === 'passed' ? 'success' : 'failed',
    }
  },

  // Stage 3: Local Build Validation
  async (testGenResult) => {
    phase('Local Build Validation')

    if (!testGenResult?.testFilesCreated?.length) {
      return {
        ...testGenResult,
        buildValidated: false,
        reason: 'No test files created',
      }
    }

    // REQUEST PERMISSION before build validation (unless trusted mode)
    const validatePermission = await requestPermission(
      'validation',
      `Repo: ${testGenResult.repoName}
Location: ${testGenResult.repoPath}
Command: mvn clean test`,
      testGenResult.repoName,
    )

    if (!validatePermission?.approved) {
      return {
        ...testGenResult,
        buildValidated: false,
        reason: trustedMode ? 'Denied in trusted mode' : 'User did not approve build validation',
      }
    }

    // Validate build
    const buildValidation = await agent(
      `Validate Spring Boot build for: ${testGenResult.repoName}
Path: ${testGenResult.repoPath}

Run: mvn clean test
- Check all tests pass
- Report any failures
- Fix if possible
- Return: buildPasses: true/false, errors?: string[]

Work in ${testGenResult.repoPath} only.`,
      {
        label: `validate:${testGenResult.repoName}`,
        phase: 'Local Build Validation',
        agentType: 'general-purpose',
        schema: {
          type: 'object',
          properties: {
            buildPasses: { type: 'boolean' },
            errors: {
              type: 'array',
              items: { type: 'string' },
            },
            testsSummary: { type: 'string' },
          },
          required: ['buildPasses'],
        },
      },
    )

    return {
      ...testGenResult,
      buildValidated: buildValidation?.buildPasses === true,
      buildErrors: buildValidation?.errors || [],
      testsSummary: buildValidation?.testsSummary,
    }
  },

  // Stage 4: Auto-Push (NO permission gate - auto-push if validation passed)
  async (validationResult) => {
    phase('Push to Branch')

    if (!validationResult?.buildValidated) {
      return {
        ...validationResult,
        featureBranchPushed: false,
        reason: 'Build validation failed or skipped',
      }
    }

    // NO PERMISSION REQUEST - Auto-push when ready
    log(`Auto-pushing ${validationResult.repoName} - no permission needed`)

    const pushResult = await agent(
      `Auto-push tests for: ${validationResult.repoName}
Path: ${validationResult.repoPath}
Branch: feature/ai-unit-test-cases
Files: ${(validationResult.testFilesCreated || []).join(', ')}

1. cd ${validationResult.repoPath}
2. Verify on feature/ai-unit-test-cases
3. git add <test-files>
4. Commit: "feat: Add comprehensive Spring Boot unit tests"
5. git push origin feature/ai-unit-test-cases

Return: {pushed: boolean, error?: string}`,
      {
        label: `push:${validationResult.repoName}`,
        phase: 'Push to Branch',
        agentType: 'general-purpose',
        schema: {
          type: 'object',
          properties: {
            pushed: { type: 'boolean' },
            error: { type: 'string' },
          },
          required: ['pushed'],
        },
      },
    )

    return {
      ...validationResult,
      featureBranchPushed: pushResult?.pushed === true,
      pushError: pushResult?.error,
    }
  },
)

// Summarize results
phase('Summary')

const successCount = results.filter((r) => r?.featureBranchPushed === true)?.length || 0
const failedCount = results.filter((r) => r?.status === 'failed')?.length || 0
const skippedCount = results.filter((r) => r?.status === 'skipped')?.length || 0

const modeLabel = trustedMode ? '🔓 TRUSTED MODE' : '🔒 SAFE MODE'
log(`\nCompleted: ${successCount} pushed, ${failedCount} failed, ${skippedCount} skipped out of ${testCases.length} total`)
log(`\n${modeLabel} - Execution Summary:`)
log(`  - Token usage reduced: Concise prompts + structured schemas`)
log(`  - Permission gates: ${trustedMode ? 'SKIPPED (trusted mode)' : 'Requested before setup, generation, validation'}`)
log(`  - Auto-push: No permission needed after build validation passes`)
log(`  - Strict location: All repos cloned to ${baseDir}`)
log(`\nRepository locations:`)
results.filter(Boolean).forEach((result, index) => {
  if (result.repoPath) {
    const status = result.featureBranchPushed ? '✓ PUSHED' : result.status === 'skipped' ? '⊘ SKIPPED' : '✗ FAILED'
    log(`  ${index + 1}. [${status}] ${result.repoName || result.repoUrl} → ${result.repoPath}`)
  }
})

return {
  totalProcessed: testCases.length,
  successful: successCount,
  failed: failedCount,
  skipped: skippedCount,
  baseDirectory: baseDir,
  mode: trustedMode ? 'trusted' : 'safe',
  optimizations: {
    tokenReduction: 'Concise structured prompts with schemas',
    permissionGates: trustedMode ? 'DISABLED (trusted mode)' : 'Before setup, generation, validation',
    strictLocation: `Enforced ${baseDir}`,
    buildValidation: 'Local Maven build before push',
  },
  results: results.filter(Boolean),
}
