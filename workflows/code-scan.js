export const meta = {
  name: 'code-scan',
  description: 'Clones/updates a repo, detects its tech stack, and dispatches only the applicable security-first static-analysis agents',
  phases: [
    { title: 'Input Validation', detail: 'Validate repoUrl/branch and enforce repo location' },
    { title: 'Repository Setup', detail: 'Clone/update + deterministic stack detection (permission gate)' },
    { title: 'Code Analysis', detail: 'Dispatch only the detected-stack analyzers, in parallel (permission gate)' },
  ],
}

// This is the headless/batch counterpart to the interactive `code-scan`
// skill (skills/code-scan/SKILL.md). Use the skill when a human is present
// to answer "which repo / which branch" conversationally; use this workflow
// when repoUrl/branch are already known (CI, scheduled runs, scripted
// multi-repo sweeps). Pass them via args — this script does not prompt.
//
// export const meta` phases intentionally omit a separate "Stack Detection"
// phase: it's folded into Repository Setup because both steps run inside
// the same zero-reasoning `code-scan-orchestrator` agent call (one Bash
// script for cloning, one for detection) — splitting them into two agent()
// calls would double the tool-call overhead for no benefit.

phase('Input Validation')

const AI_AGENT_REPO = args?.aiAgentRepo || '/Users/kevaljoshi/Documents/ai-agent'
const baseDir = args?.baseDir || `${AI_AGENT_REPO}/repos`
const trustedMode = args?.trustedMode === true

const targets = Array.isArray(args?.repos)
  ? args.repos
  : (args?.repoUrl ? [{ repoUrl: args.repoUrl, branch: args.branch }] : [])

if (!targets.length || targets.some(t => !t.repoUrl || !t.branch)) {
  throw new Error(
    "No valid scan targets. Pass: { repoUrl: 'https://github.com/org/repo.git', branch: 'main' } " +
    "or { repos: [{repoUrl, branch}, ...] }. For an interactive URL/branch prompt, use the " +
    "'code-scan' skill instead of this workflow.",
  )
}

log(`Scanning ${targets.length} repo(s)`)
log(`Repository location: ${baseDir}`)
log(trustedMode ? '🔓 TRUSTED MODE — permission gates skipped' : '🔒 SAFE MODE — permission gates before clone and before analysis')

const requestPermission = async (operationName, details, repoName) => {
  if (trustedMode) {
    log(`  → Auto-approved: ${operationName} for ${repoName}`)
    return { approved: true, trusted: true }
  }
  return await agent(
    `Ask user to confirm ${operationName}:\n${details}\n\nConfirm before proceeding.`,
    {
      label: `perm:${operationName}:${repoName}`,
      phase: 'Repository Setup',
      model: 'haiku',
      schema: {
        type: 'object',
        properties: { approved: { type: 'boolean' }, reason: { type: 'string' } },
        required: ['approved'],
      },
    },
  )
}

const ROUTING_SCHEMA = {
  type: 'object',
  properties: {
    ready: { type: 'boolean' },
    error: { type: 'string' },
    repoName: { type: 'string' },
    repoPath: { type: 'string' },
    branch: { type: 'string' },
    commit: { type: 'string' },
    analyzers: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          agent: { type: 'string' },
          fileCount: { type: 'number' },
          evidence: { type: 'array', items: { type: 'string' } },
        },
        required: ['agent'],
      },
    },
  },
  required: ['ready'],
}

const ANALYSIS_SCHEMA = {
  type: 'object',
  properties: {
    filesReviewed: { type: 'number' },
    totalIssues: { type: 'number' },
    critical: { type: 'number' },
    high: { type: 'number' },
    medium: { type: 'number' },
    low: { type: 'number' },
    info: { type: 'number' },
    topRisk: { type: 'string' },
    reportPath: { type: 'string' },
    trackerPath: { type: 'string' },
  },
  required: ['totalIssues', 'reportPath', 'trackerPath'],
}

