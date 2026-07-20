# EDS Blocks Review Checklist

## Severity Scale

| Level | Label | Meaning |
|---|---|---|
| 5 | Critical | XSS via `innerHTML` on authored content, CLS on LCP element, block completely broken |
| 4 | High | LCP regression, INP-blocking task (>50ms in decorate), accessibility blocker |
| 3 | Medium | DOM-first anti-pattern, missing `createOptimizedPicture`, CSS leak outside block |
| 2 | Low | Magic numbers, naming drift, oversized block |
| 1 | Info | Modern API migration, idiom improvement |

## Check Categories

### Block Structure
- [ ] File naming matches folder (kebab-case)
- [ ] Default export of `decorate(block)`
- [ ] CSS scoped to `.block-name`
- [ ] Variations as classes on same block (not separate files)

### CWV — LCP
- [ ] Hero images use `createOptimizedPicture` with eager loading
- [ ] Font preloads in place
- [ ] No blocking third-party scripts in eager path
- [ ] No network calls in `loadEager` delaying LCP

### CWV — CLS
- [ ] Images with explicit width/height or aspect-ratio CSS
- [ ] Fonts not causing reflow
- [ ] Dynamic content inserted below existing content
- [ ] Placeholder dimensions for async content

### CWV — INP
- [ ] `decorate()` under a frame's budget
- [ ] No synchronous heavy DOM construction
- [ ] Passive/debounced listeners
- [ ] No long synchronous loops

### DOM-first Patterns
- [ ] Consuming authored DOM (`block.children`/`row.children`) not rebuilding
- [ ] Avoiding `innerHTML` for content
- [ ] Transforming existing tree
- [ ] Handling missing/empty rows gracefully

### Vanilla JS Conventions
- [ ] No jQuery/React/Vue
- [ ] No global namespace pollution
- [ ] ES modules
- [ ] Proper listener cleanup on re-decorate
- [ ] Native DOM APIs, no `var`

### Image & Media
- [ ] `createOptimizedPicture` for content images
- [ ] `srcset` patterns
- [ ] `loading="lazy"` below-fold
- [ ] `loading="eager"` + `fetchpriority="high"` on LCP image
- [ ] No raw `<img src>` for content

### Accessibility
- [ ] Semantic HTML
- [ ] Keyboard navigation
- [ ] Focus management on dynamic content
- [ ] Alt text from authored content with fallback
