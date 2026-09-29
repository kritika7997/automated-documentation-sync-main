---
name: sdlc-artifacts
description: "Apply traceability, source-of-truth, and approval rules when editing SDLC documentation and reports."
applyTo: "requirements.md,architecture.md,design-review.md,impl-plan.md,docs/**/*.md,reports/**/*.md"
---

# SDLC Artifact Rules

- Read the current artifact and its authoritative inputs before editing; preserve stable identifiers and existing approved decisions.
- Trace requirements to source evidence and implementation tasks. Keep source policy, FAQ, approved clarification, system decision, `Not Found`, and out-of-scope information distinct.
- Write `Not Found` when source material does not establish a value. Do not invent defaults, approvals, test results, or business rules.
- Identify contradictions and unresolved decisions explicitly. Do not silently resolve them or treat recommendations as approved decisions.
- Keep requirements, architecture, design review, and implementation plan consistent. Record relevant updates when a change affects another artifact.
- Architecture decisions, design-review findings that change architecture, and implementation plans require human approval before downstream work proceeds.