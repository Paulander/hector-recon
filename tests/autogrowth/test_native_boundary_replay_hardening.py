"""Focused causal replay and versioned-boundary commitment tests."""

from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN,
    GenerationBoundary,
    GenerationPhase,
    HISTORY_VALIDATION_LEGACY,
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    StructuralMode,
)
from recon_lite_chess.autogrowth import (
    native_prospective_evidence_authority_v2 as authority_module,
)

from tests.autogrowth.test_native_authority_resource_metabolism import (
    _materialize_one_adaptive_child,
)
from tests.autogrowth.test_native_mixed_evidence_specialization import (
    _consume,
    _mixed_authority,
    _open_mint,
)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("generation", 1),
        ("phase", GenerationPhase.PROSPECTIVE_OPEN),
        ("event_frontier", 5),
        ("prior_continuation_digest", "0" * 64),
        ("accepted_real_ledger_digest", "0" * 64),
        ("request_queue_digest", "0" * 64),
        ("structural_epoch_schedule_digest", "0" * 64),
        ("candidate_manifest_digest", "0" * 64),
        ("parent_decision_history_digest", "0" * 64),
        ("specialization_genome_seed", 1),
        ("prior_digest_schema", "forged-boundary-schema"),
        ("retired_cell_ids", ("forged-cell",)),
    ),
)
def test_every_generation_boundary_field_is_reclosed_on_load(
    field: str,
    value: object,
) -> None:
    authority = _mixed_authority(AvailabilityState.AVAILABLE)
    original = authority.generation_boundaries[0]
    forged = replace(original, **{field: value})
    authority.generation_boundaries = (
        forged,
        *authority.generation_boundaries[1:],
    )

    with pytest.raises(ProspectiveV2IntegrityError):
        NativeProspectiveAuthorityV2.loads(
            authority_module.pickle.dumps(authority)
        )


def test_consumed_transaction_structure_digest_is_reclosed() -> None:
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    _opened, _emission = _consume(
        authority,
        outcome=True,
        fullmove=70,
        frame_id="boundary-replay:consumed",
    )
    token = next(iter(authority.event_transactions))
    forged = copy.deepcopy(authority)
    transaction = dict(forged.event_transactions[token])
    transaction["structure_invariant_digest"] = "0" * 64
    forged.event_transactions[token] = transaction
    # Force the causal-boundary path to be the first rejecting verifier; the
    # incremental ledger verifier also rejects this tamper, but this test is
    # specifically about the reconstructed topology commitment.
    forged._history_validation_mode = HISTORY_VALIDATION_LEGACY

    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="incremental|structure|replay|transaction",
    ):
        NativeProspectiveAuthorityV2.loads(
            authority_module.pickle.dumps(forged)
        )


def test_pending_transaction_structure_digest_is_reclosed() -> None:
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    pending, _trace, _receipt = _open_mint(
        authority,
        outcome=True,
        fullmove=71,
        frame_id="boundary-replay:pending",
    )
    forged = copy.deepcopy(authority)
    transaction = dict(forged.event_transactions[pending.pending_token])
    transaction["structure_invariant_digest"] = "0" * 64
    forged.event_transactions[pending.pending_token] = transaction
    forged._history_validation_mode = HISTORY_VALIDATION_LEGACY

    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="incremental|structure|replay|transaction",
    ):
        NativeProspectiveAuthorityV2.loads(
            authority_module.pickle.dumps(forged)
        )


@pytest.mark.parametrize("pending", (False, True))
def test_versioned_boundary_clean_load_resume_parity(
    pending: bool,
) -> None:
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    if pending:
        _open_mint(
            authority,
            outcome=True,
            fullmove=72,
            frame_id="boundary-replay:resume-pending",
        )
    else:
        _consume(
            authority,
            outcome=True,
            fullmove=72,
            frame_id="boundary-replay:resume-consumed",
        )
    assert authority.boundary_digest_schema == (
        BOUNDARY_DIGEST_SCHEMA_MUTATION_CHAIN
    )
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == authority.continuation_manifest()
    restored.verify_full_history_boundary("versioned resume parity")


def test_retirement_tombstone_state_before_is_causally_reclosed() -> None:
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    child_id = _materialize_one_adaptive_child(authority)
    authority.retire_adaptive_leaves((child_id,), reason="replay-audit")
    tombstone = copy.deepcopy(authority.retired_tombstones[child_id])
    tombstone["state_before"]["support"] += 1
    payload = authority._retirement_tombstone_payload(
        cell_id=child_id,
        state_before=tombstone["state_before"],
        state_after=tombstone["state_after"],
        retirement_generation=tombstone["retirement_generation"],
        retirement_ordinal=tombstone["retirement_ordinal"],
        retirement_reason=tombstone["retirement_reason"],
    )
    digest = authority_module._sha(payload)
    tombstone["retirement_tombstone_digest"] = digest
    authority.retired_tombstones[child_id] = tombstone
    authority.states[child_id].retirement_tombstone_digest = digest

    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="state_before|replay",
    ):
        authority.verify_full_history_boundary("tombstone causal replay")


def test_many_padded_boundaries_do_not_rescan_lifetime_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _mixed_authority(AvailabilityState.AVAILABLE)
    for _index in range(64):
        boundary = authority._generation_boundary(
            phase=authority.generation_phase,
            prior_continuation_digest=(
                authority._boundary_prior_continuation_digest()
            ),
            queue_ids=authority.sealed_request_ids,
        )
        authority._append_generation_boundary(boundary)

    refresh_calls = 0
    original_refresh = (
        NativeProspectiveAuthorityV2._refresh_hot_path_indexes
    )

    def counted_refresh(item: NativeProspectiveAuthorityV2) -> None:
        nonlocal refresh_calls
        refresh_calls += 1
        original_refresh(item)

    monkeypatch.setattr(
        NativeProspectiveAuthorityV2,
        "_refresh_hot_path_indexes",
        counted_refresh,
    )
    monkeypatch.setattr(
        NativeProspectiveAuthorityV2,
        "continuation_digest",
        lambda *_args, **_kwargs: pytest.fail(
            "flat continuation digest was rescanned during replay"
        ),
    )

    authority.verify_full_history_boundary("padded boundary replay")
    # One refresh belongs to the persisted authority's invariant boundary and
    # one to replay seed construction; neither scales with boundary count.
    assert refresh_calls == 2
    assert len(authority._boundary_request_digest_cache) <= 1


def test_structural_topology_rebuild_uses_live_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    child_id = _materialize_one_adaptive_child(authority)
    original_topology = authority_module._executed_authority_topology_manifest
    observed_sizes: list[int] = []

    def checked_topology(states):
        observed_sizes.append(len(states))
        assert all(
            not getattr(state, "retired", False)
            for state in states.values()
        )
        return original_topology(states)

    monkeypatch.setattr(
        authority_module,
        "_executed_authority_topology_manifest",
        checked_topology,
    )
    authority.retire_adaptive_leaves((child_id,), reason="topology-cache")
    assert observed_sizes
