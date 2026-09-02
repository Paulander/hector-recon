from types import SimpleNamespace

import chess
import pytest

from recon_lite import FrameContext, FrameKind
from recon_lite_chess.autogrowth.native_all_reply_envelope import (
    AvailabilityState,
    ReplyAuthority,
)
from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    _grounded_all_reply_successor_signal,
    _r1_reply_authority_from_provider,
    _v2_r0_observe_training_successor,
)
from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    StructuralMode,
    prospective_available_provider_records,
)
from recon_lite_hector.learning import (
    CompetenceSignal,
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
)
from tests.autogrowth.test_native_mixed_evidence_specialization import (
    MATE,
    _consume,
    _mixed_authority,
    _ordinary_boundary_request,
)


def _provider(
    value: float = 0.6,
    *,
    cell_id: str = "v2-authority-cell",
    certification_digest: str = "a" * 64,
) -> dict[str, object]:
    return {
        "schema_version": "native_prospective_provider.v1",
        "cell_id": cell_id,
        "authority_cell_id": cell_id,
        "provider_kind": "prospective_authority_cell",
        "expected_value": value,
        "confidence": value,
        "uncertainty": 1.0 - value,
        "grounding_level": 0,
        "grounding_ancestors": (),
        "grounding_source": "prospective_postbirth_real_certification",
        "evidence_scope": "post_birth_real_certification_ledger",
        "discovery_evidence_used": False,
        "postbirth_real_certification": True,
        "prospectively_certified": True,
        "hypothesis_digest": "c" * 64,
        "certification_receipt_count": 4,
        "certification_receipt_digest": certification_digest,
        "support": 4,
        "successes": 4,
        "contradictions": 0,
        "direct_positive_evidence": 4,
        "direct_contrast_evidence": 0,
        "lineage_parent_id": None,
    }


def _direct_provider(
    *,
    provider_id: str = "native-r0-provider:exact-r0-triplet",
    authority_cell_id: str = "exact-r0-triplet",
) -> dict[str, object]:
    return {
        "schema_version": "native_direct_provider.v1",
        "provider_kind": "native_direct_outcome_cell",
        "cell_id": provider_id,
        "authority_cell_id": authority_cell_id,
        "expected_value": 0.8,
        "confidence": 0.75,
        "uncertainty": 0.25,
        "grounding_level": 0,
        "grounding_ancestors": (),
        "grounding_source": "exact_selected_real_returns",
        "evidence_scope": "exact_selected_real_return_ledger",
        "discovery_evidence_used": False,
        "postbirth_real_certification": False,
        "prospectively_certified": False,
        "direct_outcome_authorized": True,
        "hypothesis_digest": "d" * 64,
        "certification_receipt_count": 3,
        "certification_receipt_digest": "e" * 64,
        "direct_positive_evidence": 3,
        "direct_contrast_evidence": 0,
        "lineage_parent_id": None,
    }


