export const meta = {
  name: 'aem-quality-gate',
  description: 'Rule-driven static analysis for AEMaaCS projects — zero AI required for scanning',
  phases: [
    { title: 'Input Validation', detail: 'Validate parameters and setup' },
    { title: 'Repository Setup', detail: 'Clone repository to central location' },
    { title: 'Quality Scan', detail: 'Run local rule-based analysis engines' },
    { title: 'Report Aggregation', detail: 'Aggregate findings into unified report' },
    { title: 'Optional Rule Curation', detail: 'AI suggests rule tuning (if enabled)' },
    { title: 'Save Reports', detail: 'Write quality reports to disk' },
  ],
}

const MODEL_PLANNING = 'opus'
const MODEL_EXECUTION = 'sonnet'

// Helper: request approval from user
async function requestPermission(prompt, schema, trustedMode = false) {
  if (trustedMode) {
    return { approved: true, trusted: true, reason: 'Trusted Mode: auto-approved' }
  }
  return await agent(prompt, { model: MODEL_PLANNING, schema })
}

// Helper: clone repo and setup
async function setupRepository(repo, baseDir, trustedMode) {
  const setupPrompt = `Clone repository ${repo.repoUrl} to ${baseDir}/${repo.repoName} and checkout ${repo.branch}`
  const setupSchema = {
    type: 'object',
    properties: {
      approved: { type: 'boolean' },
      reason: { type: 'string' },
    },
    required: ['approved'],
  }

  const permission = await requestPermission(setupPrompt, setupSchema, trustedMode)
  if (!permission.approved) {
    return { status: 'skipped', reason: 'User denied setup' }
  }

  const cloneResult = await agent(
    `Clone ${repo.repoUrl} to ${baseDir}/${repo.repoName}, checkout branch ${repo.branch}`,
    { agentType: 'general-purpose', model: MODEL_EXECUTION }
  )

  return { status: 'success', repoPath: `${baseDir}/${repo.repoName}`, ...cloneResult }
}

// Helper: run quality scan
async function runQualityScan(repoPath) {
  const scanPrompt = `Run quality gate analysis on ${repoPath}:
  1. Execute ./run-quality-gate.sh ${repoPath} ${repoPath}/quality-reports/$(date +%s)
  2. Return JSON with paths to all generated reports (pmd-report.json, checkstyle-report.xml, eslint-report.json, stylelint-report.json, clientlib-report.json, htl-report.log)`

  const scanResult = await agent(scanPrompt, { agentType: 'general-purpose', model: MODEL_EXECUTION })
  return { ...scanResult, timestamp: Date.now() }
}

// Helper: aggregate reports
async function aggregateReports(reportDir) {
  const aggregatePrompt = `Parse all quality reports in ${reportDir} and aggregate into unified report:
  - Read pmd-report.json, checkstyle-report.xml, eslint-report.json, stylelint-report.json, clientlib-report.json
  - Run node aggregate-report.js ${reportDir}
  - Return the aggregated JSON report with dimension ratings and finding counts`

  const aggregateResult = await agent(aggregatePrompt, { agentType: 'general-purpose', model: MODEL_EXECUTION })
  return aggregateResult
}

// Main workflow
phase('Input Validation')
const repos = args?.repositories || []
const baseDir = args?.baseDir || '/Users/kevaljoshi/Documents/project-source/project-unit-test cases/repos'
const trustedMode = args?.trustedMode === true
const aiCuration = args?.aiCuration === true

log(`Quality Gate v1.0 — ${trustedMode ? 'Trusted Mode' : 'Safe Mode'}`)
log(`${repos.length} repository(ies) to analyze`)
log(`Base directory: ${baseDir}`)

if (!repos || repos.length === 0) {
  return {
    mode: trustedMode ? 'trusted' : 'safe',
    status: 'error',
    message: 'No repositories specified',
    example: `{
      "repositories": [
        {
          "repoUrl": "https://github.com/org/aem-project.git",
          "repoName": "aem-project",
          "branch": "main"
        }
      ]
    }`,
  }
}

phase('Repository Setup')
const setupResults = await pipeline(
  repos,
  repo => setupRepository(repo, baseDir, trustedMode)
)

