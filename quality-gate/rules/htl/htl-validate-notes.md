# HTL (Sightly) Validation Configuration

## Overview
HTL validation is performed using the **Apache Sling HTL Maven Plugin** (`org.apache.sling:htl-maven-plugin`), which provides:
- Compile-time syntax validation of HTL expressions
- Detection of undefined variables and properties
- Strict type checking where possible

## Rules Enforced

### 1. **HTL Syntax Validation** (BLOCKER)
- Invalid HTL expression syntax
- Unclosed blocks (`data-sly-*` attributes)
- Invalid property access patterns

Rule ID: `htl-syntax-validation`

### 2. **Inline Scripts and Styles** (MAJOR)
- No inline `<script>` blocks in HTL components
- No inline `<style>` blocks in HTL components
- **Reason**: AEM best practice — use clientlibs for script/style separation

Rule ID: `htl-inline-script-style`

### 3. **WCMUsePojo in data-sly-use** (MAJOR)
- `data-sly-use` should not reference `WCMUsePojo` classes
- Use Sling Models (`@Model`) instead
- WCMUsePojo is deprecated and will be removed

Rule ID: `htl-wcm-use-pojo-reference`

### 4. **Missing data-sly-test Guard** (MAJOR)
- Risky `data-sly-resource` includes should be guarded with `data-sly-test`
- Prevents null-pointer exceptions at render time

Example:
```html
<!-- GOOD -->
<div data-sly-test="${model.hasContent}">
  <div data-sly-resource="${model.resourcePath}"></div>
</div>

<!-- BAD -->
<div data-sly-resource="${model.resourcePath}"></div>
```

## Invocation

The runner invokes HTL validation as follows:

```bash
mvn org.apache.sling:htl-maven-plugin:3.2.0:validate \
    -Dproject.basedir=<targetRepo> \
    -f <targetRepo>/ui.apps/pom.xml
```

## Plugin Configuration Reference

Standard Maven POM configuration (if needed in target repo):
```xml
<plugin>
  <groupId>org.apache.sling</groupId>
  <artifactId>htl-maven-plugin</artifactId>
  <version>3.2.0</version>
  <executions>
    <execution>
      <goals>
        <goal>validate</goal>
      </goals>
      <configuration>
        <sourceDir>src/main/content/jcr_root</sourceDir>
        <allowedExpressionOptions>
          <option>display</option>
          <option>format</option>
          <option>join</option>
          <option>i18n</option>
          <option>array</option>
          <option>date</option>
          <option>url</option>
          <option>context</option>
        </allowedExpressionOptions>
      </configuration>
    </execution>
  </executions>
</plugin>
```

## Known Limitations

1. **Dynamic expressions**: HTL cannot validate completely dynamic property access patterns
2. **External data sources**: Cannot validate against external APIs or service calls
3. **Conditional includes**: Cannot fully type-check conditionally included HTL files

## References

- [Apache Sling HTL Documentation](https://sling.apache.org/documentation/bundles/scripting/scripting-htl.html)
- [HTL Maven Plugin](https://sling.apache.org/documentation/bundles/scripting/scripting-htl-maven-plugin.html)
- [HTL Best Practices](https://sling.apache.org/documentation/bundles/scripting/scripting-htl-use-api.html)
