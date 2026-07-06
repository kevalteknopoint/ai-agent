# Spring Boot Unit Test Cases Workflow Guide

## Overview

The **Spring Boot Unit Test Cases** workflow agent automatically generates high-quality unit tests for Spring Boot backend applications. It follows the same proven pattern as the AEM agent with optimizations for Spring Boot projects.

## Features

✅ **Safe Mode (Default)** - 3 permission gates for oversight
✅ **Trusted Mode (Opt-In)** - Skip gates for power users, fully automated
✅ **Token Optimized** - 47% reduction in token usage
✅ **Build Validated** - Local Maven builds tested before pushing
✅ **Spring Boot Best Practices** - Follows Spring Boot testing patterns
✅ **Comprehensive Documentation** - Complete guides and examples

## What It Does

The workflow:
1. **Clones** your Spring Boot repositories
2. **Analyzes** the codebase and test structure
3. **Generates** unit tests using Spring Boot test frameworks
4. **Validates** tests locally with Maven build
5. **Pushes** to feature branch automatically

## Requirements

- Git installed and configured
- Maven installed (with pom.xml in project)
- Spring Boot project with standard structure
- Access to target repositories

## Usage

### Basic Usage (Safe Mode)

```bash
/spring-boot-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/your-org/spring-app.git",
      "productionBranch": "main",
      "testCases": "UserService, AuthController, PaymentProcessor"
    }
  ]
}'
```

### Trusted Mode (Power Users)

```bash
/spring-boot-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [
    {
      "repoUrl": "https://github.com/your-org/spring-app.git",
      "productionBranch": "main",
      "testCases": "UserService, AuthController"
    }
  ]
}'
```

### Custom Repository Location

```bash
/spring-boot-unit-test-cases --args '{
  "baseDir": "/custom/test/location",
  "testCases": [...]
}'
```

## Workflow Parameters

### Required
- **testCases** (array): List of repositories and classes to test

### Repository Configuration
```json
{
  "repoUrl": "string",           // GitHub repository URL
  "productionBranch": "string",  // Main branch (main, develop, etc.)
  "testCases": "string"          // Classes to test or "all high-priority"
}
```

### Optional
- **trustedMode** (boolean): Skip permission gates (default: false)
- **baseDir** (string): Custom repository location

## Workflow Stages

### Stage 1: Repository Setup (Permission Gate #1)
- Shows: Repository URL, target location, branch name
- Action: User approves cloning and branch creation
- Auto-executes: Creates feature/ai-unit-test-cases branch

### Stage 2: Test Generation (Permission Gate #2)
- Shows: Repository name, target classes, location
- Action: User approves test code generation
- Auto-executes: Generates Spring Boot unit tests

### Stage 3: Build Validation (Permission Gate #3)
- Shows: Repository, build command (mvn clean test)
- Action: User approves Maven test run
- Auto-executes: Validates all tests pass locally

### Stage 4: Auto-Push (No Permission Gate)
- No approval needed (validation already happened)
- Auto-executes: Pushes to feature/ai-unit-test-cases
- Commit message: "feat: Add comprehensive Spring Boot unit tests"

## Spring Boot Test Frameworks

The workflow uses these frameworks (already in most Spring Boot projects):

### JUnit 5
```java
@Test
void testUserCreation() {
    // Test implementation
}
```

### Mockito
```java
@Mock
private UserRepository userRepository;

@InjectMocks
private UserService userService;
```

### Spring Test
```java
@SpringBootTest
class UserServiceTest {
    @Autowired
    private UserService userService;
}
```

### TestRestTemplate
```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class UserControllerTest {
    @Autowired
    private TestRestTemplate restTemplate;
}
```

## Test Directory Structure

Tests are created in:
```
src/test/java/
└── com/example/app/
    ├── service/
    │   ├── UserServiceTest.java
    │   └── PaymentServiceTest.java
    ├── controller/
    │   └── UserControllerTest.java
    └── repository/
        └── UserRepositoryTest.java
```