const results = await pipeline(
  targets,

  // Stage 1: clone/update + deterministic stack detection (one cheap agent call)
  async (target) => {
    phase('Repository Setup')
    const { repoUrl, branch } = target
    const repoName = repoUrl.split('/').pop().replace(/\.git$/, '')

    const setupPermission = await requestPermission(
      'repository setup',
      `Repo: ${repoName}\nURL: ${repoUrl}\nBranch: ${branch}\nLocation: ${baseDir}/${repoName}`,
      repoName,
    )
    if (!setupPermission?.approved) {
      return { repoUrl, repoName, status: 'skipped', reason: trustedMode ? 'Denied in trusted mode' : 'User did not approve repository setup' }
    }

    const routing = await agent(
      `Set up and route this repo for code-scan.\nrepoUrl: ${repoUrl}\nbranch: ${branch}\nbaseDir: ${baseDir}\nai-agent-repo: ${AI_AGENT_REPO}`,
      { label: `setup:${repoName}`, phase: 'Repository Setup', agentType: 'code-scan-orchestrator', schema: ROUTING_SCHEMA },
    )

    if (!routing?.ready) {
      return { repoUrl, repoName, status: 'failed', reason: routing?.error || 'setup failed' }
    }

    log(`${repoName}: ${routing.analyzers?.length || 0} analyzer(s) detected — ${(routing.analyzers || []).map(a => a.agent).join(', ') || 'none'}`)

    return { repoUrl, repoName, status: 'ready', ...routing }
  },

  // Stage 2: dispatch only the detected analyzers, in parallel
  async (setupResult) => {
    phase('Code Analysis')
    if (setupResult?.status !== 'ready') return setupResult

    const { repoName, repoPath, analyzers } = setupResult
    if (!analyzers || analyzers.length === 0) {
      log(`${repoName}: no applicable stack detected — nothing to analyze`)
      return { ...setupResult, status: 'skipped', reason: 'no stack detected' }
    }

    const analysisPermission = await requestPermission(
      'code analysis',
      `Repo: ${repoName}\nAnalyzers: ${analyzers.map(a => a.agent).join(', ')}\nPath: ${repoPath}`,
      repoName,
    )
    if (!analysisPermission?.approved) {
      return { ...setupResult, status: 'skipped', reason: trustedMode ? 'Denied in trusted mode' : 'User did not approve analysis' }
    }

    const analysisResults = await parallel(
      analyzers.map(a => () =>
        agent(
          `Review the ${a.agent} domain in this repo.\n` +
          `repoPath: ${repoPath}\n` +
          `evidence: ${JSON.stringify(a.evidence || [])}\n` +
          `ai-agent-repo: ${AI_AGENT_REPO}\n\n` +
          `Follow your own workflow exactly: discover → read line-by-line → cross-file pass → ` +
          `write ./analysis/ report + findings JSON + xlsx tracker (via scripts/build_issues_xlsx.py) → ` +
          `return the structured summary.`,
          { label: `analyze:${a.agent}:${repoName}`, phase: 'Code Analysis', agentType: a.agent, schema: ANALYSIS_SCHEMA },
        ).then(r => ({ analyzer: a.agent, ...r })),
      ),
    )

    return { ...setupResult, status: 'success', analysisResults: analysisResults.filter(Boolean) }
  },
)

phase('Code Analysis')
const succeeded = results.filter(r => r?.status === 'success')
const skipped = results.filter(r => r?.status === 'skipped')
const failed = results.filter(r => r?.status === 'failed')

log(`Done: ${succeeded.length} scanned, ${skipped.length} skipped, ${failed.length} failed`)
for (const r of succeeded) {
  for (const a of r.analysisResults || []) {
    log(`  ${r.repoName} · ${a.analyzer}: ${a.totalIssues} issues → ${a.reportPath}`)
  }
}

return { totalRepos: targets.length, succeeded: succeeded.length, skipped: skipped.length, failed: failed.length, results }
