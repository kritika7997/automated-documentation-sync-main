# Implementation Plan

## Plan Scope and Governance

This plan implements the approved Automated Documentation Sync architecture and requirements only. It creates a documentation-control pipeline for policy ingestion, parsing, versioning, change detection, requirements synchronization, documentation generation, human review, and controlled publication.

The plan does not implement payroll execution, payment processing, payment confirmation, or policy-level exception approval. Payment SLA, payment confirmation evidence, policy-exception authority, retention/deletion policy, backup/recovery objectives, authoritative repositories, identity-provider choices, and provider-specific deployment choices remain `Not Found` or require human approval.

Requirements approval and architecture/design approval are already complete. Documentation synchronization approval and final publication approval remain mandatory per synchronization run.

## Dependency and Status Conventions

- A task is **Blocked by** an external or human decision when implementation cannot be finalized without it.
- A task marked **Parallelizable: Yes** may run concurrently after its listed dependencies complete.
- `SYNC_*` statuses belong to documentation synchronization. `OVERTIME_*` statuses belong to the separate overtime workflow and must not be mapped directly.
- Every task must preserve source provenance, requirement classification, `Not Found` values, conflict records, and approval evidence.

## Phase 1 — Project Foundation

### T01 — Establish Repository and Service Skeleton

- **Task ID:** T01
- **Task name:** Establish repository and service skeleton
- **Description:** Create the implementation workspace layout for API, domain services, persistence, workers, review UI, tests, configuration, and deployment documentation. Do not add business behavior.
- **Phase:** 1
- **Dependencies:** None
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-033, FR-036, FR-037
- **Related NFR-XXX requirements:** NFR-001, NFR-005
- **Architecture component:** Workflow API and Review UI; Requirements Synchronizer
- **Expected files/modules:** `src/`, `tests/`, `config/`, `docs/`, `pyproject.toml`, `README.md`
- **Required tests:** Project import/boot smoke test; test discovery check.
- **Acceptance condition:** Empty service skeleton starts and test runner discovers the test suites.

### T02 — Define Domain Identifiers and Classification Types

- **Task ID:** T02
- **Task name:** Define domain identifiers and classifications
- **Description:** Define typed representations for `FR-XXX`, `NFR-XXX`, `BR-XXX`, policy versions, source locations, classifications, `Not Found`, Out of Scope, conflict records, change sets, and review decisions.
- **Phase:** 1
- **Dependencies:** T01
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-002, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-005
- **Architecture component:** Policy Canonical Model; Requirements Synchronizer
- **Expected files/modules:** `src/domain/models.py`, `src/domain/classifications.py`, `src/domain/identifiers.py`
- **Required tests:** Identifier validation; one-primary-classification validation; explicit `Not Found` representation; Out of Scope representation.
- **Acceptance condition:** Domain types reject invalid identifiers and prevent a requirement from having multiple primary classifications.

### T03 — Define Configuration Contract and Environment Matrix

- **Task ID:** T03
- **Task name:** Define configuration contract
- **Description:** Document configuration keys and validation boundaries for project calendar, weekly start/end boundaries, time zone, working hours, source repository, documentation repository, identity, storage, and integrations. Record unresolved provider choices as `Not Found`.
- **Phase:** 1
- **Dependencies:** T01
- **Blocked by:** Authoritative policy repository, documentation repository, identity provider, and deployment provider choices.
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-006, FR-007, FR-008, FR-009, FR-033
- **Related NFR-XXX requirements:** NFR-002, NFR-004
- **Architecture component:** Configuration and Validation Service
- **Expected files/modules:** `src/config/schema.py`, `config/example.env`, `docs/configuration.md`
- **Required tests:** Missing and invalid configuration tests; no-default behavior tests.
- **Acceptance condition:** The contract distinguishes valid, invalid, and `Not Found` configuration without defining unapproved defaults.

### T04 — Define Persistence Schema and Migration Baseline

- **Task ID:** T04
- **Task name:** Define persistence schema
- **Description:** Design schemas and migrations for policy documents, versions, statements, FAQ entries, source locations, clarification decisions, requirements, links, conflicts, change sets, review decisions, publication artifacts, workflow events, project configuration, and audit events.
- **Phase:** 1
- **Dependencies:** T02
- **Blocked by:** Retention/deletion policy and backup/recovery objectives are `Not Found`; schema can proceed, lifecycle policy cannot be finalized.
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-001, FR-002, FR-016, FR-033, FR-037, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-004
- **Architecture component:** Document Object Store; Storage; Synchronization Checkpoint Store
- **Expected files/modules:** `src/storage/models.py`, `migrations/`, `src/storage/repositories.py`
- **Required tests:** Migration creation; uniqueness for immutable versions and artifacts; explicit `Not Found` storage tests.
- **Acceptance condition:** Schema supports immutable source/artifact records, provenance, checkpoints, approval evidence, and conflict records.

