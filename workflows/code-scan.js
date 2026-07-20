export const meta = {
  name: 'code-scan',
  description: 'Clones/updates a repo, detects its tech stack, and either runs the applicable security-first analyzers or — when a prior analysis/ folder exists — rescans its findings and writes fix status back to the same JSON/CSV',
  phases: [
    { title: 'Input Validation', detail: 'Validate repoUrl/branch/mode and enforce repo location' },
    { title: 'Repository Setup', detail: 'Clone/update + stack detection + prior-analysis check (permission gate)' },
    { title: 'Code Analysis', detail: 'Full scan: dispatch only the detected-stack analyzers, in parallel (permission gate)' },
    { title: 'Rescan Verification', detail: 'Rescan: re-verify prior findings against current code, batched per domain' },
    { title: 'Status Update', detail: 'Rescan: merge verdicts into the same findings JSON + CSV tracker, render summary' },
  ],
}

// This is the headless/batch counterpart to the interactive `code-scan`
// skill (skills/code-scan/SKILL.md). Use the skill when a human is present
// to answer "which repo / which branch" conversationally; use this workflow
// when repoUrl/branch are already known (CI, scheduled runs, scripted
// multi-repo sweeps). Pass them via args — this script does not prompt.
//
// `export const meta` phases intentionally omit a separate "Stack Detection"
// phase: it's folded into Repository Setup because those steps run inside
// the same zero-reasoning `code-scan-orchestrator` agent call (one Bash
// script for cloning, one for detection, one for the prior-analysis check) —
// splitting them into separate agent() calls would double the tool-call
// overhead for no benefit.
//
// Two mutually exclusive paths run after setup:
//
//   full scan  — no analysis/ folder yet. Dispatch the detected analyzers;
//                they discover issues and write the report + findings JSON +
//                CSV tracker. Expensive: every in-scope file gets read.
//   rescan     — analysis/ already there. Do NOT re-review the codebase.
//                Re-verify the findings already on record against current
//                code and write each one's status back into the same JSON and
//                the same CSV. Cheap: only files carrying a known finding get
//                read. Finds no new issues — that's the trade, and it's the
//                point.
//
// `mode: 'auto'` (the default) picks between them from what's on disk.

phase('Input Validation')

const AI_AGENT_REPO = args?.aiAgentRepo || process.cwd()
const baseDir = args?.baseDir || `${AI_AGENT_REPO}/repos`
const trustedMode = args?.trustedMode === true
const MODEL_PLANNING = 'opus'
const MODEL_EXECUTION = 'sonnet'

const VALID_MODES = ['auto', 'full', 'rescan']
const mode = (args?.mode || 'auto').toLowerCase()
if (!VALID_MODES.includes(mode)) {
  throw new Error(`Invalid mode '${args?.mode}'. Use one of: ${VALID_MODES.join(', ')}.`)
}

