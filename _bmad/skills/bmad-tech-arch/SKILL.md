# bmad-tech-arch

Multi-repository architecture discovery and technical documentation.

## When to Use

- "Create a technical architecture document"
- "Document the client's architecture from the repos"
- "Generate architecture diagrams from source code"
- "Reverse-engineer the system integration architecture"

## Agent

Load `_bmad/agents/tech-architecture-doc.md`

## Steps

1. **Intake** — ask for repos (2-8 typical), client name, depth
2. **Clone** — run task `_bmad/tasks/clone-repo.md` for each repo
3. **Detect** — run task `_bmad/tasks/detect-stack.md` per repo
4. **Analyze** — build evidence register, trace cross-repo integrations
5. **Document** — write Technical Architecture Document with diagrams
6. **Deliver** — output to `{ai_agent_repo}/output/tech-architecture/{client-slug}/`

## Depth Options

| Depth | Scope |
|---|---|
| `full` | Complete architecture document |
| `integration` | Cross-system integration only |
| `security` | Trust boundaries and data flow |
| `refresh` | Update existing doc against newer branches |

## Deliverables

- `evidence-register.csv`
- C4 context + container diagrams (Mermaid)
- Component diagrams per major subsystem
- System integration architecture
- Deployment topology
- Security/trust-boundary diagrams
- Database ER diagrams
- API inventory
- Risk register + target-state proposal
