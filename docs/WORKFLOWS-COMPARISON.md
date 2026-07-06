# AEM vs Spring Boot Workflow Agents - Comparison

## Quick Comparison

| Feature | AEM Agent | Spring Boot Agent |
|---------|-----------|-------------------|
| **Workflow Name** | aem-unit-test-cases | spring-boot-unit-test-cases |
| **Best For** | AEM Sites backend projects | Spring Boot applications |
| **Test Framework** | JUnit, Mockito, AEM Mocks | JUnit, Mockito, Spring Test |
| **Build Command** | mvn clean test -pl core -am | mvn clean test |
| **Test Location** | src/test/java/ | src/test/java/ |
| **Permission Gates** | 3 gates (Safe/Trusted) | 3 gates (Safe/Trusted) |
| **Token Optimization** | 47% reduction | 47% reduction |
| **Build Validation** | Yes (mandatory) | Yes (mandatory) |
| **Feature Branch** | feature/ai-unit-test-cases | feature/ai-unit-test-cases |

## Choosing Which Agent

### Use AEM Agent If:
✅ Working with Adobe AEM Sites projects
✅ Projects use AEM-specific APIs
✅ Need AEM Mocks for testing
✅ Projects have AEM-specific structures
✅ Testing core/ui modules in AEM

### Use Spring Boot Agent If:
✅ Working with Spring Boot applications
✅ Standard Java Spring projects
✅ Microservices architecture
✅ REST APIs with Spring Web
✅ Spring Data JPA projects

## Workflow Structure Comparison

### AEM Workflow
```
AEM Projects
├── Core Module (backend)
│   ├── Models
│   ├── Services
│   ├── Servlets
│   └── src/test/java/
├── UI Module (frontend)
└── Build: mvn clean test -pl core -am
```

### Spring Boot Workflow
```
Spring Boot Projects
├── Controllers
├── Services
├── Repositories
├── Models/Entities
└── src/test/java/
   Build: mvn clean test
```

## Test Generation Examples

### AEM Test Example
```java
@RunWith(AemContext.class)
class UserServiceTest {
    @Rule
    public AemContext context = new AemContext();

    private UserService userService;

    @Before
    public void setUp() {
        userService = new UserService(
            context.getService(UserRepository.class)
        );
    }

    @Test
    void testCreateUser() {
        // Test using AEM Mocks
    }
}
```

### Spring Boot Test Example
```java
@SpringBootTest
class UserServiceTest {
    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    void testCreateUser() {
        // Standard Spring Boot test
    }
}
```

## Execution Timeline

### AEM Workflow (3 Repositories, Safe Mode)
```
Setup Phase: 2-3 min (approvals: ~1 min)
Test Generation: 3-4 min (approval: ~1 min)
Build Validation: 5-7 min (approval: ~1 min)
Auto-Push: 1-2 min
─────────────────────
Total: 12-18 minutes
```

### Spring Boot Workflow (3 Repositories, Safe Mode)
```
Setup Phase: 2-3 min (approvals: ~1 min)
Test Generation: 3-4 min (approval: ~1 min)
Build Validation: 3-5 min (approval: ~1 min)
Auto-Push: 1-2 min
─────────────────────
Total: 10-15 minutes
```

**Note**: Spring Boot builds typically faster than AEM builds

## Safe Mode vs Trusted Mode (Both Agents)

### Safe Mode (Default)
```
Setup Phase
  → User approves cloning repository
Test Generation Phase
  → User approves test code creation
Build Validation Phase
  → User approves Maven build test
Auto-Push Phase
  → Automatic (no approval)
```

### Trusted Mode (Opt-In)
```
Setup Phase
  → Auto-approved
Test Generation Phase
  → Auto-approved
Build Validation Phase
  → Auto-approved
Auto-Push Phase
  → Automatic
```

## Permission Gates (Both Agents)

Both agents have the same permission structure:

