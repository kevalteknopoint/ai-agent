# Token Optimization Conventions

## Purpose

Shared rules to minimize token consumption across all agents without sacrificing output quality.
Every agent in the toolkit MUST follow these conventions.

## Model Assignment Policy

| Role | Model | Rationale |
|---|---|---|
| Orchestration / routing / planning | opus | Needs reasoning for dispatch decisions |
| Code reading / review / fixing | sonnet | Fast execution, sufficient for pattern matching |
| Report writing / documentation | sonnet | Structured output, no deep reasoning needed |

**Rule:** An agent's model is set ONCE in module.yaml. Agent markdown files declare it for documentation only.

## Context Window Rules

### 1. Lazy Loading (Load Only What You Need)
- Checklists are loaded BY the assigned agent, NOT pre-loaded by the orchestrator
- Only load files that are in-scope — never read an entire repo "to be safe"
- Use `grep`/`glob` to narrow targets before `read` — never brute-force read all files

### 2. Streaming Reads (Bounded Context)
- Read files in chunks of ±50 lines around the target, not full files (unless <100 lines)
- For cross-file analysis, read only the relevant interface/export lines
- Stop reading once you have enough evidence for a verdict

### 3. Output Compression
- Findings JSON uses terse field names (already standardized in build_issues_csv.py)
- Reports use Markdown tables (dense) over prose paragraphs
- Never repeat the problem statement in both `problem` and `impact` fields
- `currentCode` field: max 5 lines (the minimum to identify the pattern)
- `recommendedFix` field: max 10 lines (the minimum to show the correct pattern)
- `optimizedExample`: only include if materially different from recommendedFix

### 4. Chat Suppression
- All agents output to FILES only — zero findings printed in chat
- Final confirmation is max 5 lines (analyzers) or 3 lines (fixers/verifiers)
- Orchestrators return structured JSON, never prose explanations

### 5. Batch Size Tuning
- Default batch: 8 issues per agent dispatch (balances context vs round-trips)
- Dense files (>500 lines with multiple issues): batch size 5
- Shallow findings (naming, magic numbers): batch size 12
- The orchestrator adjusts batch size based on average issue complexity

### 6. Deduplication
- If multiple findings in the same file share the same root cause, merge them into one issue with multiple `affectedLines`
- Cross-file duplicates (same pattern in copy-pasted code): report once, list all occurrences in `relatedFiles` array

### 7. Skip Conditions (Zero-Token Paths)
- If a domain has zero detected files → skip entirely (don't load the agent)
- If all findings in a domain are already Fixed → skip fix dispatch
- If a file was deleted since the scan → mark NotApplicable without reading

## Orchestrator-Specific Optimizations

### code-scan-orchestrator
- Runs `detect_stack.sh` (deterministic, zero-LLM) before any agent dispatch
- Only loads routing plan — never reads application code itself
- Parallelizes independent domain agents (Java + CSS can run simultaneously)

### code-fix-orchestrator
- Runs `build_fix_plan.py` (deterministic, zero-LLM) for planning
- Only dispatches agents for domains with open issues
- Groups same-file issues to reduce context re-reads
- Runs `collect_fix_results.py` (deterministic) for report generation

## Per-Agent Token Budgets

| Agent Type | Max Input Context | Max Output |
|---|---|---|
| Orchestrator | 4K tokens (plan/route only) | 1K tokens (JSON plan) |
| Analyzer (per file) | 8K tokens (file + checklist) | 2K tokens (findings for that file) |
| Fixer (per batch) | 12K tokens (issues + context) | 2K tokens (fix results JSON) |
| Verifier (per batch) | 8K tokens (issues + current code) | 1K tokens (verdict JSON) |

## Cost Estimation Formula

```
estimated_cost = (
  orchestrator_calls × opus_rate +
  (files_in_scope × avg_file_tokens × sonnet_rate) +
  (batches × batch_context × sonnet_rate)
)
```

Use this to estimate before starting a large scan/fix operation.
