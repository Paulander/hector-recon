from __future__ import annotations

from recon_lite_chess.autogrowth.native_competence_envelope import (
    CompetenceContextGrowthGenome,
    CompetenceEvidenceRecord,
    GraphNativeCompetenceEnvelope,
)
from recon_lite_chess.autogrowth.native_competence_envelope_v2_training import (
    GLOBAL_EVIDENCE_RATE,
    _global_evidence_control,
    enumerate_pure_base_patterns,
    round_histograms,
)


def _record(index: int, signals: tuple[str, ...], outcome: bool):
    return CompetenceEvidenceRecord(
        evidence_key=f"record-{index}",
        active_signal_ids=signals,
        policy_response=True,
        observed_completion=outcome,
        actuator_identity=f"chess_move:a{index % 8 + 1}a{index % 8 + 1}",
        completion_terminal_identity="mate",
    )


def test_round_histograms_cover_every_frozen_round_and_required_dimension():
    records = tuple(
        _record(index, ("common", "positive"), True)
        for index in range(4)
    ) + tuple(
        _record(index + 4, ("common", "negative"), False)
        for index in range(4)
    )
    envelope = GraphNativeCompetenceEnvelope()
    envelope.grow(
        records,
        genome=CompetenceContextGrowthGenome(
            envelope.config.selection_seed
        ),
    )
    rows = round_histograms(envelope)
    assert len(rows) == envelope.config.structural_rounds == 3
    for row in rows:
        assert {
            "proposal_histogram",
            "duplication_histogram",
            "support_histogram",
            "purity_histogram",
            "mixture_histogram",
            "arity_histogram",
            "prune_histogram",
        }.issubset(row)


def test_post_run_diagnostic_enumerates_pure_patterns_without_mutation():
    records = tuple(
        _record(index, ("common", "positive", "pair"), True)
        for index in range(4)
    ) + tuple(
        _record(index + 4, ("common", "negative"), False)
        for index in range(4)
    )
    before = tuple(records)
    result = enumerate_pure_base_patterns(records)
    assert result["read_only_no_learning_feedback"] is True
    assert result["pure_pattern_count"] > 0
    assert any(
        pattern["members"] == ["positive"]
        and pattern["support"] == 4
        and pattern["failures"] == 0
        for pattern in result["patterns"]
    )
    assert tuple(records) == before


def test_global_evidence_control_uses_actual_40_of_64_rate():
    records = tuple(
        _record(index, ("signal",), index < 40)
        for index in range(64)
    )
    result = _global_evidence_control(records)
    assert GLOBAL_EVIDENCE_RATE == 0.625
    assert result["constant_probability"] == 40 / 64
    assert result["source"] == "actual_training_prevalence_40_of_64"