### T05 — Establish Test Fixtures and Quality Gates

- **Task ID:** T05
- **Task name:** Establish test fixtures and quality gates
- **Description:** Add fixture conventions for supplied MHTML/HTML policy exports, empty documents, malformed packages, conflicting formulas/contacts, and representative requirements. Configure formatting, linting, typing, and test commands without implementing production behavior.
- **Phase:** 1
- **Dependencies:** T01
- **Blocked by:** None
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-002, FR-006, FR-008, FR-009, FR-020, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-003, NFR-004, NFR-005
- **Architecture component:** Technology Recommendations; Reliability
- **Expected files/modules:** `tests/fixtures/`, `tests/conftest.py`, CI configuration, `docs/testing.md`
- **Required tests:** Fixture loading and quality-gate smoke tests.
- **Acceptance condition:** Repeatable local validation exists for later phases.

## Phase 2 — Source Document Ingestion

### T06 — Implement Policy Source Adapter Contract

- **Task ID:** T06
- **Task name:** Implement source adapter contract
- **Description:** Implement the adapter interface for retrieving the approved Overtime Compensation Policy document from the designated GitHub repository and configured repository event/workflow trigger. Capture source metadata, media type, source identifier, timestamps, commit/version metadata, and attachment relationships. Preserve original bytes before parsing.
- **Phase:** 2
- **Dependencies:** T02, T04
- **Blocked by:** None. Human-approved architecture decision designates a GitHub repository and repository event/workflow trigger as authoritative.
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-002
- **Related NFR-XXX requirements:** NFR-001, NFR-002
- **Architecture component:** Policy Source Adapter
- **Expected files/modules:** `src/ingestion/source_adapter.py`, `src/ingestion/contracts.py`, `src/ingestion/github_source_adapter.py`
- **Required tests:** Accepted package metadata; unsupported media type; duplicate source; byte-preservation tests.
- **Acceptance condition:** Every accepted input is stored immutably with source metadata and content hash.

### T07 — Implement MIME/MHTML Capture and Attachment Extraction

- **Task ID:** T07
- **Task name:** Capture MHTML and attachments
- **Description:** Decode MIME boundaries and quoted-printable content, extract the HTML body and embedded resources, and preserve unresolved references and attachment metadata.
- **Phase:** 2
- **Dependencies:** T06
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-002
- **Related NFR-XXX requirements:** NFR-001, NFR-002
- **Architecture component:** Policy Source Adapter; Document Object Store
- **Expected files/modules:** `src/ingestion/mhtml_reader.py`, `src/ingestion/attachments.py`
- **Required tests:** Supplied export fixture; quoted-printable decoding; embedded image extraction; malformed MIME tests.
- **Acceptance condition:** Raw package, body, attachments, hashes, and unresolved references are retained without silent loss.

### T08 — Implement Empty and Invalid Document Gate

- **Task ID:** T08
- **Task name:** Gate empty and invalid documents
- **Description:** Detect empty/contentless and malformed policy documents, preserve the original input for audit, mark it invalid, block synchronization, require human review, and generate no documentation update.
- **Phase:** 2
- **Dependencies:** T04, T07
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-002
- **Related NFR-XXX requirements:** NFR-001, NFR-002
- **Architecture component:** Policy Source Adapter; Policy Document Ingestion; Synchronization Checkpoint Store
- **Expected files/modules:** `src/ingestion/validation.py`, `src/workflow/checkpoints.py`
- **Required tests:** Empty body; whitespace-only body; invalid package; audit preservation; no-generator-invocation tests.
- **Acceptance condition:** Empty or invalid input cannot advance to synchronization proposal and is recorded as `SYNC_FAILED` with review required.

## Phase 3 — Policy Parsing and Canonical Model

### T09 — Implement Structured Policy Parser

- **Task ID:** T09
- **Task name:** Parse policy structure
- **Description:** Extract headings, paragraphs, lists, tables, effective dates, version rows, links, email addresses, attachments, and source locations using structured MIME/HTML parsing.
- **Phase:** 3
- **Dependencies:** T07, T02
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-002, FR-017, FR-024, FR-030, FR-034, FR-035
- **Related NFR-XXX requirements:** NFR-001, NFR-005
- **Architecture component:** Policy Parser
- **Expected files/modules:** `src/parsing/policy_parser.py`, `src/parsing/source_location.py`
- **Required tests:** Section/list/table extraction; source location tests; effective-date extraction; link/email extraction.
- **Acceptance condition:** Parser returns structured records linked to exact source locations and raw text.

### T10 — Implement FAQ Extraction

