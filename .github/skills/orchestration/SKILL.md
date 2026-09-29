---
name: orchestration
description: "Coordinate the full SDLC agent pipeline, delegate each stage, track evidence and blockers, and stop at human approval gates."
---

# SDLC Orchestration

## Pipeline

1. Requirements Agent: produce testable requirements; obtain human approval.
2. Architecture Agent: design from approved requirements; obtain human approval.
3. Design Review Agent: record risks and findings; obtain human approval for architecture changes or accepted exceptions.
4. Implementation Planning Agent: create dependency-ordered tasks; obtain human approval.
5. Implementation Agent: complete approved, unblocked tasks and report focused test results.
6. Code Review Agent: perform a read-only review; route required changes back to implementation.
7. Verification Agent: run code and documentation checks; route failures/blockers back to the appropriate stage.
8. Pull Request Agent: prepare PR material after review and verification; create a PR only on explicit user request with an available authorized tool.

## Operating Rules

- Start by inspecting existing artifacts and identifying the current approved stage; resume rather than regenerate completed work.
- Delegate to the named specialist and record its evidence, outputs, open questions, and blockers.
- Never cross a required human approval gate without explicit approval.
- A code-review result or passing tests do not constitute publication approval.
- Preserve `Not Found`, source provenance, conflicts, and out-of-scope boundaries across every handoff.
- Show the user current stage, next stage, and any decision needed. Do not claim a task or check completed without evidence.