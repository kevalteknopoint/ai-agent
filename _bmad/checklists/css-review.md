# CSS/SCSS Review Checklist

## Severity Scale

| Level | Label | Meaning |
|---|---|---|
| 5 | Critical | Breaks layout in supported browsers, blocks a11y, security risk (`expression()`) |
| 4 | High | Specificity war causing override storms, major perf regression, broken responsive |
| 3 | Medium | Architecture violation, duplicated rules, unmaintainable nesting |
| 2 | Low | Magic numbers, naming drift, minor cleanup |
| 1 | Info | Optional best practice |

## Check Categories

### Specificity & Cascade
- [ ] `!important` usage (count and justify)
- [ ] ID selectors in component styles
- [ ] Deep SCSS nesting (>3 levels)
- [ ] Overqualified selectors (`div.btn`)
- [ ] Specificity wars across files

### Architecture
- [ ] BEM/SMACSS/ITCSS adherence
- [ ] Naming consistency
- [ ] Partial/file organization
- [ ] Separation of layout/component/utility

### Performance
- [ ] Universal selectors (`*`) in hot paths
- [ ] Expensive descendant selectors
- [ ] Heavy `box-shadow`/`filter`/`backdrop-filter` stacks
- [ ] `will-change` misuse
- [ ] Reflow-forcing properties (top/left vs transform)

### Maintainability
- [ ] Dead/unused styles
- [ ] Duplicated declarations
- [ ] Hardcoded values instead of design tokens
- [ ] Magic numbers
- [ ] Inconsistent units

### Responsive
- [ ] Fixed widths without max-width
- [ ] Missing/inconsistent breakpoints
- [ ] Viewport unit misuse on inputs
- [ ] Mobile-first vs desktop-first inconsistency

### Accessibility
- [ ] Missing/removed focus styles (`outline: none` without `:focus-visible`)
- [ ] Colour as only state indicator
- [ ] Missing `prefers-reduced-motion`
- [ ] Target-size < 24px
- [ ] `font-size` in px blocking user scaling

### Cross-browser & Modern CSS
- [ ] Manual prefixes autoprefixer handles
- [ ] Missing `@supports` fallbacks (`:has`, container queries, subgrid)
- [ ] Deprecated properties

### SCSS-specific
- [ ] `@extend` overuse
- [ ] `@import` not migrated to `@use`/`@forward`
- [ ] Unused mixins/variables/functions
- [ ] Unextended placeholder selectors
- [ ] Ineffective `&`-chaining
