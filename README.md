# Automated Documentation Sync

An agent-assisted SDLC project for synchronizing requirements and engineering documentation with approved changes to the Overtime Compensation Policy. It preserves source provenance, distinguishes policy facts from approved clarifications, and keeps human review in control of architecture and publication decisions.

## Agent Workflow

Start with the **SDLC Orchestrator Agent** in GitHub Copilot Chat. It delegates each stage to the matching specialist and tracks evidence, open questions, and blockers:

1. Requirements Agent
2. Architecture Agent
3. Design Review Agent
4. Implementation Planning Agent
5. Implementation Agent
6. Code Review Agent
7. Verification Agent
8. Pull Request Agent

Human approval is required at the gates documented in `.github/copilot-instructions.md`. The Pull Request Agent prepares PR material; it does not publish without an explicit request.

Custom agent definitions live in `.github/agents/`, reusable role procedures in `.github/skills/`, project instructions in `.github/instructions/`, and the session-start workflow hook in `.github/hooks/`.

## Authoritative SDLC Documents

The repository-root `requirements.md`, `architecture.md`, `design-review.md`, and `impl-plan.md` are canonical. Do not edit empty or obsolete copies under `.github/`.

## Development

Requires Python 3.11 or newer.

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

The tests use local fakes and do not require production credentials or provider access.