- **Task ID:** T10
- **Task name:** Extract FAQ entries
- **Description:** Extract FAQ question/answer pairs separately from policy sections, preserving FAQ classification and source locations.
- **Phase:** 3
- **Dependencies:** T09
- **Blocked by:** None
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-003, FR-026, FR-027, FR-028, FR-035, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-005
- **Architecture component:** Policy Parser; Policy Canonical Model
- **Expected files/modules:** `src/parsing/faq_parser.py`, `src/domain/faq.py`
- **Required tests:** FAQ pair extraction; incomplete FAQ handling; FAQ-only 6-hour threshold; conflicting contact extraction.
- **Acceptance condition:** FAQ content is distinguishable from Source Policy content and retains provenance.

### T11 — Build Canonical Policy Representation

- **Task ID:** T11
- **Task name:** Build canonical policy model
- **Description:** Persist normalized statements, FAQ entries, tables, formulas, thresholds, contacts, dates, attachments, classifications, source locations, hashes, and conflict flags while retaining raw text.
- **Phase:** 3
- **Dependencies:** T09, T10, T04
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-002, FR-017, FR-018, FR-024, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-005
- **Architecture component:** Policy Canonical Model
- **Expected files/modules:** `src/domain/policy_model.py`, `src/storage/policy_repository.py`
- **Required tests:** Round-trip persistence; classification; raw/normalized preservation; source-location integrity.
- **Acceptance condition:** Canonical records preserve policy, FAQ, raw content, normalized content, and provenance separately.

### T12 — Register Human Clarification Records

- **Task ID:** T12
- **Task name:** Register clarification records
- **Description:** Define storage and loading of the 17 approved clarification decisions as separate authority records with scope, approval evidence, version, and applicable requirements. Do not merge them into source policy text.
- **Phase:** 3
- **Dependencies:** T02, T04
- **Blocked by:** Human-approved clarification records are available as approved input; no new clarification may be inferred.
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-003 through FR-015, FR-018 through FR-023, FR-025 through FR-029, FR-031, FR-032, FR-035, FR-036 through FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-005
- **Architecture component:** Policy Canonical Model; Requirements Synchronizer
- **Expected files/modules:** `src/domain/clarifications.py`, `src/storage/clarification_repository.py`
- **Required tests:** Decision identity/version tests; separation from source records; approval-evidence tests.
- **Acceptance condition:** Approved clarifications are independently traceable and authoritative only within their approved scope.

## Phase 4 — Versioning and Change Detection

### T13 — Implement Immutable Policy Version Registry

- **Task ID:** T13
- **Task name:** Implement policy version registry
- **Description:** Create immutable policy versions with source hash, parser version, received timestamp, effective date when present, and predecessor/supersession relationships.
- **Phase:** 4
- **Dependencies:** T11, T04
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-002
- **Related NFR-XXX requirements:** NFR-001, NFR-002
- **Architecture component:** Version Registry
- **Expected files/modules:** `src/versioning/version_registry.py`, `src/storage/version_repository.py`
- **Required tests:** Immutable version tests; duplicate hash handling; predecessor linkage; effective-date preservation.
- **Acceptance condition:** Existing versions cannot be overwritten and every generated artifact can identify its source version.

### T14 — Implement Statement-Level Change Detection

- **Task ID:** T14
- **Task name:** Detect policy changes
- **Description:** Compare statements, tables, FAQ pairs, formulas, thresholds, contacts, dates, and structure; distinguish formatting-only changes from substantive changes where configured.
- **Phase:** 4
- **Dependencies:** T13, T11
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-017, FR-018, FR-025 through FR-032, FR-034, FR-035, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-005
- **Architecture component:** Change Detection Engine
- **Expected files/modules:** `src/changes/detector.py`, `src/changes/comparators.py`
- **Required tests:** Add/remove/modify tests; table/FAQ comparison; numeric/contact change tests; formatting-only test.
- **Acceptance condition:** Each change has old/new values, source locations, classifications, and affected requirement identifiers.

### T15 — Implement Conflict and Ambiguity Detection

- **Task ID:** T15
- **Task name:** Detect conflicts and ambiguity
- **Description:** Preserve conflicting formulas, thresholds, contacts, and low-confidence parser/change results; flag them and require explicit human review outcomes.
- **Phase:** 4
- **Dependencies:** T14, T11, T12
- **Blocked by:** None
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-018, FR-026 through FR-029, FR-035, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-005
- **Architecture component:** Change Detection Engine; Conflict Record
- **Expected files/modules:** `src/changes/conflicts.py`, `src/changes/confidence.py`
- **Required tests:** Formula conflict; contact conflict; FAQ/policy conflict; low-confidence hold; no-silent-resolution tests.
- **Acceptance condition:** No ambiguous or conflicting change becomes authoritative or final without an explicit review outcome.

