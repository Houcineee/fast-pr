---
name: pa9pa9-review
description: Review a pull request for actionable defects using the project's review rules, then return structured findings for the PA9 PA9 CLI to publish.
---

# Pull request review

Review the pull request changes as a careful senior software engineer. Follow the repository's `.pa9pa9/rules.md` as the source of project-specific review policy.

## Procedure

1. Read `.pa9pa9/rules.md` and applicable repository guidance (such as `AGENTS.md`, contribution guides, and package documentation).
2. Inspect the PR diff between the supplied base and head revisions, then inspect surrounding code and call sites. The current checkout is the PR head.
3. Trace failure paths, boundary cases, error handling, data flow, and compatibility implications. Check tests or related code when useful.
4. Report only concrete defects introduced by this PR. Each finding must be actionable, explain a user-visible or operational consequence, and point to the smallest relevant changed line range.
5. Do not edit files, run modifying formatters, create commits, or push changes. Do not attempt to fix findings.

## Finding standard

- Prioritize correctness, security, data integrity, reliability, and material performance regressions.
- Do not flag pre-existing issues, speculative risks, preferences, or style differences unless project rules identify an enforceable convention with a concrete consequence.
- Avoid duplicate findings. State the condition, consequence, and a practical fix direction when useful.
- Use severity `critical`, `high`, `medium`, or `low` according to `.pa9pa9/rules.md`.
- Return an empty findings array when there are no actionable defects.

## Output contract

Return exactly one JSON object and no surrounding Markdown or commentary:

```json
{
  "summary": "A brief, neutral summary of the review.",
  "findings": [
    {
      "severity": "high",
      "title": "[P1] Prevent unauthorized access",
      "body": "Explain when the defect occurs and its concrete impact.",
      "path": "src/example.py",
      "start_line": 42,
      "end_line": 42
    }
  ]
}
```

Use repository-relative paths and line numbers from the PR head revision. Line ranges must overlap changed lines and be as short as possible. Use `P1` for critical/high, `P2` for medium, and `P3` for low in titles. Omit a finding if a reliable changed-line location is unavailable. Return valid JSON.
