# AEM Development Automation Toolkit — Agents

This repository uses the BMAD Method structure for AI-agent orchestration.

## Quick Start

Invoke any skill by name. Run `bmad-help` for context-aware guidance.

## Available Skills

| Skill | Phase | Description |
|---|---|---|
| `bmad-help` | Core | Context-aware next-step guidance |
| `bmad-code-scan` | Analysis | Multi-agent code scan (clone → detect → review) |
| `bmad-security-scan` | Analysis | Zero-AI security scan (semgrep/gitleaks/trivy) |
| `bmad-perf-test` | Analysis | k6 performance/load testing |
| `bmad-quality-gate` | Planning | Rule-driven AEM quality enforcement |
| `bmad-tech-arch` | Planning | Multi-repo architecture documentation |
| `bmad-wp-to-eds` | Solutioning | WordPress → EDS block migration |
| `bmad-vbrd-to-proofhub` | Solutioning | Visual BRD → ProofHub tasks |
| `bmad-unit-test-aem` | Implementation | AEM unit test generation |
| `bmad-unit-test-spring` | Implementation | Spring Boot unit test generation |

## Agent Personas

| Agent | Model | Triggers | Role |
|---|---|---|---|
| Code Scan Orchestrator | opus | CS, SCAN, ROUTE | Routes scans to correct analyzer |
| Code Scan Verifier | sonnet | RESCAN, VERIFY | Re-checks fixed findings |
| AEM HTL Analyzer | sonnet | HTL | Reviews HTL templates |
| Java/Spring Boot Analyzer | sonnet | JAVA, SB | Reviews backend code |
| JS/React Analyzer | sonnet | JS, REACT | Reviews frontend code |
| CSS/SCSS Analyzer | sonnet | CSS, SCSS | Reviews stylesheets |
| EDS Blocks Analyzer | sonnet | EDS, BLOCKS | Reviews EDS blocks |
| Security Scanner | sonnet | SEC, SAST, DAST | Dispatches security tools |
| Performance Tester | sonnet | PERF, LOAD, K6 | Dispatches k6 load tests |
| Architecture Documentarian | opus | ARCH, TAD | Multi-repo architecture docs |
| VBRD Translator | sonnet | VBRD, PH | Excel VBRD → ProofHub |
| WP-to-EDS Migrator | sonnet | WP, MIGRATE | WordPress → Edge Delivery |

## Structure

```
_bmad/
├── config/          # module.yaml + module-help.csv
├── agents/          # Persona files (identity, capabilities, constraints)
├── skills/          # SKILL.md per invokable workflow
├── tasks/           # Atomic reusable operations
└── checklists/      # Severity tables + check categories (loaded on-demand)
```

## Design Principles

1. **Token-efficient**: Checklists load only when an analyzer runs (not at routing time)
2. **Zero-AI where possible**: Clone, detect, scan tools are deterministic scripts
3. **Model split**: opus for planning/orchestration, sonnet for execution/review
4. **Parallel dispatch**: Independent analyzers run concurrently
5. **Idempotent**: Rescan uses same JSON/CSV — no duplicates