## Phase 5 — Requirements Synchronization

### T16 — Implement Requirements Catalog and Linkage

- **Task ID:** T16
- **Task name:** Implement requirements catalog linkage
- **Description:** Load finalized requirements, validate stable FR/NFR/BR identifiers and primary classifications, and create source-statement-to-requirement links.
- **Phase:** 5
- **Dependencies:** T02, T04, T11, T12
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-002, FR-003, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-005
- **Architecture component:** Requirements Synchronizer
- **Expected files/modules:** `src/sync/requirements_catalog.py`, `src/sync/traceability.py`
- **Required tests:** Catalog parsing; identifier uniqueness; one-primary-classification validation; source-link persistence.
- **Acceptance condition:** Every synchronized requirement has stable identity, classification, and provenance links.

### T17 — Implement Configuration and Required-Input Validation

- **Task ID:** T17
- **Task name:** Validate configuration and inputs
- **Description:** Validate project calendar, weekly boundaries, time zone, working hours, associate identifier, project code, overtime date, overtime hours, approval evidence, and other required captured inputs. Missing values become `Not Found` where applicable and block the affected operation.
- **Phase:** 5
- **Dependencies:** T03, T16
- **Blocked by:** Project-specific configuration values are external inputs; missing values intentionally block affected processing.
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-001, FR-002, FR-006 through FR-011, FR-016, FR-020
- **Related NFR-XXX requirements:** NFR-002, NFR-004
- **Architecture component:** Configuration and Validation Service
- **Expected files/modules:** `src/validation/configuration.py`, `src/validation/required_inputs.py`
- **Required tests:** Missing calendar/week/time-zone tests; working-hours 8/9/other/missing tests; missing-field tests; no-default tests.
- **Acceptance condition:** Invalid/missing configuration or required input blocks only the affected operation and never fabricates a value.

### T18 — Implement Synchronization Change-Set Builder

- **Task ID:** T18
- **Task name:** Build synchronization change sets
- **Description:** Convert approved source changes and clarification impacts into proposed documentation change sets, preserving classifications, conflicts, `Not Found`, Out of Scope, affected requirements, and source locations.
- **Phase:** 5
- **Dependencies:** T14, T15, T16, T17
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001 through FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-005
- **Architecture component:** Requirements Synchronizer; Synchronization Checkpoint Store
- **Expected files/modules:** `src/sync/change_sets.py`, `src/sync/synchronizer.py`
- **Required tests:** Impact mapping; clarification precedence; conflict retention; `Not Found` preservation; Out of Scope preservation.
- **Acceptance condition:** A change set is reproducible from source version, clarification version, requirements version, and configuration snapshot.

## Phase 6 — Documentation Generation

### T19 — Implement Documentation Template and Renderer

- **Task ID:** T19
- **Task name:** Render documentation proposals
- **Description:** Generate proposed requirements and related documentation updates from change sets, preserving stable identifiers, classifications, source links, clarification references, and unresolved items.
- **Phase:** 6
- **Dependencies:** T18
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001, FR-002, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-005
- **Architecture component:** Documentation Generator
- **Expected files/modules:** `src/generation/templates/`, `src/generation/renderer.py`
- **Required tests:** Deterministic rendering; stable identifiers; classification rendering; conflict and `Not Found` rendering.
- **Acceptance condition:** Generated output is a proposal and contains complete provenance and change-set references.

### T20 — Implement Artifact Hashing and Review Snapshot

- **Task ID:** T20
- **Task name:** Hash artifacts and snapshots
- **Description:** Produce immutable generated artifact bytes/snapshots and content hashes before review; associate hashes with the change set and source/clarification versions.
- **Phase:** 6
- **Dependencies:** T19, T04
- **Blocked by:** None
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-016, FR-033, FR-037
- **Related NFR-XXX requirements:** NFR-001, NFR-003
- **Architecture component:** Documentation Generator; Storage; PublicationArtifact
- **Expected files/modules:** `src/generation/artifacts.py`, `src/storage/artifact_repository.py`
- **Required tests:** Deterministic hash; changed-content hash; artifact immutability; hash/change-set linkage.
- **Acceptance condition:** Review and publication always operate on the exact hashed artifact under review.

## Phase 7 — Human Review and Approval

### T21 — Implement SYNC Workflow and Checkpoints

