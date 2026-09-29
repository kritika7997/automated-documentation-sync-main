---
name: implementation-planning
description: "Build or revise a dependency-ordered implementation plan with bounded tasks, blockers, traceability, tests, and acceptance criteria."
---

# Implementation Planning

## Procedure

1. Read approved requirements, architecture, design-review findings, repository structure, and existing tests.
2. Split work into small tasks in dependency order; identify parallelizable tasks only when dependencies allow it.
3. For every task, record its ID, scope, dependencies, blockers, requirement links, architecture component, expected modules, tests, and acceptance condition.
4. Mark unresolved inputs and decisions as `Not Found` or blocked. Do not silently choose providers, defaults, or business rules.
5. Check that all in-scope requirements are covered and no excluded work has been added.
6. Update `impl-plan.md`, summarize changes and open decisions, and wait for human approval before implementation.

## Quality Gate

The plan is ready for review only when tasks are testable, dependency ordered, traceable, and consistent with approved architecture.