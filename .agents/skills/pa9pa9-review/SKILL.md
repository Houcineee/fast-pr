---
name: pa9pa9-review
description: Review a pull request for actionable defects using the project's review rules, then return structured findings for the PA9 PA9 CLI to publish.
---

# Pull request review

Review the pull request changes as a careful senior software engineer. Follow the repository's `.pa9pa9/rules.md` as the source of project-specific review policy.

## Procedure

1. Read `.pa9pa9/rules.md` and the repository guidance that applies to changed files (for example `AGENTS.md`, contribution guides, and relevant package documentation).
2. Inspect the PR diff and enough surrounding code and call sites to understand behavior. Use the base and head revisions supplied by the caller; do not assume the working tree represents either revision.
3. Trace likely failure paths, boundary cases, error handling, data flow, and compatibility implications. Check tests or related code when useful.
4. Report only concrete defects introduced by this PR. A finding must be actionable, explain a user-visible or operational consequence, and point to the smallest relevant changed line range. Do not report a concern that cannot be supported by the available code/context.
5. Do not edit files, run formatters that modify files, create commits, or push changes. Do not attempt to fix findings.

## Finding standard

- Prioritize correctness, security, data integrity, reliability, and meaningful performance regressions.
- Do not flag pre-existing issues, speculative risks, personal preferences, or style differences unless the project rules identify a real, enforceable convention whose violation causes a problem.
- Avoid duplicate findings. Prefer one finding that explains the root cause over several symptoms.
- Keep each finding concise: state the condition, consequence, and (when helpful) a practical fix direction.
- Use severity `critical`, `high`, `medium`, or `low` according to `.pa9pa9/rules.md`.
- If there are no actionable defects, return an empty findings array. Do not invent issues to make the review appear useful.

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

Use repository-relative paths and line numbers from the PR diff's head revision. Line ranges must overlap changed lines and should be as short as possible. Use `P1` for critical/high, `P2` for medium, and `P3` for low in the title. If a reliable changed-line location is unavailable, omit that finding rather than inventing a location. JSON strings must be valid JSON with escaped newlines and quotes.