def test_native_shell_provider_is_an_exact_external_td_provider() -> None:
    record = _provider()
    current = {str(record["cell_id"]): record}
    provider_records = {str(record["cell_id"]): record}
    resolver = lambda cell_id: current.get(cell_id)
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=1)
    )
    credit.register("recipient")
    envelope = SimpleNamespace(
        state=AvailabilityState.AVAILABLE,
        positive_gate=True,
        replies=(
            ReplyAuthority(
                reply_id="reply",
                state=AvailabilityState.AVAILABLE,
                confidence=0.6,
                value=0.6,
                exposure_count=0,
                grounded=True,
            ),
        ),
        value=0.6,
    )

    signal = _grounded_all_reply_successor_signal(
        envelope,
        bootstrap_enabled=True,
        actual_mate=True,
        clean_preoutcome_evidence=True,
        credit=credit,
        provider_ids=(str(record["cell_id"]),),
        provider_records=provider_records,
        external_provider_resolver=resolver,
        strict_adaptive=True,
    )
    assert signal is not None
    assert signal.provider_ids == ("v2-authority-cell",)
    assert signal.grounding_ancestors == ("v2-authority-cell",)
    assert "native_intrinsic_r0_mate_in_1" not in signal.provider_ids

    event = credit.transition(
        "recipient",
        explicit_successor_signal=signal,
        external_provider_records=provider_records,
        external_provider_resolver=resolver,
    )
    assert event.provider_ids == ("v2-authority-cell",)

    # The selected REAL receipt may legitimately append clean support between
    # the virtual envelope and TD.  The captured conservative value remains
    # valid as long as the same provider advanced monotonically.
    advanced = dict(record)
    advanced.update({
        "expected_value": 0.65,
        "confidence": 0.65,
        "uncertainty": 0.35,
        "certification_receipt_count": 5,
        "certification_receipt_digest": "b" * 64,
        "direct_positive_evidence": 5,
        "support": 5,
        "successes": 5,
        "contradictions": 0,
    })
    current[str(record["cell_id"])] = advanced
    advanced_event = credit.transition(
        "recipient",
        explicit_successor_signal=signal,
        external_provider_records=provider_records,
        external_provider_resolver=resolver,
    )
    assert advanced_event.successor_value == pytest.approx(0.6)

    before = credit.snapshot()
    current.clear()  # Authority retirement/refutation is an immediate revoke.
    with pytest.raises(ValueError, match="provider"):
        credit.transition(
            "recipient",
            explicit_successor_signal=signal,
            external_provider_records=provider_records,
            external_provider_resolver=resolver,
        )
    assert credit.snapshot() == before


def test_strict_shell_path_does_not_fallback_to_global_r0() -> None:
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=1)
    )
    credit.register("recipient")
    envelope = SimpleNamespace(
        state=AvailabilityState.AVAILABLE,
        positive_gate=True,
        replies=(
            ReplyAuthority(
                reply_id="reply",
                state=AvailabilityState.AVAILABLE,
                confidence=0.6,
                value=0.6,
                exposure_count=0,
                grounded=True,
            ),
        ),
        value=0.6,
    )
    assert _grounded_all_reply_successor_signal(
        envelope,
        bootstrap_enabled=True,
        actual_mate=True,
        clean_preoutcome_evidence=True,
        credit=credit,
        provider_ids=(),
        strict_adaptive=True,
    ) is None


def test_external_shell_provider_schema_fails_closed_before_credit() -> None:
    provider_id = "v2-authority-cell"
    valid = _provider(cell_id=provider_id)
    signal = CompetenceSignal(
        value=0.6,
        confidence=0.6,
        provider_ids=(provider_id,),
        grounding_level=1,
        grounding_ancestors=(provider_id,),
    )
    malformed_records = []
    for changes in (
        {"provider_kind": None},
        {"schema_version": "wrong-schema"},
        {"grounding_ancestors": provider_id},
        {"direct_positive_evidence": 4.5},
        {"certification_receipt_count": True},
        {"confidence": 0.59, "uncertainty": 0.41},
        {"hypothesis_digest": "not-a-sha256"},
        {"certification_receipt_digest": "z" * 64},
    ):
        malformed = dict(valid)
        malformed.update(changes)
        malformed_records.append(malformed)

    for malformed in malformed_records:
        row = _r1_reply_authority_from_provider(
            "reply",
            malformed,
            exposure_count=0,
        )
        assert row.state is AvailabilityState.UNKNOWN
        assert row.grounded is False
        credit = IntrinsicCreditEngine(
            IntrinsicCreditConfig(min_grounding_evidence=1)
        )
        credit.register("recipient")
        before = credit.snapshot()
        with pytest.raises(ValueError, match="provider record|grounded"):
            credit.transition(
                "recipient",
                explicit_successor_signal=signal,
                external_provider_records={provider_id: malformed},
                external_provider_resolver=lambda _cell_id: malformed,
            )
        assert credit.snapshot() == before


