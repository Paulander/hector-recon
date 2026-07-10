from __future__ import annotations

import random

import chess
import pytest

from recon_lite_chess.autogrowth.intrinsic_krk_credit import (
    KRKIntrinsicCredit,
    MATE1_COMPETENCE_ID,
    MATE2_COMPETENCE_ID,
    fit_tg46d_mate2_competence_gate,
    native_foundation_response,
    rollout_foundation_policy,
)
from recon_lite_hector.learning import OutcomeCalibratedCompetenceGate
from recon_lite_chess.autogrowth.clean_edge_fence_stage import _load_json
from recon_lite_chess.autogrowth.handoff_reachability_audit import (
    _reconstruct_parent_foundation_from_m4_audit,
)
from recon_lite_chess.autogrowth.tg48a2_same_side_episode_training import (
    TG48a2SameSideEpisodeTrainingConfig,
    _play_episode,
    _select_white_move,
)


class _AlwaysPositiveLearner:
    def choose(self, board: chess.Board) -> chess.Move | None:
        return next(iter(board.legal_moves), None)

    def weight_for_move(self, board: chess.Board, move: chess.Move) -> float:
        return 1.0

    def active_terminal_count(self, board: chess.Board, move: chess.Move) -> int:
        return 1


def _artifact() -> dict[str, object]:
    return {
        "schema_version": "promoted-foundation-test",
        "config_hash": "config",
        "graph_summary_hash": "graph",
        "m4_only_mate1_regression_accuracy": 1.0,
        "m4_only_mate2_heldout_conversion": 0.97,
        "m4_only_mate2_regression_conversion": 0.94,
    }


def test_promoted_foundation_restores_conservative_grounded_values() -> None:
    credit = KRKIntrinsicCredit(_artifact())
    mate1 = credit.engine.states[MATE1_COMPETENCE_ID]
    mate2 = credit.engine.states[MATE2_COMPETENCE_ID]

    assert mate1.can_emit(credit.engine.config)
    assert mate2.can_emit(credit.engine.config)
    assert mate1.slow_value == 1.0
    assert mate2.slow_value == pytest.approx(0.88)
    assert mate1.grounding_level == 0
    assert mate2.grounding_level == 1
    assert mate2.grounding_ancestors == {MATE1_COMPETENCE_ID}


def test_native_response_uses_graph_choice_without_validator() -> None:
    board = chess.Board("8/8/8/8/8/4K3/1R6/7k w - - 0 1")
    learner = _AlwaysPositiveLearner()
    gate = OutcomeCalibratedCompetenceGate(
        feature_names=("a", "b", "c", "d"),
        scales=(1.0, 1.0, 1.0, 1.0),
        weights=(10.0, 0.0, 0.0, 0.0, 0.0),
        threshold=0.5,
        train_metrics={},
        validation_metrics={},
        mature=True,
    )
    response = native_foundation_response(
        board,
        {"mate1": learner, "mate2_first": learner},
        mate2_gate=gate,
    )

    assert response["graph_all_reply"] is True
    assert response["provider_ids"] == [MATE2_COMPETENCE_ID]
    assert response["validator_consulted"] is False


def test_tg46d_gate_is_selective_on_retired_regression_outcomes() -> None:
    gate = fit_tg46d_mate2_competence_gate(
        "reports/autogrowth/clean_slate_krk/tg46d_m4_foundation_consolidation/"
        "pools/tg46d_m4_only_eval.jsonl.gz"
    )

    assert gate.mature is True
    assert gate.train_metrics["false_positive"] == 0
    assert gate.validation_metrics["true_positive"] == 77
    assert gate.validation_metrics["false_positive"] == 0


def test_episode_return_contains_only_world_child_value_and_move_cost() -> None:
    credit = KRKIntrinsicCredit(_artifact())
    response = {
        "graph_all_reply": True,
        "provider_ids": [MATE2_COMPETENCE_ID],
    }
    channels, value, audit = credit.episode_return(response, real_white_moves=2)

    assert channels == {
        "world_terminal": 0.0,
        "mature_child_bootstrap": 0.827992,
        "real_move_metabolic_cost": -0.02,
    }
    assert value == 0.807992
    assert audit["validator_used_for_reward"] is False
    assert audit["authored_geometry_shaping_used"] is False

    failure_channels, failure, _ = credit.episode_return(
        {}, real_white_moves=1, terminal_kind="rook_loss"
    )
    assert failure_channels["world_terminal"] == -1.0
    assert failure == -1.0


def test_historical_same_side_start_receives_native_tg46d_value_without_shaping() -> None:
    config = TG48a2SameSideEpisodeTrainingConfig(
        credit_mode="intrinsic_foundation_value",
        max_white_moves=3,
        max_total_plies=6,
    )
    artifact = _load_json(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    trace = _play_episode(
        row={
            "fen": "8/8/8/4R3/8/8/7k/5K2 w - - 0 1",
            "split": "smoke",
            "family": "same_side",
        },
        episode_id="intrinsic_smoke",
        parent=parent,
        learner=None,
        config=config,
        behavior_policy="graph_runtime_no_exploration",
        rng=random.Random(7),
        training=False,
    )

    assert trace["endpoint_type"] == "mature_foundation_competence_available"
    assert trace["endpoint_mature_competence_available"] is True
    assert trace["reward_channels"] == {
        "world_terminal": 0.0,
        "mature_child_bootstrap": 0.8536,
        "real_move_metabolic_cost": -0.01,
    }
    assert trace["trajectory_reward"] == 0.8436
    assert trace["trainer_authored_shaping_used_for_reward"] is False
    assert trace["intrinsic_credit_audit"]["provider_ids"] == [MATE2_COMPETENCE_ID]
    assert trace["intrinsic_credit_audit"]["validator_used_for_reward"] is False


def test_foundation_calibration_rollout_observes_raw_game_outcome() -> None:
    config = TG48a2SameSideEpisodeTrainingConfig()
    artifact = _load_json(config.parent_foundation_artifact_path)
    parent = _reconstruct_parent_foundation_from_m4_audit(
        parent_artifact=artifact,
        parent_m4_audit_path=config.parent_foundation_m4_audit_path,
    )
    result = rollout_foundation_policy(
        chess.Board("6k1/8/5K2/8/7R/8/8/8 w - - 0 1"),
        parent,
        max_plies=4,
    )

    assert result["success"] is True
    assert result["outcome"] == "mate"
    assert len(result["moves"]) <= 3


def test_intrinsic_runtime_selection_cannot_fall_through_to_legacy_scorer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_legacy(*args: object, **kwargs: object) -> float:
        raise AssertionError("legacy scorer consulted")

    monkeypatch.setattr(
        "recon_lite_chess.autogrowth.tg48a2_same_side_episode_training._score_micro_move",
        fail_legacy,
    )
    move = _select_white_move(
        chess.Board("8/8/8/4R3/8/8/7k/5K2 w - - 0 1"),
        parent=None,
        learner=None,
        config=TG48a2SameSideEpisodeTrainingConfig(
            credit_mode="intrinsic_foundation_value"
        ),
        rng=random.Random(1),
        training=False,
    )

    assert move is not None
