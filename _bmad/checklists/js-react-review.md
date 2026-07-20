# JS/React Review Checklist

## Severity Scale

| Level | Label | Meaning |
|---|---|---|
| 5 | Critical | Security flaw, crash, data corruption, prod outage |
| 4 | High | Incorrect logic, memory leak, major perf gap |
| 3 | Medium | Code smell, duplication, anti-pattern |
| 2 | Low | Minor perf, naming, cleanup |
| 1 | Info | Optional best practice |

## Check Categories

### Correctness
- [ ] Undeclared/unused variables
- [ ] Null safety (missing optional chaining)
- [ ] async/await without try/catch
- [ ] Unhandled promise rejection
- [ ] Array/object access without bounds check

### React Specific
- [ ] Hooks rules violation (conditional hooks, hooks in loops)
- [ ] `useEffect` missing/incorrect dependencies
- [ ] Direct state mutation
- [ ] Missing memoization on expensive computations
- [ ] List rendering without stable `key`
- [ ] Fragment misuse

### Security
- [ ] `dangerouslySetInnerHTML` with user data
- [ ] `innerHTML` assignment
- [ ] Secrets in `localStorage`/console logs
- [ ] Insecure API handling (no HTTPS enforcement)
- [ ] Missing input validation/sanitization

### Performance
- [ ] Unnecessary re-renders (missing React.memo/useMemo/useCallback)
- [ ] Expensive computations in render path
- [ ] Repeated API calls without caching
- [ ] Memory leaks (listeners/intervals/timers not cleaned up)
- [ ] Large list rendering without virtualization

### Maintainability
- [ ] Dead/unreachable code
- [ ] Magic numbers/strings
- [ ] Deep nesting (>3 levels)
- [ ] Naming inconsistency
- [ ] Oversized components (>200 lines)

### Error Handling
- [ ] Missing `try/catch` on async operations
- [ ] Swallowed exceptions (empty catch)
- [ ] No user-facing error states
- [ ] Unguarded API response access

### Architecture
- [ ] Prop drilling (>3 levels)
- [ ] Side effects in render
- [ ] Missing utility extraction
- [ ] Separation of concerns violations
