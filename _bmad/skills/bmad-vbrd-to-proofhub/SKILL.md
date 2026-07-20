# bmad-vbrd-to-proofhub

Visual BRD Excel workbook → ProofHub developer-ready tasks.

## When to Use

- "Convert a VBRD to ProofHub"
- "Turn a Visual BRD into tasks"
- "Create ProofHub tasks from the VBRD"
- Re-sync an updated VBRD

## Agent

Load `_bmad/agents/vbrd-to-proofhub.md`

## Steps

1. **Inspect** — read workbook, confirm ProofHub project exists
2. **Parse** — extract sheets → tasklists, component blocks → tasks
3. **Enrich** — user story + requirements + AC + tech implementation per component
4. **Dry-run** — show changeset summary (new/changed/unchanged)
5. **Confirm** — explicit go-ahead required before writing
6. **Sync** — create/update ProofHub tasks (idempotent on Component ID)
7. **Attach** — per-component screenshots + full workbook

## Sync Behavior

| Component Status | Action |
|---|---|
| New | CREATE task |
| Changed | UPDATE existing task |
| Unchanged | SKIP |
| Duplicate ID in sheet | Disambiguate with document order suffix |

## Environment Requirements

- `PROOFHUB_BASE_URL`
- `PROOFHUB_API_KEY`
- `PROOFHUB_USER_AGENT`
