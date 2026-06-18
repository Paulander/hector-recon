from pathlib import Path

from recon_lite_chess.autogrowth import (
    ContinuousHandoffAttentionConfig,
    run_continuous_handoff_attention,
)


def test_tg26y_smoke_reports_continuous_attention_fields(tmp_path: Path) -> None:
    progress = tmp_path / "tg26y_progress.json"
    result = run_continuous_handoff_attention(
        config=ContinuousHandoffAttentionConfig(
            mate1_train_count=4,
            mate1_heldout_count=2,
            mate2_train_count=1,
            mate2_heldout_count=1,
            max_samples=3,
            max_shared_atom_candidates_per_choice=2,
            top_k=2,
            two_stage_top_k=3,
            epsilon_tail_count=1,
            equivalence_count=1,
            compare_repetition_2=False,
            progress_output=str(progress),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG26y_continuous_handoff_attention"
    assert progress.exists()
    assert set(payload["attention_modes"]) == {
        "binary_gate_baseline",
        "high_recall_threshold_gate",
        "top_k_request_strength",
        "top_k_epsilon_exploration",
        "softmax_temperature_sampling",
        "two_stage_attention",
    }
    for key in (
        "checkpoint_pass",
        "selected_attention_mode",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "mate2_conversion_rate",
        "mate2_first_move_success_rate",
        "mate2_same_graph_second_move_count",
        "request_strength_distribution",
        "top_k_candidate_count",
        "tail_sampled_candidate_count",
        "internal_attention_false_positive_count",
        "internal_attention_false_negative_count",
        "deep_reply_checks_run",
        "average_deep_reply_checks_per_position",
        "conversion_per_attention_mode",
        "false_negative_diagnostics",
        "false_positive_diagnostics",
        "exploration_rescue_count",
        "candidate_budget_used",
        "terminal_kind_lifecycle_active",
        "pruning_count_by_terminal_kind",
        "m4_promotion_count_by_terminal_kind",
        "m3_update_count",
        "scheduler_equivalence_mismatch_count",
        "ablation_results",
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
