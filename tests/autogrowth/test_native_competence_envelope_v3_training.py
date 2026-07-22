from __future__ import annotations

from copy import deepcopy

from recon_lite_hector.nodes import StemCellState, StemCellTerminal

from recon_lite_chess.autogrowth.native_competence_envelope import (
    AvailabilityState,
    CompetenceContextCell,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
)
from recon_lite_chess.autogrowth.native_competence_envelope_v3_training import (
    EXAMPLE_CAP_PER_ARITY,
    LEARNER_MODULE,
    LEARNER_MODULE_SHA256,
    V2_MODULE,
    V2_MODULE_SHA256,
    _diagnostic_verdict,
    _file_sha256,
    enumerate_bounded_pure_base_patterns,
    parity_mismatch_rows,
)


TERMINAL_TRACE_AUTHORITY_LEARNER_SHA256 = (
    "5079bd8600ef5795cc59639f63faf2256a8d0ddf71d101e43b85f75d3ca25458"
)

PROSPECTIVE_V2_INTEGRATION_LEARNER_SHA256 = (
    "5e1882f7bd8bc494f38031fa85c31f2e09eca2496487fbef9a1430cc0a80a754"
)


def _actuation(activation: float = 0.25) -> dict[str, object]:
    return {
        "actuator_identity": "chess_move:a1a2",
        "move_uci": "a1a2",
        "option_identity": "triplet:a1a2",
        "activation": activation,
        "candidate_count": 3,
        "formal_ticks": 9,
        "graph_owned": True,
        "host_fallback": False,
    }


def _real_row(activation: float = 0.25) -> dict[str, object]:
    return {
        "index": 0,
        "historical_pool_name": "r0_train",
        "fen": "8/8/8/8/8/8/R7/K6k w - - 0 1",
        "actuation": _actuation(activation),
        "active_competence_signal_ids": ["internal:policy_response", "a"],
    }


def test_v3_preserves_frozen_hash_and_locks_additive_terminal_trace_authority_extension() -> None:
    assert _file_sha256(V2_MODULE) == V2_MODULE_SHA256
    # Keep the historical constant unchanged so rerunning V3 with the later
    # revocable-maturity learner still fails closed.
    assert LEARNER_MODULE_SHA256 == (
        "65dda4f09bc1181a6fe3780c27b56da4fc888a377ae3cfffe3c728e9d11d2a7b"
    )
    # Preserve the terminal-trace extension hash as history; freeze the later
    # prospective-V2 integration independently. V3 itself was not rerun.
    assert TERMINAL_TRACE_AUTHORITY_LEARNER_SHA256 == (
        "5079bd8600ef5795cc59639f63faf2256a8d0ddf71d101e43b85f75d3ca25458"
    )
    assert _file_sha256(LEARNER_MODULE) == PROSPECTIVE_V2_INTEGRATION_LEARNER_SHA256


def test_admission_persists_exact_frame_field_and_float_bits() -> None:
    real = _real_row(0.25)
    reference = deepcopy(real)
    reference["actuation"]["activation"] = 0.25000000000000006
    rows = parity_mismatch_rows([real], [reference])
    assert rows == [{
        "index": 0,
        "fen": real["fen"],
        "historical_pool_name": "r0_train",
        "field": "GraphActuation.activation",
        "real_value": 0.25,
        "reference_value": 0.25000000000000006,
        "real_ieee754": "3fd0000000000000",
        "reference_ieee754": "3fd0000000000001",
    }]


def _records() -> tuple[CompetenceEvidenceRecord, ...]:
    rows = []
    for index in range(8):
        success = index < 4
        signal = "positive_atom" if success else "negative_atom"
        rows.append(CompetenceEvidenceRecord(
            evidence_key=f"evidence-{index}",
            active_signal_ids=("shared_atom", signal),
            policy_response=True,
            observed_completion=success,
            actuator_identity=f"chess_move:a{index + 1}a1",
            completion_terminal_identity="mate",
        ))
    return tuple(rows)


def test_bounded_diagnostic_has_exact_counts_digest_and_examples() -> None:
    diagnostic = enumerate_bounded_pure_base_patterns(
        _records(), GraphNativeCompetenceEnvelope()
    )
    assert diagnostic["exact_counts_by_arity"] == {
        "1": {"pure": 2, "support_qualified": 3, "tested": 3},
        "2": {"pure": 2, "support_qualified": 2, "tested": 3},
        "3": {"pure": 0, "support_qualified": 0, "tested": 1},
    }
    assert diagnostic["exact_total_counts"]["pure"] == 4
    assert diagnostic["exact_total_counts"]["attempted"] == 0
    assert diagnostic["verdict"] == "nomination_or_responsibility_failure"
    assert diagnostic["full_pattern_records_persisted"] is False
    assert all(
        len(examples) <= EXAMPLE_CAP_PER_ARITY
        for examples in diagnostic["bounded_examples_by_arity"].values()
    )
    repeated = enumerate_bounded_pure_base_patterns(
        _records(), GraphNativeCompetenceEnvelope()
    )
    assert repeated["pure_pattern_digest"] == diagnostic["pure_pattern_digest"]


def test_verdict_distinguishes_all_frozen_boundaries() -> None:
    assert _diagnostic_verdict({"pure": 0}) == (
        "current_representation_or_selectivity_insufficient"
    )
    assert _diagnostic_verdict({"pure": 1, "attempted": 0}) == (
        "nomination_or_responsibility_failure"
    )
    assert _diagnostic_verdict({
        "pure": 1, "attempted": 1, "admitted": 0,
    }) == "proposal_admission_or_capacity_failure"
    assert _diagnostic_verdict({
        "pure": 1, "attempted": 1, "admitted": 1, "matured": 0,
    }) == "lifecycle_or_evidence_accounting_defect"
    assert _diagnostic_verdict({
        "pure": 1, "attempted": 1, "admitted": 1, "matured": 1,
    }) == "native_competence_learning_engaged_compare_outcome_shuffled"


def test_diagnostic_tracks_attempt_admission_and_maturity() -> None:
    envelope = GraphNativeCompetenceEnvelope()
    envelope.audit.proposal_rows.append({
        "members": ["positive_atom"],
        "admitted": True,
        "reason": None,
    })
    diagnostic = enumerate_bounded_pure_base_patterns(_records(), envelope)
    assert diagnostic["exact_total_counts"]["attempted"] == 1
    assert diagnostic["exact_total_counts"]["admitted"] == 1
    assert diagnostic["exact_total_counts"]["matured"] == 0
    assert diagnostic["verdict"] == "lifecycle_or_evidence_accounting_defect"

    stem = StemCellTerminal("competence_context_test")
    stem.state = StemCellState.MATURE
    envelope.cells["competence_context_test"] = CompetenceContextCell(
        cell_id="competence_context_test",
        members=("positive_atom",),
        born_round=0,
        born_request_ordinal=0,
        stem_cell=stem,
        polarity=AvailabilityState.AVAILABLE,
        support=4,
        successes=4,
    )
    matured = enumerate_bounded_pure_base_patterns(_records(), envelope)
    assert matured["exact_total_counts"]["matured"] == 1
    assert matured["verdict"] == (
        "native_competence_learning_engaged_compare_outcome_shuffled"
    )