// Issues already marked Fixed/Not Applicable are skipped by default — re-reading
// a deleted file every run is cost with no signal. Pass recheckFixed to hunt for
// regressions instead.
const recheckFixed = args?.recheckFixed === true
const batchSize = Number(args?.batchSize) > 0 ? Math.floor(Number(args.batchSize)) : 12

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
log(
  mode === 'auto' ? '🔁 AUTO MODE — rescan if analysis/ exists, else full scan'
    : mode === 'rescan' ? '🔁 RESCAN MODE — re-verify prior findings only, no new-issue discovery'
      : '🔎 FULL MODE — full analysis, ignoring any prior analysis/ folder',
)
if (mode !== 'full' && recheckFixed) log('   ↳ recheckFixed: also re-verifying issues already marked Fixed/Not Applicable')
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
      model: MODEL_PLANNING,
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
    priorAnalysis: {
      type: 'object',
      properties: {
        present: { type: 'boolean' },
        planPath: { type: 'string' },
        domains: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              domain: { type: 'string' },
              findingsPath: { type: 'string' },
              csvPath: { type: 'string' },
              totalIssues: { type: 'number' },
              toVerify: { type: 'number' },
              skippedFixed: { type: 'number' },
              duplicateIds: { type: 'array', items: { type: 'string' } },
              unidentified: { type: 'number' },
              batchIds: { type: 'array', items: { type: 'string' } },
            },
            required: ['domain', 'batchIds'],
          },
        },
        // A findings file that wouldn't parse drops its whole domain. Carried
        // through the schema so it can be logged — a domain silently missing
        // from a rescan reads as "nothing to fix there".
        errors: {
          type: 'array',
          items: {
            type: 'object',
            properties: { domain: { type: 'string' }, error: { type: 'string' } },
          },
        },
      },
      required: ['present'],
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

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    batchId: { type: 'string' },
    verdictPath: { type: 'string' },
    verified: { type: 'number' },
    fixed: { type: 'number' },
    open: { type: 'number' },
    partiallyFixed: { type: 'number' },
    notApplicable: { type: 'number' },
    unverifiable: { type: 'number' },
  },
  required: ['verified'],
}

const COUNTS_SCHEMA = {
  type: 'object',
  properties: {
    Open: { type: 'number' },
    Fixed: { type: 'number' },
    'Partially Fixed': { type: 'number' },
    'Not Applicable': { type: 'number' },
    Unverifiable: { type: 'number' },
  },
}

const MERGE_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'string' },
    csv: { type: 'string' },
    commit: { type: 'string' },
    total: { type: 'number' },
    verified: { type: 'number' },
    counts: COUNTS_SCHEMA,
    newlyFixed: { type: 'array', items: { type: 'string' } },
    regressed: { type: 'array', items: { type: 'string' } },
    notVerified: { type: 'array', items: { type: 'string' } },
    duplicateIds: { type: 'array', items: { type: 'string' } },
    unknownVerdictIds: { type: 'array', items: { type: 'string' } },
    badVerdictFiles: {
      type: 'array',
      items: {
        type: 'object',
        properties: { file: { type: 'string' }, error: { type: 'string' } },
      },
    },
  },
  required: ['total'],
}

const RESCAN_SUMMARY_SCHEMA = {
  type: 'object',
  properties: {
    written: { type: 'string' },
    total: { type: 'number' },
    resolved: { type: 'number' },
    stillOpen: { type: 'number' },
    fixRate: { type: 'number' },
    newlyFixed: { type: 'number' },
    regressed: { type: 'number' },
  },
  required: ['written'],
}

// Which path a repo takes, decided from what setup actually found on disk.
// Returns { path: 'full' | 'rescan' | 'none', reason }.
const resolvePath = (setupResult) => {
  const prior = setupResult.priorAnalysis
  const present = prior?.present === true
  const domains = (prior?.domains || []).filter(d => (d.batchIds || []).length > 0)
  const toVerify = domains.reduce((sum, d) => sum + (d.toVerify || 0), 0)

  if (mode === 'full') return { path: 'full' }

  if (mode === 'rescan') {
    // An explicit rescan request with nothing to rescan does NOT silently
    // become a full scan — that would spend an analysis-sized budget the
    // caller never asked for.
    if (!present) {
      return { path: 'none', reason: 'rescan requested but no analysis/ folder found — run mode:"full" first to establish a baseline' }
    }
    if (!toVerify) {
      return {
        path: 'none',
        reason: prior.domains?.length
          ? 'rescan requested but every prior finding is already Fixed/Not Applicable — pass recheckFixed:true to re-check them for regressions'
          : 'rescan requested but the prior analysis contains no issues',
      }
    }
    return { path: 'rescan' }
  }

  // auto
  if (!present) return { path: 'full', reason: 'no prior analysis — establishing a baseline' }
  if (!toVerify) return { path: 'full', reason: 'prior analysis has nothing left to verify — running a full scan to look for new issues' }
  return { path: 'rescan', reason: `found prior analysis (${toVerify} issue(s) to verify)` }
}

