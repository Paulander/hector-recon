import json
from pathlib import Path

from recon_lite_chess.autogrowth import (
    BoundaryDatasetExpansionChildCoverageConfig,
    run_boundary_dataset_expansion_child_coverage_ladder,
)


def test_tg30_expands_boundary_dataset_with_group_disjoint_child_ladder(tmp_path: Path) -> None:
    result = run_boundary_dataset_expansion_child_coverage_ladder(
        config=BoundaryDatasetExpansionChildCoverageConfig(
            base=BoundaryDatasetExpansionChildCoverageConfig().base.__class__(
                progress_output=str(tmp_path / "progress.json"),
            ),
            expanded_boundary_pool_path=str(tmp_path / "expanded.jsonl"),
            expanded_boundary_pool_index_path=str(tmp_path / "expanded_index.json"),
            child_coverage_pool_path=str(tmp_path / "child.jsonl"),
            child_coverage_pool_index_path=str(tmp_path / "child_index.json"),
        )
    )

    output = result.write_json(tmp_path / "tg30.json")
    decision = result.decision
    assert output.exists()
    assert Path(result.config.base.progress_output).exists()
    assert Path(result.config.expanded_boundary_pool_path).exists()
    assert Path(result.config.expanded_boundary_pool_index_path).exists()
    assert Path(result.config.child_coverage_pool_path).exists()
    assert Path(result.config.child_coverage_pool_index_path).exists()

    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "repair_applied",
        "selected_repair_arm",
        "expanded_boundary_pool_entry_count",
        "unique_boundary_fen_count",
        "duplicate_boundary_count",
        "lineage_group_count",
        "boundary_train_count",
        "boundary_heldout_count",
        "boundary_regression_count",
        "boundary_decoy_count",
        "partial_support_boundary_count",
        "outside_frozen_basin_count",
        "bridge_frontier_not_foundation_count",
        "near_miss_decoy_count",
        "clean_decoy_count",
        "parent_boundary_state_count",
        "parent_recognized_count",
        "parent_all_reply_recognized_count",
        "parent_partial_support_count",
        "parent_outside_basin_count",
        "parent_decoy_false_handoff_count",
        "child_branch_created",
        "child_parent_hash",
        "selected_child_arm",
        "child_m3_update_count",
        "child_m4_promotion_count",
        "child_node_count_delta",
        "child_edge_count_delta",
        "child_quorum_count",
        "child_terminal_count",
        "child_train_recognized_count",
        "child_heldout_recognized_count",
        "child_regression_recognized_count",
        "child_decoy_recognized_count",
        "child_boundary_coverage_rate",
        "child_heldout_boundary_coverage_rate",
        "child_regression_boundary_coverage_rate",
        "child_all_reply_foundation_count",
        "child_partial_reply_foundation_count",
        "child_worst_reply_success_count",
        "child_false_positive_count",
        "child_decoy_false_handoff_count",
        "child_near_miss_false_positive_count",
        "missing_evidence_family_counts",
        "evidence_family_gain_by_arm",
        "evidence_family_false_positive_by_arm",
        "evidence_family_decoy_breakage_by_arm",
        "shadow_child_used",
        "shadow_child_used_in_main_eval",
        "parent_main_targeted_success_count",
        "child_shadow_targeted_success_count",
        "child_shadow_foundation_handoff_count",
        "child_shadow_max_move_reached_count",
        "child_shadow_safety_failure_count",
        "child_shadow_decoy_false_handoff_count",
        "parent_foundation_frozen",
        "parent_foundation_m3_updates_during_child_training",
        "parent_foundation_m4_promotions_during_child_training",
        "parent_foundation_m3_updates_during_eval",
        "parent_foundation_m4_promotions_during_eval",
        "foundation_unfrozen_in_main_arm",
        "child_used_in_main_runtime",
        "child_used_in_shadow_only",
        "parent_artifact_modified",
        "parent_foundation_sanity_pass",
        "child_foundation_sanity_pass",
        "known_trajectory_microprobe_pass",
        "s1_full_reply_validation_pass",
        "frontier_regression_pass",
        "staged_regression_pass",
        "staged_near_miss_regression_pass",
        "generic_edge_regression_pass",
        "decoy_rejection_pass",
        "failure_bucket_counts",
        "phase_timings",
        "scheduler_equivalence_mismatch_count",
        "ablation_results",
        "child_foundation_coverage_ablation_causal",
        "guard_used_during_runtime_choice",
        "guard_used_during_evaluation",
        "trainer_side_exploration_used",
        "trainer_side_exploration_used_in_final_eval",
        "shadow_child_foundation_used",
        "shadow_child_foundation_used_in_main_eval",
        "validator_skip_used_during_internal_handoff_eval",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "stage_labels_learner_visible",
        "edge_fence_labels_learner_visible",
        "bridge_labels_learner_visible",
        "staged_labels_learner_visible",
        "trajectory_labels_learner_visible",
        "s1_labels_learner_visible",
        "continuation_labels_learner_visible",
        "quality_tier_labels_learner_visible",
        "depth_labels_learner_visible",
        "reply_policy_labels_learner_visible",
        "basin_labels_learner_visible",
        "direct_provider_override",
        "purity_boundary",
    }
    assert required <= set(decision)
    assert decision["checkpoint_pass"] is True
    assert decision["repair_applied"] is False
    assert decision["expanded_boundary_pool_entry_count"] == 80
    assert decision["unique_boundary_fen_count"] == 80
    assert decision["lineage_group_count"] == 80
    assert decision["boundary_train_count"] == 32
    assert decision["boundary_heldout_count"] == 16
    assert decision["boundary_regression_count"] == 16
    assert decision["boundary_decoy_count"] == 16
    assert decision["parent_recognized_count"] == 0
    assert decision["selected_child_arm"] == "child_boundary_plus_shared_atoms"
    assert decision["child_heldout_recognized_count"] == 8
    assert decision["child_regression_recognized_count"] == 8
    assert decision["child_decoy_recognized_count"] == 0
    assert decision["child_decoy_false_handoff_count"] == 0
    assert decision["shadow_child_used"] is True
    assert decision["parent_foundation_frozen"] is True
    assert decision["foundation_unfrozen_in_main_arm"] is False
    assert decision["child_used_in_main_runtime"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["basin_labels_learner_visible"] is False
    assert decision["direct_provider_override"] is False

    rows = [
        json.loads(line)
        for line in Path(result.config.expanded_boundary_pool_path).read_text().splitlines()
        if line.strip()
    ]
    assert len(rows) == 80
    assert len({row["canonical_fen"] for row in rows}) == 80
    assert all(row["learner_visible_labels"] is False for row in rows)
    group_to_split = {}
    for row in rows:
        prior = group_to_split.setdefault(row["group_id"], row["split_assignment"])
        assert prior == row["split_assignment"]
