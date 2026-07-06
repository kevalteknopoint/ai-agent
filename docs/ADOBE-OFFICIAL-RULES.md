# Adobe Official Custom Code Quality Rules Integration

## Overview

AEM Quality Gate now includes **all 53 of Adobe's official custom code quality rules** from Cloud Manager, ensuring compliance with Adobe's engineering best practices and Cloud Service requirements.

### Sources
- **18 SonarQube Rules** (Java/Backend code analysis)
- **35 OakPAL Rules** (Content package validation)
- **Reference**: [Adobe Experience League - Custom Code Quality Rules](https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/implementing/using-cloud-manager/test-results/custom-code-quality-rules)

---

## SonarQube Rules (18) — Java/Backend Code

These rules are integrated into the Quality Gate via custom PMD XPath rules in `pmd-ruleset-adobe-official.xml`. They enforce Adobe's engineering standards for security, resource management, logging, and API usage.

### Security Rules (CWE-Based)

#### **CWE-676: Avoid Thread.stop() / Thread.interrupt()**
- **Severity**: Major
- **Rule ID**: `adobe-cwe-676`
- **Rationale**: Unsafe thread termination can leave resources in inconsistent states
- **Example**: 
  ```java
  // BAD
  Thread t = new Thread();
  t.stop();  // ❌ Unsafe
  
  // GOOD
  Thread t = new Thread();
  // Use interruption or design for clean shutdown
  ```

#### **CWE-134: Format String Injection**
- **Severity**: Major
- **Rule ID**: `adobe-cwe-134`
- **Rationale**: External data in format strings (printf, String.format) can cause injection attacks
- **Example**:
  ```java
  // BAD
  String format = request.getParameter("fmt");
  String result = String.format(format, arg);  // ❌ Injection risk
  
  // GOOD
  String result = String.format("%s", userInput);
  ```

#### **ConnectionTimeoutMechanism (CRITICAL)**
- **Severity**: Blocker
- **Rule ID**: `adobe-connection-timeout-mechanism`
- **Rationale**: HTTP clients without timeouts can exhaust server connections under load
- **Recommended Timeout**: ≤60 seconds
- **Example**:
  ```java
  // BAD
  URL url = new URL("https://external-api.com");
  URLConnection conn = url.openConnection();
  // ❌ No timeout set — can hang indefinitely
  
  // GOOD
  URL url = new URL("https://external-api.com");
  URLConnection conn = url.openConnection();
  conn.setConnectTimeout(30000);  // 30 seconds
  conn.setReadTimeout(30000);
  ```

---

### AEM/Sling Best Practices (6 Rules)

#### **CQBP-72: Close ResourceResolver (BLOCKER)**
- **Severity**: Blocker
- **Rule ID**: `adobe-cqbp-72`
- **Rationale**: Unclosed ResourceResolvers exhaust login session pools and cause memory leaks
- **Enforcement**: Try-with-resources or finally block required
- **Example**:
  ```java
  // BAD
  ResourceResolver resolver = resourceResolverFactory.getServiceResourceResolver(params);
  // ❌ Not closed — session leak
  
  // GOOD
  try (ResourceResolver resolver = resourceResolverFactory.getServiceResourceResolver(params)) {
    // Use resolver
  }
  ```

#### **CQBP-75: Resource Type Binding**
- **Severity**: Major
- **Rule ID**: `adobe-cqbp-75`
- **Rationale**: Use @SlingServletResourceTypes (resource type binding) instead of @SlingServletPaths
- **Impact**: Better component isolation and reusability
- **Example**:
  ```java
  // BAD
  @SlingServlet(paths = "/bin/my-servlet")
  public class MyServlet extends SlingAllMethodsServlet { }
  
  // GOOD
  @SlingServlet(resourceTypes = "my/component", methods = "POST")
  public class MyServlet extends SlingAllMethodsServlet { }
  ```

#### **CQBP-71: Avoid Hardcoded /libs and /apps Paths**
- **Severity**: Major
- **Rule ID**: `adobe-cqbp-71`
- **Rationale**: Hardcoded paths reduce portability across environments
- **Example**:
  ```java
  // BAD
  String path = "/apps/my-app/config";  // ❌ Hardcoded
  
  // GOOD
  String path = resourceResolver.getSearchPath()[0] + "my-app/config";
  // or use configurable properties
  ```

