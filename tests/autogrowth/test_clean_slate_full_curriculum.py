from pathlib import Path

from recon_lite_chess.autogrowth import (
    CleanSlateKRKFullCurriculumConfig,
    run_clean_slate_krk_full_curriculum,
)


def test_tg46_clean_slate_full_curriculum_bootstrap(tmp_path: Path) -> None:
    result = run_clean_slate_krk_full_curriculum(
        config=CleanSlateKRKFullCurriculumConfig(
            output_path=str(tmp_path / "bootstrap.json"),
            progress_path=str(tmp_path / "progress.json"),
            markdown_path=str(tmp_path / "bootstrap.md"),
            stage_log_path=str(tmp_path / "pools" / "stages.jsonl.gz"),
            failure_pool_path=str(tmp_path / "pools" / "failure_pool.jsonl.gz"),
            graph_summary_path=str(tmp_path / "pools" / "graph.jsonl.gz"),
            fresh_graph=True,
            mate1_heldout_count=200,
            mate2_heldout_count=120,
            edge_fence_heldout_count=160,
        )
    )
    decision = result.decision
    required = {
        "checkpoint_pass",
        "checkpoint_interpretation",
        "fresh_graph",
        "full_curriculum_attempted",
        "full_curriculum_completed",
        "first_failed_stage",
        "selected_final_runtime_policy",
        "parent_foundation_created_in_run",
        "child_branch_created_in_run",
        "canary_policy_created_in_run",
        "loaded_prior_tg_artifact_count",
        "loaded_prior_learned_node_count",
        "loaded_prior_m3_weight_count",
        "loaded_prior_m4_promotion_count",
        "loaded_prior_child_branch",
        "loaded_prior_boundary_pool_count",
        "loaded_prior_canary_policy",
        "checkpoint_specific_move_rule_count",
        "checkpoint_specific_fen_rule_count",
        "mate1_heldout_accuracy",
        "mate2_heldout_conversion_rate",
        "edge_fence_success_rate",
        "bridge_frontier_success_rate",
        "s1_full_reply_handoff_success_rate",
        "one_reply_false_positive_selected_count",
        "controlled_stage_play_success_rate",
        "paired_help_count",
        "paired_hurt_count",
        "decoy_false_handoff_count",
        "hard_decoy_false_handoff_count",
        "rook_blunder_count",
        "illegal_move_count",
        "stalemate_count",
        "live_cache_mismatch_count",
        "broad_krk_probe_success_rate",
        "broad_krk_probe_reported_separately",
        "runtime_tablebase_or_dtm_move_source",
        "action_ranker_used_for_runtime",
        "python_final_selector_used",
        "direct_provider_override",
        "learner_visible_stage_labels",
        "learner_visible_basin_labels",
        "learner_visible_continuation_labels",
        "purity_boundary",
        "selected_next_action",
        "selected_next_action_reason",
    }
    assert required <= set(decision)
    assert decision["checkpoint_pass"] is True
    assert decision["checkpoint_interpretation"] == "clean_slate_infrastructure_pass_edge_fence_blocked"
    assert decision["fresh_graph"] is True
    assert decision["full_curriculum_attempted"] is True
    assert decision["full_curriculum_completed"] is False
    assert decision["first_failed_stage"] == "edge_fence_safety_progress"
    assert decision["loaded_prior_tg_artifact_count"] == 0
    assert decision["loaded_prior_learned_node_count"] == 0
    assert decision["loaded_prior_m3_weight_count"] == 0
    assert decision["loaded_prior_m4_promotion_count"] == 0
    assert decision["loaded_prior_child_branch"] is False
    assert decision["loaded_prior_boundary_pool_count"] == 0
    assert decision["loaded_prior_canary_policy"] is False
    assert decision["checkpoint_specific_move_rule_count"] == 0
    assert decision["checkpoint_specific_fen_rule_count"] == 0
    assert decision["mate1_heldout_accuracy"] >= 0.99
    assert decision["mate2_heldout_conversion_rate"] >= 0.90
    assert decision["edge_fence_success_rate"] < 0.75
    assert decision["selected_next_action"] == "continue_clean_slate_krk_repair"
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
    assert decision["learner_visible_stage_labels"] is False
    assert Path(result.config.output_path).exists()
    assert Path(result.config.stage_log_path).exists()
    assert Path(result.config.failure_pool_path).exists()
