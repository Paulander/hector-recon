"""Hot-path regression tests for the native V2 authority transaction."""

from __future__ import annotations

import copy
from dataclasses import replace

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    _v2_r0_available,
)
from recon_lite_chess.autogrowth import (
    native_prospective_evidence_authority_v2 as authority_module,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    MIN_SUPPORT,
    NativeProspectiveAuthorityV2,
    ProspectiveV2IntegrityError,
    RequestBasis,
    StructuralMode,
)

from tests.autogrowth.test_native_mixed_evidence_specialization import (
    MATE,
    PARENT_ID,
    _consume,
    _mixed_authority,
    _open_mint,
)


def test_real_event_hot_path_has_no_authority_deepcopy_or_full_verify(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    authority_type = type(authority)
    original_deepcopy = authority_module.copy.deepcopy
    copied_authorities: list[object] = []

    def guarded_deepcopy(value: object, *args: object, **kwargs: object):
        if isinstance(value, NativeProspectiveAuthorityV2):
            copied_authorities.append(value)
            raise AssertionError("REAL hot path deep-copied the authority")
        return original_deepcopy(value, *args, **kwargs)

    def fail_full_verify(*args: object, **kwargs: object) -> None:
        raise AssertionError("REAL hot path ran full invariant verification")

    monkeypatch.setattr(authority_module.copy, "deepcopy", guarded_deepcopy)
    monkeypatch.setattr(authority_type, "_verify_invariants", fail_full_verify)

    _consume(
        authority,
        outcome=True,
        fullmove=210,
        frame_id="bounded-real:no-full-copy",
    )
    assert not copied_authorities


def test_virtual_hot_path_has_no_full_authority_reclosure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    authority.close_nomination()
    authority_type = type(authority)

    def fail_full_operation(*args: object, **kwargs: object) -> None:
        raise AssertionError("VIRTUAL hot path performed a full reclosure")

    monkeypatch.setattr(authority_type, "_verify_invariants", fail_full_operation)
    monkeypatch.setattr(authority_type, "continuation_digest", fail_full_operation)

    result = authority.open_virtual(FrameContext(
        "bounded-virtual:no-full-reclosure",
        FrameKind.VIRTUAL,
        values={"board": chess.Board(MATE.format(fullmove=211))},
    ))
    assert result["query"].response.policy_response is True


@pytest.mark.parametrize("history_size", (32, 4096))
def test_curriculum_virtual_wrapper_does_not_reclose_lifetime_history(
    monkeypatch: pytest.MonkeyPatch,
    history_size: int,
) -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    authority.close_nomination()
    session = authority.frame_session()
    for index in range(history_size):
        request_id = f"virtual-history:{index:04d}"
        authority.request_queue.append(request_id)
        authority._request_queue_hot_digest = (
            authority_module._next_hot_append_digest(
                authority._request_queue_hot_digest,
                "request_queue",
                request_id,
                len(authority.request_queue),
            )
        )

    authority_type = type(authority)

    def fail_full_operation(*args: object, **kwargs: object) -> None:
        raise AssertionError("curriculum VIRTUAL wrapper ran full reclosure")

    monkeypatch.setattr(
        authority_type,
        "continuation_manifest",
        fail_full_operation,
    )
    monkeypatch.setattr(
        authority_type,
        "continuation_digest",
        fail_full_operation,
    )
    try:
        _available, response = _v2_r0_available(
            authority,
            chess.Board(MATE.format(fullmove=214)),
            frame_id=f"bounded-virtual:history-{history_size}",
            frame_session=session,
        )
    finally:
        session.close()
    assert response["availability_source"] == (
        "v2_prospective_graph_emission"
    )


def test_late_consume_failure_rolls_back_the_mutation_journal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    _pending, _trace, receipt = _open_mint(
        authority,
        outcome=True,
        fullmove=212,
        frame_id="bounded-real:late-failure",
    )
    before = authority.continuation_manifest()
    authority_type = type(authority)
    original_append = authority_type._append_incremental_history

    def append_then_fail(self, *args: object, **kwargs: object) -> None:
        original_append(self, *args, **kwargs)
        raise ProspectiveV2IntegrityError("synthetic late REAL failure")

    monkeypatch.setattr(
        authority_type,
        "_append_incremental_history",
        append_then_fail,
    )
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="synthetic late REAL failure",
    ):
        authority.consume(receipt)
    assert authority.continuation_manifest() == before

    monkeypatch.undo()
    authority.verify_full_history_boundary("bounded-real journal rollback")


