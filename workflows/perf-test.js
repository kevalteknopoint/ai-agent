export const meta = {
  name: 'perf-test',
  description:
    'Zero-AI performance testing: generates k6 scripts, runs load/stress/soak/spike tests, analyzes results with SLA checks. No LLM tokens used in actual testing.',
  phases: [
    { title: 'Input Validation', detail: 'Validate target URL, test type, VUs, duration, endpoints' },
    { title: 'Tool Check', detail: 'Verify k6 is installed' },
    { title: 'Performance Test', detail: 'Generate k6 script → run test → analyze results (zero AI tokens)' },
    { title: 'Report', detail: 'Display test summary and SLA results' },
  ],
}

// ─── Zero-AI Performance Tester ───
// All load testing is k6 CLI. All analysis is Python scripts.
// The only AI tokens spent are on this workflow's orchestration.

phase('Input Validation')

const AI_AGENT_REPO = args?.aiAgentRepo || process.cwd()
const SCRIPTS = `${AI_AGENT_REPO}/scripts/perf-test`

// Accept either a config file or inline parameters
const targets = Array.isArray(args?.tests)
  ? args.tests
  : args?.url
    ? [args]
    : args?.config
      ? [{ config: args.config }]
      : []

if (!targets.length) {
  throw new Error(
    "No test target. Pass: { url: 'https://example.com', type: 'load', vus: 50, duration: '5m' } " +
      "or { config: '/path/to/config.json' } or { tests: [...] }. " +
      "For interactive use, use the 'perf-test' skill.",
  )
}

log(`Running ${targets.length} performance test(s)`)

// ─── Tool check ───
phase('Tool Check')

const toolCheck = await agent(
  `Run this command and report the output:\nbash ${SCRIPTS}/install_tools.sh --check-only`,
  { label: 'tool-check', model: 'sonnet' },
)

// ─── Run tests ───
phase('Performance Test')

const results = []

for (const target of targets) {
  const name = target.url || target.config || 'unknown'

  // Build command
  let cmd = `bash ${SCRIPTS}/run_test.sh`
  if (target.config) {
    cmd += ` --config '${target.config}'`
  } else {
    cmd += ` --url '${target.url}'`
    if (target.type) cmd += ` --type '${target.type}'`
    if (target.vus) cmd += ` --vus ${target.vus}`
    if (target.duration) cmd += ` --duration '${target.duration}'`
    if (target.thresholdP95) cmd += ` --threshold-p95 ${target.thresholdP95}`
    if (target.thresholdP99) cmd += ` --threshold-p99 ${target.thresholdP99}`
    if (target.thresholdError) cmd += ` --threshold-error ${target.thresholdError}`
    if (target.baseline) cmd += ` --baseline '${target.baseline}'`
    if (target.rampUp) cmd += ` --ramp-up '${target.rampUp}'`
    if (target.outputDir) cmd += ` --output-dir '${target.outputDir}'`

    // Endpoints
    const endpoints = target.endpoints || []
    for (const ep of endpoints) {
      if (typeof ep === 'string') {
        cmd += ` --endpoint '${ep}'`
      } else {
        cmd += ` --endpoint '${ep.method || 'GET'} ${ep.path} ${ep.name || ep.path}'`
      }
    }

    // Headers
    const headers = target.headers || {}
    for (const [k, v] of Object.entries(headers)) {
      cmd += ` --header '${k}: ${v}'`
    }
  }

  log(`Testing: ${name}`)

  const result = await agent(
    `Run this performance test command. The script handles everything — do NOT generate tests yourself.\n\n${cmd}\n\nAfter it completes, report: overall PASS/FAIL, p95 response time, throughput, error rate, and output directory.`,
    {
      label: `perf:${name}`,
      model: 'sonnet',
      schema: {
        type: 'object',
        properties: {
          target: { type: 'string' },
          testType: { type: 'string' },
          result: { enum: ['PASS', 'FAIL'] },
          p95: { type: 'number' },
          throughput: { type: 'number' },
          errorRate: { type: 'number' },
          outputDir: { type: 'string' },
          error: { type: 'string' },
        },
        required: ['target', 'result'],
      },
    },
  )

  results.push(result)
}

// ─── Report ───
phase('Report')

log('\n══════════════════════════════════════')
log('  Performance Test Summary')
log('══════════════════════════════════════')
for (const r of results) {
  if (r.error) {
    log(`  ✗ ${r.target}: ${r.error}`)
  } else {
    const icon = r.result === 'PASS' ? '✓' : '✗'
    log(`  ${icon} ${r.target}: ${r.result}`)
    if (r.p95) log(`    p95: ${r.p95}ms | RPS: ${r.throughput} | Errors: ${r.errorRate}%`)
    if (r.outputDir) log(`    Reports: ${r.outputDir}/`)
  }
}
log('══════════════════════════════════════')
log('Zero AI tokens used in testing.')
