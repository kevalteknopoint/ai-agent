export const meta = {
  name: 'security-scan',
  description:
    'Zero-AI security scanning: clones a repo, runs semgrep + gitleaks + trivy + hadolint + checkov + nuclei, aggregates into unified report. No LLM tokens used in actual scanning.',
  phases: [
    { title: 'Input Validation', detail: 'Validate git URL / local path, branch, scan options' },
    { title: 'Tool Check', detail: 'Verify security tools are installed' },
    { title: 'Security Scan', detail: 'Run all applicable security scanners (zero AI tokens)' },
    { title: 'Report', detail: 'Display scan summary and report locations' },
  ],
}

// ─── Zero-AI Security Scanner ───
// All scanning is deterministic CLI tools. The only AI tokens spent are on
// this workflow's orchestration (parsing args, calling bash, printing results).
// The scan itself: semgrep, gitleaks, trivy, hadolint, checkov, nuclei.

phase('Input Validation')

const AI_AGENT_REPO = args?.aiAgentRepo || process.cwd()
const SCRIPTS = `${AI_AGENT_REPO}/scripts/security-scan`
const baseDir = args?.baseDir || `${AI_AGENT_REPO}/repos`

// Accept either a single target or a batch
const targets = Array.isArray(args?.repos)
  ? args.repos
  : args?.gitUrl
    ? [{ gitUrl: args.gitUrl, branch: args.branch, targetUrl: args.targetUrl }]
    : args?.path
      ? [{ path: args.path, targetUrl: args.targetUrl }]
      : []

if (!targets.length) {
  throw new Error(
    "No scan target. Pass: { gitUrl: 'https://...', branch: 'main' } or { path: '/local/dir' } " +
      "or { repos: [{gitUrl, branch}, ...] }. For interactive use, use the 'security-scan' skill.",
  )
}

const quick = args?.quick === true
const skipSast = args?.skipSast === true
const skipSecrets = args?.skipSecrets === true
const skipDeps = args?.skipDeps === true
const skipConfig = args?.skipConfig === true
const skipDast = args?.skipDast === true
const minSeverity = args?.minSeverity || 'info'

log(`Scanning ${targets.length} target(s)`)
if (quick) log('⚡ Quick mode — fast scans only')

// ─── Tool check ───
phase('Tool Check')

const toolCheck = await agent(
  `Run this command and report the output:\nbash ${SCRIPTS}/install_tools.sh --check-only`,
  { label: 'tool-check', model: 'sonnet' },
)

// ─── Scan each target ───
phase('Security Scan')

const results = []

for (const target of targets) {
  const name = target.gitUrl
    ? target.gitUrl.replace(/.*\//, '').replace('.git', '')
    : target.path?.split('/').pop() || 'unknown'

  // Build command
  let cmd = `bash ${SCRIPTS}/run_scan.sh`
  if (target.gitUrl) {
    cmd += ` --git-url '${target.gitUrl}' --branch '${target.branch}' --base-dir '${baseDir}'`
  } else if (target.path) {
    cmd += ` --path '${target.path}'`
  }
  if (target.targetUrl) cmd += ` --target-url '${target.targetUrl}'`
  if (quick) cmd += ' --quick'
  if (skipSast) cmd += ' --skip-sast'
  if (skipSecrets) cmd += ' --skip-secrets'
  if (skipDeps) cmd += ' --skip-deps'
  if (skipConfig) cmd += ' --skip-config'
  if (skipDast) cmd += ' --skip-dast'
  if (minSeverity !== 'info') cmd += ` --severity ${minSeverity}`

  log(`Scanning: ${name}`)

  const result = await agent(
    `Run this security scan command. Do NOT analyze code yourself — the script does everything.\n\n${cmd}\n\nAfter it completes, report the summary output (total findings, per-domain counts, duration).`,
    {
      label: `scan:${name}`,
      model: 'sonnet',
      schema: {
        type: 'object',
        properties: {
          repoName: { type: 'string' },
          totalFindings: { type: 'number' },
          duration: { type: 'number' },
          domains: {
            type: 'object',
            properties: {
              sast: { type: 'number' },
              secrets: { type: 'number' },
              dependencies: { type: 'number' },
              config: { type: 'number' },
              dast: { type: 'number' },
            },
          },
          outputDir: { type: 'string' },
          error: { type: 'string' },
        },
        required: ['repoName', 'totalFindings'],
      },
    },
  )

  results.push(result)
}

// ─── Report ───
phase('Report')

log('\n══════════════════════════════════════')
log('  Security Scan Summary')
log('══════════════════════════════════════')
for (const r of results) {
  if (r.error) {
    log(`  ✗ ${r.repoName}: ${r.error}`)
  } else {
    log(`  ${r.repoName}: ${r.totalFindings} finding(s)`)
    if (r.outputDir) log(`    Reports: ${r.outputDir}/`)
  }
}
log('══════════════════════════════════════')
log('Zero AI tokens used in scanning.')
