# bmad-unit-test-aem

AEM unit test case generation for Sling Models, servlets, and OSGi components.

## When to Use

- "Generate unit tests for this AEM project"
- "Write tests for Sling Models"
- "Create JUnit tests for AEM components"

## Steps

1. Clone/update repo (task: `_bmad/tasks/clone-repo.md`)
2. Detect AEM project structure (core bundle, Sling Models, servlets)
3. Analyze existing test coverage
4. Generate JUnit 5 + Mockito + AEM Mocks tests
5. Write tests to feature branch

## Test Patterns

- Sling Model unit tests (resource-based + request-based adaptation)
- Servlet tests (doGet/doPost with mock SlingHttpServletRequest)
- OSGi service tests (component lifecycle, config injection)
- WCMUsePojo tests (deprecated pattern — flag for migration)

## Output

Tests written to `src/test/java/` mirroring source package structure.

## Reference

See `docs/AEM-UNIT-TEST-CASES-BEFORE-AFTER.md` for examples.
