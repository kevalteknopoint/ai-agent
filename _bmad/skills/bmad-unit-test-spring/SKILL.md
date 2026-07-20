# bmad-unit-test-spring

Spring Boot unit test case generation.

## When to Use

- "Generate unit tests for this Spring Boot project"
- "Write tests for controllers/services/repositories"
- "Create integration tests for Spring Boot"

## Steps

1. Clone/update repo (task: `_bmad/tasks/clone-repo.md`)
2. Detect Spring Boot structure (controllers, services, repositories, configs)
3. Analyze existing test coverage
4. Generate JUnit 5 + Mockito + SpringBootTest tests
5. Write tests to feature branch

## Test Patterns

- Controller tests (@WebMvcTest, MockMvc)
- Service tests (unit with mocked repos)
- Repository tests (@DataJpaTest)
- Integration tests (@SpringBootTest)
- Security config tests

## Output

Tests written to `src/test/java/` mirroring source package structure.

## Reference

See `docs/SPRING-BOOT-WORKFLOW-GUIDE.md` for patterns.