- **Task ID:** T21
- **Task name:** Implement synchronization workflow
- **Description:** Implement canonical `SYNC_INGESTED`, `SYNC_PARSED`, `SYNC_VERSIONED`, `SYNC_CHANGE_DETECTED`, `SYNC_PROPOSED`, `SYNC_AWAITING_REVIEW`, `SYNC_APPROVED`, `SYNC_PUBLISHED`, and `SYNC_FAILED` states with persisted transitions and checkpoint records.
- **Phase:** 7
- **Dependencies:** T04, T08, T13, T18, T20
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-033, FR-036 through FR-038
- **Related NFR-XXX requirements:** NFR-001, NFR-002
- **Architecture component:** Synchronization Checkpoint Store; Workflow API and Review UI
- **Expected files/modules:** `src/workflow/sync_states.py`, `src/workflow/orchestrator.py`, `src/workflow/checkpoint_repository.py`
- **Required tests:** Valid/invalid transitions; checkpoint persistence; restart/resume; duplicate-run tests; separate `OVERTIME_*` namespace tests.
- **Acceptance condition:** Every run has one canonical SYNC state and never uses duplicate unprefixed synchronization states.

### T22 — Implement Review Interface and Evidence Capture

- **Task ID:** T22
- **Task name:** Implement human review interface
- **Description:** Present source differences, generated proposals, conflicts, `Not Found` items, Out of Scope dispositions, and traceability. Capture reviewer identity, decision, timestamp, evidence/reference, rationale where provided, source version, clarification version, and artifact hash.
- **Phase:** 7
- **Dependencies:** T21, T20
- **Blocked by:** Identity provider and reviewer authorization model are `Not Found` and require human approval.
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-016, FR-033, FR-036 through FR-038
- **Related NFR-XXX requirements:** NFR-001, NFR-004, NFR-005
- **Architecture component:** Human Review and Approval Service; Workflow API and Review UI
- **Expected files/modules:** `src/review/service.py`, `src/review/api.py`, `ui/review/`, `src/review/evidence.py`
- **Required tests:** Proposal display; conflict display; approval/rejection/return evidence; unauthorized reviewer test; artifact hash display.
- **Acceptance condition:** A proposal cannot become `SYNC_APPROVED` without valid human review evidence.

### T23 — Enforce Unresolved-Change Review Gate

- **Task ID:** T23
- **Task name:** Enforce unresolved-change gate
- **Description:** Prevent approval/finalization while any ambiguous, low-confidence, conflicting, or unresolved `Not Found` change lacks an explicit review outcome.
- **Phase:** 7
- **Dependencies:** T15, T21, T22
- **Blocked by:** None
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-002, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-005
- **Architecture component:** Human Review and Approval Service; Change Detection Engine
- **Expected files/modules:** `src/review/gates.py`, `src/workflow/approval_policy.py`
- **Required tests:** Unresolved conflict block; unresolved `Not Found` block; explicit resolution pass; no-silent-resolution tests.
- **Acceptance condition:** Every unresolved item has an explicit outcome before `SYNC_APPROVED` is permitted.

## Phase 8 — Controlled Git/Documentation Publication

### T24 — Implement Provider-Neutral Publication Contract

- **Task ID:** T24
- **Task name:** Define controlled publication contract
- **Description:** Define the provider-neutral publication interface for protected branch/change-set and pull request/equivalent review object, without selecting a Git provider.
- **Phase:** 8
- **Dependencies:** T20, T21, T22
- **Blocked by:** Documentation repository, Git provider, and protected mechanism are pending human approval.
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-033, FR-037, FR-038
- **Related NFR-XXX requirements:** NFR-001, NFR-004
- **Architecture component:** Documentation Publication Adapter
- **Expected files/modules:** `src/publication/contracts.py`, `src/publication/provider_interface.py`
- **Required tests:** Contract validation; unsupported-provider behavior; no-publication-without-approval tests.
- **Acceptance condition:** Publication can be integrated without assuming an unapproved provider.

### T25 — Implement Publication Artifact and Approval Verification

- **Task ID:** T25
- **Task name:** Verify publication authorization
- **Description:** Require an approved change-set identifier and verify approval existence, valid approval evidence, reviewer identity/authorization, artifact hash match, and publication idempotency before any repository write.
- **Phase:** 8
- **Dependencies:** T20, T22, T24
- **Blocked by:** Identity/authorization provider and protected repository mechanism require human approval.
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-016, FR-033, FR-037, FR-038
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-004
- **Architecture component:** Documentation Publication Adapter; PublicationArtifact
- **Expected files/modules:** `src/publication/authorization.py`, `src/publication/artifact_verifier.py`, `src/publication/idempotency.py`
- **Required tests:** Missing approval; invalid evidence; invalid reviewer authorization; hash mismatch; duplicate publication; direct-unapproved-publication denial.
- **Acceptance condition:** No publication call reaches the repository unless every verification succeeds.

### T26 — Implement Protected Repository Publication

