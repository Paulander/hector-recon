import gzip
from pathlib import Path

from recon_lite_chess.autogrowth import (
    DefaultOffCanaryRuntimeCampaignConfig,
    run_default_off_canary_runtime_campaign,
)


def test_tg39_tg45_default_off_canary_runtime_campaign_smoke(tmp_path: Path) -> None:
    result = run_default_off_canary_runtime_campaign(
        config=DefaultOffCanaryRuntimeCampaignConfig(
            base=DefaultOffCanaryRuntimeCampaignConfig().base.__class__(
                progress_output=str(tmp_path / "campaign_progress.json"),
            ),
            package_doc_path=str(tmp_path / "default_off_canary.md"),
            tg39_output_path=str(tmp_path / "tg39.json"),
            tg39_progress_path=str(tmp_path / "tg39_progress.json"),
            tg39_markdown_path=str(tmp_path / "tg39.md"),
            tg40_output_path=str(tmp_path / "tg40.json"),
            tg40_progress_path=str(tmp_path / "tg40_progress.json"),
            tg40_markdown_path=str(tmp_path / "tg40.md"),
            tg41_output_path=str(tmp_path / "tg41.json"),
            tg41_progress_path=str(tmp_path / "tg41_progress.json"),
            tg42_output_path=str(tmp_path / "tg42.json"),
            tg42_progress_path=str(tmp_path / "tg42_progress.json"),
            tg43_output_path=str(tmp_path / "tg43.json"),
            tg43_progress_path=str(tmp_path / "tg43_progress.json"),
            tg44_output_path=str(tmp_path / "tg44.json"),
            tg44_progress_path=str(tmp_path / "tg44_progress.json"),
            campaign_output_path=str(tmp_path / "campaign.json"),
            campaign_markdown_path=str(tmp_path / "campaign.md"),
            tg40_paired_results_path=str(tmp_path / "tg40_paired.jsonl.gz"),
            tg40_child_interventions_path=str(tmp_path / "tg40_interventions.jsonl.gz"),
            tg40_failure_traces_path=str(tmp_path / "tg40_failures.jsonl.gz"),
            tg40_live_cache_samples_path=str(tmp_path / "tg40_live.jsonl.gz"),
            tg41_hard_decoy_pool_path=str(tmp_path / "tg41_pool.jsonl.gz"),
            tg41_hard_decoy_results_path=str(tmp_path / "tg41_results.jsonl.gz"),
            tg42_gate_diagnostics_path=str(tmp_path / "tg42_gates.jsonl.gz"),
            tg43_live_recompute_samples_path=str(tmp_path / "tg43_live.jsonl.gz"),
            tg44_parent_fail_canary_success_path=str(tmp_path / "tg44_help.jsonl.gz"),
            tg44_parent_success_canary_fail_path=str(tmp_path / "tg44_hurt.jsonl.gz"),
            tg44_both_fail_path=str(tmp_path / "tg44_both.jsonl.gz"),
            tg44_gate_closed_missed_help_path=str(tmp_path / "tg44_gate.jsonl.gz"),
            tg44_hard_decoy_near_false_positive_path=str(tmp_path / "tg44_decoy.jsonl.gz"),
            tg44_broad_probe_failure_path=str(tmp_path / "tg44_broad.jsonl.gz"),
            stage_play_tier_start=800,
            stage_play_tier_max=800,
            hard_decoy_count=1000,
            live_recompute_sample_target=1000,
            seed_count=5,
            target_tier=1,
        )
    )
    d = result.campaign["decision"]
    for path in (
        result.config.tg39_output_path,
        result.config.tg40_output_path,
        result.config.tg41_output_path,
        result.config.tg42_output_path,
        result.config.tg43_output_path,
        result.config.tg44_output_path,
        result.config.campaign_output_path,
        result.config.package_doc_path,
    ):
        assert Path(path).exists()
    for path in (
        result.config.tg40_paired_results_path,
        result.config.tg41_hard_decoy_pool_path,
        result.config.tg43_live_recompute_samples_path,
        result.config.tg44_parent_fail_canary_success_path,
    ):
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
        "tg39_pass",
        "tg40_pass",
        "tg41_pass",
        "tg42_pass",
        "tg43_pass",
        "tg44_pass",
        "tg45_pass",
        "default_runtime_policy",
        "canary_runtime_policy_name",
        "parent_only_default_unchanged",
        "parent_foundation_frozen",
        "foundation_unfrozen_in_main_arm",
        "parent_artifact_modified",
        "child_used_in_main_runtime",
        "child_used_in_experimental_runtime",
        "child_used_in_shadow_only",
        "total_stage_play_episode_count",
        "paired_stage_play_episode_count",
        "parent_stage_play_success_rate",
        "canary_stage_play_success_rate",
        "canary_stage_play_success_delta",
        "paired_help_count",
        "paired_hurt_count",
        "paired_net_help",
        "paired_help_hurt_ratio",
        "decoy_false_handoff_count",
        "hard_decoy_false_handoff_count",
        "live_recompute_sample_count",
        "live_cache_mismatch_count",
        "gate_precision",
        "gate_recall_against_helpful_interventions",
        "success_by_start_family",
        "success_by_horizon",
        "success_by_reply_policy",
        "failure_bucket_counts",
        "mined_curriculum_pool_counts",
        "selected_next_action",
        "selected_next_action_reason",
        "adoption_readiness_classification",
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
    assert required <= set(d)
    assert d["campaign_checkpoint_pass"] is True
    assert d["tg39_pass"] is True
    assert d["tg40_pass"] is True
    assert d["tg41_pass"] is True
    assert d["tg42_pass"] is True
    assert d["tg43_pass"] is True
    assert d["tg44_pass"] is True
    assert d["tg45_pass"] is True
    assert d["default_runtime_policy"] == "parent_only"
    assert d["parent_only_default_unchanged"] is True
    assert d["child_used_in_main_runtime"] is False
    assert d["paired_stage_play_episode_count"] == 800
    assert d["paired_help_count"] > d["paired_hurt_count"]
    assert d["paired_hurt_count"] == 0
    assert d["decoy_false_handoff_count"] == 0
    assert d["hard_decoy_false_handoff_count"] == 0
    assert d["live_recompute_sample_count"] >= 1000
    assert d["live_cache_mismatch_count"] == 0
    assert d["selected_next_action"] in {
        "controlled_default_off_canary_release_branch",
        "broad_krk_probe_curriculum",
        "gate_recall_tuning",
    }
    assert d["action_ranker_used_for_runtime"] is False
    assert d["runtime_tablebase_or_dtm_move_source"] is False
    assert d["python_final_selector_used"] is False
    assert d["direct_provider_override"] is False
