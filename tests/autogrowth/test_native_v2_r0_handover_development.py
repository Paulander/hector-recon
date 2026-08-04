from __future__ import annotations

from recon_lite_chess.autogrowth.native_prospective_evidence_authority_v2 import (
    VIRTUAL_AVAILABLE_VALUE,
    VIRTUAL_RESPONSE_UNCERTAINTY,
)
from recon_lite_chess.autogrowth.native_v2_r0_handover_development import (
    FIXED_GENOME_SEED,
    FIXED_SOURCE_ORDINAL,
    _binary_response,
    _deranged_slots,
    _fixed_source_item,
    _load_regression,
    _metrics,
)


def test_fixed_source_is_the_predeclared_genome() -> None:
    source = _fixed_source_item(_load_regression())
    assert int(source["ordinal"]) == FIXED_SOURCE_ORDINAL == 0
    assert int(source["genome_seed"]) == FIXED_GENOME_SEED


def test_binary_child_response_cannot_carry_confidence_ranking() -> None:
    regression = _load_regression()
    source = _fixed_source_item(regression)
    # A real query is relatively expensive to construct. The historical child
    # type is immutable, so exercise the frozen response contract through an
    # exact persisted query from the source-independent diagnostic fixture.
    from recon_lite_chess.autogrowth.native_authority_handover import ChildQuery
    from recon_lite import ChildResponse

    query = ChildQuery(
        response=ChildResponse(
            child_id=str(source["genome_seed"]),
            confirmed=False,
            policy_response=True,
            available=False,
            expected_value=0.0,
            uncertainty=0.91,
            grounded=True,
            grounding_source="viewed-real-outcomes",
        ),
        actuation=None,
        frame_id="frozen-binary-contract",
        persistent_mutation_count=0,
        effect_attempts=(),
    )
    available = _binary_response(query, available=True)
    unavailable = _binary_response(query, available=False)
    assert available.available is True
    assert available.expected_value == VIRTUAL_AVAILABLE_VALUE
    assert available.uncertainty == VIRTUAL_RESPONSE_UNCERTAINTY
    assert unavailable.selection_strength == 0.0


def test_availability_derangement_changes_only_binary_availability() -> None:
    from recon_lite import ChildResponse
    from recon_lite_chess.autogrowth.native_authority_handover import ChildQuery

    def query(frame_id: str, available: bool) -> ChildQuery:
        return ChildQuery(
            response=ChildResponse(
                child_id="r0",
                confirmed=available,
                policy_response=True,
                available=available,
                expected_value=VIRTUAL_AVAILABLE_VALUE if available else 0.0,
                uncertainty=VIRTUAL_RESPONSE_UNCERTAINTY,
                grounded=True,
                grounding_source="viewed-real-outcomes",
            ),
            actuation=None,
            frame_id=frame_id,
            persistent_mutation_count=0,
            effect_attempts=("none",),
            availability_provenance={"immutable_trace_owner": frame_id},
        )

    slots = {
        "a1a2": (query("a:0", True), query("a:1", False)),
        "b1b2": (query("b:0", False), query("b:1", True)),
        "c1c2": (query("c:0", False), query("c:1", False)),
    }
    deranged, mapping = _deranged_slots(slots)
    assert all(mapping[action] != action for action in slots)
    assert sum(
        item.response.available for rows in deranged.values() for item in rows
    ) == sum(item.response.available for rows in slots.values() for item in rows)
    for action, original_rows in slots.items():
        for original, changed in zip(original_rows, deranged[action], strict=True):
            assert changed.frame_id == original.frame_id
            assert changed.actuation == original.actuation
            assert changed.graph_signal_trace == original.graph_signal_trace
            assert changed.effect_attempts == original.effect_attempts
            assert changed.response.policy_response == original.response.policy_response
            assert changed.response.grounded == original.response.grounded
            assert changed.availability_provenance["immutable_trace_owner"] == (
                original.availability_provenance["immutable_trace_owner"]
            )


def test_selectivity_metrics_keep_unknown_as_abstention() -> None:
    rows = [
        {"state": "available", "actual_completion": True},
        {"state": "available", "actual_completion": False},
        {"state": "refuted", "actual_completion": True},
        {"state": "refuted", "actual_completion": False},
        {"state": "unknown", "actual_completion": True},
        {"state": "unknown", "actual_completion": False},
    ]
    metrics = _metrics(rows)
    assert {key: metrics[key] for key in ("tp", "fp", "tn", "fn")} == {
        "tp": 1,
        "fp": 1,
        "tn": 1,
        "fn": 1,
    }
    assert metrics["abstentions"] == 2
    assert metrics["available_count"] == 2
