---
name: design-review
description: "Review requirements and architecture for correctness, completeness, security, reliability, maintainability, and traceability before implementation."
---

# Design Review

## Procedure

1. Read `requirements.md`, `architecture.md`, and relevant design decisions.
2. Check requirement coverage, component boundaries, interfaces, data flow, security, scalability, reliability, performance, maintainability, and failure handling.
3. Identify contradictions, missing components, unsupported assumptions, and unnecessary complexity.
4. Record each finding with severity, evidence, impact, and a practical recommendation in `design-review.md`.
5. Distinguish accepted decisions from recommendations and unresolved items; request human approval for changes to approved architecture.

Do not modify architecture silently or approve a design on behalf of a human reviewer.