import json

import chess

from recon_lite_chess.autogrowth import (
    CurriculumRewardRecoveryConfig,
    KRKPositionSet,
    run_curriculum_reward_recovery,
    score_non_terminal_progress,
    validate_learner_record,
)
from recon_lite_chess.autogrowth.features import extract_learner_features
from recon_lite_chess.training.krk_curriculum import box_min_side


def test_tg24_non_terminal_progress_is_not_flat_for_safe_progress() -> None:
    before = chess.Board("8/8/8/4k3/8/8/8/R3K3 w - - 0 1")
    after = chess.Board("8/8/8/8/4k3/8/8/R3K3 w - - 0 1")

    score = score_non_terminal_progress(
        initial_features=extract_learner_features(before),
        final_features=extract_learner_features(after),
        initial_box=box_min_side(before),
        final_box=box_min_side(after),
        confinement_worsened_count=0,
        repetition_events=0,
        repeated_white_action_events=0,
        rook_attacked_count=0,
        rook_missing_count=0,
    )

    assert score != 0.0


def test_tg24_curriculum_labels_are_diagnostic_not_learner_visible(tmp_path) -> None:
    fen = "k7/8/1K6/8/8/8/8/7R w - - 0 1"
    result = run_curriculum_reward_recovery(
        config=CurriculumRewardRecoveryConfig(
            seed=1,
            train_count=2,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=2,
            horizons=(4,),
            min_sequence_credit=-1.0,
            activation_max_distance=4.0,
            after_max_distance=4.0,
            chain_max_distance=4.0,
            max_chain_edges=8,
            curriculum_probe_per_stage=1,
            max_rollout_samples=2,
        ),
        positions=KRKPositionSet(seed=1, train=(fen, fen), heldout_weakness=(fen,), heldout_broader=()),
    )
    output = result.write_json(tmp_path / "tg24_curriculum_reward_recovery.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_autogrowth_tg24_curriculum_reward_recovery.v0"
    assert payload["learner_visibility"]["curriculum_labels_in_learner_records"] is False
    assert payload["local_recon_structure"]["curriculum_labels_diagnostics_only"] is True
    assert payload["heldout_metrics"]["4"]["baseline"]["old_curriculum_reward_component_avg"] is not None
    assert payload["heldout_metrics"]["4"]["baseline"]["non_terminal_progress_delta_avg"] is not None
    validate_learner_record(payload["learner_visibility"]["validated_generic_credit_record"])


def test_tg24_audit_states_tg18_tg23_do_not_use_old_reward_runtime() -> None:
    fen = "8/8/8/8/2K5/6k1/2R5/8 w - - 0 1"
    result = run_curriculum_reward_recovery(
        config=CurriculumRewardRecoveryConfig(
            seed=1,
            train_count=1,
            heldout_weakness_count=1,
            heldout_broader_count=0,
            min_support=1,
            max_candidates=1,
            horizons=(2,),
            min_sequence_credit=-1.0,
            activation_max_distance=4.0,
            after_max_distance=4.0,
            chain_max_distance=4.0,
            max_chain_edges=4,
            curriculum_probe_per_stage=0,
        ),
        positions=KRKPositionSet(seed=1, train=(fen,), heldout_weakness=(fen,), heldout_broader=()),
    )
    payload = result.to_dict()

    audit = payload["audit"]["current_autogrowth_tg18_tg23_use"]
    assert audit["uses_krk_curriculum_reward_or_stage_generation"] is False
    assert "krk_reward" in audit["statement"]
    assert payload["decision"]["adds_retry_candidates"] is False