### Gate #1: Repository Setup
```
User sees:
- Repository name
- Repository URL
- Target location
- Production branch

User decides: Approve or Deny
```

### Gate #2: Test Generation
```
User sees:
- Repository name
- Target classes to test
- Repository location

User decides: Approve or Deny
```

### Gate #3: Build Validation
```
User sees:
- Repository name
- Repository location
- Build command

User decides: Approve or Deny
```

### Auto-Push
```
No permission gate
- Automatic push if validation passes
- Commit message: "feat: Add comprehensive [AEM/Spring Boot] unit tests"
```

## Token Optimization (Both Agents)

Both agents achieve 47% token reduction:

| Stage | Before | After | Savings |
|-------|--------|-------|---------|
| Setup | 240 | 80 | 67% |
| Generation | 320 | 170 | 47% |
| Validation | 180 | 100 | 44% |
| **Per Repo** | **~1,800** | **~950** | **~47%** |

For 3 repositories: Save ~2,550 tokens per batch

## Build Validation (Both Agents)

### AEM Build Validation
```bash
mvn clean test -pl core -am

Validates:
- Core module compiles
- All unit tests pass
- Dependencies resolve
- AEM-specific code works
```

### Spring Boot Build Validation
```bash
mvn clean test

Validates:
- Project compiles
- All unit tests pass
- Dependencies resolve
- Spring Boot configuration works
```

## Test Framework Differences

### AEM Testing Stack
```
JUnit 4/5
├── Standard assertions
Mockito
├── Mock services
├── Mock repositories
└── Verify interactions
AEM Mocks
├── AEM Context
├── Sling models
├── Resource resolver
└── Value maps
```

### Spring Boot Testing Stack
```
JUnit 4/5
├── Standard assertions
Mockito
├── Mock services
├── Mock repositories
└── Verify interactions
Spring Test
├── @SpringBootTest
├── TestRestTemplate
├── WebMvcTest
└── DataJpaTest
```

## Directory Structure Comparison

### AEM Project Structure
```
project/
├── core/                      ← Backend module
│   ├── src/main/java/
│   ├── src/test/java/         ← Tests generated here
│   ├── src/test/resources/
│   └── pom.xml
├── ui.apps/
└── pom.xml
```

### Spring Boot Project Structure
```
project/
├── src/main/java/
│   ├── controllers/
│   ├── services/
│   ├── repositories/
│   └── models/
├── src/test/java/             ← Tests generated here
│   ├── controllers/
│   ├── services/
│   └── repositories/
├── src/test/resources/
└── pom.xml
```

## Use Case Examples

### Case 1: AEM Project
```bash
/aem-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/acme/aem-sites.git",
      "productionBranch": "main",
      "testCases": "UserService, ContentHelper, AuthServlet"
    }
  ]
}'
```
- Tests AEM-specific code
- Uses AEM Mocks
- Tests against core module

### Case 2: Spring Boot Project
```bash
/spring-boot-unit-test-cases --args '{
  "testCases": [
    {
      "repoUrl": "https://github.com/acme/spring-app.git",
      "productionBranch": "main",
      "testCases": "UserService, UserController, PaymentProcessor"
    }
  ]
}'
```
- Tests Spring Boot code
- Uses Spring Test
- Tests services and controllers

### Case 3: Multiple Projects (Mixed)
```bash
# Use both workflows for different projects

# First, test AEM project
/aem-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [{...aem-project...}]
}'

# Then, test Spring Boot projects
/spring-boot-unit-test-cases --args '{
  "trustedMode": true,
  "testCases": [{...spring-project-1...}, {...spring-project-2...}]
}'
```

## CI/CD Integration Patterns

### GitHub Actions (AEM)
```yaml
- name: Generate AEM Tests
  run: /aem-unit-test-cases --args '{
    "trustedMode": true,
    "testCases": [...]
  }'
```

