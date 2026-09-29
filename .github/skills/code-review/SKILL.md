---
name: code-review
description: Perform structured peer review of implementation against requirements and architecture.
---

# Code Review Skill

Review the implementation against:

## 1. Correctness

- Does the implementation satisfy requirements.md?
- Does it follow architecture.md?
- Are edge cases handled?

## 2. Security

Check for:

- Hardcoded secrets
- Sensitive information
- Injection vulnerabilities
- Unsafe input handling
- Authentication/authorization problems

## 3. Error Handling

Check:

- API failures
- Missing files
- Empty repositories
- Invalid input
- Unexpected responses

## 4. Test Coverage

Check:

- Happy path
- Missing data
- Invalid data
- Not Found cases
- Failure scenarios

## 5. Code Clarity

Check:

- Naming
- Function size
- Complexity
- Readability
- Maintainability

## 6. DRY

Identify duplicated logic and recommend reusable functions.

## 7. Dependency Safety

Review dependencies for:

- Unnecessary packages
- Outdated versions
- Known security concerns

## Review Output

Classify findings as:

- Critical
- High
- Medium
- Low
- Informational

For each finding provide:

- File
- Location
- Problem
- Why it matters
- Recommended fix