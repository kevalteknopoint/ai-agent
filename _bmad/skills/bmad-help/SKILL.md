# bmad-help

Context-aware guidance for the AEM Development Automation Toolkit.

## When to Use

- "What should I do next?"
- "What tools are available?"
- "How do I scan a repo?"
- "What's the difference between full scan and rescan?"
- Any time you're unsure what skill/agent to invoke

## How It Works

1. Reads `_bmad/config/module-help.csv` for available skills
2. Inspects project state (existing `analysis/`, `output/`, repos)
3. Recommends next step based on context

## Quick Reference

| Phase | Skills | When |
|---|---|---|
| **1. Analysis** | `bmad-code-scan`, `bmad-security-scan`, `bmad-perf-test` | Review code, find vulnerabilities, test performance |
| **2. Planning** | `bmad-quality-gate`, `bmad-tech-arch` | Enforce standards, document architecture |
| **3. Solutioning** | `bmad-wp-to-eds`, `bmad-vbrd-to-proofhub` | Migrate components, translate requirements |
| **4. Implementation** | `bmad-unit-test-aem`, `bmad-unit-test-spring` | Generate test cases |

## Agent Triggers (for direct invocation)

| Trigger | Agent | Use |
|---|---|---|
| CS / SCAN | Orchestrator | Route a code scan |
| HTL | HTL Analyzer | Review AEM templates |
| JAVA / SB | Java Analyzer | Review Spring Boot code |
| JS / REACT | JS Analyzer | Review React frontend |
| CSS / SCSS | CSS Analyzer | Review stylesheets |
| EDS / BLOCKS | EDS Analyzer | Review EDS blocks |
| SEC / SAST | Security Scanner | Run security tools |
| PERF / LOAD | Perf Tester | Run k6 load tests |
| ARCH / TAD | Architect | Document architecture |
| WP / MIGRATE | WP Migrator | WordPress → EDS |
| VBRD / PH | VBRD Translator | Excel → ProofHub |

## Common Flows

**First time scanning a repo:**
```
bmad-code-scan → provide URL + branch → auto-detects stack → runs analyzers
```

**Checking if fixes landed:**
```
bmad-code-scan → same repo → offers rescan → verifies findings → updates CSV
```

**Full security audit:**
```
bmad-code-scan (SAST via analyzers) + bmad-security-scan (tooling) + bmad-perf-test (load)
```
