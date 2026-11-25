# PA9 PA9 pull request review rules

These are the default review rules. Add concrete project-specific architecture, language, security, and compatibility requirements below.

## Severity

1. **Critical (P1):** exploitable security vulnerability, irreversible or broad data loss, or complete outage of a core production path.
2. **High (P1):** a major feature or common workflow is broken, access controls can be bypassed, data can be corrupted, or a severe reliability regression affects users.
3. **Medium (P2):** a meaningful but limited functional defect, important edge case failure, or material regression with a reasonable workaround.
4. **Low (P3):** a small user-facing defect or maintainability issue with a concrete near-term consequence. Do not use low severity for style preferences or speculative cleanup.

When impact is uncertain, choose the lower severity and explain the condition that determines impact.

## Review criteria

- **Behavior and correctness:** Check intended behavior, boundaries, empty or missing values, state transitions, ordering, retries, and concurrency where relevant.
- **Security and privacy:** Check authorization at trust boundaries, validation, injection, unsafe deserialization, secrets, sensitive data exposure, and information disclosed by errors or logs. Report only reachable risks.
- **Data integrity:** Check persistence, migrations, transactions, idempotency, schema compatibility, destructive operations, partial failure, and retry behavior.
- **Errors and reliability:** Check timeouts, resource cleanup, error propagation, fallbacks, and silent incorrect success.
- **Interfaces and compatibility:** Check API and CLI behavior, public contracts, defaults, backwards compatibility, and supported platform/runtime versions.
- **Performance:** Report material regressions on realistic paths, such as unbounded work, repeated expensive operations, or avoidable resource growth.
- **Tests:** Consider whether changed behavior has meaningful coverage. Report missing coverage only when it creates a concrete risk of an undetected regression; do not demand tests mechanically.

## Finding requirements

A finding must be caused by changed code, describe a reproducible or clearly reachable failure, explain its impact, and identify a changed line that best exposes it. Include triggering conditions. Suggest a practical fix direction when helpful, without prescribing a broad redesign.

Do not report pre-existing issues, subjective formatting or naming preferences, hypothetical future risks without a current trigger, duplicate symptoms, or requests for tests/refactors without a specific consequence.

## Project-specific rules

Add observable requirements below. Prefer rules such as “database writes must use the transaction helper” over subjective preferences.