def test_hot_event_ignores_padded_historical_queue_for_validation_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    # Model a large historical request log whose entries are no longer active.
    # The production index is deliberately kept separate from this append-only
    # compatibility ledger; a full boundary would validate the synthetic rows.
    for index in range(512):
        request_id = f"historical-padding:{index:04d}"
        authority.request_queue.append(request_id)
        authority._request_queue_hot_digest = (
            authority_module._next_hot_append_digest(
                authority._request_queue_hot_digest,
                "request_queue",
                request_id,
                len(authority.request_queue),
            )
        )

    authority_type = type(authority)
    original_digest = authority_type._append_log_digest
    calls = 0

    def counted_digest(*args: object, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        return original_digest(*args, **kwargs)

    monkeypatch.setattr(
        authority_type,
        "_append_log_digest",
        staticmethod(counted_digest),
    )
    _consume(
        authority,
        outcome=True,
        fullmove=213,
        frame_id="bounded-real:padded-history",
    )
    assert calls == 0


def test_pending_order_cache_skips_lifetime_queue_iteration() -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )

    class NoIterationQueue(list[str]):
        def __iter__(self):  # type: ignore[override]
            raise AssertionError("pending safe point iterated lifetime queue")

    # These rows model already-settled historical requests.  The maintained
    # active order is empty, so the event-driven no-op safe point must never
    # inspect the append-only queue or the full consumption map.
    authority.request_queue = NoIterationQueue(
        f"historical-request-padding:{index:04d}" for index in range(1024)
    )
    authority._pending_request_order.clear()
    authority._pending_request_index.clear()
    assert authority._pending_request_ids() == ()
    assert authority.settle_pending_structural_requests() is None


def test_late_specialization_trigger_uses_bounded_evidence_window() -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    for index in range(16):
        _consume(
            authority,
            outcome=True,
            fullmove=230 + index,
            frame_id=f"bounded-trigger:padding-support:{index:02d}",
        )

    parent = authority.states[PARENT_ID]
    support_before = tuple(parent.support_receipt_ids)
    contradiction_before = tuple(parent.contradiction_receipt_ids)

    class NoIterationLedger(authority_module._AppendOnlyLedger):
        def __iter__(self):  # type: ignore[override]
            raise AssertionError(
                "late specialization trigger iterated a lifetime ledger"
            )

    parent.support_receipt_ids = NoIterationLedger(support_before)
    parent.contradiction_receipt_ids = NoIterationLedger(
        contradiction_before
    )
    _pending, emission = _consume(
        authority,
        outcome=False,
        fullmove=250,
        frame_id="bounded-trigger:late-contradiction",
    )

    assert emission.graph_specialization_request_ids == (PARENT_ID,)
    request = authority.deferred_requests[
        emission.request_queue_appended_ids[0]
    ]
    # The padded all-support prefix matures the parent before the late
    # contradiction, so this is the certified-revocation specialization
    # branch.  It exercises the same bounded support/contradiction selector
    # without manufacturing an impossible late mixed trigger.
    assert request.request_basis is RequestBasis.CERTIFIED_REVOCATION
    assert request.contradiction_receipt_id == emission.receipt_id
    assert request.parent_prospective_support_receipt_ids == tuple(sorted(
        support_before[-MIN_SUPPORT:]
    ))
    assert len(request.parent_prospective_support_receipt_ids) == MIN_SUPPORT

    # Restore protocol-facing mutable ledgers before asking the full boundary
    # to reconstruct every historical receipt and verify the bounded request
    # contract.
    parent.support_receipt_ids = authority_module._AppendOnlyLedger(
        parent.support_receipt_ids[:]
    )
    parent.contradiction_receipt_ids = authority_module._AppendOnlyLedger(
        parent.contradiction_receipt_ids[:]
    )
    authority.verify_full_history_boundary("bounded late trigger")