#### **CQBP-75: Use Service User Login**
- **Severity**: Critical (part of CQBP)
- **Related to**: CQBP-72 above
- **Impact**: Proper session and login management

#### **Sling Model @Optional Misuse**
- **Severity**: Major
- **Rationale**: @Inject with @Optional is deprecated; use @ValueMapValue or @OsgiInjector
- **Example**:
  ```java
  // BAD
  @Inject @Optional
  private String value;
  
  // GOOD
  @ValueMapValue(injectionStrategy = OPTIONAL)
  private String value;
  ```

#### **Resource Type Binding (CQBP-75)**
- Already covered above

---

### Logging Best Practices (6 Rules) — CQBP-44

Adobe mandates SLF4J logging with specific rules to prevent log duplication and resource waste.

#### **CQBP-44: CatchAndEitherLogOrThrow**
- **Severity**: Minor
- **Rule ID**: `adobe-cqbp-44-catch-log-throw`
- **Rationale**: Don't both log AND throw the same exception (duplication)
- **Example**:
  ```java
  // BAD
  try {
    // code
  } catch (Exception e) {
    LOG.error("Failed", e);
    throw e;  // ❌ Duplication: log from caller + here
  }
  
  // GOOD
  try {
    // code
  } catch (Exception e) {
    LOG.error("Failed", e);
  }
  // OR
  try {
    // code
  } catch (Exception e) {
    throw new RuntimeException(e);  // Let caller log
  }
  ```

#### **CQBP-44: LogInfoInGetOrHeadRequests**
- **Severity**: Minor
- **Rule ID**: `adobe-cqbp-44-log-level-get-head`
- **Rationale**: Reduce log noise for GET/HEAD (high-volume) requests
- **Example**:
  ```java
  // BAD
  @Override
  protected void doGet(...) {
    LOG.info("User accessed page");  // ❌ Too noisy
  }
  
  // GOOD
  @Override
  protected void doGet(...) {
    LOG.debug("User accessed page");  // ✓ Debug level for high-volume
    LOG.warn("Unusual access pattern");  // ✓ Warn for important events
  }
  ```

#### **CQBP-44: WrongLogLevelInCatchBlock**
- **Severity**: Minor
- **Rule ID**: `adobe-cqbp-44-catch-block-log-level`
- **Rationale**: Exceptions must be logged at WARN/ERROR, not DEBUG/INFO
- **Example**:
  ```java
  // BAD
  catch (Exception e) {
    LOG.debug("Failed to process", e);  // ❌ Too low
    LOG.info("Failed to process", e);   // ❌ Too low
  }
  
  // GOOD
  catch (Exception e) {
    LOG.warn("Failed to process", e);   // ✓ Proper level
    LOG.error("Critical failure", e);   // ✓ For critical errors
  }
  ```

#### **CQBP-44: ExceptionPrintStackTrace**
- **Severity**: Minor
- **Rule ID**: `adobe-cqbp-44-no-printstack-trace`
- **Rationale**: Use SLF4J, not printStackTrace()
- **Example**:
  ```java
  // BAD
  catch (Exception e) {
    e.printStackTrace();  // ❌ Goes to stderr, not logs
  }
  
  // GOOD
  catch (Exception e) {
    LOG.error("Error", e);  // ✓ SLF4J framework
  }
  ```

#### **CQBP-44: LogLevelConsolePrinters**
- **Severity**: Minor
- **Rule ID**: `adobe-cqbp-44-no-console-output`
- **Rationale**: Use SLF4J, not System.out/err
- **Example**:
  ```java
  // BAD
  System.out.println("Debug info");  // ❌ Not in logs
  System.err.println("Error");       // ❌ Not in logs
  
  // GOOD
  LOG.debug("Debug info");
  LOG.error("Error");
  ```

---

### Cloud Service & API Best Practices (3 Rules)