def test_frozen_direct_provider_beats_a_dematured_plastic_same_id_shadow() -> None:
    """The immutable provider domain cannot be shadowed by R1 plastic state."""

    record = _direct_provider()
    provider_id = str(record["cell_id"])
    records = {provider_id: record}
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=1)
    )
    credit.register("recipient")
    # This deliberately creates an ungrounded mutable state with the same
    # capability ID.  Captured authority records must take precedence.
    credit.register(provider_id, mature=False)
    assert credit.direct_outcome_provider_response(provider_id) is None
    signal = CompetenceSignal(
        value=0.8,
        confidence=0.75,
        provider_ids=(provider_id,),
        grounding_level=1,
        grounding_ancestors=(provider_id,),
    )
    event = credit.transition(
        "recipient",
        explicit_successor_signal=signal,
        external_provider_records=records,
        external_provider_resolver=lambda requested: (
            record if requested == provider_id else None
        ),
    )
    assert event.provider_ids == (provider_id,)
    assert event.successor_value == pytest.approx(0.8)


def test_noncanonical_direct_provider_capability_is_rejected_atomically() -> None:
    record = _direct_provider(
        provider_id="native-r0-provider:substituted-triplet",
        authority_cell_id="exact-r0-triplet",
    )
    provider_id = str(record["cell_id"])
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=1)
    )
    credit.register("recipient")
    signal = CompetenceSignal(
        value=0.8,
        confidence=0.75,
        provider_ids=(provider_id,),
        grounding_level=1,
        grounding_ancestors=(provider_id,),
    )
    before = credit.snapshot()
    with pytest.raises(ValueError, match="provider record|grounded"):
        credit.transition(
            "recipient",
            explicit_successor_signal=signal,
            external_provider_records={provider_id: record},
            external_provider_resolver=lambda _requested: record,
        )
    assert credit.snapshot() == before


@pytest.mark.parametrize(
    "live_changes",
    (
        {"grounding_level": 1},
        {"grounding_ancestors": ("unexpected-parent",)},
        {
            "certification_receipt_count": 6,
            "direct_positive_evidence": 6,
            "certification_receipt_digest": "f" * 64,
        },
    ),
)
def test_live_provider_identity_or_evidence_jump_fails_atomically(
    live_changes,
) -> None:
    captured = _provider()
    provider_id = str(captured["cell_id"])
    live = dict(captured)
    live.update(live_changes)
    credit = IntrinsicCreditEngine(
        IntrinsicCreditConfig(min_grounding_evidence=1)
    )
    credit.register("recipient")
    signal = CompetenceSignal(
        value=0.6,
        confidence=0.6,
        provider_ids=(provider_id,),
        grounding_level=1,
        grounding_ancestors=(provider_id,),
    )
    before = credit.snapshot()
    with pytest.raises(ValueError, match="provider"):
        credit.transition(
            "recipient",
            explicit_successor_signal=signal,
            external_provider_records={provider_id: captured},
            external_provider_resolver=lambda _requested: live,
        )
    assert credit.snapshot() == before


def test_native_provider_reply_row_uses_strongest_ledger_provider() -> None:
    first = _provider(0.7, cell_id="v2-authority-cell-1")
    second = _provider(
        0.8,
        cell_id="v2-authority-cell-2",
        certification_digest="b" * 64,
    )
    records = {
        str(first["cell_id"]): first,
        str(second["cell_id"]): second,
    }
    strongest = sorted(
        records.values(),
        key=lambda record: (
            float(record["expected_value"]),
            int(record["direct_positive_evidence"]),
            str(record["cell_id"]),
        ),
        reverse=True,
    )[0]
    row = _r1_reply_authority_from_provider(
        "reply",
        strongest,
        exposure_count=0,
    )
    assert row.state is AvailabilityState.AVAILABLE
    assert row.value == 0.8
    assert row.confidence == 0.8


def test_mixed_available_and_refuted_emissions_abstain_shell_provider() -> None:
    available = SimpleNamespace(
        retired=False,
        success_lower_bound=0.8,
    )
    refuted = SimpleNamespace(
        retired=False,
        success_lower_bound=0.0,
    )
    classification = NativeProspectiveAuthorityV2._classification_from_emissions(
        {"available": available, "refuted": refuted},
        {"available": ("available",), "refuted": ("refuted",)},
    )
    assert classification.state is AvailabilityState.UNKNOWN
    assert classification.available_cell_ids == ("available",)
    # The provider projection is intentionally state-gated: an AVAILABLE
    # emission alone cannot leak through a simultaneous refutation.
    assert prospective_available_provider_records(
        {"available": available, "refuted": refuted},
        classification,
    ) == ()
    assert classification.state is not AvailabilityState.AVAILABLE