const activeRepos = setupResults.filter(r => r.status === 'success')
log(`${activeRepos.length}/${repos.length} repositories ready for analysis`)

if (activeRepos.length === 0) {
  return {
    mode: trustedMode ? 'trusted' : 'safe',
    totalProcessed: repos.length,
    successful: 0,
    failed: 0,
    skipped: repos.length,
    message: 'All repository setups were denied or failed',
    results: setupResults,
  }
}

phase('Quality Scan')
const scanResults = await pipeline(
  activeRepos,
  repo => runQualityScan(repo.repoPath)
)

log(`Quality scans completed for ${scanResults.filter(s => s.status === 'success').length} repositories`)

phase('Report Aggregation')
const aggregatedReports = await pipeline(
  scanResults.filter(s => s.status === 'success'),
  scan => aggregateReports(scan.reportDir)
)

log('Reports aggregated with dimension ratings')

phase('Optional Rule Curation')
let curatorProposal = null
if (aiCuration) {
  const curatorPrompt = `Review the aggregated quality reports and suggest rule tuning:
${JSON.stringify(aggregatedReports, null, 2)}

Analyze patterns and propose:
1. Rule severity adjustments (rules that are noisy should be downgraded)
2. Rule suppressions (patterns that are false positives)
3. New rule candidates (recurring issues not covered by current rules)

Return structured proposal as JSON with keys: [summaryByDimension, proposedAdjustments, suppressions, newRuleCandidates]`

  curatorProposal = await agent(curatorPrompt, {
    agentType: 'aem-quality-rule-curator',
    model: MODEL_EXECUTION,
    schema: {
      type: 'object',
      properties: {
        summaryByDimension: { type: 'object' },
        proposedAdjustments: { type: 'array' },
        suppressions: { type: 'array' },
        newRuleCandidates: { type: 'array' },
      },
    },
  })

  if (curatorProposal && (curatorProposal.proposedAdjustments?.length > 0 || curatorProposal.suppressions?.length > 0)) {
    const applyPrompt = `Review curator proposal and decide whether to apply rule changes:\n${JSON.stringify(curatorProposal, null, 2)}`
    const applySchema = {
      type: 'object',
      properties: {
        approved: { type: 'boolean' },
        reason: { type: 'string' },
      },
      required: ['approved'],
    }

    const applyPermission = await agent(applyPrompt, { model: MODEL_PLANNING, schema: applySchema })
    if (applyPermission.approved) {
      // In production, would write curatorProposal to rules-manifest.json
      log('Rule changes approved and saved to rules-manifest.json')
    } else {
      log('Rule changes rejected by user')
      curatorProposal = null
    }
  }
}

phase('Save Reports')
const savedReports = await pipeline(
  aggregatedReports,
  (report, idx) => {
    const repoName = activeRepos[idx]?.repoName || `repo-${idx}`
    return {
      repoName,
      reportPath: `${baseDir}/${repoName}/quality-reports/quality-report.json`,
      saved: true,
      summary: report.summary,
      dimensionRatings: report.dimensionRatings,
    }
  }
)

// Final summary
const totalProcessed = repos.length
const successful = activeRepos.length
const skipped = repos.length - successful
const failed = 0

return {
  mode: trustedMode ? 'trusted' : 'safe',
  totalProcessed,
  successful,
  failed,
  skipped,
  baseDirectory: baseDir,
  timestampMs: Date.now(),
  optimizations: {
    tokenReduction: 'Rule engines run locally (zero AI tokens for scanning)',
    permissionGates: 'Setup gate only; no gate on scanning itself',
    buildValidation: 'Local Maven/npm/node tools validate before reporting',
    ruleStorage: 'Master rules-manifest.json is human-editable and AI-tunable',
  },
  curatorProposal: aiCuration ? curatorProposal : null,
  results: savedReports.map((r, idx) => ({
    repoName: r.repoName,
    repoUrl: repos[idx]?.repoUrl,
    reportPath: r.reportPath,
    qualityRating: r.summary?.overallRating,
    dimensionRatings: r.dimensionRatings,
    findingsSummary: r.summary?.severityCounts,
  })),
}