- **Task ID:** T26
- **Task name:** Publish approved change sets
- **Description:** Publish the approved artifact through the selected protected branch/change-set and pull request/equivalent mechanism, then record `SYNC_PUBLISHED` only after publication confirmation from that repository mechanism.
- **Phase:** 8
- **Dependencies:** T25, T27
- **Blocked by:** Documentation repository and provider-specific protected publication mechanism are `Not Found` pending human approval.
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-033, FR-037, FR-038
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-004
- **Architecture component:** Documentation Publication Adapter; Documentation Repository Integration
- **Expected files/modules:** `src/publication/adapter.py`, `src/publication/repository_client.py`
- **Required tests:** Provider-contract integration test; protected publication test; publication failure; no false `SYNC_PUBLISHED` test.
- **Acceptance condition:** Only an approved, hash-matched artifact is published and publication state is recorded accurately.

### T27 — Obtain Publication Mechanism Approval

- **Task ID:** T27
- **Task name:** Approve publication mechanism
- **Description:** Select and approve the authoritative documentation repository, protected branch/change-set mechanism, pull request/equivalent review object, and publication credentials boundary.
- **Phase:** 8
- **Dependencies:** T03, T24
- **Blocked by:** Human approval required; cannot be resolved from requirements or architecture alone.
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-033, FR-037, FR-038
- **Related NFR-XXX requirements:** NFR-004
- **Architecture component:** Documentation Publication Adapter; Items Requiring Human Approval
- **Expected files/modules:** `docs/decisions/publication-mechanism.md`, deployment configuration placeholders
- **Required tests:** Approval-record completeness check; provider configuration validation after decision.
- **Acceptance condition:** Human approval is recorded before T26 is unblocked.

## Phase 9 — Audit, Observability and Reliability

### T28 — Implement Append-Only Audit Trail

- **Task ID:** T28
- **Task name:** Implement audit trail
- **Description:** Record immutable events for ingestion, parsing, versioning, change detection, synchronization, review, approval, generation, publication, errors, retries, and checkpoint transitions.
- **Phase:** 9
- **Dependencies:** T04, T13, T21, T22, T25
- **Blocked by:** Audit retention period and deletion policy are `Not Found`.
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-016, FR-033, FR-037
- **Related NFR-XXX requirements:** NFR-001, NFR-004
- **Architecture component:** Audit Trail Service
- **Expected files/modules:** `src/audit/events.py`, `src/audit/service.py`, `src/storage/audit_repository.py`
- **Required tests:** Append-only behavior; event completeness; actor/timestamp/hash linkage; tamper-evidence tests.
- **Acceptance condition:** Every material state change and artifact has an auditable event with provenance.

### T29 — Implement Observability and Notifications

- **Task ID:** T29
- **Task name:** Implement observability and notifications
- **Description:** Add structured logs, metrics, traces, correlation identifiers, parser warnings, blocked-run notifications, review notifications, and error notifications without making policy decisions.
- **Phase:** 9
- **Dependencies:** T21, T28
- **Blocked by:** Notification provider is not selected; provider choice is an architecture recommendation requiring human approval.
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-033, FR-037
- **Related NFR-XXX requirements:** NFR-001, NFR-002
- **Architecture component:** Notification Adapter; Workflow API and Review UI
- **Expected files/modules:** `src/observability/`, `src/notifications/adapter.py`
- **Required tests:** Correlation propagation; blocked-run notification; notification failure isolation; no-policy-decision test.
- **Acceptance condition:** Operators can identify each run, warning, failure, and review state without exposing sensitive content.

### T30 — Implement Retry, Idempotency, and Recovery

- **Task ID:** T30
- **Task name:** Implement retry and recovery
- **Description:** Add bounded retries for transient storage/notification/repository failures, checkpoint resume, preserved earlier state, duplicate-publication prevention, and explicit failed-run handling.
- **Phase:** 9
- **Dependencies:** T21, T25, T28
- **Blocked by:** Backup/recovery objectives are `Not Found`; retry policy details are architecture recommendations requiring approval.
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-033, FR-037, FR-038
- **Related NFR-XXX requirements:** NFR-001, NFR-002
- **Architecture component:** Synchronization Checkpoint Store; Reliability
- **Expected files/modules:** `src/reliability/retry.py`, `src/reliability/recovery.py`, `src/workflow/resume.py`
- **Required tests:** Failure at every checkpoint; resume; duplicate retry; partial publication; no-success-on-failure tests.
- **Acceptance condition:** Later-stage failure never falsely finalizes a run, and safe resume is idempotent.

### T31 — Implement Security and Authorization Controls

