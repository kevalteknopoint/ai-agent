# Java/Spring Boot Review Checklist

## Severity Scale

| Level | Label | Meaning |
|---|---|---|
| 5 | Critical | Security flaw (injection, broken auth), data corruption, prod outage, deadlock, secret exposure |
| 4 | High | Incorrect business logic, N+1 query, memory/connection leak, missing @Transactional, race condition |
| 3 | Medium | Anti-pattern, layer leak, code duplication, swallowed exception, missing validation |
| 2 | Low | Magic numbers, naming, oversized method |
| 1 | Info | Optional best practice, modern API migration |

## Check Categories

### Correctness
- [ ] Null safety violations
- [ ] `Optional` misuse (`.get()` without check)
- [ ] `equals`/`hashCode` contract broken on entities
- [ ] Raw generics & unchecked casts
- [ ] Default `Charset` reliance
- [ ] Autoboxing in loops (performance + NPE risk)
- [ ] Integer overflow potential

### Spring Framework
- [ ] Field `@Autowired` instead of constructor injection
- [ ] Bean scope incorrectness
- [ ] `@Transactional` wrong placement/propagation/rollbackFor
- [ ] Self-invocation bypassing AOP proxy
- [ ] Lazy-init risk
- [ ] Circular dependencies
- [ ] `@Value` where `@ConfigurationProperties` better
- [ ] Profile-specific beans missing defaults
- [ ] `@Async` self-invocation (won't be async)

### Security
- [ ] SQL injection (string concat in `@Query`/native/createQuery)
- [ ] Command injection
- [ ] Hardcoded secrets/credentials
- [ ] Missing `@PreAuthorize`/`@Secured` on state-changing endpoints
- [ ] CSRF disabled without justification
- [ ] CORS `*` in production
- [ ] Stack traces in error responses
- [ ] Log injection (unescaped user input in logs)
- [ ] Deserialization of untrusted input
- [ ] Weak crypto (MD5/SHA-1/DES)

### Performance
- [ ] N+1 queries (missing `@EntityGraph`/`JOIN FETCH`)
- [ ] Missing pagination on list endpoints
- [ ] `EAGER` fetch defaults on collections
- [ ] Blocking calls inside `Mono`/`Flux`
- [ ] Missing `@Cacheable` on hot paths
- [ ] Expensive operations in loops
- [ ] Full-table loads without limit
- [ ] Missing indexes hinted by query patterns

### Concurrency
- [ ] Shared mutable state without synchronization
- [ ] `ThreadLocal` leaks in pooled threads
- [ ] Blocking I/O in async/reactive paths
- [ ] Race conditions in singletons
- [ ] Double-checked locking errors
- [ ] `get` + `put` instead of `computeIfAbsent`
