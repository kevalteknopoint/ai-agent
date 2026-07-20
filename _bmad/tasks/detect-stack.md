# Task: Detect Tech Stack

## Purpose

Deterministically identify which technology stacks are present in a cloned repository.

## Command

```bash
bash {ai_agent_repo}/scripts/detect_stack.sh '{repoPath}'
```

## Inputs

| Parameter | Required |
|---|---|
| repoPath | yes (from clone-repo task output) |

## Output (JSON)

```json
{
  "javaSpringBoot": { "detected": true, "evidence": ["pom.xml", "src/main/java/..."] },
  "aemHtl": { "detected": true, "evidence": ["ui.apps/.../components/**/*.html"] },
  "edsBlocks": { "detected": false },
  "jsReact": { "detected": true, "evidence": ["package.json (react dep)"] },
  "cssScss": { "detected": true, "evidence": ["src/styles/**/*.scss"] }
}
```

## Detection Signals

| Stack | Primary Signal |
|---|---|
| Java/Spring Boot | `src/main/java` + `pom.xml`/`build.gradle` |
| AEM HTL | `jcr_root/apps/**/*.html` with HTL syntax |
| EDS Blocks | `blocks/` + `scripts/aem.js` |
| JS/React | `package.json` with `react` dependency |
| CSS/SCSS | `.css`/`.scss` files outside EDS `blocks/` |

## Notes

- Detection is deterministic (shell script, zero LLM tokens)
- Evidence lists are used to scope analyzer file sets
- Multiple stacks can coexist in one repo