- **Task ID:** T31
- **Task name:** Implement security controls
- **Description:** Implement authentication integration boundaries, least-privilege authorization checks, encryption configuration, secret-store interfaces, parser isolation, untrusted-link handling, and sensitive-data access auditing without selecting unapproved providers or roles.
- **Phase:** 9
- **Dependencies:** T03, T22, T25, T28
- **Blocked by:** Identity provider, reviewer roles, access-control model, retention, and deletion policy are `Not Found` and require human approval.
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-016, FR-033, FR-037
- **Related NFR-XXX requirements:** NFR-001, NFR-004
- **Architecture component:** Security; Human Review and Approval Service; Documentation Publication Adapter
- **Expected files/modules:** `src/security/auth.py`, `src/security/authorization.py`, `src/security/secrets.py`, `src/security/sanitization.py`
- **Required tests:** Unauthenticated access; unauthorized publication; least-privilege matrix once approved; secret non-persistence; sensitive-data logging tests.
- **Acceptance condition:** Approval and publication boundaries enforce authorization and sensitive content is not exposed through logs or artifacts.

## Phase 10 — Testing and Verification

### T32 — Unit-Test Ingestion and Parsing

- **Task ID:** T32
- **Task name:** Unit-test ingestion and parsing
- **Description:** Complete unit coverage for MHTML capture, raw preservation, attachments, empty/invalid documents, policy parsing, FAQ extraction, source locations, and parser warnings.
- **Phase:** 10
- **Dependencies:** T07, T08, T09, T10, T11
- **Blocked by:** None
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-001, FR-002, FR-006, FR-017, FR-024, FR-034, FR-035, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-005
- **Architecture component:** Policy Source Adapter; Policy Parser; Canonical Policy Model
- **Expected files/modules:** `tests/unit/ingestion/`, `tests/unit/parsing/`, `tests/unit/domain/`
- **Required tests:** Happy path, missing attachments, malformed package, empty document, conflicting content, FAQ-only content.
- **Acceptance condition:** All ingestion/parser acceptance conditions are executable and passing.

### T33 — Unit-Test Versioning and Change Detection

- **Task ID:** T33
- **Task name:** Unit-test versions and changes
- **Description:** Test immutable versioning, predecessor relationships, semantic changes, conflicts, ambiguity, confidence warnings, and affected-requirement mapping.
- **Phase:** 10
- **Dependencies:** T13, T14, T15, T16
- **Blocked by:** None
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-017, FR-018, FR-025 through FR-029, FR-035, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-005
- **Architecture component:** Version Registry; Change Detection Engine
- **Expected files/modules:** `tests/unit/versioning/`, `tests/unit/changes/`
- **Required tests:** Formula/contact/threshold conflicts; formatting-only changes; low-confidence changes; immutable-version tests.
- **Acceptance condition:** Change detection produces complete, classified, provenance-linked change records.

### T34 — Unit-Test Synchronization and Generation

- **Task ID:** T34
- **Task name:** Unit-test synchronization and generation
- **Description:** Test clarification precedence, stable requirement identifiers, primary classifications, `Not Found`, Out of Scope, traceability, deterministic rendering, and artifact hashing.
- **Phase:** 10
- **Dependencies:** T12, T18, T19, T20
- **Blocked by:** None
- **Parallelizable:** Yes
- **Related FR-XXX requirements:** FR-001 through FR-005, FR-016, FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-003, NFR-005
- **Architecture component:** Requirements Synchronizer; Documentation Generator
- **Expected files/modules:** `tests/unit/sync/`, `tests/unit/generation/`
- **Required tests:** Stable-ID test; one-classification test; source-to-requirement traceability; conflict/Not Found rendering; hash determinism.
- **Acceptance condition:** Generated documentation is reproducible and fully traceable.

### T35 — Integration-Test Workflow and Publication Gates

- **Task ID:** T35
- **Task name:** Integration-test workflow gates
- **Description:** Test the full workflow through human review, approval evidence, checkpoint persistence, publication verification, protected publication contract, and separate status namespaces using provider-neutral fakes.
- **Phase:** 10
- **Dependencies:** T21, T22, T23, T24, T25, T28, T30
- **Blocked by:** Provider-specific publication integration is blocked until T27; provider-neutral tests can proceed.
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-016, FR-033, FR-036 through FR-039
- **Related NFR-XXX requirements:** NFR-001, NFR-002, NFR-004, NFR-005
- **Architecture component:** Human Review and Approval Service; Documentation Publication Adapter; Audit Trail Service
- **Expected files/modules:** `tests/integration/workflow/`, `tests/integration/publication/`, `tests/fakes/`
- **Required tests:** Approval bypass denial; invalid evidence/hash; unresolved-change block; retry/resume; duplicate publication; audit completeness.
- **Acceptance condition:** No provider-neutral integration test permits unapproved or hash-mismatched publication.

### T36 — End-to-End Verification and Requirements Coverage

