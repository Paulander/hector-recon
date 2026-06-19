from pathlib import Path

from recon_lite_chess.autogrowth import (
    NativeFoundationScaleReplayConfig,
    run_native_foundation_scale_replay,
)


def test_tg27a_smoke_reports_native_scale_replay_fields(tmp_path: Path) -> None:
    progress = tmp_path / "tg27a_progress.json"
    result = run_native_foundation_scale_replay(
        config=NativeFoundationScaleReplayConfig(
            mate1_train_count=4,
            mate1_heldout_count=2,
            mate2_train_count=1,
            mate2_heldout_count=1,
            max_shared_atom_candidates_per_choice=2,
            max_samples=2,
            equivalence_count=1,
            replay_count=2,
            full_replay_count=0,
            run_ablations=False,
            run_scheduler_equivalence=False,
            progress_output=str(progress),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG27a_native_foundation_scale_replay"
    assert progress.exists()
    for key in (
        "checkpoint_pass",
        "mate1_train_count",
        "mate1_heldout_count",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "mate2_train_count",
        "mate2_heldout_count",
        "mate2_conversion_rate",
        "mate2_first_move_success_rate",
        "mate2_same_graph_second_move_count",
        "continuation_mate1_accuracy",
        "continuation_mate1_null_count",
        "frozen_m3_used",
        "any_weight_updates_during_eval",
        "m4_promotions_during_eval",
        "replay_stability_pass",
        "replay_conversion_rates",
        "deep_reply_checks_run",
        "average_deep_reply_checks_per_position",
        "internal_attention_false_positive_count",
        "internal_attention_false_negative_count",
        "chain_terminal_failure_count",
        "mate1_continuation_failure_count",
        "selection_failure_count",
        "candidate_cap_failure_count",
        "scheduler_equivalence_mismatch_count",
        "m3_update_count",
        "m4_promotion_count_by_terminal_kind",
        "ablation_results",
        "ablation_audit_skipped",
        "scheduler_equivalence_audit_skipped",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "validator_skip_used_during_internal_handoff_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "stage_labels_learner_visible",
        "purity_boundary",
    ):
        assert key in decision
    assert decision["frozen_m3_used"] is True
    assert decision["guard_used_during_runtime_choice"] is False
    assert decision["guard_used_during_evaluation"] is False
    assert decision["validator_skip_used_during_internal_handoff_eval"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["stage_labels_learner_visible"] is False
    assert payload["replay"]["cached_frozen_records_from_graph_confirmed_eval"] is True