const results = await pipeline(
  targets,

  // Stage 1: clone/update + stack detection + prior-analysis check (one cheap agent call)
  async (target) => {
    phase('Repository Setup')
    const { repoUrl, branch } = target
    const repoName = repoUrl.split('/').pop().replace(/\.git$/, '')

    const setupPermission = await requestPermission(
      'repository setup',
      `Repo: ${repoName}\nURL: ${repoUrl}\nBranch: ${branch}\nLocation: ${baseDir}/${repoName}\nMode: ${mode}`,
      repoName,
    )
    if (!setupPermission?.approved) {
      return { repoUrl, repoName, status: 'skipped', reason: trustedMode ? 'Denied in trusted mode' : 'User did not approve repository setup' }
    }

    const routing = await agent(
      `Set up and route this repo for code-scan.\n` +
      `repoUrl: ${repoUrl}\nbranch: ${branch}\nbaseDir: ${baseDir}\nai-agent-repo: ${AI_AGENT_REPO}\n` +
      `mode: ${mode}\n` +
      (mode === 'full'
        ? `Skip the prior-analysis check (step 4) — this run is a forced full scan.`
        : `For the prior-analysis check, run plan_verification.py with ` +
          `--batch-size ${batchSize}${recheckFixed ? ' --recheck-fixed' : ''}.`),
      {
        label: `setup:${repoName}`,
        phase: 'Repository Setup',
        agentType: 'code-scan-orchestrator',
        model: MODEL_PLANNING,
        schema: ROUTING_SCHEMA,
      },
    )

    if (!routing?.ready) {
      return { repoUrl, repoName, status: 'failed', reason: routing?.error || 'setup failed' }
    }

    const decision = resolvePath(routing)
    log(`${repoName}: ${routing.analyzers?.length || 0} analyzer(s) detected — ${(routing.analyzers || []).map(a => a.agent).join(', ') || 'none'}`)
    log(`${repoName}: ${decision.path === 'none' ? 'nothing to do' : decision.path + ' scan'}${decision.reason ? ` — ${decision.reason}` : ''}`)

    return { repoUrl, repoName, status: 'ready', scanPath: decision.path, pathReason: decision.reason, ...routing }
  },

  // Stage 2: rescan the known findings, or run a full analysis — never both
  async (setupResult) => {
    if (setupResult?.status !== 'ready') return setupResult

    if (setupResult.scanPath === 'none') {
      return { ...setupResult, status: 'skipped', reason: setupResult.pathReason }
    }
    if (setupResult.scanPath === 'rescan') {
      return await runRescan(setupResult)
    }
    return await runFullScan(setupResult)
  },
)

