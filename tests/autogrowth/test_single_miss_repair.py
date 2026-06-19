from pathlib import Path

from recon_lite_chess.autogrowth import SingleMissRepairConfig, run_single_miss_repair


def test_tg27b_smoke_reports_single_miss_repair_fields(tmp_path: Path) -> None:
    progress = tmp_path / "tg27b_progress.json"
    result = run_single_miss_repair(
        config=SingleMissRepairConfig(
            mate1_train_count=4,
            mate1_heldout_count=2,
            mate2_train_count=1,
            mate2_heldout_count=1,
            max_shared_atom_candidates_per_choice=2,
            max_samples=3,
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
    assert payload["checkpoint"] == "TG27b_single_miss_repair"
    assert progress.exists()
    for key in (
        "checkpoint_pass",
        "original_tg27a_conversion_rate",
        "repaired_conversion_rate",
        "repaired_first_move_success_rate",
        "repaired_same_graph_second_move_count",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "failed_fen",
        "failure_bucket",
        "false_negative_count_before",
        "false_negative_count_after",
        "false_positive_count_before",
        "false_positive_count_after",
        "deep_reply_checks_before",
        "deep_reply_checks_after",
        "repair_type",
        "repair_rationale",
        "continuation_mate1_success_for_failed_position",
        "scheduler_equivalence_mismatch_count",
        "replay_stability_result",
        "ablation_results",
        "m3_update_count",
        "m4_promotion_count_by_terminal_kind",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "validator_skip_used_during_internal_handoff_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "stage_labels_learner_visible",
        "purity_boundary",
    ):
        assert key in decision
    assert decision["guard_used_during_runtime_choice"] is False
    assert decision["guard_used_during_evaluation"] is False
    assert decision["validator_skip_used_during_internal_handoff_eval"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["stage_labels_learner_visible"] is False
