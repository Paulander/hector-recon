from pathlib import Path

from recon_lite_chess.autogrowth import (
    TerminalLifecycleModestScaleConfig,
    run_terminal_lifecycle_modest_scale,
)


def test_tg26x_smoke_reports_lifecycle_and_modest_scale_fields(tmp_path: Path) -> None:
    progress = tmp_path / "tg26x_progress.json"
    result = run_terminal_lifecycle_modest_scale(
        config=TerminalLifecycleModestScaleConfig(
            tiny_mate1_train_count=3,
            tiny_mate1_heldout_count=1,
            tiny_mate2_train_count=1,
            tiny_mate2_heldout_count=1,
            mate1_train_count=4,
            mate1_heldout_count=2,
            mate2_train_count=1,
            mate2_heldout_count=1,
            max_ticks=20,
            max_samples=3,
            max_shared_atom_candidates_per_choice=2,
            shared_atom_min_overlap=6,
            equivalence_count=1,
            progress_output=str(progress),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG26x_terminal_lifecycle_modest_scale"
    assert progress.exists()
    assert payload["purity_boundary"]["terminal_kind_lifecycle_active"] is True
    assert payload["purity_boundary"]["guard_used_during_runtime_choice"] is False
    assert payload["purity_boundary"]["guard_used_during_evaluation"] is False
    assert payload["purity_boundary"]["runtime_tablebase_or_dtm_move_source"] is False
    assert payload["purity_boundary"]["stage_labels_learner_visible"] is False

    for key in (
        "checkpoint_pass",
        "terminal_lifecycle_policy",
        "terminal_kind_stats",
        "tiny_tg26w_conversion_rate",
        "tiny_tg26w_false_positive_internal_gate_count",
        "tiny_tg26w_false_negative_internal_gate_count",
        "tiny_tg26w_approved_count",
        "tiny_tg26w_rejected_count",
        "mate1_train_count",
        "mate1_heldout_count",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "mate2_train_count",
        "mate2_heldout_count",
        "mate2_conversion_rate",
        "mate2_first_move_success_rate",
        "mate2_same_graph_second_move_count",
        "internal_gate_approved_candidate_count",
        "internal_gate_rejected_candidate_count",
        "internal_gate_false_positive_count",
        "internal_gate_false_negative_count",
        "deep_reply_checks_run",
        "average_deep_reply_checks_per_position",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "validator_skip_used_during_internal_handoff_eval",
        "m3_update_count",
        "m4_promotion_count_by_terminal_kind",
        "pruning_count_by_terminal_kind",
        "scheduler_equivalence_mismatch_count",
        "ablation_results",
        "purity_boundary",
    ):
        assert key in decision

    assert "handoff_gate_terminal" in decision["terminal_lifecycle_policy"]
    assert "actuator_terminal" in decision["terminal_kind_stats"]
    assert decision["guard_used_during_runtime_choice"] is False
    assert decision["validator_skip_used_during_internal_handoff_eval"] is False