### GitHub Actions (Spring Boot)
```yaml
- name: Generate Spring Boot Tests
  run: /spring-boot-unit-test-cases --args '{
    "trustedMode": true,
    "testCases": [...]
  }'
```

### Jenkins Pipeline (Both)
```groovy
stage('Generate Tests') {
  parallel {
    stage('AEM Tests') {
      steps {
        sh '/aem-unit-test-cases --args "{...}"'
      }
    }
    stage('Spring Boot Tests') {
      steps {
        sh '/spring-boot-unit-test-cases --args "{...}"'
      }
    }
  }
}
```

## Comparison Table: Detailed

| Aspect | AEM Agent | Spring Boot Agent |
|--------|-----------|-------------------|
| **Agent Type** | aem-test-case-creator | spring-boot-test-creator |
| **Repository Type** | Adobe AEM Sites | Spring Boot Applications |
| **Test Frameworks** | JUnit, Mockito, AEM Mocks | JUnit, Mockito, Spring Test |
| **Module Focus** | Core/Backend | Full Application |
| **Build Profile** | -pl core -am | None (full build) |
| **Build Time** | 5-10 min | 3-5 min |
| **Typical Classes** | Services, Servlets, Models | Controllers, Services, Repositories |
| **Special Imports** | org.apache.sling.* | org.springframework.* |
| **Test Annotations** | @RunWith(AemContext) | @SpringBootTest |
| **Mocking** | AEM Mocks | Mockito, Spring Test |
| **Permission Gates** | 3 (same) | 3 (same) |
| **Token Savings** | 47% | 47% |
| **Default Mode** | Safe (3 approvals) | Safe (3 approvals) |
| **Trusted Mode** | Yes (0 approvals) | Yes (0 approvals) |
| **Build Validation** | Yes (mandatory) | Yes (mandatory) |
| **Feature Branch** | feature/ai-unit-test-cases | feature/ai-unit-test-cases |

## Decision Matrix

### Choose AEM Agent When:
✅ Working on Adobe AEM Sites projects
✅ Need AEM-specific testing patterns
✅ Testing servlets, models, or helpers
✅ Using AEM APIs extensively
✅ Projects use AEM core module structure

### Choose Spring Boot Agent When:
✅ Working on Spring Boot microservices
✅ Standard Java Spring projects
✅ REST API development
✅ Spring Data JPA/JDBC projects
✅ Standard Maven project structure

### Use Both When:
✅ Organization has mixed technology stack
✅ Some projects are AEM, others are Spring Boot
✅ Unified testing workflow desired
✅ Consistent token optimization needed

## Recommendations

### For New Users
1. **Start with Safe Mode** on both workflows
2. **Try one workflow first** (whichever matches your primary project)
3. **Learn the permission gates** and understand each stage
4. **Review generated tests** for quality
5. **Upgrade to Trusted Mode** once comfortable

### For Experienced Users
1. **Use Trusted Mode** in development
2. **Integrate into CI/CD** pipelines
3. **Run both agents** for mixed tech stacks
4. **Customize baseDir** for organization structure
5. **Monitor test quality** regularly

### For CI/CD Integration
1. **Enable Trusted Mode** in automated pipelines
2. **Run both workflows** in parallel for mixed projects
3. **Set custom baseDir** to organize test repos
4. **Schedule nightly runs** for batch testing
5. **Monitor results** for coverage improvements

## Summary

| Category | AEM | Spring Boot |
|----------|-----|-------------|
| **Architecture** | Identical | Identical |
| **Permission Gates** | 3 gates | 3 gates |
| **Token Optimization** | 47% | 47% |
| **Build Validation** | Yes | Yes |
| **Safe/Trusted Modes** | Yes | Yes |
| **Difference** | AEM-specific testing | Spring Boot-specific testing |

Both workflows provide the same production-ready structure with agent-specific optimizations for different technology stacks.

---

**Need help choosing? Check your project type and pick accordingly!** 🎯
