# Fast PR pull request review rules

These are the default review rules. Edit this file to add project-specific architecture, language, security, and compatibility requirements. Keep rules concrete enough that a reviewer can apply them consistently.

## Review priorities

Report defects introduced by the PR that can cause:

1. **Critical (P1):** an exploitable security vulnerability, irreversible or broad data loss, or a complete outage of a core production path.
2. **High (P1):** a major feature or common workflow is broken, access controls can be bypassed, data can be corrupted, or a severe reliability regression affects users.
3. **Medium (P2):** a meaningful but limited functional defect, an important edge case failure, or a material regression with a reasonable workaround.
4. **Low (P3):** a small user-facing defect or maintainability issue that has a concrete near-term consequence. Do not use low severity for style preferences or speculative cleanup.

When impact is uncertain, choose the lower severity and explain the condition that determines impact.

## What to inspect

- **Behavior and correctness:** Does the change implement the apparent intent? Check normal and boundary inputs, empty or missing values, state transitions, ordering, retries, and concurrent operations where relevant.
- **Security and privacy:** Check authorization at trust boundaries, input validation, injection risks, unsafe deserialization, secret handling, sensitive data exposure, and whether errors or logs reveal private information. Do not treat theoretical concerns as findings without a reachable path.
- **Data integrity:** Check persistence, migrations, transactions, idempotency, schema compatibility, and destructive operations. Consider partial failure and retry behavior.
- **Errors and reliability:** Check timeouts, resource cleanup, error propagation, fallback behavior, and whether a failure can silently produce incorrect success.
- **Interfaces and compatibility:** Check API/CLI behavior, public contracts, configuration defaults, backwards compatibility, and supported platform or runtime versions.
- **Performance:** Report only a material regression on a realistic path, such as unbounded work, repeated expensive operations, or avoidable resource growth.
- **Tests:** Notice missing or ineffective coverage for changed behavior, but report it only when the absence creates a concrete risk of undetected regression. Do not demand tests for every change mechanically.

## Finding requirements

A finding must be caused by changed code, describe a reproducible or clearly reachable failure, explain its impact, and identify a changed line that best exposes the issue. Include relevant triggering conditions. Suggest a direction for fixing it when that makes the action clearer, but do not prescribe a large redesign.

Do not report:

- Issues already present on the base revision.
- Formatting, naming, or stylistic preferences unless they violate a documented project rule and cause a concrete problem.
- Hypothetical future risks without a plausible current trigger or impact.
- Duplicate symptoms of the same underlying defect.
- Requests to add comments, tests, or refactors without a specific correctness, security, reliability, or maintainability consequence.

## Project-specific rules

Add project conventions below. Prefer describing observable requirements (for example, “all database writes go through the transaction helper”) over subjective preferences.