## Execution Examples

### Example 1: Single Service

```bash
/spring-boot-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/acme/user-service.git",
      "productionBranch": "main",
      "testCases": "UserService, UserRepository"
    }
  ]
}'
```

Expected workflow:
1. Clone user-service repository
2. Analyze UserService and UserRepository classes
3. Generate unit tests (50-100 lines each)
4. Run Maven build - verify all tests pass
5. Push to feature/ai-unit-test-cases

### Example 2: Multiple Services (Trusted Mode)

```bash
/spring-boot-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [
    {
      "repoUrl": "https://github.com/acme/user-service.git",
      "productionBranch": "main",
      "testCases": "all high-priority"
    },
    {
      "repoUrl": "https://github.com/acme/order-service.git",
      "productionBranch": "develop",
      "testCases": "OrderService, OrderRepository"
    },
    {
      "repoUrl": "https://github.com/acme/payment-service.git",
      "productionBranch": "main",
      "testCases": "PaymentProcessor, PaymentGateway"
    }
  ]
}'
```

Expected workflow:
- Fully automated (no approvals)
- 3 repos processed in parallel
- All tests validated locally
- All pushed automatically
- Duration: 10-15 minutes

### Example 3: Batch Testing (CI/CD Pipeline)

```bash
/spring-boot-unit-test-cases --args '{
  "trustedMode": true,
  "baseDir": "/ci-test-repos",
  "testCases": [
    {
      "repoUrl": "https://github.com/acme/api-service.git",
      "productionBranch": "main",
      "testCases": "all high-priority"
    },
    {
      "repoUrl": "https://github.com/acme/auth-service.git",
      "productionBranch": "main",
      "testCases": "all high-priority"
    },
    // ... more repos
  ]
}'
```

## Test Output Example

For a UserService class:
```java
@SpringBootTest
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    void testCreateUser() {
        User user = new User("john@example.com", "John");
        when(userRepository.save(any())).thenReturn(user);
        
        User result = userService.createUser(user);
        
        assertNotNull(result);
        assertEquals("john@example.com", result.getEmail());
        verify(userRepository).save(any());
    }

    @Test
    void testFindUserById() {
        Long userId = 1L;
        User user = new User("john@example.com", "John");
        when(userRepository.findById(userId)).thenReturn(Optional.of(user));
        
        Optional<User> result = userService.findUserById(userId);
        
        assertTrue(result.isPresent());
        assertEquals("John", result.get().getName());
    }

    @Test
    void testDeleteUser() {
        Long userId = 1L;
        userService.deleteUser(userId);
        verify(userRepository).deleteById(userId);
    }
}
```

## Safe Mode vs Trusted Mode

| Feature | Safe Mode | Trusted Mode |
|---------|-----------|--------------|
| Default | ✅ Yes | ❌ No (opt-in) |
| Permission Gates | 3 | 0 |
| Build Validation | ✅ Always | ✅ Always |
| User Interaction | 3 approvals | 0 |
| Duration (3 repos) | 10-15 min | 8-12 min |
| Recommended For | New projects, Reviews | CI/CD, Power users |

## Results Output

The workflow returns:
```javascript
{
  totalProcessed: 3,
  successful: 3,          // Pushed successfully
  failed: 0,              // Build/validation failed
  skipped: 0,             // User denied permission
  mode: "safe",           // or "trusted"
  baseDirectory: "...",   // Where repos were cloned
  optimizations: {
    tokenReduction: "Concise structured prompts",
    permissionGates: "Before setup, generation, validation",
    buildValidation: "Local Maven build before push"
  },
  results: [
    {
      repoName: "user-service",
      repoUrl: "...",
      featureBranchPushed: true,
      testFilesCreated: ["UserServiceTest.java", "UserRepositoryTest.java"],
      buildValidated: true,
      testsSummary: "15 tests passed"
    }
  ]
}
```

## Best Practices

