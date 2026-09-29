---
name: implementation
description: "Implement an approved, unblocked task from impl-plan.md with focused changes, tests, and truthful verification results."
---

# Implementation

## Procedure

1. Read `requirements.md`, `architecture.md`, `design-review.md`, and `impl-plan.md` plus the task's affected code and tests.
2. Select only the next approved, unblocked task. Stop and report if approval, a dependency, or required information is missing.
3. State the task, scope, affected files, and focused validation before editing.
4. Follow local conventions, reuse existing utilities, validate untrusted inputs, and preserve provenance and classification boundaries.
5. Add or update tests for the behavior, including relevant missing, invalid, failure, and `Not Found` cases.
6. Run the narrowest relevant test first, then required broader checks. Report exact commands and actual results.
7. Identify documentation inconsistencies and update affected artifacts only within the approved scope.

Do not change approved requirements or architecture without human approval. Never claim an unrun check passed.