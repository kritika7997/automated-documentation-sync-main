# Design Review

## Review Status

Review completed against the repository-root `requirements.md`, `architecture.md`, and `impl-plan.md`. The findings below are recommendations for human disposition; no architecture or requirement changes have been applied or approved by this review.

## Findings

### DR-001 — High: Product scope differs between requirements and architecture

- **Evidence:** The requirements business context describes overtime eligibility, compensation calculation, request tracking, and submission. Requirements FR-001 and FR-017 through FR-035 define calculation inputs, formulas, eligibility scenarios, reporting, and processing destinations. The architecture summary defines a documentation-synchronization system and says it may store overtime-related requirements and submission metadata only; its scope excludes payroll and payment processing. The architecture traceability table nevertheless maps those operational requirements to this system.
- **Impact:** The implementation boundary and acceptance target are ambiguous. A documentation-sync service cannot satisfy operational calculation and request-processing requirements unless those requirements describe source policy content rather than runtime behavior. This can lead to missing components or incorrect claims of coverage.
- **Recommendation:** Obtain human confirmation of the intended product boundary. Then reconcile the requirements, architecture, implementation plan, and requirements-coverage report so operational behavior is either explicitly in scope and architected, or explicitly represented as documentation content/out of scope. Do not implement either interpretation until approved.
- **Disposition:** Pending human decision.

### DR-002 — Medium: Architecture approval status is internally inconsistent

- **Evidence:** Architecture decision AD-001 says the documentation-only boundary is "Approved by requirements" and also says "Human approval of this architecture boundary" is needed. The implementation plan states that architecture/design approval is already complete.
- **Impact:** Agents cannot determine whether the architecture boundary is an approved constraint or an unresolved decision. This conflicts with the human-in-the-loop gate and can cause implementation to proceed under an unconfirmed scope.
- **Recommendation:** Confirm the approval record with the human owner, then make AD-001 and the implementation-plan approval statement consistent. Do not infer approval evidence from the requirements artifact alone.
- **Disposition:** Pending human confirmation.

### DR-003 — High: Sensitive-data access controls are not testable yet

- **Evidence:** NFR-004 requires protection of wage data, associate identifiers, approval evidence, and contact information, while marking the specific access-control requirements `Not Found`. The architecture recommends authentication, least privilege, encryption, and auditing, but the identity provider, reviewer roles, authorization model, and retention policy remain unresolved in the architecture and release-readiness document.
- **Impact:** The project cannot demonstrate who may view or change sensitive records, how reviewer authorization is enforced, or which tests prove those controls. This is a production security risk, even though the release-readiness document correctly lists related decisions as human-gated.
- **Recommendation:** Before production integration, obtain human approval for the identity provider, reviewer and administrator roles, sensitive-data access matrix, audit access, encryption/key boundary, and retention requirements. Convert the approved controls into testable requirements and verification cases; keep unresolved values as `Not Found`.
- **Disposition:** Open production blocker; human approval required.

## Review Coverage

| Area | Result |
|---|---|
| Requirements and architecture scope | Finding DR-001; human decision required |
| Approval governance and traceability | Finding DR-002; approval evidence must be confirmed |
| Security and sensitive-data handling | Finding DR-003; production remains blocked |
| Reliability, failure handling, and publication gating | Architecture defines checkpoints, fail-closed behavior, idempotency, and human approval; provider-specific retry and publication choices remain human-gated |
| Requirement traceability | Architecture includes a requirement mapping; scope mismatch in DR-001 prevents treating that mapping as implementation coverage |
| Scalability and performance | Provider-neutral recommendations are documented; policy-change frequency and document volume remain `Not Found` |

## Approval

This review records analysis and recommendations only. Human approval or rejection of findings, and approval of any resulting architecture changes, is `Pending`.