- **Task ID:** T36
- **Task name:** Verify end-to-end coverage
- **Description:** Run end-to-end fixtures from policy input through parsing, versioning, change detection, synchronization, generated proposal, human approval simulation, controlled publication simulation, audit, and recovery. Produce a requirement coverage report.
- **Phase:** 10
- **Dependencies:** T32, T33, T34, T35
- **Blocked by:** Production provider, identity, repository, retention, and recovery decisions remain human-gated; use approved test doubles until resolved.
- **Parallelizable:** No
- **Related FR-XXX requirements:** FR-001 through FR-039
- **Related NFR-XXX requirements:** NFR-001 through NFR-005
- **Architecture component:** All components; Verification
- **Expected files/modules:** `tests/e2e/`, `reports/requirements-coverage.md`, `docs/release-readiness.md`
- **Required tests:** Happy path; empty/invalid policy; conflicts; missing configuration; missing required input; approval gate; publication failure; partial-run recovery; status separation.
- **Acceptance condition:** Every FR/NFR has passing implementation/test evidence or is explicitly reported as blocked by `Not Found`/human approval.

## Parallel Work Summary

The following tracks can run in parallel after their dependencies complete:

- T03, T04, and T05 after T01/T02 as applicable.
- T10 alongside parser-model refinement after T09.
- T12 alongside T09/T10 after the domain and persistence baseline.
- T15 alongside version/change implementation after T14 inputs exist.
- T17 alongside synchronization-catalog work after T16.
- T20 alongside review UI preparation after T19.
- T22 alongside audit model preparation after T21/T20.
- T28, T29, and T31 can run in parallel after their listed workflow/storage dependencies.
- T32, T33, and T34 can run in parallel after their implementation slices complete.

No task may bypass T23, T25, or T27 before publication integration is considered complete.

## Human Approval Gates

1. **Requirements approval:** Already completed; requirements.md is the authoritative approved requirements source.
2. **Architecture/design approval:** Already completed; architecture.md is the authoritative approved architecture source.
3. **Documentation synchronization review:** Required for every generated change set before `SYNC_APPROVED`.
4. **Final publication approval:** Required before `SYNC_PUBLISHED`; publication must verify approval evidence, reviewer authorization, and artifact hash.
5. **Provider and operational approval:** Required for source repository, identity provider, documentation repository, protected publication mechanism, retention/deletion, backup/recovery, and notification provider choices.

## Blocked and Not Found Dependencies

- T03, T06, and T27: authoritative policy source/repository and ingestion trigger are `Not Found`.
- T22, T25, and T31: identity provider, reviewer roles, and authorization model are `Not Found` pending human approval.
- T24, T26, and T27: documentation repository, Git provider, protected mechanism, and publication credentials boundary require human approval.
- T28 and T30: retention/deletion and backup/recovery objectives are `Not Found`.
- T29: notification provider is an architecture recommendation pending human approval.
- T26 and T35/T36 production integration: provider-specific publication is blocked until the publication mechanism is approved.
- No task may implement or infer payment SLA, payment confirmation evidence, or policy-exception authority.

## Requirements Coverage Validation

- **FR-001 to FR-005:** T02, T06, T16, T17, T18, T19, T32, T34, T36.
- **FR-006 to FR-011:** T03, T08, T17, T32, T36.
- **FR-012 to FR-016:** T12, T16, T22, T23, T25, T28, T35, T36.
- **FR-017 to FR-024:** T09, T11, T14, T18, T19, T20, T33, T34, T36.
- **FR-025 to FR-030:** T09, T10, T14, T15, T18, T19, T33, T34, T36.
- **FR-031 to FR-035:** T09, T10, T14, T17, T18, T22, T26, T32, T35, T36.
- **FR-036 to FR-039:** T02, T12, T21, T22, T23, T25, T28, T30, T35, T36.
- **NFR-001:** T04, T11, T13, T16, T20, T21, T22, T28, T30, T32-T36.
- **NFR-002:** T03, T08, T17, T21, T23, T30, T32, T35, T36.
- **NFR-003:** T20, T34, T36.
- **NFR-004:** T03, T22, T25, T28, T31, T35, T36.
- **NFR-005:** T02, T11, T12, T16, T18, T19, T22, T23, T33, T34, T36.

## Dependency Validation

- **Circular dependencies:** None in the dependency graph. The empty-document gate T08 uses the persistence baseline and ingestion output without depending on later change detection or the full workflow orchestrator.
- **Critical dependency chain:** T01 → T02/T04 → T06/T07 → T09/T10/T11 → T13/T14/T15 → T16/T17/T18 → T19/T20 → T21/T22/T23 → T24/T25 → T27 → T26 → T28/T30 → T35/T36.
- **Publication gate:** T26 is blocked until T25 verification succeeds and T27 human approval is recorded.
- **Human-review gate:** T23 blocks `SYNC_APPROVED` until all unresolved items have explicit outcomes.
- **No production code written:** This document is an implementation plan only; no production code is created by the plan.
