from pathlib import Path

from recon_lite_chess.autogrowth import (
    FrozenFoundationBridgePressureConfig,
    run_frozen_foundation_bridge_pressure,
)


def test_tg28b_smoke_reports_bridge_pressure_fields(tmp_path: Path) -> None:
    progress = tmp_path / "tg28b_progress.json"
    result = run_frozen_foundation_bridge_pressure(
        config=FrozenFoundationBridgePressureConfig(
            foundation_mate1_train_count=4,
            foundation_mate1_heldout_count=2,
            foundation_mate2_train_count=1,
            foundation_mate2_heldout_count=1,
            bridge_train_count=2,
            bridge_heldout_count=2,
            generic_edge_safety_heldout_count=1,
            top_k_deep_foundation_checks=1,
            max_edge_candidates_per_position=3,
            max_ablation_positions=0,
            max_foundation_sanity_positions=1,
            max_foundation_ablation_positions=1,
            max_bounded_replies_per_candidate=1,
            max_bounded_second_moves_per_reply=1,
            max_samples=4,
            replay_count=1,
            progress_output=str(progress),
        )
    )

    payload = result.to_dict()
    decision = payload["decision"]
    assert payload["checkpoint"] == "TG28b_frozen_foundation_bridge_pressure"
    assert progress.exists()
    for key in (
        "checkpoint_pass",
        "foundation_frozen",
        "foundation_m3_updates_during_bridge_training",
        "foundation_m4_promotions_during_bridge_training",
        "foundation_m3_updates_during_eval",
        "foundation_m4_promotions_during_eval",
        "foundation_mate1_accuracy",
        "foundation_mate2_conversion_rate",
        "foundation_replay_stability_pass",
        "bridge_train_count",
        "bridge_heldout_count",
        "generic_edge_safety_heldout_count",
        "edge_fence_success_rate",
        "confinement_area_improvement_rate",
        "black_king_mobility_reduction_rate",
        "rook_blunder_count",
        "stalemate_avoidance_rate",
        "selected_move_count",
        "null_move_count",
        "immediate_after_white_move_foundation_reachable_count",
        "reply_envelope_foundation_reachable_count",
        "reply_envelope_foundation_coverage_rate",
        "bounded_bridge_foundation_reachable_count",
        "foundation_handoff_conversion_count",
        "same_graph_foundation_continuation_count",
        "foundation_frontier_request_strength_mean",
        "delta_foundation_proximity_mean",
        "bridge_confidence_confirmed_count",
        "failed_bridge_veto_count",
        "failure_bucket_counts",
        "candidate_budget_used",
        "deep_reply_checks_run",
        "average_deep_reply_checks_per_position",
        "scheduler_equivalence_mismatch_count",
        "edge_only_m3_update_count",
        "bridge_terminal_m3_update_count",
        "m4_promotion_count_by_terminal_kind_edge_bridge_only",
        "ablation_results",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "validator_skip_used_during_internal_handoff_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "stage_labels_learner_visible",
        "edge_fence_labels_learner_visible",
        "bridge_labels_learner_visible",
        "direct_provider_override",
        "purity_boundary",
    ):
        assert key in decision
    assert decision["foundation_frozen"] is True
    assert decision["guard_used_during_runtime_choice"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["edge_fence_labels_learner_visible"] is False
    assert decision["bridge_labels_learner_visible"] is False