// --- Rescan: re-verify prior findings, write status back to the same files ---
async function runRescan(setupResult) {
  phase('Rescan Verification')
  const { repoName, repoPath, priorAnalysis } = setupResult
  const domains = (priorAnalysis.domains || []).filter(d => (d.batchIds || []).length > 0)
  const totalToVerify = domains.reduce((sum, d) => sum + (d.toVerify || 0), 0)
  const totalSkipped = domains.reduce((sum, d) => sum + (d.skippedFixed || 0), 0)

  const rescanPermission = await requestPermission(
    'rescan verification',
    `Repo: ${repoName}\nDomains: ${domains.map(d => `${d.domain} (${d.toVerify ?? '?'} issue(s))`).join(', ')}\n` +
    `Issues to verify: ${totalToVerify} across ${domains.reduce((s, d) => s + d.batchIds.length, 0)} batch(es)\n` +
    `Writes status back to: ${domains.map(d => d.csvPath).join(', ')}\nPath: ${repoPath}`,
    repoName,
  )
  if (!rescanPermission?.approved) {
    return { ...setupResult, status: 'skipped', reason: trustedMode ? 'Denied in trusted mode' : 'User did not approve rescan verification' }
  }

  // Everything the plan left out gets said out loud. A rescan that verifies 38
  // of 42 findings and reports only the 38 reads as complete coverage.
  if (totalSkipped) {
    log(`${repoName}: skipping ${totalSkipped} issue(s) already marked Fixed/Not Applicable (pass recheckFixed:true to re-check them)`)
  }
  for (const d of domains) {
    if (d.duplicateIds?.length) {
      log(`${repoName} · ${d.domain}: ⚠️ ${d.duplicateIds.length} duplicate issue ID(s) excluded — a verdict can't be routed unambiguously: ${d.duplicateIds.join(', ')}`)
    }
    if (d.unidentified) {
      log(`${repoName} · ${d.domain}: ⚠️ ${d.unidentified} issue(s) with no ID excluded — cannot be verified`)
    }
  }
  for (const e of priorAnalysis.errors || []) {
    log(`${repoName}: ⚠️ domain '${e.domain}' skipped entirely — its findings file could not be read: ${e.error}`)
  }

  // Each domain verifies its batches in parallel, then merges as soon as its
  // own batches land — no cross-domain barrier, since each domain writes to a
  // different findings file. Merging is per-domain because apply_verdicts.py
  // needs every verdict for a domain before it can rewrite that domain's JSON.
  const perDomain = await parallel(domains.map(d => async () => {
    const verdicts = await parallel(d.batchIds.map(batchId => () =>
      agent(
        `Verify a batch of prior code-scan findings against the current code.\n` +
        `repoPath: ${repoPath}\n` +
        `planPath: ${priorAnalysis.planPath}\n` +
        `batchId: ${batchId}\n` +
        `domain: ${d.domain}\n\n` +
        `Follow your own workflow exactly: read the plan → pull your batch's issue records from ` +
        `${d.findingsPath} → re-read the current code (search for the pattern; do not trust the ` +
        `recorded line number) → write one verdict per issue ID to your batch's verdictPath → ` +
        `return the structured summary. Verify only your batch's IDs; do not look for new issues.`,
        {
          label: `verify:${batchId}:${repoName}`,
          phase: 'Rescan Verification',
          agentType: 'code-scan-verifier',
          model: MODEL_EXECUTION,
          schema: VERIFY_SCHEMA,
        },
      ).then(r => ({ batchId, ...r })),
    ))

    const landed = verdicts.filter(Boolean)
    if (landed.length < d.batchIds.length) {
      log(`${repoName} · ${d.domain}: ${d.batchIds.length - landed.length} of ${d.batchIds.length} batch(es) failed — their issues keep their previous status`)
    }

    // apply_verdicts.py owns the write: it merges verdicts into the findings
    // JSON and rebuilds the CSV from the same in-memory issue list, so the two
    // can't drift. A model rewriting a 300-row tracker by hand can.
    // The `[0-9]` matters: a bare `${domain}-b*` glob would let a domain named
    // as another's prefix cross-merge (`eds-b*` matches `eds-blocks-b1-...`).
    // No current domain pair collides; this keeps that true for the next one.
    const merged = await agent(
      `Merge the ${d.domain} rescan verdicts into its findings JSON and CSV tracker.\n\n` +
      `Run exactly this one command:\n` +
      `cd '${repoPath}' && python3 '${AI_AGENT_REPO}/scripts/apply_verdicts.py' ` +
      `'${d.findingsPath}' analysis/.verify/${d.domain}-b[0-9]*-verdicts.json ` +
      `--csv '${d.csvPath}' --mode rescan\n\n` +
      `Return the script's JSON output verbatim as your structured result. Do not edit ` +
      `${d.findingsPath} or ${d.csvPath} yourself — the script is the only writer. ` +
      `If the script reports badVerdictFiles, unknownVerdictIds or duplicateIds, include them; ` +
      `do not retry blindly.`,
      {
        label: `merge:${d.domain}:${repoName}`,
        phase: 'Status Update',
        model: MODEL_EXECUTION,
        effort: 'low',
        schema: MERGE_SCHEMA,
      },
    )

    return { domain: d.domain, batches: landed, merged }
  }))

  phase('Status Update')
  const domainResults = perDomain.filter(Boolean)

  const summary = await agent(
    `Render the cross-domain rescan summary for this repo.\n\n` +
    `Run exactly this one command:\n` +
    `cd '${repoPath}' && python3 '${AI_AGENT_REPO}/scripts/build_rescan_summary.py' '${repoPath}'\n\n` +
    `Return the script's JSON output verbatim as your structured result. Write nothing yourself.`,
    {
      label: `summary:${repoName}`,
      phase: 'Status Update',
      model: MODEL_EXECUTION,
      effort: 'low',
      schema: RESCAN_SUMMARY_SCHEMA,
    },
  )

  for (const r of domainResults) {
    const c = r.merged?.counts || {}
    log(
      `  ${repoName} · ${r.domain}: ${r.merged?.total ?? '?'} issue(s) — ` +
      `Fixed ${c.Fixed || 0} | Open ${c.Open || 0} | Partial ${c['Partially Fixed'] || 0} | ` +
      `N/A ${c['Not Applicable'] || 0} | Unverifiable ${c.Unverifiable || 0}` +
      `${r.merged?.regressed?.length ? ` | ⚠️ ${r.merged.regressed.length} regressed` : ''}`,
    )
    if (r.merged?.badVerdictFiles?.length) {
      log(`    ⚠️ ${r.merged.badVerdictFiles.length} unreadable verdict file(s) — those issues kept their previous status`)
    }
  }

  return { ...setupResult, status: 'success', scanPath: 'rescan', rescanResults: domainResults, rescanSummary: summary }
}

