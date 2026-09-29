---
name: pull-request
description: "Prepare a truthful pull request description, changelog entry, and reviewer checklist after code review and verification."
---

# Pull Request Preparation

## Procedure

1. Read the requirements, architecture, design review, implementation plan, code-review findings, verification output, and current change list.
2. Confirm review findings are resolved or clearly disclosed and required verification evidence exists.
3. Prepare a PR description with exactly these sections:

   - `## Summary`: two or three sentences describing the change and purpose.
   - `## Changes Made`: files changed and why.
   - `## Test Evidence`: commands and actual results only.
   - `## Known Limitations`: unresolved issues, `Not Found`, and out-of-scope items.
   - `## Reviewer Checklist`: requirements, architecture, design review, plan, code review, tests, docs, secrets, and limitations.

4. Include a suitable changelog entry when the project has an established changelog location; do not invent a new release version.
5. Create or publish a PR only when explicitly requested and an authorized GitHub tool is available. Human review remains mandatory.