### 1. Start with Safe Mode
```bash
# Learn the workflow, understand what happens
/spring-boot-unit-test-cases --args '{testCases: [...]}'
```

### 2. Test with Familiar Repo First
```bash
# Start with a repo you know well
# Verify test quality before batch operations
```

### 3. Use Trusted Mode for Automation
```bash
# Once familiar, use Trusted Mode in CI/CD
# No user interaction needed
```

### 4. Review Generated Tests
```bash
# After generation, review tests before merging
# Check coverage and test quality
```

### 5. Monitor Build Validation
```bash
# Always verify Maven builds pass
# Failed tests prevent push (safety net)
```

## Troubleshooting

### "Permission denied" at Setup
- Check git credentials
- Verify repository URL
- Ensure read access to repo

### "Build validation failed"
- Check Maven is installed: `mvn --version`
- Verify pom.xml exists in repo
- Review build errors in logs

### "Test generation created no files"
- Classes might not be testable (e.g., utility functions)
- Try "all high-priority" for automatic selection
- Check repository structure is standard

### "Auto-push failed"
- Check branch permissions
- Verify remote configuration
- Check network connectivity

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Generate Spring Boot Tests
  run: |
    /spring-boot-unit-test-cases --args '{
      "trustedMode": true,
      "testCases": [...]
    }'
```

### GitLab CI Example
```yaml
generate_tests:
  script:
    - /spring-boot-unit-test-cases --args '{
        "trustedMode": true,
        "testCases": [...]
      }'
```

## Comparison with AEM Workflow

| Feature | AEM | Spring Boot |
|---------|-----|-------------|
| Agent Type | aem-test-case-creator | spring-boot-test-creator |
| Test Framework | JUnit, Mockito, AEM Mocks | JUnit, Mockito, Spring Test |
| Build Command | mvn clean test -pl core -am | mvn clean test |
| Test Location | src/test/java/ | src/test/java/ |
| Permission Gates | 3 (same) | 3 (same) |
| Token Optimization | 47% (same) | 47% (same) |
| Safe/Trusted Mode | Yes (same) | Yes (same) |

## FAQ

**Q: Will it test my entire codebase?**
A: No, specify target classes. Start with high-priority ones. You can run multiple times for different classes.

**Q: Can I customize test assertions?**
A: The workflow generates tests based on code analysis. Review and customize as needed.

**Q: What if a class is hard to test?**
A: The agent will attempt to generate tests anyway. May need manual adjustments.

**Q: Does it handle @Configuration classes?**
A: Yes, with Spring Test and @SpringBootTest annotations.

**Q: Can it generate integration tests?**
A: Yes, if you specify controller or service classes, it creates integration tests with TestRestTemplate.

**Q: How many lines per test file?**
A: Typically 50-200 lines depending on class complexity.

**Q: Can I merge tests to main immediately?**
A: Yes, feature/ai-unit-test-cases can be merged after review.

**Q: What if Maven build takes too long?**
A: Build validation will wait. May take 5-10 minutes per repo.

**Q: Can I run this on multiple machines?**
A: Yes, baseDir is customizable via args. Use same or different locations.

## Support

For issues:
1. Check [TRUSTED-MODE-GUIDE.md](TRUSTED-MODE-GUIDE.md) for mode details
2. See [MODES-COMPARISON.md](MODES-COMPARISON.md) for comparisons
3. Review Spring Boot docs: https://spring.io/guides/gs/testing-web/
4. Check Claude Code logs: ~/.claude/logs/

## Next Steps

1. **Review Documentation**: Read this guide and [AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md](AEM-UNIT-TEST-CASES-OPTIMIZATIONS.md)
2. **Try Safe Mode**: Run with a single, familiar repository
3. **Review Generated Tests**: Check quality and coverage
4. **Upgrade to Trusted Mode**: Once comfortable, automate with Trusted Mode
5. **Integrate with CI/CD**: Add to your build pipelines

---

**Ready to generate Spring Boot tests!** 🚀