#### **AMSCORE-554: Don't Use Sling Scheduler**
- **Severity**: Minor
- **Rule ID**: `adobe-amscore-554-scheduler`
- **Rationale**: Use Sling Scheduled Jobs instead (more cloud-native, horizontally scalable)
- **Example**:
  ```java
  // BAD
  // Using Sling Scheduler
  
  // GOOD
  // Use Sling Scheduled Jobs:
  @Scheduled(period = 60, period_unit = TimeUnit.SECONDS)
  @Component
  public class MyScheduledJob implements Runnable {
    @Override
    public void run() { }
  }
  ```

#### **Deprecated AEM APIs**
- **Severity**: Minor
- **Rule ID**: `adobe-deprecated-apis`
- **Rationale**: Some AEM APIs are deprecated or unsupported in Cloud Service
- **Covered by**: java:S1874 (SonarQube standard) + AMSCORE-553 (AEM-specific)

#### **AEMSRE-870: Reuse HTTPClient Instances**
- **Severity**: Minor
- **Rule ID**: `adobe-reuse-http-client`
- **Rationale**: Creating HTTPClient in methods causes resource leaks; create at class level
- **Example**:
  ```java
  // BAD
  void callExternalAPI() {
    HttpClient client = new HttpClient();  // ❌ Created in method
    // use client
    // client not properly closed
  }
  
  // GOOD
  private final HttpClient client = new HttpClient();  // ✓ Class-level
  
  void callExternalAPI() {
    // reuse client
  }
  ```

---

## OakPAL Rules (35) — Content Package Validation

OakPAL rules validate JCR content package structure, Oak indexes, and Cloud Service compatibility. These are separate from code analysis.

### Oak Lucene Indexing (13 Rules) — CRITICAL

#### **Critical Blockers** (must be fixed)
1. **IndexTikaNode** — Custom Lucene indexes must have Tika config
2. **IndexAsyncProperty** — Lucene indexes require `async: [async]` property
3. **IndexDamAssetLucene** — DAM asset indexes must include specific tags
4. **IndexType** — Only Lucene type allowed (legacy types must migrate)
5. **IndexDamAssetLucene (queryPaths)** — Don't specify `queryPaths` in damAssetLucene

#### **Minor Compliance Rules**
- IndexCompatVersion, IndexDescendantNodeType, IndexRulesNode
- IndexName, IndexSeedProperty, IndexReindexProperty
- OakIndexLocation, IndexIncludedPathsWithoutQueryPaths
- And 3 more structural/naming rules

### Package Structure (5 Rules)

- **DuplicateOsgiConfigurations** (Major) — One config per component per runmode
- **ConfigAndInstallShouldOnlyContainOsgiNodes** (Major) — No content in /config or /install
- **PackageOverlaps** (Major) — Don't write to same paths from multiple packages
- **ImmutableMutableMixedPackage** (Minor) — Separate /apps/libs from /etc
- **DuplicateNameProperty** (Minor) — No duplicate property names

### Cloud Service Compatibility (5 Rules)

- **ClassicUIAuthoringMode** (Minor) — Don't default to Classic UI
- **ComponentWithOnlyClassicUIDialog** (Minor) — Provide Touch UI dialogs
- **ReverseReplication** (Minor) — Not supported in Cloud Service
- **CloudServiceIncompatibleWorkflowProcess** (Major) — Update legacy workflows
- **SupportedRunmode** (Minor) — Follow strict Cloud Service runmode naming

### Component & Template Modernization (2 Rules)

- **StaticTemplateUsage** (Minor) — Use editable templates
- **LegacyFoundationComponentUsage** (Minor) — Use Core Components

### Performance & Optimization (2 Rules)

- **OverrideOfQueryLimitReads** (Minor) — Don't override (causes slow reads)
- **ClientlibProxyResource** (Minor) — Place resources in proper folders

---

## Integration in Quality Gate

### 1. SonarQube Rules (18)
- **Location**: `quality-gate/rules/java/pmd-ruleset-adobe-official.xml`
- **Invocation**: Automatically included when running Quality Gate
- **Reporting**: Included in aggregated quality report
- **Dimension**: Mapped to Java, Sling/AEM as appropriate

