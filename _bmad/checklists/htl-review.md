# HTL Review Checklist

## Severity Scale

| Level | Label | Meaning |
|---|---|---|
| 5 | Critical | XSS via missing/wrong context, `@ context='unsafe'` on user data, hardcoded secrets |
| 4 | High | Business logic in template, edit-mode broken, wrong context for location |
| 3 | Medium | Hardcoded i18n, inline JS/CSS, redundant `data-sly-use`, deep nesting |
| 2 | Low | Naming, magic numbers, oversized template |
| 1 | Info | HTL idiom improvement, modern syntax preference |

## Check Categories

### XSS & Context Handling
- [ ] Missing `@ context` where required
- [ ] Wrong context for location (`html` in attribute, `attribute` in href/src)
- [ ] Missing `uri` on URLs
- [ ] Missing `scriptString`/`styleString` where needed
- [ ] `@ context='unsafe'` without justifying comment
- [ ] Authored/user data interpolated into attributes without context

### HTL Syntax & Expressions
- [ ] Incorrect expression syntax
- [ ] Dead expressions
- [ ] Redundant `!empty` checks
- [ ] Complex ternary chains that belong in Sling Model
- [ ] `data-sly-test` + `data-sly-list` scoping conflicts

### Sling Model Binding
- [ ] Multiple `data-sly-use` of same model (should use once + scope)
- [ ] Inline business logic instead of model method
- [ ] Direct `properties.foo` access where typed getter exists
- [ ] Missing model adaptation
- [ ] `data-sly-use` scope leakage

### i18n & Content
- [ ] Hardcoded user-facing strings without `@ i18n`
- [ ] Hardcoded asset/DAM/environment URLs
- [ ] Missing fallback for empty authored content
- [ ] Missing defaults for required properties

### Templates & Includes
- [ ] `data-sly-resource` vs `data-sly-include` misuse
- [ ] Missing/wrong `decorationTagName`
- [ ] Missing `data-sly-unwrap` on logic-only elements
- [ ] `data-sly-template` parameter errors
- [ ] Template name collisions

### Authoring Experience
- [ ] Missing `cq:placeholder`/empty-state handling
- [ ] Components that throw or render blank in edit mode
- [ ] Missing edit decoration
- [ ] Layout container misuse
- [ ] Breaking Universal Editor preview

### Performance
- [ ] Repeated model invocations inside `data-sly-list`
- [ ] Unnecessary nested `data-sly-use`
- [ ] Oversized templates (>150 lines)
- [ ] Redundant resource resolution

### Accessibility
- [ ] Non-semantic elements (`<div>` as button)
- [ ] Missing alt fallback
- [ ] Missing ARIA on dynamic components
- [ ] Focus-management gaps

### Maintainability
- [ ] Inline `<script>`/`<style>` in HTL output
- [ ] Complex logic embedded in template
- [ ] Undocumented template parameters
- [ ] Magic numbers
- [ ] Oversized files