def test_virtual_hot_path_ignores_padded_certification_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    # This simulates a long-lived core ledger.  Its rolling digest is kept in
    # sync so the only omitted work is the full-log reconstruction itself;
    # verify_full_history_boundary remains the tamper/replay boundary.
    state = next(iter(authority._hot_live_states().values()))
    for index in range(512):
        receipt_id = f"historical-certification-padding:{index:04d}"
        state.certification_receipt_ids.append(receipt_id)
        state.certification_receipt_digest = (
            authority_module._next_hot_append_digest(
                state.certification_receipt_digest,
                "certification_receipt",
                receipt_id,
                len(state.certification_receipt_ids),
            )
        )

    authority_type = type(authority)
    original_digest = authority_type._append_log_digest
    calls = 0

    def counted_digest(*args: object, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        return original_digest(*args, **kwargs)

    monkeypatch.setattr(
        authority_type,
        "_append_log_digest",
        staticmethod(counted_digest),
    )
    authority.open_virtual(FrameContext(
        "bounded-virtual:padded-certification-history",
        FrameKind.VIRTUAL,
        values={"board": chess.Board(MATE.format(fullmove=214))},
    ))
    assert calls == 0


def test_real_hot_path_uses_indexed_discovery_exclusion() -> None:
    """A long frozen discovery prefix is not iterated by REAL admission."""

    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    prefix = tuple(
        f"discovery-prefix-padding:{index:05d}"
        for index in range(2048)
    )

    class NoIterationTuple(tuple[str, ...]):
        def __iter__(self):  # type: ignore[override]
            raise AssertionError(
                "REAL admission iterated the discovery exclusion prefix"
            )

    # Keep the canonical tuple deliberately hostile to iteration while
    # preserving the exact runtime set projection built at the full boundary.
    authority.discovery_prefix_physical_fingerprints = NoIterationTuple(
        prefix
    )
    authority._discovery_prefix_physical_fingerprint_set = frozenset(prefix)
    _consume(
        authority,
        outcome=True,
        fullmove=218,
        frame_id="bounded-real:indexed-discovery-exclusion",
    )


def test_deepcopy_restores_discovery_physical_exclusion_index() -> None:
    """Cloning cannot silently disable the frozen-prefix replay guard."""

    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    clone = copy.deepcopy(authority)
    expected = frozenset(clone.discovery_prefix_physical_fingerprints)
    assert expected
    assert clone._discovery_prefix_physical_fingerprint_set == expected
    assert clone._hot_path_indexes_ready

    _pending, _trace, receipt = _open_mint(
        clone,
        outcome=True,
        fullmove=219,
        frame_id="bounded-real:deepcopy-discovery-exclusion",
    )
    duplicate = replace(
        receipt,
        interaction_fingerprint=next(iter(expected)),
    )
    before = clone.continuation_manifest()
    with pytest.raises(
        ProspectiveV2IntegrityError,
        match="discovery-evidence replay",
    ):
        clone.consume(duplicate)
    assert clone.continuation_manifest() == before


def test_hot_events_round_trip_through_full_replay_boundary() -> None:
    authority = _mixed_authority(
        authority_module.AvailabilityState.AVAILABLE,
    )
    _consume(
        authority,
        outcome=True,
        fullmove=215,
        frame_id="bounded-real:replay-1",
    )
    _consume(
        authority,
        outcome=True,
        fullmove=216,
        frame_id="bounded-real:replay-2",
    )
    expected = authority.continuation_manifest()
    authority.verify_full_history_boundary("bounded-real replay")
    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.continuation_manifest() == expected