def test_certified_shell_is_self_grounded_read_only_and_revocable() -> None:
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    discovery_ids = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=500 + index,
            frame_id=f"shell-provider:discovery:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    request = _ordinary_boundary_request(
        authority,
        discovery_ids,
        candidate_id="shell-provider-integration",
    )
    assert authority.settle_pending_structural_requests((request,)) is not None
    child_id = next(
        cell_id
        for cell_id, state in authority.states.items()
        if state.hypothesis.source_generation > 0
    )
    assert authority.native_provider_response(child_id) is None

    for index in range(4):
        _consume(
            authority,
            outcome=True,
            fullmove=510 + index,
            frame_id=f"shell-provider:certification:{index}",
        )
    state = authority.states[child_id]
    assert state.prospectively_certified
    provider = authority.native_provider_response(child_id)
    assert provider is not None
    assert provider["expected_value"] == pytest.approx(
        state.success_lower_bound
    )
    assert 0.0 < provider["expected_value"] < 1.0
    assert provider["discovery_evidence_used"] is False
    assert provider["certification_receipt_count"] == 4

    restored = NativeProspectiveAuthorityV2.loads(authority.dumps())
    assert restored.native_provider_response(child_id) == provider
    _consume(
        restored,
        outcome=False,
        fullmove=519,
        frame_id="shell-provider:contradiction-revocation",
    )
    assert restored.native_provider_response(child_id) is None

    board = chess.Board(MATE.format(fullmove=520))
    before = authority.continuation_digest()
    opened = authority.open_virtual(FrameContext(
        frame_id="shell-provider:virtual",
        kind=FrameKind.VIRTUAL,
        values={"board": board},
    ))
    assert authority.continuation_digest() == before
    query = opened["query"]
    assert query.response.available is True
    assert query.response.child_id == child_id
    assert query.response.expected_value == pytest.approx(
        provider["expected_value"]
    )
    assert query.availability_provenance["availability_route"] == (
        "prospectively_certified_local_shell_provider"
    )

    authority.retire_adaptive_leaves(
        (child_id,),
        reason="shell_provider_test_retirement",
    )
    assert authority.native_provider_response(child_id) is None


def test_certifying_receipt_is_not_exposed_as_preoutcome_provider() -> None:
    authority = _mixed_authority(
        AvailabilityState.AVAILABLE,
        structural_mode=StructuralMode.EVENT_DRIVEN,
    )
    discovery_ids = tuple(
        _consume(
            authority,
            outcome=True,
            fullmove=600 + index,
            frame_id=f"shell-self-bootstrap:discovery:{index}",
        )[0][2].receipt_id
        for index in range(4)
    )
    request = _ordinary_boundary_request(
        authority,
        discovery_ids,
        candidate_id="shell-self-bootstrap",
    )
    assert authority.settle_pending_structural_requests((request,)) is not None
    child_id = next(
        cell_id
        for cell_id, state in authority.states.items()
        if state.hypothesis.source_generation > 0
    )
    for index in range(3):
        _consume(
            authority,
            outcome=True,
            fullmove=610 + index,
            frame_id=f"shell-self-bootstrap:prior:{index}",
        )
    assert authority.states[child_id].prospectively_certified is False

    available, response, duplicate, _structural = (
        _v2_r0_observe_training_successor(
            authority,
            chess.Board(MATE.format(fullmove=620)),
            seen_predecessor_fens=set(),
            frame_id="shell-self-bootstrap:certifying-event",
        )
    )
    assert duplicate is False
    assert response["observed_immediate_mate"] is True
    assert response["pre_outcome_shell_provider"] is None
    assert response["provider"] is None
    # This historical fixture retains its legacy global provenance route, so
    # its raw compatibility boolean remains true.  Strict training cannot use
    # that boolean without an exact provider identity (covered above).
    assert available is True
    assert authority.states[child_id].prospectively_certified is True
    assert authority.native_provider_response(child_id) is not None