// --- Full scan: dispatch only the detected analyzers, in parallel ---
async function runFullScan(setupResult) {
  phase('Code Analysis')
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
        `write ./analysis/ report + findings JSON + csv tracker (via scripts/build_issues_csv.py) → ` +
        `return the structured summary.`,
        {
          label: `analyze:${a.agent}:${repoName}`,
          phase: 'Code Analysis',
          agentType: a.agent,
          model: MODEL_EXECUTION,
          schema: ANALYSIS_SCHEMA,
        },
      ).then(r => ({ analyzer: a.agent, ...r })),
    ),
  )

  return { ...setupResult, status: 'success', scanPath: 'full', analysisResults: analysisResults.filter(Boolean) }
}

phase('Status Update')
const succeeded = results.filter(r => r?.status === 'success')
const skipped = results.filter(r => r?.status === 'skipped')
const failed = results.filter(r => r?.status === 'failed')
const scanned = succeeded.filter(r => r.scanPath === 'full')
const rescanned = succeeded.filter(r => r.scanPath === 'rescan')

log(`Done: ${scanned.length} full-scanned, ${rescanned.length} rescanned, ${skipped.length} skipped, ${failed.length} failed`)
for (const r of scanned) {
  for (const a of r.analysisResults || []) {
    log(`  ${r.repoName} · ${a.analyzer}: ${a.totalIssues} issues → ${a.reportPath}`)
  }
}
for (const r of rescanned) {
  const s = r.rescanSummary
  log(`  ${r.repoName}: ${s?.resolved ?? '?'}/${s?.total ?? '?'} resolved (${s?.fixRate ?? '?'}%), ${s?.stillOpen ?? '?'} still open → ${s?.written || 'analysis/rescan-summary.md'}`)
}
for (const r of skipped) {
  log(`  ${r.repoName}: skipped — ${r.reason}`)
}

return {
  totalRepos: targets.length,
  mode,
  fullScanned: scanned.length,
  rescanned: rescanned.length,
  succeeded: succeeded.length,
  skipped: skipped.length,
  failed: failed.length,
  results,
}
