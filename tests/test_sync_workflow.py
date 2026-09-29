import pytest

from automated_documentation_sync.workflow.checkpoint_repository import CheckpointRepository
from automated_documentation_sync.workflow.orchestrator import DuplicateRunError, SyncOrchestrator
from automated_documentation_sync.workflow.sync_states import InvalidSyncTransitionError, SyncState, is_sync_state


def test_sync_workflow_persists_canonical_states_and_supports_resume():
    repository = CheckpointRepository()
    orchestrator = SyncOrchestrator(repository)

    orchestrator.start_run("run-1", source_version_id="source-v1")
    for state in (
        SyncState.PARSED,
        SyncState.VERSIONED,
        SyncState.CHANGE_DETECTED,
        SyncState.PROPOSED,
        SyncState.AWAITING_REVIEW,
    ):
        orchestrator.transition("run-1", state, change_set_id="change-set-1", artifact_hash="hash-1")
    orchestrator._approve_after_review("run-1", artifact_hash="hash-1")
    orchestrator._publish_after_confirmation("run-1", artifact_hash="hash-1")

    resumed = SyncOrchestrator(repository).resume("run-1")
    assert resumed.state is SyncState.PUBLISHED
    assert resumed.change_set_id == "change-set-1"
    assert resumed.artifact_hash == "hash-1"


def test_direct_approval_and_publication_transitions_are_blocked():
    orchestrator = SyncOrchestrator()
    orchestrator.start_run("run-controlled")

    with pytest.raises(InvalidSyncTransitionError, match="controlled workflow"):
        orchestrator.transition("run-controlled", SyncState.APPROVED)
    with pytest.raises(InvalidSyncTransitionError, match="controlled workflow"):
        orchestrator.transition("run-controlled", SyncState.PUBLISHED)


def test_checkpoint_history_retains_each_transition():
    orchestrator = SyncOrchestrator()
    orchestrator.start_run("run-history")
    orchestrator.transition("run-history", SyncState.PARSED)

    history = orchestrator.repository.history("run-history")

    assert tuple(checkpoint.state for checkpoint in history) == (SyncState.INGESTED, SyncState.PARSED)


def test_sync_workflow_rejects_invalid_transitions_and_duplicate_runs():
    orchestrator = SyncOrchestrator()
    orchestrator.start_run("run-1")

    with pytest.raises(InvalidSyncTransitionError):
        orchestrator.transition("run-1", SyncState.APPROVED)

    with pytest.raises(DuplicateRunError):
        orchestrator.start_run("run-1")


def test_sync_failure_is_terminal_and_overtime_namespace_stays_separate():
    orchestrator = SyncOrchestrator()
    orchestrator.start_run("run-failed")
    failed = orchestrator.transition("run-failed", SyncState.FAILED)

    assert failed.state.value == "SYNC_FAILED"
    assert is_sync_state("SYNC_FAILED") is True
    assert is_sync_state("FAILED") is False
    with pytest.raises(InvalidSyncTransitionError):
        orchestrator.transition("run-failed", SyncState.INGESTED)