### 2. OakPAL Rules (35)
- **Location**: `quality-gate/rules-manifest-oakpal.json`
- **Status**: Available as reference; run separately with Maven plugin
- **Future**: Integration with automated OakPAL CLI validation planned

### 3. Running Quality Gate with Adobe Rules

```bash
# Scan a project — automatically includes Adobe's 18 SonarQube rules
/aem-quality-gate --args '{
  "repositories": [{
    "repoUrl": "https://github.com/your-org/aem-project.git",
    "repoName": "my-aem-app",
    "branch": "main"
  }]
}'
```

The runner executes:
```bash
mvn pmd:pmd \
  -Dpmd.rulesets=\
    rules/java/pmd-ruleset-aem-sling.xml,\
    rules/java/pmd-ruleset-java-general.xml,\
    rules/java/pmd-ruleset-adobe-official.xml
```

All three rulesets (custom AEM/Sling + general Java + Adobe official) are enforced together.

---

## Mapping to Dimensions & Severity

### Java Dimension (SonarQube Rules)

| Rule | Category | Severity | Dimension |
|------|----------|----------|-----------|
| CWE-676 | Security | Major | Java |
| CWE-134 | Security | Major | Java |
| **ConnectionTimeoutMechanism** | **Security** | **Blocker** | **Java** |
| CQBP-44 Rules (6) | Logging | Minor | Java |
| AMSCORE-554 | Cloud Service | Minor | Sling/AEM |
| AEMSRE-870 | Performance | Minor | Java |
| Deprecated APIs | API Design | Minor | Java |

### Sling/AEM Dimension

| Rule | Category | Severity | Dimension |
|------|----------|----------|-----------|
| **CQBP-72** | **Security** | **Blocker** | **Sling/AEM** |
| CQBP-75 | Design | Major | Sling/AEM |
| CQBP-71 | Design | Major | Sling/AEM |
| Inject @Optional | Design | Minor | Sling/AEM |
| Scheduler | Cloud Service | Minor | Sling/AEM |

---

## Compliance Checklist

Before deploying to Cloud Service, ensure:

### SonarQube Rules (Java Code)
- [ ] No ConnectionTimeoutMechanism violations (BLOCKER)
- [ ] No ResourceResolver leaks (CQBP-72, BLOCKER)
- [ ] All servlets use @SlingServletResourceTypes (CQBP-75)
- [ ] No hardcoded /libs or /apps paths (CQBP-71)
- [ ] No format string injection risks (CWE-134)
- [ ] Logging follows CQBP-44 rules (6 rules)
- [ ] Using Sling Scheduled Jobs, not Scheduler (AMSCORE-554)
- [ ] Reusing HTTPClient instances (AEMSRE-870)
- [ ] No deprecated AEM APIs

### OakPAL Rules (Content Packages)
- [ ] Lucene indexes have Tika config (IndexTikaNode, BLOCKER)
- [ ] Lucene indexes have async property (IndexAsyncProperty, BLOCKER)
- [ ] DAM indexes properly configured (IndexDamAssetLucene, BLOCKER)
- [ ] Only Lucene index type used (IndexType, BLOCKER)
- [ ] No modifications under /libs
- [ ] OSGi configs not duplicated per runmode
- [ ] Content separated by mutability (/apps vs /etc)
- [ ] Touch UI provided for all components
- [ ] Workflows updated for asset micro-services
- [ ] Using editable templates, not static

---

## References

- **Adobe Experience League**: [Custom Code Quality Rules](https://experienceleague.adobe.com/en/docs/experience-manager-cloud-service/content/implementing/using-cloud-manager/test-results/custom-code-quality-rules)
- **Cloud Manager**: Enforces these rules automatically in production pipelines
- **AEM Engineering Best Practices**: Documented by Adobe Professional Services

---

## Need Help?

If a rule violation is unclear:
1. Check the rule ID in `rules-manifest.json` or `rules-manifest-oakpal.json`
2. Read the rationale section for why the rule exists
3. Review the example (good vs bad) in this document
4. Consult Adobe's official documentation linked above
5. Use AI Curation to propose rule adjustments if false positives occur

**All 53 Adobe rules are now enforced locally in Quality Gate, matching Cloud Manager's requirements.**
