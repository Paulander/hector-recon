import gzip
from pathlib import Path

from recon_lite_chess.autogrowth import (
    RuntimeStageGateCampaignConfig,
    run_runtime_stage_gate_campaign,
)


def test_tg36_tg38_runtime_stage_gate_campaign_smoke(tmp_path: Path) -> None:
    result = run_runtime_stage_gate_campaign(
        config=RuntimeStageGateCampaignConfig(
            base=RuntimeStageGateCampaignConfig().base.__class__(
                progress_output=str(tmp_path / "campaign_progress.json"),
            ),
            tg36_output_path=str(tmp_path / "tg36.json"),
            tg36_progress_path=str(tmp_path / "tg36_progress.json"),
            tg36_markdown_path=str(tmp_path / "tg36.md"),
            tg37_output_path=str(tmp_path / "tg37.json"),
            tg37_progress_path=str(tmp_path / "tg37_progress.json"),
            tg37_markdown_path=str(tmp_path / "tg37.md"),
            tg38_output_path=str(tmp_path / "tg38.json"),
            tg38_progress_path=str(tmp_path / "tg38_progress.json"),
            tg38_markdown_path=str(tmp_path / "tg38.md"),
            campaign_output_path=str(tmp_path / "campaign.json"),
            campaign_markdown_path=str(tmp_path / "campaign.md"),
            tg37_paired_results_path=str(tmp_path / "tg37_paired.jsonl.gz"),
            tg37_child_interventions_path=str(tmp_path / "tg37_interventions.jsonl.gz"),
            tg37_failure_traces_path=str(tmp_path / "tg37_failures.jsonl.gz"),
            tg37_live_cache_samples_path=str(tmp_path / "tg37_live.jsonl.gz"),
            tg38_failure_traces_path=str(tmp_path / "tg38_failures.jsonl.gz"),
            tg38_gate_diagnostics_path=str(tmp_path / "tg38_gates.jsonl.gz"),
            tg38_hurt_case_audit_path=str(tmp_path / "tg38_hurt.jsonl.gz"),
            stage_play_tier_start=600,
            stage_play_tier_max=600,
            seed_count=5,
            live_cache_sample_target=250,
            parity_episode_count=200,
            target_tier=1,
        )
    )
    decision = result.campaign["decision"]
    for path in (
        result.config.tg36_output_path,
        result.config.tg37_output_path,
        result.config.tg38_output_path,
        result.config.campaign_output_path,
        result.config.base.progress_output,
    ):
        assert Path(path).exists()
    for path in (
        result.config.tg37_paired_results_path,
        result.config.tg37_child_interventions_path,
        result.config.tg37_failure_traces_path,
        result.config.tg37_live_cache_samples_path,
        result.config.tg38_gate_diagnostics_path,
    ):
        assert Path(path).exists()
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            assert fh.readline()

    required = {
        "campaign_checkpoint_pass",
        "campaign_interpretation",
        "phases_completed",
        "phases_skipped",
        "total_wall_seconds",
        "requested_max_total_seconds",
        "requested_min_target_seconds",
        "overnight_budget_used_reason",
        "tg36_pass",
        "tg37_pass",
        "tg38_pass",
        "default_runtime_policy",
        "canary_runtime_policy_name",
        "parent_only_default_unchanged",
        "parent_foundation_frozen",
        "foundation_unfrozen_in_main_arm",
        "parent_artifact_modified",
        "child_used_in_main_runtime",
        "child_used_in_experimental_runtime",
        "child_used_in_shadow_only",
        "runtime_policy_installed",
        "rollback_tests_pass",
        "failclosed_tests_pass",
        "total_stage_play_episode_count",
        "paired_stage_play_episode_count",
        "parent_stage_play_success_rate",
        "canary_stage_play_success_rate",
        "canary_stage_play_success_delta",
        "paired_help_count",
        "paired_hurt_count",
        "paired_net_help",
        "paired_help_hurt_ratio",
        "child_intervention_count",
        "child_helped_success_count",
        "child_hurt_success_count",
        "decoy_false_handoff_count",
        "hard_decoy_false_handoff_count",
        "child_confusable_decoy_false_handoff_count",
        "rook_blunder_count_by_branch",
        "illegal_move_count_by_branch",
        "stalemate_count_by_branch",
        "unsafe_move_count_by_branch",
        "live_cache_sample_count",
        "parent_cache_live_mismatch_count",
        "child_cache_live_mismatch_count",
        "reply_envelope_cache_live_mismatch_count",
        "actuator_cache_live_mismatch_count",
        "success_by_start_family",
        "success_by_horizon",
        "success_by_reply_policy",
        "failure_bucket_counts",
        "selected_next_action",
        "selected_next_action_reason",
        "adoption_readiness_classification",
        "parent_foundation_sanity_pass",
        "child_foundation_sanity_pass",
        "known_trajectory_microprobe_pass",
        "s1_full_reply_validation_pass",
        "frontier_regression_pass",
        "staged_regression_pass",
        "staged_near_miss_regression_pass",
        "generic_edge_regression_pass",
        "decoy_rejection_pass",
        "hard_decoy_rejection_pass",
        "artifact_hygiene_applied",
        "largest_committed_file_bytes",
        "compressed_log_count",
        "scheduler_equivalence_mismatch_count",
        "action_ranker_used_for_runtime",
        "runtime_tablebase_or_dtm_move_source",
        "python_final_selector_used",
        "direct_provider_override",
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
        "purity_boundary",
    }
    assert required <= set(decision)
    assert decision["campaign_checkpoint_pass"] is True
    assert decision["tg36_pass"] is True
    assert decision["tg37_pass"] is True
    assert decision["tg38_pass"] is True
    assert decision["default_runtime_policy"] == "parent_only"
    assert decision["parent_only_default_unchanged"] is True
    assert decision["parent_foundation_frozen"] is True
    assert decision["foundation_unfrozen_in_main_arm"] is False
    assert decision["child_used_in_main_runtime"] is False
    assert decision["paired_stage_play_episode_count"] == 600
    assert decision["total_stage_play_episode_count"] == 3000
    assert decision["paired_help_count"] > decision["paired_hurt_count"]
    assert decision["paired_hurt_count"] == 0
    assert decision["decoy_false_handoff_count"] == 0
    assert decision["hard_decoy_false_handoff_count"] == 0
    assert decision["live_cache_sample_count"] >= 250
    assert decision["parent_cache_live_mismatch_count"] == 0
    assert decision["child_cache_live_mismatch_count"] == 0
    assert decision["selected_next_action"] == "default_off_canary_stage_play_package"
    assert decision["action_ranker_used_for_runtime"] is False
    assert decision["runtime_tablebase_or_dtm_move_source"] is False
    assert decision["python_final_selector_used"] is False
    assert decision["direct_provider_override"] is False
    assert decision["basin_labels_learner_visible"] is False
