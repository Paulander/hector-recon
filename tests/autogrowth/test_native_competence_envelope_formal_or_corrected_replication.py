from __future__ import annotations

from recon_lite_chess.autogrowth.native_competence_envelope import (
    CompetenceEvidenceRecord,
)
from recon_lite_chess.autogrowth.native_competence_envelope_formal_or_corrected_replication import (
    EXPECTED_REPLAY,
    classification_invariants,
    replay_expectation_values,
    representation_ceiling,
)


def test_replay_expectation_values_are_exact_and_arm_separated() -> None:
    evaluation = {"cohort_metrics": {"arms": {
        "connected": {
            "total_tp": 313,
            "total_fp": 39,
            "organisms_with_any_tp": 31,
            "safe_narrow_passes": 6,
            "strict_passes": 0,
        },
        "outcome_shuffled": {
            "total_tp": 0,
            "total_fp": 0,
            "organisms_with_any_tp": 0,
            "safe_narrow_passes": 0,
            "strict_passes": 0,
        },
    }}}
    assert replay_expectation_values(evaluation) == EXPECTED_REPLAY


def test_classification_invariants_are_independent_of_conflict_state() -> None:
    organisms = [{"rows": [
        {
            "formal_available": True,
            "formal_refuted": True,
            "policy_response": True,
            "available_cell_ids": ["a"],
            "refuted_cell_ids": ["b"],
        },
        {
            "formal_available": False,
            "formal_refuted": False,
            "policy_response": False,
            "available_cell_ids": ["a"],
            "refuted_cell_ids": ["b"],
        },
    ]}]
    assert all(classification_invariants(organisms).values())


def test_representation_ceiling_excludes_policy_response_and_is_read_only() -> None:
    training = tuple(
        CompetenceEvidenceRecord(
            evidence_key=f"train-{index}",
            active_signal_ids=(
                "atom:shared",
                "atom:positive" if index < 4 else "atom:negative",
                "internal:policy_response",
            ),
            policy_response=True,
            observed_completion=index < 4,
            actuator_identity="chess_move:a1a2",
            completion_terminal_identity="mate",
        )
        for index in range(64)
    )
    validation = [
        {
            "active_competence_signal_ids": [
                "atom:positive" if index < 16 else "atom:negative",
                "internal:policy_response",
            ],
            "actual_completion": index < 16,
        }
        for index in range(32)
    ]
    before = tuple(training)
    result = representation_ceiling(training, validation, [])
    assert result["read_only"] is True
    assert result["learner_feedback"] is False
    assert result["internal_policy_response_excluded"] is True
    assert tuple(training) == before
    assert result["counts_by_arity"]["1"][
        "training_pure_validation_safe"
    ] == 1
